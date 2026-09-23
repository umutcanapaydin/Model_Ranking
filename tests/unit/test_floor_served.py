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


def test_the_published_floor_moves_with_the_board(seeded: Path) -> None:
    """D-152 and D-159: the floor follows the board (and since D-162 the anchor follows the floor,
    `test_the_anchor_moves_with_the_board`)."""
    surface = "document"
    _raise_the_board(seeded, surface, above=1400.0, rows=30)  # the fixture has no Elo board
    before = _served()[surface]["min_quality"]
    assert before is not None
    _raise_the_board(seeded, surface, above=before, rows=200)
    after = _served()[surface]
    assert after["min_quality"] > before


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


# --- The owner's flood guard (2026-09-23, D-159 correction) --------------------------------------


def _board_grown(seeded: Path, tmp_path: Path, base: int, added: int) -> tuple[object, object]:
    """Fingerprints of `coding`'s board at `base` extra rows, and after `added` more nobody prices."""
    import shutil

    from app.workflows.refresh import fingerprint_of

    _raise_the_board(seeded, "coding", above=10.0, rows=base, name="base")
    live = fingerprint_of(seeded)
    grown = tmp_path / "grown.db"
    shutil.copy(seeded, grown)
    _raise_the_board(grown, "coding", above=74.5, rows=added)
    candidate = fingerprint_of(grown)
    assert live is not None and candidate is not None
    assert candidate.surfaces == live.surfaces, "a ranked row moved -- the test would prove nothing"
    return live, candidate


def test_a_board_flooded_with_rows_it_has_never_seen_is_refused(seeded: Path, tmp_path: Path) -> None:
    """Owner, 2026-09-23 (translated from Turkish: "yes, add a simple guard"): the floor is derived
    from EVERY row of the board, and D-132's new-names guard reads only ranked models. So a burst of
    rows nobody prices moved `coding`'s floor from 65.4 to 71.3 on a copy of the owner's artifact
    with nothing to object. The same limit as D-132 now applies to the board's own rows."""
    from app.workflows.refresh import upward_anomalies

    live, flooded = _board_grown(seeded, tmp_path, base=20, added=60)
    reasons = upward_anomalies(live, flooded)  # type: ignore[arg-type]
    assert any(r.startswith("coding's board") for r in reasons), reasons


def test_a_board_that_grows_at_a_boards_pace_is_not_refused(seeded: Path, tmp_path: Path) -> None:
    """The other direction: a real board adds a row or two a night. Refusing that would freeze
    the refresh, which D-128 names as the failure to fear."""
    from app.workflows.refresh import upward_anomalies

    live, grown = _board_grown(seeded, tmp_path, base=20, added=2)
    assert upward_anomalies(live, grown) == []  # type: ignore[arg-type]


