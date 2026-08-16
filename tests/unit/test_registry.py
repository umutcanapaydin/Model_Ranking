"""Canonical registry tests — cite REQ-CAN-001 and REQ-CAN-002."""

from __future__ import annotations

import json
import sqlite3

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_litellm, ingest_swebench
from app.workflows.registry import MODEL_RULES, canonicalize, reconcile
from app.workflows.schema import connect


def test_first_match_wins_maps_aliases_to_one_canonical_id() -> None:
    """REQ-CAN-001: different aliases of one model → one canonical id."""
    for alias in ("claude-4-5-opus", "Claude 4.5 Opus medium (20251101)", "claude-opus-4-5"):
        rule = canonicalize(alias)
        assert rule is not None, alias
        assert rule.canonical_id == "claude-4.5-opus", alias


def test_unmatched_names_return_none_never_guess() -> None:
    """REQ-CAN-001: unknown names are dropped (None), not fuzzy-guessed."""
    assert canonicalize("totally-unknown-model-xyz") is None


def test_variant_never_leaks_into_parent() -> None:
    """REQ-CAN-002 regression (spike bug red→green): nano/mini/codex/chat ≠ parent."""
    cases = {
        "gpt-5-nano": "gpt-5-nano",
        "gpt-5.1-nano": "gpt-5-nano",
        "gpt-5-mini-2026-01-01": "gpt-5-mini",
        "gpt-5.1-codex-mini": "gpt-5-mini",
        "gpt-5-chat-latest": "gpt-5-chat",
        "gpt-5-codex": "gpt-5-codex",
        "gpt-5.2-codex": "gpt-5.2-codex",
        "gpt-5": "gpt-5",
        "grok-4.5-fast": "grok-4.5",
        "grok-4-0709": "grok-4",
        "deepseek-v3.2-exp": "deepseek-v3.2",
        "deepseek-chat-v3": "deepseek-v3",
    }
    for alias, expected in cases.items():
        rule = canonicalize(alias)
        assert rule is not None, alias
        assert rule.canonical_id == expected, f"{alias} → {rule.canonical_id}, want {expected}"


def test_date_suffixed_alias_is_dropped_not_misversioned() -> None:
    """REQ-CAN-001/-002: 'gpt-5-2026-08-01' must NOT match gpt-5.2 (date ≠ version).

    Conservative rule: ambiguous names drop (counted) rather than guess.
    """
    assert canonicalize("gpt-5-2026-08-01") is None


def test_sibling_variants_never_leak_into_parent_families() -> None:
    """W3 review BLOCKING-2 regression: real sibling aliases must not merge into parents."""
    cases = {
        "gpt-5-pro": "gpt-5-pro",
        "azure/gpt-5-pro": "gpt-5-pro",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        "gemini-2.5-flash-lite-preview-06-17": "gemini-2.5-flash-lite",
        "grok-4-fast": "grok-4-fast",
        "grok-4-fast-reasoning": "grok-4-fast",
        "claude-opus-4-1": "claude-4.1-opus",
    }
    for alias, expected in cases.items():
        rule = canonicalize(alias)
        assert rule is not None, alias
        assert rule.canonical_id == expected, f"{alias} → {rule.canonical_id}, want {expected}"
    # unlisted siblings DROP rather than merge (conservative REQ-CAN-001)
    for alias in (
        "grok-4.1",
        "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
        "glm-4.5-air",
        "glm-4.5v",
        "qwen3-coder-flash",
        "gpt-5.1-codex-max",
        "devstral-small",
    ):
        assert canonicalize(alias) is None, f"{alias} must drop, not merge"


def test_rule_order_variants_precede_parents() -> None:
    """REQ-CAN-002: structural check — a parent rule must not shadow its variants."""
    ids = [r.canonical_id for r in MODEL_RULES]
    for variant, parent in (
        ("gpt-5-nano", "gpt-5"),
        ("gpt-5-mini", "gpt-5"),
        ("gpt-5-chat", "gpt-5"),
        ("gpt-5-codex", "gpt-5"),
        ("gpt-5.2-codex", "gpt-5.2"),
        ("gpt-5.1-codex", "gpt-5.1"),
        ("grok-4.5", "grok-4"),
        ("deepseek-v3.2", "deepseek-v3"),
        ("deepseek-v3.1", "deepseek-v3"),
    ):
        assert ids.index(variant) < ids.index(parent), f"{variant} must precede {parent}"


