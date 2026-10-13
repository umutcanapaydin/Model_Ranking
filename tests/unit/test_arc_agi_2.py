"""ARC-AGI-2 from ARC Prize's own MIT public-evaluation runs (#265, D-194) — cite REQ-SRC-012.

`abstract` ranked on Epoch's copy of the ARC Prize leaderboard, whose terms bar commercial use. ARC Prize
publishes its own runs on the 120 public evaluation tasks under MIT (`arcprize/arc_agi_v2_public_eval`).
Scoring every model setting reads about 4,300 files and the dataset has not changed since 2026-06-04, so
`scripts/derive_arc_public_eval.py` derives the scores once at a pinned revision into
`data/arc-agi-2-public-eval.json`, and the build reads that file.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

REVISION = "026789c1c12a" + "0" * 28
RECORD = {
    "dataset": "arcprize/arc_agi_v2_public_eval",
    "url": "https://huggingface.co/datasets/arcprize/arc_agi_v2_public_eval",
    "revision": REVISION,
    "licence": "MIT",
    "publisher": "ARC Prize Foundation",
    "tasks": 120,
    "min_tasks": 114,
    "settings": {
        "claude-opus-4-8-high": {"tasks_run": 120, "solved": 92.333333, "score": 76.9444, "cost_usd": 375.81},
        "gpt-5-4-xhigh": {"tasks_run": 119, "solved": 88.5, "score": 73.75, "cost_usd": None},
        "grok-4.20-beta-0309b-reasoning": {"tasks_run": 120, "solved": 30.0, "score": 25.0, "cost_usd": 12.5},
    },
}


def _arc():  # imported lazily, so this file collects before the module exists
    return importlib.import_module("app.clients.arc_prize")


def _derive():
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("derive_arc_public_eval")


def test_each_setting_is_a_row_at_its_derived_percentage() -> None:
    """covers REQ-SRC-012: the setting's folder is the raw name (its effort is read from it at the store);
    ARC Prize's harness; no evaluation date, as the dataset gives none; provenance at the revision."""
    rows, skipped = _arc().parse_arc_agi_2(json.dumps(RECORD))
    assert skipped == 0
    by_name = {r.raw_name: r for r in rows}
    opus = by_name["claude-opus-4-8-high"]
    assert (opus.score, opus.harness, opus.run_date, opus.cost_total) == (76.9444, "arc-prize", None, 375.81)
    assert (opus.benchmark, opus.metric, opus.source) == ("ARC-AGI-2 (public eval)", "% correct", "arc_agi_2")
    assert opus.source_url == f"https://huggingface.co/datasets/arcprize/arc_agi_v2_public_eval/tree/{REVISION}"
    assert by_name["gpt-5-4-xhigh"].cost_total is None


@pytest.mark.parametrize(("field", "value"), [("score", 101.0), ("score", -1.0), ("score", "76"),
                                              ("tasks_run", 113), ("tasks_run", None)])
def test_a_setting_out_of_range_or_partial_is_skipped_and_counted(field: str, value: object) -> None:
    """covers REQ-SRC-012: the file's own rule (`min_tasks`) holds at the build too."""
    record = json.loads(json.dumps(RECORD))
    record["settings"]["claude-opus-4-8-high"][field] = value
    rows, skipped = _arc().parse_arc_agi_2(json.dumps(record))
    assert "claude-opus-4-8-high" not in {r.raw_name for r in rows} and skipped == 1


@pytest.mark.parametrize("change", [{"licence": "CC-BY-NC-4.0"}, {"revision": ""}, {"settings": []}, {"tasks": 0}])
def test_a_record_that_is_not_the_licensed_derivation_is_refused(change: dict[str, object]) -> None:
    """covers REQ-SRC-012: a file that names another licence, no revision, or no settings fails the source."""
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError):
        _arc().parse_arc_agi_2(json.dumps({**RECORD, **change}))
    for raw in ("[]", "not json"):
        with pytest.raises(SourceError):
            _arc().parse_arc_agi_2(raw)


def test_a_pair_is_solved_by_either_attempt_and_a_task_scores_its_share_of_pairs() -> None:
    """covers REQ-SRC-012: ARC Prize's rule, as its own `results.json` sums it."""
    solved = {"attempt_1": {"correct": False}, "attempt_2": {"correct": True}}
    missed = {"attempt_1": {"correct": False}, "attempt_2": None}
    grids = [[[0]], [[0]]]
    assert _derive().task_score([solved], grids) == 1.0
    assert _derive().task_score([solved, missed], grids) == 0.5
    assert _derive().task_score([{"attempt_1": {"correct": "true"}}], grids) == 0.0
    assert _derive().task_score([], grids) == 0.0


