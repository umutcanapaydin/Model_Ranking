---
record_type: review
id: m17-wave-2-security-rereview-2
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---

# M17-W2 second security re-review: the slice file read in a child process (D-165, #22)

**Independent:** yes. I wrote none of the code under review. I did not write the first security look
(`m17-wave-2-security.md`) or the first re-review (`m17-wave-2-security-rereview.md`). This file is
the only repository file I changed. I made no commit and no git state change. Every probe and hostile
file I made is in `scratchpad/sec-rr2/`, outside the worktree. I reused the earlier seats' files in
`scratchpad/sec-m17w2/`, `scratchpad/sec-rr/` and `scratchpad/distinct_*.parquet`. I used no network.
For the crash case I relied on the existing SIGKILL test. I did not call `os.abort()`.

## Scope

The fix under review is `18382b8`. I re-checked these parts:

- `src/app/clients/parquet_reader.py`: the child process, including its watchdog (`:37-46`), its
  checks (`:49-113`) and `main` (`:126-130`).
- `src/app/clients/arena_slices.py`: `_read_table`, the parent side (`:195-237`), and
  `parse_arena_slices` (`:251-296`).
- `src/app/clients/protocols.py`: the `fetch_bounded_bytes` catch-all for S-R3 (`:84-94`).
- `src/app/workflows/build.py`: `_ingest_slices` (`:430-477`) and `_board_failed` (`:369-380`).
- Where a refusal reason goes after the build: `src/app/workflows/refresh.py:717` and
  `src/app/adapter/nightly.py:128-135, 356-377`.

Environment: Python 3.14.0, pyarrow 25.0.1, and a 16 GiB, 8-core macOS machine. Every file went
through `parse_arena_slices`, the real path that starts the reader, in a fresh process. The parent's
peak is `ru_maxrss` of `RUSAGE_SELF`, and the child's peak is `ru_maxrss` of `RUSAGE_CHILDREN`. All
figures are in MiB. The ceiling is `MAX_READER_RSS` = 512 MiB.

## Verdict

**BLOCKING, on one finding: S-R2-1.** Inside the child, S-R1 is closed, with a known overshoot
(S-R2-3). The child cannot take down the refresh. Every hostile file ends as a `SourceError`, and
nothing else escapes.

The ruling does not hold for the parent. D-165 says the ceiling "is the bound", and the commit
message says "the parent at most 73 MB". The parent is the refresh process, which D-165 exists to
protect. That process still reads whatever the reader writes, with no bound, through two channels:

- the answer (rows);
- the refusal reason.

A text file and a vision file that together weigh 7.8 MB take the refresh process to **1,246 MiB**,
2.4 times the reader's ceiling. That is the same magnitude as the >1 GB that made S-R1 BLOCKING.
This time the total is bounded (by the row cap, the value cap, the ceiling and the download cap),
not linear, but no control enforces that bound and no one measured it. The fix is small: cap what
the parent accepts from the reader. Details are under S-R2-1.

If the owner rules that a transient of about 1.3 GB in the refresh process is acceptable, S-R2-1
drops to MINOR. That is the owner's decision, and this review does not make it.

## Measurements: the earlier seats' files through the real path

| File (seat) | Size | Parent peak | Child peak | Outcome |
|---|---|---|---|---|
| amp_1000_1, amp_200_20, amp_4000_1 (1st) | 1-2 KB | 38 | 57-133 | `SourceError`: value too long |
| forged (1st) | 15 KB | 38 | 355 | `SourceError`: value too long |
| p_1 / p_100 (re-review) | 0.8 / 33 KB | 38 | 56 / 319 | `SourceError`: value too long / decode budget |
| p_300 / p_600 / p_1200 (re-review) | 97-389 KB | 38 | 519-529 | `SourceError`: ceiling |
| single_256m (re-review) | 9 KB | 38 | 541 | `SourceError`: ceiling |
| distinct_256 / distinct_1024 | 15 / 58 KB | 38 | 526 / 536 | `SourceError`: ceiling |
| **r3_50k (re-review)** | 29 KB | 38 | **706** (5 of 5 runs) | `SourceError`: ceiling, but 38% over it (S-R2-3) |
| r_1m, r_2400k, r_2700k, r3_600k, r3_1200k | 63-390 KB | 38 | 70-257 | `SourceError`: more than 50,000 rows read (S-R2 holds) |
| fg_cols / fg_rg (honest shapes, forged footer) | 7.3 / 10.1 MB | 45 / 70 | 207 / 175 | returned rows |

