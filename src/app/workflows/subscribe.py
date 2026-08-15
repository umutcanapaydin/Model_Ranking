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
    harness: str
    evidence_date: str | None


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
    harness: str
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
    eligible_count: int
    frontier_size: int
    unscored_plans: tuple[str, ...]  # disclosed, never silently dropped
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
          WHERE s.benchmark = :primary AND pm.model_id IS NOT NULL
          GROUP BY pm.plan_id
        ),
        detail AS (
          SELECT pm.plan_id, m.display, s.harness, s.run_date, s.score,
                 ROW_NUMBER() OVER (
                   PARTITION BY pm.plan_id
                   ORDER BY s.run_date DESC, s.harness ASC, m.display ASC
                 ) AS rn
          FROM plan_models pm
          JOIN scores s ON s.model_id = pm.model_id
          JOIN models m ON m.id = pm.model_id
          JOIN plan_best b ON b.plan_id = pm.plan_id AND b.best = s.score
          WHERE s.benchmark = :primary
        )
        SELECT p.id, p.name, p.provider, p.monthly_usd, p.currency,
               p.last_verified, p.source_url, b.best,
               (SELECT display  FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT harness  FROM detail d WHERE d.plan_id = p.id AND d.rn = 1),
               (SELECT run_date FROM detail d WHERE d.plan_id = p.id AND d.rn = 1)
        FROM plans p
        JOIN plan_best b ON b.plan_id = p.id
        ORDER BY b.best DESC, p.monthly_usd ASC, p.id
        """,
        {"primary": spec.primary_benchmark},
    ).fetchall()
    return [
        PlanRank(
            plan_id=r[0],
            plan=r[1],
            provider=r[2],
            monthly_usd=r[3],
            currency=r[4],
            last_verified=r[5],
            source_url=r[6],
            score=r[7],
            scored_by_model=r[8],
            harness=r[9],
            evidence_date=r[10],
        )
        for r in rows
    ]


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
        score=row.score,
        metric=spec.metric,
        scored_by_model=row.scored_by_model,
        harness=row.harness,
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

    close_call: str | None = None
    if len(frontier) > 1:
        gap = quality.score - frontier[1].score
        if gap <= spec.close_call:
            tie = "aynı puanda" if gap == 0 else f"sadece {gap:.1f} {unit} geride"
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
                f" ({quality.scored_by_model}, {quality.score:.1f} {unit}) bu planın sayfasında"
                " açıkça adıyla yer alıyor."
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
                    f"Liderden {quality.score - value.score:.1f} {unit} düşük, karşılığında"
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
                    f"Liderden {quality.score - cheap.score:.1f} {unit} düşük,"
                    f" ama ayda ${quality.monthly_usd - cheap.monthly_usd:.2f} daha ucuz."
                )
            ),
        ),
    )
    return SubscriptionRecommendation(
        task=spec.id,
        budget=budget,
        eligible_count=len(rows),
        frontier_size=len(frontier),
        unscored_plans=unscored,
        close_call=close_call,
        stale_notice=_stale_notice(conn),
        picks=picks,
    )