def _seed(conn: sqlite3.Connection) -> None:
    pricing = json.dumps(
        {
            "gpt-5": {
                "mode": "chat",
                "input_cost_per_token": 1.25e-06,
                "output_cost_per_token": 1e-05,
            },
            "gpt-5-nano": {
                "mode": "chat",
                "input_cost_per_token": 5e-08,
                "output_cost_per_token": 4e-07,
            },
            "mystery-model": {
                "mode": "chat",
                "input_cost_per_token": 1e-06,
                "output_cost_per_token": 2e-06,
            },
        }
    )
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "mini-SWE-agent + GPT-5", "resolved": 74.4, "date": "2025-09-01"},
                        {"name": "SomeAgent + Unknown Model Z", "resolved": 50.0},
                    ],
                }
            ]
        }
    )
    run = RunContext(observed_at="t")
    ingest_litellm(conn, FakeRawSource("litellm", pricing), run)
    ingest_swebench(conn, FakeRawSource("swebench", scores), run)


def test_reconcile_maps_and_counts_drops() -> None:
    """REQ-CAN-001: matched rows get model_id; unmatched are counted, stay NULL."""
    conn = connect()
    _seed(conn)
    report = reconcile(conn)
    assert report.pricing_matched == 2
    assert report.pricing_dropped == 1  # mystery-model
    assert report.scores_matched == 1
    assert report.scores_dropped == 1  # Unknown Model Z
    assert report.models_registered == 2  # gpt-5 (pricing+score dedup) + gpt-5-nano

    nano = conn.execute("SELECT model_id FROM pricing WHERE alias='gpt-5-nano'").fetchone()[0]
    parent = conn.execute("SELECT model_id FROM pricing WHERE alias='gpt-5'").fetchone()[0]
    assert nano == "gpt-5-nano"
    assert parent == "gpt-5"
    unmatched = conn.execute("SELECT model_id FROM pricing WHERE alias='mystery-model'").fetchone()[
        0
    ]
    assert unmatched is None
    score_mid = conn.execute("SELECT model_id FROM scores WHERE raw_name LIKE '%GPT-5'").fetchone()[
        0
    ]
    assert score_mid == "gpt-5"
    unknown_mid = conn.execute(
        "SELECT model_id FROM scores WHERE raw_name LIKE '%Unknown Model Z'"
    ).fetchone()[0]
    assert unknown_mid is None
    assert "SomeAgent + Unknown Model Z" in report.dropped_names
    assert "mystery-model" in report.dropped_names


def test_score_names_are_canonicalized_on_model_part_not_harness() -> None:
    """W2 carry-over: 'agent + model' names split before matching."""
    conn = connect()
    scores = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "gpt-5-flavored-agent + Claude 4.5 Opus", "resolved": 79.0}
                    ],
                }
            ]
        }
    )
    ingest_swebench(conn, FakeRawSource("swebench", scores), RunContext(observed_at="t"))
    reconcile(conn)
    mid = conn.execute("SELECT model_id FROM scores").fetchone()[0]
    assert mid == "claude-4.5-opus", "harness text must not drive the match"


# ── REQ-CAN-004: rule-authoring safety net (M4-W1) ───────────────────────────
# The M1-W3 defect (a parent rule swallowing a sibling variant) was found by a
# reviewer reading regexes. These two tests turn that class into a property the
# table proves about ITSELF, so every future rule is defended on the day it is
# added instead of the day it breaks a ranking.


def test_every_rule_canonicalizes_to_itself() -> None:
    """A rule's own id/display must resolve to THAT rule — never to an earlier one.

    This is the swallow check: if `gemini-3.1-pro` resolves to `gemini-3-pro`,
    two different models share one price and one score, silently.
    """
    from app.workflows.registry import MODEL_RULES, canonicalize

    for rule in MODEL_RULES:
        for probe in (rule.canonical_id, rule.display, rule.canonical_id.replace("-", " ")):
            got = canonicalize(probe)
            assert got is not None, f"{rule.canonical_id}: own name {probe!r} matches NO rule"
            assert got.canonical_id == rule.canonical_id, (
                f"swallowed: {probe!r} (rule {rule.canonical_id}) resolves to "
                f"{got.canonical_id} — a more specific rule must precede the general one"
            )


def test_no_duplicate_canonical_ids_or_patterns() -> None:
    from app.workflows.registry import MODEL_RULES

    ids = [r.canonical_id for r in MODEL_RULES]
    assert len(ids) == len(set(ids)), "duplicate canonical id"
    pats = [r.pattern for r in MODEL_RULES]
    assert len(pats) == len(set(pats)), "duplicate pattern"


