---
record_type: review
id: m18-wave-2-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 2 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records,
and it is not the wave's Code-Reviewer seat.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `d080060..4526384`, 14 commits, 55 files, +3547 / -169. `d080060` is the
merge-base; the range holds no merge.
1. Twelve commits are the plan (`1c72725`), P1 to P6, and the PRD re-pointing (`3ad7dc1`).
2. `b929a18` is the code review (PASS WITH FINDINGS, 8 MINOR, 3 K.9, 2 risks).
3. `4526384` is review round 1's fixes, made after the review. This seat is the only one that has
   tested it.

**Risk tier:** HIGH (`docs/plans/m18-wave-2-plan.md:13-15`; `m18-plan.md:54` says MED). The wave
touches `EngineClient.swift`, a security glob, and adds a Debug-only launch hook.
**Code-Reviewer verdict:** PASS WITH FINDINGS (`docs/reviews/m18-wave-2-review.md`, at `3ad7dc1`).
By D-172 there is no security seat on the wave. The fault injection below is the HIGH tier's owed one.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`, read from `d080060` with
  `git show`. It then read both plans, D-175 and D-176, the review, the issues it names and the diff.
  It has no memory of any authoring or reviewing session.

**Base-pinned policy:** `git diff --stat d080060 4526384 -- .claude .agents permission-matrix.md
.github` is empty. Nothing in the range asks anything of this seat.

## Verdict
PASS WITH FINDINGS

**Nothing blocks.**
1. Every acceptance check in the wave plan (P0 to P6) has a citing test that passes at `4526384`.
2. Every one of the review's fixes M1 to M8 and K1 to K3 is in the code, and each holds where the
   review pointed. The review's four surviving mutants (M1's whole read, M4's two view mutants, M5's
   launch environment) all die now. T5 and T7 are the links beside M3, M4 and M2 that are not held.
3. `make check-fast` and `make ui-test` pass at `4526384`. No touched module lost meaningful coverage.
4. The UI target is real: each of M17-W5's two simulator-found defects, re-introduced into
   `ContentView.swift`, turns its UI test red.

**Seven MINORs (T1 to T7).** Each is a fault that stayed green, and each comes with a test:
1. Each test is written into this worktree, uncommitted, and is green at `4526384`.
2. Each was shown red on its fault, in a scratch copy of `4526384`.
3. The author lands them in this wave, or files them.

The seven:
- **T1:** #56's error mapping mid-body is held by nothing. With the body read moved below the
  `catch`, a timeout after the first bytes escapes as a raw `URLError`, and the screen says the app
  needs an update.
- **T2:** D-176 clause 4's fallback is held for the close call only. The staleness, dating and
  effort notices, and the combined list's stale board, can each be dropped when their fact is missing.
- **T3:** D-135's weight on the combined list's stale board is held only for a dated board. An
  undated one said loudly passes.
- **T4:** three Turkish sentences are held only as not nil, or as distinct from each other. The
  English sentence in the Turkish branch passes.
- **T5:** the memo drops the surface's health, or the copy's age, on its way to the plan, and every
  test passes. Review M3's and M4's chain has a gap at its middle link.
- **T6:** `release_problems` unwired from `main()` passes every test and `make client-decls`. And
  `client_decl_gate.py` lost 0.7 points of coverage, the two lines that wire it.
- **T7:** the card notices composed in English on a Turkish screen, or with no anchor (D-143), pass
  every gate. So does an empty answer said as "no evidence" whatever its code, while the code is
  still read.

**What was run.**
- `make check-fast` at `4526384`: rc 0. `make ui-test` at `4526384`: rc 0, 8 tests with the
  engine up and 2 with it down.
- **89 faults were injected** in this worktree, each restored in place and checked (below): 11 in
  `EngineClient.swift`, 21 in `Notices.swift`, 10 in the engine, 18 in `AnswerPlan.swift`, 6 in
  `Combine.swift` and `StandingsStore.swift`, 4 in the Release gate, 3 in the project file, 9 in
  `ContentView.swift` against the text pins, 6 in `ContentView.swift` against `make ui-test`, and
  the review's M5 mutant in `LaunchRouting.swift`.
  1. 71 were killed and 3 are equivalent (N1, N2).
  2. 15 survived. They are the subject of T1 to T7.
- **Advisory kill rate: 71 of 86 non-equivalent faults, 82.6 %.** With the seven proposed tests in
  place, 86 of 86.

## Acceptance-criterion coverage (REQUIRED)

Every test named below is GREEN at `4526384`. Line numbers are at `4526384`. Fault ids are defined
under "Fault injection". The rows are the wave plan's checks (`m18-wave-2-plan.md:56-64`) and the
milestone's W2 criterion (`m18-plan.md:31`).

