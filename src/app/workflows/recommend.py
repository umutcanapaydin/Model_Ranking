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
    python -m app.workflows.recommend --db advisor.db --budget low|medium|unlimited \
        --task coding|assistant|agentic-coding
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.workflows.categories import CategorySpec, get_category
from app.workflows.rank import (
    RankingRow,
    UnbuiltEvidenceError,
    attributions_for,
    category_ranking,
    require_price_medians,
    secondary_evidence_sources,
)
from app.workflows.schema import EFFORT_UNSPECIFIED
from app.workflows.serialize import recommendation_json

# Budget thresholds on blended $/1M (documented constants — REQ-REC-002)
BUDGETS: dict[str, float | None] = {"low": 2.0, "medium": 8.0, "unlimited": None}
# Per-category thresholds live in CategorySpec (data, not code — M2-W4 review finding 1).
# These aliases exist for tests/documentation of the shipped values:
MIN_QUALITY_PCT = 65.0
VALUE_WINDOW_PTS = 6.0
CLOSE_CALL_PTS = 1.5
MIN_QUALITY_ELO = 1400.0  # recalibrated M3 (REQ-CAL-001) — see categories.py
VALUE_WINDOW_ELO = 30.0
CLOSE_CALL_ELO = 8.0
STALE_NOTICE_DAYS = 90  # REQ-REC-006
# REQ-REC-010: scores reach the JSON contract ROUNDED. Arena hands us
# 1481.5937567329202; an app rendering that is showing precision the benchmark
# does not have. Ranking, Pareto and threshold comparisons keep the raw value —
# only the boundary rounds, and it rounds once, here.
SCORE_DECIMALS = 1


def round_score(value: float) -> float:
    """Round a score for OUTPUT (ranking math keeps the raw value)."""
    return round(value, SCORE_DECIMALS)


def round_optional_score(value: float | None) -> float | None:
    """Same, for evidence-only scores that may be absent — absence is not zero."""
    return None if value is None else round(value, SCORE_DECIMALS)


def shown_gap(leader: float, other: float) -> float:
    """Display delta, computed from the ROUNDED scores the JSON actually carries.

    Subtracting first and rounding after would let the prose contradict the fields:
    two picks both printed as 77.4 while the sentence between them claims a gap.
    """
    return round_score(round_score(leader) - round_score(other))


def lead_phrase(leader: float, other: float, unit: str) -> str:
    """ "1.8 points below the leader" — or, when the shown delta is zero, "level with the leader".

    W4 re-review MINOR-1: the zero-guard existed only on `close_call`, so the same
    payload could say "same score" in one field and "0.0 points lower" in the next.
    Every trade-off string in both engines goes through here.
    """
    delta = shown_gap(leader, other)
    return "level with the leader" if delta == 0 else f"{delta:.1f} {unit} below the leader"


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
    # The effort the SELECTED EVIDENCE carries. M5 security review BLOCKING-1: this
    # published the category's ranking POLICY instead, so `coding` (no policy) served a
    # max-effort score with `effort: null` while the CSV export of the same run printed
    # `effort,max` for the same model — two artifacts contradicting each other, and
    # Trap 2 of the signed plan shipped. The policy is stated once, per answer, in
    # `Recommendation.ranking_effort`.
    effort: str | None
    higher_effort: str | None
    higher_effort_score: float | None
    effort_note: str | None
    confidence: str
    confidence_basis: str
    why: str
    trade_off: str | None


@dataclass(frozen=True)
class Recommendation:
    """Deterministic three-answer result (REQ-REC-001)."""

    task: str
    budget: str
    ranking_effort: str | None
    sources: tuple[str, ...]
    eligible_count: int
    frontier_size: int
    close_call: str | None
    effort_mix_notice: str | None  # M5: comparisons across unequal effort are DISCLOSED
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


