---
record_type: register
id: m4-w1-registry-droplist
status: ratified
date: 2026-08-15
---
# M4-W1 — Registry drop list and what was done about it (REQ-CAN-004)

**Method.** Live probe on 2026-08-15 across every source this container can reach — LiteLLM
pricing JSON, SWE-bench Verified, Aider polyglot (GitHub raw) — plus the Arena overall board
(389 rows) the owner fetched out-of-sandbox. Dropped names were ranked by score, then checked for
a matching PRICE alias: **a rule for a model with no price cannot rank, so it would be dead code.**

## Before / after

| | before W1 | after W1 |
|---|---|---|
| canonical models registered | 42 | **71** |
| score rows matched | 190 | **218** |
| plan→model links | 2 (2 dropped) | **4 (0 dropped)** |
| plan coverage — assistant | 2/9 | **3/9** |
| plan coverage — coding | 2/9 | **1/9** (see below — this is a correction, not a loss) |

Plan-name drops are now **zero**: every model a curated plan page names explicitly resolves.
Coverage stays thin because most plans name nothing at all — that is W2's roster problem, not a
registry gap, and the coverage metric (REQ-SUB-005, W3) will keep saying so.

**Coding coverage went DOWN, and that is the honest number.** Before this wave `google-ai-ultra`
ranked on coding with 77.4 % — Gemini 3 Pro's SWE-bench score. But Ultra's page names only
*Gemini 3.1 Pro*, and the two were sharing one canonical id because of the swallow defect below.
Gemini 3.1 Pro has no SWE-bench score in any reachable source, so Ultra now honestly cannot rank
on coding. The old 2/9 was a wrong answer with a confident number attached; 1/9 is a true one.
(Reviewer-verified against `plan_ranking()` at both revisions.)

## Defect found by the new self-consistency test

`gemini-3(?:[.\-]?\d+)?-pro` matched **Gemini 3.1 Pro as well as Gemini 3 Pro** — two different
models sharing one canonical id, therefore one price and one score. Live data made it visible
(both names appear, with different Elo). Fixed by giving dotted versions their own rules ahead of
the bare one. This is the M1-W3 defect class, caught this time by a property the table proves
about itself (`test_every_rule_canonicalizes_to_itself`) rather than by a human reading regexes.

## Added (score AND price present live)

OpenAI `gpt-5.6`, `gpt-5.6-sol`, `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.5`, `gpt-5.4` ·
MiniMax `minimax-m2.1` (16 live price aliases + Arena Elo 1391.1 — added at review) ·
DeepSeek `deepseek-v4-flash` (own price $0.14/$0.28 and own Elo 1431.5 — added at review) ·
Anthropic `claude-fable-5`, `claude-5-opus`, `claude-4.8-opus`, `claude-4.7-opus`,
`claude-4.6-opus` · Google `gemini-3.1-pro`, `gemini-3.6-flash`, `gemini-3.5-flash` ·
xAI `grok-4.20`, `grok-4.6` · DeepSeek `deepseek-v4-pro`, `deepseek-v4` ·
Alibaba `qwen3.8-max`, `qwen3.7-max`, `qwen3.6-max`, `qwen3.5-max` · Zhipu `glm-5.2`, `glm-5.1`,
`glm-5` · MiniMax `minimax-m3`, `minimax-m2.7`, `minimax-m2.5`.

**Effort/tier suffix rule (new, applies to all of the above):** `-max`, `-high`, `-xhigh`,
`-medium`, `-low`, `-thinking`, `-preview` and date stamps are absorbed into the base model. The
guards distinguish the two mechanically: a VERSION token is a single digit after `.`/`-`/`p`
(`3.1`, `m2p7`), a DATE is not (`-2025-09-23`, `-0324`) — the review caught the first cut blocking
dates and losing a live Qwen3 Max score row. Absorption is right because these suffixes are
runtime settings of the same model at the same price, and the coding sources already
behaved this way (`mini-SWE-agent + Claude 4.5 Opus (high)` has always resolved to the base
model). **Version markers are NOT absorbed**: 3.1 ≠ 3, m2.5 ≠ m2, glm-5.2 ≠ glm-5.

## Deliberately NOT added, with the reason

| Name (live) | Why not |
|---|---|
| `kimi-k3-max` (Elo 1476) | no price alias in any reachable pricing source — would score but never rank |
| `ernie-5.1` (1468) | same: no price |
| `muse-spark`, `muse-spark-1.1/1.2` (1473-1488) | one pricing alias total (`meta/muse-spark-1.1`); family naming still unstable |
| `mimo-v2.5-pro`, `dola-seed-2.0-pro` | vendor attribution not established from a documented source — a wrong vendor is a wrong answer |
| `amazon-nova-experimental-chat-26-02-10` | explicitly experimental |
| `grok-4.20-*-beta-0309-*` | absorbed into `grok-4.20` deliberately: build stamps are not versions. The distinct `grok-4.20-multi-agent` product ($3/$15 vs $1.25/$2.5) is excluded and drops |
| `gemini-3.7-flash` | three price aliases, no score anywhere — it would rank on nothing |
| `gemini-3.1-flash` | authored, then REMOVED in review: its only live aliases are `-image`, `-image-preview` and `-live-preview`, which are different products, not a text model |
| `glm-5-code`, `MiniMax-M2.5-lightning`, `gpt-5.5-pro` / `gpt-5.4-pro` / `gpt-5.2-pro` | distinct products or tiers with distinct prices; they drop and are COUNTED rather than folding into a base model (REQ-CAN-001) |

## Assumption recorded (owner-visible)

`GPT-5.6 Sol Pro`, as ChatGPT Pro's page names it, resolves to **`gpt-5.6-sol`** — read as "the Sol
variant, on the Pro plan". No source lists a distinct "Sol Pro" model. This is a judgment call, not a rule: if OpenAI
ships a separate Sol Pro model, the rule splits. (An earlier draft justified it by pointing at
`gpt-5-pro` as a precedent; the review checked and that id currently holds four generations of
prices with zero score rows, so it proves nothing — the argument stands on the absence of any
"Sol Pro" in live data, not on that.) The pick's `scored_by_model` field shows the
user exactly which model produced the score, so the assumption is visible in the product, not
buried.

## Next probe starts here

Re-run the drop list at every milestone. The top of the current dropped-score list — models with
scores but no rules — is where registry drift will next cost coverage.
