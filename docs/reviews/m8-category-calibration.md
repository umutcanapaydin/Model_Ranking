---
record_type: register
id: m8-category-calibration
status: ratified
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

**Corrected 2026-08-19 after the first pass calibrated the wrong population.** The first run measured
the distribution of CSV ROWS. The engine ranks MODELS, and ingestion keeps one row per model — its
best score, the same rule `parse_swe_bench_verified` already applies. On several boards those are
very different populations: `terminalbench` is 204 rows and **59 models**, `mmlu` 249 rows and 137,
`arc_agi` 191 and 168. Keeping each model's best also shifts the distribution upward, so the
original floors were low against the population they would actually govern.

Every figure below is measured on the output of `parse_board` — exactly what reaches the database.

| Category | Scale | Models | Leader | Floor (top ⅓) | `close_call` | `value_window` | Candidates |
|---|---|---|---|---|---|---|---|
| Everyday questions | ECI | 521 | 161.7 | **149.9** | **0.5** | **3.0** | 42 |
| Expert reasoning | % | 263 | 94.8 | **83.6** | **5.0** | **8.0** | 62 |
| Mathematics | % | 238 | 100.0 | **84.4** | **9.5** | **15.0** | 77 |
| Computer use | % | **59** | 84.7 | **53.4** | **0.8** | **20.0** | 11 |
| Abstract reasoning | % | 168 | 98.0 | **72.8** | **1.0** | **8.0** | 30 |
| Web development | Elo | 102 | 1711.9 | **1478.9** | **6.8** | **150.0** | 9 |

`close_call` is measurement (2 × the board's own stderr where published, else the median gap between
adjacent models). `value_window` is sized by candidate count. `min_quality` is the top third.

Mathematics is the one place the two constraints nearly collide: AIME's stderr is 4.74 points, so
`close_call` is 9.5 — a window narrower than that would declare models "within reach" while also
declaring the same gap to be noise. 15 clears it.

Coding keeps its existing 65 / 6.0 / 1.5; `agentic-coding` and `assistant` are unchanged.

## Two findings the owner should see

**1. Fractions, not percentages.** `mmlu`, `gpqa_diamond`, `otis_mock_aime`, `terminalbench` and
`arc_agi` publish scores in **0–1**, while this project's `coding` category is on **0–100**. They
are converted at ingestion (× 100), which is a unit change of the same quantity and NOT the
cross-scale mixing D-105 forbids — 0.65 and 65% are the same number. It is recorded because an
un-converted fraction silently fails every threshold: a floor of 83.6 rejects a board whose leader
reads 0.948.

**2. TWO categories are structurally thin, not one — and the first calibration hid the second.**

**Web development**: its leader sits 30 Elo above second and the top twelve span 160 Elo, so no
floor rescues it. At every floor from the 50th to the 75th percentile a 30-Elo window admits ONE
candidate; it needs 150 Elo to offer nine.

**Computer use**: the same shape, and it only became visible once the population was corrected. It
has **59 models, not 204** — the board lists each model many times under different scaffolds. Its
top six cluster between 78.4 and 84.7 and then drop to 69.9, so a 10-point window admits six
candidates and it takes **20 points** to offer eleven. Lowering the floor changes nothing, exactly
as with web development.

Both will be saying "20 points below the leader" or "150 Elo below the leader" where coding says
"3.5 points below, and 84% cheaper". **The engine discloses the gap in the trade-off sentence, so
nothing is hidden** — but these two make a thinner promise than their neighbours, and shipping them
as equals is a decision rather than an oversight.

**3. Web development, in detail.** Its leader sits 30
Elo above second place and the top twelve span 160 Elo, so no floor rescues it: at every floor from
the 50th to the 75th percentile, a 30-Elo window admits **one** candidate and a 60-Elo window admits
four. It needs a **150-Elo** window to offer nine alternatives.

