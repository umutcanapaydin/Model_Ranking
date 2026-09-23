---
record_type: register
id: m16-w4-derived-registry-2026-09-23
status: ratified
process_version: v6.0
date: 2026-09-23
---
# M16-W4 — what the derived registry changes (D-157), measured

**Measured 2026-09-23** on a candidate built from live upstreams plus a freshly fetched Epoch bundle
(`python -m app.workflows.build --epoch-dir <bundle>`), compared with the served artifact. Both
effects of this wave are in it: fresh Epoch data (P1, P2) and derived registration (P4).

- **Score rows that match no model:** 1,450 of 2,834 before; **661 of 2,581** after.
- **Models registered:** 74 before; **316** after, 242 of them new. Every new model has a price and
  a score under one derived id (D-157's threshold). Spot-checked merges: GPT-6 Astra (12 price
  aliases, 7 score names), Kimi K3, Gemini 3.7 Flash, gpt-oss-120b, Claude Fable 5.1; variants and
  dated releases stay separate (`o3-2025-04-16`, `gpt-5.2-pro-2025-12-11`).
- **Claude Fable 5.1.** `assistant`'s top score (1507.6) was credited to Fable 5 by the leak P3 fixed;
  it is Fable 5.1's.

## Surfaces and the unlimited-budget picks (Q = Best Quality, V = Best Value, P = Budget Pick)

| surface | models (served → derived) | unlimited picks, served | unlimited picks, with derived |
|---|---|---|---|
| abstract | 39 → 68 | Q: Gemini 3.1 Pro (98.0); V: GPT-5.6 Terra (96.5); P: GPT-5.6 Luna (88.0) | Q: Claude Fable 5 (98.5); V: Gemini 3.7 Flash (95.5); P: DeepSeek V4 Flash (89.0) |
| agentic-coding | 13 → 18 | Q: Claude Opus 5 (72.8); V: GPT-5.6 Sol (69.4); P: GPT-5.6 Sol (69.4) | Q: Gemini 3.8 Flash (73.8); V: Gemini 3.8 Flash (73.8); P: Gemini 3.7 Flash (65.3) |
| assistant | 65 → 188 | Q: Claude Fable 5 (1507.6); V: Gemini 3.5 Flash (1482.1); P: DeepSeek V4 Flash (1431.8) | Q: Claude Fable 5.1 (1507.6); V: Muse Spark 1.1 (1480.2); P: DeepSeek V4 Flash (1431.8) |
| coding | 44 → 55 | Q: Claude Opus 4.7 (83.5); V: GLM-5.2 (78.7); P: DeepSeek V3.2 (70.0) | Q: Claude Opus 4.7 (83.5); V: GLM-5.2 (78.7); P: DeepSeek V3.2 (70.0) |
| computer-use | 33 → 42 | Q: GPT-5.5 (84.7); V: Gemini 3.1 Pro (80.2); P: GPT-5 mini (61.6) | Q: GPT-5.5 (84.7); V: Gemini 3.1 Pro (80.2); P: GPT-5 mini (61.6) |
| document | 29 → 34 | Q: Claude Opus 5 (1516.3); V: GPT-5.6 Sol (1482.7); P: GPT-5.6 Terra (1471.6) | Q: Claude Opus 5 (1516.3); V: GPT-5.6 Sol (1482.7); P: GPT-5.6 Terra (1471.6) |
| everyday | 58 → 151 | Q: GPT-5.6 Sol (161.7); V: GPT-5.6 Terra (159.0); P: DeepSeek V4 Flash (152.5) | Q: GPT-6 Astra (166.6); V: GPT-6 Astra (166.6); P: DeepSeek V4 Flash (154.5) |
| expert | 50 → 146 | Q: Gemini 3.1 Pro (94.4); V: DeepSeek V4 Flash (91.0); P: DeepSeek V4 Flash (91.0) | Q: GPT-6 Astra (95.8); V: DeepSeek V4 Flash (91.0); P: DeepSeek V4 Flash (91.0) |
| factuality | 59 → 105 | Q: Claude Fable 5 (1500.7); V: Gemini 3 Pro (1481.2); P: GPT-5.6 Luna (1459.1) | Q: Claude Fable 5.1 (1500.7); V: Gemini 3 Pro (1481.2); P: GLM-5.3-Flash (1468.8) |
| mathematics | 51 → 136 | Q: GPT-5.6 Sol (100.0); V: DeepSeek V4 Flash (94.4); P: DeepSeek V4 Flash (94.4) | Q: Qwen3.8 Max (100.0); V: DeepSeek V4 Flash (94.4); P: Qwen3.7 Flash (86.7) |
| search | 25 → 28 | Q: GPT-5.6 Sol (1257.3); V: GPT-5.6 Sol (1257.3); P: Grok 4.5 (1212.6) | Q: GPT-5.6 Sol (1257.3); V: GPT-5.6 Sol (1257.3); P: ernie-5.1 (1227.0) |
| search_factuality | 24 → 27 | Q: GPT-5.6 Sol (1247.5); V: GPT-5.6 Sol (1247.5); P: Grok 4.5 (1216.1) | Q: GPT-5.6 Sol (1247.5); V: GPT-5.6 Sol (1247.5); P: ernie-5.1 (1214.7) |
| vision | 41 → 83 | Q: Claude Fable 5 (1325.9); V: Gemini 3.6 Flash (1299.8); P: GPT-5.6 Luna (1258.5) | Q: Claude Fable 5 (1325.9); V: GLM-5.3-Flash (1298.7); P: GLM-5.3-Flash (1298.7) |
| web-dev | 49 → 86 | Q: Claude Opus 5 (1711.9); V: GPT-5.6 Sol (1620.3); P: DeepSeek V4 Flash (1576.5) | Q: GPT-6 Astra (1800.3); V: GPT-6 Astra (1800.3); P: DeepSeek V4 Flash (1580.2) |

## Why the nightly refresh will not publish this by itself

D-132 refuses a candidate whose surface is more than 25% models the artifact has never served
("a board adds models one or two at a time"). This candidate is: `assistant` 123 of 188, `everyday`
95 of 151, and more. That refusal is the guard working -- a roster change this large is a decision,
not upstream movement -- so the first artifact with derived models is published deliberately by the
owner (a hand-run build replaces the artifact), and the nightly refresh guards from there.

The D-148 floors are also measured on these boards; with fresh data several move (see the PR).
