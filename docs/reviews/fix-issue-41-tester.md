---
record_type: review
id: fix-issue-41-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---

# Issue #41 Tester Review (fix-issue)

**Reviewer:** Tester subagent (fresh eyes; did not write the fix or its tests)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `7d7a9ac..5a15b3a` (`git merge-base origin/main HEAD` = `7d7a9ac`): `03ce782` (red test) + `5a15b3a` (fix), branch `fix/issue-41-served-without-carry-tables`
**Risk tier:** severity:low, triage `fix-issue`
**Acceptance criterion:** issue #41 and its triage comment. `refresh._served_without`, the baseline the guards compare against on an expiry night, drops every carried table's rows (`build.CARRY_TABLES` = `scores`, `pricing`, `access`) for the expired sources. A carried table the live artifact predates is skipped and never raises. `CARRY_TABLES` is imported from `build`, not copied.
**Workspace:** the fix worktree, read-only except for in-place fault injection on `src/app/workflows/refresh.py`. Its sha256 was `550ab39a…f8889` before each mutant, after each restore, and at the end. Both commits were extracted with `git archive` into the session scratchpad. No `git checkout`, `restore` or `stash` was used, and nothing was committed. Probes and the mutation harness live in the scratchpad (`tester41/probe.py`, `tester41/mutate.py`).

## Verdict
MINOR. The fix does what #41 asks. The red test fails on `03ce782` and passes on `5a15b3a`. HEAD's unit suite is green. The edge-case probes pass, and so do the checks on INV-23 and the import graph. 6 of 9 mutants are killed. One survivor is out of reach through the schema (O1). The other two show test gaps next to the criterion. First, no test expires more than one source at once (T1). Second, the "predates `access`" test checks only that nothing raises (T2). The code is correct in both cases, as the probes show. Each gap needs one test, so nothing blocks.

## Acceptance-criterion coverage

| Criterion | Citing test | Asserts | Result |
|---|---|---|---|
| The expiry baseline drops an expired source's `access` rows | `tests/unit/test_refresh_carry.py:449` `test_the_expiry_baseline_drops_an_expired_attributes_values` (section header `:431` and docstring `:450` cite #41) | `_served_without(live, {"epoch_access"}).digest` equals the digest of the same artifact with `epoch_access` removed from `access` (`:463`). `:462` first shows that the digest can see that difference. | GREEN |
| Every carried table is dropped, not only `access` | `scores`: `test_refresh_carry.py:251` and `tests/unit/test_refresh_boards.py:147` `test_an_expired_board_drops_instead_of_freezing_the_artifact`; `pricing`: `test_refresh_carry.py:362`; `access`: `:449` | Dropping each table from the loop in turn (M3, M4, M5) is killed by these tests | GREEN |
| A carried table the live artifact predates is skipped and never raises | `test_refresh_carry.py:466` `test_the_expiry_baseline_of_an_artifact_from_before_the_access_table` | no exception after `DROP TABLE access` (`:473`). It does not check that the tables still present lost the expired source's rows: see T2 | GREEN |
| The list is `build.CARRY_TABLES` itself, not a copy | `src/app/workflows/refresh.py:44`, `:955` | In a fresh interpreter, `refresh.CARRY_TABLES is build.CARRY_TABLES` is `True` | verified by probe |
| Several expired sources at once | none | no test passes more than one source (T1) | probe P1 PASS |

## Red to green on the reported symptom

Both commits were extracted with `git archive` and run with the worktree's venv. `pythonpath = ["src"]` resolves to each extracted tree, so the red run loaded `tester41/red/src/app/workflows/refresh.py`.

- **`03ce782` (red):** `tests/unit/test_refresh_carry.py` gave `1 failed, 23 passed`. The failure was `test_the_expiry_baseline_drops_an_expired_attributes_values` at `:463`. The digests differed (`482a943e…` against the expected `19046caf…`) because the `epoch_access` rows were still in the baseline. This is the symptom #41 describes.
- **`5a15b3a` (fix):** `24 passed`.
- The second new test (`:466`) passes on the red commit too. The old loop never touched `access`, so there was nothing to fail. It is a regression guard for the skip, not a red. That is expected, and it is not a finding.

## Edge-case probes (`tester41/probe.py`, against HEAD, and against `03ce782` for contrast)

A spy wrapped `refresh.serving_summary` to count rows per `(table, source)` in the in-memory scratch copy that `_served_without` summarises. The artifact had `scores` rows from aider, litellm and swebench, `pricing` rows from litellm and openrouter, and `access` rows from `epoch_access` and a second source, `other_access`.

| # | Probe | HEAD | `03ce782` |
|---|---|---|---|
| P1 | several sources expired at once: `{epoch_access, aider, litellm}` | PASS. No expired rows are left in any table, and swebench, openrouter and other_access are kept. | FAIL: `epoch_access` still in `access` |
| P2 | artifact without an `access` table, expiring `{epoch_access, aider}` | PASS. No exception, and aider's `scores` rows are gone. | PASS |
| P3a | a VIEW named `access` in place of the table | PASS. It is skipped (`type = 'table'`), and nothing raises. | PASS |
| P3b | the table spelled `ACCESS` | skipped: its `epoch_access` row is kept (O1) | n/a |
| P3c | an INDEX named `access` | PASS, skipped | PASS |
| P4 | INV-23: the served file is never written | PASS. sha256 and `mtime_ns` are unchanged, no `-journal` or `-wal` appears, the file still holds its `epoch_access` row, and the function works on a `0444` file. | PASS |
| P5 | empty source set (the caller never passes one, `refresh.py:1119`) | no exception (`IN ()`) | same |

