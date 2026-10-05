---
record_type: review
id: m18-wave-6-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W6 Code Review: first-release preparation

**Reviewer:** Code-Reviewer subagent, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `8a18324..cf83fea` (7 commits, 37 files, +4322 / -217). `8a18324` is the M18-W3 head;
the branch is stacked on `wave/m18-w3`.
**Risk tier:** HIGH (`docs/plans/m18-plan.md:124`, `docs/plans/m18-wave-6-plan.md:14`). The diff also
touches two security globs: `src/app/clients/**` and `scripts/*engine_service*.sh`. By D-172 no
security seat runs on the wave.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat).
**Fresh context:** I started with none of the authoring context. I read the base-ref policy, then
both plans and the ADRs, then the diff, and only then the commit messages and the ledger rows. The
one-line commit subjects were visible in `git log` from the start.

**Summary.** The wave does most of what it planned, and the code is careful. Each new test fails
when I take its fix away (20 mutants, all killed but one, below). The server no longer loads any
source client or `httpx`. A spent fetch budget really does make every source carry: I ran a whole
cycle with the budget at zero, and it ended "unchanged" with 41 sources carried. The locks match
each other and this seat's venv, package for package.

Nothing blocks. Eight MINORs remain. The first matters most:
1. **M1.** The cycle's own limit is a Python timer thread. It cannot fire while a call holds the
   GIL. It can abort Python if it fires during shutdown. And the new process group takes the cycle
   out of the group launchd kills when the engine dies.
2. **M2.** #88, the licence table, was planned in P4 and is not delivered or moved.
3. **M3.** The stranger protocol commits strangers' typed questions to a public repository, and
   its consent words do not say so.
4. **M4–M6.** The invariants list has wrong ids and one row that its test does not hold. The gate
   skips rows and citations it cannot parse. The TLS check misses the usual Swift trust-all.
5. **M7.** The lock covers the packages but not the build backend. The install check reads one
   spelling, and no ADR records the new install path.
6. **M8.** The server still loads one source parser, and four comments still say W-125 is open.

**Policy.** `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md` were read at the
worktree head and are unchanged from `8a18324` (`git diff --quiet 8a18324 cf83fea -- .claude .agents`
is clean). `AGENTS.md` was read from `8a18324`.

**How I worked.** Everything ran in this seat's worktree at `cf83fea`, with its own `.venv`
(Python 3.14.0, built by `make install` from `requirements/dev.lock`) and its own `advisor.db`.
1. **Gates at `cf83fea`.** Each one ran with its output in a file, and I read the exit code.
   1. pytest `-n auto` with `MODEL_RANKING_REQUIRE_ARTIFACT=1`: **1695 passed, 25 skipped**, rc 0.
      Coverage 91.81%.
   2. ruff: all checks passed. mypy (strict, `src`): no issues in 44 files.
   3. `module_coverage_floor.py`: PASS, 44 modules. `check_records.py`: PASS, no findings.
   4. `wave_check_all.py`: PASS, 51 records. `shell_dialect_check.sh`: PASS, 11 scripts.
      `conformance/run-all.py`: PASS, 16 tests.
   5. `lock_dependencies.py --check`: 3 locks current.
   6. Not run: `swift test` and `client-decls`. W6 changes no Swift file; it adds a Python pin over
      `ContentView.swift`.
2. **Imports.** Every `from app… import name` in `src`, `tests` and `scripts` (1259 names) resolves
   at the head. No test patches a moved name on its old module.
3. **Mutants: 20 in-place edits**, each restored from a byte copy and checked with `git diff
   --quiet` (all clean). 19 were killed. One survived: **M4**(1). The table is under "PASS".
4. **Probes: 7 more edits** that test a gate's reach, restored the same way. Five passed the gate
   and are findings (**M5**, **M6**, **M7**). One failed it as designed. One (a hand-edited
   transitive pin) passes the test, but pip's hash check would refuse it at install.
5. **Runtime probes**, in scratch folders:
   1. a whole refresh cycle on a copy of `advisor.db` with the fetch budget at zero (proxies set to
      `127.0.0.1:9`, so nothing could leave);
   2. the cycle limit against a call that holds the GIL (**M1**);
   3. `os.killpg` on macOS against a zombie group leader, alone and with a live member;
   4. the engine's kill when the cycle exits first and a grandchild holds the pipe (**M1**).
