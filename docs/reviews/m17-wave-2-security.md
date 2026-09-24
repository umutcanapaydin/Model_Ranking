---
record_type: review
id: m17-wave-2-security
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---

# M17-W2 security review: Arena's category slices read from a downloaded parquet file (#22, D-164)

**Independent:** yes. I wrote none of the code under review. I changed no repository file except this
one, and I made no git state change. I built and ran every hostile file in a scratch directory
outside the worktree. I used no outbound network except `make deps` (pip-audit) and
`make slopsquat`. Every transport probe ran against a loopback server.

## Scope

Range `04e2630..78db5e0` (HEAD `78db5e0`). The plan (`docs/plans/m17-wave-2-plan.md:11`, `:136`)
asked for a security look at the new read path. That path adds a native parser for a file downloaded
from the internet.

- `src/app/clients/arena_slices.py`: `ArenaSliceClient.fetch_bytes`, `_read_table`, `_date`,
  `parse_arena_slices`.
- `src/app/clients/protocols.py`: `fetch_bounded_bytes`, the helper the download relies on. Its
  code is unchanged by this range.
- `pyproject.toml`: `pyarrow>=21.0`, and the mypy override for `pyarrow.*`.
- The D-154 / W-125 claim that the serving process never loads pyarrow. The server now imports
  `arena_slices` through `src/app/workflows/rank.py:19`.
- `src/app/workflows/build.py`: `_ingest_slices` (`:429-479`) and the `main()` exception policy
  (`:827-842`).

Environment: Python 3.14 project venv, pyarrow 25.0.1, httpx 0.28.1.

## Verdict

**BLOCKING.** There are two blocking findings, and both are in `_read_table`. One small change
fixes both (see S1 and S2). There is also one minor and two nits.

The served artifact is never at risk. The build writes a candidate, and nothing publishes unless
the build finishes. The blocking findings are about the unattended nightly cycle.

- **S1:** a 3,920-byte file stops the refresh for every source, every night.
- **S2:** the footer checks do not bound memory. The code comment and the plan's risk section both
  say they do.

The precedent is M16-W4 F1 (`docs/reviews/m16-wave-4-security-p1.md`), which was rated BLOCKING.
It is the same class of bug. Its remedy said "an allowlist of exception classes is the shape that
failed here", and `epoch_bundle.py:110` was then made total. `_read_table` uses that allowlist
shape again.

## Findings

### S1 BLOCKING: non-`SourceError` exceptions escape the read and end the whole nightly cycle

**Where.** `arena_slices.py:161` and `arena_slices.py:183` catch only
`(pa.ArrowException, OSError, ValueError)`. `build.py:456` catches only `SourceError` around the
download and parse. `build.py:835` treats every other class as a builder bug and re-raises it at
`build.py:842`.

**What escapes.** I measured this with `parse_arena_slices` against small hand-built files. Each file
has the four required columns and passes every footer check.

| Hostile column | Escapes as |
|---|---|
| `leaderboard_publish_date` typed `date32`, value `2**31-1` (or `-2**31`) | `OverflowError: days=2147483647; must have magnitude <= 999999999` |
| `leaderboard_publish_date` typed `date64`, value `2**62` | `OverflowError: days=1836388031; ...` |
| `leaderboard_publish_date` typed `timestamp[us]`, value `2**62` | `OverflowError: date value out of range` |
| `leaderboard_publish_date` typed `timestamp[ms]`, value `2**62` | `OverflowError: Python int too large to convert to C int` |
| `rating` typed `timestamp[us]`, value `2**62` | `OverflowError: date value out of range` |
| `model_name` typed `duration[s]`, value `2**62` | `OverflowError: Python int too large to convert to C int` |

`OverflowError` is an `ArithmeticError`, not a `ValueError`. It is raised by `to_pylist()` at
`arena_slices.py:182`, inside the guard, but the guard does not name it.

**Through the build.** I drove `build._ingest_slices` with the real `ARENA_SLICES`, a 3,920-byte
hostile `text` file (date32 max) and a valid `vision` file. The result:

