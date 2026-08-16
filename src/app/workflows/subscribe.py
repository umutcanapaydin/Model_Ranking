"""Subscription recommender: three deterministic plan answers (REQ-REC-007/-008, D-104).

Same honesty contract as the per-model engine, one level up:
  1. Hard constraints FIRST: the monthly-USD budget cap (plan_config, data)
     filters plans before any scoring.
  2. A plan's quality score = the BEST primary-benchmark score among the
     models its page EXPLICITLY names (plan_models links; M1 rule 4 — a plan
     whose page names nothing rankable is DISCLOSED as unscored, never guessed
     into a ranking).
  3. Best Quality / Best Value (Pareto on score vs monthly price) / Budget
     Pick mirror the model engine, on the category's native scale (D-105).
  4. Stale plan rows are disclosed (REQ-SUB-003 output half), near-ties are
     disclosed, and an unmet quality floor SAYS so instead of pretending.

User-facing strings are Turkish by design (owner's market — .language-allow).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from dataclasses import dataclass

from app.workflows.categories import CategorySpec, get_category
from app.workflows.plans import stale_plans
from app.workflows.rank import attributions_for, higher_effort_evidence
from app.workflows.recommend import (
    effort_disclosure,
    effort_mix_notice,
    lead_phrase,
    round_optional_score,
    round_score,
    shown_gap,
)


@dataclass(frozen=True)
class PlanRank:
    """One rankable plan: its best explicitly-included model on the category's scale."""

    plan_id: str
    plan: str
    provider: str
    monthly_usd: float
    currency: str
    last_verified: str
    source_url: str
    score: float
    scored_by_model: str
    scored_via: str  # 'plan-page' or 'roster' — WHERE the plan->model link came from
    link_source_url: (
        str | None
    )  # roster links carry their own source; plan-page links use the plan's
    link_last_verified: str | None
    harness: str
    effort: str
    higher_effort: str | None
    higher_effort_score: float | None
    evidence_date: str | None
    evidence_source: str
    evidence_source_url: str
    evidence_raw_name: str


@dataclass(frozen=True)
class PlanPick:
    """One labeled subscription answer (REQ-REC-007)."""

    label: str
    plan: str
    provider: str
    monthly_usd: float
    currency: str
    score: float
    metric: str
    scored_by_model: str
    scored_via: str
    link_source_url: str | None
    link_last_verified: str | None
    harness: str
    effort: str | None
    higher_effort: str | None
    higher_effort_score: float | None
    effort_note: str | None
    evidence_date: str | None
    last_verified: str
    source_url: str
    why: str
    trade_off: str | None


#: The three labels a plan answer publishes. Named once so REQ-REC-014's `equivalent_to` can be
#: validated against them instead of being any string at all.
PLAN_PICK_LABELS = ("best_quality", "best_value", "budget_pick")


@dataclass(frozen=True)
class EquivalenceMember:
    """One plan that is indistinguishable on quality from a pick (REQ-REC-014)."""

    plan: str
    plan_id: str
    monthly_usd: float


@dataclass(frozen=True)
class EquivalenceGroup:
    """The plans equivalent to ONE pick, and what makes them equivalent (REQ-REC-014, W-002).

    W-002, raised at M4 and deferred here on purpose: `equivalent_plans` was a flat tuple of plan
    names, so with two or more groups a machine consumer could not tell which pick each plan was
    equivalent to, or at what price. The prose in `equivalence_note` carried the structure and the
    field did not — and prose is not something a client can render from.

    Deferred to the API milestone because the remedy is a CONTRACT shape, and a contract shape is
    decided once, where it freezes.
    """

    equivalent_to: str  # the pick's label: best_quality / best_value / budget_pick
    model: str  # the shared model that makes them indistinguishable
    score: float
    members: tuple[EquivalenceMember, ...]


