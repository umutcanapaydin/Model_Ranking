---
record_type: review
id: issue-32-rereview
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# #32 re-review: the service runs its own deployed copy of `origin/main`

**Reviewer:** a new independent seat, Code-Reviewer and Tester in one pass. Policy was read from
`.claude/agents/Code-Reviewer.md`, `.claude/agents/Tester.md`, `.agents/rules/practices.md`,
`.agents/rules/review-seats.md` and `docs/warnings.ledger.md` W-096. The range touches none of
these files.
**Independent:** yes. I wrote none of the code in the range and not the first review.
**Date:** 2026-09-25
**Commit range:** `origin/main..4162caa`. The fix under review is `16440e0..4162caa`: `65504d2`
has the red tests and `4162caa` has the implementation.
**Acceptance criteria:** issue #32 "Done when", and the owner's ruling of 2026-09-25 (issue
comment): the service runs a deployed copy of `origin/main` under
`~/Library/Application Support/model-ranking/engine`.

Constraints I kept: nothing was installed, loaded, bootstrapped, booted out or kickstarted, and
nothing was written under `~/Library`. The deploy was run only as `--deploy-only` into scratch
directories under the session scratchpad, and those directories were deleted afterwards. One
engine was started by hand from the scratch release and then stopped. Afterwards I checked:
`pgrep -f "uvicorn app.adapter.main:app|app.workflows.refresh"` found nothing, no process listened
on :8080, `~/Library/LaunchAgents` had no model-ranking plist, and `git status --short` was empty.

## Verdict
MINOR. Both blocking findings of the first review are answered by construction.

- **B1:** launchd and the processes it starts no longer read anything under `~/Desktop`.
- **B2:** the nightly refresh child runs the release it was started from. I measured this: the
  child's module path, working directory and interpreter all resolve into
  `releases/<sha>`, even when the engine is started through the `current` link.

The suite is green: 1334 passed. The red to green sequence is real: 8 of the 12 tests fail at
`65504d2` and pass at `4162caa`.

Four MINORs remain:
- the installer's failure path leaves a broken service behind;
- the release installs dependency versions the suite never ran;
- the installer's success check does not check which build answered;
- the first review's M7 (string-match tests) is not answered, and the new deploy code has the
  same gap. 11 of 16 in-place mutants survive.

No launchd run proves the "Done when" criterion. This seat may not do that run. The owner's first
install after merge is the proof (**R1**).

## The first review's findings and their state

