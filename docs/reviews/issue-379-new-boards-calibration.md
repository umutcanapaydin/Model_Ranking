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
| LiveBench 2.0 | `livebench` | 49 | 0 | 43 | 42 | `beam-1.0`, `deepseek-v4-flash-vision`, `deepseek-v4.1-flash-1017`, `nemotron-lightning-3.5`, `nemotron-super-vl-3.5`, `nemotron-ultra-3` |

- OSWorld-Verified's skipped row is Coasty CUA v1, whose run used an extra accessibility tree or coding action
  (D-219 clause 2). The unlinked names are models no catalogue entry prices.
- METR's unlinked names are models no catalogue entry prices today (GPT-2, davinci-002, an early preview) or spellings
  the registry does not read as a priced model (`o1`, `gpt-4-turbo`, `gpt-4-1106`); each is a model of 2024 or
  earlier but the preview, so no surface's leaders are missing.

- LiveBench's 43 linked names reach 42 models: `minimax-m3.1-flash` read as MiniMax M3, a curated rule that took
  any `minimax-m3` prefix. The rule now stops before a point release, as MiniMax M2's does, so M3.1 Flash is its
  own model and MiniMax M3 keeps its own score.

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
