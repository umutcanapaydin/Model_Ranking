---
record_type: review
id: m17-closure-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-29
---
# M17 Closure Tester Review

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the closure's code, tests or
records. It is not the closure security seat and not the milestone repo reviewer.
**Independent:** yes
**Date:** 2026-09-29
**Commit range:** `3f2e91d..5ae512f` (branch `enhancement/m17-closure`). The code commits are
`cc28d63` (red) → `de2fc38`, `f7a05d2` (red) → `8383001`, and `6d57e5e`. The other five commits
touch only `docs/` and `note.txt`.
**Scope:** the closure's code changes, each against its test. The records are graded only where
they make a claim about that code.
**Risk tier:** not a wave. The changes answer the Stage 4.0 security seat's MINOR-1 and MINOR-2
(`docs/reviews/m17-closure-security-review.md:128`, `:187`) and the milestone review's M1 and M16
(`docs/reviews/m17-repo-review.md:55`, `:251`), plus the `app.sh` defect the owner found.
**Base-pinned policy:** `git diff --stat 3f2e91d..5ae512f -- .claude .agents AGENTS.md
permission-matrix.md .github` is empty, so every rule applied here is the base ref's.
**Method:**
- Pre-fix code was read from `git archive` copies of `3f2e91d`, `cc28d63`, `de2fc38`, `f7a05d2` and
  `8383001`, extracted into the seat's scratchpad. No checkout, restore, stash or reset was used.
- Each mutant was applied in place by one exact string replacement and asserted unique. The seat
  ran the named tests, or the whole suite (`-n auto`, with `MODEL_RANKING_REQUIRE_ARTIFACT=1` as
  `make test` sets it). It then wrote the original bytes back and checked sha256 against the
  pre-mutation hash. All 36 restores matched.
- After the last mutant, `git hash-object` equals `HEAD:<path>` for all 12 files touched. The
  artifact copy `advisor.db` still hashes `005855fa79ec…`.
- `ios/app.sh` was not run, and the simulator, launchd and port 8080 were not touched.

## Verdict
PASS-WITH-MINORS

**Every code change in the range has a test that fails without it, and each red test fails on its
red commit and passes on its fix commit.** Nothing regressed:
- `make check-fast` passes at `5ae512f`: 1531 passed and 23 skipped, Swift 354. Lint, typecheck,
  records and client-decls all pass.
- No test line was removed or weakened in the range.
- The new date rule changes none of the 13,902 stored dates in the served artifact copy.
- The finite check would refuse none of its scores.

**Of 36 mutants, 26 die on the change's own tests. 2 more (C3, C4) pass the M1 test and die only
elsewhere in the suite. 8 survive the whole suite.**
- Two are spellings of INV-23 that the new gate does not see (**T1**). One is a served route reached
  through `schema.connect`, the writable opener that migrates on open. The other is an aliased
  `sqlite3` import.
- Three are writes inside the functions the gate allowlists (**T2**).
- Two are the M16 fix, which has no test (**T4**).
- One is an `app.sh` verb outside the test's list (**N1**).

M1's walker also misses two ways to declare a metric (**T3**). None of these is a defect in shipped
code, and each fix is small.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `5ae512f`. Mutant ids are defined under "Fault injection".

**Security MINOR-2: a stored date is a calendar date or nothing** (`src/app/workflows/ingest.py:105`,
applied at `:159`)
- `tests/unit/test_stored_scores_are_bounded.py:51` checks a date, a datetime, `<script>`, an
  impossible date, 3,960 characters and the empty string. `:66` runs through `parse_arena`, and `:77`
  through `parse_verified`. GREEN.
- A1 (identity), A2 (no `[:10]`), A3 (the old truncation, `arena.py:400`'s shape) and A4 (the rule
  not applied at the insert) are each killed.

**Security MINOR-2: a non-finite score refuses its source** (`ingest.py:133`)
- `test_stored_scores_are_bounded.py:58` covers `inf`, `-inf` and `nan`, and asserts that no row is
  stored. `:77` covers SWE-bench's `Infinity`. GREEN.
