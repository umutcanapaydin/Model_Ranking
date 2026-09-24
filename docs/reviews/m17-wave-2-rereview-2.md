---
record_type: review
id: m17-wave-2-rereview-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---
# M17-W2 second fix round: independent re-review (commits 4756919..18382b8)

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code. I also wrote neither
fix round and none of the four earlier reviews.
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** this round is `4756919..18382b8`:
- `ed0c840`: the red tests;
- `18382b8`: the fix and D-165.

I also read the whole wave, `04e2630..18382b8`, at a lighter depth.
**Risk tier:** MEDIUM (`docs/plans/m17-wave-2-plan.md:11`)

**What I read.** I read these before the code:
- the plan;
- D-164 and D-165 (the end of `docs/decisions.md`);
- `docs/reviews/m17-wave-2-rereview.md` and `docs/reviews/m17-wave-2-security-rereview.md`;
- `.claude/agents/Code-Reviewer.md`, `.agents/rules/practices.md`, `.agents/rules/review-seats.md`
  and `permission-matrix.md` §11.

`git diff --stat 04e2630..HEAD -- .claude .agents AGENTS.md permission-matrix.md subagent-profiles`
is empty, so the policy I read is the base's. Nothing in the diff addresses a reviewer.

**Families.** The commits carry `GP-Agent: claude-code/local-lane`. This seat is also Claude, and no
second family was available. At MEDIUM tier the cross-model rule is advisory only. My context was
fresh.

**How I worked:**
- **Mutants.** I ran 17 mutants in place through a script in my scratchpad. For each one, the script
  saved the file's bytes, applied the mutant, ran the tests, wrote the bytes back and compared
  SHA-256. All 17 came back byte-identical. I used no `git checkout` or `git restore`.
- **Network.** Every pytest run of mine loaded a plugin that refuses and logs every non-loopback
  connect and every DNS lookup. That includes the full suite twice, every mutant and the red replay.
  The log was never created: **0 outbound attempts**.
- **Red replay.** I replayed `ed0c840` from a `git archive` in my scratchpad.
  - That commit's crash case called `os.abort()`. It never ran, because `_reader_command` does not
    exist at `ed0c840`, so `monkeypatch.setattr` failed before any child started.
  - No new crash report appeared in `~/Library/Logs/DiagnosticReports` (the newest is 16:47, before
    this session).
- **Other sources of evidence.** I measured memory in fresh processes with `ru_maxrss`, which reads
  `RUSAGE_CHILDREN` for the reader. I read the branch's CI logs with `gh run view`, a read of GitHub
  and not a test.
- **No state changes.** I made no commit. My only file in the worktree is this one. A second
  untracked file, `docs/reviews/m17-wave-2-security-rereview-2.md`, appeared during my work. It is
  another seat's, and I did not read it.

## Verdict

**BLOCKING: 3 BLOCKING, 2 MINOR, 3 NIT; 0 K.9; 2 risks.**

On macOS, this round fixes everything it claims to fix, and each fix has a test that fails without
it:
- BLOCKING-R1 and S-R1 are bounded on the owner's machine. The re-review's 1,024-row attack file
  (58 KB) now stops the reader at 537 MB, where it peaked at 4,111 MB before. The parent stays at
  38 MB.
- S-R2, S-R3, S-R4/MINOR-R1, MINOR-R2 and NIT-R2 are fixed.
- NIT-R1 is fixed, but its new sentence is itself inaccurate (NIT-R2-1).

**Why it still blocks.** The branch's own CI is red, for three separate reasons:
1. **BLOCKING-R2-1.** On Linux, `ru_maxrss` carries across `exec`, so the reader measures its
   parent's peak as well as its own. In CI, 27 tests fail with "passed its memory ceiling".
2. **BLOCKING-R2-2.** The new network guard also refuses the live slice contract test, so that test
   can never pass.
3. **BLOCKING-R2-3.** Across the whole wave, CI's skip budget has been exceeded since `78db5e0`.

## Disposition of the re-reviews' findings

