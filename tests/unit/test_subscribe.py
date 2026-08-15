"""REQ-REC-007/-008: subscription recommender — three plan answers, honesty intact."""

from __future__ import annotations

import json
import sqlite3

import pytest

from app.workflows.ingest import RunContext
from app.workflows.plans import ingest_plans
from app.workflows.recommend import main
from app.workflows.registry import reconcile_plans
from app.workflows.schema import connect
from app.workflows.subscribe import plan_ranking, recommend_subscription

# Registry-matchable names on purpose: Gemini 3.1 Pro -> gemini-3.1-pro,
# Claude 4.5 Opus -> claude-4.5-opus, GPT-5 -> gpt-5. "Mystery Model X" matches nothing.
DOC = """
schema: 1
staleness_days: 30
budget_caps_usd: {dusuk: 10, orta: 25, sinirsiz: null}
plans:
  - id: cheap-plan
    provider: BudgetCo
    name: Cheap Plan
    monthly_usd: 8
    currency: USD
    region: US
    limits: entry tier
    included_models: [GPT-5]
    source_url: https://budgetco.example/pricing
    last_verified: 2026-08-15
  - id: mid-plan
    provider: MidCo
    name: Mid Plan
    monthly_usd: 20
    currency: USD
    region: US
    limits: flagship tier
    included_models: [Gemini 3.1 Pro]
    source_url: https://midco.example/pricing
    last_verified: 2026-08-15
  - id: top-plan
    provider: TopCo
    name: Top Plan
    monthly_usd: 100
    currency: USD
    region: US
    limits: max tier
    included_models: [Claude 4.5 Opus]
    source_url: https://topco.example/pricing
    last_verified: 2026-08-15
  - id: vague-plan
    provider: VagueCo
    name: Vague Plan
    monthly_usd: 15
    currency: USD
    region: US
    limits: frontier models, roster unpublished
    included_models: [Mystery Model X]
    source_url: https://vagueco.example/pricing
    last_verified: 2026-08-15
"""

SCORES = (
    # (model_id, raw_name, score) on SWE-bench Verified
    ("gpt-5", "agent + GPT-5", 70.0),
    ("gemini-3.1-pro", "agent + Gemini 3.1 Pro", 77.4),
    ("claude-4.5-opus", "agent + Claude 4.5 Opus", 79.2),
)


def _db(doc: str = DOC) -> sqlite3.Connection:
    conn = connect()
    ingest_plans(conn, doc, RunContext())
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    return conn


def test_three_labeled_plan_picks_unlimited_budget() -> None:
    rec = recommend_subscription(_db(), budget="sinirsiz", task="coding")
    assert rec is not None
    labels = [p.label for p in rec.picks]
    assert labels == ["best_quality", "best_value", "budget_pick"]
    assert rec.picks[0].plan == "Top Plan"  # 79.2 via Claude 4.5 Opus
    assert rec.picks[0].scored_by_model == "Claude 4.5 Opus"
    # Value: Pareto frontier, within 6.0 of 79.2 → Mid Plan (77.4 @ $20)
    assert rec.picks[1].plan == "Mid Plan"
    assert rec.picks[1].trade_off is not None
    # Budget pick: cheapest meeting floor 65.0 → Cheap Plan (70.0 @ $8)
    assert rec.picks[2].plan == "Cheap Plan"
    assert "kalite şartını geçen en ucuz plan" in rec.picks[2].why


def test_budget_cap_filters_before_scoring() -> None:
    rec = recommend_subscription(_db(), budget="orta", task="coding")
    assert rec is not None
    assert {p.plan for p in rec.picks} <= {"Cheap Plan", "Mid Plan"}  # $100 plan excluded
    assert rec.picks[0].plan == "Mid Plan"
    rec = recommend_subscription(_db(), budget="dusuk", task="coding")
    assert rec is not None
    assert all(p.plan == "Cheap Plan" for p in rec.picks)


def test_unscored_plan_is_disclosed_never_ranked() -> None:
    rec = recommend_subscription(_db(), budget="sinirsiz", task="coding")
    assert rec is not None
    assert rec.unscored_plans == ("Vague Plan",)
    assert all(p.plan != "Vague Plan" for p in rec.picks)


def test_no_rankable_plan_returns_none() -> None:
    conn = connect()
    ingest_plans(conn, DOC, RunContext())
    reconcile_plans(conn)  # no scores inserted → nothing rankable
    assert recommend_subscription(conn, "sinirsiz", "coding") is None


def test_quality_floor_unmet_warns_instead_of_pretending() -> None:
    """The M1-W4 honesty lesson, on the plan axis."""
    conn = _db()
    conn.execute("UPDATE scores SET score = 40.0")  # everyone below the 65.0 floor
    rec = recommend_subscription(conn, "sinirsiz", "coding")
    assert rec is not None
    assert "UYARI" in rec.picks[2].why
    assert "kaliteden ödün veriyorsun" in rec.picks[2].why


