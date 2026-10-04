---
record_type: register
id: m18-w3-question-reading-probe-2026-10-04
status: ratified
process_version: v6.6
date: 2026-10-04
---
# M18-W3: reading the question, measured (#66, #73, #113)

**Measured 2026-10-04** on the owner's Mac, where Apple Intelligence runs. The harnesses are
`scripts/router_probe/RefinementProbe.swift` for the baseline (the model tier alone) and
`scripts/router_probe/ReadingProbe.swift` for every variant (the model tier, then the signals in
code, as `TieredRouter.read` combines them). Both ran in a scratch copy of `ios/`. Every
configuration ran twice, because the model is not deterministic. Plan: `docs/plans/m18-wave-3-plan.md`
(deleted before merge). ADR: D-169, as amended at M18-W3.

## 1. The sets (D-147 clause 5)

**Held out, run once at the end:**
- `coding_heldout_m18_questions.json`: 80 questions, half in Turkish;
- `image_heldout_questions.json`: 30 questions, half in Turkish;
- `notasearch_heldout_questions.json`: 80 questions (40 not a search, 36 genuine, 4 either way).

An independent seat wrote the first two from the surface list and the problem statements; it read
none of the router's wording. The third was written by an independent seat for #66 in M17 and never
run.

**Tuning:**
- the M17 coding sets (`coding_heldout_m17_questions.json`, now tuning, and `coding_tuning_questions.json`);
- a reading set of 139: the nonsense set, `notasearch_tuning_questions.json` and four genuine sets;
- the author's `image_tuning_questions.json` (12).

## 2. Baseline at `93040ac` (the W2 head), held-out sets

| set | measure | run 1 | run 2 |
|---|---|---:|---:|
| coding (80) | coding questions reaching `coding` (40) | 7 | 6 |
| | web-dev (16) / document (16) / other (8) | 15 / 15 / 5 | 16 / 14 / 5 |
| image (30) | requests to make an image told "not measured" (15) | 0 | 0 |
| | requests to read one reaching `vision` (10) | 10 | 10 |
| not a search (80) | not-a-search inputs declined (40); the note did not exist | 2 | 6 |
| | genuine searches on their expected surface (36) | 28 | 26 |

## 3. Variants, on the tuning sets only, each run twice

| variant | what changed | not a search caught (28) | genuine noted / asked (110) | coding (40) | documents (16) | images made / read (6, 6) |
|---|---|---:|---:|---:|---:|---:|
| A | the model's yes/no verdict first; no word and pasted content in code | 14, 12 | 0 / 2, 0 / 2 | — | — | — |
| B | A, and an instruction to the app and small talk in code | 23, 21 | 0 / 2, 0 / 2 | — | — | — |
| C | B, and the issue-73 coding wording and an image sentence | 20, 21 | 0 / 4, 0 / 2 | 28, 33 | 10, 10 | 0, 0 / 5, 5 |
| D | C with the verdict generated last; making an image read in code | 26, 22 | 0 / 6, 0 / 7 | 33, 31 | 12, 11 | 5, 5 / 4, 4 |
| E | D, and a sentence each for documents and for reading an image | 25, 27 | 0 / 7, 0 / 8 | 31, 29 | 16, 16 | 6, 6 / 4, 4 |

What each step showed:
- **The model alone flags little** (A): it calls injections, trivia and greetings "a model search",
  as in M17. The signals in code (B) carry most of the catch.
- **The verdict's place matters** (C to D): generated first, it moved questions about documents to
  other surfaces; generated last, it flags more of both kinds.
- **The model does not decline a request to make an image**, even when told (C: 0 of 6). The line is
  drawn in code instead (D).

## 4. The held-out measure, variant E at `4373dae`

| set | measure | bar | run 1 | run 2 | baseline | met |
|---|---|---|---:|---:|---:|---|
| coding (80) | coding questions reaching `coding` (40) | 22 | 34 | 30 | 7, 6 | yes |
| | web-dev (16) | lose at most 2 | 16 | 16 | 15, 16 | yes |
| | document (16) | lose at most 2 | 14 | 14 | 15, 14 | yes |
| | other (8) | lose at most 2 | 5 | 7 | 5, 5 | yes |
| image (30) | requests to make an image told "not measured" (15) | 11 | 14 | 14 | 0, 0 | yes |
| | requests to read one reaching `vision` (10) | 9 | 10 | 10 | 10, 10 | yes |
| not a search (80) | genuine searches given the note unasked (36) | at most 2 | 0 | 0 | — | yes |
| | genuine searches asked (36) | at most 4 | 0 | 0 | — | yes |
| | not-a-search inputs given the note or asked (40) | 32 | 26 | 29 | 0, 0 | **no** |

**Coding, by group:** plain 18 and 17 of 20, near the web 11 and 9 of 12, near documents 5 and 4 of 8.

**Not a search, by class (noted / asked):**

| class | run 1 | run 2 |
|---|---|---|
| an instruction to the app (12) | 10 / 0 | 10 / 1 |
| chit-chat or nonsense (12) | 7 / 2 | 7 / 3 |
| content pasted to act on (7) | 0 / 6 | 0 / 6 |
| a knowledge question (9) | 0 / 1 | 0 / 2 |

## 5. What it says

- **#73 and #113 meet their bars.** Coding questions reach `coding` 4 to 5 times as often as before,
  with documents and web development held. A request to make an image is told it is not measured;
  a request to read one still reaches `vision`.
- **#66 meets its false-positive bound and misses its catch bar.** No genuine search was given the
  note or even asked, in either run. Injections, chit-chat and pasted content are caught. Knowledge
  questions are not: the small on-device model calls "what is the capital of Australia" a model
  search, as it did in M17, and no signal in code can read trivia without also reading genuine
  questions written as questions ("what is the weather in Berlin today" is a search, by the owner's
  line).
- **Three variants were run per problem.** By the plan, the work on #66's catch stops here.

## 6. State

- The wave ships variant E. For #66 that is below D-169 clause 6's catch bar, with no genuine search
  affected. The pull request says so, and the owner's merge accepts it or not (D-169's "Accepted when
  measured" clause is his).
- #66 stays open for knowledge questions. A stronger model is the direction the record keeps, as in
  M17.
