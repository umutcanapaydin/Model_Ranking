---
record_type: review
id: m17-wave-3-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# M17-W3 Code Review: Epoch's own boards, the Agent Arena boards, accessibility, no ids from moving aliases

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `c04ec4f..0f6e136` (12 commits, 26 files, +1101 / -81)
**Risk tier:** MEDIUM (`docs/plans/m17-wave-3-plan.md:11`)

**What I read first.** `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md`. Then the
wave plan, `docs/plans/m17-plan.md` §W3 (`:68-72`), and D-105, D-128, D-164, D-165 and the new
D-166 (`docs/decisions.md:322`, `:1141`, `:2983`, `:3013`, `:3050`). The code came before the commit
messages. `git diff --stat c04ec4f..0f6e136 -- .claude .agents AGENTS.md permission-matrix.md` is
empty, so the policy I read is the base's. Nothing in the diff addresses a reviewer.

**How I worked.**
- `make check-fast`: PASS, 6 of 6 legs (lint, typecheck, records, test, client-decls, swift-test),
  57.5 s. The full unit suite under mutation runs: 1391 passed, 7 skipped.
- **Red replay.** Each `test:` commit and the commit after it were extracted with `git archive` into
  my scratchpad and run there. No checkout, no restore.
- **Mutants.** 9 mutants, run in place by `scratchpad/w3_mutate.py`. For each one the script saved
  the bytes, applied the change, ran the tests, wrote the bytes back and checked SHA-256. **All 9
  came back byte-identical.** `git status` shows only this file.
- **Probes.** I wrote throwaway scripts against in-memory or scratch databases. I also read the
  author's scratch candidate (`scratchpad/cand.db`, `cand-build.json`) read-only.
- **Network.** No test or probe reached the network. The suite's guard (`tests/conftest.py:62-75`)
  was active, and `RUN_CONTRACT_TESTS` was unset. Nothing called `os.abort()`.

## Verdict

PASS-WITH-MINORS: 0 BLOCKING, 6 MINOR, 1 K.9, 2 risks queued.

The wave delivers every phase of its plan. The security look at the generalised D-165 reader found
no way to widen the child's answer, break the 8 MiB bound, change the numeric check or smuggle a
non-number into `scores` (details below). An IPS board cannot meet an Elo board in one ranking: the
primary ranking and the floor both filter on `metric`. The first night after merge is correct in
the code; I checked it on a pre-W3-shaped artifact. But no test pins it: a mutant that breaks the
carry of every source on that night passes the whole suite (M1). The rest are gaps at the edges:
- one declared board D-164 still leaves unguarded (M2);
- an accessibility disagreement the code does not count (M3);
- an attribute source the refresh never records as arrived (M4);
- agent-board names left out of the curation queue (M5);
- a D-166 claim its test does not check (M6).

**Red first holds.** Each of the five `test:` commits comes before its `feat:` or `fix:` commit:

| red commit | at the red commit | at the next commit |
|---|---|---|
| `1f55e7d` | `ImportError: cannot import name 'boards'` | `26382e6`: 20 passed |
| `2dcb9c7` | collection error | `d63de1f`: 6 passed |
| `5a6285b` | collection error | `2bb90d4`: 8 passed |
| `2472da4` | 12 failed, 2 passed | `e08b965`: 14 passed |
| `8ea2532` | 1 failed (`no such table: access`) | `333542c`: 1 passed |

Two `feat:` commits also edit their red tests.
- `2bb90d4` reorders one assertion and removes a `noqa`.
- `e08b965` corrects one expected id (`gpt4o-mini2024-07-18`, which is what the existing grammar
  gives) and one attribute name (`dropped` to `dropped_names`).

Neither weakens a test. Three of the reds are import or collection errors, not failed behaviour
assertions. That is acceptable for a new module, but it is the weakest kind of red.

## Security look: the D-165 reader's derived column set

`parquet_reader._columns` (`src/app/clients/parquet_reader.py:44-46`) now builds the four columns
from `limits["value_column"]`. Findings:

1. **The limits channel is not attacker-reachable.** `value_column` comes only from a declared
   `ArenaSlice` (`arena_slices.py:134`, `:230-239`). It goes through `reader_limits` (`:91-100`)
   into argv as JSON (`:294`), with no shell. The downloaded bytes go to stdin and never reach the
   limits. A file cannot choose its own value column.
