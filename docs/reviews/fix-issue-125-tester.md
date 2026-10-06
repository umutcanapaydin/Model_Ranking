---
record_type: review
id: fix-issue-125-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 125 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..6900e08 (`aebfa8a` red test, `6900e08` fix).
**Risk tier:** LOW (the suite's own client; no source file changes).

**Method.** Profile, `AGENTS.md`, `.agents/rules/issues.md` and D-174, D-175, D-177 read from the
base `0198eb3`. The acceptance criterion is the issue as its triage comment pins it: the API tests
use the test client starlette supports next, the routes and their tests' assertions stay, and
"`make lock` to the newest starlette leaves the suite green". Worktree detached at `6900e08`, its own
venv from the locks and a copy of the served `advisor.db`, behind the stubs that refuse `launchctl`,
`simctl` and `xcodebuild`. Red: the red commit's test file is byte-identical to the head's, and the
fix is the environment, so the pre-fix venv (no `httpx2`, as the base `dev.lock` installs) was
reproduced by a pytest plugin in the scratchpad that sets `sys.modules["httpx2"] = None`, which
makes `import httpx2` raise `ModuleNotFoundError` exactly as an absent package does. `make lock` was
run once (PyPI), and `make slopsquat` and `make deps` (PyPI). Faults: one exact unique replacement
per mutant, the named tests run, the original bytes written back and the sha256 compared, by a
harness in the scratchpad. No test reached the network.

## Verdict
PASS

Every clause of the criterion has a test that fails without it, red to green is on the symptom, and
all eight mutants were killed. One wording note on D-177's amendment (R1) does not change the
verdict.

## Acceptance-criterion coverage
- The test client runs on `httpx2`:
  `tests/unit/test_dependency_locks.py:302`
  (`test_the_api_tests_drive_the_engine_with_the_client_starlette_keeps`, cites #125). RED with
  `httpx2` hidden: `AssertionError: the test client runs on httpx, the path starlette deprecates`,
  and the run prints `StarletteDeprecationWarning: Using httpx with starlette.testclient is
  deprecated; install httpx2 instead`. That is the symptom itself, not a missing name. GREEN at the
  head.
- The venv gets `httpx2` because `dev.lock` pins it within the extra's range and with its hashes:
  `test_each_declared_dependency_is_locked_within_its_range[dev]` (M3, M4),
  `test_every_package_is_pinned_with_its_hashes[dev]` (M6), and the lock is current with
  `pyproject.toml`: `test_every_lock_is_current_with_pyproject[dev]` (M1, M2, M5).
- The warning is gone from every run: the head's `check-fast` test log has no
  `StarletteDeprecationWarning` (0 matches), and the whole suite passes with
  `-W error::starlette.exceptions.StarletteDeprecationWarning` (1798 passed, 25 skipped).
- The routes and their tests' assertions stay: the range changes four files, and the only test file
  it touches gains one test at its end. No API test changed.
- "`make lock` to the newest starlette leaves the suite green": `make lock` run once in this worktree
  rewrote all four locks byte for byte (sha256 of `serve`, `ingest`, `dev`, `build` and
  `pyproject.toml` equal before and after). It resolves starlette 1.7.0; fastapi 0.142.2 asks
  `starlette>=0.46.0` with no upper bound, so that is the newest starlette the resolver gets today.
  The suite is green on those locks (below).
- Provenance of the new package: starlette 1.7.0's own `full` extra declares `httpx2>=2.0.0`, and its
  test client imports `httpx2` first. `httpx2`, `httpcore2` and `truststore` ask Python >= 3.10;
  the project asks >= 3.11. `make slopsquat`: PASS, 20 declared dependencies, 0 suspect. `make
  deps`: no known vulnerabilities in the four locks.

## Suite result
- `make check-fast` at `6900e08`: PASS, six legs (lint, typecheck, records, test, client-decls,
  swift-test) in 68 s; test leg 1798 passed, 25 skipped.

## Mutants

| ID | Fault | Result | Killed by |
|---|---|---|---|
| M1 | `httpx2` dropped from the `dev` extra, left in the lock | KILLED | `test_every_lock_is_current_with_pyproject[dev]` |
| M2 | the extra asks `httpx2>=2.14`, the lock not re-resolved | KILLED | the staleness test and `test_each_declared_dependency_is_locked_within_its_range[dev]` |
| M3 | `httpx2`'s pin cut from `dev.lock` by hand, its header kept | KILLED | `test_each_declared_dependency_is_locked_within_its_range[dev]` |
| M4 | `dev.lock` pins `httpx2==2.12.0`, below the range | KILLED | as M3 |
| M5 | `dev.lock` records the base's `pyproject` hash (a stale lock) | KILLED | `test_every_lock_is_current_with_pyproject[dev]` |
| M6 | `httpx2`'s hashes stripped from `dev.lock` | KILLED | `test_every_package_is_pinned_with_its_hashes[dev]` |
| M7 | environment: `httpx2` not installed (the pre-fix venv); whole suite | KILLED | the #125 test, alone (1 failed, 1797 passed) |
| M8 | a test module forces the old client (`tests/conftest.py` hides `httpx2`); whole suite | KILLED | the #125 test, alone (1 failed, 1797 passed) |

8 of 8 killed. M1 to M5 also fail `test_a_lock_resolved_from_another_pyproject_is_reported_and_fails_the_check`
where the hash moves. M7 and M8 show the rest of the suite still runs on the `httpx` fallback, so
the #125 test is the one guard of the client choice, and it holds.

## Findings
- **R1** D-177's amendment lists what the re-lock changed in `dev.lock` as "httpx2, httpcore2,
  truststore, and `filelock` 4.0.10 to 4.0.11"; the lock also gained `httpx2-jsfetch` 1.0, a pin
  for WebAssembly only that no install here takes. The commit message names it. No test can hold a
  sentence like this, and it does not change the verdict; the author may add the name.

## Tests added/extended this review
- none

## Clean-up evidence
- Every mutant: original bytes written back, sha256 equal before and after (`pyproject.toml`,
  `requirements/dev.lock`, `tests/conftest.py`, checked again with `shasum -c` after the run).
- `make lock` rewrote the four locks with the same bytes; sha256 checked against the copy taken
  before it ran.
- `git hash-object` equals `HEAD:<path>` for `pyproject.toml` (fc63f0b9),
  `requirements/dev.lock` (79f406d6), `requirements/serve.lock` (43876b94),
  `requirements/ingest.lock` (abd1d8ea), `requirements/build.lock` (d32e82fb) and
  `tests/conftest.py` (2240ed9a). The plugin that hid `httpx2` lives in the scratchpad, not the
  tree. No checkout, restore, stash, reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| R1 | fixed: D-177's amendment names `httpx2-jsfetch` with the other `dev.lock` changes |
