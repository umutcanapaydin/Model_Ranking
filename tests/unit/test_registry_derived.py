"""M16-W4 P4, D-157 -- a model on the boards reaches the lists without a code edit.

The owner (2026-09-23, translated from Turkish): "if it is on a list, the list wins; but when we
cannot give anything, [...] we will present the list we derived from the data." So the curated rules
still win, and a name no rule matches is normalised by a FIXED grammar -- route decorations off,
separators unified, nothing else -- and registered when that id has both a price and a score.

The grammar errs toward SPLITTING: it never removes a date or a variant word, so two spellings of one
model may stay two models (the ADR's stated cost), and a variant can never merge into its parent.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows.registry import derive_identity, reconcile
from app.workflows.schema import connect


def _id(name: str) -> str | None:
    derived = derive_identity(name)
    return derived.model_id if derived else None


@pytest.mark.parametrize("name", [
    "openrouter/openai/gpt-6-astra", "azure/gpt-6-astra", "openai/gpt-6-astra:batch",
    "GPT-6 Astra", "gpt-6-astra_xhigh", "gpt-6-astra_high",
])
def test_every_spelling_of_one_model_derives_one_id(name: str) -> None:
    assert _id(name) == _id("gpt-6-astra")


@pytest.mark.parametrize("name", [
    "vertex_ai/claude-opus-5-5@default", "us.anthropic.claude-opus-5-5", "Claude Opus 5.5",
    "global.anthropic.claude-opus-5-5-v1:0",
])
def test_route_region_and_version_separators_are_decoration(name: str) -> None:
    assert _id(name) == _id("claude-opus-5.5")


@pytest.mark.parametrize(("variant", "parent"), [
    ("gpt-6-astra-mini", "gpt-6-astra"), ("openai/gpt-6-luna-pro", "gpt-6-luna"),
    ("qwen3.7-plus", "qwen3.7"), ("o3-2025-04-16", "o3"), ("mistral-small-2603", "mistral-small"),
    ("gpt-6-astra-max", "gpt-6-astra"),
])
def test_a_variant_or_a_dated_release_never_merges_into_its_parent(variant: str, parent: str) -> None:
    assert _id(variant) != _id(parent)


def test_a_parameter_count_is_not_read_as_a_version() -> None:
    """`5-5` is version 5.5; `3-235b` is version 3 and 235 billion parameters."""
    assert "3.235" not in (_id("qwen3-235b-a22b") or "")
    assert _id("qwen3-235b-a22b") is not None


def test_the_underscore_effort_is_read_off_the_name() -> None:
    derived = derive_identity("gpt-6-astra_high")
    assert derived is not None and derived.effort == "high"
    assert derive_identity("gpt-6-astra_none").effort is None  # type: ignore[union-attr]


def test_a_different_product_is_never_derived() -> None:
    assert derive_identity("openai/gpt-6-image") is None
    assert derive_identity("text-embedding-4-large") is None


# --- reconcile --------------------------------------------------------------------------------------


def _conn(prices: list[str], scores: list[tuple[str, str]]) -> sqlite3.Connection:
    conn = connect(":memory:")
    conn.executemany(
        "INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, observed_at) "
        "VALUES (?, 1, 2, 'litellm', 'u', 'z')", [(a,) for a in prices])
    conn.executemany(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
        "source_url, observed_at) VALUES (?, 'B', 'm', 70, 'none', ?, 'epoch_x', 'u', 'z')", scores)
    conn.commit()
    return conn


def test_a_name_with_a_price_and_a_score_is_registered_as_derived() -> None:
    conn = _conn(["openrouter/openai/gpt-6-astra", "azure/gpt-6-astra"],
                 [("GPT-6 Astra", "unspecified"), ("gpt-6-astra_high", "unspecified")])
    report = reconcile(conn)
    model_id = _id("gpt-6-astra")
    assert report.derived == (model_id,)
    assert conn.execute("SELECT display, vendor FROM models WHERE id = ?",
                        (model_id,)).fetchone() == ("GPT-6 Astra", "OpenAI")
    linked = conn.execute("SELECT raw_name, effort FROM scores WHERE model_id = ? ORDER BY raw_name",
                          (model_id,)).fetchall()
    assert linked == [("GPT-6 Astra", "unspecified"), ("gpt-6-astra_high", "high")]
    assert conn.execute("SELECT COUNT(*) FROM pricing WHERE model_id = ?", (model_id,)).fetchone()[0] == 2
    assert "GPT-6 Astra" not in report.dropped_names


def test_a_name_with_only_a_price_or_only_a_score_is_not_registered() -> None:
    conn = _conn(["openai/gpt-6-luna"], [("Qwen 3.9 Max", "unspecified")])
    report = reconcile(conn)
    assert report.derived == ()
    assert conn.execute("SELECT COUNT(*) FROM models").fetchone()[0] == 0
    assert {"openai/gpt-6-luna", "Qwen 3.9 Max"} <= set(report.dropped_names)


def test_the_curated_rules_win() -> None:
    """A name a curated rule matches keeps that rule's model, and no derived id shadows it."""
    conn = _conn(["gpt-5", "openai/gpt-5"], [("gpt-5", "unspecified")])
    report = reconcile(conn)
    assert report.derived == ()
    assert conn.execute("SELECT DISTINCT model_id FROM scores").fetchall() == [("gpt-5",)]


