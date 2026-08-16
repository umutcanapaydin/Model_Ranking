"""Ingestion workflow: run context + per-source loaders (REQ-ING-001/-004).

A run stamps every stored row with the same ``observed_at`` and reports
per-source stored/skipped counts (PRD §7 observability). Re-running a source
replaces its working set deterministically (REQ-ING-004).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.clients.aider import parse_polyglot, staleness_flag
from app.clients.arena import parse_arena
from app.clients.deepswe import parse_deepswe
from app.clients.epoch import (
    parse_swe_bench_verified as parse_epoch_swe_bench_verified,
)
from app.clients.epoch import validate_last_verified
from app.clients.litellm import parse_pricing
from app.clients.openrouter import parse_models
from app.clients.protocols import RawSource, SourceError
from app.clients.swebench import parse_verified
from app.workflows.registry import resolve_effort
from app.workflows.schema import (
    EFFORT_LEVELS,
    EFFORT_UNSPECIFIED,
    PricingRow,
    ScoreRow,
    reset_source,
)


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


def _store_pricing(
    conn: sqlite3.Connection, source_name: str, rows: list[PricingRow], run: RunContext
) -> None:
    """Replace one source's pricing working set atomically (REQ-ING-004)."""
    try:
        with conn:
            reset_source(conn, "pricing", source_name)
            conn.executemany(
                "INSERT INTO pricing (alias, input_per_m, output_per_m, context,"
                " source, source_url, observed_at) VALUES (?,?,?,?,?,?,?)",
                [
                    (
                        r.alias,
                        r.input_per_m,
                        r.output_per_m,
                        r.context,
                        r.source,
                        r.source_url,
                        run.observed_at,
                    )
                    for r in rows
                ],
            )
    except sqlite3.IntegrityError as exc:
        msg = f"{source_name}: pricing working set violates schema constraints: {exc}"
        raise SourceError(msg) from exc


def ingest_litellm(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse LiteLLM pricing and replace its working set (REQ-ING-001/-004)."""
    rows, skipped = parse_pricing(source.fetch_raw(), source=source.name, source_url=source.url)
    _store_pricing(conn, source.name, rows, run)
    report = SourceReport(source=source.name, stored=len(rows), skipped=skipped)
    run.reports.append(report)
    return report


def ingest_openrouter(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse OpenRouter catalog pricing (REQ-ING-005/-004)."""
    rows, skipped = parse_models(source.fetch_raw(), source=source.name, source_url=source.url)
    _store_pricing(conn, source.name, rows, run)
    report = SourceReport(source=source.name, stored=len(rows), skipped=skipped)
    run.reports.append(report)
    return report


def _store_scores(
    conn: sqlite3.Connection, source_name: str, rows: list[ScoreRow], run: RunContext
) -> int:
    """Replace one source's score working set atomically (REQ-ING-004).

    An IntegrityError is re-raised as SourceError so THIS source aborts loudly
    while callers batching sources can proceed with the rest (architecture §3);
    the transaction rolls back, so the old working set survives.
    """
    try:
        stored_rows = []
        unclassified = 0
        for row in rows:
            if row.effort is not None and row.effort not in EFFORT_LEVELS:
                msg = f"{source_name}: invalid score effort {row.effort!r}"
                raise SourceError(msg)
            inferred = resolve_effort(row.raw_name, row.effort)
            # W-010: `unspecified` is the right VALUE and silence is the wrong DISCLOSURE. A row
            # whose name carries an effort-looking suffix nobody could confirm is counted here, so
            # `effort_unknown: 0` means "none found" rather than "nothing looked".
            unclassified += int(inferred.unclassified_suffix)
            stored_rows.append((row, inferred.effort or EFFORT_UNSPECIFIED))
        with conn:
            reset_source(conn, "scores", source_name)
            conn.executemany(
                "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort,"
                " run_date, cost_total, source, source_url, observed_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        r.raw_name,
                        r.benchmark,
                        r.metric,
                        r.score,
                        r.harness,
                        effort,
                        r.run_date,
                        r.cost_total,
                        r.source,
                        r.source_url,
                        run.observed_at,
                    )
                    for r, effort in stored_rows
                ],
            )
    except sqlite3.IntegrityError as exc:
        msg = f"{source_name}: score working set violates schema constraints: {exc}"
        raise SourceError(msg) from exc
    return unclassified


def ingest_arena(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse the Arena text leaderboard (REQ-ING-007/-004)."""
    rows, skipped = parse_arena(source.fetch_raw(), source=source.name, source_url=source.url)
    unclassified = _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=skipped,
        effort_unknown=unclassified,
    )
    run.reports.append(report)
    return report


def ingest_swebench(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse SWE-bench Verified and replace its working set (REQ-ING-002/-004)."""
    rows, skipped = parse_verified(source.fetch_raw(), source=source.name, source_url=source.url)
    unclassified = _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=skipped,
        effort_unknown=unclassified,
    )
    run.reports.append(report)
    return report


def ingest_epoch(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Ingest Epoch's local SWE-bench CSV as its own source (REQ-ING-010).

    The benchmark and metric deliberately match the existing SWE-bench category,
    while ``source.name`` and the parser's ``inspect_ai`` harness keep the evidence
    independently attributable. Re-runs replace only this Epoch board's rows.
    """
    last_verified = getattr(source, "last_verified", None)
    if last_verified is None:
        msg = f"{source.name}: last_verified is mandatory for the Epoch bundle"
        raise SourceError(msg)
    last_verified = validate_last_verified(last_verified, source_name=source.name)

    rows, skipped = parse_epoch_swe_bench_verified(
        source.fetch_raw(), source=source.name, source_url=source.url
    )
    unclassified = _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=skipped,
        last_verified=last_verified,
        effort_unknown=unclassified,
    )
    run.reports.append(report)
    return report


def ingest_deepswe(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Ingest the signed DeepSWE board with explicit effort accounting.

    Release dates remain model metadata and are never stored as ``run_date``.
    Consequently source and per-plan health disclose this board as undated.
    """
    last_verified = getattr(source, "last_verified", None)
    if last_verified is None:
        msg = f"{source.name}: last_verified is mandatory for the Epoch bundle"
        raise SourceError(msg)
    last_verified = validate_last_verified(last_verified, source_name=source.name)

    rows, stats = parse_deepswe(source.fetch_raw(), source=source.name, source_url=source.url)
    unclassified = _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=stats.skipped,
        last_verified=last_verified,
        # Two populations, both REQ-CAN-005: the parser's rows whose EXPLICIT effort was
        # unusable, plus W-010's rows whose suffix could not be confirmed at store time.
        effort_unknown=stats.unknown_effort + unclassified,
        effort_conflicts=stats.conflicts,
    )
    run.reports.append(report)
    return report


def ingest_aider(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse Aider polyglot; staleness surfaces in the report (REQ-ING-003/-004)."""
    rows, skipped = parse_polyglot(source.fetch_raw(), source=source.name, source_url=source.url)
    unclassified = _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=skipped,
        health=staleness_flag(rows, run.observed_at),
        effort_unknown=unclassified,
    )
    run.reports.append(report)
    return report
