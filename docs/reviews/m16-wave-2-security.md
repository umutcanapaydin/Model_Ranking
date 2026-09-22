---
record_type: review
id: m16-wave-2-security
status: ratified
seat: independent
date: 2026-09-23
---
# M16-W2 Security Review (pulled forward, D-141): the engine starts its own refresh

> **Independent seat.** I did not write this code. I read the policy from the committed base only:
> `git show HEAD:subagent-profiles/Security-Reviewer.md` and `git show HEAD:docs/security-baseline.md`
> at `acef579`. I also read D-116, D-149, D-151 and the proposed D-154 in `docs/decisions.md`.
> The slice under review is the uncommitted working tree on top of `acef579`:
> `src/app/adapter/nightly.py` (new), `src/app/adapter/main.py` (validator, lifespan, `/health`),
> `ios/app.sh`, `scripts/retire_refresh.sh` (new), `tests/unit/test_nightly_refresh.py` (new), and the
> iOS decode and display of `min_quality` / `price_excludes`.
> I ran every experiment on copies in a scratch directory outside the repository. I started nothing on
> :8080, did not touch the repository's `advisor.db` or `.refresh.json` (their mtimes are unchanged:
> 2026-09-22 14:33 / 14:41), did not call launchd, and stopped every process I started.

## Verdict

**PASS WITH FINDINGS — 0 BLOCKING, 1 MAJOR, 4 MINOR, 4 NIT.**

The main control holds. I could not enable `MODEL_RANKING_REFRESH=nightly` in a production, strict,
unset or unrecognised `APP_ENV` by any means an operator's environment offers. The child's argv
cannot be injected into. The iOS privacy invariant (D-126) still holds.

The MAJOR is about a claim, not about the code. D-154 clause 1 and `nightly.py:12-14` both say the
network-fetching code "never loads into the serving process", and a test is cited for it. I
measured that it does load. The test passes anyway because it reads only direct imports.

## Findings

### MAJOR

**MAJOR-1: the "network code never loads into the server" invariant is false, and its test is green.**
`src/app/adapter/nightly.py:12-14`, D-154 clause 1, `tests/unit/test_nightly_refresh.py:334-347`.
- *Measured.* I imported `app.adapter.main` in the scratch copy (`APP_ENV=test`) and listed
  `sys.modules`. It contains `app.workflows.ingest`, all of `app.clients.{aider,arena,deepswe,epoch,
  litellm,openrouter,swebench}`, and `httpx`. `app.clients.arena` holds live `httpx.stream(...)`
  fetch code. The import chain predates this wave: `main` → `app.workflows.plans` (and others) →
  `app.workflows.ingest` → `app.clients.*`. This wave is the one that asserts otherwise. The test
  AST-parses only `main.py` and `nightly.py` and looks for direct `import` statements, so it passes
  even though `app.workflows.ingest` sits in its own forbidden set and is loaded.
- *Why it matters.* This is not exploitable today. Nothing in the serving path calls a fetch. But
  REQ-REF-007's "structural half" and D-116 clause 2 now rest on a guard that cannot fail
  (V3C-74). A later refactor that does call fetch code from the server would pass the same test.
- *Remedy.* Make the test measure the real thing. Import `app.adapter.main` in a subprocess and
  assert on `sys.modules`: forbid `app.workflows.{refresh,build,sources,epoch}` there, which is true
  today. Then either narrow the claim in D-154, `nightly.py` and REQ-REF-007/008 to "parsers are
  loaded, fetch entry points are never called", or move the parsers the server needs out of the
  modules that fetch.

### MINOR

**MINOR-1: the child's entire output is held in the serving process's memory.** `nightly.py:176-182`.
- *Measured.* I ran `NightlyRefresh.run_once` with a stand-in child that writes to stdout. Peak RSS
  of the parent: 25 MB → 262 MB for 50 MB of output, and 25 MB → 974 MB for 200 MB (about 4.7x:
  `communicate()` buffers, then `decode`, then `splitlines`). Only 20 lines are ever kept.
- *Context.* A real cycle prints about 30 KB. I measured this in
  `~/Library/Logs/model-ranking-refresh*.log`: 1,398 lines across several cycles. So this is not a
  live problem. But D-154's stated reason for a child process is that "a memory blow-up takes the
  server down with it". A crash message or a verbose build that grows without bound brings that
  coupling back.
- *Remedy.* Read `proc.stdout` line by line into a `collections.deque(maxlen=20)`, with a per-line
  byte cap. Alternatively, send the child's output to a file and log only its tail.

**MINOR-2: the environment gate is checked at import, but the child is started at lifespan, and
the lifespan does not check again.** `main.py:559` (validator) vs `main.py:594` /
`nightly.py:155-160` (`from_environment` checks only the switch).
- *Measured.* I imported `main` with `APP_ENV=production` and the switch off, which boots. I then
  set `MODEL_RANKING_REFRESH=nightly` in-process and entered `TestClient(app)`. `/health` said
  `"refresh": "scheduled"` and the schedule task was created while `APP_ENV` was still `production`.
