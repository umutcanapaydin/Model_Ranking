---
record_type: register
id: m8-category-calibration
status: draft
date: 2026-08-19
---
# Threshold calibration for D-127's categories

**Why this record exists.** Each category ranks on its own scale and needs its own quality floor,
value window and close-call threshold. D-105 forbids borrowing a NUMBER across scales. This
calibration found that it also forbids borrowing the **rule** — the method M3 used for Elo produced
nonsense on two of the six new scales, and that is the finding worth keeping.

Every number below was measured from the bundle on 2026-08-19, not chosen.

## What each threshold is FOR, which is what decides how to derive it

| Threshold | Question it answers | Derived from |
|---|---|---|
| `close_call` | is a gap between two models real, or noise? | **measurement**: 2 × the benchmark's own stderr, or the median gap between adjacent models where no stderr is published |
| `value_window` | how far below the leader is still "within reach"? | **product**: set so a useful number of real alternatives survive — a window admitting one candidate makes Best Value into Best Quality |
| `min_quality` | what counts as good enough to recommend at all? | **positioning**: the top third of the board, the same rule M3 used for Elo |

## The rule that did not transfer

M3 set the Elo window at roughly 4 × the noise threshold. Applied mechanically here it gives:

- **mathematics**: AIME's stderr is 4.74 points, so 4× noise is a **38-point** window — a model 38
  points below the leader counted as "within reach", which is not a recommendation, it is a shrug.
- **everyday (ECI)**: neighbour gaps are 0.25, so 4× gives a **2.0** window — which happened to be
  fine (28 candidates), but only by luck of a dense distribution.

The multiplier encodes an assumption about how spread out a board is, and boards differ. So the
window is sized by **candidate count** instead, and the noise figure is kept for `close_call`, which
is the threshold that genuinely is a measurement question.

## The numbers

| Category | Scale | n | Leader | Floor (top ⅓) | Noise | `close_call` | `value_window` | Candidates in window |
|---|---|---|---|---|---|---|---|---|
| Everyday questions | ECI | 521 | 161.7 | **149.9** | 0.25 (gap) | **0.5** | **2.0** | 28 |
| Expert reasoning | % | 263 | 94.8 | **83.6** | 2.52 (stderr) | **5.0** | **8.0** | 62 |
| Mathematics | % | 238 | 100.0 | **84.4** | 4.74 (stderr) | **9.5** | **15.0** | 77 |
| Computer use | % | 204 | 84.7 | **52.4** | 0.40 (gap) | **0.8** | **10.0** | 19 |
| Abstract reasoning | % | 191 | 98.0 | **76.5** | 0.50 (gap) | **1.0** | **5.0** | 23 |
| Web development | Elo | 109 | 1711.9 | **1471.0** | 3.39 (gap) | **6.8** | **150.0** | 9 |

Coding keeps its existing 65 / 6.0 / 1.5, and `agentic-coding` and `assistant` are unchanged by this
record.

## Two findings the owner should see

**1. Fractions, not percentages.** `mmlu`, `gpqa_diamond`, `otis_mock_aime`, `terminalbench` and
`arc_agi` publish scores in **0–1**, while this project's `coding` category is on **0–100**. They
are converted at ingestion (× 100), which is a unit change of the same quantity and NOT the
cross-scale mixing D-105 forbids — 0.65 and 65% are the same number. It is recorded because an
un-converted fraction silently fails every threshold: a floor of 83.6 rejects a board whose leader
reads 0.948.

**2. Web development is the weakest of the six, and the reason is its shape.** Its leader sits 30
Elo above second place and the top twelve span 160 Elo, so no floor rescues it: at every floor from
the 50th to the 75th percentile, a 30-Elo window admits **one** candidate and a 60-Elo window admits
four. It needs a **150-Elo** window to offer nine alternatives.

That is honest but weaker than the other categories. Coding can say "3.5 points below the leader and
84% cheaper"; web development will be saying "150 Elo below the leader" — a large quality gap to
trade for price, and the user needs to see it to judge. **The engine already discloses the gap in
the trade-off sentence, so nothing is hidden** — but this category makes a thinner promise than the
others, and shipping it as an equal is a decision rather than an oversight.
