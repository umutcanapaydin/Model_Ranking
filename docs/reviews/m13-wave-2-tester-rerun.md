---
record_type: review
id: m13-wave-2-tester-rerun
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W2 — Tester seat, re-run against the post-fix tree (V3C-72)

**Reviewer:** the same independent Tester seat as `m13-wave-2-tester.md`. It authored none of the wave's code, and none of the post-fix changes.
**Subject:** `m13-w2-r2.diff`, the full W2 diff against `HEAD` 3440abe with `docs/reviews/` excluded: 1566 lines, 15 files. It applied cleanly to a fresh `git archive HEAD`.
**Policy source (V4C-06):** `subagent-profiles/Tester.md` and `AGENTS.md` at `HEAD`, as before. No policy was read from the diff.

**Provenance.** Everything ran in two private copies under the session scratchpad. The first was used for the trials and the second for the probes. Each was built with `git archive HEAD`, then `git apply`, then a read-only copy of the gitignored `advisor.db`. The repository was read-only apart from this one new file.

## Baseline at the post-fix tree

| What | Result |
|---|---|
| `pytest tests/unit` | 857 passed / 7 skipped |
| `pytest tests` (unit + integration) | **866 passed / 12 skipped**. This reconciles with the coordinator's "866": the figure is the whole `tests/` tree, not `tests/unit`. |
| `swift test` | **163 tests, 0 failures** |

## Verdict: PASS WITH FINDINGS

**Every survivor from the first run that was named as a finding is now killed:**
- S14, the `secondaryScore` guard
- both halves of the tolerance: RR2, the 0.1 step, and RR3, the 1e-9
- P3b, the unopenable artifact
- W1 and W2, the ContentView margin and age

**Six new survivors remain, and two of them are MAJOR.** The new ContentView contract test checks that each function NAME appears. It does not check the arguments passed or what is rendered, so five wiring mutants pass it:
- W7 reprints exact positions on the pick rows, which is the very defect REQ-UNC-001 exists to remove.
- W3 renders the raw basis, which the test's own docstring says it guards against.

The sixth survivor, ID4, is a MINOR hole in `isoDate`. For each survivor the seat wrote the missing test in a probe copy and watched it go RED against the mutant while passing on the post-fix code.

## Trial table

Each trial ran in one atomic sequence:
1. Record the pre-injection md5.
2. Apply one exact string replacement.
3. Run the suite. Swift mutants ran `swift test` and the Python unit suite. ContentView and server mutants ran Python only.
4. Revert in place.
5. Compare the md5.

A final md5 of all three mutated files (`Uncertainty.swift`, `main.py`, `ContentView.swift`) matched the pre-injection values.

