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
from app.workflows.schema import EFFORT_LEVELS, EFFORT_UNSPECIFIED


@dataclass(frozen=True)
class ModelRule:
    """One ordered alias rule: first regex match wins."""

    canonical_id: str
    display: str
    vendor: str
    pattern: str
    #: What this model PRODUCES, declared by whoever writes the rule. Every rule in the table
    #: below is `"text"`; an image-editing or audio model states its own. `modality_mismatch`
    #: compares an alias's modality token against THIS field.
    #:
    #: **It is a declared field and not a substring of `canonical_id` on purpose, and the
    #: independent seat is why.** The first version of the guard asked whether the canonical id
    #: contained the token, which works for `gpt-image-1` and silently fails for every image
    #: model named after something else: `nano-banana-pro`, `seedream-4`, `flux-1-kontext`. Under
    #: that version a correctly-ordered `nano-banana-pro` rule dropped its own live pricing
    #: aliases — `gemini-3-pro-image`, `google/gemini-3-pro-image-preview` — as a modality
    #: mismatch against itself, and the test that claimed to prove the guard was future-proof
    #: used `gpt-image-1` as its fixture, so it pinned the one naming convention under which the
    #: bug is invisible. That is the fixture-blindness shape this repository has recorded three
    #: times. The rule now states what it is instead of being guessed at by its name.
    modality: str = "text"