# --- M16-W4 review BLOCKING-1: the grammar must never MERGE two products (docs/reviews/m16-wave-4-review.md)


@pytest.mark.parametrize("names", [
    ("DeepSeek-V2", "DeepSeek-V3", "deepseek/deepseek-v5"),
    ("claude-v1", "anthropic.claude-v2", "anthropic.claude-v2:1"),
    ("mistral-7b-instruct-v0:1", "mistral.mistral-7b-instruct-v0:2", "mistral-7b-instruct-v3"),
    ("vertex_ai/gemini-1.5-pro@001", "vertex_ai/gemini-1.5-pro@002"),
    ("vertex_ai/claude-3-5-sonnet@20240620", "claude-3.5-sonnet"),
    ("anthropic/claude-3.7-sonnet:thinking", "anthropic/claude-3.7-sonnet"),
    ("gpt-5:high", "gpt-5"),
    ("deepseek-coder-v2", "deepseek/deepseek-coder"),
    ("us.deepseek.r1-v1:0", "deepseek.v3-v1:0"),
])
def test_different_products_never_derive_one_id(names: tuple[str, ...]) -> None:
    ids = [_id(n) for n in names]
    assert len(set(ids)) == len(ids), dict(zip(names, ids, strict=True))


def test_a_vendor_prefix_is_dropped_only_before_its_own_family() -> None:
    assert _id("deepseek.r1") not in {"r1", None}
    assert _id("anthropic.claude-opus-5-5") == _id("claude-opus-5.5")


def test_bedrocks_api_tag_is_decoration_but_a_model_version_is_not() -> None:
    assert _id("anthropic.claude-opus-5-5-v1:0") == _id("claude-opus-5.5")
    assert _id("mistral.mistral-7b-instruct-v0:2") == _id("mistral-7b-instruct-v0.2")


def test_a_fine_tune_is_never_derived() -> None:
    assert derive_identity("ft:gpt-4o-mini:acme::abc123") is None


def test_the_next_release_does_not_inherit_a_staged_score() -> None:
    """Review BLOCKING-1: a `deepseek-v5` price met Epoch's staged `DeepSeek-V2` score."""
    conn = _conn(["deepseek/deepseek-v5"], [("DeepSeek-V2", "unspecified")])
    assert reconcile(conn).derived == ()


# --- M16-W4 review MINOR-1 and MINOR-2 --------------------------------------------------------------


def test_the_counts_never_go_negative() -> None:
    conn = connect(":memory:")
    conn.execute("INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, "
                 "observed_at) VALUES ('openai/gpt-6-astra', 1, 2, 'litellm', 'u', 'z')")
    conn.executemany(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
        "source_url, observed_at) VALUES ('gpt-6-astra_high', ?, 'm', 70, 'none', ?, 'x', 'u', 'z')",
        [("A", "high"), ("B", "unspecified")])
    report = reconcile(conn)
    assert report.scores_dropped >= 0 and report.pricing_dropped >= 0


def test_a_curated_id_is_never_taken_by_a_derived_one() -> None:
    """Review M23: `o3_none` matches no curated rule but derives to `o3`, which a curated rule owns."""
    conn = _conn(["o3_none"], [("o3_minimal", "unspecified")])
    assert reconcile(conn).derived == ()


def test_the_vendor_comes_from_the_route_when_it_names_one() -> None:
    conn = _conn(["openrouter/meta-llama/zeta-9"], [("zeta-9", "unspecified")])
    reconcile(conn)
    assert conn.execute("SELECT vendor FROM models").fetchone() == ("Meta",)


def test_a_derived_model_is_counted_as_registered() -> None:
    conn = _conn(["openai/gpt-6-astra"], [("GPT-6 Astra", "unspecified")])
    assert reconcile(conn).models_registered == 1


def test_an_effort_the_schema_does_not_store_is_still_decoration() -> None:
    assert _id("gpt-6-astra_none") == _id("gpt-6-astra") == _id("gpt-6-astra_minimal")
