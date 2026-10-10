---
record_type: review
id: m20-wave-4-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# Wave 4 Tester Review (m20): the combined list is the default answer (#212, #208, #211's wiring)

**Tester:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer, and it is not the Stage 5.1 security seat.
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `2e6bd28..6e2820f`. W4's own commits (`git log --no-merges 2e6bd28..6e2820f` on the
wave's seven files) are `1e0d0a7` (red), `b805c30`, `f97018b`, `6ab7389`, `b9c34cf` (red), `452dc48`,
`992fc35` (UI tests), `36dad00`, `4ea8548` (the first review's tests, red), `9e05bb1`, `7a3aa3e`,
`9c34e3e` (the second round's tests, red) and `6e2820f`.
**Risk tier:** HIGH
**Code-Reviewer verdict:** round 1 BLOCKING (`docs/reviews/m20-wave-4-review-round-1.md`), round 2
MINOR, M1 to M3 (`docs/reviews/m20-wave-4-review.md`), answered in `9c34e3e`/`6e2820f`. Not BLOCKING,
so this seat runs.
**Model routing (HIGH, advisory):** author family: Claude (`GP-Agent: claude-code/local-lane`) /
reviewer family: Claude (Opus 5.5). Fallback reason: no second model family is available to this seat.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75dac85...`) on
`origin/main` and in the tree. The range touches neither `.claude/` nor `.agents/`.

## Verdict
MINOR

## Summary

Every acceptance criterion W4 touches has a citing test that passes, and the gates are green apart
from one leg that needs a database this worktree lacks. Fault injection planted 22 faults (20 in the
wave's code, 2 re-plants of the W3 Tester's fixes). The wave's tests caught 12 of the 20. Seven
of the 8 they missed are real gaps, and one (A6) is equivalent: no test or screen can see it. This
review adds four tests. Each passes on the shipped code, and together they catch all seven gaps and
both re-plants. The two that matter most: the second round's M3 fix left three of the family note's
four numbers unheld (M1), and the sentence the family list itself shows was held by no test, so round 1's
BLOCKING B1 could come back with the suite green (M2). One red commit, `4ea8548`, does not compile
(M5), as in W3. No defect in the shipped behavior was found. Since W4 now calls the word reader,
the W3 Tester's probes were re-run through the answer plan, and both of its fixes hold there.

## Acceptance-criterion coverage (REQUIRED)

- **REQ-CMB-005, "the combined list is the default answer to every question asked and every surface
  the reader chooses"** → `FamilyPlanTests.swift:37` (`testAnEngineThatNamesAFamilyShowsTheFamilysListByDefault`),
  `:230` (a chosen surface, through `PlanMemo`), `:158` (`plannedOutcome`: planned only once the
  surface's answers are on screen) — GREEN. The launch screen plans nothing (`:165`).
- **REQ-CMB-005, "it says it is the product's own order, built from N boards with each board's date,
  and how many of them a model needs"** → `FamilyPlanTests.swift:117`, `:138` — GREEN, but the counts
  were not held where the list says them (M1) and the sentence the list draws was not held at all
  (M2). Closed by `FamilyPlanTests.swift:275`.
- **REQ-CMB-005, "an older board is a small note with its date, never a warning over the list"** →
  `FamilyPlanTests.swift:84`, `:101` — GREEN (faults A7 caught).
- **REQ-CMB-004 / D-188 clause 6, "the on-device model's refinements where it read the question, the
  words otherwise"** → `FamilyPlanTests.swift:58`, `:72`, `:191` — GREEN (A2, A3, A4 caught). The
  standings filter on the family path was unheld (M3); closed by `:305`. The W3 Tester's word probes,
  re-run through the answer plan as its R1 asked: closed by `:321`.
- **REQ-APP-002 / REQ-APP-008 / Ruling A, "both coding lists or neither, neither leading"** →
  `FamilyPlanTests.swift:204` (`pairedSurface`, `pairedOutcome`), `:215` (`familyLists`), `:158`
  (`plannedOutcome`) — GREEN (A11, A12, A13 caught). The view's composition of the three
  (`ContentView.swift:192-205`) is view code; only `ScreenPathTests` exercises it (R1).
- **REQ-APP-007, "one caption per state of the on-device model, in both languages"** →
  `LanguageTests.swift:598` — GREEN for English; the Turkish mapping was unheld for two states (M4).
  Closed by `LanguageTests.swift:623`. The glow is view code that no Engine test runs.

## Red→green on reported symptoms

Each red commit was built from `git archive <commit> ios scripts/router_probe` into its own scratch
folder and run with `swift test` (the whole Engine suite).

- `1e0d0a7` (red, #212): compiles; 532 tests, 6 failed assertions in exactly four tests, all
  in `FamilyPlanTests` and all added by the commit (`testAnEngineThatNamesAFamilyShowsTheFamilysListByDefault`,
  `testALanguageWordAddsItsBoardWithNoModel`, `testAnOldFamilyBoardIsASmallNoteNotTheLoudWarning`,
  `testTheWeighedHalfNoteIsSaidInBothLanguages`). Its other three (`testAFamilyOfOneBoardShowsTheCards`,
  `testAnEngineOlderThanM20KeepsTodaysPlan`, `testTheMemoPlansAgainWhenTheFamilyOrTheQuestionChanges`)
  hold what was already true, so they are green as intended. Red on its own tests only.
- `b9c34cf` (red, D-188 clause 6): compiles; 557 tests, one failing:
  `testTheOnDeviceModelsChoiceOfNoRefinementStands` (the words added `arena_text_french` where the model
  chose none). Red on its own test only; GREEN at `452dc48`.
- `4ea8548` (the first round's tests, red): **does not compile** (135 errors; M5). No Swift test
  runs.
- `9c34e3e` (the second round's tests, red): compiles, with `plannedOutcome` stubbed; 575 tests, 5
  failed assertions in exactly the two tests it adds (`testASurfaceIsPlannedOnlyOnceItsAnswersAreOnScreen`,
  `testTheFamilyNoteSaysHowThePlaceIsReachedInBothLanguages`: "placed by its mean position"). Red on
  its own tests only; GREEN at `6e2820f`.
- Round 1's B1 symptom (a family list said every model is on every board): its repro,
  `testAFamilyListSaysItsBoardsTheirDatesAndTheCoverage`, never ran red (M5). N1 re-planted the
  symptom at `6e2820f` and the wave's tests stayed green (M2); this review's test goes red on it.

## Suite result

- `make check-fast` at `6e2820f` before this review's tests: lint, typecheck, records, client-decls
  and swift-test (`swift-test-parallel`) PASS; the `test` leg stops at once with W-108 ("this run must
  execute the tests that read advisor.db, and it is missing"): the worktree has no built
  `advisor.db`, an environment fact, not the wave's. The same pytest run without
  `MODEL_RANKING_REQUIRE_ARTIFACT`, under the offline sandbox: 2141 passed, 77 skipped (the
  `advisor.db` tests), 0 failed.
- With this review's tests and this record: `make check-fast` gives lint, typecheck, records,
  client-decls PASS, and swift-test PASS ("579 test(s), exactly the ones named in
  ios/EngineTests/test-manifest.txt"); the `test` leg stops on W-108 as above. The four new tests
  alone: `swift test --filter` 4 tests, 0 failures.
- Coverage on touched code: no Swift coverage tool is wired for the Engine package; the planted
  faults below stand in for it.

## Mocks / contract tests

- No integration is added or changed. `EngineClient` and the `/v1` request are untouched in the
  range; the plan reads the family `/v1/categories` already serves (W1's contract tests).

## Fault injection

Each fault was planted in a scratch copy of `ios/` outside the worktree (taken from the worktree at
`6e2820f`), run with `swift test --filter
"FamilyPlanTests|ScreenExplanationTests|UITextLanguageTests|AnswerPlanTests|CombinedListLanguageTests|FamilyCombineTests"`,
and restored by writing the original bytes back; the sha256 was then checked against the original
(`AnswerPlan.swift` `44f5e7600d69...`, `Language.swift` `35383ff020e9...`, `Notices.swift`
`300532cbc1ed...`, `Refinements.swift` `0ef049ef56f7...`; each matched after every plant, and each matches the
worktree). Each fault that stayed green was planted again against the whole suite, and stayed green
there too. W1 and W2 re-plant the W3 Tester's two fixes (`cf4aa2f`) to show this review's probe test
holds them through the answer plan.

| id | fault | the wave's tests | this review's tests |
|---|---|---|---|
| A1 | the plan's `.familyOrder` counts boards as models | **green** (whole suite) | red (`testTheListsOwnNoteSaysEachCountInItsPlaceInBothLanguages`) |
| A2 | the words read on every tier (the model's choice ignored) | red (`testTheOnDeviceModelsChoiceOfNoRefinementStands`) | — |
| A3 | the model's refinements on every tier (the words never read) | red (3 tests) | — |
| A4 | a refinement the surface does not allow offered | red (`testARefinementTheSurfaceDoesNotAllowIsNotOffered`) | — |
| A5 | a refinement whose board the standings lack offered | **green** (whole suite) | red (`testARefinementWhoseBoardTheStandingsLackIsNotOfferedOnAFamily`) |
| A6 | `removed` not intersected with the offered refinements | green (whole suite) | green: equivalent, see below |
| A7 | every family board named as older | red (`testAnOldFamilyBoardIsASmallNoteNotTheLoudWarning`) | — |
| A8 | a family list's coverage dropped (the every-board sentence) | red (`testAFamilyListSaysItsBoardsTheirDatesAndTheCoverage`) | — |
| A9 | a one-board family combined | red (2 tests) | — |
| A10 | a removed refinement still counted | red (2 tests) | — |
| A11 | `plannedOutcome` plans a surface whose answers are not on screen | red (`testASurfaceIsPlannedOnlyOnceItsAnswersAreOnScreen`) | — |
| A12 | the paired surface planned at the manual tier | red (`testThePairedOutcomeIsTheOtherSurfaceAtTheRoutedTier`) | — |
| A13 | `familyLists` returns one coding list alone | red (`testCodingShowsBothFamilyListsOrNeither`) | — |
| A14 | a one-board family takes the pre-M20 path | red (`testAOneBoardFamilyWithEveryRefinementRemovedIsRestorable`) | — |
| A15 | the phone copy's age dropped on a family list | red (`testAnEmptyFamilyListIsTheCardsAndTheCopysAgeIsSaid`) | — |
| L1 | the English note says the model count as the board count | **green** (whole suite) | red (same as A1) |
| L2 | the Turkish note says the board count as the coverage | **green** (whole suite) | red (same) |
| L3 | the Turkish `.downloading` and `.unavailable` captions swapped | **green** (whole suite) | red (`testEachOnDeviceStateHasItsOwnCaptionInTurkish`) |
| L4 | the Turkish note says the coverage as the board count | **green** (whole suite) | red (same as A1) |
| N1 | the list's `.familyOrder` sentence is the every-board `combinedNote` (round 1's B1) | **green** (whole suite) | red (same as A1) |
| W1 | the W3 Tester's M1 fix removed (`notAfter` for "software", "yazilim") | not run (W3's tests) | red (`testTheW3WordProbesAddNoSecondReadingThroughTheAnswerPlan`) |
| W2 | the W3 Tester's M2 fix removed (`notBefore` for "saglik", "health") | not run (W3's tests) | red (same) |

**Counts:** 22 planted. Of the 20 in the wave's code, the wave's tests caught 12 and missed 8 (A1, A5,
A6, L1 to L4, N1). Each of the 8 stayed green against the whole Engine suite too. With this
review's tests, 21 of 22 are caught: the seven real gaps and both re-plants each went red when planted
again, and each file was restored and its sha256 checked. A6 is equivalent: `CombinedView.removed` is
read only by `refinementChips(view.refinements, removed: view.removed)` (`ContentView.swift:390`),
which draws a chip only for an offered refinement, so a removed refinement that is not offered
changes nothing on screen.

## Findings

### BLOCKING
- None

### MINOR

- **M1** `ios/EngineTests/FamilyPlanTests.swift:117-133` and `:138-154`, against
  `ios/ModelRanking/Engine/AnswerPlan.swift:42` and `ios/ModelRanking/Engine/Language.swift:713-716`.
  **The second round's M3 asked for a fixture whose model count, board count and coverage all differ;
  none was written, so three of the note's four numbers are still unheld.** The plan's test still
  uses 3 models on 3 boards, and the second round's new test pins `familyNote` with 2 boards and a
  coverage of 2. Four faults stayed green against the whole suite: A1 (the plan's `.familyOrder`
  counts boards as models: round 2's P10 again), L1 (the English note says the model count as the
  board count), L2 (the Turkish note says the board count as the coverage: `en az 4 panoda`, "on at
  least 4 boards", the second round's own failure scenario) and L4 (the Turkish note says the
  coverage as the board count). The fix commit's message says "the note's count, the Turkish
  coverage ... are held".
  **Failure scenario.** A later edit puts `list.boards.count` where `sharedCount` stands. Coding's
  list of 58 models then says "4 models", and `swift test` stays green; or the Turkish reader of
  coding is told a model needs 4 boards when it needs 2.
  **Fix (done in this review).** `testTheListsOwnNoteSaysEachCountInItsPlaceInBothLanguages`
  (`FamilyPlanTests.swift:275`): 5 models, 4 boards, coverage 2, through `answerPlan`, with the exact
  English and Turkish sentences. A1, L1, L2 and L4 go red on it. Closed.

- **M2** `ios/ModelRanking/Engine/Notices.swift:260-262`, drawn at
  `ios/ModelRanking/ContentView.swift:471`. **The sentence the family list itself shows was held by
  no test, so round 1's BLOCKING B1 could come back green.** The tests hold the disclosure's case
  (`view.disclosures.contains(.familyOrder(...))`) and the boards' screen (`orderNote`), but never
  `combinedDisclosure(.familyOrder(...))`, which is what `disclosureList` renders under the list. N1
  mapped `.familyOrder` back to `UIText.combinedNote` ("The app's own list: N models ranked on all
  N boards", the every-board sentence B1 removed) and stayed green against the whole suite.
  **Failure scenario.** A refactor of `combinedDisclosure` (for instance, folding the two order cases
  into one) renders the intersection sentence under every family list, while the boards' screen says
  the true one. The reader is told every model is on every board.
  **Fix (done in this review).** The same test asserts `combinedDisclosure(order, .english/.turkish)?.text`
  equals the exact family sentence, and `orderNote` equals it too. N1 goes red. Closed.

- **M3** `ios/ModelRanking/Engine/AnswerPlan.swift:201-203`. **The family path's rule that only a
  refinement whose board the standings hold is offered was held by no test.** A5 removed
  `standings.boards.contains { $0.id == refinement.board }` and stayed green against the whole suite.
  **Failure scenario.** The phone keeps a standings copy from before a refinement board was served
  (`phoneCopyDays`), or the engine omits one. A question in French gets a "French" chip, as if
  `arena_text_french` were counted; `combineFamily` silently drops the missing board, so the list does
  not include it. The chip misstates what built the list (D-160 clause 3).
  **Fix (done in this review).** `testARefinementWhoseBoardTheStandingsLackIsNotOfferedOnAFamily`
  (`FamilyPlanTests.swift:305`), for the words tier and the on-device model's tier. A5 goes red.
  Closed.

- **M4** `ios/ModelRanking/Engine/Language.swift:604-609`, against
  `ios/EngineTests/LanguageTests.swift:613-614`. **The Turkish captions for `.downloading` and
  `.unavailable` were unheld.** The second round's M3 asked for each state's caption in both
  languages; the test pins English for all five and Turkish for two. L3 swapped the two Turkish
  captions and stayed green against the whole suite.
  **Failure scenario.** A Turkish reader whose phone is still downloading the model is told it is
  unavailable (and the other way round), which is the very mix-up the first round's M5 removed for
  English.
  **Fix (done in this review).** `testEachOnDeviceStateHasItsOwnCaptionInTurkish`
  (`LanguageTests.swift:623`) pins each Turkish caption, and the two English ones the old test held
  only by a word. L3 goes red. Closed.

- **M5** commit `4ea8548`; `ios/EngineTests/FamilyPlanTests.swift:95-205` and
  `ios/EngineTests/LanguageTests.swift:603-610` at that commit. **A red commit that does not compile,
  the W3 Tester's M3 again.** Built from `git archive 4ea8548`, the test target fails with 135 errors:
  `NamedBoard`, `CombinedDisclosure.familyOrder`, `UIText.familyNote`, `orderNote`, `pairedSurface`,
  `familyLists` and `chosenOutcome` do not exist yet, and `UIText.onDeviceCaption` still takes a
  `Bool`. No Swift test runs, so none of the commit's nine new tests (the first round's B1, M2, M4
  and M5) was seen failing for its own reason. `9c34e3e` did it right: it stubs `plannedOutcome` and
  compiles.
  **Failure scenario.** A red test that would have passed on the old code, and so proves nothing,
  goes unnoticed because nothing ran.
  **Fix.** In a Swift red commit, stub every new symbol (`struct NamedBoard`, a `familyOrder` case
  mapped to an empty sentence, `func pairedSurface(...) -> String? { nil }`, and so on) so the target
  compiles and only the new tests fail. Nothing to redo for this wave: the fix commit's tests pass,
  and the planted faults above show what each test holds. Since this is the second wave running,
  the `/close-wave` red-commit check could build each red commit; that is a process change, for the
  owner to rule on.

## K.9 candidates spotted outside this wave's scope
- None

## Risks queued to next M

- **R1** `ios/ModelRanking/ContentView.swift:192-205` and `ios/UITests/ScreenPathTests.swift:113-150`.
  **The last recorded UI-test run is at `9e05bb1`; the screen changed after it.** `6e2820f` wires
  `plannedOutcome` into what the screen plans, and `9c34e3e` changed `testTheQuestionSaysWhoReadsIt`.
  The commit messages record `make ui-test` only at `9e05bb1` (`7a3aa3e`: ScreenPathTests 18 of 19,
  the one failure then passing alone). This seat could not run the simulator (it is busy, and the
  brief forbids it). The Engine functions are held (A11 to A13 caught), but which inputs the view
  passes them (`answers` for `plannedOutcome`, `ordered` for `pairedSurface`) is held only by the UI
  test. **Failure scenario.** The view passes a stale or reordered list to one of them, a coding
  question shows one list or none, and `swift test` stays green. **Fix.** Before the wave's PR is
  marked ready, run `UI_TEST_ONLY=ScreenPathTests make ui-test` at the wave's head and record the
  count in the wave-close checklist.

## Tests added/extended this review

- `ios/EngineTests/FamilyPlanTests.swift:275` `testTheListsOwnNoteSaysEachCountInItsPlaceInBothLanguages`
  — REQ-CMB-005, D-188 clause 2 (A1, L1, L2, L4, N1).
- `ios/EngineTests/FamilyPlanTests.swift:305` `testARefinementWhoseBoardTheStandingsLackIsNotOfferedOnAFamily`
  — REQ-CMB-004 (A5).
- `ios/EngineTests/FamilyPlanTests.swift:321` `testTheW3WordProbesAddNoSecondReadingThroughTheAnswerPlan`
  — REQ-CMB-004, D-188 clause 6; the W3 Tester's R1 (W1, W2).
- `ios/EngineTests/LanguageTests.swift:623` `testEachOnDeviceStateHasItsOwnCaptionInTurkish` —
  REQ-APP-007, #208 (L3).
- `ios/EngineTests/test-manifest.txt`: the four names, in byte order (`LC_ALL=C sort -c` passes).
