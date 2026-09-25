---
record_type: review
id: m17-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# M17-W2 Code Review, final: Arena's category slices become boards (fix rounds effdb04..cf141ae, whole wave 04e2630..cf141ae)

**Reviewer:** Code-Reviewer seat, new and fresh-eyed. I wrote none of this wave's code, none of its
fix rounds, and none of the earlier reviews or the Tester's verdict.
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** in full depth, `effdb04..cf141ae`:
- `156d2f4`: the red tests;
- `a73c079`: the fix;
- `8a6a260`: the mypy fix;
- `186ba17`: the Tester's file;
- `cf141ae`: the Tester's T1 and T2.

At a lighter depth, the whole wave `04e2630..cf141ae`.
**Risk tier:** MEDIUM (`docs/plans/m17-wave-2-plan.md:11`)

**Supersedes as the verdict of record:** the round-1 BLOCKING verdict that stood at this path
(commit `b4e41f2`), and the later rounds `m17-wave-2-rereview.md`, `m17-wave-2-rereview-2.md` and
`m17-wave-2-rereview-3.md`. The owner ruled in session (2026-09-25) that a fresh, independent final
review of HEAD is written here. It is not a copy of an earlier verdict. The earlier files stay in
the tree and in git history as the record of their rounds.

**What I read first.**
- The policy: `.claude/agents/Code-Reviewer.md`, `.agents/rules/practices.md`,
  `.agents/rules/review-seats.md`, `permission-matrix.md` §11 and `.claude/skills/close-wave/SKILL.md`
  step 3.
- The plan, and D-164 and D-165 (`docs/decisions.md:2983-3045`).
- The findings this range claims to fix:
  - `m17-wave-2-rereview-3.md`: MINOR-R3-1..4 and NIT-R3-1..2;
  - `m17-wave-2-security-rereview-3.md`: S-R3-1..5;
  - `m17-wave-2-tester.md`: T1 and T2.

`git diff --stat 04e2630..HEAD -- .claude .agents AGENTS.md permission-matrix.md subagent-profiles`
is empty, so the policy I read is the base's. Nothing in the diff addresses a reviewer.

**Families.** The commits carry `GP-Agent: claude-code/local-lane`. This seat is also Claude. At
MEDIUM tier the cross-model rule is advisory only. My context was fresh.

**How I worked.**
- **Mutants.** I ran 20 mutants in place from `scratchpad/cr4/mutate.py`. For each one, the script
  saved the file's bytes, applied the mutant, ran the tests, wrote the bytes back and compared
  SHA-256. I ran two more by hand the same way. **All 22 came back byte-identical.** I used no
  `git checkout` or `git restore`, and `git status` is clean apart from this file.
- **Network.** Every pytest run and probe of mine loaded `scratchpad/cr4/netblock_cr4.py`, which
  refuses and logs every non-loopback connect and every non-local DNS lookup. The log was never
  created: **0 outbound attempts**. `RUN_CONTRACT_TESTS` was never set.
- **No crash signal.** I raised none, and nothing called `os.abort()`.
- **Red replay.** I replayed `156d2f4` from a `git archive` in my scratchpad.

## Verdict

PASS-WITH-MINORS: 0 BLOCKING, 3 MINOR, 0 K.9, 1 risk queued, 3 NIT.

**Every fix this range claims is in the code.** Each claimed fix has a test that fails without it
(22 mutants, table below), with two exceptions:
- a changed constant (the 8 MiB cap);
- a resource-hygiene change (`with reader:`).

The red commit fails exactly the five tests its message says it should. **The branch is green:**
- CI on `cf141ae` passes every check. `test (py3.12)` has 1270 passed and 66 skipped; the skip
  budget reports `66 skipped of 1336 (budget 66)`.
- `live-contracts` passed 19, including both
  `test_every_declared_slice_satisfies_the_parser_contract` cases.