```
_ingest_slices raised OverflowError days=2147483647; must have magnitude <= 999999999
| caught by build main()'s exit-2 tuple: False
```

So the build dies with a traceback. The refresh records "the cycle crashed" or "could not be built"
(`refresh.py:804`, `:1081`), and nothing publishes that night. That includes the valid `vision`
slices, LiteLLM, the `overall` Arena boards, OpenRouter, Epoch and every other source. The same bytes
do it again every night until the upstream changes. The `_ingest_slices` docstring (`build.py:444`)
says a slice "never fails the build". The per-source fail-open direction (D-156, and the
`SourceError` contract in `protocols.py`) says the opposite of what happens here.

**Who can trigger it.** Anyone who controls the bytes at the URL: the dataset's maintainers, anyone
holding their Hugging Face write token, or anything a redirect points at (S3). A well-meaning schema
change can trigger it too. The comment at `arena_slices.py:190` expects a typed date column "if the
file ever changes". A typed column with one corrupt value is enough.

**Remedy.**
1. Make `_read_table` total over bad input, with the M16-W4 F1 shape. Wrap everything from
   `pq.ParquetFile(...)` through `to_pylist()`. Re-raise `SourceError` unchanged, and turn any other
   `Exception` into `SourceError(f"arena slices: unreadable parquet file: {type(exc).__name__}: {exc}")`.
   Wrap the date and row handling in `parse_arena_slices` (`:207-236`) the same way, or move them
   under that guard.
2. Check the four columns' Arrow types against the footer schema before reading. `model_name` and
   `category` must be string, large_string, or a dictionary of those. `rating` must be floating or
   integer. The date must be string, `date32` or `timestamp`. Refuse every other type as
   `SourceError`. A type nobody expects should not reach `to_pylist`.
3. Regression tests: date32 `2**31-1` and timestamp[us] `2**62` through `parse_arena_slices`
   (expect `SourceError`). Also one through `_ingest_slices`, asserting that the other config's
   slices are still stored.
4. Optional, as defence in depth: `_ingest_slices` could treat any `Exception` from one config's
   download or parse as that config's failure, and log the class. `BaseException` would still
   propagate. `main()`'s tuple should stay narrow, as its comment argues. The source boundary is the
   right place to fail open, not the builder's top level.

### S2 BLOCKING: the footer checks do not bound what the read materialises

**Where.** `arena_slices.py:42-47` states the purpose: "a small file can declare a table that would
fill this machine, and reading it first is paying for it first". `:166-172` checks `num_rows` and the
sum of `total_byte_size`. `:182` then materialises all four columns at once and converts them to
Python objects. The plan's risk section (`m17-wave-2-plan.md:136`) says the native parser is "Bounded
by the size cap before parsing".

**(a) Dictionary encoding. No forgery needed: stock `pq.write_table` defaults.** One dictionary
value is referenced by every row through RLE indices. `total_byte_size` is written honestly: it is
the encoded size, so the dictionary is counted once. The Arrow read decodes the dictionary into a
dense column, and `to_pylist` makes one Python `str` per row. I measured each file in a fresh process
(`ru_maxrss`; macOS memory compression makes this an understatement):

| File | Rows | Declared | Peak resident |
|---|---|---|---|
| 1,023 B | 1,000 | 1,048,892 B | 3,130 MB |
| 1,024 B | 4,000 | 1,048,892 B | 5,220 MB |
| 1,631 B | 200 | 20,971,837 B | 4,759 MB |

Every one of these passes all three checks: under 8 MiB, under 50,000 rows, and under 64 MiB
declared. The cost is about rows × value size × 2. At the caps (50,000 rows, a dictionary value just
under 64 MiB, and the file still about 2 KB with zstd), the allocation runs to terabytes. On the
owner's macOS machine that means swap growth until jetsam or the 30-minute kill (`nightly.py:71`).
Whichever comes first, the whole night is lost, as in S1, and the machine that runs the server is
thrashing meanwhile.

