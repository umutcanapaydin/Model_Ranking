"""Category layer + assistant ranking tests — cite REQ-CAT-001/-002/-003, REQ-ING-008."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.fakes import FakeRawSource
from app.workflows.categories import CATEGORIES, get_category
from app.workflows.ingest import (
    RunContext,
    ingest_arena,
    ingest_litellm,
    ingest_swebench,
)
from app.workflows.rank import (
    ATTRIBUTIONS,
    build_price_medians,
    category_ranking,
    coding_ranking,
    export_ranking,
)
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
    }
)
ARENA = json.dumps(
    {
        "rows": [
            {
                "row": {
                    "model_name": "gpt-5-chat",
                    "rating": 1420.5,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
            {
                "row": {
                    "model_name": "claude-4.5-opus",
                    "rating": 1415.2,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
            {
                "row": {
                    "model_name": "gemini-3-flash",
                    "rating": 1380.0,
                    "category": "overall",
                    "leaderboard_publish_date": "2026-08-01",
                }
            },
        ],
        "num_rows_total": 3,
    }
)
SWE = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {"name": "agent + Claude 4.5 Opus", "resolved": 79.2, "date": "2025-12-15"}
                ],
            }
        ]
    }
)


def _db() -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at="2026-08-11T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_arena(conn, FakeRawSource("arena", ARENA), run)
    ingest_swebench(conn, FakeRawSource("swebench", SWE), run)
    reconcile(conn)
    build_price_medians(conn)
    return conn


def test_categories_are_data_not_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-CAT-001: adding a category = adding a map entry, no code branch."""
    assert set(CATEGORIES) == {"coding", "assistant", "agentic-coding"}
    for spec in CATEGORIES.values():
        assert spec.primary_benchmark and spec.metric and spec.primary_source
    assert CATEGORIES["agentic-coding"].ranking_effort == "high"
    with pytest.raises(ValueError, match="unknown task"):
        get_category("photoshop")


def test_assistant_ranking_orders_by_elo() -> None:
    """REQ-CAT-002: assistant category ranks on Arena Elo."""
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    assert [r.model for r in ranking] == ["GPT-5 chat", "Claude 4.5 Opus", "Gemini 3 Flash"]
    assert ranking[0].score == 1420.5
    assert ranking[0].harness == "arena-crowd"


def test_no_cross_scale_averaging_structural() -> None:
    """REQ-CAT-003: a model's assistant score is its Elo, untouched by its SWE %.

    Claude has BOTH an Elo (1415.2) and a SWE % (79.2); if any blending
    happened, the assistant score could not remain exactly the raw Elo.
    """
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    claude = next(r for r in ranking if r.model == "Claude 4.5 Opus")
    assert claude.score == 1415.2  # raw Elo, not blended with 79.2
    coding = coding_ranking(conn)
    assert coding[0].score == 79.2  # raw %, not blended with Elo


def test_coding_regression_lock_via_category_layer() -> None:
    """REQ-REC-005: coding_ranking still works and equals the category-layer call."""
    conn = _db()
    assert coding_ranking(conn) == category_ranking(conn, CATEGORIES["coding"])


def test_export_filenames_derive_from_category(tmp_path: Path) -> None:
    """W3 review: assistant export must not overwrite the coding artifact."""
    conn = _db()
    a_csv, a_json = export_ranking(
        category_ranking(conn, CATEGORIES["assistant"]), tmp_path, [], category="assistant"
    )
    c_csv, c_json = export_ranking(coding_ranking(conn), tmp_path, [], category="coding")
    assert a_json.name == "assistant_ranking.json"
    assert c_json.name == "coding_ranking.json"
    assert a_csv != c_csv


def test_export_carries_attribution(tmp_path: Path) -> None:
    """REQ-ING-008: every JSON export names Arena CC-BY-4.0 + all sources + observed_at."""
    conn = _db()
    ranking = category_ranking(conn, CATEGORIES["assistant"])
    meta: list[dict[str, str | int | None]] = [
        {"source": "arena", "observed_at": "2026-08-11T00:00:00+00:00"}
    ]
    _, json_path = export_ranking(ranking, tmp_path, meta, category="assistant")
    payload = json.loads(json_path.read_text())
    attributions = " ".join(payload["attribution"])
    assert "CC-BY-4.0" in attributions
    assert "lmarena-ai/leaderboard-dataset" in attributions
    assert "OpenRouter" in attributions
    assert tuple(payload["attribution"]) == ATTRIBUTIONS
    assert payload["generated_from"][0]["observed_at"] == "2026-08-11T00:00:00+00:00"