@dataclass(frozen=True)
class SubscriptionRecommendation:
    """Deterministic three-plan result (REQ-REC-007)."""

    task: str
    budget: str
    ranking_effort: str | None
    sources: tuple[str, ...]
    eligible_count: int
    excluded_by_budget: int
    budget_notice: str | None
    frontier_size: int
    unscored_plans: tuple[str, ...]  # disclosed, never silently dropped
    # Plans that rank IDENTICALLY because their pages name the same model. The
    # three labels then legitimately collapse onto one plan, and the honest answer
    # is not to manufacture variety — it is to say "these are the same engine, buy
    # the cheapest" (M4-W4: measured on live assistant data, three <=$25 plans all
    # scoring 1479.6 via Gemini 3.1 Pro).
    # NOT every label collapse is equivalence: all labels may also land on one plan
    # because only one budget-eligible plan is scoreable. That is a coverage/budget
    # fact, reported separately by `coverage.plan_coverage`, `excluded_by_budget`, and
    # `budget_notice`; this tuple stays empty when no second plan is equivalent TO.
    equivalent_plans: tuple[EquivalenceGroup, ...]
    equivalence_note: str | None
    close_call: str | None
    effort_mix_notice: str | None  # M5: comparisons across unequal effort are DISCLOSED
    stale_notice: str | None  # REQ-REC-008
    picks: tuple[PlanPick, ...]


def _budget_cap(conn: sqlite3.Connection, budget: str) -> float | None:
    row = conn.execute("SELECT cap_dusuk, cap_orta FROM plan_config WHERE id = 1").fetchone()
    if row is None:
        msg = "plan_config missing — ingest the curated plan table first"
        raise ValueError(msg)
    caps: dict[str, float | None] = {"low": row[0], "medium": row[1], "unlimited": None}
    if budget not in caps:
        msg = f"unknown budget {budget!r}; expected one of {sorted(caps)}"
        raise ValueError(msg)
    return caps[budget]


def plan_ranking(conn: sqlite3.Connection, spec: CategorySpec) -> list[PlanRank]:
    """Best primary-benchmark score per plan via its EXPLICIT model links."""
    rows = conn.execute(
        """
        WITH plan_best AS (
          SELECT pm.plan_id, MAX(s.score) AS best
          FROM plan_models pm
          JOIN scores s ON s.model_id = pm.model_id
          WHERE s.benchmark = :primary AND s.metric = :metric
            AND (:effort IS NULL OR s.effort = :effort)
            AND pm.model_id IS NOT NULL
          GROUP BY pm.plan_id
        ),
        detail AS (
          SELECT pm.plan_id, m.id AS model_id, m.display, s.harness, s.effort,
                 s.run_date, s.score,
                 pm.link_source, pm.source_url AS link_source_url,
                 pm.last_verified AS link_last_verified,
                 s.source AS evidence_source,
                 s.source_url AS evidence_source_url,
                 s.raw_name AS evidence_raw_name,
                 ROW_NUMBER() OVER (
                   PARTITION BY pm.plan_id
                   -- plan-page links win ties: the plan's own page is the more
                   -- specific statement about what the plan includes.
                   ORDER BY (pm.link_source = 'plan-page') DESC,
                            (s.run_date IS NOT NULL) DESC, s.run_date DESC,
                            s.harness ASC, m.display ASC, s.source ASC,
                            s.raw_name ASC, pm.raw_name ASC
                 ) AS rn
          FROM plan_models pm
          JOIN scores s ON s.model_id = pm.model_id
          JOIN models m ON m.id = pm.model_id
          JOIN plan_best b ON b.plan_id = pm.plan_id AND b.best = s.score
          WHERE s.benchmark = :primary AND s.metric = :metric
            AND (:effort IS NULL OR s.effort = :effort)
        )
        SELECT p.id, p.name, p.provider, p.monthly_usd, p.currency,
               p.last_verified, p.source_url, b.best,
               (SELECT model_id   FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT display     FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT harness     FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT effort      FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT run_date    FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT link_source FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT link_source_url FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT link_last_verified FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT evidence_source FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT evidence_source_url FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT evidence_raw_name FROM detail d WHERE d.plan_id = p.id AND d.rn = 1)
        FROM plans p
        JOIN plan_best b ON b.plan_id = p.id
        ORDER BY b.best DESC, p.monthly_usd ASC, p.id
        """,
        {
            "primary": spec.primary_benchmark,
            "metric": spec.metric,
            "effort": spec.ranking_effort,
        },
    ).fetchall()
    ranking: list[PlanRank] = []
    for r in rows:
        higher_effort, higher_score = higher_effort_evidence(
            conn, r[8], spec, harness=r[10], source=r[16]
        )
        ranking.append(
            PlanRank(
                plan_id=r[0],
                plan=r[1],
                provider=r[2],
                monthly_usd=r[3],
                currency=r[4],
                last_verified=r[5],
                source_url=r[6],
                score=r[7],
                scored_by_model=r[9],
                harness=r[10],
                effort=r[11],
                higher_effort=higher_effort,
                higher_effort_score=higher_score,
                evidence_date=r[12],
                scored_via=r[13],
                link_source_url=r[14],
                link_last_verified=r[15],
                evidence_source=r[16],
                evidence_source_url=r[17],
                evidence_raw_name=r[18],
            )
        )
    return ranking


