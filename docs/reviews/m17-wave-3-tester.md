---
record_type: review
id: m17-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# Wave 3 Tester Review (m17): Epoch's own boards, the Agent Arena boards, accessibility, no ids from moving aliases

**Reviewer:** Tester subagent. Fresh eyes: I wrote none of this wave's code, its tests, its records or its reviews.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `c04ec4f66f617f24cf70685dd06a1742c4d5428a..98d8a72` (16 commits, issues #37 and #24)
**Risk tier:** MEDIUM (`docs/plans/m17-wave-3-plan.md:11`)

**Inputs I read:**
- the wave plan (`docs/plans/m17-wave-3-plan.md`, P1-P5 and decisions 1-5) and the milestone plan (`docs/plans/m17-plan.md` §W3);
- D-164, D-165 and D-166 with its appended correction (`docs/decisions.md:2983`, `:3013`, `:3050`, `:3076`);
- the measurement record (`docs/research/m17-w3-boards-and-first-night-2026-09-25.md`);
- the Code-Reviewer's verdict (`docs/reviews/m17-wave-3-review.md`, PASS-WITH-MINORS; not BLOCKING, so this seat runs) and the fix commits `5fc89b6`, `fd31317`, `35296f3` and `98d8a72`.

I read my policy from the base: `.claude/agents/Tester.md`, `.agents/rules/practices.md` and `permission-matrix.md` §11. The range does not touch them.

**Method:**
- **Suite.** I ran `make check-fast` and the full unit suite myself.
- **CI reproduction.** I ran CI's `pytest` and its skip-budget step (`scripts/coverage_floor.py`) on `git archive` trees of the base and of HEAD. These trees have no `advisor.db`, as a CI checkout has none.
- **Coverage.** I compared the touched modules between those two runs.
- **Red replay.** I replayed `5fc89b6` against `fd31317`, both from `git archive`.
- **Fault injection.** I ran 39 faults in place (`scratchpad/tester_w3/faults.py`), each against the whole unit suite. Every fault that stayed green got a remedy test in my scratchpad, and I checked that each remedy passes at HEAD and fails under its fault (`scratchpad/tester_w3/test_w3_remedies.py`, `remedies_under_faults.py`).
- **The first night.** I probed it on copies of a pre-W3 artifact and of the author's candidate (`scratchpad/tester_w3/first_night.py`).
- **Network.** Every pytest process and probe I started loaded a tripwire plugin (`scratchpad/tester_w3/netblock_tester.py`), including the xdist workers. The plugin refuses and logs every non-loopback `connect` and every DNS lookup of a non-local name. I checked that it fires on a real lookup. Its log was never created, so no test attempted a connection.
  - **One exception, and it was mine.** Before I had loaded the tripwire, one throwaway probe (not a test) called `build()` without `slices=()`. Outside pytest the conftest guard does not apply, so the real `ArenaSliceClient` downloaded the eight public `lmarena-ai` parquet files from huggingface.co (GET only). The results went to an in-memory database and I discarded them. Every later probe passed `slices=()` and loaded the tripwire.
- **What I did not do.** `RUN_CONTRACT_TESTS` was never set. No `os.abort()` ran. I used no `git checkout`, `restore` or `stash`.

## Verdict
BLOCKING: 2 BLOCKING, 4 MINOR, 2 K.9, 1 risk queued.

Every acceptance item of P1-P5 has a citing test that exercises it and is green. 30 of 39 faults turn a test red. Of the nine that stay green, five are equivalent or harmless on the declared data (explained below) and four are real gaps (T1-T4). The first night after merge publishes, and every source still carries from a pre-W3 artifact. All six Code-Review fixes (M1-M6) hold: reverting each one turns its test red.

