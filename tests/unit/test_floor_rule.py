"""D-148 clause 1 and D-159 -- the floor the engine serves is the rule, on the board it serves.

Until M17-W1 this compared a hand-kept floor in `categories.py` with a research record of one day's
measurement (`docs/research/m16-w3-floor-table-2026-09-23.md`), which is exactly the shape that went
stale (W-128). The floor is now derived where it is read (`app.workflows.floors`), so this test holds
the DERIVATION to the rule, on the artifact the owner serves, against a second, independent reading
of the rule written here -- a derivation that drifted from the ruling would disagree with it.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.adapter import main as adapter
from app.workflows.categories import CATEGORIES
from app.workflows.floors import derived_floor


def _rule(conn: sqlite3.Connection, source: str, benchmark: str, metric: str) -> float | None:
    """D-148 clause 1, read a SECOND way: SQLite orders the board and picks the row a third of the
    way down with OFFSET. `floors.py` sorts in Python; the two share no code (M17-W1 review
    MINOR-4: the first version of this oracle copied the implementation line for line)."""
    where = "source = ? AND benchmark = ? AND metric = ?"
    args = (source, benchmark, metric)
    count = conn.execute(f"SELECT COUNT(*) FROM scores WHERE {where}", args).fetchone()[0]
    if not count:
        return None
    offset = max(0, round(count / 3) - 1)
    row = conn.execute(f"SELECT score FROM scores WHERE {where} ORDER BY score DESC "
                       "LIMIT 1 OFFSET ?", (*args, offset)).fetchone()
    return round(row[0], 1)


@pytest.mark.artifact
def test_every_served_floor_is_the_rule_on_its_board() -> None:
    conn = adapter.open_readonly(Path("advisor.db"))
    try:
        derived = {s: derived_floor(conn, spec) for s, spec in CATEGORIES.items()}
        literal = {s: _rule(conn, spec.primary_source, spec.primary_benchmark, spec.metric)
                   for s, spec in CATEGORIES.items()}
    finally:
        conn.close()
    assert any(v is not None for v in derived.values()), "fails closed: no board had a floor"
    assert derived == literal
