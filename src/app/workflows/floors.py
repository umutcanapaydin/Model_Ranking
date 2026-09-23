"""Every surface's floor, derived from its board (D-148 clause 1, D-159).

A surface's floor -- the line below which the product does not recommend, and the bar a Budget Pick
must clear -- is the top third of its board's ROWS: every row the parser stored for the surface's
primary source, benchmark and metric, one per raw name, harness and effort (D-148, "every row in the
list", owner, translated from Turkish). The rule is relative to the board, so a number kept by hand
goes stale as the board grows: the fresh Epoch bundle moved six of them (W-128). The owner ruled on
2026-09-23 that it is computed every time instead (D-159).

**One definition.** The engine (`recommend`, `subscribe`, `/v1/categories`) and the measurement
script (`scripts/survey_boards.py --floors`) all call this module, so a measured floor and a served
one cannot disagree. It reads the artifact it is handed and never writes (INV-23 is the caller's).
"""

from __future__ import annotations

import sqlite3

from app.workflows.categories import CategorySpec

#: D-148 clause 1's quantile: the floor is the value one third of the way down the board.
FLOOR_FRACTION = 1 / 3


def top_third(values: list[float]) -> float | None:
    """The value one third of the way down, rounded as the output boundary rounds (D-109)."""
    if not values:
        return None
    ordered = sorted(values, reverse=True)
    return round(ordered[max(0, round(len(ordered) * FLOOR_FRACTION) - 1)], 1)


#: The surface's board: its primary source, benchmark and metric (M16-W3 review MINOR-4: another
#: source on the same benchmark, or another metric, is not this board). One clause, read by both
#: functions below, so the floor and the guard on its rows can never read different boards.
_BOARD = "FROM scores WHERE source = ? AND benchmark = ? AND metric = ?"


def _board(spec: CategorySpec) -> tuple[str, str, str]:
    return spec.primary_source, spec.primary_benchmark, spec.metric


def board_scores(conn: sqlite3.Connection, spec: CategorySpec) -> list[float]:
    """Every row of the surface's board."""
    return [row[0] for row in conn.execute(f"SELECT score {_BOARD}", _board(spec))]


def board_names(conn: sqlite3.Connection, spec: CategorySpec) -> frozenset[str]:
    """Every raw name on the board `board_scores` reads. The refresh compares these across cycles,
    because the floor is derived from every row. Where a board's raw name carries its harness or
    effort (SWE-bench's "agent + model", Epoch's `_xhigh`), a relabel of either reads as a new name;
    where it does not, a relabel on rows it already had changes nothing here."""
    return frozenset(raw for (raw,) in conn.execute(f"SELECT DISTINCT raw_name {_BOARD}", _board(spec)))


def derived_floor(conn: sqlite3.Connection, spec: CategorySpec) -> float | None:
    """The surface's floor on the artifact behind `conn`; None when its board is empty."""
    return top_third(board_scores(conn, spec))
