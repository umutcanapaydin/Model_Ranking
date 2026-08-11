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
    python -m app.workflows.recommend --db advisor.db --budget dusuk|orta|sinirsiz
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from app.workflows.rank import RankingRow, build_price_medians, coding_ranking

# Budget thresholds on blended $/1M (documented constants — REQ-REC-002)
BUDGETS: dict[str, float | None] = {"dusuk": 2.0, "orta": 8.0, "sinirsiz": None}
MIN_QUALITY_PCT = 65.0  # Budget Pick floor
VALUE_WINDOW_PTS = 6.0  # Best Value: within N points of the leader
CLOSE_CALL_PTS = 1.5  # near-tie disclosure threshold


@dataclass(frozen=True)
class Pick:
    """One labeled answer (REQ-REC-001)."""

    label: str
    model: str
    vendor: str
    swebench_verified_pct: float
    aider_polyglot_pct: float | None
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
    picks: tuple[Pick, ...]


def confidence_of(row: RankingRow) -> tuple[str, str]:
    """REQ-REC-004: two independent benchmarks → High; one → Medium."""
    if row.aider_polyglot_pct is not None:
        return "High", "two independent benchmarks (SWE-bench Verified + Aider polyglot)"
    return "Medium", "one independent benchmark (SWE-bench Verified)"


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
            if not any(
                o.swebench_verified_pct > r.swebench_verified_pct
                and o.blended_per_m < r.blended_per_m
                for o in rows
            )
        ),
        key=lambda r: (-r.swebench_verified_pct, r.blended_per_m, r.model),
    )


def _pick(label: str, row: RankingRow, why: str, trade_off: str | None) -> Pick:
    conf, basis = confidence_of(row)
    return Pick(
        label=label,
        model=row.model,
        vendor=row.vendor,
        swebench_verified_pct=row.swebench_verified_pct,
        aider_polyglot_pct=row.aider_polyglot_pct,
        blended_per_m=row.blended_per_m,
        input_per_m=row.input_per_m,
        output_per_m=row.output_per_m,
        evidence_date=row.swe_date,
        harness=row.swe_harness,
        confidence=conf,
        confidence_basis=basis,
        why=why,
        trade_off=trade_off,
    )


def recommend(conn: sqlite3.Connection, budget: str = "sinirsiz") -> Recommendation | None:
    """Compute the three answers; None when no model fits the budget."""
    if budget not in BUDGETS:
        msg = f"unknown budget {budget!r}; expected one of {sorted(BUDGETS)}"
        raise ValueError(msg)
    build_price_medians(conn)
    rows = eligible_rows(coding_ranking(conn), budget)
    if not rows:
        return None

    frontier = pareto_frontier(rows)
    quality = frontier[0]

    value_pool = [
        r
        for r in frontier
        if quality.swebench_verified_pct - r.swebench_verified_pct <= VALUE_WINDOW_PTS
    ]
    value = min(value_pool, key=lambda r: (r.blended_per_m, r.model))

    floor_pool = [r for r in rows if r.swebench_verified_pct >= MIN_QUALITY_PCT]
    floor_met = bool(floor_pool)
    cheap = min(floor_pool or rows, key=lambda r: (r.blended_per_m, r.model))

    close_call: str | None = None
    if len(frontier) > 1:
        gap = quality.swebench_verified_pct - frontier[1].swebench_verified_pct
        if gap <= CLOSE_CALL_PTS:
            tie = "aynı puanda" if gap == 0 else f"sadece {gap:.1f} puan geride"
            close_call = (
                f"{frontier[1].model} {tie} — fark hata payı içinde, ikisi de savunulabilir."
            )

    picks = (
        _pick(
            "best_quality",
            quality,
            why=f"Uygun modeller içinde en yüksek SWE-bench Verified puanı (%{quality.swebench_verified_pct:.1f}).",
            trade_off=None,
        ),
        _pick(
            "best_value",
            value,
            why=(
                f"Pareto sınırında, liderin {VALUE_WINDOW_PTS:.0f} puan yakınında kalan en ucuz model."
            ),
            trade_off=(
                None
                if value.model == quality.model
                else (
                    f"Liderden {quality.swebench_verified_pct - value.swebench_verified_pct:.1f} puan düşük, "
                    f"karşılığında %{(1 - value.blended_per_m / quality.blended_per_m) * 100:.0f} daha ucuz."
                )
            ),
        ),
        _pick(
            "budget_pick",
            cheap,
            why=(
                f"Minimum %{MIN_QUALITY_PCT:.0f} kalite şartını geçen en ucuz model."
                if floor_met
                else (
                    f"UYARI: bu bütçede %{MIN_QUALITY_PCT:.0f} kalite şartını geçen model YOK; "
                    "bu, mevcutların en ucuzu — kaliteden ödün veriyorsun."
                )
            ),
            trade_off=(
                None
                if cheap.model == quality.model
                else (
                    f"Liderden {quality.swebench_verified_pct - cheap.swebench_verified_pct:.1f} puan düşük, "
                    f"ama {quality.blended_per_m / cheap.blended_per_m:.0f} kat daha ucuz."
                )
            ),
        ),
    )
    return Recommendation(
        task="coding",
        budget=budget,
        eligible_count=len(rows),
        frontier_size=len(frontier),
        close_call=close_call,
        picks=picks,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50: tests enter HERE, not a unit shim)."""
    parser = argparse.ArgumentParser(prog="recommend", description=__doc__)
    parser.add_argument("--db", required=True, help="path to the pipeline SQLite file")
    parser.add_argument("--budget", choices=sorted(BUDGETS), default="sinirsiz")
    args = parser.parse_args(argv)

    if not Path(args.db).exists():
        print(json.dumps({"error": f"db not found: {args.db}"}))
        return 2
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(args.db)
        rec = recommend(conn, args.budget)
    except sqlite3.Error as exc:
        print(json.dumps({"error": f"db unusable: {exc}"}))
        return 2
    finally:
        if conn is not None:
            conn.close()
    if rec is None:
        print(json.dumps({"error": "no eligible model for this budget", "budget": args.budget}))
        return 1
    print(json.dumps(asdict(rec), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
