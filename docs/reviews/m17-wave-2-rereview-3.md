---
record_type: review
id: m17-wave-2-rereview-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---
# M17-W2 third fix round: independent re-review (commits 7ef0b27..effdb04)

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, none of its three
fix rounds, and none of the six earlier reviews.
**Independent:** yes
**Date:** 2026-09-24
**Commit range:** this round is `7ef0b27..effdb04`:
- `9cf081f`: the red tests;
- `effdb04`: the fix and D-165 clause 4.

I also read the whole wave, `04e2630..effdb04`, at a lighter depth.
**Risk tier:** MEDIUM (`docs/plans/m17-wave-2-plan.md:11`)

**What I read.** Before the code I read:
- the plan;
- D-165 (`docs/decisions.md:3013-3045`) and the last row of `docs/control-events.csv` (the owner's
  waiver of the three-attempts stop for this one round);
- `docs/reviews/m17-wave-2-rereview-2.md` and `docs/reviews/m17-wave-2-security-rereview-2.md`;
- `.claude/agents/Code-Reviewer.md`, `.agents/rules/practices.md`, `.agents/rules/review-seats.md` and
  `permission-matrix.md` §11.

`git diff --stat 04e2630..HEAD -- .claude .agents AGENTS.md permission-matrix.md subagent-profiles` is
empty, so the policy I read is the base's. Nothing in the diff addresses a reviewer.

**Families.** The commits carry `GP-Agent: claude-code/local-lane`. This seat is also Claude, and no
second family was available. At MEDIUM tier the cross-model rule is advisory only. My context was
fresh.

**How I worked:**
- **Mutants.** I ran 18 mutants in place from a script in my scratchpad (`scratchpad/rr3/mutants.py`).
  For each one, the script saved the file's bytes, applied the mutant, ran the tests, wrote the bytes
  back and compared SHA-256. By hand, the same way, I also removed the contract-test marker and
  re-ran the unbounded-read mutant to measure the parent's memory. All 20 runs came back
  byte-identical. I used no `git checkout` or `git restore`, and `git status` is clean apart from this
  file.
- **Another seat's file.** A second untracked file, `docs/reviews/m17-wave-2-security-rereview-3.md`,
  appeared during my work. It belongs to another seat, and I did not read it. That seat may have been
  running tests in this worktree while my mutants were applied. Each mutant was in place for at most
  30 s, in `src/app/clients/arena_slices.py`, `parquet_reader.py` or the contract test. So a red it
  saw around that time should be re-run.
- **Network.** Every pytest run of mine loaded a plugin (`scratchpad/rr3/netblock_rr3.py`) that
  refuses and logs every non-loopback connect and every DNS lookup. That covers the full suite
  (`-n auto`), every mutant and the red replay. The log was never created: **0 outbound attempts**.
- **Crash case.** It uses SIGKILL. `os.abort()` appears nowhere at HEAD, and I raised no crash
  signal.
- **Red replay.** I replayed `9cf081f` from a `git archive` in my scratchpad.
- **Measurements.** I ran the earlier seats' attack files through `parse_arena_slices` in fresh
  processes, reading the parent's peak from `RUSAGE_SELF` and the reader's from `RUSAGE_CHILDREN`.
- **CI.** I read PR #23's checks and logs with `gh`, which reads GitHub and runs no test.

## Verdict

**PASS-WITH-MINORS: 0 BLOCKING, 4 MINOR, 2 NIT; 0 K.9; 0 new risks.**

This round fixes every finding it claims to fix. Each fix has a test that was red at `9cf081f` and
that a mutant turns red again. The branch is green:
- CI at `effdb04`: `test (py3.12)` 1257 passed, 66 skipped; `test (py3.14)` passed; the skip budget
  reports `66 skipped of 1323 (budget 66)`.
- `live-contracts` reports 19 passed, including both
  `test_every_declared_slice_satisfies_the_parser_contract` cases.

**The parent is now bounded.** On every attack file from all three earlier seats, the refresh process
peaks at 38-55 MB. The worst case before this round was 1,246 MB.

**What remains.**
- The mechanism that bounds the parent, the capped read, has no test that fails without it
  (MINOR-R3-1).
