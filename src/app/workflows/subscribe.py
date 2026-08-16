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

import sqlite3
from dataclasses import dataclass

from app.workflows.categories import CategorySpec, get_category
from app.workflows.plans import stale_plans
from app.workflows.rank import higher_effort_evidence
from app.workflows.recommend import (
    effort_disclosure,
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


@dataclass(frozen=True)
class SubscriptionRecommendation:
    """Deterministic three-plan result (REQ-REC-007)."""

    task: str
    budget: str
    ranking_effort: str | None
    eligible_count: int
    frontier_size: int
    unscored_plans: tuple[str, ...]  # disclosed, never silently dropped
    # Plans that rank IDENTICALLY because their pages name the same model. The
    # three labels then legitimately collapse onto one plan, and the honest answer
    # is not to manufacture variety — it is to say "these are the same engine, buy
    # the cheapest" (M4-W4: measured on live assistant data, three <=$25 plans all
    # scoring 1479.6 via Gemini 3.1 Pro).
    # NOT every collapse is equivalence, and this field must never be read as if it
    # were: on the CODING category the three labels also land on one plan, but for
    # the opposite reason — only one curated plan is scoreable at all (1/10 after this
    # wave adds Google AI Plus; M4-W3 measured 1/9 before it. SWE-bench has published
    # nothing since 2026-02-26, so the denominator grows and the numerator does not).
    # That is a COVERAGE failure,
    # reported by `coverage.plan_coverage`, and it leaves this tuple empty because
    # there is no second plan to be equivalent TO.
    equivalent_plans: tuple[str, ...]
    equivalence_note: str | None
    close_call: str | None
    stale_notice: str | None  # REQ-REC-008
    picks: tuple[PlanPick, ...]


def _budget_cap(conn: sqlite3.Connection, budget: str) -> float | None:
    row = conn.execute("SELECT cap_dusuk, cap_orta FROM plan_config WHERE id = 1").fetchone()
    if row is None:
        msg = "plan_config missing — ingest the curated plan table first"
        raise ValueError(msg)
    caps: dict[str, float | None] = {"dusuk": row[0], "orta": row[1], "sinirsiz": None}
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
            conn, r[8], spec, harness=r[10], source=r[15]
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
                evidence_source=r[15],
                evidence_source_url=r[16],
                evidence_raw_name=r[17],
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


def _stale_notice(conn: sqlite3.Connection) -> str | None:
    """REQ-REC-008: stale plan rows named in the output, with their dates."""
    stale = stale_plans(conn)
    if not stale:
        return None
    listed = ", ".join(f"{s.name} (son doğrulama {s.last_verified})" for s in stale)
    return (
        f"Dikkat: {len(stale)} plan satırının fiyat doğrulaması eskidi — {listed}. "
        "Fiyatlar değişmiş olabilir; tabloyu yeniden doğrulamadan karara güvenme."
    )


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
        harness=row.harness,
        effort=spec.ranking_effort,
        higher_effort=row.higher_effort,
        higher_effort_score=round_optional_score(row.higher_effort_score),
        effort_note=effort_disclosure(
            spec.ranking_effort, row.higher_effort, row.higher_effort_score, spec
        ),
        evidence_date=row.evidence_date,
        last_verified=row.last_verified,
        source_url=row.source_url,
        why=why,
        trade_off=trade_off,
    )


def recommend_subscription(
    conn: sqlite3.Connection, budget: str = "sinirsiz", task: str = "coding"
) -> SubscriptionRecommendation | None:
    """Three plan answers for a task; None when no rankable plan fits the budget."""
    spec = get_category(task)
    cap = _budget_cap(conn, budget)
    ranking = plan_ranking(conn, spec)
    unscored = _unscored(conn, {r.plan_id for r in ranking})
    rows = [r for r in ranking if cap is None or r.monthly_usd <= cap]
    if not rows:
        return None

    frontier = _pareto(rows)
    quality = frontier[0]
    unit = spec.score_unit

    value_pool = [r for r in frontier if quality.score - r.score <= spec.value_window]
    value = min(value_pool, key=lambda r: (r.monthly_usd, r.plan))

    floor_pool = [r for r in rows if r.score >= spec.min_quality]
    floor_met = bool(floor_pool)
    cheap = min(floor_pool or rows, key=lambda r: (r.monthly_usd, r.plan))

    # Equivalence (M4-W4 review BLOCKING-1). The first cut compared only against the
    # QUALITY pick, so in the live `sinirsiz` case — where quality is Perplexity Max and
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
    groups: list[tuple[PlanRank, list[PlanRank]]] = []
    seen_models: set[tuple[str, float]] = set()
    for picked in (quality, value, cheap):
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
            groups.append((picked, tied))

    equivalent = tuple(sorted({r.plan for _, tied in groups for r in tied}))
    equivalence_note: str | None = None
    if groups:
        parts = []
        for picked, tied in groups:
            members = [picked, *tied]
            cheapest = min(members, key=lambda r: (r.monthly_usd, r.plan))
            dearest = max(members, key=lambda r: (r.monthly_usd, r.plan))
            span = (
                f" Aynı model için aylık fark: ${cheapest.monthly_usd:.2f} — "
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
                f" Bunlardan {', '.join(via_roster)} için kaynak, plan sayfası değil"
                " sağlayıcının yayımladığı model listesi."
                if via_roster
                else ""
            )
            parts.append(
                f"{len(members)} plan aynı modele ({picked.scored_by_model}) bağlanıyor, "
                f"yani kalite açısından ayırt edilemezler: "
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
            tie = "aynı puanda" if shown == 0 else f"sadece {shown:.1f} {unit} geride"
            close_call = (
                f"{frontier[1].plan} {tie} — fark hata payı içinde, ikisi de savunulabilir."
            )

    picks = (
        _pick(
            "best_quality",
            quality,
            spec,
            why=(
                f"Bütçeye uyan planlar içinde en yüksek {spec.primary_benchmark} skorlu model"
                f" ({quality.scored_by_model}, {quality.score:.1f} {unit}) "
                + (
                    "bu planın sayfasında açıkça adıyla yer alıyor."
                    if quality.scored_via == "plan-page"
                    else "sağlayıcının yayımladığı plan model listesinde adıyla yer alıyor."
                )
            ),
            trade_off=None,
        ),
        _pick(
            "best_value",
            value,
            spec,
            why=(
                f"Skor-fiyat Pareto sınırında, liderin {spec.value_window:.0f} {unit}"
                " yakınında kalan en ucuz plan."
            ),
            trade_off=(
                None
                if value.plan_id == quality.plan_id
                else (
                    f"{lead_phrase(quality.score, value.score, unit)}, karşılığında"
                    f" ayda ${quality.monthly_usd - value.monthly_usd:.2f} daha ucuz."
                )
            ),
        ),
        _pick(
            "budget_pick",
            cheap,
            spec,
            why=(
                f"Minimum {spec.min_quality:.0f} {unit} kalite şartını geçen en ucuz plan."
                if floor_met
                else (
                    f"UYARI: bu bütçede {spec.min_quality:.0f} {unit} kalite şartını geçen plan"
                    " YOK; bu, mevcutların en ucuzu — kaliteden ödün veriyorsun."
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
        eligible_count=len(rows),
        frontier_size=len(frontier),
        unscored_plans=unscored,
        equivalent_plans=equivalent,
        equivalence_note=equivalence_note,
        close_call=close_call,
        stale_notice=_stale_notice(conn),
        picks=picks,
    )
