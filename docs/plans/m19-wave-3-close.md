---
record_type: wave
id: m19-wave-3-close
status: draft
process_version: v6.6
date: 2026-10-06
---
# Wave-Close Checklist — M19 Wave 3, the gates see before the push

**Six issues, as the milestone plan's W3 names them; #108 by its guard only, under the wave's valve.**

**What a wave now sees before it pushes** (D-183).
- #137: `make test` counts, from every test's `needs` marker (`tests/skips.py`), how many tests CI will
  skip, and fails unless it is the budget (`coverage_floor.py --derive`). A skip spelled any other way
  the scan reads is refused, and an empty `parametrize` is a collection error. It caught this wave's
  own new CI skip before a push.
- #140: `wave-check-all` requires a heading for every wave a plan names in an amendment or a table, and
  `wave-check` holds a close to its plan's own security globs (brace forms and folders read), failing
  closed on a plan with none. A finding's sub-bullets are part of it.
- #122 (option B): on macOS `make test` runs the suite inside `scripts/offline.sb`, every child process
  included; the run stops before any test if a child could still name an outside peer. CI's half is a
  patch for the owner, posted on #122 (gap G-5 narrows to CI).
- #149: the deadline tests are held against a plain timer started beside the call; the 11.4 s was the
  test process not scheduled on a loaded machine, read to that cause (no app code blocks a thread, and
  in a test process a blocked pool delays no timer, measured).
