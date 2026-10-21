---
record_type: review
id: fix-issue-387-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-21
---
# Security Review — fix-issue-387

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), light mode. `make review-need` routed this change to `security`: gate or control code changed (`scripts/ci/nightly-hosted.yml`, `scripts/deploy_hosted_engine.sh`, `scripts/nightly_hosted.sh`), a sensitive path (`scripts/deploy_hosted_engine.sh`), a new `json.load`, and a policy edit to the brief's `Deploy commands:` (#283).
**Independent:** yes. I wrote none of this range's code, tests or records.
**Date:** 2026-10-21
**Release range:** `3eb4189a6ac04474b15a7743781367f63f5e0a0b..40b172094075c0b671c9f91eaf5489a69081c680` (4 commits, branch `fix/issue-387-hosted-refresh`, draft PR #388). Issue #387; ADR D-217 (`docs/decisions.md:5711`, proposed, with the owner's rulings of 2026-10-21).
**Reviewed head:** e4b84599d04c1e47a09a539d7d4d5161429c6081
**Risk tier:** MEDIUM. This is deploy and gate code, and it adds a deploy credential (`FLY_API_TOKEN`) to CI. The brief declares no HIGH paths (`Paths that make a change HIGH:` is `none`), and the change touches no auth, PII, payment or migration path, so no senior review is triggered.

I reviewed it in a detached worktree at the head, with its own venv (`make install`). Probes ran in throwaway repositories with stand-ins for `fly` and `curl` on `PATH`. Nothing contacted Fly.io, and no workflow was triggered. The only network calls were read-only GitHub API reads: the action tags, `setup-flyctl`'s `action.yml`, a run listing to check the `--jq` filter, and the repository's visibility. I planted four mutants and restored each from a copy; `git status` was clean afterwards.

## Verdict
PASS WITH FINDINGS (round 2, at e4b8459): BLOCKING 0 · MINOR 2 open, both filed (M1's remainder #390, M3 #389) · NIT 1 · risks queued 4 (R1 #391, R3 #392, R4 in D-217's revisit, R5 until the owner applies the workflow). Round 1 was BLOCKING 1 · MINOR 5 · risks queued 5. The dispositions are under "Round 2" below.

**B1 must be fixed before the owner applies the workflow.** As proposed, the workflow puts the deploy token in reach of code from any branch, and that code can deploy past the deploy gate. Several things hold:
- The two-job split.
- The refresh's refusal of tokens.
- The checkout without credentials.
- The gate on every night.
- `--if-new`.
- The pinned actions.

But GitHub enforces none of them on a run started from another ref, since that run uses the ref's own copy of the workflow and scripts. The fix fits in this PR: an environment for the secret, restricted to `main`, plus a ref condition. The owner-actions row that sets the secret changes with it.

What holds, with evidence:
- **The refresh holds no token.** It has no `secrets.` reference, `GH_TOKEN` is set only on the state-fetch step (`scripts/ci/nightly-hosted.yml:52-54`), and both checkouts use `persist-credentials: false` (`:40`, `:96`). The script refuses `FLY_API_TOKEN`, `GITHUB_TOKEN` and `GH_TOKEN` (`scripts/nightly_hosted.sh:30-35`). Mutant C, an empty refusal list, fails 3 tests.
- **The state filter is sound for pull requests and forks.** The workflow has no `pull_request`/`push` trigger (`:16-19`, held by `tests/unit/test_nightly_hosted.py:242`). The run listing keeps only `schedule`/`workflow_dispatch` runs on `branch=main` whose head repository is this one, and skips the current run (`:57-61`). I checked that gh's gojq `env.GITHUB_REPOSITORY` filter works against a real listing: it returns 0 runs for a foreign repository name and keeps this repository's runs. Expired artifacts are skipped (`:63`).
- **The zip extraction is safe.** `unzip ... advisor.db advisor.db.refresh.json` extracts the two named members only. A probe zip with an extra `sub/x` member extracted just the two. A zip missing a member exits 11, so the step fails (the runner's `bash -e`) and the night fails closed. Exact member names leave no zip-slip.
- **The deploy gate runs first and blocks.** `scripts/deploy_gate.py --check` runs before anything is derived (`scripts/nightly_hosted.sh:62-66`). The deploy checkout has `fetch-depth: 0` (`:97`). On `main` the policy base (`scripts/brief_fields.py:113-119`) is HEAD itself, the protected branch. Mutant B (`if false`) fails `test_a_stale_gate_deploys_nothing_and_fails_the_night`.
- **`DEPLOY_ACCEPT_DATA_FROM` is dropped.** `env -u DEPLOY_ACCEPT_DATA_FROM` is at `scripts/nightly_hosted.sh:67`. Mutant A, which drops the `-u`, fails `test_data_another_release_built_is_refused_whatever_the_environment_accepts`.
- **`--if-new` adds no loose argument and can only skip a deploy.** The argument parse accepts exactly `--if-new` (`scripts/deploy_hosted_engine.sh:35-40`). The skip needs `/health` to equal the full build stamp (`:126`), and an unreadable answer is `""` (`:119-125`), which never equals it. Mutant E, which skips whenever `--if-new` is given, fails 2 tests.
- **The health check after a deploy is unchanged in strength** (`:133-143`).
- **Every action is pinned to the commit its tag names.** `git/ref/tags/<tag>` on GitHub answered the pinned SHA for each one:
  - `actions/checkout` v4.4.0 `11d5960a`
  - `actions/setup-python` v5.6.0 `a26af69b`
  - `actions/upload-artifact` v7.0.2 `cf430e03`
  - `actions/download-artifact` v8.0.2 `9000827c`
  - `superfly/flyctl-actions` 1.5 `fc53c09e`
- **Permissions are least privilege.** The workflow has `contents: read`; the refresh adds `actions: read`; there is no `id-token`.
- **Concurrency and failure.** `cancel-in-progress: false`, and there is no `continue-on-error`. A failed refresh skips the upload (default `success()`), and `needs: refresh` skips the deploy.
- **D-116 clause 2 holds.** Ingestion runs on a runner, the serving image is unchanged (no `Dockerfile` change in the range), and the deploy job installs only `serve.lock` + `build.lock` (`:104`).

## Findings

### BLOCKING
- **B1** `scripts/ci/nightly-hosted.yml:19,86-120` and `docs/owner-actions.md:19`: the deploy token reaches any branch's code, and that code deploys past the gate. OWASP A01 (broken access control) and CICD-SEC-4 (poisoned pipeline execution).
  - **How it happens.** `workflow_dispatch` can be started on any ref (`gh workflow run nightly-hosted.yml --ref <branch>`). A dispatched run uses that ref's copy of the workflow and of `scripts/nightly_hosted.sh`, `scripts/deploy_gate.py`, `scripts/deploy_hosted_engine.sh` and `docs/reviews/*.md`. The `deploy` job has no `environment:` and no ref condition. The owner-actions row stores the token as a repository secret (`gh secret set FLY_API_TOKEN -R ...`), and every job of every ref can read a repository secret.
  - **What follows.** Once the workflow is on `main`, every branch cut from `main` carries it. A branch whose `scripts/nightly_hosted.sh` skips the gate, or prints the token, deploys unreviewed code to `model-ranking.fly.dev` or exfiltrates the token. Editing that script is ordinary agent work and needs no `.github/workflows/**` edit. The branch can also write its own `docs/reviews/release-security.md`, which the gate reads as a record. The CI issue agent's branches are such branches too.
  - **Why the guard does not stop it.** Anyone with write access can start the run: the owner, and an agent session using the owner's `gh` login. The Bash guard does not judge `gh workflow run` or `gh api .../dispatches`: `_judge_gh` refuses only `pr merge`, `pr ready` and the merge or protection APIs (`.claude/hooks/bash_guard.py:2665-2696`). Only a permission prompt stands in the way, and that prompt is absent in an unattended run.
  - **Why it blocks.** This defeats D-217 clause 4 (the gate every night), clause 2 (the token beside no unreviewed code) and D-185 clause 5 (nothing deployed by the agent). Today the proposal is not installed, so nothing is exposed yet. The owner-actions rows tell the owner to install it as is.
  - **Remedy, in this PR:**
    1. `environment: fly-production` on the `deploy` job.
    2. Change the owner-actions secret row to create that environment with a deployment branch policy of `main` only, and to store the token there (`gh secret set FLY_API_TOKEN --env fly-production -R umutcanapaydin/Model_Ranking`). There must be no repository-level `FLY_API_TOKEN`. GitHub enforces the branch policy on the server, so a branch's edited workflow cannot remove it, and a job that drops `environment:` gets no secret.
    3. `if: github.ref == 'refs/heads/main'` on both jobs, as defence in depth. This also stops a branch run from uploading a `hosted-state`.
    4. A shape test in `tests/unit/test_nightly_hosted.py` that asserts the `environment`, the ref condition, and that the owner-actions row names `--env`.

### MINOR
- **M1** `docs/project-brief.md:107` and `.claude/hooks/bash_guard.py:2665-2696`: an agent's `gh workflow run nightly-hosted.yml` on `main` is a deploy that no guard judges. D-217 clause 6 (`docs/decisions.md:5746`) says the guard judges an agent that runs the night "as it judges them", but the night can be started without running the script.
  - **Why it is minor.** After B1's fix, CI's own gate still limits such a run to reviewed code. It is still a deploy by the agent (D-185 clause 5; D-217 clause 5's "never the agent", `docs/decisions.md:4441`).
  - **Remedy.** Add `gh workflow run nightly-hosted.yml` to `Deploy commands:`, so the gate judges it and refuses it while a verdict is stale, with a test through `deploy_gate.deploy_in`. File an issue for the owner's guard to judge `gh workflow run` and `gh api -X POST .../dispatches` against the brief's deploys. The declared-command match does not cover the `dispatches` API, or a workflow named by its id.
- **M2** `scripts/nightly_hosted.sh:62-68` → `scripts/deploy_hosted_engine.sh:27`: `MODEL_RANKING_REPO` passes through, so the night's internal gate judges one tree and the deploy ships another. Probe (`probe_repo_redirect.py`): I built two scratch repos.
  - `good` had current verdicts.
  - `bad` had an unreviewed `scripts/unreviewed.sh` committed after its verdicts.

  `MODEL_RANKING_REPO=<bad> <good>/scripts/nightly_hosted.sh deploy <bad state>` printed `deploy-check PASS` for `good`, then built `bad/build/hosted/advisor.db` and called the `fly` stand-in (`deploy --build-arg APP_BUILD=release-9e7cf1d-...`), exit 0.
  - **Why it is minor.** CI never sets the variable. Locally the Bash guard's gate also judges the current directory's tree only, since it skips assignment prefixes (`scripts/deploy_gate.py:100`, `ASSIGNMENT`). The pass-through was pre-existing in the deploy script (R1). The new script strips `DEPLOY_ACCEPT_DATA_FROM` deliberately and leaves this one.
  - **Remedy.** `env -u DEPLOY_ACCEPT_DATA_FROM -u MODEL_RANKING_REPO ...` at `:67`, and a test that sets `MODEL_RANKING_REPO` to a stale scratch repo and expects no `fly` call.
- **M3** `scripts/nightly_hosted.sh:67` → `scripts/deploy_hosted_engine.sh:66-75,110` (`src/app/workflows/public.py:75`, `sqlite3.connect`): the deploy job parses the refresh's output while `FLY_API_TOKEN` is in its environment. D-217 clause 2 (`docs/decisions.md:5729-5733`) says "the code that parses untrusted data never runs beside the token". That holds for the source parsers, but not for what they produce.
  - **Why it matters.** Clause 2 is written for the case of a compromised parser. A compromised refresh controls the `advisor.db` and `.refresh.json` bytes, and on an `unchanged` night the downloaded file passes through as it is. The token-holding step then opens that SQLite file, runs `DELETE`s and a `VACUUM` on it, and `json.load`s the record.
  - **Why it is minor.** Reaching the token needs a SQLite file-format bug on top of a parser compromise. Python's `sqlite3` loads no extensions, and the record's `served_built_by` reaches the shell only quoted and compared with HEAD (`:76-101`), so it cannot inject.
  - **Remedy.** Derive the public copy without the token, by either of two routes:
    - `env -u FLY_API_TOKEN scripts/deploy_hosted_engine.sh --dry-run` in the night first, then a deploy mode that only hashes and ships the derived `build/hosted/advisor.db`;
    - derive it in the `refresh` job and hand the deploy job only the public copy.

    Either way, word clause 2 to match.
- **M4** `scripts/ci/nightly-hosted.yml:76-84`: `hosted-state` is a public artifact. The repository is public (`gh repo view`: `"isPrivate": false`), and any signed-in GitHub user can download a public repository's workflow artifacts. The artifact is the full artifact from before `app.workflows.public` strips `LEFT_OUT` and `RETIRED_COPIES`, kept for 90 days.
  - **Today it exposes nothing extra.** `LEFT_OUT` is empty (`src/app/workflows/public.py:31`, D-186), and a night built by current code carries no OpenRouter copies.
  - **The exposure is latent.** D-186 owes the licences before production, and the day a source goes into `LEFT_OUT`, the workflow publishes exactly what that entry withholds (Golden Rule 1).
  - **The ADR's premise is wrong.** D-217 rejects a release asset as "public and permanent" (`docs/decisions.md:5765`), but the store it chose is public too.
  - **Remedy.** A test that fails while `LEFT_OUT` is non-empty and the proposal uploads the unstripped state, a revisit trigger in D-217 naming it, and corrected rationale text.
- **M5** `scripts/ci/nightly-hosted.yml:111`: `setup-flyctl` installs flyctl's `latest` release (`version` defaults to `latest` in the pinned `action.yml`). The action is pinned, but the binary that receives the token is not.
  - **Remedy.** `with: version: <x.y.z>` and a shape test that asserts it.

## Gates passed
- [x] Secret scan green (`make secrets` on 40b1720: gitleaks `no leaks found`, 1293 tracked files; the dispatcher's gate line). The range adds no fixture with a secret: the tests' token is the literal `fly-test-token` (`tests/unit/test_nightly_hosted.py:150`).
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found`.
- [x] `make slopsquat` green: `20 declared dependency(ies), 0 suspect`. The range adds no import: the test's `yaml` is already declared.
- [ ] Default-deny preserved for new external surfaces: **no**. B1: a new deploy path reachable from any ref.
- [x] Permission-matrix not violated by the range itself. The range has no `.github/`, `.claude/` or `.githooks/` edit and no destructive operation (grep of the diff), and its commits carry the owner's identity. The workflow is a proposal for the owner.
- [x] Prompt-injection hygiene: nothing fetched is interpreted as an instruction. No untrusted `${{ github.event.* }}` reaches a `run:` (only `runner.temp`, `github.token` and `secrets.*`).
- [ ] Auth/PII checks + human review trigger: n/a (not HIGH; no auth, PII, payment or migration path).
- [x] SAST: `ruff check --select S tests/unit/test_nightly_hosted.py` reports `All checks passed!` (shellcheck and bandit are not installed). Conformance: `33 test(s) ... 0 failing` (the dispatcher's gate line).

## Acceptance criteria evidence
- #387 "`/health` shows a refresh no older than about a day, with the Mac off" → nothing can cite this locally. The deploy path it rests on is held by `tests/unit/test_nightly_hosted.py:160-168` (a green night deploys the kept state and checks `/health`). It is **verifiable only after the owner applies the workflow**, with the run in `docs/owner-actions.md:21`.
- #387 "A failed night leaves the previous good data served" → `tests/unit/test_nightly_hosted.py:75-84` (exit 2/3/4 fail the job), `:264-273` (one upload, not `always()`), and `:275-278` (deploy `needs: refresh`, gated on `outcome`). The live semantics (upload skipped, deploy skipped, last state read) are **verifiable only after the owner applies the workflow**.
- #387 "`make check` is green" → the dispatcher's `make gate` lines on 40b1720 (PASS). In my worktree, `tests/unit/test_nightly_hosted.py`: 25 passed.
- #387 "The deploy path still runs the deploy gate" → `tests/unit/test_nightly_hosted.py:171-178` (mutant B killed) and `:212-220` (the night is a declared deploy). D-217 clause 4. **B1 is the gap: a dispatched branch runs its own gate.**

## Risks queued
- **R1** `scripts/deploy_hosted_engine.sh:27` (pre-existing, outside the range): `MODEL_RANKING_REPO=<other tree> scripts/deploy_hosted_engine.sh` passes the Bash guard's gate, which judges the current directory, and then deploys the other tree. That tree only has to be clean and at its own `origin/main`, which a local bare repository satisfies. File an issue: the gate, or the script, should refuse a `MODEL_RANKING_REPO` that is not the judged tree.
- **R2** `scripts/ci/nightly-hosted.yml:57-59`: the state filter keys on `head_branch == main`. A writer who dispatches on a tag named `main` would probably produce a run with that `head_branch`. I did not probe it, since it would mean creating a tag. Only writers can do this. Tighten it with `.path == ".github/workflows/nightly-hosted.yml"`, and check that `head_sha` is on `main` (`gh api repos/$GITHUB_REPOSITORY/compare/<sha>...main --jq .status` is `ahead` or `identical`).
- **R3** The refresh's "the token reaches only its own step" holds for the environment, but not against a compromised process. On GitHub-hosted runners a step has passwordless `sudo` and can read the runner process's job token (`contents`/`actions: read`, harmless in a public repo) and its runtime token. The runtime token lets it write Actions cache entries in `main`'s scope. `ci.yml:44,100` restores the `pip` cache, and its `pip install pip-audit` (`ci.yml:102`) is not hash-checked. A compromised parser could reach CI that way. This is residual and pre-existing in kind. Watch it when caches or unhashed installs are added.
- **R4** `scripts/deploy_hosted_engine.sh:50` in CI fetches `origin main` without a credential (`persist-credentials: false`). That works only while the repository is public. If it goes private, every night fails closed at the fetch. This is a liveness risk, not a security one, and should go in D-217's revisit list.
- **R5** Nothing on the runner is verified until the owner applies the workflow: GitHub's skip semantics, the artifact listing, `setup-flyctl` linking `fly`, and the anonymous-runner rate limits D-217 names. The first manual run (`docs/owner-actions.md:21`) is the check. B1's environment must exist before that run.

## Round 2

**Range:** `40b172094075c0b671c9f91eaf5489a69081c680..e4b84599d04c1e47a09a539d7d4d5161429c6081`. `26608b7` commits round 1's verdict and `e4b8459` is the fix. **Reviewed head:** `e4b84599d04c1e47a09a539d7d4d5161429c6081`.

I re-verified in a new detached worktree at `e4b8459`, with its own venv (`make install`). `tests/unit/test_nightly_hosted.py`: 30 passed. I planted four new mutants and restored each from a copy; each one fails exactly one test:
- **M2:** dropping `-u MODEL_RANKING_REPO`.
- **B1:** deleting `environment: fly-production`.
- **B1:** replacing the deploy job's `github.ref` condition with `true`.
- **R2:** replacing the `identical|ahead` case with `true`.

`git status` was clean afterwards, and I removed the worktree. The only network calls were read-only GitHub reads: the flyctl release tag, the four issues, and a run listing for `.path`.

**B1: closed.**
- **The secret is the environment's.** The `deploy` job runs in `environment: fly-production` (`scripts/ci/nightly-hosted.yml:100`). The owner-actions row (`docs/owner-actions.md:19`) creates the environment and limits it to `main`:
  - `PUT .../environments/fly-production` with `custom_branch_policies: true`;
  - `POST .../deployment-branch-policies` with `name=main`, `type=branch`.

  It then stores the token with `gh secret set FLY_API_TOKEN --env fly-production` and says "never as a repository secret". GitHub enforces the branch policy on the server. A branch's edited copy of the workflow either keeps `environment:` and is refused, or drops it and gets no secret. A `type=branch` policy does not match a tag named `main`.
- **Both jobs carry the ref condition.** `if: github.ref == 'refs/heads/main'` is on both (`:35`, `:98`), as defence in depth.
- **A test holds it.** `tests/unit/test_nightly_hosted.py:299` (`test_both_jobs_run_only_on_main_and_the_token_is_an_environment_s_only_main_reaches`), and both B1 mutants fail it.
- **What no test can hold:** that the owner creates no repository-level `FLY_API_TOKEN`. That is R5's check at the first manual run.

**M1: partly fixed; the remainder is filed as #390 and stays MINOR.** `gh workflow run nightly-hosted.yml` is now a declared deploy (`docs/project-brief.md:107`), held at `tests/unit/test_nightly_hosted.py:234`. Through `deploy_gate.deploy_in`:
- These are judged as deploys:
  - `gh workflow run nightly-hosted.yml`;
  - the same with a trailing `-R a/b`;
  - `NIGHTLY-HOSTED.YML` (case-insensitive).
- These are not judged:
  - `gh -R a/b workflow run nightly-hosted.yml`, with the option before the subcommand;
  - `gh workflow run nightly-hosted`, the workflow's name;
  - `gh workflow run .github/workflows/nightly-hosted.yml`;
  - the `dispatches` API.

  #390 covers them (open, "The Bash guard does not judge every spelling of a nightly-hosted dispatch"). After B1, such a dispatch runs only `main`'s reviewed code behind CI's own gate, so what remains is the agent starting a deploy, not an unreviewed one.

**M2: closed.** `env -u DEPLOY_ACCEPT_DATA_FROM -u MODEL_RANKING_REPO` is at `scripts/nightly_hosted.sh:68`. I re-ran round 1's probe (`probe_repo_redirect.py`, a stale tree named in `MODEL_RANKING_REPO`):
- before the fix, the stale tree was built and `fly` was called;
- now it prints `fly called: False` and `bad tree built: False`. The deploy script stays in the judged tree, and there it refuses the stale tree's data as another release's.

The test is `tests/unit/test_nightly_hosted.py:205`, and the M2 mutant fails it.

**M3: open, filed as #389 (accepted as queued).** D-217 clause 2 now states the residual exactly: "the deploy still opens the refresh's SQLite output and record beside it (queued, #389)". The claim no longer overstates, and the exploit still needs a parser compromise plus a SQLite file-format bug.

**M4: closed for now.** `tests/unit/test_nightly_hosted.py:237` fails the day `LEFT_OUT` is non-empty. D-217 clauses 3, the alternatives and the revisit now say the state is public to signed-in users, and the release-asset rationale is corrected. `RETIRED_COPIES` is not tested, but a night built on the runner never carries those copies, since the current ingest drops them and the runner's first state is a fresh publish.

**M5: closed.** `setup-flyctl` now has `version: 0.4.111` (`scripts/ci/nightly-hosted.yml:125`), held at `tests/unit/test_nightly_hosted.py:324`. `gh api repos/superfly/flyctl/releases/tags/v0.4.111` answers `v0.4.111 2026-09-30T19:15:08Z prerelease=false`.

**R1:** filed as #391 (open). **R3:** filed as #392 (open). **R4:** now a revisit trigger in D-217 ("the repository goes private ..."). **R5:** stays open until the owner applies the workflow. It now also covers checking that only the environment holds the token.

**R2: closed.**
- **The run filter checks the file's path** (`scripts/ci/nightly-hosted.yml:66`). A real listing shows `schedule` runs with the plain `.github/workflows/<file>.yml` path, so the filter matches them.
- **Each candidate's `head_sha` must be on `main`.** `compare/$sha...main` answers `identical` or `ahead` only when the sha is an ancestor of `main` (`:69-70`). A failed compare `continue`s, which skips that run and never trusts it.
- **The loop runs in a pipe subshell** (`:67`), so its `exit 0` ends only the subshell. The step's tail `[ -f "$STATE/advisor.db" ] || echo ...` is right, because the runner's `-eo pipefail` still fails the step when `gh` or `unzip` fails inside the loop.
- **The test is `tests/unit/test_nightly_hosted.py:310`**, and the R2 mutant fails it.

**New in round 2:**
- **N1** (NIT) `docs/owner-actions.md:19`: the command sits in a Markdown table, so its pipe is written `\|`. This was already true in round 1's row. Copied from the raw file rather than the rendered table, `fly tokens create ... \| gh secret set ...` passes a literal `|` to `fly` instead of piping, and the token may be printed to the screen. Fix: put the command in a fenced block below the table, or note "copy from the rendered view".
- No other new finding. The fix adds no import, no new secret reference, no `continue-on-error` and no new trigger, and `make gate` is PASS on `e4b8459` (the coordinator's line).

**Acceptance criteria (round 2):** the evidence above stands at the new head. The "deploy path still runs the deploy gate" gap that B1 opened is closed by the environment. The `/health` freshness criterion and the live failed-night behaviour remain verifiable only after the owner applies the workflow (`docs/owner-actions.md:21`).
