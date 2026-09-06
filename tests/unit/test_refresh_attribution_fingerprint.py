"""The refresh fingerprint covers attribution — cites REQ-FIX-003, REQ-LIC-001.

**The reasoning that produced this defect is written down in the code, which is what makes it worth
a file of its own.** `UNHASHED_ROW_FIELDS` carried this justification:

    MEASURED, not guessed: these two are the only fields of a ranked row that appear in neither
    `PUBLIC_RANKING_FIELDS` nor `PUBLIC_PICK_FIELDS`, so no reader can see them on any surface

Every clause of that is true, and the conclusion is still wrong. `evidence_source` is not a field a
reader sees. It is the field the citations are DERIVED from: `rank.attributions_for` maps each
`scores.source` through `SOURCE_ATTRIBUTION` to produce the `sources` list, and `sources` IS in
`PUBLIC_ANSWER_FIELDS`. So the test applied — "is this field in the payload?" — was one question too
shallow. The right question is whether anything a reader sees is a function of it.

The consequence: an artifact whose evidence moved from one board to another produced an identical
`_row_digest`, D-128 saw no change, and the refresh did not publish — while the citation on screen
went on naming a source the answer no longer came from. Under REQ-LIC-001 a CC-BY citation is a
licence obligation that travels with every export, so a stale one is not a display detail.

`secondary_cost` stays unhashed and that is checked below, because a fix that swept both fields in
would be trading a real defect for a fingerprint that churns on something nobody can see.
"""

from __future__ import annotations

import dataclasses

from app.workflows.rank import RankingRow, attributions_for
from app.workflows.refresh import UNHASHED_ROW_FIELDS, _row_digest


def _row(**overrides: object) -> RankingRow:
    """A `RankingRow` built by reflection, so a new field cannot silently escape these tests."""
    values: dict[str, object] = {}
    for field in dataclasses.fields(RankingRow):
        annotation = str(field.type)
        if field.name in overrides:
            values[field.name] = overrides[field.name]
        elif "None" in annotation:
            values[field.name] = None
        elif "float" in annotation:
            values[field.name] = 1.0
        elif "str" in annotation:
            values[field.name] = "x"
        else:  # pragma: no cover
            raise AssertionError(f"unhandled field type on RankingRow.{field.name}: {annotation}")
    return RankingRow(**values)


def test_two_sources_owe_different_citations() -> None:
    """The premise, asserted first: this only matters because the reader's text changes.

    If both sources produced the same citation the fingerprint would be right to ignore the field,
    so the defect is established here rather than assumed.
    """
    arena = attributions_for(["arena"], priced=True)
    swebench = attributions_for(["swebench"], priced=True)
    assert arena != swebench


def test_a_changed_evidence_source_changes_the_digest() -> None:
    """REQ-FIX-003. Before the fix these two digests were byte-identical."""
    before = _row(model="m", evidence_source="arena")
    after = _row(model="m", evidence_source="swebench")
    assert _row_digest(before) != _row_digest(after)


def test_evidence_source_is_not_excluded_from_the_fingerprint() -> None:
    """Pin the CLAIM, not the offset.

    The behavioural test above would also pass if somebody re-added the exclusion and changed an
    unrelated field. This asserts the decision itself, which is the thing a future edit would
    reverse.
    """
    assert "evidence_source" not in UNHASHED_ROW_FIELDS


def test_secondary_cost_stays_out_of_the_fingerprint() -> None:
    """The other half of the exclusion list, and the reason the fix is one field and not two.

    `secondary_cost` is read from the artifact and rendered nowhere — no payload field is derived
    from it. Hashing it would make the refresh publish on a movement no reader can perceive, which
    is exactly the churn `UNHASHED_ROW_FIELDS` exists to prevent.
    """
    assert "secondary_cost" in UNHASHED_ROW_FIELDS
    before = _row(model="m", secondary_cost=1.0)
    after = _row(model="m", secondary_cost=99.0)
    assert _row_digest(before) == _row_digest(after)
