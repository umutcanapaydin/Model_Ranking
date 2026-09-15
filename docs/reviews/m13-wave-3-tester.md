---
record_type: review
id: m13-wave-3-tester
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W3 — Tester seat, fault injection (V3C-72)

**Reviewer:** an independent Tester seat. It authored none of the wave's code.
**Subject:** `m13-w3.diff`, which is 1509 lines across 13 files. It applied cleanly to a fresh `git archive HEAD` (`10a521c`).
**Risk tier:** HIGH (plan §2 W3).
**Policy source (V4C-06):** `subagent-profiles/Tester.md`, `AGENTS.md`, `permission-matrix.md` §11 and the format of `docs/reviews/m13-wave-2-tester-rerun.md`, all read at `HEAD`, plus `docs/plans/m13-plan.md` §1 rows 8–11, §2 W3, §4, §7 and §8. No policy was read from the diff, and no diff content tried to change review policy.
**Author family / reviewer family (V4C-03):** the author's family is not recorded. This seat runs on Claude Opus 5, so treat it as a same-family fallback. Fresh context is asserted: this session holds none of the authoring session's context.
**Sequencing.** The Code-Reviewer's record (`m13-wave-3-review.md`) is BLOCKING. The profile runs this seat after a passing code review. It ran anyway, on the coordinator's dispatch. The REQ-ASK-003 diagnostic below was run before this seat opened the Code-Reviewer's record, so B1 is an independent reproduction, not a copy.

**Provenance.** Everything ran in four private copies under the session scratchpad. Each was built with `git archive HEAD` and, except the HEAD baseline, `git apply`:

| Copy | Used for |
|---|---|
| `tester-w3` | the trials |
| `tester-w3-probe` | the probes |
| `tester-w3-cov` | wave coverage |
| `tester-w3-head` | the HEAD baseline and HEAD coverage |

A read-only copy of the gitignored `advisor.db` went into the Python copies. The repository was read-only apart from this one new file. After the run, the repository's `FrontDoor.swift`, `Router.swift` and `ContentView.swift` have the same md5 as the trial copy's pristine files: `23eeb545…`, `d6c20d5e…` and `a90fbadd…`.

## Baseline

| What | HEAD `10a521c` | W3 tree |
|---|---|---|
| `pytest tests/unit` | 858 passed / 7 skipped | **859 passed / 7 skipped** |
| `pytest tests` (unit + integration) | n/a | **868 passed / 12 skipped**. This reconciles the coordinator's "868": the figure is the whole `tests/` tree. |
| `swift test` | 163 tests, 0 failures | **178 tests, 0 failures** |
| Line coverage, `FrontDoor.swift` (new) | n/a | **100%** (91/91 lines, 11/11 functions) |
| Line coverage, `Router.swift` (touched) | **96.36%** (318/330) | **95.73%** (314/328). **A drop.** See B3. |

The deltas reconcile:
- **Python:** +1, the new contract test.
- **Swift:** `FrontDoorTests.swift` adds 22 tests. It has six classes: 3 + 3 + 6 + 6 + 2 + 2. The code review's "21" is off by one. The wave deletes 7: the six `BudgetOptionTests` and `testTheBudgetCapKeepsItsFigureInBothLanguages`. So 163 − 7 + 22 = 178.

## Verdict: BLOCKING

The pure Engine logic is well tested. `FrontDoor.swift` has 100% line coverage, and 17 of its 24 Engine mutants die, 12 of 16 in `FrontDoor.swift` itself. The coordinator's required list kills 22 of 26. What does not hold is the part of each criterion that lives outside the pure functions:

- **B1 (REQ-ASK-003).** The shipping wording tier answers both of the wave's own unmeasured examples as *measured* `everyday`. The citing tests cannot see this, because a stub declines every question, so the question text in them is inert. A probe through the shipping path is **RED**.
- **B2 (REQ-ASK-004).** A slower *routing* result overwrites a newer selection. `ask()` is not gated, and no test in the wave can fail on it. This seat concurs with the code review's BLOCKING-2, by reading the code.
- **B3 (coverage).** `Router.swift` dropped below its prior level. That is BLOCKING under `permission-matrix.md` §11, "Coverage drop on touched module". All of the new uncovered code is `TieredRouter.onDeviceState()`, the function `ContentView` calls. No test calls it.