- The new JSON-lines protocol splits lines where JSON does not (MINOR-R3-2).
- The new Linux peak reader fails open when `/proc` is unreadable (MINOR-R3-3).
- Three of the earlier remedies were done only in part (MINOR-R3-4).

None of these reopens a bound, and each fix is a line or a short test.

## Disposition of the re-reviews' findings

| Finding | Claimed fix | Verified? | Evidence (every mutant was run in place and restored byte-identical) |
|---|---|---|---|
| BLOCKING-R2-1: Linux `ru_maxrss` includes the parent's peak | `VmHWM` from `/proc/self/status` on Linux; the ceiling test reads a committed 6 KB file | **yes** | Mutant "Linux branch off" (`parquet_reader.py:55`) fails `test_arena_slices.py:208` (`85753856 == 12345*1024`). The ceiling test (`:330`) now reads `tests/fixtures/arena_slices/ceiling.parquet` and builds nothing in the test process. CI on Linux: 1257 passed, 0 "memory ceiling" failures. Remedy 3 (a high-peak parent still parses) was not added (MINOR-R3-3) |
| BLOCKING-R2-2: the network guard refuses the live contract test | `@pytest.mark.slice_download` on it | **yes, in CI only** | `test_arena_openrouter_contract.py:52`. CI `live-contracts` on `effdb04`: both slice cases PASSED. No local test pins the marker (MINOR-R3-4) |
| BLOCKING-R2-3: skip budget | 66, with the two tests named | **yes** | `docs/skip-budget.txt:17-19, 23`. CI: `coverage_floor PASS: 66 skipped of 1323 (budget 66)`. Locally the full suite skips 17, which matches the file's own "17 of these" |
| MINOR-R2-1 / S-R2-1: the parent held the whole answer | JSON lines read against `MAX_ANSWER_BYTES` (16 MiB); stderr to a file with only its tail quoted | **fixed; the bound itself is untested** (MINOR-R3-1) | `arena_slices.py:226-258`. **Measured, parent peak:** `ctl_45000` 8 KB: 54 MB (was 797). `r3_50k`: 54 MB. `longmsg`: 53 MB. `distinct_1024`, `p_1200`, `single_256m`, `par1000f`: 38 MB. Live `text`: 55 MB, 402 `english` rows. Mutant "cap check off" fails `:259`. Mutant "unbounded `read()`" **survives every slice test**, and it takes `ctl_45000` back to a 244 MB parent |
| S-R2-2: a reason copied whole into the record and `/health` | every quoted reason is at most 200 printable characters | **yes** | `parquet_reader.py:146-148`, `arena_slices.py:258, 282`. Mutant "parent error not printable" fails `:269` (`5020 < 400`). The stderr tail's own `printable` is untested (MINOR-R3-1) |
| S-R2-3: the watchdog is starved during one `json.dumps` | one JSON line per row | **yes** | `parquet_reader.py:164-166`. `r3_50k` now peaks at 261 MB in the child (was 706), and the answer cap stops it. Ceiling files stop at 512-522 MiB: 2% over at most |
| S-R2-4 / NIT-R2-3: whole environment; working directory on `sys.path` | allowlist `READER_ENV`; `-P` | **yes** | `arena_slices.py:75, 96, 99-103`. Mutant "env = dict(os.environ)" fails `:280`. Mutant "-P removed" fails `:290` ("planted module imported") |
| NIT-R2-2: the reader has no time limit of its own | `signal.alarm(timeout_s)`, which is 65 s | **yes** | `parquet_reader.py:151-154`. Mutant "alarm removed" fails `:301` after 10 s. SIGALRM's default action ends the process with no crash report |
| MINOR-R2-2: protocol checks untested, weak matches | distinct messages and per-path cases | **mostly** | `:252` now matches `exited -9`, `exited 7`, `not its protocol`, `no end line` and `end line counts 2`. Three mutants fail it: row-shape check off, end-count check off, end-type check off. The `OSError` start case and the `:438` match were not changed (MINOR-R3-4) |
| NIT-R2-1: stale sentences | rewritten | **yes** | `pyproject.toml:119-121`, `arena_slices.py:64-65` ("about 60 MB"; I measured 60 MB on the live `text` file). A new stale sentence came in with BLOCKING-R2-2's fix (NIT-R3-1) |