def test_stale_plan_rows_disclosed_in_output() -> None:
    """REQ-REC-008: the output names stale rows and their dates."""
    doc = DOC.replace("last_verified: 2026-08-15", "last_verified: 2026-05-01", 1)  # cheap-plan
    conn = connect()
    run = RunContext()
    run.observed_at = "2026-08-15T00:00:00+00:00"
    ingest_plans(conn, doc, run)
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    rec = recommend_subscription(conn, "sinirsiz", "coding")
    assert rec is not None
    assert rec.stale_notice is not None
    assert "Cheap Plan" in rec.stale_notice
    assert "2026-05-01" in rec.stale_notice


def test_close_call_disclosed_on_near_tie() -> None:
    conn = _db()
    conn.execute(
        "UPDATE scores SET score = 78.5 WHERE model_id = 'gemini-3.1-pro'"
    )  # gap 0.7 ≤ 1.5
    rec = recommend_subscription(conn, "sinirsiz", "coding")
    assert rec is not None
    assert rec.close_call is not None
    assert "Mid Plan" in rec.close_call


def test_plan_ranking_orders_by_score_then_price() -> None:
    from app.workflows.categories import CATEGORIES

    ranking = plan_ranking(_db(), CATEGORIES["coding"])
    assert [r.plan_id for r in ranking] == ["top-plan", "mid-plan", "cheap-plan"]
    assert ranking[0].score == 79.2


def test_cli_subscription_through_real_entrypoint(tmp_path, capsys) -> None:
    """V4C-50 + REQ-REC-007: the exact shipped command line."""
    db = tmp_path / "advisor.db"
    conn = connect(str(db))  # real schema + real ingest path below
    ingest_plans(conn, DOC, RunContext())
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    conn.commit()
    conn.close()

    assert main(["--db", str(db), "--budget", "orta", "--task", "coding", "--subscription"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["picks"][0]["plan"] == "Mid Plan"
    assert out["unscored_plans"] == ["Vague Plan"]

    # exit 1: no eligible plan (dusuk excludes everything rankable after price bump)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE plans SET monthly_usd = 500")
    conn.commit()
    conn.close()
    assert main(["--db", str(db), "--budget", "dusuk", "--task", "coding", "--subscription"]) == 1
    assert "no eligible plan" in capsys.readouterr().out

    # exit 2: DB without an ingested plan table config
    empty = tmp_path / "empty.db"
    connect(str(empty)).close()
    assert main(["--db", str(empty), "--budget", "orta", "--subscription"]) == 2


def test_model_path_regression_untouched(tmp_path, capsys) -> None:
    """--subscription is additive: the model CLI behaves exactly as before."""
    empty = tmp_path / "m.db"
    connect(str(empty)).close()
    assert main(["--db", str(empty), "--budget", "sinirsiz", "--task", "coding"]) == 1
    assert "no eligible model" in capsys.readouterr().out


def test_missing_plan_config_fails_with_usage_error() -> None:
    with pytest.raises(ValueError, match="plan_config missing"):
        recommend_subscription(connect(), "orta", "coding")


def test_plan_priced_exactly_at_cap_is_eligible_through_cli(tmp_path, capsys) -> None:
    """W3 review MINOR-1+2: cap boundary is INCLUSIVE (<=) and stale disclosure
    survives the real entrypoint — both asserted through main() (V4C-50)."""
    doc = DOC.replace("monthly_usd: 20", "monthly_usd: 25")  # mid-plan lands ON the orta cap
    doc = doc.replace("last_verified: 2026-08-15", "last_verified: 2026-05-01", 1)  # cheap stale
    db = tmp_path / "advisor.db"
    conn = connect(str(db))
    run = RunContext()
    run.observed_at = "2026-08-15T00:00:00+00:00"
    ingest_plans(conn, doc, run)
    reconcile_plans(conn)
    for model_id, raw, score in SCORES:
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness,"
            " run_date, source, source_url, observed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                model_id,
                raw,
                "SWE-bench Verified",
                "% resolved",
                score,
                "test-agent",
                "2026-08-01",
                "swebench",
                "https://x",
                "2026-08-15T00:00:00+00:00",
            ),
        )
    conn.commit()
    conn.close()
    assert main(["--db", str(db), "--budget", "orta", "--task", "coding", "--subscription"]) == 0
    out = json.loads(capsys.readouterr().out)
    # Boundary: the $25 plan under cap 25 MUST be eligible — and it wins on score.
    assert out["picks"][0]["plan"] == "Mid Plan"
    assert out["picks"][0]["monthly_usd"] == 25
    # REQ-REC-008 through the real entrypoint: the stale row is named with its date.
    assert out["stale_notice"] is not None
    assert "Cheap Plan" in out["stale_notice"]
    assert "2026-05-01" in out["stale_notice"]
