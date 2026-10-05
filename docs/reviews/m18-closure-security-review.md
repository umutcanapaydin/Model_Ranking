---
record_type: review
id: m18-closure-security-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# M18 closure security review: the app on the owner's phone, and the first release's groundwork

> **Independent seat.** I wrote none of M18's code, and I sat in none of its wave seats. D-172 (the
> owner's ruling) gives no wave a security pass of its own and adds this one seat over the whole
> milestone, before the closure pull request opens. **This is not the Stage 5.1 release review.** It
> uses the Stage 5.1 profile (`.claude/agents/Security-Reviewer.md`), scoped to M18. The release
> review is still owed before any deploy.
>
> Policy was read from the base, `159ec9e` (the M17 closure merge). The profile,
> `docs/security-baseline.md`, `permission-matrix.md`, `.claude/settings.json` and `conformance/` do
> not change in the range. `AGENTS.md` changes only to record D-172 and D-174.
>
> The surface is `git diff 159ec9e a259ed0`: 138 commits (129 not merges), 250 files,
> +57,868/−1,114. About 36,000 of those lines are W3's measurement files. `a259ed0` is the head of
> the stacked waves W3, W6 and W7; W1, W2, W4 and W5 are already on `main`. The only repository file
> this seat writes is this one, and it is not committed.

## Verdict

**Independent:** yes.

**PASS WITH FINDINGS.** Nothing is BLOCKING. There is **1 MAJOR, 5 MINOR and 12 INFO**.

The scale:
- **BLOCKING:** ships and is exploitable now, or the permission matrix §11 human-review trigger fires.
- **MAJOR:** not exploitable today, but a security control is weaker than its record says, in a way
  that would hide an exploitable state. Fix it before the Stage 5.1 review.
- **MINOR:** an invariant or a control that a code change could break with every gate green, or a
  claim wider than its test. Not exploitable in the current scope.
- **INFO:** checked and recorded; no action unless stated.

What M18 is built around holds under measurement:
- **The network surface (W1).** The Host check and the no-list loopback rule each fail a test when
  weakened (N1, N2). The installer keeps the mode it finds and runs only the deployed release (N3,
  N4). The launcher's three M17 survivors are now killed (W6 sample, rows 3-5).
- **The refresh's new limits (W6).** The orphan rule, the parent watch and the process-group kill each
  fail a test when removed (R4, R5, R6). A cycle ended by SIGALRM, run for real on a scratch copy,
  left the live artifact byte-identical and the lock free.
- **The server loads no client or parser (W-125)**, and every reader opens the artifact read-only
  (R7, R8). M17's INV-23 survivors are closed.
- **The phone (W2, W3).** The byte ceilings, the redirect rule, the address fallback, the boards
  request, the held reading and the closed verdict each fail a Swift test when weakened (E1-E5, E7,
  E8). A Release build that reads its launch arguments is refused by `make client-decls` (V3).
- **`make gate` passes on `a259ed0`.** No secret is in the range.

What does not hold:
- **The dependency audit lost the parser of hostile bytes (S1, MAJOR).** W6 moved pyarrow into the
  `ingest` extra. `make deps` and CI audit only `[project].dependencies`, so pyarrow is now audited by
  nothing. Nothing audits the locks that every install now reads.
- **Six of my 41 mutants survive every gate and are not known gaps.** They break four invariants: the
  one-rename publish (S2), the gap register's file protection (S3), the standings ceiling and the
  single-answer boot bound (S4). The shipped code is right in each case; the tests cannot fail.
- **D-177 says nothing is fetched beyond the locks (S5).** `make install` fetches the newest pip
  without a hash.
- **The force-push guard has holes (S6).** W7's close records a force-push. The shipped guard lets
  `git push -uf`, `git push -fu` and `git push --mirror` through (measured).

## 0. Surface and method