| Finding | Claimed | Verified? | Evidence (every mutant was run in place and restored byte-identical) |
|---|---|---|---|
| BLOCKING-R1 / S-R1: no memory bound | the file is parsed in a child under a 512 MiB ceiling (D-165) | **yes on macOS; broken on Linux** (BLOCKING-R2-1) | Three mutants each fail `test_arena_slices.py:238` ("memory" does not match): the `os._exit` disabled (`parquet_reader.py:45`), the watchdog never started (`:128`), and the parent's ceiling branch removed (`arena_slices.py:217`). **Measured:** the 256-row file (15 KB) stops at a child peak of 529 MB, and the 1,024-row file (58 KB) at 537 MB. The parent stays at 38 MB and each read takes 0.1-0.2 s. The owner's copy of the live `text` file reads at a child peak of 63 MB in 0.18 s, with all 26 `text` boards above their floors |
| S-R2: row cap from a forgeable field | rows counted as read | **yes** | Mutant "the count at `parquet_reader.py:99` disabled" fails `test_arena_slices.py:260` |
| S-R3: a non-`SourceError` from the HTTP helper | catch-all in `fetch_bounded_bytes` | **yes** | Mutant "`except Exception` at `protocols.py:89` narrowed" fails `test_arena_slices.py:389` with `IDNAError`. The `except SourceError: raise` at `:84` is behaviour-neutral: without it the error is wrapped again, still as a `SourceError` (the whole unit suite passes) |
| S-R4 / MINOR-R1: a malformed date becomes the newest | keep a date only if `fromisoformat` accepts it | **yes** | Mutant "`_date` returns `value[:10]`" fails `test_arena_slices.py:294`. At `ed0c840`, the `2026-09-1~` and `2026-09-2 ` cases fail. The horizon still holds: its mutant fails `:305` |
| MINOR-R2: the canary downloads when it trips | the guard is on `ArenaSliceClient.fetch_bytes`, and the check is by identity | **yes, but see BLOCKING-R2-2** | Mutant "`conftest.py:74` removed" fails `test_arena_slices.py:398` by name, with no download (the plugin logged nothing). The guard now covers `fetch_slices` and `measure_slices` too |
| NIT-R1: stale pyproject comment | rewritten | **partly** | The new wording is also wrong (NIT-R2-1) |
| NIT-R2: the type test fails for an incidental reason | the match is `column X has type` | **yes** | Mutant "`if not expected:` disabled" fails all 6 cases of `test_arena_slices.py:150` |

**Red to green.** At `ed0c840`, 10 tests fail and 47 pass across `test_arena_slices.py` and
`test_build_slices.py`: the reader's protocol, crash, hang, ceiling, row count, redirect, and two of
the date cases. That matches the commit message.

**The dispositions decided elsewhere, not re-litigated here:**
- S3 is #25, and K1 is #26.
- #27 is bounded by D-165.
- R1, R2 and R-R1 are refused, with their reasons, in the close record.
- NIT-R3 goes in the PR body.

## Findings

### BLOCKING (must fix before this wave closes)

