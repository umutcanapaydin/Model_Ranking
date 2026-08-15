"""Recommendation engine: three deterministic answers (REQ-REC-001..004, D-104).

Rule-based and explainable — no LLM anywhere in this path (D-104):
  1. Hard constraints FIRST: budget filters candidates before any scoring
     (REQ-REC-002).
  2. Best Quality = highest score among eligible.
  3. Best Value   = on the quality-cost Pareto frontier, within
     VALUE_WINDOW_PTS of the leader, cheapest — NEVER score/price
     (REQ-REC-003).
  4. Budget Pick  = cheapest eligible model meeting MIN_QUALITY_PCT.
  5. Confidence from independent-source count; near-ties disclosed
     (REQ-REC-004).

CLI (the live entry point, V4C-50):
    python -m app.workflows.recommend --db advisor.db --budget dusuk|orta|sinirsiz --task coding|assistant
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from app.workflows.categories import CategorySpec, get_category
from app.workflows.rank import RankingRow, build_price_medians, category_ranking

# Budget thresholds on blended $/1M (documented constants — REQ-REC-002)
BUDGETS: dict[str, float | None] = {"dusuk": 2.0, "orta": 8.0, "sinirsiz": None}
# Per-category thresholds live in CategorySpec (data, not code — M2-W4 review finding 1).
# These aliases exist for tests/documentation of the shipped values:
MIN_QUALITY_PCT = 65.0
VALUE_WINDOW_PTS = 6.0
CLOSE_CALL_PTS = 1.5
MIN_QUALITY_ELO = 1300.0
VALUE_WINDOW_ELO = 30.0
CLOSE_CALL_ELO = 5.0
STALE_NOTICE_DAYS = 90  # REQ-REC-006


@dataclass(frozen=True)
class Pick:
    """One labeled answer (REQ-REC-001)."""

    label: str
    model: str
    vendor: str
    score: float
    metric: str
    secondary_score: float | None
    blended_per_m: float
    input_per_m: float
    output_per_m: float
    evidence_date: str | None
    harness: str
    confidence: str
    confidence_basis: str
    why: str
    trade_off: str | None


@dataclass(frozen=True)
class Recommendation:
    """Deterministic three-answer result (REQ-REC-001)."""

    task: str
    budget: str
    eligible_count: int
    frontier_size: int
    close_call: str | None
    stale_notice: str | None  # REQ-REC-006: primary source health, never hidden
    picks: tuple[Pick, ...]


def confidence_of(row: RankingRow, spec: CategorySpec) -> tuple[str, str]:
    """REQ-REC-004: two independent benchmarks → High; one → Medium."""
    if row.secondary_score is not None and spec.secondary_benchmark:
        return (
            "High",
            f"two independent benchmarks ({spec.primary_benchmark} + {spec.secondary_benchmark})",
        )
    return "Medium", f"one independent benchmark ({spec.primary_benchmark})"


def eligible_rows(ranking: list[RankingRow], budget: str) -> list[RankingRow]:
    """REQ-REC-002: hard budget constraint BEFORE any scoring."""
    cap = BUDGETS[budget]
    return [r for r in ranking if cap is None or r.blended_per_m <= cap]


def pareto_frontier(rows: list[RankingRow]) -> list[RankingRow]:
    """REQ-REC-003: models not dominated on (quality, cost)."""
    return sorted(
        (
            r
            for r in rows
            if not any(o.score > r.score and o.blended_per_m < r.blended_per_m for o in rows)
        ),
        key=lambda r: (-r.score, r.blended_per_m, r.model),
    )


def _pick(label: str, row: RankingRow, spec: CategorySpec, why: str, trade_off: str | None) -> Pick:
    conf, basis = confidence_of(row, spec)
    return Pick(
        label=label,
        model=row.model,
        vendor=row.vendor,
        score=row.score,
        metric=spec.metric,
        secondary_score=row.secondary_score,
        blended_per_m=row.blended_per_m,
        input_per_m=row.input_per_m,
        output_per_m=row.output_per_m,
        evidence_date=row.evidence_date,
        harness=row.harness,
        confidence=conf,
        confidence_basis=basis,
        why=why,
        trade_off=trade_off,
    )


def _stale_notice(conn: sqlite3.Connection, spec: CategorySpec) -> str | None:
    """REQ-REC-006: if the category's primary evidence is old, SAY it.

    Deterministic proxy (NOT a persisted health flag): newest run_date on the
    primary benchmark vs the newest observed_at anywhere in the DB. Known,
    accepted limitation: a database that was never re-ingested cannot report
    itself stale (no wall-clock anchor, by determinism design — closure note).
    """
    row = conn.execute(
        "SELECT MAX(run_date), (SELECT MAX(observed_at) FROM scores) FROM scores"
        " WHERE benchmark = ?",
        (spec.primary_benchmark,),
    ).fetchone()
    latest_run, observed = row if row else (None, None)
    if latest_run is None or observed is None:
        return None
    import datetime as _dt

    try:
        age = (
            _dt.date.fromisoformat(str(observed)[:10]) - _dt.date.fromisoformat(latest_run[:10])
        ).days
    except ValueError:
        return None
    if age > STALE_NOTICE_DAYS:
        return (
            f"Dikkat: {spec.primary_benchmark} verisinin son koşusu {latest_run} — "
            f"{age} gün eski; sıralama güncel olmayabilir."
        )
    return None


def recommend(
    conn: sqlite3.Connection, budget: str = "sinirsiz", task: str = "coding"
) -> Recommendation | None:
    """Compute the three answers for a task; None when no model fits (REQ-REC-005)."""
    if budget not in BUDGETS:
        msg = f"unknown budget {budget!r}; expected one of {sorted(BUDGETS)}"
        raise ValueError(msg)
    spec = get_category(task)
    build_price_medians(conn)
    rows = eligible_rows(category_ranking(conn, spec), budget)
    if not rows:
        return None

    frontier = pareto_frontier(rows)
    quality = frontier[0]

    window = spec.value_window
    floor = spec.min_quality
    close_pts = spec.close_call

    value_pool = [r for r in frontier if quality.score - r.score <= window]
    value = min(value_pool, key=lambda r: (r.blended_per_m, r.model))

    floor_pool = [r for r in rows if r.score >= floor]
    floor_met = bool(floor_pool)
    cheap = min(floor_pool or rows, key=lambda r: (r.blended_per_m, r.model))

    close_call: str | None = None
    if len(frontier) > 1:
        gap = quality.score - frontier[1].score
        if gap <= close_pts:
            tie = "aynı puanda" if gap == 0 else f"sadece {gap:.1f} {spec.score_unit} geride"
            close_call = (
                f"{frontier[1].model} {tie} — fark hata payı içinde, ikisi de savunulabilir."
            )

    unit = spec.score_unit
    picks = (
        _pick(
            "best_quality",
            quality,
            spec,
            why=f"Uygun modeller içinde en yüksek {spec.primary_benchmark} skoru ({quality.score:.1f} {unit}).",
            trade_off=None,
        ),
        _pick(
            "best_value",
            value,
            spec,
            why=(f"Pareto sınırında, liderin {window:.0f} {unit} yakınında kalan en ucuz model."),
            trade_off=(
                None
                if value.model == quality.model
                else (
                    f"Liderden {quality.score - value.score:.1f} {unit} düşük, "
                    f"karşılığında %{(1 - value.blended_per_m / quality.blended_per_m) * 100:.0f} daha ucuz."
                )
            ),
        ),
        _pick(
            "budget_pick",
            cheap,
            spec,
            why=(
                f"Minimum {floor:.0f} {unit} kalite şartını geçen en ucuz model."
                if floor_met
                else (
                    f"UYARI: bu bütçede {floor:.0f} {unit} kalite şartını geçen model YOK; "
                    "bu, mevcutların en ucuzu — kaliteden ödün veriyorsun."
                )
            ),
            trade_off=(
                None
                if cheap.model == quality.model
                else (
                    f"Liderden {quality.score - cheap.score:.1f} {unit} düşük, "
                    f"ama {quality.blended_per_m / cheap.blended_per_m:.0f} kat daha ucuz."
                )
            ),
        ),
    )
    return Recommendation(
        task=spec.id,
        budget=budget,
        eligible_count=len(rows),
        frontier_size=len(frontier),
        close_call=close_call,
        stale_notice=_stale_notice(conn, spec),
        picks=picks,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50: tests enter HERE, not a unit shim)."""
    parser = argparse.ArgumentParser(prog="recommend", description=__doc__)
    from app.workflows.categories import CATEGORIES

    parser.add_argument("--db", required=True, help="path to the pipeline SQLite file")
    parser.add_argument("--budget", choices=sorted(BUDGETS), default="sinirsiz")
    parser.add_argument("--task", choices=sorted(CATEGORIES), default="coding")
    parser.add_argument(
        "--subscription",
        action="store_true",
        help="recommend a SUBSCRIPTION PLAN instead of a model (REQ-REC-007;"
        " budget tiers = monthly-USD caps from the curated table)",
    )
    args = parser.parse_args(argv)

    if not Path(args.db).exists():
        print(json.dumps({"error": f"db not found: {args.db}"}))
        return 2
    conn: sqlite3.Connection | None = None
    try:
        from app.workflows.subscribe import SubscriptionRecommendation, recommend_subscription

        conn = sqlite3.connect(args.db)
        rec: Recommendation | SubscriptionRecommendation | None
        if args.subscription:
            rec = recommend_subscription(conn, args.budget, args.task)
        else:
            rec = recommend(conn, args.budget, args.task)
    except sqlite3.Error as exc:
        print(json.dumps({"error": f"db unusable: {exc}"}))
        return 2
    except ValueError as exc:
        # e.g. --subscription against a DB with no ingested plan table
        print(json.dumps({"error": str(exc)}))
        return 2
    finally:
        if conn is not None:
            conn.close()
    if rec is None:
        what = "plan" if args.subscription else "model"
        print(
            json.dumps(
                {
                    "error": f"no eligible {what} for this budget",
                    "budget": args.budget,
                    "task": args.task,
                }
            )
        )
        return 1
    print(json.dumps(asdict(rec), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