Two items block, and each is a one-line fix:
- **B1: CI's `test` job will fail at HEAD.** Review M1's fix (`35296f3`) parametrises the live contract test over all eight `SLICE_CONFIGS`, which adds six env-gated skips. `docs/skip-budget.txt` still says 66. Reproduced: the base gives 66 skipped (PASS), HEAD gives 72 (FAIL).
- **B2: coverage drops on a touched module.** `build.py` goes from 94.47% to 94.37% (permission-matrix §11, "coverage drop on touched module"). The only new uncovered code is `_ingest_access`'s "parsed 0 rows" branch.

## Acceptance-criterion coverage (REQUIRED)

This project cites criteria in test and module docstrings (issue, D-id, plan item, review item), not in `# covers` comments. A citing test here is one whose docstring or module docstring names #37/#24, D-164/D-165/D-166 or the review item. **Fault** means an injected fault turned the test red (the ids are in the fault table). All tests below are GREEN at HEAD.

### P1: the Epoch boards, and D-164 over every uncovered board

| Criterion | Citing test | Proof |
|---|---|---|
| The five boards are declared like GPQA: file, label, `mean_score`, `fraction`, max 1.0 | `tests/unit/test_uncovered_boards.py:29` | F6 red |
| Each board is dated by `Started at`, and a release date is never a run date | `tests/unit/test_board_run_dates.py:42-46`, `:57`, `:113` | F6 red (3 tests) |
| Each board is attributed (CC-BY) | `tests/unit/test_categories.py:223` (reads `EPOCH_BOARDS`) | F7 red |
| The uncovered set is every declared board no surface ranks on, derived from `CATEGORIES` | `tests/unit/test_uncovered_boards.py:42`, `:51` | F1 red |
| A change on an uncovered Epoch board publishes | `tests/unit/test_uncovered_boards.py:69` | F1 and F5 red |
| A board losing a quarter is refused; its first night is not | `tests/unit/test_uncovered_boards.py:81` (with `test_refresh_boards.py`) | F8 red |
| `epoch_mmlu` (secondary evidence only) is a guarded board (review M2) | `tests/unit/test_uncovered_boards.py:92` | F1 and F2 red; red at `5fc89b6` |

### P2: the Agent Arena boards (D-105, D-165)

| Criterion | Citing test | Proof |
|---|---|---|
| Six boards on their own metric, floors 21 and ceilings 172 | `tests/unit/test_agent_boards.py:26` | table assertion |
| No IPS label is shared with an Elo board or a surface; no surface ranks on `ips` | `tests/unit/test_agent_boards.py:36` | label assertion; see F19 |
| The reader's column map: `score` is read through the child reader, and negative values are kept | `tests/unit/test_agent_boards.py:62` | F9, F10, F11, F12, F13, F14, F17 red |
| A file without its `score` column is refused | `tests/unit/test_agent_boards.py:71` | F11, F12 red |
| Each metric keeps its own band (IPS −1..1, Elo 0..5000) | `tests/unit/test_agent_boards.py:77` | F10 red |
| The Elo slices still read `rating` | `tests/unit/test_agent_boards.py:89` | column-map regression |
| One file read with two value columns is refused (review M1) | `tests/unit/test_agent_boards.py:115` | F15 red |
| Agent boards' unmatched names reach the curation queue (review M5) | `tests/unit/test_agent_boards.py:98` | F16 red; red at `5fc89b6` |
| The stale-date and hostile-file rules hold for them | no agent-file test; covered only through the shared path | **F18 stays green, see T4** |

### P3: accessibility (`model_metadata.csv`)

