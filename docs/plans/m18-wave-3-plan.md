---
record_type: plan
id: m18-wave-3-plan
status: draft
process_version: v6.6
date: 2026-10-04
---
# M18-W3 plan — reading the question, by measurement

**Working plan for `wave/m18-w3`**, deleted before merge. Milestone plan: `docs/plans/m18-plan.md`
§2 W3. The branch is stacked on `wave/m18-w2` (#116), which changes the same screen.

**Risk: HIGH**, as the milestone plan says: the wave changes what the on-device model may answer and
what `RoutingOutcome` carries (D-126), and the screen. By D-172 there is no security pass on the
slice; the Tester's fault injection is owed.

## Issues

| Issue | What |
|---|---|
| #66 | Input that is not a model search gets a guiding note, not a ranking (D-169) |
| #73 | Coding questions reach the coding surface, so Ruling A's two answers are shown |
| #113 | A request to make an image is told it is not measured, not answered with image reading |

## Starting points

- `enhancement/issue-66-not-a-model-search`: D-169, ruled by the owner on 2026-09-28. Its held-out set
  (`notasearch_heldout_questions.json`, written by an independent seat) was **never run**, so it is a
  clean held-out set here. Its five variants are in its research record: one closed value among the
  surfaces is almost never chosen, and every variant that caught more also cut genuine searches.
- `fix/issue-73-coding-routing`: variant 3's wording (coding and computer-use descriptions, and one
  instruction sentence). Its held-out set was run once, so it becomes a tuning set
  (`coding_heldout_m17_questions.json`).

## Held-out sets (D-147 clause 5), and the baseline at `93040ac`, twice

An independent seat wrote two new sets from the surface list and the problem statements. It read
none of the router's wording:
- `coding_heldout_m18_questions.json`: 80 questions, half in Turkish.
- `image_heldout_questions.json` (now `image_heldout_first_questions.json`, retired): 30 questions, half in Turkish.

The baseline was run through `RefinementProbe.swift`, the model tier alone, on the owner's Mac.

| set | measure | run 1 | run 2 |
|---|---|---:|---:|
| coding (80) | coding questions reaching `coding` (40) | 7 | 6 |
| | web-dev (16) / document (16) / other (8) | 15 / 15 / 5 | 16 / 14 / 5 |
| image (30) | requests to make an image told "not measured" (15) | 0 | 0 |
| | requests to read one reaching `vision` (10) | 10 | 10 |
| not a search (80) | not-a-search inputs declined (40); none gets a note, which does not exist yet | 2 | 6 |
| | genuine searches on their expected surface (36) | 28 | 26 |

## The bars, set after the baseline (the owner's standing instruction: the agent sets them)

Each must hold in **both** runs on its held-out set, run once at the end:
- **#73.** At least **22 of 40** coding questions reach `coding` (the baseline is 6 to 7; M17's
  variant reached 22 to 23 on an easier set, where its baseline was 8 to 10). Web-dev, document and
  other each lose at most 2 against their baseline.
- **#113.** At least **11 of 15** requests to make an image are told "not measured". At least 9 of 10
  requests to read one still reach `vision`.
- **#66**, with the question back (design 3). These follow D-169 clause 6's bound, kept:
  - at most **2** genuine searches get the note without being asked;
  - at most **4** genuine searches are asked;
  - at least **32 of 40** not-a-search inputs get the note or the question.

The M17 rule holds: three variants per problem, then stop and file it.

**Measured at `4373dae` (variant E), held out, twice** (the research record):
- #73: 34 and 30 of 40; web-dev 16, 16; document 14, 14; other 5, 7. **Met.**
- #113 and #66 were measured too, and that measure was **spoiled** (the code review's B2): the author
  had read part of the not-a-search held-out set while checking its format, and its phrases reached the
  signals. Both sets are tuning sets now. A new independent seat wrote fresh sets
  (`notasearch_heldout_m18_questions.json`, `image_heldout_m18_questions.json`), which are the measure,
  run once, after the review's fixes. The bars stay as set.

**Measured on the fresh sets at `da48707`, twice** (the research record §5; baseline at `93040ac`):
- #113: 10 and 10 of 15 told "not measured" (baseline 0, 0; bar 11, **missed by one**); reading 8 and
  8 of 10 (baseline 8, 8; bar 9, unchanged from the baseline).
- #66: 0 genuine searches noted, 1 and 2 asked (bounds 2 and 4, **held**); 21 and 20 of 40 caught
  (bar 32, **missed**).
- Three variants per problem were spent. The pull request asks the owner whether to ship what holds.

## Design (D-169, amended in this wave)

1. **Signals decided in code, and tested** (`Reading.swift`). These do not depend on the model and
   run on every tier, matched on whole words under both case foldings:
   - *no word*: text with no word in any language (keyboard runs, repeated letters, long runs with
     no vowel; an acronym is a word);
   - *small talk*: greetings and thanks, and nothing else (tuning variant B);
   - *pasted content*: three lines, a code block, or a verb of acting before a colon;
   - *an instruction to the app*: specific phrases, in both languages (tuning variant B).
2. **The model's reading:** one closed yes/no field, generated after the surface (variant D), under D-169's instructions on
   the owner's line. It is variant 3 of #66, which stayed inside the false-positive bound.
3. **The decision:**
   - *no word* or *small talk* → the note;
   - the model says "not a search" **and** pasted content or an instruction to the app → the note;
   - any one of those three alone → **the question back** ("Did you mean to find a model for this?"),
     with two taps: *find a model* (the ranking, as routed) or *no* (the note);
   - otherwise → a search, routed as today.
4. **The screen:**
   - the note and "Change", with no ranking, no request and no gap entry (D-169 clauses 4 and 5);
   - the question back shows the two taps and sends nothing until one is tapped.
5. **#73** is wording in the model tier's descriptions and instructions, measured. **#113** is wording
   and a rule in code: the model would not decline a request to make an image (tuning: 0 of 6), so a
   request to make or change one is routed as unmeasured on every tier (`makesAnImage`).

## Phases

| Phase | Issues | Acceptance check |
|---|---|---|
| P0 | — | This plan, D-169 brought in and amended, the sets and the baseline committed |
| P1, signals | #66 | Each signal is tested on its own; none fires on a genuine question in the tuning sets, but one, a task with its content after a colon, which is a doubt by D-169 and is named in the test |
| P2, reading | #66 | `RoutingOutcome` carries the reading; the boundary maps the model's field; the decision table is tested; the screen shows the note and the question back, held by UI tests |
| P3, wording | #73, #113 | Tuned on the tuning sets, at most three variants each |
| P4, measure | #66, #73, #113 | Every bar above holds in both runs on the held-out sets; the research record holds the runs |

## K.8 contracts (grep at `93040ac`)

```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:421:    static func schema(for known: [String]) throws -> GenerationSchema {
ios/ModelRanking/Engine/Router.swift:543:    static func outcome(
ios/ModelRanking/Engine/Router.swift:636:    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
```

**No `/v1` change.** A not-a-search outcome sends no request at all.

## The one alternative

**A stronger model** (a larger one on the device, or one on a server). The phone has no larger model,
and one on a server would send the question off the device (D-126), so it is not taken.
