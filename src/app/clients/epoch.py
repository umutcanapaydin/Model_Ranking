"""Epoch AI CSV-bundle client and SWE-bench Verified parser (REQ-ING-010).

Epoch publishes a documented downloadable CSV bundle. This client deliberately
does not fetch the web page or archive: it reads one allowlisted CSV from an
explicitly local, unpacked bundle. Acquisition stays a separate, auditable step.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
import re
from pathlib import Path
from typing import TYPE_CHECKING

from app.clients.protocols import SourceError
from app.workflows.schema import ScoreRow

if TYPE_CHECKING:
    from app.clients.protocols import RawSource

EPOCH_BUNDLE_URL = "https://epoch.ai/data/benchmark_data.zip"
EPOCH_SWE_BENCH_FILE = "swe_bench_verified.csv"
SOURCE_NAME = "epoch_swe_bench_verified"
BENCHMARK = "SWE-bench Verified"
METRIC = "% resolved"
HARNESS = "inspect_ai"
# Epoch's OWN prescribed citation, quoted verbatim from the bundle's README, plus the
# licence token. Two URLs appear in this module and they are different things on
# purpose (W4 review BLOCKING-3, second half): `epoch.ai/benchmarks` is the citation
# target Epoch requires; EPOCH_BUNDLE_URL above is where the bytes were acquired. The
# licence is written ONCE, in the project's `CC-BY-4.0` convention (review MINOR-8 \u2014
# it previously appeared twice, in two spellings, so a test could substring-match it).
EPOCH_ATTRIBUTION = (
    "Epoch AI, \u2018AI Benchmarking Hub\u2019. Published online at epoch.ai. "
    "Retrieved from \u2018https://epoch.ai/benchmarks\u2019 [online resource]. "
    "(CC-BY-4.0)"
)

_REQUIRED_COLUMNS = frozenset({"Model version", "mean_score", "Started at"})
_CANONICAL_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def validate_last_verified(value: object, *, source_name: str = SOURCE_NAME) -> str:
    """Return one canonical YYYY-MM-DD acquisition date or fail this source."""
    if not isinstance(value, str) or _CANONICAL_DATE.fullmatch(value) is None:
        msg = f"{source_name}: last_verified must be YYYY-MM-DD"
        raise SourceError(msg)
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        msg = f"{source_name}: last_verified must be YYYY-MM-DD"
        raise SourceError(msg) from exc
    if parsed.isoformat() != value:  # defensive: reject alternate ISO lexical forms
        msg = f"{source_name}: last_verified must be YYYY-MM-DD"
        raise SourceError(msg)
    return value


class EpochClient:
    """RawSource over the allowlisted SWE-bench CSV in a local Epoch bundle.

    ``last_verified`` is the independent bundle-acquisition clock. Evidence age
    remains based on each row's ``Started at`` value, so retrieval cannot make an
    old evaluation look fresh.
    """

    name = SOURCE_NAME
    url = f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}"

    def __init__(self, bundle_dir: str | Path, *, last_verified: str) -> None:
        if isinstance(bundle_dir, str) and "://" in bundle_dir:
            msg = f"{SOURCE_NAME}: expected a local unpacked bundle directory, not a URL"
            raise SourceError(msg)
        self.bundle_dir = Path(bundle_dir)
        self.last_verified = validate_last_verified(last_verified)

    def fetch_raw(self) -> str:
        """Read the allowlisted CSV; missing/unreadable input aborts this source."""
        path = self.bundle_dir / EPOCH_SWE_BENCH_FILE
        if not path.is_file():
            msg = f"{SOURCE_NAME}: missing CSV in local unpacked bundle: {path}"
            raise SourceError(msg)
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            msg = f"{SOURCE_NAME}: CSV is unreadable: {path}: {exc}"
            raise SourceError(msg) from exc


def _started_at(value: object) -> dt.datetime | None:
    """Return a comparable UTC evaluation timestamp, or None for bad evidence."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def _score(value: object) -> float | None:
    """Parse Epoch's [0, 1] mean score; reject bool-like and non-finite values."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        score = float(value)
    except ValueError:
        return None
    return score if math.isfinite(score) and 0.0 <= score <= 1.0 else None


def _csv_entries(raw: str) -> list[dict[str, str | None]]:
    """Validate the board envelope and return its complete, unbounded row set."""
    if not raw.strip():
        msg = f"{SOURCE_NAME}: CSV payload is empty"
        raise SourceError(msg)
    try:
        reader = csv.DictReader(io.StringIO(raw), strict=True)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            msg = f"{SOURCE_NAME}: CSV has no header"
            raise SourceError(msg)
        missing = sorted(_REQUIRED_COLUMNS.difference(fieldnames))
        if missing:
            msg = f"{SOURCE_NAME}: CSV missing required columns: {', '.join(missing)}"
            raise SourceError(msg)
        return list(reader)
    except csv.Error as exc:
        msg = f"{SOURCE_NAME}: CSV payload malformed: {exc}"
        raise SourceError(msg) from exc


def _score_row(
    entry: dict[str, str | None], *, source: str, source_url: str
) -> tuple[dt.datetime, ScoreRow] | None:
    """Map one usable Epoch record; malformed records are counted by the caller."""
    name_raw = entry.get("Model version")
    name = name_raw.strip() if isinstance(name_raw, str) else ""
    score = _score(entry.get("mean_score"))
    started = _started_at(entry.get("Started at"))
    if not name or score is None or started is None:
        return None
    return (
        started,
        ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score * 100.0,
            harness=HARNESS,
            run_date=started.date().isoformat(),
            cost_total=None,
            source=source,
            source_url=source_url,
        ),
    )


def parse_swe_bench_verified(
    raw: str, *, source: str, source_url: str
) -> tuple[list[ScoreRow], int]:
    """Parse Epoch's SWE-bench Verified CSV into the existing score contract.

    Epoch publishes ``mean_score`` as a [0, 1] fraction. The existing project's
    native SWE-bench scale is percentage points, so values are multiplied by 100.
    Duplicate model versions keep the newest evaluation; a timestamp tie keeps the
    higher score. Every discarded row is counted.
    """
    if not source.strip() or not source_url.startswith("https://"):
        msg = f"{SOURCE_NAME}: source provenance is mandatory and must use documented HTTPS"
        raise SourceError(msg)

    best: dict[str, tuple[dt.datetime, ScoreRow]] = {}
    skipped = 0
    for entry in _csv_entries(raw):
        candidate = _score_row(entry, source=source, source_url=source_url)
        if candidate is None:
            skipped += 1
            continue
        started, row = candidate
        prior = best.get(row.raw_name)
        if prior is not None:
            skipped += 1
            prior_started, prior_row = prior
            if (started, row.score) <= (prior_started, prior_row.score):
                continue
        best[row.raw_name] = (started, row)

    if not best:
        msg = f"{SOURCE_NAME}: CSV contains no usable SWE-bench rows"
        raise SourceError(msg)
    return [value[1] for value in best.values()], skipped


def _static_conformance_check(client: RawSource) -> RawSource:
    """Compile-time proof that EpochClient satisfies RawSource (D-001)."""
    return client


if TYPE_CHECKING:
    _static_conformance_check(EpochClient(Path(), last_verified="2000-01-01"))
