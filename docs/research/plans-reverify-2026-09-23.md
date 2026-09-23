---
record_type: register
id: plans-reverify-2026-09-23
status: ratified
process_version: v6.0
date: 2026-09-23
---
# Plan and roster re-verification, 2026-09-23 -- what changed and what it moves

**Why now.** Every row of `data/plans.yaml` and `data/rosters.yaml` was verified on 2026-08-15, and
the 30-day window (REQ-SUB-004, REQ-ING-009) ran out on 2026-09-14. The `plan-staleness` CI job
went red on every PR from then on. The evidence for each value is in the two files' header notes.

## What changed on the pages

- **OpenAI.** `chatgpt.com/pricing` now renders amounts (unchanged: Go $8, Plus $20, Pro from
  $100) and a per-plan compare table of models. **Owner ruling 2026-09-23: that table is an
  explicit statement** (translated from Turkish: "yes, the table counts"), so the three ChatGPT
  plans now list every model the table marks Yes, Expanded or Unlimited. Plus moved from "GPT-5.6"
  to the GPT-6 family. The $200 Pro 20x tier has been closed to new sign-ups since 2026-09-10.
- **Anthropic.** Prices unchanged; "Claude Cowork" is gone from the Pro card. The page still names
  model families only, so Claude Pro and Max stay unscored.
- **Google.** Prices unchanged. The Ultra card states Gemini 3 Pro in AI Mode, which the 2026-08-15
  row missed.
- **Perplexity.** Prices unchanged. The help-centre table swapped Gemini 3.1 Pro for Gemini 3.7
  Flash, GLM 5.2 for GLM 5.3 and Grok 4.5 for Grok 4.6 on both plans.

## A leak the new data exposed

"GPT-5 Thinking Mini" linked to **GPT-5**: the parent rule's lookahead only saw a variant token
directly after the version (REQ-CAN-002, the spike bug's shape). `registry.py` now reads a
"thinking" word before `mini`/`nano`; `tests/unit/test_registry.py` holds it.

## Names that do not link yet

GPT-6 Astra, GPT-6 Sol, GPT-6 Luna, Gemini 3.7 Flash, GLM 5.3, Kimi K3, Nemotron 3 Ultra and
Sonar 2 have no registry rule. They drop and are counted. The GPT-6 family already has scores on
Arena and Epoch and prices on LiteLLM; the registry work that makes it rank is its own change.

## What it moves (the CLI subscription answer; `/v1` and the app do not serve plans)

Measured on the same artifact (a fresh build of 2026-09-23), only the plan tables replaced. Labels
that moved:

| surface | budget | label | before | after |
|---|---|---|---|---|
| agentic-coding | low | best_quality | Google AI Plus (11.7) | ChatGPT Go (44.2) |
| agentic-coding | low | best_value | Google AI Plus (11.7) | ChatGPT Go (44.2) |
| agentic-coding | medium | best_quality | Perplexity Pro (53.8) | ChatGPT Plus (69.4) |
| agentic-coding | medium | best_value | Perplexity Pro (53.8) | ChatGPT Plus (69.4) |
| agentic-coding | medium | budget_pick | Perplexity Pro (53.8) | ChatGPT Plus (69.4) |
| agentic-coding | unlimited | best_value | ChatGPT Pro (69.4) | ChatGPT Plus (69.4) |
| agentic-coding | unlimited | budget_pick | Perplexity Pro (53.8) | ChatGPT Plus (69.4) |
| coding | medium | best_quality | Perplexity Pro (78.7) | Google AI Pro (77.4) |
| coding | unlimited | best_quality | Perplexity Pro (78.7) | Google AI Pro (77.4) |
| document | low | best_quality | Google AI Plus (1443.9) | ChatGPT Go (1456.9) |
| document | medium | best_quality | Perplexity Pro (1471.6) | ChatGPT Plus (1482.7) |
| document | medium | best_value | Google AI Plus (1443.9) | ChatGPT Go (1456.9) |
| document | medium | budget_pick | Perplexity Pro (1471.6) | ChatGPT Plus (1482.7) |
| document | unlimited | best_value | ChatGPT Pro (1482.7) | ChatGPT Plus (1482.7) |
| document | unlimited | budget_pick | Perplexity Pro (1471.6) | ChatGPT Plus (1482.7) |
| everyday | low | best_quality | Google AI Plus (154.8) | ChatGPT Go (156.1) |
| everyday | medium | best_quality | Perplexity Pro (159.0) | ChatGPT Plus (161.7) |
| everyday | medium | best_value | Perplexity Pro (159.0) | ChatGPT Plus (161.7) |
| everyday | unlimited | best_quality | ChatGPT Pro (161.7) | ChatGPT Plus (161.7) |
| everyday | unlimited | best_value | Perplexity Pro (159.0) | ChatGPT Plus (161.7) |
| mathematics | low | best_quality | Google AI Plus (95.6) | ChatGPT Go (98.3) |
| mathematics | medium | best_quality | Perplexity Pro (99.7) | ChatGPT Plus (100.0) |
| mathematics | unlimited | best_quality | ChatGPT Pro (100.0) | ChatGPT Plus (100.0) |
| search | medium | best_quality | Perplexity Pro (1212.6) | ChatGPT Plus (1257.3) |
| search | medium | best_value | Google AI Plus (1210.5) | ChatGPT Plus (1257.3) |
| search | unlimited | best_quality | ChatGPT Pro (1257.3) | ChatGPT Plus (1257.3) |
| search | unlimited | best_value | ChatGPT Pro (1257.3) | ChatGPT Plus (1257.3) |
| search_factuality | medium | best_quality | Perplexity Pro (1216.1) | ChatGPT Plus (1247.5) |
| search_factuality | medium | best_value | Google AI Plus (1198.4) | ChatGPT Plus (1247.5) |
| search_factuality | medium | budget_pick | Perplexity Pro (1216.1) | ChatGPT Plus (1247.5) |
| search_factuality | unlimited | best_quality | ChatGPT Pro (1247.5) | ChatGPT Plus (1247.5) |
| search_factuality | unlimited | best_value | ChatGPT Pro (1247.5) | ChatGPT Plus (1247.5) |
| search_factuality | unlimited | budget_pick | Perplexity Pro (1216.1) | ChatGPT Plus (1247.5) |
| web-dev | low | best_quality | Google AI Plus (1446.6) | ChatGPT Go (1518.9) |
| web-dev | low | budget_pick | Google AI Plus (1446.6) | ChatGPT Go (1518.9) |
| web-dev | medium | best_quality | Perplexity Pro (1593.2) | Perplexity Pro (1617.6) |
| web-dev | medium | best_value | Perplexity Pro (1593.2) | ChatGPT Go (1518.9) |
| web-dev | medium | budget_pick | Perplexity Pro (1593.2) | ChatGPT Go (1518.9) |
| web-dev | unlimited | best_value | Perplexity Pro (1593.2) | Perplexity Pro (1617.6) |
| web-dev | unlimited | budget_pick | Perplexity Pro (1593.2) | ChatGPT Go (1518.9) |

40 label changes across 42 answers

Two effects produce almost all of it: the ChatGPT plans became scoreable (before, only Pro was, on
GPT-5.6 Sol Pro), and Perplexity lost Gemini 3.1 Pro from its roster, so on `coding` it no longer
has a linked model with a SWE-bench score and drops to unscored.
