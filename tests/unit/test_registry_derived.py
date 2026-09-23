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
