"""Recommendation engine: three deterministic answers (REQ-REC-001..004, D-104).

Rule-based and explainable — no LLM anywhere in this path (D-104):
  1. Hard constraints FIRST: budget filters candidates before any scoring
     (REQ-REC-002).
  2. Best Quality = highest score among eligible.
  3. Best Value   = on the quality-cost Pareto frontier, within
     VALUE_WINDOW_PTS of the leader, cheapest — NEVER score/price
     (REQ-REC-003).
  4. Budget Pick  = cheapest eligible model clearing the surface's floor, derived from its
     board (D-148 clause 1, D-159).
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
from app.workflows.floors import derived_floor
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
VALUE_WINDOW_PTS = 6.0
CLOSE_CALL_PTS = 1.5
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


def trade_off_facts(
    leader_score: float, other_score: float, unit: str, dearer: float, cheaper: float
) -> dict[str, object]:
    """The values a trade-off sentence quotes — computed ONCE, so the sentence can be derived.

    D-136 says the prose is derived from the fact. That is only true if there is one computation:
    the first version of this rounded independently in two places and the sentence said "3x
    cheaper" while the fact carried `3.1`, so a client composing from the fact would have written a
    different sentence than the one the engine shipped. **Caught by the derivation test on its
    first run**, which is the whole reason that test exists.

    The rounding lives HERE, in the fact, because what the product chooses to round is part of what
    it claims — `3x cheaper` is a claim about magnitude, not a truncated `3.1`.
    """
    fact: dict[str, object] = {
        "behind_by": shown_gap(leader_score, other_score),
        "unit": unit,
    }
    if cheaper <= 0 or dearer <= 0:
        fact["cheaper"] = "unpriced"
        return fact
    ratio = dearer / cheaper
    if ratio < 1.005:
        fact["cheaper"] = "same"
    elif ratio < 2:
        fact["cheaper_by_percent"] = round((1 - cheaper / dearer) * 100)
    else:
        fact["cheaper_by_times"] = round(ratio)
    return fact


def trade_off_sentence(fact: dict[str, object]) -> str:
    """The English sentence, composed from the fact and from nothing else.

    Every number it prints comes out of `fact`, which is what makes the two halves one source of
    truth rather than two that agree today.
    """
    # `lead_phrase`'s exact wording, reproduced from the fact rather than re-invented. The first
    # version of this said "is level with the leader" and a test caught the drift: a refactor that
    # changes shipped wording as a side effect is a product change nobody approved.
    lead = (
        "level with the leader"
        if fact["behind_by"] == 0
        else f"{fact['behind_by']:.1f} {fact['unit']} below the leader"
    )
    if fact.get("cheaper") == "same":
        return f"{lead}, at the same price."
    if fact.get("cheaper") == "unpriced":
        return f"{lead}, at a lower price."
    if "cheaper_by_percent" in fact:
        return f"{lead}, and {fact['cheaper_by_percent']}% cheaper."
    return f"{lead}, but {fact['cheaper_by_times']}x cheaper."


# `cheaper_phrase` was DELETED at M12-W5 (Stage 4.0 MAJOR-5). It implemented this module's
# percentage-vs-multiple rule a second time, W2 wrote it, W4 wired `trade_off_facts` +
# `trade_off_sentence` instead, and **nothing ever called it** — while nine unit tests stood beside
# it, green, measuring a rule the product could not reach. Those tests now run through the shipping
# composer (`tests/unit/test_cheaper_phrase.py`), where a drift in the live rule fails them.
#
# The general form, and the reason this is a comment rather than a silent deletion: **two parallel
# computations that agree today are two sources of truth**, and the dangerous half is always the
# one with the test suite, because that is the half that looks maintained.


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
    #: D-136. The machine-readable half of `why` and `trade_off`: the REASON each pick was chosen
    #: and the values its sentence quotes. The English prose above is DERIVED from these — one
    #: source of truth — so a client can compose the same sentence in another language without the
    #: engine having to hold a second copy of the product's voice.
    #:
    #: If the fact and the sentence ever disagree, the FACT is right and the sentence is a defect.
    why_fact: dict[str, object]
    trade_off_fact: dict[str, object] | None


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


def secondary_age_days(conn: sqlite3.Connection, spec: CategorySpec) -> int | None:
    """How old the SECONDARY board is, or `None` when it cannot be aged. REQ-UNC-002.

    **Public since M13-W2, because `/v1/categories` publishes it (D-138).** The age decides whether
    a pick counts as measured twice, and a reader who is told "measured on one benchmark" beside a
    second score deserves the number that decided it. The route calls THIS function rather than a
    copy, so the age on screen and the age that decided the count cannot be two different numbers.

    Deliberately the same shape as `_stale_notice`'s arithmetic for the primary: newest `run_date`
    on the benchmark, against `MAX(observed_at)` as the anchor. Determinism over wall clock, so a
    rebuild of the same artifact yields the same answer.

    **Board-level, not row-level, and that is the correct grain.** Aider has not been re-run since
    2025-10-03 for anybody; asking per model would compute the same number forty-four times and
    invite a future reader to think some rows were fresher than others.
    """
    if not spec.secondary_benchmark:
        return None
    row = conn.execute(
        "SELECT MAX(run_date), (SELECT MAX(observed_at) FROM scores) FROM scores"
        " WHERE benchmark = ?",
        (spec.secondary_benchmark,),
    ).fetchone()
    latest_run, observed = row if row else (None, None)
    if latest_run is None or observed is None:
        return None
    import datetime as _dt

    try:
        return (
            _dt.date.fromisoformat(str(observed)[:10])
            - _dt.date.fromisoformat(str(latest_run)[:10])
        ).days
    except ValueError:
        return None


def confidence_of(
    row: RankingRow, spec: CategorySpec, secondary_age_days: int | None = None
) -> tuple[str, str]:
    """REQ-REC-004 / REQ-UNC-002: two CURRENT independent benchmarks → High; otherwise Medium.

    **What this used to do, and what the council ruled on 2026-09-06.** It returned "High" whenever
    a secondary score existed, with no regard for the board's age. Measured across nine surfaces and
    three budgets, exactly one pick of eighteen reached High: the coding BUDGET PICK — on the
    strength of Aider polyglot, last run 2025-10-03, **328 days before the artifact's own anchor**,
    covering 15 of 74 models. The flagship best-quality answer, Claude Opus 4.7, read "Medium".
    **The product was most confident about its cheapest fallback**, because a defunct leaderboard
    happened to have measured the older cheap model and not the newer one.

    `STALE_NOTICE_DAYS` is reused rather than a second figure invented: this module already uses 90
    to decide whether the PRIMARY can stand unqualified (REQ-REC-006), and one file holding two
    disagreeing definitions of "stale" is how a threshold becomes folklore.

    `secondary_age_days is None` means the board publishes no dates and cannot be aged, and it does
    NOT upgrade. Being unable to check is not the same as having checked — the "undated is fresh"
    assumption this repository has already shipped once.

    **This is still a coverage count wearing the word "confidence", and renaming it is a separate
    open question.** What changed is only that the count now requires the evidence to be current.
    """
    fresh = secondary_age_days is not None and secondary_age_days <= STALE_NOTICE_DAYS
    if row.secondary_score is not None and spec.secondary_benchmark and fresh:
        return (
            "High",
            f"two independent benchmarks ({spec.primary_benchmark} + {spec.secondary_benchmark})",
        )
    return "Medium", f"one independent benchmark ({spec.primary_benchmark})"


def eligible_rows(ranking: list[RankingRow], budget: str) -> list[RankingRow]:
    """REQ-REC-002: hard budget constraint BEFORE any scoring."""
    cap = BUDGETS[budget]
    return [r for r in ranking if cap is None or r.blended_per_m <= cap]


def _dominates(o: RankingRow, r: RankingRow) -> bool:
    """Does `o` dominate `r` on (quality, cost)? REQ-FIX-001.

    **The predicate this replaces was strict on BOTH axes** — `o.score > r.score and
    o.blended_per_m < r.blended_per_m` — and shipped that way from M2 to M13. Strictness on both is
    not dominance: it exempts every tie. A model with the SAME score at a HIGHER price survived,
    and so did one at the SAME price with a LOWER score, though in each case the reader is simply
    being shown a worse row with nothing to trade for it.

    Measured before the fix, against `advisor.db`: **9 of 27 (surface, budget) combinations
    published a `frontier_size` too large** — and `frontier_size` is a `/v1` field the client
    decodes (`Models.swift`). **No pick moved on that artifact**, checked across all 27
    combinations, so this is not a repair of a recommendation anybody received.

    **It is not a repair that CANNOT move a pick, and the first version of this comment said it
    was — M13-W1 review MAJOR-3.** The claimed proof was that a wrongly-retained row is never
    strictly cheaper than its dominator. The value key is `(blended_per_m, model)`, so a PRICE TIE
    breaks on model NAME, and a reviewer built the counterexample: rows `aaa-worse 80.0 @ $3`,
    `zzz-better 84.0 @ $3`, `leader 86.0 @ $9` returned `aaa-worse` as best value before the fix
    and `zzz-better` after it. The movement is always toward a strictly better model, which is why
    this is a fix rather than a change — but "did not move here" and "cannot move" are different
    claims, and this repository treats a comment's reasoning as load-bearing.

    The `subscription` engine is the one where this bites: an independent seat measured **15 of 27
    combinations changing `frontier_size` there, and 10 changing the published `close_call`
    sentence** — because plans sharing a model at a dearer price are exactly the equal-score case,
    and that is the norm in a plan catalogue rather than an edge of it.

    **Ties dominate nothing, and that is deliberate.** Two rows equal on score AND price leave the
    strict clause false, so both survive. Dropping one would trade an overstated count for a model
    that vanishes for no reason a reader could see, which is the worse defect of the two.
    """
    at_least_as_good = o.score >= r.score and o.blended_per_m <= r.blended_per_m
    strictly_better = o.score > r.score or o.blended_per_m < r.blended_per_m
    return at_least_as_good and strictly_better


def pareto_frontier(rows: list[RankingRow]) -> list[RankingRow]:
    """REQ-REC-003 / REQ-FIX-001: models not dominated on (quality, cost)."""
    return sorted(
        (r for r in rows if not any(_dominates(o, r) for o in rows)),
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


def _pick(
    label: str,
    row: RankingRow,
    spec: CategorySpec,
    why: str,
    trade_off: str | None,
    why_fact: dict[str, object],
    trade_off_fact: dict[str, object] | None = None,
    secondary_age_days: int | None = None,
) -> Pick:
    conf, basis = confidence_of(row, spec, secondary_age_days)
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
        why_fact=why_fact,
        trade_off_fact=trade_off_fact,
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


def unmet_floor_warning(floor: float | None, unit: str, noun: str) -> str:
    """The Budget Pick's warning when nothing clears the floor -- or when there is no floor to clear:
    since D-159 the floor is measured on the surface's own board, and a surface can rank models from
    another source on the same benchmark while its own board is empty."""
    if floor is None:
        return (f"WARNING: this surface's own board is empty today, so no minimum-quality bar can be "
                f"measured; this is the cheapest {noun} available.")
    return (f"WARNING: no {noun} in this budget clears the {floor:g} {unit} minimum-quality bar; "
            "this is the cheapest available and you are trading quality away.")


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
    floor = derived_floor(conn, spec)  # D-159: from the board this answer reads
    close_pts = spec.close_call

    value_pool = [r for r in frontier if quality.score - r.score <= window]
    value = min(value_pool, key=lambda r: (r.blended_per_m, r.model))

    floor_pool = [r for r in rows if floor is not None and r.score >= floor]
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
    # Computed ONCE, before either sentence, because D-136's claim is that the prose is DERIVED.
    # Two parallel computations that agree today are two sources of truth, and the derivation test
    # caught them disagreeing on its first run: `3x cheaper` beside a fact carrying `3.1`.
    # REQ-UNC-002: computed ONCE per answer, not per pick. Staleness is a property of the board,
    # so three picks asking the same question would get the same answer three times and tempt a
    # future reader into thinking they could differ.
    secondary_age = secondary_age_days(conn, spec)
    value_trade_off = trade_off_facts(
        quality.score, value.score, unit, quality.blended_per_m, value.blended_per_m
    )
    cheap_trade_off = trade_off_facts(
        quality.score, cheap.score, unit, quality.blended_per_m, cheap.blended_per_m
    )
    picks = (
        _pick(
            "best_quality",
            quality,
            spec,
            why=f"Highest {spec.primary_benchmark} score among eligible models ({quality.score:.1f} {unit}).",
            trade_off=None,
            why_fact={
                "reason": "highest_score",
                "benchmark": spec.primary_benchmark,
                "score": round_score(quality.score),
                "unit": unit,
            },
            secondary_age_days=secondary_age,
        ),
        _pick(
            "best_value",
            value,
            spec,
            why=(
                f"On the Pareto frontier, the cheapest model within {window:g} {unit} of the leader."
            ),
            trade_off=(
                None if value.model == quality.model else trade_off_sentence(value_trade_off)
            ),
            why_fact={
                "reason": "cheapest_within_window",
                "window": window,
                "unit": unit,
            },
            trade_off_fact=None if value.model == quality.model else value_trade_off,
            secondary_age_days=secondary_age,
        ),
        _pick(
            "budget_pick",
            cheap,
            spec,
            why=(
                # `:g`, not `:.0f`. The floor is a real threshold — `84.4` — and printing it as
                # `84` states a bar the engine does not apply, while the fact beside it carries the
                # true number. D-136's derivation test caught the pair disagreeing; the answer is
                # to stop rounding the claim, not to round the fact.
                f"Cheapest model that clears the {floor:g} {unit} minimum-quality bar."
                if floor_met
                else unmet_floor_warning(floor, unit, "model")
            ),
            trade_off=(
                None if cheap.model == quality.model else trade_off_sentence(cheap_trade_off)
            ),
            why_fact={
                "reason": "cheapest_above_floor" if floor_met else "nothing_clears_floor",
                "floor": floor,
                "unit": unit,
            },
            trade_off_fact=None if cheap.model == quality.model else cheap_trade_off,
            secondary_age_days=secondary_age,
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
