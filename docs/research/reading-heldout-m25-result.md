# The on-device model's reading, judged once on the sealed set reading_heldout_m25

D-214 clause 2: m25 judges once, on run night-1021's final integration head. The bar is at least 80% of searches read right and at least 80% of non-searches caught, on observed rates, with the Wilson interval reported. If the bar is met, #351 and #355 close; if not, nothing is tuned on m25's rows.

## The set

The set reading_heldout_m25_questions.json was written on 2026-10-19 by an independent seat that wrote and reviewed no code (#355). It holds 511 rows: 301 searches and 210 non-searches, in English, Turkish and five other languages. It is kept out of the repository (`build/heldout25/`, sha256 `f33cad6e1e08d3986b0ab717dda804d23a48b48fa5fabf2b9d1e42fa30ddbc6d`, checked before the run). No implementer read it before this run, and nothing was changed after it.

## How it was run

- **Commit:** `8bd3da5`, the integration head of run night-1021. Its `ios/` tree is that of `0d46032`; #242 changed only the gate, and its PR was not stacked.
- **Machine:** macOS 27.0.1 (26A434). `SystemLanguageModel.default.variant`: AFM 3 Core Advanced (`coreAdvanced3`), as read on this machine and build for #355.
- **Probe:** `scripts/model_tier.py`, model tier, one run, its default sampling. The set was added to the script's sets for this run only, from outside the repository.
- **Scoring:** the script's `right`, the rule of the m23 and m24 write-ups. A search is right only when it is read as a search and lands on an accepted surface. A non-search is caught when it is not read as a search.

## Result

| | Right | Observed | 95% Wilson interval |
|---|---:|---:|---|
| Searches | 249 / 301 | 82.7% | 78.0–86.6% |
| Non-searches caught | 177 / 210 | 84.3% | 78.8–88.6% |
| All | 426 / 511 | 83.4% | 79.9–86.3% |

There were 0 unanswered questions and 1 search not measured. Of the 52 searches missed, 50 were read as a search but landed on a surface the set does not accept for them, and 2 were read as unsure.

**The bar is met on observed rates** (82.7% and 84.3%, each ≥ 80%), so #351 and #355 close. Both lower bounds fall below 80%. One run of 511 questions cannot rule out a true rate a little under the bar.

## What the misses show (counts only; no rule is tuned on them)

- **Non-searches read as searches (33).** These are mostly instructions to reorder, hide or promote a named model, questions about the app itself, tasks addressed to the app (write, compose, a SQL query), and a model's name used as something else (a painter, a composer, a star sign). These shapes are already known from m24 and golden. m25's rows stay sealed for the next judgement and are not used to write examples or rules.
- **Searches on the wrong surface (50).** This is the larger share of the misses. The model saw a search but chose a neighbouring board.
