---
record_type: review
id: issue-265-agentic-coding-calibration
status: candidate
process_version: v7.2
date: 2026-10-21
---
# #265 — how `agentic-coding`'s thresholds were derived on Datacurve's DeepSWE dataset (D-216)

**Cited by `src/app/workflows/categories.py`.** D-216 moves `agentic-coding` from Epoch's copy of the DeepSWE board
(`epoch_deepswe_external`) to Datacurve's own dataset (`datacurve_deepswe`, CC BY 4.0). A threshold measured on one
board does not transfer to another (D-105), so the surface was calibrated again, by the rule D-194 clause 4 applied
to `computer-use` and `abstract`. The record the script wrote is `docs/research/d216-agentic-coding-calibration.json`,
and `tests/unit/test_calibrate_surface.py` pins the shipped pair to it and the record to the rule.

## The board measured

- **The artifact.** A copy of the Mac's artifact of 2026-10-21 (`main` at `c29317c`), with `epoch_deepswe_external`'s
  rows removed and the live board ingested through the source's own registered ingest, with the owner's token. Then
  the build's own reconcile and price medians. Nothing else in the copy changed.
- **The board.** The job `20260606-deep-swe-leaderboard-all-4x`, the only one the dataset lists: 27 runs over 19
  models, all by `mini-swe-agent`, each run 4 times over 113 tasks. Stored 27, skipped 0, effort unknown 0.
- **Ids.** All 27 runs link a catalogue model and all 19 models carry a price: 24 runs through the curated rules,
  3 (`grok-build-0-1`, `mimo-v2-5-pro`, `qwen3-6-plus`) through the derived identities (D-157). No alias was added.
- **Efforts** (D-216 clause 2), as the job's config states them, and as each run's published summary repeats them:
  15 at `high` (4 stated, 11 given no effort, at their model's default), 5 at `xhigh`, 4 at `medium`, 3 at `max`.

## The rule and the numbers

```
PYTHONPATH=src .venv/bin/python scripts/calibrate_surface.py --surface agentic-coding --db <the copy> \
    --stderr 1.445 --stderr-from "Datacurve's published 95% run-to-run interval per run (summary.json ci_half / 1.96), \
    median of the job's 27 runs, read 2026-10-21" --out docs/research/d216-agentic-coding-calibration.json
```

| Threshold | Value | How |
|---|---|---|
| floor | 47.3 | the top third of the board's 27 rows, every effort (D-148 clause 1, D-159; computed by the build, not kept) |
| ranked population | 15 | the models ranked at `high` that reconcile and carry a price (`rank.ranked_population`) |
| `close_call` | 2.9 | twice the board's own standard error. Datacurve publishes a 95% run-to-run interval for each run (its summary file's `ci_half`, "1.96 * std(runs)/sqrt(R)"); halved by 1.96 it is 0.22 to 2.41 points, median 1.445 |
| `value_window` | 14.5 | two models stand above the floor (GPT-5.5 at 61.9, Claude Opus 4.8 at 50.7), fewer than the three a gap needs, so the window reaches the floor: 61.9 - 47.3, to the half point |

Epoch's copy shipped `value_window` 6.0 and `close_call` 1.5. They were measured on a board of 68 rows over 25 models,
18 ranked at `high`; they are not carried over.

## What the numbers cost, stated

- **Two models above the floor.** The floor is taken over every effort on the board, and the board's top rows are
  `xhigh` and `max` runs, so at `high` only GPT-5.5 and Claude Opus 4.8 clear it. The surface's Best Quality and Best
  Value come from those two, and a Budget Pick must clear 47.3. Under Epoch's copy the same rule held more models,
  because that board was larger and newer. The owner ruled on 2026-09-23 that this surface takes no exception to the
  floor rule (D-148); that ruling is not reopened here.
- **An older board.** The dataset's one job finished on 2026-06-06, 137 days before this measurement, and the newest
  models on Epoch's copy are not in it. The evidence is now dated, so the surface says how old it is.
- **When Datacurve publishes a new job,** the source reads it with no code change, and this calibration is run again.
