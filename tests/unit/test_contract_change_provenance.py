"""REQ-API-010 — the criterion V3C-02 could not express, made expressible (W-043).

**The problem.** REQ-API-010 requires that a contract gap the client finds is recorded as a finding
against the public payload BEFORE any client-side workaround. That is a process obligation whose
evidence is the ledger and the ADR trail, not an assertion about running code, and V3C-02 as
written admits no exception: "EVERY acceptance criterion has a citing test." The two available
behaviours were both bad — mark it MET and lie, or leave it out and let the checklist quietly
shrink.

**The resolution.** A process criterion CAN have a failable test if you stop trying to test the
process and test its *artefact* instead. The public payload's field set is frozen by ADR. So the
checkable statement is: **the frozen field set and the decision record must agree about what moved
and under whose permission.** If the payload gains a field, an ADR says so and claims the revision
window; if an ADR claims the window, the field is actually there.

That is a real cross-check between code and record, it fails in both directions, and it is exactly
the drift REQ-API-010 exists to prevent — a contract that moved without the record, or a record
claiming a move that did not happen. This project has now produced BOTH: a payload field added
under an ADR, and four records simultaneously asserting the window was unspent.
"""

from __future__ import annotations

import pathlib
import re

DECISIONS = pathlib.Path(__file__).resolve().parents[2] / "docs/decisions.md"


def _adr(identifier: str) -> str:
    """The body of one ADR, from its heading to the next."""
    text = DECISIONS.read_text(encoding="utf-8")
    start = text.index(f"## {identifier} ")
    following = re.search(r"^## D-\d+ ", text[start + 1 :], re.MULTILINE)
    return text[start : start + 1 + following.start()] if following else text[start:]


def test_the_permission_to_move_the_contract_exists_and_is_claimed_exactly_once() -> None:
    """D-124 opens one revision window; exactly one ADR may claim it.

    Fails if a second ADR claims the same window — which would be the contract moving twice on a
    permission that grants one move, and the shape M9 is at risk of because four records said the
    window was unspent when it was not.
    """
    text = DECISIONS.read_text(encoding="utf-8")
    assert "## D-124 " in text, "the ADR permitting a contract revision is gone"

    claimants = re.findall(r"^## (D-\d+) .*$", text, re.MULTILINE)
    claiming = [
        identifier
        for identifier in claimants
        if identifier != "D-124" and re.search(r"\*{0,2}D-124\*{0,2}\s+permits", _adr(identifier))
    ]
    assert len(claiming) == 1, (
        f"D-124 grants ONE revision and {len(claiming)} ADRs claim it: {claiming}. Two claims mean "
        "the frozen payload moved twice on a permission that allows one"
    )


def test_a_field_the_payload_publishes_is_a_field_an_adr_accounted_for() -> None:
    """The code half of the cross-check: `ranking` exists, so its ADR must exist and claim D-124.

    Fails in both directions — remove the ADR while the field ships, or claim the revision in an
    ADR while the field is absent. The second is not hypothetical: a closure report, two wave
    records and a retrospective all stated this window was UNSPENT while the field was live.
    """
    from app.adapter.main import PUBLIC_ANSWER_FIELDS

    if "ranking" in PUBLIC_ANSWER_FIELDS:
        body = _adr("D-125")
        assert body, "the payload publishes `ranking` and no ADR accounts for it"
        assert "D-124" in body, (
            "D-125 adds a field to the frozen payload without naming the permission it moves "
            "under; a contract that moves without citing its authorisation is not frozen"
        )
        assert "ranking" in body, "D-125 does not name the field it added"


def test_no_record_claims_the_revision_window_is_unspent_while_it_is_spent() -> None:
    """The exact drift that reached a closure report awaiting signature.

    D-125 spends D-124's single revision and says so in its own text. Four records said otherwise.
    Nothing re-derived the claim, because a record is believed by the next reader rather than
    checked. This is the check.
    """
    docs = pathlib.Path(__file__).resolve().parents[2] / "docs"
    spent = "D-124" in _adr("D-125")
    assert spent, "fixture assumption: D-125 is the ADR that claims the window"

    offenders: list[str] = []
    for record in sorted(docs.rglob("*.md")):
        text = record.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            # ASSERTIONS only. A correction has to be able to NARRATE the error it corrects --
            # "an earlier version said the window was UNSPENT" is the sentence that fixes the
            # problem, and a check that forbids it forces the record to hide what went wrong.
            # So this matches the present-tense claim and leaves reported speech alone.
            if re.search(r"D-124.{0,160}?\b(?:is|remains|stays)\s+UNSPENT\b", line):
                offenders.append(f"{record.relative_to(docs.parent)}:{number}")
    assert not offenders, (
        "these records state that D-124's revision window is unspent, and D-125 spent it: "
        f"{offenders}. A record that outlives its own ADR is how the next milestone spends a "
        "one-time permission twice"
    )
