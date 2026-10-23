"""#415 (D-220 clause 2): a cut the owner accepted is not a loss.

Epoch re-ran its chess board in 2026-10 and published 154 of the 245 models the served artifact held.
The owner accepted that cut once: `data/accepted-cuts.yaml` names the board and exactly the rows it
may lose. The D-164 guard stops counting those rows as lost, and only those: any other row lost is
judged as before, and a cut named for one board excuses nothing on another. A file that cannot be read
as the schema says fails the refresh (closed), never excuses everything.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.workflows import boards as declared_boards
from app.workflows import refresh
from app.workflows.refresh import degradations, fingerprint_of

from .test_refresh_board_ids import SLICE, _boards

BOARD = f"board {SLICE.source}"


def _drop(*indexes: int) -> object:
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany("DELETE FROM scores WHERE source = ? AND raw_name = ?",
                         [(SLICE.source, f"Probe {i:02d}") for i in indexes])
    return change


def _judged(tmp_path: Path, change: object, cuts: dict[str, frozenset[str]],
            base: object = None) -> list[str]:
    def both(conn: sqlite3.Connection) -> None:
        if base is not None:
            base(conn)  # type: ignore[operator]
        change(conn)  # type: ignore[operator]

    live = fingerprint_of(_boards(tmp_path / "live.db", base))  # type: ignore[arg-type]
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", both))
    assert live is not None and candidate is not None
    return degradations(live, candidate, cuts=cuts)


def _names(*indexes: int) -> frozenset[str]:
    return frozenset(f"Probe {i:02d}" for i in indexes)


def test_without_a_cut_a_quarter_lost_is_refused(tmp_path: Path) -> None:
    """The control: three of twelve rows gone refuses the night (D-164 clause 2)."""
    reasons = _judged(tmp_path, _drop(0, 1, 2), cuts={})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_the_owner_accepted_is_not_a_loss(tmp_path: Path) -> None:
    assert _judged(tmp_path, _drop(0, 1, 2), cuts={SLICE.source: _names(0, 1, 2)}) == []


def test_a_row_lost_outside_the_accepted_cut_still_counts(tmp_path: Path) -> None:
    """Five rows gone, two of them named: three of twelve is still a quarter."""
    reasons = _judged(tmp_path, _drop(0, 1, 2, 3, 4), cuts={SLICE.source: _names(0, 1)})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_named_for_one_board_excuses_nothing_on_another(tmp_path: Path) -> None:
    other = next(board.source for board in declared_boards.uncovered() if board.source != SLICE.source)
    reasons = _judged(tmp_path, _drop(0, 1, 2), cuts={other: _names(0, 1, 2)})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_excuses_an_unlinked_row_by_its_spelling(tmp_path: Path) -> None:
    def unlinked(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET model_id = NULL WHERE source = ?", (SLICE.source,))

    assert _judged(tmp_path, _drop(0, 1, 2), cuts={SLICE.source: _names(0, 1, 2)}, base=unlinked) == []


def test_the_committed_file_accepts_epochs_chess_re_run_and_nothing_else() -> None:
    cuts = refresh.load_accepted_cuts()
    assert set(cuts) == {"epoch_chess"}
    assert len(cuts["epoch_chess"]) == 94
    assert "QwQ-32B" in cuts["epoch_chess"]


@pytest.mark.parametrize("raw", [
    "",                                                     # an empty file is not "no cuts"
    "cuts: []\nextra: 1\n",                                 # an unknown key
    "cuts:\n  - board: epoch_chess\n    rows: [a]\n",      # no decision, no reason
    "cuts:\n  - board: not_a_board\n    decision: D-220\n    reason: r\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: []\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: [1]\n",
])
def test_a_file_that_is_not_the_schema_fails_closed(raw: str) -> None:
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw)


def test_a_file_with_no_cuts_excuses_nothing() -> None:
    assert refresh.parse_accepted_cuts("cuts: []\n") == {}