6. **A probe crashed once. Please tell the owner.** Probe 5.2's first run ended with **SIGABRT
   (rc -6)**. I had not called `abort`. The likely cause is Python's fatal error when a daemon
   thread holds stdout's lock at shutdown. It may have left a crash report, or shown a "Python quit
   unexpectedly" dialog, on the owner's Mac. I did not run it again. I used a variant that cannot
   take that path. The cause is a finding in itself (**M1**(2)).
7. **Read only:** GitHub issues #88, #121, #122, #123, #85, #60, #107 and #110, and the repository's
   visibility (`PUBLIC`).
8. **Not done, by this seat's rules:** no installer run by hand, no `launchctl`, `xcodebuild` or
   `simctl`, no Docker build, no network in tests, no `make lock`, no commit or push.
9. **Tree:** clean apart from this file.

## Verdict
MINOR (no BLOCKING; eight MINOR, M1–M8; one K.9, K1; three risks, R1–R3)

I recommend fixing M1, M3 and M4 in this wave. M1 is the wave's own fix for W-126, and parts of it
hold less than the ADR says. M3 must be fixed before the protocol is used with a real person. M4 is
the list the closure's security seat will start from.

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/refresh.py:102-113`, `:1303-1317`; `src/app/adapter/nightly.py:270`, `:306-309`. **The cycle's own limit is weaker than D-154's amendment says, in four ways.**

  The amendment (`docs/decisions.md:2431-2441`) and W-126's FIXED row say the cycle "stops itself
  at 27 minutes", so "an engine killed hard no longer leaves it holding the lock". The limit is a
  `threading.Timer` that calls `print` and then `os._exit(5)`.
  1. **It cannot fire while a call holds the GIL.** The probe patched `refresh` to run one
     backtracking regex, with the limit at 1 s. The process exited with code 5 after **5.8 s**, the
     moment the regex returned. A call that never returns is never stopped. A regex over upstream
     text, a large `json.loads` or a large sort are such calls. The constant's comment says
     "whatever it is doing" (`refresh.py:96`).
  2. **Firing late can abort Python.** In the probe's first run, the main thread finished just as
     the late timer ran, and the process died with **SIGABRT, rc -6, after 11.3 s**. The timer's
     line was in stdout. The likely cause is the timer's buffered `print` racing the interpreter's
     shutdown. On the owner's Mac that is a crash report, and `/health` would say "crashed".
  3. **The new process group leaves launchd's cleanup.** `start_new_session=True` puts the cycle
     in a session of its own. The service's plist sets no `AbandonProcessGroup`
     (`scripts/install_engine_service.sh:86-96`). Its default, from `man 5 launchd.plist`: "When a
     job dies, launchd kills any remaining processes with the same process group ID as the job."
     Before this wave the cycle was in the engine's group, so an engine killed hard under the
     service (D-170) took its cycle and reader with it. Now they run on, holding the lock, for up
     to 27 minutes. This is from the man page. I could not measure it, since `launchctl` is
     refused to this seat.
  4. **The group kill runs only while the child is alive** (`nightly.py:306`). The probe: a cycle
     starts a grandchild that inherits its output, then calls `os._exit(5)`. The engine waited out
     its timeout and reported **"killed"**, not "timed out". **The grandchild was still alive.**
     Today's reader has its own pipes, so this is not reachable today. It is W-130's own class:
     "reachable the day it does".

  **The fix:**
  1. Add a backstop no GIL can delay: `signal.setitimer(signal.ITIMER_REAL, …)` a minute after the
     timer, with SIGALRM's default action. The kernel then ends the process. Map that exit in
     `nightly.CODE_NAMES`.
  2. Write the timer's line with `os.write(1, …)`, not `print`.
  3. Let the cycle leave when its parent is gone: the timer thread can poll `os.getppid()`. Or say
     in the amendment that a hard engine death now leaves the cycle running for up to 27 minutes.
  4. On a drain timeout, call `killpg` whether or not the child has exited. A group id is not
     reused while any member lives, so this is safe.

  Pin (1) and (4) with tests; the probes above are ready-made shapes.

- **M2** `docs/plans/m18-wave-6-plan.md:26`, `:56`; `docs/plans/m18-plan.md:35`, `:128`. **#88, the licence table, is in the plan and not in the wave, and no amendment moves it.**

  P4's check reads: "A licence table for every served source, with options and their cost to the
  product". The milestone's W6 criterion includes "The licences are ruled." The wave delivered #91
  only. #88 is open in M18. The valve amendment (`m18-plan.md:220-223`) moves P5, not #88. The new
  list leans on the table: retired INV-21 is "a licensing rule, with the licence table (#88)"
  (`docs/security-invariants.md:201`). The ruling is the owner's, but the table and its options are
  the agent's work. **The fix:** write the table, or amend the plan to move #88, with the reason.

- **M3** `docs/research/stranger-first-use-protocol.md:45-47`, `:84-90`, `:98-99`, `:38`. **The protocol publishes the strangers' questions without asking them for that, and it opens the engine to the network without closing it after.**
  1. **Consent.** §6 writes the kept questions, as typed, to `scripts/router_probe/stranger_heldout_<date>_questions.json`.
     That is a committed file, and the repository is **public** (`gh repo view`: `PUBLIC`). §7
     keeps the questions off #91 "since the issue is public". The script read to the person says
     only "at the end you choose which notes I may keep". Free text can carry anything about a
     person. **The fix:** say in both languages that the kept questions are published in a public
     repository, and ask for that. Or keep the set out of git: a git-ignored local file, measured
     locally.
  2. **The network.** §2 starts the engine with `--lan` and never says to close it.
     D-171 note 7 makes `--no-lan` the one control. **The fix:** add "run the installer with
     `--no-lan` after the session" to §5.

- **M4** `docs/security-invariants.md:68`, `:85`, `:192`, `:160-161`, `:25-26`. **The list has one row whose test does not hold it, wrong ids in two places, a wrong count, and a pointer to a record that does not exist.**

  The closure's security seat starts from this list, so its words must be exact.
  1. **INV-38 is held for "others" only.** The row says the refresh refuses a directory "that
     group or others can write". The one cited test uses mode `0o777`
     (`tests/unit/test_refresh.py:1627-1639`). Mutant: `mode & stat.S_IWOTH` alone
     (`refresh.py:615`). The test **passed**. No test holds the group half.
  2. **INV-3's source says "INV-32 merged here".** INV-32 is the strict-boot row (`:55`). The
     merged id is INV-8.
  3. **INV-8's description is not what INV-8 was.** The retired table says "Every remote fetch is
     https". M1 to M5 called it "Only 3 documented endpoints, no scraping (D-101)"
     (`docs/reviews/m1-security-review.md:27`, `m4-security-review.md:84`).
  4. **"Six more hold only in part" is wrong.** Seven rows say "Partial": INV-27, -62, -63, -67,
     -76, -6 and -78.
  5. **"M18-W6 mutated ten more (its wave record)" points at nothing.** No file in the range holds
     the ten mutants. Only the commit message `f984977` lists them.

  **The fix:** add a test with a group-writable directory (`0o770`). Correct items 2–4. Put the
  ten mutants, with their results, in the wave's close record and point the sentence there.

- **M5** `tests/unit/test_security_invariants.py:34`, `:36`, `:89-95`. **The gate skips a row or a citation it cannot parse, so a parsing slip fails open.**
  1. **A row ROW does not match is silently dropped.** ROW needs the line to end in `|`. Probe: a
     new last row `| INV-84 | … | \`tests/unit/test_no_such_file.py::test_nothing\` | ` with a
     trailing space, and the count left at 71. The gate: **6 passed**. The row and its missing test
     were never read. The same row without the space fails, as it should. "Skipped" fires only
     below the highest number, and the count is the only backstop for a new row.
  2. **A citation TEST does not match is silently dropped** if a readable one sits beside it.
     Probe: `` `tests/unit/test_nope.py::TestX::test_gone` `` added to INV-11's cell. The gate: **6
     passed**. A class path or a parametrized id is never checked.

  **The fix:** in "The list", any line that starts with `| INV-` and does not match ROW is a
  finding. In a cell, any backticked `tests/` or `ios/` path that TEST does not match is a finding.
  Pin both with these two probes.

