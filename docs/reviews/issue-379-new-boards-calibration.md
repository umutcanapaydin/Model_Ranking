---
record_type: review
id: issue-379-new-boards-calibration
status: candidate
process_version: v7.2
date: 2026-10-22
---
# #379 — the new boards measured: how many names link, and how `long-tasks`' thresholds were derived (D-219)

**Cited by `src/app/workflows/categories.py`.** D-219 serves four of #379's ten boards. For each, this note records the
unlinked-id count (a board under half linked is not served until its aliases are fixed) and, where a board is a
surface's primary, its D-148 calibration. A board that joins a family as a second board moves no threshold: the floor
of every board is derived from its rows each time it is read (D-148 clause 1, D-159), and the surface's window and tie
margin stay its primary's.

## The artifact measured

A copy of the Mac's artifact (the engine service's of 2026-10-15), with each new board ingested through its own
registered ingest from the recorded fixture (`tests/fixtures/`), then the build's own `registry.reconcile` and
`rank.build_price_medians`. Nothing else changed, and no alias was added.

## The unlinked-id count

| board | source | rows stored | skipped | linked | priced models | unlinked |
|---|---|---:|---:|---:|---:|---|
| OSWorld-Verified | `osworld_verified` | 20 | 1 | 15 | 15 | `doubao-1-5-thinking-vision-pro-250428`, `doubao-1-5-thinking-vision-pro-250717`, `kimi-vl-a3b`, `UI-TARS-250705`, `qwen3-vl-flash-2025-10-25` |
| METR time horizons | `metr_time_horizons` | 26 | 0 | 20 | 20 | `davinci-002`, `gpt2`, `gpt-4-1106`, `gpt-4-turbo`, `o1`, `claude-mythos-preview-early` |
| LiveBench 2.0 | `livebench` | 49 | 0 | 42 | 42 | `beam-1.0`, `deepseek-v4-flash-vision`, `deepseek-v4.1-flash-1017`, `minimax-m3.1-flash`, `nemotron-lightning-3.5`, `nemotron-super-vl-3.5`, `nemotron-ultra-3` |
| SimpleBench | `simplebench` | 106 | 2 | 91 | 85 | `Claude Fable`, `Ox Alpha`, `Nemotron 3 Ultra`, `Claude 3.5 Sonnet 10-22`, `Claude 3.5 Sonnet 06-20`, `o1-2024-12-17 (med)`, `o1-mini`, `GPT-4.5`, `GPT-4 Turbo`, `GPT-4o mini`, `Gemini 2.0 Flash Thinking`, `Gemini 2.0 Flash Exp`, `Gemini 1.5 Pro 002`, `Mistral Large v2`, `Command R+` |

- OSWorld-Verified's skipped row is Coasty CUA v1, whose run used an extra accessibility tree or coding action
  (D-219 clause 2). The unlinked names are models no catalogue entry prices.
- METR's unlinked names are models no catalogue entry prices today (GPT-2, davinci-002, an early preview) or spellings
  the registry does not read as a priced model (`o1`, `gpt-4-turbo`, `gpt-4-1106`); each is a model of 2024 or
  earlier but the preview, so no surface's leaders are missing.

- LiveBench's `minimax-m3.1-flash` first read as MiniMax M3: the curated rule took any `minimax-m3` prefix. The rule
  now stops before a point release, as MiniMax M2's does, so M3.1 Flash is unlinked until a catalogue prices it, and
  MiniMax M3 keeps its own score. The count above is after that fix.
- SimpleBench's two skipped rows are its human baselines. Its 91 linked names reach 85 models: a dated snapshot
  (Gemini 2.5 Pro's 03-25 and 06-05, DeepSeek R1's 05/28, DeepSeek V3's 03-24), a thinking or preview run beside the
  plain one, and `GPT-5.6 Sol Pro (xhigh)` beside `GPT-5.6 Sol (xhigh)`, which the registry reads as one model as it
  reads Sol's Pro mode on every board (Epoch's `_promax` rows, the catalogue's `-pro` alias at Sol's price). A board
  ranks a model by its best row, as on every board. Most of the unlinked names are models of 2024 no catalogue
  prices now.

## `long-tasks` (D-218 clause 2)

```
PYTHONPATH=src .venv/bin/python scripts/calibrate_surface.py --surface long-tasks --db <the copy> \
    --stderr 21.862 --stderr-from "METR's published 95% interval of each model's 50% time horizon \
    (benchmark_results_1_1.yaml, (ci_high - ci_low) / (2 x 1.96)), median of its 26 models, read 2026-10-22" \
    --out docs/research/issue-379-long-tasks-calibration.json
```

| Threshold | Value | How |
|---|---|---|
| floor | 223.7 minutes | the top third of the board's 26 rows (D-148 clause 1, D-159; computed by the build, not kept) |
| ranked population | 20 | the models that reconcile and carry a price (`rank.ranked_population`) |
| `close_call` | 43.7 minutes | twice METR's own error: each model's published 95% interval, halved by 1.96, median 21.862 minutes |
| `value_window` | 401.5 minutes | eight models stand at or above the floor; the first gap wider than 43.7 past three candidates is 341.7 to 293.0 minutes, and its middle is 401.5 below the leader (Claude Opus 4.6, 718.8) |

`score_anchor` stays unset: the engine pins it on an Elo surface only (D-162), and minutes are their own scale (D-105).

## What the numbers cost, stated

- **A wide window in minutes.** METR's intervals are wide (Claude Opus 4.6's runs from 317 to 3,634 minutes), so the
  tie margin is 43.7 minutes and Best Value reaches GPT-5.4 at 341.7.
- **An older board.** METR's newest model was released on 2026-04-07; the page says it was updated "while this page was
  being maintained". Its rows are undated (D-139), so the list says its evidence is undated, as D-188 clause 4 has it.
- **When METR publishes a new time-horizon version,** the source moves to it and this calibration is run again.

## Routing to `long-tasks`, measured

`make model-tier` (`scripts/model_tier.py`) on this branch and on the integration head (`9c8f499`), each tier's rows
compared question by question (`--compare`), on the golden set (49 questions) and the m24 held-out set (173):

| tier | golden | m24 |
|---|---|---|
| Apple Intelligence (model tier) | 41 -> 42 of 49 (net +1) | 154 -> 156 of 173 (net +2, McNemar p=0.625) |
| wording tier, first examples | net -2 | net -1 |
| wording tier, shipped examples | 22 -> 21 of 49 (net -1) | 84 -> 85 of 173 (net +1) |

No question of either set reaches `long-tasks` on the model tier. The first examples ("which ai can work on one task
for hours", "an assistant that ...") drew ordinary questions there on the wording tier; the shipped ones name the
length of the job in hours and days. The wording probe's English replica (`scripts/router_probe/probe.swift`) holds
`probe_questions.json` and `heldout_questions.json`, and loses two Turkish questions of `coding_tuning_questions.json`
to near-ties (a Flutter crash, a lease to summarise); the app reads both by their words (`flutter`, `sozlesme`) before
any embedding. Every Swift test stays green.