| Criterion | Citing test | Proof |
|---|---|---|
| The vocabulary; a value outside it, or a missing name or value, is skipped and counted | `tests/unit/test_access.py:29`, `:35`, `:43` | F27 red |
| A file without the columns is a `SourceError` | `tests/unit/test_access.py:49` | direct |
| Names link as their scores do; two names that disagree give no value and are counted | `tests/unit/test_access.py:60` | F21, F22, F26 red; F25 equivalent |
| One name listed twice with two values is a disagreement (review M3) | `tests/unit/test_access.py:146` (×2 orders) | F21, F22, F23 red; red at `5fc89b6` |
| Additive only: no existing column changes | `tests/unit/test_access.py:80` | shape assertion |
| The fingerprint moves with accessibility | `tests/unit/test_access.py:94` | F24 red |
| A pre-W3 artifact still fingerprints | `tests/unit/test_access.py:132` | F20 red |
| The build reads the file through the bundle, and a missing file is a missing line | `tests/unit/test_access.py:109` | F26 red; **the path guard is unpinned (F28), see T3** |
| The build reports the attribute as arrived (review M4) | `tests/unit/test_access.py:161` | F29 red; red at `5fc89b6` |
| The build links what it ingests (the reconcile join, in `build()`) | none; `:60` and `:109` call `access.link` themselves | **F30 stays green, see T1** |
| The attribute carries with its rows (review M1) | `tests/unit/test_carry_forward.py:349` (calls `Carry.restore` directly) | F34 red; **the build's call to it is unpinned (F31), see T2** |
| A metadata file with no valid row | none | **the branch is uncovered, see B2** |

### P4: moving aliases (D-166)

| Criterion | Citing test | Proof |
|---|---|---|
| The list is the thirteen, each with a reason | `tests/unit/test_moving_aliases.py:21` | F39 red |
| Each alias derives no id, in every spelling the grammar folds (`GPT-4o mini`, `openrouter/…`) | `tests/unit/test_moving_aliases.py:28` (×8) | F36 red (8); F37 red (4) |
| Dated names still derive | `tests/unit/test_moving_aliases.py:35` (×3) | direct |
| Reconcile registers nothing from an alias and counts it dropped (D-166 clause 1 as corrected, `docs/decisions.md:3076`) | `tests/unit/test_moving_aliases.py:47` | F36 red |
| A curated rule still wins over the list, through `reconcile` (review M6) | `tests/unit/test_moving_aliases.py:60` | F38 red |

### P5: measured, and the first night after merge

| Criterion | Evidence | Proof |
|---|---|---|
| A failed source still carries from a pre-W3 live artifact (review M1) | `tests/unit/test_carry_forward.py:336` | F32 and F33 red |
| My own first-night probe on copies: live = the worktree's gitignored pre-W3 `advisor.db` (317 models, no `access` table), candidate = the author's `cand.db`, compared with HEAD's `fingerprint_of`, `degradations` and `upward_anomalies` | `scratchpad/tester_w3/first_night.py` | results below; both copies unchanged by SHA-256 |
| The survey and the served change | the research record §2-§5 | agrees with my probe (317 models, 47 boards) |
| `smoke_deps` gains the agent configs | derived from `SLICE_CONFIGS` (`scripts/smoke_deps.py:114-116`); the probe is tested generically at `tests/unit/test_arena_slices.py:696` | live run recorded once, research §6 |

What the first-night probe returned:
- 47 boards fingerprinted on each side, `epoch_mmlu` included (136 names on each);
- `degradations` returned `[]` and `upward_anomalies` returned `[]`;
- the digests differ, so the night publishes;
- all 54 of the live artifact's sources restore as `carried` into a W3-schema candidate, both with and without an arrival record;
- `epoch_access` restores as `absent`, which is correct: the live artifact has no such rows.

## Red→green on reported symptoms

| Red → fix | At the red commit | At the fix |
|---|---|---|
| `5fc89b6` → `fd31317` (review M2-M5) | 5 failed: `test_uncovered_boards.py:92`, `test_access.py:146` ×2, `:161`, `test_agent_boards.py:98` | 25 passed |
| M1 and M6 tests (`35296f3`, added after their fixes) | red proven by reverting each fix in place: F15, F32, F33, F34, F38 | green at HEAD |
| `8ea2532` → `333542c` (the missing-table fingerprint) | the Code-Reviewer replayed it; F20 confirms `:132` guards it | green |