def _unscored(conn: sqlite3.Connection, ranked_ids: set[str]) -> tuple[str, ...]:
    """Plans that cannot rank — disclosed with the ranking, never hidden."""
    return tuple(
        name
        for (pid, name) in conn.execute("SELECT id, name FROM plans ORDER BY id")
        if pid not in ranked_ids
    )


def _pareto(rows: list[PlanRank]) -> list[PlanRank]:
    """Plans not dominated on (quality score, monthly price) — REQ-REC-003 shape."""
    return sorted(
        (
            r
            for r in rows
            if not any(o.score > r.score and o.monthly_usd < r.monthly_usd for o in rows)
        ),
        key=lambda r: (-r.score, r.monthly_usd, r.plan),
    )


def _stale_notice(conn: sqlite3.Connection, ranking: list[PlanRank]) -> str | None:
    """REQ-REC-008/W-003: disclose price and selected-roster clocks separately."""
    notices: list[str] = []
    stale = stale_plans(conn)
    if stale:
        listed = ", ".join(f"{s.name} (last verified {s.last_verified})" for s in stale)
        notices.append(
            f"Note: the price verification of {len(stale)} plan row(s) has gone stale — {listed}. "
            "Prices may have changed; do not rely on this answer without re-verifying the table."
        )

    cfg = conn.execute("SELECT staleness_days FROM plan_config WHERE id = 1").fetchone()
    if cfg is None:
        return " ".join(notices) or None
    window = int(cfg[0])
    observed = {
        plan_id: value
        for plan_id, value in conn.execute("SELECT id, observed_at FROM plans ORDER BY id")
    }
    stale_rosters: list[PlanRank] = []
    for row in ranking:
        if row.scored_via != "roster":
            continue
        if row.link_last_verified is None or row.link_source_url is None:
            raise ValueError(f"{row.plan_id}: selected roster link has incomplete provenance")
        try:
            age = (
                dt.date.fromisoformat(str(observed[row.plan_id])[:10])
                - dt.date.fromisoformat(row.link_last_verified)
            ).days
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{row.plan_id}: selected roster link has invalid dates") from exc
        if age > window:
            stale_rosters.append(row)
    if stale_rosters:
        listed = ", ".join(
            f"{row.plan} (roster last verified {row.link_last_verified}, "
            f"kaynak {row.link_source_url})"
            for row in stale_rosters
        )
        notices.append(
            f"Note: the verification of {len(stale_rosters)} selected roster link(s) has gone "
            f"stale — {listed}. Do not rely on this answer without re-verifying the model list."
        )
    return " ".join(notices) or None


def _pick(
    label: str, row: PlanRank, spec: CategorySpec, why: str, trade_off: str | None
) -> PlanPick:
    return PlanPick(
        label=label,
        plan=row.plan,
        provider=row.provider,
        monthly_usd=row.monthly_usd,
        currency=row.currency,
        score=round_score(row.score),
        metric=spec.metric,
        scored_by_model=row.scored_by_model,
        scored_via=row.scored_via,
        link_source_url=row.link_source_url,
        link_last_verified=row.link_last_verified,
        harness=row.harness,
        effort=row.effort,
        higher_effort=row.higher_effort,
        higher_effort_score=round_optional_score(row.higher_effort_score),
        # Pass the EVIDENCE effort, not the policy — the policy is already `spec`.
        effort_note=effort_disclosure(row.effort, row.higher_effort, row.higher_effort_score, spec),
        evidence_date=row.evidence_date,
        last_verified=row.last_verified,
        source_url=row.source_url,
        why=why,
        trade_off=trade_off,
    )


def _budget_notice(excluded_by_budget: int) -> str | None:
    """The one place the priced-out sentence is written (REQ-REC-013, D-111)."""
    if not excluded_by_budget:
        return None
    return f"The budget cap excluded {excluded_by_budget} scoreable plan(s) from the options."


