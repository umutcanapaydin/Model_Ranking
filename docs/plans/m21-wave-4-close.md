---
record_type: wave
id: m21-wave-4-close
status: draft
process_version: v6.6
date: 2026-10-10
---
# Wave-Close Checklist — M21 Wave 4, the controls

**The plan's W4 issues, plus #248 and #249.**
- **Delivered:** #200, #183, #201, #202, #203, #249, #182, #178, #179, #181, #248, #227.
- **Waiting on the owner's approval:** #189, the Bash guard's second reading (four OWNER APPROVAL commits).
- **The owner's:** #122. Its CI patches are posted on the issue.
- **Carried:** #108. Measuring it would open a crash dialog on the owner's Mac, and CI runs no Swift.

**What the controls now see** (D-192).
- **The commit range.** A close is read over its wave's whole commit range: from the wave's base to the close's own last commit. The range's diff decides the HIGH rule, and a rename counts both paths.
- **The ADR.** An ADR must come before the code it governs. Hooks and settings count as code.
- **The process log.** It must have a heading that names the wave.
- **Skipped and waived rows.** Every one, including N/A, must name a ledgered control in its check cell.
- **The session.** Row 8 states whether the session started in the repository.
- **The decision log.** It pairs every spelling of Amends with an Amended-by pointer back.
- **CI's job list.** It is read from its workflow.
- **The Swift legs:**
  - run inside the offline profile;
  - run the deadline tests on a one-thread pool;
  - run under a watchdog that kills the whole process group.
