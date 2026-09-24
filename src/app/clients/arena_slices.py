"""Arena's category slices, read from the dataset's own parquet file (M17-W2, #22, D-164).

**Why this is not `ArenaClient` with a category argument.** Every config of the dataset carries all
its category slices in one split, ordered by category, and `ArenaClient` reads only the `overall`
prefix through `/rows`. Reaching the other slices that way means paging the whole split: about 110
requests a night for `text` alone, the pattern that rate-limited this client before (W-007). The
`filter` endpoint that would select one slice still answers 500 for `text` (W-024, measured
2026-09-24). The dataset publishes each split as ONE parquet file (`text`: 588,920 bytes), so the
owner ruled (2026-09-24) that the slices are read from it, through `pyarrow`: one request per config.

**Same dataset, same licence, same rules.** The file is the dataset's own, on its `main` revision
(`<config>/latest-00000-of-00001.parquet`), under the same CC-BY-4.0 grant as the rows `ArenaClient`
reads, and every row goes through `arena.score_rows`, the rules the `overall` boards already obey.
A file that is resharded (`-00000-of-00002`) is a 404 and so a failed source: loud, and carried
(D-156), never half read.

**The file is read in a process of its own, under a memory ceiling** (`app.clients.parquet_reader`;
the owner's ruling of 2026-09-24 on the wave's re-reviews). pyarrow decodes a whole column chunk
before any check in Python can run, and a file's sizes are its writer's claims, so no check inside
the decoding process bounds it. This module never imports pyarrow: the serving process imports
`app.clients.*` (W-125), and `tests/unit/test_arena_slices.py` fails if the server ever loads it.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.clients.arena import DATASET, score_rows
from app.clients.parquet_reader import EXIT_OVER_CEILING, EXIT_UNMEASURED, printable
from app.clients.protocols import SourceError, fetch_bounded_bytes
from app.workflows.schema import ScoreRow

#: The configs whose slices are read. Adding one is a decision (the plan names each exclusion).
SLICE_CONFIGS = ("text", "vision")
PARQUET_URL = "https://huggingface.co/datasets/{dataset}/resolve/main/{config}/{split}-00000-of-00001.parquet"

#: The download is capped while it is read (`fetch_bounded_bytes`). `text` is 0.6 MB on 2026-09-24,
#: so 8 MB is a thirteen-fold margin that still stops a changed file long before it costs anything.
MAX_PARQUET_BYTES = 8 * 1024 * 1024
_TIMEOUT_S = 30.0
_DEADLINE_S = 120.0
#: The reader's limits, handed to it as JSON (`reader_limits`). The footer's two are a cheap first
#: refusal of an honest file that grew, not a bound: a forged footer passes them by construction.
#: `text` declares 10,606 rows on 2026-09-24; rows are also counted as they are read.
MAX_PARQUET_ROWS = 50_000
MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
#: What is actually decoded, counted batch by batch after pyarrow has decoded it. The four columns
#: of `text` decode to well under 2 MB on 2026-09-24.
MAX_DECODED_BYTES = 32 * 1024 * 1024
#: The longest model name, category or date string read. Real ones are under 100 characters.
MAX_VALUE_CHARS = 256
_BATCH_ROWS = 2_048
#: THE bound: the reader's peak resident size, watched from inside it. The live `text` file reads
#: at about 60 MB (measured 2026-09-24); files built to decode gigabytes stop at the ceiling.
MAX_READER_RSS = 512 * 1024 * 1024
#: How long the reader may take. The live `text` file takes under a second. The reader's own alarm
#: is a little later, so the parent's clean refusal comes first and the alarm only ends an orphan.
READER_TIMEOUT_S = 60.0
#: The largest answer the parent reads (security re-look 2, S-R2-1). The live `text` answer is
#: 1,616,244 bytes of JSON lines (measured 2026-09-24), so 8 MiB is a five-fold margin; at 16 MiB a
#: crafted answer took the refresh process to 245 MiB (security re-look 3, S-R3-1).
MAX_ANSWER_BYTES = 8 * 1024 * 1024
#: The variables the reader may see: none of the owner's tokens (S-R2-4), the same shape as the
#: nightly child's allowlist (`nightly.CHILD_ENV`).
READER_ENV = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ")
#: How much of a failed reader's stderr the reason quotes: an operator's clue, never a dump.
_STDERR_QUOTED = 200


def reader_limits() -> dict[str, int]:
    """The limits handed to the reader, read from this module when it runs (tests change them)."""
    return {
        "max_rows": MAX_PARQUET_ROWS,
        "max_uncompressed_bytes": MAX_UNCOMPRESSED_BYTES,
        "max_decoded_bytes": MAX_DECODED_BYTES,
        "max_value_chars": MAX_VALUE_CHARS,
        "batch_rows": _BATCH_ROWS,
        "max_rss_bytes": MAX_READER_RSS,
        "timeout_s": int(READER_TIMEOUT_S) + 5,
    }


def _reader_command() -> list[str]:
    # `-P`: the working directory stays off the import path, so a planted `pyarrow.py` is never
    # imported (S-R2-4); the package comes from PYTHONPATH (`_reader_env`).
    return [sys.executable, "-B", "-P", "-m", "app.clients.parquet_reader"]


def _reader_env() -> dict[str, str]:
    env = {name: os.environ[name] for name in READER_ENV if name in os.environ}
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def parquet_url(config: str, split: str = "latest") -> str:
    """The file the dataset publishes for one config's split, and the provenance its rows carry."""
    return PARQUET_URL.format(dataset=DATASET, config=config, split=split)


