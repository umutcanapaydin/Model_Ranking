---
record_type: brief
id: m15-board-survey-2026-09-21
status: draft
process_version: v5.0
date: 2026-09-21
---
# M15-W1 — every board of the dataset we already license, measured on one footing

**What this is.** The product reads 3 of the 22 boards in `lmarena-ai/leaderboard-dataset`. Which
of the other 19 could carry a surface is a question with a numeric answer — how many models on it
this engine could actually recommend — and M15's plan says measure it rather than argue it.

**How to reproduce.** `bash ~/Desktop/terminal_output/model_ranking/survey.sh`, which runs
`scripts/survey_boards.py --db advisor.db`. It writes nothing to the artifact: every board is
ingested into a throwaway copy, reconciled, and read through the engine's own `ranked_population`
(REQ-EVI-002). Run on the owner's machine 2026-09-21 21:55; neither agent lane can reach the
dataset API. Raw record: `m15-runs/20260921-215558/survey.json`.

**The method reproduces the surfaces already shipped**, which is the only reason to trust the rest
of the table: `text` → 65 ranked (live `assistant` ranks 65), `document` → 29 (29), `text_factuality`
→ 59 (59).

## The table

`ranked` is the column that decides anything: models that reconcile to the registry AND carry a
price median. `D145` and `ranked⅓` are the two candidate floor rules (W-094), same quantile,
different population.

| board | rows | distinct models | **ranked** | leader | spread | D145 floor | ranked⅓ floor |
|---|---|---|---|---|---|---|---|
| text * | 402 | 357 | **65** | 1507.6 | 193.2 | 1394.9 | 1450.6 |
| text_factuality * | 171 | 143 | **59** | 1500.7 | 139.3 | 1450.6 | 1460.7 |
| webdev | 127 | 105 | **53** | 1758.0 | 596.9 | 1510.1 | 1517.1 |
| vision | 152 | 129 | **41** | 1325.9 | 162.7 | 1248.2 | 1284.8 |
| document * | 44 | 36 | **29** | 1516.3 | 113.1 | 1467.5 | 1471.0 |
| search | 34 | 33 | **25** | 1257.3 | 251.1 | 1206.9 | 1210.5 |
| search_factuality | 32 | 31 | **24** | 1247.5 | 115.6 | 1203.7 | 1211.9 |
| the six `agent_*` boards | 46 | 42 | **21** | see below | | | |
| image_edit, image_to_video, text_to_image, text_to_video, video_edit | 10–78 | 10–78 | **0** | — | — | — | — |
| `*_style_control` (document, search, text, vision) | = their base board | | | | | | |

`*` = already read by the product.

**Three findings from the zeros and the duplicates.**

1. **Every image and video board ranks nothing**, exactly as M14-W1 measured for image editing: the
   models on them are priced per image or per second, and this engine only ranks what somebody can
   buy at a per-token price. That is not a data problem to solve in W3; it is the pricing-basis
   question the owner still owes a ruling on, and it now has five boards behind it instead of one.
2. **`*_style_control` boards are the same board with style effects controlled for** — identical
   row counts, ranked populations within one model, floors within 5 Elo. They are a methodological
   variant, not a new question, and giving a reader both would be two answers to one question.
3. **`webdev` here is LMArena's, and the product's `web-dev` surface is Epoch's.** 53 ranked models
   against Epoch's 49, on a different scale. This is a candidate SECOND board for an existing
   surface (REQ-CAT-003 evidence), not a twelfth surface.

## The six `agent_*` boards are a different kind of measurement

They publish `score`, not `rating`: a number with a 95% interval and an observation count, some of
them over two million observations. The Elo parser correctly drops every row, which is why the
first run of this survey reported them as empty.

| board | leader | last | median neighbour gap | ranked |
|---|---|---|---|---|
| agent | 13.7 | −14.0 | 0.9 | 21 |
| agent_bash_recovery_steps | 13.1 | −26.3 | 0.6 | 21 |
| agent_praise_complaint | 31.8 | −19.4 | 1.8 | 21 |
| agent_steerability | 11.1 | −6.6 | 0.8 | 21 |
| agent_task_outcome_explicit | 19.8 | −18.0 | 0.9 | 21 |
| agent_tool_hallucination | 0.4 | −1.2 | 0.0 | 21 |

**These are the boards closest to the questions the owner's coverage direction names** — *does it
invent tool calls*, *does it take a correction*, *does it recover when a command fails*. They are
already licensed, 21 ranked models each, and a rate needs no anchor, so D-143's "one score out of
100" would be an identity here rather than a conversion.

**And they cannot be served on this evidence.** Two things are unknown and one is a decision:

- **The scale is not documented in the rows.** The values go NEGATIVE (−26.3 at worst), so they are
  not a plain rate. A signed number that this project cannot define must not be printed to a reader
  as a score. The dataset's own documentation has to say what it is first.
