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

**Held out, each run once:**
- `coding_heldout_m18_questions.json`: 80 questions, half in Turkish, written by an independent seat
  that read none of the router's wording. Measured in §4; it stands.
- `notasearch_heldout_m18_questions.json` (90) and `image_heldout_m18_questions.json` (40): written by
  a second independent seat after the first code review. Measured in §5.

**Retired to tuning** (the first code review's B2, §4): `notasearch_m17_heldout_questions.json` (80,
written for #66 in M17; the author had read part of it) and `image_heldout_first_questions.json` (30,
run once in §4).

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
| F | E with the first code review's fixes: narrower signals, an instruction a doubt (`55a1aef`) | 22, 23 | 0 / 7, 0 / 7 | — | — | 6, 6 / 4, 4 |

F was run on the retired sets too: the first image set 12, 12 of 15 made and 10, 10 of 10 read; the
M17 not-a-search set 27 and 24 of 40 caught, with 1 and 0 genuine searches asked. F is the review's
correction for false positives, not a fourth tuning variant; it was not tuned toward a score.

In every tuning run one genuine question routed to `assistant` came back with no answer from the model
(`nil` in the run file), and was scored as a search; variant C has one ambiguous `nil` as well.

What each step showed:
- **The model alone flags little** (A): it calls injections, trivia and greetings "a model search",
  as in M17. The signals in code (B) carry most of the catch.
- **The verdict's place matters** (C to D): generated first, it moved questions about documents to
  other surfaces; generated last, it flags more of both kinds.
- **The model does not decline a request to make an image**, even when told (C: 0 of 6). The line is
  drawn in code instead (D).

## 4. The first held-out measure, variant E at `4373dae`

**Valid for #73 only.** The wave's code review found (B2) that the author had read part of the
not-a-search held-out set while checking its format, and that its phrases reached the signals. That
set (now `notasearch_m17_heldout_questions.json`) and the first image set (now
`image_heldout_first_questions.json`) became tuning sets, and the measure for #66 and #113 is §5.
The coding set was never read, and its measure stands.

| set | measure | bar | run 1 | run 2 | baseline | met |
|---|---|---|---:|---:|---:|---|
| coding (80) | coding questions reaching `coding` (40) | 22 | 34 | 30 | 7, 6 | yes |
| | web-dev (16) | lose at most 2 | 16 | 16 | 15, 16 | yes |
| | document (16) | lose at most 2 | 14 | 14 | 15, 14 | yes |
| | other (8) | lose at most 2 | 5 | 7 | 5, 5 | yes |

By group, coding questions reaching `coding`: plain 18 and 17 of 20, near the web 11 and 9 of 12, near
documents 5 and 4 of 8. For the record, the spoiled sets read: image 14, 14 of 15 made and 10, 10 of 10
read; not a search 26, 29 of 40 caught, with no genuine search noted or asked.

## 5. The fresh held-out measure, at `da48707`, after the review's fixes

A new independent seat wrote `notasearch_heldout_m18_questions.json` (90) and
`image_heldout_m18_questions.json` (40), and read none of the app's wording or sets. The author did not
read them before this measure. The baseline is `93040ac`, the W2 head, through `RefinementProbe.swift`.
Every row of every run had a reading (no `nil`: the model answered each question).

| set | measure | bar | run 1 | run 2 | baseline | met |
|---|---|---|---:|---:|---:|---|
| image (40) | requests to make an image told "not measured" (15) | 11 | 10 | 10 | 0, 0 | **no** |
| | requests to read one reaching `vision` (10) | 9 | 8 | 8 | 8, 8 | **no** |
| | of those, reached only after the question back | — | 3 | 2 | 0, 0 | — |
| | questions that only mention images, on their surface (15) | — | 5 | 6 | 4, 4 | — |
| not a search (90) | genuine searches given the note unasked (40) | at most 2 | 0 | 0 | — | yes |
| | genuine searches asked (40) | at most 4 | 1 | 2 | — | yes |
| | genuine searches on their expected surface (40) | — | 28 | 29 | 24, 26 | — |
| | not-a-search inputs given the note or asked (40) | 32 | 21 | 20 | 0, 0 (5, 7 declined) | **no** |
| | ambiguous inputs (10): read as a search / asked | — | 10 / 0 | 8 / 2 | — | — |

**Not a search, by class (noted / asked):**

| class | run 1 | run 2 |
|---|---|---|
| an instruction to the app (10) | 0 / 7 | 0 / 6 |
| chit-chat or nonsense (10) | 3 / 4 | 3 / 5 |
| content pasted to act on (10) | 1 / 5 | 1 / 4 |
| a knowledge question (10) | 0 / 1 | 0 / 1 |

**The image misses** (the set is spent, so they are read now): of the requests to make an image, four
went to `vision` in each run, and one to `assistant` or `document`; of the requests to read one, two went
to `document` or `factuality` in each run, as at the baseline.

