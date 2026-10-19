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

## Phases (one commit each, `make check` green after each)

1. **Measure.** Add `ModelTierMeasurementTests`, which runs the real `ModelRouter` over the golden set and m24. It reports surface accuracy, search/not-a-search accuracy, the wording tier side by side, latency, and nil/timeout counts, into a report under build/. Add a make target named model-tier. It runs only with `RUN_MODEL_TIER=1` on a machine where the model is available, and otherwise prints SKIPPED with the reason. It is never a silent pass.
   *Acceptance:* the report exists with both tiers' numbers on both sets, and the skip is visible in `swift test` output.
2. **Improve the model tier.** Change the instructions, `CategoryHints` and refinement guidance against the m24 misses. Keep each change only if the model-tier target shows no m24 row turned from right to wrong (D-206).
   *Acceptance:* the before and after numbers are in the PR body, and no regressions.
3. **Apple Intelligence in every case.**
   - The wording tier does not override a model answer.
   - The session is prewarmed at launch.
   - A `downloading` model is waited for or retried before the wording tier answers.
   - The glow is always on while the model is available, and livelier while it reads.

   Each behaviour gets a red test first, in `RouterBoundaryTests` or `FrontDoorTests`, through the scripted model seam.
   *Acceptance:* each behaviour has its citing test, and REQ-APP-007 is updated.
4. **Judge.** An independent seat writes m25 (`docs/research/reading-wave-m24-probe.md`'s method), without seeing phases 1-3. The model-tier target scores it.
   *Acceptance:* the bar in decision 1 is met, or the PR says by how much it is missed and files the rest.