# fmt: off
MODEL_RULES: tuple[ModelRule, ...] = (
    # ── Anthropic (variants before parents) ─────────────────────────────
    # M4-W1: families added from a LIVE drop-list probe (LiteLLM pricing + SWE-bench +
    # Arena overall board, 2026-08-15). A family is only added when live data carries
    # BOTH a score and a price for it — a rule for a model that cannot rank is dead code.
    # Effort suffixes (-max/-xhigh/-high/-medium/-low) map to the same priced model,
    # but M5 resolves and stores the suffix BEFORE this table is consulted. They are
    # never allowed to disappear as score dimensions. Preview/date tokens remain aliases.
    # M16-W4: the parent rule had no version guard, so Fable 5.1's prices folded into Fable 5.
    ModelRule("claude-fable-5.1",  "Claude Fable 5.1",  "Anthropic", r"claude[-_ ]?fable[-_ ]?5[.\-]1(?!\d)"),
    ModelRule("claude-fable-5",    "Claude Fable 5",    "Anthropic", r"claude[-_ ]?fable[-_ ]?5(?![.\-]?\d)"),
    ModelRule("claude-5-opus",     "Claude Opus 5",     "Anthropic", r"claude[-_ ]?opus[-_ ]?5(?![.\-]?\d)|claude[-_ ]?5[-_ ]?opus"),
    # M4-W2: named by Perplexity's documented plan roster, and live in both pricing
    # (claude-sonnet-5) and Arena (claude-sonnet-5-high).
    ModelRule("claude-5-sonnet",   "Claude Sonnet 5",   "Anthropic", r"claude[-_ ]?sonnet[-_ ]?5(?![.\-]?\d)|claude[-_ ]?5[-_ ]?sonnet"),
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
    # "Thinking" is ChatGPT's name for a reasoning mode; ChatGPT's plan table writes the variant
    # after it ("GPT-5 Thinking Mini", 2026-09-23), past the parent rule's lookahead.
    ModelRule("gpt-5-nano",        "GPT-5 nano",        "OpenAI",    r"gpt[-_ ]?5(?:[.\-]?\d)?[-_ ]?(?:thinking[-_ ]?)?nano"),
    ModelRule("gpt-5-mini",        "GPT-5 mini",        "OpenAI",    r"gpt[-_ ]?5(?:[.\-]?\d)?[-_ ]?(?:codex[-_ ]?|thinking[-_ ]?)?mini"),
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
    # Kimi K2.x are DISTINCT models, not effort variants of K2. The unguarded
    # `kimi[-_ ]?k2` rule swallowed both (M5 closure, live Epoch SWE-bench: k2.5=73.8
    # and k2.6=76.7 collapsed onto one id and MAX() published 76.7 as "Kimi K2") — the
    # same swallow class M4-W1 fixed for the GPT-5.x Pro family, recurring on a new
    # source because the live-name corpus had never seen these names.
    ModelRule("kimi-k2.6",         "Kimi K2.6",         "Moonshot",  r"kimi[-_ ]?k2[.\-]6(?!\d)"),
    ModelRule("kimi-k2.5",         "Kimi K2.5",         "Moonshot",  r"kimi[-_ ]?k2[.\-]5(?!\d)"),
    ModelRule("kimi-k2",           "Kimi K2",           "Moonshot",  r"kimi[-_ ]?k2(?![.\-]\d)"),
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


#: **REQ-CAN-002's defect class, on the axis nobody enumerated.** The module docstring already
#: states the rule: a variant's price or score may never leak into its parent family, and the rule
#: table orders sub-variants first so `gpt-5-nano` cannot be read as `gpt-5`. That ordering defends
#: the SIZE axis. It does nothing on the MODALITY axis, because there is no `gpt-5-image` rule for
#: `openai/gpt-5-image` to match first — so it fell through to the `gpt-5` family rule and an image
#: model's price became the text model's price.
#:
#: **Measured on `advisor.db` built 2026-08-27, and the figures below are the INDEPENDENT SEAT's,
#: not the author's.** The author's first write-up of this block undercounted three of them, in a
#: file its own docstring calls the project's core IP; the numbers here are the ones that survived
#: re-measurement, and the correction is recorded in `docs/warnings.ledger.md` rather than quietly
#: overwritten.
#:
#: Of 2,661 distinct pricing aliases, **19 carrying five modality tokens were reconciled to six
#: text models** (`gpt-4o`, `gpt-5`, `gpt-5.4`, `gemini-2.5-flash`, `gemini-2.5-pro`,
#: `deepseek-v4-flash`). **Four of those models published an inflated price:**
#: `gpt-5` input `1.562` where the text-only rows give `1.094` (**+43%**), `gpt-5.4` `2.5/15.0`
#: against `2.188/13.125`, `gemini-2.5-flash` `0.3/2.5` against `0.262/2.188`, and
#: `deepseek-v4-flash` `0.105/0.21` against `0.1/0.2`.
#:
#: **It did not stop at a printed number, and the first version of this comment said it did.**
#: 72 price cells moved across eight of the nine surfaces, and **the comparative sentences moved
#: with them**: `trade_off` and its D-136 `trade_off_fact` differ on **16 of 27** (surface, budget)
#: answers — `computer-use` / Best Value went from `cheaper_by_percent: 20` to `9`, a 2.2x swing in
#: a claim the product composes a sentence from. What did NOT move, verified across all 27
#: answers: the model order, the identity of every pick, `eligible_count` and `frontier_size`.
#: Nobody was recommended the wrong model. Everybody was told the wrong price, and some were told
#: the wrong saving.
#:
#: A modality token makes an alias a DIFFERENT PRODUCT, priced on a different basis — an image
#: model per image, an audio model per second, a transcription SKU per minute. The guard is
#: deliberately NOT "drop anything containing these words": it refuses only when the alias carries
#: a modality the matched rule does not DECLARE, so a rule that states `modality="image"` keeps its
#: own aliases whatever it is named.
#:
#: **What this does not cover, stated rather than implied.** A retrieval SKU of a text model is
#: still a different product at a different price, and the tokens below catch `gpt-4o-search-preview`
#: while leaving `gpt-5-search-api` and `o4-mini-deep-research` reconciled to their families
#: (measured: no price effect today, the two-stage median absorbs them). That is a naming-fashion
#: boundary, not a principled one. The principled fix is a declared SKU axis, which is larger than
#: this wave; it is ledgered, not hidden.
# fmt: off
_MODALITY_TOKENS: tuple[str, ...] = (
    "image", "video", "audio", "speech", "tts", "transcribe", "transcription",
    "embed", "embedding", "rerank", "moderation", "vision", "search-preview",
)
# fmt: on

_MODALITY_RX: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (token, re.compile(rf"(^|[-_/. ]){re.escape(token)}([-_/. ]|\d|$)", re.IGNORECASE))
    for token in _MODALITY_TOKENS
)


