"""Ranking + median price + export tests — cite REQ-CAN-003, REQ-RANK-001/-002."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pytest

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_litellm, ingest_swebench
from app.workflows.rank import BLEND_NOTE, build_price_medians, coding_ranking, export_ranking
from app.workflows.registry import reconcile
from app.workflows.schema import connect

PRICING = json.dumps(
    {
        # three providers for gpt-5: median must beat the outlier (REQ-CAN-003)
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "openrouter/gpt-5": {
            "mode": "chat",
            "input_cost_per_token": 1.30e-06,
            "output_cost_per_token": 1.1e-05,
        },
        "cheap-provider/gpt-5": {
            "mode": "chat",
            "input_cost_per_token": 1e-08,
            "output_cost_per_token": 1e-08,
        },
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
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
                    {"name": "worse-agent + GPT-5", "resolved": 60.0, "date": "2025-05-01"},
                ],
            }
        ]
    }
)
AIDER = """
- model: gpt-5
  pass_rate_2: 88.0
  total_cost: 12.5
  date: 2025-08-12
"""


def _pipeline(conn: sqlite3.Connection) -> None:
    from app.workflows.ingest import ingest_aider

    run = RunContext(observed_at="2026-08-10T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SCORES), run)
    ingest_aider(conn, FakeRawSource("aider", AIDER), run)
    reconcile(conn)
    build_price_medians(conn)


def test_median_not_min_beats_outlier() -> None:
    """REQ-CAN-003: an outlier cheap alias must not become the reference price."""
    conn = connect()
    _pipeline(conn)
    in_m, out_m = conn.execute(
        "SELECT in_m, out_m FROM px_median WHERE model_id='gpt-5'"
    ).fetchone()
    assert in_m == 1.25  # median of (0.01, 1.25, 1.30)
    assert out_m == 10.0


def test_ranking_takes_best_score_and_its_harness() -> None:
    """REQ-RANK-001: best score per model wins; its harness travels with it."""
    conn = connect()
    _pipeline(conn)
    ranking = coding_ranking(conn)
    assert [r.model for r in ranking] == ["Claude 4.5 Opus", "GPT-5"]
    gpt5 = ranking[1]
    assert gpt5.score == 74.4
    assert gpt5.harness == "mini-SWE-agent"
    assert gpt5.secondary_score == 88.0
    assert gpt5.secondary_cost == 12.5
    assert gpt5.blended_per_m == round(1.25 * 0.75 + 10.0 * 0.25, 2)


def test_model_without_price_is_excluded() -> None:
    """REQ-RANK-001: a model with a score but NO price must not appear (real seed)."""
    conn = connect()
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [{"name": "TRAE + Doubao-Seed-Code", "resolved": 78.8}],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    build_price_medians(conn)
    # the score-only model IS in the registry…
    assert conn.execute("SELECT id FROM models WHERE id='doubao-seed-code'").fetchone()
    # …but has no price, so it must not rank
    assert coding_ranking(conn) == []


def test_tied_best_scores_pick_deterministically() -> None:
    """W3 review MINOR-3: ties resolve by newest run_date, then harness name."""
    conn = connect()
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "zeta-agent + GPT-5", "resolved": 74.4, "date": "2025-01-01"},
                        {"name": "alpha-agent + GPT-5", "resolved": 74.4, "date": "2025-09-01"},
                    ],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)
    reconcile(conn)
    build_price_medians(conn)
    (row,) = coding_ranking(conn)
    assert row.harness == "alpha-agent"  # newest date wins regardless of insert order
    assert row.evidence_date == "2025-09-01"


def test_even_count_median_is_middle_mean() -> None:
    """REQ-CAN-003 edge: two provider prices → median is their mean."""
    conn = connect()
    pricing = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1e-06,
                "output_cost_per_token": 2e-06,
            },
            "azure/gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 2e-06,
                "output_cost_per_token": 4e-06,
            },
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    reconcile(conn)
    build_price_medians(conn)
    in_m, out_m = conn.execute(
        "SELECT in_m, out_m FROM px_median WHERE model_id='gpt-5'"
    ).fetchone()
    assert in_m == 1.5
    assert out_m == 3.0


def test_median_of_per_source_medians_beats_outlier_source() -> None:
    """REQ-ING-006 (M2): a source with MANY cheap aliases must not outweigh another source."""
    from app.workflows.ingest import ingest_openrouter

    conn = connect()
    run = RunContext(observed_at="t")
    # litellm: ONE fair price
    ingest_litellm(
        conn,
        FakeRawSource(
            "litellm",
            json.dumps(
                {
                    "gpt-5": {
                        "mode": "chat",
                        "input_cost_per_token": 1.25e-06,
                        "output_cost_per_token": 1e-05,
                    }
                }
            ),
        ),
        run,
    )
    # openrouter: THREE dirt-cheap aliases of the same model
    cheap = {"prompt": "0.00000001", "completion": "0.00000001"}
    ingest_openrouter(
        conn,
        FakeRawSource(
            "openrouter",
            json.dumps(
                {
                    "data": [
                        {"id": "a/gpt-5", "pricing": cheap},
                        {"id": "b/gpt-5", "pricing": cheap},
                        {"id": "c/gpt-5", "pricing": cheap},
                    ]
                }
            ),
        ),
        run,
    )
    reconcile(conn)
    build_price_medians(conn)
    in_m, _ = conn.execute("SELECT in_m, out_m FROM px_median WHERE model_id='gpt-5'").fetchone()
    # per-source medians: litellm=1.25, openrouter=0.01 → cross-source median = 0.63 (mean of two)
    # under the OLD flat median the three cheap rows would win outright (0.01)
    assert in_m == pytest.approx((1.25 + 0.01) / 2, abs=0.01)
    assert in_m > 0.5, "outlier source must not dominate the reference price"


def test_export_empty_ranking_does_not_crash(tmp_path: Path) -> None:
    """REQ-RANK-002 edge: empty ranking → header-only CSV + empty JSON rows."""
    csv_path, json_path = export_ranking([], tmp_path, [])
    assert csv_path.read_text().strip().startswith("model,")
    assert json.loads(json_path.read_text())["rows"] == []


def test_export_csv_and_json_identical_rows(tmp_path: Path) -> None:
    """REQ-RANK-002: one command → CSV + JSON with identical rows + metadata."""
    conn = connect()
    _pipeline(conn)
    ranking = coding_ranking(conn)
    meta: list[dict[str, str | int | None]] = [
        {"source": "litellm", "observed_at": "2026-08-10T00:00:00+00:00"}
    ]
    csv_path, json_path = export_ranking(ranking, tmp_path, meta)

    with csv_path.open() as f:
        csv_rows = list(csv.DictReader(f))
    payload = json.loads(json_path.read_text())
    assert payload["note"] == BLEND_NOTE
    assert payload["generated_from"] == meta
    assert len(csv_rows) == len(payload["rows"]) == len(ranking)
    for c, j in zip(csv_rows, payload["rows"], strict=True):
        assert c["model"] == j["model"]
        assert float(c["blended_per_m"]) == j["blended_per_m"]