- **M6** `tests/unit/test_security_surface.py:78-79`, `:108-127`. **Two of the four closed gaps are narrower than their rows say.**
  1. **INV-11 misses the usual Swift trust-all.** The pattern lists
     `.performDefaultHandling.*serverTrust`. That is the safe default, not a bypass. Probe: in
     `EngineClient.swift`, a delegate method that calls `completionHandler(.useCredential, …
     URLCredential(trust: $0) …)`. `test_nothing_turns_tls_verification_off`: **1 passed**.
     `EngineClient.swift` may use the network (D-126), so the compiler gate does not refuse it
     either. **The fix:** refuse `URLCredential(trust:` and `.useCredential`. Pin the probe's line
     in the planted test.
  2. **INV-77 reads static imports and declared dependencies only.** `importlib.import_module`
     and a model package pulled in by a dependency (it would sit in the locks) both pass. The fix
     is small: read the three locks too, or narrow the row to what the check reads.

- **M7** `pyproject.toml:1-35`; `tests/unit/test_dependency_locks.py:120`; `Makefile:80-81`; `Dockerfile:16-17`; `scripts/install_engine_service.sh:121-122`; `AGENTS.md:15`. **"Every install … resolves nothing else" (INV-81) holds for the packages, not for the build backend. The check reads one spelling, and no ADR records the new install path.**
  1. **The build backend is not locked.** `pyproject.toml` has no `[build-system]` table. So each
     `pip install --no-deps -e .` (and the Dockerfile's `--no-deps .`) builds in isolation, with
     pip's default `setuptools` fetched at its newest and not hash-checked. Evidence: this seat's
     venv holds the project as an editable install, and holds no `setuptools`. The installed
     environment is locked; the code that runs at install time is not.
  2. **The install check reads one spelling.** It finds `pip install` and `$(PIP) install`
     (`:120`). Probes added to the Dockerfile, each beside the locked install:
     `RUN pip3 install requests`, and `RUN python -m pip --no-cache-dir install requests`. The
     test: **16 passed**, both times.
  3. **No ADR records the change.** It changes how D-170's release and D-116's image are built. It
     adds a dev tool (`uv`) and moves pyarrow to an extra, and `AGENTS.md` §1 was edited to say so.
     The profile's §4 flags an `AGENTS.md` edit with no ADR. The `Dockerfile` is a K.10 surface
     (`AGENTS.md` §6: "changes need DevOps review"). The plan puts the CI lines to the owner, but
     says nothing of the Dockerfile.

  **The fix:**
  1. Add `[build-system]` with a pinned backend. Then either lock it and install with
     `--no-build-isolation`, or state the limit in INV-81 and `scripts/lock_dependencies.py`.
  2. Match any `pip`/`pip3`/`uv pip` line that holds `install`, wherever the subcommand sits.
  3. Write a short ADR, or amend D-170 and D-116, for the locks, `--no-deps` and the `ingest`
     extra. Name the Dockerfile change in the PR as needing the owner's K.10 review, beside the CI
     diff.

- **M8** `src/app/workflows/standings.py:23`; `src/app/workflows/access.py:45-101`; `src/app/adapter/nightly.py:14-19`, `:72-73`; `src/app/clients/arena_slices.py:20-21`; `tests/unit/test_arena_slices.py:684-687`. **W-125 is marked FIXED for "the source parsers", but the server still loads one, and four comments still say the old thing.**
  1. **`app.workflows.access` is a source parser, and the server loads it.** It holds
     `parse_metadata`, `store` and `link` for Epoch's downloaded `model_metadata.csv`. The server
     imports it through `standings.py:23`, for `served()` alone. Measured: `app.workflows.access` is
     in `sys.modules` after `import app.adapter.main`. The new test refuses `app.clients.*` and
     `ingest` only. This is W-125's own class, and the plan's check says "no client and no ingest
     module".
  2. **Stale text that now says the opposite of the code:**
     1. `nightly.py:14-19`: "The serving process DOES load the source PARSERS and their HTTP client
        library … Untangling that chain is W-125."
     2. `arena_slices.py:20-21`: "the serving process imports `app.clients.*` (W-125)".
     3. `test_arena_slices.py:684-687`: "The server imports `arena_slices` itself (through
        `rank.SOURCE_ATTRIBUTION`)".
     4. `nightly.py:72-73`: "A real cycle takes 6-9 seconds … Thirty minutes is not a prediction of
        a slow night". The D-154 amendment says this is no longer true.

  **The fix:** move `served()` (and what it needs) to a module with no parser. Add
  `app.workflows.access`'s parse side to the refused list, or narrow the ledger row. Then correct
  the four texts.

