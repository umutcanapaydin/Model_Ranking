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
    ARENA_ATTRIBUTION,
    PRICING_ATTRIBUTION,
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
    assert set(CATEGORIES) == {
        "coding",
        "assistant",
        "agentic-coding",
        "everyday",
        "expert",
        "mathematics",
        "computer-use",
        "abstract",
        "web-dev",
    }
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
    # W4 review BLOCKING-2: an export cites the sources IT carries. This ranking is
    # Arena-only, so claiming SWE-bench/Aider/Epoch here would be a false provenance
    # claim — the exact defect the static catalogue produced in every payload.
    assert "Epoch AI" not in attributions
    assert "swebench.com" not in attributions
    assert tuple(payload["attribution"]) == (ARENA_ATTRIBUTION, PRICING_ATTRIBUTION)
    assert payload["generated_from"][0]["observed_at"] == "2026-08-11T00:00:00+00:00"


# --- M8: the six categories added when the scope widened to all AI tools (D-126/D-127) ---------


def test_no_category_can_exclude_a_model_it_calls_level_with_the_leader() -> None:
    """The invariant the M8 calibration was rebuilt on: `value_window` >= `close_call`.

    `close_call` is a MEASURED fact about the benchmark -- two scores inside it are
    indistinguishable at the board's own precision, and the surface says so. `value_window` is
    the reach of the Best Value pick. If a window were narrower than the close-call threshold,
    the product would disclose "level with the leader" about a model and in the same breath
    refuse to consider it -- ranking noise as if it were quality, which is the one thing this
    engine exists not to do.

    It can fail: `expert` was drafted at window 8.0 against close_call 5.0 and passed; the
    original `mathematics` draft (window 15.0, close 9.5) passed too. Narrow either below its
    close_call and this goes red.
    """
    for name, spec in CATEGORIES.items():
        assert spec.value_window >= spec.close_call, (
            f"{name}: value_window {spec.value_window} is narrower than close_call "
            f"{spec.close_call}; models the surface calls indistinguishable from the leader "
            "would be excluded from the value pick"
        )


def test_every_source_the_build_ingests_can_be_attributed() -> None:
    """A source whose evidence cannot be credited must never reach a user (REQ-ING-008).

    This gates a defect that has already happened: wiring the Epoch boards raised
    `ValueError: unattributed evidence source 'epoch_mmlu'` at BUILD time, after the categories
    were written and the ingestion had run. The rule existed and its gate did not, so the only
    thing that caught it was running the pipeline by hand.

    The referent is the SOURCE REGISTRY, not the category map -- deliberately, because the first
    version of this test asked only about each category's `primary_source` and a mutant that
    deleted `epoch_mmlu`'s attribution walked straight through it. `epoch_mmlu` is nobody's
    primary source; it is served as EVIDENCE, which is precisely the population the control
    covers and the test did not. A test narrower than the rule it cites is not a gate.
    """
    from app.workflows.rank import SOURCE_ATTRIBUTION
    from app.workflows.sources import EPOCH_BOARDS, LOCAL_BUNDLES, REMOTE_SOURCES

    ingested = (
        {s.name for s in REMOTE_SOURCES if s.writes_scores}
        | {b.name for b in LOCAL_BUNDLES}
        | {b.source_name for b in EPOCH_BOARDS}
    )
    unattributed = sorted(ingested - set(SOURCE_ATTRIBUTION))
    assert not unattributed, (
        f"the build ingests {unattributed} with no SOURCE_ATTRIBUTION entry; serving a pick "
        "whose evidence comes from one of these raises at request time"
    )


def test_every_category_is_reachable_by_the_name_the_api_accepts() -> None:
    """A category in the map that `get_category` cannot resolve is a category nobody can query."""
    for name, spec in CATEGORIES.items():
        assert get_category(name) is spec
        assert spec.id == name, f"{name} carries id {spec.id!r}; the API would route on the key"