def effort_disclosure(
    effort: str | None,
    higher_effort: str | None,
    higher_effort_score: float | None,
    spec: CategorySpec,
) -> str | None:
    """REQ-REC-011 Turkish disclosure for the named comparison level and range.

    M5 security review BLOCKING-1, second half: a category with NO effort policy used to
    say nothing at all — so a max-effort score served under `coding` was silent about
    being a max-effort score. Silence about an effort the evidence explicitly carries is
    the same overclaim in a quieter register. It now says which level the evidence is
    from, and that this category does not compare at a fixed level.
    """
    if spec.ranking_effort is None:
        if effort in (None, EFFORT_UNSPECIFIED):
            return None
        return (
            f"This category does not compare at a fixed effort level; this score comes from a "
            f"run at {effort} effort."
        )
    if effort is None:
        return None
    if higher_effort is None or higher_effort_score is None:
        return (
            f"This model was ranked at {spec.ranking_effort} effort; the same harness and source "
            "publish no comparable result at a higher effort."
        )
    return (
        f"This model was ranked at {spec.ranking_effort} effort; at {higher_effort} effort it "
        f"reaches {round_score(higher_effort_score):.1f} {spec.score_unit}."
    )


def effort_mix_notice(efforts: list[str | None], spec: CategorySpec) -> str | None:
    """Say so when the compared answers do NOT come from one effort level.

    M5 quality gate: the owner's Q1 ruling is "rank at ONE named effort level so the
    comparison stays fair". A category with no policy compares whatever each board
    published — on the live Epoch board that means an 83.5 at `max` ranked above a 78.7
    at an unstated level. No model mixes efforts with ITSELF there, so nothing is
    overstated per model; what was unstated is that the models are not compared at equal
    effort. This does not make an unequal comparison fair. It makes it VISIBLE, which is
    the least this product may do while the policy question is with the owner.
    """
    if spec.ranking_effort is not None:
        return None  # the category already compares at one declared level
    distinct = {e for e in efforts if e}
    if len(distinct) < 2:
        return None
    named = ", ".join(sorted(distinct))
    return (
        "Note: this category does not compare at a fixed effort level, and the scores in this "
        f"answer come from different levels ({named}). A model run at a higher effort can look "
        "better than one run at a lower effort."
    )


def _pick(label: str, row: RankingRow, spec: CategorySpec, why: str, trade_off: str | None) -> Pick:
    conf, basis = confidence_of(row, spec)
    return Pick(
        label=label,
        model=row.model,
        vendor=row.vendor,
        score=round_score(row.score),
        metric=spec.metric,
        secondary_score=round_optional_score(row.secondary_score),
        blended_per_m=row.blended_per_m,
        input_per_m=row.input_per_m,
        output_per_m=row.output_per_m,
        evidence_date=row.evidence_date,
        harness=row.harness,
        effort=row.effort,
        higher_effort=row.higher_effort,
        higher_effort_score=round_optional_score(row.higher_effort_score),
        # Pass the EVIDENCE effort, not the policy — the policy is already `spec`.
        effort_note=effort_disclosure(row.effort, row.higher_effort, row.higher_effort_score, spec),
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
            f"Note: the latest run of {spec.primary_benchmark} data is {latest_run} — "
            f"{age} days old; the ranking may not be current."
        )
    return None


