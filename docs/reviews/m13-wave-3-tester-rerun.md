---
record_type: review
id: m13-wave-3-tester-rerun
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W3 — Tester seat, re-run against the post-fix tree (V3C-72)

**Reviewer:** the same independent Tester seat as `m13-wave-3-tester.md`. It authored none of the wave's code, and none of the post-fix changes.
**Subject:** `m13-w3-r2.diff`, the full W3 diff against `HEAD` `10a521c` with `docs/reviews/` excluded: 1969 lines across 13 files. It applied cleanly to a fresh `git archive HEAD`.
**Policy source (V4C-06):** `subagent-profiles/Tester.md`, `AGENTS.md` and `permission-matrix.md` §11 at `HEAD`, as before. No policy was read from the diff.
**Author family / reviewer family (V4C-03):** the author's family is unrecorded. The reviewer runs on Claude Opus 5, so this is a same-family fallback. Fresh context is asserted.

**Provenance.** Everything ran in three private copies under the session scratchpad. Each was built with `git archive HEAD`, then `git apply`, then a read-only copy of `advisor.db`:

| Copy | Used for |
|---|---|
| `tester-w3r2` | the Engine trials and coverage |
| `tester-w3r2-py` | the `ContentView` trials, then one diagnostic for DC4 |
| `tester-w3r2-probe` | the probes |

The repository was read-only apart from this one new file.

**The subject is the frozen diff, not the working tree.** During this run the repository's `Router.swift` changed: its md5 is `af47f6bd…`, where the frozen tree's is `8de3ed55…`. The change adds two hunks: alternatives on the decline branch, and `job.cancel()` in `firstWithin`. Neither is reviewed here. `FrontDoor.swift` (`d0c7cca0…`) and `ContentView.swift` (`65248a10…`) match the frozen tree.

## Baseline at the post-fix tree

| What | Result |
|---|---|
| `pytest tests/unit` | 860 passed / 7 skipped |
| `pytest tests` (unit + integration) | **869 passed / 12 skipped**. This reconciles the coordinator's "869". |
| `swift test` | **191 tests, 0 failures** |
| Line coverage, `FrontDoor.swift` | **100%** (106/106) |
| Line coverage, `Router.swift` | **97.64%** (373/382). HEAD was 96.36%, and the first W3 tree was 95.73%. |

## Verdict: PASS WITH FINDINGS

**All three blocking items from the first record are discharged:**
- **B1 (REQ-ASK-003): discharged.** The first record's RED probe, `ProbeW3ShippingTierTests.testTheWavesOwnUnmeasuredExamplesOnTheShippingTier`, now passes. `UnmeasuredQuestionTests` routes the photo, speed and context-window questions through the shipping `SimilarityRouter`. The decline block is load-bearing: skipping it (DC2), keeping only its first hint (DC3) and marking its outcome measured (DC5) are each killed.
- **B2 (REQ-ASK-004): discharged.** Removing `invalidate()` from `select()` (RGV1), moving the post-routing guard below `routing = outcome` (RGV2), taking the ticket after the await (RGV4) and a no-op `invalidate()` (IV1) are each killed.
- **B3 (coverage): discharged.** `Router.swift` is above its HEAD level. The one new uncovered line is the `.notEligible` fallback at `Router.swift:468`, which is OS1 and ledgered.

**15 of the first record's 17 non-equivalent survivors are now killed.** RN2t and OS1 remain.

**One new MAJOR finding: the decline hints over-decline.** See below. The Code-Reviewer's re-review reports the same finding as NEW-1. This seat measured it before opening that record.

## Trial table

Each trial ran in one atomic sequence:
1. Record the pre-injection md5.
2. Apply the exact string replacement. RGV2, RO1 and WF2 each apply two, because they move a line.
3. Run the suite.
4. Revert in place by splicing the original text back at its recorded offset.
5. Compare the md5.

