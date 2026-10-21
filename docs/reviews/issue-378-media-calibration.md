---
record_type: review
id: issue-378-media-calibration
status: ratified
process_version: v5.0
date: 2026-10-21
---
# #378 — how the five image and video surfaces' thresholds were derived

**Cited by `src/app/workflows/categories.py`** (`_MEDIA_CLOSE_CALL`). D-218 clause 1 opens LMArena's
image and video boards as five surfaces ranked on quality only: no price, no value window, no budget
filter. Each surface therefore ships two thresholds, not three, and both follow rules the product
already ships (D-148). Every number comes from one run of `scripts/calibrate_board.py` per board on
2026-10-21, against the live dataset, and can be reproduced from the repository root with:

```
PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config text_to_image --db advisor.db --out docs/research/issue-378-text_to_image-calibration.json
PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config image_edit --db advisor.db --out docs/research/issue-378-image_edit-calibration.json
PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config text_to_video --db advisor.db --out docs/research/issue-378-text_to_video-calibration.json
PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config image_to_video --db advisor.db --out docs/research/issue-378-image_to_video-calibration.json
PYTHONPATH=src .venv/bin/python scripts/calibrate_board.py --config video_edit --db advisor.db --out docs/research/issue-378-video_edit-calibration.json
```

## The rules applied

| Threshold | Rule | Where the rule comes from |
|---|---|---|
| floor (`min_quality`) | the top third of the board's rows, derived from the served board every time it is read | D-148 clause 1, D-159 |
| `score_anchor` | the floor, on an Elo surface | D-162 |
| `close_call` | the median rating gap among pairs of ranked models whose PUBLISHED 95% intervals overlap, over one name per model | the M14 rule the other Arena surfaces ship (`docs/reviews/m15-category-calibration.md`, W-113) |
| `value_window` | none: a surface ranked on quality only has no Best Value | D-218 clause 1 |

The ranked population of a quality-only surface is every model its board names that the build links
to a model id (`app.workflows.registry._reconcile_media`): no price is required, because none of these
models is priced per token.

## The measurement (boards as published on 2026-10-21)

| Surface | Board published | Rows | Ranked models | Overlapping pairs | Floor (top third of rows) | `close_call` |
|---|---|---:|---:|---:|---:|---:|
| `text_to_image` | 2026-10-07 | 82 | 82 | 166 | 1165.5 | 3.8 |
| `image_edit` | 2026-10-20 | 60 | 59 | 58 | 1357.8 | 3.4 |
| `text_to_video` | 2026-09-22 | 48 | 48 | 133 | 1347.9 | 12.3 |
| `image_to_video` | 2026-09-22 | 48 | 48 | 94 | 1384.9 | 9.9 |
| `video_edit` | 2026-08-27 | 10 | 10 | 8 | 1392.2 | 16.3 |

- `image_edit` drops one name: `ChatGPT Image Latest (High Fidelity, 20251216)`, a `-latest` alias, which
  moves by definition and names no one release (D-166).
- `video_edit` ranks ten models. D-218 clause 1 names the board, so it opens; clause 3's 15-model rule is
  for the new boards of #379. Its tie margin is the widest because so few models share its intervals.
- The floors are served values: they move with each board, as every floor does (D-159). The table
  records what they were on the day the margins were measured.