- **Records.** No longer state a gate's property flatly (#248).
- **The Bash guard's second reading:**
  - splits the command as the shell does;
  - bounds its own time and size;
  - lists by class what it does not hold (G-7);
  - is confirmed against known inputs only.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m21-plan.md` §2 W4: **HIGH**, since gate definitions change (`scripts/wave_check.py`, `scripts/check_records.py`, `Makefile`) and `.claude/settings.json`, `.claude/hooks/**` are security globs (§3); the owner reviews the wave (AGENTS.md §3) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit, from `a1283b9`/`2ac522c` to `ba28c7d`/`c1084bd`; the Tester built each red commit from `git archive`: each fails only on its own tests; `a1283b9` showed "14 skipped" through a file-wide mark, fixed in `99f3d35` (`docs/reviews/m21-wave-4-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m21-wave-4-review-round-1.md` (`fa37f8e`) and `-round-2.md` (`6ff94db`): **BLOCKING**, each on the guard's lexer, answered by `64b862a` and `36e74fa`/`bd55823`. `docs/reviews/m21-wave-4-review.md` (`a5346f5`): **MINOR**, M1–M4, R1, R2. `docs/reviews/m21-wave-4-tester.md` (`30e4314`): **MINOR**, M1–M6, K1, R1. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild`, and edited no `.claude/` file | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`); the M21 closure seat reads this slice, ledgered as `security-pass,m21` in `docs/control-events.csv` | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 21 faults: 10 caught as delivered, 20 with its tests (`30e4314`); the one left (a per-process SIGKILL with nothing left to kill) cannot be caught. The reviews planted their own, each survivor held since `1702041`, `26b6510` and `a804582`. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | The close checks through `scripts/wave_check.py` on planted repositories (`tests/unit/test_wave_check_m21_rules.py`); the decision log through `scripts/check_records.py`; CI's list through `ci.yml` (`tests/unit/test_ci_needs.py`); the Swift legs through the Makefile (`tests/unit/test_offline_run.py`, `tests/unit/test_swift_strict_pool.py`, `tests/unit/test_swift_watchdog.py`); the guard through its hook (`conformance/test-hook-claims.py`) | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | `docs/security-invariants.md`: INV-6 (the Swift legs offline, with a child process refused an outside peer), G-5 narrowed, G-7 (the guard's second reading: what it holds and does not, by class); negative cases in `conformance/test-hook-claims.py` (MUST_BLOCK, MUST_ALLOW) and `tests/unit/test_offline_run.py` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash; every plant was made in a scratch copy or from saved bytes and checked (`docs/reviews/m21-wave-4-tester.md`). Session started in the repository: no | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | A close's range has one producer, `scripts/wave_check.py`'s range reader, held over planted repositories; the Bash guard's verdict has two, the text check and `.claude/hooks/bash_guard.py`, each held alone by `conformance/test-hook-claims.py` | ✅ |
| 9b | Scope & draft PR | Delivered as listed above; #189 waits on the owner's approval of `c3b8b9a`, `64b862a`, `36e74fa`, `bd55823`; #122's CI patches are the owner's; #108 carried. Draft PR on `wave/m21-w4` against `main`, stacked on `wave/m21-w3` | ✅ |
| 9a | Economy | `git diff --shortstat origin/wave/m21-w3...HEAD`: 41 files, 4167 insertions(+), 71 deletions(-); the gates (`scripts/wave_check.py`, `scripts/check_records.py`), the guard (`.claude/hooks/bash_guard.py`), `scripts/watchdog.py` and their tests, and four review records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit but the D-192 docs commit 9cf8e12, gated by check-records; check-fast ran green after it with no change) · make swift-test · make client-decls · make ui-test · make wave-check · conformance/test-hook-claims.py · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` at `f02cee4`: the screen target 23 of 23 (19 screen paths and the ScrollStep tests) and FailureScreenTests 2 of 2 (`ios/UITests/ScreenPathTests.swift`). The per-wave security pass is N/A by rule (D-172), ledgered. Bypass: `9cf8e12` (the owner's ruling on the `commit-after-check-fast` control is pending from the M20 closure) | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-10 · Wave commit range: `origin/wave/m21-w3...HEAD`

## Review findings — each one fixed here, filed, or refused

Rounds 1 and 2 were answered by `f3df6ea`/`64b862a` and `1702041`/`da6b95f`, then
`ac4a0c8`/`36e74fa`/`bd55823` and `26b6510`/`e3e5a8a`. The rows below are the last round's and the
Tester's.

| finding | disposition |
|---|---|
| review M1 | fixed `f2b7d35` |
| review M2 | fixed `f2b7d35` |
| review M3 | fixed `f2b7d35` |
| review M4 | fixed `f2b7d35` |
| review R1 | fixed `f2b7d35` |
| review R2 | #189 |
| tester M1 | fixed `c1084bd` |
| tester M2 | fixed `30e4314` |
| tester M3 | fixed `30e4314` |
| tester M4 | fixed `99f3d35` |
| tester M5 | fixed `c1084bd` |
| tester M6 | fixed `99f3d35` |
| tester K1 | fixed `f02cee4` |
| tester R1 | fixed `30e4314` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .claude/hooks/bash_guard.py .claude/settings.json INSTALL.md Makefile conformance/test-hook-claims.py docs/architecture.md docs/control-events.csv docs/decisions.md docs/plans/m21-plan.md docs/prd.md docs/process-log.md docs/reviews/m21-wave-4-review-round-1.md docs/reviews/m21-wave-4-review-round-2.md docs/reviews/m21-wave-4-review.md docs/reviews/m21-wave-4-tester.md docs/security-invariants.md docs/wave-checklist.template.md ios/EngineTests/FrontDoorTests.swift ios/EngineTests/OfflineTestCase.swift ios/EngineTests/test-manifest.txt ios/UITests/ScreenPathTests.swift ios/UITests/ScrollStep.swift scripts/check_records.py scripts/watchdog.py scripts/wave_check.py scripts/wave_check_all.py tests/skips.py tests/unit/test_ci_needs.py tests/unit/test_client_decl_gate.py tests/unit/test_fetch_bounds.py tests/unit/test_ios_client_contract.py tests/unit/test_needs_git.py tests/unit/test_offline_run.py tests/unit/test_prd_citations.py tests/unit/test_router_hints.py tests/unit/test_security_invariants.py tests/unit/test_security_surface.py tests/unit/test_skip_budget_local.py tests/unit/test_swift_strict_pool.py tests/unit/test_swift_watchdog.py tests/unit/test_wave_check_m21_rules.py docs/plans/m21-wave-4-close.md
Mutant set author: the Tester seat (21) and the three review seats; the author's plants are supporting evidence only
Observed RED:   the Tester's survivors die on its tests (`30e4314`, `ba28c7d`); each round's on its red commit (`f3df6ea`, `1702041`, `ac4a0c8`, `26b6510`, `a804582`)
Owner instruction: "keep the PRs as drafts, don't wait for me, continue with the open issues" and "process the waves one by one" (owner, 2026-10-09, translated from Turkish)
K.8 contracts:  no /v1 field or route changes; the close template's row 8 gains the session field; the Bash hook gains a second reading, a 30 s timeout and onFailure block (OWNER APPROVAL)
Stopped at three attempts: NONE (the guard's lexer drew two BLOCKING verdicts; the third round was MINOR)
Hand-kept lists: the guard's guarded programs and read-only fly subcommands, the wrappers it reads through, the off-register PRD rows
```
