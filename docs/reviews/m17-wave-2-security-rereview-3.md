---
record_type: review
id: m17-wave-2-security-rereview-3
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---

# M17-W2 third security re-review: the reader's answer, bounded (D-165 clause 4, #22)

**Independent:** yes. I wrote none of the code under review and none of the earlier reviews
(`m17-wave-2-security.md`, `-security-rereview.md`, `-security-rereview-2.md`). This file is the only
repository file I changed. I made no commit and changed no git state. Every probe and hostile file I
made is in `scratchpad/sec-rr3/`, outside the worktree. I reused the earlier seats' files in
`scratchpad/sec-m17w2/`, `sec-rr/`, `sec-rr2/` and `scratchpad/distinct_*.parquet`. I used no network
and did not call `os.abort()`. Stub readers that had to die were ended with SIGKILL.

## Scope

- The fix `effdb04` (red tests `9cf081f`), read against D-165 clauses 1-4 (`docs/decisions.md`).
- `src/app/clients/arena_slices.py`: `_reader_command` (`:93-96`), `_reader_env` (`:99-103`),
  `_read_table` (`:215-270`), `_answered_rows` (`:273-295`) and `parse_arena_slices` (`:309-354`).
- `src/app/clients/parquet_reader.py`: `_peak_rss` (`:48-59`), `_watch` (`:62-66`), `_guard`
  (`:151-154`) and `main` (`:157-166`).
- Downstream of the read: `build.py::_ingest_slices` (`:430-477`), `ingest.py::_store_scores`
  (`:104-`) and the whole `build()` (`:590-`).

Environment: Python 3.14.0, pyarrow 25.0.1, macOS on a 16 GiB machine. The parent's peak is
`ru_maxrss` of `RUSAGE_SELF` and the reader's is `ru_maxrss` of `RUSAGE_CHILDREN`, measured in a
fresh process per file. All figures are MiB.

## Verdict

**MINOR.** S-R2-1, the BLOCKING finding of the last round, is closed. The parent now reads the
reader's answer against a control (`:246-250`), stderr goes to a file (`:226, :257-258`), and every
quoted reason is 200 printable characters or fewer. I could not push the refresh process past
**245 MiB** with any file every check accepts. The last round measured 1,246 MiB, and that growth
had no control. No hostile file made anything but a `SourceError` leave `_read_table`,
`fetch_slices` or `_ingest_slices`.

The author's figure, "parent peak ≤77 MB", is true of the earlier files only. The largest answer
the 16 MiB cap lets through costs the parent 190 MiB for one config, and 245 MiB across a whole
build (S-R3-1). That cost is bounded by a control, so it is MINOR, not BLOCKING. It is a residual
the owner should know by its number (see "Residual for the owner").

Four more MINOR findings (S-R3-2 to S-R3-5) and two NITs. None is reachable by a hostile file as a
way past the bound. Each is a regression in robustness or a control that fails open, and each has
a small fix.

## Measurements: every earlier seat's file, through `parse_arena_slices` (the real path)