@dataclass(frozen=True)
class ArenaSlice:
    """One category slice of one config, declared as data and stored as its own board."""

    config: str
    category: str
    #: Rows on the slice's publish date when it was declared (2026-09-13, measured 2026-09-24).
    measured_rows: int

    @property
    def source_name(self) -> str:
        """The `scores.source` id. Distinct from every `overall` board's id (`arena_<config>`)."""
        return f"arena_{self.config}_{self.category}"

    @property
    def benchmark(self) -> str:
        """The label rankings join on: shared with no other board, or two boards merge (M14-W2)."""
        return f"Arena {self.config} ({self.category})"

    @property
    def minimum_rows(self) -> int:
        """Half the measured count: below any real day, far above a truncated file (W-024)."""
        return self.measured_rows // 2

    @property
    def maximum_rows(self) -> int:
        """Four times the measured count: far above a board that grew, far below a file built to
        fill the artifact (security re-look 3, S-R3-5: 100,000 rows where 402 were declared)."""
        return self.measured_rows * 4

    def bounds_problem(self, rows: int) -> str | None:
        """Why `rows` parsed rows are not this slice, or None. The ONE rule the build, the smoke
        probe and the contract test hold a slice to (final review M1)."""
        if rows < self.minimum_rows:
            return f"parsed {rows} rows, below its floor of {self.minimum_rows}"
        if rows > self.maximum_rows:
            return f"parsed {rows} rows, over its ceiling of {self.maximum_rows}"
        return None


def _slices(config: str, measured: dict[str, int]) -> tuple[ArenaSlice, ...]:
    return tuple(ArenaSlice(config, category, rows) for category, rows in measured.items())


#: The 35 boards the owner ruled on 2026-09-24: every meaningful slice. Left out, each for its
#: reason (`docs/plans/m17-wave-2-plan.md`): `overall` (read by `ArenaClient`), `exclude_ties` (a
#: method variant), `hard_prompts_english` (the intersection of two slices taken here) and
#: `vision/creative_writing` (no rows on the newest date).
ARENA_SLICES: tuple[ArenaSlice, ...] = (
    *_slices("text", {
        "english": 402,
        "non_english": 402,
        "hard_prompts": 402,
        "instruction_following": 402,
        "creative_writing": 400,
        "multi_turn": 400,
        "coding": 397,
        "math": 384,
        "longer_query": 380,
        "expert": 352,
        "chinese": 373,
        "russian": 366,
        "german": 299,
        "spanish": 283,
        "french": 281,
        "korean": 269,
        "japanese": 265,
        "polish": 222,
        "industry_software_and_it_services": 402,
        "industry_writing_and_literature_and_language": 401,
        "industry_entertainment_and_sports_and_media": 400,
        "industry_life_and_physical_and_social_science": 400,
        "industry_business_and_management_and_financial_operations": 395,
        "industry_mathematical": 379,
        "industry_legal_and_government": 375,
        "industry_medicine_and_healthcare": 371,
    }),
    *_slices("vision", {
        "english": 152,
        "chinese": 117,
        "diagram": 108,
        "ocr": 108,
        "homework": 102,
        "creative_writing_vision": 90,
        "humor": 84,
        "entity_recognition": 48,
        "captioning": 34,
    }),
)