- A5 (check removed), A6 (`isinf` only), A7 (`== inf` only) and A8 (the row dropped silently, not
  refused) are each killed.
- A refused source is carried, as the comment at `:130-132` says. `_store_scores` raises before its
  `with conn:`, and every build caller catches `SourceError` and falls back to the carry
  (`src/app/workflows/build.py:203`, `:432`, `:526`).

**Security MINOR-1: only the named writers open a database without `open_readonly`**
(`tests/unit/test_readonly_uri.py:136`)
- GREEN. It kills the seat's seven surviving INV-23 mutants, all of them re-applied here:
  - I1 → B1, `/v1/boards` at `src/app/adapter/main.py:1409`;
  - I1w → B2;
  - I2 → B13, `/v1/categories` at `:1262`;
  - I3 → B10, the boot check at `:228`;
  - I6 → B9, `fingerprint_of` at `src/app/workflows/refresh.py:516`;
  - I4 → B14, `_served_without` at `:944`;
  - I8 → B15, `survey_boards --floors` at `scripts/survey_boards.py:427`.
- Reverting any of the three readers this closure moved is killed: B4 (`recommend.py:643`), B5
  (`coverage.py:290`) and B6 (`calibrate_board.py:153`).
- B7 and B8 survive (**T1**). B11, B12 and B16 survive (**T2**).
- **The three readers run read-only against the real artifact.** On a scratch copy of `advisor.db`:
  - `calibrate_board.py --self-check`, `recommend --task coding`, `recommend --task assistant
    --subscription` and `coverage --today 2026-09-29` each exit 0;
  - the copy's sha256 is unchanged afterwards, and no `-journal` or `-wal` file is left.
- `--self-check` on a missing path now fails without creating a file. The seat had measured a
  0-byte database there (`m17-closure-security-review.md:161-162`).

**Security MINOR-1: `/v1/boards` and `/v1/categories` leave the artifact byte-identical**
(`tests/unit/test_api_v1.py:744`)
- GREEN. B2 (`/v1/boards` writes on each GET) and B3 (`/v1/categories` writes) are each killed.
- B3b writes through `schema.connect`, which the gate cannot see, and it is killed by this test
  alone. So the `/v1/categories` case holds up on its own.

**Milestone review M1: every declared metric has a direction** (`tests/unit/test_board_standings.py:552`)
- GREEN. C1 (an Epoch board's metric changed at `src/app/workflows/sources.py:283`) and C2 (`ips`
  dropped from `HIGHER_IS_BETTER`, `src/app/workflows/standings.py:34`) are each killed.
- C3 and C4 pass this test (**T3**).

**Milestone review M16: `calibrate_board` prints the shipped floor by `floors.top_third`**
(`scripts/calibrate_board.py:88`, `:239`)
- No test. E1 and E2 survive the whole suite (**T4**).
- The code itself is right. `floor_shipped` is `top_third` over every parsed row, which is
  `derived_floor`'s rule (`src/app/workflows/floors.py:56-58`) over the rows the build would store.
- `threshold_candidates` and `board_third_D145` compute what the two private copies computed:
  the same index and the same rounding for n = 1, 2 and 3 and above.

**`ios/app.sh` addresses the simulator it boots by name**
(`tests/unit/test_engine_service.py:332`)
- GREEN. It covers all five app commands (`ios/app.sh:124-126`, `:161`, `:183`).
- D1 (`install`), D2 (`spawn`), D3 (`terminate` in `down`) and D5 (`booted` through a variable) are
  each killed. D4 survives (**N1**).

## Red→green on reported symptoms
- **MINOR-1 and MINOR-2, red at `cc28d63`** (a `git archive` copy):
  - 11 tests fail: five date cases, the three non-finite cases, both parser tests and the gate.
  - The gate names exactly `calibrate_board.py::_self_check`, `coverage.py::main` and
    `recommend.py::main`, as the commit message says.
  - At `de2fc38` the same four files pass: 84 passed.
- **One precision about `nan`.** At `cc28d63`, NaN was already refused. SQLite stores it as NULL, and
  the NOT NULL constraint raised a `SourceError` ("violates schema constraints"). The `nan` case is
  red there only on its `match="finite"`. `inf` and `-inf` were stored.