@dataclass(frozen=True)
class BudgetShutout:
    """Why a budget produced NO answer at all (W4 review MINOR-1).

    `recommend_subscription` returns None when the cap excludes every scoreable plan —
    and the first cut computed the priced-out count AFTER that early return, so the one
    case where the user most needs the sentence ("your budget excluded all 6") printed
    a bare error. W-006's complaint was unfixed at exactly its sharpest point while the
    ledger row already read FIXED.
    """

    scoreable_plans: int
    excluded_by_budget: int
    budget_notice: str | None


def budget_shutout(
    conn: sqlite3.Connection, budget: str = "unlimited", task: str = "coding"
) -> BudgetShutout:
    """Count what the cap excluded, for the no-answer path. Read-only."""
    spec = get_category(task)
    cap = _budget_cap(conn, budget)
    ranking = plan_ranking(conn, spec)
    excluded = len([r for r in ranking if cap is not None and r.monthly_usd > cap])
    return BudgetShutout(
        scoreable_plans=len(ranking),
        excluded_by_budget=excluded,
        budget_notice=_budget_notice(excluded),
    )


def recommend_subscription(
    conn: sqlite3.Connection, budget: str = "unlimited", task: str = "coding"
) -> SubscriptionRecommendation | None:
    """Three plan answers for a task; None when no rankable plan fits the budget."""
    spec = get_category(task)
    cap = _budget_cap(conn, budget)
    ranking = plan_ranking(conn, spec)
    unscored = _unscored(conn, {r.plan_id for r in ranking})
    rows = [r for r in ranking if cap is None or r.monthly_usd <= cap]
    if not rows:
        return None
    excluded_by_budget = len(ranking) - len(rows)
    budget_notice = _budget_notice(excluded_by_budget)

    frontier = _pareto(rows)
    quality = frontier[0]
    unit = spec.score_unit

    value_pool = [r for r in frontier if quality.score - r.score <= spec.value_window]
    value = min(value_pool, key=lambda r: (r.monthly_usd, r.plan))

    floor_pool = [r for r in rows if r.score >= spec.min_quality]
    floor_met = bool(floor_pool)
    cheap = min(floor_pool or rows, key=lambda r: (r.monthly_usd, r.plan))

    # Equivalence (M4-W4 review BLOCKING-1). The first cut compared only against the
    # QUALITY pick, so in the live `unlimited` case — where quality is Perplexity Max and
    # BOTH other labels collapse onto Google AI Plus — it said nothing, and the single
    # most useful fact in the data went unsaid: Google AI Ultra at $99.99 scores exactly
    # what Google AI Plus scores at $4.99. Equivalence is now computed for EVERY plan a
    # label actually picked.
    #
    # A group is built from PlanRank rows and keyed on `plan_id`, never on the display
    # name (W4 re-review MINOR-3): `plans.name` carries no UNIQUE constraint, so two
    # curated rows may share a name, and re-resolving membership by name would pull a
    # DIFFERENT plan — scoring a different model — into the price span this sentence
    # claims is "the same model". Only `rows` (already cap-filtered) is scanned, so a
    # plan the budget excluded can never be named as an option.
    groups: list[tuple[str, PlanRank, list[PlanRank]]] = []
    seen_models: set[tuple[str, float]] = set()
    # Labelled, because REQ-REC-014 makes the pick a group is equivalent TO part of the contract.
    for label, picked in zip(PLAN_PICK_LABELS, (quality, value, cheap), strict=True):
        # One group per (model, score): the three labels frequently pick the same
        # plan, and the note must not repeat itself when they do.
        key = (picked.scored_by_model, picked.score)
        if key in seen_models:
            continue
        seen_models.add(key)
        tied = sorted(
            (
                r
                for r in rows
                if r.plan_id != picked.plan_id
                and r.scored_by_model == picked.scored_by_model
                and r.score == picked.score
            ),
            key=lambda r: (r.monthly_usd, r.plan, r.plan_id),
        )
        if tied:
            groups.append((label, picked, tied))

    equivalent = tuple(
        EquivalenceGroup(
            equivalent_to=label,
            model=picked.scored_by_model,
            score=picked.score,
            members=tuple(
                EquivalenceMember(plan=r.plan, plan_id=r.plan_id, monthly_usd=r.monthly_usd)
                for r in tied
            ),
        )
        for label, picked, tied in groups
    )
    equivalence_note: str | None = None
    if groups:
        parts = []
        for _label, picked, tied in groups:
            members = [picked, *tied]
            cheapest = min(members, key=lambda r: (r.monthly_usd, r.plan))
            dearest = max(members, key=lambda r: (r.monthly_usd, r.plan))
            span = (
                f" Monthly difference for the same model: ${cheapest.monthly_usd:.2f} — "
                f"${dearest.monthly_usd:.2f}."
                if dearest.monthly_usd > cheapest.monthly_usd
                else ""
            )
            # M4 closure L-1: the verb may not claim more than the evidence. A
            # roster-linked member's PLAN PAGE names no model — the provider's separate
            # model list does — so the group says "links to" and then names which
            # members rest on the roster. `_pick`'s `why` text already draws exactly
            # this line; the group sentence must not blur it back.
            via_roster = sorted(r.plan for r in members if r.scored_via != "plan-page")
            provenance = (
                f" For {', '.join(via_roster)} the source is the provider's published model "
                "list, not the plan page."
                if via_roster
                else ""
            )
            parts.append(
                f"{len(members)} plans link to the same model ({picked.scored_by_model}), so "
                f"they are indistinguishable on quality: "
                f"{', '.join(sorted(r.plan for r in members))}. "
                f"Bu grupta en ucuzu {cheapest.plan} (${cheapest.monthly_usd:.2f}/ay)."
                f"{span}{provenance}"
            )
        equivalence_note = " ".join(parts)

    close_call: str | None = None
    if len(frontier) > 1:
        gap = quality.score - frontier[1].score  # RAW: the threshold decision
        # Display delta is computed from the ROUNDED scores the JSON actually carries,
        # so the text can never contradict the fields (review MINOR-3), and a sub-0.05
        # gap says "same score" instead of the nonsense "only 0.0 behind" (MINOR-4).
        shown = shown_gap(quality.score, frontier[1].score)
        if gap <= spec.close_call:
            tie = "is level" if shown == 0 else f"is only {shown:.1f} {unit} behind"
            close_call = (
                f"{frontier[1].plan} {tie} — the gap is within the margin of error and either "
                "choice is defensible."
            )

    picks = (
        _pick(
            "best_quality",
            quality,
            spec,
            why=(
                f"The plan within budget whose model has the highest {spec.primary_benchmark} score"
                f" ({quality.scored_by_model}, {quality.score:.1f} {unit}) "
                + (
                    "is named explicitly on this plan's own page."
                    if quality.scored_via == "plan-page"
                    else "is named in the provider's published model list for this plan."
                )
            ),
            trade_off=None,
        ),
        _pick(
            "best_value",
            value,
            spec,
            why=(
                f"On the score-price Pareto frontier, the cheapest plan within "
                f"{spec.value_window:.0f} {unit} of the leader."
            ),
            trade_off=(
                None
                if value.plan_id == quality.plan_id
                else (
                    f"{lead_phrase(quality.score, value.score, unit)}, and"
                    f" ayda ${quality.monthly_usd - value.monthly_usd:.2f} daha ucuz."
                )
            ),
        ),
        _pick(
            "budget_pick",
            cheap,
            spec,
            why=(
                f"Cheapest plan clearing the {spec.min_quality:.0f} {unit} minimum-quality bar."
                if floor_met
                else (
                    f"WARNING: no plan in this budget clears the {spec.min_quality:.0f} {unit} "
                    "minimum-quality bar; this is the cheapest available and you are trading "
                    "quality away."
                )
            ),
            trade_off=(
                None
                if cheap.plan_id == quality.plan_id
                else (
                    f"{lead_phrase(quality.score, cheap.score, unit)},"
                    f" ama ayda ${quality.monthly_usd - cheap.monthly_usd:.2f} daha ucuz."
                )
            ),
        ),
    )
    return SubscriptionRecommendation(
        task=spec.id,
        budget=budget,
        ranking_effort=spec.ranking_effort,
        # W4 review BLOCKING-2: the plan engine ranks on the curated monthly price,
        # so it must NOT claim the per-token pricing feeds it never read.
        sources=attributions_for({r.evidence_source for r in ranking}, priced=False),
        eligible_count=len(rows),
        excluded_by_budget=excluded_by_budget,
        budget_notice=budget_notice,
        frontier_size=len(frontier),
        unscored_plans=unscored,
        equivalent_plans=equivalent,
        equivalence_note=equivalence_note,
        close_call=close_call,
        effort_mix_notice=effort_mix_notice([p.effort for p in picks], spec),
        stale_notice=_stale_notice(conn, ranking),
        picks=picks,
    )
