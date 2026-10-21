---
record_type: review
id: issue-265-agentic-coding-calibration
status: candidate
process_version: v7.2
date: 2026-10-21
---
# #265 — how `agentic-coding`'s thresholds were derived on Datacurve's own DeepSWE leaderboard (D-216)

**Cited by `src/app/workflows/categories.py`.** D-216 moves `agentic-coding` from Epoch's copy of the DeepSWE board
(`epoch_deepswe_external`) to Datacurve's own leaderboard (`datacurve_deepswe`), the JSON its site loads. A threshold measured on one board does not transfer to another (D-105), so the surface
was calibrated again, by the rule D-194 clause 4 applied to `computer-use` and `abstract`, on the list the source
reads. The record the script wrote is `docs/research/d216-agentic-coding-calibration.json`, and
`tests/unit/test_calibrate_surface.py` pins the shipped pair to it and the record to the rule.

## The board measured

- **The artifact.** A copy of the Mac's artifact of 2026-10-21 (`main` at `c29317c`), with `epoch_deepswe_external`'s
  rows removed and the source ingested live through its own registered ingest, which read the leaderboard (every row's
  link is `https://deepswe.datacurve.ai/`). Then the build's own reconcile and price medians. Nothing else changed.
- **The board.** Datacurve's leaderboard v1.1 (`leaderboard-live.json`), compiled 2026-09-22, newest job 2026-09-01:
  70 configurations over 28 models, all `mini-swe-agent`, 113 tasks each. Stored 70, skipped 0, effort unknown 0.
- **Ids.** All 70 rows link a catalogue model and all 28 models carry a price, through the curated rules and the
  derived identities (D-157). No alias was added.
- **Efforts** (D-216 clause 3), as the leaderboard states them: 18 rows at `high`, and Kimi K2.7 Code, which states
  none and ran at its default, stands at `high` too; 14 `xhigh`, 14 `max`, 12 `medium`, 11 `low`.

## The rule and the numbers

```
PYTHONPATH=src .venv/bin/python scripts/calibrate_surface.py --surface agentic-coding --db <the copy> \
    --stderr 1.313 --stderr-from "Datacurve's published 95% run-to-run interval per row of its leaderboard \
    (leaderboard-live.json v1.1, ci_half / 1.96), median of its 70 rows, read 2026-10-21" \
    --out docs/research/d216-agentic-coding-calibration.json
```

| Threshold | Value | How |
|---|---|---|
| floor | 67.0 | the top third of the board's 70 rows, every effort (D-148 clause 1, D-159; computed by the build, not kept) |
| ranked population | 19 | the models ranked at `high` that reconcile and carry a price (`rank.ranked_population`) |
| `close_call` | 2.6 | twice the board's own standard error. Datacurve publishes a 95% run-to-run interval for each row (`ci_half`, "1.96 * std(runs)/sqrt(R)"); halved by 1.96 the median is 1.313 points |
| `value_window` | 3.0 | five models stand above the floor at `high`: Gemini 3.8 Flash 73.8, GPT-6 Astra 73.2, Claude Opus 5 72.8, GPT-5.6 Sol 69.4, Claude Fable 5 68.6. The first gap wider than 2.6 past three candidates is 72.8 to 69.4; its middle is 2.7 below the leader |

**The rounding defect this found.** The script rounds the window to the half point, and 2.7 rounded to 2.5, below the
close call of 2.6. `test_categories.py` refused it: a window narrower than the tie margin would exclude a model the
surface calls level with the leader. The script now takes the half point above in that case (3.0), which stays inside
the gap (69.4 is 4.4 below the leader). The D-194 records are unchanged by it.

Epoch's copy shipped `value_window` 6.0 and `close_call` 1.5, measured on an older snapshot of this list on M8's rule;
they are not carried over.

## What the numbers cost, stated

- **A narrow value window.** Best Value reaches the top three at `high` (3.0 points); GPT-5.6 Sol and Claude Fable 5
  stand above the floor but outside the window, because the board tells them apart from the leaders.
- **Undated evidence.** The leaderboard names no date per row (D-216 clause 4), so the surface says its evidence is
  undated, as it did on Epoch's copy.
- **A night the site fails** is carried by the refresh (D-156): the previous night's rows, these thresholds.
- **When Datacurve publishes a new leaderboard version,** this calibration is run again.