def modality_mismatch(name: str, rule: ModelRule) -> str | None:
    """The modality token that makes ``name`` a different product from ``rule``, if any.

    Returns the offending token so the caller can COUNT the drop by reason rather than record an
    anonymous miss. `None` means the alias and the matched model agree on modality.
    """
    for token, rx in _MODALITY_RX:
        if rx.search(name) and token != rule.modality:
            return token
    return None


def canonicalize_with_reason(name: str) -> tuple[ModelRule | None, str | None]:
    """The lookup plus WHY it failed: ``(rule, None)``, ``(None, token)`` or ``(None, None)``.

    Two refusals are not the same fact and REQ-CAN-001 counts drops for a reason:

    * ``(None, None)`` — no rule matched. That is **registry drift**: a model we do not know
      about yet, and the drop list is the triage queue for it.
    * ``(None, token)`` — a rule matched and was refused, because the name carries a modality
      this model does not produce. That is **not drift**; it is the guard working, and a name
      that lands here must never be triaged as a missing rule.

    The seat that reviewed the first version of this wave found the reason computed and then
    thrown away: nineteen refusals went into the same flat list as 2,393 genuine blind spots, in
    a list whose stated purpose is to find drift at closure. Returning the reason is what makes
    the two countable apart.
    """
    for rule, rx in _COMPILED:
        if rx.search(name):
            token = modality_mismatch(name, rule)
            return (None, token) if token else (rule, None)
    return (None, None)


def canonicalize(name: str) -> ModelRule | None:
    """First-match-wins lookup; None = unmatched (caller counts drops).

    A match is refused when the name carries a modality the matched model does not produce
    (`modality_mismatch`): an image, audio or transcription variant is a different product and
    its price is not this model's price. Callers that need to know WHICH refusal happened use
    `canonicalize_with_reason`.
    """
    return canonicalize_with_reason(name)[0]


_EFFORT_SUFFIX = re.compile(r"(?P<separator>[-_])(?P<effort>max|xhigh|high|medium|low)\Z", re.I)
#: #38: the Agent Arena boards, Aider and SWE-bench write a run's effort in a TRAILING parenthesis
#: (`GPT 6 Astra (Max)`, `gpt-5 (high)`), where Epoch writes `_max`. Only a schema effort level counts:
#: `(no thinking)`, `(default)`, `(May 2024)` and a parenthesis before another one stay name text.
_PAREN_EFFORT = re.compile(r"\s*\((?P<effort>max|xhigh|high|medium|low)\)\Z", re.I)


@dataclass(frozen=True)
class EffortResolution:
    """Explicit score effort plus the model name with a true effort suffix removed."""

    model_name: str
    effort: str | None
    conflict: bool = False
    invalid_explicit: bool = False
    #: W-010. The raw name ends in an effort-looking token that could NOT be confirmed as an
    #: effort, because the base name has no registry rule to compare against. The row is not
    #: wrong to store as `unspecified` — it is wrong to store it SILENTLY. REQ-CAN-005 says an
    #: undeterminable effort is counted and disclosed, never defaulted.
    unclassified_suffix: bool = False