- #117: a signal word only a live held-out set holds is flagged by the entry, and each current one is
  named with where it came from; four were added after their set (#177).
- #108: the source refuses a bare `URLSessionConfiguration()` in its two spellings; the cause was read
  (lldb, statically), not measured, so the issue stays open.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m19-wave-3-plan.md` (deleted in this close) and `docs/plans/m19-plan.md` §2 W3: **HIGH**, since gate definitions change (`Makefile`, `scripts/wave_check*.py`, `scripts/coverage_floor.py`) and `tests/conftest.py` is a security glob (`m19-plan.md` §3); the owner reviews the wave (AGENTS.md §3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #137 (`3f1bc30`, `08df6f4`), #140 (`fff70d0`, `16e3986`), #122 (`ea24722`, `b6fbc73`), #149 (`a0d58a9`, `de12beb`), #117 (`fbfc756`, `03329e4`), #108 (`4e39f30`, `f5d70cf`); the review (`7e01e53`, `f47231b`) and the Tester (`542c5d1`, `0a55d41`). Each red commit's only failures were its own tests (measured with `make check-fast`); #117's and #108's red commits used stubs returning nothing, so lint stayed clean. Each new check was watched failing on a planted violation and quiet on correct input | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m19-wave-3-review.md` (`960b2d3`): **MINOR**, M1–M10, K1, K2, R1–R3, on `133a525..f393bc4`. `docs/reviews/m19-wave-3-tester.md` (`e162748`): **MINOR**, M1–M9, on `133a525..f47231b`. Each seat had its own worktree at its range's end, its own venv from the locks and a copy of the served artifact, behind stubs refusing `launchctl`, `simctl` and `xcodebuild` (D-174) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172. The M19 closure seat reads this slice, from `docs/security-invariants.md` (INV-6 and gap G-5 changed here) | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 31 code faults: 28 caught as delivered, all 31 with its three tests (`e162748`), plus three data plants and a replay; every file restored byte-identical (sha256). The review's four code mutants were answered: the `--derive` and `headless_waves` callers are held by tests (`7e01e53`), and the M7 plant (a deadline that waits the model out) now fails both deadline tests, replayed by the author and restored byte-identical (`f47231b`). Each fix's own plants are in its commit message | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | #137 through `coverage_floor.py --derive` as `make test` runs it (`test_skip_budget_local.py::test_the_local_check_counts_what_ci_will_skip_and_passes_on_the_tree`, `::test_a_planted_test_that_needs_the_artifact_fails_the_local_check`). #140 through `wave_check.py` on a planted close and `wave_check_all.main` (`test_wave_check_m19_rules.py`). #122 through `make -n test` and a child process of the run (`test_offline_run.py`). #149 through `TieredRouter.route` (`FrontDoorTests.swift::SlowTierTests`). #117 over the tree's own lists and sets (`test_ios_client_contract.py::test_every_signal_word_only_a_live_held_out_set_holds_is_reviewed`, `::test_m18_w3s_own_case_is_flagged_phrase_by_phrase`). #108 over every Swift file (`test_swift_tests_offline.py::test_no_swift_source_builds_a_bare_session_configuration`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: INV-6 gains the offline run and the bare-configuration guard, with `test_offline_run.py::test_a_run_that_must_be_offline_and_is_not_stops_before_any_test`, `::test_a_child_process_the_suite_starts_cannot_name_an_outside_peer`, `::test_a_child_process_cannot_look_a_name_up_either` and `test_swift_tests_offline.py::test_a_bare_session_configuration_is_refused_in_both_of_its_spellings`; gap G-5 narrows to CI's test job (#122) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python, restored from saved bytes in a `finally` and compared. A probe of LaunchServices (`open -g https://example.invalid/` inside a trial profile) may have opened a browser tab on the owner's Mac; the address cannot resolve, so nothing was sent, and it was not repeated. The session started outside the repository, so its hooks were not loaded (#142) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | INV-6's producers: the pytest process (the in-process guard, M18-W7), every child of the run (the profile, `scripts/offline.sb`, entered only through `make test`'s recipe, which the conftest's refusal holds), and the Swift test bundle (the tripwire, and the source check for what it cannot see). Gaps tracked: CI's children (#122), the Swift tests' children (#179) | ✅ |
| 9b | Scope & draft PR | Delivered: #137, #140, #122's macOS half, #149, #117. In part: #108 (its guard; the cause measured stays open). CI's half of #122 is the owner's. Filed: #177, #178, #179, #180, #181, #182, #183. Draft PR on `wave/m19-w3` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat 133a525 HEAD`: 44 files changed, 2066 insertions(+), 92 deletions(-) before this close's own records. Over the ~400-line guide: the gates and their recipe are 11 files, 397 insertions(+), 13 deletions(-); the rest are tests (each check with its planted cases), the two verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · make gate · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` was not rerun: no app code changed in this range (only `ios/EngineTests`). The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-06 · Wave commit range: `133a525..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `f47231b` |
| review M2 | fixed `f47231b` (reading the commit range's own diff is #183) |
| review M3 | fixed `f47231b` |
| review M4 | fixed `7e01e53` |
| review M5 | fixed `f47231b` |
| review M6 | fixed `f47231b` |
| review M7 | fixed `f47231b` |
| review M8 | fixed `f47231b` |
| review M9 | fixed `f47231b` |
| review M10 | fixed `f47231b` |
| review K1 | #179 |
| review K2 | #180 |
| review R1 | #181 |
| review R2 | #182 |
| review R3 | fixed `f47231b` |
| tester M1 | fixed `0a55d41` |
| tester M2 | fixed `0a55d41` |
| tester M3 | fixed `0a55d41` |
| tester M4 | fixed `0a55d41` |
| tester M5 | fixed `0a55d41` |
| tester M6 | fixed `0a55d41` |
| tester M7 | fixed `0a55d41` |
| tester M8 | fixed `0a55d41` |
| tester M9 | fixed `0a55d41` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        Makefile pyproject.toml docs/decisions.md docs/plans/m19-plan.md docs/plans/m19-wave-3-plan.md docs/security-invariants.md docs/skip-budget.txt docs/reviews/m19-wave-3-review.md docs/reviews/m19-wave-3-tester.md scripts/coverage_floor.py scripts/offline.sb scripts/wave_check.py scripts/wave_check_all.py tests/conftest.py tests/skips.py tests/integration/test_arena_openrouter_contract.py tests/integration/test_epoch_bundle_contract.py tests/integration/test_litellm_contract.py tests/integration/test_scores_contract.py tests/unit/test_skip_budget_local.py tests/unit/test_wave_check_m19_rules.py tests/unit/test_offline_run.py tests/unit/test_ios_client_contract.py tests/unit/test_swift_tests_offline.py tests/unit/test_proxy_rule_and_workers.py (and sixteen more test files: fourteen with a skip moved to its `needs` marker, two with a comment that pointed at the old skip) ios/EngineTests/FrontDoorTests.swift ios/EngineTests/OfflineTestCase.swift ios/EngineTests/test-manifest.txt docs/plans/m19-wave-3-close.md (and the plan deleted)
Mutant set author: the Tester seat (31 code faults) and the Code-Reviewer seat (four); the author's plants are supporting evidence only
Observed RED:   the review's `--derive` and `headless_waves` callers survived and are now held (test_offline_run.py::test_make_test_still_counts_the_skips_ci_will_take, test_wave_check_m19_rules.py::test_wave_check_all_reports_a_headless_wave); the Tester's F4, F5 and F9 survived and die on its tests in test_skip_budget_local.py
Owner instruction: "merged continue" and "all merged" (owner, 2026-10-06), and "proceed with what you recommend, don't ask" (owner, 2026-09-29, translated from Turkish), under which #122's option B and #117's matching were taken; W3 delivers the plan's third wave as amended
K.8 contracts:  coverage_floor.py gains `--derive`; tests/skips.py (new) is the one registry of skips, with the `needs` marker and `--ci-skips-report`; wave_check.py gains plan_globs and the plan-glob HIGH rule; wave_check_all.py gains headless_waves; the Makefile's `test` recipe runs inside scripts/offline.sb on macOS and runs `--derive`. No /v1 field or route changes; no app code changes
Stopped at three attempts: NONE
Hand-kept lists: tests/skips.py NEEDS (each need's CI availability, #182), the held-out-only reviewed entries (HELD_OUT_ONLY_REVIEWED, each with its origin), RETIRED_HELD_OUT
```
