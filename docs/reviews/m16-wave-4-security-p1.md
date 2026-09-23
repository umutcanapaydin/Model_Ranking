---
record_type: review
id: m16-wave-4-security-p1
status: ratified
seat: independent
process_version: v6.0
date: 2026-09-23
---

# M16-W4 P1 security review: the refresh fetches the Epoch bundle (D-158)

## Seat

Independent security seat. I wrote none of the code under review and changed no repository file
except this one. I made no git state changes. Every hostile input ran in a scratch directory, against
copies built by the test helpers. The owner's `advisor.db` was never opened. I used the network once,
for one real fetch of the documented URL into scratch.

## Scope

Commit `f2ffaee` ("the nightly refresh fetches the Epoch bundle itself", D-158):

- `src/app/clients/epoch_bundle.py` (new): `fetch_bundle`, `unpack`, `_plan`, `_write`,
  `_safe_relative`.
- `src/app/clients/protocols.py`: `fetch_bounded_bytes` (the `limit=` parameter; `follow_redirects=True`).
- `src/app/workflows/refresh.py`: `_fetched_epoch`, `_discard`, the `_cycle` wiring, `--fetch-epoch`.
- `src/app/adapter/nightly.py`: `refresh_command` now passes `--fetch-epoch` by default.
- Downstream readers of the unpacked files, `src/app/clients/epoch_board.py` and
  `src/app/clients/epoch.py`. I checked how they read the files, but not their parsers in depth.

Line numbers below refer to `f2ffaee`. The branch moved while I worked (`477ef68`, `420a216`,
`1271c59` and an uncommitted `registry.py` edit by another seat). None of those change
`epoch_bundle.py`, `protocols.py` or `_fetched_epoch`/`_discard`. I re-ran every cycle-level
reproduction against a `git archive f2ffaee` export, and the results were identical.

## Policy source

Read only from the protected base:
`git show origin/main:subagent-profiles/Security-Reviewer.md` and
`git show origin/main:docs/security-baseline.md`. The commit touches no policy file.
`git diff origin/main f2ffaee -- subagent-profiles docs/security-baseline.md permission-matrix.md .claude AGENTS.md CLAUDE.md`
is empty. The commit's `docs/prd.md` and `docs/decisions.md` changes only record D-158.

## Verdict

**BLOCKING**: one blocking finding (F1), three minors, two nits.

The served artifact holds on every path I drove: 12 cycle-level cases, including crashes, SIGKILL
and refusals. It was byte-identical afterwards every time. The blocking finding concerns
availability and the slice's own contract, not artifact integrity. A single hostile byte in the
archive crashes the whole nightly cycle for all nineteen sources, instead of carrying the Epoch
boards as D-158 clause 3 promises. The remedy is small (see F1).

## Findings

### F1 BLOCKING: hostile archives escape the refusal path and crash the whole cycle

**Where.** `epoch_bundle.py:101` catches only `zipfile.BadZipFile` around `zipfile.ZipFile(...)`.
`epoch_bundle.py:86` catches `(BadZipFile, zlib.error, EOFError, RuntimeError, NotImplementedError)`
around the member read. `refresh.py:858` (`_fetched_epoch`) catches only `(SourceError, OSError)`.

**What escapes (measured on Python 3.14.0, the project venv):**