class ArenaSliceClient:
    """Downloads one config's parquet file, which carries every slice of that config."""

    def __init__(self, config: str, split: str = "latest") -> None:
        if config not in SLICE_CONFIGS:
            msg = f"arena slices: no slices are declared for config {config!r}; known: {SLICE_CONFIGS}"
            raise SourceError(msg)
        self.config = config
        self.name = f"arena_slices_{config}"
        self.url = parquet_url(config, split)

    def fetch_bytes(self) -> bytes:
        """The whole file, capped while it is read and bounded in time."""
        return fetch_bounded_bytes(
            self.url, self.name, _TIMEOUT_S, limit=MAX_PARQUET_BYTES, deadline=_DEADLINE_S
        )


def fetch_slices(
    config: str, slices: Sequence[ArenaSlice], *, client: Any = None
) -> tuple[dict[str, list[ScoreRow]], dict[str, int]]:
    """Download one config's file and parse its declared slices: the one path every reader takes
    (the build, the survey, the smoke probe, the contract test; wave review N2)."""
    download = (client or ArenaSliceClient)(config)
    boards = [board for board in slices if board.config == config]
    return parse_arena_slices(download.fetch_bytes(), boards, source_url=download.url)


def _read_table(raw: bytes) -> list[dict[str, Any]]:
    """The file's rows, read by `app.clients.parquet_reader` in a process of its own (D-165).

    **Every way the reader can fail is a `SourceError`** (wave review B1, security S1): it passed its
    memory ceiling, ran out of time, crashed, answered past `MAX_ANSWER_BYTES`, or answered
    something that is not its protocol. A failure that is not a `SourceError` is re-raised by the
    build on purpose and would end the whole unattended cycle over one bad file. Nothing the reader
    says is held whole: the answer is read against its bound, stderr goes to a file and only its
    tail is quoted, and every quoted reason is short and printable (security re-look 2, S-R2-1/-2).
    """
    stopped = threading.Event()
    try:
        stderr_file = tempfile.TemporaryFile()  # noqa: SIM115 -- entered by the `with` just below
    except OSError as exc:  # security re-look 3, S-R3-4: a missing TMPDIR ended the cycle
        msg = f"arena slices: no temporary file for the reader's stderr: {exc}"
        raise SourceError(msg) from exc
    with stderr_file as stderr:
        try:
            reader = subprocess.Popen(  # noqa: S603 -- our own interpreter and module, no shell
                [*_reader_command(), json.dumps(reader_limits())], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=stderr, env=_reader_env())
        except OSError as exc:
            msg = f"arena slices: the reader could not be started: {exc}"
            raise SourceError(msg) from exc

        def stop() -> None:
            stopped.set()
            reader.kill()

        timer = threading.Timer(READER_TIMEOUT_S, stop)
        timer.start()
        with reader:  # closes the reader's pipes on the way out (re-review 3, NIT-R3-2)
            try:
                assert reader.stdin is not None and reader.stdout is not None
                with contextlib.suppress(BrokenPipeError):
                    reader.stdin.write(raw)
                    reader.stdin.close()
                answer = reader.stdout.read(MAX_ANSWER_BYTES + 1)
                if len(answer) > MAX_ANSWER_BYTES:
                    reader.kill()
                    msg = (f"arena slices: the reader's answer passed {MAX_ANSWER_BYTES} bytes "
                           "and was cut off")
                    raise SourceError(msg)
                code = reader.wait()
            finally:
                timer.cancel()
                if reader.poll() is None:
                    reader.kill()
                    reader.wait()
        stderr.seek(max(0, stderr.seek(0, os.SEEK_END) - _STDERR_QUOTED))
        tail = printable(stderr.read().decode("utf-8", "replace").strip())

    if stopped.is_set():
        msg = f"arena slices: the reader took more than {READER_TIMEOUT_S:g} seconds and was stopped"
        raise SourceError(msg)
    if code == EXIT_UNMEASURED:
        msg = ("arena slices: the reader could not measure its memory and stopped itself; the "
               "reading machine, not the file, needs a look")
        raise SourceError(msg)
    if code == EXIT_OVER_CEILING:
        msg = (f"arena slices: the reader passed its memory ceiling of {MAX_READER_RSS} bytes and "
               "was stopped; the file has changed shape")
        raise SourceError(msg)
    if code != 0:
        msg = f"arena slices: the reader exited {code}: {tail}"
        raise SourceError(msg)
    return _answered_rows(answer)