**Red to green.** At `9cf081f`, 9 tests fail and 58 pass across `test_arena_slices.py` and
`test_build_slices.py`:
- the JSON-lines protocol;
- the Linux peak;
- the two end-line cases;
- the answer bound;
- the short, printable reason;
- the environment;
- the planted module;
- the orphan alarm.

That matches the commit message. The ceiling test passes at `9cf081f`, as it should: its file is
committed and the watchdog already existed.

**All mutants** (19 distinct; every file restored byte-identical):

| Killed (13) | Survived (6) |
|---|---|
| cap check off; parent reason not printable; env not allowlisted; `-P` removed; alarm removed; Linux branch off; end-count check off; end-type check off; row-shape check off; timer not started (30 s); `stopped` not set; watchdog `os._exit` off; parent ceiling branch off | **unbounded `stdout.read()`**; **whole stderr read**; **stderr tail not printable** (MINOR-R3-1); `except OSError` at start narrowed (MINOR-R3-4); `BrokenPipeError` not suppressed, a race-dependent path that my probe below shows handled; the contract-test marker removed (MINOR-R3-4) |

The contract-test marker mutant: removing it leaves
`test_arena_openrouter_contract.py` and `test_arena_slices.py` at 57 passed and 7 skipped
(MINOR-R3-4).

## The new parent read: what I probed

I drove `_read_table` directly, with `_reader_command` replaced by `python -c` programs. The script is
`scratchpad/rr3/probes.py`.

| Reader behaviour | Result | Parent peak | Time |
|---|---|---|---|
| 200 MB to stderr (starting with ESC), exit 1 | `SourceError: the reader exited 1: EEEE…` (200 chars) | 38 → 38 MB | 0.11 s |
| 200 MB to stderr, then a valid answer | 1 row | 38 → 38 MB | 0.09 s |
| 1 MB to stdout **before** reading a 4 MB stdin (a deadlock) | `took more than 3 seconds` | 42 → 43 MB | 3.01 s |
| exits 0 without reading an 8 MB stdin | `no end line` (the EPIPE is suppressed) | 50 → 51 MB | 0.06 s |
| answers, then lingers with stdout open | timeout | flat | 2.01 s |
| 17 MB answer, then sleeps | `answer passed 16777216 bytes` | flat | 0.06 s |
| starts a grandchild that holds stdout for 20 s | timeout, but only after 20 s | flat | 20.08 s |

What this shows:
- **Deadlock.** The parent writes all of stdin before it reads stdout, and the real reader reads all
  of stdin before it writes (`parquet_reader.py:160`), so the two cannot block each other. If a
  future reader wrote first, the Timer covers the write, the read and `wait()`, so the deadlock ends
  as a timeout.
- **Heavy stderr** goes to a disk file, so it can neither fill a pipe nor grow the parent. Only the
  last 200 bytes are read back (`:257`).
- **File descriptors** stayed at 4 across all eight probes, so none leaked (but see NIT-R3-2).
- **A grandchild.** The Timer kills only the reader, so a grandchild holding stdout would extend the
  wait. The reader starts no processes, so this is a property to keep, not a defect.
- **The Timer/kill race.**
  - `timer.cancel()` does not stop a callback that is already running. A reader that finishes at
    exactly `READER_TIMEOUT_S` can therefore be reported as a timeout, which fails closed and is
    harmless.
  - `Popen.send_signal` polls before it kills. A kill after the reader was reaped is a no-op, apart
    from CPython's documented microsecond window when `poll()` and `wait()` run on two threads at
    once.

  Neither is a finding.
- **Linux vs macOS.** `TemporaryFile`, `close_fds`, `-P` (Python 3.11 or later; `requires-python` is
  `>=3.11`) and SIGALRM behave the same on both. The one platform branch is `_peak_rss`
  (MINOR-R3-3).