| id | first review said | state now | evidence |
|---|---|---|---|
| B1 | launchd's bash cannot read a script under `~/Desktop`, and git cannot `getcwd()` there (W-096) | **Answered by design** | The plist runs `/bin/bash` on a wrapper in Application Support. The wrapper execs the release's launcher. The logs are in `~/Library/Logs`. No git runs under launchd (`install_engine_service.sh:33-64`, `engine_service.sh:35-44`). Tests: `tests/unit/test_engine_service.py:56-76`. Probe: a real release contains no reference to the checkout path (`grep -rIl` over `releases/`, `.venv` included, found nothing). I started the launcher with `env -i HOME=… PATH=/usr/bin:/bin:/usr/sbin:/sbin` from `/tmp`. The process's cwd was `releases/6834c7d`, and `/health` answered `"build":"release-6834c7d","refresh":"scheduled"`. The release venv links to `/opt/homebrew/opt/python@3.14/bin/python3.14`, outside Desktop. It is the same stable path as the dev venv, even though the installer passes the versioned `Cellar` path from `sys._base_executable`. Not proven under launchd; see **R1**. |
| B2 | the nightly refresh child runs whatever is checked out | **Answered** | Measured with the release's own python, started through `current`: `nightly._SRC` = `…/releases/6834c7d/src`, `_REPO` = `…/releases/6834c7d`, and `sys.executable` = `…/releases/6834c7d/.venv/bin/python`. So a running engine's child keeps its own release after `current` is swapped. The deploy takes `origin/main` whatever is checked out (`test_engine_service.py:108-119`). The mutant that deploys `HEAD` instead is killed (m12). |
| M1 | tests pass `GIT_*` from a hook into scratch git | **Answered** | `test_engine_service.py:36` (`_CLEAN_GIT_ENV`) is used by all five subprocess helpers (`:41, :81, :105, :118, :135`). |
| M2 | bootout then an immediate bootstrap races launchd | **Answered** | `ios/app.sh:145-150` and `install_engine_service.sh:129-130` use `kickstart -k`. The mutant that restores stop+start is killed (m03). |
| M3 | with the service installed and the checkout on a branch, `restart` stops the engine and starts none | **Answered by design** | There is no branch gate any more: the service always runs the deployed release. What remains is the ruling's intended consequence: while the service is installed, `app.sh` cannot run the checkout's engine. `app.sh:76` says so ("the deployed main"). |
| M4 | the installer kills every engine and can leave the owner with none | **Partly answered** | It kills only a listener that is this project's engine (`install_engine_service.sh:115-122`), and it unloads the service if `/health` does not answer (`:144-148`). The failure path still leaves the owner with no engine, and it leaves a broken service installed: see new **M1**. The listener check has no test (m14 survives). |
| M5 | the service is bound to whichever checkout ran the installer | **Answered by design** | The service runs `$DEPLOY/current`, not a checkout. What remains is the first-artifact copy, which comes from wherever the installer runs: see **N3**. |
| M6 | the log is unbounded, and a failing start loops every minute | **Answered in part** | The launcher rotates the log at start once it passes 10 MB (`engine_service.sh:26-31`; test `:165-174`; mutant m15 killed), so each restart of a failure loop keeps the log bounded (at most about 2 × 10 MB). The failure paths still exit at once and restart every 60 s, and a long run is not rotated: see **N7**. |
| M7 | the tests for the app.sh routing, the remover and the launcher environment are string matches; 6 of 10 mutants survived | **Not answered** | 5 of those 6 still survive (m01, m02, m04, m05, m06). The detached-HEAD mutant is moot now that there is no branch gate. The fix commit does not mention M7. Carried as new **M4**. |
| N1 | paths go into the plist and the wrapper unescaped | Open | `install_engine_service.sh:38-40, 50-60`, unchanged in kind. See **N8**. |
| N2 | `--service` honours `MODEL_RANKING_REPO` | Answered | A tree without `RELEASE` is refused in service mode (`engine_service.sh:37-41`; test `:138-144`; mutant m07 killed). |
| N3 | the gate trusted the branch name `main` | Answered | The deploy takes `origin/main` (`install_engine_service.sh:69-75`). |
| N4 | the issue body describes the old design | Open | See **N8**. |
| N5 | the remover does not refuse an empty `HOME` and does not confirm the port is free | Partly answered | `HOME` is now checked (`remove_engine_service.sh:7`). The port-free confirmation is still missing. See **N8**. |
| K1 | an engine started by hand runs the checkout's code in its nightly child | Dispositioned | The ruling keeps it for the development engine. It is noted at `ios/app.sh:80-81`. |
| R1 | it was unknown whether python still reads Desktop under launchd | Superseded | Nothing the service runs is under Desktop any more. The new risk is the post-merge proof (**R1** below). |

## Findings

### BLOCKING
- none

### MINOR

- **M1** `scripts/install_engine_service.sh:89, 144-148`, `ios/app.sh:32, 75-78`: **a failed
  install or upgrade leaves a broken service installed and no engine.**

  When `/health` does not answer within 60 s, the failure path runs `bootout`. It does not
  remove the plist or the wrapper, and it does not undo the `current` swap, which ran at `:89`
  before anything was verified. The consequences:
  - At the next login, `RunAtLoad` starts the broken release again. `KeepAlive` then retries it
    every 60 s, with no end, and each try adds a line to the launchd log, which nothing rotates.
  - `ios/app.sh:32` decides that the service is installed by checking that the plist exists. So
    every `./ios/app.sh up` goes through the broken service (`:75-78`) and never starts the
    checkout's engine. The only way out is `remove_engine_service.sh`, and the failure message
    does not name it.
  - For an upgrade, the previous release is still on disk and was serving a moment before. The
    failure path does not roll back to it, so a bad `main` becomes "no engine" instead of "the
    old engine".

  One way to reach this path for certain: `origin/main` is still `6834c7d` today, and its tree
  has no `scripts/engine_service.sh` (measured in the scratch release). An install run before
  #32 merges deploys a release without the launcher. The wrapper's `exec` then fails and the
  service ends up in the state above. The deploy does not check that the release contains the
  launcher before it swaps `current`.

  *Direction:* check that `$rel/scripts/engine_service.sh` exists before the swap. On failure,
  point `current` back at the previous release and kickstart it when there is one; on a first
  install, remove the plist and the wrapper. Name `remove_engine_service.sh` in the message.

