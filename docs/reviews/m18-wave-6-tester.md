---
record_type: review
id: m18-wave-6-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 6 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `8a18324..4f6d025` (10 commits, 43 files, +5467 / -247). `8a18324` is the M18-W3
head; the branch is stacked on it. The code review read `8a18324..cf83fea`. Two commits came after
its head: `cd67cc8` (the licence table, #88) and `4f6d025` (its fix round, M1 and M3 to M8). This
seat is the first to test them.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:124`, `docs/plans/m18-wave-6-plan.md:14`). The diff
touches two security globs: `src/app/clients/**` and `scripts/*engine_service*.sh`. By D-172 no
security seat runs on the wave.
**Code-Reviewer verdict:** MINOR, M1 to M8 (`docs/reviews/m18-wave-6-review.md`). Not BLOCKING, so
this seat runs.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: I started from `.claude/agents/Tester.md` and `.agents/rules/practices.md`, then
  read both plans, the ADRs (D-154 as amended, D-177, D-116, D-156, D-165, D-170, D-171), the code
  review and the diff. I have no memory of any authoring or reviewing session.

**Base-pinned policy:** `git diff --stat 8a18324 4f6d025 -- .claude .agents permission-matrix.md
.github` is empty. So the profile and the rules I used are the base's. No commit in the range carries
`Co-Authored-By` or "Generated with".

## Verdict
MINOR

**Nothing blocks.** Every acceptance check in the wave plan has a citing test that passes, or a
record where the check is a record (P4). The suite is green. No touched module lost coverage. No
test was weakened, skipped or deleted in the range.

**Fault injection: 53 of 73 faults killed (72.6%).** All 73 restored byte-identically. The 20 that
stayed green are T1. I wrote a test for each one. Each new test passes on `4f6d025` and fails on its
fault (23 of 23 checks). With them, 73 of 73 die. The tests are uncommitted in this worktree and in
`docs/reviews/m18-wave-6-tester.patch`.

**The ten sampled rows of the invariants list: 10 of 10 killed** by a test the row cites.

**Six MINORs (T1 to T6), one K.9 (K1), three risks (R1 to R3).** T1 is closed by the patch once the
author applies it. T2 to T4 are seven probes that a gate passes: the gates fail open on spellings
they do not read. T5 must be fixed before the stranger protocol is used with a real person.

## Acceptance-criterion coverage

W6 has no REQ-ID. Its checks are the wave plan's phase table (`docs/plans/m18-wave-6-plan.md:50-57`).
The new tests cite their W-, D- and issue ids in docstrings and comments.

- **P1, #89: the list holds every M16 and M17 closure row and the M18 waves.** →
  `docs/security-invariants.md`. I read the list against both closure tables. Every M16 row (1 to
  25) and every M17 row (1 to 29) is folded in: most by number, two by the finding or issue they
  came from (M16 row 17 as "M16 MINOR-2" in INV-23; M17 row 25 as "#36" in INV-29), and the
  superseded ones under "Retired ids". — RECORD, MET.
- **P1: each row cites the negative test that fails without it.** →
  `tests/unit/test_security_invariants.py:147` (`test_the_list_holds_together`) holds that each cited
  test exists. That a cited test fails is the mutation samples' job: the author's 11, the
  review's 20 and my 10 rows (below), all killed. — GREEN.
- **P1: a gate refuses a row whose test does not exist.** → `test_security_invariants.py:175`. —
  GREEN. Gaps in the gate's reach: T2.
- **P1: a gate refuses a test that names an invariant no row lists.** → `:151` (the real tree) and
  `:201` (planted). — GREEN.
- **P1: a sample of rows is mutated, each killed by its row's test.** → "Mutation samples" in the
  list, the review's table, and my ten below. — MET.
- **P2, W-125: the server imports no client and no ingest module, held by the import test extended
  to them (red first).** → `tests/unit/test_nightly_refresh.py:442`, with
  `tests/unit/test_arena_slices.py:683`. No separate red commit exists. I reproduced red with five
  imports put back (E1 to E5b below): each fails the test. — GREEN.
- **P2, W-126: a wall-clock limit inside `refresh.main` (red first).** →
  `tests/unit/test_refresh.py:1872` (a sleep and a held GIL), `:1893` (a dead engine), `:1933` (the
  budget is set); `tests/unit/test_fetch_bounds.py:199`, `:211` (the budget refuses and cuts);
  `test_nightly_refresh.py:237`, `:284`. Red reproduced by B1, B2, C1, A1 to A5. — GREEN. Holes in
  the pins, now closed: T1.
- **P2, W-130: the cycle runs in its own group, and the timeout kills the whole group (red
  first).** → `test_nightly_refresh.py:203`, `:248`. Red reproduced by D1 (no new session: the
  drain waited about 30 s). — GREEN. The cancel path was unpinned: T1.
- **P3, #26: pyarrow moves to an `ingest` extra.** → `pyproject.toml:31-33`;
  `tests/unit/test_dependency_locks.py:106`. Red by F3. — GREEN.
- **P3, #35: hashed locks from `pyproject.toml`; `make install` and the release venv install from
  them.** → `test_dependency_locks.py:87`, `:96`, `:153`. This seat's venv was built by `make install`
  from the locks. — GREEN. Spellings the check does not read: T3.
- **P3: a gate fails when a lock is stale.** → `test_dependency_locks.py:63`, `:67`. Red by F1. The
  `stale` function itself was never watched failing (F2): T1, now `:168`. — GREEN.
- **P3: the Dockerfile installs the serving lock.** → `test_dependency_locks.py:153`
  (`Dockerfile` case). Red by F6. — GREEN. No image built, by this seat's rules.
- **P3: the CI change is the owner's, proposed as a diff.** → D-177 clause 5 puts the diff in the
  wave's pull request. It is not in the range yet. — OPEN UNTIL THE PR. `/close-wave` should check
  it is in the PR body.
- **P4, #88: a licence table for every served source, with options and their cost; the owner
  rules; an ADR follows.** → `docs/research/data-licences-2026-10-04.md`. I checked that all 63
  sources in `rank.SOURCE_ATTRIBUTION` fall in a table row (22 by name, 41 Arena slices by the
  row's `arena_text_*`, `arena_vision_*` and `arena_agent*` counts, which match). The counts line
  matches the table. §B holds the options and costs; §C the questions. The ruling and its ADR are
  the owner's. — RECORD, MET IN FORM. This closes the review's M2.
- **P4, #91: a protocol for a stranger's first use, with consent and nothing leaving the device
  unasked.** → `docs/research/stranger-first-use-protocol.md`. Consent and `--no-lan` are now in
  §3 and §5 (the review's M3). §7 still attaches the notes to a public issue: T5. — RECORD, MET
  WITH T5.
- **P5: moved to M19 by the valve.** → `docs/plans/m18-plan.md:220-223`; wave plan `:59-65`; gaps
  G-1 to G-3 name #85, #60, #107 and #110 (`docs/security-invariants.md:169-171`). — MET BY THE
  VALVE.

## Red→green on reported symptoms

There are no separate red commits in the range. So I removed each fix in place and watched its test
fail, then restored the file and watched it pass:
- **W-130**, the kill waiting on a grandchild: no `start_new_session` (D1). Both group tests fail,
  and the run took 58.9 s against about 25 s green. Green after restore.
- **W-125**, the server loading clients: an import of `access`, `httpx`, `pyarrow` or a client put
  back (E1, E2, E3, E4b, E5b). `test_nightly_refresh.py:442` fails each time.
- **W-126**, no limit inside the cycle: no itimer (B1), or SIGALRM handled in Python (B2, the
  review's M1(1) class: the held-GIL case fails). `test_refresh.py:1872` fails.
- **The review's M1(3)**, a dead engine's cycle running on: the watch never fires (C1), or the
  engine's pid ignored (C2). `test_refresh.py:1893` fails.
- **The review's M1(4)**, the group kill skipped when the cycle had exited: D2 and D4.
  `test_nightly_refresh.py:248` fails.
- **The review's M4(1)**, INV-38's group half: `S_IWOTH` alone. `test_refresh.py:1653` fails.
- **The review's M5**: unreadable rows ignored (G1), no `rstrip` (G2), unread citations ignored
  (G3). `test_security_invariants.py:209` fails each time.
- **The review's M6(2)**: the by-name import branch removed (H10). `test_security_surface.py:150`
  fails. M6(1) was pinned only together with another pattern: T1.
- **The review's M7(2)**: the install check's pattern put back to its `cf83fea` form.
  `test_dependency_locks.py:163` fails on two of its four spellings.

## Suite result

- **`make test` at `4f6d025`:** 1709 passed, 25 skipped, rc 0. Coverage 91.80%. `coverage-floor`
  PASS, 45 modules. Evidence: `=============== 1709 passed, 25 skipped, 370 warnings in 42.12s`.
- **`make test` with this seat's tests:** 1721 passed, 25 skipped, rc 0. Coverage 91.80%. The four
  new tests that start processes or set signals ran three more times on their own, with 4
  workers: green each time.
- **Other gates at `4f6d025`,** each with its output in a file and its exit code read: `make lint`
  rc 0 (with my tests too), `make typecheck` rc 0 (45 files), `make check-records` rc 0,
  `check-records-selftest` rc 0, `install-check` rc 0, `shell-dialect` rc 0, `wave-check-all` rc 0,
  `conformance` rc 0 (16 tests), `lock_dependencies.py --check` rc 0 (4 locks current).
- **Not run:** `swift test` and `client-decls` (W6 changes no Swift file; the simulator is not this
  seat's), `make lock` (network), any installer by hand, any Docker build.
- **Coverage on touched code** (from this run's `coverage.json`; the review measured 91.81% total
  at `cf83fea`): `protocols.py` 100%, `run_records.py` 100%, `board_tables.py` 100%,
  `access_served.py` 100%, `access.py` 100%, `standings.py` 100%, `nightly.py` 99.6%, `registry.py`
  98.8%, `arena_slices.py` 98.5%, `rank.py` 97.5%, `ingest.py` 97.6%, `refresh.py` 95.4%,
  `plans.py` 92.7%, `arena.py` 92.3%, `swebench.py` 90.3%, `epoch.py` 87.0%. The lines left in
  `refresh.py`'s new code are the watch's `os.kill` (`:125-126`), which runs only in a child
  process, where coverage is not collected. No drop.

## Mocks / contract tests

- **No new external integration.** The budget is in `bounded_get`, which every client already
  uses. The tests drive the canonical fakes: `respx` and the `loopback_http` server in
  `test_fetch_bounds.py`. The existing contract tests (`tests/integration/`) are skipped without the
  network, as before.
- **The child processes** are real interpreters, started the way the engine starts them
  (`nightly._child`), not stubs.

## Fault injection

Each fault replaced one exact string once, in place. The named tests then ran in a fresh pytest
process in its own session, with `PYTHONDONTWRITEBYTECODE=1`. Then the file was written back from
its byte copy, with its old mtime, and its sha256 compared. All 118 runs (faults, probes, the
row sample, the checks of my own tests) restored byte-identically. `git diff --quiet` was clean
after every batch. Any run past its time limit would have been ended by SIGKILL to its group; none
needed it.

**Kill rate: 53 of 73 (72.6%).** With this seat's tests: 73 of 73.

| group | faults | killed | stayed green (T1) |
|---|---|---|---|
| A, the fetch budget (`protocols.py:65-93`, `:142`; `refresh.py:1324`) | 6 | 5 | A6: `main` passes 60 times the budget |
| B, the SIGALRM limit (`refresh.py:112-133`, `:1322-1336`) | 7 | 3 | B3 timer left armed; B4 watch left running; B5 SIG_DFL left; B6 `close` never called |
| C, the parent watch (`refresh.py:116-126`; `nightly.py:274`) | 4 | 2 | C3 the engine does not name itself; C4 the poll at ten minutes |
| D, the group kill (`nightly.py:221-224`, `:280`, `:291-323`) | 7 | 6 | D3 no group kill in `finally` (the cancel path) |
| E, the server's import refusals | 5 | 5 | — |
| F, the lock staleness and install checks | 7 | 6 | F2 `stale` answers None for every lock |
| G, the invariants gate's own code | 15 | 11 | G6 a row that is retired too; G7 the count; G8 a near-empty list; G13 broken gap and retired rows |
| L, faults in the list the gate must refuse | 5 | 5 | — |
| H, the TLS, CI-permission and model checks | 16 | 9 | H1a to H1e, five TLS patterns each deletable; H4 a job's own scope; H5 `write-all` |
| the review's M4(1), re-checked | 1 | 1 | — |
| **total** | **73** | **53** | **20** |

**What each group broke.**
1. **A:** the budget ignored (A1); no refusal when spent (A2); an open fetch not cut (A3);
   `bounded_get` skips the budget (A4); the budget outlives its block (A5); `main` passes a budget
   60 times too long (A6).
2. **B:** no itimer (B1); SIGALRM handled by Python (B2); `close` leaves the timer (B3), the watch
   (B4) or SIG_DFL (B5); `main` never calls `close` (B6); the limit at 29.5 minutes (B7).
3. **C:** the watch never fires (C1); `MODEL_RANKING_ENGINE_PID` ignored (C2); the engine does not
   set it (C3); the poll at 600 s (C4).
4. **D:** no new session (D1); no group kill on the timeout path (D2) or in `finally` (D3); an
   exited cycle called "killed" (D4); the leader killed, not the group (D5); SIGALRM not "timed out"
   (D6); SIGALRM unnamed (D7).
5. **E:** `standings` imports `access` (E1); `board_tables` imports `httpx` (E2); `run_records`
   imports `pyarrow` (E3); `floors` imports a client (E4b); `access_served` imports the parser
   (E5b).
6. **F:** a dependency added, not re-locked (F1); `stale` never reports (F2); `pyarrow` in
   `serve.lock` (F3); `make install` without `--no-build-isolation` (F4) or without the build lock
   (F5); the Dockerfile's serving lock without `--require-hashes` (F6); the release takes
   `serve.lock` (F7).
7. **G:** each refusal in `problems`, `unreadable`, `parse` and `dangling` removed in turn
   (`test_security_invariants.py:62-144`).
8. **L:** a row with a cell missing; a wrong count; a broken gap row; `INV-99` in `src`; a cited
   test renamed.
9. **H:** each of the six TLS patterns removed in turn (`test_security_surface.py:81-82`);
   `ctx.check_hostname = False` planted in `src`; the job scope, `write-all`, the writers' list and
   the secret check each removed (`:43-55`); a job, then the workflow, given `contents: write` in
   `ci.yml`; the by-name import branch removed; `import torch` planted in a function in `src`;
   `openai` planted in `serve.lock`.

**Left out of the count, with the reason.**
1. **Equivalent:** `registry.py` importing a client (E4). The server does not load `registry`
   (`sys.modules` after `import app.adapter.main`, measured), so nothing can see it. E4b puts the
   same import in `floors.py`, which the server loads.
2. **Invalid:** E5, H11 and H13 failed on an import error (a circular import, and `torch` and
   `google` not installed), not on the check. Each was redone as E5b, H11b and H13b.

**Probes:** seven more edits test a gate's reach, not a fault in the code. Each passed the gate
(T2 to T4): L6, L7, L8, F8, F9, H3 and H13b.

## Ten rows of the invariants list, mutated

None of these rows was in the author's sample (INV-23, -25 to -29, -40, -47, -5, -58, -70) or the
review's (INV-31, -34, -38, -46, -55, -9, -70, -42, -43, -81). Each fault removes the invariant in
place. Only the tests the row cites ran.

| # | row | the fault | result |
|---|---|---|---|
| 1 | INV-30 | `/v1/budgets` also takes POST (`main.py:1364`) | killed: `test_api_v1.py::test_no_mutating_route_exists` |
| 2 | INV-32 | `strict = environment in PRODUCTION_ENVS` (`main.py:534`) | killed: `test_api_config.py::test_an_unrecognised_environment_is_treated_as_strict` |
| 3 | INV-36 | each standing carries its `score` (`standings.py:114`) | killed: `test_board_standings.py::test_the_payload_carries_no_score_at_all`, `::test_the_key_sets_are_frozen` |
| 4 | INV-37 | the thread limiter not set (`main.py:616`) | killed: `test_api_config.py::test_the_concurrency_cap_is_applied_to_the_running_loop` |
| 5 | INV-41 | the tail not cut (`nightly.py:164`) | killed: `test_nightly_refresh.py::test_the_tail_never_holds_more_than_its_limit` |
| 6 | INV-3 | a suffix entry read as a substring (`protocols.py:110`) | killed: `test_fetch_bounds.py::test_a_suffix_entry_is_a_domain_not_a_substring` |
| 7 | INV-48 | the member count 1000 times its limit (`epoch_bundle.py:59`) | killed: `test_epoch_bundle_fetch.py::test_too_many_members_are_refused` |
| 8 | INV-22 | the containment check off (`epoch_board.py:105`) | killed: `test_epoch_board.py::test_a_symlink_escaping_the_bundle_is_refused`, `::test_a_declared_file_that_climbs_out_of_the_bundle_is_refused`, `test_access.py::test_a_metadata_file_that_resolves_outside_the_bundle_is_refused` |
| 9 | INV-52 | the median-price guard 100 times wider (`refresh.py:287`) | killed: `test_refresh.py::test_a_median_price_collapse_is_refused`, `test_refresh_carry.py::test_an_expiry_night_does_not_admit_a_price_jump_either` |
| 10 | INV-60 | an unmatched name not cut (`build.py:416`) | killed: `test_registry_disclosure.py::test_an_unmatched_name_is_bounded_before_it_reaches_health` |

All ten restored byte-identically.

## D-154 as amended, against the code

The amendment is `docs/decisions.md:2431-2445`. Each clause, against `4f6d025`:
1. **"The cycle's downloads share a budget of 20 minutes; past it, the sources left carry."**
   `refresh.FETCH_BUDGET_SECONDS` is 20 minutes (`refresh.py:93`). `main` sets it
   (`refresh.py:1324`). `bounded_get` refuses a new fetch and cuts an open one (`protocols.py:85-93`,
   `:142`). A refused fetch is a `SourceError`, which D-156 carries. — HOLDS. The value `main` passes
   was unpinned (A6): now pinned.
2. **"The cycle ends at 27 minutes. The kernel ends it (SIGALRM, default action)."**
   `_Limits` sets SIG_DFL and `setitimer(ITIMER_REAL, 1620)` (`refresh.py:114-115`). No Python code
   runs at the limit, so no `print` can race the shutdown (the review's M1(2)). — HOLDS.
3. **"The engine reports 'timed out'."** `nightly.CODE_NAMES[-SIGALRM]` and `run_once`
   (`nightly.py:85`, `:309-310`). — HOLDS.
4. **"The engine kills it at 30 minutes, as before."** `nightly.TIMEOUT_SECONDS` (`:75`). The order
   20 < 27 < 30, with room between, is pinned (`test_nightly_refresh.py:284`). — HOLDS.
5. **"The engine starts the cycle in a session of its own and kills the whole group, whether or
   not the cycle itself has exited."** `start_new_session=True` (`nightly.py:280`); `_kill_group`
   before the `exited` check (`:291-297`). — HOLDS on the timeout path. The cancel path's group kill
   (`:323`) was unpinned (D3): now pinned.
6. **"The engine names itself (`MODEL_RANKING_ENGINE_PID`), and a cycle whose engine is gone ends
   itself within seconds, the same way as at its limit."** `nightly.py:274`; `refresh.py:116-126`,
   a 5 s poll, then SIGALRM to itself. — HOLDS. The engine's naming (C3) and "within seconds" (C4)
   were unpinned: now pinned.

One thing the amendment does not say: a cycle ended by SIGALRM runs no `finally`, so its scratch
waits for the next day's sweep (R1).

## The code review's findings, re-checked

Each against the code at `4f6d025`:
- **M1 (the cycle's limit).** (1) The kernel's SIGALRM replaces the timer thread; the held-GIL case
  is a test parameter and is red under B1 and B2. (2) No `print` runs at the limit. (3) The parent
  watch replaces launchd's cleanup; red under C1 and C2. (4) The group is killed whether or not the
  cycle exited; red under D2 and D4. — FIXED, with T1's pins added.
- **M2 (#88 missing).** `cd67cc8` delivers the licence table. — FIXED.
- **M3 (the protocol's consent and network).** Publication is asked for by name in both languages
  (§3, §5). `--no-lan` closes the session (§5). — FIXED, but see T5.
- **M4 (the list's words).** (1) INV-38's group half has a test; the review's survivor now dies.
  (2) INV-3 says "INV-8 merged here". (3) INV-8's retired row says what INV-8 was. (4) "Seven more
  hold only in part": I counted seven. (5) The mutation samples are in the list. — FIXED. One count
  slip remains in the ledger: T6.
- **M5 (the gate fails open).** A row or citation the gate cannot read is now a finding; red under
  G1 to G3. — FIXED for the two probes. Three more spellings pass: T2.
- **M6 (TLS and the model check).** `URLCredential(trust:` and `.useCredential` are refused; the
  model check reads by-name imports and the locks. — FIXED. Five TLS patterns were not pinned one by
  one (T1). Two spellings still pass: T4.
- **M7 (the build backend, spellings, the ADR).** `[build-system]` and `build.lock` exist; every
  install uses `--no-build-isolation`; the check reads `pip3`, `python -m pip` and `uv pip`; D-177
  records it. — FIXED. Two spellings still pass: T3.
- **M8 (the parser the server loads, four stale comments).** `access_served.py` holds the reader;
  the server-import test refuses `app.workflows.access`; red under E1 and E5b. The four texts are
  corrected (`nightly.py:14-19`, `:72-74`; `arena_slices.py:20-22`; `test_arena_slices.py:686-689`).
  — FIXED.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T1** `tests/unit/test_refresh.py`, `test_nightly_refresh.py`, `test_dependency_locks.py`, `test_security_invariants.py`, `test_security_surface.py`. **Twenty faults stayed green. Each now has a test, in the patch.**
  1. **The limits (A6, B3 to B6, C3, C4, D3).** `main` could pass any budget. It could leave its
     27-minute timer armed, its parent watch running or SIG_DFL on SIGALRM. Any test or tool that
     calls `main` in process would then be ended 27 minutes later. The engine could stop naming
     itself to the cycle. The poll could be ten minutes. The cancel path could skip the group kill:
     the engine's graceful stop then waited about 30 s on a grandchild holding the pipe, and left it
     running.
  2. **The lock check (F2).** `stale` could answer None for every lock.
  3. **The invariants gate (G6, G7, G8, G13).** Four refusals were never watched failing: a number
     that is a row and retired, a wrong count, a near-empty list, and a broken gap or retired row.
     A broken gap row was reported only as the gap being missing.
  4. **The surface checks (H1a to H1e, H4, H5).** Five TLS patterns could each be deleted, since
     the planted lines held two at once or none. A job's own `permissions:` and `write-all` were
     never planted.

  **The fix:** apply `docs/reviews/m18-wave-6-tester.patch` (8 tests, 12 items, +224 lines). Each
  test passes on `4f6d025` and fails on its fault (the table under "Tests added").

- **T2** `tests/unit/test_security_invariants.py:34`, `:40`, `:66-70`, `:91-94`. **The invariants gate still fails open on three spellings.** Each probe was added to the list with the count left as it was, and the gate passed:
  1. `|INV-84 | x | y | \`tests/unit/test_no_such_file.py::test_nothing\` |` (no space after the
     first `|`). `unreadable` reads only lines that start with `| INV-`, so this row is never
     read, and its missing test never checked.
  2. A citation of a helper, not a test: `` `tests/unit/test_refresh.py::_builder` ``.
     `declared_names` accepts any `def`, so a row can cite a function that pytest never runs.
  3. A bare path beside a good citation: `<br>tests/unit/test_nope.py::test_gone`. `CITED` reads
     only backticked text.

  **The fix:** in "The list", treat any line that starts with `|` and is not the header or the
  rule line, and does not match `ROW`, as unreadable. Accept only names that pytest or XCTest runs
  (`test_` in Python, `test` in Swift). Treat any `tests/…::` or `ios/…::` path outside backticks
  as unreadable.

- **T3** `tests/unit/test_dependency_locks.py:121`, `:140-144`. **The install check passes two installs that fetch outside the locks (INV-81).**
  1. `pip install --no-cache-dir --prefix=/install --no-deps --no-build-isolation . requests` in the
     `Dockerfile`. A command without `--require-hashes` passes if it has the two flags, whatever
     else it installs. `requests` would be fetched at its newest, unhashed.
  2. `"${PIP}" install requests` in `scripts/install_engine_service.sh`. The pattern reads `pip` in
     lower case only, so `$PIP` and `${PIP}` are not read.

  **The fix:** a command without `--require-hashes` may name only the project (`.`, `-e .`,
  `-e "$rel"`). Match `pip` without regard to case. Pin both probes in
  `test_the_install_check_reads_every_spelling`.

- **T4** `tests/unit/test_security_surface.py:81-82`, `:114-128`. **Two more spellings pass the TLS and model checks.**
  1. `httpx.Client(**{"verify": False})` in `src`. `TLS_OFF` reads `verify=False`, not
     `"verify": False`.
  2. `from google import generativeai` in a function in `src`. `MODEL_PACKAGES` lists
     `google.generativeai`, but for `from X import Y` the check reads only `X`, here `google`.

  **The fix:** add `["']verify["']\s*:\s*False` to `TLS_OFF`. For `ImportFrom`, also test
  `module + "." + name` for each name. Pin both.

- **T5** `docs/research/stranger-first-use-protocol.md:63`, `:108-109`. **§7 attaches the session notes to a public issue, and §4 says the notes hold every question as typed.** §4: the owner writes down "each thing typed, exactly as typed". §7: "The session notes, without names, are attached to #91 by the owner. The questions themselves are not attached, since the issue is public." Read together, a question a person struck out in §5 would still be published, on #91. That undoes the consent the review's M3 fixed. **The fix:** say what the attached notes hold (for example, per person: how many questions, in which language, and what the screen did), and say that no typed text goes on the issue.

- **T6** `src/app/adapter/nightly.py:297`, `:303`; `docs/warnings.ledger.md:185`. **Two small slips.**
  1. When the timeout fires after the cycle has exited, `run_once` logs the output's tail twice:
     once in the `except` branch, and again after it. Up to 40 lines where 20 were meant.
  2. W-131's FIXED text says "Ten rows were mutated in the wave". The list's own table has eleven
     (`docs/security-invariants.md:224-234`).

  **The fix:** log the tail once. Say "eleven".

## K.9 candidates spotted outside this wave's scope

- **K1** `requirements/dev.lock` (starlette, through fastapi). **The locked test client warns that it will drop `httpx`.** Every run prints `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` (`fastapi/testclient.py:1`). The suite drives the API through that client. The next `make lock` after starlette removes it would turn most API tests red at once. Not this wave's change: the lock only fixed the version that warns. Enhancement: track it before the next lock refresh (D-177's "Revisit when").

## Risks queued to next M

- **R1** `src/app/workflows/refresh.py:101`, `:1086-1098`. **A cycle ended at its limit leaves its scratch for a day.** SIGALRM's default action runs no `finally`, so the candidate, the build report and an unpacked Epoch bundle stay beside the artifact. The next cycle's sweep removes them only once they are a day old (W-124). That is bounded, and the candidate is the artifact's size. What would show it: `advisor.db.*.candidate` files after a "timed out" night.
- **R2** `src/app/workflows/refresh.py:116-117`. **A hand-run cycle in a shell that has `MODEL_RANKING_ENGINE_PID` set ends itself in about 5 s.** The variable names a process that is not its parent, so the watch sends SIGALRM, with no message. The engine sets it only in the child's environment, so this needs a person to copy it. What would show it: a hand-run refresh exiting -14 after a few seconds.
- **R3** `src/app/workflows/refresh.py` (the publish, then the record). **The review's R3 stands.** The limit can still land between the publish and the record. The kernel's signal makes that window no wider and no narrower. What would show it: a "timed out" night whose artifact fingerprint changed.

## Tests added/extended this review

Uncommitted in this worktree, and in `docs/reviews/m18-wave-6-tester.patch` (sha256
`a6c4c812c0b70c40146fa44c5263704347567765f0684307c9b4f837031f512a`; `git apply -R --check` clean
against the tree). Each passes on `4f6d025`, and each fails on its fault:

| test | proves | fails on |
|---|---|---|
| `tests/unit/test_refresh.py:1958` `test_main_gives_the_declared_budget_and_leaves_nothing_armed` | W-126: the declared budget; the limit armed with SIG_DFL while the cycle runs; the timer, the handler and the watch given back | A6, B1, B2, B3, B4, B5, B6 |
| `tests/unit/test_refresh.py:2009` `test_a_cycle_whose_named_engine_is_not_its_parent_ends_within_seconds` | D-154 as amended: "within seconds", at the shipped poll; the named pid, deterministically | C2, C4 |
| `tests/unit/test_nightly_refresh.py:718` `test_the_engine_names_itself_to_the_cycle` | the engine's side of the watch | C3 |
| `tests/unit/test_nightly_refresh.py:733` `test_a_cancelled_cycle_takes_its_group_with_it` | W-130 on the graceful stop's path | D3 |
| `tests/unit/test_dependency_locks.py:168` `test_a_lock_resolved_from_another_pyproject_is_reported_and_fails_the_check` | #35: `stale` and `--check` report a stale or missing lock | F2 |
| `tests/unit/test_security_invariants.py:224` `test_a_retired_row_a_wrong_count_a_short_list_and_a_broken_gap_are_refused` | W-131: four of the gate's refusals | G6, G7, G8, G13 |
| `tests/unit/test_security_surface.py:165` `test_each_way_of_turning_tls_off_is_refused_on_its_own` (5 items) | INV-11: each pattern alone | H1a, H1b, H1c, H1d, H1e |
| `tests/unit/test_security_surface.py:171` `test_the_workflow_check_reads_a_jobs_scope_and_write_all` | INV-10: a job's scope and `write-all` | H4, H5 |

The two process tests (`:2009` and `:733`) take about 5 s and 1 s. Each child they start is ended:
the first by its own SIGALRM, or by `subprocess.run`'s SIGKILL at 30 s; the second by the group kill
under test, and by SIGKILL in the test's `finally`.

## How I worked

1. **One worktree,** `w6-tester`, detached at `4f6d025`, with its own `.venv` (Python 3.14, built by
   `make install` from the locks) and its own `advisor.db`. Every command ran with the guard
   stubs first on `PATH`. No other worktree or the owner's repository was touched.
2. **No crash dialogs.** No probe used `abort`, `fatalError`, `precondition` or `try!`, and none
   raced a thread's `print` against shutdown. Processes ended by SIGALRM (the wave's own limit) or
   SIGKILL only. After every batch, `pgrep` found no process left from this seat.
3. **Not done, by this seat's rules:** no installer run by hand, no `launchctl`, `xcodebuild` or
   `simctl`, no simulator, no Docker build, no network in tests, no `make lock`, no commit or push.
4. **Tree at the end:** the five test files above, this record and the patch. Nothing else differs
   from `4f6d025`.

*Filled by: Tester seat (independent) · Date: 2026-10-04 · Commit range: `8a18324..4f6d025`*
