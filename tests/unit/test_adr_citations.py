"""Every ADR cited in this repository exists. M12-W1, REQ-GOV-001.

**D-120 was cited in 26 files and never written.** `src/app/workflows/build.py` calls it
"`schema.py`'s frozen D-120 contract"; `tests/unit/test_roster_window.py` calls it "a K.8 frozen
contract, so the SET is pinned"; the M10 and M11 plans both list it among the surfaces this project
promises not to move. `docs/decisions.md` went D-118 → D-121. **The most-deferred-to contract in
the repository had no record**, and eleven milestones of review never noticed, because every
citation was locally plausible and nobody crossed from the citation to the definition.

D-119 was the same, cited in four files, with `docs/closure-report-m6.md` stating in as many words
that it had been *"written at closure"*.

That is the shape the M11 council named — a thing asserted somewhere and exercised nowhere, each
half locally correct — and it is the reason this file exists rather than a note in a record. A rule
that is only prose is a rule that gets re-broken.

**The measurement that shaped this test:** the council seat that found it also reported P-002 and
P-003 as phantoms, citing 7 and 5 files. They are neither. `docs/decisions.md` explains them as
reserved mirrors of D-006 and D-007, and every one of those "citations" was the substring `P-002`
inside `REQ-APP-002`. So this test matches on WORD BOUNDARIES, and a naive grep would have had it
failing on requirement ids from the day it shipped.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = ROOT / "docs" / "decisions.md"

#: Ids that are deliberately RESERVED rather than written, with the reason stated in the decision
#: log itself. `P-001` reserves the `D-001..D-099` band and pins `P-002`/`P-003` as mirrors of
#: D-006/D-007. A reserved id is not a phantom; it is a decision about numbering.
RESERVED = {"P-002", "P-003"}

#: **This gate owns the PROJECT band only.** `P-001` reserves `D-001..D-099` for the pipeline's own
#: decisions, and this repository inherits them rather than authoring them: `docs/onboarding.md`
#: and `scripts/bootstrap-check.sh` are GP-owned files citing GP-owned ADRs, and `decisions.md`
#: here carries only the universal set `D-001..D-005` that `bootstrap-check` C4 requires.
#:
#: Written after the first run failed on D-008, D-013, D-019, D-021, D-025 and D-026. Every one is
#: a real citation and NONE is this project's to write, so failing on them would be a gate that
#: cannot be satisfied by anyone who can act on it — which is how a gate gets switched off.
#: Narrowing the scope is the fix; pretending they are fine is not, so they are named here.
def _owned(adr: str) -> bool:
    """Is this an id THIS repository is responsible for defining?"""
    band, number = adr.split("-")
    return band == "P" or int(number) >= 100

#: Scanned for citations. Deliberately NOT the whole tree: `.git` and the venv contain other
#: projects' identifiers, and a gate that fails on somebody else's ADR is a gate that gets deleted.
SCANNED = ("docs", "src", "tests", "scripts", "subagent-profiles")


def _defined() -> set[str]:
    text = DECISIONS.read_text(encoding="utf-8")
    return set(re.findall(r"^##\s+((?:D|P)-\d{3})\b", text, re.M))


def _cited() -> dict[str, set[str]]:
    """id -> the files citing it. Word-boundaried, so `REQ-APP-002` is not a citation of `P-002`."""
    pattern = re.compile(r"(?<![A-Za-z0-9-])((?:D|P)-\d{3})(?![0-9])")
    out: dict[str, set[str]] = {}
    for top in SCANNED:
        for path in sorted((ROOT / top).rglob("*")):
            if path.suffix not in {".md", ".py", ".sh", ".swift"} or not path.is_file():
                continue
            if path.resolve() == DECISIONS.resolve():
                continue
            for found in pattern.findall(path.read_text(encoding="utf-8", errors="replace")):
                out.setdefault(found, set()).add(str(path.relative_to(ROOT)))
    return out


def test_every_cited_adr_exists() -> None:
    """The citing test for REQ-GOV-001, and it was RED when it was written."""
    defined, cited = _defined(), _cited()

    phantom = {
        adr: sorted(files)
        for adr, files in cited.items()
        if adr not in defined and adr not in RESERVED and _owned(adr)
    }

    assert not phantom, (
        "these ADRs are cited but were never written — a contract nobody can read is a contract "
        f"nobody agreed to: { {k: ([*v[:4], '…'] if len(v) > 4 else v) for k, v in phantom.items()} }"
    )


def test_the_reserved_ids_are_still_reserved_and_still_explained() -> None:
    """`RESERVED` is an exemption, and an exemption nobody re-checks becomes a hole.

    If `decisions.md` stops explaining why P-002 and P-003 have no section of their own, they stop
    being reserved and become exactly the defect this file exists to catch.
    """
    text = DECISIONS.read_text(encoding="utf-8")

    for adr in sorted(RESERVED):
        assert adr in text, (
            f"{adr} is exempted here as a reserved mirror, and `docs/decisions.md` no longer "
            "mentions it. Either write it or stop reserving it"
        )
    assert "reserved mirrors" in text, (
        "the sentence that makes RESERVED legitimate has gone from the decision log"
    )


def test_the_numbering_has_no_silent_gaps_in_the_project_band() -> None:
    """A gap is not automatically wrong — but an UNEXPLAINED one is how D-119 and D-120 hid.

    Every missing number in the project band must be accounted for: written, or named somewhere in
    the decision log as deliberately skipped.
    """
    defined = _defined()
    project = sorted(int(a.split("-")[1]) for a in defined if a.startswith("D-1"))
    text = DECISIONS.read_text(encoding="utf-8")

    unexplained = [
        f"D-{n}"
        for n in range(project[0], project[-1] + 1)
        if f"D-{n}" not in defined and f"D-{n}" not in text
    ]

    assert not unexplained, (
        f"the project ADR band skips {unexplained} with no mention anywhere in the decision log. "
        "That is how D-119 and D-120 stayed invisible while 26 files deferred to them"
    )
