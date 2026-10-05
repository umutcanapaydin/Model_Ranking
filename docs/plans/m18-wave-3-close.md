---
record_type: wave
id: m18-wave-3-close
status: draft
process_version: v6.6
date: 2026-10-05
---
# Wave-Close Checklist — M18 Wave 3, reading the question

**The app reads whether what was typed is a search for a model, and coding questions reach the
coding answers.**

**Reading the question (#66, D-169 as amended).**
- The code reads four signals on every tier: no word in any language, small talk, pasted content,
  and an instruction to the app.
- The on-device model gives one closed yes/no verdict, generated after the surface.
- The outcome follows from those:
  - no word or small talk: the note;
  - a doubt in code, together with the model's "something else": the note;
  - either one alone: a one-tap question back, which sends nothing until the reader answers.
- Measured on a fresh held-out set:
  - no genuine search got the note, and 1 and 2 of 40 were asked;
  - 21 and 20 of 40 inputs that are not a search were caught, against a bar of 32. That bar is
    missed.

**Coding questions (#73).** They reach `coding` in 34 and 30 of 40 cases (baseline 7 and 6), with
web development and documents held. **Met.**

**Requests to make an image (#113).**
- The model does not decline them, so a code rule answers one routed to `vision` as unmeasured.
- It caught 10 of 15 at the measure, and 7 of 15 in the code that ships. The bar was 11.
- Reading an image reaches `vision` 8 of 10 times, as at the baseline. The bar was 9.
- Both bars are missed, and the pull request asks the owner.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md` §2 W3 and the wave plan: **HIGH** (what the on-device model's output decides, D-126, and the screen). The wave plan is deleted in this close | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Signals, boundary and screen were test-first (`2bd9154`); three tuning variants per problem were measured on tuning sets only (`4373dae`); each review round's fixes came with the reviewers' own lines as tests (`55a1aef`, `2d5f86a`, `b6ab027`). Every commit ran only after `make check-fast` returned 0 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | Code review, three rounds by three seats. Round 1 is `docs/reviews/m18-wave-3-review-round-1.md`, BLOCKING (B1–B4). Round 2 is `docs/reviews/m18-wave-3-rereview.md`, BLOCKING (B4 carried, B5). Round 3 is `docs/reviews/m18-wave-3-review.md`, the verdict of record: **PASS WITH MINOR**. Tester, two seats. The first is `docs/reviews/m18-wave-3-tester-round-1.md`, BLOCKING on T1 (closed by its own test). The second is `docs/reviews/m18-wave-3-tester.md` (2026-10-05, at `a4c898f`), the verdict of record: **MINOR**, T10–T13. Each record moved to the path `/close-wave` reads, as M17-W2 did. Each seat had its own worktree; the third reviewer and both Testers had their own venv (the second review's K5). The first Tester ran the simulator | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M18 closure seat reads this slice, from `docs/security-invariants.md` (W6) | N/A |
| 5 | Tester fault-injection, restore byte-identical | The first Tester injected 104 faults, 3 equivalent, and killed 71 of 101 (70.3 %); with its tests, 101 of 101 (`a4c898f`). The second re-ran the first seat's 33 survivors, each now killed. It killed 51 of its own 61, and 61 of 61 with its tests (`ff48675`). Both restored every file in place by sha256, never by `checkout` or `restore`. The third reviewer ran 17 mutants, all accounted for | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The reading: `ReadingTests` and `ReadingThroughTheTiersTests` drive `TieredRouter` and the boundary. The screen: `make ui-test`, 16 passed (the author at `b6ab027` and the first Tester); the held card's wiring pinned in the client gate (T8, T11, T12). The measures: `docs/research/m18-w3-question-reading-probe-2026-10-04.md`, with every run file and both scorers | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | "No held-out question is written into the code or its tests" (D-147 clause 5): `test_no_held_out_question_is_written_into_the_code_or_its_tests`. "A tracked symlink is refused": `test_no_tracked_links.py`. D-126's closed verdict: `testTheBoundaryMapsTheModelsVerdict`, and the reading enum pin in `test_router_hints.py`. W6's `docs/security-invariants.md` lists them | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None on the wave's work. The seats restored in place by hash | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a reading: `ModelOutputBoundary.outcome` (the model's verdict) and `TieredRouter.read` (the signals), nothing else (the enum pin refuses a fourth case). Producers of a gap entry: `recordsGap`, which only a search reaches (`testOnlyASearchIsKeptInTheGapRegister`) | ✅ |
| 9b | Scope & draft PR | Delivered: #73 (met), #66 and #113 (built, measured, bars missed; the owner is asked in the PR). Filed: #117, #118, #119, #120, #126, #127, #132, #133. Draft PR on `wave/m18-w3` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat 93040ac HEAD`: 98 files, +38291 before this close. About 36,000 of those lines are the per-question run files of the measures (`docs/research/m18-w3-runs/`). The app code and scripts are 17 files, +1120. VARIANCE noted: a measured wave with three review rounds | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make ui-test (local, D-175; the author and the first Tester) · the reading probes on the owner's Mac · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR, with one question to the owner`. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-05 · Wave commit range: `93040ac..HEAD`

## Review findings — each one fixed here, filed, or refused

The verdicts of record are the third review and the second Tester. The earlier rounds' ids follow,
so that every finding of the wave has a row.

| finding | disposition |
|---|---|
| review M16 | fixed `b6ab027` |
| review M17 | fixed `b6ab027` |
| review M18 | fixed `b6ab027` |
| review M19 | fixed `b6ab027` |
| review M20 | fixed `b6ab027` |
| review K6 | #119 |
| review K7 | #105 |
| review K8 | #120 |
| review R1 | fixed `a4c898f` |
| review R2 | refused — measured by the first Tester, it does not hold on these sets: through the code's signals alone, 473 genuine questions got no note, one question back (the colon doubt the suite names) and no image override |
| review R3 | #91 |
| review R4 | #113 |
| review R5 | fixed `8a18324` |
| review R6 | #113 |
| tester T10 | fixed `ff48675` |
| tester T11 | fixed `ff48675` |
| tester T12 | fixed `ff48675` |
| tester T13 | fixed `ff48675` |
| tester K11 | #132 |
| tester K12 | #133 |
| round-1 tester T1 to T8 | fixed `a4c898f` |
| round-1 tester T9 | fixed `a4c898f` (REQ-IMG-003's numbers were already in `8a18324`) |
| round-1 tester K9 | #126 |
| round-1 tester K10 | #127 |
| round-1 tester R7 | #113 (the PR's question carries its numbers) |
| round-1 tester R8 | #66 (the PR's question carries its numbers) |
| round-2 review B4 | fixed `2d5f86a` |
| round-2 review B5 | fixed `5f0937b` |
| round-2 review M9 to M13 | fixed `2d5f86a` |
| round-2 review M14, M15 | fixed `5f0937b` |
| round-2 review K4 | #118 |
| round-2 review K5 | fixed in the seat setup: each later seat built its own venv (`make install`) |
| round-2 review R1 to R4 | carried into round 3 as its R1 to R4, above |
| round-1 review B1 to B3 | fixed `55a1aef` |
| round-1 review B4 | fixed `2d5f86a` |
| round-1 review M1 to M8 | fixed `55a1aef` |
| round-1 review K1 | fixed `55a1aef` |
| round-1 review K2 | #117 |
| round-1 review K3 | fixed `53937c4` |
| round-1 review R1 to R3 | carried into round 2 |

The record files' nested sub-points were renumbered from bullets to numbered lists, format only,
so that the wave check reads only the findings' own bullets (`1c612ca` and this close).

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .gitignore .language-allow docs/decisions.md docs/plans/m18-wave-3-plan.md (deleted) docs/prd.md docs/research/m18-w3-question-reading-probe-2026-10-04.md docs/research/m18-w3-runs/* docs/reviews/m18-wave-3-* ios/EngineTests/ReadingTests.swift ios/EngineTests/RefinementBoundaryTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/ContentView.swift ios/ModelRanking/Engine/FrontDoor.swift ios/ModelRanking/Engine/Language.swift ios/ModelRanking/Engine/Reading.swift ios/ModelRanking/Engine/Router.swift ios/ModelRanking/Engine/ScriptedRouting.swift ios/UITests/ScreenPathTests.swift scripts/router_probe/* tests/unit/test_ios_client_contract.py tests/unit/test_no_tracked_links.py tests/unit/test_router_hints.py
Mutant set author: the two Tester seats (104 and 28 faults, plus the first seat's 33 re-run) and the third Code-Reviewer (17); the author's own mutants are supporting evidence only
Observed RED:   the first Tester's L1-L4 (D-169's sentences unrun, Language.swift's coverage below its floor) killed by its own test; the round-2 review's image-rule probes failing `testTheImageRuleNeverOverridesAnotherSurface` with the vision condition dropped
Owner instruction: the milestone plan's W3 as the owner merged it (#93), "proceed with what you recommend from now on, do not ask me" (owner, translated from Turkish, 2026-09-29), and D-169's clause 6, under which a missed bar goes back to the owner as one question in the PR
K.8 contracts:  RoutingOutcome gains `reading: InputReading` (.search, .notASearch, .unsure); the model's schema gains the closed `request` field, generated last; recordsGap reads `reading`. No /v1 change
Stopped at three attempts: #66 (catch bar) and #113 (both bars): three variants each, then stopped (D-169 clause 6); the PR asks the owner
Hand-kept lists: InputSignals' word lists (small talk, instruction verbs and objects, acting verbs, image nouns and verbs, picture targets, keyboard rows), each held by ReadingTests over the tuning sets; the held-out gate's retired-set list
```
