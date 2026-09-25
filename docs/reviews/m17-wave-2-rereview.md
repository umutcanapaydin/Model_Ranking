---
record_type: review
id: m17-wave-2-rereview
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---
# M17-W2 fix round -- independent re-review (commits 78db5e0..b4e41f2)

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, none of the fix round,
and neither the first review nor the security look.
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** fix round `78db5e0..b4e41f2`:
- `ac7bf89`: the red tests;
- `0b7a535`: the fix;
- `b4e41f2`: the two review files.

I also read the whole wave `04e2630..b4e41f2`, at a lighter depth.
**Risk tier:** MEDIUM (`docs/plans/m17-wave-2-plan.md:11`)

**What I read.** I read these before the code:
- the plan;
- D-164 (`docs/decisions.md:2983`);
- `docs/reviews/m17-wave-2-review.md` (the review) and `docs/reviews/m17-wave-2-security.md` (the
  security look);
- `.claude/agents/Code-Reviewer.md`, `.agents/rules/practices.md`, `.agents/rules/review-seats.md`
  and `permission-matrix.md` §11.

`git diff --stat 04e2630..HEAD -- .claude .agents AGENTS.md permission-matrix.md subagent-profiles` is
empty, so the policy I read is the base's. Nothing in the diff addresses a reviewer, so there is no
injection-class finding.

**Families.** The commits carry `GP-Agent: claude-code/local-lane`, and this seat is also Claude. No
second family was available. At MEDIUM tier the cross-model rule is advisory only. My context was
fresh.

**How I worked:**
- **Mutants.** I ran them in place in the worktree through a script. For each mutant, the script
  saved the file's bytes, applied the mutant, ran the tests, wrote the original bytes back and
  compared SHA-256. All nine came back byte-identical. I used no `git checkout` or `git restore`.
- **Hostile files and the red replay.** I built the hostile parquet files and did the red replay in
  my scratchpad. The replay used a `git archive` of `ac7bf89`.
- **No state changes.** `git status --short` is empty apart from this file. I made no commit.
- **Network: a disclosure.** Three test runs of mine fetched
  `huggingface.co/.../text/latest-00000-of-00001.parquet`, a read-only GET of a public file.
  - They were the red replay of `ac7bf89` (twice) and the `conftest` mutant.
  - In each, `test_a_marked_test_that_injects_no_client_cannot_reach_the_network` ran with the real
    client and downloaded the file before it failed. That is MINOR-R2 below. I did not intend these
    requests.
  - Every run of the suite at HEAD made zero non-loopback connections (see B2).

## Verdict

**BLOCKING: 1 BLOCKING, 2 MINOR, 3 NIT; 0 K.9; 1 risk.**