| Files | Parent peak | Reader peak | Outcome |
|---|---|---|---|
| amp_*, forged, p_1, same_600 | 38 | 55-355 | `SourceError`: value too long |
| p_100 | 38 | 334 | `SourceError`: decode budget |
| p_300, p_600, p_1200, single_256m, distinct_256, distinct_1024 | 38 | 515-523 | `SourceError`: ceiling |
| par300f, par1000f (parallel decode, forged footer; 4 runs each) | 38 | **519-596** | `SourceError`: ceiling |
| r_1m, r_2400k, r_2700k, r3_600k, r3_1200k | 38 | 70-257 | `SourceError`: more than 50,000 rows |
| r3_50k (S-R2-3's 706 MiB file) | 54 | 261 | `SourceError`: answer past 16 MiB |
| ctl_10000 … ctl_50000 (S-R2-1 channel a) | 54 | 65-109 | `SourceError`: answer past 16 MiB |
| lm1k, lm39 (S-R2-1 channel b, 3.9 MB reason) | 38-45 | 50-111 | `SourceError`, reason 214 chars, ESC shown as `?` |
| fg_cols, fg_rg, rg1 (honest shapes, forged footer) | 45-74 | 170-206 | rows returned |
| live `text` / `vision` | 55 / 39 | 60 / 54 | rows returned |

The parent never passed 74 MiB on these files, so the author's measurement holds for them. The
reader overshoots its 512 MiB ceiling by up to 16% (596 MiB) on the parallel-decode files. That is
S-R2-3's known, bounded residual. The commit's "reader ≤558 MB" is a little low: I measured 519 to
596 across four runs.

## Findings

### S-R3-1 MINOR: the largest answer the cap allows costs the refresh process 190 MiB per config and 245 MiB per build. The claim "≤77 MB" does not cover it.

**Where.** `arena_slices.py:246` reads up to `MAX_ANSWER_BYTES` (16 MiB, `:72`), then `:277` does:

- `answer.decode("utf-8")`, which builds ONE str of the whole answer;
- `.splitlines()`, which builds a second copy as 50,001 lines;
- `json.loads` of each line, which gives two dicts, five key strings and four values per row.

**The attack.** The file is legal in every respect. It has 50,000 distinct model names of 224 ASCII
characters, all rated inside the Elo band, all in category `english`, all on the newest date. It is
written in row groups of 2,048 so that each batch's dictionary stays under the decode budget. One
name starts with an astral character (U+1F600). That single character makes CPython store the whole
decoded answer at 4 bytes per character: a 16 MiB answer becomes a 64 MiB str. The file is 230 KB,
and the reader's answer is 16,750,018 bytes, 27 KB under the cap. Build it with
`sec-rr3/build.py 50000 224 0 1`.

| Measured (`sec-rr3/`) | Parent peak | Reader peak |
|---|---|---|
| `run.py` through `parse_arena_slices`, text slices, ASCII only | 142 | 95 |
| the same file with one astral character | **190** | 96 |
| its phases (`phases.py`): answer read / whole-answer str / splitlines / parsed | 54 / 118 / 137 / 190 | |
| `ingest.py` through `_ingest_slices`, both configs, file DB | **240** | 95 |
| `ingest.py`, `:memory:` DB | 330 | 97 |
| `fullbuild.py`: the whole `build()`, file DB, fixtures for the other sources | **245** (21 s; the live `text` file: 73, 1.4 s) | |
| other shapes: 27,369 rows of padded dates; 45,714 rows of 256 characters | 175 / 187 | 89 / 94 |

`_ingest_slices` peaks above a single parse because `text`'s 50,000 `ScoreRow`s are still bound
to `rows` (`build.py:453`) while `vision` is read.

**Why MINOR, not BLOCKING.** The growth is now capped by a control that fires (`:247-250`), not by
accident. The worst case is 0.25 GiB, a fifth of what made S-R2-1 BLOCKING, and it is a short spike
during one refresh. What is wrong is the claim: the commit and D-165 clause 4 say nothing the
reader says is held whole, but the answer, up to 16 MiB, is held whole and then roughly 9.5 times
over. A 16 MiB cap is ten times the honest 1.6 MB answer, and the memory scales the same way.

**Fix (cheap, either or both).**

1. Split the bytes, not a decoded str: `[json.loads(line) for line in answer.split(b"\n") if line]`.
   `json.loads` takes bytes. This drops the 64 MiB str and the splitlines copy: measured 190 → 125
   MiB (`alt.py`). It also closes S-R3-2.
2. Lower `MAX_ANSWER_BYTES` to 4 MiB, which is 2.5 times the honest answer. Measured with the
   largest answer that cap allows (12,500 rows): 76 MiB (`cap4.py`).

### S-R3-2 MINOR: one model name with U+2028, U+2029 or U+0085 fails every slice of its config. The new line protocol introduced this regression.

**Where.** The reader writes rows with `json.dumps(..., ensure_ascii=False)`
(`parquet_reader.py:165`). That call escapes characters below U+0020 but writes U+0085, U+2028 and
U+2029 raw. The parent splits with `str.splitlines()` (`arena_slices.py:277`), which breaks a line
on each of those three. So a row's JSON is cut in the middle of a string, and `json.loads` fails.

**Measured** (`sec-rr3/seps.py`). I took the live `text` file and changed one row's `model_name` to
`gpt<char>x`:

- With U+2028, U+2029 or U+0085, the result is `SourceError: the reader answered something that is
  not its protocol`, and all 26 `text` slices fail.
- With U+001C or U+00E9, the file parses (9,402 rows).

The previous protocol, one JSON document, parsed all five.

**Why MINOR.** An attacker gains nothing new: a hostile file can already fail its config many ways.
But an honest upstream name with one of these characters would black out the whole config, loudly
and carried (D-156), with a reason that points at the reader rather than at the data. It cannot
forge a row either: the first fragment is always an unterminated string (`{"row": {"model_name":
"…`), so the parse fails closed. **Fix:** S-R3-1 fix 1 (split on `b"\n"`). Add a test with a name
containing U+2028.

### S-R3-3 MINOR: the watchdog fails open. One exception in the peak read ends the ceiling, and the reader then runs unbounded.

**Where.** `parquet_reader.py:62-66`. `_watch` has no `try`. On Linux, `_peak_rss` reads
`/proc/self/status` (`:55-58`). If that read raises once, the daemon thread dies, and `main` goes
on with no ceiling. The cause could be `/proc` not mounted in a minimal container or chroot, or an
unexpected format. Nothing reports it, because stderr is only quoted on a non-zero exit.

**Measured** (`sec-rr3/failopen.py`). I ran the real `main()` in-process with the platform read as
`linux` and `_PROC_STATUS` pointing at a missing path, with the default limits. The watchdog died
with `FileNotFoundError`, and each file then ran to its later refusal with no ceiling:

| File | Reader peak |
|---|---|
| p_300 | 983 MiB |
| single_256m | 836 MiB |
| par300f | 2,768 MiB |
| p_1200 (389 KB) | **2,838 MiB** |

With the watchdog alive, each of these files stops at 515-596 MiB.

**Why MINOR.** The refresh process is unaffected, because the ceiling protects the machine, not the
parent. The owner's nightly runs on macOS, where `_peak_rss` does not touch `/proc`. CI's Linux has
`/proc`. Still, this is the control D-165 calls "the bound", and it fails in the open direction.
**Fix:** wrap the body of `_watch` so that any exception ends the process, for example with
`os._exit(EXIT_OVER_CEILING)` or a distinct code the parent maps to a `SourceError`. Add a test
that makes `_peak_rss` raise.

### S-R3-4 MINOR: the parent's own tempfile is made outside the `try`. A missing temp directory escapes as `FileNotFoundError` and ends the cycle.

**Where.** `arena_slices.py:226`. `tempfile.TemporaryFile()` runs before the `try` at `:227`, so
its `OSError` is not turned into a `SourceError`. `_ingest_slices` catches only `SourceError`
(`build.py:454`). The build re-raises anything else on purpose, and that ends the cycle, which is
the exact outcome D-165 clause 2 exists to prevent.

**Measured** (`sec-rr3/tmpfail.py`). I set `tempfile.tempdir` to a missing directory and ran
`_ingest_slices` with the live `vision` file. The result: `ESCAPES builtins.FileNotFoundError: [Errno
2] No such file or directory: '/nonexistent-tmp/tmp…'`. `tempfile` caches its choice of directory,
so a temp directory removed after the first use in a long-lived process reproduces this without any
setting.

**Why MINOR.** The trigger is the environment, not the file. A hostile upstream cannot cause it, and
a broken temp directory may break other stages too. **Fix:** move the `TemporaryFile` into the same
`try` as `Popen` (`except OSError` → `SourceError`), or wrap the whole `_read_table` body the way
`fetch_bounded_bytes` does (`protocols.py:84-94`).

### S-R3-5 MINOR: a legal file puts 50,000 rows in one slice. Nothing bounds a slice's rows from above.

**Where.** `build.py:461` checks a floor (`minimum_rows`, half the measured count) but no ceiling.
The reader allows 50,000 rows per file (`MAX_PARQUET_ROWS`).

**Measured** (`sec-rr3/fullbuild.py`). The 230 KB file from S-R3-1, served for both configs,
compared with the live `text` file:

| | Hostile file | Live `text` file |
|---|---|---|
| Rows stored in `arena_text_english` and `arena_vision_english` | 100,000 (declared: 402 and 152) | |
| Build time | 21-25 s | 1.4 s |
| Artifact size (baseline without slices: 86 KB) | **76 MB** | |
| Parent peak | 245 MiB | 73 MiB |

The rows are not served, because no name matches a model. `_most_unmatched` leaves slice sources
out (`build.py:335-339`), so they do not flood the report either.

**Why MINOR.** Everything is bounded (50,000 rows × 256 characters), nothing crashes, and no row
reaches a surface unless its name matches a real model. Even then, duplicates collapse to one row
per name (`score_rows`). But a slice declared at 402 rows that suddenly holds 50,000 is a changed
file, the same as a slice below its floor. **Fix:** refuse a slice above a multiple of its declared
count, for example 4 × `measured_rows`, with the same `SourceError` the floor uses.

### S-R3-N1 NIT: the reader's own alarm is void if the parent ignores or blocks SIGALRM.

`parquet_reader.py:154` relies on SIGALRM's default action. A signal ignored in the parent stays
ignored across `exec`, and a blocked mask is inherited. `restore_signals` resets only SIGPIPE and
SIGXFSZ.

**Measured** (`sec-rr3/alarm.py`, the real reader, `timeout_s: 2`, stdin left open):

| Parent's SIGALRM | Result |
|---|---|
| Default | Reader ended at 2.07 s by SIGALRM |
| `SIG_IGN` | Reader still running at 6 s; the probe SIGKILLed it |
| Blocked with `pthread_sigmask` | Reader still running at 6 s; the probe SIGKILLed it |

Nothing in `src/` touches SIGALRM today, and the parent's own 60 s timer is the primary control, so
this is hardening for the orphan case only. **Fix:** in `_guard`, call
`signal.signal(SIGALRM, SIG_DFL)` and `signal.pthread_sigmask(SIG_UNBLOCK, {SIGALRM})` before
`alarm`.

### S-R3-N2 NIT: stderr to a file bounds memory, not disk. A process holding the reader's stdout outlives the timer.

These were measured with stub readers (`sec-rr3/stubs.py`, `READER_TIMEOUT_S` = 3 s, an 8 MiB
stdin). The parent's peak was 46-62 MiB in every case.

- **Stderr volume.** A reader that writes stderr as fast as it can wrote **4.5 GB** to the parent's
  tempfile in 3 s before the timer killed it. At the real 60 s that could be about 90 GB of temp
  disk. The tempfile is unlinked, so the space comes back when the file closes. I found no way for a
  parquet file to make the real reader write stderr in a loop: pyarrow does not log per page, and
  Python prints each warning once. A reader that writes 2 GB of stderr and then answers is parsed
  normally.
- **A process holding the reader's stdout.** A stub that starts a grandchild process holding its
  stdout kept the parent in `stdout.read` until that process exited: 12 s against a 3 s timer. Of
  15 runs, 14 then raised the timeout `SourceError`. The very first run returned an empty answer
  instead, and I could not reproduce that. The real reader starts no processes, so this cannot be
  reached from a file.
- **Everything else held.** A reader that never reads stdin was stopped at 3.02 s, and the 8 MiB
  write ended quietly with `EPIPE`. A reader that writes a byte every 50 ms, or closes stdout and
  hangs, was stopped at 3.03 s with a `SourceError`. A stdout flood was cut at 16 MiB in 0.03 s. A
  SIGKILLed reader that had written ESC, OSC, CR/LF, U+2028 and NEL gave a reason of 200 printable
  characters, with each control character shown as `?`.

**Hardening, if wanted:**

- In the reader, set `resource.setrlimit(RLIMIT_FSIZE, …)` to a few MiB. That bounds stderr on
  disk.
- In the parent, use `start_new_session=True` plus `os.killpg` in `stop()`. That reaches any
  descendant.

## What holds

- **The environment and the import path** (`sec-rr3/envprobe.py`). The reader sees only `LANG`,
  `LC_CTYPE`, `PATH`, `PYTHONIOENCODING`, `PYTHONPATH` and `TMPDIR`, plus the variable macOS injects,
  `__CF_USER_TEXT_ENCODING`. An `HF_TOKEN` set in the parent does not reach it. `sys.flags.safe_path`
  is on, the working directory is not on `sys.path`, and `site.ENABLE_USER_SITE` is off (venv).
  S-R2-4 is closed.
- **Reasons are short and printable.** Every reason I produced was at most 214 characters in total,
  including the `arena slices:` prefix, and carried no control characters. S-R2-2 is closed at its
  source.
- **Only `SourceError` leaves the read, for anything a file can cause.** That covers every file
  above and every stub (crash, timeout, flood, garbage, a truncated end line). The one exception is
  S-R3-4, which the environment causes, not a file. The child's rows are flat, so `json.loads` cannot
  recurse. With the parent capped at 0.25 GiB, `MemoryError` is not a realistic path.
- **Timeout and kill.** The timer's `SourceError` fires in every stalled-reader case, and the reader
  is reaped. The real reader's own alarm ends an orphan at its limit (65 s in production).
- **Hygiene.**
  - `gitleaks detect` over the tree finds no leaks.
  - `ruff --select S` on the two modules reports only S101 (`arena_slices.py:242`, an `assert` that
    documents a type). The project config ignores S101, and the asserted condition always holds with
    `PIPE`.
  - No new dependency in `effdb04`: `pyproject.toml` changed only a mypy comment.

## Residual for the owner

The owner does not need to rule on a blocker. One number should be known, though. **With the
shipped 16 MiB answer cap, a 230 KB hostile file that passes every check takes the refresh process
to 245 MiB and a 21 s build, and adds a 76 MB artifact** (S-R3-1, S-R3-5). The honest file costs
73 MiB. Two small changes bring the parent to about 76 MiB, the level the author claimed:

- split the answer as bytes;
- lower the cap to 4 MiB.

A slice ceiling would bound the artifact. If the owner accepts roughly 0.25 GiB and a 76 MB artifact
as the worst case, all five findings can be filed and worked after the wave. None of them blocks it.

## Reproduction

Every script is in `scratchpad/sec-rr3/`. Run each one with `PYTHONPATH=<worktree>/src` and the
worktree's `.venv/bin/python`. `fullbuild.py` also needs `W=<worktree>` and must run from the
worktree.

| Script | What it does |
|---|---|
| `run.py <file>` | Parent and reader peaks through `parse_arena_slices` |
| `build.py n len pad astral out` | Legal files that fill the answer cap (`b50k_224u.parquet` is the worst) |
| `answer_size.py <file>` | The reader's answer size, uncapped |
| `phases.py`, `alt.py`, `cap4.py` | The parent's memory by phase; as shipped vs. a bytes split vs. a 4 MiB cap |
| `ingest.py`, `fullbuild.py` | Through `_ingest_slices` and through the whole `build()` |
| `seps.py` | S-R3-2 |
| `failopen.py` | S-R3-3 |
| `tmpfail.py` | S-R3-4 |
| `alarm.py` | S-R3-N1 |
| `stubs.py <case>`, `gc.py` | S-R3-N2 and the timer paths |
| `envprobe.py` | The reader's environment and `sys.path` |
