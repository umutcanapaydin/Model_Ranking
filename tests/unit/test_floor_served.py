"""M17-W1 P2, D-159 -- the floor every reader uses is the one derived from the served board.

Before D-159 each surface's floor was a number in `categories.py`, so a board could grow for a month
and the Budget Pick, the subscription bar and `/v1/categories` (D-152, shown on the detail screen)
went on using a floor measured on a board that no longer existed (W-128). Now the floor MOVES WITH
THE BOARD, and these tests move it the only way it can move: by changing the board's rows.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter
from app.workflows.categories import CATEGORIES
from app.workflows.floors import derived_floor
from app.workflows.recommend import recommend

from .test_api_v1 import _seeded_db
from .test_uncertainty_contract import PINNED_SCORE_ANCHORS


@pytest.fixture
def seeded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "seeded.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    return db


def _served() -> dict[str, dict]:
    response = TestClient(adapter.app).get("/v1/categories")
    assert response.status_code == 200
    return {entry["id"]: entry for entry in response.json()["categories"]}


def _raise_the_board(db: Path, surface: str, above: float, rows: int, name: str = "unranked") -> None:
    """Add `rows` rows to the surface's own board, every one above `above`."""
    spec = CATEGORIES[surface]
    with sqlite3.connect(db) as conn:
        conn.executemany(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) VALUES (?, ?, ?, ?, 'h', 'unspecified', ?, 'u', 'z')",
            [(f"{name}-{above:g}-{i}", spec.primary_benchmark, spec.metric, above + 1 + i, spec.primary_source)
             for i in range(rows)])


def test_every_surface_publishes_the_floor_derived_from_its_served_board(seeded: Path) -> None:
    served = _served()
    conn = sqlite3.connect(seeded)
    for surface, spec in CATEGORIES.items():
        assert served[surface]["min_quality"] == derived_floor(conn, spec), surface


def test_the_published_floor_moves_with_the_board_and_the_anchor_does_not(seeded: Path) -> None:
    """D-152 and D-146 clause 2 together: the floor follows the board; the anchor is an owner's
    ruling and follows nothing."""
    surface = "document"
    _raise_the_board(seeded, surface, above=1400.0, rows=30)  # the fixture has no Elo board
    before = _served()[surface]["min_quality"]
    assert before is not None
    _raise_the_board(seeded, surface, above=before, rows=200)
    after = _served()[surface]
    assert after["min_quality"] > before
    assert after["score_anchor"] == PINNED_SCORE_ANCHORS[surface]


def test_with_no_artifact_no_floor_is_invented(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The detail screen already says nothing when the engine sends no floor (REQ-FLR-002)."""
    monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "absent.db"))
    served = _served()
    assert {entry["min_quality"] for entry in served.values()} == {None}


def test_the_budget_pick_clears_the_floor_of_the_board_it_reads(seeded: Path) -> None:
    """A floor raised above every ranked model means nothing clears it: the answer says so rather
    than keeping a bar measured on yesterday's board."""
    surface = "coding"
    conn = sqlite3.connect(seeded)
    floor = derived_floor(conn, CATEGORIES[surface])
    rec = recommend(conn, "unlimited", surface)
    assert rec is not None and floor is not None
    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.score >= floor
    conn.close()

    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.why_fact["floor"] == floor

    best = max(p.score for p in rec.picks)
    _raise_the_board(seeded, surface, above=best, rows=500)
    conn = sqlite3.connect(seeded)
    raised = derived_floor(conn, CATEGORIES[surface])
    rec = recommend(conn, "unlimited", surface)
    assert rec is not None and raised is not None and raised > best
    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.why_fact == {"reason": "nothing_clears_floor", "floor": raised, "unit": budget.why_fact["unit"]}


def test_the_budget_pick_says_when_its_board_is_empty(seeded: Path) -> None:
    """A surface can rank models from another source on its benchmark while its OWN board (D-148:
    its primary source) is empty. Then no floor can be measured, and the answer says exactly that --
    it never falls back to a number nobody measured."""
    spec = CATEGORIES["coding"]
    with sqlite3.connect(seeded) as conn:
        conn.execute("UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE source = ? AND benchmark = ?",
                     (spec.primary_source, spec.primary_benchmark))
    conn = sqlite3.connect(seeded)
    assert derived_floor(conn, spec) is None
    rec = recommend(conn, "unlimited", "coding")
    assert rec is not None
    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.why_fact["floor"] is None and budget.why_fact["reason"] == "nothing_clears_floor"
    assert "board is empty" in budget.why
