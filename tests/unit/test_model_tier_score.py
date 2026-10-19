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


def test_mcnemar_is_the_exact_two_sided_test_of_fixed_against_broken() -> None:
    """#351 (D-206, the three research reports): a change is kept when it fixes more questions than it breaks
    beyond chance. Under greedy decoding each variant runs once, and the exact McNemar test is the one for a
    single run; with five or fewer changed questions no result can reach p < 0.05."""
    mcnemar = _model_tier().mcnemar
    assert round(mcnemar(9, 1), 4) == 0.0215
    assert round(mcnemar(13, 3), 4) == 0.0213
    assert round(mcnemar(15, 5), 4) == 0.0414
    assert mcnemar(5, 0) > 0.05
    assert mcnemar(0, 0) == 1.0
    assert mcnemar(3, 9) == mcnemar(9, 3)


def test_a_comparison_names_each_question_a_change_fixed_or_broke() -> None:
    expected = [["a", "coding"], ["b", "NOT_A_SEARCH"], ["c", "coding"], ["d", "coding"], ["e", "NOT_A_SEARCH"]]
    base = [_row("a", "vision"), _row("b", "everyday"), _row("c", "coding"), _row("d", "coding"),
            _row("e", "everyday", reading="unsure")]
    candidate = [_row("a", "coding"), _row("b", "everyday", reading="unsure"), _row("c", "vision"),
                 _row("d", "coding"), _row("e", "everyday", reading="notASearch")]
    result = _model_tier().compare(expected, base, candidate)
    assert (result.fixed, result.broken) == (["a", "b"], ["c"])
    assert (result.searches_net, result.not_searches_net) == (0, 1)


def test_a_run_is_named_by_its_label_and_number() -> None:
    """`--compare greedy kinds` reads run 1 of each label; `greedy:1 greedy:2` checks one label's two runs."""
    module = _model_tier()
    assert module.run_name("greedy") == ("greedy", 1)
    assert module.run_name("greedy:2") == ("greedy", 2)
    assert module.rows_path("greedy", "m24", "model", 2) == ROOT / "build" / "model-tier" / "greedy" / "m24-model-2.json"