# ── REQ-CAN-004 (M4-W1 review MINOR-7): rules are defended by LIVE NAMES ─────
# The two properties above only probe a rule against its OWN id. The M4-W1
# review proved that is too narrow: every real swallow it found involved a name
# a SOURCE emits, not a name the table writes. This corpus is copied verbatim
# from live sources on 2026-08-15 (LiteLLM pricing aliases, Arena model_name,
# SWE-bench entries) — including every wrong mapping that review caught, so a
# regression re-breaks the exact case that was paid for.
LIVE_NAME_EXPECTATIONS: tuple[tuple[str, str | None], ...] = (
    # M5 closure: found on the LIVE Epoch SWE-bench board, not in any earlier corpus.
    # `kimi-k2.5` (73.8) and `kimi-k2.6` (76.7) both folded into `kimi-k2`, so MAX()
    # published the newer model's score under the older model's name. Same swallow
    # class as the GPT-5.x Pro family M4-W1 fixed — a rule table is only defended by
    # the names its sources actually emit.
    ("kimi-k2.6", "kimi-k2.6"),
    ("kimi-k2.5", "kimi-k2.5"),
    ("kimi-k2", "kimi-k2"),
    ("Kimi K2.6", "kimi-k2.6"),
    ("kimi-k2-instruct", "kimi-k2"),
    # variant must never fold into its base (own price AND own score live)
    ("deepseek-v4-flash", "deepseek-v4-flash"),
    ("deepseek-v4-pro", "deepseek-v4-pro"),
    ("deepseek-v4", "deepseek-v4"),
    ("minimax/MiniMax-M2.5-lightning", None),
    ("zai/glm-5-code", None),
    ("glm-5v-turbo", None),
    ("oci/xai.grok-4.20-multi-agent", None),
    # image / live-API products are not text models
    ("gemini-3-pro-image", None),
    ("gemini-3.1-flash-image", None),
    ("gemini-3.1-flash-lite", None),
    # versioned Pro models drop and are counted; they never join bare GPT-5 Pro
    ("gpt-5.5-pro", None),
    ("gpt-5.4-pro", None),
    ("gpt-5.2-pro", None),
    ("gpt-5-pro", "gpt-5-pro"),
    # provider version notations: dotted, dashed, and Fireworks' `p`
    ("fireworks_ai/glm-5p1", "glm-5.1"),
    ("glm-5p2", "glm-5.2"),
    ("fireworks_ai/minimax-m2p1", "minimax-m2.1"),
    ("minimax-m2p7", "minimax-m2.7"),
    ("minimax-m2.1-preview", "minimax-m2.1"),
    # DATE stamps are absorbed (a version token is one digit; a date is not)
    ("qwen3-max-2025-09-23", "qwen3-max"),
    ("dashscope/qwen3-max-2026-01-23", "qwen3-max"),
    ("gpt-5.5-2026-04-23", "gpt-5.5"),
    ("claude-opus-4-6-20260205", "claude-4.6-opus"),
    # effort / tier suffixes are absorbed
    ("claude-opus-5-max", "claude-5-opus"),
    ("claude-opus-5-high", "claude-5-opus"),
    ("gpt-5.6-sol-xhigh", "gpt-5.6-sol"),
    ("gemini-3.5-flash-medium", "gemini-3.5-flash"),
    # Epoch SWE-bench rows copied verbatim from the owner-fetched 2026-08-15 bundle
    ("glm-5.2_max", "glm-5.2"),
    ("gemini-3.1-pro-preview-customtools", "gemini-3.1-pro"),
    ("qwen3.7-max-preview", "qwen3.7-max"),
    ("gemini-3-flash (thinking-minimal)", "gemini-3-flash"),
    ("grok-4.20-beta-0309-reasoning", "grok-4.20"),
    # version markers are NOT absorbed
    ("gemini-3.1-pro-preview", "gemini-3.1-pro"),
    ("gemini-3-pro", "gemini-3-pro"),
    ("qwen3.5-max", "qwen3.5-max"),
    ("minimax-m2.5", "minimax-m2.5"),
    ("minimax-m2", "minimax-m2"),
    ("glm-5", "glm-5"),
    # the plan pages' own strings (what the product actually links on)
    ("GPT-5.6", "gpt-5.6"),
    ("GPT-5.6 Sol Pro", "gpt-5.6-sol"),
    ("Gemini 3.1 Pro", "gemini-3.1-pro"),
    ("Gemini 3 Pro", "gemini-3-pro"),
)


def test_live_names_resolve_to_the_right_model() -> None:
    """Every entry is a string a real source emitted, with the answer we owe it."""
    from app.workflows.registry import canonicalize

    wrong = []
    for name, expected in LIVE_NAME_EXPECTATIONS:
        rule = canonicalize(name)
        got = rule.canonical_id if rule else None
        if got != expected:
            wrong.append(f"{name!r} -> {got} (want {expected})")
    assert not wrong, "live-name mapping regressions:\n  " + "\n  ".join(wrong)
