---
record_type: review
id: m17-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# Wave 3 Tester Review (m17), second seat: Epoch's own boards, the Agent Arena boards, accessibility, no ids from moving aliases

**Reviewer:** Tester subagent, second seat. Fresh eyes: I wrote none of this wave's code, tests, records or reviews. I am not the Code-Reviewer and not the first Tester.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `c04ec4f66f617f24cf70685dd06a1742c4d5428a..c482cc3` (18 commits, issues #37 and #24)
**Risk tier:** MEDIUM (`docs/plans/m17-wave-3-plan.md:11`)

**This verdict supersedes the BLOCKING verdict committed at `c482cc3`.** That verdict stays in git history (`git show c482cc3:docs/reviews/m17-wave-3-tester.md`). It blocked on B1 (CI's skip budget) and B2 (a coverage drop on `build.py`), and raised T1-T4. Its K1, K2 and R1 are filed as #40, #41 and #42, so they are not repeated here. The author answered all six in `de50f91`. I re-tested the whole wave, not only that commit.

**Inputs I read:**
- the wave plan (P1-P5, decisions 1-5) and the milestone plan §W3;
- D-164, D-165, D-166 and D-166's appended correction (`docs/decisions.md`);
- the measurement record (`docs/research/m17-w3-boards-and-first-night-2026-09-25.md`);
- the Code-Reviewer's verdict (PASS-WITH-MINORS, so this seat runs), and its fixes `5fc89b6`, `fd31317`, `35296f3` and `98d8a72`;
- the first Tester's verdict and the fix commit `de50f91`.

I read my policy from the base: `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `permission-matrix.md` §11. The range does not touch them.

**Method:**
- **CI's view.** I extracted the base (`c04ec4f`) and `c482cc3` with `git archive` into my scratchpad. These trees have no `advisor.db`, as a CI checkout has none. In each tree I ran what CI's `test` job runs:
  - bare `pytest` (the `pyproject.toml` addopts: branch coverage, `coverage.json`, `.pytest-report.xml`);
  - `scripts/coverage_floor.py --junit .pytest-report.xml`, the skip budget;
  - `scripts/module_coverage_floor.py`.

  The environment was `env -i` with no `RUN_CONTRACT_TESTS`, `EPOCH_DATA_DIR` or `MODEL_RANKING_REQUIRE_ARTIFACT`. I ran Python 3.14 only. No 3.12 interpreter is on this machine, and the skip conditions do not depend on the version.
- **The owner's view.** I ran `make check-fast` in the worktree, which has the artifact. `git status --porcelain --ignored` was identical before and after.
- **Mutation.** I ran 40 mutants on a `git archive` copy of `c482cc3`. Its `src/` and `tests/` are byte-identical to the worktree's tracked files (only the untracked `egg-info` differs). Each mutant was an exact-once string replacement, run against the whole unit suite (`-n auto`), then written back and checked with SHA-256. All 40 came back identical, and the copy's source tree hash is the same before and after (`302451cc…`). No mutant touched the worktree. Scripts: `scratchpad/tester2_w3/mutants.py`, `mutants_head.json`.
- **Red replay.** I extracted `8ea2532`/`333542c` and `5fc89b6`/`fd31317` with `git archive` and ran each red test on both sides of its fix.
- **The first night.** I probed it offline. The live side is a copy of the worktree's pre-W3 `advisor.db` (317 models, no `access` table). The candidate is a second copy, with every model link cleared and re-reconciled by `c482cc3`'s `reconcile`, `access.link`, `reconcile_plans` and `build_price_medians`. The probe calls no `build()` and no fetch (`scratchpad/tester2_w3/first_night.py`).
- **Network.** Every pytest process and probe loaded a tripwire (`scratchpad/tester2_w3/netblock/sitecustomize.py`, on `PYTHONPATH`, so xdist workers and `make` legs load it too). It refuses and logs every non-loopback `connect` and every DNS lookup of a non-local name. I checked that it fires on a real lookup and a real connect. Its log was never created: nothing tried.
- **What I did not do.** I never called `build()` outside the unit tests' own fixtures. `RUN_CONTRACT_TESTS` was never set. No `os.abort()` ran. I used no `git checkout`, `restore` or `stash`. This file is the only one I changed in the worktree.

## Verdict
PASS-WITH-MINORS: 0 BLOCKING, 2 MINOR (T5, T6).

- **B1 is resolved.** CI's view at `c482cc3`: 72 skipped, budget 72, `coverage_floor PASS: 72 skipped of 1437 (budget 72)`. The base gives 66 of 1378 against 66. The 72 break down exactly as `docs/skip-budget.txt:13-20` says: 49 need `advisor.db`, 16 are `RUN_CONTRACT_TESTS` contract tests (1+1+3+8+1+1+1, the 8 being `test_arena_openrouter_contract.py:54` over the eight `SLICE_CONFIGS`), and 7 need `EPOCH_DATA_DIR`. The owner's view skips 23 (16+7), as the file's last comment says.
- **B2 is resolved.** `build.py` goes from 94.47% at the base to 94.93% at `c482cc3`, the same measure the first Tester used. No touched module is below its base (table below).
- **T1-T4 are resolved.** Each of the four remedy tests in `de50f91` goes red under the fault it names (X01-X05 below). T4's side note, that the canonical fake cannot write an agent file, is still open. It is T6.
- **Suites are green.** Every P1-P5 item has a citing test that exercises it and is green. Both reported symptoms replay red to green. 33 of 40 mutants are killed. Four survivors are equivalent on the declared data. Three are one real gap, T5.

## Acceptance-criterion coverage (REQUIRED)

This project cites criteria in test and module docstrings (issue, D-id, plan item, review item), not in `# covers` comments. A citing test here is one whose docstring or module docstring names #37/#24, D-164/D-165/D-166, the plan item or the review item. **Killed by** names the mutant that turned it red. All tests below are GREEN at `c482cc3`.

### P1: the Epoch boards, and D-164 over every uncovered board

| Criterion | Citing test | Killed by |
|---|---|---|
| Five boards declared like GPQA (file, label, `mean_score`, `Started at`, `fraction`, 1.0) | `tests/unit/test_uncovered_boards.py:29` (module docstring cites D-164, #37) | shape asserted directly |
| Each is dated by its run, not its release | `tests/unit/test_board_run_dates.py:41-46` | as above |
| Each is attributed (CC-BY) | `tests/unit/test_categories.py:238-249`, over every ingested source | as above |
| A change on an uncovered Epoch board moves the fingerprint | `tests/unit/test_uncovered_boards.py:69` | X12 |
| A quarter lost is refused, and a board's first night is not a quarter new | `tests/unit/test_uncovered_boards.py:81`; `tests/unit/test_refresh_boards.py` | X13, X14 |
| The set is derived from `CATEGORIES`, not listed | `tests/unit/test_uncovered_boards.py:42`, `:51` | X10 |
| A secondary-evidence board is still a board (review M2) | `tests/unit/test_uncovered_boards.py:92` | X10 |

### P2: the Agent Arena boards (D-165's reader)

| Criterion | Citing test | Killed by |
|---|---|---|
| The reader's column map (`score` for agent, `rating` for Elo) | `tests/unit/test_agent_boards.py:62`, `:71`, `:89` | X33 |
| `ips` rows under their own metric, harness and band; negative values kept | `tests/unit/test_agent_boards.py:62`, `:77` | X26, X27, X34 |
| Six boards declared, each with its own source id, floor and ceiling | `tests/unit/test_agent_boards.py:26`; `tests/unit/test_arena_slices.py:631` | X32 |
| An `ips` board never joins an `elo` ranking (hard criterion) | `tests/unit/test_agent_boards.py:36` (labels disjoint, no surface on `ips`), `:115` (one file read cannot mix value columns) | X25 |
| Hostile file: a text `score` column is refused by the reader (first Tester's T4) | `tests/unit/test_agent_boards.py:138` | X05 |
| Stale and future dates on an agent file (first Tester's T4) | `tests/unit/test_agent_boards.py:145` | X06, X07 |
| The agent boards' unmatched names reach the curation queue (review M5) | `tests/unit/test_agent_boards.py:98` | X28 |

### P3: accessibility

| Criterion | Citing test | Killed by |
|---|---|---|
| Vocabulary; rows with no name or value, or an unknown value, are skipped and counted | `tests/unit/test_access.py:29`, `:35`, `:43`, `:49` | X18 |
| The reconcile join; a disagreement gives no value and is counted | `tests/unit/test_access.py:60` | X15, X20, X40 |
| One name listed twice with two values is a disagreement, not the last row (review M3) | `tests/unit/test_access.py:146` | X36 |
| No existing table changes shape | `tests/unit/test_access.py:80` | shape asserted directly |
| The fingerprint moves with it; a pre-W3 artifact still fingerprints | `tests/unit/test_access.py:94`, `:132` | X11, X21 |
| Read through the bundle's path guard (first Tester's T3) | `tests/unit/test_access.py:224` | X03, X37 |
| A file with no valid row is a missing line (first Tester's B2) | `tests/unit/test_access.py:242` | X04 |
| `build()` links what it stores (first Tester's T1) | `tests/unit/test_access.py:189` | X01 |
| A missing file carries the last good values through `build()` (first Tester's T2, D-156) | `tests/unit/test_access.py:202`; `tests/unit/test_carry_forward.py:349` | X02, X22 |
| The first night: a live artifact without `access` still carries (review M1) | `tests/unit/test_carry_forward.py:336` | X23, X24 |
| The build reports the attribute as arrived (review M4) | `tests/unit/test_access.py:161` | X29 |
| **The build's report of a failed or disagreeing attribute** | none: T5 | X30, X31, X39 survive |

### P4: moving aliases (D-166)

| Criterion | Citing test | Killed by |
|---|---|---|
| Each listed alias derives no id, in every spelling the grammar folds | `tests/unit/test_moving_aliases.py:21`, `:28` | X08, X38 |
| A dated name still derives | `tests/unit/test_moving_aliases.py:35` | as above |
| Reconcile registers no model from an alias and counts it dropped (D-166's correction, review M6) | `tests/unit/test_moving_aliases.py:47` | X08, X38 |
| A curated rule still wins, through `reconcile` | `tests/unit/test_moving_aliases.py:60` (asserts the row links to the rule's id and is not dropped) | not mutated by me; the review's M6 fix made it reach `reconcile` |

### P5: measured and recorded

- **The survey and the first night:** `docs/research/m17-w3-boards-and-first-night-2026-09-25.md` §2-§5.
  - I reproduced §2 and §3 independently, offline, on a copy of the worktree's pre-W3 artifact.
  - `serving_summary` does not raise on the table-less live side and fingerprints 47 boards.
  - The re-reconciled candidate drops exactly the twelve ids §2 lists and registers 305 models. §2 has 306, the extra one being `hy4-preview`, which needs the agent boards' live rows.
  - `degradations == []` and `upward_anomalies == []`.
  - The surface losses are exactly §3's: assistant 190→185, coding 55→54, everyday 151→147, expert 148→146, mathematics 138→136.
- **`smoke_deps`:** `scripts/smoke_deps.py:114-116` derives its probes from `SLICE_CONFIGS`, which now holds the six agent configs (`src/app/clients/arena_slices.py:54-55`).

## Red→green on reported symptoms

- **The table-less artifact** (the P5 measurement's defect, research §1): `tests/unit/test_access.py::test_an_artifact_from_before_the_table_still_fingerprints` fails at `8ea2532` (1 failed) and passes at `333542c` (1 passed). Both trees came from `git archive`.
- **Review M2-M5:** the five tests `5fc89b6` added fail at `5fc89b6` (5 failed: M3 ×2, M4, M5, M2) and pass at `fd31317` (5 passed).
- **Review M1 and M6** (`35296f3`), and the first Tester's B2 and T1-T4 (`de50f91`), are tests over code that already existed. Their "red" is the fault each one names. X01-X05 and X22-X24 turn each red, and the code restored turns it green.

## Suite result

- **CI's view** (`git archive` of `c482cc3`, bare `pytest`, no artifact): `1365 passed, 72 skipped`, exit 0. Skip budget: `coverage_floor PASS: 72 skipped of 1437 (budget 72)`. `coverage-floor PASS: 40 module(s), floor 60%, 1 exempt`. Total coverage 91.08%, against a `fail_under` of 85.
- **CI's view at the base** (`c04ec4f`): `1312 passed, 66 skipped`. Skip budget `66 of 1378 (budget 66)` PASS. Total 90.80%.
- **The owner's view** (`make check-fast` in the worktree): `check-fast PASS in 49.9s`, 6 of 6 legs (lint, typecheck, records, test, client-decls, swift-test). The test leg: `1414 passed, 23 skipped`.
- **Coverage on touched code**, CI's view, `percent_covered` (statements and branches, `branch = true`), base → `c482cc3`. The worktree's `coverage.json` from `check-fast` gives the same figures for these modules at `c482cc3`.

| module | base | c482cc3 |
|---|---:|---:|
| `src/app/clients/arena.py` | 92.24 | 92.34 |
| `src/app/clients/arena_slices.py` | 98.63 | 98.72 |
| `src/app/clients/epoch_board.py` | 91.67 | 91.79 |
| `src/app/clients/parquet_reader.py` | 86.90 | 87.07 |
| `src/app/workflows/access.py` | new | 100.00 |
| `src/app/workflows/boards.py` | new | 100.00 |
| `src/app/workflows/build.py` | 94.47 | **94.93** |
| `src/app/workflows/rank.py` | 93.67 | 93.67 |
| `src/app/workflows/refresh.py` | 95.91 | 95.95 |
| `src/app/workflows/registry.py` | 97.38 | 98.06 |
| `src/app/workflows/schema.py` | 94.12 | 94.12 |
| `src/app/workflows/sources.py` | 100.00 | 100.00 |

No touched module drops. `scripts/survey_boards.py` is outside `source = ["src/app"]`.

- **Weakened or deleted tests:** I compared the test function names at the base and at `c482cc3`. One test was renamed, `test_the_table_is_the_35_boards_the_owner_ruled` → `test_the_table_is_the_boards_the_owner_ruled` (`tests/unit/test_arena_slices.py:631`). It still asserts 26 `text` and 9 `vision` slices, and now 6 agent boards and 41 in all. No test was deleted. No `skip` or `xfail` was added (one each at the base and at `c482cc3`).

## Mutation (fault injection)

The mutants ran on the scratch copy. Each was run against the whole unit suite, and each was restored and verified with SHA-256. Kill rate: 33/40 (82.5%). Leaving out the four equivalent survivors, it is 33/36 (91.7%).

| id | mutant (file:line at `c482cc3`) | result |
|---|---|---|
| X01 | `build.py:730` `access.link` replaced by an empty report | KILLED (`test_access.py:189`, `:202`) |
| X02 | `build.py:483` `_ingest_access` never falls back | KILLED (`test_access.py:202`) |
| X03 | `build.py:473` metadata read with a plain `read_text` | KILLED (`test_access.py:224`) |
| X04 | `build.py:474` "parsed 0 rows" guard removed | KILLED (`test_access.py:242`) |
| X05 | `parquet_reader.py:111` type check keyed on `"rating"` | KILLED (3 agent tests) |
| X06 | `arena_slices.py:425` newest-date filter removed | KILLED (7) |
| X07 | `arena_slices.py:402` future-date horizon removed | KILLED (2) |
| X08 | `registry.py:460` D-166 gate off | KILLED (9) |
| X09 | `boards.py:44` primary-benchmark exclusion removed | SURVIVED, equivalent: no declared board is excluded by benchmark alone (probe: `[]`) |
| X10 | `boards.py:43` secondary benchmark counted as coverage (M2 reverted) | KILLED |
| X11 | `refresh.py:478` access out of the fingerprint | KILLED |
| X12 | `refresh.py:469` Epoch boards out of the fingerprint | KILLED |
| X13 | `refresh.py:278` board quarter-lost guard off | KILLED (2) |
| X14 | `refresh.py:222` board quarter-new guard off | KILLED |
| X15 | `access.py:112` a disagreement served a guessed value | KILLED (3) |
| X16 | `access.py:81` a curated rule links to an unregistered id | SURVIVED, equivalent on data: 0 of the 839 Epoch spellings in the pre-W3 artifact resolve differently |
| X17 | `access.py:78` effort suffix not stripped before resolving | SURVIVED, equivalent on data: 0 of 839 differ, because `derive_identity` strips the suffix itself |
| X18 | `access.py:57` vocabulary not enforced | KILLED (3) |
| X19 | `access.py:68` `store` keeps the source's earlier rows | SURVIVED, equivalent in the build: the candidate is a fresh database and `store` runs once per source per build |
| X20 | `access.py:96` conflicts not counted | KILLED (3) |
| X21 | `access.py:108` table-existence check removed | KILLED |
| X22 | `build.py:216` `access` not a carried table | KILLED (2) |
| X23 | `build.py:326` `if not live_cols: continue` removed | KILLED |
| X24 | `build.py:263` age read on a table the live artifact lacks | KILLED |
| X25 | `arena_slices.py:394` mixed value columns accepted | KILLED |
| X26 | `arena_slices.py:429` Elo band applied to agent boards | KILLED (2) |
| X27 | `arena_slices.py:152` agent harness lost | KILLED |
| X28 | `build.py:354` agent boards out of the curation queue (M5 reverted) | KILLED |
| X29 | `build.py:716` access report not in `report.sources` (M4 reverted) | KILLED |
| X30 | `build.py:718` `access_missing` left out of `required_operator_actions` | **SURVIVED, T5** |
| X31 | `build.py:482` access failure not recorded as drift | **SURVIVED, T5** |
| X32 | `arena_slices.py:231` agent `source_id` dropped | KILLED |
| X33 | `parquet_reader.py:46` reader ignores the value column | KILLED (4) |
| X34 | `arena.py:105` IPS band widened | KILLED |
| X35 | `schema.py:449` `reset_source` refuses `access` | KILLED (75) |
| X36 | `schema.py:41` `UNIQUE (raw_name, source)` (M3 reverted) | KILLED (2) |
| X37 | `epoch_board.py:105` bundle path guard off | KILLED (5) |
| X38 | `registry.py:421` `deepseek-chat` dropped from the list | KILLED (3) |
| X39 | `build.py:731` build report's `conflicting` emptied | **SURVIVED, T5** |
| X40 | `access.py:94` unlinked names counted as linked | KILLED |

## Mocks / contract tests

- **Arena parquet (D-165 reader).** The canonical fake is `src/app/clients/fakes.py:44` (`slice_parquet`). The contract test is `tests/integration/test_arena_openrouter_contract.py:54-55`, now parametrised over `SLICE_CONFIGS`, the six agent files included (review M1, `35296f3`). It is env-gated and counted in the skip budget. The agent tests do not use the canonical fake: T6.
- **Epoch bundle.** The accessibility tests build `model_metadata.csv` with a local CSV helper (`tests/unit/test_access.py:22-26`). Its vocabulary is the measured one (`src/app/workflows/access.py:24-28`, plan "What the data looks like"). The Epoch boards use the existing reader and parser (`src/app/clients/epoch_board.py:91-112`). No new `EPOCH_DATA_DIR`-gated test reads the real new files. I note this and do not raise it: the owner's runs skip those tests too (skip budget: 7), and the nightly build counts a changed file's refused rows in its report.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **T5** `src/app/workflows/build.py:718`, `:481-482`, `:731`. **The build's own report of the attribute is unpinned.** Three mutants each leave the whole unit suite green: X30 drops `access_missing` from `required_operator_actions`, X31 drops the drift line for a failed metadata file, and X39 empties `report.access["conflicting"]`.

  So a bundle that arrives without `model_metadata.csv`, or with one that no longer parses, could stop showing on the operator line and in `/health`'s `refresh_drift` (`src/app/adapter/nightly.py:377`), and nothing would go red. The only test of that path (`tests/unit/test_access.py:109`) reads `_ingest_access`'s return value, not the build report. The research record's §5 ("Six models get no value because their names disagree") is read from `report.access["conflicting"]`, which no test pins through `build()`.

  Remedy, verified in my scratchpad (`scratchpad/tester2_w3/remedies/test_zz_tester2_remedies.py`, `remedies.log`). Both tests pass at `c482cc3`, and each fails under its mutants:
  1. `build()` with an existing bundle directory that lacks the file. Assert a `required_operator_actions` line starting `epoch_access is unavailable`, and a `drift` entry starting `epoch_access:`. This kills X30 and X31.
  2. `build()` with one name listed under two values. Assert `report.access["conflicting"] == ["claude-4.5-opus"]`. This kills X39.
- **T6** `tests/unit/test_agent_boards.py:46`, `:124`; `src/app/clients/fakes.py:44-69`. **Two bespoke parquet builders stand beside the canonical fake, for the same integration.** `_agent_file` (P2) and `_dated_file` (added by `de50f91` for T4) each write an Agent Arena file by hand, because `slice_parquet` can only write a `rating` column. Practices ("one canonical mock per integration") and this profile's §5 ask for consolidation.

  The consequence is that no test drives an agent board through `build()` / `_ingest_slices` (`grep agent tests/unit/test_build_slices.py` is empty). An agent board's store and floor path is covered only because it is shared with the Elo slices. The Code-Reviewer listed this as a deviation, and the first Tester's T4 suggested the remedy.

  Remedy: give `slice_parquet` a `value_column` (default `rating`), move both helpers onto it, and add one `@pytest.mark.slices` build of an agent board in `test_build_slices.py` that asserts `metric == "ips"` and `harness == "arena-agent"` on the stored rows.

## K.9 candidates spotted outside this wave's scope
- none new. The first Tester's K1 and K2 are #40 and #41.

## Risks queued to next M
- none new. The first Tester's R1 (no loss guard on accessibility) is #42.

## Tests added/extended this review
- none in the tree. This seat was told to write only this file. The two remedy tests for T5 are in `scratchpad/tester2_w3/remedies/test_zz_tester2_remedies.py`. Both pass at `c482cc3`, and they fail under X30, X31 and X39 (`scratchpad/tester2_w3/remedies.log`).
