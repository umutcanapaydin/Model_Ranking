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

**`pyarrow` is imported inside the read (`_bounded_rows`) and nowhere else.** The serving process imports
`app.clients.*` (W-125), and a native library parsing a downloaded file belongs in the refresh child
(D-154). `tests/unit/test_arena_slices.py` fails if the server ever loads it.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.clients.arena import DATASET, score_rows
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
#: A parquet file is compressed, and its footer DECLARES how big the table is. Both are checked
#: against the footer before a single column is materialised: a small file can declare a table that
#: would fill this machine, and reading it first is paying for it first. `text` declares 10,606
#: rows; the uncompressed bound is generous for eleven columns of that.
MAX_PARQUET_ROWS = 50_000
MAX_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
#: What is actually decoded, counted batch by batch, since the footer's sizes are only claimed. The
#: four columns of `text` decode to well under 2 MB on 2026-09-24.
MAX_DECODED_BYTES = 32 * 1024 * 1024
#: The longest model name, category or date string read. Real ones are under 100 characters.
MAX_VALUE_CHARS = 256
_BATCH_ROWS = 2_048
_COLUMNS = ("model_name", "rating", "category", "leaderboard_publish_date")
_TEXT_COLUMNS = ("model_name", "category", "leaderboard_publish_date")


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
    """The file's rows, as plain Python values, read under the bounds above.

    **Every failure inside is a `SourceError`, whatever its class** (wave review B1, security S1).
    The first version caught three exception classes, and a 1.3 KB file with a `date32` at its
    maximum raised `OverflowError` out of the conversion: not a `SourceError`, so the build
    re-raised it, as it does on purpose for a defect, and one hostile file ended the whole nightly
    cycle. A list of the exceptions a native library may raise is a list nobody can finish.
    """
    try:
        return _bounded_rows(raw)
    except SourceError:
        raise
    except Exception as exc:
        msg = f"arena slices: the parquet file could not be read: {type(exc).__name__}: {exc}"
        raise SourceError(msg) from exc


def _bounded_rows(raw: bytes) -> list[dict[str, Any]]:
    """Footer, then types, then the rows batch by batch, counting what is actually decoded.

    **The footer's sizes are the writer's claims** (security S2): a 1 KB file of stock dictionary
    encoding passed every footer check and reached 5.2 GB, and a forged `total_byte_size` passes by
    construction. So the footer checks stay as a first, cheap refusal, and the bound that holds is
    counted: the string columns stay dictionary-encoded while they are read, every batch's decoded
    size is added to a budget, and a value longer than any real one is refused before rows are made
    of it. What remains is one page decoded at the size its own header declares, which no reader
    of this file format can refuse before decoding it (issue filed with the wave close).
    """
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    try:
        parquet = pq.ParquetFile(pa.BufferReader(raw), read_dictionary=list(_TEXT_COLUMNS))
    except Exception as exc:
        msg = f"arena slices: the download is not a readable parquet file: {exc}"
        raise SourceError(msg) from exc

    meta = parquet.metadata
    if meta.num_rows > MAX_PARQUET_ROWS:
        msg = f"arena slices: the file declares {meta.num_rows} rows, over {MAX_PARQUET_ROWS}"
        raise SourceError(msg)
    declared = sum(meta.row_group(i).total_byte_size for i in range(meta.num_row_groups))
    if declared > MAX_UNCOMPRESSED_BYTES:
        msg = f"arena slices: the file declares {declared} bytes, over {MAX_UNCOMPRESSED_BYTES}"
        raise SourceError(msg)
    _check_columns(parquet.schema_arrow, pa)

    rows: list[dict[str, Any]] = []
    decoded = 0
    for batch in parquet.iter_batches(batch_size=_BATCH_ROWS, columns=list(_COLUMNS)):
        decoded += batch.nbytes
        if decoded > MAX_DECODED_BYTES:
            msg = f"arena slices: over {MAX_DECODED_BYTES} bytes decoded; the file has changed shape"
            raise SourceError(msg)
        for column in _TEXT_COLUMNS:
            values = batch.column(column)
            longest = pc.max(pc.utf8_length(values.dictionary)).as_py() if len(values) else None
            if longest is not None and longest > MAX_VALUE_CHARS:
                msg = f"arena slices: a {column} value is longer than {MAX_VALUE_CHARS} characters"
                raise SourceError(msg)
        rows.extend(batch.to_pylist())
    return rows


def _check_columns(schema: Any, pa: Any) -> None:
    """The four columns read, each of the type the live file has (security S1): anything else is a
    changed file, refused before a single value is converted."""
    present = set(schema.names)
    missing = [column for column in _COLUMNS if column not in present]
    if missing:
        msg = f"arena slices: the file has no column {', '.join(missing)}"
        raise SourceError(msg)
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
            msg = f"arena slices: column {column} has type {kind}, not the type the live file has"
            raise SourceError(msg)


def _date(value: object) -> str | None:
    return value[:10] if isinstance(value, str) and value else None


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

