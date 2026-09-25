---
record_type: review
id: issue-32-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-25
---
# #32 review: a launchd service keeps the engine running, from main only

**Reviewer:** independent seat, Code-Reviewer and Tester in one pass (policy read from
`.claude/agents/Code-Reviewer.md`, `.claude/agents/Tester.md`, `.agents/rules/practices.md`,
`.agents/rules/review-seats.md`; the range does not touch any of them)
**Independent:** yes
**Date:** 2026-09-25
**Commit range:** `origin/main..16440e0` (2ff8dc7 red test, 16440e0 implementation)
**Acceptance criteria:** issue #32, owner ruling 2026-09-25, and its "Done when"

Nothing was installed, loaded, booted out or kickstarted, and nothing was written under
`~/Library`. The service was examined through `--print-plist` / `--print-wrapper`, scratch git
repositories, and reading the code against `docs/warnings.ledger.md` W-096.

## Verdict
BLOCKING. Two findings. First, on the owner's Mac the service is very unlikely to start the
engine: the project's own measured record (W-096) says the handover shape does not work under
launchd. Second, the branch gate does not cover the nightly refresh, and the nightly refresh is
the reason the service exists. The suite is green (1331 passed). The tests do not see either
problem: one test checks only the launchd arguments, and the other checks only the moment the
process starts.

## Findings

### BLOCKING