## Import change (`refresh.py:44`)

- `build` does not import `refresh`. After `import app.workflows.build`, `app.workflows.refresh` is not in `sys.modules`. No module under `src/` imports `refresh` either. `runner:196` reads only `status_path`.
- `refresh` already imported `build` (`from app.workflows.build import main as build_main`, `:45`), so this adds a name, not a new edge. There is no cycle.
- D-154's child process is `python -m app.workflows.refresh`. `python -B -m app.workflows.refresh --help` runs cleanly (exit 0). With `refresh` as `__main__`, `build` does not re-import `refresh`, so no second copy of the module is loaded. The serving-process import test (`tests/unit/test_nightly_refresh.py:353`, REQ-REF-007 measured transitively) passes in the suite.

## Suite result

- `tests/unit` with `-n auto` at HEAD: **1361 passed, 56 skipped, 0 failed** in 28.2 s. All 56 skips need the built `advisor.db`, which is gitignored and not in this worktree (W-108; `test_why_facts`, `test_budgets_endpoint`, `test_unavailable_after_boot` and others). None is a refresh test.
- No network was used, and `build()` was not called. The probes build artifacts with `schema.connect` and `access.store` only.
- Coverage: `--no-cov` as instructed. The three changed lines (`refresh.py:954-955` and the DELETE at `:957`) all run in `test_refresh_carry.py:449` and `:466`.

## Fault injection (in place, restored by string replacement in a `finally`, sha256 checked after each)

Each mutant was run against the whole unit suite (`pytest -x -n auto tests/unit`). Bytecode went to a scratch `PYTHONPYCACHEPREFIX`, so no stale `.pyc` could mask a mutant. The runner used a SIGKILL-on-timeout process group. Each restore matched `550ab39a55b079d957b4266f9c836de794956f8e80b2da426f171f66e68f8889`, and so did the final check. `git status` stayed clean.

| # | Mutant (`src/app/workflows/refresh.py`) | Result | Killing test / note |
|---|---|---|---|
| M1 | the loop goes back to `("scores", "pricing")` (`:955`) | KILLED | `test_refresh_carry.py:449` |
| M2 | existence filter removed: `for table in CARRY_TABLES` (`:955`) | KILLED | `test_refresh_carry.py:466` (`no such table: access`) |
| M3 | `access` skipped | KILLED | `test_refresh_carry.py:449` |
| M4 | `scores` skipped | KILLED | `test_refresh_carry.py:251`, `test_refresh_boards.py` |
| M5 | `pricing` skipped | KILLED | `test_refresh_carry.py:362` |
| M6 | `type = 'table'` dropped from the `sqlite_master` query (`:954`) | survived, **unreachable** | O1 |
| M7 | only the first expired source is dropped (`:957`) | **SURVIVED** | T1 |
| M8 | `present` always empty, so nothing is dropped | KILLED | `test_refresh_carry.py:251`, `test_refresh_boards.py` |
| M9 | an artifact missing any carried table drops nothing (`if set(CARRY_TABLES) <= present`) | **SURVIVED** | T2 |

## BLOCKING
- none

## MINOR (the author fixes each on this branch or files it as an issue)

- **T1** `src/app/workflows/refresh.py:956-957` and `tests/unit/test_refresh_carry.py:449`: no test expires more than one source at once. Mutant M7 drops only the first source and survives the whole unit suite. Every existing call passes one source (`:372`, `:373`, `:463`, `:473`). Several sources expiring together is the normal case: every `epoch_*` source (`epoch_access`, `epoch_gpqa`, `epoch_eci` and the rest) reads the one Epoch bundle (D-158), so a stale bundle expires them all on the same night. Probe P1 shows HEAD handles it correctly. To pin it, give `_artifact_with_access` a `scores` row from a second source and call `_served_without(live, {access.SOURCE, "<that source>"})` against a copy with both sources deleted from every table.
- **T2** `tests/unit/test_refresh_carry.py:473`: `assert _served_without(live, {"aider"}).surfaces is not None` is always true once the call returns, because `surfaces` is a dict. The test proves only that nothing raises. Mutant M9 drops nothing when the artifact predates `access`, and it survives: `:466` has no `scores` rows to lose, and every other test uses an artifact that has `access`. The first expiry night after the upgrade runs against exactly such an artifact. Under M9 its baseline would equal the live artifact, and the guards would refuse a legitimate expiry night, which is the M16-W3 defect again. Probe P2 shows HEAD drops aider's `scores` rows correctly. To pin it, add a `scores` row for the expired source to the fixture, then assert its surface count falls, as `:372` does, or compare digests as `:463` does.

## Observations (no action required)

- **O1** `src/app/workflows/refresh.py:954`: the existence check reads `sqlite_master.name` exactly. A view or index named `access` is skipped correctly (P3a, P3c), so it cannot be fooled into a DELETE that raises. A table spelled `ACCESS` is also skipped and keeps its rows (P3b), even though SQLite would accept `DELETE FROM access` against it. The schema never creates that spelling: `CREATE TABLE IF NOT EXISTS access` (`src/app/workflows/schema.py:32`). `build.py:264` uses the same exact-match check, so the two stay consistent. M6 is unreachable for the same reason. It is not worth a test.
- **O2** The commit message and the comment at `refresh.py:952` say "a second copy of the list". The issue says "third". Both describe the same fix, and the copy is gone either way.

## Tests added or extended by this review
- none. This review writes only this file. The probes and the mutation harness stayed in the session scratchpad and were not committed.