### `ios/ModelRanking/Engine/Uncertainty.swift`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| RR1a | `rankRanges`: ahead `>` → `>=` (:78) | RED | **none: GREEN** (equivalent) | True |
| RR1b | `rankRanges`: behind `>` → `>=` (:80) | RED | **none: GREEN** (equivalent) | True |
| RR2 | the 0.1 served-resolution step dropped (:71) | RED | `testEachPositionIsTheRangeTheMarginCannotNarrow`, `testOneRoundingStepIsConcededInTheDirectionThatCannotOrderATie`, `testShortLabelsForTheRankingList`, `testTheLabelIsTurkishOnATurkishScreen` | True |
| RR3 | the 1e-9 float tolerance dropped (:71) | RED | `testOneRoundingStepIsConcededInTheDirectionThatCannotOrderATie` | True |
| RR4 | nil-margin fallback returns ranges, everything tied (:69) | RED | `testNoMarginMeansTodaysExactPositionsNotOneBigTie`, `testAMarginThatIsNotAUsableNumberIsTreatedAsNone` | True |
| RR5 | `ahead` counted from the lower side (`score - other`) | RED | 9 tests, including `testEachPositionIsTheRangeTheMarginCannotNarrow` and `testModelsClearlyApartKeepExactPositions` | True |
| RR5b | `ahead` counted with `<` instead of `>` | RED | 11 tests, including `testTwoModelsInsideTheMarginOfEachOtherAlwaysOverlap` | True |
| RR6 | `worst` ignores the models clearly behind (:84) | RED | 7 tests, including `testModelsClearlyApartKeepExactPositions` | True |
| L1 | a range is printed as its best, exact-looking position (:103) | RED | `testTheLabelSaysTheRangeOrTheExactPosition`, `testShortLabelsForTheRankingList`, `testTheLabelIsTurkishOnATurkishScreen` | True |
| LS1 | `leaderSentence` emitted when the leader stands alone (:120) | RED | `testNothingIsSaidWhenTheLeaderStandsAlone` | True |
| LS2 | `leaderSentence` counts exact first places, not ranges touching 1 (:119) | RED | `testHowManyTheBenchmarkCannotSeparateFromTheLeaderIsStatedOnce`, `testAMarginOfOneIsOnePointAndAnEloMarginIsCountedInElo`, `testTheSentenceIsTurkishOnATurkishScreen` | True |
| LS3 | the singular unit is never used (:121) | RED | `testAMarginOfOneIsOnePointAndAnEloMarginIsCountedInElo` | True |
| S14 | `evidenceBreadth`: `secondaryScore != nil` guard removed (:230) | RED | `testAPickTheSecondBoardNeverScoredIsNotToldItDid` | True |
| S8 | "High" maps to 1 (:208) | RED | `testTwoCurrentBenchmarksStateTheSecondOnesAge`, `testAPayloadThatContradictsItselfShowsNothingRatherThanRepeatingIt` | True |
| S9 | the secondary age is dropped (:233) | RED | `testASecondScoreFromAStaleBoardCarriesItsAge`, `testTheAgeSurvivesTheTurkishScreen`, `testTwoCurrentBenchmarksStateTheSecondOnesAge` | True |
| S10 | the `label()` guard is bypassed (:230) | RED | `testABenchmarkNameThatIsASentenceIsNotInterpolated` | True |
| S11 | a negative age is printed (:233) | RED | `testAnAgeThatCannotBeADayCountIsNotPrintedAsOne` | True |
| S12 | the "High"-without-a-second-score guard is removed (:212) | RED | `testAPayloadThatContradictsItselfShowsNothingRatherThanRepeatingIt` | True |
| EL1 | `evidenceLine`: a contradiction falls back to the basis (`?? basis`, :169-173) | RED | `testAPayloadThatContradictsItselfShowsNothingRatherThanRepeatingIt` | True |
| EL2 | `evidenceLine`: an unknown verdict shows nothing rather than the engine's basis (:175) | RED | `testAVerdictThisBuildDoesNotKnowShowsTheEnginesOwnBasis` | True |
| EL3 | `evidenceLine`: "High" routed to the raw basis (:168) | RED | `testAPayloadThatContradictsItselfShowsNothingRatherThanRepeatingIt` | True |
| ID1 | `isoDate`: the month range check dropped (:274) | RED | `testOnlyARealCalendarDayIsPrintedAsADate` | True |
| ID2 | `isoDate`: the day-in-month check dropped (:277) | RED | `testOnlyARealCalendarDayIsPrintedAsADate` | True |
| ID4 | `isoDate`: the ASCII-digit check dropped (:266) | RED | **none: GREEN** | True |

### Server: `src/app/adapter/main.py`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| P1 | `close_call_margin` serves `value_window` | RED | `test_every_advertised_surface_publishes_its_margin_on_its_own_scale`, `test_the_served_margin_reproduces_the_engines_own_close_call_decision[outside]` | True |
| P2a | undated board: age `0` instead of `null` | RED | `test_an_undated_second_board_publishes_no_age` | True |
| P3a | `_secondary_ages` re-raises from the query `except` (:1174) | RED | `test_discovery_answers_without_an_artifact_and_says_the_age_is_unknown[not-sqlite]` | True |
| P3b | `_secondary_ages` re-raises from the open `except` (:1165) | RED | `test_discovery_answers_when_the_artifact_exists_but_cannot_be_opened` | True |

### Wiring: `ios/ModelRanking/ContentView.swift`

| # | Mutant | Expected | Observed RED tests | revert-clean |
|---|---|---|---|---|
| W1 | `rankRanges(…, margin: nil)` (:152) | RED | `test_ios_client_contract.py::test_the_screen_calls_the_uncertainty_functions_it_depends_on` | True |
| W2 | `secondaryAgeDays: nil` passed to `PickRow` (:162) | RED | `test_the_screen_calls_the_uncertainty_functions_it_depends_on` | True |
| W3 | `Text(pick.confidenceBasis)` rendered in place of `Text(evidence)` (:673) | RED | **none: GREEN** | True |
| W4 | `leaderSentence(ranges: ranges, margin: nil, …)` (:169) | RED | **none: GREEN** | True |
| W5 | `secondaryBenchmark: nil` passed to `PickRow` (:161) | RED | **none: GREEN** | True |
| W6 | the leader note is not rendered in the full list (`Text(leaderNote)` → `EmptyView()`, :736) | RED | **none: GREEN** | True |
| W7 | `PickRow(…, ranges: nil, …)` (:160) | RED | **none: GREEN** | True |

## Kill rate