- **BLOCKING-R2-1** `src/app/clients/parquet_reader.py:37-46` and
  `tests/unit/test_arena_slices.py:238-257`. **On Linux the reader measures its parent's peak, not its
  own. CI is red with 27 failures, and the ceiling test proves nothing there.**
  - **The mechanism.** On Linux, `getrusage(RUSAGE_SELF).ru_maxrss` is carried across `execve`.
    The kernel folds the pre-exec memory map's high-water mark into `signal->maxrss`. CPython 3.10+
    spawns with `vfork` on Linux, so that pre-exec map is the parent's own. The reader therefore
    starts with `ru_maxrss` at least equal to its parent's lifetime peak.
  - **macOS behaves differently.** I measured it: a parent holding 816 MB spawns a child that
    reports 14.6 MB. That is why `make check-fast` passes locally.
  - **What CI shows.** Run `36008630772` on `18382b8` gives **27 failed, 1221 passed** on both
    py3.12 and py3.14. Every failure reads "the reader passed its memory ceiling of 536870912 bytes":
    - every test in `test_arena_slices.py` that parses through the reader and comes *after* `:238`,
      from `:274` to `:355`;
    - `test_build_slices.py`, 6 tests;
    - `test_refresh_boards.py`, 6 tests;
    - `test_survey_floors.py`, 1 test.

    Every reader test *before* `:238` passes.
  - **The cause is the ceiling test itself.** CI runs `pytest` in one process (`ci.yml:54`). I
    measured the same single-process run locally: the test process's peak goes from 141 MB to
    **612 MB during `:238`**, because the test builds 96 distinct 1 MiB strings. It is 626-689 MB
    for the files after it. From that point every reader child on Linux starts above 512 MiB.
  - **In a clean run, the test is vacuous on Linux.** The worker is already at 141 MB when `:238`
    starts, above the test's 100 MiB ceiling. So the child exits 3 before it decodes anything, and
    the watchdog mutants would survive there.
  - **Why it blocks.**
    - "Test red" (§11): the wave's PR cannot merge.
    - D-165 names no platform. Its bound means "the parent's peak or the reader's, whichever is
      larger" on every Linux host, and that includes CI's "Build the evidence database through the
      real entry point" step.
  - **Remedy:**
    1. On Linux, read the reader's own memory map instead of `ru_maxrss`: `VmHWM` in
       `/proc/self/status` belongs to the post-exec map. Keep `ru_maxrss` on macOS, where it is
       per-process (measured above).
    2. Make the ceiling test build its file without a 600 MB spike, or build it once on disk. Then
       it cannot poison later tests, and it tests the reader's own growth.
    3. Add a test that a reader spawned from a parent with a high peak still parses a good file. It
       fails on Linux today.

- **BLOCKING-R2-2** `tests/conftest.py:73-74` and
  `tests/integration/test_arena_openrouter_contract.py:53-64`. **The new network guard refuses the
  wave's own live contract test, so V3C-44 for the slice fake can no longer pass.**
  - **What happens.** The guard replaces `ArenaSliceClient.fetch_bytes` in every test not marked
    `slice_download`. `test_every_declared_slice_satisfies_the_parser_contract` calls
    `fetch_slices(config, boards)` against the live file, and it is not marked.
  - **Evidence.**
    - Locally with `RUN_CONTRACT_TESTS=1`, under my socket block, both cases fail at once with
      "tests never reach the network" and attempt no connection.
    - In CI, `contract-tests` run `36008630800` on `18382b8` has **2 failed, 17 passed** with the same
      message. The same job **passed** on `4756919`.
  - **Why it blocks.** It turns a green gate red. It also makes the live check that keeps the
    canonical fake honest unable to pass, which is `practices.md`'s "one canonical mock + a contract
    test" rule and the `writing-a-control` rule that a check must be able to pass.
  - **Remedy.** Choose one of:
    - mark the two contract tests `slice_download` and reword the marker (`conftest.py:44`) to
      "reaches the real download: through respx in unit tests, live in the env-gated contract
      tests";
    - skip the patch for `tests/integration` when `RUN_CONTRACT_TESTS=1`.

    Either way, add a test that fails if a contract test is guarded, for example one asserting the
    marker on the contract module's slice test.

- **BLOCKING-R2-3** `docs/skip-budget.txt:21`, whole wave. **CI's `test` job has been red on this
  branch since `78db5e0`, independently of the two findings above.**
  - **Evidence.**
    - The CI run on `4756919` ends with `coverage_floor FAIL: 66 test(s) skipped of 1302, budget is
      64`. Every CI run from `78db5e0` onward failed (`bc7e43d` and `0b7a535` were cancelled). The
      last green run is `ab98437`.
    - The two new env-gated contract tests (`78db5e0`) are the likely +2. The file's own header
      says to raise the budget "deliberately, in the tree, where a reviewer sees it".
  - **Why it blocks.** The gate is red ("Test red", §11). Neither earlier re-review caught it,
    because both ran only the local gates.
  - **Remedy.** Set the budget to 66, with a line naming the two
    `test_every_declared_slice_satisfies_the_parser_contract` cases, or whatever CI then measures.