I also re-ran both earlier seats' value and dictionary probes (`sec-rr/values.py`, `sec-rr/dicts.py`),
24 cases in all, through the new path. Every one gives the same outcome the re-review recorded.
Non-finite ratings are refused. A date that does not parse is refused (S-R4 holds). Invalid UTF-8
is a `SourceError`: I tried an encoded lone surrogate, a raw 0xff and an overlong NUL, both through
`parse_arena_slices` and through `_ingest_slices`. None of them reaches sqlite.

## Findings

### S-R2-1 BLOCKING: the parent reads the reader's output with no bound. A hostile pair of files takes the refresh process to 1.25 GB.

**Where.**

- `arena_slices.py:207-210` calls `subprocess.run(..., capture_output=True)`, which buffers all of
  stdout and all of stderr.
- `:226` calls `json.loads(done.stdout)` on the whole answer.
- `:230-232` copies the child's `error` string into the `SourceError` without truncating it.
- `build.py:453-456` then calls `_board_failed` once per slice of the config, 26 times for `text`.
  Each call copies `f"{source}: {why}"` into `drift` and into `missing` (`:378`, `:380`).
  `_surfaces_left_without_evidence` (`:343-366`) then makes a third copy.

**Channel (a): the answer.** Take a file of N rows in which every text value is 256 copies of
`\x01`. Dictionary encoding stores each value once, so the file is 8 KB. Each value is 256 bytes in
memory, and the check at `parquet_reader.py:108-111` passes it at exactly 256 characters. But
`json.dumps` (with `ensure_ascii`) writes each character as `\u0001`, so the answer is six times the
data (`sec-rr2/esc.py`):

| Rows (all the same row) | File | Answer | Child peak | **Parent peak** |
|---|---|---|---|---|
| 10,000 | 4,448 B | 45 MB | 156 | 206 |
| 30,000 | 6,230 B | 134 MB | 357 | 544 |
| 45,000 | 8,000 B | 201 MB | 508 (under the ceiling) | **797** |
| 50,000 | 8,012 B | 224 MB | 558: ceiling, answer dropped | 38 |

Here is where the parent's memory goes for the 45,000-row file (`sec-rr2/parent_phases.py`):

- 534 MiB after `subprocess.run`: `communicate` keeps a list of chunks and then joins them.
- 790 MiB after `json.loads`: the whole bytes object is decoded to a str before it is parsed.

The child stayed legal the whole time: it read no more than 50,000 rows, no value over 256
characters, and it stayed under its ceiling. For comparison, an honest `text`-shaped file of 10,606
rows gives an answer of 1.6 MB.

**Channel (b): the refusal reason.** `_check_columns` puts the column's type in its refusal
(`parquet_reader.py:77-79`), and the file's writer chooses that type. If `rating` is a
`struct<name: int8>` whose field name is 3.9 MB, the reason is a single 3.9 MB string. The name
starts with `\x1b[2J\x1b[31mFORGED LOG LINE\n`. The file is 7.8 MB, under the 8 MiB download cap
(`sec-rr2/longmsg.py`). Through `_ingest_slices` with both configs, the reason becomes 35 drift lines
and 35 missing lines, 130 MB each, and 130 MB of operator actions. Peak memory of the refresh process
(`sec-rr2/drift_mem.py`):

- 48 MiB at the start;
- 328 MiB after `_ingest_slices`;
- 448 MiB after the operator actions;
- **712 MiB** once the build's report (260 MB with `indent=2`) is serialised.

