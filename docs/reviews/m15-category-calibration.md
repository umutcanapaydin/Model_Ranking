---
record_type: review
id: m15-category-calibration
status: ratified
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

*(M15 closure: that script lives outside the repository -- M15-W3 review m-5. What it runs, from
the repository root, is one command per board:)*

```
.venv/bin/python -B scripts/calibrate_board.py --config vision --out build/vision.json
.venv/bin/python -B scripts/calibrate_board.py --config search --out build/search.json
.venv/bin/python -B scripts/calibrate_board.py --config search_factuality --out build/search_factuality.json
```

## The rules applied, and why each is the one the product already ships

| Threshold | Rule | Where the rule comes from |
|---|---|---|
| `min_quality` | top third of the WHOLE board, over distinct models | D-145, and W-094's measurement: nine of the eleven shipped floors sit closer to this rule than to the ranked-population one (`docs/research/m15-board-survey-2026-09-21.md`) |
| `close_call` | median rating gap among pairs whose PUBLISHED 95% intervals overlap | the M14-W2 rule — the board's own statement of what it cannot tell apart |
| `value_window` | 4 × `close_call` | the ratio `assistant` ships (30 against 8) |
| `score_anchor` | the floor as pinned today, and pinned separately | D-146 clause 2: a recalibration must not move every card's number |

## The measurement

*The `ranked`, pairs, `close_call` and window columns below are superseded by the 2026-09-22
correction at the end of this record (W-113). The floors stand.*

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

**2. The ranked count for `vision` disagrees between two runs.** *(Resolved 2026-09-22 at the
M15 closure -- see the correction at the end of this record. The paragraph below is kept as it
was written.)* The W1 survey (2026-09-21 21:55) counted 41 rankable models on `vision`; this
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

## Correction, 2026-09-22 (M15 closure) -- W-113 resolved, and two tie margins moved

Both scripts were run on the same artifact minutes apart: `survey_boards.py` said 41, this script
said 64. Same data, so the difference was the counting. **41 is right.** This script counted board
NAMES that map to a ranked model; one model often sits on a board under two or three names (a dated
snapshot, a thinking variant -- `GPT-4o` three times, `Claude 4 Sonnet` three times), so 64 names
were 41 models. The "moved by one" on the two smaller boards was the same defect, not a day of
price movement: 25 and 24 models, 26 and 25 names.

It did not stop at the count. `close_call` paired every name with every other, so a model was
paired with its own snapshot and every snapshot was paired with every neighbour again. On
`search_factuality` the near-zero self-pairs pulled the median down; on `vision` the duplicated
neighbour pairs (333 against 156) outweighed them and held it up. Either way the median described
names, not models. Re-measured over one name
per model -- its best-rated one, the score the engine ranks it on:

| board | ranked models | overlapping pairs | floor (D-145) | close_call | window |
|---|---|---|---|---|---|
| vision | 41 | 156 | 1248.2 (unchanged) | **7.8** (was 8.1) | **31.2** (was 32.3) |
| search | 25 | 44 | 1206.9 (unchanged) | 6.5 (unchanged) | 25.9 (unchanged) |
| search_factuality | 24 | 39 | 1203.7 (unchanged) | **4.9** (was 4.2) | **19.5** (was 17.0) |

The owner ruled the corrected margins in (2026-09-22) and `categories.py` carries them. Floors and
anchors do not move: the floor is computed over the whole board and never read the ranked count.
The script now counts models (`ranked_population`) and prints the name count beside it
(`rankable_board_names`); `tests/unit/test_calibrate_board.py` pins the one-name-per-model step and
fails on the old pairing.
