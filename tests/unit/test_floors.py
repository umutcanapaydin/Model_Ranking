"""M17-W1, D-159 -- every floor is derived from its board, by one function.

D-148 clause 1: a surface's floor is the top third of its board's ROWS, one per raw name as the parser
stores them. The owner ruled (2026-09-23, M17 plan §0.1) that it is computed from the served
artifact every time, not kept by hand. `app.workflows.floors` is the one definition: the engine
reads it, and `scripts/survey_boards.py --floors` measures with it, so the two cannot disagree.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.workflows import floors
from app.workflows.categories import CATEGORIES

from .test_survey_floors import _artifact, _script


def test_the_floor_is_the_top_third_of_the_rows() -> None:
    assert floors.top_third([90.0, 88.0, 80.0, 70.0, 60.0, 50.0]) == 88.0
    assert floors.top_third([70.0]) == 70.0
    # twelve rows: the fourth from the top (a quarter would be the third)
    assert floors.top_third([float(v) for v in range(12, 0, -1)]) == 9.0
    assert floors.top_third([]) is None


def test_the_board_is_the_surfaces_own_source_benchmark_and_metric(tmp_path: Path) -> None:
    """Review MINOR-4's predicates (M16-W3): another source on the same benchmark, or another
    metric on the same source, is not this surface's board."""
    path = _artifact(tmp_path, [("a", 90.0, "high"), ("a", 88.0, "low"), ("b", 80.0, "unspecified")])
    spec = CATEGORIES["expert"]
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                   "source_url, observed_at) VALUES ('x', ?, ?, 99, 'h', 'unspecified', 'other_src', "
                   "'u', 'z')", (spec.primary_benchmark, spec.metric))
    conn = sqlite3.connect(path)
    assert sorted(floors.board_scores(conn, spec)) == [80.0, 88.0, 90.0]
    assert floors.derived_floor(conn, spec) == 90.0


def test_an_empty_board_has_no_floor(tmp_path: Path) -> None:
    path = _artifact(tmp_path, [("a", 90.0, "unspecified")])
    assert floors.derived_floor(sqlite3.connect(path), CATEGORIES["coding"]) is None


@pytest.mark.parametrize("rows", [
    [("a", 90.0, "high"), ("a", 88.0, "low"), ("b", 80.0, "unspecified"), ("c", 70.0, "unspecified"),
     ("d", 60.0, "unspecified"), ("e", 50.0, "unspecified")],
    [("a", 51.5, "unspecified")],
])
def test_the_measurement_script_and_the_engine_agree(tmp_path: Path, rows: list) -> None:  # type: ignore[type-arg]
    path = _artifact(tmp_path, rows)
    conn = sqlite3.connect(path)
    table = {row["surface"]: row["floor_rows"] for row in _script().floors(conn)}
    assert table == {s: floors.derived_floor(conn, spec) for s, spec in CATEGORIES.items()}