def resolve_effort(model_name: str, explicit: str | None = None) -> EffortResolution:
    """Resolve score effort without mistaking model-family names for settings.

    A terminal token is an effort suffix only when removing it leaves the same
    canonical model. Thus ``claude-opus-5_max`` resolves to Claude Opus 5 at max,
    while the model family ``qwen3.7-max`` remains intact. A valid explicit column
    wins a suffix disagreement and the caller can disclose the conflict.
    """
    explicit_value = explicit.strip().lower() if isinstance(explicit, str) else ""
    explicit_effort = explicit_value if explicit_value in EFFORT_LEVELS else None
    invalid_explicit = bool(explicit_value and explicit_effort is None)

    suffix_effort: str | None = None
    full_refused_for: str | None = None
    base_name = model_name
    match = _EFFORT_SUFFIX.search(model_name.strip()) or _PAREN_EFFORT.search(model_name.strip())
    if match:
        candidate_base = model_name.strip()[: match.start()]
        full_rule, full_refused_for = canonicalize_with_reason(model_name)
        base_rule = canonicalize(candidate_base)
        if (
            full_rule is not None
            and base_rule is not None
            and full_rule.canonical_id == base_rule.canonical_id
        ):
            suffix_effort = match.group("effort").lower()
            base_name = candidate_base

    effort = explicit_effort or suffix_effort
    if effort == EFFORT_UNSPECIFIED:  # defensive; not a valid explicit parser value
        effort = None
    return EffortResolution(
        model_name=base_name,
        effort=effort,
        conflict=bool(explicit_effort and suffix_effort and explicit_effort != suffix_effort),
        invalid_explicit=invalid_explicit,
        # REQ-CAN-005 counts a suffix it could not classify BECAUSE the base name has no rule to
        # compare against. A name the modality guard refused is a different fact: the registry
        # knows this family perfectly well and is declining a different product from it. Counting
        # that as an undeterminable effort would put a working control's output into a register
        # that exists to measure our blind spots (M14-W1 review, MINOR-4).
        unclassified_suffix=bool(
            match and suffix_effort is None and effort is None and full_refused_for is None
        ),
    )


# ── D-157: identities DERIVED from the data, for names no curated rule matches ─────────────────────
#
# The owner (2026-09-23, translated from Turkish): "if it is on a list, the list wins; but when we
# cannot give anything, [...] we will present the list we derived from the data." The curated table
# above still wins. A name it does not match is normalised by the fixed grammar below and registered
# when the derived id has BOTH a price and a score -- what it needs to rank, and nothing it does not.
#
# The grammar removes DECORATION only, from a CLOSED list: the route a price feed puts in front of a
# model; `:batch`, `:free`, `:nitro`, `:floor`, `:exacto`; `@default`, `@latest`; a region head; a
# vendor head only before that vendor's own family word; Bedrock's `-v1:0` only after such a
# head; Epoch's underscore effort; and separator spelling. Every other token stays -- `-v2`, `@002`,
# `:thinking`, `:high`, a date -- so the failure it can have is a SPLIT (the ADR's stated cost).
# The first version stripped any `-vN` and anything after `:` or `@`, and merged deepseek-coder-v2
# into deepseek-coder and three Mistral 7B versions into one (M16-W4 review BLOCKING-1).
# What it cannot see: two sources spelling a name IDENTICALLY are one model to it, even where a
# vendor reused the name for two releases; only a curated rule can split those.

