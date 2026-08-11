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
from app.clients.litellm import parse_pricing
from app.clients.openrouter import parse_models
from app.clients.protocols import RawSource, SourceError
from app.clients.swebench import parse_verified
from app.workflows.schema import PricingRow, ScoreRow, reset_source


@dataclass(frozen=True)
class SourceReport:
    """What one source contributed to this run (PRD §7 observability)."""

    source: str
    stored: int
    skipped: int
    health: str | None = None  # REQ-ING-003: staleness / anomaly flags, never hidden


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
) -> None:
    """Replace one source's score working set atomically (REQ-ING-004).

    An IntegrityError is re-raised as SourceError so THIS source aborts loudly
    while callers batching sources can proceed with the rest (architecture §3);
    the transaction rolls back, so the old working set survives.
    """
    try:
        with conn:
            reset_source(conn, "scores", source_name)
            conn.executemany(
                "INSERT INTO scores (raw_name, benchmark, metric, score, harness,"
                " run_date, cost_total, source, source_url, observed_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        r.raw_name,
                        r.benchmark,
                        r.metric,
                        r.score,
                        r.harness,
                        r.run_date,
                        r.cost_total,
                        r.source,
                        r.source_url,
                        run.observed_at,
                    )
                    for r in rows
                ],
            )
    except sqlite3.IntegrityError as exc:
        msg = f"{source_name}: score working set violates schema constraints: {exc}"
        raise SourceError(msg) from exc


def ingest_arena(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse the Arena text leaderboard (REQ-ING-007/-004)."""
    rows, skipped = parse_arena(source.fetch_raw(), source=source.name, source_url=source.url)
    _store_scores(conn, source.name, rows, run)
    report = SourceReport(source=source.name, stored=len(rows), skipped=skipped)
    run.reports.append(report)
    return report


def ingest_swebench(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse SWE-bench Verified and replace its working set (REQ-ING-002/-004)."""
    rows, skipped = parse_verified(source.fetch_raw(), source=source.name, source_url=source.url)
    _store_scores(conn, source.name, rows, run)
    report = SourceReport(source=source.name, stored=len(rows), skipped=skipped)
    run.reports.append(report)
    return report


def ingest_aider(conn: sqlite3.Connection, source: RawSource, run: RunContext) -> SourceReport:
    """Fetch + parse Aider polyglot; staleness surfaces in the report (REQ-ING-003/-004)."""
    rows, skipped = parse_polyglot(source.fetch_raw(), source=source.name, source_url=source.url)
    _store_scores(conn, source.name, rows, run)
    report = SourceReport(
        source=source.name,
        stored=len(rows),
        skipped=skipped,
        health=staleness_flag(rows, run.observed_at),
    )
    run.reports.append(report)
    return report
