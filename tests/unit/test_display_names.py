"""#112 (M18-W7): the names a reader sees are product names, in their maker's word order.

On the 2026-10-04 artifact 28 of 315 models were served under their raw id (`mimo-v2.6-flash`,
`o3-2025-04-16`), and Claude names came in two word orders ("Claude 4.5 Opus" beside "Claude Opus
4.6"). Anthropic names its models "Claude 3.5 Sonnet" up to version 3.7 and "Claude Opus 4.5" from
version 4 on, so that is the rule. `/v1` changes no field; only `models.display` values move.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from app.workflows import registry

ARTIFACT = Path("advisor.db")

#: The ids served under their raw id on the 2026-10-04 artifact (`select id from models where
#: display = id`, plus the six dated Claude ids served under a board's raw spelling).
RAW_ON_2026_10_04 = {
    "dbrx-instruct", "mimo-v2-flash", "mimo-v2-omni", "mimo-v2-pro", "mimo-v2.5", "mimo-v2.6-flash",
    "mimo-v2.6-pro", "minimax-m1", "nova-lite", "nova-micro", "nova-pro", "o1-2024-12-17", "o1-preview",
    "o3", "o3-2025-04-16", "o3-mini", "o3-mini-high", "o3-pro", "o4-mini", "qwen2-72b-instruct",
    "qwen2.5-14b-instruct", "qwen2.5-32b-instruct", "qwen2.5-72b-instruct", "qwen2.5-7b-instruct",
    "qwen3-4b", "qwen3.5-122b-a10b", "qwq-plus", "trinity-large-thinking", "claude3.5-haiku20241022",
    "claude3.5-sonnet20240620", "claude3.5-sonnet20241022", "claude3-haiku20240307",
    "claude3-opus20240229", "claude3-sonnet20240229",
}
#: Ids that ARE their product name: OpenAI writes its reasoning models in lower case, as their ids.
SPELLED_AS_THEIR_ID = {"o1-preview", "o3", "o3-mini", "o3-pro", "o4-mini"}
#: Ids of 2026-10-04 that are no longer models: each is another model's score now.
NO_LONGER_MODELS = {
    "o3-mini-high",  # #130: o3-mini at high effort
    # #129: each dated id is its release's only snapshot, one model with the undated one
    "claude3-haiku20240307", "claude3-opus20240229", "claude3-sonnet20240229", "claude3.5-haiku20241022",
    "o3-2025-04-16", "gpt5-2025-08-07",
}

CLAUDE = re.compile(r"Claude (?:(?P<old>\d(?:\.\d)?) (?:Opus|Sonnet|Haiku)|(?:Opus|Sonnet|Haiku) (?P<new>\d(?:\.\d)?))\b")


def _claude_order_problem(display: str) -> str | None:
    match = CLAUDE.match(display)
    if not match:
        return None
    version = float(match.group("old") or match.group("new"))
    if version >= 4 and match.group("old"):
        return f"{display!r}: from Claude 4 on the tier comes first ('Claude Opus 4.5')"
    if version < 4 and match.group("new"):
        return f"{display!r}: before Claude 4 the version comes first ('Claude 3.5 Sonnet')"
    return None


def test_every_claude_name_is_in_anthropics_word_order() -> None:
    names = [rule.display for rule in registry.MODEL_RULES] + list(registry.DISPLAY_NAMES.values())
    assert sum(1 for name in names if name.startswith("Claude")) >= 10, "no Claude names were read"
    problems = [p for name in names if (p := _claude_order_problem(name))]
    assert not problems, problems


def test_the_word_order_check_fails_on_the_old_spellings() -> None:
    assert _claude_order_problem("Claude 4.5 Opus")
    assert _claude_order_problem("Claude Sonnet 3.5")
    assert not _claude_order_problem("Claude Opus 4.6")
    assert not _claude_order_problem("Claude 3.7 Sonnet")


def test_no_model_served_under_its_raw_id_is_left_without_a_name() -> None:
    named = set(registry.DISPLAY_NAMES) | SPELLED_AS_THEIR_ID | NO_LONGER_MODELS
    assert RAW_ON_2026_10_04 - named == set(), sorted(RAW_ON_2026_10_04 - named)


def test_each_name_in_the_table_is_a_bounded_spelling_and_wins_for_its_model() -> None:
    """A table name reaches `/v1` like any display, so it keeps D-157's bound (M16 MAJOR-1)."""
    for model_id, name in registry.DISPLAY_NAMES.items():
        assert name != model_id, model_id
        assert registry._DISPLAY.fullmatch(name), name
        assert registry._derived_display(model_id, [model_id]) == name, model_id