Engine mutants ran `swift test` and `pytest tests/unit`. `ContentView.swift` is outside the SwiftPM target, so its mutants ran `pytest tests/unit`. **All 72 trials were revert-clean**, and the final md5 of all three files matched the pristine values in every copy. No trial crashed the suite; OD1 now fails through `XCTUnwrap`, not a fatal error.

`contract` below is `test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on`. `UQT` is `UnmeasuredQuestionTests`.

### `ios/ModelRanking/Engine/FrontDoor.swift`

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| CS1 | `canSubmit`: `&&` → `\|\|` | `SubmissionTests.testBlankQuestionsAreNotSent`, `.testNothingIsSentTwiceWhileTheFirstIsStillRouting` | True |
| CS2 | `canSubmit`: trim dropped | `SubmissionTests.testBlankQuestionsAreNotSent` | True |
| RG1 | `isCurrent` → `true` | three `RequestGateTests`, including `testASelectionMadeWhileAQuestionRoutesWins` | True |
| RG2 | `begin` without incrementing | three `RequestGateTests` | True |
| IV1 | `invalidate()` a no-op (new) | `RequestGateTests.testASelectionMadeWhileAQuestionRoutesWins` | True |
| EL1a | `echoLine`: `>` → `>=` (first-record survivor) | `EchoTests.testAQuestionOfExactlyTheLimitIsQuotedWhole` | True |
| EL1b | `prefix(echoLimit + 1)` | `EchoTests.testALongQuestionIsCutRatherThanWrappedIntoAParagraph`, `.testOneCharacterOverTheLimitIsCut` | True |
| EL1c | `prefix(echoLimit - 1)` (first-record survivor) | `EchoTests.testOneCharacterOverTheLimitIsCut` | True |
| EL2 | newlines kept | `EchoTests.testTheEchoIsTrimmedAndKeptToOneLine` | True |
| RN1 | manual ↔ wording-unmeasured, English | `RouterBoundaryTests.testAnUnmeasuredOutcomeDisclosesItselfRatherThanImplyingAMeasurement`, `UQT.testTheWordingTiersDeclineSaysItIsGoingByTheWording`, `UQT.testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured` | True |
| RN1m | manual ↔ model-unmeasured, English | `UQT.testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured` | True |
| RN1t | manual ↔ model-unmeasured, Turkish (first-record survivor) | `UQT.testEveryUnmeasuredBranchSaysItsOwnThingInTurkish` | True |
| RN1ts | manual ↔ wording-unmeasured, Turkish | `UQT.testEveryUnmeasuredBranchSaysItsOwnThingInTurkish` | True |
| RN2 | measured similarity, English, gets the unmeasured text | `UQT.testAMeasuredMatchDoesNotCarryTheUnmeasuredSentence` | True |
| RN2t | the same in Turkish (first-record survivor) | **none: GREEN** | True |
| RN3 | measured model tier, English, gets the unmeasured text | `RouterBoundaryTests.testAMeasuredOutcomeDoesNotCarryTheUnmeasuredSentence`, `UQT.testAMeasuredMatchDoesNotCarryTheUnmeasuredSentence` | True |
| RN3t | the same in Turkish | **none: GREEN** | True |
| RN5 | the wording tier's decline loses "Going by its wording" | `UQT.testTheWordingTiersDeclineSaysItIsGoingByTheWording` | True |
| OD1 | `.turnedOff` help → `nil` | `OnDeviceHelpTests.testEveryDegradedStateExplainsItselfInBothLanguagesWithoutSoundingLikeAnError`, which now fails without a crash | True |
| SC1 | `surfaceChoices` drops the last surface | `EchoTests.testTheCorrectionReachesEverySurfaceTheEngineServes`, `.testTheCorrectionIsInTheReadersLanguage` | True |
| SC2 | the wrong surface marked selected | `EchoTests.testTheCorrectionReachesEverySurfaceTheEngineServes` | True |