| criterion (phase, issue) | citing test (file:line) | entry | faults it kills | status |
|---|---|---|---|---|
| P0: the plan and D-175 committed | `docs/plans/m18-wave-2-plan.md`; D-175 `docs/decisions.md:3491`, D-176 `:3570` | records | n/a | MET |
| P1 #69: `make ui-test` drives ask, the combined list, a chip removed and restored, the detail, "Change" and the failure screen | `ScreenPathTests.swift:60`, `:68`, `:84`, `:97`, `:114`, `:128`, `:145`, `:157`; `FailureScreenTests.swift:21`, `:40` | real path: the app on the iPhone 17 Pro simulator against an engine on 127.0.0.1:8090 serving a copy of today's artifact | U1 to U6 | GREEN: 10 of 10 at `4526384`, run by this seat |
| P1: each of M17-W5's two simulator-found defects fails a test when re-introduced | `ScreenPathTests.swift:68` (the chip), `:84` (the row) | real path, as above | U1, U2; A18 (the chip, on the plan) | GREEN, and each red on its defect (below). R1 of the review is closed |
| P1 / D-175 cl. 3: scripted routing passes the model's boundary; Release builds carry no hook | `RouterBoundaryTests.swift:283`, `:291`, `:297`, `:303`; `test_client_decl_gate.py:85`; `make client-decls` | unit; the compiler gate on the Mac | G1, G2 (by the gate only), G4, M5R | GREEN. G3 survives: T6 |
| P1: the text gate's one-folder rule reads every target | `test_router_hints.py:383` (rule at `:586`) | a scan of `project.pbxproj` | R1, R2, R3 | GREEN |
| P2 #63: each of the 14 findings reproduced, standing or gone | `ScreenAuditTests.swift` (captures, no assertions); the table on #63 (2026-10-04) | records | n/a | MET (read) |
| P3 #63 finding 1: one card per model | `AnswerPlanTests.swift:339`, `:352`, `:365`, `:373` | unit: `pickCards`, `PickCard.reasons` | A11, A12, A13 | GREEN |
| P3 #63 finding 2 / D-176: notices composed from facts in both languages, English where a fact is missing | `NoticesTests.swift:29` to `:266`; `test_why_facts.py:135`, `:153`; `test_recommend.py:339` | unit; real path for the engine half (`/v1` on today's artifact) | N4 to N7, N9, N11 to N17, P1 to P4, P10 | GREEN. N1, N2, N3, N10: T2. N8: T3. N18 to N20: T4. View wiring: T7 |
| P3 #63 findings 5 to 9, 11 to 14, A | `LanguageTests.swift:546` to `:638`; `DetailTests.swift:190`, `:228`; `AnswerPlanTests.swift:383`; `test_ios_client_contract.py:165`, `:178` | unit | A17, V9 | GREEN |
| P3 #95: the local-network prompt in Turkish | `test_engine_address.py:89` | a file check | n/a | GREEN. A device shows it, not the simulator: the review's R2 stands |
| P3 #96: the failure screen in both languages | `LanguageTests.swift:514`, `:525`; `FailureScreenTests.swift:40` | unit; real path | U5 | GREEN |
| P4 #67, #72: the combined list's disclosures as fields of its plan, a stale board and a stale phone copy included | `AnswerPlanTests.swift:165`, `:182`, `:199`, `:212`, `:227`; `StandingsStoreTests.swift:131`; `test_ios_client_contract.py:124`; `ScreenPathTests.swift:97` | unit on the plan; a text pin on the view; real path | A1 to A6, A16, S1, S2, V1 to V5, U4 | GREEN. The memo's forwarding: T5 |
| P5 #70: the plan computed when its inputs change | `AnswerPlanTests.swift:247`, `:254`; `test_ios_client_contract.py:124` (no `answerPlan(` in the view, the stamp bumped) | unit; text pin | A9, A10, V5 | GREEN |
| P5 #74: `combine` passes the oracle and is O(n log n) | `CombinePropertyTests.swift:79`, `:72`, `:113`; `:140` (20,000 models under 5 s) | unit; property oracle | C1, C2, C3 | GREEN. C4 is equivalent: N2. Red on the old code (below) |
| P5 #56: a response is cut off at its route's ceiling while it streams | `EngineClientTests.swift:623`, `:643`, `:683`, `:693`, `:703`, `:710`; `test_ios_client_contract.py:580`, `:593` | real `URLSession` over stub protocols | E1, E2, E3, E6, E7, E8, E10, V10 | GREEN. E4, E5 are equivalent: N1. Mid-body errors: T1 |
| P6 #78: a reader filter, held by a UI test; recorded in D-175 | `AnswerPlanTests.swift:399`, `:410`; `ScreenPathTests.swift:114`; `decisions.md:3563` | unit; real path | A14, A15 | GREEN |
| Review M2 / D-176 cl. 7: three empty reasons by code | `test_empty_answer_reasons.py:200`, `:219`; `NoticesTests.swift:114`, `:125`, `:135` | engine real path; unit | P5 to P9, N5, N6, N7 | GREEN. Red on the pre-fix engine (below) |
| W2 milestone criterion: #63 reproduced and ruled; a committed UI test drives the screen | the rows above | | | MET |
| REQ-APP-002, Ruling A on screen (restated, #68) | `ScreenPathTests.swift:145`; `test_ios_client_contract.py:379` | real path; text gate | U3 | GREEN. The PRD keeps it PARTIAL (no ADR for the selected-surface-first order), and I agree |
| REQ-APP-003, every disclosure visible | the P4, D-176 and review M2 rows | | | GREEN, with T2, T3, T5 and T7 |
| REQ-APP-005, no ranking value of the client's own | `test_ios_client_contract.py:379` (`("Combine.swift", "placed")` permitted for #74), `:274`, `:301` | text gate | C1 to C3 hold the sort itself | GREEN. PRD PARTIAL, unchanged by the wave |
| REQ-ASK-002, shown and corrected in one tap | `ScreenPathTests.swift:128` | real path | U6 | GREEN. PRD PARTIAL (two taps on the model tier), unchanged |

**The PRD's evidence pointers.** The PRD lines this range adds or changes carry 119 `file:line`
citations. I resolved each at `4526384`. 118 land on a test or definition line. The other is
`ContentView.swift:74`, a deliberate pointer to the `unlimited` budget. REQ-API-001's `:516` and `:525`
(review M8) are the two tests they name.

## Red→green on reported symptoms

No commit in the range is a red-only commit: each phase carries its test and its fix together. So
this seat ran each load-bearing test against the code before its fix.

| symptom | red: the test on the pre-fix code | green: at `4526384` |
|---|---|---|
| #74, a payload at the cap froze the screen | `Combine.swift` from `d080060` under `4526384`'s tests: `testALargeListCombinesWithoutFreezing` FAILS, "combine took 72.8 s for 20000 shared models"; the three oracle tests pass on it (same ranks) | 0.198 s |
| Review M2, "could not be read" said as an evidence gap | `b929a18`'s engine with `4526384`'s `test_empty_answer_reasons.py`: 2 of 5 FAIL (the two code tests) | 5 of 5 |
| Review M1, a whole read passed every test | E1, the review's own mutant: 2 tests fail (`EngineClientTests.swift:623`, `:643`). At review it passed 17 | pass |
| Review M4, a nil health and a branch-wrapped list passed the pins | V1 and V2, the review's own mutants: `test_ios_client_contract.py:124` fails on each. U4: the branch mutant also fails `ScreenPathTests.swift:97` | pass |
| Review M5, a Release launch-environment read passed the gate | M5R, the review's own mutant: `make client-decls` FAILS in both Release configurations (`ProcessInfo.environment` ... compiled into a Release build). G1 (the environment off the list): `test_client_decl_gate.py:85` fails | pass |
| Review M7, "Change" asserted no choice | U6, a choice that chooses nothing: `ScreenPathTests.swift:128` FAILS, "Showing: Coding" is equal to "Showing: Coding" | pass |
| M17-W5 defect 1, a removed chip vanished | U1 (the screen): `ScreenPathTests.swift:68` FAILS, "the removed chip vanished"; A18 (the plan): `AnswerPlanTests.swift:78`, `:85` fail | pass |
| M17-W5 defect 2, the boards row took no tap | U2 (`.contentShape` removed): `ScreenPathTests.swift:84` FAILS, "a tap in the row's empty middle did not open the boards" | pass |
| Review K1, the ordering note under every surface | U3 (`ordered.count > 1` removed): `ScreenPathTests.swift:145` FAILS, "a one-answer surface says its order means nothing" | pass |
| #96, English sentences under a Turkish title | U5 (the English `errorDescription`): `FailureScreenTests.swift:40` FAILS, "the failure's sentence is not Turkish" | pass |

**Weakened or deleted tests.** I read every line the range removes under `tests/`,
`ios/EngineTests/` and `ios/UITests/`.
1. The Swift lines removed change an expected string to the wave's new wording: "Score 65.0 / 100"
   to "65.0 / 100", dates in words, "Run at" to "Evaluation tool" and "Effort level", effort names
   in Turkish, and the page count grouped per language. Each has its replacement assertion beside
   it.
2. `SOURCE_HEALTH_KEYS` gains `reason`, and `test_ios_visual_contract.py`'s `Text(whyText)` becomes
   the `ForEach(whyTexts` pattern a merged card renders. Both are stricter.
3. `testTheTurkishPriceStillCarriesTheSameNumberAsTheEnglish` now normalises the grouped page count
   before comparing digits. It still compares every amount.
4. The redirect pin moves from `data(from:delegate:)` to `session.bytes(from:delegate: SameHostOnly(`,
   which is stricter (it names the delegate). E10 shows it still fails.
5. The one-folder rule is rewritten to read every target. R1 to R3 show it fails on each defect.

No test was skipped, deleted or weakened.

## Suite result
- **`make check-fast` at `4526384`: PASS, rc 0, in 54 s.** This seat's guard was first on PATH,
  and `PYTHONPATH` pointed at this worktree's `src`.
  1. lint, typecheck and records: PASS.
  2. test: **1660 passed, 25 skipped**. `coverage-floor`: PASS, 42 modules.
  3. client-decls: PASS, 18 files in 4 configurations (Release 2237 declarations, Debug 2242).
  4. swift-test (parallel): PASS, **423 tests**, exactly the manifest.
- **`make ui-test` at `4526384`: PASS, rc 0.** With the engine up: 8 of 8. With it down: 2 of 2.
  The engine ran from this worktree's `src` on 127.0.0.1:8090, from a copy of the artifact
  (sha256 `5c6977a9c67c…`, unchanged after).
- **With this seat's tests added** (below): `make check-fast` PASS, rc 0: 1662 passed, 25 skipped;
  428 Swift tests, exactly the manifest.
- **Coverage on touched code** (permission-matrix §11). Python: `pytest -n 4 --cov=src/app
  --cov=scripts --cov-branch` on `git archive` copies of `d080060` and `4526384`, each with the same
  artifact (1642 and 1660 passed). Swift: `swift test --enable-code-coverage` on the same copies
  (367 and 423 tests), read with `llvm-cov report`.

| module | base `d080060` | head `4526384` | change |
|---|---|---|---|
| `src/app/adapter/main.py` | 98.04 % | 98.04 % | 0 |
| `src/app/workflows/recommend.py` | 95.42 % | 95.47 % | +0.05 |
| `scripts/client_decl_gate.py` | 63.77 % | 63.08 % | -0.69: T6. 78.50 % with T6's test |
| `EngineClient.swift` (lines) | 91.12 % | 91.96 % | +0.84 |
| `Combine.swift` | 91.89 % | 93.48 % | +1.59 |
| `StandingsStore.swift` | 80.43 % | 83.93 % | +3.50 |
| `AnswerPlan.swift` | 98.70 % | 97.40 % | -1.30, see below |
| `Language.swift` | 79.58 % | 82.48 % | +2.90 |
| `Notices.swift` (new) | n/a | 95.24 % | |
| `ScriptedRouting.swift` (new) | n/a | 100 % | |

`AnswerPlan.swift`'s three unexecuted new lines are two stored-property defaults
(`staleness`, `phoneCopyDays`) and `PickCard.id`, which only SwiftUI's `ForEach` reads. No behaviour
is unexecuted there. `ContentView.swift`, `LaunchRouting.swift` and the UI target are outside the
Swift package, so no coverage figure exists for them; the UI run is their evidence.

## Mocks / contract tests
- **`StubProtocol`** (`EngineClientTests.swift:203`) stays the canonical stub. **`ChunkedStub`**
  (`:553`) is a second `URLProtocol`, and it earns its place: `StubProtocol` hands the body over in
  one piece with no headers, so it cannot show a read that stops early or a declared length. I do
  not count it as a parallel mock. T1's stub is a third, for the one case neither can make: a
  transfer that fails after its response.
- **The engine contract.** `close_call_fact`, `unavailable_reason_code` and `source_health.reason`
  are held on the real `/v1` path (`test_why_facts.py:135` over nine surfaces on today's artifact,
  `test_empty_answer_reasons.py:200`, `:219`), and the Swift decoders read the same keys
  (`NoticesTests.swift:135`). Both sides spell the codes as literals; a renamed code would fail one
  side's test (P5, P6 and N7 show each side).
- **No new external integration.**

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T1** `ios/ModelRanking/Engine/EngineClient.swift:274-282`; `ios/EngineTests/EngineClientTests.swift`. **#56 moved the body read inside the request's `do`, so a transfer that fails after its first bytes is still mapped. Nothing holds that.**
   1. The review read it as a gain ("it now also covers an error thrown mid-stream, because `read`
      runs inside the same `do`"). Fault E9 moves the read below the `catch` chain. Every Swift and
      Python test passed, and so did the pins: the read still goes through the ceiling.
   2. Under E9, a timeout or a lost connection mid-body reaches `load()` as a plain `URLError`, and
      `load()` turns it into `undecodable`. The screen then says "This version of the app could not
      read the answer it was sent. Updating the app is the fix." That is the wrong advice, the M8
      plan's Trap 2.
   3. Why nothing caught it: every stub fails before it answers, or answers whole. A stub that sends
      its failure at once also misses it. `URLSession` holds an untyped response back to sniff its
      first 512 bytes, so the failure is thrown by `bytes(from:)` itself. This seat's first test
      passed under E9 for that reason.
   4. **The fix:** `MidStreamFailureTests`, below. Its stub answers 200 with a JSON content type and
      2 KiB of body, then fails 0.2 s later from its own queue. It asserts a timeout is `.timedOut`
      and a lost connection is `.offline`. It kills E9, 5 runs of 5.
- **T2** `ios/ModelRanking/Engine/Notices.swift:218-226`, `:249`; `docs/prd.md:480`. **D-176 clause 4 ("a missing fact, an unknown kind ... shows the engine's English. Nothing is dropped") is held for the close call only.**
   1. Faults N1, N2 and N3 turn the staleness, dating and effort fallbacks into drops
      (`map { compose ?? $0 }` to `flatMap { _ in compose }`). N10 does the same to the combined
      list's stale board. Each passed every test.
   2. Only N4, the close call's, is killed (`NoticesTests.swift:266`).
   3. Each fallback is reachable: an engine older than D-176 clause 7 sends an empty `source_health`
      with no `reason`; a dating kind this build does not know; an effort notice over picks that
      name fewer than two levels.
   4. REQ-LOC-001 is marked MET with "Where a fact is missing the engine's English is shown"
      (`prd.md:480`), and D-135 forbids a cut.
   5. **The fix:** `testEveryNoticeWithoutAComposableFactIsTheEnginesEnglish` and the last assertion
      of `testTheCombinedListWeighsAndFallsBackAsTheCardsDo`, below. They kill N1, N2, N3 and N10.
- **T3** `ios/ModelRanking/Engine/Notices.swift:250-251`. **D-135's weight for the combined list's stale board is held only for a dated board.**
   1. `combinedDisclosure` says a stale board none of whose sources carries a date as a property
      (quiet), as `classifyDisclosures` does on the cards. Fault N8 makes it always loud. Every test
      passed: `AnswerPlanTests.swift:182` checks only a dated board.
   2. That is the permanent warning on a board that publishes no dates, which D-135 exists to stop,
      moved to the combined list.
   3. **The fix:** the first two assertions of `testTheCombinedListWeighsAndFallsBackAsTheCardsDo`.
      They kill N8.
- **T4** `ios/ModelRanking/Engine/Notices.swift:106-108`, `:165-167`, `:45-46`. **Three Turkish sentences are held only as not nil, or as distinct from each other.**
   1. Fault N18 puts the English mixed-dating note in the Turkish branch. N19 does it to the
      over-budget reason, N20 to the unreadable health. Each passed every test.
   2. The tests that cover them: `NoticesTests.swift:86` (`XCTAssertNotNil` on the mixed note),
      `:114` (three distinct sentences per language, which English ones are), `:129` (not nil).
   3. This is #63 finding 2, English on the Turkish screen, held by tests that cannot see it.
   4. **The fix:** `testEveryComposedNoticeDiffersFromItsEnglish`, below. It walks every composer
      and asserts the Turkish differs from the English. It kills N18, N19 and N20.
- **T5** `ios/ModelRanking/Engine/AnswerPlan.swift:224-226`. **The memo can drop the surface's health or the copy's age on the way to the plan, and every test passes.**
   1. Review M3 and M4 built a chain: the view hands `routedSurfaceHealth(...)` and
      `staleCopyDays(...)` to `PlanMemo.Inputs` (pinned by `test_ios_client_contract.py:124`), and
      `answerPlan` turns them into disclosures (`AnswerPlanTests.swift:182`, `:199`).
   2. The middle link is not held. Fault A7 passes `phoneCopyDays: nil` from the memo to the plan,
      A8 `primaryHealth: nil`. Each passed every test, because the memo's tests
      (`AnswerPlanTests.swift:247`, `:254`) give it neither.
   3. Under either, the screen never says a stale board or an old phone copy: #72, both halves.
   4. **The fix:** `testTheMemoHandsThePlanTheHealthAndTheCopysAge`, below. It kills A7 and A8.
- **T6** `scripts/client_decl_gate.py:394-395`; `tests/unit/test_client_decl_gate.py`. **D-175 clause 3's "a test holds that" holds `release_problems`, not that `make client-decls` runs it.**
   1. Fault G3 deletes the two lines in `main()` that apply it to the Release configurations. All
      Python tests passed, and so did `client_decl_gate.py` itself (rc 0): today's app has no hook
      in Release, so nothing is there to refuse.
   2. Fault G2 applies it to Debug instead. Only the real gate on a Mac catches that; CI cannot.
   3. This is the shape of the W5 Tester's T3 (`self_test` unwired from `main()`).
   4. Coverage: those two lines are why `client_decl_gate.py` fell from 63.77 % to 63.08 %.
   5. **The fix:** `test_main_refuses_a_release_dump_that_carries_a_ui_test_hook`, below. Canned
      dumps stand in for the compiler, so it runs on CI. A hook in the Release dumps makes `main()`
      return 1, and the same hook in the Debug dumps returns 0. It kills G2 and G3, and takes the
      file to 78.50 %.
- **T7** `ios/ModelRanking/ContentView.swift:725-727`, `:748`. **The view's calls into D-176's composers are held by nothing: review M4's class, on the cards.**
   1. Fault V7 composes the card notices in `.english` whatever the reader chose. V8 passes
      `anchor: nil`, so an anchored Elo gap is said in Elo under rows that say "59.6 / 100" (D-143).
      Each passed every Python test and `make client-decls`.
   2. Fault V6b says every empty answer as "no evidence" while still reading the code
      (`answer.unavailableReasonCode.map { _ in "no_evidence" }`). That is review M2 again, at the
      view. It passed every gate. (V6, which drops the code outright, is killed, but only by the
      optional-field rule at `test_ios_client_contract.py:60`.)
   3. No UI test reaches a Turkish notice, an anchored close call or an empty answer.
   4. **The fix:** `test_the_screen_composes_the_empty_reason_and_the_notices_from_their_facts`,
      below, pinned by value as the review's M4 fix pinned `primaryHealth`. It kills V6b, V7 and V8.

## Notes (no change required by this verdict)

- **N1** **Equivalent on this platform: E4 and E5**, the two `bytes.task.cancel()` calls in
  `EngineClient.read`.
   1. When `read` throws, the `URLSession.AsyncBytes` it holds is released, and the release cancels
      the task. The explicit cancels are belt and braces.
   2. Evidence for E4: under it, `EngineClientTests.swift:623` still saw the stub stopped before its
      32nd of 64 chunks.
   3. Evidence for E5: a probe in a scratch copy, a declared 10 MiB over 64 chunks. Under E5 the stub
      sent 1 chunk and was stopped, the same as at `4526384`. The probe was deleted.
- **N2** **Equivalent: C4** (`countBelow` never examines the last position). Every position searched
  is itself in the sorted list, so a lower bound never needs the index past the last element, and
  never returns it. The oracle (`CombinePropertyTests.swift:79`) agrees.
- **N3** **The review's fixes, each checked.**
   1. M1: E1 is the review's mutant, now killed by two tests. E2 and E3 die too.
   2. M2: P5 to P9 and N5 to N7 die. The engine's three reasons travel as codes (D-176 clause 7).
      The view's half is T7.
   3. M3: A3, A4, A6, S1 and S2 die. The memo's half is T5.
   4. M4: V1 and V2, the review's mutants, die on the pin. U4 shows the branch mutant red on screen.
   5. M5: G1 and M5R die. The wiring is T6.
   6. M6: `git check-ignore -v ios/Config/UITests.local.xcconfig` names `.gitignore:73`, and
      `test_engine_address.py:21` holds it.
   7. M7: the "Change" test picks `surface.vision` and asserts the shown surface changed; U6 is red.
   8. M8: REQ-API-001's `:516` and `:525` are the two tests. REQ-LOC-001 is cited at
      `NoticesTests.swift:8` and `test_why_facts.py:136`.
   9. K1, K2, K3: U3 is red without K1. `LanguageTests.swift:638` names every effort the engine
      serves. `ScreenPathTests.swift:145` drives coding's two answers.
- **N4** **`staleCopyDays` says the copy's whole age, and its doc says "past the day".**
  `StandingsStore.swift:106` documents "whole days the served copy has been kept past the day it is
  meant to last", and `AnswerPlan.swift:26` "whole days ... past its day". It returns the whole age:
  3 for a copy fetched 3 days and a minute ago (`StandingsStoreTests.swift:131`). The sentence on
  screen says "reached this phone 3 days ago", which is what is returned, so the reader is told the
  truth. Only the two comments overstate.
- **N5** **This seat's own false kills, discarded.** The first run's engine check ran five test
  files in one process, and that set fails at `4526384` itself: 5 tests of `test_api_config.py`
  fail after `test_empty_answer_reasons.py`. I re-ran P1 to P10 with `test_api_config.py` on its
  own; every one is killed by an engine test (`test_why_facts.py:135`, `test_recommend.py:339`,
  `test_empty_answer_reasons.py:200`, `:219`, `test_api_v1.py`). The order dependence is K1.
- **N6** **Not done by this seat, by its rules.** No installer, `launchctl`, `sudo`, commit or push.
  #95's prompt was not seen on a device: the review's R2 stands. `ScreenAuditTests` was not run;
  it asserts nothing.

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_api_config.py`; `tests/unit/test_empty_answer_reasons.py`. **Five config tests fail when they run after `test_empty_answer_reasons.py` in one process, at `d080060` as at `4526384`.**
   1. Reproduce: `pytest -p no:cacheprovider --no-cov tests/unit/test_empty_answer_reasons.py
      tests/unit/test_api_config.py` gives 5 failed, 26 passed at `4526384` (5 failed, 24 passed at
      `d080060`). Each file alone passes.
   2. The failures include `test_production_refuses_to_boot_without_its_evidence_database` and
      `test_a_malformed_origin_is_refused`: state from the first file's app leaks into the second.
   3. `make test` (`-n auto`) and CI (serial, collection order) both run `test_api_config.py` first,
      so neither sees it today. A reordering, or a new test file between the two, would.
   4. This is a test-isolation defect, pre-existing. File it.

## Risks queued to next M
- none beyond the review's R2 (#95 on a device), which stands.

## Fault injection (HIGH: mandatory)

**Harness:** scratch `w2t/mut.py`, with the faults in `w2t/faults.py`, `rerun_p.py`, `extra_faults.py`
and `ui_faults.py`. For each fault it does the following:
1. It checks every file it touches against `HEAD`: `git hash-object` must equal
   `git rev-parse HEAD:<file>`, and `git status --porcelain --untracked-files=no` must be empty.
2. It records each file's sha256 and saves its bytes.
3. It makes exact string edits, each required to match exactly once. All were dry-run first, for
   the match count and, on Python files, for syntax.
4. It runs the targeted checks: `swift test --filter` for the classes the fault touches, the Python
   test files that pin it, `client_decl_gate.py`, or `UI_TEST_ONLY=Class/test make ui-test` (each
   with its engine started from this worktree's `src`). If nothing fails, it runs the whole Swift
   suite (`swift test --parallel`) and the whole Python suite (`-n auto`, with
   `MODEL_RANKING_REQUIRE_ARTIFACT=1`), and `make client-decls` for a gate or view fault.
5. It writes the original bytes back **in place**, never with `git checkout` or `restore`.
6. It asserts three things: sha256 equals the pre-edit hash, `git hash-object` equals HEAD's blob,
   and the tracked tree is clean.

Every one of the 99 runs (89 faults, and P1 to P10 run twice, N5) says `restored: true` and
`git_clean: true`. After the last run, all 695 tracked files matched the sha256 baseline taken
before the first fault (`shasum -c`: 695 OK), and the artifact's sha256 was unchanged
(`5c6977a9c67c…`). Every kill is a test assertion or a gate's refusal; none is a compile error or a
build failure (each log was read for the failing assertion).

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob that `git hash-object` matched):

| file | faults | sha256 (pre = post) | HEAD blob |
|---|---|---|---|
| `ios/ModelRanking/Engine/EngineClient.swift` | 11 (E1–E10, V10) | `d07fbe7bb673` | `7f85c7ef3b` |
| `ios/ModelRanking/Engine/Notices.swift` | 21 (N1–N20, V9) | `a91ce97b6eb8` | `faeeb9a867` |
| `src/app/workflows/recommend.py` | 4 (P1–P4) | `f61c0b6672bd` | `251b9b9532` |
| `src/app/adapter/main.py` | 6 (P5–P10) | `6fc1349ab67c` | `9b1f3b3839` |
| `ios/ModelRanking/Engine/AnswerPlan.swift` | 18 (A1–A18) | `3f926f850f01` | `797cff32dd` |
| `ios/ModelRanking/Engine/Combine.swift` | 4 (C1–C4) | `205435bd98ee` | `1934a6970a` |
| `ios/ModelRanking/Engine/StandingsStore.swift` | 2 (S1, S2) | `89e06edaf212` | `6add128f1a` |
| `scripts/client_decl_gate.py` | 4 (G1–G4) | `865d86bca0b7` | `936eaccf79` |
| `ios/ModelRanking/LaunchRouting.swift` | 1 (M5R) | `044ed88e61b3` | `3083a04259` |
| `ios/ModelRanking.xcodeproj/project.pbxproj` | 3 (R1–R3) | `50175c2820e4` | `56947fe912` |
| `ios/ModelRanking/ContentView.swift` | 15 (V1–V8, V6b, U1–U6) | `313f2a3b735c` | `21ea3f4491` |

**The faults.** "Every Swift and Python test" means the 423 Swift tests and 1660 Python tests at
`4526384`. The line cited is each killing test's `func` or `def` line at `4526384`.

| id | the fault | result | killed by |
|---|---|---|---|
| E1 | review M1 replay: whole read, size checked after, declared-length guard deleted | KILLED | `EngineClientTests.swift:623`, `EngineClientTests.swift:643` |
| E2 | declared-length guard removed | KILLED | `EngineClientTests.swift:643` |
| E3 | off by one: reads ceiling + 1 bytes | KILLED | `EngineClientTests.swift:693`, `EngineClientTests.swift:710` |
| E4 | the transfer is not cancelled at the ceiling (throw without cancel) | SURVIVED, equivalent | N1 |
| E5 | a declared length over the ceiling refused without cancelling the task | SURVIVED, equivalent | N1 |
| E6 | every route read to the boards' 4 MiB ceiling | KILLED | `EngineClientTests.swift:623`, `EngineClientTests.swift:693`, `EngineClientTests.swift:710` |
| E7 | an unsized route gets the 4 MiB ceiling, not the smallest | KILLED | `EngineClientTests.swift:623`, `EngineClientTests.swift:683`, `EngineClientTests.swift:693` (+1) |
| E8 | the EngineError rethrow removed (a ceiling refusal flattened to unreachable) | KILLED | `EngineClientTests.swift:537`, `EngineClientTests.swift:623`, `EngineClientTests.swift:643` (+2) |
| E9 | the body read outside the do: a URLError thrown mid-stream is not mapped | SURVIVED (every Swift and Python test) | T1 |
| E10 | the redirect delegate not passed to the streamed request | KILLED | `test_ios_client_contract.py:593` |
| N1 | staleness: the engine's English dropped when no sentence can be composed | SURVIVED (every Swift and Python test) | T2 |
| N2 | dating: the engine's English dropped for a kind this build does not know | SURVIVED (every Swift and Python test) | T2 |
| N3 | effort mix: the engine's English dropped when fewer than two efforts compose | SURVIVED (every Swift and Python test) | T2 |
| N4 | close call: the engine's English dropped without a fact | KILLED | `NoticesTests.swift:266` |
| N5 | a no-source health with no reason said as no source (the pre-M2 rule) | KILLED | `NoticesTests.swift:125` |
| N6 | an unreadable health said as no source | KILLED | `NoticesTests.swift:125`, `NoticesTests.swift:135` |
| N7 | review M2 at the composer: 'unreadable' said as no evidence | KILLED | `NoticesTests.swift:114`, `NoticesTests.swift:135` |
| N8 | D-135: a stale board whose sources carry no date said loudly on the combined list | SURVIVED (every Swift and Python test) | T3 |
| N9 | D-135: a stale phone copy said quietly | KILLED | `AnswerPlanTests.swift:199` |
| N10 | combined list: a stale board with no composable sentence dropped, not said in English | SURVIVED (every Swift and Python test) | T2 |
| N11 | close call names a model the ranking does not list | KILLED | `NoticesTests.swift:186` |
| N12 | D-143: an anchored Elo gap said in Elo | KILLED | `NoticesTests.swift:175` |
| N13 | the stalest age said as the newest | KILLED | `NoticesTests.swift:29` |
| N14 | a future-dated source counted as aged | KILLED | `NoticesTests.swift:52` |
| N15 | D-135 classification fed no ages (every staleness quiet) | KILLED | `NoticesTests.swift:243` |
| N16 | one effort level said as a mix | KILLED | `NoticesTests.swift:92` |
| N17 | D-176 cl. 5: the stale clause names the source ids | KILLED | `NoticesTests.swift:43`, `:195` |
| N18 | the Turkish mixed-dating note left in English | SURVIVED (every Swift and Python test) | T4 |
| N19 | the Turkish over-budget reason left in English | SURVIVED (every Swift and Python test) | T4 |
| N20 | the Turkish unreadable-health notice left in English | SURVIVED (every Swift and Python test) | T4 |
| P1 | close_call_fact never set | KILLED | `test_recommend.py:339`, `test_why_facts.py:135` |
| P2 | close_call_fact quotes the raw gap, not the shown one | KILLED | `test_recommend.py:339`, `test_why_facts.py:135` |
| P3 | close_call_fact names the leader | KILLED | `test_recommend.py:339`, `test_why_facts.py:135` |
| P4 | close_call_fact unit dropped to points | KILLED | `test_why_facts.py:135` |
| P5 | over-budget answer coded no_evidence | KILLED | `test_empty_answer_reasons.py:200` |
| P6 | no-evidence answer coded over_budget | KILLED | `test_empty_answer_reasons.py:200` |
| P7 | the read-failure answer carries no code | KILLED | `test_empty_answer_reasons.py:219` |
| P8 | the read-failure health says no_source | KILLED | `test_empty_answer_reasons.py:219` |
| P9 | the no-source health carries no reason | KILLED | `test_empty_answer_reasons.py:200` |
| P10 | close_call_fact not a public answer field | KILLED | `test_api_v1.py:206`, `test_why_facts.py:135` |
| A1 | the stale board dropped from the combined list's disclosures (review replay) | KILLED | `AnswerPlanTests.swift:165`, `AnswerPlanTests.swift:182` |
| A2 | a fresh board said as stale | KILLED | `AnswerPlanTests.swift:182` |
| A3 | the stale phone copy dropped | KILLED | `AnswerPlanTests.swift:199` |
| A4 | the stale phone copy said after the quiet ones | KILLED | `AnswerPlanTests.swift:199` |
| A5 | tied places never said | KILLED | `AnswerPlanTests.swift:165` |
| A6 | answerPlan drops the phone copy's age | KILLED | `AnswerPlanTests.swift:199` |
| A7 | the memo drops the phone copy's age on its way to the plan | SURVIVED (every Swift and Python test) | T5 |
| A8 | the memo drops the surface's health on its way to the plan | SURVIVED (every Swift and Python test) | T5 |
| A9 | the memo never re-plans | KILLED | `AnswerPlanTests.swift:254` |
| A10 | the memo re-plans only when the question changes | KILLED | `AnswerPlanTests.swift:254` |
| A11 | #102: one card per name, whatever the row | KILLED | `AnswerPlanTests.swift:373` |
| A12 | the value-window reason kept on the best's card (review replay) | KILLED | `AnswerPlanTests.swift:339` |
| A13 | a floor warning merged away on the best's card | KILLED | `AnswerPlanTests.swift:339`, `AnswerPlanTests.swift:365` |
| A14 | #78: an unpublished access claimed | KILLED | `AnswerPlanTests.swift:399`, `AnswerPlanTests.swift:410` |
| A15 | #78: the filter applied when off | KILLED | `AnswerPlanTests.swift:410` |
| A16 | review M4: the plan given the first answer's health, not the routed surface's | KILLED | `AnswerPlanTests.swift:212` |
| A17 | finding A: the rest never shown on request | KILLED | `AnswerPlanTests.swift:383` |
| A18 | M17-W5 defect 1 at the plan: every refinement removed, no chip to restore | KILLED | `AnswerPlanTests.swift:78`, `AnswerPlanTests.swift:85` |
| C1 | the binary search takes `<=` (review replay) | KILLED | `CombinePropertyTests.swift:79` |
| C2 | the positions searched unsorted | KILLED | `CombinePropertyTests.swift:79` |
| C3 | rank counted among every model on the board, not the shared ones | KILLED | `CombinePropertyTests.swift:72`, `CombinePropertyTests.swift:79` |
| C4 | the search never looks at the last position | SURVIVED, equivalent | N2 |
| S1 | a copy younger than a day said as stale | KILLED | `StandingsStoreTests.swift:131` |
| S2 | a kept copy served after a failed fetch dated now | KILLED | `StandingsStoreTests.swift:131` |
| G1 | the launch environment off the Debug-only list (review M5 undone) | KILLED | `test_client_decl_gate.py:85` |
| G2 | the hook rule applied to Debug configurations, not Release | KILLED | `make client-decls`: device, debug, simulator, debug |
| G3 | release_problems unwired from main() | SURVIVED (`make client-decls` and every test) | T6 |
| G4 | release_problems refuses nothing | KILLED | `test_client_decl_gate.py:85` |
| M5R | review M5 replay: a Release build reads its launch environment | KILLED | `make client-decls`: device, release, simulator, release |
| R1 | the UI target typed as a framework (review replay) | KILLED | `test_router_hints.py:383` |
| R2 | the app target also compiles UITests (review replay) | KILLED | `test_router_hints.py:383` |
| R3 | the UI target an app extension compiling its own folder | KILLED | `test_router_hints.py:383` |
| V1 | review M4 replay: the plan given a nil health | KILLED | `test_ios_client_contract.py:124` |
| V2 | review M4 replay: the combined disclosures under `if showingAllCombined` | KILLED | `test_ios_client_contract.py:124` |
| V3 | the plan never told the phone copy's age | KILLED | `test_ios_client_contract.py:124` |
| V4 | the kept copy's time never recorded | KILLED | `test_ios_client_contract.py:124` |
| V5 | #70: new standings do not bump the memo's stamp | KILLED | `test_ios_client_contract.py:124` |
| V6 | review M2 at the view: the empty answer said as no evidence whatever its code | KILLED | `test_ios_client_contract.py:60` |
| V6b | review M2 at the view, the field still read: every code said as no evidence | SURVIVED (`make client-decls` and every test) | T7 |
| V7 | D-176 at the view: the card notices composed in English whatever the reader's language | SURVIVED (`make client-decls` and every test) | T7 |
| V8 | D-143 at the view: the close call composed with no anchor | SURVIVED (`make client-decls` and every test) | T7 |
| V9 | the ordering note's copy drifts from ORDERING_NOTE | KILLED | `test_ios_client_contract.py:165` |
| V10 | a second request path beside the streamed one | KILLED | `test_ios_client_contract.py:580` |
| U1 | M17-W5 defect 1 on the screen: the removed chips are not rendered | KILLED | `make ui-test`: `ScreenPathTests.swift:68` |
| U2 | M17-W5 defect 2: the 'See the boards' row takes a tap on its text only | KILLED | `make ui-test`: `ScreenPathTests.swift:84` |
| U3 | review K1 undone: the ordering note under a one-answer surface | KILLED | `make ui-test`: `ScreenPathTests.swift:145` |
| U4 | review M4's branch mutant, on the screen | KILLED | `make ui-test`: `ScreenPathTests.swift:97` |
| U5 | #96 undone: the failure's sentence in English under a Turkish title | KILLED | `make ui-test`: `FailureScreenTests.swift:40` |
| U6 | review M7: a choice in the chooser chooses nothing | KILLED | `make ui-test`: `ScreenPathTests.swift:128` |

## Tests added/extended this review

**In this worktree, uncommitted** (`git diff`: 6 files, +185, all tests and the Swift manifest; the
whole diff is also kept as scratch `w2t/logs/proposed-tests.diff`). Each new test sits at the end of
its file or class, so no `file:line` citation in the PRD moves.

| test (file:line) | closes | red on (in a scratch copy of `4526384`) |
|---|---|---|
| `ios/EngineTests/EngineClientTests.swift:804` `MidStreamFailureTests.testATransferThatDiesMidBodyIsMappedLikeOneThatNeverStarted`, with its stub at `:773` | T1, #56 | E9, 5 runs of 5 |
| `ios/EngineTests/NoticesTests.swift:279` `testEveryNoticeWithoutAComposableFactIsTheEnginesEnglish` | T2, D-176 cl. 4, REQ-LOC-001 | N1, N2, N3 (and N4) |
| `ios/EngineTests/NoticesTests.swift:312` `testTheCombinedListWeighsAndFallsBackAsTheCardsDo` | T2, T3, D-135, #72 | N8, N10 |
| `ios/EngineTests/NoticesTests.swift:322` `testEveryComposedNoticeDiffersFromItsEnglish` | T4, #63 finding 2 | N18, N19, N20 |
| `ios/EngineTests/AnswerPlanTests.swift:325` `testTheMemoHandsThePlanTheHealthAndTheCopysAge` | T5, #70, #72, review M3, M4 | A7, A8 |
| `tests/unit/test_client_decl_gate.py:95` `test_main_refuses_a_release_dump_that_carries_a_ui_test_hook` | T6, D-175 cl. 3, review M5 | G2, G3 |
| `tests/unit/test_ios_client_contract.py:1172` `test_the_screen_composes_the_empty_reason_and_the_notices_from_their_facts` | T7, D-176, D-143, review M2 | V6, V6b, V7, V8 |
| `ios/EngineTests/test-manifest.txt` | the five Swift tests above, regenerated with `swift test --list-tests \| sort` | n/a |

- **Green:** `make check-fast` PASS with them in place: 1662 Python passed, 25 skipped; 428 Swift
  tests, exactly the manifest; `ruff` clean; client-decls PASS.
- **Red:** each was run against each fault it is written for, in scratch `w2t/trees/prop`, with the
  fault applied and its bytes then written back (`w2t/prop_red.out`). Each failed by assertion.
- **Two things learned writing T1's test.** A stub that fails at once is thrown by
  `bytes(from:)` itself, and so is one that sends an untyped response: `URLSession` holds an untyped
  response back until it has sniffed 512 bytes. The stub therefore types its response and sends
  2 KiB before it fails.

*Filled by: Tester seat (independent) · Date: 2026-10-04 · Commit range: `d080060..4526384`*