### MINOR (the author fixes each in this wave or files it as an issue)

- **MINOR-R2-1** `src/app/clients/parquet_reader.py:130` and `src/app/clients/arena_slices.py:206-226`.
  **The reader's answer has no size bound, so a 14 KB file takes the refresh process to 752 MB.**
  The watchdog also cannot stop the reader while `json.dumps` holds the interpreter lock.
  - **The file.** 30,000 rows whose `model_name` and `category` are the same 256-character astral
    string: one dictionary entry, 14,075 bytes on disk. It passes every first refusal: 256
    characters is at the cap, and the rows, decode budget and ceiling all hold.
  - **Why the answer is large.** `json.dumps` escapes each astral character as 12 ASCII bytes, so
    the answer is 179 MiB.
  - **Measured.** Each run was a fresh process with a parent baseline of 37-38 MB:

    | Rows | File | Reader peak | Refresh process peak | Result |
    |---|---|---|---|---|
    | 10,000 | 9.7 KB | not measured | 275 MB | parsed |
    | 20,000 | 9.7 KB | not measured | 514 MB | parsed |
    | 30,000 | 14 KB | 500 MB | **752 MB** | parsed |
    | 36,000 | 14 KB | **589 MB** | 37 MB | ceiling |
    | 50,000 | 18 KB | **796 MB** | 37 MB | ceiling |

  - **The parent.** It holds the whole of `stdout` (`capture_output=True`) and then the parsed
    strings. Its cost is bounded, because the reader must stay under its ceiling to answer, but the
    bound is about 1.5× the ceiling and sits *in the process D-165 was written to protect*. The fix
    commit's "the parent at most 73 MB" was measured on files whose answers are small.
  - **The reader's overshoot.** It reaches 796 MB against 512 MiB, because the watchdog thread
    cannot run inside `json.dumps` (C code that holds the lock). That contradicts "leaving ... the
    moment it passes the ceiling" (`parquet_reader.py:9`, D-165 clause 1). It is bounded by the row
    and value caps.
  - **Remedy:**
    - `json.dumps(answer, ensure_ascii=False)`, which makes the answer 3× smaller for astral text;
    - a cap on the serialized answer in the reader, turned into an `error`, for example 16 MiB
      (`text` answers about 1 MB today);
    - optionally, a capped read of `stdout` in the parent.

    Add a test with the repeated-astral file.

- **MINOR-R2-2** `src/app/clients/arena_slices.py:214-216`, `:222-224`, `:233-236` and `:243-244`;
  `tests/unit/test_arena_slices.py:209-215` and `:351`. **The parent's protocol checks are partly
  untested, and three message matches cannot tell the failure paths apart.**
  - **Surviving mutants.**
    - "`returncode != 0` branch removed" passes all 3 cases of `:218`. Each case uses
      `match="reader"`, which every message contains: without the branch, the crash and exit-7
      cases fall through to "not its protocol".
    - "row-shape check removed" passes the whole slice suite. An answer such as `{"rows": [1]}`
      would then escape as `AttributeError`, not as a `SourceError`.
  - **A weak match that CI exposed.** `:351` (`match="bytes"`) passed in CI while the reader was
    refusing by *ceiling*. The ceiling message contains "536870912 bytes".
  - **Coverage.** `arena_slices.py` went from 99% (the previous re-review) to 94%, and the new
    `parquet_reader.py` is at 86%. Most of that is code now running in an untraced child and
    exercised there: the footer-bytes mutant fails `:344`. The parent lines listed above are the
    real gap. §11 lists a coverage drop on a touched module as BLOCKING-class. I rate it MINOR
    because the drop is mostly measurement, and I leave the call to the Tester.
  - **Remedy.**
    - Match on `exited -9`, `not its protocol` and `exited 7`.
    - Add `{}` and `{"rows": [1]}` answer cases, plus an `OSError` start case (for example a
      missing executable).
    - Match `:351` on `declares`.

