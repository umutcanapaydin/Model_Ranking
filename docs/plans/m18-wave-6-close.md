---
record_type: wave
id: m18-wave-6-close
status: draft
process_version: v6.6
date: 2026-10-04
---
# Wave-Close Checklist — M18 Wave 6, first-release preparation

**What a first release beyond the owner's Mac needs, short of the owner's rulings.**

**The refresh cycle (#90).**
- W-125: the server loads no source client, parser or HTTP client.
- W-126: the cycle has three limits:
  - a 20-minute fetch budget, after which the late sources carry (D-156);
  - the kernel ends the cycle at 27 minutes;
  - the engine's kill at 30.
  A cycle whose engine is gone ends within seconds.
- W-130: the engine kills the cycle's whole process group, even after the cycle has exited.

**Installs (#35, #26, D-177).**
- Four hash-checked locks, the build backend's among them.
- Every install takes its lock and builds the project with nothing more fetched.
- pyarrow is the refresh's extra, off the serving image.
- The CI half is the owner's, proposed on #81.

**The security invariants (#89).**
- 71 invariants, each citing its negative tests, held by a gate that fails closed.
- Six gaps, G-1 to G-6, each on an issue. (This said five; corrected at the M18 closure, the repo
  review's M9. W7 closed two and the closure added two; the list's count is the one to read.)
- 11 rows were mutated by the author, 20 mutants were run by the review, and 10 rows were mutated
  by the Tester. Every mutant died once the review's and the Tester's tests were in.

**Records.**
- The data licences for the owner to rule on (#88).
- A protocol for a stranger's first use (#91).
- P5 (#110, #107, #60, #85) moved to M19 by the plan's valve.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m18-plan.md` §2 W6 and the wave plan: **HIGH** (the release's security invariants, the install path, the gates that hold D-126 and D-160). The wave plan is deleted in this close | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Each fix was red first, and the commit messages say so: W-125's import test (eleven client modules loaded), W-130's grandchild (30 s against 2 s), the review's M1 tests (five, each red on the code before, run in a scratch worktree at `HEAD`), #35's three install mutants, #89's planted lists. Every commit ran only after `make check-fast` returned 0 | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m18-wave-6-review.md` (`ac9a41e`): **MINOR**, M1–M8, 1 K.9, 3 risks, on `8a18324..cf83fea`. `docs/reviews/m18-wave-6-tester.md` (`465e6cf`): **MINOR**, T1–T6, 1 K.9, 3 risks, on `8a18324..4f6d025`. Each seat had its own worktree, its own venv from the locks (`make install`) and a copy of the served artifact (D-174 as W7 amends it); the reviewer ran behind stubs refusing launchctl, xcodebuild and simctl, and the Tester the same | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172. The M18 closure seat reads this slice, starting from `docs/security-invariants.md` | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester: 73 faults, 53 killed (72.6 %), 73 of 73 with its eight tests (`b24d743`); ten list rows mutated, ten killed; every fault restored and checked by sha256 and `git diff --quiet`. The reviewer: 20 mutants, 19 killed; the survivor (INV-38's group half) has a test (`4f6d025`). The author: eleven rows mutated (the list's "Mutation samples"), each killed, each restored by hash | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | #90: the server-import test runs the real server in a fresh interpreter; the limits run `refresh.main` and `NightlyRefresh.run_once` as processes. #35: `test_dependency_locks.py` reads the real locks and the real install files; `make install`, a release-style venv and the Docker image were each built from the locks at `4f6d025`. #89: `test_security_invariants.py` reads the real list and the tracked tree. #88 and #91 are records | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | This wave writes the list: `docs/security-invariants.md`, rows INV-10, -11, -42, -43, -70, -77 and -81 among the new or changed ones, each citing the tests that fail without it | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work | One `git checkout -- .github` reverted the author's own trial apply of the workflow patch (`.github` held nothing else uncommitted); the second trial used `git apply -R`. The seats restored in place by hash | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | Producers of a remote fetch in the cycle: every client reads through `protocols.bounded_get`, which the budget bounds (`test_every_remote_client_reads_through_the_bounded_fetcher`). Producers of an install: `Makefile`, `scripts/install_engine_service.sh`, `Dockerfile`, held by `test_every_install_reads_its_lock_and_resolves_nothing_else`; CI is the owner's (#81) | ✅ |
| 9b | Scope & draft PR | Delivered: #89, #90, #35, #26, #88 (the table and the questions; the ruling is the owner's), #91. Moved: P5 (#110, #107, #60, #85) to M19, by the plan's valve (milestone plan amendment). Owner's: #81 (the patch is on the issue), #115. Filed: #121, #122, #123, #124, #125. Draft PR on `wave/m18-w6` against `main`, opened in this close | ✅ |
| 9a | Economy | `git diff --shortstat 8a18324 HEAD`: 44 files, +6213/−248 before this close. The four locks are 2,600 of those lines, generated. The code and build (`src/`, `scripts/`, `Makefile`, `Dockerfile`, `pyproject.toml`) are about 800. VARIANCE noted: a HIGH release wave with two review rounds' tests | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make install (locked) · make wave-check · make gate · a Docker build of the serving image (twice) · pip-audit on the locks · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-04 · Wave commit range: `8a18324..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `4f6d025` |
| review M2 | fixed `cd67cc8` |
| review M3 | fixed `4f6d025` |
| review M4 | fixed `4f6d025` |
| review M5 | fixed `4f6d025` |
| review M6 | fixed `4f6d025` |
| review M7 | fixed `4f6d025` |
| review M8 | fixed `4f6d025` |
| review K1 | #81 |
| review R1 | #81 |
| review R2 | refused — not a defect left open: the locked release install was run on this Mac at `4f6d025` (ingest.lock and build.lock, then the project with `--no-build-isolation`), and the venv imports the refresh and pyarrow; the deploy itself is the owner's step |
| review R3 | refused — the window is the time between an atomic rename and a small JSON write; D-156 allows the next cycle's older arrival, as the review itself says, and the engine's kill always had the same window |
| tester T1 | fixed `b24d743` |
| tester T2 | fixed `b24d743` |
| tester T3 | fixed `b24d743` |
| tester T4 | fixed `b24d743` |
| tester T5 | fixed `b24d743` |
| tester T6 | fixed `b24d743` |
| tester K1 | #125 |
| tester R1 | refused — bounded by design: the next cycle's sweep removes a killed cycle's day-old scratch (INV-31, `test_scratch_a_killed_cycle_left_is_swept_by_the_next`) |
| tester R2 | fixed `b24d743` |
| tester R3 | refused — the review's R3, the same window, refused above for the same reason |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        .language-allow AGENTS.md Dockerfile Makefile docs/decisions.md docs/plans/m18-plan.md docs/plans/m18-wave-6-plan.md (deleted) docs/research/data-licences-2026-10-04.md docs/research/stranger-first-use-protocol.md docs/reviews/m18-wave-6-review.md docs/reviews/m18-wave-6-tester.md docs/security-invariants.md docs/warnings.ledger.md pyproject.toml requirements/build.lock requirements/dev.lock requirements/ingest.lock requirements/serve.lock scripts/install_engine_service.sh scripts/lock_dependencies.py src/app/adapter/nightly.py src/app/clients/arena.py src/app/clients/arena_slices.py src/app/clients/epoch.py src/app/clients/protocols.py src/app/clients/swebench.py src/app/workflows/access.py src/app/workflows/access_served.py src/app/workflows/board_tables.py src/app/workflows/ingest.py src/app/workflows/plans.py src/app/workflows/rank.py src/app/workflows/refresh.py src/app/workflows/registry.py src/app/workflows/run_records.py src/app/workflows/standings.py tests/unit/test_arena_slices.py tests/unit/test_dependency_locks.py tests/unit/test_fetch_bounds.py tests/unit/test_ios_client_contract.py tests/unit/test_nightly_refresh.py tests/unit/test_refresh.py tests/unit/test_security_invariants.py tests/unit/test_security_surface.py
Mutant set author: the Tester seat (73 faults, ten list rows) and the Code-Reviewer seat (20); the author's eleven list rows are supporting evidence only
Observed RED:   a grandchild holding the cycle's output kept the timeout kill waiting 30 s against a 2 s timeout (test_the_timeout_kill_takes_a_grandchild_that_holds_the_output); one regex holding the interpreter kept the old limit 4.8 s late (test_the_cycle_ends_at_its_limit_whatever_it_is_doing)
Owner instruction: "proceed with what you recommend from now on, do not ask me" (owner, translated from Turkish, 2026-09-29), and the milestone plan's W6 as the owner merged it (#93). The licence questions are put to the owner in the PR, not decided
K.8 contracts:  NightlyRefresh: the child runs in its own session; CODE_NAMES gains -SIGALRM, "timed out"; MODEL_RANKING_ENGINE_PID in the child's environment. refresh: FETCH_BUDGET_SECONDS, CYCLE_LIMIT_SECONDS, PARENT_POLL_SECONDS; protocols.cycle_budget. New modules run_records, board_tables, access_served (re-exported where they were). pyproject: [build-system] and the ingest extra. No /v1 change
Stopped at three attempts: NONE
Hand-kept lists: test_security_surface.MODEL_PACKAGES and WRITERS (the one workflow allowed to write), test_dependency_locks.PROJECT, lock_dependencies.LOCKS — each named with its reason in place
```