- **Direction is per board.** A high `agent_steerability` is good; a high
  `agent_tool_hallucination` means a model that invents tool calls more often. Every ranking this
  engine computes assumes higher is better. Serving a lower-is-better board is an engine decision
  (an ADR), not a configuration value.
- `agent_tool_hallucination`'s median neighbour gap is **0.0** at one decimal: on today's numbers
  most of its models are indistinguishable, and a surface that cannot separate anybody is a list
  that looks like a ranking without being one (D-138's whole subject).

## W-094 answered, on all eleven shipped surfaces

The question has been open since M14-W2: `categories.py` says every threshold is sized on the
**ranked population**, while the two M14 surfaces were floored on the **whole board** by D-145.
Both rules were computed for every shipped surface from the live artifact (no network; the board
population is read from the `scores` table, the ranked population through `ranked_population`).

| surface | shipped floor | board ⅓ (D-145) | ranked ⅓ | closer to |
|---|---|---|---|---|
| coding | 65.0 | 66.6 | 75.8 | **board** |
| assistant | 1400.0 | 1394.9 | 1450.6 | **board** |
| agentic-coding | 50.0 | 67.2 | 64.4 | ranked |
| everyday | 149.9 | 144.6 | 153.2 | ranked |
| expert | 83.6 | 83.3 | 91.0 | **board** |
| mathematics | 84.4 | 86.4 | 95.6 | **board** |
| computer-use | 53.4 | 57.3 | 61.6 | **board** |
| abstract | 72.8 | 79.5 | 87.2 | **board** |
| web-dev | 1478.9 | 1480.0 | 1522.9 | **board** |
| document | 1467.5 | 1467.5 | 1471.0 | **board** (by construction) |
| factuality | 1450.6 | 1450.6 | 1460.7 | **board** (by construction) |

**Nine of eleven sit closer to the board rule, and the two that do not are the two thinnest
boards** (`agentic-coding` has 17 distinct models; `everyday` is the one ECI surface). So the rule
the product actually shipped is D-145's — the top third of the whole board over distinct models —
and the comment above the thresholds has been describing the other one since M8.

**Recommendation to the owner (his ruling, W-094):** adopt D-145's rule for all eleven, correct the
comment, and re-derive `agentic-coding` and `everyday` under it in W3 — 50.0 against a board third
of 67.2 is not a rounding difference, it is a floor that admits models the rule would refuse.

## What W1 recommends for W3

1. **`vision` (41 ranked)** — "reading a screenshot, a photo, a scanned page". The largest
   unclaimed board, ordinary Elo, no new engine behaviour.
2. **`search_factuality` (24) with `search` (25)** — "answering by looking it up, and getting it
   right". The retrieval-pricing worry from M14 is smaller than it looked: 24 of 31 models on the
   board already carry a per-token price in this artifact. What is still unpriced is the search
   call itself, and that is the same pricing-basis ruling the image boards need.
3. **`webdev` as a second board for `web-dev`**, not a new surface.
4. **The six `agent_*` boards: research, not build.** Find the dataset's definition of `score`,
   then bring the direction question back as an ADR. They are the best match to the product's
   stated direction and the worst match to its current engine.
5. **Nothing for image or video** until the pricing basis is ruled.

## Correction, 2026-09-22 — after the independent W1 review

`docs/reviews/m15-wave-1-review.md` (`seat: independent`) recomputed every number in this record
from the artifact with its own queries. **Every floor value above is right.** Three statements are
not, and they stand corrected here rather than edited above:

1. **"The rule the product actually shipped is D-145's" is wrong** (review M-1). The M8 floors are
   the top third of the board's ROWS, one per raw name, which is what `docs/reviews/m8-category-
   calibration.md` counted; D-145 counts DISTINCT canonical models. Under the rows count
   `abstract`, `computer-use`, `mathematics` and `web-dev` reproduce exactly, `everyday` (149.6) and
   `expert` (83.4) within 0.3, `coding` (65.4 on the `swebench` rows) within 0.4. **Only
   `agentic-coding` (50.0) fits no rule.** The direction of W-094 stands, and more strongly: ten of
   eleven surfaces sit on a board rule, none on the ranked one.
2. **"The two that do not are the two thinnest boards" is withdrawn.** ECI has 295 distinct models
   and 521 rows. `agentic-coding`'s 67.2 also pools every effort level; on the `high` rows the
   surface ranks, the board third is 64.4 (review m-2).
3. **"Nine of eleven"** counts `document` and `factuality`, which hold by construction; the
   independent evidence is seven of nine (review m-3). The style-control floors are not "within 5
   Elo" of the base boards: `text` differs by 15.4, `search` by 9.6 and 9.1, `vision` by 7.2 and
   6.1 (review m-1).

Provenance gap (review M-2): `scripts/survey_boards.py` reproduces the three LMArena rows of the
W-094 table, not the other eight. The review reproduced them with its own queries; a script mode
that prints all three candidate floors for every surface is owed with W-094's re-derivation (M16).

