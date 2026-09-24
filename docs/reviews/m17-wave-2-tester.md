---
record_type: review
id: m17-wave-2-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---
# Wave 2 Tester Review (m17): Arena's category slices become boards

**Reviewer:** Tester subagent. Fresh eyes: I wrote none of this wave's code and none of its reviews.
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** `04e263025df29d3266e1be29d21c8be09042dc56..8a6a260` (28 commits, issue #22, PR #23)
**Risk tier:** MEDIUM (`docs/plans/m17-wave-2-plan.md:11`)

**Inputs I read:**
- the plan (`docs/plans/m17-wave-2-plan.md`: phases P1-P4, decisions 1-7), the milestone plan
  (`docs/plans/m17-plan.md` §2 W2) and issue #22;
- D-164 and D-165 (`docs/decisions.md:2983`, `:3013`) and the research record
  (`docs/research/m17-w2-slice-survey-2026-09-24.md`);
- the last code re-review (`m17-wave-2-rereview-3.md`, PASS-WITH-MINORS; not BLOCKING, so this seat
  runs).

I read my policy from the base: `.claude/agents/Tester.md`, `.agents/rules/practices.md`,
`.agents/rules/review-seats.md` and `permission-matrix.md` §11. The diff does not touch any of them.

**Method:**
- **Suite.** I ran `make check-fast` and then the full suite myself.
- **Coverage.** I compared coverage on the touched modules with a run of the base commit from
  `git archive`.
- **Red replay.** I replayed all nine red commits against their fix commits, each from `git archive`
  in my scratchpad.
- **Fault injection.** I ran 26 faults in place (`scratchpad/tester_w2/faults.py`).
- **Network.** Every pytest process I started loaded a tripwire plugin
  (`scratchpad/tester_w2/netblock_tester.py`). The same applies to every xdist worker, which I
  checked. The plugin refuses and logs every non-loopback `connect` and every DNS lookup of a
  non-local name. I also checked that it fires on a real lookup.
- **What I did not do.** I did not run the env-gated contract tests locally
  (`RUN_CONTRACT_TESTS` unset). No `os.abort()` ran: the one red commit that carried it
  (`ed0c840`) failed before starting the child. No new `Python-*.ips` crash report appeared in
  `~/Library/Logs/DiagnosticReports` during my work.

## Verdict
PASS-WITH-MINORS: 0 BLOCKING, 2 MINOR, 0 K.9, 0 risks queued.

Every acceptance criterion of P1-P4, and every clause of D-164 and D-165, has a test that exercises
it and is green. For 25 of the 26 faults I injected, a test goes red. I read each red to check that
it is the named behaviour failing, not a setup error.

**One fault stays green (T1).** The parent can read the reader's whole answer before it checks the
size. With that change the suite still passes, only 20 s slower.
- The test added in `156d2f4`/`a73c079` was meant to close re-review 3's MINOR-R3-1. It does not
  catch this fault, so MINOR-R3-1 is still open.
- A one-line remedy exists. I checked that it passes at HEAD and goes red under the fault.

**No citing test for the smoke-deps probe (T2).** The plan's new `smoke_deps` slice probe (P4) has
no citing test. I exercised it by hand, offline.

Neither finding is a behaviour fault at HEAD, and the suite reached no network.

## Acceptance-criterion coverage (REQUIRED)

The project cites criteria in test and module docstrings (issue, D-id, plan item), not in
`# covers` comments. Only `tests/unit/test_health.py:18` uses that form. So a "citing test" here is
a test whose docstring or module docstring names #22, D-164/D-165 or the review item.

**Red** means the replay of the red commit failed on that test. **Fault** means an injected fault
turned it red (fault ids are in the next section). Unless a row says otherwise, the test file is
`tests/unit/test_arena_slices.py` (P1, D-165), `tests/unit/test_build_slices.py` (P2) or
`tests/unit/test_refresh_boards.py` (P3), as each section names.

### P1: the read (`tests/unit/test_arena_slices.py`)

| Criterion | Citing test | Proof | State |
|---|---|---|---|
| A small parquet yields each declared slice's rows, and `overall` is not one of them | `:60` | red at `48cb481` | GREEN |
| Newest-date rule per slice (decision 2, FP-M2-2) | `:80`, `:484`, `:495` | F4 turns all three red | GREEN |
| A file over the cap is cut off (decision 7, 8 MB) | `:569` (respx) | F9 red | GREEN |
| A file that is not parquet is a `SourceError` | `:509` | red at `48cb481` | GREEN |
| A missing column is a `SourceError` | `:515` (×4) | red at `48cb481` | GREEN |
| An `Infinity`, NaN or out-of-band rating is refused and counted | `:103` (×4) | red at `48cb481` | GREEN |
| The serving process does not import `pyarrow` (decision 6, D-154) | `:653` (server and module) | F8 red | GREEN |
| `ARENA_SLICES` and `ARENA_SLICE_CLIENT` are declared, so the registry mirror accepts the client | `tests/unit/test_sources.py:46` | the mirror test refuses an undeclared client | GREEN |

### P2: the boards (`tests/unit/test_build_slices.py`)

| Criterion | Citing test | Proof | State |
|---|---|---|---|
| No slice's rows reach `assistant` or `vision` (no served benchmark) | `:56` | F7 red | GREEN |
| One slice under its floor fails alone | `:80` | F5 red | GREEN |
| A failed download fails its config's slices and no other | `:116` | F6 red | GREEN |
| Each failed slice carries on its own clock (D-156, D-164 c4) | `:128` | F6 red | GREEN |
| Every board has a distinct benchmark label and source id (decision 3) | `tests/unit/test_arena_slices.py:624` | F7 red | GREEN |
| `floor < measured` for every board (decision 4) | `tests/unit/test_arena_slices.py:636` | table assertion over all 35 | GREEN |
| A slice far over its measured size fails alone (4× ceiling, S-R3-5) | `:98` | F15 red | GREEN |
| Attribution is derived from the table (CC-BY) | `:182`, `tests/unit/test_categories.py:223` | F16 red (both) | GREEN |
| The table is the owner's 35 boards, and the left-out slices stay out | `tests/unit/test_arena_slices.py:603`, `:611`; `:176` | table assertions | GREEN |
| `build()` reads the slice table at call time (the seam reaches the caller) | `:154` | red at `7b29be5` | GREEN |
| A hostile file fails its slices, never the build | `:193` | F6 red | GREEN |
| Slice rows do not crowd the unmatched-names queue (review K2) | `:218` | F20 red | GREEN |

### P3: published and guarded, D-164 (`tests/unit/test_refresh_boards.py`, through the real `refresh`)

| Criterion | Citing test | Proof | State |
|---|---|---|---|
| A candidate that changes only a board publishes (c1) | `:68` | F1 red | GREEN |
| The fingerprint moves with a board's standings and model, not with a re-stamp or a sub-rounding move (c1, D-109) | `:79` | F1, F24, F25 red | GREEN |
| A board that loses a quarter of its names is refused (c2, D-128) | `:114` | F2 red | GREEN |
| A board whose names are a quarter new is refused (c2, D-132) | `:126` | F3 red | GREEN |
| A board seen for the first time is not refused (c3) | `:101` | F23 red | GREEN |
| Ordinary movement publishes | `:137` | F1 red | GREEN |
| An expired board drops rather than freezing the artifact (c4, D-156) | `:147` | red at `9b92171` | GREEN |

### P4: measured and recorded

| Criterion | Citing test / evidence | Proof | State |
|---|---|---|---|
| `survey_boards.py --slices` measures each slice on a COPY and reports the ranked population | `tests/unit/test_survey_floors.py:121` | red at `376577f`; the record is `docs/research/m17-w2-slice-survey-2026-09-24.md` (35 boards, 316 models before and after) | GREEN |
| `smoke_deps` gains one probe per config | **none in the suite** | exercised by hand, see T2 | MINOR T2 |
| The `agent_*` configs are filed | issue #24 (open) | not a test criterion | done |
| D-164 accepted by the owner | `docs/decisions.md:2985` (status: accepted) | not a test criterion | done |

### D-165: the reader in a process of its own (`tests/unit/test_arena_slices.py`)

| Clause | Citing test | Proof | State |
|---|---|---|---|
| c1: the child stops at its memory ceiling | `:433` (committed `ceiling.parquet`) | F10 red | GREEN |
| c1: the parent stops a reader past `READER_TIMEOUT_S` | `:423` | F14 red | GREEN |
| c2: a crash (SIGKILL), a nonzero exit, garbage, a bad row shape, a missing or wrong end line are each a `SourceError` | `:252` (×6) | F11 red | GREEN |
| c2: a reader that cannot start, or a missing TMPDIR, is a `SourceError` | `:303`, `:311` | red at `156d2f4` (`:311`) | GREEN |
| c3: types, footer, rows as read, value length and decode budget are first refusals | `:151`, `:521`, `:534`, `:450`, `:464`, `:472`; in-process protocol `:176` | F19 red (`:151`, `:176`) | GREEN |
| c4: an answer over `MAX_ANSWER_BYTES` is refused | `:259`, `:269` | F26 red (both) | GREEN |
| c4: the parent never holds the answer whole (the capped read) | `:269` claims it | **F13 stays green**, see T1 | MINOR T1 |
| c4: only stderr's tail is quoted, and it is printable | `:282` | F11 red | GREEN |
| c4: a quoted reason is at most 200 printable characters | `:372` | red at `9cf081f` | GREEN |
| c4: the reader's environment is allowlisted | `:383` | F12 red | GREEN |
| c4: `-P` means a planted `pyarrow.py` is not imported | `:393` | F21 red | GREEN |
| c4: the Linux peak comes from `VmHWM` and fails closed | `:208`, `:347`, `:326` (×4) | red at `9cf081f`/`156d2f4` | GREEN |
| c4: an orphaned reader stops itself (SIGALRM) | `:404` | red at `9cf081f` | GREEN |
| A name with U+2028, U+2029 or U+0085 is read whole | `:294` | red at `156d2f4` | GREEN |

## Red→green on reported symptoms

I replayed every red commit against its fix, from `git archive` into my scratchpad, with the network
tripwire loaded:

| Red → fix | Red at the red commit | Green at the fix |
|---|---|---|
| `48cb481` → `511e2b1` | collection error (no module) | 23 passed |
| `55e2f19` → `42de70d` | 2 failed | 26 passed |
| `7b29be5` → `ebf0981` | 9 failed | 50 passed |
| `9b92171` → `ab98437` | 7 failed; the P3 reds read "nothing a user would notice changed", the exact pre-D-164 symptom | 7 passed |
| `376577f` → `bc7e43d` | 1 failed | 7 passed |
| `ac7bf89` → `0b7a535` | 13 failed | 60 passed |
| `ed0c840` → `18382b8` | 10 failed | 58 passed |
| `9cf081f` → `effdb04` | 9 failed | 57 passed, 7 skipped |
| `156d2f4` → `a73c079` | 5 failed | 79 passed |

- **One red test reached for the network, and the tripwire stopped it.** At `ac7bf89`,
  `test_a_marked_test_that_injects_no_client_cannot_reach_the_network` reached `huggingface.co`.
  The tripwire refused the lookup before any DNS query left the machine. That test was the red for
  a real hole (the build's default client was unguarded), which `18382b8` closed with the
  client-level guard in `tests/conftest.py:75`. No other replay made an attempt.
- **Two tests added as reds were green at their own red commit:** `:269` and `:282`, both from
  `156d2f4`. They answer a missing test for mechanisms that already existed, so a real red was only
  possible by fault injection:
  - `:282` goes red under F11;
  - `:269` does not go red under the fault it names (F13). See T1.

## Suite result

- **`make check-fast`:** PASS in 52.7 s. All six legs passed: lint, typecheck, records, test,
  client-decls and swift-test. The test leg: `1318 passed, 17 skipped`. `coverage-floor PASS: 38
  module(s), floor 60%, 1 exempt`.
- **Full suite under the tripwire** (`pytest -n auto -p netblock_tester`,
  `MODEL_RANKING_REQUIRE_ARTIFACT=1`): `1318 passed, 17 skipped, 288 warnings in 10.54s`. The attempt
  log was never created: **0 outbound connection attempts, 0 DNS lookups**.
  - The tripwire covers the pytest processes. It does not cover the children the suite starts
    (the slice reader and the `pyarrow`-probe subprocesses). None of those opens a socket: the reader
    reads its file from stdin (`parquet_reader.py:171`).
- **CI at `8a6a260`** (`gh pr checks 23`): every check passes.
  - `test (py3.12)`: 1269 passed, 66 skipped. That is the same 1,335 tests; the 49 artifact-gated
    tests (W-108) skip on CI and run locally.
  - `live-contracts`: 19 passed, including
    `test_every_declared_slice_satisfies_the_parser_contract[text]` and `[vision]`.
- **Coverage on touched code, base `04e2630` → HEAD** (line coverage; branch coverage is on):

| Module | Base | HEAD |
|---|---|---|
| `arena.py` | 90.3% | 92.3% |
| `build.py` | 93.9% | 94.5% |
| `refresh.py` | 95.8% | 95.9% |
| `rank.py` | 93.6% | 93.7% |
| `sources.py` | 100% | 100% |
| `protocols.py` | 100% | 100% |
| `fakes.py` | 100% | 100% |
| `arena_slices.py` (new) | n/a | 98.5% |
| `parquet_reader.py` (new) | n/a | 87.5% |

- No touched module drops.
- `parquet_reader.py` is measured in process only. Its unmeasured lines (for example `:88-89`,
  `:97-98`, `:164`) run in the child process, and F10 and F19 show that tests exercise them there.

## Fault injection (in place, byte-identical)

Protocol, one atomic sequence per fault, scripted in `scratchpad/tester_w2/faults.py`:
1. Read the file's bytes and SHA-256.
2. Assert the pattern occurs exactly once, and apply the fault.
3. Run the named tests with the tripwire.
4. Write the original bytes back in a `finally` block.
5. Recompute the SHA-256 and compare.

All 26 faults came back **byte-identical**. `git status --porcelain` was empty before and after
every batch. No `git checkout` and no `git restore` was used.

| Id | Fault | Result |
|---|---|---|
| F1 | the fingerprint skips slice standings (`refresh.py:473`) | RED: `:68`, `:79`, `:137` |
| F2 | the board loss guard is off (`refresh.py:277`) | RED: `:114` |
| F3 | the board new-names guard is off (`refresh.py:221`) | RED: `:126` |
| F4 | the newest-date filter is off (`arena_slices.py:364`) | RED: `:80`, `:484` ×4, `:495` |
| F5 | the per-slice floor is off (`build.py:461`) | RED: build `:80` |
| F6 | a failed download silently skips its slices (`build.py:455`) | RED: build `:116`, `:128`, `:193` |
| F7 | slices share `Arena <config>` as their label (`arena_slices.py:129`) | RED: `:624`, build `:56` |
| F8 | `import pyarrow` at module level (`arena_slices.py:39`) | RED: `:653` ×2 |
| F9 | the 8 MB cap is removed, leaving the 32 MiB default (`arena_slices.py:208`) | RED: `:569` |
| F10 | the watchdog is never started (`parquet_reader.py:164`) | RED: `:433` |
| F11 | a nonzero reader exit is read as success (`arena_slices.py:281`) | RED: `:252` ×2, `:282` |
| F12 | the reader inherits the whole environment (`arena_slices.py:101`) | RED: `:383` |
| **F13** | **the parent reads the answer unbounded (`arena_slices.py:259`: `read(MAX_ANSWER_BYTES + 1)` → `read()`)** | **STAYED GREEN: 68 passed in 25.2 s against 5.2 s. See T1.** |
| F14 | the parent's timer is never started (`arena_slices.py:252`) | RED: `:423` |
| F15 | the 4× slice ceiling is off (`build.py:465`) | RED: build `:98` |
| F16 | the slices are unattributed (`rank.py:65`) | RED: build `:182`, `test_categories.py:223` |
| F17 | the future-date horizon is off (`arena_slices.py:341`) | RED: `:495` |
| F18 | an undated file is served (`arena_slices.py:342`) | RED: `:113` |
| F19 | the column type check is off (`parquet_reader.py:108`) | RED: `:151` ×4, `:176` and 2 more |
| F20 | slice rows are counted in the unmatched queue (`build.py:338`) | RED: build `:218` |
| F21 | `-P` is dropped from the reader command (`arena_slices.py:97`) | RED: `:393` |
| F22 | the conftest client guard is off (`tests/conftest.py:75`) | RED: `:588` |
| F23 | a first-seen board is refused as new (`refresh.py:156`) | RED: refresh `:101` |
| F24 | the fingerprint reads the raw score, not the D-109 rounding | RED: refresh `:79` |
| F25 | the fingerprint ignores the reconciled model | RED: refresh `:79` |
| F26 | the answer length check is removed (`arena_slices.py:260`) | RED: `:259`, `:269` |

**Why F13 stays green.** With `read()` unbounded, the parent reads until the 20 s timer kills the
endless reader. Then the unchanged length check raises the same reason, "the reader's answer passed
10000 bytes and was cut off". Meanwhile the parent held everything the reader wrote in those 20 s,
which is the memory D-165 clause 4 exists to bound. `:269` asserts only the reason, which is the
same either way.

**The remedy, verified.** I ran this test from my scratchpad, not added to the tree. It is `:269`
plus a time bound: set `READER_TIMEOUT_S = 8.0`, call `_read_table`, and assert that it returns in
less than `READER_TIMEOUT_S / 2`. Results:
- at HEAD: 1 passed in 0.03 s;
- under F13: 1 failed in 8.04 s;
- the file came back byte-identical (`6ebd9a619251…`).

## Mocks / contract tests

- **Arena slice download.** The canonical fake is in `src/app/clients/fakes.py:44`: `slice_parquet`,
  `FakeSliceDownload` and `fake_slice_client`. Every build, refresh and survey test drives it, and I
  found no parallel fake. The unit transport tests use respx on the real client (`:555-585`). The
  contract test against the live file is
  `tests/integration/test_arena_openrouter_contract.py:54`. It is env-gated, and CI's
  `live-contracts` job passed both configs at `8a6a260`. `:361` pins its `slice_download` marker.
  **OK.**
- **Network guard.** The client-level guard is at `tests/conftest.py:75`, and `build()` sees an
  empty slice table unless a test is marked `slices`. `:588` and build `:170` assert both, F22 shows
  the first has teeth, and my tripwire run confirms them. **OK.**

## Test integrity (weakened or deleted to green)

Every removed test function or assertion in the range, per commit:

- **`42de70d`**: `test_the_serving_process_never_loads_pyarrow` was replaced by the parametrized
  `:653`, which also checks the module itself. Stronger.
- **`ac7bf89`**: `test_a_date_column_typed_as_a_timestamp_is_read_as_its_date` was removed. This
  reverses the behaviour on purpose: wave review B1 restricted the columns to the live file's types,
  and a timestamp is now refused (`:145`, one of the `:151` cases).
- **`ed0c840`**: two tests were replaced.
  - `test_any_failure_inside_the_read_is_a_source_error` became `:160`, on the reader.
  - `test_a_marked_test_that_injects_no_client_cannot_reach_the_network` became the client-level
    guard and `:588`. That is a wider guard.
- **`9cf081f` and `effdb04`**: two assertions were replaced by stronger ones.
  - The protocol assertion now checks JSON lines.
  - `"HF_TOKEN" not in str(...)` became a direct `'clean'` answer, which the old form could pass
    with the allowlist gone.
- **`a73c079`**: the watchdog test became the parametrized `:326` (×4 failure kinds).
- **`bc7e43d`**: the fix commit relaxed its own red test from `bytes_after > bytes_before` to
  `bytes_after >= bytes_before > 0` (`tests/unit/test_survey_floors.py:152`). The reason given is
  that four rows can fit in free SQLite pages, which is plausible for a fixture this small. The live
  measurement (2,097,152 → 7,110,656 bytes) is in the research record. Accepted: the behaviour the
  test cites, a survey on a copy that never writes the served file, is still asserted at `:153`.

No skip or xfail was added. `docs/skip-budget.txt` rose from 64 to 66 for the two new env-gated
contract cases, with the reason written in the file.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **T1** `tests/unit/test_arena_slices.py:269`, `src/app/clients/arena_slices.py:259`: removing the capped read (F13) leaves the suite green, only 20 s slower. Both `:259` and `:269` still see the same "answer passed" reason after the timer kills the reader, and meanwhile the parent held the whole answer, the memory D-165 clause 4 bounds. So re-review 3's MINOR-R3-1, which `156d2f4`/`a73c079` claimed to close, is still open, and `:269` was green at its own red commit. Remedy, verified from my scratchpad (passes at HEAD, fails under F13): in `:269`, set `READER_TIMEOUT_S = 8.0` and assert that `_read_table` returns in less than `READER_TIMEOUT_S / 2`. The profile makes the test for a fault that stays green mandatory in this wave, so fixing it here is preferred over filing it.
- **T2** `scripts/smoke_deps.py:74-92`: the slice probe that P4 adds, one per config, has no citing test. I exercised it offline with the canonical fake and the tripwire loaded. A full `vision` file gave `9 slices, 421 rows`, and one row short on `ocr` gave `ValueError: below their declared floors: arena_vision_ocr`. The probe's floor check is the same one the live contract test (`tests/integration/test_arena_openrouter_contract.py:54`) asserts in CI, and no earlier smoke-deps probe has a unit test, so this is MINOR, not BLOCKING. Fix: a unit test driving `_slice_probe` with `fake_slice_client` for the pass and the short case.

## Tests added/extended this review
- none in the tree (this seat was told to write only this file). I ran the T1 remedy test and the
  T2 probe check from `scratchpad/tester_w2/`, as described above.