def test_the_committed_record_is_the_licensed_derivation_and_parses() -> None:
    """covers REQ-SRC-012: the file the build reads, as committed."""
    record = json.loads(Path("data/arc-agi-2-public-eval.json").read_text(encoding="utf-8"))
    assert (record["dataset"], record["licence"], record["tasks"]) == ("arcprize/arc_agi_v2_public_eval", "MIT", 120)
    assert len(record["revision"]) == 40
    rows, skipped = _arc().parse_arc_agi_2(json.dumps(record))
    assert len(rows) >= 40 and skipped == 0


def test_abstract_ranks_on_arc_agi_2_and_epochs_copy_is_gone() -> None:
    """covers REQ-SRC-012 (D-194 clause 2): the surface, its family and the source list."""
    from app.workflows import board_tables, categories, families, sources

    spec = categories.CATEGORIES["abstract"]
    assert (spec.primary_source, spec.primary_benchmark) == ("arc_agi_2", "ARC-AGI-2 (public eval)")
    assert families.FAMILIES["abstract"] == ("arc_agi_2", "epoch_chess", "epoch_mystery")
    assert "arc_agi_2" in {s.name for s in sources.REMOTE_SOURCES}
    assert "epoch_arc_agi" not in {b.source_name for b in board_tables.EPOCH_BOARDS}


def test_arc_prize_is_credited_under_mit_with_its_dataset() -> None:
    """covers REQ-SRC-012 (D-194 clause 5): the citation and the Credits screen name the licence."""
    from app.workflows import board_tables, rank

    citation = rank.SOURCE_ATTRIBUTION["arc_agi_2"]
    assert "(MIT)" in citation and "huggingface.co/datasets/arcprize/arc_agi_v2_public_eval" in citation
    assert "public evaluation" in citation and citation in rank.ATTRIBUTIONS
    credit = board_tables.CREDITS["arc_prize"]
    assert (credit.licence, credit.url) == ("MIT", "https://huggingface.co/datasets/arcprize/arc_agi_v2_public_eval")
    assert [c["id"] for c in rank.credits_for([citation])] == ["arc_prize"]


# --- The #265 review (docs/reviews/issue-265-licensed-sources-review.md) ------------------------------------

GRID = [[1, 2], [3, 4]]


def test_an_attempt_arc_prize_never_marked_is_scored_against_the_published_solution() -> None:
    """covers REQ-SRC-012 (the review's B1): ARC Prize left `correct` null on whole settings (GPT-5 Pro,
    Claude Sonnet 4.5). Read as wrong, they were served at 0. A null mark is scored by comparing the
    answer with ARC-AGI-2's published solution; a boolean mark is ARC Prize's and is kept."""
    derive = _derive()
    unmarked_right = {"attempt_1": {"correct": None, "answer": [[0]]}, "attempt_2": {"correct": None, "answer": GRID}}
    unmarked_wrong = {"attempt_1": {"correct": None, "answer": [[0]]}, "attempt_2": None}
    marked_wrong = {"attempt_1": {"correct": False, "answer": GRID}}
    assert derive.task_score([unmarked_right], [GRID]) == 1.0
    assert derive.task_score([unmarked_right, unmarked_wrong], [GRID, GRID]) == 0.5
    assert derive.task_score([marked_wrong], [GRID]) == 0.0
    assert derive.task_score([{"attempt_1": {"correct": None, "answer": GRID}}], []) == 0.0  # no solution: unsolved


def test_the_committed_record_scores_unmarked_settings_and_names_its_solutions() -> None:
    """covers REQ-SRC-012 (the review's B1 and M6): the derivation names the solutions it scored unmarked
    attempts against, and dates each setting by its runs. The settings the review found served at 0 score
    what they solved. The comparison agrees with ARC Prize's marks on all but 17 of 16,681 (where ARC
    Prize marked an attempt, its mark is kept); a model a board measures at 0, as Claude 3 Haiku is
    here, stays at 0."""
    record = json.loads(Path("data/arc-agi-2-public-eval.json").read_text(encoding="utf-8"))
    solutions = record["solutions"]
    assert solutions["repository"] == "arcprize/ARC-AGI-2" and solutions["licence"] == "Apache-2.0"
    assert len(solutions["revision"]) == 40
    assert record["marks_checked"] > 10_000 and record["marks_disagreeing"] * 200 <= record["marks_checked"]
    settings = record["settings"]
    assert settings["gpt-5-pro-2025-10-06"]["score"] > 10, "GPT-5 Pro solved task 1818057f, unmarked"
    assert settings["claude-sonnet-4-5-20250929-thinking-32k"]["score"] > 10
    assert all(len(entry["run_date"]) == 10 for entry in settings.values())


