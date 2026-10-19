# Enhancement plan: Apple Intelligence reads every question (#351)

**Golden Rules served:** 2 (understand every question with an AI model, Apple Intelligence in every case) and 3 (the most correct list), as v1 order steps 3 and 4, worked together (D-210).

## Goal

The app answers every question through Apple Intelligence wherever the device has it. The on-device model's understanding is **measured** and then raised to the owner's bar. Until now, every measurement and every reading rule ran on the wording tier only.

## Where it starts

- `TieredRouter.route` (`ios/ModelRanking/Engine/Router.swift:1285`) asks the model first, with an 8 s deadline. The wording tier answers when the model is unavailable, times out or returns nothing. It also answers when the model says "none of these" for a question it read as a search (`:1291`).
- The golden test runs `TieredRouter(model: nil)`. The fresh m24 set (173 rows) scores 83/173 on the wording tier. The model tier has never been scored.
- The owner's Mac has Apple Intelligence `available` (macOS 26.5). The Engine package builds for `.macOS(.v26)`.

## Scope

**In:** measuring the model tier; its instructions, surface descriptions and schema; the wording tier no longer overriding a model answer; a prewarmed session and waiting for a downloading model; the glow following the model's reading; a new independent fresh set (m25) as the judge.

**Out:** the fallback LLM for devices without Apple Intelligence (its own ADR, D-210); composing a list no board ranks (v1 step 6, last); the engine and `/v1`.

## Decisions (resolved with the owner, 2026-10-19, #351)

1. **Bar.** On m25 the model tier gets at least 85% of surfaces right and catches at least 80% of non-searches, and it beats the wording tier on both.
2. **Glow.** It is always shown while Apple Intelligence is available, and it turns livelier while the model reads the question.
3. **m24 enters the repository as a tuning set.** It was kept out only while #295 was open, and #295 is closed. m25, written in phase 4, is the held-out judge and stays out of the repository until it has judged.
4. **The model names what a non-search is.** Its answer may be one of a closed set of non-search kinds: the task itself, a question of fact, a question about this app, small talk or no meaning, an instruction to the app. `ModelOutputBoundary` maps each to the not-a-search verdict. This widens INV-69's closed set; the owner approved changing its tests, and an ADR records it before the code. It is measured first: on 2026-09-28 (#66, variant 4) five named kinds caught 25 of 39 non-searches but cut 45 of 89 genuine searches, under the line D-211 has since moved (the task itself was a search then). `InputSignals.namesAnAI` (it forces 7 of m24's 61 non-searches to search) is measured with and without the kinds, and stays only if it still earns its rows.
5. **m25.** About 300 searches and 200 non-searches: the non-search side needs 170-350 rows to show 80% at all. The bar is met on the observed rates; the Wilson interval is reported beside them.
6. **Which model judges.** Every run records the OS build and, on 27, `SystemLanguageModel.default.variant`. The owner's Mac (M3) and iPhone 17 Pro Max may both run AFM 3 Core Advanced, while most iPhones run AFM 3 Core. If so, the verdict names the variant it judged. The owner's iPhone 12 Pro has no Apple Intelligence: it checks the path without it.

## Research (2026-10-19)

Three research agents, the owner's. All three: greedy decoding first; then the non-search kinds and retrieved examples; no adapters (OS 27 removed them), no voting, no self-reported confidence, no free-text reasoning; decide on per-question pairs with an exact McNemar test. One report's own source check found the large retrieval gains were measured against random examples, so the kinds go first. Checked on the owner's Mac (M3, macOS 26.5.2): `NLContextualEmbedding`'s Latin model covers Turkish (512 dimensions, installed), so retrieval can start with Apple's embedding at no app size; Russian and Arabic questions are answered, not refused, though neither is an Apple Intelligence language (m24 holds two of each).

## Phases (one commit each, `make check` green after each)

1. **Measure.** Add `ModelTierMeasurementTests`, which runs the real `ModelRouter` over the golden set and m24. It reports surface accuracy, search/not-a-search accuracy, the wording tier side by side, latency, and nil/timeout counts, into a report under build/. Add a make target named model-tier. It runs only with `RUN_MODEL_TIER=1` on a machine where the model is available, and otherwise prints SKIPPED with the reason. It is never a silent pass.
   *Acceptance:* the report exists with both tiers' numbers on both sets, and the skip is visible in `swift test` output.
2. **Improve the model tier.** Change the instructions, `CategoryHints` and refinement guidance against the m24 misses. Each step stays only if, on per-question rows, it fixes more m24 rows than it breaks (exact McNemar, D-206) and the golden set loses at most 2.
   1. Greedy decoding: one question always reads the same way on one model version.
   2. The model-tier target keeps each question's row and compares two runs.
   3. The non-search kinds (decision 4).
   4. Retrieved examples: the 8 nearest labelled questions by Apple's embedding, against a fixed block of 8.
   5. Only if 3 and 4 fall short: a second classifier beside the model. It never overrides the model without the owner's ruling.

   *Acceptance:* the before and after numbers are in the PR body, and no regressions.
3. **Apple Intelligence in every case.**
   - The wording tier does not override a model answer.
   - The session is prewarmed when the question field gains focus (latency only, all three reports).
   - A `downloading` model is waited for or retried before the wording tier answers.
   - The glow is always on while the model is available, and livelier while it reads.

   Each behaviour gets a red test first, in `RouterBoundaryTests` or `FrontDoorTests`, through the scripted model seam.
   *Acceptance:* each behaviour has its citing test, and REQ-APP-007 is updated.
4. **Judge.** An independent seat writes m25, about 500 questions (the owner's answer of 2026-10-19: 173 rows tell apart only about 8 points), by `docs/research/reading-wave-m24-probe.md`'s method, without seeing phases 1-3. The model-tier target scores it on macOS 27, whose on-device model readers on iOS 27 have.
   *Acceptance:* the bar in decision 1 is met, or the PR says by how much it is missed and files the rest.