### NIT

- **NIT-R2-1** `pyproject.toml:119-120` and `src/app/clients/arena_slices.py:61-62`. **Stale
  sentences, the N1/S5/NIT-R1 class a third time.**
  - `pyproject.toml` says pyarrow "is imported in one place". The canonical fake imports it too
    (`src/app/clients/fakes.py:52-53`).
  - `arena_slices.py:61-62` says the live file reads "at 44 MB" and that an attack file "was stopped
    at 225 MB". I measure 63 MB, and D-165 says about 60 MB. A stop at 225 MB is not possible under
    a 512 MiB ceiling, so it is left over from an earlier ceiling.
- **NIT-R2-2** `src/app/clients/parquet_reader.py:126-130`. **The reader has no time limit of its
  own.**
  - The refresh stops it after 60 s. The nightly's 30-minute kill, however, is a `proc.kill()` of the
    refresh alone (`src/app/adapter/nightly.py:296-298`), not of its process group. A reader that is
    spinning when that kill lands is orphaned.
  - This is unlikely: the kill must fall inside the reader's 60-second window.
  - Fix: `signal.alarm(...)` at the top of `main()`. SIGALRM's default action ends the process with
    no crash report.
- **NIT-R2-3** `src/app/clients/arena_slices.py:83`. **`python -m` puts the working directory first
  on `sys.path`.** A `json.py` or `resource.py` in the refresh's working directory (the repo root,
  `nightly.py:261`) would shadow the stdlib in the reader. The refresh itself runs with the same
  exposure, so this is not new. `-P` (Python 3.11+) would close it for the reader at no cost.

## The child-process design, the other points I checked

- **Environment.** The reader inherits the refresh's environment plus `src` first on `PYTHONPATH`
  (`arena_slices.py:203-205`). In production that environment is already the nightly's allowlist
  (`nightly.py:87-89`). `app/__init__.py` is empty and `app/clients/__init__.py` holds only a
  docstring, so nothing writes to `stdout` before the answer. `-B` keeps bytecode out of the tree.
- **Protocol.** The limits travel in `argv` and the file on `stdin`. Exit 3 is unique: Python exits
  with 1 or 2 by itself, and a signal gives a negative status. Any `error` string is a
  `SourceError`. A rating of NaN or ±inf is emitted as `NaN`/`Infinity`, read back as such, and
  refused by `score_rows`.
- **Timeout and cleanup.** `subprocess.run` kills and reaps the child on `TimeoutExpired` and on any
  exception. The hang mutant ("timeout removed") fails `:228` after 30 s.
- **Test isolation under xdist.** `test_the_reader_answers_rows_or_an_error_in_process` replaces
  `_watch` before `main()` starts the thread, so no watchdog lives on in a worker. The crash case
  uses SIGKILL. `os.abort()` appears nowhere at HEAD.
- **The network guard.** Apart from BLOCKING-R2-2, it is sound.
  - It sits on the class, per test, through `monkeypatch`.
  - The respx tests run with respx's default `assert_all_mocked`, so an unmocked request raises
    rather than connecting.
  - My full-suite runs made 0 outbound attempts.
- **D-154 still holds.** `arena_slices` imports only `EXIT_OVER_CEILING` from the reader, whose
  top-level imports are stdlib. `test_arena_slices.py:463` passes.

## Acceptance criteria evidence

The plan names no REQ-IDs. The criteria of this round (D-165) are these:

