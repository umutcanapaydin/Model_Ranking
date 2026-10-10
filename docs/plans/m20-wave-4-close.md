---
record_type: wave
id: m20-wave-4-close
status: draft
process_version: v6.6
date: 2026-10-08
---
# Wave-Close Checklist — M20 Wave 4, the combined list is the answer

**Three issues: #212, #208, and #211's wiring. #199 moved to M21 after the first review.**

**What the reader now sees** (D-188 clauses 4 to 6, proposed).
- **Our own list is the default answer.** It answers every question asked and every surface the
  reader chooses. The launch screen, which answers no one yet, keeps the primary boards' picks.
- **A family list says what built it.** It names how many boards it was built from, each with its
  date, and how many of those boards a model needs. Its place is the average of the model's relative
  places on those boards. An older board is a small note with its date, never a warning over the
  list. One tap shows where each board placed a model.
- **The primary board's own answer is one tap away, and one tap back.**
- **Coding shows two family lists, or neither.** Neither list leads, and each has its own controls.
- **The refinements come from the on-device model where it read the question,** and from the
  question's words otherwise. The answer plan is the one place that reads the words.
- **Apple Intelligence (#208):** a moving glow on the question while it reads it, still under
  Reduce Motion, and one small line per state of the on-device model saying who reads the question.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m20-plan.md` §2 W4: **HIGH**, amended from MEDIUM after W3's review, since `ios/ModelRanking/Engine/AnswerPlan.swift` joined the security globs as the one word reader (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #212 (`1e0d0a7`, `b805c30`), D-188 clause 6 (`b9c34cf`, `452dc48`), the screen paths (`992fc35`, `36dad00`), the first review (`4ea8548`, `9e05bb1`), the second (`9c34e3e`, `6e2820f`). `4ea8548` did not compile (the Tester's M5, refused below); the others fail only on their own tests (`docs/reviews/m20-wave-4-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m20-wave-4-review-round-1.md` (`004f625`): **BLOCKING**, B1, M1–M7, K1–K3, R1, R2, answered by `9e05bb1`. `docs/reviews/m20-wave-4-review.md` (`c8eb25c`): **MINOR**, M1–M3, K1, R1. `docs/reviews/m20-wave-4-tester.md` (`cd834b3`): **MINOR**, M1–M5, R1. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M20 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 22 faults: 12 of its 20 caught as delivered; with its four tests 21 of 22 (the one left changes nothing a reader can see). The first review planted 12 (8 survived, all caught since `4ea8548`), the second 20 (6 survived, held since `9c34e3e` and the Tester's tests). Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-CMB-004 and REQ-CMB-005 through `answerPlan`, `familyLists`, `plannedOutcome` and the disclosures (`ios/EngineTests/FamilyPlanTests.swift`); REQ-APP-007 through `UIText.onDeviceCaption` (`ios/EngineTests/LanguageTests.swift`) and the screen (`ScreenPathTests.swift::testTheQuestionSaysWhoReadsIt`); REQ-APP-002 and REQ-APP-008 on the simulator (`ios/UITests/ScreenPathTests.swift`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | The one word reader (D-188 clause 6) is `AnswerPlan.swift`, held by `tests/unit/test_router_hints.py::test_only_the_answer_plan_reads_refinements_from_the_words`; the model's choice of no refinement stands (`FamilyPlanTests.swift::testTheOnDeviceModelsChoiceOfNoRefinementStands`). Nothing typed reaches the engine: `EngineClient` is unchanged in the range | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python and restored from saved bytes (`docs/reviews/m20-wave-4-tester.md`) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | A combined list reaches the screen from one producer, `answerPlan` (`ios/ModelRanking/Engine/AnswerPlan.swift`), through `PlanMemo`; the pair rule from `familyLists`; the outcome planned from `plannedOutcome`. The view composes no outcome of its own (`tests/unit/test_router_hints.py`) | ✅ |
| 9b | Scope & draft PR | Delivered: #212, #208, #211 (with W3). Moved to M21: #199. Filed: #219, #220 (first review K2, K3 and R2). Draft PR on `wave/m20-w4` against `main`, stacked on `wave/m20-w3` | ✅ |
| 9a | Economy | `git diff --stat origin/wave/m20-w3...HEAD` before this close: 17 files, 1610 insertions(+), 56 deletions(-), of which the code is `ContentView.swift` (174), `AnswerPlan.swift` (130), `Language.swift` (67) and `Notices.swift` (5); the rest are tests (484), three verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · make ui-test · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` at `6e2820f`: ScreenPathTests 19 of 19, FailureScreenTests 2 of 2; again at `cd834b3` (ScreenPathTests 19 of 19) (`scratchpad` run log, `ios/UITests/ScreenPathTests.swift`). The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-08 · Wave commit range: `origin/wave/m20-w3...HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| round-1 B1 | fixed `9e05bb1` |
| round-1 M1 | fixed `9e05bb1` |
| round-1 M2 | fixed `9e05bb1` |
| round-1 M3 | fixed `9e05bb1` |
| round-1 M4 | fixed `9e05bb1` |
| round-1 M5 | fixed `9e05bb1` |
| round-1 M6 | fixed `9e05bb1` |
| round-1 M7 | fixed `9e05bb1` |
| round-1 K1 | fixed `9e05bb1` |
| round-1 K2 | #219 |
| round-1 K3 | #220 |
| round-1 R1 | fixed `9e05bb1` |
| round-1 R2 | #220 |
| review M1 | fixed `6e2820f` |
| review M2 | fixed `6e2820f` |
| review M3 | fixed `6e2820f` |
| review K1 | fixed `6e2820f` |
| review R1 | #220 |
| tester M1 | fixed `cd834b3` |
| tester M2 | fixed `cd834b3` |
| tester M3 | fixed `cd834b3` |
| tester M4 | fixed `cd834b3` |
| tester M5 | refused — a pushed red commit is not rewritten; red commits stub new symbols from `9c34e3e` on |
| tester R1 | fixed `6e2820f` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .language-allow docs/decisions.md docs/plans/m20-plan.md docs/plans/m21-plan.md docs/prd.md docs/reviews/m20-wave-4-review-round-1.md docs/reviews/m20-wave-4-review.md docs/reviews/m20-wave-4-tester.md ios/EngineTests/FamilyPlanTests.swift ios/EngineTests/LanguageTests.swift ios/EngineTests/UITextLanguageTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/ContentView.swift ios/ModelRanking/Engine/AnswerPlan.swift ios/ModelRanking/Engine/Language.swift ios/ModelRanking/Engine/Notices.swift ios/UITests/ScreenPathTests.swift docs/plans/m20-wave-4-close.md
Mutant set author: the Tester seat (22) and the two review seats (12; 20); the author's plants are supporting evidence only
Observed RED:   the Tester's survivors die on its four tests (`cd834b3`); the first review's on `4ea8548`; the second review's on `9c34e3e`
Owner instruction: "Yes, of course, let's do it in M20; it's our biggest strength" (owner, 2026-10-08, translated from Turkish), and the Apple Intelligence glow with a small "enhanced" line (#208, owner, 2026-10-08, translated from Turkish)
K.8 contracts:  no /v1 field or route changes; `CombinedView` gains `coverage` and `NamedBoard` dates, `CombinedDisclosure` gains `.familyOrder`, `UIText.onDeviceCaption` takes an `OnDeviceState`; D-188 clause 5 amended (chosen surfaces, the launch screen)
Stopped at three attempts: NONE
Hand-kept lists: the five captions in `ScreenPathTests.testTheQuestionSaysWhoReadsIt`, the UI target's scripted routing (#199, M21)
```