def test_a_setting_is_stored_with_the_date_of_its_latest_run() -> None:
    """covers REQ-UNC-003 (the review's M6): every attempt carries its start time; the evidence is dated."""
    record = json.loads(json.dumps(RECORD))
    record["settings"]["claude-opus-4-8-high"]["run_date"] = "2026-05-14"
    rows, _ = _arc().parse_arc_agi_2(json.dumps(record))
    assert {r.raw_name: r.run_date for r in rows}["claude-opus-4-8-high"] == "2026-05-14"


def test_a_record_without_a_task_floor_holds_every_setting_to_all_the_tasks() -> None:
    """covers REQ-SRC-012 (the review's M3): with no `min_tasks`, a setting short of `tasks` is partial."""
    record = {k: v for k, v in json.loads(json.dumps(RECORD)).items() if k != "min_tasks"}
    rows, skipped = _arc().parse_arc_agi_2(json.dumps(record))
    assert "gpt-5-4-xhigh" not in {r.raw_name for r in rows} and skipped == 1


# --- The #265 review, round 2 (docs/reviews/issue-265-licensed-sources-review-round-2.md) -------------------

OTHER = [[5]]


def test_an_unmarked_attempt_is_compared_with_the_solution_of_its_own_pair_index() -> None:
    """covers REQ-SRC-012 (round 2's N1, N2): pairs are matched by `metadata.pair_index`, not by position, and
    a task's second pair is compared with its second solution."""
    second = {"attempt_1": {"correct": None, "answer": OTHER, "metadata": {"pair_index": 1}}}
    first = {"attempt_1": {"correct": None, "answer": GRID, "metadata": {"pair_index": 0}}}
    assert _derive().task_score([second, first], [GRID, OTHER]) == 1.0
    assert _derive().task_score([first, {"attempt_1": {"correct": None, "answer": GRID}}], [GRID, OTHER]) == 0.5


def test_a_setting_is_dated_by_its_latest_attempt_and_one_unmarked_before_the_solutions_is_not_comparable() -> None:
    """covers REQ-UNC-003, REQ-SRC-012 (round 2's N1, N2): ARC Prize removed the first test pair of five tasks on
    2025-05-15, so an unmarked attempt run before then is compared with solutions it never answered."""
    derive = _derive()
    def attempt(start: str, correct: object) -> dict[str, object]:
        return {"correct": correct, "answer": GRID, "metadata": {"start_timestamp": start, "pair_index": 0}}
    later = [[{"attempt_1": attempt("2025-10-01T00:00:00+00:00", None), "attempt_2": attempt("2025-09-30T00:00:00+00:00", None)}]]
    earlier = [[{"attempt_1": attempt("2025-04-14T10:00:00+00:00", None)}]]
    marked_earlier = [[{"attempt_1": attempt("2025-04-14T10:00:00+00:00", True)}]]
    assert derive._latest_run(later) == "2025-10-01"
    assert derive.comparable(later) and not derive.comparable(earlier) and derive.comparable(marked_earlier)


def test_the_committed_record_pins_its_solutions_lists_each_disagreement_and_leaves_out_gpt_4_1() -> None:
    """covers REQ-SRC-012 (round 2's N1): the solutions are the pinned commit; each disagreement with a mark is
    named; GPT-4.1's unmarked runs of 2025-04-14 are left out, not scored against later solutions."""
    record = json.loads(Path("data/arc-agi-2-public-eval.json").read_text(encoding="utf-8"))
    assert record["solutions"]["revision"] == _derive().SOLUTIONS_COMMIT
    assert len(record["disagreements"]) == record["marks_disagreeing"]
    assert {"gpt-4-1-2025-04-14", "gpt-4-1-mini-2025-04-14"} <= set(record["left_out_as_predating_solutions"])
    assert record["unscorable"] == 0