- **`app.sh`, red at `f7a05d2`:** it fails with `['booted', 'booted', 'booted', 'booted', 'booted']`,
  and passes at `8383001`.
- **Guards with no symptom.** The two bytes cases and the M1 walker pass on pre-fix code, as
  `cc28d63`'s message says. No defect existed there to reproduce. That they can fail is shown by B2,
  B3, B3b, C1 and C2.
- **Weakened or deleted tests:** `git diff 3f2e91d..5ae512f -- tests ios/EngineTests conformance`
  removes no line. The only edit to an existing line is `8383001` moving `import re` into sorted
  order.

## Behaviour regression checks

**Can `_calendar_date` drop a date a real client relies on? No.**

| Client | How it writes `run_date` | In the served artifact copy |
|---|---|---|
| Epoch (the SWE-bench run) | `started.date().isoformat()`, `src/app/clients/epoch.py:172` | `epoch_swe_bench_verified`: 33 × `YYYY-MM-DD` |
| Epoch boards | validated, `epoch_board.py:200-207` | 12 sources, `YYYY-MM-DD` or NULL (four boards undated by design) |
| Aider | validated, `aider.py:52-61` | 68 × `YYYY-MM-DD` |
| DeepSWE | always `None`, `deepswe.py:149` | stored under `epoch_deepswe_external`, 68 × NULL |
| SWE-bench | the whole string, `swebench.py:104` | 173 × `YYYY-MM-DD` |
| Arena overall (`ARENA_BOARDS`) | `str(pub)[:10]`, `arena.py:400` | 6 sources, 848 × `YYYY-MM-DD` |
| Arena slices and Agent Arena | validated, `arena_slices.py:372-380` | 41 sources, 10,703 × `YYYY-MM-DD` |
| LiteLLM, OpenRouter | build no `ScoreRow` (pricing only) | n/a |

- Across all 13,902 rows and 63 sources, `_calendar_date(run_date) == run_date` holds for every row.
- The recorded SWE-bench snapshot (`data/m5-swebench-baseline.json`) parses to 173 rows, all
  `YYYY-MM-DD`, and none changes.
- The one change for a well-formed value is intended: a full timestamp is kept as its date
  (`test_stored_scores_are_bounded.py:44`). No client in the table produces one.

**Can the finite check refuse a real source today? No.**
- All 13,902 scores in the artifact copy are `typeof = real` and finite.
- The SWE-bench snapshot has none that are not finite.
- The Arena parser already skips a non-finite rating (`arena.py:386`).

**The suite:**
- `make check-fast` at `5ae512f` passes:
  - pytest 1531 passed and 23 skipped;
  - Swift 354 tests, matching the manifest;
  - lint, typecheck, records and client-decls pass.
- `00f9423..5ae512f` touches only docs, so this is the same code the report measured.

**Coverage on touched code:**
- `ingest.py` 96.3%. The new lines (`:105-115`, `:133-135`, `:159`) are all covered.
- `coverage.py` 94.3% and `recommend.py` 95.4%, with the changed lines covered.
- `ingest.py:168-170`, the `IntegrityError` path, is now uncovered, because NaN no longer reaches it
  (**N3**).

## The closure report's claims about the code