| Criterion | Evidence |
|---|---|
| A file that would exhaust memory is stopped at the ceiling (macOS) | `tests/unit/test_arena_slices.py:238`; `src/app/clients/parquet_reader.py:42-46`, `:128`; `src/app/clients/arena_slices.py:217-220`. Linux: BLOCKING-R2-1 |
| A reader that crashes, answers garbage or exits non-zero is a `SourceError` | `test_arena_slices.py:218` (3 cases); `arena_slices.py:221-236` (see MINOR-R2-2) |
| A reader that hangs is stopped | `test_arena_slices.py:228`; `arena_slices.py:209-213` |
| Every failure inside the reader is an `error` answer | `test_arena_slices.py:159`, `:172`; `parquet_reader.py:116-123` |
| Rows are counted as read | `test_arena_slices.py:260`; `parquet_reader.py:98-101` |
| A malformed redirect is a `SourceError` | `test_arena_slices.py:389`; `src/app/clients/protocols.py:84-94` |
| A non-date never becomes the newest date | `test_arena_slices.py:294` (4 cases); `arena_slices.py:240-248` |
| No test downloads a slice file | `test_arena_slices.py:398`; `tests/conftest.py:61-76` (see BLOCKING-R2-2) |
| The server never loads pyarrow | `test_arena_slices.py:463` |

## K.8 contract drift check

```
src/app/workflows/build.py:53:from app.clients.arena_slices import ARENA_SLICES, ArenaSlice, fetch_slices
src/app/workflows/build.py:453:            rows, refused = fetch_slices(config, boards, client=client_type)
scripts/survey_boards.py:375:            rows, _ = fetch_slices(config, boards, client=client)
scripts/smoke_deps.py:85:        rows, _ = fetch_slices(config, boards)
tests/integration/test_arena_openrouter_contract.py:59:    rows, refused = fetch_slices(config, boards)
src/app/clients/arena_slices.py:37:from app.clients.parquet_reader import EXIT_OVER_CEILING
src/app/clients/arena_slices.py:251:def parse_arena_slices(
```
- The signatures of `fetch_slices` and `parse_arena_slices` are unchanged.
- The new names are `reader_limits`, `MAX_READER_RSS`, `READER_TIMEOUT_S` (in `arena_slices`) and
  `EXIT_OVER_CEILING` (in `parquet_reader`). They are used only inside those two modules and the
  tests.
- `fetch_bounded_bytes` keeps its signature. It now turns every exception into a `SourceError`,
  which changes behaviour for every source. S-R3 asked for exactly that, and the change is in the
  commit message.

**Verdict: OK, nothing drifted.**

## Whole-wave pass (04e2630..HEAD, lighter depth)

- Beyond BLOCKING-R2-3, I agree with the earlier reviews' conclusions on plan compliance and
  boundaries.
- `docs/decisions.md` gains only D-165 in this round, and no earlier ADR changed. D-165 is an
  owner-ruled addition, not a reversal.
- There are no drive-by edits. The helper change in `protocols.py` is S-R3's remedy.
- An observation, not a finding: CI already runs on a `pull_request` event for `wave/m17-w2`, so a
  PR for this wave is open while its reviews are BLOCKING.

## K.9 candidates spotted outside this wave's scope

- none

## Risks queued to next M

- **R2-R1** **On macOS, RSS is not the whole cost.** Memory the compressor holds does not count in
  `ru_maxrss`, so under memory pressure the ceiling measures less than the true footprint. It is
  real if a reader's `phys_footprint` is seen well above its `ru_maxrss` on the owner's machine.
- **R2-R2** **A limit tuned to one machine** (D-165's own cost). The live `text` file reads at 63 MB
  against 512 MiB. It is real when a live read passes about 256 MB, since `make smoke-deps` prints
  the refusal.

## Gates

- `make check-fast` at HEAD `18382b8` (macOS): **PASS, 6/6 legs**. The suite passes; the module
  coverage is in MINOR-R2-2.
- CI on `18382b8`: **red**.
  - `CI`: 27 failed (BLOCKING-R2-1), plus the skip budget (BLOCKING-R2-3).
  - `contract-tests`: 2 failed (BLOCKING-R2-2).
- Whole suite under the socket and DNS block: **0 outbound attempts**.

## What I did not check

- **Linux locally.** No Linux host or container was available. BLOCKING-R2-1 rests on CI's logs and
  on the kernel's documented `getrusage` behaviour, not on a local run.
- **The live download.** I parsed the owner's scratchpad copy of `text`, not the live file.
- **Test adequacy beyond the mutants listed.** That is the Tester's seat.