#: Region heads a price feed puts before a model (`us.`, `global.`): always decoration.
_REGION_PREFIXES = frozenset({"us", "eu", "au", "jp", "apac", "global", "us-gov", "ca", "sa"})
#: A VENDOR head (`anthropic.`) is decoration only before that vendor's own family word:
#: `anthropic.claude-...` is Claude, but `deepseek.r1` is a model called R1 at DeepSeek, and dropping
#: the head there left a bare `r1` (M16-W4 review BLOCKING-1).
_VENDOR_FAMILIES: dict[str, tuple[str, ...]] = {
    "anthropic": ("claude",), "meta": ("llama",), "amazon": ("nova", "titan"),
    "mistral": ("mistral", "mixtral", "ministral", "pixtral", "codestral", "magistral", "devstral"),
    "cohere": ("command",), "ai21": ("jamba",), "deepseek": ("deepseek",), "qwen": ("qwen", "qwq"),
    "openai": ("gpt", "o1", "o3", "o4"), "google": ("gemini", "gemma"), "xai": ("grok",),
    "writer": ("palmyra",), "moonshotai": ("kimi",), "minimax": ("minimax",),
}
#: After `:`, the route decorations price feeds append. Anything else names a variant and STAYS:
#: `:thinking` is a different product, `:1` is Claude 2.1, `:high` is an effort (review BLOCKING-1).
_COLON_DECORATION = frozenset({"batch", "free", "nitro", "floor", "exacto"})
#: After `@`, only these are decoration; `@001` and `@20240620` are releases.
_AT_DECORATION = frozenset({"default", "latest"})
#: Epoch writes a run's effort after an underscore (`gpt-6-astra_high`). `none`, `minimal`,
#: `promax` and `unknown` are not efforts this schema stores; they are removed and read as unspecified.
_UNDERSCORE_EFFORT = re.compile(r"_(none|minimal|low|medium|high|xhigh|max|promax|unknown)\Z", re.I)
#: The route segment before a model name, as price feeds write it, to the vendor it names.
_VENDOR_SLUGS: dict[str, str] = {
    "openai": "OpenAI", "anthropic": "Anthropic", "google": "Google", "gemini": "Google",
    "meta-llama": "Meta", "meta": "Meta", "mistralai": "Mistral", "mistral": "Mistral",
    "qwen": "Alibaba", "alibaba": "Alibaba", "deepseek": "DeepSeek", "deepseek-ai": "DeepSeek",
    "x-ai": "xAI", "xai": "xAI", "moonshotai": "Moonshot", "z-ai": "Zhipu", "zai-org": "Zhipu",
    "amazon": "Amazon", "microsoft": "Microsoft", "nvidia": "NVIDIA", "minimax": "MiniMax",
    "cohere": "Cohere", "ai21": "AI21", "xiaomi": "Xiaomi", "baidu": "Baidu", "tencent": "Tencent",
}
#: When no route names a vendor, the family word a derived id starts with.
_FAMILY_VENDORS: tuple[tuple[str, str], ...] = (
    ("gpt", "OpenAI"), ("o1", "OpenAI"), ("o3", "OpenAI"), ("o4", "OpenAI"), ("claude", "Anthropic"),
    ("gemini", "Google"), ("gemma", "Google"), ("llama", "Meta"), ("qwen", "Alibaba"),
    ("qwq", "Alibaba"), ("grok", "xAI"), ("mistral", "Mistral"), ("ministral", "Mistral"),
    ("magistral", "Mistral"), ("codestral", "Mistral"), ("devstral", "Mistral"),
    ("deepseek", "DeepSeek"), ("kimi", "Moonshot"), ("glm", "Zhipu"), ("nova", "Amazon"),
    ("phi", "Microsoft"), ("nemotron", "NVIDIA"), ("nvidia", "NVIDIA"), ("minimax", "MiniMax"),
    ("mimo", "Xiaomi"), ("command", "Cohere"), ("jamba", "AI21"),
)


@dataclass(frozen=True)
class DerivedIdentity:
    """A derived model id, and the effort Epoch's underscore suffix stated, if any."""

    model_id: str
    effort: str | None


def _decorated(text: str, mark: str, decoration: frozenset[str]) -> str:
    """Drop `mark` + a known decoration; keep any other suffix as a name token."""
    base, sep, suffix = text.partition(mark)
    if not sep:
        return text
    return base if suffix in decoration else f"{base}-{suffix.replace(mark, '-')}"


def _without_heads(text: str) -> tuple[str, bool]:
    """Region and vendor dotted heads removed (a vendor only before its own family word), and
    whether any was: Bedrock's `-v1:0` API tag is decoration only on such a routed name."""
    routed = False
    while True:
        head, dot, rest = text.partition(".")
        family = _VENDOR_FAMILIES.get(head, ())
        if dot and rest and (head in _REGION_PREFIXES or (bool(family) and rest.startswith(family))):
            text, routed = rest, True
            continue
        return text, routed