**The contract test pins names, not behaviour.** 11 of 20 `ContentView` mutants survive. They include:
- the `Change` sheet never opening
- the sheet's buttons doing nothing
- the echo being computed and never rendered
- the alternatives never being rendered, which the test's own message says it guards
- the in-flight flag never being released, which locks the field after the first question

Each one is killed by a probe this seat wrote in its copy.

## Trial table

Each trial ran in one atomic sequence:
1. Record the pre-injection md5.
2. Apply one exact string replacement. WF2 applies two, because it moves a line.
3. Run the suite.
4. Revert in place by splicing the original text back at its recorded offset.
5. Compare the md5.

Engine mutants ran `swift test` and `pytest tests/unit`. `ContentView.swift` is outside the SwiftPM target (`ios/Package.swift:45`, `path: "ModelRanking/Engine"`), so its mutants ran `pytest tests/unit` only: the Python source-contract test is the only test that can see that file.

**All 44 trials were revert-clean.** A final md5 of all three mutated files matched the pre-injection values. OD1 was re-run alone to capture its raw output, and it was revert-clean again.

### `ios/ModelRanking/Engine/FrontDoor.swift`

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| CS1 | `canSubmit`: `&&` → `\|\|` (:46) | `SubmissionTests.testBlankQuestionsAreNotSent`, `.testNothingIsSentTwiceWhileTheFirstIsStillRouting` | True |
| CS2 | `canSubmit`: trim dropped (:46) | `SubmissionTests.testBlankQuestionsAreNotSent` | True |
| RG1 | `isCurrent` → `true` (:35) | `RequestGateTests.testASlowerResponseForAnOlderSelectionCannotOverwriteTheNewerOne`, `.testTheCurrentResponseIsAppliedWhicheverOrderTheyArriveIn` | True |
| RG2 | `begin` without `latest += 1` (:31) | all three `RequestGateTests` | True |
| EL1a | `echoLine`: `count > echoLimit` → `>=` (:67) | **none: GREEN** | True |
| EL1b | `echoLine`: `prefix(echoLimit + 1)` (:67) | `EchoTests.testALongQuestionIsCutRatherThanWrappedIntoAParagraph` | True |
| EL1c | `echoLine`: `prefix(echoLimit - 1)` (:67) | **none: GREEN** | True |
| EL2 | `echoLine`: newlines kept (:62-65) | `EchoTests.testTheEchoIsTrimmedAndKeptToOneLine` | True |
| RN1 | `routingNotice`: English manual and unmeasured texts swapped (:111-122) | `RouterBoundaryTests.testAnUnmeasuredOutcomeDisclosesItselfRatherThanImplyingAMeasurement`, `UnmeasuredQuestionTests.testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured` | True |
| RN1t | the same swap in Turkish (:115-126) | **none: GREEN** | True |
| RN2 | measured similarity (English) returns the unmeasured text (:127-128) | `UnmeasuredQuestionTests.testAMeasuredMatchDoesNotCarryTheUnmeasuredSentence` | True |
| RN2t | the same in Turkish (:129-130) | **none: GREEN** | True |
| RN3 | measured model tier (English) returns the unmeasured text (:131-132) | `RouterBoundaryTests.testAMeasuredOutcomeDoesNotCarryTheUnmeasuredSentence`, `UnmeasuredQuestionTests.testAMeasuredMatchDoesNotCarryTheUnmeasuredSentence` | True |
| OD1 | `OnDeviceState.help`: `.turnedOff` (English) → `nil` (:164-166) | `OnDeviceHelpTests.testEveryDegradedStateExplainsItselfInBothLanguagesWithoutSoundingLikeAnError` (`XCTAssertNotNil` at `FrontDoorTests.swift:236`) | True |
| SC1 | `surfaceChoices`: the last surface dropped (:87) | `EchoTests.testTheCorrectionReachesEverySurfaceTheEngineServes`, `.testTheCorrectionIsInTheReadersLanguage` | True |
| SC2 | `surfaceChoices`: the first surface marked selected (:91) | `EchoTests.testTheCorrectionReachesEverySurfaceTheEngineServes` | True |