def _answered_rows(answer: bytes) -> list[dict[str, Any]]:
    """The reader's JSON lines, held to the protocol: rows then an end line counting them, or one
    error line."""
    # Split as bytes on `\n` only: `str.splitlines()` also splits on U+2028, U+2029 and U+0085,
    # which a model name may carry and the reader writes raw (re-review 3, MINOR-R3-2), and bytes
    # are held once rather than again as a decoded copy (security re-look 3, S-R3-1).
    try:
        lines = [json.loads(line.decode("utf-8")) for line in answer.split(b"\n") if line]
    except ValueError as exc:
        msg = "arena slices: the reader answered something that is not its protocol"
        raise SourceError(msg) from exc
    if len(lines) == 1 and isinstance(lines[0], dict) and isinstance(lines[0].get("error"), str):
        msg = f"arena slices: {printable(lines[0]['error'])}"
        raise SourceError(msg)
    *body, last = lines or [None]
    rows = [line.get("row") if isinstance(line, dict) else None for line in body]
    if not all(isinstance(row, dict) for row in rows):
        msg = "arena slices: the reader answered something that is not its protocol"
        raise SourceError(msg)
    if not (isinstance(last, dict) and isinstance(last.get("end"), int)):
        msg = "arena slices: the reader's answer has no end line; it was cut short"
        raise SourceError(msg)
    if last["end"] != len(rows):
        msg = f"arena slices: the reader's end line counts {last['end']} rows, and it sent {len(rows)}"
        raise SourceError(msg)
    return [row for row in rows if isinstance(row, dict)]


def _date(value: object) -> str | None:
    """A publish date, only if it IS one (security re-look S-R4): as text, `2026-09-1~` sorts above
    every real date and would have become the newest."""
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def parse_arena_slices(
    raw: bytes, slices: Sequence[ArenaSlice], *, source_url: str, today: dt.date | None = None
) -> tuple[dict[str, list[ScoreRow]], dict[str, int]]:
    """Every declared slice's rows, keyed by its source id; returns (rows, refused per slice).

    **A slice is served only on its config's newest publish date** (FP-M2-2, per slice). The file
    holds one config, so its newest date is the config's; a slice with no rows on that date is
    refused and its rows counted, never served old. A declared slice absent from the file parses to
    no rows, which its own row floor then turns into a failure of that slice alone.
    """
    records = _read_table(raw)
    # Security S4: a date past tomorrow is not a snapshot, it is a stray row. Taken as the newest,
    # one such row would have darkened every slice of the config; so it is refused and counted.
    horizon = ((today or dt.datetime.now(tz=dt.UTC).date()) + dt.timedelta(days=1)).isoformat()
    dates = [d for d in (_date(r.get("leaderboard_publish_date")) for r in records)
             if d and d <= horizon]
    if records and not dates:
        # Review M1: `parse_arena` keeps every row when no date is present, and for one `overall`
        # prefix that is survivable. Here it is not: with no date the newest snapshot cannot be
        # chosen, and a file of two snapshots would serve a stale-but-higher rating as current.
        msg = "arena slices: no row carries a readable leaderboard_publish_date"
        raise SourceError(msg)
    newest = max(dates) if dates else None

    by_category: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        category = record.get("category")
        if isinstance(category, str):
            by_category.setdefault(category, []).append(record)

    rows: dict[str, list[ScoreRow]] = {}
    refused: dict[str, int] = {}
    for board in slices:
        entries = by_category.get(board.category, [])
        # The date is handed on as the string `score_rows` reads, whatever type the column had.
        current = [
            {**e, "leaderboard_publish_date": newest}
            for e in entries
            if _date(e.get("leaderboard_publish_date")) == newest
        ]
        parsed, bad = score_rows(
            current, source=board.source_name, source_url=source_url, benchmark=board.benchmark
        )
        rows[board.source_name] = parsed
        refused[board.source_name] = bad + len(entries) - len(current)
    return rows, refused

