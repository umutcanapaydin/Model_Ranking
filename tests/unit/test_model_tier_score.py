"""#351 phase 1: the model-tier report scores a reading-probe run against its set.

A set row is `[question, expected]`. `expected` is a surface, `a|b` when either surface answers it, or
`NOT_A_SEARCH`. A search is right when the app's reading is `search` and the surface is one of the
expected ones, measured. A line that is not a search is caught when the reading is anything but `search`
(`notASearch` or `unsure`: the reader is never shown a ranking for it unasked). The rule is the one the
m23 and m24 probe write-ups scored by; on the m24 set's wording-tier run it gives their 83, 70 and 13.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _model_tier():
    spec = importlib.util.spec_from_file_location("model_tier_under_test", ROOT / "scripts" / "model_tier.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(q: str, surface: str, reading: str = "search", unmeasured: str = "false") -> dict[str, str]:
    return {"q": q, "surface": surface, "reading": reading, "unmeasured": unmeasured}


def test_a_search_is_right_on_any_expected_surface_measured_and_read_as_a_search() -> None:
    score = _model_tier().score(
        [["a", "coding|web-dev"], ["b", "coding"], ["c", "coding"], ["d", "coding"]],
        [_row("a", "web-dev"), _row("b", "coding", unmeasured="true"), _row("c", "coding", reading="unsure"),
         _row("d", "vision")])
    assert (score.right, score.searches_right, score.searches) == (1, 1, 4)
    assert score.searches_unmeasured == 1


def test_a_line_that_is_not_a_search_is_caught_by_any_reading_but_search() -> None:
    score = _model_tier().score(
        [["a", "NOT_A_SEARCH"], ["b", "NOT_A_SEARCH"], ["c", "NOT_A_SEARCH"]],
        [_row("a", "everyday", reading="notASearch"), _row("b", "everyday", reading="unsure"), _row("c", "coding")])
    assert (score.not_searches_caught, score.not_searches, score.right) == (2, 3, 2)


def test_a_question_the_run_did_not_answer_is_wrong_and_counted() -> None:
    score = _model_tier().score([["a", "coding"], ["b", "NOT_A_SEARCH"]],
                                [_row("a", "nil", reading="nil")])
    assert (score.right, score.no_answer) == (0, 2)


def test_an_empty_run_is_an_error_not_a_zero_score() -> None:
    module = _model_tier()
    try:
        module.score([["a", "coding"]], [])
    except module.EmptyRun:
        return
    raise AssertionError("an empty run scored instead of failing")


def test_a_golden_row_marked_not_a_search_is_scored_as_one() -> None:
    """D-211 clause 2: the golden set's `not_a_search` rows are NOT_A_SEARCH to the model-tier score."""
    rows = dict((q, e) for q, e in _model_tier().load_set("golden"))
    assert rows["kira kontrat\u0131m\u0131 okuyup bana \u00f6zet \u00e7\u0131kar"] == "NOT_A_SEARCH"
    assert rows["which ai is best at fixing bugs in a large java project"] == "coding"
