---
record_type: register
id: m16-w4-derived-registry-2026-09-23
status: ratified
process_version: v6.0
date: 2026-09-23
---
# M16-W4 — what the derived registry changes (D-157), measured

**Measured 2026-09-23**, re-measured after the review's BLOCKING-1 fix
(`docs/reviews/m16-wave-4-review.md`). The candidate was built from live upstreams plus a freshly
fetched Epoch bundle (`python -m app.workflows.build --epoch-dir <bundle>`) and compared with the
served artifact. Both effects of this wave are in it: fresh Epoch data (P1, P2) and derived
registration (P4).

- **Score rows that match no model:** 1,450 of 2,834 before; **652 of 2,581** after.
- **Models registered:** 74 before; **317** after. Every new model has a price and a score under one
  derived id (D-157's threshold).
- **The grammar removes decoration only, and after the review it means that.** The first version
  also removed `-vN`, everything after `:` or `@`, and any vendor head. That merged products:
  deepseek-coder-v2's score was priced as `deepseek-coder`, and three Mistral 7B versions were
  priced as one. Now only these are removed:
  - Bedrock's `-v1`/`-v1:0` tag, after a Bedrock-style prefix;
  - `:batch`, `:free`, `:nitro`, `:floor` and `:exacto`;
  - `@default` and `@latest`;
  - a vendor head, before that vendor's own family word.

  Everything else stays a name token, so the remaining failure is a SPLIT.
- **What the grammar cannot see.** Two sources that spell a name identically are one model to it.
  Where a vendor reused one name for two releases, the sources themselves do not say which one they
  mean: `claude-3.5-sonnet` (2024-06 and 2024-10), and `mistral-7b-instruct`, undated on both
  Arena and OpenRouter. Only a curated rule can split those.
- **Claude Fable 5.1.** `assistant`'s top score (1507.6) was credited to Fable 5 by the leak P3
  fixed. It is Fable 5.1's.

## Surfaces and the unlimited-budget picks (Q = Best Quality, V = Best Value, P = Budget Pick)

| surface | models (served → derived) | served | with derived |
|---|---|---|---|
| abstract | 39 → 68 | Q: Gemini 3.1 Pro (98.0); V: GPT-5.6 Terra (96.5); P: GPT-5.6 Luna (88.0) | Q: Claude Fable 5 (98.5); V: Gemini 3.7 Flash (95.5); P: DeepSeek V4 Flash (89.0) |
| agentic-coding | 13 → 18 | Q: Claude Opus 5 (72.8); V: GPT-5.6 Sol (69.4); P: GPT-5.6 Sol (69.4) | Q: Gemini 3.8 Flash (73.8); V: Gemini 3.8 Flash (73.8); P: Gemini 3.7 Flash (65.3) |
| assistant | 65 → 189 | Q: Claude Fable 5 (1507.6); V: Gemini 3.5 Flash (1482.1); P: DeepSeek V4 Flash (1431.8) | Q: Claude Fable 5.1 (1507.6); V: Muse Spark 1.1 (1480.2); P: DeepSeek V4 Flash (1431.8) |
| coding | 44 → 55 | Q: Claude Opus 4.7 (83.5); V: GLM-5.2 (78.7); P: DeepSeek V3.2 (70.0) | Q: Claude Opus 4.7 (83.5); V: GLM-5.2 (78.7); P: DeepSeek V3.2 (70.0) |
| computer-use | 33 → 42 | Q: GPT-5.5 (84.7); V: Gemini 3.1 Pro (80.2); P: GPT-5 mini (61.6) | Q: GPT-5.5 (84.7); V: Gemini 3.1 Pro (80.2); P: GPT-5 mini (61.6) |
| document | 29 → 34 | Q: Claude Opus 5 (1516.3); V: GPT-5.6 Sol (1482.7); P: GPT-5.6 Terra (1471.6) | Q: Claude Opus 5 (1516.3); V: GPT-5.6 Sol (1482.7); P: GPT-5.6 Terra (1471.6) |
| everyday | 58 → 151 | Q: GPT-5.6 Sol (161.7); V: GPT-5.6 Terra (159.0); P: DeepSeek V4 Flash (152.5) | Q: GPT-6 Astra (166.6); V: GPT-6 Astra (166.6); P: DeepSeek V4 Flash (154.5) |
| expert | 50 → 148 | Q: Gemini 3.1 Pro (94.4); V: DeepSeek V4 Flash (91.0); P: DeepSeek V4 Flash (91.0) | Q: GPT-6 Astra (95.8); V: DeepSeek V4 Flash (91.0); P: DeepSeek V4 Flash (91.0) |
| factuality | 59 → 105 | Q: Claude Fable 5 (1500.7); V: Gemini 3 Pro (1481.2); P: GPT-5.6 Luna (1459.1) | Q: Claude Fable 5.1 (1500.7); V: Gemini 3 Pro (1481.2); P: GLM-5.3-Flash (1468.8) |
| mathematics | 51 → 138 | Q: GPT-5.6 Sol (100.0); V: DeepSeek V4 Flash (94.4); P: DeepSeek V4 Flash (94.4) | Q: Qwen3.8 Max (100.0); V: DeepSeek V4 Flash (94.4); P: Qwen3.7 Flash (86.7) |
| search | 25 → 28 | Q: GPT-5.6 Sol (1257.3); V: GPT-5.6 Sol (1257.3); P: Grok 4.5 (1212.6) | Q: GPT-5.6 Sol (1257.3); V: GPT-5.6 Sol (1257.3); P: ernie-5.1 (1227.0) |
| search_factuality | 24 → 27 | Q: GPT-5.6 Sol (1247.5); V: GPT-5.6 Sol (1247.5); P: Grok 4.5 (1216.1) | Q: GPT-5.6 Sol (1247.5); V: GPT-5.6 Sol (1247.5); P: ernie-5.1 (1214.7) |
| vision | 41 → 85 | Q: Claude Fable 5 (1325.9); V: Gemini 3.6 Flash (1299.8); P: GPT-5.6 Luna (1258.5) | Q: Claude Fable 5 (1325.9); V: GLM-5.3-Flash (1298.7); P: GLM-5.3-Flash (1298.7) |
| web-dev | 49 → 86 | Q: Claude Opus 5 (1711.9); V: GPT-5.6 Sol (1620.3); P: DeepSeek V4 Flash (1576.5) | Q: GPT-6 Astra (1800.3); V: GPT-6 Astra (1800.3); P: DeepSeek V4 Flash (1580.2) |

## Median price per surface ($/1M blended), which D-132's price guard also compares

| surface | served | with derived | move |
|---|---|---|---|
| abstract | $3.94 | $3.25 | -18% |
| agentic-coding | $4.50 | $3.72 | -17% |
| assistant | $2.95 | $0.83 | -72% |
| coding | $2.96 | $2.95 | -1% |
| computer-use | $3.01 | $1.66 | -45% |
| document | $3.94 | $3.47 | -12% |
| everyday | $3.00 | $1.08 | -64% |
| expert | $3.00 | $0.97 | -68% |
| factuality | $2.98 | $1.30 | -56% |
| mathematics | $3.00 | $0.99 | -67% |
| search | $5.25 | $4.71 | -10% |
| search_factuality | $5.38 | $4.92 | -8% |
| vision | $3.06 | $1.60 | -48% |
| web-dev | $2.98 | $1.69 | -43% |

## Why the nightly refresh will not publish this by itself

D-132 refuses the candidate on two guards (review MINOR-3), and both are the guard working:
- **New names:** a surface where more than 25% of the models were never served. `assistant` is 123 of
  188, `expert` 66%, down to `agentic-coding` 28%.
- **The median price:** eight surfaces move more than 25%. `assistant` goes $2.95 → $0.83 (-72%),
  because the derived roster adds many older, cheaper models. Every "cheaper by N%" sentence the app
  composes is relative to that median, so the owner sees this before publishing.

So the first artifact with derived models is published deliberately by the owner, with a hand-run
build that replaces the artifact. The nightly refresh guards from there.