**(b) The footer is the writer's word.** I built a plain-encoded (`use_dictionary=False`), zstd file
of 300 × 1 MiB values. Its honest `total_byte_size` of 314,584,113 bytes is refused. I then rewrote
that one varint in the footer to a non-canonical encoding of 1,000, at the same length, and nothing
else. The 15,194-byte file now declares `total_byte_size` 1,000, passes every check, and parses with
a peak resident size of 967 MB. zstd compressed it about 20,000:1, so a file at the 8 MiB cap
reaches the hundreds-of-GB range. `num_rows` is also only declared, but it is not the binding
problem: 50,000 rows is enough.

The same gap lets arbitrarily long `model_name` strings through. `score_rows` (`arena.py:381`)
accepts any `str`, and D-160 (W4) serves these boards.

**Remedy.** I measured this remedy against both files above:
1. Open with `pq.ParquetFile(..., read_dictionary=["model_name", "category",
   "leaderboard_publish_date"])`, so a dictionary page stays a dictionary.
2. Read with `iter_batches(batch_size=256, columns=list(_COLUMNS))` and keep a running
   `batch.nbytes` budget against `MAX_UNCOMPRESSED_BYTES`. That makes the bound measure what was
   decoded, not what was declared.
3. Before `to_pylist`, refuse any dictionary whose longest value is over a small cap, for example
   `pc.max(pc.binary_length(col.dictionary)) > 512`. A model name, category or date is short.

With 1 and 2, the 4,000-row dictionary file read at a peak of 48 MB and the forged file at 345 MB.
Point 3 then keeps `to_pylist` from re-expanding the long values.

A residual risk remains. pyarrow decodes one page at the uncompressed size declared in that page's
header, up to about 2 GiB. The only complete bound is a per-process memory limit, and macOS does not
enforce `RLIMIT_AS`. If the owner accepts that residual, record it (`/log-decision`) instead of
leaving the comment at `:42-45` to claim more than the code does. Add regression tests for (a) and
(b).

### S3 MINOR: the "bounded in time" download is bounded only once the body starts

**Where.** `arena_slices.py:144`'s docstring says "capped while it is read and bounded in time",
with `_DEADLINE_S = 120` (`:41`). But `protocols.py:74` checks the deadline only inside the
`iter_bytes()` loop. Connecting, the TLS handshake, the response headers and every redirect hop all
happen before the first chunk arrives. None of them counts against the deadline. `follow_redirects`
is left at its default `True` (`protocols.py:48`), so httpx follows up to 20 hops, to any host and
any scheme.

**Measured on loopback, with `timeout=2`, `deadline=3`:**
- A server that drips one header line a second ran for 12.2 s, 4x the deadline. The deadline fired
  only when the body began.
- 20 redirects, each answered after 1.5 s, ran for 31.7 s before httpx gave up on the redirect
  count.

With the real values (30 s per operation, 21 hops, and h11's 16 KiB header buffer at
`DEFAULT_MAX_INCOMPLETE_EVENT_SIZE`), time before the body is effectively bounded only by the engine's
30-minute kill. That kill loses the whole night, as in S1.

This is the helper's pre-existing behaviour. M16-W4 F4's remedy covered only the body loop. The
epoch bundle avoided the redirect half with `follow_redirects=False`
(`epoch_bundle.py:133`). This client cannot do that: `resolve/main` on Hugging Face normally
redirects a large file to its CDN. I did not verify that live, because outbound network is ASK.

**What holds.** The byte cap counts decoded bytes. A gzip bomb (203,860 bytes on the wire, 200 MiB
decoded) was cut at 8 MiB with no growth in resident size. httpx 0.28.1 has no brotli or zstd decoder
installed in this venv, so it neither advertises nor decodes those encodings. No credentials are sent
on any hop, and TLS verification is httpx's default.

