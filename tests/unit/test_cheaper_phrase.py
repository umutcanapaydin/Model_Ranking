"""How much cheaper, said in a way that cannot claim a saving that is not there. M12-W2.

`f"{ratio:.0f}x cheaper"` shipped for eleven milestones. For every ratio under 1.5 it rounds to
**"1x cheaper"**, which tells a reader they give up points and save nothing — the opposite of the
trade-off the sentence exists to describe. Found by the M11 council.

**Rewritten at M12-W5 (Stage 4.0 MAJOR-5), and the rewrite is the point.**

These nine assertions were written against `cheaper_phrase`, which W2 added and **nothing ever
called**. W4 then wrote a second implementation of the same rule — `trade_off_facts` +
`trade_off_sentence` — and wired THAT one into the answer. So the rule shipped twice: once tested
and dead, once live and covered only by its own newer tests. Nine green tests stood beside a
function the product could not reach, and they would have gone on passing after the live rule
drifted, because the thing they measured was not the thing that runs. V3C-73: an implemented,
unit-green control that is not on the live request path is an unshipped control.

`cheaper_phrase` is now DELETED and every assertion below goes through the shipping composer. Where
the two disagreed, the live one is the contract, because it is the one the reader sees.

The header used to add: *"NOT visible on today's data, where every ratio is 3x or more, which is
why it has tests rather than a fix."* **That was false when it was written.** The M12 starting tree,
against the shipped `advisor.db`, served `task=computer-use&budget=low` a `budget_pick` reading
`2.7 points below the leader, but 1x cheaper.` — `best_quality` at `0.98`, `budget_pick` at `0.69`,
a ratio of `1.4203`. It was on a live surface on the day the sentence was written. The fix was real;
the reasoning recorded beside it was an assumption nobody measured, and an assumption is exactly
what a nine-test substitute for a fix rests on.
"""

from __future__ import annotations

import pytest

from app.workflows.recommend import trade_off_facts, trade_off_sentence


def cheaper_phrase(dearer: float, cheaper: float) -> str:
    """The clause the reader actually gets, taken off the SHIPPING path.

    Not a reimplementation: it calls the same two functions the answer calls, and
    returns the part of the sentence these tests are about. If the live rule
    changes, these nine fail — which is what they were supposed to do all along.
    """
    fact = trade_off_facts(10.0, 10.0, "points", dearer, cheaper)
    return trade_off_sentence(fact).split("leader, ", 1)[-1]



def test_a_small_saving_is_a_percentage_not_a_rounded_multiple() -> None:
    """The defect itself. 1.42x rounds to `1x cheaper`: give up quality, save nothing."""
    phrase = cheaper_phrase(1.42, 1.0)

    assert "1x cheaper" not in phrase, f"the reader is told they save nothing: {phrase}"
    assert "30%" in phrase


def test_a_large_saving_stays_a_multiple_because_that_is_how_people_say_it() -> None:
    assert cheaper_phrase(36.09, 0.31) == "but 116x cheaper."
    assert cheaper_phrase(10.0, 3.0) == "but 3x cheaper."


def test_the_boundary_between_the_two_forms_is_exercised_from_both_sides() -> None:
    """The fixture reaches the threshold, which is the one thing this project's threshold tests
    have most often failed to do (M11 council, tester seat: 22% kill rate on calibrations)."""
    assert "%" in cheaper_phrase(1.99, 1.0), "just below 2x must read as a percentage"
    assert "x cheaper" in cheaper_phrase(2.01, 1.0), "just above 2x must read as a multiple"


def test_two_models_at_the_same_price_report_no_saving_at_all() -> None:
    """`0% cheaper` is not a small saving, it is a sentence that should not exist — and it is
    reachable: nothing stops two models sharing a price, and pairs do in the shipped artifact."""
    assert cheaper_phrase(5.0, 5.0) == "at the same price."


@pytest.mark.parametrize("dearer,cheaper", [(1.0, 0.0), (0.0, 1.0), (0.0, 0.0), (-1.0, 1.0)])
def test_a_free_or_impossible_price_does_not_divide_by_zero(dearer: float, cheaper: float) -> None:
    """A free model is not a defect and must not crash the sentence that describes it."""
    phrase = cheaper_phrase(dearer, cheaper)

    assert phrase and phrase.endswith("."), f"got: {phrase!r}"
    assert "inf" not in phrase.lower() and "nan" not in phrase.lower()


def test_the_phrase_is_a_clause_the_caller_can_join_onto_its_sentence() -> None:
    """Fixture blindness guard: every assertion above would pass on a function returning a bare
    number, which would then read as `"5.9 points below the leader, 3"`."""
    for phrase in (cheaper_phrase(10.0, 3.0), cheaper_phrase(1.42, 1.0), cheaper_phrase(5.0, 5.0)):
        assert phrase[0].islower() or phrase.startswith("at "), phrase
        assert phrase.endswith("."), phrase