- **M2** `scripts/install_engine_service.sh:79`: **the release installs fresh, unpinned
  dependencies from PyPI, so the service runs versions the suite never ran against.**

  `pip install -e "$rel"` resolves the `>=` ranges in `pyproject.toml` at deploy time. I compared
  the scratch release's `pip freeze` with the development venv's, which is the one the gate runs.
  11 packages differ: starlette 1.6.0 → 1.7.0, uvicorn 0.52.1 → 0.54.0, pydantic 2.13.4 → 2.13.5,
  pydantic_core, anyio, click, idna, watchfiles, websockets, python-dotenv, typing-inspection.

  B2's point was that the service runs reviewed and tested code. The code is now reviewed, but
  the dependency set it runs on was never tested. A breaking upstream release would first show up
  as a failed redeploy, and then M1's outage follows. The project has no lock file, so
  `make install` has the same property. The service is the first place where it runs unattended.

  *Direction:* install with `-c` against the dev venv's `pip freeze`, which the gate just ran.
  Or record the freeze in the release and print any difference.

- **M3** `scripts/install_engine_service.sh:136-141`, `ios/app.sh:149-150`: **the success check
  accepts any answer from `/health`, not the release that was just deployed.**

  After `kickstart -k`, the installer reports "engine: UP" on the first 200 from :8080, whatever
  the build. `app.sh restart` does the same. `ios/app.sh:39-45` records this project's own
  incident: a dying engine went on answering `/health` and was taken for a new one. L.7's lesson
  is that the build stamp is the only thing that tells you which engine you got. The installer
  prints the stamp but does not check it.

  I did not measure whether `kickstart -k` returns before the old process stops listening,
  because this seat may not run launchd. That is the reason to check the stamp and not rely on
  the timing.

  *Direction:* wait for `"build":"release-$sha"`.

