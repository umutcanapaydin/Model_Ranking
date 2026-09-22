---
record_type: review
id: m15-router-recalibration
status: draft
process_version: v5.0
date: 2026-09-22
---
# M15-W3 — the router probe W-115 owed, and why the wording tier now reads examples

**Cited by `ios/ModelRanking/Engine/Router.swift` (`CategoryHints.examples`) and D-147.** Written by
the lead agent that made the change. This is an author's measurement, not an independent review.

## 1. What was owed

W-115 fixed the wording of the three M15-W3 hints and left one thing unmeasured: the M10 calibration
probe (`docs/reviews/m10-router-calibration.md`) had not been re-run with fourteen hints. The router
centres its scores on the mean over the hints it is given, so adding three hints moved every
existing margin by an unknown amount. `make check` on the owner's Mac, 2026-09-22, was red on
exactly that: six `swift test` cases in `FrontDoorTests.UnmeasuredQuestionTests`, all routing.

## 2. The measurement, one sentence per surface

`scripts/router_probe/probe.swift` replicates `SimilarityRouter.route`'s arithmetic and prints
every score. It reproduced every `swift test` failure exactly, so it measures the shipping router.
Two question sets were used:

- `probe_questions.json`: the questions the Swift tests route (the M10 probe, reachability, the
  one-tap cases and the three declines).
- `heldout_questions.json`: 22 new questions, **written before any change below and never tuned
  against**. It exists because tuning to the probe is the failure the M10 record warns about.

| router | probe, pre-M15 surfaces | held-out, pre-M15 surfaces |
|---|---|---|
| HEAD 855b44a, 11 one-sentence hints | **18/18** | 5/17 |
| M15-W3 tree, 14 one-sentence hints | 11/18 | 3/17 |

**M15-W3 broke seven routes that worked before.** `search` and `search_factuality` became hubs: in
the centred space they were close to almost everything. "build me a landing page" went to `search`
(0.282, with `web-dev` third at 0.183), "solve this competition math problem" went to `search`, and
the screenshot question went to `search_factuality` (0.317, with `vision` at 0.190).
`search_factuality` was in the top three for 11 of 21 probe questions.

**Rewording does not converge.** Four rewrites of the three new hints scored 12, 11, 7 and 7 of 21:
whichever sentence changed became the next hub. A hubness penalty (subtracting each hint's mean
similarity to the others) changed nothing, because after centring that mean is nearly equal for
every hint. Past this point, rewording one sentence per surface is fitting to the probe.

The held-out row also shows something W3 did not cause: **the one-sentence tier was already weak on
wording it had not seen** (5 of 17 before M15).

## 3. The change: six example questions per surface

The wording tier now compares a question with six example questions per surface
(`CategoryHints.examples`), and each decline is a group of six in the same form
(`CategoryHints.unmeasuredHints`). Centring subtracts the mean over all the examples. A group scores
as the **mean of its two closest examples**. `byID` is unchanged, because the on-device model tier
reads a description rather than examples.

The examples are plain questions written for each surface. None is copied from a test or from the
held-out set.

| how a group scores | probe (21) | held-out (22) |
|---|---|---|
| closest example | 18 | 18 |
| **mean of the two closest (shipped)** | **21** | **18** |
| mean of all six | 18 | 17 |

The held-out set was scored after the scoring rule was chosen on the probe, and no example was
changed after reading it.

**The four held-out misses**, kept as they are so the set stays honest:

- "let an ai work through my whole repo and open a pull request" goes to `coding` 0.437, with
  `agentic-coding` second at 0.414.
- "prove there are infinitely many primes" goes to `factuality` 0.259, with `mathematics` second.
- "book a flight for me on a travel website" goes to `web-dev` 0.340, and `computer-use` is not in
  the top three.
- "what number comes next in 2 6 12 20" declines (0.169 against 0.167), and `abstract` is not
  offered.

**The thinnest margin in the probe:** "build me a landing page" routes to `web-dev` at 0.467 against
the image-making decline group at 0.456. "draw a logo" and "create an illustration" sit close to
design work. It passes, and it is the first place to look if a decline example is ever added.

**The declines are now wide.** The three decline questions score 0.57 to 0.68 against their groups,
where one sentence each had left "which model answers fastest" declining by 0.001.

## 4. Gates

- `make swift-test`: 257 of 257 (floor 257), with the tests unchanged.
- `tests/unit/test_router_hints.py::test_every_described_surface_has_example_questions_for_the_wording_tier`
  fails when a surface has a description and no examples, or fewer than two. Mutated by renaming
  `vision`'s examples; it failed, and passed again once they were restored.

## 5. What this record does not claim

Forty-three questions are a probe, not an evaluation, and one person wrote both the examples and the
held-out set. The honest reading is that the example tier is materially better than the one-sentence
tier on wording neither has seen (18 of 22 against 3 of 17 and 5 of 17), and that it is still the
second tier. Cost: about 100 short embeddings per question instead of 17; the whole probe, model
load included, runs in about a second on the owner's Mac. It has not been timed on a phone.

## 6. Correction, 2026-09-22: one example was a copy of a held-out question

The M15 closure security seat (`docs/reviews/m15-closure-security-review.md`, INFO) found that
the decline example "which model has the lowest latency" was word for word the held-out question
of the same text. Section 3's statement that "none is copied from a test or from the held-out set"
was false for that one example, and the held-out set was not fully held out.

**Remedy.** The example was replaced with "compare response times between models", and both sets
were measured again: **probe 21 of 21, held-out 18 of 22, unchanged.** The latency question
still declines, at 0.417 against the decline group and 0.269 against the closest surface.

**What else the check showed.** A similarity pass over every example against both question sets
found no other copy. It found close paraphrases, all written by the same person: "make my selfie
look better" against the probe's "make my profile photo look better" (0.78), and "which model is
fastest" against "which model answers fastest" (0.86). So the probe's three declines are weak
evidence, and the held-out set is best read as "written first, by someone who then wrote the
examples". A held-out set written by someone else is the only fix for that, and it is owed with
any further example change (D-147 clause 5).
