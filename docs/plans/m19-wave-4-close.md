---
record_type: wave
id: m19-wave-4-close
status: draft
process_version: v6.6
date: 2026-10-07
---
# Wave-Close Checklist — M19 Wave 4, reading the question, a second round

**#66 improves and misses its bars; #113 is where it was; the valve's question goes to the owner.**
On fresh held-out sets written by an independent seat and never read by the author until measured
(`docs/research/m19-w4-question-reading-probe.md`, D-184):
- #66: knowledge questions caught 5 and 5 of 20 as the code ships (1 and 3 before; bar 14), not-a-search
  inputs 24 and 26 of 50 (18 and 21; D-169's bar 40), with no genuine search given the note and 1 and 0
  of 40 asked. The question-of-fact doubt (`InputSignals.asksAFact`) and the second-round signals ship.
- #113: the image rule stays on `vision`. The wave's reach beyond it drew three review verdicts on one
  class (MAJOR, BLOCKING, BLOCKING) and came out (#191); its Turkish "make" drew a fourth and came out.
  As the code ships, requests to make an image told "not measured" are 2 and 1 of 20 with the model
  and 14 of 20 without it, the baseline.
- #177: the three M18 held-out sets are retired to tuning.

By D-169 clause 6 nothing more is tuned on these sets; the pull request asks the owner whether to
ship what holds.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m19-wave-4-plan.md` (deleted in this close) and `docs/plans/m19-plan.md` §2 W4: **HIGH**, since what the on-device model's output decides (D-126) is touched and `ios/ModelRanking/Engine/Router.swift` is a security glob (§3); the owner reviews the wave (AGENTS.md §3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: the tuning misses (`1ef5657`, `de8c3f8`), the first review (`1e9a92a`, `671b305`), the second (`b2723f8`, `ec5159e`), the slice-out (`b957ec0`, `d324669`) the fourth (`58da18c`, `3697d64`) and the fifth (`f569f91`, `b38819b`); each red commit's only failures were its own tests (measured with `make check-fast`), and each fails on its own exported tree and passes on its fix (the Tester). The measure: the baseline and bars committed before any variant (`a34453b`); three variants per problem on tuning sets only; the held-out measure twice per tier (`ae2c528`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m19-wave-4-review.md` (round 5): **MINOR**, M1–M3, K1, R1–R3, on `3426ff3..3697d64` (`c372e23`), after rounds 1 to 4 (`-review-round-1.md` MAJOR, `-rereview.md` BLOCKING, `-review-round-3.md` BLOCKING, `-review-round-4.md` BLOCKING). `docs/reviews/m19-wave-4-tester.md` (`0bd4353`): **MINOR**, M1–M6, K1, on `3426ff3..d324669`. Each seat had its own worktree, its own venv from the locks and a copy of the served artifact, behind stubs refusing `launchctl`, `simctl` and `xcodebuild` (D-174) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172. M19's closure seat reads the milestone, this wave included; it ran on `wave/m19-w5`, which carries this wave | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 70 faults: 45 caught as delivered, 66 with its tests (`0bd4353`); every file restored byte-identical (sha256). The reviews planted 17, 18, 25 and 25 more; each survivor is a finding fixed or filed. The replay of every committed model-tier run was checked row for row | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | P1 (#177) through the held-out gates (`test_ios_client_contract.py::test_every_signal_word_only_a_live_held_out_set_holds_is_reviewed`, `::test_no_held_out_question_is_written_into_the_code_or_its_tests`). P2 and P5 through the committed runs and `score_w4.py` (`test_reading_probe_scorer.py`). P3 (#66) through `TieredRouter.route` (`ReadingTests.swift::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote`, the `ReadingSecondRound*` classes). P4 (#113) through `TieredRouter.route` on `vision` (`::testTheImageRuleOverridesOnlyAQuestionRoutedToVision`, `::testATurkishRequestToReadAnImageWithYapKeepsVision`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | None changed: the reading signals guard no security boundary, and the held-out gates are not security invariants (`docs/security-invariants.md`, "Not a row") | N/A |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python or in a scratch copy, restored from saved bytes and compared. The session started outside the repository, so its hooks were not loaded (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | No invariant hardened. The reading's producers are `InputSignals` and `TieredRouter.read`, every tier (D-169 as amended) | N/A |
| 9b | Scope & draft PR | Delivered: #177. In part: #66 (improved, bars missed: the owner's question), #113 (unchanged as shipped). Filed: #186, #191, #192, #193, #194, #195. Draft PR on `wave/m19-w4` against `main` | ✅ |
| 9a | Economy | `git diff --shortstat 3426ff3 HEAD -- ':!docs/research/m19-w4-runs'`: 22 files changed, 3728 insertions(+), 74 deletions(-) before this close's own records; the rest are the committed probe runs (JSON). Over the ~400-line guide: the code is 135 lines added and 37 removed in `ios/ModelRanking`; the rest are tests, five review and Tester records and the measure's record | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · make gate · make ui-test (19/19, after the M19 repo review's M1 found three UI tests the question-of-fact doubt had turned red; 3 of 16 failed at `ebbc324`) · the on-device probe (ReadingProbe, the owner's Mac) · gates SKIPPED: the plan's coding-set guard for variants that change the model's instructions (none was built; record §3) · tokens/cost: not measured · outcome: shipped as a draft PR`. Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-07 · Wave commit range: `3426ff3..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `b38819b` |
| review M2 | fixed `b38819b` |
| review M3 | fixed `f569f91` (the two folding assertions) and `b38819b` (D-184 cited) |
| review K1 | #192 (a comment names the tests its change would break) |
| review R1 | #194 |
| review R2 | #195 |
| review R3 | #195 |
| tester M1 | fixed `0bd4353` |
| tester M2 | fixed `0bd4353` |
| tester M3 | #193 |
| tester M4 | fixed `3697d64` |
| tester M5 | fixed `3697d64` |
| tester M6 | #186 |
| tester K1 | #191 |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        ios/ModelRanking/Engine/Reading.swift ios/ModelRanking/Engine/Router.swift ios/EngineTests/ReadingTests.swift ios/EngineTests/test-manifest.txt scripts/router_probe/ReadingProbe.swift scripts/router_probe/ReplayProbe.swift scripts/router_probe/notasearch_heldout_m19_questions.json scripts/router_probe/image_heldout_m19_questions.json tests/unit/test_ios_client_contract.py tests/unit/test_reading_probe_scorer.py .language-allow docs/decisions.md docs/prd.md docs/plans/m19-plan.md docs/plans/m19-wave-4-plan.md docs/research/m19-w4-question-reading-probe.md docs/research/m19-w4-runs/ (the scorer, the tuning sets and every run) docs/reviews/m19-wave-4-review-round-1.md docs/reviews/m19-wave-4-rereview.md docs/reviews/m19-wave-4-review-round-3.md docs/reviews/m19-wave-4-review-round-4.md docs/reviews/m19-wave-4-review.md docs/reviews/m19-wave-4-tester.md docs/plans/m19-wave-4-close.md (and the plan deleted)
Mutant set author: the Tester seat (70) and the five review seats; the author's plants are supporting evidence only
Observed RED:   the Tester's 25 survivors (21 now die on its tests and the gate changes it wrote; the scorer's on test_reading_probe_scorer.py); the reviews' mutants on the reading signals, held by the round tests
Owner instruction: "merged continue" (owner, 2026-10-06) and "you do not need to wait for the merges ... solve the bugs as issues triaged medium and above" (owner, 2026-10-07); the standing instruction of 2026-09-29, under which #177's retirement was taken
K.8 contracts:  no /v1 field or route changes; the model's schema and instructions unchanged; InputSignals gains asksAFact and the second-round signals (D-184)
Stopped at three attempts: the image rule's reach beyond vision (#191), taken out after its third verdict
Hand-kept lists: the reading signals' word lists (each word from a tuning row, #117's check, #186), HELD_OUT_ONLY_REVIEWED, RETIRED_HELD_OUT
```
