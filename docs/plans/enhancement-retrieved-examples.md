# Enhancement plan: Apple Intelligence reads each question beside its nearest labelled examples (#353)

**Golden Rules served:** 2 (understand every question with an AI model, Apple Intelligence in every case), as v1 order step 3-4 (D-210). Part of #351's phase 2.

## Goal

The model tier sees, with each question, the labelled questions closest to it, and reads it better for that. All three of the owner's research reports rank retrieved examples among the top two levers; one report's own source check found the largest published gains were measured against random examples, so the gain here is measured, not assumed.

## Scope

**In:** a pool of labelled example questions (D-212 clause 2), its vectors computed with Apple's `NLContextualEmbedding` (its Latin model covers Turkish; checked on the owner's Mac), the 8 nearest examples added to the model tier's prompt, and the model-tier measurement (#351, phase 1) measuring it.

**Out:** a bundled third-party encoder (only if Apple's embedding finds poor neighbours: its own issue); a classifier that overrides the model (never without the owner's ruling); m25 (#355).

## Decisions

1. **The pool** (D-212 clause 2): the older probe sets, relabelled by an independent seat; m24, the golden set and m25 never enter it, and no pool row is a near-duplicate of one of theirs (difflib 0.9, containment, translations checked by embedding similarity).
2. **Kept only if measured.** On m24 the retrieved block beats both a fixed block of 8 examples and no block, by an exact McNemar test, with the golden set losing at most 2 rows and searches and non-searches each losing at most 2.

## Phases

1. **Measure offline.** Build the pool and its vectors, and run three variants on m24 and golden through the model-tier measurement in a scratch copy: no examples, a fixed 8, the nearest 8.
   *Acceptance:* the three runs' rows are kept and compared; the decision is written on #353.
2. **Ship it, if it is kept.** The pool and its vectors ship in the app; the model tier retrieves on the device. A red test first: the prompt carries the nearest labelled examples for a question, and none from a held-out set.
   *Acceptance:* the citing tests, `make gate` green, the measured numbers in the PR body.