**27 of 35 killed (77%).** Excluding the two equivalent mutants (RR1a, RR1b): **27 of 33 (82%).** By file:

| File | Killed |
|---|---|
| `Uncertainty.swift` | 21 of 24 |
| `main.py` | 4 of 4 |
| `ContentView.swift` | 2 of 7 |

**Earlier survivors, re-checked:**

| Earlier survivor | Now | Killed by |
|---|---|---|
| S14 | Killed | `testAPickTheSecondBoardNeverScoredIsNotToldItDid` |
| S2, the tolerance | Killed as RR2 and as RR3 | `testOneRoundingStepIsConcededInTheDirectionThatCannotOrderATie`, as the coordinator predicted. `94.4 - 89.3` really is `5.1000000000000085`, so both halves are load-bearing. |
| P3b | Killed | `test_discovery_answers_when_the_artifact_exists_but_cannot_be_opened` |
| W1, W2 | Killed | the new contract test |
| W3, the evidence line | **Still survives in its new form** | nothing |

## Surviving mutants and the test each needs

| Mutant | Severity | Where | Finding | Test that should exist | Probe |
|---|---|---|---|---|---|
| **W7** | **MAJOR** | `ContentView.swift:160` | `PickRow` falls back to `rankRanges(…, margin: nil)`, which gives exact positions, whenever it is not handed the ranges. Dropping `ranges: ranges` reprints `#2 of 50` on the pick rows, in the largest type on the screen, for a model the engine calls tied with the leader. That is REQ-UNC-001's own defect. The contract test passes because `rankLabel(` still appears. | Assert that the `PickRow(…)` call carries `ranges: ranges`. | RED against W7 |
| **W3** | **MAJOR** | `ContentView.swift:673`; `test_ios_client_contract.py:441` | The new test's docstring names "a view that … went back to rendering the raw basis" as a change that broke nothing. The test still does not catch it: rendering `Text(pick.confidenceBasis)` leaves `evidenceLine(` present in the `evidenceText` property. A test that names a defect it cannot see is the claim-versus-behaviour mismatch V3C-86 asks this seat to find. | Assert `Text(evidence)` is rendered and that no `Text(pick.confidenceBasis)` exists outside comments. | RED against W3 |
| W4 | MINOR | `ContentView.swift:169` | `leaderSentence` given `margin: nil` returns `nil`, so the tie with the leader is never stated. Only the margin on `rankRanges` is pinned. | Assert the pattern `leaderSentence(ranges: ranges, margin: info?.closeCallMargin`. | RED against W4 |
| W5 | MINOR | `ContentView.swift:161` | The second board is not passed on, so the evidence line never names it. | Assert `secondaryBenchmark: info?.secondaryBenchmark` inside the `PickRow(…)` call. | RED against W5 |
| W6 | MINOR | `ContentView.swift:736` | The leader note is computed and never rendered. Presence of the `leaderSentence(` name does not prove display. | Assert `Text(leaderNote)` is rendered. | RED against W6 |
| ID4 | MINOR | `Uncertainty.swift:266` | Without the ASCII-digit check, `Int()` accepts a signed component. `isoDate("2026-+1-05")` returns the string, and the evidence line prints *"Measured on 1 benchmark (run 2026-+1-05)."* Reaching it needs a malformed payload. | `XCTAssertNil(isoDate("2026-+1-05"))`, or the same string through `evidenceBreadth` giving `"Measured on 1 benchmark."` | RED against ID4 |
| RR1a, RR1b | none | `Uncertainty.swift:78,80` | Equivalent. `>` and `>=` differ only at a gap of exactly `margin + 0.1 + 1e-9`, which one-decimal served scores (D-109) cannot produce. | none | n/a |

**About the probes.** The seat tested all five wiring pins in a probe copy. They are three Python tests that strip `//` comments, as the existing test does, and read the `PickRow(…)` call body with a one-level-nested-parentheses pattern. All three passed on the post-fix tree, and each of W3–W7 turned one of them RED. The ID4 probe passed on the post-fix tree and went RED against ID4. No probe was added to the repository.

## Notes

- **The M12 signature question from the first record is closed.** The coordinator reports that the owner answered "I sign it" (translated) to a direct question in session. This seat records that report; it did not witness the answer.
- **Test integrity (V3C-86) at the post-fix tree.** The rank-band tests were replaced along with the band design they tested, by the owner's ruling. The new tests are stronger, not weaker: `testTwoModelsInsideTheMarginOfEachOtherAlwaysOverlap` asserts the overlap as a property over every shipping margin, and it is among those RR5b kills. The one integrity finding is W3's docstring above.
