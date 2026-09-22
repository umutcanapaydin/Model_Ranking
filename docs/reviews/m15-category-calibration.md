---
record_type: review
id: m15-category-calibration
status: draft
process_version: v5.0
date: 2026-09-22
---
# M15-W3 — how the three new surfaces' thresholds were derived

**Cited by `src/app/workflows/categories.py`.** Every number the three new surfaces ship comes from
one run of `scripts/calibrate_board.py` on the owner's machine, 2026-09-22 14:27
(`m15-runs/calib-20260922-142701/`), and can be reproduced with:

```
bash ~/Desktop/terminal_output/model_ranking/calibrate_new.sh
```

## The rules applied, and why each is the one the product already ships

| Threshold | Rule | Where the rule comes from |
|---|---|---|
| `min_quality` | top third of the WHOLE board, over distinct models | D-145, and W-094's measurement: nine of the eleven shipped floors sit closer to this rule than to the ranked-population one (`docs/research/m15-board-survey-2026-09-21.md`) |
| `close_call` | median rating gap among pairs whose PUBLISHED 95% intervals overlap | the M14-W2 rule — the board's own statement of what it cannot tell apart |
| `value_window` | 4 × `close_call` | the ratio `assistant` ships (30 against 8) |
| `score_anchor` | the floor as pinned today, and pinned separately | D-146 clause 2: a recalibration must not move every card's number |

## The measurement

| board | distinct models | ranked | lowest | leader | overlapping pairs | floor (D-145) | close_call | window |
|---|---|---|---|---|---|---|---|---|
| vision | 129 | 64 | 1163.2 | 1325.9 | 333 | **1248.2** | **8.1** | **32.3** |
| search | 33 | 26 | 1006.2 | 1257.3 | 46 | **1206.9** | **6.5** | **25.9** |
| search_factuality | 31 | 25 | 1131.9 | 1247.5 | 45 | **1203.7** | **4.2** | **17.0** |

`search_factuality`'s margin is the tightest of the three and its window follows it down: on that
board the crowd separates models more sharply than on `search`, which is what one would expect from
a question with a right answer.

## Two things stated rather than smoothed over

**1. The first run of this script reported `ranked_population: 0` for all three boards, and it was
right to.** `calibrate_board.py` read the ranked population out of `advisor.db`, and these boards
had never been ingested — a board is calibrated BEFORE it is served, by definition. The script now
stores and reconciles the fetched rows in a THROWAWAY COPY of the database, the way
`scripts/survey_boards.py` already did, and the real artifact is still never touched. The zero was
a true answer to the wrong question, and it is recorded here because the next person to see a zero
should know which question it answered.

**2. The ranked count for `vision` disagrees between two runs, and the disagreement is NOT
resolved.** The W1 survey (2026-09-21 21:55) counted 41 rankable models on `vision`; this
calibration (2026-09-22 14:27) counts 64. The two smaller boards moved by one each (25→26, 24→25),
which a day of price and registry movement explains; 41→64 is not that. The floors agree to the
decimal across both runs — 1248.2, 1206.9, 1203.7 — because the floor is computed over the whole
board and does not depend on the ranked population at all, so **no threshold this milestone ships
depends on the disputed number.** What does depend on it is the sentence "41 models we could
recommend", which is why it is in `docs/warnings.ledger.md` as W-113 rather than silently
corrected. Owning milestone: M15 closure.

## What was refused, from the same measurement

- **Every image and video board** (`image_edit`, `image_to_video`, `text_to_image`, `text_to_video`,
  `video_edit`): zero rankable models, all priced per image or per second. The pricing-basis ruling
  is what unblocks them, not more data.
- **The `*_style_control` boards**: the same boards with style effects controlled for — identical
  row counts, ranked populations within one model, floors within 5 Elo. Two answers to one question.
- **`webdev`**: 53 rankable, but the product already has a `web-dev` surface on Epoch's board. A
  candidate SECOND board for that surface (REQ-CAT-003 evidence), not a fifteenth surface.
- **The six `agent_*` boards**: a signed score with no published definition, direction that differs
  per board, and one whose models cannot be separated at all. Research before build.