def test_the_refresh_refuses_a_flooded_board_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The flood guard through the real `refresh()` and `build.main`."""
    from app.workflows.refresh import EXIT_REFUSED, refresh

    from .test_build import _sources
    from .test_refresh_carry import _first_cycle, _use

    live = _first_cycle(tmp_path, monkeypatch, swebench=_swebench_with(16))
    _use(monkeypatch, _sources(swebench=_swebench_with(16, high=30)))
    outcome, code = refresh(live)
    assert code == EXIT_REFUSED, outcome.reason
    assert "coding's board" in (outcome.reason or ""), outcome.reason


def test_a_board_that_returns_is_not_refused(seeded: Path, tmp_path: Path) -> None:
    """A board that was empty and answers again is a source RETURNING (D-132's own exemption), not
    a flood: every name on it is new, and refusing it would keep the surface without a floor."""
    import shutil

    from app.workflows.refresh import fingerprint_of, upward_anomalies

    spec = CATEGORIES["coding"]
    blind = tmp_path / "blind.db"
    shutil.copy(seeded, blind)
    with sqlite3.connect(blind) as conn:
        conn.execute("UPDATE scores SET source = 'epoch_swe_bench_verified' WHERE source = ? "
                     "AND benchmark = ?", (spec.primary_source, spec.primary_benchmark))
    live, returned = fingerprint_of(blind), fingerprint_of(seeded)
    assert live is not None and returned is not None
    assert not live.board["coding"] and returned.board["coding"], "the fixture proves nothing"
    assert not [r for r in upward_anomalies(live, returned) if "board" in r]


def _board_changed(seeded: Path, tmp_path: Path, base: int, added: int = 0, removed: int = 0) -> tuple:
    """Fingerprints of `coding`'s board with `base` extra rows, then `added` more and `removed` of
    the extra ones, all rows nobody prices -- so the ranked rows never move."""
    import shutil

    from app.workflows.refresh import fingerprint_of

    _raise_the_board(seeded, "coding", above=10.0, rows=base, name="base")
    live = fingerprint_of(seeded)
    changed = tmp_path / "changed.db"
    shutil.copy(seeded, changed)
    _raise_the_board(changed, "coding", above=74.5, rows=added)
    with sqlite3.connect(changed) as conn:
        conn.execute("DELETE FROM scores WHERE rowid IN (SELECT rowid FROM scores "
                     "WHERE raw_name LIKE 'base-%' ORDER BY raw_name LIMIT ?)", (removed,))
    candidate = fingerprint_of(changed)
    assert live is not None and candidate is not None
    assert candidate.surfaces == live.surfaces, "a ranked row moved -- the test would prove nothing"
    return live, candidate


@pytest.mark.parametrize(("added", "refused"), [(10, False), (11, True)])
def test_the_board_growth_limit_is_a_quarter_exactly(
    seeded: Path, tmp_path: Path, added: int, refused: bool
) -> None:
    """Re-review 2 MINOR-2: the quarter is pinned at its edge. 30 names gaining 10 is 10 of 40, AT a
    quarter, which passes (D-132: "more than"); 11 of 41 is over it."""
    from app.workflows.refresh import upward_anomalies

    live, grown = _board_changed(seeded, tmp_path, base=27, added=added)
    assert len(live.board["coding"]) == 30
    flagged = any(r.startswith("coding's board") for r in upward_anomalies(live, grown))
    assert flagged is refused


@pytest.mark.parametrize(("removed", "refused"), [(9, False), (10, True)])
def test_a_board_that_loses_a_quarter_of_its_names_is_refused(
    seeded: Path, tmp_path: Path, removed: int, refused: bool
) -> None:
    """Re-review 2 MAJOR-1: the guard counted only names ADDED. A board that lost 85 of its 173
    unpriced rows moved `coding`'s floor from 65.4 to 71.4 and published; when they came back, the
    guard refused them every night as "never seen". The loss is now held to D-128's limit: 10 of 40
    names is AT a quarter, which D-128 refuses ("at or over"); 9 is under it."""
    from app.workflows.refresh import degradations

    live, shrunk = _board_changed(seeded, tmp_path, base=37, removed=removed)
    assert len(live.board["coding"]) == 40
    flagged = any(r.startswith("coding's board") for r in degradations(live, shrunk))
    assert flagged is refused


def test_the_refresh_refuses_a_board_that_shrinks_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MAJOR-1 through the real `refresh()`: 16 of 18 names leave the board, and the cycle refuses."""
    from app.workflows.refresh import EXIT_REFUSED, refresh

    from .test_build import _sources
    from .test_refresh_carry import _first_cycle, _use

    live = _first_cycle(tmp_path, monkeypatch, swebench=_swebench_with(16))
    _use(monkeypatch, _sources(swebench=_swebench_with(0)))
    outcome, code = refresh(live)
    assert code == EXIT_REFUSED, outcome.reason
    assert "coding's board" in (outcome.reason or ""), outcome.reason


# --- #15: the out-of-100 anchor is the surface's derived floor (owner, 2026-09-23) -------------


def test_every_elo_surface_anchors_its_score_at_its_served_floor(seeded: Path) -> None:
    """#15: `score_anchor` is the floor the surface recommends from, so the app's "50 is at the
    bar" is true. Off Elo there is no anchor: a percentage is already out of 100, and ECI stays
    rank-only (D-143)."""
    for surface in ("document", "assistant"):
        _raise_the_board(seeded, surface, above=1400.3, rows=30)  # a floor with a decimal
    served = _served()
    assert served["document"]["min_quality"] % 1, "a whole-number floor cannot catch a rounded anchor"
    for surface, spec in CATEGORIES.items():
        if spec.metric == "elo":
            assert served[surface]["score_anchor"] == served[surface]["min_quality"], surface
        else:
            assert served[surface]["score_anchor"] is None, surface
    assert served["document"]["score_anchor"] is not None, "the fixture proves nothing"


def test_the_anchor_moves_with_the_board(seeded: Path) -> None:
    """#15, the reverse of D-146 clause 2: the board grows, the floor rises, and the anchor goes
    with it."""
    surface = "document"
    _raise_the_board(seeded, surface, above=1400.0, rows=30)
    before = _served()[surface]["score_anchor"]
    assert before is not None
    _raise_the_board(seeded, surface, above=before, rows=200, name="higher")
    after = _served()[surface]
    assert after["score_anchor"] > before
    assert after["score_anchor"] == after["min_quality"]


def test_with_no_artifact_no_anchor_is_invented(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a served board there is no floor, so no anchor: the app keeps the engine's own
    scale (D-146 clause 1) rather than reading every Elo score against a number nobody measured."""
    monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "absent.db"))
    assert {entry["score_anchor"] for entry in _served().values()} == {None}
