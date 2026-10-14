"""#262: every source a `/v1` answer can cite is credited by `/v1/boards` on the same artifact.

The Credits screen shows the credits `/v1/boards` derives from the boards it serves; a recommendation
cites its own sources, its secondary benchmark's among them (`rank.secondary_evidence_sources`). That
reads every row of the secondary benchmark and skips the effort filter `board_standings` applies, so a
source could be cited on an answer and missing from the screen.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.aider import BENCHMARK, METRIC
from app.workflows import standings
from app.workflows.categories import CATEGORIES
from app.workflows.recommend import BUDGETS

from .test_api_v1 import _seeded_db


def _with_aider(path: Path) -> None:
    """`coding`'s secondary, Aider, for every model the seeded SWE-bench board ranks."""
    _seeded_db(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, run_date,"
                     " source, source_url, observed_at) SELECT model_id, raw_name, ?, ?, score / 2, 'aider',"
                     " 'unspecified', run_date, 'aider', 'https://aider.chat', observed_at FROM scores"
                     " WHERE source = 'swebench' AND model_id IS NOT NULL", (BENCHMARK, METRIC))


def _cited_and_credited(db: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[set[str], set[str]]:
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    client = TestClient(main.app)
    cited = {source for task in CATEGORIES for budget in BUDGETS
             for answer in client.get(f"/v1/recommendations?task={task}&budget={budget}").json().get("answers", [])
             for source in answer.get("sources", [])}
    credited = set(client.get("/v1/boards").json()["attributions"])
    return cited, credited


def test_every_citation_an_answer_carries_is_credited_on_the_boards_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "advisor.db"
    _with_aider(db)
    cited, credited = _cited_and_credited(db, monkeypatch)
    assert any("Aider" in source for source in cited), cited
    assert cited <= credited, cited - credited


def test_a_secondary_board_the_effort_filter_hides_is_still_credited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The issue's case: an effort policy on the secondary benchmark leaves its rows off `/v1/boards`,
    while `coding`'s answers still cite them."""
    db = tmp_path / "advisor.db"
    _with_aider(db)
    monkeypatch.setattr(standings, "_policies", lambda: {BENCHMARK: "high"})
    cited, credited = _cited_and_credited(db, monkeypatch)
    assert any("Aider" in source for source in cited), cited
    assert cited <= credited, cited - credited
