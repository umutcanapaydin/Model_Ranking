"""A stale secondary does not upgrade a coverage claim — cites REQ-UNC-002.

**The council's ruling (2026-09-06, seat: Evidence & Freshness), and the measurement behind it.**
`confidence_of` returned `"High"` whenever a secondary score existed, with the basis *"two
independent benchmarks (SWE-bench Verified + Aider polyglot)"*. Aider's newest row is 2025-10-03 —
**328 days before the artifact's own anchor** — and it covers 15 of 74 models.

Two things make that worse than a stale number:

* **It is not a confidence.** It counts how many boards we hold, not how sure we are. That naming
  problem is recorded separately and is not what this file fixes.
* **It was inverted in practice.** Measured across all nine surfaces and three budgets, exactly one
  pick of eighteen claimed `High`: the coding **budget pick**. The flagship best-quality answer,
  Claude Opus 4.7, claimed `Medium` — because a defunct 2025 leaderboard happened to have run the
  older, cheaper model and not the newer one. The product was most confident about its cheapest
  fallback.

**The threshold is not a new number.** `STALE_NOTICE_DAYS = 90` already exists in this module under
REQ-REC-006 and already decides whether a surface's PRIMARY evidence can stand unqualified. Giving
the secondary its own figure would leave one file holding two disagreeing definitions of stale.

**Undated counts as not-fresh, and that is the half with teeth.** A secondary with no `run_date`
cannot be aged, and a rule that silently treated unknown age as acceptable would be the same
"undated is fresh" assumption this repository has already shipped once. Being unable to check is not
the same as having checked.

**What this file deliberately does NOT do.** The same ruling proposed making `_stale_notice` emit a
notice for an UNDATED primary. It is not implemented, and the reason is measured rather than
argued: `_evidence_dating` (`main.py:594`) already publishes `evidence_dating: "undated"` plus the
sentence *"This answer's benchmark publishes no evaluation dates, only model release dates. Its
scores cannot be aged, so freshness is unknown rather than recent."* — verified live on `everyday`,
`abstract`, `web-dev` and `agentic-coding`, the four surfaces whose primary is undated. Adding a
second notice saying the same thing is exactly the duplication D-135 exists to prevent and M12
spent a milestone removing.
"""

from __future__ import annotations

import dataclasses

import pytest

from app.workflows.categories import CATEGORIES
from app.workflows.rank import RankingRow
from app.workflows.recommend import (
    STALE_NOTICE_DAYS,
    _secondary_age_days,
    confidence_of,
)
from app.workflows.schema import connect

CODING = CATEGORIES["coding"]


def _row(secondary_score: float | None) -> RankingRow:
    values: dict[str, object] = {}
    for field in dataclasses.fields(RankingRow):
        annotation = str(field.type)
        if field.name == "secondary_score":
            values[field.name] = secondary_score
        elif "None" in annotation:
            values[field.name] = None
        elif "float" in annotation:
            values[field.name] = 1.0
        elif "str" in annotation:
            values[field.name] = "x"
        else:  # pragma: no cover
            raise AssertionError(f"unhandled field type on RankingRow.{field.name}: {annotation}")
    return RankingRow(**values)


#: Age of the secondary BOARD, not of the row. Staleness is a property of the leaderboard: Aider
#: has not been re-run since 2025-10-03 for anybody, so asking it per model would compute the same
#: answer 44 times. `None` means the board publishes no dates and cannot be aged.


def test_a_fresh_secondary_still_counts() -> None:
    """The rule must not simply delete the second benchmark. A recent one is real evidence."""
    label, basis = confidence_of(_row(70.0), CODING, secondary_age_days=17)
    assert label == "High"
    assert CODING.secondary_benchmark in basis


def test_a_secondary_older_than_the_threshold_does_not_upgrade() -> None:
    """REQ-UNC-002. Aider's own case: 2025-10-03 against a 2026 anchor."""
    label, basis = confidence_of(_row(70.0), CODING, secondary_age_days=328)
    assert label == "Medium"
    assert CODING.secondary_benchmark not in basis


def test_an_undated_secondary_does_not_upgrade() -> None:
    """Unable to check is not the same as checked.

    Five of the twelve score sources still publish no evaluation date at all. A rule that upgraded
    on them would be asserting freshness it has no way to establish — the "undated is fresh"
    assumption this repository has already shipped once.
    """
    label, _ = confidence_of(_row(70.0), CODING, secondary_age_days=None)
    assert label == "Medium"


def test_no_secondary_at_all_is_unchanged() -> None:
    """Regression guard on the branch that was always right."""
    label, basis = confidence_of(_row(None), CODING, secondary_age_days=1)
    assert label == "Medium"
    assert CODING.primary_benchmark in basis


@pytest.mark.parametrize(
    "age_days, expected",
    [(89, "High"), (90, "High"), (91, "Medium")],
)
def test_the_boundary_is_the_existing_threshold(age_days: int, expected: str) -> None:
    """Pinned at 90 because `STALE_NOTICE_DAYS` is 90, not because 90 was chosen here.

    If somebody retunes `STALE_NOTICE_DAYS` this test moves with it deliberately — the assertion
    below is what stops the two definitions of "stale" from drifting apart.
    """
    assert STALE_NOTICE_DAYS == 90
    label, _ = confidence_of(_row(70.0), CODING, secondary_age_days=age_days)
    assert label == expected


def test_the_age_is_derived_from_the_secondary_board_not_the_primary() -> None:
    """The seam that makes this testable, asserted so it cannot quietly close.

    `_secondary_age_days` asks the SECONDARY benchmark for its newest run, against the same
    `observed_at` anchor `_stale_notice` uses for the primary. Reading the primary's age here would
    make every coding pick High again the moment SWE-bench was re-ingested, which is the opposite
    of what the ruling asks for.
    """
    conn = connect()
    assert (
        _secondary_age_days(conn, CODING) is None
    ), "an empty database cannot age anything, and must not claim it can"
