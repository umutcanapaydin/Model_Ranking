"""#112 (M18-W7): the names a reader sees are product names, in their maker's word order.

On the 2026-10-04 artifact 28 of 315 models were served under their raw id (`mimo-v2.6-flash`,
`o3-2025-04-16`), and Claude names came in two word orders ("Claude 4.5 Opus" beside "Claude Opus
4.6"). Anthropic names its models "Claude 3.5 Sonnet" up to version 3.7 and "Claude Opus 4.5" from
version 4 on, so that is the rule. `/v1` changes no field; only `models.display` values move.
"""

from __future__ import annotations

import re

from app.workflows import registry

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
SPELLED_AS_THEIR_ID = {"o1-preview", "o3", "o3-mini", "o3-mini-high", "o3-pro", "o4-mini"}

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
    named = set(registry.DISPLAY_NAMES) | SPELLED_AS_THEIR_ID
    assert RAW_ON_2026_10_04 - named == set(), sorted(RAW_ON_2026_10_04 - named)


def test_each_name_in_the_table_is_a_bounded_spelling_and_wins_for_its_model() -> None:
    """A table name reaches `/v1` like any display, so it keeps D-157's bound (M16 MAJOR-1)."""
    for model_id, name in registry.DISPLAY_NAMES.items():
        assert name != model_id, model_id
        assert registry._DISPLAY.fullmatch(name), name
        assert registry._derived_display(model_id, [model_id]) == name, model_id