- *Context.* This is not reachable from outside. Each uvicorn worker re-imports the module, so the
  validator re-runs, and only code already inside the process can change `os.environ`. It is a
  defence-in-depth gap: a fail-closed control should be checked where its effect happens.
- *Remedy.* In `from_environment()`, return `None` (and log) unless `APP_ENV` is relaxed as well,
  or pass the validator's verdict into the lifespan.

**MINOR-3: `retire_refresh.sh` trusts whatever answers on :8080.** `scripts/retire_refresh.sh:19-29`.
- *Measured.* I copied the script to scratch and changed only its port to 18778. I put a 10-line
  Python server there that always returns `{"refresh":"scheduled"}`, and I stubbed `launchctl` and
  `rm` through `PATH` with a fake `HOME`. The script printed "safe to retire", booted the job out
  and removed both files. With nothing listening it correctly refused ("Nothing was changed", rc=1).
- *Why it matters.* Any local process on :8080 can get the owner to retire the only nightly refresher
  and make it look healthy. So can an engine started with a different `MODEL_RANKING_DB`. The result
  is that the served artifact silently goes stale. The impact is availability of freshness only.
- *Remedy.* Also require `build` to match `git rev-parse --short HEAD` (app.sh sets
  `APP_BUILD=dev-<sha>`). Check that the listener's PID is the repo's `.venv` uvicorn, using
  `lsof -iTCP:8080 -sTCP:LISTEN`. Compare the plist's `--db` with the engine's configured database,
  which argues for an authenticated or local-only diagnostic rather than more `/health` fields
  (V3C-103).

**MINOR-4: the network-fetching child inherits the whole parent environment.** `nightly.py:169-170`.
- *Measured.* The stand-in child printed the names of environment variables containing
  `SECRET`/`TOKEN`. It saw the `FAKE_SECRET_TOKEN` I had set, and it also saw a token-named variable
  from my launching shell. I printed names only, never values. `app.sh` starts the engine from the
  owner's interactive shell, so whatever that shell exports reaches the process that parses
  untrusted upstream content. Its last 20 output lines also go to `ios/.build/engine.log`.
  `grep` finds no `os.environ` / `getenv` read in `src/app` other than `nightly.py` and `main.py`,
  so the refresh needs none of that environment.
- *Remedy.* Build the child's environment from an allowlist: `PATH`, `HOME`, `LANG`/`LC_*`, `TZ`,
  `TMPDIR`, proxy variables if used, `PYTHONPATH`, `MODEL_RANKING_*`.

### NIT

- **NIT-1: a module can shadow `app.workflows.refresh` from the working directory.**
  `nightly.py:131,172` (`-m`, `cwd=_REPO`). `python -m` puts the cwd first on `sys.path`, ahead of
  the injected `PYTHONPATH`. *Measured:* a stand-in `app/workflows/refresh.py` at the copy's repo
  root ran instead of the real one (`sys.path[0]` = repo root). It exited 0, so the engine logged
  `exit 0 (published)`. Writing to the repo root takes the same trust as writing `src/`, and
  `app.sh` (`cd "$REPO"`, `-m uvicorn`) already has the same exposure for the parent. My first
  3-worker run from the copy's root failed with `No module named 'app.adapter'` for exactly this
  reason. *Remedy:* use `-P` (Python 3.11+; the venv runs 3.14.0) or `cwd=_SRC`.
- **NIT-2: each uvicorn worker runs its own schedule.** *Measured:* `--workers 3` on 127.0.0.1:18777
  with a stale record started three catch-up children, one per worker PID. `refresh.py`'s `flock`
  makes two of them exit `busy` in the real cycle, so nothing overlaps. But N workers make N fetch
  attempts and N sets of log lines. `app.sh` runs one worker. *Remedy:* document single-worker, or
  refuse the switch when `WEB_CONCURRENCY` or the worker count is above 1.
- **NIT-3: `/health` is unauthenticated and gives the exact minute of the next fetch, plus whether a
  fetch is running now.** `main.py:1191`, `nightly.py:222-231`. *Measured:*
  `"refresh_next": "2026-09-23T00:50"` and `"refresh_last_at": "2026-09-22T11:41:08...+00:00"`. The
  engine binds to 127.0.0.1 in `app.sh`, and a strict environment always reports `"refresh": "off"`
  (verified), so no remote party can see this today. No path or fingerprint is exposed. Each call
  also re-reads and parses `.refresh.json`. *Remedy:* none needed while this stays dev-only. If the
  engine is ever deployed, move these fields to the authenticated diagnostic (V3C-103).
