"""Canonical model registry: alias → canonical model (REQ-CAN-001/-002).

The rule table is ORDERED and first-match-wins. Sub-variant rules
(mini/nano/codex/chat…) MUST precede their parent-family rules so a variant's
price or score never leaks into the parent (REQ-CAN-002 — the spike bug,
2026-08-06: GPT-5-nano's price surfaced as GPT-5's). Unmatched names are
dropped WITH a count, never guessed (REQ-CAN-001).

This table is curated data — the project's core IP. Review at every closure.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from app.clients.swebench import split_harness


@dataclass(frozen=True)
class ModelRule:
    """One ordered alias rule: first regex match wins."""

    canonical_id: str
    display: str
    vendor: str
    pattern: str


# fmt: off
MODEL_RULES: tuple[ModelRule, ...] = (
    # ── Anthropic (variants before parents) ─────────────────────────────
    # M4-W1: families added from a LIVE drop-list probe (LiteLLM pricing + SWE-bench +
    # Arena overall board, 2026-08-15). A family is only added when live data carries
    # BOTH a score and a price for it — a rule for a model that cannot rank is dead code.
    # Effort/tier suffixes (-max, -high, -xhigh, -medium, -low, -thinking, -preview,
    # date stamps) are absorbed into the base model: they are runtime settings of the
    # same model at the same price, and the coding sources already behaved this way.
    ModelRule("claude-fable-5",    "Claude Fable 5",    "Anthropic", r"claude[-_ ]?fable[-_ ]?5"),
    ModelRule("claude-5-opus",     "Claude Opus 5",     "Anthropic", r"claude[-_ ]?opus[-_ ]?5|claude[-_ ]?5[-_ ]?opus"),
    ModelRule("claude-4.8-opus",   "Claude Opus 4.8",   "Anthropic", r"claude[-_ ]?4[.\-]8[-_ ]?opus|claude[-_ ]?opus[-_ ]?4[.\-]8"),
    ModelRule("claude-4.7-opus",   "Claude Opus 4.7",   "Anthropic", r"claude[-_ ]?4[.\-]7[-_ ]?opus|claude[-_ ]?opus[-_ ]?4[.\-]7"),
    ModelRule("claude-4.6-opus",   "Claude Opus 4.6",   "Anthropic", r"claude[-_ ]?4[.\-]6[-_ ]?opus|claude[-_ ]?opus[-_ ]?4[.\-]6"),
    ModelRule("claude-4.5-opus",   "Claude 4.5 Opus",   "Anthropic", r"claude[-_ ]?4[.\-]?5[-_ ]?opus|claude[-_ ]?opus[-_ ]?4[.\-]?5"),
    ModelRule("claude-4.5-sonnet", "Claude 4.5 Sonnet", "Anthropic", r"claude[-_ ]?4[.\-]?5[-_ ]?sonnet|claude[-_ ]?sonnet[-_ ]?4[.\-]?5"),
    ModelRule("claude-4.5-haiku",  "Claude 4.5 Haiku",  "Anthropic", r"claude[-_ ]?4[.\-]?5[-_ ]?haiku|claude[-_ ]?haiku[-_ ]?4[.\-]?5"),
    ModelRule("claude-4.1-opus",   "Claude Opus 4.1",   "Anthropic", r"claude[-_ ]?4[.\-]1[-_ ]?opus|claude[-_ ]?opus[-_ ]?4[.\-]1"),
    ModelRule("claude-4-opus",     "Claude 4 Opus",     "Anthropic", r"claude[-_ ]?4[-_ ]?opus|claude[-_ ]?opus[-_ ]?4(?![.\-]?[15])"),
    ModelRule("claude-4-sonnet",   "Claude 4 Sonnet",   "Anthropic", r"claude[-_ ]?4[-_ ]?sonnet|claude[-_ ]?sonnet[-_ ]?4(?![.\-]?5)"),
    ModelRule("claude-3.7-sonnet", "Claude 3.7 Sonnet", "Anthropic", r"claude[-_ ]?3[.\-]?7[-_ ]?sonnet"),
    # ── OpenAI: variant rules BEFORE parent-family rules (REQ-CAN-002) ──
    ModelRule("gpt-5-pro",         "GPT-5 Pro",         "OpenAI",    r"gpt[-_ ]?5[-_ ]?pro"),
    ModelRule("gpt-5-nano",        "GPT-5 nano",        "OpenAI",    r"gpt[-_ ]?5(?:[.\-]?\d)?[-_ ]?nano"),
    ModelRule("gpt-5-mini",        "GPT-5 mini",        "OpenAI",    r"gpt[-_ ]?5(?:[.\-]?\d)?[-_ ]?(?:codex[-_ ]?)?mini"),
    ModelRule("gpt-5-chat",        "GPT-5 chat",        "OpenAI",    r"gpt[-_ ]?5(?:[.\-]?\d)?[-_ ]?chat"),
    ModelRule("gpt-5.2-codex",     "GPT-5.2 Codex",     "OpenAI",    r"gpt[-_ ]?5[.\-]?2[-_ ]?codex(?![-_ ]?max)"),
    ModelRule("gpt-5.1-codex",     "GPT-5.1 Codex",     "OpenAI",    r"gpt[-_ ]?5[.\-]?1[-_ ]?codex(?![-_ ]?max)"),
    ModelRule("gpt-5-codex",       "GPT-5 Codex",       "OpenAI",    r"gpt[-_ ]?5[-_ ]?codex(?![-_ ]?max)"),
    # GPT-5.6 ships three named variants (luna/sol/terra, live in both pricing and
    # Arena) — distinct models, so they precede the bare 5.6 rule.
    ModelRule("gpt-5.6-sol",       "GPT-5.6 Sol",       "OpenAI",    r"gpt[-_ ]?5[.\-]6[-_ ]?sol"),
    ModelRule("gpt-5.6-luna",      "GPT-5.6 Luna",      "OpenAI",    r"gpt[-_ ]?5[.\-]6[-_ ]?luna"),
    ModelRule("gpt-5.6-terra",     "GPT-5.6 Terra",     "OpenAI",    r"gpt[-_ ]?5[.\-]6[-_ ]?terra"),
    ModelRule("gpt-5.6",           "GPT-5.6",           "OpenAI",    r"gpt[-_ ]?5[.\-]6(?!\d)(?![-_ ]?(?:sol|luna|terra|codex|pro))"),
    ModelRule("gpt-5.5",           "GPT-5.5",           "OpenAI",    r"gpt[-_ ]?5[.\-]5(?!\d)(?![-_ ]?codex|[-_ ]?pro)"),
    ModelRule("gpt-5.4",           "GPT-5.4",           "OpenAI",    r"gpt[-_ ]?5[.\-]4(?!\d)(?![-_ ]?codex|[-_ ]?pro)"),
    ModelRule("gpt-5.2",           "GPT-5.2",           "OpenAI",    r"gpt[-_ ]?5[.\-]2(?!\d)(?![-_ ]?codex|[-_ ]?pro)"),
    ModelRule("gpt-5.1",           "GPT-5.1",           "OpenAI",    r"gpt[-_ ]?5[.\-]1(?!\d)(?![-_ ]?codex|[-_ ]?pro)"),
    ModelRule("gpt-5",             "GPT-5",             "OpenAI",    r"gpt[-_ ]?5(?![.\-]?\d|[-_ ]?mini|[-_ ]?nano|[-_ ]?chat|[-_ ]?codex|[-_ ]?pro)"),
    ModelRule("o3",                "o3",                "OpenAI",    r"\bo3(?![-\w])|\bo3[-_ ](?:high|medium|low)"),
    ModelRule("o4-mini",           "o4-mini",           "OpenAI",    r"\bo4[-_ ]?mini"),
    ModelRule("gpt-4.1",           "GPT-4.1",           "OpenAI",    r"gpt[-_ ]?4\.1(?![-_ ]?(mini|nano))"),
    ModelRule("gpt-4o",            "GPT-4o",            "OpenAI",    r"gpt[-_ ]?4o(?![-_ ]?mini)"),
    # ── Google ──────────────────────────────────────────────────────────
    # M4-W1 FIX (swallow defect found by the new self-consistency test): the old
    # `gemini-3(?:[.\-]?\d+)?-pro` matched 3.1/3.5/3.6 too, so Gemini 3.1 Pro and
    # Gemini 3 Pro shared one canonical id — one price and one score for two models.
    # Dotted versions now rank on their own evidence and precede the bare rule.
    ModelRule("gemini-3.1-pro",    "Gemini 3.1 Pro",    "Google",    r"gemini[-_ ]?3[.\-]1[-_ ]?pro(?![-_ ]?image)"),
    ModelRule("gemini-3-pro",      "Gemini 3 Pro",      "Google",    r"gemini[-_ ]?3[-_ ]?pro(?![.\-]\d(?!\d))(?![-_ ]?image)"),
    ModelRule("gemini-3.6-flash",  "Gemini 3.6 Flash",  "Google",    r"gemini[-_ ]?3[.\-]6[-_ ]?flash(?![-_ ]?lite)"),
    ModelRule("gemini-3.5-flash",  "Gemini 3.5 Flash",  "Google",    r"gemini[-_ ]?3[.\-]5[-_ ]?flash(?![-_ ]?lite)"),
    ModelRule("gemini-3-flash",    "Gemini 3 Flash",    "Google",    r"gemini[-_ ]?3[-_ ]?flash(?![-_ ]?(?:lite|image))(?![.\-]\d(?!\d))"),
    ModelRule("gemini-2.5-pro",    "Gemini 2.5 Pro",    "Google",    r"gemini[-_ ]?2[.\-]?5[-_ ]?pro"),
    ModelRule("gemini-2.5-flash-lite", "Gemini 2.5 Flash-Lite", "Google", r"gemini[-_ ]?2[.\-]?5[-_ ]?flash[-_ ]?lite"),
    ModelRule("gemini-2.5-flash",  "Gemini 2.5 Flash",  "Google",    r"gemini[-_ ]?2[.\-]?5[-_ ]?flash(?![-_ ]?lite)"),
    # ── xAI (newest/dotted before bare 4) ───────────────────────────────
    ModelRule("grok-4.20",         "Grok 4.20",         "xAI",       r"grok[-_ ]?4[.\-]20(?!\d)(?![-_ ]?multi)"),
    ModelRule("grok-4.6",          "Grok 4.6",          "xAI",       r"grok[-_ ]?4[.\-]6(?!\d)"),
    ModelRule("grok-4.5",          "Grok 4.5",          "xAI",       r"grok[-_ ]?4[.\-]5(?!\d)"),
    ModelRule("grok-4-fast",       "Grok 4 Fast",       "xAI",       r"grok[-_ ]?4[-_ ]?fast"),
    ModelRule("grok-4",            "Grok 4",            "xAI",       r"grok[-_ ]?4(?!\.\d)(?![-_ ]\d{1,2}(?!\d))(?![-_ ]?fast)"),
    # ── DeepSeek (dotted versions before bare v3) ───────────────────────
    ModelRule("deepseek-v4-pro",   "DeepSeek V4 Pro",   "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?4[-_ ]?pro"),
    ModelRule("deepseek-v4-flash", "DeepSeek V4 Flash", "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?4[-_ ]?flash"),
    ModelRule("deepseek-v4",       "DeepSeek V4",       "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?4(?![.\-p]\d(?!\d))(?![-_ ]?(?:pro|flash))"),
    ModelRule("deepseek-v3.2",     "DeepSeek V3.2",     "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?3[.\-]2(?!\d)"),
    ModelRule("deepseek-v3.1",     "DeepSeek V3.1",     "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?3[.\-]1(?!\d)"),
    ModelRule("deepseek-v3",       "DeepSeek V3",       "DeepSeek",  r"deepseek[-_ ]?(?:chat[-_ ]?)?v?3(?![.\-]?\d)"),
    ModelRule("deepseek-r1",       "DeepSeek R1",       "DeepSeek",  r"deepseek[-_ ]?r1(?![-_ ]?distill)"),
    # ── Others (dotted versions before bare families) ───────────────────
    ModelRule("qwen3.8-max",       "Qwen3.8 Max",       "Alibaba",   r"qwen[-_ ]?3[.\-]8[-_ ]?max"),
    ModelRule("qwen3.7-max",       "Qwen3.7 Max",       "Alibaba",   r"qwen[-_ ]?3[.\-]7[-_ ]?max"),
    ModelRule("qwen3.6-max",       "Qwen3.6 Max",       "Alibaba",   r"qwen[-_ ]?3[.\-]6[-_ ]?max"),
    ModelRule("qwen3.5-max",       "Qwen3.5 Max",       "Alibaba",   r"qwen[-_ ]?3[.\-]5[-_ ]?max"),
    ModelRule("qwen3-coder",       "Qwen3 Coder",       "Alibaba",   r"qwen[-_ ]?3[-_ ]?coder(?![-_ ]?(?:flash|plus))"),
    ModelRule("qwen3-max",         "Qwen3 Max",         "Alibaba",   r"qwen[-_ ]?3[-_ ]?max"),
    ModelRule("kimi-k2",           "Kimi K2",           "Moonshot",  r"kimi[-_ ]?k2"),
    ModelRule("glm-5.2",           "GLM-5.2",           "Zhipu",     r"glm[-_ ]?5[.\-p]2(?!\d)"),
    ModelRule("glm-5.1",           "GLM-5.1",           "Zhipu",     r"glm[-_ ]?5[.\-p]1(?!\d)"),
    ModelRule("glm-5",             "GLM-5",             "Zhipu",     r"glm[-_ ]?5(?![.\-p]\d(?!\d))(?!v)(?![-_ ]?code)"),
    ModelRule("glm-4.6",           "GLM-4.6",           "Zhipu",     r"glm[-_ ]?4[.\-]?6"),
    ModelRule("glm-4.5",           "GLM-4.5",           "Zhipu",     r"glm[-_ ]?4[.\-]?5(?!v|[-_ ]?air)"),
    ModelRule("mistral-large",     "Mistral Large",     "Mistral",   r"mistral[-_ ]?large"),
    ModelRule("devstral",          "Devstral",          "Mistral",   r"devstral(?![-_ ]?(?:small|medium))"),
    ModelRule("doubao-seed-code",  "Doubao Seed Code",  "ByteDance", r"doubao[-_ ]?seed[-_ ]?code"),
    ModelRule("minimax-m3",        "MiniMax M3",        "MiniMax",   r"minimax[-_ ]?m3"),
    ModelRule("minimax-m2.7",      "MiniMax M2.7",      "MiniMax",   r"minimax[-_ ]?m2[.\-p]7"),
    ModelRule("minimax-m2.5",      "MiniMax M2.5",      "MiniMax",   r"minimax[-_ ]?m2[.\-p]5(?![-_ ]?lightning)"),
    ModelRule("minimax-m2.1",      "MiniMax M2.1",      "MiniMax",   r"minimax[-_ ]?m2[.\-p]1(?!\d)"),
    ModelRule("minimax-m2",        "MiniMax M2",        "MiniMax",   r"minimax[-_ ]?m2(?![.\-p]\d(?!\d))"),
)
# fmt: on

_COMPILED: tuple[tuple[ModelRule, re.Pattern[str]], ...] = tuple(
    (rule, re.compile(rule.pattern, re.IGNORECASE)) for rule in MODEL_RULES
)


def canonicalize(name: str) -> ModelRule | None:
    """First-match-wins lookup; None = unmatched (caller counts drops)."""
    for rule, rx in _COMPILED:
        if rx.search(name):
            return rule
    return None


@dataclass(frozen=True)
class ReconcileReport:
    """Reconciliation outcome (REQ-CAN-001: drops are counted, never guessed)."""

    pricing_matched: int
    pricing_dropped: int
    scores_matched: int
    scores_dropped: int
    models_registered: int
    dropped_names: tuple[str, ...] = ()  # reviewed at closure — blind spots stay visible


@dataclass(frozen=True)
class PlanReconcileReport:
    """Plan-model linkage outcome (REQ-SUB-001; drops counted, never guessed)."""

    matched: int
    dropped: int
    dropped_names: tuple[str, ...] = ()


def reconcile_plans(conn: sqlite3.Connection) -> PlanReconcileReport:
    """Map plan_models.raw_name (page-stated names) to canonical models.

    A plan's included-model name that no registry rule matches stays NULL and
    is COUNTED — the drop list is the visibility mechanism for registry drift
    (M1 rule 4), exactly as with pricing aliases and score raw_names.
    """
    matched = dropped = 0
    dropped_names: list[str] = []
    with conn:
        for (raw_name,) in conn.execute("SELECT DISTINCT raw_name FROM plan_models").fetchall():
            rule = canonicalize(raw_name)
            if rule is None:
                dropped += 1
                dropped_names.append(raw_name)
                continue
            matched += 1
            conn.execute(
                "UPDATE plan_models SET model_id = ? WHERE raw_name = ?",
                (rule.canonical_id, raw_name),
            )
            conn.execute(
                "INSERT OR REPLACE INTO models (id, display, vendor) VALUES (?,?,?)",
                (rule.canonical_id, rule.display, rule.vendor),
            )
    return PlanReconcileReport(matched, dropped, tuple(sorted(dropped_names)))


def reconcile(conn: sqlite3.Connection) -> ReconcileReport:
    """Map pricing aliases + score raw_names to canonical models.

    Score names embed the harness ("agent + model") — the model-ish remainder
    from split_harness is what gets canonicalized (W2 review carry-over).
    Unmatched rows keep model_id NULL and are counted as dropped.
    """
    seen: dict[str, ModelRule] = {}
    dropped: list[str] = []
    p_matched = p_dropped = s_matched = s_dropped = 0

    with conn:
        for (alias,) in conn.execute("SELECT DISTINCT alias FROM pricing").fetchall():
            rule = canonicalize(alias)
            if rule is None:
                p_dropped += 1
                dropped.append(alias)
                continue
            p_matched += 1
            seen[rule.canonical_id] = rule
            conn.execute(
                "UPDATE pricing SET model_id = ? WHERE alias = ?", (rule.canonical_id, alias)
            )
        for (raw_name,) in conn.execute("SELECT DISTINCT raw_name FROM scores").fetchall():
            _, model_part = split_harness(raw_name)
            rule = canonicalize(model_part)
            if rule is None:
                s_dropped += 1
                dropped.append(raw_name)
                continue
            s_matched += 1
            seen[rule.canonical_id] = rule
            conn.execute(
                "UPDATE scores SET model_id = ? WHERE raw_name = ?", (rule.canonical_id, raw_name)
            )
        for rule in seen.values():
            conn.execute(
                "INSERT OR REPLACE INTO models (id, display, vendor) VALUES (?,?,?)",
                (rule.canonical_id, rule.display, rule.vendor),
            )
    return ReconcileReport(
        p_matched, p_dropped, s_matched, s_dropped, len(seen), tuple(sorted(dropped))
    )