### `ios/ModelRanking/Engine/Router.swift`

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| TR1 | `TieredRouter` manual → `unmeasured: false` (:414) | `RouterBoundaryTests.testWithNoTierAtAllTheReaderStillGetsASurface`, `UnmeasuredQuestionTests.testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured` | True |
| SA1 | alternatives `[]` (:222) | `AlternativeSurfaceTests.testTheWordingTierOffersTheNextClosestSurfacesAsAlternatives` | True |
| SA2 | the best included (`closest.prefix(2)`) (:222) | same | True |
| SA3 | only one kept (`dropFirst().prefix(1)`) (:222) | same | True |
| SA4 | insertion `<` → `<=` (:204) | **none: GREEN** (equivalent) | True |
| SA5 | alternatives offered on the unmeasured branch (:215) | `AlternativeSurfaceTests.testAnUnmeasuredQuestionOffersNoAlternativesBecauseNothingMatched` | True |
| SA6 | a later hint is inserted only if it is a new best or the list is short: `slot < 3` → `slot == 0 \|\| closest.count < 3` (:205) | **none: GREEN** | True |
| OS1 | `onDeviceState()` fallback `.notEligible` → `.available` (:426) | **none: GREEN** | True |

### `ios/ModelRanking/ContentView.swift` (Python contract test only)

`contract` below is `test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on` (:528).

| # | Mutant | Observed RED tests | revert-clean |
|---|---|---|---|
| WF1 | `.focused($questionFocused)` removed (:199) | contract | True |
| WF2 | `routingInFlight = true` moved from `submit()` into `ask()` (:458, :465) | contract | True |
| WF3 | the `guard gate.isCurrent(ticket)` after the recommendation deleted (:515) | contract | True |
| WF3b | `load()`'s `defer` clears `reloading` without asking `isCurrent` (:502) | **none: GREEN** | True |
| WF3c | the categories re-read applied without `isCurrent` (:508) | contract | True |
| WF4 | `echoLine(question: question, …)` instead of `asked` (:231) | contract | True |
| WF5 | alternatives not rendered: `ForEach([String](), …)` (:255) | **none: GREEN** | True |
| WF5b | alternatives rendered, and a tap does nothing (:256) | **none: GREEN** | True |
| WF6 | `.searchable(text:…)` back on the home `NavigationStack` (:89) | contract | True |
| WF7 | `.disabled(!canSubmit(…))` dropped (:215) | contract | True |
| WF8 | `asked = typed` dropped from `ask()` (:471) | **none: GREEN** | True |
| WF9 | `select()` no longer clears `routing` (:486) | **none: GREEN** | True |
| WF10 | `.sheet(isPresented: $choosingSurface) { surfaceSheet }` removed (:90) | **none: GREEN** | True |
| WF11 | the sheet's buttons close it without selecting (:282) | **none: GREEN** | True |
| WF12 | `defer { routingInFlight = false }` dropped from `ask()` (:465) | **none: GREEN** | True |
| WF13 | the `Change` button does nothing (:240) | **none: GREEN** | True |
| WF14 | `Text(echo)` → `Text(surfaceTitle(outcome.categoryID))` (:233) | **none: GREEN** | True |
| WF15 | the send button calls `ask()` directly, bypassing `submit` (:206) | contract | True |
| WF16 | Return calls `ask()` directly (:201) | contract | True |
| WF17 | on-device help shown only when `tier == .model` (:267) | **none: GREEN** | True |

## Kill rate

**26 of 44 killed (59%).** Excluding the one equivalent mutant (SA4): **26 of 43 (60%).**

| File | Killed |
|---|---|
| `FrontDoor.swift` | 12 of 16 |
| `Router.swift` | 5 of 8 (SA4 equivalent) |
| `ContentView.swift` | 9 of 20 |

**The coordinator's required list alone: 22 of 26 (85%), or 22 of 25 (88%) without SA4.** Its survivors are:
- EL1a and EL1c, the two directions of "the limit off by one". EL1b, the third, dies.
- SA4, `<` → `<=`, which is equivalent.
- WF5, "stop rendering `outcome.alternatives`".

The other 14 survivors come from mutants this seat added.

**Probes.** 16 of the 17 non-equivalent survivors are killed by a probe this seat wrote in `tester-w3-probe`. Every probe passed on the unmutated W3 tree, and each went RED against its mutant, with the md5 revert-clean. OS1 has no probe: see below. No probe was added to the repository.

## BLOCKING