def recommend(
    conn: sqlite3.Connection, budget: str = "unlimited", task: str = "coding"
) -> Recommendation | None:
    """Compute the three answers for a task; None when no model fits (REQ-REC-005).

    **This function no longer writes (M7-W2, REQ-API-007).** It used to call
    `build_price_medians`, which runs `DELETE FROM px_median` + `INSERT` — so a read API rewrote an
    operator table on every request, and could not be driven from a read-only handle at all. M6
    could not remove it (the plan forbade engine changes) and contained it instead, by copying the
    whole database into memory per unauthenticated GET: **W-017**, measured at roughly 47,000x
    amplification and named by D-116 as a condition of go-live.

    The medians were only ever persisted at READ time because there was no BUILD time to persist
    them at. M7-W1 created one, so the write moves there and the containment it forced can go.
    """
    if budget not in BUDGETS:
        msg = f"unknown budget {budget!r}; expected one of {sorted(BUDGETS)}"
        raise ValueError(msg)
    spec = get_category(task)
    require_price_medians(conn)
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
        gap = quality.score - frontier[1].score  # RAW: the threshold decision
        shown = shown_gap(quality.score, frontier[1].score)
        if gap <= close_pts:
            tie = "is level" if shown == 0 else f"is only {shown:.1f} {spec.score_unit} behind"
            close_call = (
                f"{frontier[1].model} {tie} — the gap is within the margin of error and either "
                "choice is defensible."
            )

    unit = spec.score_unit
    picks = (
        _pick(
            "best_quality",
            quality,
            spec,
            why=f"Highest {spec.primary_benchmark} score among eligible models ({quality.score:.1f} {unit}).",
            trade_off=None,
        ),
        _pick(
            "best_value",
            value,
            spec,
            why=(
                f"On the Pareto frontier, the cheapest model within {window:.0f} {unit} of the leader."
            ),
            trade_off=(
                None
                if value.model == quality.model
                else (
                    f"{lead_phrase(quality.score, value.score, unit)}, "
                    f"and {(1 - value.blended_per_m / quality.blended_per_m) * 100:.0f}% cheaper."
                )
            ),
        ),
        _pick(
            "budget_pick",
            cheap,
            spec,
            why=(
                f"Cheapest model that clears the {floor:.0f} {unit} minimum-quality bar."
                if floor_met
                else (
                    f"WARNING: no model in this budget clears the {floor:.0f} {unit} "
                    "minimum-quality bar; this is the cheapest available and you are trading "
                    "quality away."
                )
            ),
            trade_off=(
                None
                if cheap.model == quality.model
                else (
                    f"{lead_phrase(quality.score, cheap.score, unit)}, "
                    f"but {quality.blended_per_m / cheap.blended_per_m:.0f}x cheaper."
                )
            ),
        ),
    )
    return Recommendation(
        task=spec.id,
        budget=budget,
        ranking_effort=spec.ranking_effort,
        # W4 review BLOCKING-2: name only the sources this answer actually read.
        sources=attributions_for(
            {r.evidence_source for r in rows}
            | (
                secondary_evidence_sources(conn, spec)
                if any(r.secondary_score is not None for r in rows)
                else set()
            ),
            priced=True,
        ),
        eligible_count=len(rows),
        frontier_size=len(frontier),
        close_call=close_call,
        effort_mix_notice=effort_mix_notice([p.effort for p in picks], spec),
        stale_notice=_stale_notice(conn, spec),
        picks=picks,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (V4C-50: tests enter HERE, not a unit shim)."""
    parser = argparse.ArgumentParser(prog="recommend", description=__doc__)
    from app.workflows.categories import CATEGORIES

    parser.add_argument("--db", required=True, help="path to the pipeline SQLite file")
    parser.add_argument("--budget", choices=sorted(BUDGETS), default="unlimited")
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
        from app.workflows.subscribe import (
            BudgetShutout,
            SubscriptionRecommendation,
            budget_shutout,
            recommend_subscription,
        )

        conn = sqlite3.connect(args.db)
        rec: Recommendation | SubscriptionRecommendation | None
        shutout: BudgetShutout | None = None
        if args.subscription:
            rec = recommend_subscription(conn, args.budget, args.task)
            if rec is None:
                shutout = budget_shutout(conn, args.budget, args.task)
        else:
            rec = recommend(conn, args.budget, args.task)
    except UnbuiltEvidenceError as exc:
        # **Exit 2, not 1, and the distinction is the whole point of M7-W2.** Exit 1 means "no
        # model fits this budget" — a RESULT, computed from real evidence. An artifact whose price
        # medians were never built produces no evidence at all, and reporting that as exit 1 would
        # tell the operator their budget was too tight when the truth is the database was never
        # finished. Same false-cause defect the /v1 surface had, one boundary over.
        print(json.dumps({"error": str(exc), "artifact": "unbuilt"}))
        return 2
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
        payload: dict[str, object] = {
            "error": f"no eligible {what} for this budget",
            "budget": args.budget,
            "task": args.task,
        }
        if args.subscription and shutout is not None:
            # W4 review MINOR-1: the case where the budget excluded EVERYTHING is the
            # one the user most needs explained, so the count ships here too.
            payload["scoreable_plans"] = shutout.scoreable_plans
            payload["excluded_by_budget"] = shutout.excluded_by_budget
            payload["budget_notice"] = shutout.budget_notice
        print(json.dumps(payload, ensure_ascii=False))
        return 1
    print(json.dumps(recommendation_json(rec), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
