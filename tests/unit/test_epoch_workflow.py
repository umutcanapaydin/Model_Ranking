"""Epoch workflow wiring tests — cite REQ-ING-010 and REQ-ING-004."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import pytest

from app.clients.epoch import EPOCH_BUNDLE_URL, EPOCH_SWE_BENCH_FILE, SOURCE_NAME, EpochClient
from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.workflows.categories import CATEGORIES
from app.workflows.coverage import plan_evidence_health
from app.workflows.ingest import RunContext, ingest_epoch, ingest_swebench
from app.workflows.plans import ingest_plans
from app.workflows.registry import reconcile, reconcile_plans
from app.workflows.rosters import ingest_rosters
from app.workflows.schema import connect

EPOCH_URL = f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}"
EPOCH_CSV = """Model version,mean_score,Started at,id
glm-5.2_max,0.787,2026-06-25T13:13:06.902Z,glm-run
gemini-3.1-pro-preview-customtools,0.756,2026-02-24T13:34:48.126Z,gemini-run
"""


def _epoch() -> FakeRawSource:
    return FakeRawSource(
        SOURCE_NAME,
        EPOCH_CSV,
        url=EPOCH_URL,
        last_verified="2026-08-15",
    )


def test_epoch_ingest_is_wired_with_independent_provenance() -> None:
    """REQ-ING-010: the live workflow stores Epoch as an attributable score source."""
    conn = connect()
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")

    report = ingest_epoch(conn, _epoch(), run)

    assert (report.source, report.stored, report.skipped, report.last_verified) == (
        SOURCE_NAME,
        2,
        0,
        "2026-08-15",
    )
    stored = conn.execute(
        "SELECT raw_name, score, harness, run_date, source_url, observed_at"
        " FROM scores WHERE source = ? ORDER BY raw_name",
        (SOURCE_NAME,),
    ).fetchall()
    assert stored == [
        (
            "gemini-3.1-pro-preview-customtools",
            75.6,
            "inspect_ai",
            "2026-02-24",
            EPOCH_URL,
            run.observed_at,
        ),
        (
            "glm-5.2_max",
            78.7,
            "inspect_ai",
            "2026-06-25",
            EPOCH_URL,
            run.observed_at,
        ),
    ]


def test_epoch_rerun_replaces_only_its_board_and_registry_resolves_live_names() -> None:
    """REQ-ING-004/-010: source replacement is isolated; live names reconcile."""
    conn = connect()
    swebench = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {
                            "name": "other-agent + Gemini 3.1 Pro",
                            "resolved": 60.0,
                            "date": "2026-02-26",
                        }
                    ],
                }
            ]
        }
    )
    ingest_swebench(
        conn,
        FakeRawSource("swebench", swebench),
        RunContext(observed_at="swebench-stamp"),
    )
    ingest_epoch(conn, _epoch(), RunContext(observed_at="epoch-old"))
    report = ingest_epoch(conn, _epoch(), RunContext(observed_at="epoch-new"))
    reconciliation = reconcile(conn)

    assert report.stored == 2
    assert conn.execute("SELECT COUNT(*) FROM scores WHERE source = 'swebench'").fetchone() == (1,)
    assert conn.execute(
        "SELECT DISTINCT observed_at FROM scores WHERE source = ?", (SOURCE_NAME,)
    ).fetchall() == [("epoch-new",)]
    assert reconciliation.scores_matched == 3
    resolved = dict(
        conn.execute("SELECT raw_name, model_id FROM scores WHERE source = ?", (SOURCE_NAME,))
    )
    assert resolved == {
        "glm-5.2_max": "glm-5.2",
        "gemini-3.1-pro-preview-customtools": "gemini-3.1-pro",
    }


def test_epoch_workflow_refuses_to_drop_its_verification_clock() -> None:
    """REQ-ING-010: the production ingest report must carry Epoch's own clock."""
    source = FakeRawSource(SOURCE_NAME, EPOCH_CSV, url=EPOCH_URL)

    with pytest.raises(SourceError, match="last_verified is mandatory"):
        ingest_epoch(connect(), source, RunContext(observed_at="2026-08-16T00:00:00+00:00"))


def test_real_epoch_board_reproduces_plan_level_freshness_distribution() -> None:
    """REQ-ING-011b/REQ-SUB-007: real engine selects 2 fresh, 3 stale, 5 unscored."""
    raw_dir = os.environ.get("EPOCH_DATA_DIR")
    if raw_dir is None:
        pytest.skip("set EPOCH_DATA_DIR to the unpacked owner-fetched Epoch bundle")

    root = Path(__file__).resolve().parents[2]
    conn = connect()
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")
    ingest_plans(conn, (root / "data/plans.yaml").read_text(encoding="utf-8"), run)
    ingest_rosters(conn, (root / "data/rosters.yaml").read_text(encoding="utf-8"), run)
    client = EpochClient(raw_dir, last_verified="2026-08-15")
    ingest_epoch(conn, client, run)
    reconcile_plans(conn)
    reconcile(conn)

    health = plan_evidence_health(conn, CATEGORIES["coding"], today=dt.date(2026, 8, 16))
    assert (health.fresh, health.stale, health.undated, health.unscored) == (2, 3, 0, 5)
    by_name = {row.plan: row for row in health.plans}
    assert {
        name: (by_name[name].status, by_name[name].selected_model, by_name[name].evidence_date)
        for name in ("Perplexity Pro", "Perplexity Max")
    } == {
        "Perplexity Pro": ("fresh", "GLM-5.2", "2026-06-25"),
        "Perplexity Max": ("fresh", "GLM-5.2", "2026-06-25"),
    }
    assert {
        by_name[name].status for name in ("Google AI Plus", "Google AI Pro", "Google AI Ultra")
    } == {"stale"}
    assert {
        by_name[name].evidence_date
        for name in ("Google AI Plus", "Google AI Pro", "Google AI Ultra")
    } == {"2026-02-24"}