def test_a_board_spelling_in_the_other_order_is_turned_round() -> None:
    """The W7 review's M4: the rule held the curated names only; a derived Claude kept whatever word
    order its board wrote."""
    assert registry._derived_display("claude4.9-opus", ["Claude 4.9 Opus"]) == "Claude Opus 4.9"
    assert registry.claude_word_order("Claude Sonnet 3.5") == "Claude 3.5 Sonnet"
    assert registry.claude_word_order("Claude Fable 5") == "Claude Fable 5"
    assert registry.claude_word_order("Claude Opus 4.5 (20251101)") == "Claude Opus 4.5 (20251101)"


@pytest.mark.artifact
def test_every_model_the_artifact_serves_is_named_by_this_code_as_a_product() -> None:
    """The plan's check for #112, over the served names: every model in the artifact, named the way
    this code would name it, from the names its own rows carry. An approximation of the build, which
    names a derived model from each score's PARSED name (the W7 Tester's T4: 20 of 200 derived names
    differ); its two checks, no raw id and Anthropic's order, hold on either input. None reads as its
    raw id, but OpenAI's, and every Claude is in Anthropic's order (the review's M4, and its R1: a new
    model served under its raw id shows here)."""
    conn = sqlite3.connect(f"file:{ARTIFACT}?mode=ro", uri=True)
    curated = {rule.canonical_id: rule.display for rule in registry.MODEL_RULES}
    raw_ids, misordered = [], []
    for (model_id,) in conn.execute("SELECT id FROM models"):
        if model_id in NO_LONGER_MODELS:  # an artifact built before its fix holds it until the next build
            continue
        names = [n for (n,) in conn.execute(
            "SELECT raw_name FROM scores WHERE model_id = ? UNION SELECT alias FROM pricing WHERE model_id = ?",
            (model_id, model_id))]
        name = curated.get(model_id) or registry._derived_display(model_id, names)
        if name == model_id and model_id not in SPELLED_AS_THEIR_ID:
            raw_ids.append(model_id)
        if problem := _claude_order_problem(name):
            misordered.append(problem)
    assert not raw_ids, f"served under their raw id: {sorted(raw_ids)}"
    assert not misordered, misordered


def test_claude_4_is_the_edge_and_the_rest_of_a_name_stays() -> None:
    """Tester (M18-W7), #112: the turn's edges. Claude 4 itself is tier first, a Haiku turns like an
    Opus, and what follows the version (a date, a mode) stays with the name. With the edge moved
    either way, Haiku left out, or the rest of the name dropped, every earlier test passed."""
    turn = registry.claude_word_order
    assert turn("Claude 4 Opus") == "Claude Opus 4"
    assert turn("Claude Opus 4") == "Claude Opus 4"
    assert turn("Claude 4.9 Haiku") == "Claude Haiku 4.9"
    assert turn("Claude Haiku 3.5") == "Claude 3.5 Haiku"
    assert turn("Claude 4.9 Opus (thinking)") == "Claude Opus 4.9 (thinking)"
    assert turn("Claude Sonnet 3.7 (2025-02-19)") == "Claude 3.7 Sonnet (2025-02-19)"
