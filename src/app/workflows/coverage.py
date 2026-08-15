"""Coverage + source health: the two numbers that must never drift silently.

REQ-SUB-005 — **plan coverage**: how many curated plans can actually be ranked,
per category, and for the ones that cannot, WHY. M3 shipped a subscription
answer that offered one plan three times; nothing in the pipeline said so. A
product whose value is "we link plans to evidence" has to measure the linking.

REQ-ING-011 — **source health**: how old each source's newest evidence is. The
M3 owner run surfaced it by accident (SWE-bench's newest run was 170 days old,
Aider's 316). Freshness is now computed, reported, and disclosed rather than
noticed.

Both are DERIVED — they read the database, never write it — so they can run
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

from app.workflows.categories import CATEGORIES

# A source whose newest evidence is older than this is reported stale. Same
# WINDOW as the recommendation engine's stale_notice (REQ-REC-006), so "old"
# is one number in one place. The CLOCKS deliberately differ and that is not a
# contradiction: the engine compares run_date to the ingest stamp (deterministic
# by design, D-104 — a DB that is never re-ingested cannot report itself stale),
# while this report compares run_date to TODAY, because a report is allowed to
# know what day it is. Review MINOR-2: say which clock, do not imply one.
SOURCE_STALE_DAYS = 90


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
                " WHERE s.benchmark = ? AND pm.model_id IS NOT NULL",
                (spec.primary_benchmark,),
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
    except sqlite3.Error as exc:
        print(f"error: db unusable: {exc}", file=sys.stderr)
        return 2
    finally:
        if conn is not None:
            conn.close()

    print(
        json.dumps(
            {
                "plan_coverage": [asdict(c) for c in cov],
                "source_health": [asdict(h) for h in health],
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