- **Honest margin.** The live `text` answer is 1,616,244 bytes, 10.4× under the cap. `vision` is
  147,188 bytes, 114× under it.

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **MINOR-R3-1** `src/app/clients/arena_slices.py:246, 257-258`; `tests/unit/test_arena_slices.py:259-266`.
  **The bound that fixes S-R2-1 has no test that fails without it.** The same holds for the two
  stderr bounds.
  - **The answer bound.** `test_an_answer_over_its_bound_is_cut_off` checks the message and nothing
    else. Replacing `reader.stdout.read(MAX_ANSWER_BYTES + 1)` with `reader.stdout.read()` keeps the
    message, because the length check still fires once everything has been read. All 67 slice tests
    pass. On `ctl_45000` the refresh process then peaks at **244 MB**, where the capped read gives
    54 MB. That is the regression S-R2-1 was BLOCKING for, and nothing would catch it.
  - **The stderr tail.** With `stderr.seek(0)` (read all of stderr) or with the tail's `printable`
    removed, the suite still passes. No test has a reader that fails with a large or
    control-character stderr.
  - **Remedy.** Two cheap tests make these discriminating:
    1. A `-c` reader that writes more than a patched `MAX_ANSWER_BYTES`, flushes, and then sleeps
       30 s, with `READER_TIMEOUT_S` at 5. The capped read raises "answer passed" at once. An
       unbounded read waits for EOF and raises the timeout instead.
    2. A `-c` reader that writes `"\x1b[31m\n" + "E" * 100_000` to stderr and exits 1. Assert the
       message is under 400 characters and carries no ESC and no newline.

- **MINOR-R3-2** `src/app/clients/arena_slices.py:277`. **`str.splitlines()` splits on U+0085, U+2028
  and U+2029. `json.dumps(..., ensure_ascii=False)` (`parquet_reader.py:165`) writes those characters
  raw. So one model name that contains one of them, in any category of the file, fails every slice of
  that config.**
  - **Measured** through `parse_arena_slices` on a two-row file:
    - `model x`, `model\x85x` and `model x` each give `SourceError: the reader answered
      something that is not its protocol`;
    - `model\x1cx`, and every character under U+0020, parse, because JSON escapes them.
  - **A regression from this round.** At `18382b8` the answer was one JSON document, and such a row
    reached `score_rows`, which refuses or keeps rows one at a time. Now one upstream row darkens all
    26 `text` boards, including a row in a category the wave does not read. The failure is loud and
    carried (D-156), so no wrong data is served.
  - **Remedy.**
    - Split the bytes on `b"\n"` before decoding: `[json.loads(line) for line in answer.split(b"\n")
      if line]`. JSON never writes a raw `\n` inside a line.
    - Add a test case with `"model x"` that parses.

- **MINOR-R3-3** `src/app/clients/parquet_reader.py:55-59, 62-66`. **The new Linux peak reader fails
  open.**
  - **(a) An unreadable status file.** If `/proc/self/status` cannot be read, `_peak_rss` raises
    inside the watchdog thread. The thread dies (Python prints a traceback to stderr) and the reader
    runs on with no ceiling. I reproduced it: with `sys.platform` set to `linux`, `_PROC_STATUS` set
    to a missing path and a 1-byte ceiling, the watchdog thread was dead after 1 s and the process
    was still running.
  - **(b) A status file without `VmHWM`.** Line 59 returns `ru_maxrss`, which Linux reports in KiB,
    and the code compares it with bytes. The ceiling becomes 1,024 times larger. CI's coverage
    report shows line 59 was never run on Linux.
  - **(c) No positive control.** Remedy 3 of BLOCKING-R2-1 (a reader started by a high-peak parent
    still parses a good file) was not added. So on Linux nothing shows that the ceiling test at
    `test_arena_slices.py:330` does not pass vacuously, which it would if the reader's own baseline
    after imports were above that test's 100 MiB.
  - **Why MINOR, not BLOCKING.** §11 lists a safety control that fails open as BLOCKING-class.
    Neither trigger happens on this project's two hosts: production runs on macOS, which never takes
    this branch, and CI runs on Ubuntu, which mounts `/proc` with `VmHWM`. The parent is now bounded
    on its own by the answer cap (MINOR-R3-1 aside), so a reader with no ceiling endangers only
    itself.
  - **Remedy.**
    - In `_watch`, treat any exception from `_peak_rss` as over the ceiling
      (`os._exit(EXIT_OVER_CEILING)`), so it fails closed.
    - Scale the Linux fallback by 1024.
    - Add a positive control: `ceiling.parquet`'s honest sibling (a small file) parses under the
      same 100 MiB ceiling.