The fix commit `fd31317` edits `test_access.py:118-127`, only to follow `_ingest_access`'s new return type (a list of reports, not a count). It asserts the same facts, so nothing was weakened. `35296f3` deletes one test: the curated-rule test that could not fail (review M6). It is replaced by `:60`, which goes red under F38.

## Suite result

- **`make check-fast`:** PASS in 54.4 s. All six legs pass. The test leg reports `1408 passed, 23 skipped` and `coverage-floor PASS: 40 module(s)`.
- **Full unit suite under the tripwire** (`-n auto`): `1399 passed, 7 skipped`, with 0 connection attempts.
- **CI reproduction** (`git archive` trees, no `advisor.db`, `RUN_CONTRACT_TESTS` unset):
  - base `c04ec4f`: 1312 passed, 66 skipped. `coverage_floor PASS: 66 skipped of 1378 (budget 66)`;
  - HEAD `98d8a72`: 1359 passed, 72 skipped. `coverage_floor FAIL: 72 test(s) skipped of 1431, budget is 66`;
  - the six new skips are exactly `test_every_declared_slice_satisfies_the_parser_contract[agent…]` ×6 (B1).
- **Coverage on touched code** (same no-artifact runs, base → HEAD, lines and branches):

| Module | Base | HEAD |
|---|---|---|
| `arena.py` | 92.2% | 92.3% |
| `arena_slices.py` | 98.6% | 98.7% |
| `epoch_board.py` | 91.7% | 91.8% |
| `parquet_reader.py` | 86.9% | 87.1% |
| `build.py` | **94.47%** | **94.37%** (B2) |
| `rank.py` | 93.7% | 93.7% |
| `refresh.py` | 95.9% | 96.0% |
| `registry.py` | 97.4% | 98.1% |
| `schema.py` | 94.1% | 94.1% |
| `sources.py` | 100% | 100% |
| `access.py` (new) | n/a | 100% |
| `boards.py` (new) | n/a | 100% |

`build.py`'s only new missing line and branch are `:474-476` (`if not rows: raise SourceError("parsed 0 rows …")`). The same figure, 94.371%, comes from the `coverage.json` of `make check-fast`, which has the artifact.

## Fault injection (in place, byte-identical)

The protocol was one atomic sequence per fault, scripted in `scratchpad/tester_w3/faults.py`:
1. read the file's bytes and SHA-256;
2. assert the pattern occurs exactly once, and apply the fault;
3. run the whole unit suite (`-n auto`, with the tripwire);
4. write the original bytes back in `finally`;
5. recompute the SHA-256 and compare.

All 39 faults, and the four remedy runs, came back **byte-identical**. Afterwards each of the 11 touched source files matched `git show HEAD:<file>` by SHA-256, and `git status --porcelain` showed only the reviewer's untracked file.

