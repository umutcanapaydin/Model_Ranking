"""M17-W3 P4 (#37) -- D-166: a moving, undated API alias never creates a derived model.

A score under `deepseek-chat` was measured on whatever release the alias meant that day; its price
is what it means today. D-157 joined the two into one "model". The M16-W4 re-review counted thirteen
such ids (MINOR-1); twelve were registered on the served artifact of 2026-09-25.
"""

from __future__ import annotations

import pytest

from app.workflows import registry
from app.workflows.registry import derive_identity, reconcile
from app.workflows.schema import connect

LISTED = ("claude3.5-sonnet", "mistral7b-instruct", "deepseek-chat", "deepseek-reasoner", "command-r",
          "command-r-plus", "mistral-medium", "gpt4-turbo", "gpt4o-mini", "o1", "o1-mini", "yi-large",
          "claude-instant", "command-r+", "claude-instant-v1")


def test_the_list_is_the_one_the_review_found_each_with_a_reason() -> None:
    assert set(registry.MOVING_ALIASES) == set(LISTED)
    assert all(reason.strip() for reason in registry.MOVING_ALIASES.values())


@pytest.mark.parametrize("name", ["deepseek-chat", "o1", "gpt-4o-mini", "GPT-4o mini", "claude-3-5-sonnet",
                                  "openrouter/anthropic/claude-3.5-sonnet", "command-r-plus", "Yi-large"])
def test_a_moving_alias_derives_no_model(name: str) -> None:
    assert derive_identity(name) is None


@pytest.mark.parametrize(("name", "derived"), [("gpt-4o-mini-2024-07-18", "gpt4o-mini2024-07-18"),
                                               ("deepseek-v3.2", "deepseek-v3.2"),
                                               ("o1-2024-12-17", "o1-2024-12-17")])
def test_a_dated_name_still_derives(name: str, derived: str) -> None:
    identity = derive_identity(name)
    assert identity is not None and identity.model_id == derived


def _row(conn, raw: str) -> None:  # type: ignore[no-untyped-def]
    conn.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                 "source_url, observed_at) VALUES (?, 'b', 'elo', 1300, 'h', 'unspecified', 's', 'u', 'z')", (raw,))
    conn.execute("INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, observed_at) "
                 "VALUES (?, 1, 2, 'p', 'u', 'z')", (raw,))


def test_reconcile_registers_no_model_from_an_alias_and_counts_it_dropped() -> None:
    conn = connect(":memory:")
    try:
        _row(conn, "deepseek-chat")
        _row(conn, "deepseek-v3.2")
        report = reconcile(conn)
        ids = {r[0] for r in conn.execute("SELECT id FROM models")}
        assert "deepseek-chat" not in ids and "deepseek-v3.2" in ids
        assert "deepseek-chat" in report.dropped_names
    finally:
        conn.close()


def test_a_curated_rule_still_wins_over_the_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-166 clause 2: the list stops derivation only. A curated rule written for a listed alias
    still takes its rows, through the reconcile the build runs (wave review M6: the first version
    of this test never reached code that reads the list, so it could not fail)."""
    import re

    rule = registry.ModelRule("deepseek-v3.2", "DeepSeek V3.2", "DeepSeek", r"deepseek[-_ ]?chat")
    monkeypatch.setattr(registry, "_COMPILED", ((rule, re.compile(rule.pattern, re.I)), *registry._COMPILED))
    conn = connect(":memory:")
    try:
        _row(conn, "deepseek-chat")
        report = reconcile(conn)
        linked = conn.execute("SELECT model_id FROM scores WHERE raw_name = 'deepseek-chat'").fetchone()
        assert linked == ("deepseek-v3.2",)
        assert "deepseek-chat" not in report.dropped_names
    finally:
        conn.close()


# --- #40: spellings the exact list missed, and the `-latest` suffix as a rule -------------------


@pytest.mark.parametrize("name", ["Command R+", "anthropic.claude-instant-v1", "claude-instant-v1",
                                  "chatgpt-4o-latest", "claude-3-5-sonnet-latest", "mistral-large-latest",
                                  "openrouter/openai/gpt-5-chat-latest", "Gemini-Flash-Latest"])
def test_a_moving_spelling_the_list_missed_derives_no_model(name: str) -> None:
    """#40 (Tester K1 of M17-W3): a `-latest` alias moves by definition, so the suffix is a rule,
    not list entries; `Command R+` and `claude-instant-v1` are two more spellings of listed aliases."""
    assert derive_identity(name) is None


@pytest.mark.parametrize("name", ["chatgpt-4o-latest-20250326", "gpt-5.2-chat-latest-20260210",
                                  "claude-instant-1.2"])
def test_a_dated_release_of_a_latest_alias_still_derives(name: str) -> None:
    """A date or version after the alias names one release, which is exactly what D-166 keeps."""
    assert derive_identity(name) is not None


def test_reconcile_registers_no_model_from_a_latest_alias() -> None:
    """A name no curated rule takes: `mistral-large-latest` would be the curated `mistral-large`'s,
    and a curated rule still wins over the list (D-166 clause 2)."""
    conn = connect(":memory:")
    try:
        _row(conn, "gemini-flash-latest")
        report = reconcile(conn)
        assert conn.execute("SELECT COUNT(*) FROM models").fetchone()[0] == 0
        assert "gemini-flash-latest" in report.dropped_names
    finally:
        conn.close()


@pytest.mark.parametrize("name", ["gpt-5-chat-latest_high", "gpt-4o-latest:free", "oci/cohere.command-latest",
                                  "us.anthropic.claude-3-5-sonnet-latest-v1:0"])
def test_a_decorated_latest_alias_derives_no_model(name: str) -> None:
    """Tester T1 of #40: the rule reads the name as the grammar spells it, after the effort, the
    colon decoration and a dotted vendor head are gone -- all spellings price feeds use."""
    assert derive_identity(name) is None


def test_a_curated_rule_still_takes_a_latest_name() -> None:
    """Tester T2 of #40, D-166 clause 2 through reconcile: `mistral-large-latest` is the curated
    `mistral-large`'s, and the `-latest` rule only stops derivation."""
    conn = connect(":memory:")
    try:
        _row(conn, "mistral-large-latest")
        report = reconcile(conn)
        assert conn.execute("SELECT model_id FROM scores").fetchone() == ("mistral-large",)
        assert "mistral-large-latest" not in report.dropped_names
    finally:
        conn.close()
