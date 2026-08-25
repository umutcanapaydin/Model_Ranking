"""C2b counts CONTROLS, and the count can be discharged. M12-W1, REQ-GOV-001.

V4C-13 says the third acceptance of a control sends **the control** for review, not the people.
The implementation grouped on the ledger's second column — free text naming where a finding came
from, *"M8 independent security review, MAJOR-1"* — which is unique on every row by construction.
Measured at M12-W1: **22 ACCEPTED rows, 22 distinct keys, zero triggers ever**, while K.7 had been
bypassed ten times and two records asserted that C2b had fired.

A counter that cannot count is worse than no counter, because records begin to cite it.

Two properties are pinned here and they pull against each other on purpose:

  * it must FIRE — three acceptances of one control, with nothing pointing at a review;
  * it must be DISCHARGEABLE — by doing what it asks and naming the decision that reviewed the
    control. A finding that cannot be discharged is an alarm somebody eventually silences, and the
    silencing is never recorded.

**Amended at M12-W5 on the Stage 4.0 seat's MAJOR-1, which found the rekey had not made the counter
able to count.** Two defects, opposite in direction:

  * the key was read from the PATH column, and a path does not name a control — 19 of 22 ACCEPTED
    rows had no key at all, so C2b was reading three rows and calling the other nineteen zero. It
    now reads the whole row, and `C2d` requires any acceptance from W-087 on to name its control,
    because an acceptance nobody can count is precisely the one that repeats.
  * the discharge was any `D-nnn` appearing anywhere in any counted row. W-020 mentions D-120 — the
    CLI exit-code contract, nothing to do with fresh eyes — and that incidental mention silenced
    K.7 permanently. The discharge is now the explicit token `C2b-reviewed: D-nnn @N`, and `@N`
    anchors it to the count it was written against, so a FOURTH acceptance after the review re-arms
    the trigger. **A trigger that can never fire twice is not a trigger**, and this milestone spent
    itself finding that shape elsewhere.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.check_records import warning_ledger

HEADER = "| id | rule | first seen | path | status | reason |\n|---|---|---|---|---|---|\n"
WHY = "no second seat available — milestone M9"


def _ledger(tmp_path: Path, rows: str) -> Path:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "warnings.ledger.md").write_text(HEADER + rows, encoding="utf-8")
    return tmp_path


def _rules(root: Path) -> set[str]:
    return {f.rule for f in warning_ledger(root)}


def test_three_acceptances_of_one_control_fire(tmp_path: Path) -> None:
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | some review, MINOR-{n} | m6-w{n} | K.7 / V3C-78 | ACCEPTED | {WHY} |\n"
        for n in (1, 2, 3)
    ))

    assert "C2b" in _rules(root)


def test_two_acceptances_do_not(tmp_path: Path) -> None:
    """The limit is three. A counter that fires at two is a counter people route around."""
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | some review, MINOR-{n} | m6-w{n} | K.7 / V3C-78 | ACCEPTED | {WHY} |\n"
        for n in (1, 2)
    ))

    assert "C2b" not in _rules(root)


def test_naming_the_decision_that_reviewed_the_control_discharges_it(tmp_path: Path) -> None:
    """**The half that makes this a control rather than an alarm.**

    K.7 reached three in the real ledger, the control WAS reviewed, and D-133 is the outcome. The
    rows cite it, so the trigger is satisfied — by having done the thing, not by an exemption list.
    """
    rows = "".join(
        f"| W-{n} | some review, MINOR-{n} | m6-w{n} | K.7 / V3C-78 | ACCEPTED | {WHY} |\n"
        for n in (1, 2)
    ) + (f"| W-3 | some review | m6-w3 | K.7 / V3C-78 | ACCEPTED | {WHY}; "
         "C2b-reviewed: D-133 @3 |\n")

    assert "C2b" not in _rules(_ledger(tmp_path, rows))


def test_a_loose_ADR_mention_does_not_discharge_the_trigger(tmp_path: Path) -> None:
    """Stage 4.0 MAJOR-1. Rows cite ADRs for a dozen unrelated reasons.

    The real W-020 names D-120, the CLI exit-code contract, in a row about fresh eyes — and under
    the previous rule that silenced K.7 for good. A control discharged by a coincidence was never
    reviewed; it was merely mentioned near one.
    """
    rows = "".join(
        f"| W-{n} | some review | m6-w{n} | K.7 | ACCEPTED | {WHY}; see D-120 for the exit codes |\n"
        for n in (1, 2, 3)
    )
    assert "C2b" in _rules(_ledger(tmp_path, rows))


def test_the_discharge_re_arms_when_the_control_is_accepted_again(tmp_path: Path) -> None:
    """`@N` anchors the discharge to the count it was written against.

    K.7 was reviewed at three acceptances and D-133 recorded the outcome. M12 then bypassed it four
    more times, because D-133 settled who reviews and never touched WHEN — so the fourth acceptance
    has to be heard. Without the anchor it could not be: the marker silenced the control forever,
    which is the same defect as a gate that cannot fail, wearing governance clothes.
    """
    def rows(count: int) -> str:
        body = "".join(
            f"| W-{n} | some review | m6-w{n} | K.7 | ACCEPTED | {WHY} |\n"
            for n in range(1, count)
        )
        return body + (f"| W-{count} | some review | m6-w{count} | K.7 | ACCEPTED | {WHY}; "
                       "C2b-reviewed: D-133 @3 |\n")

    assert "C2b" not in _rules(_ledger(tmp_path, rows(3))), "an anchor at its own count discharges"
    assert "C2b" in _rules(_ledger(tmp_path, rows(4))), "a fourth acceptance must re-arm"


def test_an_acceptance_that_names_no_control_is_reported_rather_than_counted_as_zero(
    tmp_path: Path,
) -> None:
    """C2d. 19 of the 22 real ACCEPTED rows named no control anywhere.

    Silence and zero are not the same measurement, and a counter that cannot tell them apart
    reports the wrong one with total confidence.
    """
    rows = f"| W-087 | some review | m12-w5 | `src/app/main.py` | ACCEPTED | {WHY} |\n"
    assert "C2d" in _rules(_ledger(tmp_path, rows))
    keyed = f"| W-087 | some review | m12-w5 | K.7 — `src/app/main.py` | ACCEPTED | {WHY} |\n"
    assert "C2d" not in _rules(_ledger(tmp_path, keyed))


def test_three_DIFFERENT_controls_do_not_fire(tmp_path: Path) -> None:
    """The defect this replaces, inverted. Grouping on something that varies per row makes the
    counter unreachable; grouping on something that is constant per row would make it fire on
    everything. Three separate controls accepted once each is not a pattern."""
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | some review | m6-w{n} | {c} | ACCEPTED | {WHY} |\n"
        for n, c in ((1, "K.7"), (2, "V3C-02"), (3, "INV-23"))
    ))

    assert "C2b" not in _rules(root)


def test_the_free_text_provenance_column_is_no_longer_the_key(tmp_path: Path) -> None:
    """The regression test for the original defect. Identical control, three DIFFERENT provenances
    — which is what every real row looks like — must still fire."""
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | {p} | m6-w{n} | K.7 | ACCEPTED | {WHY} |\n"
        for n, p in ((1, "M6 code review"), (2, "M7 tester, MAJOR-2"), (3, "M8 security, MINOR"))
    ))

    assert "C2b" in _rules(root), (
        "three acceptances of K.7 from three different reviews did not fire — the counter is "
        "keyed on provenance again, which is unique per row and therefore never reaches three"
    )


@pytest.mark.parametrize("status", ["FIXED", "ESCALATED", "OPEN"])
def test_only_ACCEPTED_rows_count(tmp_path: Path, status: str) -> None:
    """A control that was FIXED three times is not a control being bypassed."""
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | some review | current | K.7 | {status} | {WHY} |\n" for n in (1, 2, 3)
    ))

    assert "C2b" not in _rules(root)


def test_an_ADR_cited_three_times_is_not_a_control_being_bypassed(tmp_path: Path) -> None:
    """`CONTROL_ID` excludes `D-\\d+`, and this is the test that makes that exclusion real.

    It was written after a mutant that ADDED `D-\\d+` to the pattern survived the rest of this
    file. The code comment claimed the exclusion prevents over-firing; today's ledger does not
    exhibit the case, so the claim was asserted and unexercised — the exact shape the M11 council
    found a dozen times and the reason this repository keeps finding controls that were never real.

    A decision is not a control that gets bypassed. Three rows that happen to cite `D-121` in their
    context column are three rows referring to a ruling, not three acceptances of it.
    """
    root = _ledger(tmp_path, "".join(
        f"| W-{n} | some review, MINOR-{n} | m6-w{n} | `docs/decisions.md` D-121 | ACCEPTED "
        f"| {WHY} |\n"
        for n in (1, 2, 3)
    ))

    assert "C2b" not in _rules(root), (
        "C2b fired on an ADR cited three times. A decision is not a control, and counting it means "
        "the trigger goes off for rows that merely refer to a ruling"
    )
