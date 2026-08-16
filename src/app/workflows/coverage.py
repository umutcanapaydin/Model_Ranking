"""Coverage and evidence health reports that must never drift silently.

REQ-SUB-005 — **plan coverage**: how many curated plans can actually be ranked,
per category, and for the ones that cannot, WHY. M3 shipped a subscription
answer that offered one plan three times; nothing in the pipeline said so. A
product whose value is "we link plans to evidence" has to measure the linking.

REQ-ING-011 — **source health**: how old each source's newest evidence is. The
M3 owner run surfaced it by accident (SWE-bench's newest run was 170 days old,
Aider's 316). Freshness is now computed, reported, and disclosed rather than
noticed.

REQ-ING-011b — **plan evidence health**: how old the exact score row selected
for each curated plan is. This is deliberately separate from source health: a
fresh unrelated source row cannot make a stale selected plan row look fresh.

All three are DERIVED — they read the database, never write it — so they can run
after any ingest, in CI, or against the owner's local file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from app.workflows.categories import CATEGORIES, CategorySpec
from app.workflows.recommend import round_score
from app.workflows.subscribe import plan_ranking

# A source whose newest evidence is older than this is reported stale. Same
# WINDOW as the recommendation engine's stale_notice (REQ-REC-006), so "old"
# is one number in one place. The CLOCKS deliberately differ and that is not a
# contradiction: the engine compares run_date to the ingest stamp (deterministic
# by design, D-104 — a DB that is never re-ingested cannot report itself stale),
# while this report compares run_date to TODAY, because a report is allowed to
# know what day it is. Review MINOR-2: say which clock, do not imply one.
SOURCE_STALE_DAYS = 90
PLAN_FRESH_DAYS = 60


@dataclass(frozen=True)
class CategoryCoverage:
    """Plan coverage for one category (REQ-SUB-005)."""

    category: str
    total_plans: int
    scoreable_plans: int
    scoreable: tuple[str, ...]
    unscoreable_no_links: tuple[str, ...]  # no plan-page or roster link resolved at all
    unscoreable_no_scores: tuple[str, ...]  # links resolve, but no score on THIS benchmark


@dataclass(frozen=True)
class SourceHealth:
    """Freshness of one evidence source (REQ-ING-011)."""

    source: str
    rows: int
    newest_run_date: str | None
    age_days: int | None
    stale: bool  # True also when rows exist but no parseable date does (fail toward disclosure)


EvidenceStatus = Literal["fresh", "stale", "undated", "unscored"]


@dataclass(frozen=True)
class PlanEvidenceHealth:
    """Freshness of the exact score row selected for one curated plan."""

    category: str
    plan_id: str
    plan: str
    status: EvidenceStatus
    selected_model: str | None
    score: float | None
    harness: str | None
    evidence_source: str | None
    evidence_source_url: str | None
    evidence_date: str | None
    age_days: int | None


@dataclass(frozen=True)
class CategoryEvidenceHealth:
    """REQ-ING-011b partition: every curated plan counted exactly once."""

    category: str
    total_plans: int
    fresh: int
    stale: int
    undated: int
    unscored: int
    plans: tuple[PlanEvidenceHealth, ...]


def plan_coverage(conn: sqlite3.Connection) -> tuple[CategoryCoverage, ...]:
    """Per category: which plans can be ranked, and why the rest cannot."""
    total = conn.execute("SELECT COUNT(*) FROM plans").fetchone()[0]
    linked = {
        pid
        for (pid,) in conn.execute(
            "SELECT DISTINCT plan_id FROM plan_models WHERE model_id IS NOT NULL"
        )
    }
    # Read once, not per category (review MINOR-3). `.get(pid, pid)` keeps the
    # report honest if a link ever outlives its plan: show the id, never crash.
    names: dict[str, str] = dict(conn.execute("SELECT id, name FROM plans"))
    out: list[CategoryCoverage] = []
    for spec in CATEGORIES.values():
        scoreable = {
            pid
            for (pid,) in conn.execute(
                "SELECT DISTINCT pm.plan_id FROM plan_models pm"
                " JOIN scores s ON s.model_id = pm.model_id"
                " WHERE s.benchmark = ? AND s.metric = ?"
                " AND (? IS NULL OR s.effort = ?) AND pm.model_id IS NOT NULL",
                (
                    spec.primary_benchmark,
                    spec.metric,
                    spec.ranking_effort,
                    spec.ranking_effort,
                ),
            )
        }
        no_links = sorted(names.get(p, p) for p in names if p not in linked)
        no_scores = sorted(names.get(p, p) for p in names if p in linked and p not in scoreable)
        out.append(
            CategoryCoverage(
                category=spec.id,
                total_plans=total,
                scoreable_plans=len(scoreable),
                scoreable=tuple(sorted(names.get(p, p) for p in scoreable)),
                unscoreable_no_links=tuple(no_links),
                unscoreable_no_scores=tuple(no_scores),
            )
        )
    return tuple(out)


def plan_evidence_health(
    conn: sqlite3.Connection,
    spec: CategorySpec,
    today: dt.date,
    window_days: int = PLAN_FRESH_DAYS,
) -> CategoryEvidenceHealth:
    """Classify each plan by the evidence row the ranking engine selects.

    Source-global newest dates answer whether a feed is still publishing. They
    do not answer how old the evidence behind a particular plan recommendation
    is. Reusing ``plan_ranking`` keeps score/model/harness/date/provenance tied to
    one real selected row and prevents a fresh unrelated row masking stale picks.
    """
    if window_days <= 0:
        raise ValueError("plan evidence freshness window must be positive")

    selected = {row.plan_id: row for row in plan_ranking(conn, spec)}
    plans: list[PlanEvidenceHealth] = []
    counts: dict[EvidenceStatus, int] = {
        "fresh": 0,
        "stale": 0,
        "undated": 0,
        "unscored": 0,
    }
    for plan_id, plan in conn.execute("SELECT id, name FROM plans ORDER BY id"):
        row = selected.get(plan_id)
        if row is None:
            status: EvidenceStatus = "unscored"
            item = PlanEvidenceHealth(
                category=spec.id,
                plan_id=plan_id,
                plan=plan,
                status=status,
                selected_model=None,
                score=None,
                harness=None,
                evidence_source=None,
                evidence_source_url=None,
                evidence_date=None,
                age_days=None,
            )
        else:
            age: int | None = None
            if row.evidence_date is None:
                status = "undated"
            else:
                try:
                    evidence_day = dt.date.fromisoformat(row.evidence_date)
                    if evidence_day.isoformat() != row.evidence_date:
                        raise ValueError
                except ValueError as exc:
                    msg = (
                        f"{spec.id}/{plan_id}: selected evidence date is not ISO-8601: "
                        f"{row.evidence_date!r}"
                    )
                    raise ValueError(msg) from exc
                age = (today - evidence_day).days
                status = "fresh" if age < window_days else "stale"
            item = PlanEvidenceHealth(
                category=spec.id,
                plan_id=plan_id,
                plan=plan,
                status=status,
                selected_model=row.scored_by_model,
                score=round_score(row.score),
                harness=row.harness,
                evidence_source=row.evidence_source,
                evidence_source_url=row.evidence_source_url,
                evidence_date=row.evidence_date,
                age_days=age,
            )
        counts[status] += 1
        plans.append(item)

    total = len(plans)
    if sum(counts.values()) != total:  # pragma: no cover - defensive invariant
        raise AssertionError("plan evidence statuses do not partition the curated plans")
    return CategoryEvidenceHealth(
        category=spec.id,
        total_plans=total,
        fresh=counts["fresh"],
        stale=counts["stale"],
        undated=counts["undated"],
        unscored=counts["unscored"],
        plans=tuple(plans),
    )


def source_health(
    conn: sqlite3.Connection, today: dt.date, window_days: int = SOURCE_STALE_DAYS
) -> tuple[SourceHealth, ...]:
    """Newest evidence per score source, and whether it has gone quiet."""
    out: list[SourceHealth] = []
    for source, rows, newest in conn.execute(
        "SELECT source, COUNT(*), MAX(run_date) FROM scores GROUP BY source ORDER BY source"
    ):
        age: int | None = None
        if newest:
            try:
                age = (today - dt.date.fromisoformat(str(newest)[:10])).days
            except ValueError:
                age = None
        # Review MINOR-1: a source with rows but no parseable newest date used to
        # report `stale=False` — i.e. "fresh" — which is exactly the direction a
        # health check must never fail in. Unknown age is now treated as stale;
        # `age_days: null` still says WHY, so the report stays diagnosable.
        stale = age > window_days if age is not None else rows > 0
        out.append(
            SourceHealth(
                source=source, rows=rows, newest_run_date=newest, age_days=age, stale=stale
            )
        )
    return tuple(out)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50). 0 = reported, 1 = a category has ZERO coverage, 2 = usage."""
    parser = argparse.ArgumentParser(prog="coverage", description=__doc__)
    parser.add_argument("--db", required=True, help="path to the pipeline SQLite file")
    parser.add_argument("--today", default=None, help="YYYY-MM-DD (tests/CI determinism)")
    args = parser.parse_args(argv)

    if not Path(args.db).is_file():
        print(f"error: db not found: {args.db}", file=sys.stderr)
        return 2
    try:
        today = (
            dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(tz=dt.UTC).date()
        )
    except ValueError:
        print(f"error: --today is not YYYY-MM-DD: {args.today!r}", file=sys.stderr)
        return 2
    conn: sqlite3.Connection | None = None
    try:
        # M4 closure (security review MINOR-4): "this report never writes" was a
        # convention held up by reading the code. `mode=ro` makes it a MECHANISM —
        # SQLite refuses any write on this handle, so a future edit that adds one
        # fails loudly here instead of silently mutating the owner's database.
        conn = sqlite3.connect(f"file:{Path(args.db).as_posix()}?mode=ro", uri=True)
        cov = plan_coverage(conn)
        health = source_health(conn, today)
        plan_health = tuple(plan_evidence_health(conn, spec, today) for spec in CATEGORIES.values())
    except (sqlite3.Error, ValueError) as exc:
        print(f"error: evidence unusable: {exc}", file=sys.stderr)
        return 2
    finally:
        if conn is not None:
            conn.close()

    print(
        json.dumps(
            {
                "plan_coverage": [asdict(c) for c in cov],
                "source_health": [asdict(h) for h in health],
                "plan_evidence_health": [asdict(h) for h in plan_health],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    # Zero coverage in any category means the product cannot answer at all there —
    # louder than a number in a report nobody reads (the v4.3 "warning into a void" rule).
    if any(c.scoreable_plans == 0 for c in cov):
        print("COVERAGE ZERO in at least one category", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