| Id | Fault | Result |
|---|---|---|
| F1 | `declared()` forgets `EPOCH_BOARDS` | RED: uncovered `:42`, `:69`, `:92` |
| F2 | review M2 reverted: a secondary benchmark counts as coverage | RED: uncovered `:92` |
| F3 | `uncovered()` drops the primary-source clause | green, **equivalent**: both clauses pick the same six boards |
| F4 | `uncovered()` drops the primary-benchmark clause | green, **equivalent**: as F3 |
| F5 | the refresh fingerprints only `arena_*` boards (W2 behaviour) | RED: uncovered `:69` |
| F6 | SimpleQA dated by release date | RED: run dates `:57`, `:113`; uncovered `:29` |
| F7 | `epoch_chess` unattributed | RED: categories `:223` |
| F8 | the D-164 board loss guard off | RED: refresh boards; uncovered `:81` |
| F9 | IPS boards use the Elo band | RED: agent `:62` |
| F10 | the IPS band drops negatives (0..1) | RED: agent `:62`, `:77` |
| F11 | the reader ignores the column map (always `rating`) | RED: agent `:62`, `:71` |
| F12 | the parent never passes the value column | RED: agent `:62`, `:71` |
| F13 | `score_rows` stores every row as `elo` | RED: agent `:62` |
| F14 | agent boards on the Arena harness | RED: agent `:62` |
| F15 | review M1: the mixed-value-column guard off | RED: agent `:115` |
| F16 | review M5 reverted | RED: agent `:98` |
| F17 | the numeric check keyed on the name `rating` | RED: agent `:62` |
| **F18** | **the type check skipped when the value column is not `rating` (a hostile agent file)** | **STAYED GREEN, see T4** |
| F19 | the primary ranking ignores `metric` (`rank.py:281`) | green, redundant today: labels are disjoint, and `test_agent_boards.py:36` pins that |
| F20 | `served()` without the missing-table check | RED: access `:132` |
| F21 | `served()` serves a disagreeing model | RED: access `:60`, `:146` ×2 |
| F22 | `link()` never counts a disagreement | RED: access `:60`, `:146` ×2 |
| F23 | review M3 reverted: `UNIQUE (raw_name, source)` | RED: access `:146` ×2 |
| F24 | the fingerprint ignores accessibility | RED: access `:94` |
| F25 | `_model_for` does not strip the effort | green, **equivalent** on Epoch spellings: `derive_identity` strips `_high` itself, and the curated patterns match with the suffix (probed) |
| F26 | `_model_for` ignores curated rules | RED: access ×5 |
| F27 | a value outside the vocabulary is accepted | RED: access `:43` |
| **F28** | **`model_metadata.csv` read without `read_bundle_file`'s path guard** | **STAYED GREEN, see T3** |
| F29 | review M4 reverted | RED: access `:161` |
| **F30** | **the build never calls `access.link`** | **STAYED GREEN, see T1** |
| **F31** | **a failed metadata file never falls back to the carry** | **STAYED GREEN, see T2** |
| F32 | review M1-1: no skip for a table the live artifact lacks | RED: carry `:336` |
| F33 | review M1-2: `age_days` reads every carried table unchecked | RED: carry `:336` |
| F34 | review M1-3: `access` dropped from `CARRY_TABLES` | RED: carry `:349` |
| F35 | the review M1 rollback resets a hard-coded pair again | green, **harmless**, as the reviewer judged: `epoch_access` has no candidate rows when it falls back |
| F36 | the `MOVING_ALIASES` gate off | RED: aliases `:28` ×8 |
| F37 | the list checked on the raw name, before normalisation | RED: aliases `:28` ×4 |
| F38 | review M6: the list also blocks a curated rule | RED: aliases `:60` |
| F39 | one alias dropped from the list | RED: aliases `:21`, `:28` |

**Remedies, verified.** Each remedy below is in `scratchpad/tester_w3/test_w3_remedies.py`, not in the tree. At HEAD: 6 passed.

| Remedy | What it does | Under its fault |
|---|---|---|
| `r30` | `build()` with a `model_metadata.csv` naming `claude-opus-4-5-20251101`; asserts `access.served(conn) == {"claude-4.5-opus": "API access"}` and `report.access["linked"] == 1` | F30: 2 failed |
| `r31` | a live artifact holding an `epoch_access` row, and a candidate `build()` whose bundle lacks the file; asserts `epoch_access` in `report.carried` and the value served | F31: 1 failed |
| `r28` | `model_metadata.csv` as a symlink to a file outside the bundle; asserts a missing line saying "outside the bundle" and no rows | F28: 1 failed |
| `r18` | an agent file whose `score` column is text; asserts a `SourceError` naming `score` | F18: 1 failed |
| stale dates | an agent file with an older date and a future date: only the newest rows are served, and 2 are refused | passes at HEAD; the shared path |
| `b2` | a metadata file with the columns but no valid row is `missing == ["epoch_access: parsed 0 rows from model_metadata.csv"]` | covers `build.py:474-476` |

