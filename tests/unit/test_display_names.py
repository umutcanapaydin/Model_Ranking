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
    "o3-2025-04-16",
}

#: #112's remainder (the W7 review's M4 class): served under a lower-case spelling of the id, not the
#: id itself. Measured with M19-W1's code on a candidate built from live sources on 2026-10-06.
LOWER_CASE_ON_2026_10_06 = {
    "c4ai-aya-expanse32b", "codellama34b-instruct", "codellama70b-instruct", "command-a03-2025",
    "command-r-plus08-2024", "command-r08-2024", "devstral-small2505", "ernie5.1", "gemini-exp1206",
    "gemini3.1-flash-lite-preview", "gemma2-27b-it", "gemma2b-it", "gemma3-12b-it", "gemma3-27b-it",
    "gemma3-4b-it", "gemma4-31b", "gemma7b-it", "glm4.5-air", "glm4.5v", "glm5v-turbo", "gpt-oss120b",
    "gpt-oss20b", "gpt3.5-turbo0125", "gpt3.5-turbo0613", "gpt3.5-turbo1106", "gpt4-0125-preview",
    "gpt4-0613", "gpt4-1106-preview", "gpt4-turbo2024-04-09", "gpt4.5-preview", "gpt4o-mini2024-07-18",
    "gpt5.1-codex-max", "granite4.1-8b", "granite4.2-8b", "grok-code-fast1", "grok4.1-fast-reasoning",
    "grok4.20-multi-agent-beta0309", "grok4.3", "jamba1.5-large", "jamba1.5-mini", "llama2-7b-chat",
    "llama3-70b-instruct", "magistral-small2509", "mercury2", "mistral-medium2505",
    "mistral-small2402", "nova2-lite",
    "o1-mini2024-09-12", "o1-pro2025-03-19", "pixtral12b2409", "qwen-plus2025-01-25", "qwen-turbo2024-11-01",
    "qwen3-30b-a3b-thinking2507", "qwen3-4b-instruct2507", "qwen3-vl235b-a22b-thinking", "step3.5-flash",
    "zephyr7b-beta",
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


def test_no_model_served_under_a_lower_case_spelling_of_its_id_is_left_without_a_name() -> None:
    """#112's remainder: `c4ai-aya-expanse-32b` is the id with its dashes back, not a name."""
    assert LOWER_CASE_ON_2026_10_06 - set(registry.DISPLAY_NAMES) == set(), sorted(
        LOWER_CASE_ON_2026_10_06 - set(registry.DISPLAY_NAMES))


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
    """The plan's check for #112, over the served names: every model in the artifact, named by this
    code's own `reconcile` over the artifact's rows, as a build names them. None reads as its raw id
    or a lower-case spelling of it (#112's remainder), but OpenAI's, and every Claude is in
    Anthropic's order (the review's M4, and its R1: a new model served under its raw id shows here).

    M19-W1: this read each model's score names AND price aliases, an approximation of the build,
    which names a derived model from its score names only (the W7 Tester's T4). A capitalised price
    alias (`azure_ai/Phi-3-medium-4k-instruct`) then hid 17 lower-case names the build serves."""
    source = sqlite3.connect(f"file:{ARTIFACT}?mode=ro", uri=True)
    conn = sqlite3.connect(":memory:")
    try:
        source.backup(conn)
        conn.execute("UPDATE scores SET model_id = NULL")
        conn.execute("UPDATE pricing SET model_id = NULL")
        conn.execute("DELETE FROM models")
        registry.reconcile(conn)
        served = conn.execute("SELECT id, display FROM models").fetchall()
    finally:
        source.close()
        conn.close()
    assert len(served) > 100, "the artifact named almost nothing: the check would prove nothing"
    raw_ids, lower_case, misordered = [], [], []
    for model_id, name in served:
        if name == model_id and model_id not in SPELLED_AS_THEIR_ID:
            raw_ids.append(model_id)
        elif name == name.lower() and model_id not in SPELLED_AS_THEIR_ID | set(registry.DISPLAY_NAMES):
            # #112's remainder: the id with its dashes back is no name. A table name is ruled with its
            # source, and OpenAI writes some in lower case (`gpt-oss-120b`, `o1-mini (2024-09-12)`).
            lower_case.append(model_id)
        if problem := _claude_order_problem(name):
            misordered.append(problem)
    assert not raw_ids, f"served under their raw id: {sorted(raw_ids)}"
    assert not lower_case, f"served under a lower-case spelling of their id: {sorted(lower_case)}"
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