2. **The answer cannot widen.** `iter_batches(columns=list(columns))` (`parquet_reader.py:135`)
   still selects exactly four columns, so `to_pylist` gives four keys per row. A duplicated
   top-level name makes `schema.field` raise, and `read_rows` (`:160-161`) turns that into an
   `error`. The row cap (`:137`), the decode budget (`:140-143`), the text-length cap on the three
   text columns (`:144-149`) and the parent's `read(MAX_ANSWER_BYTES + 1)`
   (`arena_slices.py:312-317`) are all unchanged. The 8 MiB bound holds.
3. **The numeric check did not weaken.** `columns[1]` must be a float or an integer
   (`parquet_reader.py:109-113`), exactly as `rating` was. A dictionary-encoded value is unwrapped
   first. Decimal and bool are refused. The mutant `column == 'rating'` fails
   `test_agent_boards.py:62`.
4. **Nothing non-numeric reaches `scores`.** `score_rows` (`arena.py:381-390`) still refuses a
   non-number, a bool, a non-finite value and a value outside the band. The band is now the
   board's own: IPS `(-1, 1)`, Elo `(0, 5000)`. The mutant "IPS boards use `ELO_BAND`" fails
   `test_agent_boards.py:62`. A huge integer or a NaN from the child is refused by the band and by
   `isfinite`.
5. **One file, one value column.** `parse_arena_slices` refuses boards with mixed value columns
   (`arena_slices.py:393-396`). No test pins this guard (the mutant `if False:` passes the suite).
   Only declared data could trip it today, so I note it under M1 and do not raise it on its own.

**D-105: IPS never meets Elo.** The primary ranking filters `benchmark = :primary AND metric =
:metric` (`rank.py:281`, `:294`). The surface board and floor filter `source, benchmark, metric`
(`floors.py:36-40`). The six agent boards have their own labels, `metric="ips"` and harness
`arena-agent` (`arena_slices.py:150-156`, `arena.py:103-105`).
`test_agent_boards.py:36-43` asserts the following:
- no IPS label is shared with an Elo slice or with any surface's benchmark;
- no category ranks on `ips`.

The secondary-evidence join has no metric filter (`rank.py:299`, `:309`). That is evidence-only by
D-105, and no category names an agent label.

## First night after merge

Each piece checked on an artifact shaped like the one served today (no `access` table):

