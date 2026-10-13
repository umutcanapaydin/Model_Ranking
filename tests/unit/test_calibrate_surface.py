"""D-194 clause 4 (#265): a surface moved to a licensed board is calibrated on it, by a script, and ships the
thresholds its record states — cite REQ-SRC-012.

`scripts/calibrate_board.py` reads Arena's boards only. `scripts/calibrate_surface.py` sizes a surface the
build already holds: `close_call` is twice the board's own standard error (M8's measurement rule), and
`value_window` puts its edge in the first gap wider than `close_call` that leaves at least three
candidates, at the gap's middle, so the window never splits two models the board cannot tell apart.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

RECORDS = {"computer-use": "docs/research/d194-computer-use-calibration.json",
           "abstract": "docs/research/d194-abstract-calibration.json"}


def _script():  # imported lazily, so this file collects before the script exists
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("calibrate_surface")


def test_the_window_ends_in_the_first_gap_wider_than_the_close_call_past_three_candidates() -> None:
    """covers REQ-SRC-012: TB 4.0's priced board of 2026-10-13 above its floor of 44.5."""
    scores = [64.85, 61.82, 58.18, 57.88, 51.82, 49.39, 44.55, 41.82, 12.0]
    picked = _script().thresholds(scores, floor=44.5, stderr=1.648)
    assert picked["close_call"] == 3.3
    # 57.88 -> 51.82 is the first gap past three candidates wider than 3.3; its middle is 10 below 64.85
    assert (picked["value_window"], picked["candidates"]) == (10.0, 4)


def test_a_board_with_no_such_gap_admits_every_model_above_its_floor() -> None:
    """covers REQ-SRC-012: with nothing to split on, the window reaches the floor."""
    picked = _script().thresholds([50.0, 49.0, 48.0, 47.0, 46.5], floor=46.0, stderr=1.0)
    assert (picked["value_window"], picked["candidates"]) == (4.0, 5)


def test_a_stderr_that_is_not_positive_is_refused() -> None:
    with pytest.raises(ValueError):
        _script().thresholds([50.0, 40.0], floor=40.0, stderr=0.0)


@pytest.mark.parametrize(("surface", "record"), sorted(RECORDS.items()))
def test_a_moved_surface_ships_the_thresholds_its_calibration_record_states(surface: str, record: str) -> None:
    """covers REQ-SRC-012 (D-194 clause 4): the pinned pair is read from the record the script wrote."""
    from app.workflows.categories import CATEGORIES

    written = json.loads(Path(record).read_text(encoding="utf-8"))
    spec = CATEGORIES[surface]
    assert written["surface"] == surface and written["source"] == spec.primary_source
    assert (spec.close_call, spec.value_window) == (written["close_call"], written["value_window"])


def test_a_binomial_standard_error_is_taken_over_the_models_above_the_floor() -> None:
    """The review's M1: taken over every derived setting, zeros below the floor drove it toward 0."""
    script = _script()
    above = [79.0, 77.0, 75.8, 63.6]
    assert script.binomial_stderr([*above, 0.0, 0.0, 0.0, 0.0, 0.0], floor=27.4, tasks=120) == script.binomial_stderr(
        above, floor=27.4, tasks=120)
    assert round(script.binomial_stderr([50.0], floor=0.0, tasks=100), 3) == 5.0



@pytest.mark.parametrize(("surface", "record"), sorted(RECORDS.items()))
def test_each_record_is_what_the_script_computes_from_the_records_own_data(surface: str, record: str) -> None:
    """The #265 Tester's M1: the shipped pair is pinned to the record; the record is pinned to the rule."""
    written = json.loads(Path(record).read_text(encoding="utf-8"))
    scores = [score for _, score in written["above_floor"]]
    picked = _script().thresholds(scores, floor=written["floor"], stderr=written["stderr"])
    assert (picked["close_call"], picked["value_window"], picked["candidates"]) == (
        written["close_call"], written["value_window"], written["candidates"])


def test_a_model_on_the_floor_is_within_reach_and_the_window_is_a_half_point() -> None:
    """The #265 Tester's M1: the floor is inclusive, and the window's edge is rounded to half a point."""
    picked = _script().thresholds([60.0, 59.0, 58.0, 50.0], floor=50.0, stderr=0.5)
    assert picked["candidates"] == 3 and picked["value_window"] == 6.0  # mid-gap 6.0, past 3 candidates
    assert _script().thresholds([60.0, 59.0, 58.0, 57.0], floor=57.0, stderr=1.0)["candidates"] == 4
    assert _script().thresholds([60.0, 59.9, 59.8, 52.8], floor=50.0, stderr=0.5)["value_window"] == 3.5  # mid 3.7
