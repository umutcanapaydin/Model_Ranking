---
record_type: review
id: m17-wave-2-security-rereview
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-24
---

# M17-W2 security re-review: the fix of the slice parser's security look (#22, D-164)

**Independent:** yes. I wrote none of the code under review, and I did not write the first security
look (`docs/reviews/m17-wave-2-security.md`). This file is the only repository file I changed. I
made no commit and no git state change. Every hostile file and probe lives in a scratch directory
outside the worktree (`scratchpad/sec-rr/`, plus the first seat's `scratchpad/sec-m17w2/`). Every
transport probe ran against a loopback server. I used no outbound network.

## Scope

The fix is `0b7a535`, and its red tests are in `ac7bf89`. HEAD is `b4e41f2`, which is docs only. I
re-checked these functions:

- `src/app/clients/arena_slices.py`: `fetch_slices` (`:157-164`), `_read_table` (`:167-182`),
  `_bounded_rows` (`:185-230`), `_check_columns` (`:233-252`) and `parse_arena_slices`
  (`:259-304`).
- `src/app/workflows/build.py`: `_ingest_slices` (`:430-478`) and `main()`'s exit-2 tuple (`:833`).
- `src/app/clients/protocols.py`: `fetch_bounded_bytes` (`:45-87`). The slice download goes
  through it, and this range does not change it.

I did not re-review S3 (the pre-body time bound), which is filed as #25. S-R3 below belongs with it.

Environment: Python 3.14.0, pyarrow 25.0.1, httpx 0.28.1, idna 3.20, and a 16 GiB macOS machine.
Each file was parsed in a fresh process, and peak RSS was read with `ru_maxrss`. macOS compresses
memory, so that figure understates the real cost.

## Verdict

**BLOCKING.** S1 is closed. S2 is closed only for honest footers.

- **S1 is closed for the parser.** Every hostile file I tried now ends as `SourceError`. That
  includes the first seat's 27 files, the date32 case through `_ingest_slices`, and new files with
  odd values, dictionaries and encodings. Nothing escapes `parse_arena_slices`, either inside the
  read or after it. A non-`SourceError` does still escape the slice path, but from the shared HTTP
  helper, not from the parser. That escape is S-R3, and it predates this wave.
- **S2(a) is closed.** The stock-writer dictionary bomb now peaks at 72 MB. It peaked at 5.2 GB
  before the fix.
- **S2(b) is not closed. This is S-R1.** A file whose footer lies still has no memory bound. The
  code comment (`arena_slices.py:193-194`) and the plan (`m17-wave-2-plan.md:139`) say that what
  remains is "one page decoded at the size its own header declares". The measured residual is one
  2,048-row batch. That batch can span up to 2,048 pages in each text column: a 389 KB file
  reached 4.2 GB. The decode budget is checked only after the whole batch has been decoded.

The fix for S-R1 is small, and it can land together with S-R2's.

## Findings

### S-R1 BLOCKING: the decode budget is checked after a whole batch, and a batch spans many pages. The residual is not "one page".

**Where.** `arena_slices.py:218-222` reads `iter_batches(batch_size=_BATCH_ROWS, ...)` with
`_BATCH_ROWS = 2_048` (`:53`). It adds `batch.nbytes` to the budget only after pyarrow has built
the batch. A value is never split across pages, but a batch of 2,048 rows can take its values from
2,048 separate pages. pyarrow decompresses each page at the size in that page's own header. The
footer check at `:210-213` reads `total_byte_size`. The footer's author can forge that field (S2(b)),
and nothing else bounds what one batch decodes.

**Measured.** Each file has `model_name` values of 1 MiB, one value per page. The values are
distinct, the pages are plain-encoded and zstd-compressed, and `total_byte_size` is forged to
1,000 with the first seat's same-length varint rewrite:

| Pages in the first batch | File | Peak RSS | Outcome |
|---|---|---|---|
| 1 | 849 B | 71 MB | refused: value too long |
| 100 | 32,840 B | 334 MB | refused: over the decode budget |
| 300 | 97,448 B | 970 MB | refused: over the decode budget |
| 600 | 194,348 B | 1,814 MB | refused: over the decode budget |
| 1,200 | 388,750 B | 4,232 MB | refused: over the decode budget |

Each file is refused with a `SourceError`, but only after the memory has been spent. The cost grows
linearly, at about 3.5 bytes resident per byte decoded. For comparison, a single page with a
256 MiB value costs 835 MB. That single-page case is the declared residual, which works out to
about 6.5 GB for a page at the 2 GiB header maximum.

Past 1,200 pages the numbers are an extrapolation; I did not run them. One batch is 2,048 rows,
across three text columns. Under zstd a long run of equal bytes costs a few bytes per 128 KiB
block. So a file under the 8 MiB download cap can declare 2,048 pages of tens of MiB each in each
column. That is tens to hundreds of GB for the first batch, well past the machine. The nightly
cycle then dies to jetsam or to the 30-minute kill. That is S2's original consequence: the whole
night is lost, for every source.

Identical values do not reproduce this. The dictionary builder deduplicates them (600 identical
pages peaked at 72 MB), so the file needs distinct values. It also needs a forged footer, so the
attacker is the same one as in S2(b) and #27: whoever controls the bytes at the URL.

**Why BLOCKING.** The first look rated S2(b) BLOCKING at 967 MB. The fix records a residual of one
page, and the owner is asked to accept that residual. The measured residual is up to 2,048 pages
per column, which has no practical bound. Both the comment and the plan claim a bound the code does
not have, the same defect S2 named.

**Remedy.** Choose one of these two:

1. **Small batches, with the dictionary counted once.** `_BATCH_ROWS = 16` brings the 600-page
   file down to 102 MB, and `_BATCH_ROWS = 1` brings it to 71 MB. **Do not only shrink the batch.**
   `batch.nbytes` counts the whole dictionary again in every batch. For plain-encoded pages that
   dictionary also grows cumulatively (measured: 2048, 4096, 6144, ... entries). At
   `_BATCH_ROWS = 1`, a synthetic 10,606-row honest file shaped like `text` was **refused** (over
   32 MB "decoded"). At 16 it parsed in 81 ms, against 49 ms at 2,048. So count each batch's
   `indices.nbytes`, plus only the growth of each dictionary since the previous batch. What remains
   is about 16 pages per text column. Record that in the comment, the plan and #27.
2. **Pre-scan the page headers (the complete bound).** Each column chunk's page headers are plain
   Thrift-compact structs, and the whole file is already in memory. Walk them from the chunk's
   dictionary or data page offset, the same offset pyarrow reads from. Sum `uncompressed_page_size`
   over the four columns, and refuse above the budget before anything is decoded. pyarrow allocates
   exactly that header size and fails any page that decompresses to a different length. So this
   bounds what the read can decode, and it would also close #27. It costs about 60 lines, and it
   needs its own hostile tests.

In either case, add the regression tests the first look asked for and that the fix did not add:

- a forged-footer file;
- a batch whose first rows each come from a separate page, with a patched budget;
- an assertion that the refusal happens with less than N MB resident.

`test_decoding_past_the_budget_is_refused` (`tests/unit/test_arena_slices.py:179`) uses one batch of
50 short rows, so it cannot tell a check made before decoding from one made after.

### S-R2 MINOR: the row cap reads a forgeable field, and the Python objects are outside the budget

**Where.** `arena_slices.py:207` compares `meta.num_rows`, the file-level `FileMetaData.num_rows`,
with `MAX_PARQUET_ROWS`. The reader does not use that field. It decodes the row count of each row
group. `:229` then converts every batch to Python dicts and strings, and the decode budget never
counts those.

**Measured.** In these files only the file-level `num_rows` is forged, to 1,000. The row groups keep
the true count, and `total_byte_size` is honest:

| File | Rows actually read | Values | Peak RSS | Outcome |
|---|---|---|---|---|
| 63 KB | 1,000,000 | short, repeated | 658 MB | **returned** after 4.3 s |
| 65 KB | 2,400,000 | short, int8 rating | 1,400 MB | **returned** after 10.2 s |
| 390 KB | 1,200,000 | every text value at 256 four-byte characters | 4,217 MB | refused only by the date check |

Each row costs the budget about 13 bytes: three int32 indices and an int8 rating. In Python it costs
up to about 3.5 KB, because `to_pylist` makes a new `str` for every row. The 32 MB budget therefore
admits about 2.3 million rows, or about 8 GB resident. That is bounded, and of the same order as the
declared one-page residual, which is why I rate it MINOR. But it passes the stated "50,000 rows" and
"32 MB decoded" bounds by a wide margin. The fix is two lines, and it belongs in the same commit as
S-R1's.

**Remedy.**

- Count `batch.num_rows` as each batch arrives, and refuse past `MAX_PARQUET_ROWS`.
- Optionally, also check `sum(meta.row_group(i).num_rows)` next to the footer checks.
- Test it with a forged `num_rows`. `tools.forge` in the scratch directory shows how.

With the count in place, the Python side is bounded at 50,000 × about 3.5 KB, roughly 175 MB.

### S-R3 MINOR: a non-`SourceError` still escapes the slice download, from the shared HTTP helper, and ends the build

**Where.** `protocols.py:84` catches only `httpx.HTTPError`. `build.py:454` catches only
`SourceError` around `fetch_slices`, and the `main()` tuple at `build.py:833` does not name
`ValueError`. The `_ingest_slices` docstring says a slice "never fails the build" (`build.py:445`).

**Measured.** I ran the real `ArenaSliceClient` with its URL swapped for a loopback server. Each
response was one `302` whose `Location` host is malformed:

| `Location` | Escapes as |
|---|---|
| `http://xn--/x` | `idna.core.IDNAError: Malformed A-label` |
| `http://xn--a/x` | `idna.core.InvalidCodepoint` |
| `https://xn--zz-/x` | `idna.core.IDNAError: A-label must not end with a hyphen` |
| `http://` + 300 × `a` + `/x` | `UnicodeEncodeError: 'idna' codec ... label too long` |

All four are `ValueError` subclasses. Through `build._ingest_slices` the first one gives:

```
_ingest_slices raised idna.core.IDNAError: Malformed A-label, no Punycode eligible content found
| caught by build main()'s exit-2 tuple: False
```

Here `text` answered with the bad redirect and `vision` answered with a valid file. `vision`'s slices
are never stored, the build ends with a traceback, and nothing publishes that night. Thirteen other
malformed answers all ended as `SourceError`: an invalid port, a non-ASCII host, `ftp:` and `file:`
schemes, bad gzip, a garbage status line, bad chunking, an empty body and an HTML body.

**Why MINOR here.** The helper predates this wave (`protocols.py` was last changed in `cd2f942`),
and so does its catch. LiteLLM, OpenRouter, SWE-bench and Aider all fetch through it, and the build
catches them with the same `SourceError`-only clause (`build.py:197`). The attacker must control an
HTTP response somewhere on the redirect chain, which TLS protects. This is narrower than S1's
attacker, who controlled the file's bytes. The Epoch bundle does not follow redirects, so it is not
exposed. The slice URL does redirect by design (`resolve/main` to the CDN), and #25 already records
that any host on any scheme is followed.

**Remedy.**

- Give `fetch_bounded_bytes` the shape `_read_table` now has: re-raise `SourceError`, and turn every
  other `Exception` into `SourceError(f"{name} fetch failed: {type(exc).__name__}: {exc}")`.
- Add a loopback test with `Location: http://xn--/x`.
- Optionally adopt S1's remedy step 4, which the fix left out: `_ingest_slices` treats any
  `Exception` from one config's fetch or parse as that config's failure. That would have contained
  this.
- Record the finding on #25, or file it with `/file-issue`, since it affects every fetched source.

### S-R4 NIT: S4 is only partly closed, because the horizon is a string comparison

**Where.** `arena_slices.py:272-274` keeps any `_date` value that compares at or below
`today + 1` as a string. Any value that sorts between the real newest date and the horizon still
becomes `newest`, including values that are not dates.

**Measured.** I used `today=2026-09-24` and 400 real rows dated `2026-09-13`. With one added row
dated `2026-09-2`, `2026-09-1~` or `2026-09-25`, the english slice returns only that 1 row, refuses
400, and stores `run_date` as the stray string. Rows dated `9999-12-31` and `TBD` are now refused
correctly.

**Impact.** The failure is safe. The slice falls under its floor and is carried (D-156). A file with
enough rows under a non-date could store a `run_date` that the staleness readers
(`recommend.py:440-445`, `coverage.py:245-248`) cannot parse, and they then report "unknown" rather
than crash.

**Remedy.** This is the first look's remedy for S4: keep only values for which
`dt.date.fromisoformat(v[:10])` succeeds, then apply the horizon.

## What holds

- **S1 at the parser.** The wrapper at `arena_slices.py:176-182` is total: it re-raises
  `SourceError` and converts every other `Exception` (including `MemoryError` and `RecursionError`).
  `_check_columns` (`:233-252`) refuses every non-string date or name type and every non-numeric
  rating before any value is converted. The first seat's `escapes.py` now ends every case as
  `SourceError` or as a clean return:
  - date32, date64 and huge timestamps are refused by type;
  - an invalid-UTF-8 value becomes `SourceError` (`UnicodeDecodeError`);
  - a duplicate column becomes `SourceError` (`KeyError`);
  - nested, map and depth-400 columns are refused.

  The first seat's `build_escape.py` now returns, with `vision` stored and the `text` slices listed
  as missing.
- **Nothing escapes after the read.** Each of these either returned or became a `SourceError`:
  - ratings: NaN, ±inf, -0.0, 1e308, uint64 max, int64 min and float16;
  - model names that are empty, blank, NUL or RTL-override;
  - dates that are all empty, contain an embedded NUL, or come from an unread category.

  `score_rows` (`arena.py:380-389`) refuses non-finite and out-of-band ratings, and a uint64 or int64
  is in range for `float()`.
- **The value-length check is sound across encodings and dictionaries.** `read_dictionary` always
  gives `dictionary<string>`, including for plain, large_string and string_view columns. The check
  refused a 300-character value in each of these files:
  - plain-encoded throughout;
  - dictionary-encoded that falls back to plain mid-chunk;
  - several row groups, with the long value only in the last group's dictionary;
  - one row group, with the long value in the fourth batch;
  - large_string with a stored Arrow schema;
  - string_view.

  For plain pages the dictionary grows cumulatively across batches, so every value is seen. The
  check measures characters: 257 four-byte characters are refused, and 256 (1 KB) are allowed. An
  empty dictionary, from an all-null column, returns and refuses its rows.
- **S2(a).** The first seat's 1 KB dictionary files peak at 72 MB (they were 3.1 to 5.2 GB), and its
  1.6 KB file peaks at 148 MB. With an honest footer, the footer checks and the budget together hold.
- **The footer is cheap to parse.** A 7.3 MB footer with 60,000 columns parsed at 221 MB in 0.14 s.
  Twenty thousand row groups parsed at 193 MB in 0.84 s, though that file is over the download cap.
- **D-154 still holds.** Importing `app.adapter.main` loads `app.clients.arena_slices` (`True`)
  and not `pyarrow` (`False`). `tests/unit/test_arena_slices.py` passes 35 of 35.
- **Secrets and dependencies.** `make secrets` (gitleaks) reports no leaks. The fix changes no
  dependency manifest (`pyproject.toml` is untouched in `78db5e0..0b7a535`).

## Gates

- [x] Secret scan green (`make secrets`)
- [x] No new dependency in the fix (so `make deps` and `make slopsquat` are unchanged from the
      first look)
- [x] Hostile input to the parser fails as a source (S1)
- [ ] Decoded memory bounded apart from the declared residual (S-R1 blocks, S-R2 minor)
- [ ] Hostile input to the slice download fails as a source (S-R3, which predates this wave)

## Risks queued

- #27 should record the true residual once S-R1 is fixed. If the page-header pre-scan is adopted,
  #27 can close.
- S-R3 affects every fetched source. Record it on #25 or file it on its own.
