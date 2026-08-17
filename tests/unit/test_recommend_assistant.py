"""Task-aware recommendation tests — cite REQ-REC-005 and REQ-REC-006."""

from __future__ import annotations

import json
import sqlite3

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_arena, ingest_litellm
from app.workflows.rank import build_price_medians
from app.workflows.recommend import MIN_QUALITY_ELO, VALUE_WINDOW_ELO, recommend
from app.workflows.registry import reconcile
from app.workflows.schema import connect

PRICING = json.dumps(
    {
        "gpt-5-chat": {
            "mode": "chat",
            "input_cost_per_token": 1.25e-06,
            "output_cost_per_token": 1e-05,
        },
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "gemini-3-flash": {
            "mode": "chat",
            "input_cost_per_token": 5e-07,
            "output_cost_per_token": 3e-06,
        },
        "kimi-k2": {
            "mode": "chat",
            "input_cost_per_token": 5e-07,
            "output_cost_per_token": 1.2e-06,
        },
    }
)


def _arena(
    rows: list[dict[str, object]], observed: str = "2026-08-11T00:00:00+00:00"
) -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at=observed)
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    payload = json.dumps({"rows": [{"row": r} for r in rows], "num_rows_total": len(rows)})
    ingest_arena(conn, FakeRawSource("arena", payload), run)
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    return conn


FRESH = "2026-08-01"
ROWS = [
    {
        "model_name": "gpt-5-chat",
        "rating": 1420.5,
        "category": "overall",
        "leaderboard_publish_date": FRESH,
    },
    {
        "model_name": "claude-4.5-opus",
        "rating": 1415.2,
        "category": "overall",
        "leaderboard_publish_date": FRESH,
    },
    {
        "model_name": "gemini-3-flash",
        "rating": 1398.0,
        "category": "overall",
        "leaderboard_publish_date": FRESH,
    },
    {
        "model_name": "kimi-k2",
        "rating": 1250.0,
        "category": "overall",
        "leaderboard_publish_date": FRESH,
    },
]


def test_assistant_task_three_picks_on_elo_scale() -> None:
    """REQ-REC-005: --task assistant yields three picks scored in Elo, wording in Elo."""
    conn = _arena(ROWS)
    rec = recommend(conn, "unlimited", "assistant")
    assert rec is not None
    assert rec.task == "assistant"
    assert [p.label for p in rec.picks] == ["best_quality", "best_value", "budget_pick"]
    quality = rec.picks[0]
    assert quality.model == "GPT-5 chat"
    assert quality.metric == "elo"
    assert "Elo" in rec.picks[1].why  # trade-off wording on the native scale


def test_assistant_value_window_uses_elo_threshold() -> None:
    """REQ-REC-005: Elo window (30) picks the cheapest within reach of the leader."""
    assert VALUE_WINDOW_ELO == 30.0
    conn = _arena(ROWS)
    rec = recommend(conn, "unlimited", "assistant")
    assert rec is not None
    # window: 1420.5-30 = 1390.5 → gemini (1398, $1.13) is in; kimi (1250) is out
    assert rec.picks[1].model == "Gemini 3 Flash"


def test_assistant_budget_floor_uses_elo() -> None:
    """REQ-REC-005 + REQ-CAL-001: Elo floor, recalibrated to 1400 against the live board
    (kimi 1250 and gemini 1398 are both below it; only the 1415.2 model clears)."""
    assert MIN_QUALITY_ELO == 1400.0
    conn = _arena(ROWS)
    rec = recommend(conn, "unlimited", "assistant")
    assert rec is not None
    assert rec.picks[2].score >= MIN_QUALITY_ELO


def test_coding_task_unchanged_regression() -> None:
    """REQ-REC-005: default task stays coding; empty coding data → None (unchanged)."""
    conn = _arena(ROWS)  # arena data only — no coding scores
    assert recommend(conn, "unlimited") is None  # coding default finds nothing
    assert recommend(conn, "unlimited", "assistant") is not None


