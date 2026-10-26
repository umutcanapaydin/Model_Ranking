---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-26
---
# Security Review — release v0.2.0 (Stage 5.1, light mode, run v020)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`; the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` read from `main`), Stage 5.1, light mode, dispatched by run v020 for release v0.2.0 at the release Tester's head
**Independent:** yes. I wrote none of this range's code, tests or records, and none of its earlier reviews.
**Date:** 2026-10-25; delta rounds 2026-10-26 (the nightly workflow, then hotfix-1026)
**Release range:** `471dd79d740f5054d7cc4c7916ca8d4162bfc199..9ef64482ae331c65491ef2675289b22caa5db0da`: the release below, then the deploy delta `6416d53..0222150` (the nightly workflow), then the deploy delta `0222150..9ef6448` (hotfix-1026: #459, #460, #461), each read in its round at the end. First round: `471dd79d740f5054d7cc4c7916ca8d4162bfc199..6416d539b0a98bd1b9a23dc30a132b55ff9a92a5` on `integration/run-v020` (draft PR #432), 66 commits, 86 files. `471dd79` is the reviewed head of the v0.1.0 verdict. `6416d53` is the release Tester's v0.2.0 verdict (MINOR, reviewed head `e87f9a9`).
**Reviewed head:** 9ef64482ae331c65491ef2675289b22caa5db0da. The hotfix-1026 round added no test, so the reviewed head is the release Tester's delta head it was dispatched at; the Tester's verdict commit `1a99f07` on top and this verdict's own commit change docs only. Earlier heads: `0222150b195f2eba06fe33707c1124fcbd8ad70b` (the nightly-workflow round) and `6416d539b0a98bd1b9a23dc30a132b55ff9a92a5` (the first round).
**Risk tier:** LOW by the brief: `docs/project-brief.md:110` declares no HIGH path. I read the range at MEDIUM depth because it edits the deploy gate, the brief reader, two deploy scripts and the nightly's process model. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-v020` at `6416d53`, under `$TMPDIR`. I did not run `make install`. Tests and probes ran with the main clone's `.venv` interpreter, `PYTHONPATH` set to the worktree's `src` and `PYTHONDONTWRITEBYTECODE=1`; I checked that `app.__file__` resolves into the worktree. I copied the gitignored `advisor.db` in. I made no edit or commit in the main checkout and no network call, and I did not touch launchd, Fly or GitHub.

> **This record replaces** the v0.1.0 verdict: the deploy delta `9208fd8..471dd79`, PASS, reviewed head `471dd79`. That text stays in git, at `git show 471dd79:docs/reviews/release-security.md`, together with the verdicts it extended at `9208fd8` and `660af4b`. This range closes the v0.1.0 MINORs it carried: #410, #411, #412, #417, #418 and #419. Their remaining edges are filed as #444 (from #410) or closed by #429 (from #418).

## Verdict
MINOR: BLOCKING 0 · MAJOR 0 · MINOR 3 open (M1-M2, #453; M4 from the hotfix-1026 round, to be filed; M3 fixed in `9683734`) · NIT 0 · risks queued 6 (R1-R2 from the first round, R3-R4 from the nightly-workflow round, R5-R6 from the hotfix-1026 round). The hotfix-1026 round `0222150..9ef6448` (#459, #460, #461) found no BLOCKING: D-225's republish publishes only the running release's own fresh build of content equal to what is served, after the W-047 re-read, so it launders nothing past the deploy's #198 refusal; its one MINOR (M4) is the serving-bound check it skips.

The nightly-workflow round `6416d53..0222150` (the owner-installed nightly workflow) found no BLOCKING, MAJOR or MINOR: it adds two risks queued and nothing that lets a branch, a tag or a crafted artifact reach the deploy token.

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

## Delta round 2026-10-26 (6416d53..0222150)

**Reviewer:** Security-Reviewer subagent, dispatched for the deploy delta of release v0.2.0. I read the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` from `main`.
**Independent:** yes. I wrote none of this range's code, tests or records. I wrote none of the earlier reviews of #387 or #389 either.
**Range:** `6416d539b0a98bd1b9a23dc30a132b55ff9a92a5..0222150b195f2eba06fe33707c1124fcbd8ad70b`, 10 commits, 4 of them code. Code in the range (`git diff --stat 6416d53..0222150 -- . ':!docs'`):
- `.github/workflows/nightly-hosted.yml` (new, 144 lines);
- `conformance/test-ci-yaml.py` (+5);
- `scripts/nightly_hosted.sh` (mode 644 to 755 only);
- `tests/unit/test_nightly_hosted.py` (+26).
**Risk tier:** LOW by the brief: `docs/project-brief.md:110` declares no HIGH path. I read the workflow at HIGH depth because it is the only place the production deploy token is used. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-nightly` at `bb27bac` (it holds `0222150`), under `$TMPDIR`. I used the main clone's `.venv` interpreter, with `PYTHONPATH` set to the worktree's `src` and `PYTHONDONTWRITEBYTECODE=1`. I made no edit in the main checkout. I made no call that changes anything on GitHub or Fly, and I did not touch launchd. I read GitHub only through read-only `gh api` and `gh run view` calls: the environment, its branch policy, the secret names, the ruleset, the collaborators, the tags of the pinned actions, and run 40230588976.

**Verdict of this round:** PASS for the delta. BLOCKING 0 · MAJOR 0 · MINOR 0 · risks queued 2 (R3, R4). The record's verdict stays MINOR, because the first round's M1 and M2 (#453) are still open.

### What I leaned on and what I re-read
- **The workflow's text was already reviewed.** It is byte-equal to the proposal (`cmp .github/workflows/nightly-hosted.yml scripts/ci/nightly-hosted.yml` exits 0). The proposal and `scripts/nightly_hosted.sh` have not changed since `docs/reviews/fix-issue-389-security.md` (reviewed head `93d9ee2`). That review followed `docs/reviews/fix-issue-387-security.md`, round 2 at `e4b8459`, whose B1 was the reason for the environment.
  - `git diff --stat 93d9ee2..0222150 -- scripts/ci/ scripts/nightly_hosted.sh` shows only the 3-line `GIT_*` unset (`scripts/nightly_hosted.sh:24-26`). The first round of this record covered that change.
  - So this round asks what installing the file adds: GitHub's settings, which no test in the tree can read, and the two code edits.
- **Authority.** `e6647b9` (the workflow), `d2b77de` (test-ci-yaml) and `023522a` (the mode) carry no `GP-Agent` trailer: they are the owner's own commits, merged through PRs #454 and #455. The one agent commit, `0222150` (`GP-Agent: tester`), touches only a test. No commit adds AI attribution, `reset --hard`, a force push, an `rm -rf` or a `DROP`.

### Findings

#### BLOCKING
- none

#### MAJOR
- none

#### MINOR
- none

#### PASS (with evidence)
- **Only `main` reaches the token, and GitHub enforces it, not the workflow's own text.**
  - The workflow side: `deploy` runs in `environment: fly-production` (`.github/workflows/nightly-hosted.yml:113`), and the token is read only at `:143`, in the one step that ships.
  - The GitHub side, read with `gh api`:
    - `environments/fly-production` has `deployment_branch_policy: {protected_branches: false, custom_branch_policies: true}`.
    - Its single policy is `{"name":"main","type":"branch"}`, so a **tag** named `main` does not match.
    - `FLY_API_TOKEN` is listed among the environment's secrets.
    - `actions/secrets` (the repository level) lists none.
  - What this means: a run dispatched from another branch or a tag uses that ref's copy of the workflow, which can drop the `if:` at `:37` and `:110-112`. It still cannot enter the environment, so it gets no token. That closes the #387 review's B1 in settings, which is where it has to be closed (D-217 clause 2).
  - Citing test (shape only): `tests/unit/test_nightly_hosted.py:418`.
- **Who can start it.** The triggers are `schedule` and `workflow_dispatch` only (`:22-25`). There is no `pull_request` and no `pull_request_target` (`tests/unit/test_nightly_hosted.py:469`).
  - A schedule runs on the default branch.
  - Dispatching needs write access. `collaborators` lists one account, the owner (admin).
  - `actions/permissions/workflow` gives `default_workflow_permissions: read` and `can_approve_pull_request_reviews: false`.
  - Branch protection on `main` refuses force pushes and deletion, with `enforce_admins: true`.
- **Least privilege.** The workflow's permissions are `contents: read` (`:27-28`). The refresh job adds `actions: read` (`:39-41`), and the deploy job keeps `contents: read` (`:116-117`).
  - Both checkouts set `persist-credentials: false` (`:47`, `:121`).
  - `GH_TOKEN` is set only on the step that fetches the state (`:60-62`).
  - The refresh and prepare modes refuse `FLY_API_TOKEN`, `GITHUB_TOKEN` and `GH_TOKEN` in their environment (`scripts/nightly_hosted.sh:38-45`).
- **No script injection.** No `run:` block contains a `${{ }}` expression: `grep -nE '^\s+run:.*\$\{\{'` finds none, and the six expressions in the file are at `:43`, `:61-62`, `:92-93` and `:143`.
  - These are all `env:`, `with:` or `outputs:` values, built from `github.token`, `runner.temp`, a secret or a step output.
  - The one step output, `outcome`, is compared only inside the deploy job's `if:` (`:112`). No `run:` reads it, so a forged value can at most start a deploy that the gate and the stamp check still judge.
- **Neither a crafted artifact nor a crafted branch reaches the deploy job's code.**
  - `hosted-public` is downloaded by name, with no `run-id` and no `github-token` input (`:128-132`). So `actions/download-artifact` reads only the current run's artifacts, and only this run's `refresh` job can upload those.
  - `v8.0.2` is past the extraction path-traversal fix. Whatever the artifact holds lands under `build/hosted/`.
  - The deploy job then runs nothing from `build/hosted/`:
    - the gate is `.venv/bin/python scripts/deploy_gate.py --check`, so the script's own directory heads the import path;
    - `fly` comes from `$RUNNER_TEMP/bin` (`:136-140`);
    - `--ship` reads the copy only to hash it, and reads the stamp's first line with whitespace removed, compared exactly (the #389 review).
  - `hosted-state` is read only from this file's own schedule or dispatch runs, in this repository, whose commit is an ancestor of `main` or equal to it (`:65-72`). It reaches only the token-free refresh. The deploy job never names it (`tests/unit/test_nightly_hosted.py:449`, the `hosted-state not in text` assertion).
  - The residual is data, not code: a refresh compromised by a source can poison the data it ships. D-217 clause 2 and #389 accept that, and it is the trust boundary W-005 already names.
- **Every action is pinned to a commit, and each commit is the tag its comment names.** `gh api repos/<action>/commits/<tag> --jq .sha` resolves:
  - `actions/checkout` `v4.4.0` to `11d5960a…`;
  - `actions/setup-python` `v5.6.0` to `a26af69b…`;
  - `actions/upload-artifact` `v7.0.2` to `cf430e03…`;
  - `actions/download-artifact` `v8.0.2` to `9000827c…`;
  - `superfly/flyctl-actions` `1.5` to `fc53c09e…`.

  All five equal the SHAs at `:45`, `:48`, `:88`, `:99`, `:119`, `:123`, `:129` and `:133`. The flyctl binary is pinned to `0.4.111` (`:135`). No action caches anything, so there is no cache to poison.
- **The deploy job runs the deploy gate first, and the gate fails closed (D-217 clause 4).**
  - The code: `scripts/nightly_hosted.sh:80-84` runs `deploy_gate.py --check` before any copy or `fly` call. A crash, a missing interpreter or a stale verdict all give a non-zero exit, and the script stops.
  - The live evidence is run 40230588976, a `workflow_dispatch` on `main` at `b762ffe`:
    - `refresh` succeeded;
    - `deploy` failed at "The night's deploy" with `deploy-check FAIL: 3 file(s) changed since the reviewed head 6416d53 of docs/reviews/release-security.md` and `[night] nothing deployed`;
    - the log masks the token as `***`;
    - the gate read its policy from `b762ffe`, which on `main` is the protected ref itself.
- **`conformance/test-ci-yaml.py:88-92` does not let the control go vacuous in this tree.**
  - The new branch skips a line only while inside a step (`step is not None`) and only deeper than the step's own keys. A key on the `- ` line itself is never skipped, because that path is the `if`, not the `elif`.
  - A `run: |` body is consumed earlier, by the block-scalar reader at `:51-55`.
  - Mutation probe: with `elif False:` in its place, run in memory against the worktree's workflows, the check FAILS with 2 findings. Those are `the stdlib fallback parser disagrees with PyYAML on job refresh` and the same for `deploy`, so the branch is load-bearing.
  - Without the mutation: `test-ci-yaml PASS: 34 step(s) checked, 0 finding(s), 4 workflow(s) ... by PyYAML`.
  - The grading path in this repository is PyYAML. `conformance/run-all.py:53` prefers `.venv/bin/python`, and `pyyaml==6.0.3` is in `requirements/dev.lock:1249`.
  - The fallback is never the grade here. With `yaml` made unimportable, the check exits 2 (`NOT-EVALUABLE: ci.yml uses a construct the stdlib fallback parser does not read`), which is a refusal, not a pass. R3 is the edge the new branch opens in that fallback.
  - A probe comparing `run` and `if` as well, over every workflow, finds the fallback and PyYAML equal except for a trailing `"` that the fallback's `strip("'\"")` drops from two `run:` values. That is cosmetic: both still contain `nightly_hosted.sh`.
- **The mode change is the fix, not a widening.** The workflow starts `scripts/nightly_hosted.sh` as a command (`:86`, `:97`, `:144`). Mode 755 makes that work, and changes nothing about what the script may do.
  - The Tester's test derives the started set from the workflow, fails on an empty set, and checks both the disk and the index (`tests/unit/test_nightly_hosted.py:483-506`).
  - It ran here: `43 passed` in `test_nightly_hosted.py`. The coverage-floor message is expected on a partial run.
- **The Tester's open MINORs carry no security weight.** M3: deleting the installed workflow stays green, which fails safe, since without the file nothing deploys. M4: no nested-`name:` sample; R3 below extends it.

### Gates passed (delta)
- [x] Secret scan green.
  - `make secrets` on `b762ffe`: `no leaks found` over 1348 tracked files (dispatcher).
  - Re-run here on the range: `gitleaks git --log-opts=6416d53..0222150` reports `5 commits scanned`, `no leaks found`.
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found` (dispatcher). No lock, `pyproject.toml` or requirement changed in the range.
- [x] `make slopsquat` green: PASS, 0 suspect (dispatcher). No new import: `tests/unit/test_nightly_hosted.py` uses only `os`, which was already imported.
- [x] Default-deny preserved: the only new external surface is the deploy path. It is gated by the environment's branch policy, the job's ref condition, the deploy gate and the stamp check, and each one refuses by default.
- [x] Permission matrix not violated: the owner installed the workflow; no agent commit touches `.github/workflows/**`, `.claude/` or `.githooks/`.
- [x] Prompt-injection hygiene: nothing in the range feeds fetched text to an agent. No diff content tried to alter policy.
- [x] Auth/PII and the human-review trigger: not applicable (no HIGH path, no auth, PII, payment or migration code).
- [x] SAST: no Python source under `src/` changed in the range. The conformance edit is a `continue`. Conformance PASS (33), 0 failing (dispatcher).

### Acceptance criteria evidence (delta)
- **D-217 clause 2** (only the deploy job holds the token, and it is the environment's secret, which only `main` reaches).
  - Code and settings: `.github/workflows/nightly-hosted.yml:113`, `:143`, `:37`, `:110-112`; the environment policy `main`/`branch`; no repository secret.
  - Tests: `tests/unit/test_nightly_hosted.py:418`, `:449`.
- **D-217 clause 3** (state only from this file's own runs on `main`). Code: `.github/workflows/nightly-hosted.yml:65-72`. Test: `tests/unit/test_nightly_hosted.py:429`.
- **D-217 clause 4** (the deploy gate first; a stale verdict deploys nothing).
  - Code: `scripts/nightly_hosted.sh:80-84`.
  - Live: run 40230588976.
  - Test: `tests/unit/test_nightly_hosted.py:449` (the deploy step runs `nightly_hosted.sh deploy build/hosted`).
- **#455** (the script the workflow starts is executable). Mode 100755 at `0222150`. Test: `tests/unit/test_nightly_hosted.py:497`.
- **test-ci-yaml's nested-key fix**: `conformance/test-ci-yaml.py:88-92`, proven load-bearing by the agreement check at `:363-377` (mutation probe above).

### Risks queued (delta)
- **R3** `conformance/test-ci-yaml.py:88`, with `:371-377`. **In the stdlib fallback, a step whose keys are indented more than two columns past its `- ` loses those keys.**
  - The skip measures from `step_ind + 2`, not from the column of the step's first key. So for `-   name: Lint` followed by `run: echo skipped`, aligned under `name`, the fallback reads `{'name': 'Lint'}` with no `run`, while PyYAML reads both (probe).
  - The step-command check then skips the step (`if not run: continue`, `:311`).
  - The PyYAML agreement check compares only `(name, uses)` (`:372-373`), so it cannot see the lost `run`.
  - Before this change the fallback read those keys.
  - Not reachable in this tree: no workflow uses that indent, the grade runs on PyYAML, and the fallback refuses `ci.yml` (exit 2). The `REQUIRED` invocations would still fail closed if their only step were written that way.
  - Remedy, upstream of this project with the Tester's M4:
    1. Measure the skip from the first key's column on the `- ` line.
    2. Compare normalised `run` and `if` in the agreement check, beside `name` and `uses`.
    3. Add a nested-`name:` sample and a wide-indent sample to the self-proof.
- **R4** GitHub setting `environments/fly-production`: `can_admins_bypass: true`.
  - Today it is the owner alone: the repository has one collaborator, the admin, who already holds the token.
  - It becomes a gap the day a second admin is added.
  - Revisit then: turn the bypass off, and add the owner as a required reviewer if deploys ever become anything other than the night's own.

## Delta round 2026-10-26 hotfix (0222150..9ef6448)

**Reviewer:** Security-Reviewer subagent, dispatched for the deploy delta before the next hosted deploy. I read the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` from `main`.
**Independent:** yes. I wrote none of this range's code, tests or records, and none of the Tester's verdicts on it.
**Range:** `0222150b195f2eba06fe33707c1124fcbd8ad70b..9ef64482ae331c65491ef2675289b22caa5db0da` on `integration/hotfix-1026` (not pushed), 20 commits with the Tester's verdict `1a99f07` on top (docs only). Code: `src/app/workflows/refresh.py` (+41/-8, #460, D-225, D-226), `src/app/adapter/main.py` and `pyproject.toml` (the version, #459), `scripts/remove_engine_service.sh` deleted (#461), `.path-refs-allow` (one row), tests `tests/unit/test_release_restamp.py`, `tests/unit/test_app_version.py`, `tests/unit/test_engine_service.py`.
**Reviewed head:** 9ef64482ae331c65491ef2675289b22caa5db0da. I added no test.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). I read `refresh.py` at MEDIUM depth because it now decides what the deploy's #198 refusal accepts. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/security-hotfix-1026` at `1a99f07`, under `$TMPDIR`. The main clone's `.venv` interpreter, `PYTHONPATH` set to the worktree's `src` and `PYTHONDONTWRITEBYTECODE=1`. Probes ran from a scratch file outside the tree, against `tmp_path` artifacts. No edit in the main checkout, no network call that changes anything, no launchd, Fly or GitHub write; one read-only `gh issue list`.

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 1 (M4) · risks queued 2 (R5, R6).

### Findings

#### BLOCKING
- none

#### MINOR
- **M4** `src/app/workflows/refresh.py:1668-1669`, held by `tests/unit/test_release_restamp.py:173-185`. **A D-225 republish skips the serving-bound check, so it can publish, and the night can then deploy, an artifact the engine this release ships refuses to start on.**
  - The bound check (`egress_problems`, D-173 clause 4, #57) lives inside `_reason_to_refuse` (`:1264`). On `same`, `:1668` calls only `_replaced_underneath`, so the candidate is never checked. D-226 clause 1 lists the serving-bound check among the skipped refusals on purpose.
  - Unlike the others, that check does not compare content. It is an absolute property of the candidate under the bounds of the code that will serve it. `src/app/adapter/main.py:698` applies the same function when the engine starts, and in production a problem there refuses the start.
  - Probe: the live artifact was published by `release-aaaaaaa`, and the bound is then lowered (`MODEL_RANKING_MAX_RANKED_ROWS=1`). The same release's cycle returns `1` (unchanged). `release-bbbbbbb`'s cycle returns `0` with `unchanged content, republished as this release's own build (D-225)`, and the record says `served_built_by: release-bbbbbbb`. `egress_problems` on the published file then reports the bound.
  - Why it matters: D-225 fires exactly when the code changes. A release that lowers a bound default (`serving_bounds.py:41`) or adds a bound would republish on its first quiet night, pass `prepare` (the deploy script checks no bound), and ship to Fly an image whose engine refuses to start. `fly.toml` sets no bound variable, so the engine reads the code's defaults. Before D-225 that night stayed `unchanged`, the deploy refused another release's data, and the old machine kept serving. The test's premise, "the live file already serves exactly this", holds only for the old engine.
  - Why MINOR, not BLOCKING: the engine's own start check still fails closed, so oversized data is never served; the cost is availability. No outside party can trigger it, because a bound changes only through reviewed code. And it does not fire for this deploy: `serving_bounds.py` and the bound constants in `main.py` are unchanged in the range, so the live state, built by the previous release under the same defaults, is within them.
  - Remedy (supersedes D-226 clause 1 in part, so it is the owner's ruling): on `same`, run `egress_problems(candidate, bounds_from_env())`. If it reports anything, do not publish. Return the unchanged outcome with the bound named in the reason, so the night is not counted as a refusal (D-226's concern) and the deploy refuses as it did before D-225. Then turn `tests/unit/test_release_restamp.py:173-185` around: it should assert that the file is not replaced. Fix this before any release that touches `src/app/workflows/serving_bounds.py`.

#### PASS (with evidence)
- **The republish launders nothing past the #198 refusal.**
  - What is published is the running release's own fresh candidate (`refresh.py:1696`). It is published only when its served digest equals the live one (`:1645`), so it serves the same content.
  - It runs only after the W-047 re-read (`:1668`, `_replaced_underneath` at `:1285-1300`). Probe: `tests/unit/test_release_restamp.py:150-170` passes, so a writer that replaces the artifact mid-cycle is never overwritten and never relabelled.
  - Rows carried forward from the live file for a source that failed (D-156) were already published on every changed night, judged only against that same live file. The republish adds no new way for another builder's rows to ship.
- **Who controls `APP_BUILD` in the night.** Only `scripts/nightly_hosted.sh:55` sets it, from the checkout's own `HEAD`. The refresh and prepare legs run beside no token (`:38-45`), and the deploy leg unsets `DEPLOY_ACCEPT_DATA_FROM` (`:48`, `:90`). The deploy re-derives `HEAD_SHORT` from its own checkout and refuses any prepared stamp that is not `release-<HEAD>-data-<digest>-from-<HEAD>` (`scripts/deploy_hosted_engine.sh:100-106`). A cycle with no `release-` stamp never republishes (`refresh.py:1010-1012`; test `tests/unit/test_release_restamp.py:60`).
- **A crafted `.refresh.json` can force a publish, and that is harmless.**
  - Probe: a record whose `served_built_by` is a list, another release or missing makes the cycle publish (`refresh.py:1013-1017`; tests `:76`, `:112`).
  - What it forces is the publish of this release's own same-content build, after the re-read. That is the outcome D-225 intends.
  - The opposite forgery, a record that names the running release, keeps the cycle unchanged (probe: exit `1`). The deploy already trusts that label (`deploy_hosted_engine.sh:121-132`, `:141`), so the forgery gives nothing it did not give before this range.
  - The record sits beside the artifact in one trust domain: whoever can write one can write the other. In the night, both come only from the workflow's own runs on `main` (D-217 clause 3).
- **Skipping the content refusals lets nothing degraded through, M4 aside.** Every input of `degradations` and `upward_anomalies` is fixed by the digest (`refresh.py:762-876`), with two exceptions:
  - The surface boards' model ids. These come from the release's own alias and registry data, not from a feed, and re-keying them is what D-225 exists to ship.
  - The own board's unranked rows. They reach users only through the floor, which is hashed (`:820`).
  - Gaps in the digest's coverage (R5) are gaps those guards cannot see either.
- **The `json.loads` signal** (`refresh.py:1014`). It catches `OSError` and `ValueError`, which includes `JSONDecodeError` and `UnicodeDecodeError`, and treats a record that is not an object as another builder's (`:1017`). It reads only the refresh's own record, in the state directory. Probe: a record nested 200,000 deep raises `RecursionError`, but first in the pre-existing `_read_last_ok` (`:1306`), and the cycle fails closed: the artifact is byte-identical, and no candidate or scratch file is left. See R6.
- **#459.** `APP_VERSION` and `pyproject.toml` say `0.2.0` (`src/app/adapter/main.py:83`, `pyproject.toml:9`). `/health` already served the version, so nothing new is disclosed. `tests/unit/test_app_version.py:44-48` fails closed on an empty `docs/releases/`.
- **#461.**
  - The remover is deleted by a commit, not by an `rm`.
  - The Bash guard still refuses its name (`.claude/hooks/bash_guard.py:424`), which is safe: it refuses a file that is gone. The owner-actions row that retires the guard rule is the owner's.
  - The `.path-refs-allow:153` row is exact: no wildcard, the one deleted path. It carries a reason (#461, D-224 clause 3) and sits in the section for retired files.
  - The owner-actions edits change status cells and one row's text. No command added in the range writes anything the agent may not.
- **Destructive operations and authority.** No commit in the range adds `reset --hard`, a force push, `rm -rf`, `DROP`, or a write under `.claude/`, `.githooks/` or `.github/workflows/**` (`git diff --name-status 0222150..1a99f07`).

### Gates passed (delta)
- [x] Secret scan green: `make secrets` on `6411610`, no leaks (dispatcher). Re-run here: `gitleaks git --log-opts=0222150..1a99f07` reports `17 commits scanned`, `no leaks found`.
- [x] `make deps` (pip-audit --strict) green on `6411610` (dispatcher). No lock or dependency range changed; `pyproject.toml` changes only `version`.
- [x] `make slopsquat` PASS: 20 declared, 0 suspect (dispatcher). No new third-party import: `tests/unit/test_app_version.py` imports `re`, `tomllib`, `pathlib` and `fastapi.testclient`, all already in use.
- [x] Default-deny preserved: no new route or external surface. The deploy's #198 refusal and `DEPLOY_ACCEPT_DATA_FROM` are unchanged (`scripts/deploy_hosted_engine.sh` is not in the diff).
- [x] Permission matrix not violated: no agent write to `.claude/`, `.githooks/`, `.github/workflows/**`, `Dockerfile` or `fly.toml`.
- [x] Prompt-injection hygiene: nothing in the range feeds fetched text to a model or an agent, and no diff content tried to change policy.
- [x] Auth/PII and the human-review trigger: not applicable (no HIGH path; no auth, PII, payment or migration code).
- [x] SAST: `bandit` and `semgrep` are not installed in this seat. `ruff check --select S` on `src/app/workflows/refresh.py` and `src/app/adapter/main.py` passes ("All checks passed!"), and `pyproject.toml:75` keeps `S` in the gate's ruff set. Conformance PASS, 33 tests (dispatcher, `6411610`). Tests here: `tests/unit/test_release_restamp.py`, `test_app_version.py` and `test_engine_service.py` give `21 passed` at `1a99f07`. The coverage-floor message is expected on a partial run.

### Acceptance criteria evidence (delta)
- **D-225 clause 1** (a release republishes over another builder's or a missing record). Code: `src/app/workflows/refresh.py:1006-1017`, `:1645-1646`. Tests: `tests/unit/test_release_restamp.py:35`, `:76`, `:112`, `:126`.
- **D-225 clause 3** (no churn for the same release or a cycle without a release stamp). Code: `refresh.py:1010-1012`, `:1017`. Tests: `tests/unit/test_release_restamp.py:51`, `:60`.
- **D-226 clause 2** (the re-read runs on a republish). Code: `refresh.py:1668`, `:1285-1300`. Test: `tests/unit/test_release_restamp.py:150`.
- **D-226 clause 1** (the content refusals are skipped). Code: `refresh.py:1668-1669`. Test: `tests/unit/test_release_restamp.py:173` (the serving-bound part is M4).
- **#459**. Code: `src/app/adapter/main.py:83`, `pyproject.toml:9`. Tests: `tests/unit/test_app_version.py:39`, `:44`.
- **#461**. The deletion of `scripts/remove_engine_service.sh` at `1ab57a0`, and `.path-refs-allow:153`. Its documented-paths gate is `conformance/test-documented-paths.py`, conformance PASS (dispatcher).

### Risks queued (delta)
- **R5** `src/app/workflows/refresh.py:762-876` against `src/app/workflows/standings.py:96-130`. **The digest does not cover everything `/v1/boards` serves.**
  - On a surface's own board, a standing names the model's id (`_Row.model` is `s.model_id`), while the digest hashes the ranked row's display name.
  - On an undeclared-surface board, the standing's `effort` and the price filter (`px_median`) are not hashed: only `raw_name|model_id|score` are (`:841-843`).
  - Before this range, a change confined to those fields was never published. Now it ships once per release, on the first quiet night, and no guard looks at those fields on either path.
  - Not exploitable: ids come from the release's own data. But D-225's "Revisit when: the fingerprint stops covering everything the deploy ships" is already true of the public artifact, which carries the whole database minus `plans` (`src/app/workflows/public.py:33-46`).
  - Revisit with the next change to the fingerprint: hash the standings payload itself, or narrow D-225's wording to what `/v1` serves.
- **R6** `src/app/workflows/refresh.py:1014`, `:1049`, `:1306`. **A record nested deeper than the interpreter's recursion limit raises `RecursionError`, which none of the record readers catch.** The cycle fails closed (probe: the artifact is unchanged and the scratch files are gone), but the crash handler's own `write_status` raises again, so no record of the crash is written. Same class as #466; fold it into #466's fix by catching `RecursionError` beside `ValueError`, or by bounding the record's size before parsing.
