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

The protocol: argv[1] is the limits as JSON, stdin is the file, stdout is one JSON object, either
`{"rows": [...]}` or `{"error": "..."}`. Every failure inside is an `error`, whatever its class.
"""

from __future__ import annotations

import json
import os
import resource
import sys
import threading
import time
from typing import Any

#: The exit status of a reader that passed its memory ceiling.
EXIT_OVER_CEILING = 3
_TEXT_COLUMNS = ("model_name", "category", "leaderboard_publish_date")
_COLUMNS = ("model_name", "rating", "category", "leaderboard_publish_date")


class _Refused(Exception):
    """A refusal with its own message (a changed file), as opposed to a failure of the library."""


def _peak_rss() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak) if sys.platform == "darwin" else int(peak) * 1024  # bytes on macOS, KiB on Linux


def _watch(ceiling: int) -> None:
    while True:
        if _peak_rss() > ceiling:
            os._exit(EXIT_OVER_CEILING)
        time.sleep(0.002)


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


def main() -> None:
    limits = json.loads(sys.argv[1])
    threading.Thread(target=_watch, args=(limits["max_rss_bytes"],), daemon=True).start()
    answer = read_rows(sys.stdin.buffer.read(), limits)
    sys.stdout.write(json.dumps(answer))


if __name__ == "__main__":
    main()