| Claim (`docs/closure-report-m17.md`) | Holds? |
|---|---|
| `:34` citing tests `test_stored_scores_are_bounded.py:51` and `test_readonly_uri.py:136` | Yes. Both lines are the test definitions. |
| `:90` pytest 1531 passed / 23 skipped, Swift 354 | Yes, reproduced at `5ae512f`. |
| `:94-95` MINOR-1 and MINOR-2 fixed, each red first | Red first: yes. "Fixed": the seat's remedy steps 1, 3 and 4 were done. Step 2, a runtime watcher through the served readers (`m17-closure-security-review.md:181-182`), was not done, and the report does not say so. Its absence is why B7 and B8 survive (**T1**). |
| `:94` "INV-23 gate on every reader" (and the gate's docstring, `test_readonly_uri.py:137`) | Only for `sqlite3.connect` spelled so (**T1**). |
| `:108` M1 fixed (`cc28d63`), M16 fixed (`6d57e5e`) | M1: yes, with a walker narrower than the review's disposition (**T3**). M16: the code is right but unpinned (**T4**). |
| `:113-114` `app.sh` red `f7a05d2` → fixed `8383001` | Yes. |
| `:136-137` a board with an undeclared metric "is now gated" | Yes, for a metric declared as a `*METRIC` constant or a `metric=` string (**T3**). |

## Mocks / contract tests
- No integration or test double changed in the range, so nothing applies.

## BLOCKING
- none

## MINOR (the author fixes each in this closure or files it as an issue)

- **T1** `tests/unit/test_readonly_uri.py:120-122` and `:137`: the INV-23 gate matches only a call
  spelled `sqlite3.connect`.
  - **What survives.** `/v1/boards` opening the artifact through `app.workflows.schema.connect`
    passes all 1531 tests (B7). That opener's own contract is read-write and migrate-on-open
    (`src/app/workflows/schema.py:428-440`), and `src/app/adapter/main.py:350-352` names it as what a
    serving path must never use (W-009). An aliased `import sqlite3 as _sq` also passes all 1531
    tests (B8).
  - **Why the bytes tests stay green.** Their fixture is always at the current schema.
    `schema.connect`'s `BEGIN IMMEDIATE`, DDL, `migrate()` and commit then change no byte, so both
    `test_api_v1.py:727` and `:744` pass under B7. They could only catch it against an older-schema
    artifact.
  - **What the gate says.** Its docstring and the report (`closure-report-m17.md:94`) say "every
    reader". The seat's remedy step 2, a runtime watcher, would kill both mutants. It was not done
    and is not recorded as deferred.
  - **Remedy (either):**
    - have the gate also refuse a call to `schema.connect` outside a named writer (`build.py:883`
      gets an entry, and `connect()` with no argument is `:memory:`), and resolve `sqlite3` aliases
      and `from sqlite3 import connect`;
    - or do remedy step 2.

    Then correct the report's line.

- **T2** `tests/unit/test_readonly_uri.py:107-109`, `:132`, `:140` and `:145`: the allowlist is
  keyed by file and function, and each entry's reason goes unchecked.
  - **The count is never read.** `_connect_calls` counts the calls per key, but the test compares
    only key sets.
  - **What survives the whole suite:**
    - B16, a second `sqlite3.connect(args.db)` that writes, added to `calibrate_board.main`;
    - B11, `calibrate_board.main` opening the operator's `--db` (default `advisor.db`) instead of its
      scratch copy (`scripts/calibrate_board.py:210`), then storing the fetched rows into it;
    - B12, the same change in `survey_boards.measure` (`scripts/survey_boards.py:250`).
  - **What the reasons claim.** "A scratch copy the script makes, never the artifact". Nothing holds
    that.
  - **Remedy:**
    - compare the counts;
    - in `tests/unit/test_calibrate_board.py:103`, the one test that runs `main()`, assert that the
      `--db` file's bytes are unchanged. `survey_boards.measure` has no test that runs it; its
      sibling `measure_slices` does (`tests/unit/test_survey_floors.py:143`), and the same assertion
      belongs there.

- **T3** `tests/unit/test_board_standings.py:542-548`: the metric walker reads only an `ast.Assign`
  to a `*METRIC` name and a `metric=` string keyword.
  - **Survivors.** A dataclass field default (`ast.AnnAssign`) passes the test (C3). That is the shape
    `ArenaSlice.metric: str = METRIC` already has (`src/app/clients/arena_slices.py:135`). So does a
    constant whose name does not end in `METRIC` (C4, at `arena.py:103`).
  - **Why the suite still caught them.** Only through tests that pin the existing boards' metric
    values (`tests/unit/test_agent_boards.py`, `test_arena_slices.py`, `test_build_slices.py`). A new
    board would have no such pin.
  - **What the review asked for.** Its disposition (`docs/reviews/m17-repo-review.md:72-74`) was to
    walk the registries: SOURCES, ARENA_SLICES and the Epoch boards.
  - **Remedy:** walk the registries at run time, or at least read `ast.AnnAssign`.

- **T4** `scripts/calibrate_board.py:88` and `:239`: milestone review M16's fix has no test.
  - **E1.** E1 computes `floor_shipped` by the retired D-145 rule, the exact defect M16 named. All
    1531 tests pass.
  - **The fixture cannot tell the rules apart.** The one `main()` test's four rows
    (`tests/unit/test_calibrate_board.py:94-97`) give 1320.0 under both rules. An assertion added
    there would not separate them either.
  - **E2.** E2 (the `min_quality` candidate zeroed) also survives. `_self_check` has no test at all.
  - **Remedy.** Assert `floor_shipped == floors.top_third(<every row>)` on a fixture where the
    distinct-model third and the every-row third differ, for example a model listed under two names
    near the one-third cut.

## NIT
- **N1** `tests/unit/test_engine_service.py:339`: the regex names four verbs.
  - `xcrun simctl uninstall booted "$BUNDLE"` added to `build_and_launch` passes the whole suite
    (D4). Refusing `booted` after any `simctl` verb, rather than after four named ones, closes it.
  - The test pins spelling only. That `simctl` resolves `"$DEVICE"` by name is shown by the owner's
    use (`docs/process-log.md:586-587`), not by a test. This seat did not run it.
- **N2** `src/app/workflows/build.py:274-315`: `Carry.restore` copies a live artifact's rows
  verbatim, so a carried row never meets `_calendar_date` or the finite check.
  - "Every client meets here" (`ingest.py:106`) is true of clients, not of carried rows.
  - The served artifact copy holds no row either rule would change, so nothing can be carried in
    past them today.
  - The security seat's third remedy leg for MINOR-2, a negative test through `/v1/boards`, was not
    added. The storage tests prove the rule without it.
- **N3** `src/app/workflows/ingest.py:133`: `math.isfinite` raises `TypeError` on a non-numeric
  score.
  - A `None` score used to surface as `SourceError` through NOT NULL, at `:168-170`, a path now left
    uncovered.
  - No parser can produce one: each coerces with `float()`, `ScoreRow.score` is typed `float`, and
    every stored score is `real`.

## Fault injection

Hashes are the first 12 hex digits of sha256. "restored" means the post-restore hash equals the
pre-mutation hash. "Suite" means the whole pytest suite (`-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`).

| Id | File:line | Mutation | Run against | Result | Restored |
|---|---|---|---|---|---|
| A1 | `ingest.py:112` | `_calendar_date` returns its input | `test_stored_scores_are_bounded.py` | RED, 6 failed | `be7e353cce95` |
| A2 | `ingest.py:112` | no `[:10]` | same | RED, 1 failed (the timestamp case) | `be7e353cce95` |
| A3 | `ingest.py:112` | `value.strip()[:10]`, unvalidated | same | RED, 5 failed | `be7e353cce95` |
| A4 | `ingest.py:159` | `r.run_date` stored raw | same | RED, 7 failed | `be7e353cce95` |
| A5 | `ingest.py:133` | finite check removed | same | RED, 4 failed | `be7e353cce95` |
| A6 | `ingest.py:133` | `math.isinf` only | same | RED, 1 failed (`nan`) | `be7e353cce95` |
| A7 | `ingest.py:133` | `== math.inf` only | same | RED, 2 failed | `be7e353cce95` |
| A8 | `ingest.py:135` | `continue` instead of raise | same | RED, 4 failed | `be7e353cce95` |
| B1 | `main.py:1409` | `/v1/boards` on `sqlite3.connect` (seat I1) | gate, both bytes tests | RED, the gate | `04f1b87d7dfa` |
| B2 | `main.py:1409` | as B1, plus a `CREATE TABLE` and commit per GET (I1w) | same | RED, the gate and bytes `[/v1/boards]` | `04f1b87d7dfa` |
| B3 | `main.py:1262` | `/v1/categories` writes per GET | same | RED, the gate and bytes `[/v1/categories]` | `04f1b87d7dfa` |
| B3b | `main.py:1262` | as B3, through `schema.connect` | same | RED, bytes `[/v1/categories]` only | `04f1b87d7dfa` |
| B4 | `recommend.py:643` | CLI on `sqlite3.connect` | gate | RED | `448e0fe01b86` |
| B5 | `coverage.py:290` | CLI back to its hand-built `?mode=ro` line | gate | RED | `feafb8c4a59b` |
| B6 | `calibrate_board.py:153` | `_self_check` on `sqlite3.connect` | gate | RED | `c5e094a2a6ce` |
| B7 | `main.py:1409` | `/v1/boards` on `schema.connect` | gate, bytes; then suite | **GREEN**, 1531 passed (**T1**) | `04f1b87d7dfa` |
| B8 | `main.py:1409` | `/v1/boards` on `import sqlite3 as _sq` | gate, bytes; then suite | **GREEN**, 1531 passed (**T1**) | `04f1b87d7dfa` |
| B9 | `refresh.py:516` | `fingerprint_of` on `sqlite3.connect` (I6) | gate | RED | `5009cb5c3f00` |
| B10 | `main.py:228` | boot check on `sqlite3.connect` (I3) | gate | RED | `04f1b87d7dfa` |
| B11 | `calibrate_board.py:210` | `main` stores into `args.db`, not the scratch copy | suite | **GREEN**, 1531 passed (**T2**) | `c5e094a2a6ce` |
| B12 | `survey_boards.py:250` | `measure` stores into `db`, not the scratch copy | suite | **GREEN**, 1531 passed (**T2**) | `d33e06ff5b06` |
| B13 | `main.py:1262` | `/v1/categories` on `sqlite3.connect` (I2) | gate | RED | `04f1b87d7dfa` |
| B14 | `refresh.py:944` | `_served_without` on `sqlite3.connect` (I4) | gate | RED | `5009cb5c3f00` |
| B15 | `survey_boards.py:427` | `--floors` on `sqlite3.connect` (I8) | gate | RED | `d33e06ff5b06` |
| B16 | `calibrate_board.py:183` | an extra `sqlite3.connect(args.db)` write in `main` | gate, `test_calibrate_board.py`; then suite | **GREEN**, 1531 passed (**T2**) | `c5e094a2a6ce` |
| C1 | `sources.py:283` | `epoch_eci` metric `ECI v2` | M1 test | RED | `70f64cd22fb3` |
| C2 | `standings.py:34` | `ips` dropped from `HIGHER_IS_BETTER` | M1 test | RED | `534b0d20409f` |
| C3 | `arena_slices.py:135` | field default `metric: str = "elo_v2"` | M1 test; then suite | M1 test GREEN (**T3**); suite RED, 5 failed | `0c75d0dbac89` |
| C4 | `arena.py:103` | `_KIND = "ips_v2"`, `IPS_METRIC = _KIND` | M1 test; then suite | M1 test GREEN (**T3**); suite RED, 7 failed | `8f8c1dd11cab` |
| D1 | `app.sh:125` | `install booted` | `app.sh` test | RED | `3dbd4c407373` |
| D2 | `app.sh:183` | `spawn booted` | same | RED | `3dbd4c407373` |
| D3 | `app.sh:161` | `terminate booted` in `down` | same | RED | `3dbd4c407373` |
| D4 | `app.sh:124` | an added `simctl uninstall booted` | same; then suite | **GREEN**, 1531 passed (**N1**) | `3dbd4c407373` |
| D5 | `app.sh:126` | `SIM=booted; simctl launch "$SIM"` | same | RED | `3dbd4c407373` |
| E1 | `calibrate_board.py:239` | `floor_shipped` by the retired D-145 rule | suite | **GREEN**, 1531 passed (**T4**) | `c5e094a2a6ce` |
| E2 | `calibrate_board.py:88` | `min_quality` candidate fixed at 0.0 | suite | **GREEN**, 1531 passed (**T4**) | `c5e094a2a6ce` |

## Tests added/extended this review
- None. This seat's brief lets it write only this verdict file, so the missing tests are the
  remedies of **T1** to **T4** and **N1**, for the author to add or file.
