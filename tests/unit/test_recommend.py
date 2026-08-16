"""Recommendation engine tests — cite REQ-REC-001..004."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.epoch import EPOCH_ATTRIBUTION
from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_aider, ingest_litellm, ingest_swebench
from app.workflows.recommend import (
    BUDGETS,
    CLOSE_CALL_PTS,
    MIN_QUALITY_PCT,
    VALUE_WINDOW_PTS,
    eligible_rows,
    pareto_frontier,
    recommend,
)
from app.workflows.registry import reconcile
from app.workflows.schema import connect

PRICING = json.dumps(
    {
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "deepseek-v3.2": {
            "mode": "chat",
            "input_cost_per_token": 2.8e-07,
            "output_cost_per_token": 4.1e-07,
        },
        "gemini-3-flash": {
            "mode": "chat",
            "input_cost_per_token": 5e-07,
            "output_cost_per_token": 3e-06,
        },
        "gpt-5-nano": {
            "mode": "chat",
            "input_cost_per_token": 5e-08,
            "output_cost_per_token": 4e-07,
        },
    }
)
SCORES = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {
                        "name": "live-SWE-agent + Claude 4.5 Opus",
                        "resolved": 79.2,
                        "date": "2025-12-15",
                    },
                    {"name": "mini-SWE-agent + GPT-5", "resolved": 74.4, "date": "2025-09-01"},
                    {
                        "name": "mini-SWE-agent + DeepSeek V3.2",
                        "resolved": 70.0,
                        "date": "2026-02-17",
                    },
                    {
                        "name": "mini-SWE-agent + Gemini 3 Flash",
                        "resolved": 75.8,
                        "date": "2026-02-17",
                    },
                    {"name": "mini-SWE-agent + GPT-5 nano", "resolved": 40.0, "date": "2025-09-01"},
                ],
            }
        ]
    }
)
AIDER = """
- model: deepseek-v3.2
  pass_rate_2: 74.2
  total_cost: 3.5
  date: 2026-02-17