**Waves.**
- W1: the engine on the home network by opt-in, the Host check (D-171), the launchd service tested by
  running it (#86).
- W2: the screen; the phone's byte ceilings (#56); a Debug-only UI test hook (D-175).
- W3: the reading of the question: input signals, a closed verdict, a held reading (D-169); the
  held-out discipline gate.
- W4: the engine backlog (D-173): roster ids, the accessibility loss guard, the candidate's serving
  bounds, the boards memo and gzip.
- W5: the gates: decoded URLs (#58), the declaration gate's fixture (#51), offline Swift tests (#59),
  read-only opens through the audit event, auto-HIGH for input parsing (#83).
- W6: W-125, W-126 and W-130 fixed; the four hash-checked locks and pyarrow off the image (D-177); the
  invariants list (#89).
- W7: the tests' network guard (#122), the gap register's writer (#121), the launcher's hint (#104),
  the PRD citation gate (#105).

**Method.**
- **Worktree.** My own, detached at `a259ed0`, with a venv built from the locks and a copy of the
  served artifact. Every command ran behind the guard stubs for `launchctl`, `xcodebuild` and `simctl`.
- **Mutants.** A script applies each mutant as an exact, single-match edit. It records each file's
  sha256 first, runs the row's cited tests, and, for a survivor, the full suite. Phone mutants run the
  Swift classes named, or the text gate and `client-decls` for the view, which `swift test` does not
  compile. The script restores the bytes and asserts the sha256, then checks `git status`. Every
  restore matched. `PYTHONDONTWRITEBYTECODE=1` throughout; any bytecode the children wrote was removed.
- **The served artifact.** Read in place only. sha256 `5c6977a9…475b` before and after. The one probe
  that needed a refresh ran on a copy in my scratch folder.
- **Network.** `make gate`'s `deps` and `slopsquat` legs reached PyPI, as expected. I also ran
  pip-audit against the four locks and against `.`, which reach the same PyPI service, to measure S1.
  No product upstream was contacted. `RUN_CONTRACT_TESTS` was not set. GitHub was not read.
- **The owner's machine.** No installer, `launchctl`, Docker or simulator. The engine on port 8080 was
  not contacted; I only listed processes. One probe ran `refresh.main` on a scratch copy and ended by
  SIGALRM, a normal termination. No process of mine ended in SIGABRT, SIGSEGV or SIGBUS, and none is
  left running.
- **Model calls.** The gate's full `swift test` ran the on-device model tests once. Every mutant run
  skipped `RouterBoundaryTests`.

**Gates I ran myself:**

| Gate | Result |
|---|---|
| `make gate` at `a259ed0` | **PASS.** pytest 1766 passed, 25 skipped; `swift-test` 462, each in the manifest; `client-decls` 19 files in 4 configurations; conformance 16; gitleaks (tree) no leaks; pip-audit `.` none; slopsquat 19 dependencies |
| `gitleaks detect --log-opts=159ec9e..a259ed0` | 129 commits, **no leaks** |
| `git diff 159ec9e a259ed0 \| gitleaks stdin` | **no leaks**. A random `ghp_` token fires, so the scan is live |
| `pip-audit --strict --disable-pip --no-deps -r requirements/<lock>.lock`, each of the four locks | **no known vulnerabilities** (ingest: 24 packages, pyarrow 25.0.1 among them) |
| `pip-audit --strict . -f json` (what `make deps` audits) | 23 packages; **pyarrow is not among them** (S1) |
| `ruff check --select S,BLE src scripts` (the SAST substitute) | 18 hits, against 29 at `159ec9e`. Each is a documented catch-all or an `assert` on a pipe, as at M17. No new rule class |
| The project's Bash guard, run on payloads | `-uf`, `-fu` and `--mirror` pushes pass (S6) |

## 1. Findings

### BLOCKING

None.

### MAJOR

**S1 (MAJOR): The dependency audit no longer sees pyarrow, the package that parses hostile parquet,
and it never sees the locked versions every install now runs.**

**Where.**
- `Makefile:255`: `$(PY) -m pip_audit --strict .`. CI runs the same: `.github/workflows/ci.yml:105`,
  `:113`.
- pip-audit's project mode reads `[project].dependencies` only, and resolves them fresh
  (`pip_audit/_dependency_source/pyproject.py:74`, pip-audit 2.10.1).
- `pyproject.toml:31-32`: since `d894ab5` (W6), pyarrow is in the `ingest` extra. At `159ec9e` it was
  in `dependencies` (`pyproject.toml:19`), so it was audited.
- `docs/security-invariants.md:152`, INV-80: "Declared dependencies have no known advisory". Its
  cited test, `test_dependency_gate.py::test_the_gate_sees_every_declared_dependency`, checks slopsquat
  only.

**Measured.**
- `pip-audit --strict . -f json` audits 23 packages. pyarrow is not one of them.
- `requirements/ingest.lock` pins pyarrow 25.0.1 for the engine's release. Nothing in the gate or in
  CI audits any lock.
- Today the four locks are clean (my hand run, §0), and the fresh resolution of the base dependencies
  equals `serve.lock`. That equality lasts only until the next upstream release.

**Why MAJOR.**
- pyarrow is the one dependency that parses bytes from the network. D-165 runs it in a child for that
  reason, but the child runs as the owner's user, so it can read his files. pyarrow has had a critical
  code-execution flaw in exactly this path before (CVE-2023-47248, its IPC and Parquet readers).
- A new advisory for the locked pyarrow would leave `make deps`, the pre-push hook and CI green.
- D-177's own trigger is "a dependency must be upgraded for a security advisory". Nothing in the gate
  would raise it.
- The W6 review's K1 saw CI's half (a fresh install, not the locks) and filed it to #81, the owner's
  file. It did not see that `make deps`, the agent's own leg, has the same blindness, or that pyarrow
  left the audit altogether.

**Remedy.**
1. `make deps` audits the locks:
   `pip-audit --strict --disable-pip --no-deps -r requirements/serve.lock -r requirements/ingest.lock -r requirements/dev.lock -r requirements/build.lock`.
   Keep `pip-audit .` too if the fresh view is wanted.
2. A test that `make deps` names every lock, the shape of `test_every_install_reads_its_lock_and_resolves_nothing_else`.
3. INV-80's row cites the lock audit.
4. Add the same audit to the CI patch on #81.

### MINOR

**S2 (MINOR): INV-4's "a publish is one atomic rename" has no negative test on the refresh.
Publishing by copying over the live file passes all 1766 tests.**

- **Where.** `src/app/workflows/refresh.py:1260`, `candidate.replace(target)`.
- **Measured.** R1 replaced it with `shutil.copyfile(candidate, target)`. The cited tests and the full
  suite pass. The build's rename (R1b, `build.py:977`) is killed, but only because the copy leaves the
  workspace file behind; the refresh deletes its candidate in `finally`, so nothing is left to see.
- **Why it matters now.** W6's limit ends a stuck cycle with SIGALRM at any instruction, and the
  engine's kill at 30 minutes is SIGKILL. The rename is the one thing that keeps the live artifact
  whole when that happens mid-publish. A copy would let the engine read a half-written database, and
  a kill mid-copy would leave it torn.
- **Why MINOR.** The shipped code renames. My SIGALRM probe left the live file byte-identical.
- **Remedy.** A test that the publish replaces the file, not its bytes: the target's inode after a
  publish is the candidate's, or a reader holding the old file across the publish still reads the old
  bytes.

**S3 (MINOR): INV-67 is held only where the gap register's store is defined. The view can save the
typed questions without file protection, and can hand the store a writer of its own, with every gate
green.**

- **Where.**
  - `ios/ModelRanking/Engine/FrontDoor.swift:290-297`: the store's initialiser is public, with
    `writeOptions` and `write` as parameters.
  - `ios/ModelRanking/ContentView.swift:868` and `:630`: the view's two saves.
  - `tests/unit/test_router_hints.py:708-725`: the writer pin reads only the arguments inside the
    parentheses.
- **Measured.**
  - V1: `GapRegisterStore(url: GapRegisterStore.onDevice.url).save(gaps)` at `:868`. The typed
    question is then written without `.completeFileProtection`.
  - V2: `GapRegisterStore(url: GapRegisterStore.onDevice.url) { _, _ in }.save(gaps)` at `:630`. A
    trailing closure is the writer, and the pin does not see it.
  - Each passes the text gate (72 tests), `client-decls` in all four configurations, and the full
    Python suite. `swift test` does not compile the view.
- **The pair.** W7's writer parameter and W5's declaration gate. The gate still keeps a view's writer
  off the file system and the network. But the store's own parameters now let the view weaken what
  the store promises, and the pin that was meant to stop that reads one spelling.
- **Why MINOR.** It needs a code change, and the data stays on the device. The shipped view uses
  `.onDevice` both times.
- **Remedy.** Pin that every `GapRegisterStore` reference outside `FrontDoor.swift` is
  `GapRegisterStore.onDevice`, or give the view one save function in `FrontDoor.swift` and pin that.
  Add V1 and V2 to G-3's list if they stay open.

**S4 (MINOR): Two invariants cite negative tests that cannot fail.**

- **INV-74, the standings ceiling.**
  - `ios/EngineTests/StandingsStoreTests.swift:177-180` feeds `Data(count: 4 MiB + 1)` and asserts a
    throw. Zero bytes are not JSON, so it throws with or without the ceiling.
  - E6 (the ceiling 64 times wider) and E6b (no ceiling) pass 453 Swift tests.
  - On the network path the ceiling still holds through `EngineClient.read` (E1, E2 killed). The
    disk path (`StandingsStore.load`) has only this one.
- **INV-33, the single-answer boot bound.**
  - The engine refuses to boot on an artifact that would publish more than
    `MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS` in one answer (`src/app/adapter/main.py:466-469`).
  - INV-33's row lists only "ranked models, standings". H4 (the engine's check reads that bound 1000
    times wider) passes the full suite.
  - The shared check is killed through the refresh (H2, `test_refresh.py:1765`), so INV-56 holds. The
    engine's own boot use does not.
- **Remedy.** Test the ceiling with a valid standings payload padded past 4 MiB, and assert the
  "larger than" refusal. Add the single-answer bound to INV-33, with a boot test.

**S5 (MINOR): D-177 and INV-81 say nothing is fetched beyond the locks. Two things are.**

- `Makefile:75`: the venv is made with `python -m venv --upgrade-deps`. That fetches the newest pip
  from PyPI, with no hash, and runs it before the hash-checked install. `dev.lock` then pins pip, but
  only after the unpinned one has run.
- `Dockerfile:9`, `:21`: the base image is `python:3.11-slim` by tag, not by digest. Its pip is the
  tool that checks the hashes.
- `tests/unit/test_dependency_locks.py:121-163` reads `pip install` lines only, so it sees neither.
- The release's venv (`install_engine_service.sh:121`) makes its venv without `--upgrade-deps`, so the
  owner's engine is not affected.
- **Remedy.** Drop `--upgrade-deps` (the venv's bundled pip then installs `dev.lock`, which pins pip
  with its hash), pin the base image by digest, or narrow D-177's words to what is held.

**S6 (MINOR): The guard that stops a force-push has holes, and W7 recorded a force-push.**

- **Where.** `.claude/settings.json:49`, the Bash PreToolUse guard. It matches `--force`,
  `--force-with-lease`, a lone `-f` and a `+` refspec.
- **Measured.** I ran the guard's own command on payloads, under `/bin/sh` with `/usr/bin/grep`:
  - exit 0 (allowed): `git push -uf origin wave/x`, `git push -fu origin wave/x`,
    `git push --mirror origin`;
  - exit 2 (blocked): `--force`, `-f`, `+wave/x`, `--force-with-lease`, any push to `main`, and
    `git reset --hard`.
- `conformance/test-hook-claims.py:281` has none of the allowed spellings in `MUST_BLOCK`. So INV-82
  ("an agent cannot run a destructive git command") holds for the listed spellings only.
- `docs/plans/m18-wave-7-close.md:43` records that `58e8bf4` "was … force-pushed to `wave/m18-w7`".
  The record does not say how the guard let it through. A combined flag would do it, and so would a
  session started outside the repository, which loads none of its hooks.
- **Why MINOR.** `main` stays protected twice: the guard's own rule for it (measured: exit 2 for
  `-uf … main`) and branch protection. What is exposed is a wave branch's history.
- **Remedy.** Match any short-option cluster holding `f` after `push`, and `--mirror`; add those to
  `MUST_BLOCK`. Say in W7's record how the push ran.

### INFO (verified; no action unless stated)

**S7: The home network, as built, is what D-171 says.** The Host check stops a browser page, not a
device: anyone who can reach the Mac can send `Host: localhost` and read the public GETs. `--lan`
binds every interface on every network the Mac joins, and a reinstall keeps it (N3 killed). The
phone's requests cross Wi-Fi in cleartext, carrying `task` and `budget`. D-171's cost and notes 2, 4, 7
and 9 say all of this. Nothing is writable and nothing is private, so no action while that holds.

**S8: The tests' network guard trusts loopback** (`tests/conftest.py:36-49`). Two consequences:
- A unit test can read the owner's live engine on `127.0.0.1:8080`. Its routes are GET only, so a
  test can read but change nothing.
- With `HTTPS_PROXY` set to a loopback proxy, `httpx` connects to the proxy and the proxy reaches the
  internet. The guard sees only loopback. Read, not run. Clearing the proxy variables in `conftest.py`
  closes it.

**S9: `SameHostOnly` compares the host only** (`EngineClient.swift:134`). A redirect to another port or
scheme on the engine's host is followed. INV-72's words say host, so this matches them. On the
http-only home network it changes nothing.

**S10: The phone's session keeps cookies** (`EngineClient.swift:205-209`). The ephemeral session
accepts a cookie from the engine's host and sends it on every later request, the parameterless
`/v1/boards` included. Anyone on the cleartext Wi-Fi could set one too. The declaration gate refuses
`HTTPCookieStorage` as a symbol, but the session's default needs no symbol. Read, not run. One line
closes it: `httpShouldSetCookies = false` and `httpCookieAcceptPolicy = .never`.

**S11: The launcher's preflight refuses on output, not on exit status** (`scripts/engine_service.sh:57-67`).
A preflight killed with no output (for example, out of memory) would let the start go on, in the
relaxed lane where startup problems only warn. The Host middleware still refuses a network arrival
with no list, so the network half holds. Read, not run.

**S12: A cycle ended by SIGALRM, measured.** On a scratch copy, with a 3-second limit and a builder
that half-writes its candidate and sleeps:
- exit 142 (SIGALRM); the live artifact's sha256 unchanged; the lock free (another process took it at
  once);
- left behind: the `.candidate`, `.sources` and `.last-ok` scratch, which the next cycle sweeps after
  a day (INV-49; the W6 Tester's R1).
- Not in the sweep's list (`refresh.py:1097`): `write_status`'s `.writing` scratch, and a SQLite
  `-journal` beside a candidate killed mid-write. Read, not seen in the probe. Litter, not unsafe.
- The publish-then-record window is the W6 review's R3, already queued.

**S13: The owner's phone runs a Debug build.** He builds with Xcode's Run, and the scheme's launch
action is Debug (`ModelRanking.xcscheme:34`). So D-175's Release guarantee does not cover his install.
Only Xcode can pass launch arguments to it, so nothing outside his Mac can steer it.

**S14: The owner's Mac name and LAN address are in the tracked tree** (`ios/Config/Engine.xcconfig:4`,
`docs/owner-iphone.md:19`, `:22`, `ios/EngineTests/EngineClientTests.swift:56`, `:720-747`,
`tests/unit/test_engine_host.py:37`). The repository is public. The name holds his first name, and the
Mac announces it on every network anyway (D-171 note 2). Low-grade; a placeholder name in tests and
docs would do.

**S15: G-1 is still open, re-measured.** M17's P2 (a refinement relayed onto `/v1/boards` through a
static on `EngineClient`) passes the text gate, `client-decls` in four configurations and 453 Swift
tests on this head. #85, moved to M19.

**S16: W3's "a tracked symlink is refused" is not a row.** W3's close (row 7) calls it a security
invariant and says W6's list holds it. W6 wrote the list before W3 merged, and the list's gate sees
only `INV-n` spellings. Add the row (`tests/unit/test_no_tracked_links.py`) or drop the claim.

**S17: Under D-172 this seat was the only security read of the input-parsing diffs.** INV-83 still
marks such a wave HIGH, but HIGH no longer buys a security pass. I read W4's #71
(`protocols.py:168`, the deadline decided before the close) and W6's budget (`protocols.py:57-93`): the
budget only shortens a deadline, and a spent one raises `SourceError`, so the source carries. Both
hold as read; the W6 review sampled INV-42, and R10 shows a failed fetch carries.

**S18: Carried from M17, unchanged.**
- CI installs unlocked and audits `.` (#81, the owner's file).
- The phone gates run only on the Mac: CI is Linux, where `client-decls` and `swift-test` skip.
- `issue-agent.yml:13`, `:31` still name branch protection as what stops a self-merge (M17 I-2).
- The installer resolves `origin/main` three times and prunes old releases with `rm -rf` inside its
  own folder (M17 I-6).

## 2. The M17 closure seat's findings, on this head

| M17 finding | Status | Evidence |
|---|---|---|
| MINOR-1: INV-23 had no test on M17's readers | **Closed** | W5's audit-event tests (`test_readonly_uri.py`). R8 (`fingerprint_of` read-write) killed; W6's `/v1/boards` mutant killed. `calibrate_board.py:153` opens read-only |
| MINOR-2: upstream dates and infinities verbatim | **Closed** | `_store_scores` refuses a non-finite score and stores a calendar date or nothing (`ingest.py:113`, `:139`). D1 killed; W6's date mutant killed |
| MINOR-3: the privacy sinks by spelling | **Open, as G-1** (#85, M19) | P2 replayed: survives (S15) |
| MINOR-4: the launcher by substring | **Closed** | The launcher and installer run in tests. W6 rows 3-5 killed; N3, N4 killed |
| MINOR-5: W-125, W-126, W-130, W-131 | **Closed** | FIXED in `docs/warnings.ledger.md:179-185`. R4-R7 killed; the list exists |
| I-1: policy | **No weakening** | Only `AGENTS.md` changes, to record D-172 and D-174 |
| I-2: the issue agent's comment | Unchanged | S18 |
| I-3: the stale brief | **Closed** | `docs/project-brief.md:55` |
| I-4: no Host check | **Closed by D-171** | N1, N2 killed |
| I-5: a refresh past a boot bound | **Closed by #57** | R3 killed |
| I-6: install hygiene | **Lock half closed** (D-177; G3, G4 killed) | Prune and triple resolution unchanged (S18) |
| I-8: the `select` guard | **Closed** | INV-70; W6 row 11 killed |
| I-9: no accessibility loss guard | **Closed by #42** | INV-55; the W6 review's mutant killed |
| Its 13 survivors | **11 closed, 2 open** | 7 INV-23, 3 launcher, 1 `select` now killed. P2 and P3 are G-1 |

## 3. The invariants list: what I mutated, and whether it is complete

The earlier M18 samples covered INV-23, -25 to -29, -40, -47, -5, -58, -70 (W6 author); -31, -34,
-38, -46, -55, -9, -42, -43, -81 (W6 review); and -30, -32, -36, -37, -41, -3, -48, -22, -52, -60,
-10, -11 (W6 Tester). I chose rows they did not cover, rows of M18's new surface, and different edits
on rows they did. Mutant ids: N, the network surface; H, the HTTP surface; R, the artifact and the
refresh; D, parsing; G, the gates; E, the phone's Engine layer in Swift; V and P2, the view.

| # | Row | The edit | Result | Killed by |
|---|---|---|---|---|
| N1 | INV-26 | Host check accepts a Host that starts with an allowed name (`main.py:689`) | KILLED | `test_engine_host.py::test_a_host_not_on_the_list_is_refused` |
| N2 | INV-25 | a private (LAN) arrival counts as loopback (`main.py:504`) | KILLED | `::test_without_a_list_a_request_arriving_on_a_network_address_is_refused` |
| N3 | INV-28 | a reinstall opens the network over any wrapper (`install_engine_service.sh:51`) | KILLED | `test_engine_service.py::test_a_reinstall_keeps_the_home_network_unless_told_to_close_it` |
| N4 | INV-29 | the wrapper runs the development checkout (`install_engine_service.sh:76`) | KILLED | `::test_the_wrapper_runs_the_deployed_release_with_its_own_artifact` |
| H1 | INV-33 | the ranked-models boot bound off (`serving_bounds.py:169`) | KILLED | `test_stage40_minors.py::test_an_artifact_with_too_many_ranked_models_refuses_to_boot` |
| H2 | INV-33, -56 | the shared single-answer check 1000 times wider (`serving_bounds.py:154`) | KILLED | `test_refresh.py::test_a_candidate_past_a_serving_bound_is_refused` only |
| H4 | INV-33 | the engine's boot check reads that bound 1000 times wider (`main.py:468`) | **SURVIVED** | none; 1766 passed (S4) |
| H3 | INV-35 | the answer's field allowlist passes every field (`main.py:1070`) | KILLED | `test_api_config.py::test_the_public_payload_carries_only_declared_fields` |
| R1 | INV-4 | the refresh publishes by copying over the live file (`refresh.py:1260`) | **SURVIVED** | none; 1766 passed (S2) |
| R1b | INV-4 | the build publishes by copying (`build.py:977`) | KILLED | `test_build_artifact_safety.py`, by the leftover workspace, not by atomicity |
| R2 | INV-53 | roster guards compare display names (`refresh.py:544`) | KILLED | `test_refresh.py::test_a_candidate_that_only_re_spells_names_moves_no_guard` |
| R3 | INV-56 | no serving bound on the candidate (`refresh.py:945`) | KILLED | `::test_a_candidate_past_a_serving_bound_is_refused` |
| R4 | INV-42 | an orphaned cycle ignores the engine's PID (`refresh.py:120`) | KILLED | `::test_a_cycle_whose_engine_is_gone_ends_itself` |
| R5 | INV-42 | the parent watch never fires (`refresh.py:130`) | KILLED | same |
| R6 | INV-42 (W-130) | the cycle shares the engine's process group (`nightly.py:280`) | KILLED | `test_nightly_refresh.py::test_the_timeout_kill_takes_a_grandchild_that_holds_the_output` |
| R7 | INV-43 | a module the server loads imports `httpx` (`serving_bounds.py`) | KILLED | `::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers` |
| R8 | INV-23 | `fingerprint_of` opens the live artifact read-write (`refresh.py:603`) | KILLED | `test_readonly_uri.py::test_nothing_opens_a_database_but_the_named_writers_and_the_read_only_opener` |
| R9 | INV-49 | the sweep removes scratch of any age (`refresh.py:1100`) | KILLED | `test_epoch_bundle_fetch.py::test_scratch_a_killed_cycle_left_is_swept_by_the_next` |
| R10 | INV-50 | only an `OSError` from the Epoch fetch is a failed source (`refresh.py:1074`) | KILLED | `::test_a_fetch_that_fails_leaves_the_boards_to_carry` |
| D1 | INV-5 | a non-finite score is stored (`ingest.py:113`) | KILLED | `test_stored_scores_are_bounded.py::test_a_non_finite_score_refuses_the_source` |
| D2 | INV-1 | the YAML size bound off (`yaml_guard.py:115`) | KILLED | `test_yaml_guard.py::test_an_oversized_document_is_refused_by_size` |
| D3 | INV-2 | `reset_source` takes any table (`schema.py:449`) | KILLED | `test_schema.py::test_reset_source_rejects_unknown_table` |
| G1 | INV-63 | `decodeIfPresent` making a URL is not the network (`client_decl_gate.py:216`) | KILLED | `test_client_decl_gate.py::test_the_gate_refuses_its_compiled_fixture` |
| G2 | INV-75 | a Release build may read its launch environment (`client_decl_gate.py:324`) | KILLED | `::test_a_release_build_carries_no_ui_test_hook` |
| G3 | INV-81 | the release's project install drops `--no-deps` (`install_engine_service.sh:124`) | KILLED | `test_dependency_locks.py::test_every_install_reads_its_lock_and_resolves_nothing_else` |
| G4 | INV-81 | the image's project install drops `--no-deps` (`Dockerfile:19`) | KILLED | same |
| G5 | INV-83 | a wave touching input parsing need not be HIGH (`wave_check.py:370`) | KILLED | `test_wave_check_m18_rules.py::test_a_wave_touching_input_parsing_must_be_high` |
| G6 | INV-62 | the declaration gate forgets `UserDefaults` (`client_decl_gate.py:139`) | **SURVIVED** (gap G-3) | none; 1766 passed, and the shipped client uses none |
| E1 | INV-71 | a declared length over the ceiling is read (`EngineClient.swift:327`) | KILLED | `ResponseCeilingTests.testADeclaredLengthOverTheCeilingIsRefusedBeforeTheBody` |
| E2 | INV-71 | the streamed read never stops (`EngineClient.swift:334`) | KILLED | `ResponseCeilingTests`, 6 of 6 |
| E3 | INV-72 | a redirect to a host that ends with the engine's is followed (`:134`) | KILLED | `SameHostOnlyTests.testAHostThatMERELYENDSWithTheEngineHostIsRefused` |
| E4 | INV-73 | any scheme with a host is an engine address (`:172`) | KILLED | `EngineAddressTests.testAnythingElseFallsBackToLoopback` |
| E5 | INV-65 | the boards request carries a parameter (`:243`) | KILLED | `BoardsRequestTests.testTheBoardsRequestCarriesNothing` |
| E6 | INV-74 | the standings ceiling 64 times wider (`Models.swift:409`) | **SURVIVED** | none (S4) |
| E6b | INV-74 | no standings ceiling (`Models.swift:409`) | **SURVIVED** | none; 453 Swift tests (S4) |
| E7 | INV-68 | the register keeps a held reading (`FrontDoor.swift:347`) | KILLED | `ReadingThroughTheTiersTests.testOnlyASearchIsKeptInTheGapRegister` |
| E8 | INV-69 | the model's verdict ignored (`Router.swift:590`) | KILLED | `testTheBoundaryMapsTheModelsVerdict` and four more |
| V1 | INV-67 | the view saves without file protection (`ContentView.swift:868`) | **SURVIVED** | none: text gate, `client-decls`, 1766 (S3) |
| V2 | INV-67 | the view hands the store a trailing-closure writer (`ContentView.swift:630`) | **SURVIVED** | none: same (S3) |
| V3 | INV-75 | a Release build reads its launch arguments (`LaunchRouting.swift:10`, `:14`) | KILLED | `make client-decls`, both Release configurations |
| P2 | INV-66 | M17's P2 replayed: a refinement on `/v1/boards` | **SURVIVED** (gap G-1) | none: text gate, `client-decls`, 453 Swift tests |

**Score.** 41 mutants: 28 in Python, shell and the gates, 9 in the Swift Engine, 4 that need the view.
**33 killed, 8 survived (80.5 %).** Two survivors are known gaps (G6 is G-3, P2 is G-1); without them,
33 of 39 (84.6 %). Every new survivor is in a finding: H4, E6 and E6b (S4), R1 (S2), V1 and V2 (S3).
22 rows were sampled for the first time in M18.

**Is the list complete for M18's surface?** Mostly. It covers every M18 change I could tie to a
security property, and its gate fails closed as its header says. What is missing or overstated:
- INV-80 says advisories are checked for declared dependencies; the extras and the locks are not (S1).
- INV-33 omits the single-answer boot bound (S4).
- INV-81 says nothing else is fetched; `--upgrade-deps` and the base image are (S5).
- INV-4 and INV-74 each cite tests that cannot fail (S2, S4).
- INV-67's "protected while locked" holds only at the store's definition (S3).
- INV-82 holds for the listed push spellings only (S6).
- W3's tracked-symlink rule is not a row (S16).
- The gaps are stated accurately as far as I checked: I re-measured G-1 (P2) and G-3 (G6), and read
  G-5. I did not check G-2.

## 4. Pairs no single wave could see

| Pair | What I found |
|---|---|
| The tests' guard trusts loopback (W7) × the engine binds loopback (W1) | A unit test can read the live engine; GET only. A loopback proxy is blind to the guard (S8) |
| The register's writer parameter (W7) × the declaration gate (W5) | The gate keeps a view's writer off the file system and network. The store's parameters let the view drop file protection, and the pin misses a trailing closure (S3) |
| The locks (W6) × `make deps` | The audit reads neither the locks nor the `ingest` extra; pyarrow left it (S1) |
| `MODEL_RANKING_ENGINE_PID` in the child's environment (W6) | Used only when the cycle is already orphaned (`refresh.py:120`), so a copied variable cannot end a cycle run by hand. The parquet reader's own allowlist does not carry it (`arena_slices.py:82`). R4 killed |
| `--lan` (W1) × a reinstall × the Host list | The mode is kept (N3), the address recomputed, and the list always has `127.0.0.1` and `localhost`. Exposure as D-171 says (S7) |
| The SIGALRM limit (W6) × the publish rename | Only the rename keeps the live file whole at a kill, and no test holds it (S2). As shipped it holds (S12) |
| gzip (W4) × the phone's ceilings (W2) | URLSession decompresses before `EngineClient.read` counts, so the ceiling bounds decoded bytes and a compressed bomb stops there (E2 killed). Read |
| The Host check (W1) × CORS and gzip (W4) | `_known_host` is added after both, so it runs before them, a CORS preflight included (`main.py:666-695`). Held by `test_every_path_is_behind_the_host_check` |
| The UI test hook (W2) × the reading (W3) | A scripted answer passes `ModelOutputBoundary.outcome(… request:)` like the model's (`ScriptedRouting.swift:26`). V3 killed |
| D-175's Release guarantee (W2) × the owner's install (W1) | His phone runs Debug (S13) |
| pyarrow off the image (W6) × W-125 | `serve.lock` has no pyarrow and the server loads none (R7), but the audit lost it too (S1) |
| D-172 × INV-83 | HIGH no longer buys a security read; this seat read the parsing diffs (S17) |

## 5. The baseline and the profile, walked

| Item | Status | Evidence |
|---|---|---|
| §1 Secrets | **PASS** | §0 scans. No `.env*` in the diff; `Engine.local.xcconfig` and `UITests.local.xcconfig` are ignored (`.gitignore`) |
| §2 Dependency hygiene | **FINDING** | One new dependency, `uv` (dev), PyPI-checked by slopsquat. Locks clean by hand. S1, S5 |
| §3 External surface, default deny | **PASS** | No new route. `/v1` gains three additive fields, all in the allowlist (H3 killed). Loopback by default (INV-28), the network by opt-in, every path Host-checked |
| §4 Prompt injection (HIGH) | **PASS** | The on-device model's output is a closed set: a served surface, a declared refinement, one of two verdicts (E8 killed, INV-69). Pasted content and instructions are signals in code. The engine has no model (INV-77) |
| §5 Auth, PII, payment, migration | **Not triggered** | None of these is in the diff. The gap register is the one store of what a reader typed (S3) |
| §6 Destructive operations | **FINDING** | W7 recorded a force-push of its own branch; the guard has holes (S6). The installer's `rm -rf` is scoped to its release folder (M17 I-6) |
| §7 SAST | **Substitute ran** | `ruff --select S,BLE`, §0. bandit and semgrep are not installed |
| §8 PII and logging | **PASS, with S14** | No log carries what a reader typed. The owner's Mac name is in the tracked tree |
| Baseline 3: CORS | **PASS** | INV-31 (the W6 review's mutant killed). The service sets no origin |
| Baseline 4: startup config, prod refuses | **PASS** | INV-32; the bind rule joins the validator (`main.py:576-581`); the launcher refuses on its output (S11) |
| Baseline 6: generic errors | **PASS** | `unknown_host` is a generic 400 with `nosniff` (`main.py:692-694`) |
| Fail direction | **PASS** | The Host check, the bounds, the ceilings and the limits fail closed; a source fails open per source (D-156) |
| Built is wired | **PASS** | Each control above was reached from its live entry: the FastAPI app, the launcher and installer as scripts, `refresh.main` as a process, `EngineClient.fetch`, `make client-decls` on the real client |
| Invariants list, a negative test per row | **FINDING** | §3 |
| Senior human review trigger | **Not triggered** | No auth, PII, payment or migration path |

**Acceptance criteria with a security side (file:line).**
- REQ-DEV-001 (the network surface): `tests/unit/test_engine_host.py:72`, `:116`;
  `tests/unit/test_engine_service.py:376`, `:433`; `ios/EngineTests/EngineClientTests.swift:761`.
  `docs/prd.md:588` marks it PARTIAL until the owner's own run.
- REQ-GAP-001 (the register stays on the device): `ios/EngineTests/FrontDoorTests.swift:745`, `:749`;
  `ios/EngineTests/ReadingTests.swift:334`; holds, with S3.
- REQ-API-001 (read-only `/v1`): `tests/unit/test_api_v1.py:516`, `:525`.
- REQ-REF-009 (the refresh publishes nothing the engine would refuse): `tests/unit/test_refresh.py:1749`,
  `:1765`.
- REQ-REF-007 and W-125 (the server loads no refresh or client): `tests/unit/test_nightly_refresh.py:442`.
- D-126 (the model's output is a closed set) and D-175 (no hook in Release):
  `ios/EngineTests/ReadingTests.swift:227`; `tests/unit/test_client_decl_gate.py:85`.
- W6's "one invariants list, a negative test per row": `tests/unit/test_security_invariants.py:154`,
  `:158`, `:182`, `:192`, `:201`; with §3's exceptions.

## 6. Skip ledger

| Check | Why it did not run | Consequence |
|---|---|---|
| The installer for real, `launchctl`, Docker, the simulator | Out of bounds for this seat | The installer and launcher were judged through their tests and by reading. The image build was not repeated; W6 built it twice |
| A connection to the owner's engine on 8080 | Out of bounds | S7 and S8 are reasoned from code and D-171 |
| `RUN_CONTRACT_TESTS`, `EPOCH_DATA_DIR` tests (25 skipped) | Network and the owner's bundle | Upstream shape drift is not re-checked here |
| bandit, semgrep | Not installed; this seat installs nothing | `ruff --select S,BLE` instead |
| `make ui-test` | Needs the simulator | The view's mutants were judged by the text gate and `client-decls`; nothing runs the view |
| `RouterBoundaryTests` in mutant runs | They call the on-device model | They ran once, in the gate's `swift test` |
| M17's P3 replay | P2 shows G-1 is still open; P3 is the same gap | Not re-measured |
| GitHub reads (branch protection, #81's state) | No GitHub access was asked for | S18's CI items come from the tracked workflows and the records |
| A live run of S8 (proxy), S10 (cookies), S11 (silent preflight) | Each needs a network, a device or a killed process on the owner's machine | Each is marked "read, not run" |

## 7. What I did not check

- The app on a device or the simulator, and what a hostile engine's answer looks like on screen.
- Whether the owner's GitHub settings match `docs/branch-protection.md`.
- Whether a hostile but well-formed upstream can move a ranking inside the refresh's guards. The
  upstreams are authoritative for their numbers by design.
- The data licences (#88). They are the owner's ruling and not a security question.
- The Code-Reviewer and Tester verdicts, beyond the security records cited above.

## Dispositions, at the closure

Written by the lead agent after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| S1 | fixed `c256864`: `make deps` audits the four locks, and an empty set fails closed; the CI command is proposed on #81 |
| S2 | fixed `c256864`: `test_a_publish_replaces_the_file_and_never_writes_into_it` kills R1 |
| S3 | fixed `c256864`: the view names the store only as `.onDevice`, and the writer pin sees a trailing closure; V1 and V2 each fail a test |
| S4 | fixed `c256864`: a valid padded payload past the ceiling (E6 killed); the engine's single-answer boot bound in INV-33 (H4 killed) |
| S5 | fixed `c256864` for `make install` (no `--upgrade-deps`, checked on a scratch venv); the image's base by digest is #141, gap G-8 |
| S6 | #142, gap G-7 (a hook change is the owner's). W7's record now says how its push ran: the session had started outside the repository, so no hook was loaded |
| S7 | no action: D-171 states it |
| S8 | #143 |
| S9 | no action: it matches INV-72's words |
| S10 | #144 |
| S11 | #145 |
| S12 | #146 |
| S13 | no action; the closure pull request tells the owner |
| S14 | #147, the owner's call |
| S15 | gap G-1, #85, moved to M19 |
| S16 | fixed `c256864` (INV-84), with the repo review's M9 |
| S17 | no action |
| S18 | carried: #81 (the owner's CI), and M17's I-2 and I-6 as recorded |