That is honest but weaker than the other categories. Coding can say "3.5 points below the leader and
84% cheaper"; web development will be saying "150 Elo below the leader" — a large quality gap to
trade for price, and the user needs to see it to judge. **The engine already discloses the gap in
the trade-off sentence, so nothing is hidden** — but this category makes a thinner promise than the
others, and shipping it as an equal is a decision rather than an oversight.

---

> **Ratified 2026-08-20.** It sat `draft` while being the sole cited evidence for thresholds
> already shipping in the scoring path — an independent review's MINOR-5. A draft record that
> load-bearing is a record nobody has agreed to and everybody is relying on.

## Correction, 2026-08-19: the table above measures a population the engine never ranks

Appended rather than edited: the numbers above were honestly derived and were derived from the
wrong set, and replacing them would erase the third instance of a mistake worth being able to count.

**What was measured:** every model on each board. **What the engine ranks:** models that reconcile
to the registry AND carry a price median. Only those can be recommended, because a model nobody can
buy is not an answer. The gap is not small:

| Board | Rows ingested | Reconciled to a model | Priced — the ranked population |
|---|---|---|---|
| `epoch_eci` | 521 | 284 | **58** |
| `epoch_gpqa` | 263 | 130 | **50** |
| `epoch_aime` | 238 | 131 | **51** |
| `epoch_arc_agi` | 168 | 125 | **39** |
| `epoch_webdev` | 102 | 72 | **49** |
| `epoch_terminalbench` | 59 | 47 | **33** |
| `epoch_mmlu` | 136 | 6 | 3 |

`epoch_mmlu` is the clearest case: it lists academic and pre-commercial models, six of which this
product has ever heard of. A threshold calibrated on its 136 rows would describe a population the
engine cannot serve at all.

**Why it changed the answer.** The priced subset is the COMMERCIAL FRONTIER, and the frontier is far
more tightly clustered than the board behind it — `expert` has a median of 89.6 against a leader of
94.4. Windows sized on the full board were therefore far too generous once applied to the frontier:

| Category | Window (as drafted) | Candidates admitted | Window (corrected) | Candidates |
|---|---|---|---|---|
| `expert` | 8.0 | 34 of 37 above the floor | **5.0** | 25 |
| `mathematics` | 15.0 | 34 of 34 | **10.0** | 28 |
| `computer-use` | 20.0 | 14 of 14 | **5.0** | 5 |
| `abstract` | 8.0 | 20 of 20 | **5.0** | 8 |
| `web-dev` | 150.0 | 23 of 23 | **100.0** | 3 |
| `everyday` | 3.0 | — | **3.0** (unchanged) | 5 |

`coding`, the reference this product already ships, admits 7. A window admitting every model above
the floor does not select — it re-states the floor, and Best Value collapses into "the cheapest
thing we would recommend at all".

**Why `expert` and `mathematics` are not narrowed to match `coding`.** Because they cannot be,
honestly. §61 above states the invariant and this is the first data that exercises it: on GPQA the
twelve highest-scoring priced models span 1.8 points against a 2.52 standard error, and on AIME
three models tie at exactly 100.0. Those models are indistinguishable at the boards' own precision.
Narrowing the window below `close_call` would make the product disclose "level with the leader"
about a model and simultaneously refuse to consider it — ranking noise as though it were quality.
25 and 28 candidates is the honest count when 25 and 28 models are genuinely tied. Both boards are
ledgered as **W-035**: a benchmark at its ceiling stops recording improvement, and these two will
grow less informative on their own with every gate green.

**The invariant is now executable**, not remembered:
`tests/unit/test_categories.py::test_no_category_can_exclude_a_model_it_calls_level_with_the_leader`.

**Third occurrence, ledgered as W-037.** This is the third time these thresholds have been sized
against the wrong population — CSV rows, then parsed board rows, now the full board instead of the
ranked subset — and all three were caught by measuring rather than by review. The engine's ranked
population has no name in the codebase, so the question keeps getting answered from whatever data
is nearest to hand.