def test_assistant_close_call_wording_in_elo() -> None:
    """W4 review: nonzero near-tie wording carries the Elo unit."""
    # runner-up must sit ON the frontier (cheaper than the leader) to be disclosed
    rows = [
        {
            "model_name": "gpt-5-chat",
            "rating": 1420.5,
            "category": "overall",
            "leaderboard_publish_date": FRESH,
        },
        {
            "model_name": "gemini-3-flash",
            "rating": 1417.0,
            "category": "overall",
            "leaderboard_publish_date": FRESH,
        },
    ]
    conn = _arena(rows)
    rec = recommend(conn, "unlimited", "assistant")
    assert rec is not None
    assert rec.close_call is not None
    assert "is only 3.5 Elo behind" in rec.close_call


def test_stale_primary_source_is_disclosed() -> None:
    """REQ-REC-006: old Arena snapshot → stale_notice present; fresh → None."""
    old_rows = [dict(r, leaderboard_publish_date="2025-01-01") for r in ROWS]
    conn = _arena(old_rows, observed="2026-08-11T00:00:00+00:00")
    rec = recommend(conn, "unlimited", "assistant")
    assert rec is not None
    assert rec.stale_notice is not None
    assert "days old" in rec.stale_notice

    fresh_conn = _arena(ROWS, observed="2026-08-11T00:00:00+00:00")
    fresh_rec = recommend(fresh_conn, "unlimited", "assistant")
    assert fresh_rec is not None
    assert fresh_rec.stale_notice is None


def test_close_call_threshold_is_the_calibrated_elo_value() -> None:
    """REQ-CAL-001 citing test: close_call=8 must be DEFENDED, not merely written.

    The M3 closure review injected 8→5 and the whole suite stayed green — a
    stay-green fault, so this test is mandatory (V3C-72). The gap below (6.5 Elo)
    sits INSIDE the calibrated window and OUTSIDE the old one: disclosure here
    proves the shipped value is the calibrated one.
    """
    from app.workflows.categories import CATEGORIES
    from app.workflows.recommend import CLOSE_CALL_ELO

    assert CLOSE_CALL_ELO == 8.0
    rows = [
        {**ROWS[0], "rating": 1420.5},  # leader (gpt-5-chat)
        # Runner-up 6.5 Elo behind AND cheaper, so it sits on the Pareto frontier
        # (close_call only inspects the frontier — documented design choice):
        # a tie under the calibrated 8, no tie under the old 5.
        {**ROWS[2], "rating": 1414.0},
        ROWS[3],
    ]
    rec = recommend(_arena(rows), "unlimited", "assistant")
    assert rec is not None
    assert rec.close_call is not None, "a 6.5-Elo gap must be disclosed under the calibrated 8"
    assert "Elo" in rec.close_call
    # The aliases in recommend.py are documentation of the shipped data — drift is a defect.
    spec = CATEGORIES["assistant"]
    assert (spec.min_quality, spec.value_window, spec.close_call) == (
        MIN_QUALITY_ELO,
        VALUE_WINDOW_ELO,
        CLOSE_CALL_ELO,
    )


def test_assistant_quality_floor_unmet_warns_on_elo_scale() -> None:
    """REQ-CAL-001 side effect (closure review NOTE-7): the recalibrated 1400 floor
    makes the honesty branch reachable on the Elo scale — it must SAY so."""
    rec = recommend(_arena(ROWS), "low", "assistant")
    assert rec is not None
    assert "WARNING" in rec.picks[2].why
    assert rec.picks[2].score < MIN_QUALITY_ELO


def test_elo_scores_are_rounded_in_the_output(tmp_path, capsys) -> None:
    """REQ-REC-010 through the real CLI: no raw float reaches the JSON contract."""
    import json as _json
    import sqlite3

    from app.workflows.recommend import main

    db = tmp_path / "advisor.db"
    src = _arena([{**ROWS[0], "rating": 1481.5937567329202}, ROWS[3]])
    dest = sqlite3.connect(db)
    src.commit()
    src.backup(dest)
    dest.commit()
    dest.close()
    assert main(["--db", str(db), "--budget", "unlimited", "--task", "assistant"]) == 0
    out = _json.loads(capsys.readouterr().out)
    assert out["picks"][0]["score"] == 1481.6