### PASS (what looks good)

- **Every new test fails without its fix.** There are no separate red commits, so I removed each
  fix in place:

  | mutant | test | result |
  |---|---|---|
  | `rank.py` imports the client tables again | `test_nightly_refresh.py:406` | failed |
  | `plans.py` imports `ingest` again | `:406` | failed |
  | `registry.py` imports `app.clients.protocols` | `:406` | failed |
  | no `start_new_session` | `test_nightly_refresh.py:203` | failed, 30.5 s (W-130's 30 s) |
  | no `killpg` | `:203` | failed, 30.5 s |
  | `bounded_get` ignores the budget | `test_fetch_bounds.py:199`, `:211` | failed |
  | the budget refuses a new fetch but does not cut an open one | `test_fetch_bounds.py:211` | failed |
  | the limit timer set to 10⁶ s | `test_refresh.py:1853` | failed |
  | `main` without `cycle_budget` | `test_refresh.py:1876` | failed |
  | code 5 not named "timed out" | `test_nightly_refresh.py:237` | failed |
  | the limit at 31 minutes | `test_nightly_refresh.py:248` | failed |
  | INV-31 `allow_credentials=True` | `test_api_config.py` (cited) | failed |
  | INV-34 the 500 without `nosniff` | cited tests | failed |
  | INV-38 group-writable allowed | `test_refresh.py:1627` | **passed: M4**(1) |
  | INV-46 the bundle follows redirects | `test_epoch_bundle_fetch.py` (cited) | failed |
  | INV-55 the accessibility guard off | `test_refresh.py` (cited) | failed |
  | INV-9 the page cap silent | `test_arena_client.py` (cited) | failed |
  | INV-70 the `select` guard removed | `test_ios_client_contract.py:806` | failed |
  | INV-70 the guard moved below `routingGate.invalidate()` | `:806` | failed |
  | INV-81 `--require-hashes` removed from `make install` | `test_dependency_locks.py:115` | failed |

- **A spent budget really carries (D-156).** I ran `refresh()` on a copy of `advisor.db` inside
  `cycle_budget(0.0)`. 41 sources failed with "the refresh cycle's time budget is spent". All
  carried at age 3.9 days, none expired, and the cycle ended **exit 1, "unchanged"**. The live copy
  was untouched. Every download goes through `bounded_get` (`protocols.py:114`): aider, arena (its
  429 retries included), arena slices, the Epoch bundle, litellm, openrouter and swebench. Arena's
  429 sleep is not counted, but it is at most 30 s per page, well inside the 7-minute gap to the
  limit.
- **The process-group kill is right on macOS.** Measured on this Mac:
  1. `killpg` on a group whose leader is an unreaped zombie and a member is alive: no error, and
     the member died.
  2. The same group with only the zombie: `PermissionError` (EPERM). So suppressing it is correct.
  3. After the reap: `ProcessLookupError`.

  `killpg` runs only while `returncode` is None. A group id is not reused while a member lives, so
  pid reuse cannot aim it at a stranger's group. The gap is the other side: **M1**(4).
- **The timer cannot fire in a process it should not.** The only callers of `refresh.main` are the
  `-m` entry point and in-process tests. `main` cancels the timer in `finally` on every path. The
  tests that call it in process (`test_refresh.py:559`, `:610-616`, `:1893`;
  `test_epoch_bundle_fetch.py:167-169`) finish in well under 27 minutes. The `_Cycle.ends` budget is
  restored on exit (`test_refresh.py:1895`).
- **The import move is clean.** The moved names are re-exported with `X as X` where anything imports
  them. `SourceError` is one class everywhere, so every `except SourceError` still catches. The
  conftest's `build_mod.ARENA_SLICES` patch acts where `build.py` reads it (`build.py:411`, `:739`),
  as before. No test patches a moved constant on its old module.
- **The locks are consistent.**
  1. The shared packages have the same versions and hashes in all three locks. The only difference
     is `pyarrow`, which is not in `serve`.
  2. This venv equals `dev.lock`, package for package. `pip` is excluded from `freeze`; `colorama`
     is Windows-only.
  3. The staleness hash covers `requires-python`, the dependencies and each lock's extras. That is
     everything in `pyproject.toml` that uv's resolution reads here (there is no `[tool.uv]`).
  4. A hand-edited transitive pin passes the tests, but `--require-hashes` would refuse it at
     install, so it fails closed.
- **The invariants list is thorough.** 71 rows, 12 retired ids, 6 gaps on 7 open issues (#85,
  #60, #107, #110, #121, #122, #123). Every M16 and M17 closure row is folded in. No `INV-25`
  or higher was used anywhere before this wave, so the new numbers collide with nothing.
- **Discipline.** All 7 commits carry `GP-Task: M18-W6`. None carries `Co-Authored-By` or
  "Generated with". One new `noqa` (`S603`, with its reason, on the lock script's own `uv` call,
  `scripts/lock_dependencies.py:80`), and no new `type: ignore`.
  The P5 valve is recorded in both plans (`m18-plan.md:220-223`; wave plan `:63-65`). P5 was not
  half-done.

## Producers of hardened invariant(s)

| producer | invariant | citing test | gap |
|---|---|---|---|
| the server's import chain: `main` → `subscribe` → `plans` → `run_records`; `rank` → `board_tables`; `standings` → `access`; `registry` | INV-43: the server loads no client, ingest module or HTTP client | `test_nightly_refresh.py:406` | `access` is a parser (**M8**) |
| `bounded_get` (`protocols.py:114`), through every client listed under PASS | INV-42: the fetches share a budget | `test_fetch_bounds.py:199`, `:211`; `test_refresh.py:1876` | Arena's 429 sleep is uncounted (at most 30 s; accepted) |
| the limit timer (`refresh.py:102-113`) | INV-42: the cycle stops itself | `test_refresh.py:1853`; `test_nightly_refresh.py:237`, `:248` | GIL, shutdown abort, launchd group (**M1**(1)–(3)) |
| the engine's kill (`nightly.py:281-311`) | INV-42, W-130: the kill takes the group | `test_nightly_refresh.py:186`, `:203` | the child exited first (**M1**(4)) |
| `make install` (`Makefile:80-81`), the release (`install_engine_service.sh:121-122`), the image (`Dockerfile:16-17`) | INV-81: every install takes its lock | `test_dependency_locks.py:60`, `:64`, `:78`, `:87`, `:97`, `:115` | build backend; spellings (**M7**) |
| CI installs (`ci.yml:46`, `:104-105`; `contract-tests.yml:87`, `:107`) | INV-81 | none: the owner's surface | **K1**; the proposed CI diff |
| `.github/workflows/*.yml` | INV-10: CI reads only | `test_security_surface.py:59`, `:66` | none found |
| httpx clients (`protocols.py:151`); Swift session delegates | INV-11: TLS is never off | `test_security_surface.py:86`, `:94` | Swift trust-all (**M6**(1)) |
| imports under `src`, `pyproject.toml` | INV-77: no model in the engine | `test_security_surface.py:119`, `:131` | dynamic import, the locks (**M6**(2)) |
| `ContentView.swift:927` (`select`) | INV-70: only a listed surface becomes `task` | `test_ios_client_contract.py:806` (`:909-914`) | none |
| `docs/security-invariants.md` | W-131: one list, each row cited | `test_security_invariants.py:127`, `:131`, `:155`, `:165`, `:174`, `:181` | unread rows and citations (**M5**); INV-38 (**M4**) |

## Acceptance criteria evidence

W6 has no REQ-ID; its criteria are the Stage 5.1 prerequisites (`m18-plan.md:35`). The new tests
cite their W-, D- and issue ids in docstrings, for example `test_nightly_refresh.py:204` ("W-130
(M18-W6, #90)") and `test_dependency_locks.py:1` ("M18-W6 (#35, #26)"). Per phase
(`m18-wave-6-plan.md:50-57`):
- **P1, #89** → `docs/security-invariants.md` → `test_security_invariants.py:127`, `:131`, and the
  four planted-list tests `:155-186`. Four gaps closed: `test_security_surface.py:59`, `:86`, `:119`;
  `test_ios_client_contract.py:909-914`. Mutation sample: mine, 9 of 10 killed. **Met, with M4,
  M5, M6.**
- **P2, W-125** → `run_records.py`, `board_tables.py`, `registry.py:20-35` →
  `test_nightly_refresh.py:406` (new assertion `:429-435`). Mutants killed. **Met, with M8.**
- **P2, W-126** → `protocols.py:57-93`, `:142`; `refresh.py:88-113`, `:1303-1317` →
  `test_fetch_bounds.py:199`, `:211`; `test_refresh.py:1853`, `:1876`; `test_nightly_refresh.py:237`,
  `:248`. The carry probe: exit 1, 41 sources carried. **Met, with M1.**
- **P2, W-130** → `nightly.py:270`, `:306-309` → `test_nightly_refresh.py:203`; red at 30.5 s
  without the fix. **Met, with M1(4).**
- **P3, #35 and #26** → `requirements/*.lock`, `scripts/lock_dependencies.py`, `Makefile:77-85`,
  `install_engine_service.sh:118-123`, `Dockerfile:12-17`, `pyproject.toml:21-29`, `:46` →
  `test_dependency_locks.py:54-127`; `--check` PASS; the venv equals `dev.lock`. The CI diff is
  for the PR. **Met, with M7.**
- **P4, #88** → nothing in the range. **Not met, and not amended: M2.**
- **P4, #91** → `docs/research/stranger-first-use-protocol.md`. **Met in form, with M3.**
- **P5** → moved to M19 (`m18-plan.md:220-223`); gaps G-1 to G-3 name #85, #60, #107, #110.
  **Met by the valve.**

## Every file in the diff

`git diff --stat 8a18324 cf83fea`, 37 files. I read every file's diff in full. For the three lock
files I read the headers and the pins, and checked the rest by script.
1. **Records (10).**
   1. `.language-allow`: the protocol's Turkish script, with a reason.
   2. `AGENTS.md`: §1's tech stack names the locks and the `ingest` extra (**M7**(3)).
   3. `docs/decisions.md`: D-154's amendment, the three limits and the group kill (**M1**).
   4. `docs/plans/m18-plan.md`: the W6 valve amendment.
   5. `docs/plans/m18-wave-6-plan.md`: new, the working plan (**M2**).
   6. `docs/research/stranger-first-use-protocol.md`: new (**M3**).
   7. `docs/security-invariants.md`: new, 71 rows (**M4**).
   8. `docs/warnings.ledger.md`: W-125, W-126, W-130 and W-131 to FIXED (**M1**, **M8**).
   9. `pyproject.toml`: pyarrow to `ingest`, also in `dev`; `uv` in `dev` (**M7**(1)).
   10. `Dockerfile`: the serving lock, then `--no-deps .` (**M7**).
2. **Locks and install (5).** `requirements/dev.lock` (72 pins), `ingest.lock` (24), `serve.lock`
   (23); `Makefile` (install from the lock, the `lock` target); `scripts/install_engine_service.sh`
   (the release takes `ingest.lock`).
3. **Scripts (1).** `scripts/lock_dependencies.py`: new, writes and checks the locks.
4. **Engine (14).**
   1. `nightly.py`: the new session, the group kill, code 5.
   2. `arena.py`, `arena_slices.py`, `epoch.py`, `swebench.py`: definitions moved out and
      re-exported.
   3. `protocols.py`: `SourceError` re-exported; the cycle budget.
   4. `access.py`, `plans.py`, `rank.py`: import from the new modules.
   5. `board_tables.py`, `run_records.py`: new, client-free.
   6. `ingest.py`: the record types re-exported.
   7. `refresh.py`: `EXIT_TIMED_OUT`, the two limits, the timer.
   8. `registry.py`: `split_harness` and `UNKNOWN_HARNESS`.
5. **Tests (7).**
   1. `test_dependency_locks.py`: new (**M7**).
   2. `test_fetch_bounds.py`: two budget tests.
   3. `test_ios_client_contract.py`: the INV-70 pin.
   4. `test_nightly_refresh.py`: three W-126/W-130 tests; the server-import test widened.
   5. `test_refresh.py`: two limit tests.
   6. `test_security_invariants.py`: new, the gate (**M5**).
   7. `test_security_surface.py`: new, INV-10, INV-11, INV-77 (**M6**).

## K.8 contract drift check

`git grep -n` at `cf83fea`, for the wave plan's symbols (`m18-wave-6-plan.md:72-79`), the
milestone's engine symbols (`m18-plan.md:154-167`) and what this wave added:
```
src/app/adapter/nightly.py:74:TIMEOUT_SECONDS = 30 * 60.0
src/app/adapter/nightly.py:265:            proc = await asyncio.create_subprocess_exec(
Makefile:87:install: $(VENV)/.installed  ## Stage 0: create the venv, install the project, write .gp/installed
pyproject.toml:25:ingest = [
pyproject.toml:28:dev = [
src/app/workflows/ingest.py:95:def _store_scores(
src/app/workflows/schema.py:404:def open_readonly(path: str | Path) -> sqlite3.Connection:
src/app/workflows/standings.py:34:HIGHER_IS_BETTER = frozenset({"elo", "ips", "% correct", "% resolved", "% pass_rate_2", "ECI"})
src/app/clients/protocols.py:17:from app.workflows.run_records import SourceError as SourceError
src/app/clients/protocols.py:65:def cycle_budget(seconds: float) -> Iterator[None]:
src/app/clients/protocols.py:80:def cycle_ends() -> float | None:
src/app/workflows/ingest.py:26:from app.workflows.run_records import RunContext as RunContext
src/app/workflows/ingest.py:27:from app.workflows.run_records import SourceReport as SourceReport
src/app/clients/arena_slices.py:44:from app.workflows.board_tables import ARENA_SLICES as ARENA_SLICES
src/app/clients/arena_slices.py:45:from app.workflows.board_tables import ArenaSlice as ArenaSlice
src/app/clients/epoch.py:19:from app.workflows.board_tables import EPOCH_ATTRIBUTION as EPOCH_ATTRIBUTION
src/app/clients/swebench.py:15:from app.workflows.registry import split_harness as split_harness
src/app/workflows/refresh.py:90:EXIT_TIMED_OUT = 5
src/app/workflows/refresh.py:95:FETCH_BUDGET_SECONDS = 20 * 60.0
src/app/workflows/refresh.py:99:CYCLE_LIMIT_SECONDS = 27 * 60.0
scripts/lock_dependencies.py:33:LOCKS: dict[str, tuple[str, ...]] = {"serve": (), "ingest": ("ingest",), "dev": ("dev", "ingest")}
```
1. `_store_scores` (was `:117`) and `install:` (was `:81`) moved lines only, because lines above
   them were removed or added. Their signatures are unchanged.
2. Every moved public name is re-exported from its old module, so no import path changed.
3. `refresh.py`'s exit codes gain 5. `nightly.CODE_NAMES` restates it, and its test pins the pair.
4. `/v1` is unchanged: no route or field moved.
5. The clients now import three `app.workflows` modules, but clients already imported
   `app.workflows.schema` and `registry` before (`deepswe.py:14`). D-001 is about vendor SDKs, and
   none moved.

**Verdict: OK.** No symbol drifted.

## K.9 candidates spotted outside this wave's scope

- **K1** `.github/workflows/ci.yml:102-106`. **CI's dependency audit reads a fresh install, not the locks that deploy.** The step runs `pip install -e .` and then `pip-audit`, so it audits whatever was newest that day. After #35 the versions that deploy are in `requirements/serve.lock` and `ingest.lock`. `pip-audit -r requirements/serve.lock -r requirements/ingest.lock --require-hashes` would audit those exactly. This is the owner's file, so it belongs in the CI diff the PR proposes. Enhancement.

## Risks queued to next M

- **R1** `requirements/*.lock`. **The universal lock has not met CI's Pythons.** It was installed on this Mac (Python 3.14, arm64), and the author records one image build on 3.11. CI's Linux jobs (3.12 and 3.14, `ci.yml:30-46`) still resolve `.[dev]` fresh. When the owner adopts the CI diff, a pinned version with no wheel for one of those Pythons, and no sdist that builds, fails that job. What would show it: the first CI run on the lock.
- **R2** `scripts/install_engine_service.sh:115-123`. **The locked release install runs in no test.** `test_engine_service.py:104` always passes `--no-venv`, and the real path needs the network. Its first run is the owner's next deploy after this merges. What would show it: that deploy's "FAIL: the release's venv".
- **R3** `src/app/workflows/refresh.py:1236-1250`. **The limit can fire between the publish and the record.** `candidate.replace(target)` publishes. The record, with this cycle's arrivals, is written a few lines later. A timer firing in between leaves a published artifact, no record, and `/health` saying "timed out". The next cycle then measures carry ages from older arrivals, which D-156 allows ("can only overstate the age"). The engine's kill had the same window. What would show it: a "timed out" night whose artifact fingerprint changed.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-04 · Commit range: `8a18324..cf83fea`*
