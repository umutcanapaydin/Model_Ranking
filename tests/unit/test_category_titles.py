"""The titles are what a reader MEETS. REQ-CMP-003.

Renamed at M12-W2 after a 60-year-old CFO used the app. Before that, eleven milestones of titles
had been written by people who already knew what a benchmark was — `Abstract reasoning` for unseen
visual puzzles, `Expert reasoning` for PhD-level science, `Agentic coding` for a word the industry
invented last year.

The rule these tests hold is narrow on purpose, because "is this name good" is not a question a
gate can answer and pretending otherwise would be the ceremony this project's council warned about.
What a gate CAN answer:

  * no two surfaces begin with the same word — the defect that made the owner mix up two of his own
    chips, and made the lead agent mix up the same two while reading his screenshots;
  * no title carries a term whose meaning is internal to this field;
  * the ids, which are the contract, did not move while the titles did.
"""

from __future__ import annotations

import pytest

from app.workflows.categories import CATEGORIES

#: Words that only mean something to somebody already inside this industry. Each was on screen at
#: M11 and each was named by the owner or by the council's product seat.
JARGON = ("abstract", "elo", "eci", "benchmark", "inference", "token", "llm", "eval")

#: **`agentic` is deliberately absent from `JARGON`, by owner ruling.** Asked which names to
#: simplify he answered, translated from Turkish: *"Coding, Agentic Coding ok — there is no simpler
#: version of those."* The council recommended `Coding on its own`; the lead agent applied it
#: anyway, and the first-word test below caught the collision with `Coding`. The rename was
#: reverted. Recorded here rather than silently omitted, so the next person who reads this list
#: and thinks "agentic is obviously jargon" finds the ruling instead of re-litigating it.
OWNER_RULED_TITLES = {"Agentic coding"}


def test_no_two_titles_begin_with_the_same_word() -> None:
    """`Everyday assistant / chat` and `Everyday questions` were two different surfaces.

    The owner tapped the wrong one on his own screen and reported it as a routing defect. Two
    labels a reader cannot tell apart are not two labels.
    """
    firsts: dict[str, list[str]] = {}
    for spec in CATEGORIES.values():
        firsts.setdefault(spec.title.split()[0].lower(), []).append(spec.title)
    # `Agentic coding` participates: the ruling is about the WORD, not about exemption from the
    # collision rule, and it happens not to collide.

    collisions = {word: titles for word, titles in firsts.items() if len(titles) > 1}

    assert not collisions, (
        f"these titles start with the same word and will be confused: {collisions}"
    )


@pytest.mark.parametrize("surface", sorted(CATEGORIES))
def test_no_title_uses_a_word_that_only_this_industry_knows(surface: str) -> None:
    words = set(CATEGORIES[surface].title.lower().replace("/", " ").split())

    found = sorted(words & set(JARGON))

    assert not found, (
        f"`{CATEGORIES[surface].title}` uses {found}, which a reader outside this field does not "
        "have. The title should say what the surface MEASURES"
    )


def test_the_ids_are_unchanged_because_they_are_the_contract() -> None:
    """Titles are product; ids are `/v1/categories` (D-127). Renaming a title must never move one.

    Written out here rather than read from the module, for the reason the route-drift test gives:
    a set compared against itself confirms nothing.
    """
    assert set(CATEGORIES) == {
        "coding",
        "agentic-coding",
        "assistant",
        "everyday",
        "expert",
        "mathematics",
        "computer-use",
        "abstract",
        "web-dev",
        # M14-W2: two ids ADDED. An addition extends the contract a client already reads; it moves
        # nothing an existing client depends on. A rename or a removal still fails here.
        "document",
        "factuality",
        # M15-W3: three more, chosen by the W1 survey's measurement rather than by intuition.
        "vision",
        "search",
        "search_factuality",
    }


def test_every_surface_still_has_a_title_at_all() -> None:
    """Fixture blindness guard: every assertion above passes trivially on an empty string."""
    for surface, spec in CATEGORIES.items():
        assert spec.title.strip(), f"{surface} has no title"
        assert spec.title != surface, f"{surface} is showing its id as its title"
