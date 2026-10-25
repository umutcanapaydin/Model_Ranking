---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-25
---
# Security Review — release v0.2.0 (Stage 5.1, light mode, run v020)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`; the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` read from `main`), Stage 5.1, light mode, dispatched by run v020 for release v0.2.0 at the release Tester's head
**Independent:** yes. I wrote none of this range's code, tests or records, and none of its earlier reviews.
**Date:** 2026-10-25
**Release range:** `471dd79d740f5054d7cc4c7916ca8d4162bfc199..6416d539b0a98bd1b9a23dc30a132b55ff9a92a5` on `integration/run-v020` (draft PR #432), 66 commits, 86 files. `471dd79` is the reviewed head of the v0.1.0 verdict. `6416d53` is the release Tester's v0.2.0 verdict (MINOR, reviewed head `e87f9a9`).
**Reviewed head:** 6416d539b0a98bd1b9a23dc30a132b55ff9a92a5. I added no test, so the reviewed head is the head I was dispatched at. This verdict's own commit changes docs only.
**Risk tier:** LOW by the brief: `docs/project-brief.md:110` declares no HIGH path. I read the range at MEDIUM depth because it edits the deploy gate, the brief reader, two deploy scripts and the nightly's process model. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-v020` at `6416d53`, under `$TMPDIR`. I did not run `make install`. Tests and probes ran with the main clone's `.venv` interpreter, `PYTHONPATH` set to the worktree's `src` and `PYTHONDONTWRITEBYTECODE=1`; I checked that `app.__file__` resolves into the worktree. I copied the gitignored `advisor.db` in. I made no edit or commit in the main checkout and no network call, and I did not touch launchd, Fly or GitHub.

> **This record replaces** the v0.1.0 verdict: the deploy delta `9208fd8..471dd79`, PASS, reviewed head `471dd79`. That text stays in git, at `git show 471dd79:docs/reviews/release-security.md`, together with the verdicts it extended at `9208fd8` and `660af4b`. This range closes the v0.1.0 MINORs it carried: #410, #411, #412, #417, #418 and #419. Their remaining edges are filed as #444 (from #410) or closed by #429 (from #418).

## Verdict
MINOR: BLOCKING 0 · MAJOR 0 · MINOR 3 · NIT 0 · new risks queued 2.

The release adds no external surface: no new route, no new dependency and no new third-party import. The product's deploy controls got stricter: #410, `--no-replace-objects`, the safety surface, and `MODEL_RANKING_SERVED` now required. The accepted-cuts exception got narrower (#418, #429). All three findings come from two places: #426's new build child, and one test that the #427 retirement left uncited. None of them is exploitable in the current scope. None lets wrong data reach the served artifact, because only the parent publishes. Each has a short remedy.

### What I re-read and what I leaned on
- **#410 (the deploy gate, the brief reader, conformance).** I leaned on `docs/reviews/fix-issue-410-security.md` (round 2, MINOR, reviewed head `831f072`).
  - `git diff --stat 831f072..6416d53` shows `scripts/deploy_gate.py`, `scripts/brief_fields.py` and `conformance/` unchanged since that head.
  - Two commits follow it, both test-only: `c611817` (its M4: the replace test can now fail) and `b70fc0b` (the Tester's B1: every surface D-223 clause 5 names).
  - Its M1 to M3 and R1 to R2 are filed as #444.
  - I re-read `scripts/brief_fields.py:87` (`git --no-replace-objects`) and `scripts/deploy_gate.py:96`.
- **#418 and #429 (the accepted cuts).** I leaned on `docs/reviews/fix-issue-418-security.md` (PASS WITH FINDINGS, head `eaeee31`). I checked that its MINORs are closed in code:
  - M1, the 30-day cap: `src/app/workflows/refresh.py:337-339`, `:350`.
  - M2, the ADR is a live header outside any code block, not superseded, and names the board: `refresh.py:354-367`.
  - M3, a name with no letter or digit is refused: `refresh.py:344`.
  - `scripts/review_need.py:90`, `:194` routes any change to `data/accepted-cuts.yaml` to security. Its R1 is ruled by D-223 clause 4.
- **Read in full here (never reviewed per change):**
  - #426: `refresh.py` and `build.py`.
  - #427: both deploy scripts, `docs/cold-start.sh`, `docs/security-invariants.md`, `docs/watchlist.md`, `ios/Config/*` and `scripts/remove_engine_service.sh`.
  - #411: thirteen client catches.
  - #412 and #417: the regexes.
  - #419: the modality guard.
  - #403: `media_price_collisions`.
  - #450: the data YAML.
  - #447: the PRD gate.
  - #396: `scripts/client_decl_gate.py`, read only for exec, shell and relaxed rules. Its removed lines are rules moved or reworded, and no refusal was dropped.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `src/app/workflows/refresh.py:1449`. **The build child drops `-P`, so the working directory is back on its import path.**
  - Every other child the engine starts runs with `-B -P -m`, and each was reviewed for exactly this:
    - `src/app/adapter/nightly.py:227` (security pass NIT-1: "a stray `app/` beside the repository cannot stand in for the refresh").
    - `src/app/clients/arena_slices.py:105` (S-R2-4: a planted `pyarrow.py`).
    - `scripts/nightly_hosted.sh:56`.
  - The parent's own `-P` does not reach a child. Probe: I ran the parent with `-P` in a temp directory holding `app/workflows/build.py`. `build_in_child(["--db","x"])` printed `PLANTED build` and returned 0. A shadowing `yaml`, `httpx` or `pyarrow` in the working directory would load the same way.
  - It is not exploitable today. The hosted night runs from the trusted checkout root (`scripts/nightly_hosted.sh:36`), which holds no `.py` file. It is still a regression of a reviewed hardening.
  - **Remedy:** make the default command `[sys.executable, "-B", "-P", "-m", "app.workflows.build"]`, and add a test that pins the flags, as `tests/unit/test_nightly_refresh.py:468` does for the refresh.
- **M2** `src/app/workflows/refresh.py:1745`, with `:1444-1456` and `src/app/clients/protocols.py:87`. **The cycle's clocks no longer reach the build.** This is built ≠ wired (`docs/security-baseline.md`, "Invariants and wiring").
  - **(a) The fetch budget is unwired.**
    - `cycle_budget(FETCH_BUDGET_SECONDS)` sets `_Cycle.ends` in the parent. Every fetch now runs in the child, where `_Cycle.ends is None`, so each download keeps its full deadline and nothing caps the cycle.
    - Probe: inside `cycle_budget(1200)` the parent saw a deadline. A child started by `build_in_child` saw `cycle_ends() is None` (exit 0).
    - Effect: a slow night (W-126) is now killed whole at 25 minutes, with no publish and every source lost. Before, each late source was cut at 20 minutes and carried its data (D-156).
    - `tests/unit/test_refresh.py:1935` (`test_the_cycle_runs_inside_its_fetch_budget`) still passes, because it patches `refresh` and never reaches a fetch.
  - **(b) The child's limit runs from the child's start, not the cycle's.**
    - The epoch fetch runs in the parent before the build. If it takes more than two minutes, the parent's 27-minute `SIGALRM` fires first.
    - That signal keeps the kernel's default action (`refresh.py:130-131`). The parent dies and writes no record. The child runs on as an orphan, and its `.candidate`, `.sources` and `.progress` temp files stay beside the artifact, because the parent's `finally` (`:1712`) never ran.
    - Probe: a parent with a 1-second `SIG_DFL` alarm and a child limit of 10 seconds exited 142. The child wrote its file 3 seconds later.
    - This is the failure #426 set out to close. D-223 clause 1 says "the cycle's own alarm kills" the build.
  - The live artifact is never at risk, because only the parent renames. The cost is fresh data and stray files.
  - **Remedy:**
    1. Hand the child the cycle's remaining fetch deadline, through an argument or the environment, and read it once into `cycle_budget` in `build.main`.
    2. Set the child's limit to `min(BUILD_LIMIT_SECONDS, cycle deadline - margin)`, measured from the cycle's start.
    3. Add one test through `refresh.main` that a fetch inside the child sees a budget.
- **M3** `docs/security-invariants.md:42-43` (INV-25, INV-26) and D-224 clause 2. **The hosted engine's refusal to start lost its invariant citation.**
  - `tests/unit/test_engine_host.py:59` (`test_a_bind_beyond_loopback_needs_a_list_of_hosts`) was cited only by INV-27, which is now retired.
  - The control it tests is the one the hosted image relies on: `validate_startup_config` (`src/app/adapter/main.py:635`, run at import at `:785`). `Dockerfile:34-36` binds `0.0.0.0` and counts on the process refusing to boot without `MODEL_RANKING_ALLOWED_HOSTS`.
  - D-224 clause 2 says INV-25 and INV-26 keep this refusal. Neither row cites a test of it at startup: both are request-time checks.
  - The test still exists and passes, so this is a traceability gap, not a hole. An uncited security test is "one refactor from a silent hole".
  - **Remedy:** add `tests/unit/test_engine_host.py::test_a_bind_beyond_loopback_needs_a_list_of_hosts` and `tests/unit/test_hosted_engine.py::test_the_image_tells_its_startup_check_where_it_binds` to INV-25's citing tests, or to a new row: "the hosted engine refuses to boot on a bind beyond loopback with no Host list".

### PASS
- **The deploy scripts fail closed and have no default.**
  - `scripts/deploy_hosted_engine.sh:43`, `:109-112` refuses an unset `MODEL_RANKING_SERVED` before reading anything. The Mac path default is gone, so a deploy never guesses which data it ships.
  - The `--ship` path (`:95-107`) still requires the prepared stamp, which names this commit and the copy's own digest.
  - `docs/cold-start.sh:10`, `:16` refuses the same way.
  - `scripts/nightly_hosted.sh prepare` sets the variable itself and still refuses a token in its environment.
  - Citing test: `tests/unit/test_deploy_hosted.py:355`.
- **The #427 deletions leave nothing dangling.**
  - No tracked file runs `scripts/engine_service.sh`, `scripts/install_engine_service.sh` or `ios/app.sh up`. The remaining hits are harmless:
    - the Bash guard, which still refuses those names; retiring that rule is the owner's call, per the 2026-10-25 owner-actions row;
    - the guard's own bounds tests;
    - a regression assertion in `tests/unit/test_testflight_ready.py:91`.
  - INV-27 to INV-29 retire under the owner's ruling D-224, which answers an Escalate-NOW stop. Each has a `docs/watchlist.md` row with its return trigger.
  - Mutation samples 3 to 5 were removed with a note, not silently.
  - `NSLocalNetworkUsageDescription` is gone from `ios/Config/Info.plist` and from the Turkish strings, held by `tests/unit/test_engine_address.py:42` and `:157`.
  - The serving engine's own Host and bind controls (INV-25, INV-26) are untouched. M3 is about their citation only.
- **The progress file is handled safely.**
  - `mkstemp` creates it with mode 0600 in the artifact's directory (`refresh.py:1577`), and the cycle's `finally` unlinks it (`:1712`).
  - The child only appends to it (`build.py:650-653`).
  - The reader (`refresh.py:1468-1490`) skips torn lines, stray events and stamps that are not numbers. An unreadable file gives `{}`. The Tester pinned this at `e87f9a9`.
  - The child gets an argv list, not a shell (`refresh.py:1451`), and its stdout goes to stderr.
  - The child stays in the cycle's process group, so the engine's group kill still reaches it. M2(b) is the case where the parent dies alone.
- **Untrusted input is parsed more strictly.**
  - #411: every client's `json.loads` on fetched bytes catches `ValueError` and `RecursionError`. One bad source now fails and carries its data instead of aborting the night. `tests/unit/test_client_json_errors.py:60` scans every client.
  - #412: `src/app/clients/simplebench.py:30` is linear (`tests/unit/test_simplebench.py:167`).
  - #417: `src/app/workflows/registry.py:397`, `:423` are linear (`tests/unit/test_arena_respelling.py:78`). I re-derived the bound: `[^()]*` stops at the next parenthesis, so the total scan is linear.
  - #419: the modality guard (`registry.py:322-324`) now refuses `GPT-4o (image)` (`tests/unit/test_arena_respelling.py:115`, `:124`).
- **The accepted-cuts exception is narrower.**
  - A cut excuses only its own lost names (`refresh.py:397`).
  - It applies only until its `until:` date, at most 30 days out, and only under a live ADR that names its board.
  - Every malformed cut fails the refresh closed (`tests/unit/test_accepted_cuts.py:249`, `:259`, `:337`).
- **No SQL is built from input.** `media_price_collisions` (`src/app/workflows/build.py:656-670`) binds its two values as parameters, and it only reports drift; it refuses nothing.
- **Authority held.**
  - The one workflow edit (`ci.yml`, `pytest -n auto`) is the owner's: `15e5c9e`, no `GP-Agent` trailer, merged through PR #425. It stays inside `unshare --net`, and `permissions: contents: read` is unchanged.
  - No agent commit touches `.github/workflows/**`, `.claude/` or `.githooks/`.
  - The only commits without a `GP-Agent` trailer are the owner's three #424 commits.
  - No commit message carries AI attribution (grep count 0).
  - No commit adds a `reset --hard`, a force push, an `rm -rf` or a `DROP`.
- **#450's data changes are clean.** Only `last_verified` dates and roster names changed, transcribed with a probe log. No URL, token or secret.

## Gates passed
- [x] Secret scan green.
  - `make secrets` on the integration branch: `no leaks found` (dispatcher).
  - Re-run here on the exact range: `gitleaks git --log-opts=471dd79..6416d53` reports `66 commits scanned`, `no leaks found`.
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found` (dispatcher). No lock, `pyproject.toml` or requirement changed in the range. `scripts/lock_dependencies.py` changes a comment only.
- [x] `make slopsquat` green: PASS (dispatcher). The only new import is the standard library's `subprocess` in `refresh.py`; everything else is the project's own code.
- [x] Default-deny preserved for new external surfaces: none was added. No route, endpoint or CORS change. The deploy scripts now refuse when no artifact is named.
- [x] Permission matrix not violated: no agent write under `.github/workflows/**`, `.claude/` or `.githooks/`. The owner ruled the retired security invariants (D-224).
- [x] Prompt-injection hygiene: nothing new feeds untrusted text to an agent. Fetched feeds are parsed as data. No diff content tried to alter policy.
- [x] Auth/PII checks and the human-review trigger: not applicable. No HIGH path (`docs/project-brief.md:110`), and no auth, PII, payment or migration code.
- [x] SAST.
  - `bandit` is not installed in the venv, so I ran `ruff check --select S` over the touched source (`refresh.py`, `build.py`, `registry.py`, `src/app/clients/`).
  - One finding, S101 at `src/app/clients/arena_slices.py:187`, which predates the range.
  - The new `Popen` (`refresh.py:1451`) carries a reasoned `S603` waiver: an argv list, the project's own interpreter, no shell.
  - Conformance PASS (33) (dispatcher).
  - Range tests run here: 295 passed across `test_refresh_build_child`, `test_accepted_cuts`, `test_deploy_gate_pin`, `test_deploy_hosted`, `test_engine_host`, `test_client_json_errors`, `test_engine_service`, `test_simplebench` and `test_arena_respelling`. The coverage-floor message is expected on a partial run.

## Acceptance criteria evidence
- **#426** (a killed night names its source; each source's seconds are kept).
  - Code: `src/app/workflows/refresh.py:1444-1456`, `:1468-1490`, `:1121`; `src/app/workflows/build.py:650-653`.
  - Tests: `tests/unit/test_refresh_build_child.py:27`, `:39`, `:56`, `:70`, `:94`, `:115`, `:131`, `:139`.
  - Gaps: the missing `-P` flag (M1) and the fetch budget (M2).
- **#427** (the Mac engine is retired; a deploy needs a named artifact).
  - Code: `scripts/deploy_hosted_engine.sh:43`, `:109-112`; `docs/cold-start.sh:10`, `:16`; `ios/Config/Info.plist:13` (only `NSAllowsLocalNetworking` remains).
  - Tests: `tests/unit/test_deploy_hosted.py:355`; `tests/unit/test_engine_address.py:35`, `:157`; `tests/unit/test_testflight_ready.py:91`.
- **#410** (the pin exemption cannot be forged; the deploy scripts are safety surface).
  - Code: `scripts/brief_fields.py:87`, `scripts/deploy_gate.py:96`.
  - Tests: `tests/unit/test_deploy_gate_pin.py:77`, `:89`, `:98`, `:109`, `:139`, `:150`, `:185`.
- **#418 and #429** (cuts by name, an expiry within 30 days, a live ADR, a security route).
  - Code: `src/app/workflows/refresh.py:326-367`; `scripts/review_need.py:90`, `:194`.
  - Tests: `tests/unit/test_accepted_cuts.py:62`, `:155`, `:249`, `:259`, `:293`, `:337`.
- **#411**: the catch in every client (`src/app/clients/*.py`). Tests: `tests/unit/test_client_json_errors.py:60`, `:65`.
- **#412**: `src/app/clients/simplebench.py:30`. Test: `tests/unit/test_simplebench.py:167`.
- **#417**: `src/app/workflows/registry.py:397`, `:423`. Test: `tests/unit/test_arena_respelling.py:78`.
- **#419**: `src/app/workflows/registry.py:322-324`. Tests: `tests/unit/test_arena_respelling.py:115`, `:124`.
- **#403**: `src/app/workflows/build.py:656-670`. Tests: `tests/unit/test_media_price_collision.py:29`, `:34`, `:38`.
- **#396**: `scripts/client_decl_gate.py`. Tests: `tests/unit/test_client_decl_gate.py:1597`, `:1623`, `:1640`.
- **#447**: `tests/unit/test_prd_status.py:61`.
- **#413**: `tests/unit/test_record_schema_sync.py:44`, `:48`.

## Risks queued
- **R1** `ios/Config/Info.plist:13`. **`NSAllowsLocalNetworking` still applies to every build.**
  - Since D-222, only two cases need cleartext to a local address: the simulator against `make run`, and a Debug `Engine.local.xcconfig`. INV-73 still names local networking as the one transport exception.
  - Revisit at the app's next transport change: make the exception Debug-only, through a Debug Info.plist or a key the xcconfig substitutes.
- **R2** `src/app/workflows/refresh.py:1468-1490`. **The progress reader accepts `nan` and `inf`.**
  - `float(stamp)` accepts them, and `write_status` (`:1121`) would then write a non-standard JSON token into the night's record.
  - Nothing outside can reach this: only the cycle's own child writes the 0600 progress file.
  - Fold a `math.isfinite` check into M2's fix if that fix touches the reader.
