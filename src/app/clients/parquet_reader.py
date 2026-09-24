"""Reads one Arena slice parquet file in a process of its own, under a memory ceiling (M17-W2, #22).

**Why a process of its own.** pyarrow decodes a whole column chunk before any check written in
Python can run, whatever the batch size, and the sizes a file declares are the writer's claims: two
independent re-reviews made a 57 KB file take more than 1 GB, and the growth is linear up to the
download cap. No check inside the process that decodes can bound that. So the parent
(`arena_slices._read_table`) starts this module as a child, hands it the file on stdin, and the
child watches its own peak resident size from a thread that runs while pyarrow decodes (it
releases the interpreter lock), leaving with `EXIT_OVER_CEILING` the moment it passes the ceiling.
The owner chose this over accepting the risk (2026-09-24). A native crash in the library ends this
child too, never the refresh.

The protocol: argv[1] is the limits as JSON, stdin is the file, and stdout is JSON lines: one
`{"row": {...}}` per row and a last `{"end": <rows>}`, or a single `{"error": "..."}`. Every failure
inside is an `error`, whatever its class, and its reason is short and printable. One line per row,
not one document: a single `json.dumps` of every row holds the interpreter lock long enough to
starve the watchdog (security re-look 2, S-R2-3), and the parent reads the answer against a bound
(S-R2-1). The reader also stops itself at its own time limit, so a reader orphaned by a killed
refresh does not run on (re-review 2, NIT-R2-2).
"""

from __future__ import annotations

import json
import os
import resource
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any

#: The exit status of a reader that passed its memory ceiling.
EXIT_OVER_CEILING = 3
#: The longest reason the reader gives: an operator's clue, never a copy of the file's contents.
REASON_CHARS = 200
#: Where Linux keeps this process's own peak resident size (`VmHWM`).
_PROC_STATUS = Path("/proc/self/status")
_TEXT_COLUMNS = ("model_name", "category", "leaderboard_publish_date")
_COLUMNS = ("model_name", "rating", "category", "leaderboard_publish_date")


class _Refused(Exception):
    """A refusal with its own message (a changed file), as opposed to a failure of the library."""


def _peak_rss() -> int:
    """This process's own peak resident size, in bytes.

    On Linux from `VmHWM`, not `ru_maxrss`: a child's `ru_maxrss` starts from its parent's peak, so
    a reader started by a large refresh process passed its ceiling before reading a byte (re-review
    2, BLOCKING-R2-1). On macOS `ru_maxrss` is the process's own, in bytes.
    """
    # Read into a plain `str`: mypy narrows `sys.platform` to the platform it runs on, and on Linux
    # CI then called the macOS return below unreachable.
    platform: str = sys.platform
    if platform.startswith("linux"):
        for line in _PROC_STATUS.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1]) * 1024
        # Never `ru_maxrss` here: Linux reports it in KiB, which made the ceiling 1,024 times too
        # large (re-review 3, MINOR-R3-3). The watchdog turns this into a stop.
        msg = f"no VmHWM line in {_PROC_STATUS}"
        raise LookupError(msg)
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _watch(ceiling: int) -> None:
    """Stops the reader past `ceiling`. **Fails closed** (re-review 3, MINOR-R3-3): a watchdog that
    cannot read the peak stops the reader as over its ceiling, never dies and leaves it unbounded."""
    try:
        while _peak_rss() <= ceiling:
            time.sleep(0.002)
    except BaseException:  # noqa: S110 -- any failure to measure is a stop, by design
        pass
    os._exit(EXIT_OVER_CEILING)


def _check_footer(parquet: Any, limits: dict[str, int]) -> None:
    """The footer's claims: a cheap first refusal, never the bound (the ceiling is)."""
    meta = parquet.metadata
    if meta.num_rows > limits["max_rows"]:
        msg = f"the file declares {meta.num_rows} rows, over {limits['max_rows']}"
        raise _Refused(msg)
    declared = sum(meta.row_group(i).total_byte_size for i in range(meta.num_row_groups))
    if declared > limits["max_uncompressed_bytes"]:
        msg = f"the file declares {declared} bytes, over {limits['max_uncompressed_bytes']}"
        raise _Refused(msg)


