"""Which boards can be aged, and which honestly cannot — cites REQ-UNC-003.

**What was assumed, and what is actually true.** Six of twelve score sources carry no `run_date` at
all, and that was carried into M13's plan as a defect to repair. Read against the bundle it is two
different situations wearing one symptom:

* `epoch_capabilities_index.csv`, `arc_agi_external.csv`, `mmlu_external.csv` and
  `deepswe_external.csv` publish only a **model release date** — when the model came out, not when
  it was evaluated. There is no evaluation date to read. `sources.py` says so in its own comment and
  the engine already discloses it per answer: `evidence_dating: "undated"` with the sentence *"This
  answer's benchmark publishes no evaluation dates, only model release dates."* Verified live
  against the running engine on the `computer-use` surface. **That half of REQ-UNC-003 was already
  met before M13 opened, and recording it as a defect would have been a repair of nothing.**
* `terminalbench_external.csv` is different: it carries a **`Run date` column, populated on 204 of
  204 rows** with real evaluation dates from 2025-10-31 onward, and the board declaration simply
  never named it. That is a date the product had and threw away.

`webdev_arena_external.csv` carries `Last updated`, and it is deliberately NOT wired: 33 of 109 rows
only, every one the same value, which makes it the date the leaderboard page was refreshed rather
than the date any model was measured. Presenting that in the same field as an evaluation date would
be a new small lie in a product whose whole discipline is not telling those.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.clients.epoch_board import EpochBoard, parse_board
from app.workflows.sources import EPOCH_BOARDS

BOARDS = {board.source_name: board for board in EPOCH_BOARDS}

#: Boards whose upstream publishes an evaluation date. The value is the column that carries it, so
#: a rename upstream fails here rather than silently reverting the surface to undated.
DATED_BOARDS = {
    "epoch_gpqa": "Started at",
    "epoch_aime": "Started at",
    "epoch_terminalbench": "Run date",
}

#: Boards whose upstream publishes only a model RELEASE date. Undated is the honest state, and the
#: engine discloses it (REQ-API-004). Pinned so a later edit cannot quietly invent a date for them
#: by pointing `date_column` at "Release date" — which would report the model's birthday as the
#: date its score was measured.
UNDATED_BOARDS = {"epoch_eci", "epoch_arc_agi", "epoch_mmlu", "epoch_webdev"}


@pytest.mark.parametrize("source_name, column", sorted(DATED_BOARDS.items()))
def test_a_board_with_an_evaluation_date_declares_it(source_name: str, column: str) -> None:
    """REQ-UNC-003. `epoch_terminalbench` failed this: the column was there and unread."""
    board = BOARDS[source_name]
    assert board.date_column == column


@pytest.mark.parametrize("source_name", sorted(UNDATED_BOARDS))
def test_a_board_with_no_evaluation_date_claims_none(source_name: str) -> None:
    """The other direction, and the one that protects the disclosure.

    `_evidence_dating` asks only whether `evidence_date` is not None. So pointing an undated board
    at any date-shaped column would flip its surface from an honest "undated" to a confident
    "dated" without a single test noticing — which is exactly the failure `epoch_board.py`'s own
    comment records from the truncation defect.
    """
    assert BOARDS[source_name].date_column is None


def test_every_declared_board_is_covered_by_this_file() -> None:
    """Derive the roster instead of typing it, so a new board cannot skip this decision.

    A board added without a ruling on its dating would inherit `date_column=None` silently, and the
    product would report its evidence as undated whether or not that is true.
    """
    assert set(BOARDS) == DATED_BOARDS.keys() | UNDATED_BOARDS


def test_the_terminalbench_column_actually_parses(tmp_path: Path) -> None:
    """A declaration nothing reads is not a repair.

    The header spelling is asserted against a fixture shaped like the real file, so a `date_column`
    naming a column that does not exist — which `parse_board` answers with `None`, silently —
    fails here instead of shipping.
    """
    csv = tmp_path / "terminalbench_external.csv"
    csv.write_text(
        "Model version,Accuracy mean,Release date,Run date\n"
        "Claude Opus 4.7,0.512,2026-01-15,2025-10-31\n"
        "GPT-5.6 Sol,0.488,2026-02-01,2025-11-02\n", encoding="utf-8"
    )
    board = EpochBoard(
        file="terminalbench_external.csv",
        source_name="epoch_terminalbench",
        benchmark="TerminalBench",
        metric="% resolved",
        score_column="Accuracy mean",
        date_column=BOARDS["epoch_terminalbench"].date_column,
    )
    rows, _ = parse_board(csv.read_text(encoding="utf-8"), board)
    dates = [row.run_date for row in rows]
    assert dates == [
        "2025-10-31",
        "2025-11-02",
    ], f"the declared date column did not reach the parsed rows: {dates}"


def test_a_release_date_is_never_read_as_an_evaluation_date(tmp_path: Path) -> None:
    """The mistake this whole file exists to make impossible.

    Every one of these CSVs carries `Release date`. It is the most available date-shaped column in
    the bundle and the wrong one: a model released in January and evaluated in August would report
    its evidence as eight months fresher than it is.
    """
    for source_name in sorted(UNDATED_BOARDS):
        assert BOARDS[source_name].date_column != "Release date"
    for source_name in DATED_BOARDS:
        assert BOARDS[source_name].date_column != "Release date", source_name
