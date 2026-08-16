"""DeepSWE CSV parser with explicit reasoning-effort semantics (REQ-CAN-005)."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.clients.epoch import EPOCH_BUNDLE_URL, validate_last_verified
from app.clients.protocols import SourceError
from app.workflows.registry import resolve_effort
from app.workflows.schema import ScoreRow

if TYPE_CHECKING:
    from app.clients.protocols import RawSource

SOURCE_NAME = "epoch_deepswe_external"
EPOCH_DEEPSWE_FILE = "deepswe_external.csv"
BENCHMARK = "DeepSWE"
METRIC = "% resolved"

_REQUIRED_COLUMNS = frozenset(
    {"Model version", "Pass@1", "Harness", "Reasoning effort", "Release date"}
)


@dataclass(frozen=True)
class EffortParseStats:
    """Discard/conflict accounting; unknown effort is never silently defaulted."""

    skipped: int
    unknown_effort: int
    conflicts: int


class DeepSWEClient:
    """RawSource over the allowlisted DeepSWE CSV in a local Epoch bundle.

    ``last_verified`` records when the local bundle was acquired. DeepSWE has
    no evaluation-date column, so this clock never becomes score evidence age.
    """

    name = SOURCE_NAME
    url = f"{EPOCH_BUNDLE_URL}#{EPOCH_DEEPSWE_FILE}"

    def __init__(self, bundle_dir: str | Path, *, last_verified: str) -> None:
        if isinstance(bundle_dir, str) and "://" in bundle_dir:
            msg = f"{SOURCE_NAME}: expected a local unpacked bundle directory, not a URL"
            raise SourceError(msg)
        self.bundle_dir = Path(bundle_dir)
        self.last_verified = validate_last_verified(last_verified, source_name=SOURCE_NAME)

    def fetch_raw(self) -> str:
        """Read only the allowlisted board; acquisition stays out of runtime."""
        path = self.bundle_dir / EPOCH_DEEPSWE_FILE
        if not path.is_file():
            msg = f"{SOURCE_NAME}: missing CSV in local unpacked bundle: {path}"
            raise SourceError(msg)
        try:
            return path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            msg = f"{SOURCE_NAME}: CSV is unreadable: {path}: {exc}"
            raise SourceError(msg) from exc


def _entries(raw: str) -> list[dict[str, str | None]]:
    if not raw.strip():
        raise SourceError(f"{SOURCE_NAME}: CSV payload is empty")
    try:
        reader = csv.DictReader(io.StringIO(raw), strict=True)
        if reader.fieldnames is None:
            raise SourceError(f"{SOURCE_NAME}: CSV has no header")
        missing = sorted(_REQUIRED_COLUMNS.difference(reader.fieldnames))
        if missing:
            msg = f"{SOURCE_NAME}: CSV missing required columns: {', '.join(missing)}"
            raise SourceError(msg)
        return list(reader)
    except csv.Error as exc:
        raise SourceError(f"{SOURCE_NAME}: CSV payload malformed: {exc}") from exc


def _fraction(value: object) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        score = float(value)
    except ValueError:
        return None
    return score if math.isfinite(score) and 0.0 <= score <= 1.0 else None


def parse_deepswe(
    raw: str, *, source: str, source_url: str
) -> tuple[list[ScoreRow], EffortParseStats]:
    """Parse DeepSWE; explicit column wins a suffix conflict and conflicts are counted.

    ``Release date`` is deliberately not mapped to ``run_date``: it dates the model,
    not the evaluation. DeepSWE evidence therefore remains undated.
    """
    if not source.strip() or not source_url.startswith("https://"):
        msg = f"{SOURCE_NAME}: source provenance is mandatory and must use documented HTTPS"
        raise SourceError(msg)

    best: dict[tuple[str, str, str], ScoreRow] = {}
    skipped = unknown = conflicts = 0
    for entry in _entries(raw):
        raw_name = entry.get("Model version")
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        raw_harness = entry.get("Harness")
        harness = raw_harness.strip() if isinstance(raw_harness, str) else ""
        score = _fraction(entry.get("Pass@1"))
        raw_explicit = entry.get("Reasoning effort")
        explicit = raw_explicit if isinstance(raw_explicit, str) else None
        resolution = resolve_effort(name, explicit)

        if resolution.invalid_explicit or resolution.effort is None:
            skipped += 1
            unknown += 1
            continue
        effort = resolution.effort
        if not name or not harness or score is None:
            skipped += 1
            continue
        if resolution.conflict:
            conflicts += 1

        row = ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score * 100.0,
            harness=harness,
            run_date=None,
            cost_total=None,
            source=source,
            source_url=source_url,
            effort=effort,
        )
        key = (row.raw_name, row.harness, effort)
        prior = best.get(key)
        if prior is not None:
            skipped += 1
            if row.score <= prior.score:
                continue
        best[key] = row

    if not best:
        raise SourceError(f"{SOURCE_NAME}: CSV contains no usable DeepSWE rows")
    return list(best.values()), EffortParseStats(skipped, unknown, conflicts)


def _static_conformance_check(client: RawSource) -> RawSource:
    """Compile-time proof that DeepSWEClient satisfies RawSource (D-001)."""
    return client


if TYPE_CHECKING:
    _static_conformance_check(DeepSWEClient(Path(), last_verified="2000-01-01"))