#: D-166 (owner ruling 2026-09-25): undated API aliases whose meaning MOVES, as the grammar spells
#: them. A score under one was measured on whatever release the alias meant on its run date; the
#: price is what it means today; so they never create a derived model. The list only stops
#: derivation: a curated rule that names one still takes it (the list wins, D-157). The thirteen
#: are the M16-W4 re-review's (MINOR-1); an alias a vendor repoints is added here with its reason.
MOVING_ALIASES: dict[str, str] = {
    "claude3.5-sonnet": "Anthropic moved the undated name from 2024-06-20 to 2024-10-22",
    "mistral7b-instruct": "hosts serve v0.1, v0.2 or v0.3 under the undated name",
    "deepseek-chat": "DeepSeek repoints its API alias at each V3.x release",
    "deepseek-reasoner": "DeepSeek repoints its API alias at each R1 / V3.x reasoning release",
    "command-r": "Cohere repointed the alias (2024-03 to 2024-08)",
    "command-r-plus": "Cohere repointed the alias (2024-04 to 2024-08)",
    "mistral-medium": "Mistral reused the name for a different generation",
    "gpt4-turbo": "OpenAI moved the alias across the preview and 2024-04-09 releases",
    "gpt4o-mini": "an undated OpenAI alias, pinned only by its dated snapshot",
    "o1": "OpenAI moved the alias from the preview to 2024-12-17",
    "o1-mini": "an undated OpenAI alias, pinned only by its dated snapshot",
    "yi-large": "01.AI's alias, served by hosts from different dates",
    "claude-instant": "Anthropic served 1.0 and 1.2 under the undated name",
}


def derive_identity(name: str) -> DerivedIdentity | None:
    """The grammar's id for ``name``; None for a different product (the modality guard)."""
    if any(rx.search(name) for _, rx in _MODALITY_RX):
        return None
    text = name.strip()
    effort: str | None = None
    suffix = _UNDERSCORE_EFFORT.search(text) or _PAREN_EFFORT.search(text)
    if suffix:
        token = suffix.group(1).lower()
        effort = token if token in EFFORT_LEVELS else None
        text = text[: suffix.start()]
    text = text.rsplit("/", 1)[-1].lower()         # the route: `openrouter/openai/...`
    if text.startswith("ft:"):
        return None                                # a fine-tune is its owner's model, not the base
    text = _decorated(text, "@", _AT_DECORATION)
    text, routed = _without_heads(text)
    if routed:
        text = re.sub(r"-v1:0\Z", "", text)          # Bedrock's API tag, only after its prefix;
        # a bare `-v1` there is a model version (`anthropic.claude-v1`, Claude 1: re-review NIT-1)
    text = _decorated(text, ":", _COLON_DECORATION)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    text = re.sub(r"(?<=\d)-(\d)(?=-|\Z)", r".\1", text)  # `opus-5-5` is 5.5; `3-235b` is not
    text = re.sub(r"([a-z])-(\d)", r"\1\2", text)     # `gpt-6` and `gpt6` are one spelling
    if not text or not re.fullmatch(r"[a-z0-9][a-z0-9.+\-]*", text):
        return None
    if text in MOVING_ALIASES:
        return None                                # D-166: a moving alias names no one release
    return DerivedIdentity(model_id=text, effort=effort)


def _derived_vendor(model_id: str, aliases: list[str]) -> str:
    for alias in sorted(aliases):
        parts = alias.lower().split("/")
        candidates = [parts[-2]] if len(parts) > 1 else []
        candidates += parts[-1].split(".")[:-1]
        for slug in candidates:
            if slug in _VENDOR_SLUGS:
                return _VENDOR_SLUGS[slug]
    for prefix, vendor in _FAMILY_VENDORS:
        if model_id.startswith(prefix):
            return vendor
    return "Other"


