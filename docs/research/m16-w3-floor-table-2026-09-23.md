---
record_type: register
id: m16-w3-floor-table-2026-09-23
status: ratified
process_version: v6.0
date: 2026-09-23
---
# M16-W3 — every floor under D-148, and what it would change

**Measured on the served artifact** (`advisor.db`, published 2026-09-22T11:33Z) with
`scripts/survey_boards.py --floors --db advisor.db`, read-only and offline. D-148 clause 1: a
surface's floor is the top third of its board's ROWS as the parser stores them. The pick comparison
re-ran `recommend()` at each budget with only that surface's floor replaced, nothing else changed.

## The floors

| surface | board rows | models | ranked | today | D-148 (rows) | move | D-145 (models) | ranked |
|---|---|---|---|---|---|---|---|---|
| coding | 173 | 130 | 44 | 65.0 | 65.4 | +0.4 | 63.4 | 75.8 |
| assistant | 402 | 357 | 65 | 1400.0 | 1406.7 | +6.7 | 1394.9 | 1450.6 |
| agentic-coding | 49 | 17 | 13 | 50.0 | 64.4 | +14.4 | 67.2 | 64.4 |
| everyday | 521 | 295 | 58 | 149.9 | 149.6 | -0.3 | 144.6 | 153.2 |
| expert | 263 | 183 | 50 | 83.6 | 83.4 | -0.2 | 83.3 | 91.0 |
| mathematics | 238 | 158 | 51 | 84.4 | 84.4 | 0.0 | 86.4 | 95.6 |
| computer-use | 59 | 45 | 33 | 53.4 | 53.4 | 0.0 | 57.3 | 61.6 |
| abstract | 168 | 82 | 39 | 72.8 | 72.8 | 0.0 | 79.5 | 87.2 |
| web-dev | 102 | 79 | 49 | 1478.9 | 1478.9 | 0.0 | 1480.0 | 1522.9 |
| document | 44 | 36 | 29 | 1467.5 | 1470.7 | +3.2 | 1467.5 | 1471.0 |
| factuality | 171 | 143 | 59 | 1450.6 | 1451.5 | +0.9 | 1450.6 | 1460.7 |
| vision | 152 | 129 | 41 | 1248.2 | 1253.3 | +5.1 | 1248.2 | 1284.8 |
| search | 34 | 33 | 25 | 1206.9 | 1206.9 | 0.0 | 1206.9 | 1210.5 |
| search_factuality | 32 | 31 | 24 | 1203.7 | 1202.1 | -1.6 | 1203.7 | 1211.9 |

This reproduces the M15-W1 review's measurement: under the rows count the M8 floors hold
(`abstract`, `computer-use`, `mathematics`, `web-dev` exactly; `everyday`, `expert` within 0.3;
`coding` within 0.4), the five M14/M15 surfaces were floored on D-145's distinct-model count (their
"models" column equals today's floor), and `agentic-coding` fits no rule.

## What changes for a reader

Of the nine floors that move, **one changes a pick**:

| surface | budget | pick | today | under D-148 |
|---|---|---|---|---|
| agentic-coding | medium | Budget Pick | Grok 4.5 (53.8) | GPT-5.6 Sol (69.4) |
| agentic-coding | unlimited | Budget Pick | Grok 4.5 (53.8) | GPT-5.6 Sol (69.4) |

No Best Value or Best Quality changes anywhere; the `low` budget changes nowhere. At `medium`,
GPT-5.6 Sol is already both Best Quality AND Best Value, so under D-148 it holds all THREE labels
there. *Correction, same day: the question put to the owner said "both labels"; it is all three.
The applied change was verified on the artifact after the ruling, which is where this showed.*
*Put back to the owner with the correction; **confirmed the same day: "the rule stays"** (translated
from Turkish).*

**`agentic-coding`'s board carries five effort levels** (low 8 rows, medium 9, high 13, xhigh 10,
max 9); the surface ranks at `high` (`ranking_effort`). Its floor is 64.4 either way: over all 49
rows, and over the 13 `high` rows alone.

**Which rows count** (review NIT-4): each row as stored, one per raw name, harness and effort. On
every one of the 14 boards raw names are unique per row, so "one per raw name" and "one per row"
give the same count today; if a board ever lists a raw name twice, this record counts both.

**Subscription plans (the CLI, not `/v1` or the app)** -- found by the independent review after the
ruling, and not in the table the owner ruled from:

| surface | budget | plan Budget Pick | today | under D-148 |
|---|---|---|---|---|
| agentic-coding | medium | Budget Pick | Perplexity Pro ($20, 53.8) | Google AI Plus ($4.99, 11.8), with "no plan in this budget clears the 64.4 bar" |
| agentic-coding | unlimited | Budget Pick | Perplexity Pro ($20, 53.8) | ChatGPT Pro ($100, 69.4) |

At `medium` no plan clears 64.4, so the subscription answer falls back to the cheapest plan with a
warning. **Put to the owner and accepted 2026-09-23** (translated from Turkish: "accepted, we will
look at it later, no problem"): the CLI-only subscription answer follows the same rule.

## The ruling

**Ruled by the owner 2026-09-23 (in session): the rule applies to `agentic-coding` too.** Its floor
moves to 64.4 with the other eight, so D-148 holds on every surface with no exception, and Grok 4.5
stops being the Budget Pick at `medium` and `unlimited` because it is not in the top third of its
board.

## What this record did not decide

Plan §0.3: the owner rules each surface whose pick changes. Here that is `agentic-coding` alone;
the other eight moves change no pick and follow D-148 as already ruled.