- **M4** `tests/unit/test_engine_service.py:177-197` (carries the first review's M7): **the
  app.sh routing, the remover, the launcher's environment and preflight, and most of the new
  deploy logic are unguarded.** 11 of 16 in-place mutants survive (table below). They include:
  - m10: a same-sha redeploy runs `rm -rf` on the finished, live release and rebuilds it. That is
    the one code path that would delete a running engine's code.
  - m11: `RELEASE` is written before the venv, which breaks the "RELEASE written last"
    invariant.
  - m08 and m09: the pruning guard and the keep count.
  - m13: the failure path no longer unloads the service.
  - m14: the installer kills any listener on :8080.

  All of these can be tested offline:
  - Stub `launchctl` and `curl` on `PATH` and use a scratch `HOME`, then run `app.sh`'s
    `stop_engine` and `status` and the remover.
  - Make `MODEL_RANKING_REPO/.venv/bin/python` a stub that fails. The deploy must then leave no
    `RELEASE` and must not swap `current`.
  - Deploy the same sha twice and assert that the tree's inode is unchanged.
  - Deploy four releases and assert that the previous `current` survives.
  - Run the launcher with a stub `.venv/bin/python` that records its environment, to check the
    exported nightly switch and the preflight refusal as behaviour, not as text.

### NIT

- **N1** `ios/app.sh:68-72`: with the service installed, `start_engine` still refuses when the
  checkout's `advisor.db` is missing. The service serves `engine/data/advisor.db` and does not
  need that file.
- **N2** `ios/app.sh:159-161`: `down` unloads the service only when `/health` answers. If the
  engine is between restarts (a crash inside `ThrottleInterval`, or the first seconds after
  login), `down` prints "was not running" and launchd brings the engine back within a minute.
  When the service is loaded, `down` should boot it out whether or not the engine answers.
- **N3** `scripts/install_engine_service.sh:85-88`: the first-artifact copy is safe for SQLite
  itself: publishes are `workspace.replace(target)` (`src/app/workflows/build.py:850`), and
  `cp` reads one inode. But the copy reads the database and then its record, with no snapshot
  of the pair. A hand-started engine's nightly publish that lands between the two copies pairs an
  old database with a new record, and then `RECENT` can skip that night's cycle. Copying the
  record first turns the worst case into one extra catch-up. The copy also comes from whatever
  tree the installer runs in, which could be a worktree with a test artifact (the rest of the
  first review's M5).
- **N4** `scripts/install_engine_service.sh:75`: `git archive … | tar -x` runs without
  `pipefail`. Measured: `git archive nosuchref | tar -x -C dir` exits 0. With `--no-venv`, an
  archive that fails would still get a `RELEASE` stamp on an empty tree.
- **N5** `scripts/install_engine_service.sh:89-93`: pruning protects only the new sha, not the
  release that `current` pointed at before the swap. Under the installer's flow with
  `KEEP_RELEASES=3` this is safe. A probe of five successive deploys kept the three newest, and
  the previous live one was always among them. But three `--deploy-only` runs into the live
  directory with no restart in between would delete the running engine's release, and its
  nightly child's interpreter lives there (see B2's evidence). Also, `ln -sfn` is not an atomic
  swap: it unlinks, then links.
- **N6** `scripts/install_engine_service.sh:126-130`: on an installed job, the installer rewrites
  the plist and then runs `kickstart -k`, which keeps launchd's loaded copy. A future change to
  the plist (for example to `ThrottleInterval`) reaches launchd only after a bootout or a new
  login.
- **N7** `scripts/engine_service.sh:26-31`, `ios/app.sh:164-167`: the log is rotated only when
  the launcher starts, so a healthy engine that runs for months is never rotated. `app.sh logs`
  uses `tail -f`, which keeps following the rotated `.1` file after a rotation (`tail -F` does
  not). Nothing rotates the launchd log `model-ranking-engine-launchd.log`.
- **N8** Carried from the first review:
  - N1: `$HOME` and the deploy paths go into the plist and into the wrapper's `"…"` without
    escaping (`install_engine_service.sh:38-40, 50-60`).
  - N4: the issue #32 body still says the log is `ios/.build/engine.log`, and that "if the
    checkout is on another branch, the service does not start the engine". Its "Done when" still
    reads "A branch checkout never runs as the engine". Rewrite the body in place to match the
    ruling.
  - N5: the remover does not confirm that :8080 is free after the bootout
    (`remove_engine_service.sh:12-17`).

## Acceptance-criterion coverage

- Service with RunAtLoad, KeepAlive, ThrottleInterval: `test_engine_service.py:48-53`. GREEN.
- launchd opens nothing under `~/Desktop` (B1, W-096): `test_engine_service.py:56-76` checks the
  program, the wrapper path, the log paths and the exact handover line. GREEN. Probes: the release
  has no reference to the checkout, and the launcher ran from the release with an empty
  environment.
- The engine and its nightly child run the deployed `origin/main` (B2):
  `test_engine_service.py:108-119` checks that `origin/main` is deployed whatever is checked out,
  with no `.git`, and with the `RELEASE` stamp. `:138-144` checks that the service runs only a
  release, and `:147-154` is the positive control. GREEN. B2 in the running process was measured
  by hand (`_SRC`, `_REPO` and `sys.executable` all inside `releases/<sha>`).
- The artifact persists across redeploys: `test_engine_service.py:122-129`. GREEN, and the
  overwrite mutant is killed (m16).
- One launcher, the same environment and preflight: `test_engine_service.py:177-181` is a string
  presence check. Mutants m05 and m06 survive (**M4**). By hand: the release started, and
  `/health` answered `"refresh":"scheduled"`.
- `app.sh` goes through launchctl, and `status` names the service: `test_engine_service.py:184-190`
  is a string check. m01 and m02 survive, and nothing tests `status` (**M4**).
- The remover takes the service off: `test_engine_service.py:193-197` is a string check, and m04
  survives (**M4**).
- "Done when: after a restart `/health` answers `scheduled` with no command": no test can show
  this without launchd. See **R1**.

## Red to green
- I exported `65504d2` with `git archive` into a scratch directory and ran its test file there.
  Result: `8 failed, 4 passed`. The 8 are the Desktop, wrapper, deploy, artifact, release-only,
  positive-control, rotation and `kickstart -k` tests. At `4162caa`: `12 passed`.
- `4162caa` changed one assertion from the red commit: `"starting" not in stdout` became
  `"starting on :" not in stdout` (`test_engine_service.py:144`). This is a correction, not a
  weakening. The refusal message itself says "not starting (#32)", so the original assertion
  could never pass, and "starting on :" is the engine's actual start line.

## Suite result
- `make test`: `1334 passed, 17 skipped` (the network contract tests), and
  `coverage-floor PASS: 38 module(s), floor 60%, 1 exempt`.
- `make shell-dialect`: `PASS: 14 script(s), one dialect, all parse`. `shellcheck` is not
  installed on this host.
- The tests make no network calls: `_deploy` fetches from a local bare repository.

## Deploy probe (manual; the one network use was the deploy's own `git fetch` and `pip`)
- I ran `bash scripts/install_engine_service.sh --deploy-only "<scratch>/App Support/engine"`.
  The path has a space on purpose, like "Application Support". It exited 0 in 11.7 s and produced
  `current -> releases/6834c7d`. The release has no `.git`, has its own `.venv` (an editable
  install pointing at `releases/6834c7d/src`), and has `RELEASE` = `6834c7d`. The copied
  `data/advisor.db` and `advisor.db.refresh.json` kept their modes (644 and 600).
- I then ran `env -i HOME PATH=/usr/bin:/bin:/usr/sbin:/sbin MODEL_RANKING_REPO=…/current
  MODEL_RANKING_DB=…/data/advisor.db ENGINE_LOG_FILE=… /bin/bash scripts/engine_service.sh --service`
  from `/`. The log said `starting on :8080, release-6834c7d, serving …/data/advisor.db`, and
  `/health` returned
  `{"status":"ok","build":"release-6834c7d","evidence":"servable","refresh":"scheduled",…}`.
  I stopped it with `pkill -f "uvicorn app.adapter.main:app"`. The log shows a clean lifespan
  shutdown, and afterwards no engine and no refresh child was left.
- Pruning, measured over five `--deploy-only --no-venv` runs on a scratch origin: after each run,
  the three newest releases remained, and the live release and the previous one were always kept.
- A redeploy while a nightly cycle is writing does not touch `data/advisor.db` (`:85`). The
  restart that follows ends the cycle. Its `flock` is released by the kernel, the live artifact
  stays whole (publishing is an atomic replace), and any scratch it left beside the artifact is
  swept by the next cycle (`refresh.py` `_sweep_stale_scratch`). No finding.

## Fault injection
Each mutant was applied in place with an exact string replace, the test file was run, and the file
was restored by string replace. md5 of `ios/app.sh` and `scripts/*.sh` was taken before and after
the whole run. Result: all identical, and `git status --short` was empty. No `git checkout` or
`git restore` was used.

| mutant | file | result | restored |
|---|---|---|---|
| m01 `service_installed` always false | ios/app.sh | **SURVIVED** | identical `3cf5e38f` |
| m02 `stop_engine` pkills with the service installed | ios/app.sh | **SURVIVED** | identical |
| m03 restart through stop+start, not `kickstart -k` | ios/app.sh | KILLED | identical |
| m04 remover keeps the plist | remove_engine_service.sh | **SURVIVED** | identical `59138dae` |
| m05 `export MODEL_RANKING_REFRESH=nightly` commented | engine_service.sh | **SURVIVED** | identical `203290c2` |
| m06 preflight never refuses | engine_service.sh | **SURVIVED** | identical |
| m07 service mode runs a tree without `RELEASE` | engine_service.sh | KILLED | identical |
| m08 prune guard for the new sha removed | install_engine_service.sh | **SURVIVED** | identical `7f609837` |
| m09 `KEEP_RELEASES=1` | install_engine_service.sh | **SURVIVED** | identical |
| m10 a finished release is rebuilt in place (`rm -rf` of the live tree) | install_engine_service.sh | **SURVIVED** | identical |
| m11 `RELEASE` written before the venv | install_engine_service.sh | **SURVIVED** | identical |
| m12 deploy `HEAD`, not `origin/main` | install_engine_service.sh | KILLED | identical |
| m13 failure path keeps the service loaded | install_engine_service.sh | **SURVIVED** | identical |
| m14 installer kills any listener on :8080 | install_engine_service.sh | **SURVIVED** | identical |
| m15 no log rotation | engine_service.sh | KILLED | identical |
| m16 the artifact is copied over the served one on each deploy | install_engine_service.sh | KILLED | identical |

## K.8 contract drift check
- The label `com.ilgar.modelranking.engine`, the plist path, the wrapper path and the log path
  are still three hand-kept copies:
  - `install_engine_service.sh:23-29`
  - `remove_engine_service.sh:8-10`
  - `ios/app.sh:29-31`

  Nothing has drifted today. `test_engine_service.py:193-197` checks the label and two paths
  across the installer and the remover. It does not check `app.sh` or the log path.

## K.9 candidates spotted outside this change's scope
- **K1** `pyproject.toml:9-20`: there is no lock file. Every `make install` and every release venv
  resolves fresh versions (measured drift: see **M2**). This is project-wide, not only #32.

## Risks queued
- **R1** The "Done when" criterion can be shown only after merge. Before merge, `origin/main`
  has no launcher, so an install then takes **M1**'s path. The owner's first install after the
  merge is the evidence. Read it from the log's `starting on :8080, release-<sha>` line and from
  `/health`'s `build` field (**M3**), not from `launchctl print`, whose state reads the same
  before a job starts and after it ends (W-096).
