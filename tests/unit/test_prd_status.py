"""#28 -- every requirement in docs/prd.md states where it stands, in one vocabulary.

The statuses had been written by the milestone that wrote each requirement and never moved:
"proposed", "accepted (m3-plan signed)", "SPECIFIED (m6-plan signed ...)" for a `/v1` served
since M6, "**W1.**", "DONE (M4-W2, commit ...)". So the PRD could not answer the owner's question
of what is left (2026-09-25). A status now opens with one of four words, and this test refuses
any other, so the column cannot drift back into a history log.
"""

from __future__ import annotations

import re
from pathlib import Path

PRD = Path(__file__).resolve().parents[2] / "docs" / "prd.md"
VOCABULARY = ("MET", "PARTIAL", "OPEN", "SUPERSEDED")
_OPENS = re.compile(r"^\*\*(" + "|".join(VOCABULARY) + r")\b")


def _statuses() -> list[tuple[str, int, str]]:
    """(REQ id, line, status text) for every requirement, in both of the PRD's shapes."""
    lines = PRD.read_text(encoding="utf-8").splitlines()
    found: list[tuple[str, int, str]] = []
    current: str | None = None
    for number, line in enumerate(lines, 1):
        heading = re.match(r"^###\s+(REQ-[A-Z]+-\d+[a-z]?)\b", line)
        if heading:
            current = heading.group(1)
        elif line.startswith("## ") or line.startswith("### "):
            current = None
        if current and line.startswith("**Status:**"):
            found.append((current, number, line.removeprefix("**Status:**").strip()))
            current = None
        row = re.match(r"^\|\s*(REQ-[A-Z]+-\d+[a-z]?)\s*\|", line)
        if row:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            found.append((row.group(1), number, cells[-1]))
    return found


def test_the_prd_is_read_at_all() -> None:
    """A reader that finds nothing would pass the test below vacuously."""
    assert len(_statuses()) >= 100


def test_every_requirement_opens_its_status_with_one_of_four_words() -> None:
    off = [f"{req} (line {n}): {text[:60]}" for req, n, text in _statuses() if not _OPENS.match(text)]
    assert not off, "statuses outside MET / PARTIAL / OPEN / SUPERSEDED:\n" + "\n".join(off)


def test_a_superseded_requirement_names_what_replaced_it() -> None:
    bare = [f"{req} (line {n})" for req, n, text in _statuses()
            if text.startswith("**SUPERSEDED") and not re.search(r"\bD-1\d\d\b|REQ-[A-Z]+-\d+|m\d+-plan", text)]
    assert not bare, f"superseded with no ADR, plan or requirement named: {bare}"