## Mocks / contract tests

- **Arena parquet (the slices and now the agent boards).** The canonical fake is `app.clients.fakes.slice_parquet` / `fake_slice_client` (`src/app/clients/fakes.py:44`). It writes only a `rating` column, so every agent-file test uses a bespoke builder (`tests/unit/test_agent_boards.py:46`). No test drives an agent board through `build()` with the fake (T4). The contract test against the live file now covers every config (`tests/integration/test_arena_openrouter_contract.py:55`). It is env-gated and I did not run it. Research §6 records one live run. Its six new skips cause B1.
- **The Epoch bundle (boards and metadata).** These are local files. There is no network and so no contract test. The path guard is shared (`read_bundle_file`, `src/app/clients/epoch_board.py:91`), but only the boards' use of it is tested (T3).
- **Network guard.** `tests/conftest.py:62-75` held: my tripwire log is empty for every pytest run.

## Test integrity (weakened or deleted to green)

Every removed test line in the range, `git diff c04ec4f..98d8a72 -- tests`:
- **the table-size assertions**, `35` to `41` (`test_arena_slices.py:631-638`, `test_build_slices.py:178`): the owner-ruled six boards were added, and the per-config counts are still asserted;
- **`.slices` to `.boards`** (`test_refresh_boards.py:89`): a rename;
- **`boards=()` gains `access_files=()`** (`test_build.py:479`);
- **the contract test's parameter list** became `SLICE_CONFIGS`, which is wider;
- **the unfailable curated-rule test**, replaced by `test_moving_aliases.py:60`, which F38 turns red.

No skip or xfail was added by hand. The six new skips are the contract parameters (B1).

## BLOCKING
- **B1** `docs/skip-budget.txt:23`, `tests/integration/test_arena_openrouter_contract.py:55`. CI's required `test` job runs `scripts/coverage_floor.py` (`.github/workflows/ci.yml:61`). At HEAD it fails: 72 skipped against a budget of 66. `35296f3` (review M1) parametrised the contract test over all eight `SLICE_CONFIGS` and added six env-gated skips, but did not raise the budget, whose own comment counts "10 contract tests" (`docs/skip-budget.txt:17-19`). Reproduced on `git archive` trees: base 66 (PASS), HEAD 72 (FAIL). Fix: set the budget to 72 and update the contract line to 16, with the reason, in the same tree. I checked that `coverage_floor.py --budget-file` with 72 passes on HEAD's report.
- **B2** `src/app/workflows/build.py:474-476`. Coverage on a touched module drops: `build.py` goes from 94.47% (base) to 94.37% (HEAD). That is BLOCKING by `permission-matrix.md` §11. The only new uncovered code is `_ingest_access`'s "parsed 0 rows" branch. That is a real edge: a metadata file whose rows are all outside the vocabulary or unnamed. Fix: one test, such as the scratch `b2` above (a file with the columns and no valid row gives the missing line `epoch_access: parsed 0 rows from model_metadata.csv`). It passes at HEAD and lifts `build.py` above the base.

