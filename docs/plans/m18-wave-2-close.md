---
record_type: wave
id: m18-wave-2-close
status: draft
process_version: v6.6
date: 2026-10-04
---
# Wave-Close Checklist — M18 Wave 2, screen quality

**The screen is tested on the simulator, says everything in the reader's language, and keeps what
it shows short and true.**

**The UI test target (#69, D-175).** `make ui-test` runs `ModelRankingUITests` on the iPhone 17 Pro
simulator against a local engine. It covers ask, the combined list, removing and restoring a chip,
the detail, "Change" and the failure screen, with routing scripted through `ModelOutputBoundary`.
Both of M17-W5's simulator-found defects fail a test when put back.

**#63, the 14 UI findings, reproduced and decided one by one (D-175).**
- 3 was gone; 10 is the engine's data (#112); the other 12 are fixed.
- Two new findings: A, the combined list's length, is fixed. B, a drawing request ranked as image
  reading, is #113, for W3.

**Language (D-176).** The notices are composed from facts in both languages. `/v1` gains
`close_call_fact`, `unavailable_reason_code` and `source_health.reason`, each additive. The failure
screen (#96) and the local-network prompt (#95) are Turkish too.

**The combined list.**
- Its disclosures are fields of its plan (#67). Among them: a stale board and an old phone copy
  (#72).
- It shows ten rows and the rest on request.
- It can be filtered to models with an API or open weights (#78).

**Cost and robustness.** `combine` runs in O(n log n) (#74). The plan is computed when its inputs
change (#70). Every response is streamed and stopped at its route's ceiling (#56).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md` §2 W2 says MED. The wave plan (`docs/plans/m18-wave-2-plan.md:13-15`, deleted in this close) raised it to **HIGH**: `ios/ModelRanking/Engine/EngineClient.swift` is a security glob, and the wave adds a Debug-only test hook. The milestone plan records it in its W2-close amendment | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Each change's tests were written and seen to fail before the code: the engine's `close_call_fact` (`88e0ea3`); the Swift composers, which would not compile first; #74's cost test (59 s, red, before `a472b75`); #56's ceilings; the review round's fixes (`4526384`, each review mutant replayed and killed). Every commit ran only after `make check-fast` returned 0. **One slip:** `5b1add8` was first committed on a red check (the audit test's Turkish words), and amended before it was pushed. The red tests and their fixes went in the same commits, not in separate pairs as in W5 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m18-wave-2-review.md` (`b929a18`): **PASS WITH FINDINGS**, 8 MINOR, 3 K.9, 2 risks, on `d080060..3ad7dc1`. `docs/reviews/m18-wave-2-tester.md` (`be23b04`): **PASS WITH FINDINGS**, 7 MINOR, 1 K.9, on `d080060..4526384`. The seats ran one after the other, each in its own worktree behind command guards (D-174). The Tester was allowed the simulator; the reviewer was not | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (the owner's ruling, 2026-09-29). The M18 closure seat reads this slice; `EngineClient.swift` (#56) and the Release hook gate (D-175) are the parts to read | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester injected 89 faults: 3 equivalent, 71 of 86 killed (82.6 %). Its seven tests (`93ac320`) kill all 86. Five screen faults, run through `make ui-test`, each fail their UI test, among them the two M17-W5 defects. The Code-Reviewer ran 17 mutants; its 4 survivors became M1, M4 and M5, and each now dies. The Tester restored in place and checked every file by sha256 and HEAD blob. The author's own mutants were restored by copy and checked by md5 | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The screen: the UI target drives the built app against a running engine (`ios/UITests/ScreenPathTests.swift`, `FailureScreenTests.swift`), 10 tests passed at `4526384` by both the author and the Tester. The engine: `close_call_fact` and the reason codes through the HTTP routes (`test_why_facts.py`, `test_empty_answer_reasons.py`, `test_api_v1.py`). The phone's logic through `swift test` (428 tests, each named in the manifest). The Release hook gate through `make client-decls` on real compiler output, and through `main()` on canned output (`test_client_decl_gate.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | "Every response is read through its route's byte ceiling, and stopped there": `ResponseCeilingTests` (a 4 MiB stream stopped before its last chunk; a declared length refused before the body) and `test_every_response_is_read_through_its_routes_ceiling`. "A Release build reads neither its launch arguments nor its launch environment": `make client-decls` (both Release configurations refused the review's mutant) and `test_main_refuses_a_release_dump_that_carries_a_ui_test_hook`. The single invariants list is #89 (W6) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None on the wave's work. The Code-Reviewer restored its own mutants with `git checkout --` on each file in its detached worktree, where nothing of the wave was uncommitted (its file says so). The Tester restored in place, never with `checkout` or `restore` | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a network read on the phone: `EngineClient.fetch` only, one session call (`session.bytes(from:delegate:)`), pinned by the gate. Producers of launch input in a Release build: none; the one launch-argument read is `LaunchRouting.swift`, in Debug only. `-language` reaches Release by design, through the one `@AppStorage` (D-175 "as built") | ✅ |
| 9b | Scope & draft PR | Delivered: P0-P6 of the wave plan, all ten issues (#69, #63, #67, #72, #70, #74, #56, #78, #95, #96). Deferred: none. Filed and triaged: #112, #113, #114, #115. The milestone plan's W2-close amendment records it. Draft PR on `wave/m18-w2` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat d080060 HEAD`: 56 files, +4233/−169, before this close. Code and build (`src/`, `scripts/`, `ios/ModelRanking/`, `ios/Config/`, the project, `Makefile`, `.gitignore`): 26 files, +1330/−116. The rest are tests, the two reviews, the ADRs and the PRD. VARIANCE noted: a HIGH wave of ten issues, with a new test target and a review round | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make ui-test (local, D-175) · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. The per-wave security pass is not run by rule (D-172), not skipped. Bypass: none. CI's first run on #116 failed its skip budget (86 skipped, budget 76): ten new artifact tests skip where there is no `advisor.db`. `b436552` made them one, added a fixture test that runs in CI, and raised the budget to 77 with its reason in `docs/skip-budget.txt`; CI then passed at `993a1ce` | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-04 · Wave commit range: `d080060..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `4526384` |
| review M2 | fixed `4526384` |
| review M3 | fixed `4526384` |
| review M4 | fixed `4526384` |
| review M5 | fixed `4526384` |
| review M6 | fixed `4526384` |
| review M7 | fixed `4526384` |
| review M8 | fixed `4526384` |
| review K1 | fixed `4526384` (the app says the ordering note only where two answers are) |
| review K2 | fixed `4526384` |
| review K3 | fixed `4526384` |
| review R1 | refused — the Tester ran `make ui-test` at `4526384` (10 passed) and saw five screen faults fail their UI tests; that no gate runs it is D-175's decision, not a gap in this wave |
| review R2 | #115 |
| tester T1 | fixed `93ac320` |
| tester T2 | fixed `93ac320` |
| tester T3 | fixed `93ac320` |
| tester T4 | fixed `93ac320` |
| tester T5 | fixed `93ac320` |
| tester T6 | fixed `93ac320` |
| tester T7 | fixed `93ac320` |
| tester K1 | #114 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .gitignore .language-allow Makefile docs/decisions.md docs/plans/m18-plan.md docs/plans/m18-wave-2-plan.md (deleted) docs/prd.md docs/reviews/m18-wave-2-review.md docs/reviews/m18-wave-2-tester.md ios/Config/UITests.xcconfig ios/EngineTests/AnswerPlanTests.swift ios/EngineTests/CombinePropertyTests.swift ios/EngineTests/DetailTests.swift ios/EngineTests/EngineClientTests.swift ios/EngineTests/LanguageTests.swift ios/EngineTests/NoticesTests.swift ios/EngineTests/RouterBoundaryTests.swift ios/EngineTests/ScoresTests.swift ios/EngineTests/StandingsStoreTests.swift ios/EngineTests/UncertaintyTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking.xcodeproj/project.pbxproj ios/ModelRanking.xcodeproj/xcshareddata/xcschemes/ModelRanking.xcscheme ios/ModelRanking.xcodeproj/xcshareddata/xcschemes/ModelRankingUITests.xcscheme ios/ModelRanking/ContentView.swift ios/ModelRanking/Engine/AnswerPlan.swift ios/ModelRanking/Engine/Combine.swift ios/ModelRanking/Engine/Detail.swift ios/ModelRanking/Engine/EngineClient.swift ios/ModelRanking/Engine/FrontDoor.swift ios/ModelRanking/Engine/Language.swift ios/ModelRanking/Engine/Models.swift ios/ModelRanking/Engine/Notices.swift ios/ModelRanking/Engine/Router.swift ios/ModelRanking/Engine/Scores.swift ios/ModelRanking/Engine/ScriptedRouting.swift ios/ModelRanking/Engine/StandingsStore.swift ios/ModelRanking/Engine/Uncertainty.swift ios/ModelRanking/LaunchRouting.swift ios/ModelRanking/tr.lproj/InfoPlist.strings ios/UITests/FailureScreenTests.swift ios/UITests/ScreenAuditTests.swift ios/UITests/ScreenPathTests.swift scripts/client_decl_gate.py scripts/ui_test.sh src/app/adapter/main.py src/app/workflows/recommend.py tests/unit/test_api_config.py tests/unit/test_api_v1.py tests/unit/test_client_decl_gate.py tests/unit/test_empty_answer_reasons.py tests/unit/test_engine_address.py tests/unit/test_ios_client_contract.py tests/unit/test_ios_visual_contract.py tests/unit/test_recommend.py tests/unit/test_router_hints.py tests/unit/test_why_facts.py
Mutant set author: the Tester seat (89 faults) and the Code-Reviewer seat (17); the author's own set (the M17-W5 defects, the ceiling and plan pins, the review's mutants replayed) is supporting evidence only
Observed RED:   the "See the boards" row without contentShape fails testTheBoardsRowAnswersATapAwayFromItsText at its assertion "a tap in the row's empty middle did not open the boards"; a read that takes the whole stream and checks its size after fails testTheReadStopsAtTheCeilingWhileTheResponseStreams ("64 of 64 chunks were sent before the read stopped")
Owner instruction: "the restriction of simulator has been disgarded you can test when ever you need" (2026-10-04) and "proceed with what you recommend from now on, do not ask me" (owner, translated from Turkish, 2026-09-29). The wave drives the screen on the simulator, and each product choice in #63 and #78 is the agent's recommendation, recorded in D-175
K.8 contracts:  /v1 answers gain close_call_fact, unavailable_reason_code and source_health.reason (D-176, additive); EngineClient.fetch streams (byteCeiling per route); answerPlan gains primaryHealth and phoneCopyDays; StandingsStore gains currentKept
Stopped at three attempts: NONE
Hand-kept lists: UIText.surfaceBlurb (one line per surface id, held by a test over the fourteen served ids); effortName (the engine's effort vocabulary, unknown kept as is); orderingNoteEnglish and blendInputPercent/blendOutputPercent (copies of engine values, each held equal by a test)
```