| # | Where | Finding | Evidence | Test that must exist |
|---|---|---|---|---|
| **B1** | `FrontDoorTests.swift:139`, `:150`; `Router.swift:212-223` | **REQ-ASK-003 fails on the shipping tier, and its citing tests cannot fail on it (V3C-86, BLOCKING at HIGH).** Both tests build `TieredRouter(model: DecliningModel(), similarity: Silent())`, and `DecliningModel` returns the decline sentinel whatever it is asked. Replace *"make my profile photo look better"* with any string and they still pass. The wave's own `OnDeviceState` comment says that for readers below the 15 Pro *"the wording tier IS the product"*, and on that tier (`TieredRouter(model: nil, similarity: SimilarityRouter())`) the results are wrong. The rest of the diagnostic is mixed. Image, audio, video and "cheapest per token" questions do go unmeasured, but "lowest latency" and "longest context window" both go to measured `everyday`. **Every wrong-axis question this seat tried is answered as measured.** | The wave's two examples, *"make my profile photo look better"* and *"which model answers fastest"*, both route to `everyday`, `tier = similarity`, `unmeasured = false`. The notice is *"Matched on wording, not on meaning"*, not the sentence saying what the ranking cannot tell. Probe `ProbeW3ShippingTierTests.testTheWavesOwnUnmeasuredExamplesOnTheShippingTier` is **RED on the W3 tree: 4 failures** (two questions × `unmeasured` and the notice). This seat found it independently; it is the code review's BLOCKING-1. | That probe, made green by a fix, or an owner amendment that scopes REQ-ASK-003 to the model tier and states the wording-tier gap in the prd row. A stub test may stay, relabelled as a test of the decline path. |
| **B2** | `ContentView.swift:464-480`; `:240`, `:256` | **REQ-ASK-004's "can never overwrite" is proven only for `load()`.** `ask()` awaits `router.route` and then writes `routing`, `asked` and `task`, and starts a load, with no ticket. `Change` and the alternatives stay enabled while `routingInFlight` is set, so a `select()` during the await is overwritten by the late route. The citing tests (`FrontDoorTests.swift:32`, `:48`, `:58`) exercise the struct alone. The contract test's REQ-ASK-004 block reads only `load()`. | By reading. This seat concurs with the code review's BLOCKING-2. `ContentView` is not executable under `swift test`, so no behavioural probe was possible. | Once the fix exists, pin it structurally: a ticket or selection generation taken in `ask()` before `await router.route`, and compared before `routing = outcome`. The alternative is `.disabled(routingInFlight)` on `Change` and on the alternatives. |
| **B3** | `Router.swift:420-427` | **Coverage drop on a touched module (`permission-matrix.md` §11).** `Router.swift` fell from 96.36% to 95.73% line coverage. The only new uncovered code is `TieredRouter.onDeviceState()`, the function `ContentView` stores as `onDevice` to decide whether to show the help. No test calls it. It is why OS1 survives. | `llvm-cov` at HEAD and at W3, both run by this seat. | A test that calls `TieredRouter.onDeviceState()` and asserts it equals `ModelRouter.state` where FoundationModels is present. For the pre-iOS-26 fallback (OS1), add an injection seam, such as the platform state passed in, with a test that `nil` gives `.notEligible`. |

## Surviving mutants and the test each needs