#: What a display name may look like. It reaches `/v1` and the app as a model's name, so it is a
#: SPELLING of the model and nothing else (M16 Stage 4.0 security review, MAJOR-1).
_DISPLAY = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .+()\-]{0,63}")


def _derived_display(model_id: str, names: list[str]) -> str:
    """A board's own spelling when one has it (`GPT-6 Astra`), else the shortest, else the id.

    A candidate is only the name's last route segment, bounded to 64 characters of a closed
    alphabet, and it must READ AS THE SAME MODEL through the grammar. Taken verbatim, a score's
    name served "Visit evil.example ... /zeta 9" as a model name, with no length bound (MAJOR-1)."""
    candidates = set()
    for name in names:
        bare = _PAREN_EFFORT.sub("", _UNDERSCORE_EFFORT.sub("", name.rsplit("/", 1)[-1])).strip()
        derived = derive_identity(bare)
        if _DISPLAY.fullmatch(bare) and derived is not None and derived.model_id == model_id:
            candidates.add(bare)
    spaced = sorted(n for n in candidates if " " in n)
    if spaced:
        return spaced[0]
    return min(candidates, key=lambda n: (len(n), n)) if candidates else model_id


@dataclass(frozen=True)
class ReconcileReport:
    """Reconciliation outcome (REQ-CAN-001: drops are counted, never guessed)."""

    pricing_matched: int
    pricing_dropped: int
    scores_matched: int
    scores_dropped: int
    models_registered: int
    dropped_names: tuple[str, ...] = ()  # reviewed at closure — blind spots stay visible
    #: The subset of `dropped_names` refused by the modality guard, each with the token that
    #: refused it. These are NOT registry drift and must be subtracted before the drop list is
    #: read as a list of models we are missing (M14-W1 review, MAJOR-2).
    modality_drops: tuple[tuple[str, str], ...] = ()
    #: D-157: the models registered from the data by the grammar, not by a curated rule.
    derived: tuple[str, ...] = ()

    @property
    def drift_dropped(self) -> int:
        """Drops that really do mean "no rule for this model" — the triage number."""
        return self.pricing_dropped + self.scores_dropped - len(self.modality_drops)


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


@dataclass
class _Pending:
    """Names no curated rule matched, grouped by derived id until both halves are known."""

    prices: dict[str, list[str]]
    scores: dict[str, list[tuple[str, str, str | None, str]]]

    def ready(self, curated: set[str]) -> list[str]:
        """D-157's threshold: a price AND a score, and never an id a curated rule owns."""
        return sorted(set(self.prices) & set(self.scores) - curated)


def _register_derived(conn: sqlite3.Connection, pending: _Pending, model_id: str) -> tuple[int, int]:
    """Link one derived model's rows and register it. Returns (aliases, score names) linked."""
    aliases = pending.prices[model_id]
    names = pending.scores[model_id]
    for alias in aliases:
        conn.execute("UPDATE pricing SET model_id = ? WHERE alias = ?", (model_id, alias))
    for raw_name, effort, stated, _ in names:
        if effort == EFFORT_UNSPECIFIED and stated:
            # The effort the name states becomes the row's, so an effort-ranked surface can see it.
            # OR IGNORE: a row already stored at that effort under the same name keeps its own.
            conn.execute(
                "UPDATE OR IGNORE scores SET model_id = ?, effort = ? WHERE raw_name = ? AND effort = ?",
                (model_id, stated, raw_name, effort),
            )
        conn.execute(
            "UPDATE scores SET model_id = ? WHERE raw_name = ? AND effort = ? AND model_id IS NULL",
            (model_id, raw_name, effort),
        )
    conn.execute(
        "INSERT OR REPLACE INTO models (id, display, vendor) VALUES (?,?,?)",
        (model_id, _derived_display(model_id, [part for *_, part in names]),
         _derived_vendor(model_id, aliases)),
    )
    return len(aliases), len(names)