**Both channels in one cycle** (`sec-rr2/combo.py`): `text` carries the long reason and `vision`
carries the escape-amplified answer. The two downloads total 7,808,885 bytes. The refresh process
peaks at 1,015 MiB after `_ingest_slices` and at **1,246 MiB** once the report is serialised. The
child peaks at 508 MiB, never past its ceiling.

**Why BLOCKING.**

- The ruling bought a process boundary to bound this process. D-165 clause 3 says "the ceiling is
  the bound". It is the bound for the child only.
- The commit's claim ("the parent at most 73 MB") covered neither channel.
- This repository has met this defect before. M16-W2 security MINOR-1 found a child's output
  buffered whole: 200 MB took the server to 974 MB. That was fixed with a 64 KiB tail
  (`nightly.py:90-92`). Here the same shape has a demonstrated trigger from untrusted input.

**Fix.**

1. Read the reader's stdout with a cap: use `Popen` with a bounded read, and kill the reader past
   `MAX_READER_ANSWER_BYTES` (16 MB is ten times the honest 1.6 MB). Keep a stderr tail, not the
   whole stream.
2. Truncate the reason, and escape control characters in it, once in `_read_table`. `build.py:326`
   already caps upstream names at 80 characters (`UNMATCHED_NAME_CHARS`) for the same reason.
3. Optionally, write the answer with `ensure_ascii=False`. That shrinks astral and Latin text but
   not control characters, so the cap stays the control.

A test that feeds the 8 KB file and asserts the parent's peak would kill a regression.

### S-R2-2 MINOR: a hostile reason is persisted and parsed by the serving process on every `/health`.

**Where.** `refresh.py:717` writes `outcome.drift` into `<db>.refresh.json` without a size bound.
`nightly.py:356` calls `read_record` on every `/health` request, and `read_record`
(`nightly.py:128-135`) reads and `json.loads` the whole file. `/health` shows only the source names
(`_drifted`, `nightly.py:176-179`), so the text never reaches a response. The serving process parses
it all the same.

**Measured** (`sec-rr2/health_read.py`). With the 35 drift lines from channel (b), the record is 136
MB. One `/health` read takes 157 ms, and the serving process's peak goes from 24 MiB to **420 MiB**.
The cost repeats on every request until the next cycle replaces the record. The raw ESC sequences
and newlines are stored as they are. JSON escapes them in the record, but any consumer that prints a
drift line unescaped would carry them into the log.

**Why MINOR.** The server binds to 127.0.0.1 (`ios/app.sh:93`). The only callers are the owner's
scripts, and the iOS app does not poll `/health`. The trigger needs a hostile upstream file, and the
cost is bounded. S-R2-1's truncation (fix 2) closes this finding too. It is listed separately because
it lands in the serving process and persists for a day.

### S-R2-3 MINOR: the watchdog is starved while the GIL is held. The ceiling is soft, by up to 38%.

**Where.** The watchdog (`parquet_reader.py:42-46`) needs the GIL to call `getrusage` and
`os._exit`. `main` calls `json.dumps(answer)` (`:130`) as a single C call that holds the GIL for its
whole run and builds the full answer.

**Measured.** The re-review's `r3_50k.parquet` holds 50,000 rows of 256 four-byte characters, which
the checks allow. It stops the reader at **706 MiB** in 5 of 5 runs. The phases with the watchdog off
(`sec-rr2/phases.py`):

- 277 MiB after `read_rows`;
- 723 MiB after `json.dumps` (a 443 MB answer);
- 1,158 MiB after the `encode` that `write` performs.

The watchdog fires between those phases. When pyarrow decodes with the GIL released, the watchdog
runs normally. Three text columns decompressed in parallel (`sec-rr2/par.py`, footer forged) stopped
at 521-591 MiB. The commit's "513-527 MB" does not cover either case.

**Why MINOR.** The overshoot is bounded by the largest answer the row cap and the value cap allow,
about 0.2 GB, and the refresh process is unaffected. Fix 1 of S-R2-1 caps the answer. With that cap
the dump is small, and the overshoot falls to what the parallel decode can add. Alternatively, have
the child count the answer's size as it collects rows, before it serialises. Either way, the ceiling
should be documented as "512 MiB plus the overshoot measured".