| Mutant | Severity | Finding | Test that should exist | Probe |
|---|---|---|---|---|
| **WF10, WF11, WF13** | **MAJOR** | **The correction path is unpinned.** The strips are gone, so the `Change` sheet is the only way to reach 7 of 9 surfaces. REQ-ASK-002 says *"a correction reaches every one of the nine surfaces"*, but the tests prove only the pure `surfaceChoices` list. The sheet can stop opening (WF10), the button can do nothing (WF13), and the sheet's buttons can stop selecting (WF11), and everything stays green. | Assert `Button(UIText.change(language)) { choosingSurface = true }`, `.sheet(isPresented: $choosingSurface) { surfaceSheet }`, and `Button { select(choice.id) }` inside the `ForEach(surfaceChoices(…))`. Also assert that `select()` sets `task = id` and loads. | `test_probe_change_opens_the_sheet` (WF10, WF13) and `test_probe_every_choice_and_alternative_selects_its_surface` (WF11): RED |
| **WF5, WF5b** | **MAJOR** | **The contract test's own message, *"the one-tap alternatives are never shown"*, names a defect it cannot see (V3C-86).** It asserts only that the substring `outcome.alternatives` appears, and the `if !outcome.alternatives.isEmpty` guard keeps that substring when nothing is rendered. This is the same claim-versus-behaviour shape as W2's W3 survivor. | Assert `ForEach(outcome.alternatives, …) { id in Button(surfaceTitle(id)) { select(id) } }`. | `test_probe_every_choice_and_alternative_selects_its_surface`: RED for both |
| **WF8, WF14** | **MAJOR** | **The echo is not proven rendered.** REQ-ASK-002's headline is that `"prove a theorem" → Mathematics` *renders with the reader's own words*. With `asked = typed` dropped (WF8), `echoLine` returns `nil` and the row falls back to `Showing: …`. With `Text(echo)` replaced (WF14), the echo is computed and never shown. Both stay green. | Assert that `Text(echo)` is the body of the `if let … echo = echoLine(question: asked, …)` branch, and that `asked = typed` is in `ask()`. | `test_probe_the_echo_is_rendered_from_the_question_asked`: RED for both |
| **WF12** | **MAJOR** | **The in-flight flag's release is unpinned.** Without `defer { routingInFlight = false }`, `canSubmit` is false forever after the first question, so the button stays disabled and Return is refused. REQ-ASK-001, "can be submitted", fails from the second question on. | Assert that `ask()` opens with `defer { routingInFlight = false }`. | `test_probe_the_in_flight_flag_is_always_released`: RED |
| WF9 | MINOR | After a correction, the router's echo and notice stay on screen. An unmeasured outcome's *"Below is the general chat ranking"* would sit above the Coding ranking the reader chose. | Assert `routing = nil` in `select()`. | `test_probe_a_correction_retires_the_routers_echo`: RED |
| WF3b | MINOR | A stale load's `defer` clears `reloading` while the current load is still running, so the spinner stops early. The code review's M3 found the same. | Assert `defer { if gate.isCurrent(ticket) { reloading = false } }`. | `test_probe_a_stale_load_cannot_clear_the_current_progress`: RED |
| WF17 | MINOR | The on-device help condition can be inverted without any test failing. The code review's M4 found the same. | Assert `if outcome.tier != .model, let help = onDevice.help(language)`. | `test_probe_on_device_help_is_shown_when_the_model_did_not_route`: RED |
| EL1a, EL1c | MINOR | The long-echo test bounds the length from one side only. A question of exactly 60 characters can gain an ellipsis (EL1a), and the cut can fall at 59 (EL1c). | Assert that a question of exactly `echoLimit` characters is quoted whole, and that one more character is cut to exactly `echoLimit` plus `…`. | `ProbeW3EchoBoundaryTests.testTheEchoCutsAtExactlyTheLimit`: RED for both |
| RN1t, RN2t | MINOR | The Turkish branches are checked only for differing from the English ones. Turkish manual can lose `Değiştir` (RN1t). A Turkish *measured* match can carry the unmeasured `söyleyemez` sentence (RN2t). The dangerous direction, an unmeasured Turkish notice reading as measured, *is* killed by `:150`. | Assert, in Turkish, what the English tests assert: manual contains `Değiştir`, unmeasured contains `söyleyemez` and not `Değiştir`, and neither measured tier contains `söyleyemez`. | `ProbeW3TurkishNoticeTests.testEachTurkishNoticeSaysWhatItsEnglishSays`: RED for both |
| SA6 | MINOR | The alternatives test checks count, distinctness, membership and "not the best". It never checks that they are the *next two closest*, so an insertion that keeps a wrong second and third stays green. The code review found the insertion correct as written. This is a missing pin, not a defect. | Order invariance. The best and its two alternatives cannot depend on the order the engine lists its surfaces in, so assert that all nine rotations of `known` give the same outcome for several questions. The stronger fix is to extract the top-3 insertion as a pure function and test it on fixed scores. | `ProbeW3AlternativesTests.testTheAlternativesDoNotDependOnTheOrderOfTheSurfaces`: RED |
| OS1 | MINOR | The fallback line is reachable only where FoundationModels is absent (iOS < 26), not on this macOS 26 host. | The injection seam named in B3. | none possible on this host |
| SA4 | none | Equivalent. `<` and `<=` differ only on an exact cosine tie, and each surface has one hint (`CategoryHints.byID`). The code review's S3 agrees. | none | n/a |