### `ios/ModelRanking/Engine/Router.swift`

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| TR1 | manual → `unmeasured: false` | `RouterBoundaryTests.testWithNoTierAtAllTheReaderStillGetsASurface`, `UQT.testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured` | True |
| SA1 | alternatives `[]` | `AlternativeSurfaceTests.testTheWordingTierOffersTheNextClosestSurfacesAsAlternatives` | True |
| SA2 | the best included | same | True |
| SA3 | only one alternative kept | same | True |
| SA4 | insertion `<` → `<=` | **none: GREEN** (equivalent) | True |
| SA5 | alternatives on the floor branch | `AlternativeSurfaceTests.testAnUnmeasuredQuestionOffersNoAlternativesBecauseNothingMatched` | True |
| SA5d | alternatives on the new decline branch | **none: GREEN** | True |
| SA6 | the insertion keeps a wrong second and third (first-record survivor) | `AlternativeSurfaceTests.testTheAlternativesDoNotDependOnTheOrderTheSurfacesArrivedIn` | True |
| OS1 | `onDeviceState()` fallback → `.available` | **none: GREEN** (host-unreachable, ledgered) | True |
| DC1 | the decline comparison `>` → `>=` | **none: GREEN** (equivalent) | True |
| DC2 | the decline block skipped | `UQT` image, speed and context-window tests | True |
| DC3 | only the first decline hint used | `UQT` speed and context-window tests | True |
| DC4 | the audio/video decline hint deleted | **none: GREEN** | True |
| DC5 | a decline marked measured | `UQT` image, speed and context-window tests | True |
| FW1 | `firstWithin` loses its timeout task | `SlowTierTests.testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier` | True |
| FW2 | `ResumeOnce` no longer clears the continuation, so it resumes twice | **none: GREEN** | True |
| MT1 | `modelTimeout = 0` | `SlowTierTests.testTheShippedDeadlineIsLongerThanTheMeasuredColdStart` | True |
| MT2 | `route` ignores `modelTimeout` (passes 3600) | `SlowTierTests.testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier` | True |

### `ios/ModelRanking/ContentView.swift` (Python contract test only)

