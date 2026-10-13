"""D-194 through the build's own path (#265 — the Tester's B1 and M3) — cite REQ-SRC-012.

Each new board is ingested by the `RemoteSource` the build registers for it, so a source wired to another
source's ingest, or an ingest that drops rows, fails here. The stored efforts are the ones a reader is
shown. `computer-use` and `abstract` then answer on `/v1/recommendations`, and the first refresh from an
artifact an older release built to one this release built passes both of the refresh's gates.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fakes import FakeRawSource
from app.workflows import sources
from app.workflows.ingest import RunContext, ingest_litellm
from app.workflows.rank import build_price_medians
from app.workflows.registry import reconcile
from app.workflows.schema import connect

from .test_api_v1 import PRICING, _seeded_db
from .test_arc_agi_2 import RECORD
from .test_terminalbench_4 import FILES, LISTING, _raw

#: A LiteLLM price for every model the two fixtures name, so each one can be ranked.
PRICES = json.dumps({name: {"mode": "chat", "input_cost_per_token": 3e-06, "output_cost_per_token": 1.5e-05}
                     for name in ("claude-opus-5-5", "glm-5.3-flash", "gemini-3.8-flash", "claude-opus-4-8",
                                  "gpt-5.4", "grok-4.20-beta-0309b-reasoning")})
PAYLOADS = {"terminalbench_4": (_raw(FILES), LISTING), "arc_agi_2": (json.dumps(RECORD), RECORD["url"])}


def _ingest_new_boards(conn: sqlite3.Connection, run: RunContext) -> None:
    for name, (payload, url) in PAYLOADS.items():
        source = next(s for s in sources.REMOTE_SOURCES if s.name == name)
        report = source.ingest(conn, FakeRawSource(name, payload, url=url), run)
        assert report.stored == 3, (name, report)


def _built(path: Path) -> None:
    conn = connect(str(path))
    run = RunContext(observed_at="2026-10-13T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICES), run)
    _ingest_new_boards(conn, run)
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()


def test_each_new_board_is_stored_by_its_registered_ingest_at_the_efforts_a_reader_sees(tmp_path: Path) -> None:
    """covers REQ-SRC-012: TB 4.0's `none` effort is unspecified; ARC's `-high` and `-xhigh` suffixes are
    read at the store; a setting with no suffix is unspecified."""
    db = tmp_path / "built.db"
    _built(db)
    with sqlite3.connect(db) as conn:
        stored = {(source, raw): (benchmark, effort) for source, raw, benchmark, effort in conn.execute(
            "SELECT source, raw_name, benchmark, effort FROM scores")}
    assert stored == {
        ("terminalbench_4", "anthropic/claude-opus-5-5"): ("Terminal-Bench 4.0", "max"),
        ("terminalbench_4", "z-ai/glm-5.3-flash"): ("Terminal-Bench 4.0", "unspecified"),
        ("terminalbench_4", "gemini/gemini-3.8-flash"): ("Terminal-Bench 4.0", "high"),
        ("arc_agi_2", "claude-opus-4-8-high"): ("ARC-AGI-2 (public eval)", "high"),
        ("arc_agi_2", "gpt-5-4-xhigh"): ("ARC-AGI-2 (public eval)", "xhigh"),
        ("arc_agi_2", "grok-4.20-beta-0309b-reasoning"): ("ARC-AGI-2 (public eval)", "unspecified"),
    }


@pytest.mark.parametrize(("task", "board", "top"), [("computer-use", "Terminal-Bench 4.0", 64.8),
                                                   ("abstract", "ARC-AGI-2", 76.9)])
def test_the_moved_surfaces_answer_on_their_new_boards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, task: str, board: str, top: float
) -> None:
    """covers REQ-SRC-012 (D-194 clause 2): the surface a reader asks ranks on the board D-194 moved it to."""
    from app.adapter import main

    db = tmp_path / "built.db"
    _built(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    answer = TestClient(main.app).get(f"/v1/recommendations?task={task}").json()["answers"][0]
    assert answer["surface"] == task and answer["unavailable_reason_code"] is None, answer
    assert any(board in source for source in answer["sources"]), answer["sources"]
    assert answer["picks"][0]["label"] == "best_quality" and answer["picks"][0]["score"] == top


def test_the_first_refresh_from_an_older_releases_artifact_passes_both_gates(tmp_path: Path) -> None:
    """covers REQ-SRC-012 (D-194 clause 6; the Tester's M3): the live artifact holds the retired sources, the
    candidate the new ones; neither gate refuses, so the startup refresh publishes."""
    from app.workflows.refresh import degradations, fingerprint_of, upward_anomalies

    live, candidate = tmp_path / "live.db", tmp_path / "candidate.db"
    _seeded_db(live)
    with sqlite3.connect(live) as conn:
        for source, benchmark in (("epoch_arc_agi", "ARC-AGI"), ("epoch_terminalbench", "TerminalBench")):
            conn.execute("INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, run_date,"
                         " source, source_url, observed_at) SELECT model_id, raw_name, ?, metric, score, harness, effort,"
                         " run_date, ?, 'https://epoch.ai', observed_at FROM scores WHERE source = 'swebench'",
                         (benchmark, source))
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url, observed_at)"
                     " SELECT alias, model_id, input_per_m, output_per_m, 'openrouter', 'https://openrouter.ai',"
                     " observed_at FROM pricing WHERE source = 'litellm'")
    _seeded_db(candidate)
    conn = connect(str(candidate))
    run = RunContext(observed_at="2026-10-13T00:00:00+00:00")
    # LiteLLM's working set is replaced as a whole, so the candidate's holds the seeded prices and these.
    ingest_litellm(conn, FakeRawSource("litellm", json.dumps(json.loads(PRICING) | json.loads(PRICES))), run)
    _ingest_new_boards(conn, run)
    conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url, observed_at)"
                 " SELECT alias, NULL, input_per_m, output_per_m, 'models_dev', 'https://models.dev/api.json',"
                 " observed_at FROM pricing WHERE source = 'litellm'")
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()
    before, after = fingerprint_of(live), fingerprint_of(candidate)
    assert before is not None and after is not None
    assert degradations(before, after) == []
    assert upward_anomalies(before, after) == []
