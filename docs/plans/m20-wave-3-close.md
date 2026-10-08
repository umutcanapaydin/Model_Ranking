---
record_type: wave
id: m20-wave-3-close
status: draft
process_version: v6.6
date: 2026-10-08
---
# Wave-Close Checklist — M20 Wave 3, the question picks its family

**Two issues, as the milestone plan's W3 names them: #211 (its Engine half; W4 wires it, as the plan
now says) and #206.**

**What the phone can now do** (D-188 clause 6, proposed, amending D-168 clause 4).
- `Refinements.familyBoards` gives a question's boards: its surface's family, then at most two
  refinements the surface allows, language before domain. With no family (an engine older than M20),
  the primary board leads.
- `Refinements.read` reads the refinements from the words where the on-device model did not read the
  question. It works in English and Turkish, and reads only words with one meaning. It takes at most
  one language and one domain, the first of each the question names.
  - An English language name counts only as the task's language ("in French", "learn Spanish",
    "Korean translation"). It does not count as a nationality ("German cars", "in Chinese stocks").
  - A domain word with a second meaning is not read: law, health, a novel approach, user stories, a
    server's health, AI software.
- A gate holds one reader of the words, by its path, whatever the spelling.
- #206: a short Turkish question made of model names (and their tiers) is a general question, before
  the English embedding.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m20-plan.md` §2 W3: **HIGH**, since `ios/ModelRanking/Engine/Router.swift` is a security glob (§3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #211 (`4df0cfc`, `7c12a7b`), the first review (`7408af2`, `fb773fe`), the second (`40cfcce`, `1adde33`), the Tester (`5c4fdc2`, `cf4aa2f`). `7408af2` did not compile, so its new tests were not seen failing for their own reason (the Tester's M3, refused below); the others fail only on their own tests (`docs/reviews/m20-wave-3-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m20-wave-3-review-round-1.md` (`81b1c42`, renamed at this close): **BLOCKING**, B1, M1–M6, R1, answered by `fb773fe`. `docs/reviews/m20-wave-3-review.md` (`0b65414`, written as round 2 and renamed at this close, the repo's convention for the last round): **MINOR**, M1–M7, K1, R1. `docs/reviews/m20-wave-3-tester.md` (`11c30cf`): **MINOR**, M1–M3, T1–T3, R1. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M20 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 30 faults (26 Swift, 4 gate): 21 caught as delivered, all 30 with its four tests (`11c30cf`). The first review planted 7 (5 survived, all caught since `7408af2`); the second planted 12 Swift and 5 gate faults (each survivor held since `40cfcce`). Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-CMB-004 through `Refinements.read` and `familyBoards` (`ios/EngineTests/QuestionFamilyTests.swift`) and, on wave/m20-w4, through `answerPlan` (`FamilyPlanTests.swift`); #206 through `SimilarityRouter.route` (`ios/EngineTests/KeywordRoutingTests.swift`); the one reader through the source (`tests/unit/test_router_hints.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | D-168 clause 4's boundary moves: a refinement read from the words reaches the list through one reader, the answer plan. Negative: `test_router_hints.py::test_only_the_answer_plan_reads_refinements_from_the_words` and `::test_no_other_name_reaches_the_word_reader` refuse a second reader by any spelling; the question still never leaves the phone (`::test_nothing_typed_by_the_reader_reaches_the_engine`) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python and restored from saved bytes (`docs/reviews/m20-wave-3-tester.md`) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Refinements reach a list from two producers: `ModelOutputBoundary.refinements` (the model) and `Refinements.read` (the words), the second called only from `AnswerPlan.swift`; both held by `tests/unit/test_router_hints.py` | ✅ |
| 9b | Scope & draft PR | Delivered: #206; #211's Engine half (its wiring is W4's, `docs/plans/m20-plan.md`). Filed: #218 (second review K1). Draft PR on `wave/m20-w3` against `main`, stacked on `wave/m20-w2` | ✅ |
| 9a | Economy | `git diff --stat origin/wave/m20-w2...HEAD` before this close: 13 files, 1283 insertions(+), 17 deletions(-), of which the code is `Refinements.swift` (146) and `Router.swift` (29); the rest are tests (290), three verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit but cf4aa2f, whose comment failed check-records and was fixed in 65efe0e) · make swift-test · make client-decls · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` was not run: no screen changed in this range (`ios/ModelRanking/Engine/` only). The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-08 · Wave commit range: `origin/wave/m20-w2...HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| round-1 B1 | fixed `fb773fe` |
| round-1 M1 | fixed `fb773fe` |
| round-1 M2 | fixed `fb773fe` |
| round-1 M3 | fixed `fb773fe` |
| round-1 M4 | fixed `7408af2` |
| round-1 M5 | fixed `fb773fe` |
| round-1 M6 | fixed `fb773fe` |
| round-1 R1 | fixed `fb773fe` |
| review M1 | fixed `1adde33` |
| review M2 | fixed `1adde33` |
| review M3 | fixed `1adde33` |
| review M4 | fixed `1adde33` |
| review M5 | fixed `40cfcce` |
| review M6 | fixed `1adde33` |
| review M7 | fixed `1adde33` |
| review K1 | #218 |
| review R1 | fixed `452dc48` |
| tester M1 | fixed `cf4aa2f` |
| tester M2 | fixed `cf4aa2f` |
| tester M3 | refused — a pushed red commit is not rewritten; Swift red commits add a stub from here on, as `cf4aa2f` records |
| tester T1 | fixed `11c30cf` |
| tester T2 | fixed `11c30cf` |
| tester T3 | fixed `11c30cf` |
| tester R1 | fixed `cf4aa2f` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .language-allow docs/decisions.md docs/plans/m20-plan.md docs/prd.md docs/reviews/m20-wave-3-review-round-1.md docs/reviews/m20-wave-3-review.md docs/reviews/m20-wave-3-tester.md ios/EngineTests/KeywordRoutingTests.swift ios/EngineTests/QuestionFamilyTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/Engine/Refinements.swift ios/ModelRanking/Engine/Router.swift tests/unit/test_router_hints.py docs/plans/m20-wave-3-close.md
Mutant set author: the Tester seat (30) and the two review seats (7; 17); the author's plants are supporting evidence only
Observed RED:   the Tester's 9 survivors die on its tests (`11c30cf`); the first review's on `7408af2`; the second review's on `40cfcce`
Owner instruction: "Yes, of course, let's do it in M20; it's our biggest strength" (owner, 2026-10-08, translated from Turkish), on the app composing its own list per question from many boards
K.8 contracts:  no /v1 field or route changes; `Refinements.familyBoards(primary:family:surface:chosen:)` and `Refinements.read` are new in the Engine; `CategoryHints.readings` is internal; D-188 clause 6 amends D-168 clause 4
Stopped at three attempts: NONE
Hand-kept lists: `Refinements.refinementWords` and its guards (`notAfter`, `notBefore`, `notStarting`, the language context words), `CategoryHints.comparisonParticles` and `modelTierWords`; the gate's one allowed reader
```