- **B1** `scripts/install_engine_service.sh:26-33` (wrapper line 31), `scripts/engine_service.sh:25`, `scripts/engine_service.sh:40`
  : **the shape contradicts W-096, so the service is not expected to start the engine.**
  W-096 recorded two facts under launchd. (a) `/bin/bash` could not read a script that lives
  under `~/Desktop`: exit 126, `/bin/bash: .../Desktop/.../scripts/refresh_job.sh: Operation not
  permitted`. The shape that worked had **the whole job script** in Application Support. That
  script `cd`'d into Desktop and ran the venv **python**, and bash never read a file under
  Desktop. (b) "a launchd process cannot `getcwd()` inside `~/Desktop` (`git rev-parse` fails
  with `Operation not permitted`)".
  The generated wrapper is `exec /bin/bash "<repo>/scripts/engine_service.sh" --service`. That
  is (a) again: the same `/bin/bash`, as the job's program, opening a script under Desktop. If
  bash did get past (a), the branch gate is `git rev-parse --abbrev-ref HEAD` run from inside
  `$REPO`, which is (b). Under (b) the branch becomes `'?'`, so the gate fails closed and the
  engine never starts: "the checkout is on '?', not main". The scratch probe below shows this
  message for a directory where git cannot answer. `APP_BUILD` would also become `dev-` (line 40).
  For either reason the likely result is a job that retries every 60 s forever and never serves.
  The issue's "Done when" (after a restart, `/health` answers with `"refresh": "scheduled"`)
  would not be met. The installer does wait for `/health` and says so, so the failure is loud at
  install time, not silent. But the PR says it follows the W-096 shape (`install_engine_service.sh:9-13`:
  "The shape is W-096's, the one that worked"), and it does not.
  The test meant to hold W-096 (`tests/unit/test_engine_service.py:47-57`) checks only
  `ProgramArguments` and the log paths. It passes while the wrapper's single line reopens
  Desktop. It encodes the half of the lesson that no longer bites.
  *Why blocking:* this is the whole deliverable, and the repository's own measurement predicts
  it fails. No run under launchd proves otherwise, and this seat may not do that run.
  *Direction (for the author, not prescribed):* keep every file bash reads outside Desktop. Copy
  the launcher into Application Support, as the refresher's `refresh_job.sh` was. Do not base the
  branch gate on `git` running with its working directory under Desktop: for example, the venv
  python, which did read Desktop under launchd, could read `.git/HEAD`. Then have the owner run
  one sentinel-style probe under launchd before merge (W-096's "wait on a sentinel" lesson).
  Evidence: `docs/warnings.ledger.md:150`; `--print-wrapper` output:
  ```
  exec /bin/bash "/…/svc32/scripts/engine_service.sh" --service
  ```
  scratch repo with no git answer: `[engine] … the checkout is on '?', not main: not starting (#32).`

- **B2** `scripts/engine_service.sh:24-32` with `src/app/adapter/nightly.py:204-210,256-262`
  : **the branch gate runs once, at process start, but the nightly refresh runs whatever is
  checked out at 23:00.**
  The engine starts the refresh as a child process:
  `sys.executable -B -P -m app.workflows.refresh` with `cwd=_REPO` and `PYTHONPATH=_SRC`. So
  every night the refresh loads `app.workflows.refresh` from the working tree as it is at that
  moment. Take a service engine started on `main`. If the Desktop checkout is then switched to a
  wave branch, the service never re-checks the branch: KeepAlive only acts when the process
  exits, and a healthy engine runs for months. That night, the branch's refresh, build and
  fetchers write `advisor.db`, the served artifact. Meanwhile `/health` still reports main's
  `APP_BUILD`, which was captured at start (line 40). This is the trap the ruling names ("A
  service that runs 'whatever branch is checked out' is the trap the old refresher had"), and it
  moves into the one thing the service exists to keep running. The criterion "A branch checkout
  never runs as the engine" holds only for the uvicorn process image. It does not hold for what
  the engine runs.
  *Why blocking:* the stated safety property of the change does not hold for its purpose.
  *Direction:* check the branch before each cycle, at the point where the child is spawned, and
  skip the cycle (and log it) when the checkout is off main. Another option is to run the service
  from a checkout that only ever holds `main`. Add a test that fails when the check is removed.
  Note: this also bears on B1. A checkout the service owns, outside `~/Desktop`, would remove both
  problems at once.

### MINOR

- **M1** `tests/unit/test_engine_service.py:69-85`: **the tests can commit into, and switch the
  branch of, the repository that runs them.** `_scratch_repo` and `_launch` pass
  `{**os.environ}` to git. Measured here: a `git push` from a linked worktree exports `GIT_DIR` to
  the pre-push hook (git 2.50.1, probe repo). `.githooks/pre-push` runs `make gate`, and
  `make hooks` is the documented Stage 0 step. Agents work in worktrees. With `GIT_DIR` pointing
  at a decoy repo, the test run left a commit `scratch` by `t <t@example.invalid>` in the decoy
  and switched its HEAD to `wave/m99-w1`, and 2 tests failed. The hook is not installed in this
  clone today (`core.hooksPath` unset), so this is latent. When it fires, it damages the worktree
  being pushed. Fix: strip `GIT_*` variables from the environment given to every git and
  launcher subprocess.

- **M2** `ios/app.sh:46-52,75-78,143-144`, `scripts/install_engine_service.sh:81-82`: **bootout
  and then an immediate bootstrap races launchd.** `launchctl bootout` can return before the job
  has finished being removed. A `bootstrap` right after it then fails ("Bootstrap failed: 5",
  hidden by `2>/dev/null`), and the `kickstart` fallback finds no service, so `restart` stops the
  engine and starts none. `stop_engine` waits only until `/health` stops answering, and uvicorn
  stops listening before its lifespan shutdown (which kills a running nightly child) finishes.
  For `restart`, `launchctl kickstart -k gui/$UID/<label>` restarts in place without unloading.
  Otherwise, wait until `launchctl print` fails before bootstrapping.

- **M3** `ios/app.sh:75-78,143-144`: **with the service installed and the checkout on a branch,
  `restart` stops a working engine and starts none.** `stop_engine` boots out the main engine.
  The bootstrapped service then sleeps 300 s at the gate, and `app.sh` reports "FAILED to start"
  after 10 s. That leaves the owner with no engine and no nightly refresh until the checkout is
  back on main. A developer on a branch can no longer run their branch's engine through
  `app.sh` at all. Refuse up front, before any bootout, when the service is installed and the
  checkout is off main, and say what to do.

- **M4** `scripts/install_engine_service.sh:64-74,85-95`: **the installer can leave the owner with
  no engine.** It kills every `uvicorn app.adapter.main:app` on the machine, including engines in
  other worktrees on other ports, before the plist is linted and before launchd accepts the job.
  It does this even when run off main, where the service will only wait (line 67 prints a note
  and carries on). If the process holding 8080 is not this engine, nothing is killed, and the
  service fails to bind every 60 s forever. `scripts/retire_refresh.sh:24-28` already checks that
  the listener IS this engine. On failure (line 93) the service stays loaded and keeps looping,
  and the message does not say that `remove_engine_service.sh` takes it off.

- **M5** `scripts/install_engine_service.sh:18` against `ios/app.sh:16`: **the service is bound to
  whichever checkout the installer was run from.** `REPO` is taken from the script's own
  location, while `app.sh` hardcodes the Desktop path. Run from a worktree (this review's
  `--print-wrapper` pointed at `/private/tmp/.../svc32`), the service would run a checkout that
  `app.sh` does not manage and that can be deleted. A worktree on a branch never starts, and a
  deleted one exits 90 every minute. Refuse unless the installer runs from the main working tree
  (`git rev-parse --git-dir` equals `--git-common-dir`), or pin the path the way `app.sh` does.

- **M6** `scripts/install_engine_service.sh:47-51`, `scripts/engine_service.sh:34-38,50-54`:
  **nothing bounds the log, and a failing start loops every minute.** `KeepAlive=true` with
  `ThrottleInterval=60` restarts a missing-`advisor.db` or preflight exit every 60 s. Each restart
  starts a Python interpreter (preflight) and writes several lines, about 1440 times a day, for
  as long as the fault lasts. In normal running, uvicorn's access log writes one line for every
  app request, and each nightly cycle can add up to `OUTPUT_TAIL_BYTES` = 64 KB of child output.
  launchd only appends. `ios/.build/engine.log` used to be truncated at each `app.sh` start; the
  service log is never truncated, and nothing rotates it until go-live, months away. Make the
  failure paths sleep before they exit, as the off-main path already does. Also bound the log:
  for example, truncate or roll it in the launcher when it passes a size, or turn off the access
  log under `--service`.

- **M7** `tests/unit/test_engine_service.py:108-130`: **the tests for the `app.sh` routing, the
  remover and the launcher's environment are string matches, and 6 of 10 in-place mutants
  survived** (table below). None of the tests notices when `app.sh` stops recognising the
  service, when `stop_engine` goes back to `pkill` with the service installed, when the remover
  no longer deletes the plist, when the nightly export is commented out, or when the preflight
  stops refusing. The detached-HEAD case also has no test. It is correct today: `'HEAD'` is
  refused, per the scratch probe. The launcher's `MODEL_RANKING_REPO` hook shows these
  behaviours can be tested with stubs. For example, run `app.sh`'s functions with a fake
  `launchctl` on `PATH` and a scratch `HOME`, and run the remover the same way.

### NIT

- **N1** `scripts/install_engine_service.sh:26-55`: the paths go into the plist unescaped and into
  the wrapper inside `"..."`. A `&` or `<` in `$HOME` breaks the plist; `plutil -lint` catches
  that before loading (measured: "unknown ampersand-escape"). A `$` or backtick in the repository
  path would be expanded when the wrapper runs. The paths with spaces ("Application Support") are
  quoted correctly everywhere: the plist `<string>`, the wrapper, `mkdir -p "$(dirname …)"`, and
  `rm -f "$WRAPPER"`.
- **N2** `scripts/engine_service.sh:17`: `--service` still honours `MODEL_RANKING_REPO`, which
  `launchctl setenv` could supply to every gui-domain job. Service mode could ignore it.
- **N3** `scripts/engine_service.sh:26`: the gate trusts the branch NAME `main`. A local `main`
  that is ahead of `origin/main` with unreviewed commits passes the gate. This is acceptable
  under the ruling's wording, but worth one line in the header comment.
- **N4** Issue #32 body: the plan says the service logs to `ios/.build/engine.log`, but it logs to
  `~/Library/Logs/model-ranking-engine.log` (correct under W-096). PR and issue bodies are live
  documents (practices, "Writing and pruning"), so rewrite that line in place.
- **N5** `scripts/remove_engine_service.sh:5-17`: unlike `retire_refresh.sh:19`, it does not refuse
  an empty `HOME`, and it does not confirm that the engine and port are free after the bootout.

## Acceptance-criterion coverage

- "Service with RunAtLoad, KeepAlive, ThrottleInterval": `tests/unit/test_engine_service.py:38-44`,
  asserts on the generated plist. GREEN; the KeepAlive mutant was killed.
- "launchd opens nothing under ~/Desktop (W-096)": `tests/unit/test_engine_service.py:47-57`,
  GREEN, but it proves only the direct arguments. See **B1**.
- "Runs only from main": `tests/unit/test_engine_service.py:88-92` (branch refused, exit 0),
  `:95-99` (positive control on main), `:102-105` (by hand, any branch). GREEN, and the
  gate-removed mutant was killed. It covers start time only; see **B2**. There is no detached-HEAD
  test (**M7**).
- "One launcher, same env and preflight": `tests/unit/test_engine_service.py:108-114` is a string
  presence check, and two mutants survived (**M7**). By hand, the launcher started the engine from
  this worktree: `/health` gave `"build":"dev-16440e0"`, `"refresh":"scheduled"`, and the engine
  stopped cleanly.
- "`app.sh` down/restart through launchctl; `status` says whether installed":
  `tests/unit/test_engine_service.py:117-123` is a string check. Two mutants survived. No test
  covers `status` (**M7**).
- "Remover takes it off": `tests/unit/test_engine_service.py:126-130` is a string check, and a
  mutant survived (**M7**).
- "Done when: after a restart `/health` answers `scheduled` with no command": no test is
  possible without launchd, and B1 predicts it fails. The owner's install run is the only
  evidence available, and it has to be read from the log (a sentinel line), not from
  `launchctl print`.

## Red to green
- `2ff8dc7` adds only the test file. At that commit `scripts/engine_service.sh`,
  `install_engine_service.sh` and `remove_engine_service.sh` do not exist
  (`git ls-tree 2ff8dc7 scripts/`), and `ios/app.sh` has no mention of the service. All 9 tests
  are therefore red there. At `16440e0` all 9 are green.

## Suite result
- `make test` in the worktree: `1331 passed, 17 skipped` (network contract tests skipped), and
  `coverage-floor PASS: 38 module(s), floor 60%`.
- `make shell-dialect`: `PASS: 14 script(s), one dialect, all parse`. `shellcheck` is not
  installed on this host.

## Fault injection (each mutant applied in place, the file run, then restored by string replace, with md5 checked before and after)

| mutant | file | result | restored |
|---|---|---|---|
| gate removed (`if false`) | engine_service.sh | KILLED (1 failed) | identical `039fdc0f…` |
| gate lets detached `HEAD` through | engine_service.sh | **SURVIVED** | identical |
| off-main path exits 1 | engine_service.sh | KILLED | identical |
| `export MODEL_RANKING_REFRESH=nightly` commented out | engine_service.sh | **SURVIVED** | identical |
| preflight never refuses | engine_service.sh | **SURVIVED** | identical |
| wrapper drops `--service` | install_engine_service.sh | KILLED | identical `16fbc5a4…` |
| `KeepAlive` false | install_engine_service.sh | KILLED | identical |
| `service_installed` always false | ios/app.sh | **SURVIVED** | identical `2ffd98b0…` |
| `stop_engine` pkills with service installed | ios/app.sh | **SURVIVED** | identical |
| remover no longer deletes the plist | remove_engine_service.sh | **SURVIVED** | identical `b02e6f61…` |

`git status --short` was empty after the run. No `git checkout` or `git restore` was used.

## Branch-gate probes (scratch repositories, `ENGINE_SERVICE_WAIT_S=0`)
- detached HEAD: refused (`'HEAD'`), exit 0.
- linked worktree on a branch: refused, exit 0.
- linked worktree on `main` (the primary checkout was on another branch): passes the gate, and
  stops next at `advisor.db`.
- not a git repository: refused as `'?'`. This is the B1(b) outcome.
- missing directory: exit 90.

## K.8 contract drift check
- Label `com.ilgar.modelranking.engine`, plist path, wrapper path and log path appear identically
  in `install_engine_service.sh:19-22`, `remove_engine_service.sh:6-8` and `ios/app.sh:29-31`.
  These are three hand-kept copies of one fact (the drift the practices file ranks first).
  Nothing has drifted today. `tests/unit/test_engine_service.py:126-130` checks two of the three
  for the label and the paths, and it does not check the log path.

## K.9 candidates spotted outside this change's scope
- **K1** `src/app/adapter/nightly.py:256-262`: independent of #32, every engine started by hand
  with `app.sh` has had B2's property since D-154, because the nightly child always runs the
  current checkout. If B2 is fixed only for the service, file the hand-started case separately.

## Risks queued
- **R1** If B1 is fixed by moving the gate or the launcher out of Desktop, the next unknown is
  whether the venv python still reads Desktop under launchd for uvicorn, as it did for the
  refresh. The owner's install run shows it: the log gets a sentinel line, and `/health` answers
  within the installer's 20 s.
