---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — release v0.2.0 (Stage 5.1, light mode, run v020)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`; the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` read from `main`), Stage 5.1, light mode, dispatched by run v020 for release v0.2.0 at the release Tester's head
**Independent:** yes. I wrote none of this range's code, tests or records, and none of its earlier reviews.
**Date:** 2026-10-25; delta rounds 2026-10-26 (the nightly workflow, then hotfix-1026) and 2026-10-27 (the launchd guard retirement, build 6; then night-1027: D-227, D-228), and 2026-10-29 (run night-1028: D-229, build 7); and 2026-10-31 (run 1030 and fixes-1030: D-230, D-231; then fixes-1031: D-232, D-233)
**Release range:** `471dd79d740f5054d7cc4c7916ca8d4162bfc199..6e6f5beb81fc12d29d51540fc132be230d8d880b`: the release below, then the deploy delta `6416d53..0222150` (the nightly workflow), then the deploy delta `0222150..9ef6448` (hotfix-1026: #459, #460, #461), then the deploy delta `9ef6448..50c4764` (#470's guard retirement, build 6, the Tester's `50c4764`), then the deploy delta `50c4764..718cae4` (night-1027: #473, #474, #476 and the Tester's round), then the deploy delta `718cae4..c29392c` (run night-1028: eleven issues on #483, build 7 and the Tester's round), then the deploy delta `c29392c..ed18de5` (run 1030 and fixes-1030: #496, #494, #488, #493, #500, #484, #510, #506, #511, #509, #503, #501, #505, the owner's guard patch #497/#498, and the release Tester's two tests), then the deploy delta `ed18de5..6e6f5be` (fixes-1031: #517, #522, #518, #535 and the release Tester's three test files), each read in its round at the end. First round: `471dd79d740f5054d7cc4c7916ca8d4162bfc199..6416d539b0a98bd1b9a23dc30a132b55ff9a92a5` on `integration/run-v020` (draft PR #432), 66 commits, 86 files. `471dd79` is the reviewed head of the v0.1.0 verdict. `6416d53` is the release Tester's v0.2.0 verdict (MINOR, reviewed head `e87f9a9`).
**Reviewed head:** 6e6f5beb81fc12d29d51540fc132be230d8d880b. This is the release Tester's head for the fixes-1031 round: `integration/fixes-1031` at `243d115` plus the Tester's three test files (`6e6f5be`). The fixes-1031 round added no test and changed no code. Earlier heads: `ed18de5bef8ad54d501b8a268db9900073ab903f` (the run-1030 round), `c29392c6847ef1d3857711ed00bc8d9263efcd37` (the night-1028 round), `718cae416dc4b20ab9a39a10295b8e6b61aadfd9` (the night-1027 round), `50c4764bd94ffaa21201eaffaa6892f65c07e811` (the 2026-10-27 guard round), `9ef64482ae331c65491ef2675289b22caa5db0da` (the hotfix-1026 round), `0222150b195f2eba06fe33707c1124fcbd8ad70b` (the nightly-workflow round) and `6416d539b0a98bd1b9a23dc30a132b55ff9a92a5` (the first round).
**Risk tier:** LOW by the brief: `docs/project-brief.md:110` declares no HIGH path. I read the range at MEDIUM depth because it edits the deploy gate, the brief reader, two deploy scripts and the nightly's process model. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-v020` at `6416d53`, under `$TMPDIR`. I did not run `make install`. Tests and probes ran with the main clone's `.venv` interpreter, `PYTHONPATH` set to the worktree's `src` and `PYTHONDONTWRITEBYTECODE=1`; I checked that `app.__file__` resolves into the worktree. I copied the gitignored `advisor.db` in. I made no edit or commit in the main checkout and no network call, and I did not touch launchd, Fly or GitHub.

> **This record replaces** the v0.1.0 verdict: the deploy delta `9208fd8..471dd79`, PASS, reviewed head `471dd79`. That text stays in git, at `git show 471dd79:docs/reviews/release-security.md`, together with the verdicts it extended at `9208fd8` and `660af4b`. This range closes the v0.1.0 MINORs it carried: #410, #411, #412, #417, #418 and #419. Their remaining edges are filed as #444 (from #410) or closed by #429 (from #418).

## Verdict
MINOR: BLOCKING 0 · MAJOR 0 · MINOR 4 open (M9 as #526, M10 as #529, M11 as #530, and M12 new from the fixes-1031 round, routed to #541) · NIT 0 · risks queued 5 open (R3, R4, R5, R8, R10 as #531) and R11 new. The fixes-1031 round `ed18de5..6e6f5be` (#517, #522, #518, #535 and the release Tester's tests; D-232, D-233) found no BLOCKING and nothing that loosens the deploy gate: every change adds a base to read, a file to the surface or a reason to exempt nothing, and the policy, the workflows and the DevFlow pin are still read only at protected refs, never from the change's tree alone. Its open edges are already filed: #533 (the guard lets a session move the refs both bases come from), #534 (a stale `origin/HEAD`) and #541 (more spellings that hide a directory change). M12 adds three more spellings to #541. R11: `policy_root` is now dead code that returns the merge-base only.

The run-1030 round's verdict, as it read when it closed: MINOR: BLOCKING 0 · MAJOR 0 · MINOR 3 open (M9, M10, M11 from the run-1030 round, each to be filed; M8 closed by #496) · NIT 0 · risks queued 5 open (R3, R4, R5, R8, and R10 new; R1 closed by #488, R6 by #496, R9 by #493/#500/#505/#509/#511, R2 by #453). The run-1030 round `c29392c..ed18de5` (#496, #494, #488, #493, #500, #484, #510, #506, #511, #509, #503, #501, #505, the owner's guard patch #497/#498 and the release Tester's two tests; D-230, D-231) found no BLOCKING. #496's one status reader closes M8 and R6 in every Python reader. #488 takes `NSAllowsLocalNetworking` out of a Release build. The deploy gate now reads every base object through one hash-checking reader and compares the tree by content. #484's Settings door is one pinned file. The guard patch is the owner's, and both hooks pin its sha256. Its three MINORs: M9 (the release Tester's M11, confirmed and routed to the owner as Escalate-NOW class): `GIT_WORK_TREE` makes `make deploy-check` and `deploy_gate.py "fly deploy"` judge another checkout and PASS. The guard's `--judge` is not fooled. M10: the owner's v-tag rule lets `git tag -m -l v1.0` through, because an option's value is read as a flag. M11: a local `INFOPLIST_OTHER_PREPROCESSOR_FLAGS` still gives a Release build the ATS exception. None reaches tonight's deploy, provided the owner deploys by hand from their own shell with no `GIT_*` variable set and the `tree` line of `make deploy-check` names the checkout being deployed.

The night-1028 round's verdict, as it read when it closed: MINOR: BLOCKING 0 · MAJOR 0 · MINOR 1 open (M8 from the night-1028 round, to be filed; M1-M2 closed by #453 via #489, M6-M7 closed by #478 and #479 via #490, each verified in the night-1028 round; M5 closed with #471; M3 fixed in `9683734`; M4 closed by #474, D-227) · NIT 0 · risks queued 8 open (R1-R6 as before; R8-R9 from the night-1028 round; R7 closed by #477, which removed the entry). The night-1028 round `718cae4..c29392c` (D-229, eleven issues, build 7) found no BLOCKING: the #453 build child now runs with `-P` inside the cycle's clocks, the #466 status reader and the #477-#479 policy loader fail closed on every shape their issues name, #444's deploy-gate change only tightens (its own verdict, `docs/reviews/fix-issue-444-security.md`), and the #481 guide opens no URL; its one MINOR (M8) is that every reader of the refresh's status record still crashes on a deeply nested file, the #466 class by another road. #493, the escalated gate bypass #444's review found, stays open and is the run's stop (R9); `git fsck --full` finds no forged object in this repository's store today. The night-1027 round `50c4764..718cae4` (#473, #474, #476) found no BLOCKING: D-227 closes M4 on the one path that skipped the bound, and D-228's re-spellings change only how the guards read the candidate, never what is published, fail closed on every malformed file probed, and owe exactly a cut's ADR and expiry; its MINORs are that a pair excuses its model's every row rather than its named rows (M6), and that a duplicate key in the policy file silently overrides the first (M7). The 2026-10-27 round `9ef6448..50c4764` (#470, D-224, build 6) found no BLOCKING: the guard's retirement changes the verdict only of commands that name the two deleted launchd scripts (23 of 850 probed), and both hooks pin the guard file's actual sha256; its one MINOR (M5) is the `launchctl` line the retirement took out of the guard's own "Not held" list. The hotfix-1026 round `0222150..9ef6448` (#459, #460, #461) found no BLOCKING: D-225's republish publishes only the running release's own fresh build of content equal to what is served, after the W-047 re-read, so it launders nothing past the deploy's #198 refusal; its one MINOR (M4) is the serving-bound check it skips.

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

## Delta round 2026-10-27 (9ef6448..50c4764)

**Reviewer:** Security-Reviewer subagent, dispatched by `/going-live` step 2 for the deploy delta before tonight's hosted deploy. I read the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` from `main`.
**Independent:** yes. I wrote none of this range's code, tests or records, and none of the Tester's verdicts on it.
**Range:** `9ef64482ae331c65491ef2675289b22caa5db0da..50c4764bd94ffaa21201eaffaa6892f65c07e811` on `release/v0.2.0`, 11 commits, with the Tester's verdict `96c6791` on top (docs only). Code: `.claude/hooks/bash_guard.py` (-20/+2) and `.claude/settings.json` (the re-pin), both the owner's patch `b9b7c1b` (#470, D-224, #284, no `GP-Agent` trailer); `tests/unit/test_bash_guard_bounds.py` (`b9b7c1b`, then the Tester's `50c4764`); `ios/ModelRanking.xcodeproj/project.pbxproj` (`b72de72`, build 6). The rest is records.
**Reviewed head:** 50c4764bd94ffaa21201eaffaa6892f65c07e811. I added no test.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). `make review-need` routes the range to security because it changes gate or control code (#283). I read the guard change at MEDIUM depth. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-1027` at `50c4764`, under `$TMPDIR`. The main clone's `.venv` interpreter with `PYTHONPATH` at the worktree's `src`. Probes loaded the guard at `9ef6448` and at `50c4764` as modules from a scratch directory outside the tree and only called `judge_call`, which judges and runs nothing. No edit in the main checkout, no network call, no launchd, Fly or GitHub access.

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 1 (M5) · risks queued 0.

### Findings

#### BLOCKING
- none

#### MINOR
- **M5** `.claude/hooks/bash_guard.py:243-262` (the "Not held, by class" list). **The retirement took out the line saying that `launchctl` itself, a script that runs an installer, and a renamed copy are not held, but those classes are still not held.**
  - Removed in `b9b7c1b`: "the owner's launchd service changed by `launchctl` itself, by a script that runs the installer, or by a copy of it under another name (#284)".
  - Probe, both guard versions: `launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.ilgar.modelranking.engine.plist`, `launchctl bootout ...`, `cp x.plist ~/Library/LaunchAgents/`, `echo x > ~/Library/LaunchAgents/a.plist` and `plutil -replace ... ~/Library/LaunchAgents/a.plist` are all allowed. No rule caught them before this range, and none catches them now.
  - `permission-matrix.md`, `docs/refusals.md` and `docs/security-baseline.md` do not name `launchctl` or `LaunchAgents` either (`git grep -n -i "launchctl\|launchd"` finds nothing in them). The guard's list was the one place that said it.
  - Why it matters: the list exists "so nobody believes otherwise". An agent that changes the owner's machine through a LaunchAgent is still an unguarded class. The watchlist row (`docs/watchlist.md:53`) names "a launchd service ... again" as the trigger that brings the rule back, but nothing tells the next reader that the gap exists today.
  - Why MINOR: the removal weakens no refusal, as the differential below shows. The owner's service is gone (the remover ran before `1ab57a0`, D-224 clause 3), and the text is documentation only.
  - Remedy, the owner's (the agent may not write `.claude/`): at the next guard patch, put back one class line without the script names, for example "the owner's machine changed through `launchctl`, or a plist written under `~/Library/LaunchAgents` (#284)", then `make guard-pin`. Until then, a row in `docs/owner-actions.md`.

#### PASS (with evidence)
- **Is any refusal weakened?** No.
  - Differential: I fed 850 commands to `judge_call` of both guard versions, with no deploy gate (an empty `OWN` and `$CLAUDE_PROJECT_DIR`). The commands were every string literal in `tests/unit/test_bash_guard_bounds.py` at `9ef6448`, plus 30 probes: `launchctl`, LaunchAgents writes, restore-then-run, glob program words, the deploy script in every form, `.claude/` writes, `core.hooksPath`, `fly deploy`, `rm -rf ~` and a force push.
  - Exactly 23 verdicts changed. Each one went from refused to allowed, and each command names `install_engine_service.sh` or `remove_engine_service.sh`. No other command's verdict changed, and none changed reason.
  - Both scripts are gone from the tree (`eefbe5f` deleted the installer, `1ab57a0` the remover; `git ls-files` lists neither). The retired rule could only refuse a name with nothing behind it.
- **Restoring the deleted installer is still refused.** `git checkout eefbe5f^ -- scripts/install_engine_service.sh && scripts/install_engine_service.sh` is refused by both versions as a destructive `git checkout` (C.9). `git show eefbe5f^:scripts/install_engine_service.sh | bash` is refused at `50c4764` as a shell reading its commands from a pipe. A copy written under another name and then run (`bash x.sh`) was never held: it is "code another program runs" (`bash_guard.py:246`), and that line stays.
- **The removal is exact.** The patch removes the `LAUNCHD`, `LAUNCHD_REMOVE`, `LAUNCHD_READ_ONLY` and `LAUNCHD_SCRIPT` constants, the two names from `GUARDED`, the one `judge_words` branch and its two docstring paragraphs. The remaining `GUARDED` set (`bash_guard.py:414-415`) and the deploy script's rule (`:413`, `:1745`) are byte-identical in meaning. `git grep` finds no remaining reference to the retired names in code. The test file's surviving mentions are comments, and `tests/unit/test_engine_service.py` asserts their absence.
- **The pin is the guard's actual file.** `shasum -a 256 .claude/hooks/bash_guard.py` at `50c4764` gives `36cf17e8484a9cc4740aa2ed2e6e52fafa7979590d916390f1d86bd28ada0961`. That is the only 64-hex value in `.claude/settings.json`, at `:79` (Write/Edit hook) and `:90` (Bash hook), and both short forms in the messages say `36cf17e8484a`. The old guard at `9ef6448` hashes to `728db666f6c2...`, the old pin. `.claude/hooks/guard_pin.py --check` gives `guard-pin PASS ... 36cf17e8484a`. No other file pins the guard: `728db666` survives only in two earlier review records.
- **A later edit cannot slip past the pin.** Each hook hashes `$r/.claude/hooks/bash_guard.py` and runs that same path only on a match, otherwise exit 2 (`onFailure: block`). An unpinned edit therefore fails closed, and both the guard and `settings.json` sit under `.claude/`, which the Write/Edit hook and the Bash guard refuse to agents. The hash-then-run window predates the range and needs a `.claude/` writer to use it.
- **The Tester's `50c4764` restores the right case.** `tests/unit/test_bash_guard_bounds.py:737` (`bash scripts/deploy_hosted_engine.sh --help`, `sh scripts/deploy_hosted_engine.sh --version`) holds a guarded script file, not a `-c` string, read past a shell's trailing `--help` (`bash_guard.py:2750-2752`). A shell treated as "help only" would let the deploy script run and turn the test red. `:755` keeps an all-caps directory and file case for the deploy script.
- **Build 6** (`b72de72`): `project.pbxproj` changes only `CURRENT_PROJECT_VERSION` 5→6 in four configurations. Signing style, bundle ids, entitlements and `Info.plist` are unchanged.
- **Authority.** The `.claude/` change is the owner's own commit (`b9b7c1b`, no `GP-Agent` trailer, merged through PR #470). No agent commit in the range writes `.claude/`, `.githooks/` or `.github/workflows/**`. No commit adds `reset --hard`, a force push, `rm -rf` or `DROP`, and no commit message carries AI attribution: the only "claude" hits are the `GP-Agent: claude-code` trailers and a `.claude/` path.

### Gates passed (delta)
- [x] Secret scan green: `make secrets` on `f32cdbf`, no leaks found (dispatcher). Re-run here: `gitleaks git --log-opts=9ef6448..50c4764` gives `no leaks found`.
- [x] `make deps` green on `f32cdbf` (dispatcher). No lock, `pyproject.toml` or requirement changed in the range.
- [x] `make slopsquat` PASS on the same manifest (dispatcher). There is no new import: the test file's edits are parameter strings.
- [x] Default-deny preserved: no route, endpoint or external surface added. The control change removes a rule over deleted files only (differential above).
- [x] Permission matrix not violated: the `.claude/` change is the owner's patch. It is recorded as a retired control in `docs/watchlist.md:53`, with the trigger that brings it back.
- [x] Prompt-injection hygiene: nothing in the range feeds fetched text to a model or an agent, and no diff content tried to change policy.
- [x] Auth/PII and the human-review trigger: not applicable (no HIGH path; no auth, PII, payment or migration code).
- [x] SAST: no `src/` file changed, so there was nothing new for `ruff --select S` or `bandit`. Conformance PASS, 33 tests (dispatcher). Run here at `50c4764`: `tests/unit/test_bash_guard_bounds.py` gives `686 passed`, and `conformance/test-bash-guard.py` reports 591 tool calls with 0 wrong verdicts. The coverage-floor message is expected on a partial run.

### Acceptance criteria evidence (delta)
- **D-224 / #284** (the guard's rules for the deleted launchd installer and remover retire with them). Code: `.claude/hooks/bash_guard.py:413-415` (`GUARDED` without them) and `:1745` (only the deploy script's rule left in that place). Tests: `tests/unit/test_bash_guard_bounds.py:737` and `:755` (the guarded-script `--help` case and the case-insensitive name now held by the deploy script). The differential above shows no other verdict changed. Record: `docs/watchlist.md:53`.
- **The re-pin.** `.claude/settings.json:79`, `:90` equal the guard's sha256. Check: `.claude/hooks/guard_pin.py --check` PASS.
- **Build 6.** `ios/ModelRanking.xcodeproj/project.pbxproj`, `CURRENT_PROJECT_VERSION = 6` in all four build configurations.

### Risks queued (delta)
- none

## Delta round 2026-10-27 night-1027 (50c4764..718cae4)

**Reviewer:** Security-Reviewer subagent, dispatched for the deploy delta before tonight's hosted deploy. I read the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` from `main`.
**Independent:** yes. I wrote none of this range's code, tests or records, and none of the Tester's verdicts on it.
**Range:** `50c4764bd94ffaa21201eaffaa6892f65c07e811..718cae416dc4b20ab9a39a10295b8e6b61aadfd9` on `integration/night-1027`, with the release Tester's round (`07a7fc6` tests, `4a19f6b` verdict) inside it. Code: `src/app/workflows/refresh.py` (+160/-17: #474, D-227, `_why_unchanged`; #476, D-228, `parse_accepted_respellings`, `respelled`), `data/accepted-cuts.yaml` (the first `respellings` entry: 27 `text_to_image` pairs, until 2026-11-10), tests `tests/unit/test_accepted_respellings.py` (new), `tests/unit/test_accepted_cuts.py`, `tests/unit/test_release_restamp.py`. #473 is records only (the owner's guard patch lives in a gitignored `build/` file, outside this range).
**Reviewed head:** 718cae416dc4b20ab9a39a10295b8e6b61aadfd9. I added no test.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). `make review-need RANGE=50c4764..HEAD` routes the range to security for one signal, "policy edit: data/accepted-cuts.yaml" (D-221 clause 4). I read the refresh change at MEDIUM depth, because the file is an exception to four refresh guards (D-128, D-132, D-159, D-164). No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-1027b` at `718cae4`, under `$TMPDIR`, with its own `.venv` from `make install` (the hash-checked locks), `app.__file__` resolving into the worktree, and the gitignored `advisor.db` copied in. Probes ran from a scratch directory outside the tree with `python -I`, against hand-built `ServingSummary` values and parser input; none wrote the tree. No edit in the main checkout, no network call beyond the locked install, no launchd or Fly access, and GitHub read-only (`gh issue view 467 475 477`, `gh issue list`).

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 2 (M6, M7) · risks queued 1 (R7). Nothing here blocks tonight's deploy.

### Findings

#### BLOCKING
- none

#### MINOR
- **M6** `src/app/workflows/refresh.py:443-454` (`_respelled_ids`), applied by `:414-440`. **A pair moves its whole model, so one listed name excuses every row of the old model and admits every row of the new one, listed or not.**
  - The pair `old -> new` is tested by name, but what it changes is model-level: `respelled` rewrites every `LinkedRow` of the candidate's model `n` as the served model `o` (`_moved_rows`, `:457-461`). Any other row of `o` that left the board, and any other row that arrived linked to `n`, are then read as kept, as long as the counts match.
  - Probe: a served board of 6 rows, three of them one model `o` (`seedream-4-2k`, `seedream-4-fal`, `seedream-4-hr`). The candidate has three rows of a new model `n` (`Seedream 4.0 (2K)`, `Seedream 4.0 (fal)` and `UNLISTED`). With no pair, the guards refuse: "would lose 3 of 6 rows" and "would be 3 of 6 rows this artifact has never seen". With the one pair `seedream-4-2k -> Seedream 4.0 (2K)`, nothing is refused. Two unlisted old names and one unlisted new name rode on that one pair.
  - D-228's rationale says pairs "name exactly the rows the owner accepted". For cuts, D-221 clause 2 ruled the opposite after the #418 review: a cut excuses "a row by its own raw name, never by model". The re-spelling exception brought back the by-model reading that cuts gave up, and no ADR records that choice. `tests/unit/test_accepted_respellings.py:276` holds a model with two rows under the same raw name, never a model with two names, one of them unlisted.
  - Why MINOR, not BLOCKING: the latitude matches what a model that keeps its id already gets (a `LinkedRow` ignores raw names, D-179). Using it needs an upstream that sends a listed new name deriving a model the board never had, and only rows that link to that same derived id ride along. It is bounded to `text_to_image`, to the night of the first publish (after it the pairs are inert, `:447-450`), and to 2026-11-10. The Tester measured tonight's board as 82 rows in and 82 out.
  - Remedy: in `_respelled_ids`, accept a found `(n, o)` only when every raw name of `o` on the served board is a listed old name and every raw name of `n` in the candidate is the listed new name of one of them, i.e. `before[o] <= pairs.keys()` and `after[n] == {pairs[x] for x in before[o]}`. Add the probe above as a test. Alternatively, amend D-228 so it says the excuse is by model and why, and correct the "exactly the rows" rationale. File before the next `respellings` entry.
- **M7** `src/app/workflows/refresh.py:321-330` (`_accepted_doc`, through `src/app/workflows/yaml_guard.py:104`), and `:338`, `:390`. **A duplicate mapping key in the policy file silently overrides the first, and a non-scalar `board:` crashes with `TypeError` instead of the schema error.**
  - PyYAML's `safe_load` keeps the last of two equal keys. Probes against `parse_accepted_respellings`:
    - two lines `"a": "B"` then `"a": "C"` under `pairs:` parse as `{'a': 'C'}`;
    - an entry whose first key is `board: coding` and a later one `board: text_to_image` parses as `text_to_image`;
    - two `until:` keys keep the second;
    - a second top-level `respellings: []` drops the first list without a word.
  - The file is policy that a security review reads line by line (D-221 clause 4). The new `pairs` map is its first map whose keys are data, 27 of them in one block, so a later duplicate can quietly retarget a pair the reviewer read earlier. Each override still has to pass the schema, the ADR (which must name the effective board) and the 30-day cap, so the exception cannot widen past what a well-formed entry could say. The risk is that the reviewed text and the effective policy differ.
  - `board: [text_to_image]` or `board: {x: 1}` raises `TypeError: unhashable type` at `board not in known` (`:338` for cuts, `:390` for re-spellings), not `AcceptedCutError`. The night still fails closed: `main` records `crashed: TypeError` and exits `EXIT_FAILED` (`:1921-1926`), and nothing publishes. Only the message is wrong. This was already true of cuts before the range.
  - Why MINOR: every case fails closed or narrows to a schema-valid entry, and a duplicate is visible in the diff a reviewer reads.
  - Remedy: refuse duplicate keys in `_accepted_doc`, or for every curated YAML in `safe_load_bounded`. Walk the composed node (it is already composed at `yaml_guard.py:125`) and refuse any `MappingNode` whose key values repeat. Check `isinstance(board, str)` before `board not in known` in both checkers. Add one test per shape.

#### PASS (with evidence)
- **D-227 closes M4, and the bound check now covers every publish path.** `_why_unchanged` (`refresh.py:1408-1424`) runs `egress_problems(candidate, bounds_from_env())` on every `same` cycle that would republish under D-225. If the candidate is past a bound, the cycle returns `EXIT_UNCHANGED` with the bound named, and nothing is published (`:1790-1806`). The other paths already ran it first: `_reason_to_refuse` (`:1387`) covers a first artifact and a moved night. A `same` night that would not republish publishes nothing, so it needs no check. `tests/unit/test_release_restamp.py:173` reproduces my M4 probe (`MODEL_RANKING_MAX_RANKED_ROWS=1`, a second release). It now asserts `EXIT_UNCHANGED`, a byte-identical served file, `served_built_by` still the first release and `consecutive_refusals == 0`, and it still refuses a moved night at the bound. `live_fingerprint=fresh.digest` (`:1796`) equals `live.digest`, because `quiet` implies `same`. A bad bound variable raises in `bounds_from_env` and fails the cycle closed, as it did on the other path. #467 is still open: it is closed when its PR merges.
- **Nothing published differs from the candidate as built.** `respelled` returns `dataclasses.replace(candidate, ...)` with the candidate's `digest` (`:440`). Only `board`, `boards`, `models` and `spellings` change, and those are inputs to the guards and the record. `surfaces`, `eligible`, `median_price`, `displays` and `accessible` keep their candidate values, so the count, budget and median guards still see the candidate as built. The publish is `candidate.replace(target)` of the built file (`:1841`). `candidate_fingerprint`, the deploy stamp's digest and the `same` decision all read the unchanged digest. `_judged` asserts this (`tests/unit/test_accepted_respellings.py:52`), and so does `:288`. The summary is never written to disk: only `RefreshOutcome` is recorded, and its `renamed` names each accepted pair as `old -> new on <board>`, which is D-228 clause 3 (probe output: `old0 -> NEW0 on text_to_image's board`).
- **A pair cannot hide a real loss, and cannot carry an injected set past its own names (M6's model latitude aside).** Probes with hand-built summaries, a 12-row board:
  - four listed new names linked to models the board already had stay refused: "would lose 4 of 12", three reasons (`now[new] not in before`, `:450`);
  - a revert after the publish, old names coming back, is refused: inert, because `old in was` fails;
  - the listed swap plus unlisted injected models is judged as before, because the injected rows are not moved.

  The shapes the Tester added (`tests/unit/test_accepted_respellings.py:247-273`: the old model stayed, onto a kept model, the old name stayed, the new name was served, after the publish) each hold one condition of `:448-450` on its own. `:95` holds the one-to-one rule. A pair named for one board changes nothing on another (`:69`). Unlinked rows are never moved (`_moved_rows` keeps `UnlinkedRow` as it is), and an unlinked new name is not in `now`, so its pair is inert. The one case that passes by design is an upstream that removes a listed old model and adds a different model under exactly the listed new name: that is the owner's acceptance of that name (R7).
- **A malformed or hostile file fails closed.** 24 probes against `parse_accepted_respellings`:
  - Raise `AcceptedCutError`: an alias bomb (refused by the expansion bound, "expands to 1234567909 nodes"); nesting 5,000 deep (refused by the depth guard); an unhashable mapping key; a `!!python/object/apply` tag (`safe_load`: no constructor); int, bool and null names or values; a name with no letter or digit; a `datetime` `until:`; an `until:` 44 days out; an ADR the log does not hold; a blank reason; one board named twice; `respellings:` null; `cuts` missing.
  - Accepted as schema-valid: a YAML merge key (`<<: *p`) inside `pairs`. The merged pairs are checked like any other, and the schema rejects a merge at the top level. Duplicate keys are M7.
  - An `AcceptedCutError`, or anything else the loader raises, propagates out of `_cycle` (`:1784`). `main` turns it into `EXIT_FAILED` with nothing published (`:1921-1926`). `tests/unit/test_accepted_respellings.py:202` holds this through the real entry. The loader runs on every cycle, including `same` nights and a first artifact. So a broken or expired file now stops nights the cuts loader never reached. That is closed, not open, and its dated instance is the Tester's M7 (#477, open).
- **The ADR and `until:` rules hold for re-spellings exactly as for cuts.** Both checkers call the one `_check_terms` (`refresh.py:348-359`). It requires an ADR id that is a live header of `docs/decisions.md` outside any code fence, not superseded, and naming the board as a whole word (`_check_cut_adr`, `:477-489`), a non-blank reason, and `today <= until <= today + 30` (`MAX_CUT_DAYS`). Probes above refuse each. D-228 names `text_to_image`, and the committed entry's `until: 2026-11-10` is 14 days out. The re-spelling checker adds what cuts do not need: exactly the five keys, `pairs` a non-empty map of string to string, no identity pair, no shared target, and no name both old and new (`:384-400`). The board may be a surface as well as a declared board (`:372`), as D-228 clause 1 and the D-221 amendment record. The cuts parser accepts a file that holds re-spellings without reading them (`:327`), and only `_cycle` consumes them (`:1784`). So no reader skips their validation: `git grep` finds no other consumer of `data/accepted-cuts.yaml` outside tests and `scripts/review_need.py:90`.
- **The routing still sees the file.** `scripts/review_need.py:90` lists `data/accepted-cuts.yaml` as an exception file, and its signal routed this range here.
- **Destructive operations and authority.** No commit in the range adds `reset --hard`, a force push, `rm -rf` or `DROP`, or writes `.claude/`, `.githooks/` or `.github/workflows/**` (`git diff --name-only 50c4764..718cae4`: ten files, all under `data/`, `src/`, `tests/` and `docs/`). Every agent commit carries a `GP-Agent:` trailer (`claude-code` or `tester`), and none carries AI attribution. The new owner-actions row (#473) hands the owner a patch with a pinned sha256 and `make guard-pin`. The agent did not write the guard.

### Gates passed (delta)
- [x] Secret scan green: `make secrets` at `ac7bba9`, no leaks found (dispatcher). Re-run here: `gitleaks git --log-opts=50c4764..718cae4` gives `no leaks found`. The 27 pairs are public model names.
- [x] `make deps` green at `ac7bba9`, "No known vulnerabilities found" (dispatcher). No lock, `pyproject.toml` or requirement changed in the range.
- [x] `make slopsquat` PASS (dispatcher). There is no new import: `git diff 50c4764..718cae4 -- src` adds no `import` line. The new test imports `datetime`, `sqlite3`, `pathlib`, `pytest` and `app` modules, all already in use.
- [x] Default-deny preserved: no route, endpoint or external surface added. The exception is opt-in per board and per pair, and an absent file accepts none (`refresh.py:403-411`).
- [x] Permission matrix not violated: no agent write to `.claude/`, `.githooks/`, `.github/workflows/**`, `Dockerfile` or `fly.toml`.
- [x] Prompt-injection hygiene: upstream names reach only the night's record (`renamed`), as before the range. Nothing feeds fetched text to a model or an agent, and no diff content tried to change policy.
- [x] Auth/PII and the human-review trigger: not applicable (no HIGH path; no auth, PII, payment or migration code).
- [x] SAST: `bandit` and `semgrep` are not installed in this seat. `ruff check --select S src/app/workflows/refresh.py src/app/workflows/yaml_guard.py` gives "All checks passed!". Conformance PASS, 33 tests, 0 failing (dispatcher, `ac7bba9`). Tests here at `718cae4`: the three delta files give `106 passed`, and `tests/unit -k "refresh or cut or respell or restamp or yaml or egress or bound"` gives `1260 passed, 1 skipped` (the Epoch bundle test, which needs the owner's download). The coverage-floor message is expected on a partial run.

### Acceptance criteria evidence (delta)
- **D-227 clauses 1-2** (a republish runs the bound check; past a bound it stays unchanged, names the bound, and counts no refusal). Code: `src/app/workflows/refresh.py:1408-1424`, `:1790-1806`. Test: `tests/unit/test_release_restamp.py:173`.
- **D-227 clause 3** (the other content refusals stay skipped on a republish; the re-read stays). Code: `refresh.py:1813-1814`. Tests: `tests/unit/test_release_restamp.py:35`, `:150`.
- **D-228 clause 1** (the schema, a cut's terms, fails closed). Code: `refresh.py:321-330`, `:348-359`, `:366-400`. Tests: `tests/unit/test_accepted_respellings.py:116`, `:122`, `:148`, `:153`, `:202`, `:208`.
- **D-228 clause 2** (a pair is judged as the row it was, only when it is a re-spelling; one board; one to one). Code: `refresh.py:414-454`, `:1784`. Tests: `tests/unit/test_accepted_respellings.py:56`, `:64`, `:69`, `:74`, `:87`, `:95`, `:191`, `:268`, `:276` (M6 is the part no test holds).
- **D-228 clause 3** (what is published is the candidate as built; the record names each pair). Code: `refresh.py:440`, `:1787`. Tests: `tests/unit/test_accepted_respellings.py:52`, `:288`.
- **D-228 clause 4** (the first entry). `data/accepted-cuts.yaml:16-49`, 27 pairs, `until: 2026-11-10`. Test: `tests/unit/test_accepted_respellings.py:208`. Its expiry is the Tester's M7 (#477).

### Risks queued (delta)
- **R7** `data/accepted-cuts.yaml:16-49`. **Until tonight's first publish, the 27 listed new names are trusted as successors whatever model they derive.**
  - An upstream that dropped a listed model and added a different one under exactly its listed new name would pass the board and novelty guards. Probe "Hostile listed-name swap": 0 reasons. That is the acceptance D-228 makes, and scores were never guarded.
  - The window closes on its own. The first night that publishes makes every pair inert (the served board holds the new names), and the entry fails the refresh after 2026-11-10.
  - Revisit: remove the entry in the PR that follows the first publish, which #477 already asks for. A second `respellings` entry should name the measured candidate ids beside the names, so a pair binds a model as well as a name.

## Delta round 2026-10-29 night-1028 (718cae4..c29392c)

**Reviewer:** Security-Reviewer subagent, dispatched for the deploy delta before build 7's upload and the merge of #483. I read the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` as the session loaded them; nothing in the range edits them.
**Independent:** yes. I wrote none of this range's code, tests or records, none of the Tester's verdicts on it, and neither per-fix security verdict in it (`fix-issue-477-security.md`, `fix-issue-444-security.md`).
**Range:** `718cae416dc4b20ab9a39a10295b8e6b61aadfd9..c29392c6847ef1d3857711ed00bc8d9263efcd37` on `integration/run-night-1028` (draft PR #483), 33 files. The record is `docs/plans/run-night-1028.md`, the rulings D-229. Code: `src/app/workflows/refresh.py` (#453 the build child, #466 `write_status`, #478 `_respelled_ids`, #479 the board type), `src/app/workflows/build.py` (#453 `--fetch-seconds`), `src/app/workflows/yaml_guard.py` (#479 `unique_keys`), `scripts/deploy_gate.py` and `scripts/review_need.py` (#444), `conformance/test-ci-yaml.py` (#457), `data/accepted-cuts.yaml` (#477, the D-228 entry retired), `ios/ModelRanking/ContentView.swift`, `Engine/FrontDoor.swift`, `Engine/Language.swift` (#481), `project.pbxproj` (build 7). Tests only: #463, #452, #456, and the release Tester's `0f1837f` (which also adds M9's `accessibilityLabel`).
**Reviewed head:** c29392c6847ef1d3857711ed00bc8d9263efcd37. I added no test. `0f1837f` is the last commit that changes code (`ContentView.swift:610`); `3cddbdd` and `c29392c` change `docs/` only.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). `make review-need RANGE=718cae4..c29392c` routes the range to security for gate or control code (`conformance/test-ci-yaml.py`, `scripts/deploy_gate.py`, `scripts/review_need.py`), a sensitive name (`scripts/deploy_gate.py`), a new parser of untrusted input (`json.loads`) and policy edits (`data/accepted-cuts.yaml`, the plan). I read it at MEDIUM depth. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-1028` at `c29392c`, under `$TMPDIR`, with its own `.venv` from `make install` (the hash-checked locks, D-174), `app.__file__` resolving into the worktree. No `advisor.db` copied in. Probes ran from a scratch directory outside the tree with `python -I` (one, the planted-module probe, with `-P` from a directory holding a planted `app/`); none wrote the tree. No edit in the main checkout, no network call beyond the locked install, no launchd or Fly access; GitHub read-only (`gh issue view 471 493 494`, `gh issue list`).

**Leaned on, not repeated.** `docs/reviews/fix-issue-477-security.md` (MINOR, reviewed head `c9d6584`) for #477-#479, and `docs/reviews/fix-issue-444-security.md` (MINOR, reviewed head `fba96ba`) for #444. After `c9d6584` the policy code changed once, in `a56cf3d`, which I re-probed below. After `fba96ba` `scripts/` and `src/` did not change (`git diff --stat fba96ba c29392c -- scripts src conformance` lists tests only), so I did not re-review the deploy gate; #444's M1-M3 are #494 and its R1 is #493.

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 1 (M8) · risks queued 2 (R8, R9). Nothing here blocks build 7's upload or the merge of #483 once `make deploy-check` is green; R9 (#493) is the owner's stop and stays open.

### Findings

#### BLOCKING
- none

#### MINOR
- **M8** `src/app/workflows/refresh.py:1185-1188` (`write_status`), with `:1151` (`_another_release_built`), `:1463-1464` (`_read_last_ok`) and `src/app/adapter/nightly.py:143` (`read_record`). **Every reader of the refresh's status record catches `ValueError` but not `RecursionError`, so a deeply nested `.refresh.json` still crashes every cycle: the #466 class by another road.**
  - #466's fix reads a record that is valid JSON but not an object as none (`:1188`), and its test holds `[]`, `"x"`, `3` and `null` (`tests/unit/test_refresh_carry.py:528-538`). `json.loads` on a 200,000-deep array or object raises `RecursionError`, a `RuntimeError`, which none of the four `suppress`/`except` clauses names.
  - Probe, each reader against a status file holding `"[" * 200000 + "]" * 200000`: `write_status` raised `RecursionError`; so did `_read_last_ok`, `_another_release_built` (with `APP_BUILD=release-x`) and `nightly.read_record`. The other shapes I tried were read as before: a 5,000-digit integer, `1e400`, `NaN`, invalid UTF-8, a list `sources_last_ok`, a boolean `consecutive_refusals`.
  - Effect: the cycle fails loud and closed (`main` prints `crashed: RecursionError` and returns `EXIT_FAILED`, `:1960-1965`), but it never rewrites the record, so every later night crashes the same way. That is the "never recovered" state #466 was filed for, and the stale record is the state D-129 forbids. `_read_build_sources` and `_read_build_list` (`:1478-1479`, `:1501-1502`) share the pattern, on files the build child writes.
  - Why MINOR: reaching it needs a write to the engine's volume. The cycle itself writes the record with `json.dumps` and never nests it.
  - Remedy: read the record through one helper that returns `{}` on `OSError`, `ValueError` or `RecursionError`, or for anything that is not a dict, and use it in the four readers (and the two build-report readers). Add the deep-nesting probe to `test_a_previous_record_that_is_not_an_object_is_read_as_none`'s parameters. **Needs a new issue.**

#### PASS (with evidence)
- **#453 closes the first round's M1 and M2.**
  - `-P`: the default child command is `[sys.executable, "-B", "-P", "-m", "app.workflows.build"]` (`refresh.py:1646`), as at `nightly.py:227` and `arena_slices.py:105`. I re-ran M1's probe: a parent with `-P` in a directory that holds a planted `app/workflows/build.py` printed the real build's help, not `PLANTED build`. `tests/unit/test_refresh_build_child.py:154` pins the flags.
  - The cycle's clock: `_Limits` sets `_CycleClock.ends` when it arms the alarm and clears it on close (`refresh.py:132`, `:151`). The child's limit is `min(BUILD_LIMIT_SECONDS, deadline - 120 s - now)` (`:1643`), so the cycle always outlives the child and writes why. A negative remainder kills the child at once: `Popen.wait(timeout=-30)` raised `TimeoutExpired` after 0.0 s, so the night returns `EXIT_BUILD_KILLED` and publishes nothing. Tests: `:171`, and the Tester's wiring test `:182`.
  - The fetch budget: the parent hands the child `--fetch-seconds max(0, ends - now)` (`:1644-1645`), and `build.main` wraps `build()` in `cycle_budget(args.fetch_seconds)` (`build.py:994-1004`). Tests: `test_refresh_build_child.py:211`, `:233`.
  - The progress reader drops `nan` and `inf` stamps (`refresh.py:1682`; test `:256`).
- **`--fetch-seconds`: what a negative, `nan` or `inf` value does.** I probed `_within_the_cycle` under `cycle_budget(v)`:
  - `-5`, `0`, `-inf` and `1e-9` refuse every fetch ("the refresh cycle's time budget is spent"). Each source then fails and carries its last good data (D-156). That is closed.
  - `nan`, `inf` and `1e308` leave each fetch its own deadline (120 s): `nan <= 0` is false and `min(120, nan)` is 120. The budget is off, as for a build run by hand. That is open, but still bounded by the per-fetch deadline and by the parent's kill of the child (`:1643`).
  - The parent cannot send any of them. `FETCH_BUDGET_SECONDS` and `CYCLE_LIMIT_SECONDS` are constants (`:101`, `:109`), `max(0.0, x)` turns a `nan` remainder into `0.0`, and `:.1f` writes only finite numbers here. The child's argv is not an input anyone else controls. R8 queues the hardening.
- **#466:** a non-object record is read as none in `write_status` (`refresh.py:1186-1188`). The other three readers already checked `isinstance(..., dict)` before the range (`:1153`, `:1465`, `nightly.py:146`). M8 is the one shape left.
- **#477-#479, and the #477 round's M1-M4, fixed in `a56cf3d`.** I re-probed through `safe_load_bounded(..., unique_keys=True)` and the two parsers:
  - Refused: a merge key `<<: *p`, the explicit `!!merge` tag, `<<: [*p]`, a quoted `"<<"` written twice, a repeated key inside a sequence's mapping, and a repeated key inside an anchored mapping that is later aliased (`yaml_guard.py:169-175`).
  - A repeated key inside a mapping used as a key is refused by PyYAML's own `ConstructorError`. Constructor-equal keys (`yes`/`true`) still merge, which cannot reach a valid policy, as the #477 round recorded.
  - The walk is linear: 100,000 keys in one mapping took 0.14 s (`Counter`, `:172`; test `test_accepted_respellings.py:371`).
  - `board: [text_to_image]` and `board: {x: 1}` now raise `AcceptedCutError` in both parsers (`refresh.py:340`, `:392`; test `test_accepted_respellings.py:387`).
  - The #477 round's M4 probe (served `A{a1,a2}`, `X{b2,x}`; candidate `B{b1,b2}`, `X{x}`) now moves nothing, and the two-name control still moves `B -> A` (`refresh.py:453-464`).
  - With the D-228 entry gone, the file holds `cuts: []` and no `respellings` (`data/accepted-cuts.yaml:19`), so no exception is live tonight. The Tester's added shape `a-new-name-the-pairs-do-not-list` and the loaders' default (`test_accepted_respellings.py:278`, `:352`) close the #477 round's R1.
- **#444: no loosening after `fba96ba`.** The only later change is the Tester's `Release.yml` case (`tests/unit/test_deploy_gate_444.py:64-68`), which adds a refusal. `scripts/review_need.py:92` adds `docs/devflow-pin.txt` to `EXCEPTION_FILES`, which only adds routing (test `test_deploy_gate_444.py:105`, `:115`).
- **#457 and #456 only tighten.** `conformance/test-ci-yaml.py:262-266`, `:298-302` adds a self-proof sample that fails the check if the fallback parser renames a step after its `with: name:`. Conformance here: `test-ci-yaml PASS: 34 step(s) checked, 0 finding(s)`. `tests/unit/test_nightly_hosted.py:483-494` turns a missing installed nightly workflow from a pass into a failure. Neither touches `.github/workflows/**`.
- **#481 opens no URL and adds no surface.** The guide is static text in both languages (`FrontDoor.swift:221-303`). The caption and help line open a sheet only when the model is not available (`FrontDoor.swift:239`, `ContentView.swift:598-617`, `:699`). The sheet has one button, "Done" (`ContentView.swift:811`). `UIText.openSettings` is declared and drawn nowhere, and #484 holds that exception for the owner. `git grep 'openURL\|UIApplication.*open\|URL(string'` over `ios/ModelRanking` finds the same three `EngineClient.swift` lines as at `718cae4`. `scripts/client_decl_gate.py`: `client-decls PASS: 22 client file(s) in 4 configuration(s)`. The guide says nothing about the reader and logs nothing. M9's label (`ContentView.swift:610`) repeats the caption's own words, so VoiceOver says what the screen shows.
- **Build 7** changes `CURRENT_PROJECT_VERSION` from 6 to 7 in four configurations (`project.pbxproj:239`, `:260`, `:280`, `:296`) and nothing else. Signing style, entitlements, `Info.plist` and ATS settings are unchanged; #488 (`NSAllowsLocalNetworking` in every build) predates the range and is still open.
- **The Tester's tests (`0f1837f`) and the test-only issues (#463, #452).** They add no network: one `respx` mock (`test_terminalbench_4.py:209`), and `Popen` replaced by a recorder. They write only under `tmp_path`. The wiring test arms a real `_Limits(600, 60)` and closes it in `finally` (`test_refresh_build_child.py:198-202`). The `#463` change widens a linearity sample (`test_arena_respelling.py:98`) and loosens no bound. None of them deletes or weakens a security-invariant test.
- **Across the stack.**
  - The fetch budget reaches the child, but the child's limit is the earlier of its own 25 minutes and the cycle's alarm less two minutes. So a slow night is cut source by source at the budget (carried, D-156), not killed whole, and the cycle always writes its record. M8 is the one way that record write still fails.
  - The policy file is now empty of exceptions, so nothing the re-spelling code moves can act tonight. The loader still runs every cycle and fails closed on a malformed file.
  - The deploy gate's exemption narrowed (#444), and the pin file now routes here.
  - Nothing in the range widens a route, an endpoint, a CORS rule or a token's reach.
- **The object store holds no forged object today.** #493's bypass needs a loose tree object rewritten under its id. `git fsck --full --no-dangling` over the shared store (18,422 loose objects, 17 packs) reports no hash mismatch, no missing object and no error; it prints only three `garbage found` warnings (an interrupted fetch's `tmp_pack`/`tmp_idx` and this worktree's `refs` directory). `git fsck --connectivity-only` is clean. So `make deploy-check` on this store reads genuine trees for `718cae4` and `c29392c`. This is evidence about today's store only; it does not close #493.
- **Destructive operations and authority.** No commit in the range adds `reset --hard`, a force push, `rm -rf` or `DROP`, or writes `.claude/`, `.githooks/`, `.github/workflows/**`, `Dockerfile` or `fly.toml` (`git diff --name-only 718cae4..c29392c`). Every non-merge agent commit carries `GP-Agent:` (`claude-code`, or `security-reviewer` on `c845e94`), and none carries AI attribution (`git log --format=%B` for "Co-Authored" or "Generated with": 0).

### Gates passed (delta)
- [x] Secret scan green: `make secrets` at `c29392c`, no leaks found (dispatcher). Re-run here: `gitleaks git --log-opts=718cae4..c29392c` scanned 35 commits and found no leaks.
- [x] `make deps` green (dispatcher, `make gate` PASS at `c29392c`). No lock, `pyproject.toml` or requirement changed in the range.
- [x] `make slopsquat` PASS, cached at the same manifest (dispatcher). There is no new third-party import: `git diff 718cae4..c29392c -- src` adds `contextlib`, `collections.Counter` and two names from `app.clients.protocols`.
- [x] Default-deny preserved: no route, endpoint or external surface added. The app adds a sheet and opens no URL. The policy file holds no exception.
- [x] Permission matrix not violated: no agent write to `.claude/`, `.githooks/`, `.github/workflows/**`, `Dockerfile` or `fly.toml`. #493's remedy is left to the owner, as D-229 clause 3 says.
- [x] Prompt-injection hygiene: nothing feeds fetched text to a model or an agent. No diff content tried to change policy. The plan and D-229 grant only what the dispatcher stated.
- [x] Auth/PII and the human-review trigger: not applicable (no HIGH path; no auth, PII, payment or migration code).
- [x] SAST: `bandit` and `semgrep` are not in the locks. `ruff check --select S` over `build.py`, `refresh.py`, `yaml_guard.py`, `deploy_gate.py`, `review_need.py` and `test-ci-yaml.py` gives "All checks passed!". Conformance PASS, 33 tests (dispatcher). Tests here at `c29392c`: the eleven touched test files (`test_refresh_build_child`, `test_refresh_carry`, `test_accepted_respellings`, `test_accepted_cuts`, `test_deploy_gate_444`, `test_deploy_gate_pin`, `test_nightly_hosted`, `test_arena_respelling`, `test_osworld`, `test_simplebench`, `test_terminalbench_4`) give `418 passed`. The coverage-floor message is expected on a partial run.

### Acceptance criteria evidence (delta)
- **#453** (`-P`; inside the cycle's alarm and fetch budget; finite times only). Code: `src/app/workflows/refresh.py:132`, `:151`, `:1641-1646`, `:1682`; `src/app/workflows/build.py:938-942`, `:994-1004`. Tests: `tests/unit/test_refresh_build_child.py:154`, `:171`, `:182`, `:211`, `:233`, `:256`.
- **#466** (a record that is not an object is none). Code: `refresh.py:1186-1188`. Test: `tests/unit/test_refresh_carry.py:528`. M8 is the shape no test holds.
- **#477** (the entry retired; the suite reads no committed policy; the night does). `data/accepted-cuts.yaml:17-19`; `tests/conftest.py:313-320`. Tests: `tests/unit/test_accepted_respellings.py:208`, `:343`, `:352`.
- **#478** (a pair names rows, every sibling a re-spelling). Code: `refresh.py:445-464`. Tests: `test_accepted_respellings.py:263-280` (the `_NOT_A_RE_SPELLING` shapes), and the two-name control.
- **#479** (a key written twice, a merge key, a non-name board are refused, in linear time). Code: `yaml_guard.py:105`, `:149-150`, `:158-178`; `refresh.py:326`, `:340`, `:392`. Tests: `test_accepted_respellings.py:328`, `:361`, `:371`, `:387`.
- **#444** (see its verdict). Code: `scripts/deploy_gate.py:252-328`, `scripts/review_need.py:92`. Tests: `tests/unit/test_deploy_gate_444.py:30`, `:69`, `:80`, `:88`, `:105`, `:115`.
- **#456, #457.** `tests/unit/test_nightly_hosted.py:476-494`; `conformance/test-ci-yaml.py:262-266`, `:298-302`.
- **#481, D-229 clause 1** (the caption and help line open a guide for each unavailable state; no first-launch guide; no URL). Code: `ios/ModelRanking/Engine/FrontDoor.swift:221-303`, `ios/ModelRanking/ContentView.swift:598-617`, `:699-705`, `:787-816`. Tests: `ios/EngineTests/FrontDoorTests.swift:893`, `:898`, `:923`, `:936`, `:946`, `:952`, `:959`.
- **D-229 clause 2** (build 7). `ios/ModelRanking.xcodeproj/project.pbxproj:239`, `:260`, `:280`, `:296`.
- **D-229 clause 3** (control changes only tighten). #444: `docs/reviews/fix-issue-444-security.md` ("Q1, no loosening"), and here the test-only delta after `fba96ba`. #456 and #457: above.

### Risks queued (delta)
- **R8** `src/app/workflows/build.py:938-942`, `:994-995`. **`--fetch-seconds` accepts `nan` and `inf`, and either one turns the fetch budget off in the child.** argparse's `type=float` reads both. Under `cycle_budget(nan)` or `cycle_budget(inf)`, each fetch keeps its own deadline. The parent never sends such a value today (see the PASS above), and the parent's kill still bounds the child. So this is open only for a future caller. Revisit: give the option a type that refuses a non-finite or negative number (fail closed), and have `cycle_budget` itself refuse a non-finite `seconds`, the next time either is touched.
- **R9** `scripts/deploy_gate.py:195` (`changed_since`), filed as **#493**, escalated, and recorded as the run's stop (`docs/plans/run-night-1028.md`, "Stops"). This verdict does not close it. A forged loose tree reachable from a reviewed head would hide a code change from `git diff`, and so from this verdict's `**Reviewed head:**` check. Tonight's store passes `git fsck --full`. Until #493 is fixed, run `git fsck --full --no-dangling` once before `make deploy-check` for a deploy that rests on this record. Clean output means the trees the gate diffs are genuine.

## Delta round 2026-10-31 run-1030 (c29392c..ed18de5)

**Reviewer:** Security-Reviewer subagent, dispatched by `/going-live` ("First, `make deploy-check`", step 2) for the deploy delta before tonight's owner deploy. I read `.claude/agents/Security-Reviewer.md`, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` as the session loaded them from `main`. The range edits none of them. It does edit `.claude/hooks/bash_guard.py` and `.claude/settings.json` (the owner's patch, read below as code under review, not as policy).
**Independent:** yes. I wrote none of this range's code, tests or records. I wrote none of its per-change security verdicts (`docs/reviews/fix-issue-{484,493,494,501,505,506,509,511}-security.md`, `docs/reviews/integration-{fixes-1030,run-1030}-security.md`) and not the release Tester's verdict on it.
**Range:** `c29392c6847ef1d3857711ed00bc8d9263efcd37..ed18de5bef8ad54d501b8a268db9900073ab903f`, 50 files, 32 of them code. That is `main` at `290557c` (#512, #513, #514) plus the release Tester's `ed18de5`, which adds two tests. Issues: #496, #494, #488, #493, #500, #484, #510, #506, #511, #509, #503, #501, #505, and the owner's guard patch #497/#498 (`f5b9395`). Rulings: D-230, D-231.
**Reviewed head:** ed18de5bef8ad54d501b8a268db9900073ab903f, the release Tester's head. I added no test and changed no code.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). `make review-need RANGE=c29392c..290557c` routes the range to security for gate or control code (`.claude/hooks/bash_guard.py`, `.claude/settings.json`, `conformance/test-deploy-shipped.py`, `scripts/brief_fields.py`, `scripts/deploy_gate.py`, `scripts/client_decl_gate.py`), a new parser of untrusted input (`json.loads`) and policy edits (#283). I read it at MEDIUM depth, and the deploy gate at HIGH depth, because tonight's deploy rests on it. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** my own detached worktree at `ed18de5` in the session scratchpad (`relsec-wt`), with its own `.venv` from `make install` (the hash-checked locks, D-174; not a symlink) and a copy of the main clone's `advisor.db`.
  - Probes ran in that worktree, and in two more places in the scratchpad:
    - a second detached worktree at `4c314a1` (`relsec-probe/oldwt`), where both verdicts are current, used only as the "other checkout" of M9;
    - a scratch repository (`relsec-probe/tagrepo`) for M10. The Bash guard refused its removal as a work tree, so it is left for the owner (below, "Clean-up").
  - One Release simulator build, unsigned, with its own derived data in the scratchpad, for M11. The planted `ios/Config/Engine.local.xcconfig` was removed after each probe, and `git status` is clean.
  - I made no edit in the main checkout. I did not touch `wtrel`, `wt517`, launchd, Fly or GitHub. The only network calls were the locked install, `make deps` and `make slopsquat`.

**Leaned on, not repeated.** The per-change verdicts above, for the deploy gate's eight fixes: the hashed reviewed head and every tree under it (#493), the flagged index entries (#500), the content comparison (#505), renames (#506), the verified base reads (#509), the one object reader (#511), the declared-command surface (#494, #501) and the Settings door (#484). The stack's own delta verdict `integration-run-1030-security.md` (PASS, reviewed head `91890d6`) checked that every review fix survives the merges. After `91890d6`, `git diff --stat 91890d6..ed18de5` lists docs and the Tester's two tests only. Their open R items are filed as #517, #518 and #522, with fixes on unmerged branches, so they are outside this range.

**First-time attention (reviewed per change by no one):** #496 (`src/app/workflows/status_record.py`, `refresh.py`, `nightly.py`), #488 (`ios/Config/Info.plist`, `ios/Config/Engine.xcconfig`), the owner's guard patch #497/#498 (`.claude/hooks/bash_guard.py`, `.claude/settings.json`), #503 (`scripts/ui_test.sh`), and the release Tester's two tests. I also re-read the deploy gate's entry points (`scripts/deploy_gate.py:940-1010`) for the Tester's M11.

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 3 (M9, M10, M11) · risks queued 1 new (R10).
  - Nothing here blocks tonight's deploy, provided the owner deploys by hand from their own shell, as D-185 has it, with no `GIT_*` variable set (M9).
  - M8 (the previous round's), R1, R6 and R9 are closed in this range.

### Findings

#### BLOCKING
- none

#### MINOR
- **M9** `scripts/deploy_gate.py:940-947` (`toplevel`), `:593-602` (`_redirected`), `:997-1001` (`main`). **The release Tester's M11, confirmed here: `GIT_WORK_TREE` in the environment makes `make deploy-check`, and the argv form `deploy_gate.py "fly deploy"`, judge another checkout and PASS.** This is the #505 review's M2 by another road. It is Escalate-NOW class, because a gate result stays green with no test, and it is routed to the owner.
  - Probe, from my worktree at `ed18de5`. Its own `make deploy-check` FAILs: "32 file(s) changed since the reviewed head c29392c".
    - `GIT_WORK_TREE=<a checkout at 4c314a1> make deploy-check` printed "security: ... MINOR at c29392c, no code changed since", "tester (light mode): ... no code changed since" and "deploy-check PASS". `GIT_DIR=<that checkout's git dir> GIT_WORK_TREE=<it>` gives the same PASS.
    - `GIT_WORK_TREE=<it> python3 scripts/deploy_gate.py "fly deploy"` exited 0 with no message. Without the variable it printed "BLOCKED: deploy gate -- `fly deploy` is a deploy, and 32 file(s) changed".
  - Cause: `toplevel` asks `git rev-parse --show-toplevel`, which honours `GIT_WORK_TREE` and `GIT_DIR`, and every later git call inherits them. `_redirected` reads only `core.worktree`.
  - What does not redirect it, each probed against a new `src/app/evil_probe.py` in a checkout whose verdicts are current (FAIL every time, the new file seen): `GIT_INDEX_FILE` naming a missing index, `GIT_OBJECT_DIRECTORY`, `GIT_CEILING_DIRECTORIES`, `GIT_DISCOVERY_ACROSS_FILESYSTEM`, and `core.worktree` given through `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`.
  - Why MINOR and not BLOCKING tonight:
    - The guard's `--judge` path judges the folder it runs in, with Claude Code's environment, not the command's assignments. So `GIT_WORK_TREE=x fly deploy` from an agent is still refused, held by `tests/unit/test_deploy_gate_505_tester.py:20`.
    - `fly deploy` is the owner's, by hand (D-185).
    - The forged PASS still prints its first line as `deploy-check: tree <the other checkout>` (`:966`), so it is visible to a reader who looks.
    - What can be forged is the `make deploy-check` PASS that `/going-live` and the owner read. That is a control result, so it must be fixed, not accepted.
  - **Remedy:**
    1. At import, beside `os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"` (`:102`), drop every `GIT_*` variable but that one from `os.environ`, so `brief_fields` inherits the clean environment too. Alternatively, refuse while any of `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE` or `GIT_CONFIG_*` is set. Either way, derive the list from `git help -g`/`git rev-parse --local-env-vars`, not by hand (AGENTS.md §3.5).
    2. In `--check`, refuse when the top level differs from the folder `make` was run in.
    3. Add one test per variable, through `--check` and the argv form.
  - Until the fix: run `env | grep '^GIT_'` before `make deploy-check` (empty is clean), and check that its `tree` line names the checkout being deployed.
  - **Needs a new issue.**
- **M10** `.claude/hooks/bash_guard.py:3127-3131` (`_moves_owner_ref`), with `:3231` (`letters`). **The owner's #410 guard patch lets `git tag -m -l v1.0` make a `v*` tag: an option's value is read as an option, so a value spelled like `-l`, `-n` or `-v` turns creation into "listing".**
  - `letters` and `given` (`:3231-3235`) are built from every word that starts with `-`, the values of `-m`, `-F` and `--message` included. The walk at `:3116-3125` skips those values correctly, but the listing test at `:3128` reads `letters` instead of what the walk found.
  - Probe, through `judge_call` (the harness of `tests/unit/test_bash_guard_bounds.py:97`). These were ALLOWED:
    - `git tag -m -l v1.0`
    - `git tag -a -m -n v1.0`
    - `git tag -m --list v1.0`
    - `git tag --message -l v1`
    - `git tag -m=-l v1`
    - `git tag -F -l v1`
  - These were refused as before: `git tag v1`, `git tag --del v1`, `git tag --forc v1`, `git -c x=y tag v1`, `git --git-dir=.git tag v1`, `git update-ref refs/tags/v1 HEAD`.
  - In a scratch repository, git 2.54 made `v1.0`, `v1.1` and `v1.2` from the first, second and fourth commands. `git cat-file -p v1.0` ends with the message `-l`.
  - A related gap: `git fetch origin 'refs/*:refs/*'` and `'+refs/*:refs/*'` are allowed, and they land a remote's `refs/replace/` refs. They are not named in the guard's "Not held" list (`:265-267` names only tags).
  - Why MINOR: neither bypass reaches a deploy.
    - The deploy gate reads no local tag.
    - The gate ignores replace refs: `GIT_NO_REPLACE_OBJECTS=1` at `scripts/deploy_gate.py:102`, and `git --no-replace-objects` at `scripts/brief_fields.py:91` and `:125`.
    - The rule protects release tags, the owner's (D-223 clause 5). Pushing a tag is already "not held".
  - **Remedy (the owner's file):**
    1. Decide `deleting` and `listing` from the option words the walk reached as options, never from `letters`, so a value of a `TAG_VALUED` option is never read as a flag.
    2. Add the six spellings above to `test_a_version_tag_or_a_replace_ref_is_the_owners` (`tests/unit/test_bash_guard_bounds.py:1063`).
    3. Either refuse a fetch refspec whose destination glob covers `refs/replace/` (`refs/*`), or name it in "Not held".
  - **Needs a new issue**, for the owner's `make guard-pin`.
- **M11** `ios/Config/Engine.xcconfig:28-30`, held by `tests/unit/test_testflight_ready.py:183`. **#488's "no local file can give a Release build the exception" holds only for the two settings it pins. A local `INFOPLIST_OTHER_PREPROCESSOR_FLAGS` still gives an archive `NSAllowsLocalNetworking`.**
  - The test checks only that `INFOPLIST_PREPROCESS` and `INFOPLIST_PREPROCESSOR_DEFINITIONS[config=Release]` are set after `#include? "Engine.local.xcconfig"` (`:18`). Xcode's Info.plist preprocessor also reads `INFOPLIST_OTHER_PREPROCESSOR_FLAGS` and `INFOPLIST_PREFIX_HEADER`, and Engine.xcconfig sets neither.
  - Probe: I planted `INFOPLIST_OTHER_PREPROCESSOR_FLAGS = -DENGINE_LOCAL_NETWORKING=1` in a local `Engine.local.xcconfig` and built `-configuration Release -sdk iphonesimulator CODE_SIGNING_ALLOWED=NO` with derived data in the scratchpad. `BUILD SUCCEEDED`. `plutil -p` on the built `Info.plist` shows `NSAppTransportSecurity => { NSAllowsLocalNetworking => true }`, with `EngineURL => https://model-ranking.fly.dev`.
  - The order does hold for the setting the test names: a local `INFOPLIST_PREPROCESS[config=Release] = NO` is overridden, and `-showBuildSettings` gives `INFOPLIST_PREPROCESS = YES`.
  - Why MINOR:
    - The local file is the owner's own and gitignored (`.gitignore:74`).
    - A Release build's address is still pinned to HTTPS (`:23`), so the exception reaches no host the app talks to.
    - Without the local file, the Release bundle has no exception, as the Tester measured.
    - It is the same class as the M19 review's S1 for the address: one local line changes what an archive carries.
  - **Remedy:**
    1. After the include, set `INFOPLIST_OTHER_PREPROCESSOR_FLAGS[config=Release] =` and `INFOPLIST_PREFIX_HEADER[config=Release] =`.
    2. Make `:183` derive the settings it pins from every `INFOPLIST_*PREPROCESS*` and `INFOPLIST_PREFIX_HEADER` setting Xcode lists (`xcodebuild -showBuildSettings`), not from a hand-kept pair, or have it fail closed on an unpinned one.
    3. Add a check to `docs/release-testflight.md` that runs `plutil -p` on the archive's `Info.plist` before upload.
  - **Needs a new issue.**

#### PASS (with evidence)
- **#496 closes M8 and R6.** `src/app/workflows/status_record.py:14-23` returns `{}` on `OSError`, `ValueError` or `RecursionError`, and for anything that is not an object. Every Python reader of `<artifact>.refresh.json` now goes through it:
  - `write_status` (`refresh.py:1183`), `_another_release_built` (`:1151`), `_read_last_ok` (`:1458`) and `nightly.read_record` (`nightly.py:141`).
  - `git grep 'refresh\.json\|status_path('` finds no other Python reader.
  - The fail directions are unchanged:
    - `_another_release_built` still says "another release built" (publish this release's own build) for a record it cannot read. That was `True` before and is `{}` → `None != built_by` → `True` now.
    - `read_record` maps `{}` to `None`, and `needs_catch_up` treats `None` and `{}` alike (`nightly.py:144-155`): one catch-up.
  - The module imports only `json` and `pathlib`, so the server loads no client (W-125).
  - Tests: `tests/unit/test_refresh_carry.py:532`, `:547` (200,000-deep, each reader). Red under the Tester's F1 and F49.
  - The one reader left outside it is `scripts/deploy_hosted_engine.sh:128` (R10). It fails closed.
- **#488 makes the exception Debug-only, closing R1 except for M11's path.**
  - `ios/Config/Info.plist:13-20` wraps the key in `#if ENGINE_LOCAL_NETWORKING` inside XML comments. With the symbol undefined, the preprocessor leaves an empty comment, so the plist stays valid.
  - `Engine.xcconfig:29-30` defines the symbol for Debug only.
  - Tests: `test_testflight_ready.py:166` (Xcode's own `cc -E -P` per configuration) and `:183`. The Tester's built bundles: Release `NSAppTransportSecurity => {}`, Debug `NSAllowsLocalNetworking => true`.
- **The owner's guard patch (#497/#498, `f5b9395`) is the owner's and is pinned.**
  - `f5b9395` carries no `GP-Agent` trailer. It is the only commit in the range that touches `.claude/`, `.githooks/` or `.github/` (`git log --no-merges c29392c..ed18de5 -- .claude .githooks .github`).
  - `shasum -a 256 .claude/hooks/bash_guard.py` = `9d1faaf6bf7f119496bc61f34d525a1de607443e77b21c857c130fac2d529ae1`, the value both hooks in `.claude/settings.json` pin (2 of 2).
  - The new rule only adds refusals. No existing refusal was removed: the diff adds lines and one `if` in `_judge_git` (`:3252-3254`), after `_moves_default`.
  - Its tests: `tests/unit/test_bash_guard_bounds.py:1063` (27 refusals) and `:1078` (23 allowed); 100 passed here with the Tester's two tests. M10 is the spelling they miss.
- **#503 adds no surface.** `scripts/ui_test.sh:93-95` runs `xcrun simctl uninstall "$DEVICE" com.ilgar.modelranking`, quoted, on the named simulator, with its output to the run's log. It removes only the app's data on a simulator. The quiet `|| true` is the Tester's M10, a harness reliability matter, not a security one.
- **#484 (D-230) is one pinned door.**
  - `ios/ModelRanking/SettingsDoor.swift:9-11` opens `UIApplication.openSettingsURLString`, the system's constant. Nothing the reader typed reaches it.
  - `scripts/client_decl_gate.py:605-624` grants its five declarations only in that file, and only while its bytes hash to `SETTINGS_DOOR_SHA256`. It also requires each declaration to be seen (`:3145-3146`), so the gate fails closed on a changed or emptied door.
  - `ContentView.swift:800-805` draws it only under `guide.opensSettings`.
  - `make client-decls` PASS in the Tester's `make check`. I leaned on `fix-issue-484-security.md` for the rest.
- **The deploy gate's combined surface, beyond M9.**
  - Every git call goes through `--no-replace-objects` or `GIT_NO_REPLACE_OBJECTS=1`. Every base object is read through the one hash-checking reader (`scripts/brief_fields.py:136-150`).
  - The comparison is by content, with no index stat, fsmonitor, attribute filter or ignore file the change can write.
  - The `--judge` payload parse (`scripts/deploy_gate.py:985-993`) names no `RecursionError`. A deep payload makes the gate exit 1 with a traceback, which the guard reads as a refusal ("exited 1 and gave no reason", `.claude/hooks/bash_guard.py:3466`). The guard builds the payload itself with `json.dumps`. Closed.
  - `conformance/test-deploy-shipped.py:58-60` now declares `fly deploy`. This strengthens the fixture: with #494's fail-closed empty declaration, a fixture with none made the refusal tests vacuous.
- **The release Tester's two tests** (`tests/unit/test_deploy_gate_505_tester.py:20`, `tests/unit/test_deploy_gate_510_tester.py:19`) write only under `tmp_path`, make no network call, and add refusals, not exemptions. Both pass here.
- **Authority, identity and destructive operations.**
  - Every non-merge commit but the owner's `f5b9395` carries `GP-Agent:`.
  - No commit message carries AI attribution: `git log --format=%B c29392c..ed18de5` gives 0 hits for "Co-Authored-By", "Generated with" or `claude.ai/code`.
  - No added line in `src/`, `scripts/`, `.claude/`, `conformance/` or `tests/` adds `reset --hard`, a force push, `rm -rf` or `DROP TABLE`.
  - No agent write to `.github/workflows/**`, `Dockerfile` or `fly.toml`.
- **The serving image and `/v1` are untouched.** `git diff --stat c29392c..ed18de5 -- pyproject.toml requirements/ Dockerfile fly.toml deploy/ .github/ src/app/adapter/main.py` is empty. The only `src/` changes are the status reader and its three call sites. There is no new route, endpoint, CORS rule or dependency.

### Gates passed (delta)
- [x] `make secrets` at `ed18de5`, run here: exit 0, gitleaks "no leaks found" (~23.26 MB scanned). Also `gitleaks git --log-opts=c29392c..ed18de5`: "no leaks found".
- [x] `make deps` at `ed18de5`, run here: exit 0. `pip_audit --strict` over `requirements/{build,dev,ingest,serve}.lock`: "No known vulnerabilities found". No lock, `pyproject.toml` or requirement changed in the range.
- [x] `make slopsquat` at `ed18de5`, run here: exit 0, "slopsquat PASS: 20 declared dependency(ies), 0 suspect". There is no new third-party import: the range adds only `app.workflows.status_record` and the standard library's `json`.
- [x] `make conformance` at `ed18de5`, run here: exit 0, "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)".
- [x] Default-deny preserved: no new route or endpoint. The app's one new egress is the system Settings page, through a pinned door (D-230). A Release Info.plist has no ATS exception (M11 is a local-file path to one).
- [x] Permission matrix not violated: the only `.claude/` change is the owner's own commit. No agent write to `.github/workflows/**`, `.githooks/`, `Dockerfile` or `fly.toml`.
- [x] Prompt-injection hygiene: nothing feeds fetched text to a model or an agent. No diff content tried to change policy. The plan and D-230/D-231 grant only what the dispatcher stated.
- [x] Auth/PII and the human-review trigger: not applicable. There is no HIGH path, and no auth, PII, payment or migration code.
- [x] SAST: `bandit` is not in the locks. `ruff check --select S` over `status_record.py`, `refresh.py`, `nightly.py`, `deploy_gate.py`, `brief_fields.py` and `client_decl_gate.py` gives two S101 hits:
  - `scripts/brief_fields.py:138`, new in `d7780fc`: an `assert` that narrows a `Popen`'s pipes, which `open_batch` always sets. With `-O`, a missing pipe would raise `AttributeError` instead. No effect.
  - `src/app/adapter/nightly.py:295`, which predates the range.
  - Range tests here: `test_refresh_carry`, `test_testflight_ready`, `test_settings_door_484` and every `test_deploy_gate_*` file; see "Range tests" below.

### Acceptance criteria evidence (delta)
- **#496** (a record nested past the recursion limit is no record, in every reader): `src/app/workflows/status_record.py:14-23`; `refresh.py:1151`, `:1183`, `:1458`; `nightly.py:141`. Tests: `tests/unit/test_refresh_carry.py:532`, `:547`.
- **#488** (Release has no `NSAllowsLocalNetworking`; Debug has it): `ios/Config/Info.plist:13-20`, `ios/Config/Engine.xcconfig:28-30`. Tests: `tests/unit/test_testflight_ready.py:166`, `:183`. M11 is the shape `:183` misses.
- **#493, #500** (a forged object under the reviewed head, and a flagged index entry, refuse): `scripts/deploy_gate.py:308-390`. Tests: `tests/unit/test_deploy_gate_493.py:26`, `:49`, `:78`, `:100`, `:110`, `:126`, `:143`.
- **#494, #501** (a declared command exempts only what the known programs read): `scripts/deploy_gate.py:441-545`, `:647-700`. Tests: `tests/unit/test_deploy_gate_494.py:48`, `:58`, `:72`, `:96`, `:117`, `:132`; `tests/unit/test_deploy_gate_501.py:41`, `:50`, `:63`.
- **#505, #506** (by content; a rename is both its sides): `scripts/deploy_gate.py:208-306`, `:593-602`. Tests: `tests/unit/test_deploy_gate_505.py:25`, `:37`, `:51` and the rest of the file; `tests/unit/test_deploy_gate_506.py:18`, `:35`; `tests/unit/test_deploy_gate_505_tester.py:20`. M9 is the environment's road.
- **#509, #510, #511** (one verified reader for every base read): `scripts/brief_fields.py:123-150`. Tests: `tests/unit/test_deploy_gate_509.py:31`, `:43`, `:55`, `:84`, `:98`; `tests/unit/test_deploy_gate_511.py:25`, `:38`, `:45`; `tests/unit/test_deploy_gate_510_tester.py:19`.
- **#484, D-230** (one pinned door to Settings): `ios/ModelRanking/SettingsDoor.swift:8-13`, `scripts/client_decl_gate.py:605-624`, `:3145-3146`, `:3415-3421`. Tests: `tests/unit/test_settings_door_484.py:27`, `:37`, `:46`.
- **#503** (the offline pass starts with no kept answer): `scripts/ui_test.sh:93-106`; the Tester's `make ui-test` runs 2 and 3.
- **#497/#498** (the guard refuses `v*` tags and replace refs): `.claude/hooks/bash_guard.py:3099-3142`, `:3252-3254`; pin `.claude/settings.json:79`, `:90`. Tests: `tests/unit/test_bash_guard_bounds.py:1063`, `:1078`. M10 is the spelling they miss.

### Risks queued (delta)
- **R10** `scripts/deploy_hosted_engine.sh:128-131`. **The deploy script's reader of the status record catches `(OSError, ValueError)` but not `RecursionError`, and does not use #496's `read_status`.**
  - Under `set -euo pipefail` (`:33`), a deeply nested record crashes the inline Python, and the command substitution ends the script. So the deploy is refused, with a traceback instead of "unreadable". It fails closed.
  - Reaching it needs a write to the served artifact's folder.
  - Revisit when the script is next touched: read the record through `app.workflows.status_record.read_status`, or catch `RecursionError`, so the refusal names its reason.
- Still open from earlier rounds: R3, R4, R5, R8. R2 was closed by #453 (`refresh.py:1676`). R1 was closed by #488 (M11 aside), R6 by #496, and R9 by #493, #500, #505, #509 and #511.

### Range tests
- At `ed18de5`, in this seat's venv: `tests/unit/test_refresh_carry.py`, `test_testflight_ready.py`, `test_settings_door_484.py` and every `test_deploy_gate_*.py`: 251 passed (404.8 s). Also `test_deploy_gate_505_tester.py`, `test_deploy_gate_510_tester.py` and the guard patch's two parametrized tests in `test_bash_guard_bounds.py`: 100 passed. The coverage-floor message is expected on a partial run.

### Clean-up
- I removed my worktree (`relsec-wt`) and the probe worktree (`relsec-probe/oldwt`) with `git worktree remove`, without force, after restoring the two verdict files I had copied in to validate this one. `git worktree list` names neither now.
- The validation, before the restore: with this file and the Tester's scratch verdict copied in at `ed18de5`, `scripts/deploy_gate.py --check` printed "security: docs/reviews/release-security.md MINOR at ed18de5, no code changed since". `make check-records` printed "check_records PASS [repo]: no findings" (437 records).
- The Bash guard refused removing `relsec-probe/tagrepo`, a scratch repository holding only an empty commit and the three probe tags. It is in the session scratchpad and holds nothing of the project. The owner may delete it.

## Delta round 2026-10-31 fixes-1031 (ed18de5..6e6f5be)

**Reviewer:** Security-Reviewer subagent, dispatched by `/going-live` step 2 for the deploy delta. I read `.claude/agents/Security-Reviewer.md`, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` as the session loaded them from `main`. The range edits none of them, and nothing under `.claude/`, `.githooks/` or `.github/`.
**Independent:** yes. I wrote none of this range's code, tests or records, none of its per-change verdicts (`docs/reviews/fix-issue-{517,522,535}-security.md`, `docs/reviews/integration-fixes-1031-security.md`) and not the release Tester's verdict on it.
**Range:** `ed18de5bef8ad54d501b8a268db9900073ab903f..6e6f5beb81fc12d29d51540fc132be230d8d880b`, 17 files: `scripts/deploy_gate.py`, `scripts/brief_fields.py`, `scripts/client_decl_gate.py`, seven test files, `docs/decisions.md` (D-232, D-233), `docs/process-log.md` and six review records. Issues: #517, #522, #518, #535, and the release Tester's `6e6f5be` (tests only).
**Reviewed head:** 6e6f5beb81fc12d29d51540fc132be230d8d880b, the release Tester's head. I added no test and changed no code.
**Risk tier:** LOW by the brief (`docs/project-brief.md:110` declares no HIGH path). `make review-need RANGE=ed18de5..HEAD` routes it to security as a policy edit (#283) and as gate code (`brief_fields.py`, `client_decl_gate.py`, `deploy_gate.py`). I read the deploy gate at HIGH depth. No auth, PII, payment or migration code is in the range, so the §11 senior-review trigger does not fire.
**Seat:** my own detached worktree at `6e6f5be` in the session scratchpad (`wtsec`), with its own `.venv` from `make install` (the hash-checked locks) and its own `advisor.db` copy. Probes ran as a temporary test file in that tree, deleted after the run; `git status` is clean apart from this file. No edit in the main checkout or another worktree, and no network call beyond `make slopsquat`.

**The question this round asks: does any change loosen the deploy gate, or let the change under evaluation alter the policy it is judged by?** No. I read every hunk of the three scripts myself:
  - **Every base read only widens, and only to protected refs.** `protected_bases` (`scripts/brief_fields.py:330-340`) returns the merge-base and the tip of the same default-branch ref, or `[]`. `_policy` (`scripts/deploy_gate.py:164-183`) reads the brief at each through `root_at`, so one unreadable or forged base makes the whole policy `None` (refused, #283/#509). `declared` (`:687-692`) takes the union of the tree's and each base's `Deploy commands:`. `verdicts` (`:660`) takes the union of the modes, so a tip that says heavy owes the milestone Tester as well, and a light mode anywhere still keeps the milestone verdict from standing in. `_workflow_texts` (`:894-917`) adds the tip's workflow copies, each verified, and any read failure marks the read incomplete, which makes every dispatch a deploy (`:763`).
  - **The pin is read at both bases, never in the tree.** `devflow_pins` (`:402-413`) gives `None` unless every base holds a well-formed pin (`all(found)`, `:412`). `shipped_unchanged` (`:437`) exempts a file only when its bytes equal every pin's. With one base this is the old rule. With two it exempts a subset. The tree's `docs/devflow-pin.txt` and `.gp/installed` are not read.
  - **The surface only grows.** `_runs_unread` (`:533-539`) is the old first-word check OR'ed with the new regex (`:523-526`), so it is true wherever it was true before. `deploy_surface` (`:581`) adds `_workflow_names` to the set it built before. A larger surface, or `None`, exempts less.
  - **What the tree adds counts only against it.** The tree's brief, workflows and modes are still read, but each one only adds a declaration, a deploy workflow, a mode or a surface file. Nothing in the tree can remove a base's declaration, a base's mode, or a base's pin.
  - **#535 is one exact entry.** `scripts/client_decl_gate.py:1393` adds `"Date.<="` to the standings sink's list only. The list is matched by exact symbol (`:3393`, `:3405`), so it widens nothing else. `fetchedAt <= now` (`ios/ModelRanking/Engine/StandingsStore.swift:126`, `:148`) compares two dates and reaches no egress. The owner ruled on it (the comment at `:1391`).
  - **On this tree**, `protected_bases` gives `['290557c...']`, one base, because `origin/main` is the merge-base. `devflow_pins` gives one pin (`49f6634...`). The surface is 9 files, the nightly workflow and its scripts among them. So today the gate judges exactly as it did at `ed18de5`, apart from the larger surface.

**Leaned on, not repeated:** `fix-issue-517-security.md` (MINOR, round 2 at `9ca56c4`), `fix-issue-522-security.md` (PASS, round 2 at `6d2e10d`, then R4/R5 in `6a02cc3`), `fix-issue-535-security.md` (PASS at `3ba886f`) and `integration-fixes-1031-security.md` (MINOR at `12567c3`, which checked the merges). After `12567c3`, `git diff --stat` lists the #535 verdict, the delta reviews and the Tester's three test files only.

**Verdict of this round:** MINOR. BLOCKING 0 · MAJOR 0 · MINOR 1 new (M12, routed to the open #541) · risks queued 1 new (R11). Nothing here blocks a deploy that `make deploy-check` passes once both verdicts name this head.

### Findings

#### BLOCKING
- none

#### MINOR
- **M12** `scripts/deploy_gate.py:523-526` (`_UNREAD_IN_WORKFLOW`), `:541-547` (`_workflow_names`). **Three more spellings of #541's class: a dispatched deploy workflow changes directory, or checks out into a subfolder, without the gate reading it, so the script it starts stays exemptible.**
  - Probe, on the #522 fixture (`tests/unit/test_deploy_gate_522.py:22-29` with `_upgrade_shipping` of `scripts/ship_it.sh`). `repo.check()` exit 0 means exempt:
    ```
    - run: scripts/ship_it.sh                                       -> 1  (the control)
    - run: sudo -D scripts ./ship_it.sh                             -> 0  (sudo 1.9.3+: -D/--chdir)
    - run: sudo --chdir=scripts ./ship_it.sh                        -> 0
    - uses: actions/checkout@v4 / with: path: sub / - run: sub/scripts/ship_it.sh   -> 0
    - run: python -c "import os; os.chdir('scripts'); os.system('./ship_it.sh')"  -> 0
    ```
  - None of these is a regression: at `ed18de5` nothing a workflow started was on the surface at all.
  - Why MINOR: the spelling has to sit in a workflow file that is itself never exempt (`:582-583`). The exempt file must also equal both DevFlow pins byte for byte (`:437`). The real workflows have none of these: `actions/checkout` there takes no `path:`, and the only `sudo` (`.github/workflows/ci.yml:68`) is in CI, not a dispatched deploy.
  - **Remedy:** add the three spellings to #541, and to its parametrisation in `tests/unit/test_deploy_gate_522.py:34-56`. Close the class there rather than by name: treat an `actions/checkout` step with `path:`, and a `sudo`/`env` with any directory option, as unread. The interpreter case is #522's R1 (a path built at run time), queued under D-232's "Revisit when". No new issue.

### PASS (with evidence)
- **#517 / D-232 clause 1** (the policy at the merge-base and at the tip): `scripts/brief_fields.py:330-340`; `scripts/deploy_gate.py:164-183`, `:660`, `:687-692`, `:894-917`. Tests: `tests/unit/test_deploy_gate_517.py:42`, `:55`, `:89`.
- **D-233** (both pins must hold the bytes): `scripts/deploy_gate.py:402-413`, `:437`. Tests: `tests/unit/test_deploy_gate_517.py:67`; `tests/unit/test_deploy_gate_517_tester.py:33` and `:45`, which fail when `all(found)` is weakened to `any(found)` (the Tester's commit message).
- **#522 / D-232 clause 2** (a dispatched workflow's text puts what it names on the surface, and a hidden start exempts nothing): `scripts/deploy_gate.py:523-547`, `:581`. Tests: `tests/unit/test_deploy_gate_522.py:58` (19 spellings), `:67` (the control that keeps the exemption working), `:78` (R5); `tests/unit/test_deploy_gate_522_tester.py:30` (`pushd`, `--chdir`, a runner by path inside `-c`).
- **#518** (tests only): `tests/unit/test_deploy_gate_518.py:31`, `:54`, `:69`, `:84`, `:94`. Each writes under `tmp_path` only.
- **#535**: `scripts/client_decl_gate.py:1391-1393`. Tests: `tests/unit/test_client_decl_gate_535_tester.py:41`, `:48`, `:54` (the operator passes in the standings sink only, its neighbours stay refused, and the engine client's sink does not gain it).
- **Authority, identity and destructive operations.** Every non-merge commit in the range carries `GP-Agent: claude-code` (14 of 14). `git log --format=%B` finds no AI attribution. No added line in `scripts/` or `tests/` adds `reset --hard`, a force push, `rm -rf`, `DROP TABLE`, `shell=True`, `eval` or `exec`. `git diff --stat ed18de5..6e6f5be -- .github .claude .githooks Dockerfile fly.toml pyproject.toml requirements src ios conformance Makefile` is empty.
- **No external surface.** No route, endpoint, CORS rule, dependency or import is added, and the serving image is untouched.

### Gates passed (delta)
- [x] `make secrets` at `6e6f5be`, run here: gitleaks "no leaks found" (~23.40 MB). Also `gitleaks git --log-opts=ed18de5..6e6f5be`: "no leaks found".
- [x] `make deps`: the dispatcher's line at `243d115`, "No known vulnerabilities found". I did not re-run it, because no lock, `pyproject.toml` or requirement changed in the range (the empty `git diff --stat` above).
- [x] `make slopsquat` at `6e6f5be`, run here: "slopsquat PASS: 20 declared dependency(ies), 0 suspect". There is no new import.
- [x] `make conformance` at `6e6f5be`, run here: "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)".
- [x] Default-deny preserved: no new external surface. The deploy gate only tightens (above).
- [x] Permission matrix not violated: no agent write to `.claude/`, `.githooks/`, `.github/workflows/**`, `Dockerfile` or `fly.toml`.
- [x] Prompt-injection hygiene and base-pinned policy: the gate reads the brief, the workflows and the pin at protected refs (the two bases), never from the change alone. No diff or record content tries to change policy. D-232 and D-233 grant only tightening, and each says a loosening change is refused at review.
- [x] Auth/PII and the human-review trigger: not applicable. There is no HIGH path, and no auth, PII, payment or migration code.
- [x] SAST: `bandit` is not in the locks. `ruff check --select S` over the three scripts gives one S101, `scripts/brief_fields.py:138`, which predates the range (the run-1030 round's note).

### Acceptance criteria evidence (delta)
- **#517** (a branch cut before the declaration still has its deploy guarded; the tip's mode and workflows are read) → `scripts/brief_fields.py:330-340`, `scripts/deploy_gate.py:164-183`, `:660`, `:692`, `:907`; `tests/unit/test_deploy_gate_517.py:42`, `:55`, `:89`.
- **D-233** (a file is DevFlow's only when both pins hold its bytes; a missing pin exempts nothing) → `scripts/deploy_gate.py:412`, `:437`; `tests/unit/test_deploy_gate_517.py:67`, `tests/unit/test_deploy_gate_517_tester.py:33`, `:45`.
- **#522** (what a dispatched workflow names is on the surface; a runner, a directory change or `uses: ./` exempts nothing) → `scripts/deploy_gate.py:523-547`, `:581`; `tests/unit/test_deploy_gate_522.py:58`, `:67`, `:78`, `tests/unit/test_deploy_gate_522_tester.py:30`. M12 lists the spellings it misses.
- **#518** (the verified reader's fail-closed paths each have a test) → `tests/unit/test_deploy_gate_518.py:31`, `:54`, `:69`, `:84`, `:94`.
- **#535** (`Date.<=` in the standings sink only) → `scripts/client_decl_gate.py:1393`; `tests/unit/test_client_decl_gate_535_tester.py:41`, `:48`, `:54`.

### Risks queued (delta)
- **R11** `scripts/deploy_gate.py:186-190` (`policy_root`). **#517 left the old single-base accessor in place. Nothing calls it (`git grep -n policy_root` finds only its definition), and it returns the merge-base's brief only.** A future caller that reads the policy through it would reopen #517 for that read, and every test would stay green. Remedy: delete it the next time the file is touched, or make it return the list `_policy` gives.
- Still open, filed, not re-filed here: #526 (M9, `GIT_*` variables), #529 (M10), #530 (M11), #531 (R10), #533 (the #517 review's M1: the guard lets a session move `origin/main` or recreate `main`, so both bases come from a ref the change chose), #534 (the #517 review's R3: a stale `origin/HEAD` wins over `origin/main`) and #541 (the fixes-1031 stack's M2, now with M12's three spellings). R3, R4, R5 and R8 stand from earlier rounds.
- #533 is the one that matters most for D-232. Two bases from one ref are one base once that ref is moved. Until #533 is fixed, the owner deploys from their own shell (D-185), where the guard's gaps do not apply. `git rev-parse origin/main` should match GitHub's `main` before `make deploy-check`.

### Range tests
- At `6e6f5be`, in this seat's venv: every `tests/unit/test_deploy_gate*.py` and `tests/unit/test_client_decl_gate_535_tester.py`, `-n 4`: 248 passed (38.9 s).
