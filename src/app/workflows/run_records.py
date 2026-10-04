"""What a source run records, and how a source fails (W-125, M18-W6).

These three were defined beside the parsers, in `app.workflows.ingest` and
`app.clients.protocols`. The serving process needs them too, for the plans table, and importing
them from there loaded every parser and the HTTP client into the server (W-125). They import
nothing from a client, and `tests/unit/test_nightly_refresh.py` holds that the server loads none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


class SourceError(RuntimeError):
    """A source could not be fetched or its payload failed validation.

    Ingestion of THIS source aborts loudly; other sources proceed
    (architecture §3 — fairness-class fail OPEN).
    """


@dataclass(frozen=True)
class SourceReport:
    """What one source contributed to this run (PRD §7 observability)."""

    source: str
    stored: int
    skipped: int
    health: str | None = None  # REQ-ING-003: staleness / anomaly flags, never hidden
    last_verified: str | None = None  # source acquisition/curation clock, not evidence age
    effort_unknown: int = 0  # REQ-CAN-005: cannot silently default an unclassified run
    effort_conflicts: int = 0  # explicit-column/suffix disagreement, explicit value wins


@dataclass
class RunContext:
    """One pipeline run: a single observed_at stamp + per-source reports."""

    observed_at: str = field(
        default_factory=lambda: datetime.now(tz=UTC).isoformat(timespec="seconds")
    )
    reports: list[SourceReport] = field(default_factory=list)
