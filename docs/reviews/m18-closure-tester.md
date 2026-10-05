---
record_type: review
id: m18-closure-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# M18 Closure Tester Review

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the closure's code, tests or
records. It is not the closure security seat and not the milestone repo reviewer.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** `a259ed0..5cd6c88` (branch `enhancement/m18-closure`). The code commits are
`d749403` (W7's CI fix: `tests/conftest.py`, `tests/unit/test_no_network.py`, `docs/skip-budget.txt`)
and `c256864` (the `Makefile`, four Python test files and `ios/EngineTests/StandingsStoreTests.swift`).
The other five commits touch only records. `git diff --stat a259ed0..5cd6c88 -- src ios/ModelRanking
scripts` is empty: no shipped Python or Swift source changed.
**Scope:** the closure's code changes, each against its test, and the records' claims about that code
(`docs/security-invariants.md`, the two reviews' "Dispositions, at the closure", D-177's amendment).
**Risk tier:** not a wave. The changes answer the M18 repo review's M1, M2 and M3
(`docs/reviews/m18-repo-review.md`) and the closure security seat's S1 to S5
(`docs/reviews/m18-closure-security-review.md`).
**Base-pinned policy:** this profile was read from `a259ed0`. In the range,
`git diff --stat a259ed0..5cd6c88 -- .claude .agents AGENTS.md permission-matrix.md .github` shows
only `.agents/rules/issues.md` (D-178's note on closing bugs), which no rule of this seat reads.
**Model family:** author Claude, reviewer Claude; no second family in this session.
**Method:**
1. The seat's worktree is detached at `5cd6c88`, with the venv `make install` built from the locks and
   a copy of the served artifact (`advisor.db`, sha256 `6b3e80f2cb154bcd...`), behind command stubs
   that refuse `launchctl`, `simctl` and `xcodebuild` (D-174). The engine installer, launchd, the
   simulator, Docker and port 8080 were not touched.
2. Pre-fix code was read with `git show a259ed0:<path>` and from a `git archive` of `5cd6c88`, both
   extracted into the seat's scratchpad. No checkout, restore, stash or reset was used.
3. Each mutant is one or more exact, unique string replacements, applied by a script that recorded
   each file's sha256, ran the tests, wrote the original bytes back and asserted the hash. 45 mutants
   and two controls; every restore matched. Python ran with `PYTHONDONTWRITEBYTECODE=1` and `-B`.
4. The conftest's step-out was also run end to end. A probe suite (a contract module in a scratch
   `tests/integration` folder, with unit modules before and after it) was run by pytest against a copy
   of each conftest, with the guard's own reference to the real name lookup replaced by a stub, so
   nothing left the machine.
5. The INV-84 index mutant was planted in a copy of the index (`GIT_INDEX_FILE`); the real index was
   not written by it.
6. The four tests this seat wrote were added to the worktree, shown green on `5cd6c88` and red on their
   mutants, then taken out by the inverse replacement. Their full text is under "Tests added this
   review", for the lead to commit.

## Verdict
PASS-WITH-MINORS

**Every closure fix holds, and each has a test that fails without it.** All ten "M18 closure"
mutation samples in `docs/security-invariants.md` are killed by the test the list names. `make
check-fast` passes at `5cd6c88`. No test line was weakened or deleted.

**Of 45 mutants, 33 die on the suite at `5cd6c88` and 12 survive.**
1. Four beat the new `make deps` tests: an audit whose failure make ignores, or that is not strict
   (**T2**).
2. Three beat the new venv check: `--upgrade-deps` on a continued line or in a make variable (**T3**).
   The release script's venv command is continued today.
3. Two beat INV-4's new test: a publish that deletes the live file first, and `shutil.move` (**T1**).
4. One beats every gap-register pin, the egress gate and `client-decls`: the view builds an
   unprotected store through an unapplied initialiser (**T4**).
5. Two are equivalent today: `os.replace` for `Path.replace` (D4), and the lift cleared before a
   contract test's fixtures are torn down (A6, **R1**).

The seat wrote a test for each of T1 to T4. With them, 43 of the 45 die; the two left are D4 and A6.
None of the survivors is a defect in shipped code: each is a spelling the new tests do not see.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `5cd6c88`. Mutant ids are defined under "Fault injection".

**Repo review M1: a live contract test steps out of the network guard on every thread**
(`tests/conftest.py:126-140`)
- `tests/unit/test_no_network.py:82` drives the two hookwrappers as pytest does; `:115` reads the rule
  from a worker thread. A1 (the lift set after the yield, M1's own shape), A2 (never cleared), A3 (the
  main thread only), A4 (`RUN_CONTRACT_TESTS` ignored) and A5 (the path ignored) are each killed.
- The probe, run by pytest with `RUN_CONTRACT_TESTS=1` ("reached" means the guard let the lookup
  through to the stub):

| Where the lookup runs | `a259ed0` conftest | `5cd6c88` conftest |
|---|---|---|
| a unit test before any contract test | refused | refused |
| a contract test's body | reached | reached |
| a contract module's module-scoped fixture | **refused** | reached |
| a worker thread in a contract test | **refused** | reached |
| a contract test's fixture, which then raises | reached | reached |
| a unit test after that contract test: its body, its module fixture, its worker thread | refused | refused |
| every case above, with `RUN_CONTRACT_TESTS` unset | refused | refused |

- So a non-contract test stays guarded after a contract test on the same worker, and the lift does not
  leak when a contract test's setup raises: pytest runs the teardown hook after a failed setup.
- A6 survives (**R1**).

**Repo review M2: the skip budget is 78** (`docs/skip-budget.txt`)
- Measured. The suite run in a `git archive` of `5cd6c88`, with no artifact, skips 78. That count holds
  one skip CI does not have ("needs a git checkout") and lacks the one Xcode-gated test, which runs on
  this Mac and skips in CI: 78 - 1 + 1 = 78. The archive run's 3 failures are `git ls-files` outside a
  checkout.
- The file's own parts add up (51 + 18 + 7 + 1 + 1), and this Mac skips 25 (18 + 7), as it says.

**Security S1, repo review M3: `make deps` audits every lock and fails closed with none**
(`Makefile:257`, `:264-265`)
- `tests/unit/test_dependency_locks.py:141` and `:152`. B1 (the pre-fix recipe, `pip_audit --strict .`),
  B3 (`build.lock` left out), B4 (`ingest.lock`, the pyarrow lock, left out), B2 (the guard removed) and
  B8 (the guard on the wrong variable) are each killed.
- The dry run expands to `.venv/bin/python -m pip_audit --strict --disable-pip -r requirements/build.lock
  -r requirements/dev.lock -r requirements/ingest.lock -r requirements/serve.lock`. The audit itself was
  not run: it needs PyPI.
- B5, B6, B7 and B9 survive (**T2**).

**Security S5: `make install`'s venv has no `--upgrade-deps`** (`Makefile:77`)
- `tests/unit/test_dependency_locks.py:119` and `:127`. C1 (the pre-fix line) and C6 (the flag on the
  release script's venv line) are each killed. C5 (`$(PIP) install --upgrade pip` before the locks) is
  killed by the older `test_every_install_reads_its_lock_and_resolves_nothing_else`.
- `requirements/dev.lock:859` pins pip with its hashes, so the bundled pip installs a locked pip, as
  D-177's amendment says. The scratch-venv check the commit message cites was not re-run (PyPI).
- C2, C3 and C4 survive (**T3**).

**Security S2: INV-4, a publish replaces the live file and never writes into it**
(`src/app/workflows/refresh.py:1260`)
- `tests/unit/test_refresh.py:2071`. D1 (the seat's R1, `shutil.copyfile`) is killed, and across the
  whole suite only by this test (1 failed, 1775 passed). D3 (a copy into a temporary file in another
  directory, then a rename) and D6 (the bytes written into the live file) are each killed.
- D3 is an atomic publish that the test refuses, since the live inode is not the candidate's. That is
  stricter than INV-4's words, and harmless.
- D2 and D5 pass the whole suite (**T1**). D4 (`os.replace`) is equivalent.

**Security S4: INV-74, the standings ceiling on the disk path** (`ios/ModelRanking/Engine/Models.swift:409`)
- `ios/EngineTests/StandingsStoreTests.swift:184` kills F1 (the seat's E6, the ceiling 64 times wider),
  F2 (no ceiling, E6b) and F4 (one byte wider). `:199` kills F3 (`<` for `<=`, a valid payload at the
  ceiling refused).
- The pre-fix test could not fail: F1 with `:184` put back to `Data(count: max + 1)` passes all 15
  `StandingsStoreTests` (F1o).

**Security S4: INV-33, the largest single answer bounds the boot** (`src/app/adapter/main.py:468`)
- `tests/unit/test_stage40_minors.py:82`. E1 (the seat's H4, the bound 1000 times wider) is killed, and
  across the whole suite only by this test (1 failed, 1775 passed). E2 (the bound + 1) and E3 (the
  bound - 1) are each killed.

**Security S3: INV-67, the view reaches the gap register only as `GapRegisterStore.onDevice`**
(`ios/ModelRanking/ContentView.swift:49`, `:630`, `:868`)
- `tests/unit/test_router_hints.py:708` and `:731`. G1 (the seat's V1) is killed by `:731`, and G2 (V2,
  a trailing-closure writer) by both, as the list says. G8 (a store built in a helper in
  `EngineClient.swift`) is killed by `:731`.
- G3 (`.init(`) and G4 (`let s: GapRegisterStore = .init(...)`) are killed by `:731` and by the egress
  gate at `:399`. G5, G6 (`type(of: GapRegisterStore.onDevice).init(...)`) and G7 (a type alias declared
  in `FrontDoor.swift`) pass both pins and are killed only by the egress gate's `.init(` and `typealias`
  patterns (`:477`, `:499`). All three compile: `client-decls` passes in its four configurations.
- G9 passes every test, the egress gate and `client-decls` (**T4**).

**Repo review M9: INV-84, no tracked symbolic link** (the tests are M18-W3's; the row is new)
- H1 (a link planted in a copy of the index) and H2 (the `.venv` line dropped from `.gitignore`) are
  each killed.

## Red-green on reported symptoms
- **M1.** `5cd6c88`'s `tests/unit/test_no_network.py` against `a259ed0`'s conftest: 2 failed (the two
  tests the fix changed or added), 5 passed. Against `5cd6c88`'s: 7 passed. That red is by missing
  names; the probe's table is the behaviour, refused at `a259ed0` and reached at `5cd6c88`.
- **M3 and S1.** B1 is the pre-fix recipe: red. `5cd6c88`: green.
- **S5.** C1 is the pre-fix line: red. `5cd6c88`: green.
- **S4.** F1o (the old test, green under E6) against F1 (the new test, red under E6). E1 is red, and only
  the new test turns it red.
- **S2 and S3.** No symptom: the shipped code renames, and the shipped view uses `.onDevice`. D1, G1
  and G2 show each new test can fail.
- **Weakened or deleted tests.** `git diff a259ed0..5cd6c88 -- tests ios/EngineTests conformance`
  removes three things, each replaced by a stronger one: the two zero-byte ceiling assertions (now a
  valid padded payload, both ways), the step-out test's fixture driver (now the hooks, plus a
  worker-thread test), and the writer pin's `"write:" in call` (now also a trailing closure).

## Suite
- **`make check-fast` at `5cd6c88`: PASS in 70.0 s**, six legs:
  `lint`; `typecheck`; `records` (`check-records`, `check-records-selftest`, `install-check`,
  `harvest-context-check`, `shell-dialect`, `wave-check-all`, `conformance`); `test` (pytest 1776
  passed, 25 skipped; `coverage-floor` PASS over 45 modules); `client-decls` (19 files in 4
  configurations); `swift-test` (462 tests, exactly the manifest).
- Run again at the end, with this record the only change in the tree: PASS in 49.4 s, the same counts.
- With the seat's four tests added: 1780 passed, 25 skipped, and `ruff check` clean.
- `make gate` was not run: it reaches PyPI.
- **Coverage on touched code.** The only production file the range changes is the `Makefile`. Of the
  code the new tests guard, `refresh.py:1261-1262`, the publish's `except OSError` branch, is
  uncovered; T1's test runs it.

## The records' claims about the code

| Claim | Holds? |
|---|---|
| `docs/security-invariants.md`, the ten "M18 closure" samples, each "killed" by the named test | Yes, all ten: H1, H2, B1, B2, D1, F1, E1, G1, G2 (both pins), C1. |
| The INV-4, INV-33, INV-67, INV-80, INV-81 and INV-84 rows cite these tests | Yes. Each named test exists and is green. |
| "72 rows. One has no test yet (INV-66). Eight more hold only in part. Six gaps are open" | Yes: 72 distinct rows; INV-66 has none; INV-6, -62, -63, -67, -76, -78, -81 and -82 are partial; G-1, G-2, G-3, G-5, G-7 and G-8 are open. |
| D-177's amendment: no `--upgrade-deps`, the locked pip installed; `make deps` audits the four locks | Yes. It keeps G-8 (the image's base by tag) open, as it says. |
| Security dispositions S1 to S5 "fixed `c256864`"; "V1 and V2 each fail a test"; "E6 killed"; "H4 killed" | Yes. Each new test is beaten by one more spelling: S1 by T2, S2 by T1, S3 by T4, S5 by T3. |
| Repo review M1 "fixed `d749403`; CI on #136 green, `live-contracts` included" | The mechanism: yes, by the probe. The CI run and the live contract tests were not re-run (network). |
| Repo review M2, the budget is 78 | Yes, measured. |

## Mocks / contract tests
- No integration or test double changed. The live contract tests were not run (they need the network);
  the step-out they rely on was proven with a stub in place of the real lookup.

## BLOCKING
- none

## MINOR (the author fixes each in this closure or files it as an issue)

- **T1** `src/app/workflows/refresh.py:1260`, INV-4 ("a publish is one atomic rename"): a publish that is
  not one rename passes every test.
   1. D2, `target.unlink(missing_ok=True)` then `candidate.rename(target)`, passes all 1776 tests. The new
      test (`tests/unit/test_refresh.py:2071`) sees the candidate's inode at the live path and the old
      bytes under an open reader, and both hold. Between the two steps there is no artifact, and a
      SIGALRM or SIGKILL there leaves none.
   2. D5, `shutil.move`, passes too. It renames until a rename fails, then copies into the live file:
      the torn publish S2 named.
   3. The publish's failure branch (`:1261-1262`) is uncovered.
   4. Remedy: commit `test_a_publish_whose_rename_fails_leaves_the_live_artifact_where_it_was` (below).
      It refuses the rename onto the live path and asserts the live file is still there, byte-identical,
      and nothing is published. It kills D1, D2, D5 and D6, and passes D3 and D4, the two atomic
      publishes.

- **T2** `Makefile:264-265`, INV-80: the new tests pin what `make deps` audits, not that the audit's
  verdict is make's.
   1. Each of these passes `tests/unit/test_dependency_locks.py`: B5, a `-` before the audit line (make
      ignores its failure, and `make -n` prints the line without the `-`); B6, `|| true` after it; B7,
      `--strict` dropped; B9, a guard that prints its message and goes on.
   2. `test_an_audit_with_no_lock_fails_closed` passes B9 because its `PY=false` audit fails anyway, so
      the exit status cannot tell the guard from the audit.
   3. Remedy: commit `test_the_audit_decides_make_deps` (below). `PY=false` must fail `make deps`;
      no lock with `PY=true`, an audit that passes, must fail it with the message; the audit line keeps
      `--strict`. It kills B2, B5, B6, B7, B8 and B9, and runs no audit.

- **T3** `tests/unit/test_dependency_locks.py:115-124`, INV-81 and S5: the venv check reads one physical
  line at a time.
   1. C3, `--upgrade-deps` on the next line of the release script's venv command, passes. That command
      is continued today (`scripts/install_engine_service.sh:121`), so this is the natural place for
      the flag to come back.
   2. C2 (the same in the `Makefile`) and C4 (`VENV_OPTS := --upgrade-deps`, then `-m venv $(VENV_OPTS)`)
      pass too. For both, `make -n` prints a venv command with `--upgrade-deps`.
   3. The older install check joins continued lines (`install_commands`); this one does not.
   4. Remedy: commit `test_no_venv_upgrade_hides_on_a_continued_line_or_in_a_variable` (below), or fold
      its two changes into the existing test: read the `Makefile`'s venv rule from make's dry run, and
      join continued lines. It kills C1, C2, C3, C4 and C6.

- **T4** `ios/ModelRanking/ContentView.swift:868`, INV-67 and S3: the view can still build its own,
  unprotected store with every gate green.
   1. G9 replaces the save at `:868` with
      `let make = type(of: GapRegisterStore.onDevice).init` and
      `make(GapRegisterStore.onDevice.url, [.atomic], GapRegisterStore.onDevice.write).save(gaps)`.
   2. The typed question is then written with `[.atomic]` only, without `.completeFileProtection`: V1
      spelled another way. It compiles in all four `client-decls` configurations, and all 1776 tests
      pass.
   3. Why each gate passes: the name is always followed by `.onDevice` (the new pin); no
      `GapRegisterStore(` is written (the writer pin); the initialiser is never applied as `.init(`,
      and no `write(` call is written (the egress gate).
   4. The control: a type error at the same line fails `client-decls` (Z0), so G9 compiled.
   5. Remedy: commit `test_the_view_only_loads_and_saves_the_on_device_store` (below). Outside
      `FrontDoor.swift`, `GapRegisterStore` may only be followed by `.onDevice.load(` or
      `.onDevice.save(`. It kills G1 to G9. The structural fix the security seat offered also holds:
      one save function in `FrontDoor.swift` that the view calls, and nothing else.

## Improvements to file and risks

- **K1** `tests/unit/test_router_hints.py:477`: the egress gate refuses `.init(` but not an unapplied
  `.init`. G9 uses one; T4's test closes it for the gap register only. Belongs with G-3's holes (#107):
  refuse `type(of:` and an `.init` that is not followed by `(` in the client, or name the unapplied
  form in G-3.

- **R1** `tests/conftest.py:138-140`: clearing the lift before the yield, so a contract test's fixtures
  are torn down under the guard (A6), passes every test and the probe.
   1. It matters only for a fixture that reaches out while it tears down. None does today.
   2. The conftest's own comment says the lift is "cleared after". No test holds the order.

- **R2** `tests/conftest.py:128`: `"integration" in Path(str(path)).parts` reads the absolute path.
   1. With `RUN_CONTRACT_TESTS=1`, a checkout under any folder named `integration` lifts the guard for
      every test: `is_live_contract_test` answers True for
      `/home/ci/integration/model_ranking/tests/unit/test_api_v1.py`.
   2. The rule is unchanged from `a259ed0`, and it bites only in a run that already reaches the network.
      Reading the path relative to the rootdir closes it.

## Fault injection

Hashes are the first 12 hex digits of sha256. "Restored" is the hash after the original bytes were
written back, equal in every row to the hash before the mutation. "Suite" is the whole pytest suite
(`-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`). "Seat test" names which of this seat's four tests
kills the mutant (the suite with them added).

| Id | File:line | Mutation | Run against | Result at `5cd6c88` | Seat test | Restored |
|---|---|---|---|---|---|---|
| A1 | `conftest.py:133` | the lift set after the yield (M1's shape) | `test_no_network.py`, probe | RED: `:82`; probe: module fixture refused | n/a | `24c883126c01` |
| A2 | `conftest.py:140` | the lift never cleared | same | RED: `:82` (left lifted); probe unchanged | n/a | `24c883126c01` |
| A3 | `conftest.py:63` | the lift honoured on the main thread only | same | RED: `:115`; probe: worker refused | n/a | `24c883126c01` |
| A4 | `conftest.py:128` | `RUN_CONTRACT_TESTS` ignored | `test_no_network.py` | RED: `:82` | n/a | `24c883126c01` |
| A5 | `conftest.py:128` | the path ignored | same, probe | RED: `:82`, `:115`; probe: unit tests reach out | n/a | `24c883126c01` |
| A6 | `conftest.py:139-140` | the lift cleared before the yield | same, probe | **GREEN** (**R1**) | survives | `24c883126c01` |
| B1 | `Makefile:265` | `pip_audit --strict .` (the pre-fix recipe; closure #3) | `test_dependency_locks.py` | RED: `:141` | n/a | `f543bbde2add` |
| B2 | `Makefile:264` | the no-lock guard removed (closure #4) | same | RED: `:152` | T2 | `f543bbde2add` |
| B3 | `Makefile:257` | `build.lock` filtered out | same | RED: `:141` | n/a | `f543bbde2add` |
| B4 | `Makefile:257` | `ingest.lock` filtered out | same | RED: `:141` | n/a | `f543bbde2add` |
| B5 | `Makefile:265` | `-` before the audit line | same | **GREEN** (**T2**) | T2 | `f543bbde2add` |
| B6 | `Makefile:265` | `\|\| true` after the audit | same | **GREEN** (**T2**) | T2 | `f543bbde2add` |
| B7 | `Makefile:265` | `--strict` dropped | same | **GREEN** (**T2**) | T2 | `f543bbde2add` |
| B8 | `Makefile:264` | the guard tests `$(PY)` | same | RED: `:152` | T2 | `f543bbde2add` |
| B9 | `Makefile:264` | the guard prints, then `true` | same | **GREEN** (**T2**) | T2 | `f543bbde2add` |
| C1 | `Makefile:77` | `-m venv --upgrade-deps` (the pre-fix line; closure #10) | same; `make -n` | RED: `:119[Makefile]` | T3 | `f543bbde2add` |
| C2 | `Makefile:77` | `--upgrade-deps` on a continued line | same; `make -n` shows it | **GREEN** (**T3**) | T3 | `f543bbde2add` |
| C3 | `install_engine_service.sh:121` | `--upgrade-deps` on a continued line; `bash -n` parses | same | **GREEN** (**T3**) | T3 | `235000318551` |
| C4 | `Makefile:75-77` | `VENV_OPTS := --upgrade-deps`, used on the venv line | same; `make -n` shows it | **GREEN** (**T3**) | T3 | `f543bbde2add` |
| C5 | `Makefile:83` | `$(PIP) install --upgrade pip` before the locks | same | RED: `test_every_install_reads_its_lock_and_resolves_nothing_else` | n/a | `f543bbde2add` |
| C6 | `install_engine_service.sh:121` | `-m venv --upgrade-deps` on the release's venv line | same | RED: `:119[...sh]` | T3 | `235000318551` |
| D1 | `refresh.py:1260` | `shutil.copyfile(candidate, target)` (the seat's R1; closure #5) | refresh files; suite | RED: `:2071`, the only failure in the suite | T1 | `6f2718148f4c` |
| D2 | `refresh.py:1260` | `target.unlink()`, then `candidate.rename(target)` | refresh files; suite | **GREEN**, 1776 passed (**T1**) | T1 | `6f2718148f4c` |
| D3 | `refresh.py:1260` | copy to a temporary file in another directory, then rename | refresh files | RED: `:2071` (inode) | passes (atomic) | `6f2718148f4c` |
| D4 | `refresh.py:1260` | `os.replace(candidate, target)` | refresh files | GREEN: equivalent | passes | `6f2718148f4c` |
| D5 | `refresh.py:1260` | `shutil.move(candidate, target)` | refresh files | **GREEN** (**T1**) | T1 | `6f2718148f4c` |
| D6 | `refresh.py:1260` | `target.write_bytes(candidate.read_bytes())` | refresh files | RED: `:2071` | T1 | `6f2718148f4c` |
| E1 | `main.py:468` | the single-answer bound x1000 (the seat's H4; closure #7) | `test_stage40_minors.py`; suite | RED: `:82`, the only failure in the suite | n/a | `6fc1349ab67c` |
| E2 | `main.py:468` | the bound + 1 | same | RED: `:82` (no refusal) | n/a | `6fc1349ab67c` |
| E3 | `main.py:468` | the bound - 1 | same | RED: `:82` (refused at the bound) | n/a | `6fc1349ab67c` |
| F1 | `Models.swift:409` | the ceiling x64 (the seat's E6; closure #6) | `swift test --filter StandingsStoreTests` | RED: `:184` | n/a | `c5cbf0204bcb` |
| F1o | as F1, plus `StandingsStoreTests.swift:186` put back to `Data(count:)` | the pre-fix test under E6 | same | GREEN, 15 tests: the old test could not fail | n/a | `c5cbf0204bcb`, `6373c8ff4976` |
| F2 | `Models.swift:409` | no ceiling (E6b) | same | RED: `:184` | n/a | `c5cbf0204bcb` |
| F3 | `Models.swift:409` | `<` for `<=` | same | RED: `:199` | n/a | `c5cbf0204bcb` |
| F4 | `Models.swift:409` | the ceiling + 1 | same | RED: `:184` | n/a | `c5cbf0204bcb` |
| G1 | `ContentView.swift:868` | `GapRegisterStore(url: GapRegisterStore.onDevice.url).save` (V1; closure #8) | `test_router_hints.py -k gap_register` | RED: `:731` | T4 | `e3aaf221f87f` |
| G2 | `ContentView.swift:630` | the same with a trailing `{ _, _ in }` (V2; closure #9) | same | RED: `:708`, `:731` | T4 | `e3aaf221f87f` |
| G3 | `ContentView.swift:868` | `GapRegisterStore.init(url: ...)` | same | RED: `:399`, `:731` | T4 | `e3aaf221f87f` |
| G4 | `ContentView.swift:868` | `let s: GapRegisterStore = .init(url: ...)` | same | RED: `:399`, `:731` | T4 | `e3aaf221f87f` |
| G5 | `ContentView.swift:868` | `type(of: GapRegisterStore.onDevice).init(url: ...)` | same; suite; `client-decls` | RED: `:399` only; compiles | T4 | `e3aaf221f87f` |
| G6 | `ContentView.swift:630` | G5 with a trailing-closure writer | same; `client-decls` | RED: `:399` only; compiles | T4 | `e3aaf221f87f` |
| G7 | `FrontDoor.swift:277`, `ContentView.swift:868` | `typealias QuestionLog = GapRegisterStore` at home; `QuestionLog(url: ...)` in the view | same; `client-decls` | RED: `:399` only; compiles | T4 | `8ec9c9a549bb`, `e3aaf221f87f` |
| G8 | `EngineClient.swift:187`, `ContentView.swift:868` | a `plainGapStore` helper in another file | same | RED: `:731` | T4 | `d07fbe7bb673`, `e3aaf221f87f` |
| G9 | `ContentView.swift:868` | an unapplied `type(of:).init`, called with `[.atomic]` and the on-device writer | all of `test_router_hints.py`; suite; `client-decls` | **GREEN**: 1776 passed, compiles (**T4**) | T4 | `e3aaf221f87f` |
| Z0 | `ContentView.swift:868` | control: `.save(42)`, a type error | `client-decls` | RED: it fails to compile, so `client-decls` type-checks the view | n/a | `e3aaf221f87f` |
| H1 | the index (a copy, through `GIT_INDEX_FILE`) | a `120000` entry planted, then removed (closure #1) | `test_no_tracked_links.py` | RED: `test_no_symbolic_link_is_tracked`; green once removed | n/a | real index `ff31a2eeefe93526` before and after |
| H2 | `.gitignore:4` | the `.venv` line dropped (closure #2) | same | RED: `test_the_ignore_file_catches_a_venv_link_too` | n/a | `f322fad8debe` |

**Score.** 45 mutants (F1o and Z0 are controls). 33 are RED at `5cd6c88`; 12 survive, of which D4 is
equivalent and A6 is harmless today. With the seat's four tests: 43 RED; D4 and A6 left.

## Tests added this review

Each was added to the worktree, run green on `5cd6c88` (the whole suite: 1780 passed, 25 skipped;
`ruff check` clean), run red on the mutants in its row above, and then taken out again, so the
closure's tree is unchanged. Each goes at the end of the file named, or where stated.

**T1**: `tests/unit/test_refresh.py`, at the end (it uses the file's `os`, `pytest`, `Path`, `_artifact`,
`refresh` and `EXIT_FAILED`). It kills D1, D2, D5 and D6.

```python
def test_a_publish_whose_rename_fails_leaves_the_live_artifact_where_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV-4, "a publish is one atomic rename" (the M18 closure Tester's T1).

    Deleting the live file and then renaming the candidate in passed every test, the one above
    included: the live path ends as the candidate's inode, and an open reader keeps the old bytes.
    Between the two steps there is no artifact, and a kill there (SIGALRM at 27 minutes, SIGKILL at
    30) leaves none. Here the rename onto the live path fails, as a full disk or a kill would stop
    it: the live file is still there, byte-identical, and nothing is published.
    """
    live = _artifact(tmp_path / "advisor.db", top_score=74.5)
    before = live.read_bytes()
    refused: list[str] = []

    def refusing(real):  # type: ignore[no-untyped-def]
        def move(src, dst, *args, **kwargs):  # type: ignore[no-untyped-def]
            if os.path.realpath(dst) == os.path.realpath(live):
                refused.append(str(src))
                raise OSError("the test refuses the rename onto the live artifact")
            return real(src, dst, *args, **kwargs)
        return move

    monkeypatch.setattr(os, "replace", refusing(os.replace))
    monkeypatch.setattr(os, "rename", refusing(os.rename))

    def building(argv: list[str]) -> int:
        _artifact(Path(argv[argv.index("--db") + 1]), top_score=75.5)
        return 0

    outcome, code = refresh(live, builder=building)

    assert refused, "the candidate was never renamed onto the live path"
    assert live.is_file(), "the live artifact was gone when the publish failed"
    assert live.read_bytes() == before, "a publish that failed changed the live artifact"
    assert code == EXIT_FAILED and not outcome.published, outcome.reason
```

**T2 and T3**: `tests/unit/test_dependency_locks.py`, after `test_an_audit_with_no_lock_fails_closed`
(they use the file's `_make`, `UNLOCKED_UPGRADE`, `ROOT` and `Path`). T2's test kills B2, B5, B6, B7, B8
and B9; T3's kills C1, C2, C3, C4 and C6.

```python
def test_the_audit_decides_make_deps() -> None:
    """The M18 closure Tester's T2. The two tests above read what is audited, and that no lock
    stops the target. Neither reads that the audit's verdict is make's: a `-` before the audit
    line, `|| true` after it, `--strict` dropped, or a guard that prints its message and goes on
    each passed both. `PY=false` is an audit that fails and `PY=true` one that passes; neither
    runs pip-audit, so nothing is fetched."""
    failed = _make("PY=false", "deps")
    assert failed.returncode != 0, "an audit that failed left `make deps` green: " + failed.stdout + failed.stderr
    empty = _make("LOCKS=", "PY=true", "deps")
    assert empty.returncode != 0 and "no lock under requirements/" in empty.stdout, (
        "no lock, and an audit of nothing passed: " + empty.stdout + empty.stderr)
    audits = [line for line in _make("-n", "deps").stdout.splitlines() if "pip_audit" in line]
    assert len(audits) == 1 and "--strict" in audits[0].split(), audits


def test_no_venv_upgrade_hides_on_a_continued_line_or_in_a_variable(tmp_path: Path) -> None:
    """The M18 closure Tester's T3. `test_no_venv_upgrades_pip_before_the_locks` reads one line at a
    time, so `--upgrade-deps` on the next line of a continued command passed it, in the Makefile and
    in the release script, whose venv command is continued today; so did a make variable holding
    it. The Makefile's venv rule is read here from make's own dry run, expanded, and each file with
    its continued lines joined."""
    venv = tmp_path / "venv"  # named, never made: a dry run
    run = _make("-n", f"VENV={venv}", f"{venv}/pyvenv.cfg")
    assert run.returncode == 0 and "-m venv" in run.stdout, run.stdout + run.stderr
    assert not UNLOCKED_UPGRADE.search(run.stdout.replace("\\\n", " ")), run.stdout
    for path in ("Makefile", "scripts/install_engine_service.sh", "Dockerfile"):
        code = "\n".join(line for line in (ROOT / path).read_text(encoding="utf-8").splitlines()
                         if not line.lstrip().startswith("#"))
        assert not UNLOCKED_UPGRADE.search(code.replace("\\\n", " ")), f"{path} upgrades pip outside the locks"
```

**T4**: `tests/unit/test_router_hints.py`, at the end (it uses the file's `pathlib`, `re` and `_code`). It
kills G1 to G9.

```python
def test_the_view_only_loads_and_saves_the_on_device_store() -> None:
    """The M18 closure Tester's T4 (INV-67). The pin above reads the name before `.onDevice`, not
    what follows it. `let make = type(of: GapRegisterStore.onDevice).init`, then
    `make(GapRegisterStore.onDevice.url, [.atomic], GapRegisterStore.onDevice.write).save(gaps)`,
    builds a store with no file protection (V1 spelled another way). It compiled in all four
    `client-decls` configurations and passed every test: the name is always followed by
    `.onDevice`, the initialiser is never applied by name, and no `write(` call is written. Outside
    `FrontDoor.swift`, the store is only ever `GapRegisterStore.onDevice.load()` or `.save(`."""
    root = pathlib.Path(__file__).resolve().parents[2]
    app = root / "ios" / "ModelRanking"
    home = app / "Engine" / "FrontDoor.swift"
    uses, other = 0, []
    for path in sorted(app.rglob("*.swift")):
        if path == home:
            continue
        code = _code(path.read_text(encoding="utf-8"))
        for match in re.finditer(r"\bGapRegisterStore\b", code):
            uses += 1
            if not re.match(r"\s*\.\s*onDevice\s*\.\s*(?:load|save)\s*\(", code[match.end():]):
                line = code.count("\n", 0, match.start()) + 1
                other.append(f"{path.relative_to(root)}:{line}: {code[match.start():match.start() + 70]!r}")
    assert uses, "the view names the gap register nowhere; was it read?"
    assert not other, f"the view does more with the gap register than load and save it: {other}"
```

If the lead commits them, INV-4's, INV-80's, INV-81's and INV-67's rows in
`docs/security-invariants.md` should cite them.

## Clean-up evidence
- Every mutant's restore matched its pre-mutation sha256 (the "Restored" column).
- After the last mutant and after the seat's tests were taken out, `git hash-object` equals
  `git rev-parse HEAD:<path>` for each of the 14 files the seat touched: `tests/conftest.py`,
  `Makefile`, `scripts/install_engine_service.sh`, `src/app/workflows/refresh.py`,
  `src/app/adapter/main.py`, `ios/ModelRanking/Engine/Models.swift`,
  `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/FrontDoor.swift`,
  `ios/ModelRanking/Engine/EngineClient.swift`, `ios/EngineTests/StandingsStoreTests.swift`,
  `.gitignore`, `tests/unit/test_refresh.py`, `tests/unit/test_dependency_locks.py` and
  `tests/unit/test_router_hints.py`.
- The worktree's index was not written by the H1 plant: it hashed `ff31a2eeefe93526` before and right
  after it. Later `git status` runs refreshed its stat cache (the mutants had changed file times), so
  the file's hash moved, but its entries did not: `git diff --cached` is empty, no `120000` entry
  exists, and `git ls-files -s` hashes the same as `HEAD`'s tree listing (`eb2027a7d4f4`).
- The artifact copy `advisor.db` still hashes `6b3e80f2cb154bcd...`.
- `git status --short` shows this file alone: `?? docs/reviews/m18-closure-tester.md`.
- Nothing was committed.

## Dispositions, at the closure

Written by the lead agent after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed `6836a48`: the seat's test, committed; D2 shown red by the lead too |
| T2 | fixed `6836a48`: the seat's test, committed; B6 shown red by the lead too |
| T3 | fixed `6836a48`: the seat's test, committed |
| T4 | fixed `6836a48`: the seat's test, committed |
| K1 | #107 (gap G-3), commented with the unapplied `.init` form |
| R1 | fixed `6836a48`: the step-out test holds the order (A6 red) |
| R2 | fixed `6836a48`: the rule reads the path from the repository down, with a test (red on the old rule); the live Epoch contract tests still pass |