"""


def _db() -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SCORES), run)
    ingest_aider(conn, FakeRawSource("aider", AIDER), run)
    reconcile(conn)
    return conn


def test_three_labeled_deterministic_picks() -> None:
    """REQ-REC-001: exactly three labeled picks; every field populated; deterministic."""
    conn = _db()
    rec1 = recommend(conn, "sinirsiz")
    rec2 = recommend(conn, "sinirsiz")
    assert rec1 is not None
    assert rec1 == rec2  # same state + inputs → same picks
    assert [p.label for p in rec1.picks] == ["best_quality", "best_value", "budget_pick"]
    for p in rec1.picks:
        assert p.model and p.vendor and p.why and p.confidence in ("High", "Medium")
        assert p.harness
    assert rec1.picks[0].model == "Claude 4.5 Opus"


def test_req_lic_001_epoch_citation_is_in_model_recommendation_and_readme() -> None:
    """REQ-LIC-001: the licensed citation ships where recommendation data is served."""
    rec = recommend(_db(), "sinirsiz")
    assert rec is not None
    assert EPOCH_ATTRIBUTION in rec.sources
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    assert EPOCH_ATTRIBUTION.removesuffix(" (CC BY 4.0 / CC-BY-4.0)") in readme


def test_budget_filter_is_hard_constraint() -> None:
    """REQ-REC-002: low budget → no pick may exceed the threshold; constants tested."""
    conn = _db()
    assert BUDGETS["dusuk"] == 2.0
    assert BUDGETS["orta"] == 8.0
    assert BUDGETS["sinirsiz"] is None
    rec = recommend(conn, "dusuk")
    assert rec is not None
    for p in rec.picks:
        assert p.blended_per_m <= 2.0, f"{p.model} exceeds the low-budget cap"
    # the expensive leader must be gone
    assert all(p.model != "Claude 4.5 Opus" for p in rec.picks)


def test_no_eligible_model_returns_none() -> None:
    """REQ-REC-002 edge: an impossible budget yields None, not a bad answer."""
    conn = connect()  # empty db
    assert recommend(conn, "dusuk") is None


def test_pareto_non_dominance() -> None:
    """REQ-REC-003: no recommended model is worse AND more expensive than another."""
    conn = _db()
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    ranking = eligible_rows(
        __import__("app.workflows.rank", fromlist=["coding_ranking"]).coding_ranking(conn),
        "sinirsiz",
    )
    for p in rec.picks:
        dominated = any(o.score > p.score and o.blended_per_m < p.blended_per_m for o in ranking)
        assert not dominated, f"{p.model} is dominated"


def test_frontier_excludes_dominated_models() -> None:
    """REQ-REC-003: GPT-5 (74.4, $3.44) is dominated by Gemini 3 Flash (75.8, $1.12)."""
    conn = _db()
    from app.workflows.rank import build_price_medians, coding_ranking

    build_price_medians(conn)
    frontier = pareto_frontier(coding_ranking(conn))
    names = [r.model for r in frontier]
    assert "GPT-5" not in names
    assert "Gemini 3 Flash" in names


def test_value_pick_rule_within_window_cheapest() -> None:
    """REQ-REC-003: value = within VALUE_WINDOW_PTS of leader, cheapest on frontier."""
    assert VALUE_WINDOW_PTS == 6.0
    conn = _db()
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    value = rec.picks[1]
    # leader 79.2; window ≥73.2 → Gemini 3 Flash (75.8, $1.12) beats Claude ($11.25)
    assert value.model == "Gemini 3 Flash"
    assert value.trade_off is not None


def test_budget_pick_respects_min_quality() -> None:
    """REQ-REC-001/002: budget pick = cheapest ≥ MIN_QUALITY_PCT (nano at 40% excluded)."""
    assert MIN_QUALITY_PCT == 65.0
    conn = _db()
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    cheap = rec.picks[2]
    assert cheap.model == "DeepSeek V3.2"  # cheapest above 65%; nano (40%) ineligible
    assert cheap.score >= 65.0


def test_confidence_grades_by_source_count() -> None:
    """REQ-REC-004: DeepSeek has SWE+Aider → High; single-source models → Medium."""
    conn = _db()
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    by_label = {p.label: p for p in rec.picks}
    assert by_label["budget_pick"].confidence == "High"
    assert by_label["best_quality"].confidence == "Medium"


def test_close_call_is_disclosed() -> None:
    """REQ-REC-004: a near-tie at the top is stated, not hidden."""
    assert CLOSE_CALL_PTS == 1.5
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1e-06,
                "output_cost_per_token": 4e-06,
            },
            "gemini-3-flash": {
                "mode": "chat",
                "input_cost_per_token": 5e-07,
                "output_cost_per_token": 3e-06,
            },
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "a + GPT-5", "resolved": 75.8, "date": "2025-09-01"},
                        {"name": "b + Gemini 3 Flash", "resolved": 75.8, "date": "2026-02-17"},
                    ],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    assert rec.close_call is not None
    assert "aynı puanda" in rec.close_call


def test_budget_pick_warns_when_quality_floor_unmet() -> None:
    """W4 review BLOCKING-1 regression: below-floor fallback must SAY so, never lie."""
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5-nano": {
                "mode": "chat",
                "input_cost_per_token": 5e-08,
                "output_cost_per_token": 4e-07,
            }
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [{"name": "mini-SWE-agent + GPT-5 nano", "resolved": 40.0}],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    rec = recommend(conn, "dusuk")
    assert rec is not None
    cheap = rec.picks[2]
    assert cheap.score < MIN_QUALITY_PCT
    assert "UYARI" in cheap.why  # honest disclosure, not the standard floor text
    assert "geçen en ucuz model." not in cheap.why


def test_budget_filters_nonempty_ranking_to_none() -> None:
    """REQ-REC-002: models EXIST but none fits the budget → None (not empty-db artifact)."""
    conn = connect()
    pricing = json.dumps(
        {
            "claude-4-5-opus": {
                "mode": "chat",
                "input_cost_per_token": 5e-06,
                "output_cost_per_token": 2.5e-05,
            }
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [{"name": "live-SWE-agent + Claude 4.5 Opus", "resolved": 79.2}],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    assert recommend(conn, "sinirsiz") is not None  # sanity: it ranks
    assert recommend(conn, "dusuk") is None  # $11.25 blended > $2 cap


def test_unknown_budget_raises() -> None:
    with pytest.raises(ValueError, match="unknown budget"):
        recommend(connect(), "yok-boyle-butce")


def test_secondary_score_rounds_and_absence_stays_absent(tmp_path, capsys) -> None:
    """W4 review MINOR-2 citing test: `round_optional_score` through the real CLI.

    REQ-REC-010 rounds the JSON contract, but the secondary (evidence-only) score is
    nullable — and the one thing a rounding helper must never do to a missing number is
    turn it into 0.0. Both halves are asserted in the same output: DeepSeek carries an
    Aider score with junk precision, the leader carries none.
    """
    from app.workflows.recommend import main

    conn = _db()
    conn.execute(
        "UPDATE scores SET score = 74.24444444 WHERE model_id = 'deepseek-v3.2'"
        " AND benchmark = 'Aider polyglot'"
    )
    conn.commit()
    db = tmp_path / "advisor.db"
    dest = sqlite3.connect(db)
    conn.backup(dest)
    dest.commit()
    dest.close()

    assert main(["--db", str(db), "--budget", "sinirsiz"]) == 0
    picks = {p["model"]: p for p in json.loads(capsys.readouterr().out)["picks"]}
    assert picks["DeepSeek V3.2"]["secondary_score"] == 74.2  # rounded, not raw
    assert picks["Claude 4.5 Opus"]["secondary_score"] is None  # absent, not 0.0


def test_model_engine_trade_off_never_claims_a_gap_the_fields_deny() -> None:
    """W4 re-review BLOCKING-A, model-engine half: same guard, second call site.

    `lead_phrase` is shared with the subscription engine, so the helper itself is
    defended there; this test pins the four CALL SITES in this module — inlining the raw
    delta back into any trade-off string reintroduces "0.1 points lower" between two
    picks the JSON both prints as 79.2.
    """
    conn = _db()
    conn.execute("UPDATE scores SET score = 79.249 WHERE model_id = 'claude-4.5-opus'")
    conn.execute("UPDATE scores SET score = 79.151 WHERE model_id = 'gemini-3-flash'")
    rec = recommend(conn, "sinirsiz")
    assert rec is not None
    assert rec.picks[0].score == rec.picks[1].score == 79.2
    assert rec.close_call is not None
    assert "aynı puanda" in rec.close_call
    trade_off = rec.picks[1].trade_off
    assert trade_off is not None
    assert trade_off.startswith("Liderle aynı puanda,")
    assert "Liderden" not in trade_off
