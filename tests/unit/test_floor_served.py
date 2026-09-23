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
    assert budget.why_fact["reason"] == "no_floor_measured"
    assert "board is empty" in budget.why


# --- M17-W1 review (docs/reviews/m17-wave-1-review.md) -------------------------------------------


def test_a_floor_moved_by_rows_the_ranking_never_carries_is_a_served_change(seeded: Path) -> None:
    """BLOCKING-1: the floor counts every row of the board, the ranking only the ones it can rank. A
    board that grows by models nobody prices moves the floor and the Budget Pick, and the refresh's
    fingerprint must see it -- or it reports "nothing a user would notice changed" and never publishes."""
    from app.workflows.refresh import fingerprint_of

    before = fingerprint_of(seeded)
    _raise_the_board(seeded, "coding", above=74.5, rows=60)
    after = fingerprint_of(seeded)
    assert before is not None and after is not None
    assert after.digest != before.digest


def test_an_empty_own_board_has_its_own_reason_code(seeded: Path) -> None:
    """MINOR-1: `nothing_clears_floor` with a null floor meant two things, and the phone could word
    neither. No measurable floor is its own reason."""
    spec = CATEGORIES["coding"]
    with sqlite3.connect(seeded) as conn:
        conn.execute("UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE source = ? "
                     "AND benchmark = ?", (spec.primary_source, spec.primary_benchmark))
    rec = recommend(sqlite3.connect(seeded), "unlimited", "coding")
    assert rec is not None
    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.why_fact["reason"] == "no_floor_measured"
    assert "floor" not in budget.why_fact or budget.why_fact["floor"] is None


def test_the_no_floor_fact_carries_the_unit_the_app_words_it_with(seeded: Path) -> None:
    """Re-review MINOR-R2 (mutant E3): the app's sentence needs the unit, and without it the Turkish
    screen shows the engine's English. The fact's whole shape is pinned here, on the engine side."""
    spec = CATEGORIES["coding"]
    with sqlite3.connect(seeded) as conn:
        conn.execute("UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE source = ? "
                     "AND benchmark = ?", (spec.primary_source, spec.primary_benchmark))
    rec = recommend(sqlite3.connect(seeded), "unlimited", "coding")
    assert rec is not None
    budget = next(p for p in rec.picks if p.label == "budget_pick")
    assert budget.why_fact == {"reason": "no_floor_measured", "unit": spec.score_unit}


@pytest.mark.parametrize("surface", sorted(CATEGORIES))
def test_every_surfaces_floor_is_hashed_to_its_published_precision(
    seeded: Path, monkeypatch: pytest.MonkeyPatch, surface: str
) -> None:
    """Re-review MINOR-R1 (mutants R4, R5): a fingerprint that hashed only one surface's floor, or
    hashed it to whole points, passed every test that moved `coding`. Each surface's floor, moved by
    the 0.1 `/v1/categories` publishes and nothing else, must change the digest."""
    from app.workflows import refresh as refresh_module

    real = refresh_module.derived_floor

    def floor_at(value: float) -> object:
        def floor(conn: sqlite3.Connection, spec: object) -> float | None:
            return value if spec is CATEGORIES[surface] else real(conn, spec)  # type: ignore[arg-type]
        return floor

    # 50.2 -> 50.3: the published one-decimal step, inside one whole point.
    monkeypatch.setattr(refresh_module, "derived_floor", floor_at(50.2))
    before = refresh_module.fingerprint_of(seeded)
    monkeypatch.setattr(refresh_module, "derived_floor", floor_at(50.3))
    after = refresh_module.fingerprint_of(seeded)
    assert before is not None and after is not None
    assert after.surfaces == before.surfaces, "the ranked rows moved -- the test would prove nothing"
    assert after.digest != before.digest, surface


def test_every_quoted_floor_is_printed_as_the_engine_applies_it() -> None:
    """MINOR-2 (W-084): the check on printed bars read `{spec.min_quality...}`, which no longer
    exists, so `{floor:.0f}` -- a bar the engine does not apply -- passed. Every place that prints the
    derived floor prints it with `:g`."""
    import inspect
    import re

    from app.workflows import recommend as recommend_module
    from app.workflows import subscribe

    quoted = re.compile(r"\{floor(:[^}]+)?\}")
    for module in (recommend_module, subscribe):
        source = inspect.getsource(module)
        specs = quoted.findall(source)
        assert specs, f"{module.__name__} prints no floor at all -- this check reads nothing"
        assert set(specs) == {":g"}, (module.__name__, specs)


def _swebench_with(unpriced: int, high: int = 0) -> str:
    """The SWE-bench fixture plus `unpriced` low rows nobody prices and `high` high ones."""
    import json

    from .test_build import SWEBENCH

    board = json.loads(SWEBENCH)
    board["leaderboards"][0]["results"] += [
        {"name": f"some-agent + Unpriced Model {i}", "resolved": 10.0 + i, "date": "2026-01-01",
         "logs": True, "trajs": True} for i in range(unpriced)] + [
        {"name": f"some-agent + Unpriced Leader {i}", "resolved": 90.0 + i, "date": "2026-01-01",
         "logs": True, "trajs": True} for i in range(high)]
    return json.dumps(board)


def test_the_refresh_publishes_a_board_that_grew_only_by_unranked_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BLOCKING-1 through the real `refresh()` and `build.main`: the upstream adds models nobody
    prices, no ranked row changes, the floor rises -- and the cycle publishes."""
    from app.workflows.refresh import EXIT_PUBLISHED, fingerprint_of, refresh

    from .test_build import _sources
    from .test_refresh_carry import _first_cycle, _use

    # A board of 18 rows grows by 2 (11%): a real board's pace, under the owner's flood guard below.
    live = _first_cycle(tmp_path, monkeypatch, swebench=_swebench_with(16))
    before = fingerprint_of(live)
    floor_before = derived_floor(sqlite3.connect(live), CATEGORIES["coding"])
    _use(monkeypatch, _sources(swebench=_swebench_with(16, high=2)))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    # Re-review NIT-R2: the precondition, asserted -- no ranked row moved, and the floor did.
    after = fingerprint_of(live)
    assert before is not None and after is not None
    assert after.surfaces == before.surfaces and after.models == before.models
    floor_after = derived_floor(sqlite3.connect(live), CATEGORIES["coding"])
    assert floor_before is not None and floor_after is not None and floor_after > floor_before