| path | code | behaviour I observed | pinned by a test? |
|---|---|---|---|
| fingerprint of the live artifact | `access.served` checks `sqlite_master` (`access.py:108-109`) | fingerprints | yes, `test_access.py:132` (red replayed) |
| carry of a failed source | `_live_rows` skips a table the live artifact lacks (`build.py:324-326`) | `epoch_gpqa` → `carried` (age 2.0) | **no** (M1) |
| carry age from the rows | `age_days` lists only tables the live artifact has (`build.py:262-265`) | works | **no** (M1) |
| carry of `epoch_access` itself | `CARRY_TABLES` includes `access` (`build.py:215`) | pre-W3 live → `absent`, and the build goes on (exit 3, which the refresh accepts: `refresh.py:1086`) | **no** (M1) |
| board guards (D-164) | `boards.uncovered()` over 46 boards; a new board's empty live set counts as returning | measured `[]` / `[]` (research §2) | yes, `test_uncovered_boards.py:81-89` |
| moving aliases leave 5 surfaces | D-128, at most 5 of 190 lost | measured (research §3) | n/a, measured |

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/build.py:262-265`, `:324-326`, `:215`, `:307-308`. **The first-night
  carry path has no test, and the mutants that break it pass the suite.** Three mutants each pass
  all 62 carry, access and slice tests, and the third passes all 1391 unit tests:
  1. delete `if not live_cols: continue`;
  2. make `age_days` read every `CARRY_TABLES` table without checking it exists;
  3. drop `access` from `CARRY_TABLES`.

  On the night after merge, mutant 1 or 2 turns every carried source into `absent`: the query on
  the missing `access` table raises, and `restore` swallows it. That is the path the plan names as
  its first risk (`m17-wave-3-plan.md:108-111`). Every carry test builds its live artifact with
  the current schema, so none of them sees a pre-W3 artifact. In the same function, the rollback
  branch still resets a hard-coded `("pricing", "scores")` (`:307-308`) instead of
  `CARRY_TABLES`: the fact is now written in two places. It is harmless today, because the only
  source with `access` rows is `epoch_access`, whose candidate rows are empty whenever it falls
  back. The mixed-value-column guard (`arena_slices.py:393-396`) also has no test. **Fix:**
  1. one test that restores a source from a live artifact with `access` dropped (expect
     `carried`);
  2. one that restores `epoch_access` from a W3-shaped live artifact (expect `carried` with the
     rows);
  3. `CARRY_TABLES` at `:307`.
- **M2** `src/app/workflows/boards.py:36-41`. **`epoch_mmlu` is a declared board that is now in
  neither the D-164 fingerprint nor its guards.** `uncovered()` leaves out any board whose label is
  a surface's secondary benchmark. Its docstring gives the reason: such a board "is already
  covered by that surface's ranking". That is not true for a secondary board. The D-159 board
  guard reads the primary board only (`floors.py:36-40`, `refresh.py:461`). The ranked rows carry
  a secondary value only for models that rank. My probe:
  1. store 8 MMLU rows: the digest does not move;
  2. delete half of them: `degradations` returns `[]`.

  The mutant "primary benchmarks only" passes all 1391 tests, so the choice is not pinned either
  way. D-164 clause 1 says "each declared board", and W4 serves board standings. Minor, because
  MMLU was unguarded before this wave too and is evidence-only. **Fix:** drop
  `secondary_benchmark` from the exclusion, and add a test.
- **M3** `src/app/workflows/access.py:64-73`. **Two rows under the same name that disagree are
  settled by row order, not counted.** `store` writes `INSERT OR REPLACE` under
  `UNIQUE (raw_name, source)` (`schema.py:32-40`). So `x,Open weights (unrestricted)` followed by
  `x,API access` serves `API access`, and the reverse order serves `Open weights`. In both cases
  `conflicting == ()`. I reproduced both. That breaks the wave's own rule, "never guessed"
  (`access.py:7-9`, plan decision 4): a filter would put a model under "open" on file order alone.
  The live file has one duplicated name, whose two rows agree, so the defect is latent. **Fix:**
  1. count a same-name disagreement in `parse_metadata`, or store both rows (drop the `UNIQUE`
     or add `accessibility` to it) so that `link`'s `COUNT(DISTINCT accessibility)` sees it;
  2. one test.
- **M4** `src/app/workflows/build.py:707-711`, `:482`. **`epoch_access` never reaches
  `report.sources`, so the refresh never records it as arrived.** Its `SourceReport` goes to
  `run.reports` only. The stored count is discarded (`_access_stored`). `sources_json()["arrived"]`
  (`build.py:127-129`) and the per-source rows in `as_json` leave it out. Two effects:
  1. `sources_last_ok` never holds `epoch_access` (`refresh.py:670-675`), so its carry age
     always falls back to the rows' `observed_at`, which the `Carry` docstring says "can
     overstate the age" (`build.py:225-227`);
  2. `/health` cannot show when the attribute last arrived.

  The build report does carry `linked`, `unlinked` and `conflicting` (`build.py:725-727`). **Fix:**
  return the `SourceReport` and extend `report.sources` with it, as the boards and slices do.
- **M5** `src/app/workflows/build.py:349-356`. **The six agent boards are left out of the curation
  queue, for a reason that applies only to slices.** `_most_unmatched` leaves out every
  `ARENA_SLICES` source, because "a category slice repeats its `overall` board's names". The agent
  boards are now `ARENA_SLICES` entries, but they are no one's slice: their names are display
  spellings (`GPT 6 Astra (Max)`) that no other source carries. On the author's candidate, each
  agent board has 10 unmatched names, and none can reach `/health`'s `refresh_unmatched`.
  **Fix:** exclude `board.metric == METRIC` slices only, or key the exclusion on "a category of a
  config that has an `overall` board".
- **M6** `docs/decisions.md:3065-3066`, `tests/unit/test_moving_aliases.py:56-64`. **D-166 says a
  moving alias's rows "are named in the unmatched report (`/health`'s `refresh_unmatched`)"; the
  test checks something else, and the claim holds for 1 of 12.** The test asserts
  `report.dropped_names`, which is the reconciler's full list and not what `/health` shows.
  `refresh_unmatched` is `_most_unmatched`: the top 20 by row count, without slices
  (`build.py:340`, `:346-357`). In the author's candidate report (`cand-build.json`), `unmatched`
  names `deepseek-chat` only. The other eleven aliases are unmatched but not listed. Plan P4, "the
  unmatched report names them" (`m17-wave-3-plan.md:100`), is therefore not met as written.
  Separately, `test_a_curated_rule_still_wins_over_the_list` (`:40-46`) checks
  `canonicalize_with_reason`, which never reads `MOVING_ALIASES`, so it cannot fail. A reconcile
  test with a curated rule on a listed alias would. **Fix:** correct D-166's sentence, or append
  it as a clause (supersede, never edit). Or have `/health` list the moving aliases seen. Then add
  a test that can fail.

### Deviations noted, not raised as findings

- Plan decision 4 names the table `model_access(model_id, accessibility, source)`
  (`m17-wave-3-plan.md:72`). The code ships `access(raw_name, model_id, accessibility, source,
  source_url, observed_at)`. The code's shape is the better one, but the plan was not amended.
- Plan P2 lists "the stale-date and hostile-file rules hold for them" (`:92`). No test drives an
  agent file through them. They run on the shared `parse_arena_slices` and reader path, which
  `test_arena_slices.py` covers for `rating` files.
- The agent-file fixture is a bespoke builder (`test_agent_boards.py:46-59`), not the canonical
  fake (`app.clients.fakes.slice_parquet`, which has no `score` column).
- The live contract test is still parametrised `["text", "vision"]`
  (`tests/integration/test_arena_openrouter_contract.py:53`) rather than `SLICE_CONFIGS`, so CI's
  live leg does not see the six agent files. The research record's §6 live smoke run covers them
  once, by hand. See practices, "one canonical mock per integration + a contract test". Worth
  folding into M1's test work.
- D-166 landed in the boards commit `26382e6`, before its own red test. The ADR still came before
  the code.

### PASS (what looks good)

- **D-164 now derives its board set** from `ARENA_SLICES`, `EPOCH_BOARDS` and `CATEGORIES`
  (`boards.py:28-41`). The refresh uses it for the fingerprint and both guards (`refresh.py:223`,
  `:278`, `:468-476`). The rename from `slices` to `boards` reached every caller (grep below).
- **`score_rows`** takes the value key, metric, harness and band as keyword arguments with Elo
  defaults (`arena.py:361-364`), so `parse_arena` is unchanged. The per-board metric comes from one
  declaration (`arena_slices.py:132-156`).
- **The Epoch boards** are five rows of data (`sources.py:297-340`). Each is dated by `Started at`
  (`test_board_run_dates.py:41-46`) and attributed (`rank.py:81-86`, and the existing
  `test_categories.py:238-249` covers every ingested source).
- **One path guard now.** `read_bundle_file` (`epoch_board.py:91-112`) serves both the boards and
  `model_metadata.csv`.
- **`MOVING_ALIASES`** is checked after normalisation (`registry.py:460-461`), so `GPT-4o mini`,
  `claude-3-5-sonnet` and `openrouter/anthropic/claude-3.5-sonnet` are all stopped
  (`test_moving_aliases.py:26-29`), while dated names still derive (`:32-37`). My mutant with
  the gate off (`if False:` at `registry.py:460`) fails 9 tests, as the author's commit says.
- **The measurement record** found a real defect before the pull request (the missing-table
  fingerprint) and fixed it red-first. It also states the first night's losses by surface.
- No drive-by edits outside the plan. No swallowed exceptions added. No `type: ignore` or `noqa`
  added in `src/` beyond the carry query's existing `S608` pattern. No new dependency.

## Acceptance criteria evidence

| plan item | evidence |
|---|---|
| P1: each new Epoch board ingests under its own source and label | `sources.py:297-340`; `test_uncovered_boards.py:29-39`; `test_board_run_dates.py:41-46` |
| P1: an uncovered Epoch board's change publishes | `refresh.py:468-476`; `test_uncovered_boards.py:69-78` |
| P1: an uncovered board losing a quarter is refused; its first night is not | `refresh.py:223`, `:278`; `test_uncovered_boards.py:81-89` |
| P1: the set is derived from `CATEGORIES` | `boards.py:36-41`; `test_uncovered_boards.py:42-59` (secondary exclusion unpinned, M2) |
| P2: the reader's column map | `parquet_reader.py:44-46`, `:97-116`; `arena_slices.py:91-100`, `:393-397`; `test_agent_boards.py:62-74`, `:89-94` |
| P2: `ips` rows under their own metric and band | `arena.py:103-105`, `:381-399`; `test_agent_boards.py:62-68`, `:77-86` |
| P2: six boards declared with floors and ceilings | `arena_slices.py:227-239`; `test_agent_boards.py:26-33`; `test_arena_slices.py:631-638`; `test_build_slices.py:176-178` |
| P2: an `ips` board never joins an `elo` ranking | `rank.py:281`, `:294`; `floors.py:36-40`; `test_agent_boards.py:36-43` |
| P3: the table; additive only | `schema.py:30-40`; `test_access.py:80-91` |
| P3: the reconcile join; disagreement counted | `access.py:76-99`; `test_access.py:60-77` (same-name case open, M3) |
| P3: the fingerprint moves with it; a pre-W3 artifact still fingerprints | `refresh.py:477-479`, `access.py:101-112`; `test_access.py:94-106`, `:132-141` |
| P3: the build reads it through the bundle guard; a missing file is a missing line | `build.py:451-483`; `test_access.py:109-129` |
| P4: each listed alias derives no id | `registry.py:418-432`, `:460-461`; `test_moving_aliases.py:21-29`, `:56-64` |
| P4: a curated rule still wins | `test_moving_aliases.py:40-46` (cannot fail, M6) |
| P4: the unmatched report names them | not met as written (M6) |
| P5: the survey, the served change, `smoke_deps` | `docs/research/m17-w3-boards-and-first-night-2026-09-25.md` §2-§6; `scripts/smoke_deps.py:114-116` derives from `SLICE_CONFIGS` |

## K.8 contract drift check

The plan's K.8 symbols (`m17-wave-3-plan.md:48-60`), at `0f6e136`:

```
src/app/workflows/registry.py:435:def derive_identity(name: str) -> DerivedIdentity | None:
src/app/workflows/registry.py:616:def reconcile(conn: sqlite3.Connection) -> ReconcileReport:
src/app/workflows/refresh.py:469:    for board in declared_boards.uncovered():
src/app/clients/parquet_reader.py:44:def _columns(limits: dict[str, Any]) -> tuple[str, ...]:
src/app/clients/arena.py:41:METRIC = "elo"
src/app/clients/arena.py:103:IPS_METRIC = "ips"
src/app/clients/arena.py:361:def score_rows(
src/app/workflows/schema.py:25:CREATE TABLE IF NOT EXISTS models (
src/app/workflows/schema.py:32:CREATE TABLE IF NOT EXISTS access (
```

Callers of `score_rows`:

```
src/app/clients/arena.py:356:    rows, refused = score_rows(working, source=source, source_url=source_url, benchmark=benchmark)
src/app/clients/arena_slices.py:427:        parsed, bad = score_rows(
```

`grep -rn "\.slices\b" src scripts` returns no attribute use of the renamed `ServingSummary.slices`.

**Verdict: OK.**
- `derive_identity` and `reconcile` moved lines but kept their signatures.
- `_COLUMNS` was private and became `_columns(limits)`.
- `score_rows` gained keyword arguments with defaults: widened compatibly.
- The refresh loop iterates the derived set, as plan decision 1 says.
- `models` is unchanged.
- The one contract deviation is the table name and shape (noted above).

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/registry.py` (`resolve_effort`, `derive_identity`). **A parenthesised
  effort, `GPT 6 Astra (Max)`, `Grok 4.7 (xHigh)` or `Gemini 3.8 Flash (High)`, is neither
  resolved nor derived.** `resolve_effort` returns the name unchanged with `effort=None`, and
  `derive_identity` returns None, because `(` fails the grammar's `fullmatch`. So on each agent
  board, about 10 of 43 rows go unlinked. They include the highest-effort rows of models that are
  registered (`gpt6-astra`, `kimi-k3`). A bug in the effort grammar. It limits what W4 can combine,
  and M5 hides it today.

## Risks queued to next M

- **R1** **Adding a board can rename served models.** The agent boards spell names with spaces, and
  `_derived_display` (D-157) prefers a spaced spelling. So five derived models change their served
  name on the first night (research §3), although the plan says "No surface ... change"
  (`m17-wave-3-plan.md:19`). The ids are unchanged. The surface guards count names, so a board
  that renames many models at once could trip D-128 or D-132 for a reason that is cosmetic. It
  would show as `degradations` citing names that differ only in spelling.
- **R2** **The first night after merge removes twelve derived models from five surfaces** (D-166's
  cost; research §2-§3). Claude 3.5 Sonnet, GPT-4o mini, `o1`, `o1-mini`, `deepseek-chat` and
  others leave the phone's lists. It was measured below D-128's quarter (worst: 5 of 190). A
  source that fails the same night and cannot carry would add to that loss. That is why M1's test
  matters. It would show as the owner seeing those models vanish; the refresh would not refuse.
