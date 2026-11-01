"""The release delta Tester of `integration/fixes-1101` (2026-11-01): D-240 clause 2, "as narrow as written".

#544's refinements check (`test_refinements.py::test_every_board_a_question_can_select_is_served`) excuses a refinable
surface whose primary board is missing only when its source is optional (D-121), the artifact holds no row of it at
all, and `/v1` discloses the gap as `no_evidence`; "any other missing primary fails". The check reads the real
artifact, where the one missing primary (`arena_document`, 2026-10-30) meets all three, so loosening the source's
test stayed green: F-E1 (`required` not read), F-E2 (the row count not read), F-E3 (every source excused). They are
held here on a fixture table, which CI runs too (no artifact, so no skip).
"""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows.sources import REMOTE_SOURCES

from .test_refinements import _sent_nothing

REQUIRED = next(s.name for s in REMOTE_SOURCES if s.required)
OPTIONAL = next(s.name for s in REMOTE_SOURCES if not s.required)


def _scores(*sources: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE scores (source TEXT)")
    conn.executemany("INSERT INTO scores (source) VALUES (?)", [(s,) for s in sources])
    return conn


# covers D-240 clause 2, #544
def test_only_an_optional_source_with_no_row_at_all_is_an_outage() -> None:
    assert _sent_nothing(_scores(), OPTIONAL), "the outage itself: optional, and nothing of it in the artifact"
    assert not _sent_nothing(_scores(), REQUIRED), "a required source (D-121) that sent nothing is no outage"
    assert not _sent_nothing(_scores(OPTIONAL), OPTIONAL), "rows of it are left: its board was lost, not unsent"
    with pytest.raises(AssertionError):
        _sent_nothing(_scores(), "no-such-source")

