---
record_type: review
id: m17-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---
# M17-W2 Code Review -- Arena's category slices become boards (commits 04e2630..78db5e0)

**Reviewer:** Code-Reviewer subagent. I did not write any code in this wave.
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** `04e263025df29d3266e1be29d21c8be09042dc56..78db5e03c48fdd4e6fd71cb21d7759ab2b9dee0a`
(15 commits on `wave/m17-w2`, draft PR #23)
**Risk tier:** MEDIUM (from `docs/plans/m17-wave-2-plan.md`)

**What I read.** I read the plan before the code:
- `docs/plans/m17-wave-2-plan.md`, and `docs/plans/m17-plan.md` §2 W2 and §3 (K.8);
- D-164, plus D-128, D-132, D-154 and D-156, in `docs/decisions.md`;
- `docs/research/m17-w2-slice-survey-2026-09-24.md`;
- issue #22 and issue #24 (the `agent_*` follow-up the plan asked for).

Then I read all 22 changed files in the diff, and the unchanged code each one calls. That includes
`Carry.restore`, `_fall_back`, `_surfaces_left_without_evidence`, `_most_unmatched`, build `main()`,
`refresh()`, `_served_without`, `_mostly_new`, `fetch_bounded_bytes`, `source_health` and every
reader of the `scores` table in `src/`.

**Policy.** My policy came from `.claude/agents/Code-Reviewer.md`, `.agents/rules/practices.md`,
`.agents/rules/review-seats.md` and `permission-matrix.md` §3 and §11. `git diff --stat
04e2630..78db5e0 -- .claude .agents AGENTS.md permission-matrix.md subagent-profiles` is empty, so
the policy I read is the base's. Nothing in the diff addresses a reviewer, so there is no
injection-class finding.

**Families.** The commits carry `GP-Agent: claude-code/local-lane`, and this seat is also Claude.
No second family was available. The tier is MEDIUM, so the cross-model rule is advisory only. My
context was fresh: I did not see the author's session.

**No state changes.** I changed no git state. The only file I wrote in the repository is this one.
I built my probes, mutants and red replays in scratch copies (`git archive` into my scratchpad),
never in the worktree. An untracked security review file for this wave appeared in the worktree
while I worked. Another seat wrote it. I did not read it or touch it.

## Verdict

**BLOCKING -- 2 BLOCKING, 2 MINOR, 3 NIT; 2 K.9 candidates; 2 risks.**

Both BLOCKING items are small to fix: an exception class plus one test for B1, and one argument for
B2. Everything else in the wave is sound, and most of it is well built.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** src/app/clients/arena_slices.py:181-185 -- **the fix for the P2 review's finding is
  incomplete and untested.** A valid 1.3 KB parquet file still takes down the whole nightly cycle.
  - **The claim.** Commit `84165dd` moved `to_pylist()` inside the guard, with the comment "an
    exception that is not a `SourceError` is re-raised by the build on purpose, and would end the
    whole unattended cycle over one bad file". The commit says "No new test: no valid parquet
    file was found that makes the conversion itself fail."
  - **The counterexample.** A valid file does exist. The guard catches only
    `(pa.ArrowException, OSError, ValueError)` (line 183). If `leaderboard_publish_date` is a
    typed `date32` or `timestamp` column holding a value outside Python's date range, `to_pylist()`
    raises `OverflowError: date value out of range`.
  - **How I reproduced it.** On a scratch copy of HEAD, I wrote such a file with `pq.write_table`
    (1,316 bytes, date32 value `-1_000_000`). I ran it through `parse_arena_slices`, and also
    through `build._ingest_slices` with `fake_slice_client`. The traceback ends at
    `_read_table` line 182, and the output was `ESCAPED OverflowError date value out of range`.
    `timestamp('us')` and `timestamp('ms')` values past year 9999 escape the same way.
  - **Why it blocks.** `_ingest_slices` catches only `SourceError`
    (src/app/workflows/build.py:456 and :468). Build `main()` re-raises anything else
    (build.py:840-842). `refresh.main` then records a crash and exits `EXIT_FAILED`
    (src/app/workflows/refresh.py:1226-1231).
    - So one optional board's file stops every source from publishing, every night, until the
      upstream file changes.
    - That contradicts the ingest's own contract at build.py:443-444: "A slice is optional ... it
      never fails the build".
    - Under permission-matrix §11, "a reported symptom must be reproduced with a failing test
      before its fix (red→green)" is a GATE item. The symptom was reported, and the fix shipped
      without a red test.
    - Coverage confirms the new branch never runs: `arena_slices.py` misses lines 183-185.
  - **Fix.** Add `OverflowError` to the tuple at line 183. `ArithmeticError` would also do, and
    keeps the catch narrow, as build.py:831-835 warns it should stay. Add a red test with the
    out-of-range `date32` file in tests/unit/test_arena_slices.py.
  - **Not affected.** Today's live column is a string, so the trigger needs an upstream type
    change plus an absurd value. That is why the product is not broken tonight. The plan's own
    risk line calls this surface "a native parser of a downloaded file", though, and the claim the
    wave makes about it is false.

- **B2** tests/unit/test_survey_floors.py:131-132 -- **a unit test makes real outbound HTTP to
  huggingface.co on every `make test`.** `permission-matrix.md` §3 says "Outbound HTTP from test:
  DENY", and the wave's own conftest says tests stay off the network.
  - **The cause.**
    `test_the_slice_survey_counts_rows_and_the_models_the_engine_can_rank` is marked `slices`, so
    the autouse fixture in tests/conftest.py:54-60 does not empty `build_mod.ARENA_SLICES`. The
    test then builds its fixture artifact with
    `build(conn, ..., sources=_sources(), minimum_models=2)`. It passes no `slices=()` and injects
    no client, so the build downloads both real parquet files through the real
    `ArenaSliceClient`.
  - **Evidence.** I ran the suite with a spy on `httpx.stream`. This test called
    `.../resolve/main/text/latest-00000-of-00001.parquet` and
    `.../vision/latest-00000-of-00001.parquet`. No other slice-marked test did: the respx tests
    were false positives of the spy, and the other slice tests were clean. The test still passes
    either way, because a failed download only becomes an operator line. That is why nobody saw
    it.
    - Online, the test downloads about 645 KB and writes live rows into its fixture.
    - Offline or on a slow network, it waits on a 30 s timeout per file, with a 120 s deadline.
  - **Why the control could not catch it.** The conftest control only covers unmarked tests. The
    test that guards the control (tests/unit/test_build_slices.py:152) checks only the unmarked
    half. Nothing makes a marked test inject a client.
  - **Fix.** Pass `slices=()` at test_survey_floors.py:131. Better still, have the conftest point
    `ARENA_SLICE_CLIENT` at a fake that raises for a marked test that did not inject its own. Then
    the next marked test that forgets fails instead of silently reaching the network.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** docs/prd.md:400-401 -- **REQ-REF-002 and REQ-REF-003 no longer describe what the
  refresh does.**
  - REQ-REF-002's status says "changed" is "Derived through `category_ranking`, the same function
    that serves". The fingerprint now also hashes the raw rows of 35 boards that no function
    serves yet (src/app/workflows/refresh.py:463-474).
  - REQ-REF-003 says the refresh refuses "a loss of more than a quarter of any surface". It now
    also refuses a board (refresh.py:219-225 and :276-279).
  - D-164 says it "Extends REQ-REF-002's 'changed', D-128 and D-132". The requirement rows the
    owner reads were not updated. This is doc drift, which §11 classes as MINOR.

- **M2** src/app/workflows/refresh.py:473 -- **the `model_id` part of D-164 clause 1 has no test
  that fails without it.**
  - D-164 names three things in the fingerprint: the name, "the model it reconciled to (what W4
    serves as the model's identity)", and the score.
  - I built a mutant that drops `{model_id}` from the digest line. It survives all 147 tests in
    `test_refresh_boards.py`, `test_refresh.py`, `test_nightly_refresh.py` and
    `test_refresh_carry.py`.
  - tests/unit/test_refresh_boards.py:79 moves the score and `observed_at`, never the
    reconciliation.
  - The fix is one assertion: `UPDATE scores SET model_id = ...` moves the digest.

### NIT

- **N1** tests/unit/test_arena_slices.py:267-270 -- the docstring says "today it [the server]
  never imports `arena_slices`". Since `ebf0981` it does: `rank.py:19` imports
  `app.clients.arena_slices`, and the server loads `rank`.
  - I checked in a fresh interpreter. `import app.adapter.main` puts `app.clients.arena_slices` in
    `sys.modules`, and `pyarrow` is not there.
  - The test is stronger than its docstring says. Only the docstring is stale.
- **N2** src/app/workflows/build.py:416-426 -- `_slice_failed` repeats the failure block in
  `_ingest_boards` (build.py:396-402) line for line. The "group by config, download, parse" loop is
  also written four times:
  - build.py:447-455;
  - scripts/survey_boards.py:373-379;
  - scripts/smoke_deps.py:82-86;
  - tests/integration/test_arena_openrouter_contract.py:57-60.

  One helper in `arena_slices.py` that returns rows per config would make the four callers one.
- **N3** docs/decisions.md (D-164 clause 2) -- the ADR says a board is refused when "a quarter or
  more of its raw names are ... new (D-132)".
  - D-132 says "more than a quarter", and the code does exactly that:
    `len(fresh) > len(now) * MAX_SURFACE_GAIN` (refresh.py:161), measured against the candidate's
    names.
  - The code is right, and the ADR misquotes it.
  - Don't edit the accepted text. Add a clarification line, the way D-159 got one.

## Acceptance criteria evidence

The plan names no REQ-IDs. Its acceptance criteria are the red-first lists of P1-P4, plus D-164.

**P1 -- the read**
| Criterion | Evidence |
|---|---|
| A small parquet yields each declared slice's rows | tests/unit/test_arena_slices.py:59 |
| The newest-date rule, per slice | test_arena_slices.py:79. Also :112 (an undated file fails closed) and :123 (a typed date column is read) |
| A file over the cap | test_arena_slices.py:198 |
| Not parquet | :140 |
| A missing column | :145 |
| An `Infinity` rating | :101 (with NaN, over the band, and negative) |
| Footer row and byte bounds | :152 and :165 |
| The server does not import `pyarrow` | test_arena_slices.py:263. I checked that it really runs, see N1 |
| `ARENA_SLICES` and `ARENA_SLICE_CLIENT` in the registry | src/app/workflows/sources.py:248 and tests/unit/test_sources.py:60 |
| The `score_rows` extraction is behaviour-preserving | src/app/clients/arena.py:358-398 against base. The loop is identical, and the skipped count is preserved |

**P2 -- the boards**
| Criterion | Evidence |
|---|---|
| No slice's rows reach a served benchmark | tests/unit/test_build_slices.py:69-74 |
| One slice under its floor fails alone | :80 |
| A failed download fails only its config | :98 |
| A failed download carries each slice (D-156) | :110 |
| `build()` reads the table at call time | :136 |
| Distinct benchmark labels | test_arena_slices.py:235 |
| `floor < measured` for every board | :247 |
| Every slice attributed | test_build_slices.py:164 and tests/unit/test_categories.py:245 |

**P3 -- published and guarded (D-164)**
| Criterion | Evidence |
|---|---|
| A board-only change publishes | tests/unit/test_refresh_boards.py:68 |
| The fingerprint moves with a board and ignores restamps | :79 (but see M2) |
| A board losing a quarter is refused | :110 |
| A board a quarter new is refused | :122 |
| A board seen for the first time is not refused | :97 |
| An expired board drops | :143 |
| Movement below both limits publishes | :133 |

**P4 -- measured and recorded**
| Criterion | Evidence |
|---|---|
| The survey | scripts/survey_boards.py:353-411 and tests/unit/test_survey_floors.py:121 (see B2) |
| The research record | `docs/research/m17-w2-slice-survey-2026-09-24.md` |
| `smoke_deps` gains one probe per config | scripts/smoke_deps.py:74-93 and :114-116 |
| The live contract | tests/integration/test_arena_openrouter_contract.py:52-65 |
| The `agent_*` issue | #24 |
| D-164 | docs/decisions.md, end of file, marked "ruled by the owner 2026-09-24" |

**Red to green.** I extracted red commit `9b92171` with `git archive` and ran
`test_refresh_boards.py` on it: **7 failed**. The P3 tests were therefore red before `ab98437`.

**Mutants.**
- Dropping the slice loss guard (refresh.py:277) is killed by test_refresh_boards.py:110.
- Dropping the slice new-name guard (refresh.py:221) is killed by :122.
- Dropping `model_id` from the digest survives (M2).

## Plan compliance

The wave delivers each item of `docs/plans/m17-wave-2-plan.md` §Phases P1-P4 and the seven
"Decisions made on the owner's behalf":
- 1: one fetch per config (build.py:447-457);
- 2: newest date per config (arena_slices.py:207-236);
- 3: ids and labels from one table (arena_slices.py:65-78);
- 4: half-measured floors (arena_slices.py:75-78);
- 5: D-164 (refresh.py:219-225, :276-279 and :463-474);
- 6: the lazy import (arena_slices.py:152-157);
- 7: the 8 MB cap (arena_slices.py:39 and :143-147).

Decision 6 said "extending the D-154 guard to name it". What was built is a new subprocess test
(test_arena_slices.py:263) rather than an edit of
tests/unit/test_nightly_refresh.py:352. It asserts the same property, so this is not a deviation
worth a finding.

Nothing was added or dropped without the plan. There are no drive-by edits. `note.txt` is the
session's resume pointer, and the plan and ADR are the wave's own.

## K.8 contract drift check

`docs/plans/m17-plan.md` §3 declares four contracts: D-104/D-105/D-126, `/v1` additive only, where
arithmetic may happen, and the combined-list disclosure. This wave touches none of them. `git diff
--stat 04e2630..78db5e0 -- src/app/adapter ios schemas` is empty, so there is no `/v1`, app or
schema change.

The wave's own shared names are consistent:
```
src/app/workflows/build.py:53:from app.clients.arena_slices import ARENA_SLICES, ArenaSlice, parse_arena_slices
src/app/workflows/build.py:623:    slices = ARENA_SLICES if slices is None else slices
src/app/workflows/refresh.py:42:from app.clients.arena_slices import ARENA_SLICES
src/app/workflows/refresh.py:467:    for board in sorted(ARENA_SLICES, key=lambda b: b.source_name):
src/app/workflows/rank.py:19:from app.clients.arena_slices import ARENA_SLICES
src/app/workflows/rank.py:65:    **{board.source_name: ARENA_ATTRIBUTION for board in ARENA_SLICES},
src/app/workflows/sources.py:248:ARENA_SLICE_CLIENT = ArenaSliceClient
src/app/workflows/build.py:446:    client_type = ARENA_SLICE_CLIENT if client is None else client
src/app/clients/arena.py:358:    rows, refused = score_rows(working, source=source, source_url=source_url, benchmark=benchmark)
src/app/clients/arena_slices.py:232:        parsed, bad = score_rows(
```
`DECLARED_SLICES` (P1-review M4) is gone everywhere. `parse_arena`'s public signature is unchanged.

**Boundary (D-001/K.1).** `arena_slices.py` imports only `app.clients.*` and
`app.workflows.schema.ScoreRow`, the same as `arena.py:25` and `epoch_board.py:32`. Network access
goes only through `fetch_bounded_bytes`.

**Verdict:** OK, nothing drifted.

## Hardened-invariant producers (D-164: a board is fingerprinted and guarded)

Only HIGH waves require this section, but it helps here, so I include it.

Rows reach `scores` under a slice `source` from three producers:
- `_ingest_slices` (build.py:429). Tests: test_build_slices.py:56, :80, :98 and :136.
- `Carry.restore` for a carried slice (build.py:264). Test: test_build_slices.py:110.
- `measure_slices`, which writes only to a scratch copy (scripts/survey_boards.py:353). Test:
  test_survey_floors.py:121.

There is one consumer, `serving_summary` (refresh.py:463-474), and both guards read it.

**Gaps:** the `model_id` component (M2).

## Integration checks with no finding

- **Readers of `scores` in `src/`.** I checked every one:
  - `rank.py` and `adapter/main.py:773` select by a surface's benchmark;
  - `/health`'s source list is keyed on the benchmark (main.py:771-777);
  - `adapter/main.py:252` counts distinct models, and slices are subsets of `overall`;
  - `recommend.py:226` takes a MAX date, which slices share.

  None of them lets slice rows reach a surface.
- **`ci_coverage_gate.py`.** A failed slice produces an "(no surface names it as primary)"
  operator line. It carries no "must disclose" marker, so the CI coverage gate does not read it as
  a blinded surface.
- **First night.** The live summary reports each of the 35 boards as an empty set, so
  `_mostly_new` passes them as returning (D-164 clause 3). test_refresh_boards.py:97 covers it.

## K.9 candidates spotted outside this wave's scope

- **K1** Dockerfile:13 -- `pip install .` puts every runtime dependency into the serving image,
  so `pyarrow` (126 MB in `.venv`) now ships to a host where D-116 and D-154 clause 2 forbid the
  refresh from ever running.
  - The server never imports it (N1 checked this), so the cost is image size and a scanner
    surface, not behaviour.
  - An `ingest` optional extra would keep it off the serving image. That changes the Dockerfile,
    CI install lines and the refresh wrapper, which is beyond W2's scope.
  - Enhancement.
- **K2** src/app/workflows/build.py:331-335 -- `_most_unmatched` ranks the curation queue that
  `/health` and the refresh record show by ROW count.
  - An unmatched Arena text name can now count up to 27 rows (`overall` plus 26 slices), against 1
    to 5 for a name on other boards.
  - I measured the upper bound on a scratch copy of the worktree's `advisor.db`, copying every
    `arena` or `arena_vision` row into each slice. Arena names in the top 20 went from 15 to 20.
  - The queue was already mostly Arena, so the harm is small. It will still hide the non-Arena
    names the queue exists to surface.
  - Counting distinct benchmark families, or leaving slice sources out of the count, fixes it.
  - Enhancement.

## Risks queued to next M

- **R1** **Partial upstream publishes.** A slice is served only on its config's newest date
  (arena_slices.py:214-236), and slices already lag: `vision/creative_writing` has no rows on the
  newest date. If upstream publishes a new date for `overall` before the slices, every lagging
  slice falls under its floor. It then carries, and after 30 days it expires. **It is real if**
  refresh records show `arena_*_*` sources in `carried` on nights when `arena` arrived.
- **R2** **Thin vision boards can hold back a whole night.** `arena_vision_captioning` has 34
  rows, so D-128's quarter is 9 names. One noisy upstream day on a thin board refuses the entire
  publish, including every surface's fresh data. This is D-164's stated cost. **It is real if** a
  refusal naming `board arena_vision_*` happens more than once in a month, which is D-164's own
  revisit trigger.

## Gates

`make check-fast` on the worktree at HEAD `78db5e0`: **PASS, 6/6 legs, 59.7 s.**
- lint, typecheck, records (including `wave-check-all` and `conformance`), client-decls and
  swift-test all passed.
- test: **1273 passed, 17 skipped**, total coverage 91%.
- Touched modules:
  - `arena_slices.py`: 97%, missing lines 183-185 (see B1);
  - `build.py`: 94%;
  - `refresh.py`: 96%.
- coverage-floor: PASS, 37 modules.

## What I did not check

- **The live contract test and `smoke_deps` against the network.** I did not run
  tests/integration/test_arena_openrouter_contract.py:52 or scripts/smoke_deps.py. The research
  record reports the live measurement.
- **A real nightly cycle with the slices, or the research record's numbers.** Those would need the
  live download.
- **Supply-chain questions about `pyarrow>=21.0`** (slopsquat, pip-audit, native-parser hardening).
  That is the security seat's work, and the plan names a security look at P1.
- **Test adequacy beyond the mutants above.** That is the Tester's seat, which runs next.