## MINOR (the author fixes each in this wave or files it as an issue)
- **T1** `src/app/workflows/build.py:730`: nothing pins that `build()` links what it ingests. Replacing `access.link(conn)` with an empty report (F30) leaves the whole suite green, and every accessibility value the phone would get is then gone. `test_access.py:60` and `:109` call `access.link` themselves, and `:161` asserts only arrival. Remedy, verified (passes at HEAD, fails under F30): extend `test_access.py:161` to build with a name the fixture registers (`claude-opus-4-5-20251101`) and assert `access.served(conn) == {"claude-4.5-opus": "API access"}` and `report.access["linked"] == 1`. The fault table says to write it this wave.
- **T2** `src/app/workflows/build.py:483`: review M1 asked that "`epoch_access`'s carry" be pinned, and `test_carry_forward.py:349` does so for `Carry.restore` only. Removing `_ingest_access`'s call to `_fall_back` (F31) stays green. On a night the metadata file fails, every filter would then drop instead of carrying. Remedy, verified (passes at HEAD, fails under F31): a `build()` whose live artifact holds an `epoch_access` row and whose bundle lacks the file; assert `epoch_access` in `report.carried` and the value served.
- **T3** `src/app/workflows/build.py:473`: the reviewer's P3 row "the build reads it through the bundle guard" has no test. Reading `model_metadata.csv` with a plain `read_text` (F28) stays green, although the bundle is an unpacked ZIP from the internet, and M5's symlink finding (`epoch_board.py:77-79`) is the reason the guard exists. Remedy, verified (passes at HEAD, fails under F28): plant `model_metadata.csv` as a symlink to a file outside the bundle; assert a missing line containing "outside the bundle" and no `access` rows.
- **T4** `tests/unit/test_agent_boards.py:46`, `src/app/clients/parquet_reader.py:114`, `src/app/clients/fakes.py:44`: plan P2's red-first item "the stale-date and hostile-file rules hold for them" has no agent-file test. Skipping the reader's type refusal when the value column is not `rating` (F18) stays green. `score_rows` still refuses a non-number (`arena.py:384-389`), so nothing wrong is served, but D-165 clause 3's first refusal is unpinned for `score`. The canonical fake cannot write a `score` column, so the agent tests use a bespoke builder, and no test drives an agent board through `build()` (practices: "one canonical mock per integration"). Remedy, verified: a text-typed `score` file raises a `SourceError` naming `score` (passes at HEAD, fails under F18). An agent file with an older date and a future date serves only the newest rows and refuses 2 (passes at HEAD). Teaching `slice_parquet` a `value_column` would let `test_build_slices.py` cover one agent board end to end.

## K.9 candidates spotted outside this wave's scope
- **K1** `src/app/workflows/registry.py:417-433`, `:460-461`: D-166's list is spelling-exact after normalisation, and some spellings of moving aliases escape it. `Command R+` derives `command-r+`, not `command-r-plus`. `anthropic.claude-instant-v1` derives `claude-instant-v1`. Every `*-latest` alias derives an id: `chatgpt-4o-latest` gives `chatgpt4o-latest`, and `claude-3-5-sonnet-latest` gives `claude3.5-sonnet-latest`. All of them are latent on the candidate. `Command R+` is unmatched on `epoch_eci`, and no `-latest` id is registered. But the candidate's pricing already carries `mistral-large-latest` and `gpt-chat-latest` aliases, so one matching score name would derive a model from an alias that moves by definition. D-166 clause 3 grows the list by review, and a `-latest` suffix rule may be the general form.
- **K2** `src/app/workflows/refresh.py:951`: `_served_without` still deletes an expired source's rows from a hard-coded `("scores", "pricing")`. That is a third copy of `CARRY_TABLES` (`build.py:216`), which review M1 unified in `build.py` only. It is harmless today, because no guard reads `access`. It stops being harmless the day one does, or the day W4 adds an accessibility guard.

## Risks queued to next M
- **R1** `src/app/workflows/build.py:474`: accessibility has no loss guard. `_ingest_access` refuses only a file with zero valid rows. A truncated `model_metadata.csv` with one valid row publishes: the fingerprint moves (`refresh.py:477-479`), and no D-128/D-164-style guard compares the served count (219 models on the candidate, research §5). Values would vanish from the phone's filters in W4 without a refusal. It would show as the build report's `access.linked` falling by an order of magnitude on a night that still publishes.

## Tests added/extended this review
- none in the tree. This seat was told to write only this file. The remedy tests for B2 and T1-T4 are in `scratchpad/tester_w3/test_w3_remedies.py`. Each one passes at HEAD, and each T remedy fails under its fault (`scratchpad/tester_w3/remedies.log`).
