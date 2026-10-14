"""The reading wave's Tester (`docs/reviews/backlog-reading-tester.md`): the scorer D-196 rests on
(`docs/research/reading-wave-m22-runs/score.py`).

Every figure in D-196's "Measured" paragraph and in `docs/research/reading-wave-m22-probe.md` is a count
that scorer made from a committed run. No test read it, so a planted fault in it (a question that is not
a search counted right only when the reading asks about it, a search counted right whatever its
reading, an own-set search counted right on any surface) passed the whole suite (the Tester's T1).

Counts only: these tests read the held-out set's labels, never print a question, and compare the
scorer's output and the committed runs with the figures the record gives. # covers D-196
"""

import contextlib
import io
import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "docs/research/reading-wave-m22-runs"
HELD_OUT = ROOT / "scripts/router_probe/reading_heldout_m22_questions.json"


def _scored() -> dict[str, str]:
    """Each line `score.py` prints, keyed by the run it names; the scorer prints counts only."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        runpy.run_path(str(RUNS / "score.py"), run_name="score")
    return {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in out.getvalue().splitlines() if ":" in line}


def _labels() -> list[str]:
    return [label for _, label in json.loads(HELD_OUT.read_text(encoding="utf-8"))]


def _rows(name: str) -> dict[int, dict[str, str]]:
    return {row["row"]: row for row in json.loads((RUNS / f"{name}.json").read_text(encoding="utf-8"))}


def _right(row: dict[str, str], label: str) -> bool:
    if label == "NOT_A_SEARCH":
        return row["reading"] != "search"
    return row["reading"] == "search" and row["unmeasured"] == "false" and row["surface"] in label.split("|")


def test_each_held_out_run_answers_the_set_row_for_row() -> None:
    """A run that dropped or repeated a row would shift every count the scorer makes from it."""
    size = len(_labels())
    assert size == 147, "D-196 counts 147 questions"
    assert sum(label != "NOT_A_SEARCH" for label in _labels()) == 89, "D-196 counts 89 searches"
    for path in sorted(RUNS.glob("*-wording-*.json")) + sorted(RUNS.glob("before-model-*.json")):
        rows = [row["row"] for row in json.loads(path.read_text(encoding="utf-8"))]
        assert sorted(rows) == list(range(size)), f"{path.name} does not answer the set row for row"


def test_d196s_held_out_figures_are_the_scorers_counts() -> None:
    """D-196 "Measured": 88 right before and 91 after; searches right 59 then 62, not measured 8 then 0;
    29 of 58 caught throughout; the first head 65; the model tier asked 1 and 3 of 89 searches."""
    scored = _scored()
    wording = "searches 89: right {right}, not measured {unmeasured}, asked 0 | not a search 58: caught 29"
    for run in ("before-wording-1", "before-wording-2"):
        assert scored[run] == "right 88/147 | " + wording.format(right=59, unmeasured=8), run
    for run in ("after-wording-1", "after-wording-2"):
        assert scored[run] == "right 94/147 | " + wording.format(right=65, unmeasured=0), run
    for run in ("review-wording-1", "review-wording-2", "final-wording-1"):
        assert scored[run] == "right 91/147 | " + wording.format(right=62, unmeasured=0), run
    asked = sorted(int(re.search(r"asked (\d+)", scored[run]).group(1)) for run in ("before-model-1", "before-model-2"))
    assert asked == [1, 3], "D-196 clause 2: the model tier asked 1 and 3 of 89 searches"


def test_d196s_own_set_figures_are_the_scorers_counts() -> None:
    """D-196 "Measured": the wave's own 61 Turkish searches, 31 right before and 44 after; typed in plain
    letters, 29 and 39."""
    scored = _scored()
    assert scored["own-before"] == "letters 31/61 (not measured 22), plain 29/61 (not measured 22)"
    assert scored["own-both-spellings"] == "letters 44/61 (not measured 0), plain 39/61 (not measured 0)"


def test_d196s_question_by_question_figures_follow_from_the_runs() -> None:
    """D-196 "Measured": against before, 3 rows gained and none lost, and no question answered before the
    wave changes its surface; against the first head, 4 searches lost and 1 gained, three of the 4
    answered `everyday` again; the cost, 10 lines that are not a search, uncaught, moved from "not
    measured" to a ranking."""
    labels = _labels()
    before, first, final = _rows("before-wording-1"), _rows("after-wording-1"), _rows("final-wording-1")
    gained = [i for i in before if not _right(before[i], labels[i]) and _right(final[i], labels[i])]
    lost = [i for i in before if _right(before[i], labels[i]) and not _right(final[i], labels[i])]
    assert (len(gained), len(lost)) == (3, 0)
    moved = [i for i in before if before[i]["unmeasured"] == "false"
             and (before[i]["surface"], before[i]["reading"]) != (final[i]["surface"], final[i]["reading"])]
    assert moved == [], "a question answered before the wave changed its surface or reading"
    head_lost = [i for i in first if labels[i] != "NOT_A_SEARCH" and _right(first[i], labels[i])
                 and not _right(final[i], labels[i])]
    head_gained = [i for i in first if labels[i] != "NOT_A_SEARCH" and not _right(first[i], labels[i])
                   and _right(final[i], labels[i])]
    assert (len(head_lost), len(head_gained)) == (4, 1)
    assert sum(final[i]["surface"] == "everyday" for i in head_lost) == 3
    cost = [i for i in before if labels[i] == "NOT_A_SEARCH" and before[i]["unmeasured"] == "true"
            and final[i]["unmeasured"] == "false" and final[i]["reading"] == "search"]
    assert len(cost) == 10
