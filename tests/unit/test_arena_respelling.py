"""#415 (D-220 clause 1): LMArena re-spelled every model on 2026-10-13, from slugs
(`claude-3-5-sonnet-20240620`) to display names (`Claude 3.5 Sonnet (20240620)`).

The text grammar refused a name with a parenthesis, so a model whose slug resolved (a curated rule or
a derived id) arrived unlinked under its new spelling, and left every surface it was on. The fixture is
every such pair recorded from the dataset's 2026-10-22 file: the new spelling must resolve exactly as
the old one did. A trailing effort parenthesis (`GPT-6 Astra (Max)`) is #38's reading and is left out
of the fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.workflows.registry import canonicalize, derive_identity

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "arena_respelling" / "text-2026-10-22.json"
PAIRS = [(pair["was"], pair["now"]) for pair in json.loads(FIXTURE.read_text(encoding="utf-8"))["pairs"]]


def _resolution(name: str) -> tuple[str, str | None, str | None]:
    """What the reconcile links a name to: a curated rule's id, else the grammar's derived id."""
    rule = canonicalize(name)
    if rule is not None:
        return ("rule", rule.canonical_id, None)
    derived = derive_identity(name)
    return ("derived", derived.model_id if derived else None, derived.effort if derived else None)


def test_the_fixture_holds_the_recorded_pairs() -> None:
    """Fails closed: an emptied fixture would pass the test below vacuously."""
    assert len(PAIRS) == 104
    assert ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet (20240620)") in PAIRS


@pytest.mark.parametrize(("was", "now"), PAIRS, ids=[now for _, now in PAIRS])
def test_a_bracketed_display_name_resolves_as_its_slug_did(was: str, now: str) -> None:
    assert _resolution(now) == _resolution(was)


@pytest.mark.parametrize(("name", "expected"), [
    ("Claude 3.5 Sonnet (20241022)", "claude3.5-sonnet20241022"),
    ("GPT-4o mini (2024-07-18)", "gpt4o-mini2024-07-18"),
    ("Grok 4.20 Multi-Agent Beta (0309)", "grok4.20-multi-agent-beta0309"),
    ("Qwen3-235B-A22B-Instruct (2507)", "qwen3-235b-a22b-instruct2507"),
])
def test_the_measured_lost_links_come_back(name: str, expected: str) -> None:
    """Four of the 31 `arena` rows the 2026-10-22 candidate unlinked (the #415 diagnosis)."""
    assert _resolution(name)[1] == expected


def test_a_curated_rule_matches_the_bracketed_spelling_of_its_alias() -> None:
    """`mistral-large-2411` is a curated alias; its display name reaches the same rule."""
    slug, display = canonicalize("mistral-large-2411"), canonicalize("Mistral Large (2411)")
    assert slug is not None and display is not None
    assert display.canonical_id == slug.canonical_id


@pytest.mark.parametrize(("name", "model_id", "effort"), [
    ("GPT 6 Astra (Max)", "gpt6-astra", "max"),       # #38: a trailing effort parenthesis is still the run's effort
    ("gpt-5 (high)", "gpt5", "high"),
    ("gpt-6-astra_high", "gpt6-astra", "high"),        # a name that resolved before is read exactly as before
    ("deepseek-v3.2-exp", "deepseek-v3.2-exp", None),
])
def test_a_name_that_resolved_before_resolves_as_before(name: str, model_id: str, effort: str | None) -> None:
    """The bracket reading applies only to a name the grammar refused; nothing that resolved moves. Pinned to the
    id and effort, not only "derives" (the #416 delta Tester's M2: three faults stayed green on the weaker form)."""
    derived = derive_identity(name)
    assert derived is not None
    assert (derived.model_id, derived.effort) == (model_id, effort)


@pytest.mark.parametrize("name", ["x (" + " " * 20_000 + "y", "x" + " " * 20_000 + "(y)"],
                         ids=["unclosed-after-a-run", "a-run-before-the-bracket"])
def test_the_bracket_reading_is_linear_on_a_long_whitespace_run(name: str) -> None:
    """#417 (the #416 security delta's M1): `\\s*\\(` retried at every start in a whitespace run, so a 20k-space
    name took a second in `canonicalize_with_reason`; an upstream file of such names could stall the night."""
    import time

    from app.workflows.registry import canonicalize_with_reason

    started = time.perf_counter()
    canonicalize_with_reason(name)
    derive_identity(name)
    assert time.perf_counter() - started < 0.25


def test_a_moving_alias_in_brackets_still_derives_nothing() -> None:
    """D-166: an undated alias names no one release, however it is spelled."""
    assert derive_identity("o1-mini") is None
    assert derive_identity("Command R (latest)") is None


@pytest.mark.parametrize("name", [
    "Claude 3.5 Sonnet (20241022) (high)",
    "GPT 5 (2025-08-07) (medium)",
])
def test_a_trailing_effort_never_becomes_part_of_a_bracket_read_id(name: str) -> None:
    """D-220 clause 2 beside #38: a name whose last parenthesis is a run's effort is not read as dash
    tokens, so the effort never lands in a model id (`gpt5-2025-08-07-medium`). Found by the release
    Tester's fault injection: without the effort exemption, the suite stayed green."""
    effort = name.rsplit("(", 1)[1].rstrip(")")
    derived = derive_identity(name)
    assert derived is None or (derived.effort == effort and effort not in derived.model_id), derived