### S-R2-4 MINOR: the reader inherits the whole environment and imports from the working directory.

**Where.** `arena_slices.py:204-205` passes `{**os.environ, ...}`, and `:82-83` runs
`python -B -m`, which puts the working directory first on `sys.path`.

**Measured** (`sec-rr2/inherit.py`, which runs a probe through the same `subprocess.run`):

- The child saw every token-like variable I set, 54 variables in all.
- Its only open descriptors were 0-2, because `close_fds` is on by default. That is good.
- A `pyarrow.py` placed in the working directory replaced the reader. `_read_table` returned that
  file's forged row (`PLANTED`, 9999.0).

**Why MINOR.** Planting a file in the working directory needs write access there, which is already
code execution. The parent resolves imports the same way when it runs with `-m`. The nightly path
already strips tokens: the engine starts the refresh with the `CHILD_ENV` allowlist
(`nightly.py:87-89, 258`). So the exposure is limited to manual runs. Still, the child is where a
hostile file meets a native parser, and the process boundary isolates memory, not privilege.

**Fix.** Pass a minimal environment (`PATH`, `HOME`, `LANG`, `TMPDIR`, `PYTHONPATH`). That follows
the project's own `CHILD_ENV` precedent. Also add `-P` (Python 3.11+) so the working directory is
not on `sys.path`.

## What holds

- **Timeout and kill.** I froze the real reader with SIGSTOP and set a 3 s limit
  (`sec-rr2/timeout.py`). The call ended at 3.01 s with a `SourceError`. The reader was killed and
  reaped: no zombie remained, and the parent had no children left. The reader starts no processes,
  so a kill leaves no grandchildren. `subprocess.run` waits after it kills, so a stray descriptor
  holder could not hang it anyway.
- **Orphaned reader (a residual, not a finding).** The engine kills only the refresh's own pid when
  the refresh passes its 30-minute limit (`nightly.py:298`). A reader running at that moment would be
  orphaned, and it has no time limit of its own. It ends on its own: stdin reaches EOF, or the write
  fails with EPIPE, and the slowest file I built parsed in 1.3 s (a 10.4 MB file of 20,000 one-row
  row groups).
- **Peak versus current RSS.** Peak is the right choice, because a short spike cannot slip between
  polls. On macOS, `ru_maxrss` leaves out compressed pages, so under memory pressure the child's real
  footprint can exceed what the watchdog sees. That was not reproducible without such pressure.
- **Nothing but `SourceError` leaves `_read_table`, `fetch_slices` or `_ingest_slices`.** That holds
  for every file above, including crash, timeout, garbage stdout and invalid UTF-8.
  - The only other exception `_read_table` could raise is `MemoryError` in `json.loads`, and S-R2-1's
    cap removes that.
  - The child cannot produce deep nesting, so `RecursionError` cannot happen.
  - `fetch_bounded_bytes` now turns anything that is not a `SourceError` into one
    (`protocols.py:84-94`), which closes S-R3.
- **Hygiene.** `ruff --select S` is clean on the three changed modules, and `make secrets`
  (gitleaks) reports no leaks. `pyarrow` is imported only in the reader, and a test checks that the
  server never loads it.

## Reproduction

Every script is in `scratchpad/sec-rr2/`. Run each one with `PYTHONPATH=<worktree>/src` and the
worktree's `.venv/bin/python`.

| Script | What it does |
|---|---|
| `run.py <file>` | Parent and child peaks through `parse_arena_slices` |
| `esc.py` | Channel (a) files |
| `longmsg.py` | Channel (b) file |
| `parent_phases.py` | Where the parent's memory goes, phase by phase |
| `drift_mem.py` | Channel (b) through `_ingest_slices` |
| `combo.py` | Both channels in one cycle |
| `health_read.py` | The cost of one `/health` read |
| `phases.py` | The reader's phases with the watchdog off |
| `par.py` | The parallel decode |
| `inherit.py` | What the reader inherits |
| `timeout.py` | The frozen reader |
| `surrogate.py` | Invalid UTF-8 |