| Archive | Exception out of `unpack` |
|---|---|
| member name with the UTF-8 flag (0x800) set and invalid UTF-8 bytes | `UnicodeDecodeError`, raised by `ZipFile()` itself |
| `ZIP_LZMA` member with corrupt properties bytes | `_lzma.LZMAError: Corrupt input data` |
| `ZIP_ZSTANDARD` (method 93, supported by 3.14's zipfile) member with a corrupt frame | `compression.zstd.ZstdError` |

None of these is `SourceError` or `OSError`, so each one walks past `_fetched_epoch` and out of
`_cycle`. `refresh()` records "the cycle crashed" and re-raises, and `main()` exits 2. The build
never runs. That night nothing refreshes, including LiteLLM, Arena, OpenRouter and every other
source. The same bytes do it again on every following night. D-158 clause 3 says a failed or
refused fetch "is a failed source … and nothing else in the cycle changes". The architecture's
fail direction for sources is per-source fail-OPEN (`protocols.py` `SourceError` docstring:
"Ingestion of THIS source aborts loudly; other sources proceed"). This path does the opposite:
content from one upstream stops all of them.

**Who can trigger it.** Anyone who controls the bytes served at `https://epoch.ai/data/benchmark_data.zip`:
epoch.ai, its Cloudflare edge, or anything a redirect points to (see F5). No local access is
needed. The 2026-09-23 real bundle does not trigger it. Nothing in the test suite would catch the
next such exception class either, because the tests cover only the exception types the code
already names.

**Reproduction** (real `refresh()`, real `build.main`, `_first_cycle` from
`tests/unit/test_refresh_carry.py`, on `tmp_path` copies):

```python
payload = zip_with_member("AAAA.csv"); patch b"AAAA" -> b"\xff\xfe\xfd\xfc" and OR 0x800 into the
          general-purpose flag of the local (offset 6) and central (offset 8) headers
live = _first_cycle(tmp_path, monkeypatch)
refresh(live, fetch_epoch=functools.partial(epoch_bundle.fetch_bundle, get=lambda u: payload))
# -> raises UnicodeDecodeError; record: outcome='failed',
#    reason="the cycle crashed: UnicodeDecodeError: ..."; sources_last_ok unchanged;
#    live digest unchanged; scratch dir advisor.db.<rand>.epoch left behind (F2)
monkeypatch.setattr(epoch_bundle, "_download", lambda url: payload)
refresh_mod.main(["--db", str(live), "--fetch-epoch"])     # -> exit 2, stdout "crashed: UnicodeDecodeError"
```

A 40 MB valid deflated member followed by an LZMA member whose bytes 4..8 are XOR-ed with `0xFF`
gives `LZMAError` the same way, and leaves the 41,943,040 bytes it had already written in the
leaked scratch directory.

**Remedy.**

1. Make `unpack` total over bad input. Wrap everything from `zipfile.ZipFile(...)` through the last
   `_write` so that any `Exception` other than `SourceError` becomes
   `SourceError(f"{NAME}: unreadable archive: {type(exc).__name__}")`. An allowlist of exception
   classes is the shape that failed here: the stdlib adds codecs (zstd arrived in 3.14).
2. As defence in depth, have `_fetched_epoch` treat any `Exception` from the fetcher as a failed
   source (log it and carry). `BaseException` should still propagate, but only after cleanup (F2).
3. Add regression tests with the three payloads above: through `unpack` (expect `SourceError`)
   and through `refresh(..., fetch_epoch=...)` (expect no raise, the boards carry, and no scratch
   left behind). Per `writing-a-control`, show each test red on the current code first.

### F2 MINOR: the scratch directory leaks on every exit path except the two named ones

**Where.** `refresh.py:855` creates the scratch with `mkdtemp`. `_fetched_epoch` removes it only in
`except (SourceError, OSError)`. `_cycle` removes it in `finally` through `_discard(epoch_dir)`
(`refresh.py:1034`). But `epoch_dir` is bound only when `_fetched_epoch` *returns*
(`refresh.py:923`), so any other exception raised inside the fetch leaves `epoch_dir is None`, and
the `finally` discards nothing.

**Measured leaks:**

- F1's exceptions: an empty directory for the name case, 41.9 MB for the LZMA case. The unpack
  budget allows up to 256 MB per night.
- `KeyboardInterrupt` (or `MemoryError`) raised in the fetcher after unpacking leaves
  `advisor.db.<rand>.epoch/gpqa_diamond.csv`. By contrast, a `KeyboardInterrupt` in the *builder*
  after a successful fetch is cleaned up, which is correct.
- A killed process (the engine's `proc.kill()` at `TIMEOUT_SECONDS`, the W-124 class) leaves the
  `.epoch` directory next to `.last-ok` and `.sources`. Reproduced with `os.kill(os.getpid(),
  SIGKILL)` from inside the builder after a fetch: exit 137, `advisor.db.<rand>.epoch/gpqa_diamond.csv`
  remains. Nothing sweeps `*.epoch`: `build._sweep_abandoned_workspaces` globs only `*.building`.

**Why it matters beyond disk use.** The nightly artifact is `MODEL_RANKING_DB`, which on the
owner's machine is `advisor.db` in the repository root. `.gitignore` covers `*.candidate` and
`*.building` but not `advisor.db.*.epoch/`, `*.sources` or `*.last-ok`
(`git check-ignore advisor.db.abc.epoch/gpqa_diamond.csv` matches nothing). A leaked directory
therefore shows up as untracked, redistributable-looking content in a public GitHub repository, and
one `git add -A` publishes Epoch's `_external` CSVs, whose licences W-129 records as
not-Epoch's-to-grant.

**Remedy.**

- In `_fetched_epoch`, use `try: fetch_epoch(scratch) except BaseException: rmtree(scratch); raise`,
  with the carry branch for `Exception` per F1.
- Extend the W-124 sweep (it is the same `refresh.py` change) to `advisor.db.*.epoch` directories
  older than a day.
- Add `*.epoch/`, `*.sources` and `*.last-ok` (anchored to the artifact name if preferred) to
  `.gitignore`.

Test each: a fetcher that raises `KeyboardInterrupt` should leave no scratch.

### F3 MINOR: a 64 MB download can cost about 600 MB of RAM before the member-count refusal

**Where.** `epoch_bundle.py:101` (`ZipFile()` parses the whole central directory into `ZipInfo`
objects) runs before `epoch_bundle.py:56` (`len(members) > MAX_MEMBERS`).
`MAX_BUNDLE_BYTES = 64 MiB` (`:34`) is 28 times the real 2.3 MB bundle.

**Reproduction.** I hand-built a zip64 archive of 67,108,769 bytes: one 1-byte local file and
1,312,060 central-directory entries with distinct names. `unpack` refused it correctly
("1312060 members, over the limit of 2000"), but only after 3.1 s. Peak RSS went from 227 MB to
814 MB. The process runs as a child of the serving engine on the owner's machine, and the bound
still holds, so this is a minor.

**Remedy.** Cut `MAX_BUNDLE_BYTES` to about 16 MB, which is still seven times today's bundle.
Optionally, read the entry count from the end-of-central-directory record, or reject the archive
when `len(payload)` minus the central-directory offset is implausible, before building
`infolist()`.

Two related measurements hold and need no change:

- `fetch_bounded_bytes` counts *decoded* bytes. A loopback server sending `Content-Encoding: gzip`
  over 1 GiB of zeros (1.04 MB on the wire) was cut off at 64 MiB with a peak of about 158 MB over
  baseline. Only gzip, deflate and identity decoders are installed (`brotli` and `zstandard` are
  absent), so there is no high-ratio transport codec.
- The unpack budget is counted while writing. Three 100 MB members were refused at 256 MiB in 0.1 s.
  Ten central entries overlapping one 100 MB local body were refused by the budget. A header that
  declares 10 bytes over a 50 MB body was refused by the CRC check.

### F4 MINOR: the download has no total deadline, so a slow upstream costs the whole night

**Where.** `protocols.py:60`: `timeout=timeout` (60 s) is httpx's *per-operation* timeout
(connect, read, write, pool). It is not a deadline for the whole download.

**Reproduction.** A loopback server sent 1 byte every 0.5 s. `fetch_bounded_bytes(..., timeout=1.0)`
kept reading for 6.1 s and stopped only because the server did. At 60 s per read and a 64 MiB
limit, a drip-feeding (or degraded) upstream holds the cycle until the engine's 30-minute
`proc.kill()`. That loses the refresh for every source that night and leaks scratch (F2, W-124).
Existing text sources share the helper, but this is the first large binary download the nightly
depends on by default.

**Remedy.** Track a monotonic deadline across the `iter_bytes()` loop in `fetch_bounded_bytes`,
using a `deadline=` parameter (about 120 s for the bundle), and raise `SourceError` when it passes.
The bundle then fails as a source and carries.

### F5 NIT: redirects are followed to any host and any scheme

**Where.** `protocols.py:60`: `follow_redirects=True`. httpx 0.28.1's `_redirect_url` places no
scheme or host restriction, so an https-to-http downgrade and cross-host hops are followed, up to
20 (`DEFAULT_MAX_REDIRECTS`). Loopback check: a 302 from `127.0.0.1` to `localhost` was followed
and its body returned.

**Real URL today.** One real fetch returned 200 directly: no redirect history, TLS 1.3 served by
Cloudflare, `application/zip`, 2,306,806 bytes. It unpacked to 87 files and 6.4 MB with no
refusals and no symlinks. TLS verification is httpx's default (certifi). Nothing needs a redirect
today, so following them only widens who can supply the bytes that F1 turns into a whole-cycle
crash.

**Remedy.** Pass `follow_redirects=False` for the bundle, or check that `response.url` is
`https://epoch.ai/...` before reading the body.

### F6 NIT: error normalisation in `unpack`

- The budget refusal raised inside `_write`'s `try` is `SourceError`, which subclasses
  `RuntimeError`, so the `except (..., RuntimeError, ...)` re-wraps it. The log then reads
  "member 'z' is unreadable: epoch bundle: the bundle expands past 268435456 bytes", which
  describes a zip bomb as a corrupt member.
- Name collisions reach the caller as bare `OSError`, not `SourceError`: `FileExistsError` or
  `IsADirectoryError` for a file and a directory with the same name, for the member `.`, and for
  `a/` followed by `a`; `ENAMETOOLONG` for a component over 255 bytes or a 5,000-character path.
  `refresh` catches `OSError`, so each of these carries correctly (measured). But
  `fetch_bundle`'s callers are told to expect `SourceError`.

**Remedy.** Re-raise `SourceError` unchanged before the generic wrap. Folding `OSError` from name
handling into `SourceError` inside `unpack` falls out of F1's remedy.

## What holds (measured, not assumed)

- **Path traversal.** These were refused before any write: `../`, `a//../../x`, `//etc/x`,
  absolute paths, `..\\`, `C:x`, `C:/`. NUL in a name is truncated by `zipfile`, so
  `a.csv\x00/../../x` becomes `a.csv`. Unicode look-alikes (`..／x.csv`, `․․/x.csv`) and
  trailing dots or spaces (`.. /x.csv`, `... `) are ordinary names that stay inside the directory.
  Case collisions and duplicate names overwrite inside the directory (last writer wins). That is not
  an escape, and the upstream already controls content.
- **Links.** `S_IFLNK` members are refused. Extraction uses `open("wb")`, so no link can be created
  from the archive in any case. Zip has no hard-link member type, and Python writes regular files.
  A link pre-planted in the destination is refused by the resolved-path check, and the scratch is a
  fresh `0700` `mkdtemp` in a directory that `environment_problems` already requires to be not
  group- or world-writable.
- **Refusals carry and never touch the artifact.** Six cases went through the real `refresh()`:
  traversal, not-a-zip, file-then-dir `OSError`, an empty valid zip, a GPQA CSV with a wrong header,
  and a GPQA CSV with a 200,000-byte field. All returned exit 1 ("nothing a user would notice
  changed"), with the live digest unchanged, the scratch at `0700` beside the artifact, and no
  scratch left afterwards. `epoch_board.parse_board` and `epoch._csv_entries` both turn `csv.Error`
  into `SourceError`.
- **Concurrency.** The fetch runs inside `_cycle`, and so under the `flock`. A busy trigger fetches
  nothing. Each cycle's scratch is uniquely named.
- **Network off by default in tests.** `refresh(fetch_epoch=None)` is the default. The CLI test
  patches `refresh`. The flag is resolved at call time.
- **Hygiene.** There are no new third-party imports (`zipfile`, `zlib`, `stat`, `io`, `shutil` are
  stdlib) and no secrets or `.env` in the diff. `ruff --select S` over the four source files reports
  only the pre-existing `S101` at `nightly.py:252`, outside the diff. The network call lives in
  `clients/` (permission-matrix §3).

## What I did not check

- Windows path semantics. The code rejects `\` and a drive colon in the first component, but I ran
  only on macOS APFS (case-insensitive).
- Manipulation of CSV *values* by a hostile but well-formed bundle. The upstream is authoritative
  for its numbers. The D-128 degradation and upward-anomaly guards are pre-existing and were not
  re-derived here.
- `trust_env`: httpx honours `HTTPS_PROXY`, `SSL_CERT_FILE` and similar from the engine's
  environment. That environment is owner-controlled and outside this slice.
- Memory while parsing a board CSV near the 256 MB unpack budget (`read_text` of the whole file).
  It is bounded by the budget. I did not measure it.
- The commits after `f2ffaee` on this branch. In particular, `420a216` writes `drift` lines,
  which can contain upstream column names, into the status record. `nightly._drifted` exposes only
  the source-name prefix. I did not review that surface.
- `gitleaks` and `pip-audit`. Those are Stage 2 gates. I confirmed only that the diff adds no
  dependency. Bandit and semgrep are not installed. My SAST was ruff's `S` rules only.
- The milestone-wide combined surface, which belongs to the Stage 4.0 closure seat.