## Per-criterion citing-test check

**The citation form.** Every criterion is cited by a `// MARK: - REQ-ASK-00N` section header in `FrontDoorTests.swift`, and by the `# REQ-ASK-00N` comments in the contract test. None is cited by a per-test `covers` comment. That is acceptable, but coarser than the profile's form.

| REQ-ID | Citing tests, and whether they enter through the live entry point | Verdict |
|---|---|---|
| REQ-ASK-001 | **Logic:** `FrontDoorTests.swift:70`, `:74` and `:78` enter through `canSubmit`, which `ContentView` calls at `:215` and `:457`. **Wiring:** the contract test at `:528` kills WF1, WF2, WF7, WF15 and WF16. **Gaps:** the release of the in-flight flag (WF12, MAJOR) is unpinned. Focus and the keyboard have no test, and cannot have one: there is no UI test target, and the plan's named UI test does not exist (plan §7). | **Logic proven; submission after the first question unpinned; keyboard unverified.** This seat concurs with the code review's MAJOR-1. |
| REQ-ASK-002 | **Logic:** `echoLine` at `:88`, `:93`, `:98` and `:106`, and `surfaceChoices` at `:110` and `:125`, are the functions `ContentView` calls. The alternatives are tested through `SimilarityRouter.route` at `:204` and `:216`, which is the live tier. **Wiring:** the contract pins `echoLine(question: asked` and `surfaceChoices(categories`. **Gaps:** rendering and the correction path (the three MAJORs above), "next closest" (SA6), and the echo boundary. | **Partly proven.** The pure half is proven. The on-screen half is unpinned. |
| REQ-ASK-003 | `:139` and `:150` enter through `TieredRouter.route`, the live entry, but with stub tiers, so the question is inert. `:162`, the manual path, is valid, and the `RouterBoundaryTests.swift:59` inversion is valid. **On the shipping tier the criterion fails** (B1). | **FAIL** (B1) |
| REQ-ASK-004 | `:32`, `:48` and `:58` test `RequestGate` alone. The contract test pins the ticket, three guards and the categories gate, and kills WF3 and WF3c. **Gaps:** routing is not gated (B2); the guard's position relative to `state =` is unpinned (the code review's M1); the `defer` gate is unpinned (WF3b). | **FAIL** (B2) |

## Test integrity (V3C-86)

- **Deleted tests.** Seven were deleted: the six `BudgetOptionTests` (`OwnerSessionDefectTests.swift`) and `LanguageTests.testTheBudgetCapKeepsItsFigureInBothLanguages`. They went with the code they tested (`BudgetOption`, `capLabel`, `UIText.budget`, `EngineClient.budgets()`), under plan §2 W3, *"Remove both top strips"*. Those symbols no longer exist, so this is removal, not weakening to green. The prd row REQ-BGT-001 still cites them; this seat concurs with the code review's MAJOR-2.
- **Inverted assertion.** `RouterBoundaryTests.swift:59` is inverted. The quoted authority is verified at `HEAD`: `m13-plan.md:74` reads *"`tier = manual` may not carry `unmeasured = false`"*. The new assertion is the stronger one, and TR1 dies on it.
- **Claim versus behaviour.** Two instances, both listed above: B1, where the test names claim an image question and a speed question but the question text is inert, and WF5, where the contract message claims to catch an unrendered alternative.

## Notes

- **NIT-1: a failing assertion takes the whole run down.** `OnDeviceHelpTests` force-unwraps `english!` right after `XCTAssertNotNil(english)`, at `FrontDoorTests.swift:236-239`. Against OD1, the raw output shows `:236 XCTAssertNotNil failed`, then `:239: Fatal error: Unexpectedly found nil while unwrapping an Optional value`. The `xctest` process dies, `swift test` exits 1, and the remaining tests never run. OD1 is still killed. But a regression here would hide every later failure in that process. The fix is `let english = try XCTUnwrap(state.help(.english))`.
- **The records gate.** `scripts/check_records.py --root .`, run in the probe copy with this record in place, scanned 83 records. Its one finding (L1) is in this seat's private probe file, not in this record.
- **This seat did not re-litigate** the code review's MAJOR-2 and MINOR-1…8. Where a finding here overlaps one of them, the overlap is named.