- **MINOR-R3-4** `tests/integration/test_arena_openrouter_contract.py:52`,
  `src/app/clients/arena_slices.py:231-233` and `tests/unit/test_arena_slices.py:438`. **Three parts
  of the earlier remedies were not done.**
  - **The contract-test marker is pinned only by CI's live job.** BLOCKING-R2-2's remedy asked for "a
    test that fails if a contract test is guarded". I removed the marker in place: the local suite
    gives 57 passed and 7 skipped, and it stays green. A one-line unit test asserting
    `get_closest_marker("slice_download")` on that test (or a grep of the module) would pin it.
  - **The reader-could-not-start path is untested.** MINOR-R2-2 asked for an `OSError` start case.
    Narrowing `except OSError` to another class leaves 67 of 67 slice tests passing, and CI's
    coverage report lists `arena_slices.py 231-233` as missed. Fix: patch `_reader_command` to a
    missing executable and match "could not be started".
  - **`:438` still matches `"bytes"`.** MINOR-R2-2 asked for `declares`. Today the ceiling message
    ("536870912 bytes") and the answer-bound message ("16777216 bytes") both contain "bytes". The
    footer check is still covered, because disabling it makes the test fail by not raising. So only
    the diagnosis is weak.

### NIT

- **NIT-R3-1** `tests/conftest.py:44` and `:59-60`. **Stale sentences, the N1/S5/NIT-R1/NIT-R2-1 class
  a fourth time.**
  - The `slice_download` marker is described as "with respx mocking httpx".
  - The comment says "Only a test marked `slice_download`, which mocks the transport with respx,
    reaches the real method".

  Since `effdb04`, the live contract test carries the marker and mocks nothing. The rewording that
  re-review 2 proposed (live in the env-gated contract tests, through respx in unit tests) was not
  applied.
- **NIT-R3-2** `src/app/clients/arena_slices.py:228-256` and `tests/unit/test_arena_slices.py:310`.
  **`_read_table` never closes `reader.stdout`.** Under `-W default::ResourceWarning`,
  `test_arena_slices.py` gives 11 of
  `ResourceWarning: unclosed file <_io.BufferedReader name=14>`.
  - On the `BrokenPipeError` path, `reader.stdin.close()` is skipped as well.
  - CPython frees both at refcount zero, so my probes saw no fd growth, and the leak is new this round
    only because `subprocess.run` used to close them.
  - Fix: `with subprocess.Popen(...) as reader:`. The orphan test (`:310`) also leaves its stdin
    open.

## Acceptance criteria evidence

The plan names no REQ-IDs. This round's criteria are D-165 clause 4 and the two re-reviews' findings:

| Criterion | Evidence |
|---|---|
| The parent never holds the reader's answer whole (S-R2-1) | `arena_slices.py:246-250`; `test_arena_slices.py:259`. Measured parent 38-55 MB on every attack file. The bound itself is untested (MINOR-R3-1) |
| Every quoted reason is at most 200 printable characters (S-R2-2) | `parquet_reader.py:146-148`; `arena_slices.py:258, 282`; `test_arena_slices.py:269` |
| No single dump starves the watchdog (S-R2-3) | `parquet_reader.py:164-166`; `test_arena_slices.py:176` (`test_the_reader_answers_rows_or_an_error_in_process`, which checks one line per row and the end line) |
| The reader sees an allowlisted environment and starts with `-P` (S-R2-4, NIT-R2-3) | `arena_slices.py:75, 96, 99-103`; `test_arena_slices.py:280`, `:290` |
| The reader stops at its own time limit (NIT-R2-2) | `parquet_reader.py:151-154`; `test_arena_slices.py:301` |
| The peak is the reader's own on Linux (BLOCKING-R2-1) | `parquet_reader.py:48-59`; `test_arena_slices.py:208`; CI py3.12/py3.14 green on `effdb04`. Fail-open edges in MINOR-R3-3 |
| The ceiling test does not poison later tests | `test_arena_slices.py:330` reads `tests/fixtures/arena_slices/ceiling.parquet` (6,197 bytes); the generator is `make_ceiling.py` |
| The live contract test can pass (BLOCKING-R2-2) | `test_arena_openrouter_contract.py:52`; CI `live-contracts` 19 passed on `effdb04` |
| CI's skip budget holds (BLOCKING-R2-3) | `docs/skip-budget.txt:23` (`66`); CI `66 skipped of 1323 (budget 66)` |
| Every reader failure path has its own message (MINOR-R2-2) | `test_arena_slices.py:252` (6 cases). The start `OSError` path is untested (MINOR-R3-4) |