def _unmatched(
    name: str, grammar_name: str, refused_for: str | None,
    dropped: list[str], modality_drops: list[tuple[str, str]],
) -> DerivedIdentity | None:
    """A name no curated rule took: the modality guard's refusal is dropped for its reason; anything
    else is derived, or dropped when the grammar cannot read it."""
    if refused_for:
        modality_drops.append((name, refused_for))
        dropped.append(name)
        return None
    derived = derive_identity(grammar_name)
    if derived is None:
        dropped.append(name)
    return derived


def reconcile(conn: sqlite3.Connection) -> ReconcileReport:
    """Map pricing aliases + score raw_names to canonical models.

    Score names embed the harness ("agent + model") — the model-ish remainder
    from split_harness is what gets canonicalized (W2 review carry-over).
    A name no curated rule matches is staged under its derived id (D-157) and linked only when that
    id has both a price and a score; every other unmatched row keeps model_id NULL and is counted.
    """
    seen: dict[str, ModelRule] = {}
    dropped: list[str] = []
    modality_drops: list[tuple[str, str]] = []
    pending = _Pending(prices={}, scores={})
    p_matched = s_matched = 0
    # Counted BEFORE any row changes: linking a derived model can rewrite a row's effort, which
    # merges two (name, effort) pairs into one, and a total taken after that went negative (M16-W4
    # review MINOR-1). Matches are counted over the same pairs, at the same moment.
    p_total = conn.execute("SELECT COUNT(DISTINCT alias) FROM pricing").fetchone()[0]
    s_total = conn.execute("SELECT COUNT(*) FROM (SELECT DISTINCT raw_name, effort FROM scores)"
                           ).fetchone()[0]

    with conn:
        for (alias,) in conn.execute("SELECT DISTINCT alias FROM pricing").fetchall():
            rule, refused_for = canonicalize_with_reason(alias)
            if rule is None:
                derived = _unmatched(alias, alias, refused_for, dropped, modality_drops)
                if derived is not None:
                    pending.prices.setdefault(derived.model_id, []).append(alias)
                continue
            p_matched += 1
            seen[rule.canonical_id] = rule
            conn.execute(
                "UPDATE pricing SET model_id = ? WHERE alias = ?", (rule.canonical_id, alias)
            )
        for raw_name, effort in conn.execute(
            "SELECT DISTINCT raw_name, effort FROM scores"
        ).fetchall():
            _, model_part = split_harness(raw_name)
            explicit = None if effort == EFFORT_UNSPECIFIED else effort
            identity = resolve_effort(model_part, explicit)
            rule, refused_for = canonicalize_with_reason(identity.model_name)
            if rule is None:
                derived = _unmatched(raw_name, identity.model_name, refused_for, dropped,
                                     modality_drops)
                if derived is not None:
                    pending.scores.setdefault(derived.model_id, []).append(
                        (raw_name, effort, derived.effort, identity.model_name))
                continue
            s_matched += 1
            seen[rule.canonical_id] = rule
            conn.execute(
                "UPDATE scores SET model_id = ? WHERE raw_name = ? AND effort = ?",
                (rule.canonical_id, raw_name, effort),
            )
        for rule in seen.values():
            conn.execute(
                "INSERT OR REPLACE INTO models (id, display, vendor) VALUES (?,?,?)",
                (rule.canonical_id, rule.display, rule.vendor),
            )
        derived_ids = pending.ready({rule.canonical_id for rule in MODEL_RULES})
        for model_id in derived_ids:
            prices, scores = _register_derived(conn, pending, model_id)
            p_matched += prices
            s_matched += scores
        linked = set(derived_ids)
        dropped += [a for mid, aliases in pending.prices.items() if mid not in linked for a in aliases]
        dropped += [n[0] for mid, names in pending.scores.items() if mid not in linked for n in names]
    return ReconcileReport(
        p_matched,
        p_total - p_matched,
        s_matched,
        s_total - s_matched,
        len(seen) + len(derived_ids),
        tuple(sorted(dropped)),
        tuple(sorted(modality_drops)),
        tuple(derived_ids),
    )