def _check_columns(schema: Any, pa: Any) -> None:
    """The four columns read, each of the type the live file has (security S1)."""
    present = set(schema.names)
    missing = [column for column in _COLUMNS if column not in present]
    if missing:
        msg = f"the file has no column {', '.join(missing)}"
        raise _Refused(msg)
    for column in _COLUMNS:
        kind = schema.field(column).type
        if pa.types.is_dictionary(kind):
            kind = kind.value_type
        expected = (
            pa.types.is_floating(kind) or pa.types.is_integer(kind)
            if column == "rating"
            else pa.types.is_string(kind) or pa.types.is_large_string(kind)
        )
        if not expected:
            msg = f"column {column} has type {kind}, not the type the live file has"
            raise _Refused(msg)


def _rows(raw: bytes, limits: dict[str, int]) -> list[dict[str, Any]]:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    try:
        parquet = pq.ParquetFile(pa.BufferReader(raw), read_dictionary=list(_TEXT_COLUMNS))
    except Exception as exc:
        msg = f"the download is not a readable parquet file: {exc}"
        raise _Refused(msg) from exc
    _check_footer(parquet, limits)
    _check_columns(parquet.schema_arrow, pa)

    rows: list[dict[str, Any]] = []
    decoded = 0
    for batch in parquet.iter_batches(batch_size=limits["batch_rows"], columns=list(_COLUMNS)):
        # Counted as read (security re-look S-R2): the footer's row count is the writer's claim.
        if len(rows) + batch.num_rows > limits["max_rows"]:
            msg = f"more than {limits['max_rows']} rows read"
            raise _Refused(msg)
        decoded += batch.nbytes
        if decoded > limits["max_decoded_bytes"]:
            msg = f"over {limits['max_decoded_bytes']} bytes decoded; the file has changed shape"
            raise _Refused(msg)
        for column in _TEXT_COLUMNS:
            values = batch.column(column)
            longest = pc.max(pc.utf8_length(values.dictionary)).as_py() if len(values) else None
            if longest is not None and longest > limits["max_value_chars"]:
                msg = f"a {column} value is longer than {limits['max_value_chars']} characters"
                raise _Refused(msg)
        rows.extend(batch.to_pylist())
    return rows


def read_rows(raw: bytes, limits: dict[str, int]) -> dict[str, Any]:
    """The protocol's answer for one file: its rows, or an error. Never raises."""
    try:
        return {"rows": _rows(raw, limits)}
    except _Refused as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"the parquet file could not be read: {type(exc).__name__}: {exc}"}


def printable(reason: str) -> str:
    """A reason short enough to log and free of control characters (security re-look 2, S-R2-2)."""
    return "".join(c if c.isprintable() else "?" for c in reason[:REASON_CHARS])


def _guard(limits: dict[str, int]) -> None:
    """The memory ceiling and the reader's own time limit (SIGALRM ends the process)."""
    threading.Thread(target=_watch, args=(limits["max_rss_bytes"],), daemon=True).start()
    signal.alarm(limits["timeout_s"])


def main() -> None:
    limits = json.loads(sys.argv[1])
    _guard(limits)
    answer = read_rows(sys.stdin.buffer.read(), limits)
    if "error" in answer:
        sys.stdout.write(json.dumps({"error": printable(answer["error"])}) + "\n")
        return
    for row in answer["rows"]:
        sys.stdout.write(json.dumps({"row": row}, ensure_ascii=False) + "\n")
    sys.stdout.write(json.dumps({"end": len(answer["rows"])}) + "\n")


if __name__ == "__main__":
    main()