Every row below that is RED was killed by `contract`, and by nothing else.

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| WF1 | `.focused` removed | contract | True |
| WF2 | the in-flight flag set in `ask()`, not `submit()` | contract | True |
| WF3 | the guard after the recommendation deleted | contract | True |
| WF3b | `load()`'s `defer` ungated (first-record survivor) | contract | True |
| WF3c | the categories re-read ungated | contract | True |
| WF3m | `state = .loaded` placed above its guard (the code review's M1) | contract | True |
| WF4 | the echo quotes `question`, not `asked` | contract | True |
| WF5 | alternatives not rendered (first-record survivor) | contract | True |
| WF5b | alternatives inert (first-record survivor) | contract | True |
| WF6 | `.searchable` back on the home screen | contract | True |
| WF7 | the send button's `.disabled` dropped | contract | True |
| WF8 | `asked = typed` dropped (first-record survivor) | contract | True |
| WF9 | `select()` keeps `routing` (first-record survivor) | contract | True |
| WF10 | the `.sheet` removed (first-record survivor) | contract | True |
| WF11 | the sheet's buttons do not select (first-record survivor) | contract | True |
| WF12 | the in-flight flag never released (first-record survivor) | contract | True |
| WF13 | `Change` does nothing (first-record survivor) | contract | True |
| WF14 | the echo computed and not rendered (first-record survivor) | contract | True |
| WF15 | the send button bypasses `submit` | contract | True |
| WF16 | Return bypasses `submit` | contract | True |
| WF17 | the on-device help condition inverted (first-record survivor) | contract | True |
| RGV1 | `routingGate.invalidate()` removed from `select()` | contract | True |
| RGV2 | the post-routing guard moved below `routing = outcome` | contract | True |
| RGV3 | the guard after `ask()`'s own `await load()` deleted | **none: GREEN** | True |
| RGV4 | the ticket taken after `await router.route` | contract | True |
| AK1 | `if categories.isEmpty { await load() }` dropped | **none: GREEN** | True |
| AK5 | `!=` → `==` on the routed surface (the code review's M5) | contract | True |
| RO1 | the echo set before the load (MINOR-8) | contract | True |
| BU1 | `budget = "low"` (the code review's M2) | contract | True |
| OR1 | the notice loses its orange (the code review's M6) | contract | True |
| CE1 | the send button enabled with no surfaces | **none: GREEN** | True |
| CE2 | `Change` enabled with no surfaces | **none: GREEN** | True |
| CE3 | the "surfaces unavailable" line never shown | **none: GREEN** | True |

## Kill rate

**59 of 72 killed (82%).** Excluding the two equivalent mutants (SA4 and DC1): **59 of 70 (84%).**

| File | Killed |
|---|---|
| `FrontDoor.swift` | 19 of 21 |
| `Router.swift` | 12 of 18 |
| `ContentView.swift` | 28 of 33 |

**The coordinator's list for the new code: 6 of 9 killed.** DC2, DC3, FW1, MT1, RGV1 and RGV2 die. DC1 is equivalent. FW2 and AK1 survive.

**The first record's survivors:** 15 of the 17 non-equivalent ones are killed, by the tests the coordinator named. RN2t still survives, and OS1 is ledgered.

**Probes.** 10 of the 11 non-equivalent survivors are killed by a probe this seat wrote in `tester-w3r2-probe`. OS1 is the exception; it cannot run on this host. For DC4 no question could be found that the deleted hint decides, so its probe is not really a kill: see the survivors table. Every probe passed on the unmutated post-fix tree, and each went RED against its mutant, with the md5 revert-clean. No probe was added to the repository.

## New finding

| # | Severity | Where | Finding | Evidence | Test that should exist |
|---|---|---|---|---|---|
| NEW-1 | **MAJOR** | `Router.swift:94-98`, `:231-242` | **The fix for B1 over-declines.** The decline hints fire on a question that mentions a picture or latency even when the job itself is measured. Such a question now gets the chat ranking, labelled unmeasured. The calibration test holds seven probe questions, and none of them uses the decline vocabulary, so nothing pins this. It is the opposite error to the one REQ-ASK-003 forbids, and a regression against REQ-RTR-001. | On the first W3 tree these routed as measured, and on the post-fix tree all three decline: *"build a photo gallery website"* (was `web-dev`), *"write a script that resizes images"* (was `agentic-coding`), *"optimise the latency of my web API"* (was `coding`). The probe `ProbeW3R2FalseDeclineTests.testAMeasuredJobThatMentionsADeclineTopicIsStillMeasured` is **RED on the post-fix tree, with 3 failures**. Coding questions with "faster" or "slow" in them ("make my python code run faster", "speed up this slow SQL query") still route to `coding`. | Calibration pairs that mention the decline vocabulary but ask for a measured job, asserted measured. Otherwise, if the owner accepts false declines as the cheaper error (the working tree's comment argues this), record that acceptance and assert that the declined outcome carries its alternatives. |

## Surviving mutants and the test each needs

| Mutant | Severity | Finding | Test that should exist | Probe |
|---|---|---|---|---|
| RN2t, RN3t | MINOR | A measured Turkish notice can carry the unmeasured `söyleyemez` sentence. The new Turkish test covers only the three unmeasured branches. | Assert that the Turkish notice for each measured tier (`.model` and `.similarity`) does not contain `söyleyemez`. | First-record `ProbeW3TurkishNoticeTests.testEachTurkishNoticeSaysWhatItsEnglishSays`: RED for both |
| SA5d | MINOR | Whether a declined question carries alternatives is pinned in neither direction. The frozen tree gives none, and the working tree now deliberately adds two. | Whichever the owner keeps: `[]` on the frozen design, or two measured surfaces on the working tree's. | `ProbeW3R2DeclineTests.testADeclinedQuestionOffersNoAlternatives`: RED |
| FW2 | MINOR | No test lives past the deadline of a call that answered in time, so a `ResumeOnce` that resumes twice is never exercised. On the shipping default (8 s) the timer's resume happens after the test has returned. | Call `firstWithin(0.1, …)` with work that answers at once, then wait 0.4 s. On the mutant, the timer's resume is the fatal `CONTINUATION MISUSE`. | `ProbeW3R2ResumeOnceTests.testTheLosingTaskDoesNotResumeASecondTime`: RED (fatal error) |
| RGV3 | MINOR | The guard after `ask()`'s own `await load()` is unpinned. Suppose the reader picks from `Change` while the routed surface loads. The load itself is gated, but `ask()` then sets `asked` and `routing`, so the overruled route's echo and notice reappear above the surface the reader chose. | Assert `await load()` directly followed by `guard routingGate.isCurrent(ticket) else { return }` inside `ask()`. | `test_probe_r2_a_selection_during_the_load_still_wins`: RED |
| AK1 | MINOR | The reload of an empty surface list before routing (MINOR-7) is unpinned. Without it, a question asked after a failed discovery call is dropped silently. | Assert `if categories.isEmpty { await load() }` precedes `let known` in `ask()`. | `test_probe_r2_an_empty_surface_list_is_reloaded_before_routing`: RED |
| CE1, CE2, CE3 | MINOR | The no-surfaces handling (MINOR-7) is unpinned. The contract regex for the send button was loosened to drop its closing parenthesis, so it accepts the button without `\|\| categories.isEmpty`. | Assert the full `.disabled(… \|\| categories.isEmpty)`, `.disabled(categories.isEmpty)` on `Change`, and the `surfacesUnavailable` line under `if categories.isEmpty`. | `test_probe_r2_no_surfaces_is_disabled_and_said`: RED for all three |
| DC4 | NIT | Deleting the audio/video hint changes none of 12 audio and video questions this seat tried: transcription, video edit, text to speech, voice cloning, a jingle, noise removal, game music, voice chat, captions, a sound effect, and others. Each routes identically either way, because the floor or another hint already declines it. The diagnostic's revert was md5-clean. | Either delete the hint, or add a question it alone decides. | none: no deciding question found |
| OS1 | ledgered | The `.notEligible` fallback line cannot run on a macOS 26 host. The coordinator ledgers it. | An injection seam, as the first record said. | none possible |
| SA4, DC1 | none | Equivalent. They differ only on an exact cosine tie. | none | n/a |

## Per-criterion citing-test check (post-fix)

| REQ-ID | Citing tests and entry point | Verdict |
|---|---|---|
| REQ-ASK-001 | `SubmissionTests` enter through `canSubmit`. The contract test now also pins the release of the in-flight flag (WF12), both submission paths (WF15, WF16) and focus (WF1). The keyboard is unverified by design: the prd row now reads **PARTIAL** and names the owner's verification. | Logic proven. Keyboard: the owner's, as recorded. |
| REQ-ASK-002 | `EchoTests` (both sides of the boundary now), `AlternativeSurfaceTests` through the live `SimilarityRouter`, and the contract test's end-to-end correction path (WF5, WF5b, WF8–WF11, WF13, WF14 all killed). | Proven. NEW-1 widens the two-tap case. |
| REQ-ASK-003 | `UQT` image, speed and context-window tests through the shipping `SimilarityRouter`. The calibration counter-test, the model-decline path (now labelled as that), manual, and `RouterBoundaryTests.swift:59`. | Proven for under-declining. Over-declining is NEW-1, unpinned. |
| REQ-ASK-004 | `RequestGateTests` (including `testASelectionMadeWhileAQuestionRoutesWins`), and the contract test for `load()` and for `ask()`'s routing ticket. | Proven, except the post-load guard (RGV3, MINOR). |

## Notes

- **Test integrity (V3C-86).** The only test weakened between the two rounds is the `.disabled` regex. It lost its closing parenthesis so that it would accept the new `|| categories.isEmpty`, and that is what lets CE1 through. It is a loosening to accommodate new code, not a deletion to green, and it is recorded above. The stub-based decline test was kept and relabelled as a test of the decline path, as the first record asked.
- **Turkish notice wording.** The new wording-tier notice opens `Kelimelerine bakılırsa`, and the manual notice still names `Değiştir`. Both are asserted.