- **NIT-4: `retire_refresh.sh` with `HOME=""`.** `set -u` catches an unset `HOME` (measured:
  "unbound variable", rc=1). An empty `HOME` gets through and aims `rm -f` at
  `/Library/LaunchAgents/com.hcs.modelranking.refresh.plist` and
  `/Library/Application Support/model-ranking/refresh_job.sh` (measured with a stubbed `rm`). The
  names are fixed and the paths need root, so this is harmless. The script also prints "removed:"
  even when nothing existed, because `rm -f` always succeeds. *Remedy:* `: "${HOME:?}"` and
  `[ -e "$DST" ] && rm ...`.

### PASS (what I attacked and could not break)

- **Switch vs environment matrix** (real module import in a subprocess with `env -i`). With the
  switch at `nightly`, the process refused to boot (`ConfigError`) for each of: unset `APP_ENV`,
  `""`, `production`, `prod`, `PRODUCTION`, `staging`, `test;prod`, and a Cyrillic-`е` `tеst`. It
  booted only for `test`, `" test "`, `TEST` and `dev`, which are relaxed by design. In production,
  `NIGHTLY` and `" nightly "` were refused under the D-116 message, and `on` / `1` / `nightly\n`
  were refused as unknown values. `off` and empty booted. `enabled()` and `switch_problem()`
  normalise the same way (`strip().lower()`), so the validator and the lifespan cannot disagree
  about a spelling.
- **Argv injection.** The child is started with `create_subprocess_exec`, with no shell.
  `MODEL_RANKING_DB` goes through `Path.resolve()`, so it is always absolute: `-evil` and
  `--epoch-dir=x` became `/…/-evil` and `/…/--epoch-dir=x`. For `MODEL_RANKING_EPOCH_DIR`, the
  values `--db=/tmp/evil` and `-x` were rejected by argparse (exit 2, a `failed` cycle). The values
  `; rm -rf ~`, `$(id)` and `a b` reached the build as one inert argument each. I checked this with
  the real `refresh.main` and a stubbed `refresh()`, so no network was used.
- **Publish while serving (REQ-REF-006/007).** The publish is `candidate.replace(target)`
  (`refresh.py:820`), which is an atomic rename. The lock is a kernel `flock`, released when the
  process dies. The suite's `test_a_cycle_killed_mid_publish_leaves_the_live_artifact_and_the_lock_usable`
  and `test_the_server_answers_while_a_cycle_hangs` pass. The timeout and cancel paths kill the child
  and wait for it (`nightly.py:189-195`).
- **Secrets.** `gitleaks detect --pipe` on `git diff` and `gitleaks --no-git` on the three new files
  found no leaks. No new third-party import: `nightly.py` is stdlib only, and `pyproject.toml` is
  unchanged. The logged command line holds only the interpreter, the db path and the epoch dir.
- **iOS / D-126.** `python3 scripts/client_decl_gate.py` → `client-decls PASS: 11 client file(s)
  in 4 configuration(s)`. `.venv/bin/pytest -q --no-cov tests/unit/test_router_hints.py` →
  `7 passed`. The added Swift lines contain no URL/Session/UserDefaults/print/Logger/FileManager/
  Keychain/Pasteboard call. `priceExcludes` is an allowlisted code: only `"search_call"` maps to
  wording, and anything else renders nothing. `minQuality` is decoded as `Double?` and displayed.
- `tests/unit/test_nightly_refresh.py` + `tests/unit/test_ios_client_contract.py`: `56 passed`.

## Gates

- [x] Secret scan (gitleaks on the diff and the new files): clean
- [x] No new dependency (stdlib only), so slopsquat and pip-audit are not affected
- [x] Default-deny: the switch is off by default and refused in every strict environment (measured)
- [x] No new mutating route. `/health` gains read-only fields; `/v1` is unchanged
- [ ] SAST: `bandit` and `semgrep` are not installed in `.venv` or on `PATH`. Not run (see below)

## What I did not check

- **SAST.** I ran no bandit or semgrep pass; neither is installed. I did not install anything
  (`make install` is forbidden to this seat).
- **A real refresh cycle.** Every child I ran was a stand-in, to avoid network fetches and to keep
  away from the repository's artifact. I did not show that upstream data can reach the child's
  output (MINOR-1 is the unbounded buffer, not a demonstrated remote trigger).
- **`ios/app.sh up` end to end.** It binds :8080 and starts from the real repo, which this seat may
  not do. I read its diff only.
- **The real `retire_refresh.sh`, or launchd.** I tested only a copy with its port changed and
  stubbed `launchctl`/`rm`.
- **Swift build and `swift test`.** Not run. The D-126 evidence is the two gates named above plus a
  grep of the added lines.
- **Mac sleep and clock-change behaviour of the schedule.** I measured no timing beyond the
  `/health` fields.
- **The Code-Reviewer and Tester seats' verdicts for this wave.** I did not read them.