- Locally: `make check-fast` PASS, 6 of 6 legs. The full suite gave 1319 passed and 17 skipped,
  twice, under the network block.

**What remains is small.** None of it reopens a bound.
- The new per-slice row ceiling is checked by the build but not by the two other readers that
  check the floor (M1).
- One part of an earlier remedy is still not done: a positive control for the ceiling test (M2).
- D-165 still states the old 16 MiB answer cap (M3).

## Disposition of the fix rounds' findings

| Finding | Claimed fix | Verified? | Evidence (every mutant run in place, restored byte-identical) |
|---|---|---|---|
| MINOR-R3-1 (answer bound untested) + Tester T1 | `test_arena_slices.py:269-285`: an endless reader, with an elapsed-time assertion `< 4.0` s against an 8 s limit | **yes** | Mutant A: `read(MAX_ANSWER_BYTES + 1)` → `read()` (`arena_slices.py:259`) fails `:269` in 9.7 s. This is the mutant the Tester's F13 showed staying green before `cf141ae` |
| MINOR-R3-1 (stderr tail untested) | `:288`: 1 MB of stderr, then ESC and `TAILMARK`, exit 7 | **yes** | Mutant B: `stderr.seek(0)`, reading all of it, fails `:288`. Mutant C: `printable` removed from the tail (`:272`) fails `:288` |
| MINOR-R3-2 / S-R3-2 (U+2028/U+2029/U+0085) | split the bytes on `b"\n"`, then decode each line (`arena_slices.py:294`) | **yes** | Mutant D (the old `decode().splitlines()`) fails `:300`. At `156d2f4`, `:300` is red |
| MINOR-R3-3 (a) / S-R3-3 (the watchdog fails open) | `_watch` wraps the loop, and any exception ends the reader with `EXIT_OVER_CEILING` (`parquet_reader.py:69-77`) | **yes** | Mutant E (the old loop with no `try`) fails `:330[failure0]`. The test covers `OSError`, `ValueError`, `LookupError` and `MemoryError` |
| MINOR-R3-3 (b) (Linux fallback in KiB) | no `VmHWM` line raises `LookupError` (`parquet_reader.py:62-65`) | **yes** | Mutant F (the `ru_maxrss` fallback) fails `:353` |
| MINOR-R3-3 (c) (no positive control for the ceiling test) | not claimed | **no, still open (M2)** | Mutant Q adds 150 MiB to the reader's measured peak. It **survives the whole unit suite** (1310 passed, `-n auto`) |
| MINOR-R3-4 (a) (contract marker unpinned) | `:367` asserts the marker on the live test | **yes** | Mutant P (marker removed at `test_arena_openrouter_contract.py:52`) fails `:367` |
| MINOR-R3-4 (b) (start `OSError` untested) | `:309`: a missing executable | **yes** | Mutant G (`except OSError` → `ValueError` at `arena_slices.py:243`) fails `:309`. CI coverage no longer lists `231-233` |
| MINOR-R3-4 (c) (`:438` matched `"bytes"`) | `:547` matches `the file declares .* bytes, over 10` | **yes** | Mutant H (footer bytes check off, `parquet_reader.py:87`) fails `:540` |
| NIT-R3-1 (stale marker sentences) | `tests/conftest.py:44, 59-61` rewritten | **yes** | Both sentences now name the respx unit tests and the env-gated live test |
| NIT-R3-2 (`reader.stdout` never closed) | `with reader:` (`arena_slices.py:253`) | **yes, for the parent** | Under `-W default::ResourceWarning`, `test_arena_slices.py` gives 1 warning, where re-review 3 counted 11. The one left is the orphan test's own stdin, which re-review 3 also named (NIT-1). Mutant L (`with` removed) survives, as a hygiene change is expected to |
| S-R3-1 (16 MiB costs the parent 190-245 MiB) | cap 8 MiB (`arena_slices.py:73`), plus the bytes split (no whole decoded str) | **yes in code** | The bytes split is pinned by `:300` (mutant D). Mutant K (cap back to 16 MiB) survives, since no test pins a constant, which is acceptable. D-165 still says 16 MiB (M3) |
| S-R3-4 (TemporaryFile outside the guard) | in its own `try`, `OSError` → `SourceError` (`arena_slices.py:233-237`) | **yes** | Mutant I (`except ValueError`) fails `:317`. At `156d2f4`, `:317` is red |
| S-R3-5 (no row ceiling per slice) | `ArenaSlice.maximum_rows = 4 × measured` (`arena_slices.py:136-140`); build refusal (`build.py:465-468`) | **yes, in the build** | Mutant J (check off) and mutant O (400× instead of 4×) both fail `test_build_slices.py:98`. The smoke probe and the live contract test do not apply it (M1) |
| Tester T2 (smoke probe untested) | `:669` drives `_slice_probe("vision")` with the canonical fake: a full file, then one slice one row short | **yes** | Mutant N (the probe's floor check off, `smoke_deps.py:87`) fails `:669` |
| `8a6a260` (mypy on Linux) | `platform: str = sys.platform` (`parquet_reader.py:57`) | **yes** | Reverted in place: `mypy --platform linux src` gives `parquet_reader.py:65: error: Statement is unreachable`, and `--platform darwin` passes. At HEAD both pass |

**Red to green.** At `156d2f4`, `test_arena_slices.py` and `test_build_slices.py` give 5 failed and
71 passed. The five that fail:
- the Unicode separator;
- the missing tempdir;
- the fail-closed watchdog;
- Linux without `VmHWM`;
- the slice ceiling.

The MINOR-R3-1 and -4 tests are green there. The commit says so ("untested, not wrong"), and
mutants A, B, C, G, H and P show that each of them can fail.

**The new `with reader:` exit path.** `Popen.__exit__` closes stdin again and may re-raise a flush
error, which is a new way for a non-`SourceError` to leave `_read_table`. I probed it
(`scratchpad/cr4/pipeprobe.py`) with five stub readers:
- exit 0 or exit 1 without reading;
- read 10 bytes, then exit;
- read 9,000 bytes, then answer;
- close fd 0, then answer.

Each ran against ten input sizes, from 1 byte to 8 MB, across the 8,192-byte buffer edge, three
times each: 150 runs in all. **All 150 ended in rows or a `SourceError`. Nothing escaped.**

## Findings

### BLOCKING (must fix before this wave closes)

- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/build.py:461-468`, `scripts/smoke_deps.py:86`,
  `tests/integration/test_arena_openrouter_contract.py:63`. **The per-slice bounds live in three
  places, and the new ceiling reached one of them.** The build now refuses a slice above
  `maximum_rows` (S-R3-5). The owner's deploy gate (`smoke_deps._slice_probe`) and CI's live
  contract test still check only `minimum_rows`. So on a night when a slice grows past four times
  its declared count, both say "usable" while the nightly build refuses that board. That is the
  "configured is not working" gap the smoke gate exists to close, and it is the
  one-fact-in-several-places drift (`.agents/rules/practices.md`, K.5). It is unlikely soon (4× is
  a wide margin), which is why this is MINOR. **Fix:** one method on `ArenaSlice` that names what
  is wrong with a count, or returns `None`. The build, the probe and the contract test all call it.
  Extend `test_arena_slices.py:669` with an over-ceiling case.

- **M2** `tests/unit/test_arena_slices.py:439-453`. **MINOR-R3-3's part (c), BLOCKING-R2-1's remedy
  3, is still not done. So the ceiling test cannot tell "decoding took the reader over" from "the
  reader was over before it read a byte".** Mutant Q adds 150 MiB to the reader's measured peak
  (`parquet_reader.py:66`). That is the shape of the BLOCKING-R2-1 regression: a reader over its
  ceiling at birth. It survives `tests/unit` (1310 passed), because every other parse runs at the
  512 MiB ceiling. Since `a73c079`, `_watch` also turns any failure to measure into
  `EXIT_OVER_CEILING`, so this one test now passes for a third wrong reason too. **Fix, verified
  from `scratchpad/cr4/posctl.py`:** under the same `MAX_READER_RSS = 100 MiB` and the same patched
  footer bound, a two-row `slice_parquet` file parses at HEAD, and fails with "memory ceiling"
  under mutant Q. Add it next to `:439`.

- **M3** `docs/decisions.md:3036`; `src/app/clients/arena_slices.py:73, 136-140`. **D-165 clause 4
  still says `MAX_ANSWER_BYTES` (16 MiB). The code is 8 MiB since `a73c079`.** The clause's
  opening, "Nothing the reader says is held whole by the parent", overstates it: the answer, up to
  the cap, is held whole as bytes. S-R3-1 made the same point. The new per-slice row ceiling (four
  times the measured count) is written only in code and tests; the plan's decision 4 names the
  floor alone. Clause 4 was itself added in place while the ADR is not yet on main, so correcting
  its number before merge follows the same path. After merge it needs a superseding note.

### NIT

- **NIT-1** `tests/unit/test_arena_slices.py:419`. The orphan test leaves its own `stdin` pipe open.
  This is the second half of NIT-R3-2, and it is the one `ResourceWarning` left in the file. Fix:
  `reader.stdin.close()` in its `finally`.
- **NIT-2** `src/app/clients/parquet_reader.py:75-77`, `src/app/clients/arena_slices.py:277-280`.
  The fail-closed watchdog reports an unmeasurable peak the same way as a real one: "passed its
  memory ceiling … the file has changed shape". On a host without a readable `/proc`, every night's
  slices would fail, and the reason would send the operator to the file. S-R3-3 offered a distinct
  exit code for this. Fails closed, loud and carried, so a NIT.
- **NIT-3** `tests/unit/test_arena_slices.py:285`. The T1 assertion is wall-clock (`< 4.0` s against
  an 8 s limit). The stub reader imports nothing, and the test ran green in both `-n auto` runs and
  on CI, so the margin is ample. It is the one timing assertion this range adds.

## Acceptance criteria evidence

The plan names no REQ-IDs. Its criteria are the red-first bullets of §Phases, plus D-164 and D-165.

| Criterion | Evidence (test file:line) |
|---|---|
| P1: each declared slice gets its rows from a parquet file | `tests/unit/test_arena_slices.py:60` |
| P1: newest date per slice | `:80`, `:489`, `:501` |
| P1: over the cap, not parquet, missing column, `Infinity` rating | `:575`, `:515`, `:521`, `:102` |
| P1: the server does not import `pyarrow` (D-154 extended) | `:658-659` |
| P2: no slice row reaches `assistant` or `vision` | `tests/unit/test_build_slices.py:56` (benchmarks disjoint from every surface's) |
| P2: one slice under its floor fails alone; a failed download fails its config only | `test_build_slices.py:80`, `:116`, `:128` |
| P2: distinct benchmark labels; `floor < measured` | `test_arena_slices.py:630`, `:642` |
| P3 (D-164.1): a board-only change publishes; the fingerprint moves with a board only | `tests/unit/test_refresh_boards.py:68`, `:79`. Mutant D164-1 (board rows left out of the digest, `refresh.py:473`) fails `:68` |
| P3 (D-164.2): a quarter lost / a quarter new is refused | `test_refresh_boards.py:114`, `:126`. Mutants D164-2 (`refresh.py:221`, `:277`) fail each |
| P3 (D-164.3): a board seen first publishes | `test_refresh_boards.py:101` |
| P4: the survey measures slices; the record | `tests/unit/test_survey_floors.py:121`; `docs/research/m17-w2-slice-survey-2026-09-24.md` |
| P4: `smoke_deps` has one probe per config | `test_arena_slices.py:669` (T2) |
| P4: the `agent_*` issue | #24 (open, `enhancement`, `out-of-scope`) |
| D-165.1-2: a child process, a ceiling, a time limit; every failure a `SourceError` | `test_arena_slices.py:252`, `:429`, `:439`, `:309`, `:317`; `test_build_slices.py:193` |
| D-165.4: bounded answer, stderr tail only, short printable reason, allowlisted env, `-P`, own alarm | `test_arena_slices.py:259`, `:269`, `:288`, `:378`, `:389`, `:399`, `:410` |
| This range: Unicode separators; fail-closed watchdog; no `VmHWM`; contract marker; slice ceiling | `test_arena_slices.py:300`, `:330`, `:353`, `:367`; `test_build_slices.py:98` |

**Producers of the hardened invariant** ("only `SourceError` leaves the slice read"). This is not
required at MEDIUM tier, and is given for the seam D-165 clause 2 names.

| Producer | Where | Citing test |
|---|---|---|
| tempfile creation | `arena_slices.py:233-237` | `:317` |
| process start | `:239-245` | `:309` |
| answer bound | `:259-264` | `:259`, `:269` |
| timeout | `:274-276` | `:429` |
| ceiling exit | `:277-280` | `:439` |
| non-zero exit | `:281-283` | `:252`, `:288` |
| protocol violations | `:293-311` | `:252`, `:300` |
| the stdin close on `Popen.__exit__` | `:253` | none in the suite; probed (150 runs, 0 escapes, above) |

Gaps: the last row. It is untestable without a race, and the probe shows it holds.

## K.8 contract drift check

```
$ grep -rn "fetch_slices(\|def parse_arena_slices\|ARENA_SLICE_CLIENT\b\|maximum_rows\|MAX_ANSWER_BYTES\|from app.clients.parquet_reader import" src scripts tests/integration
src/app/clients/arena_slices.py:40:from app.clients.parquet_reader import EXIT_OVER_CEILING, printable
src/app/clients/arena_slices.py:73:MAX_ANSWER_BYTES = 8 * 1024 * 1024
src/app/clients/arena_slices.py:137:    def maximum_rows(self) -> int:
src/app/clients/arena_slices.py:212:def fetch_slices(
src/app/clients/arena_slices.py:259:                answer = reader.stdout.read(MAX_ANSWER_BYTES + 1)
src/app/clients/arena_slices.py:326:def parse_arena_slices(
src/app/workflows/build.py:69:    ARENA_SLICE_CLIENT,
src/app/workflows/build.py:447:    client_type = ARENA_SLICE_CLIENT if client is None else client
src/app/workflows/build.py:453:            rows, refused = fetch_slices(config, boards, client=client_type)
src/app/workflows/build.py:465:                if len(parsed) > board.maximum_rows:
src/app/workflows/sources.py:248:ARENA_SLICE_CLIENT = ArenaSliceClient
scripts/smoke_deps.py:85:        rows, _ = fetch_slices(config, boards)
scripts/survey_boards.py:375:            rows, _ = fetch_slices(config, boards, client=client)
tests/integration/test_arena_openrouter_contract.py:60:    rows, refused = fetch_slices(config, boards)
```

- The signatures of `fetch_slices` and `parse_arena_slices` are unchanged in this range.
- `maximum_rows` is new, public on `ArenaSlice`, and read by the build only (M1).
- `arena_slices` still imports only two stdlib-only names from the reader. The
  server-never-loads-pyarrow test passes.

**Verdict: OK, nothing drifted.** M1 is a missing use of the new name, not a broken contract.

## Whole wave, 04e2630..cf141ae (lighter depth)

- **Plan compliance.**
  - §Scope "In" is delivered: `pyarrow>=21.0` (`pyproject.toml:19`), the client and parse, the
    35-row table (`arena_slices.py:151-191`, pinned by `test_arena_slices.py:609`), the ingest and
    per-slice carry, derived attribution, D-164, the survey record and the smoke probe.
  - §Scope "Out" holds: no surface, `/v1` or app file is touched.
  - The row ceiling is a scope addition answering a security finding (S-R3-5). It is in the spirit
    of plan decision 7 ("a `SourceError` or a counted skip"), but it is recorded nowhere but code
    (M3).
- **Boundaries.**
  - `clients/` holds the read.
  - `workflows/` holds the ingest and the guards.
  - `scripts/` reach the one `fetch_slices` path.
- **Drive-bys.** None found. `note.txt`, `docs/prd.md` and `docs/skip-budget.txt` are
  resume-state, PRD and budget upkeep for this wave.
- **Swallowed exceptions.**
  - `_watch`'s `except BaseException: pass` is followed unconditionally by `os._exit`, so it
    converts rather than swallows (NIT-2 is about the message).
  - `contextlib.suppress(BrokenPipeError)` around the stdin write is safe, per the probe above.
- **Dependencies.** No new import in this range. `pyarrow` was declared in the wave's P1.
- **Suppressions.** `# noqa: SIM115` (`arena_slices.py:234`) is justified in its own comment: the
  file is entered by the `with` on the next line. `# noqa: S110` (`parquet_reader.py:75`) is by
  design.
- **Open items from earlier rounds, already dispositioned elsewhere:** #24 (`agent_*`), #25
  (`fetch_bounded_bytes`), #26 (pyarrow off the serving image), #27 (page decoded at declared size,
  bounded by D-165). Not re-litigated.
- **The ledger.** `docs/control-events.csv`'s last row is the owner's waiver of the three-attempts
  stop for one more fix of the parquet memory bound. This range is that fix's follow-up of minors,
  not a fourth attempt at a BLOCKING finding.

## K.9 candidates spotted outside this wave's scope

- none

## Risks queued to next M

- **R1** `src/app/clients/parquet_reader.py:162-165` (`_guard`). **The security re-look's two NITs,
  S-R3-N1 and S-R3-N2, have no disposition in any record I found.** S-R3-N1: the reader's own
  alarm is void when its parent ignores or blocks SIGALRM. S-R3-N2: stderr to a file bounds memory,
  not disk, and a process holding the reader's stdout outlives the parent's timer. Neither is
  reachable from a file today: nothing in `src/` touches SIGALRM, and the reader starts no process.
  **What would show the risk is real:** a signal handler or mask added to the nightly or refresh
  process, or a reader that starts a helper process. Then orphaned readers would outlive a killed
  refresh. Cheap hardening: `signal.signal(SIGALRM, SIG_DFL)` plus `pthread_sigmask(SIG_UNBLOCK,
  …)` in `_guard`, and `start_new_session=True` with `os.killpg` in `stop()`.

## Gates

- `make check-fast` at `cf141ae` (macOS): **PASS, 6 of 6 legs** (72.7 s).
- Full suite, `-n auto`, under the socket and DNS block, run twice: **1319 passed, 17 skipped, 0
  outbound attempts**.
- `mypy --platform linux src` and `mypy --platform darwin src`: both clean.
- CI on `cf141ae` (`gh pr checks 23`): every check passes:
  - `test (py3.12)` and `test (py3.14)`;
  - `live-contracts`, with both slice cases PASSED;
  - `dep-audit`, `secret-scan`, `install-and-governance`, `governance-contract` and
    `plan-staleness`.

  PR #23 is a draft, and its head is `cf141ae`.
- Commit trailers `04e2630..HEAD`: no `Co-Authored-By` and no "Generated with".

## What I did not check

- **Linux locally.** The Linux claims rest on CI's green run on `cf141ae` (the coverage report shows
  the `/proc` path ran) and on the mypy platform check.
- **The live download.** No test or probe of mine reached the network.
- **Memory figures.** I did not re-measure the parent's peak. S-R3-1's cap and bytes-split fix is
  verified as code and by mutant D, not by a new memory measurement.
- **Test adequacy beyond the mutants listed.** That is the Tester's seat.