**Remedy.** Add a `response` event hook to the stream. On every hop, it should refuse a
non-`https` URL, refuse a host outside an allowlist (`huggingface.co`, `*.hf.co`), and check the
monotonic deadline. For a hard wall-clock bound that also covers a header drip, run the stream under
a watchdog that closes the client when the deadline passes. At minimum, reword the docstring so it
claims only what holds.

### S4 NIT: the newest date is an unvalidated string maximum over every row in the file

`_date` (`arena_slices.py:193`) keeps any non-empty string's first 10 characters. `newest`
(`:214`) is the lexicographic `max` over all rows, including categories no slice reads. So one row
dated `9999-12-31`, or any string that sorts above `2026` such as `TBD`, moves `newest` to a date no
declared slice has. Every slice of that config then falls under its floor.

The failure is safe. Each slice raises `SourceError` and carries under D-156, and nothing is ever
served stale. The rule is also the same one `parse_arena` uses (`arena.py:351`). But one stray row
turns 26 boards dark. Accept only values that parse as `YYYY-MM-DD` (`dt.date.fromisoformat`), and
count the rest as refused.

### S5 NIT: two stale sentences about where pyarrow lives

- `arena_slices.py:17` says pyarrow "is imported inside `parse_arena_slices`". It is imported in
  `_read_table` (`:152-154`).
- The docstring of `tests/unit/test_arena_slices.py:267-270` says "today it never imports
  `arena_slices`". The server does import it now, through `rank.py:19`. That makes the server half of
  the test live rather than vacuous, which is good, but the sentence is now wrong.

## What holds

- **The serving process never loads pyarrow (D-154, W-125).** I checked this directly: importing
  `app.adapter.main` leaves `app.clients.arena_slices` in `sys.modules` (`True`) and `pyarrow` out of
  it (`False`). `tests/unit/test_arena_slices.py::test_neither_the_server_nor_the_slice_module_loads_pyarrow`
  passes for both parameters. Only `_read_table` and the test helper `fakes.slice_parquet` import
  pyarrow, and only the build, the refresh child and the scripts call `parse_arena_slices`.
- **Dependencies.** `make deps` (pip-audit `--strict`) reports "No known vulnerabilities found", and
  `make slopsquat` reports "PASS: 18 declared dependency(ies), 0 suspect". pyarrow 25.0.1 is
  installed. The `>=21.0` floor is far above the fix for CVE-2023-47248 (14.0.1: arbitrary code on
  reading `PyExtensionType` metadata). An `arrow.json` extension annotation and a garbage
  `ARROW:schema` were both read harmlessly. For the record: pip-audit sees the pyarrow wheel, not the
  C++ libraries vendored inside it (thrift, zstd, snappy, lz4, brotli), and the project has no
  lockfile, so the floor is the only pin.
- **mypy override.** `ignore_missing_imports` is scoped to `pyarrow` and `pyarrow.*` only.
- **Other malformed inputs map to `SourceError`, as intended.** I checked: not a parquet file, a
  truncated footer, an empty body, invalid UTF-8 in a string column (a `UnicodeDecodeError`, which
  is a `ValueError`), a 400-deep nested list column (the flatbuffers verifier), an unknown or
  out-of-range timezone, and a `time64` date column. A decimal, map, 50-deep list or duplicate-name
  column is refused row by row, not crashed on. The read projects only the four required columns.
- **Secrets.** `make secrets` (gitleaks) found no leaks.

## Gates

- [x] Secret scan green (`make secrets`)
- [x] `make deps` (pip-audit) green
- [x] `make slopsquat` green
- [x] No new external surface on the server. The server loads the declared slice table, not the
  parser.
- [ ] Hostile input to the read path fails as a source (S1 and S2 block)
- [ ] SAST: `bandit` is not installed in the venv, so it did not run. The findings above come from
  targeted hostile-input runs.

## Risks queued

- S3's pre-body time bound lives in the shared helper, so it affects every fetched source, not just
  this one. If it is not fixed in this wave, it should become an issue (`/file-issue`).
- The residual in S2 (one page decoded at its declared size) needs an owner decision if the batched
  read is adopted without a process memory limit.