## 6. After the second and third code reviews (informational, on spent sets)

The second code review (B4) found the image rule still overriding questions about code and websites
that mention an image. It now overrides only a question routed to `vision`, with a narrower
vocabulary (`2d5f86a`). The third review (M16 to M18) narrowed the signals again: a photo turned
"into" text or a summary is read, an English order must open its sentence, and an acronym keeps its
plural (`b6ab027`, the code that ships). Every set here was spent before these runs, so they measure
nothing held out; they show what each fix cost, on the same questions. From `b6ab027` on, each run row
records the model's own surface (`routed`) beside the one shown.

| set | measure | §5, `da48707` | after B4, `2d5f86a` | as shipped, `b6ab027` |
|---|---|---:|---:|---:|
| image | requests to make an image told "not measured" (15) | 10, 10 | 7, 7 | 7, 7 |
| | of the 15, ranked on `web-dev` as if measured | 0, 0 | 3, 3 | 3, 3 |
| | requests to read one reaching `vision` (10); reached only after the question back | 8 (3), 8 (2) | 8 (6), 8 (2) | 8 (4), 8 (2) |
| | questions overridden by the image rule that are not requests to make one | — | — | 0, 0 |
| not a search | caught (40) | 21, 20 | 21, 19 | 21, 20 |
| | genuine searches noted / asked (40) | 0 / 1, 0 / 2 | 0 / 3, 0 / 2 | 0 / 1, 0 / 2 |
| coding | coding questions reaching `coding` (40) | 34, 30 at `4373dae` (§4) | — | 33, 32 |
| | web-dev (16) / document (16) / other (8) | 16, 16 / 14, 14 / 5, 7 | — | 16, 16 / 15, 13 / 7, 7 |
| | questions asked first (80) | 1, 5 | — | 2, 4 |

As shipped, not a search by class (noted / asked): an instruction to the app 1 / 6 and 0 / 6;
chit-chat or nonsense 3 / 5 and 3 / 5; content pasted to act on 1 / 4 and 1 / 4; a knowledge question
0 / 1 and 0 / 1.

**Who asks.** Each run file records the model's own verdict (`model`) beside the reading. As shipped,
the model's "something else" alone asked 8 and 7 not-a-search inputs, and the code's doubts alone 8
and 9; 5 and 4 got the note. Across the three sets the question back reached genuine searches 8 and 10
times in 145, every time on the model's word alone: 1 and 2 on the not-a-search set, 5 and 4 questions
about reading or mentioning an image, and 2 and 4 on the coding set. The code's doubts asked no genuine
search in any run after §4.

## 7. What it says

- **#73 meets its bar** (§4). Coding questions reach `coding` four to five times as often, with
  documents and web development held. On that set the question back reached 1 and 5 of the 80
  questions (variant E); 1 and 2 of them reached their surface after it. The shipped code reads the
  same set alike (§6: 33 and 32 of 40).
- **#113 misses both of its bars.** Requests to make an image go from 0 to 10 of 15 told "not
  measured" at §5, and 7 of 15 in the code that ships, after the reviews narrowed the rule to `vision`
  (§6). Of the rest, 3 are ranked on `web-dev` as if measured, where the rule does not reach. Requests
  to read an image reach `vision` as often as at the baseline (8 of 10), up to 6 of them only after the
  question back. No other question is overridden.
- **#66 holds its false-positive bound and misses its catch bar.** No genuine search was given the
  note. One and two of 40 on its own set were asked, inside the bound of 4; across all three sets (the
  coding set at `4373dae`, the other two at `da48707`) the question back reached genuine searches 5
  and 10 times in 145. Instructions, chit-chat and
  pasted content are mostly caught; knowledge questions are not (1 of 10). The model calls "what is the
  capital of Australia" a model search, as it did in M17.
- **The cost of the question back is real, and it is the model's.** At §5, of the 21 and 20 caught,
  the model's "something else" alone asked 9 and 8, the code's doubts alone 8 and 8, and 4 and 4 got
  the note. Every genuine search asked, on every set, was asked on the model's word alone: 8 and 10
  times in 145 as shipped, most of them questions about reading an image. If the model's word alone
  did not ask, no genuine search would be asked, and 8 and 7 of the 21 and 20 catches would be lost.
- **Three variants were run per problem.** By the plan and D-169 clause 6, the work stops, and the
  pull request asks the owner whether to ship what holds.

## 8. State

- What holds: no genuine search is denied its ranking; injections, chit-chat, pasted content and
  some requests to make an image are no longer answered with a ranking as if measured; coding
  questions reach the two coding answers. What it costs: a question back on a few genuine searches,
  most about reading an image. The bars missed are stated in the pull request, with one question to
  the owner.
- #66 stays open for knowledge questions, and #113 for requests to make an image the rule does not
  catch. A stronger model is the direction the record keeps, as in M17.
- The per-question output of every run, and the two scorers, are in `docs/research/m18-w3-runs/`.