Seven of the eight review findings are fixed with tests that fail without the fix: B1, B2, M1, M2,
N1, N2 and K2. N3 is fixed, with a caveat (NIT-R3). Of the security findings, S1 and S5 are fixed.
S2 and S4 are only partly fixed:
- **S2.** The dictionary half, S2(a), is fixed. The forged-footer half, S2(b), is not. The fix
  commit's evidence for S2(b) comes from a file whose values are all identical, so the length check
  refused it rather than the budget. With distinct values, the new read peaks as high as the old
  one did. The residual that the code, the plan and the S2 disposition (#27) describe as "one page"
  is really the whole column's decoded bytes. See BLOCKING-R1.
- **S4.** Only future dates are refused. A malformed date string that sorts below tomorrow still
  becomes the newest date. See MINOR-R1.

## Disposition of the first-round findings

| Finding | Claimed | Verified? | Test that fails without the fix (mutant run in place, restored byte-identical) |
|---|---|---|---|
| B1 / S1: non-`SourceError` escapes | every failure is a `SourceError`, plus column types | **yes** | Mutant "catch-all narrowed to `(OSError, ValueError)`" fails `test_arena_slices.py:159`. Mutant "type check disabled" fails all 6 cases of `:150`. `test_build_slices.py:175` drives the review's date32 file through `_ingest_slices`, and `vision/ocr` is still stored. I re-ran every hostile type from the security look's S1 table: all are refused as `SourceError` (see "Hostile inputs") |
| B2: a marked test reached the network | a refusing client for marked tests; survey builds with `slices=()` | **yes** | Mutant "conftest monkeypatch removed" fails `test_build_slices.py:200`. I ran the whole suite (1285 tests) under a socket and DNS spy: **0 non-loopback connects, 0 lookups**. A positive control recorded a connect. See MINOR-R2 for how the canary behaves when it trips |
| M1: PRD drift | REQ-REF-002/-003 name D-164 | **yes** | `docs/prd.md:400-401`. The wording matches the code: loss `>=` a quarter (`refresh.py:178`), new `>` a quarter (`refresh.py:162`) |
| M2: `model_id` untested in the digest | assertion added | **yes** | Mutant "drop `{model_id}` from the digest line" fails `test_refresh_boards.py:96` |
| N1 / S5: stale sentences | fixed | **yes** | `arena_slices.py:17`, `test_arena_slices.py:329-335`. A new stale sentence appeared at `pyproject.toml:119` (NIT-R1) |
| N2: duplication | `fetch_slices` and `_board_failed` | **yes** | One path, `arena_slices.py:157-164`. Its callers are `build.py:453`, `survey_boards.py:375`, `smoke_deps.py:85` and `test_arena_openrouter_contract.py:59`. The Epoch boards and the slices share `build.py:369-380` |
| N3: D-164 misquotes D-132 | corrected in place | **yes, with a caveat** | `docs/decisions.md:2998-2999`. See NIT-R3 |
| K2: slices crowd the unmatched queue | slice sources left out of the count | **yes** | Mutant "`NOT IN` clause removed" fails `test_build_slices.py:210`. SQLite accepts `NOT IN ()`, which is the unmarked-test case where `ARENA_SLICES` is `()`, and the suite exercises it |
| S2(a): dictionary expansion | dictionary read, 256-char value cap | **yes** | I re-measured the security look's 1 KB-class file (4,000 rows, one 1 MB value; 1,445 B) in a fresh process. Before the fix it peaked at **4,252 MB**. At HEAD it is refused at **72 MB**. Mutant "length check disabled" fails `test_arena_slices.py:171`. Mutant "`read_dictionary` removed" fails 8 tests |
| S2(b): the footer is the writer's word | batch budget of 32 MB; residual "one page" -> #27 | **no** | See BLOCKING-R1 |
| S4: stray newest date | future dates refused | **partly** | Mutant "horizon filter removed" fails `test_arena_slices.py:190`. Malformed strings still pass (MINOR-R1) |

**Red to green.** I replayed `ac7bf89` from a `git archive`. **13 failed, 47 passed** across
`test_arena_slices.py`, `test_build_slices.py`, `test_refresh_boards.py` and `test_survey_floors.py`.
The only new test that stayed green is M2's, which the commit message says it would be: the behaviour
was untested, not wrong.

## Findings

### BLOCKING (must fix before this wave closes)

- **BLOCKING-R1** `src/app/clients/arena_slices.py:48-50`, `:188-194` and `:216-222`;
  `docs/plans/m17-wave-2-plan.md:136-139`. **S2(b) is not fixed, and the residual the wave hands to
  #27 is described as three orders of magnitude smaller than it is.**
  - **The claim.** The docstring (`:190-194`) says "the bound that holds is counted ... What remains
    is one page decoded at the size its own header declares". The plan's risk line repeats it. The
    fix commit's evidence is "its forged-footer file at 370 MB (was 967 MB)".
  - **The evidence was measured on the wrong file.** I rebuilt S2(b)'s file both ways:
    plain-encoded, zstd, 1 MiB values, with the footer's `total_byte_size` forged. I simulated the
    forgery by lifting `MAX_UNCOMPRESSED_BYTES` in the measuring process. A forged footer passes that
    check identically, and the security look showed the forgery is one same-length varint. Peak
    resident size, each file in a fresh process (baseline 64 MB after imports):

    | File | Pre-fix (`78db5e0`) | HEAD | Refused by |
    |---|---|---|---|
    | 300 **identical** 1 MiB values, 15,625 B | 974 MB | **370 MB** | the length cap |
    | 256 **distinct** 1 MiB values, 15,194 B | 841 MB | **905 MB** | the decode budget, after the decode |
    | 1,024 **distinct** 1 MiB values, 58,211 B | not run | **4,111 MB** | the decode budget, after the decode |

    The 370 MB figure is the length cap refusing a dictionary of one value. Give each value a
    distinct 8-byte prefix and the fix bounds nothing: HEAD peaks higher than the code it replaced.
    The peak scales with the rows, about 1 GB per 14 KB of file. The 8 MiB download cap therefore
    still admits the "hundreds of GB" the security look described.
  - **Why the budget cannot bound it.** `decoded += batch.nbytes` (`:219`) runs after pyarrow has
    produced the batch. I measured the first batch alone on the 1,024-row file:

    | Read options | Peak |
    |---|---|
    | `batch_size=2048` | 3,931 MB |
    | `batch_size=32` | 1,164 MB |
    | `batch_size=1`, no dictionary, `buffer_size=65536`, `pre_buffer=False` | 1,069 MB |

    So pyarrow decodes the column chunk ahead of the batch it yields. No batch size or read option
    I tried keeps the decode to one page. The residual is the column chunk's decoded size, bounded
    only by compression ratio x 8 MiB. It is not one page.
  - **Why this blocks.** S2 was BLOCKING because "the footer checks do not bound memory. The code
    comment and the plan's risk section both say they do." The same sentence is now true of the
    decode budget. The owner is being asked to accept a residual (#27) that is misdescribed, and
    an owner cannot accept a risk as described when the description is wrong. The failure is
    unchanged from S2: a small file can exhaust memory on the owner's machine, so the night is lost
    to jetsam or the 30-minute kill (`nightly.py:71`), and the machine that serves thrashes
    meanwhile.
  - **Remedy.** The cheapest honest close needs no new bound:
    1. Rewrite `arena_slices.py:48-50` and `:188-194` and the plan's risk line to say what holds.
       The budget and the length cap bound what is retained and converted to Python. They do not
       bound what pyarrow decodes, and a forged footer with distinct values reaches about 1 GB per
       14 KB of file.
    2. Put these measurements in #27's body.
    3. Have the owner accept that residual through `/log-decision`, which the security look already
       asked for.

    If a real bound is wanted instead: parse in a child process that the refresh kills past an RSS
    ceiling, and turn that into a `SourceError` for the config. macOS does not enforce
    `RLIMIT_AS`. Either way, add a regression test with distinct values. The current
    `test_arena_slices.py:179` patches the budget to 64 bytes and cannot see this.

### MINOR (the author fixes each in this wave or files it as an issue)

- **MINOR-R1** `src/app/clients/arena_slices.py:255-256` and `:272-274`. **S4 is only half fixed. A
  malformed date string that sorts below tomorrow still becomes the config's newest date, and it
  darkens every slice.**
  - **What happens.** `_date` keeps any string's first 10 characters, and the horizon is a
    lexicographic `<=`. S4's remedy was to accept only what `dt.date.fromisoformat` parses.
  - **Measured at HEAD** (`today=2026-09-24`): one stray row in `exclude_ties`, a category no slice
    reads. The other rows are two `multi_turn` rows dated `2026-09-13`.

    | Stray date | `multi_turn` rows served |
    |---|---|
    | `9999-12-31` | 1 (refused, as intended) |
    | `TBD` | 1 (refused) |
    | `2026-09-1~` | **0** |
    | `2026-09-2 ` (trailing space) | **0** |

  - **Impact.** The failure is safe: each slice falls under its floor, carries under D-156, and is
    never served stale. It is still S4's harm, one stray row turning 26 boards dark, through a
    malformed string, which is the likelier upstream accident.
  - **Fix.** One line: keep a date only if `dt.date.fromisoformat(value[:10])` succeeds. Add those
    two strings to `test_arena_slices.py:190`.
  - A valid in-horizon date on an unread category (`2026-09-20`) also moves the newest date. That is
    plan decision 2 ("its config's newest publish date"), which the owner ruled, so it is not part of
    this finding. It is the first review's R1.

- **MINOR-R2** `tests/unit/test_build_slices.py:199-207`. **B2's canary performs the network request
  it guards against at the moment it trips.**
  - **How.** The test calls `build_mod.ARENA_SLICE_CLIENT("text").fetch_bytes()` and expects a
    `SourceError`. When the conftest guard regresses, that is the real `ArenaSliceClient`, and the
    call downloads the live file before the test fails with "DID NOT RAISE". I confirmed this on the
    red replay and on the conftest mutant, and it is how my three outbound requests happened.
    `permission-matrix.md` §3 denies outbound HTTP from a test in every state, including a failing
    one.
  - **Fix.** Assert the identity without calling it, for example
    `assert build_mod.ARENA_SLICE_CLIENT is not ArenaSliceClient`, or patch
    `app.clients.arena_slices.fetch_bounded_bytes` to raise inside the test first.
  - **Related (same fix site).** The guard covers only `build_mod.ARENA_SLICE_CLIENT`, and only for
    marked tests. These paths still reach the real client:
    - `fetch_slices(config, boards)`, which defaults to `ArenaSliceClient` (`arena_slices.py:162`);
    - `survey_boards.measure_slices`, whose default client is `ArenaSliceClient`
      (`survey_boards.py:354`);
    - an unmarked test that passes explicit `slices=` to `build()` without a client.

    None does today (the spy saw 0 connects). Patching `arena_slices.fetch_bounded_bytes`
    suite-wide in the same fixture would close all four paths at once.

### NIT

- **NIT-R1** `pyproject.toml:119-120`. "Its two call sites are in `arena_slices._read_table`" is
  stale. The imports now sit in `_bounded_rows` (`arena_slices.py:196-198`), and there are three of
  them. This is the N1/S5 class again, one file over.
- **NIT-R2** `tests/unit/test_arena_slices.py:150-156`, the `timestamp("s")` case. With the type check
  disabled, this case still fails, but for an incidental reason: the `.dictionary` attribute error,
  or "no readable date", whose message happens to contain the column name. It does not isolate the
  type check the way the date32 and date64 cases do. The date32 case is the one that pins S1, so
  this is cosmetic.
- **NIT-R3** `docs/decisions.md:2998-2999`. D-164's clause 2 was edited in place after the owner
  accepted D-164 ("ruled by the owner 2026-09-24"). The first review asked for a clarification line,
  the way D-159 got one. The commit's reason is fair: the ADR is not on `main` yet, and the edit
  aligns the text with D-132 and the code. The PR body should still tell the owner that the
  accepted wording changed, so the ruling is not on text the owner never saw.

## Hostile inputs re-run at HEAD (security S1 and S2)

Every S1 file from the security look ends as `SourceError` at the type check:
- date32 `2**31-1`;
- date64 `2**62`;
- `timestamp[us]` and `timestamp[ms]` at `2**62`;
- a `rating` typed `timestamp[us]`;
- a `model_name` typed `duration[s]`.

Also refused as `SourceError`: a `decimal128` rating, and a rating stored as `dictionary<string>`.

Read row by row, with none crashing: a `float16` rating, a `uint64` max rating (refused by the band),
a `large_string` name, an all-null name and a null rating.

The owner's copies of the live files (`text` 588,920 B and `vision` 56,113 B, scratchpad copies from
2026-09-24) parse at HEAD with every one of the 35 boards at or above its floor. They decode to
357,839 B against the 32 MB budget, so the new type check and budget do not refuse today's real file.

## Acceptance criteria evidence

The plan names no REQ-IDs. The first review's P1-P4 tables stand: I re-checked their line anchors
after the fix round, and they are unchanged or shifted as listed below. The fix round's new
criteria:

| Criterion | Evidence |
|---|---|
| A column of an unexpected type is refused before conversion | `tests/unit/test_arena_slices.py:150` (6 cases) |
| Any exception inside the read is a `SourceError` | `test_arena_slices.py:159`; `src/app/clients/arena_slices.py:176-182` |
| A hostile file fails its slices, never the build | `tests/unit/test_build_slices.py:175`; `src/app/workflows/build.py:450-457` |
| An over-long value is refused | `test_arena_slices.py:171`; `arena_slices.py:223-228` |
| Decoding past the budget is refused | `test_arena_slices.py:179`; `arena_slices.py:218-222` (see BLOCKING-R1 for what this does not bound) |
| A future date does not move the newest date | `test_arena_slices.py:190`; `arena_slices.py:272-274` (see MINOR-R1) |
| A marked test cannot reach the network | `test_build_slices.py:200`; `tests/conftest.py:57-75` (see MINOR-R2) |
| The reconciled model is in the fingerprint | `tests/unit/test_refresh_boards.py:93-96`; `src/app/workflows/refresh.py:473` |
| The unmatched queue excludes slice rows | `test_build_slices.py:210`; `build.py:329-340` |
| The server never loads pyarrow | `test_arena_slices.py:328` (both parameters pass) |

Shifted first-review anchors: the P1 tests now start at `test_arena_slices.py:59`, `:79`, `:102`,
`:112`, `:204`, `:210`, `:216`, `:229`, `:262`, `:299` and `:311`. The P3 tests are at
`test_refresh_boards.py:68`, `:79`, `:101`, `:114`, `:126`, `:137` and `:147`.

## K.8 contract drift check

`grep -n` of the wave's shared names at HEAD:
```
src/app/workflows/build.py:53:from app.clients.arena_slices import ARENA_SLICES, ArenaSlice, fetch_slices
src/app/workflows/build.py:447:    client_type = ARENA_SLICE_CLIENT if client is None else client
src/app/workflows/build.py:453:            rows, refused = fetch_slices(config, boards, client=client_type)
scripts/survey_boards.py:375:            rows, _ = fetch_slices(config, boards, client=client)
scripts/smoke_deps.py:85:        rows, _ = fetch_slices(config, boards)
tests/integration/test_arena_openrouter_contract.py:59:    rows, refused = fetch_slices(config, boards)
src/app/workflows/sources.py:248:ARENA_SLICE_CLIENT = ArenaSliceClient
```
`parse_arena_slices` gained a keyword-only `today=` with a default, so every caller is unchanged.
`_slice_failed` is gone and nothing refers to it. There are no `/v1`, `ios` or schema changes in the
wave. **Verdict: OK, nothing drifted.**

## Whole-wave pass (04e2630..HEAD, lighter depth)

- I re-read `_ingest_slices` (`build.py:431-477`), `serving_summary`'s board block
  (`refresh.py:463-474`), `_mostly_lost`/`_mostly_new` for boards (`refresh.py:219-225`, `:276-278`),
  `rank.py:62-65` and `sources.py:244-248` against D-164.
- I agree with the first review's plan-compliance and boundary conclusions. Nothing new is out of
  scope, and there are no drive-by edits.
- `# noqa: S608` at `build.py:337` follows the existing precedent at `refresh.py:948`: placeholders
  only, no data interpolated.
- The new mypy override is scoped to `pyarrow` and `pyarrow.*`.

## K.9 candidates spotted outside this wave's scope

- none (the first review's K1 is #26; the security look's S3 is #25)

## Risks queued to next M

- **R-R1** **A benign typed date column now darkens all 35 boards.**
  - **What changed.** The fix refuses a `date32`/`timestamp` date column outright
    (`arena_slices.py:245-251`). That reverses the P1 review's accommodation. The security look's
    remedy had allowed `date32` and `timestamp`.
  - **Why it is only a risk.** The failure is loud and safe: each board carries, then expires after
    30 days.
  - **It is real if** `make smoke-deps` or the live contract test reports
    `column leaderboard_publish_date has type ...`.

## Gates

- `make check-fast` at HEAD `b4e41f2`: **PASS, 6/6 legs** (lint, typecheck, records, test,
  client-decls, swift-test).
  - test: **1285 passed, 17 skipped**, total coverage 91%.
  - `arena_slices.py`: 99% (one partial branch, `286->284`);
  - `build.py`: 94%;
  - `refresh.py`: 96%.
- Whole suite under a socket and DNS spy: **0 outbound**.

## What I did not check

- **The live contract test and `smoke_deps` against the network.** Instead, I parsed the owner's
  scratchpad copies of the live files (2026-09-24) at HEAD.
- **The contents of issues #25, #26 and #27** (no network). BLOCKING-R1 asks that #27's body carry
  the measurements above.
- **Test adequacy beyond the mutants listed.** That is the Tester's seat.
