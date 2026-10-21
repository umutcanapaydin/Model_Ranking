"""`agentic-coding` moves from Epoch's copy of DeepSWE to Datacurve's own dataset (#265, D-216) — cite REQ-SRC-012.

The surface, its family and the registry name the new source; Epoch's copy is no longer built, and stays attributed
and credited as a retired source, so an artifact an older release built still boots (D-194 clause 6). Datacurve is
credited for its dataset under CC BY 4.0. Through the build's own ingest and the served API, `agentic-coding`
answers from the recorded job at `high` effort.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_litellm
from app.workflows.rank import build_price_medians
from app.workflows.registry import reconcile
from app.workflows.schema import connect

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "datacurve"
JOB = "20260606-deep-swe-leaderboard-all-4x"
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
DATASET = "https://huggingface.co/datasets/datacurve/deep-swe-leaderboard"


def _envelope() -> str:
    return json.dumps({"job": JOB, **{name: (FIXTURES / f"{name}.json").read_text(encoding="utf-8")
                                      for name in ("result", "config")}})


def test_agentic_coding_ranks_on_datacurve_and_epochs_copy_is_not_built() -> None:
    """covers REQ-SRC-012 (D-216 clause 1): the surface, its family and the registry; nothing builds Epoch's copy."""
    from app.workflows import categories, families, sources

    spec = categories.CATEGORIES["agentic-coding"]
    assert (spec.primary_source, spec.primary_benchmark, spec.metric, spec.ranking_effort) == (
        "datacurve_deepswe", "DeepSWE", "% resolved", "high")
    assert families.FAMILIES["agentic-coding"] == ("datacurve_deepswe", "terminalbench_4", "arena_agent")
    assert "datacurve_deepswe" in {s.name for s in sources.REMOTE_SOURCES}
    assert "epoch_deepswe_external" not in {b.name for b in sources.LOCAL_BUNDLES}
    assert all("epoch_deepswe_external" not in family for family in families.FAMILIES.values())


def test_datacurve_is_credited_under_cc_by_4_0_with_its_dataset() -> None:
    """covers REQ-SRC-012 (D-216 clause 6): the citation names the publisher, the dataset and the licence, and the
    Credits screen names Datacurve under CC BY 4.0 with both links."""
    from app.workflows import board_tables, rank

    citation = rank.SOURCE_ATTRIBUTION["datacurve_deepswe"]
    assert "Datacurve" in citation and DATASET in citation and CC_BY in citation
    assert citation in rank.ATTRIBUTIONS
    credit = board_tables.CREDITS["datacurve"]
    assert (credit.publisher, credit.url, credit.licence, credit.licence_url) == (
        "Datacurve", DATASET, "CC BY 4.0", CC_BY)
    assert [c["id"] for c in rank.credits_for([citation])] == ["datacurve"]


def test_epochs_copy_stays_attributed_and_credited_as_a_retired_source() -> None:
    """covers REQ-SRC-012 (D-216 clause 6, D-194 clause 6): an older artifact's rows keep D-193's citation and its
    credit, so the engine boots on it until the refresh replaces it; no build names the source again."""
    from app.workflows import board_tables, rank

    retired = board_tables.RETIRED_EXTERNAL_ATTRIBUTION["epoch_deepswe_external"]
    assert "https://deepswe.datacurve.ai/" in retired and "epoch_deepswe_external" not in rank.SOURCE_ATTRIBUTION
    assert "epoch_deepswe_external" not in board_tables.EPOCH_EXTERNAL_ATTRIBUTION
    assert rank.attributions_for(["epoch_deepswe_external"], priced=False) == (retired,)
    assert [c["id"] for c in rank.credits_for([retired])] == ["datacurve_leaderboard", "epoch_compilation"]
    assert board_tables.CREDITS["datacurve_leaderboard"].licence == "© Datacurve; no licence published"


def _built(path: Path) -> None:
    """The board through the build's own ingest, with a LiteLLM price for every model the job names."""
    from app.workflows import sources

    models = {key.split("__")[1] for key in json.loads((FIXTURES / "result.json").read_text(encoding="utf-8"))["stats"]["evals"]}
    prices = json.dumps({name: {"mode": "chat", "input_cost_per_token": 3e-06, "output_cost_per_token": 1.5e-05}
                         for name in sorted(models)})
    conn = connect(str(path))
    run = RunContext(observed_at="2026-10-21T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", prices), run)
    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    assert declared.ingest(conn, FakeRawSource("datacurve_deepswe", _envelope()), run).stored == 27
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()


def test_every_run_of_the_recorded_job_links_a_catalogue_model(tmp_path: Path) -> None:
    """covers REQ-SRC-012: the 27 runs name 19 models, and the alias rules link every one."""
    db = tmp_path / "built.db"
    _built(db)
    with sqlite3.connect(db) as conn:
        linked = dict(conn.execute("SELECT raw_name, model_id FROM scores WHERE source = 'datacurve_deepswe'"))
    assert len(linked) == 19 and all(linked.values()), linked
    assert linked["gpt-5-5"] == "gpt-5.5" and linked["claude-opus-4-8"] == "claude-4.8-opus"


def test_agentic_coding_answers_from_the_datacurve_board_at_high_effort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-012 (D-216 clauses 1 and 2): the surface ranks the recorded job's `high` and default runs;
    GPT-5.5's `xhigh` run, the board's top score, is not ranked as a `high` one."""
    from app.adapter import main

    db = tmp_path / "built.db"
    _built(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    answer = TestClient(main.app).get("/v1/recommendations?task=agentic-coding").json()["answers"][0]
    assert answer["surface"] == "agentic-coding" and answer["unavailable_reason_code"] is None, answer
    assert any("Datacurve" in source for source in answer["sources"]), answer["sources"]
    top = answer["picks"][0]
    assert top["label"] == "best_quality" and top["score"] == 61.9, top