## K.8 contract drift check

```
$ grep -rn "fetch_slices(\|import.*fetch_slices\|from app.clients.parquet_reader import" src scripts tests/integration
src/app/clients/arena_slices.py:40:from app.clients.parquet_reader import EXIT_OVER_CEILING, printable
src/app/clients/arena_slices.py:205:def fetch_slices(
src/app/workflows/build.py:53:from app.clients.arena_slices import ARENA_SLICES, ArenaSlice, fetch_slices
src/app/workflows/build.py:453:            rows, refused = fetch_slices(config, boards, client=client_type)
scripts/survey_boards.py:375:            rows, _ = fetch_slices(config, boards, client=client)
scripts/smoke_deps.py:82:        from app.clients.arena_slices import ARENA_SLICES, fetch_slices
scripts/smoke_deps.py:85:        rows, _ = fetch_slices(config, boards)
tests/integration/test_arena_openrouter_contract.py:57:    from app.clients.arena_slices import ARENA_SLICES, fetch_slices
tests/integration/test_arena_openrouter_contract.py:60:    rows, refused = fetch_slices(config, boards)
```

- The signatures of `fetch_slices` and `parse_arena_slices` are unchanged.
- The new names are `MAX_ANSWER_BYTES`, `READER_ENV`, `_reader_env`, `_answered_rows` (in
  `arena_slices`), and `REASON_CHARS`, `printable`, `_peak_rss`, `_guard` (in `parquet_reader`). They
  are used only inside those two modules and their tests.
- D-154 still holds: `arena_slices` imports two names from the reader, whose top-level imports are
  stdlib only, and the server-never-loads-pyarrow test passes.

**Verdict: OK, nothing drifted.**

## Whole-wave pass (04e2630..effdb04, lighter depth)

- I agree with the earlier reviews on plan compliance (`docs/plans/m17-wave-2-plan.md` §Scope and
  §Phases) and on the `clients/` / `workflows/` boundary.
- The round's only non-code edits are these:
  - `docs/skip-budget.txt`;
  - `pyproject.toml`'s mypy comment;
  - the `ceiling.parquet` fixture and its generator;
  - D-165 clause 4.

  None of them is a drive-by.
- **An observation, not a finding.** D-165 clause 4 was added in place to an ADR the owner ruled.
  The commit explains why ("not yet on main"), `make check-records` passes, and the clause cites
  S-R2-1 as its source. Its last sentence ("stops itself at its own time limit if its parent is
  gone") is slightly broader than the code: the alarm fires whether or not the parent is alive,
  which is harmless.
- `note.txt` and `docs/prd.md` changed in earlier commits of the wave, as ordinary resume-state and
  PRD upkeep.
- **Coverage.** CI shows `arena_slices.py` at 97% (up from 94% in re-review 2) and
  `parquet_reader.py` at 84%. The reader's missed lines are code that runs only in the untraced
  child (`_watch`, `_guard`, `main`'s error branch) plus the Linux fallback of MINOR-R3-3. The
  per-module floor passes. The Tester seat can judge whether it wants the child's lines traced.
- **Dispositions decided elsewhere, not re-litigated:** S3 → #25; K1 → #26; #27 bounded by D-165;
  R1, R2, R-R1, R2-R1, R2-R2 refused with reasons in the close record; NIT-R3 into the PR body.

## K.9 candidates spotted outside this wave's scope

- none

## Risks queued to next M

- none. R2-R1 and R2-R2 are disposed of elsewhere, and this round adds no new risk.

## Gates

- `make check-fast` at `effdb04` (macOS): **PASS, 6/6 legs** (54 s).
- The full suite, `-n auto`, under the socket and DNS block: **1306 passed, 17 skipped, 0 outbound
  attempts**.
- CI on `effdb04` (`gh pr checks 23`): every check passes, including `test (py3.12)`,
  `test (py3.14)` and `live-contracts`.

## What I did not check

- **Linux locally.** No Linux host was available, because the Docker daemon is not running. The Linux
  claims rest on CI's green run on `effdb04` and on reading the code.
- **The live download.** I parsed the scratchpad copies of `text` and `vision`, not the live files.
- **Test adequacy beyond the mutants listed.** That is the Tester's seat.
