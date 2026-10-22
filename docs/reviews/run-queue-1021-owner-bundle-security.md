---
record_type: review
id: owner-bundle-queue-1021-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-22
---
# Security Review — run queue-1021 owner bundle (#390 deploy gate, #392 workflows)

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` on the range: `security`)
**Independent:** yes. I wrote none of the gate change, the tests, the patch or the issues.
**Date:** 2026-10-22
**Release range:** `f8a5f9f..275acbf` (branch `owner/run-queue-1021-bundle`; round 2 read `9bf45eb..78ba0a0`, round 3 read `78ba0a0..275acbf`, 6 commits) + `build/owner-run-queue-1021.patch`
**Reviewed head:** 275acbf721529864dd3429d6b39f62b4a814ed4f + owner patch sha256 4ac3b3409b9b6d48ac36776b5eb4cdd1734ab2f8fa8b780f0318af7478c7fc2d (round 2: 78ba0a0e87284b17843273e0927d4f371b986b94 + ece1bf5efdae00660bedd850a389287682d2017832fe0411ff7329e41650c741; round 1: 9bf45eb37c9018b4e0aee4b6ed40b67b8301441c + 1835a354bc7847a1fcb38181c2ba2f73deba04edd16d763d71c9ac08e2c0d7d2)
**Risk tier:** MEDIUM. The change touches a control on the safety surface (`scripts/deploy_gate.py` is in `SAFETY_SURFACE`) and CI's install path. The brief declares no HIGH paths (`docs/project-brief.md:110`), and nothing here touches auth, PII, payment or a migration, so no senior-review line is owed.

## Verdict
BLOCKING (round 3: B2 in the owner patch's guard change. A raw VT, FF, CR or LF in an `env -S` string is a separator to env, but not to the shell rules the guard reads it with. It is B1's class, and round 2's remedy left it out. B1's six spellings are fixed, and so are M7-M9 and N4-N6. M10 is new: a MINOR outside the change. See "Round 3" below. The round 1 and round 2 text is kept as found. Round 2 was BLOCKING on B1: the `env -S` escapes in the owner patch's guard change, with MINOR M7-M9 and NIT N4-N6.)

Nothing is loosened. `deploy_in` still runs the declared match first (`scripts/deploy_gate.py:357-360`), and the new `gh` reading only adds refusals. A gate exception exits non-zero, and the guard refuses on any non-zero exit (`.claude/hooks/bash_guard.py:3350-3353`), so the gate fails closed. The four spellings #390 names are now refused, through the gate and through the guard. The patch removes both `cache: 'pip'` restores and every unhashed `pip install`.

Some gaps remain in the same class, and each one ships its impact at MINOR. These protections still hold:
- The `fly-production` environment admits only `main`.
- The night runs `deploy_gate.py --check` on main's checkout.

So a dispatch that slips past the gate still ships only reviewed code. What it loses is D-185 clause 5 ("no agent deploys"), the same grade as the origin finding (#387 review, M1). M1-M3 are agent-writable gate code inside #390's own scope ("by any spelling"): fix them on this branch before handover, or keep #390 open with them filed. M6 is pre-existing and outside the range, but it is a fail-open of the guard's own `fly deploy` refusal. The caller should file it now and tell the owner.

## Method
- I worked in my own worktree at `9bf45eb` (`$TMPDIR/sr-bundle-1021`) with its own venv: dev.lock + build.lock with `--require-hashes`, then the project `--no-deps -e .`. I touched neither the main checkout nor `wt-bundle`.
- **The patch.** Its sha256 matched `1835a354...`. `git apply --check` was clean, and then I applied it.
- **Tests before the patch:** `test_deploy_gate_dispatch.py`, `test_deploy_gate_base_policy.py` and `test_ci_installs.py` gave 100 passed and 1 failed. The failure is `test_no_workflow_restores_a_cache_and_every_pip_install_is_hash_checked`, red by design.
- **Tests after the patch:**
  - The same files plus `test_nightly_hosted.py`: 142 passed.
  - `test_bash_guard_bounds.py` and both `test_review_need_*`: 732 passed.
  - `conformance/test-ci-yaml.py`: PASS (26 steps, 0 findings).
  - `conformance/run-all.py`: PASS (33 tests, 0 failing).
- **Mutation probes on `deploy_gate.py`.** I made 10 mutants. All 10 were killed by `test_deploy_gate_dispatch.py`:
  - no base read
  - UNKNOWN fail-open
  - the `workflows and` guard dropped
  - `name:` derivation dropped
  - `-R` not valued
  - alias reader returns None
  - rerun dropped
  - declared dispatch files dropped
  - stem dropped
  - no `unquote`
- **Mutation probes on `test_ci_installs.py`.** I made 4 mutants and all 4 were killed: the hash check always passes; the `actions/cache` check is dropped; installs are not counted; a stray lock is accepted.
- **Probes.** I ran about 140 probes in a scratch repository, each set up like the test's `own` fixture. Each probe went through `deploy_gate.deploy_in` directly, and through `bash_guard.judge_call` with `OWN` pointed at that repository.
- **Read-only checks against GitHub (GET only; I ran no dispatch and no write):**
  - path normalisation of `repos/umutcanapaydin/Model_Ranking/actions/workflows/...`;
  - `gh workflow view` on a path, a stem and a name;
  - the source of `gitleaks/gitleaks-action@ff98106e`, `anthropics/claude-code-action@9d7150bc` and `superfly/flyctl-actions@fc53c09e`.
- **Dependency resolution.** `pip install --dry-run --require-hashes -r requirements/dev.lock` for Linux x86_64 resolves on Python 3.11 (exit 0); the governance job now installs the full dev lock on 3.11. It also resolves on 3.12.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/deploy_gate.py:383,443-445`: a REST dispatch that names the workflow by its URL-encoded path passes the gate.
  - **Example:** `gh api -X POST repos/o/r/actions/workflows/.github%2Fworkflows%2Fnightly-hosted.yml/dispatches -f ref=main` is "not a deploy" (`deploy_in` returns None; the guard allows it).
  - **Why it passes:** `_gh_api` unquotes the endpoint before matching. The decoded slashes break `DISPATCH`'s `[^/?#]+` segment, and neither `RERUN` nor `REPOSITORY_DISPATCH` matches.
  - **GitHub accepts this form.** `GET repos/umutcanapaydin/Model_Ranking/actions/workflows/.github%2Fworkflows%2Fci.yml` answered `id 331653943, path .github/workflows/ci.yml`, the same workflow as `.../workflows/ci.yml`. `//`, `/./` and `/x/../` all answer 404, so only the encoded path gets through.
  - **Remedy:** match `DISPATCH` on the raw, lower-cased endpoint, then `unquote` and basename the captured segment, or on the decoded text match `/actions/workflows/(.+?)/dispatches` and basename it. Add the case to `DEPLOYS`.
- **M2** `scripts/deploy_gate.py:408-413` (`_workflow_of`): a workflow word that the shell or a wrapper rewrites is read literally, and a name it does not know passes.
  - **Not deploys, guard included:**
    - `gh workflow run .github/workflows/nightly-host*.yml`. It is a glob, and in zsh and bash it expands to the installed file once the owner installs it. `gh workflow view .github/workflows/ci.yml` shows gh resolves a path.
    - `cd .github/workflows && gh workflow run rel*`
    - `gh workflow run [r]elease.yml`
    - `gh workflow run {release.yml,}` (bash: one word, `release.yml`)
    - `find .github -name release.yml -exec gh workflow run {} \;`
    - `echo release.yml | xargs -I X gh workflow run X`
  - **Same root cause:** when the brief declares a dispatch whose file is unreadable (not yet fetched, as after the owner installs it on main), the workflow's `name:` passes. In my probe `r1`, `gh workflow run the-night` passes and `night.yml` is refused.
  - **Remedy, failing closed:** a workflow word that names no workflow the gate read (tree or base: file, stem or `name:`), or that holds a glob or brace character (`*?[]{}`), is UNKNOWN whenever a deploy workflow exists. This over-refuses only a typo, and it also covers `xargs -I`, for which the guard does not pass its `behind_xargs` to the gate.
- **M3** `scripts/deploy_gate.py:432-435,454-461`: the docstring says an alias "whose expansion is one of these" is judged, but these pass:
  - `gh alias set -s ship 'gh workflow run release.yml'`. With `--shell` and no `!`, the gate reads the expansion as gh words, `gh gh workflow ...`.
  - `gh alias set ship -` with the expansion on stdin, which `gh alias set --help` documents; also `<<< 'workflow run release.yml'`.
  - A shell expansion that the reader does not unwrap the way the guard does: `'!bash -c "gh workflow run release.yml"'`, `'!x=gh; $x workflow run release.yml'`, `'!curl -X POST .../dispatches'`.
  - A prefix alias, where both steps pass: `gh alias set w workflow && gh w run release.yml`, and `gh alias set a api && gh a -X POST repos/o/r/actions/workflows/release.yml/dispatches`. gh appends the extra arguments.
  - **Time of check:** an alias set while the verdicts are current is allowed, and its later `gh ship` is never judged. Judging the definition cannot hold this.
  - **Remedy:** judge the invocation. A `gh` command whose first positional is not one of gh's own commands is an alias or an extension that the gate cannot read, so it is UNKNOWN. That also closes pre-session aliases, aliases in `~/.config/gh/config.yml` or `GH_CONFIG_DIR`, and `gh <extension>`. gh's command set would be a named enumeration with a written reason (AGENTS.md section 3.5), or derived from `gh help`. Also make every `gh alias set` or `gh alias import` UNKNOWN while a deploy workflow exists: a shell alias is arbitrary code.
- **M4** The three classes the author named as not covered have no disposition, which leaves an open loop (AGENTS.md section 3): curl or another HTTP client with `gh auth token`, a pre-session gh alias, and a workflow that deploys through an action.
  - I found no issue for any of them (`gh issue list`: #389-#396 cover none), no entry in `docs/refusals.md`, and nothing in the range's process-log or assumptions rows.
  - **Same class, unnamed:**
    - `gh extension install` followed by `gh <ext>`;
    - a workflow that deploys as `flyctl deploy`, or with the command split across a `\` continuation line. My probe `r6`: `_runs_deploy` (`scripts/deploy_gate.py:490-501`) derives none of the three workflows as a deploy.
  - **Remedy:** file each as an issue, or refuse it in `docs/refusals.md` with a reason, before #390 closes. For the workflow class, a derivation that fails closed: a workflow with `environment:`, or one that reads a `secrets.` other than `GITHUB_TOKEN`, is a deploy workflow.
- **M5** `.github/workflows/ci.yml:93` (after the patch; `gitleaks/gitleaks-action@ff98106e`): CI still restores an Actions cache, the path #392 is about (R3).
  - **What it does:** `src/gitleaks.js:27-30` at that sha calls `cache.restoreCache` with key `gitleaks-cache-8.24.3-linux-x64`, and on a miss downloads the release with no checksum and saves it.
  - **The attack:** a compromised nightly refresh job on `main` holds the runtime token. It can write that key once the entry is evicted (7 days without access, or the 10 GB limit filled by the same token). Every later `secret-scan` run, a PR's included, would then run its binary, and a planted gitleaks reports no leaks.
  - **The claims it contradicts:** the patch's comment (`ci.yml:7`, "no dependency cache") and the test's docstring (`tests/unit/test_ci_installs.py:10`). The test sees only `setup-python` `cache:` and `actions/cache` (`:142-145`), not caches inside an action.
  - **Remedy, in the patch:** run gitleaks from a pinned release tarball checked with `sha256sum -c`, in place of the action. Or file it as #392's remainder.
  - **For the test:** list each third-party `uses:` as a named entry with a written reason why it restores no Actions cache. `claude-code-action` sets `no-cache: true` on setup-bun. `setup-flyctl` uses only the runner's local tool cache.
- **M6** `.claude/hooks/bash_guard.py:1541-1550`. This is pre-existing, outside the range, and owner-only. The guard reads `env -S` only from a word that starts with `-S` or `--split-string`. So a combined option passes the guard whole, with no deploy gate and no D-185 `fly` refusal:
  - `env -iS 'fly deploy'`, `env -iS'fly deploy'`, `env -vS'fly deploy'`, `env -0S 'fly deploy'` and `env -iS'gh workflow run release.yml'` are all ALLOW.
  - `env -S'fly deploy'`, `env -i -S 'fly deploy'` and `env -uX -S'fly deploy'` are refused.
  - macOS `env` runs `env -iS 'echo y'` and `env -i -vS'echo x'`, as I checked.
  - **Remedy:** read `S` anywhere in a short-option cluster: `re.match(r"^-[^-]*S", arg)`, taking the rest of the word or else the next word. Add the four spellings above as must-block cases to `test_bash_guard_bounds.py`.
  - This is the guard's own refusal failing open. File it now and tell the owner. It does not block this bundle, which does not touch the guard.

### PASS
- **The red test reproduces #390, and the fix holds it.** The four spellings the issue names are refused: through `deploy_in` against this repository's own brief and `scripts/ci/nightly-hosted.yml` (`tests/unit/test_deploy_gate_dispatch.py:198-212`), and through the guard's `judge_call` (`:236-244`).
- **The gh options I tried are read at every placement.** None of these slipped past: `gh -R`, `gh workflow --repo`, `-Ra/b`, `-rmain`, `--json`, `--`, `--hostname`, `-XPOST`, `--input`, `-H`, `--paginate`, `--cache`, `-i`, upper-case endpoints, `%2E` or `%73` in the endpoint, `?query` and `#fragment`.
- **Wrappers.** `env`, `command`, `exec -a`, `nice`, `timeout`, `script`, `watch`, `bash -c`, `sh -c`, `eval`, a function body, a subshell, `$( )`, plain `xargs` and `\gh`/`"gh"`/`g\h` are all refused through the guard.
- **Unreadable words fail closed.** An id, `$w`, `$(...)`, `$'...'` and a missing workflow are all UNKNOWN, and UNKNOWN is a deploy whenever a deploy workflow exists.
- **Q2: the derivation fails closed where the brief declares the dispatch.** The declared `gh workflow run nightly-hosted.yml` puts the file in the set without any text (`scripts/deploy_gate.py:507`). An id, a rerun or `$w` is still refused with no workflow file anywhere (probe `r1`), and with no base at all (probe `r2`). An unreadable workflow file raises `PermissionError`, and the guard refuses on the gate's non-zero exit (probe `r3`).
- **Q3: the policy is base-pinned, and a change cannot shrink the set.** `declared()` is the base brief joined with the tree's. The workflow texts are the tree's joined with the base's (`:464-487`), and the names from both copies are kept. A change that drops the deploy step still dispatches a deploy (`test_dispatch.py:188`). A change that renames the workflow (probe `r4`) blocks both the old and the new name. The guard refuses every way I tried of moving the base: `update-ref` of origin/main, `fetch .` into it, `remote set-head`, `symbolic-ref` of origin/HEAD (#318).
- **Q4: the patch leaves no unhashed `pip install` and no `cache:` in either workflow.** The installs are `ci.yml:55,56,107,141` and `contract-tests.yml:88,89,108,109`. `pip-audit==2.10.1` and `pyyaml==6.0.3` are hashed in `requirements/dev.lock:950,1249`. The dev lock resolves on 3.11 and 3.12 for Linux. The 3.11 install is new, in `install-and-governance`. The audit job's `--disable-pip` reads the locks, not the environment, so the heavier install does not change what is audited. M5 is the one remaining cache restore.
- **The agent half (`test_ci_installs.py`) derives its file set and fails closed.** An empty set, a YAML parse error, or zero installs is a failure. Its planted cases kill all four of my mutants.
- **No new third-party import.** The new imports are `urllib.parse` (stdlib), and `yaml`/`pytest` in tests, already declared (`pyproject.toml:21,51`).

## Gates passed
- [x] Secret scan green (`scripts/secrets_scan.py` in my worktree with the patch applied: no leaks found)
- [x] `pip-audit --strict --disable-pip` over every lock: no known vulnerabilities
- [x] `slopsquat` green: 20 declared dependencies, 0 suspect (no new third-party import in the range)
- [x] Default-deny preserved: the change only adds refusals, and an exception or an unreadable word fails closed
- [x] Permission matrix not violated: the agent wrote no `.github/workflows/**`; the patch is the owner's to apply (`docs/owner-actions.md:22`)
- [x] Prompt-injection hygiene: the gate reads workflow and brief text as data and never executes it; it parses the alias text it reads with `shlex`
- [ ] Auth/PII checks + human review trigger: not applicable (no auth, PII, payment or migration path; brief HIGH paths `none`)
- [x] SAST-equivalent: about 140 adversarial probes and 14 mutants, listed above; `conformance/run-all.py` PASS

## Acceptance criteria evidence
- **#390.** Expected: "An agent that starts the nightly deploy by any spelling meets the deploy gate."
  - The four spellings in the issue's Steps are refused: `tests/unit/test_deploy_gate_dispatch.py:198-212` (the real tree) and `:236-244` (the guard's `judge_call`). The general cases are at `:96-160`.
  - "Any spelling" is not yet met: see M1, M2 and M3, and M4 for the named classes.
- **#392.** Done when: the agent proposes the diff, the owner applies it, and a conformance test holds that no CI install runs without `--require-hashes`.
  - The test: `tests/unit/test_ci_installs.py:170-185`. It is red at `9bf45eb` and green with the patch applied.
  - The installs: `.github/workflows/ci.yml:55,107,141`, `contract-tests.yml:88,108`.
  - "So no other workflow's run can write what main's CI restores" is not yet met: see M5.

## Risks queued
- **R1** `scripts/deploy_gate.py:26` says "a dispatch runs the default branch's copy". With `--ref <branch>` or `-f ref=<branch>`, GitHub runs that branch's copy, and neither the tree nor the base the gate reads need hold it (`gh workflow run ci.yml --ref evil-branch` passes). Today this is not exploitable: `nightly-hosted` runs only when `github.ref == 'refs/heads/main'`, and the only Fly token is the main-only `fly-production` environment's secret. Treat a dispatch whose ref is not the default branch as UNKNOWN, or correct the docstring.
- **R2** Unverified, because checking it needs a write call. `POST .../check-suites/{id}/rerequest`, `.../check-runs/{id}/rerequest` and GraphQL `rerequestCheckSuite` may re-run an Actions run, and the gate allows them. `POST .../actions/runs/{id}/pending_deployments` would release a waiting deploy job if `fly-production` ever gains required reviewers. Adding these to `RERUN` is cheap.
- **R3** The `nightly-hosted` deploy job's `setup-flyctl` downloads `flyctl` 0.4.111 with no checksum. It uses only the runner's local tool cache, so it is not a cache-poisoning path. This is the version pin of the #387 review's M5; a checksum would complete it.

## NIT
- **N1** `scripts/deploy_gate.py:485`: a failing `git ls-tree` or `git show` at the base is swallowed, and the loop stops at the first failing file. The docstring's "the verdicts refuse every deploy then" holds only when `protected_base` is None, not when the base resolves but cannot be read. Fail closed instead: on that exception, make every dispatch UNKNOWN.
- **N2** `scripts/deploy_gate.py:389`: `WORKFLOW_NAME` drops everything from ` #` on, including inside quotes. `name: "Ship #1"` is read as `ship`, so `gh workflow run "Ship #1"` passes (probe `r5`). M2's fail-closed rule covers this.
- **N3** `docs/owner-actions.md:22`: the row names the patch's sha256, but its command does not check it. The patch sits in gitignored `build/`. Prefix the command with `echo "1835a354bc7847a1fcb38181c2ba2f73deba04edd16d763d71c9ac08e2c0d7d2  build/owner-run-queue-1021.patch" | shasum -a 256 -c &&`. The owner still sees the diff in the draft PR before merging.

## Round 2 (2026-10-22, head 78ba0a0, patch sha256 ece1bf5e...)

**Verdict: BLOCKING.** The patch fixes #400 in part but not completely: B1 below. Everything on the branch is good to go, and all of it is verified, except the new MINORs M7-M9.

### Method
- I worked in my own worktree at `78ba0a0` (`$TMPDIR/sr2-bundle-1021`) with its own venv, built from dev.lock and build.lock with `--require-hashes`. I touched neither the main checkout nor `wt-bundle`.
- **The patch.** Its sha256 matched `ece1bf5e...`. `git apply --check` was clean, and then I applied it.
- **Before the patch:** the agent half is red, as intended. The failures are:
  - `test_ci_installs`: 2 tests;
  - `test_bash_guard_env_split`: 18 tests.
- **After the patch:**
  - `test_deploy_gate_dispatch`, `test_deploy_gate_base_policy`, `test_ci_installs`, `test_bash_guard_env_split`, `test_nightly_hosted`, `test_bash_guard_bounds` and both `test_review_need_*`: 942 passed;
  - `conformance/test-ci-yaml.py`: PASS (27 steps);
  - `conformance/run-all.py`: PASS (33 tests, `test-bash-guard` included, run against the patched guard);
  - the secret scan: no leaks.
  - The range changes no lock and adds no third-party import, so I did not re-run `pip-audit` or slopsquat.
- **The guard pin.** The sha256 of the patched `.claude/hooks/bash_guard.py` is `48068c55e8d50faa27741ec152c40d29b6a098eb71a037039787c54b13879bb0`. Both hooks in the patched `.claude/settings.json` pin exactly that value. The `settings.json` hunks change only the two pins.
- **Mutants on the patched guard.** I copied the guard to a scratch mirror under `cl/hooks/`, a path not named `.claude`, with the env-split test pointed at it. I made 6 mutants, and all 6 were killed:
  - an unread option passes;
  - `S` is not valued;
  - an unknown letter is accepted;
  - only a cluster's first letter is read;
  - no long-option prefixes;
  - the option's value is not skipped.
- **Mutants on the round-2 gate.** I made 9 mutants, and all 9 were killed by `test_deploy_gate_dispatch.py`:
  - `GH_COMMANDS` dropped;
  - alias definitions allowed;
  - the unknown-name rule dropped;
  - `REWRITTEN` dropped;
  - `complete` ignored;
  - an incomplete base read stays silent;
  - `SAME_PROGRAM` dropped;
  - no continuation join;
  - the old `DISPATCH` regex.
- **Probes.** I re-ran every round-1 probe file, and added about 90 probes: through the patched guard's `judge_call`, and through `deploy_in`.
- **Real tools, harmless commands only:** macOS `env -S` with `echo`; and gh 2.100.0 with shell aliases that only `echo`, in an isolated `GH_CONFIG_DIR` under the scratchpad. I made no dispatch and no write call to GitHub.
- **gitleaks.** I downloaded `gitleaks_8.24.3_checksums.txt` and the linux_x64 tarball from the v8.24.3 release, uploaded by `zricethezav`. The checksums file lists `9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c`, and the tarball's own sha256 equals it. That is the value in the patched `ci.yml`.

### Round-1 items
- **M1 fixed.** `DISPATCH` now reads `(.+?)` on the decoded endpoint (`scripts/deploy_gate.py`, `DISPATCH`). `.github%2Fworkflows%2Frelease.yml` and its lower-case `%2f` form are refused, and `.github%2Fworkflows%2Fci.yml` is allowed.
- **M2 fixed.** These are now refused:
  - the glob, `[r]`, `{release.yml,}` and `cd .github/workflows && gh workflow run rel*`;
  - `find -exec ... {}` and `xargs -I X ... X`;
  - a name that no workflow read here has.
  - `gh workflow run ci.yml` and `CI` are still allowed.
- **M3 fixed, with remainders M7-M9 below.** An unknown gh command is refused (`gh zzz`, `gh co`, `gh ship`), and so are `gh alias set` and `gh alias import` whatever the expansion. `gh alias list` and `gh alias delete` are allowed.
- **M4 dispositioned.** `flyctl` and `\` continuations are now derived (killed mutants). The rest is filed as #401, which also holds R2.
- **M5 fixed in the patch.**
  - **No cache.** `ci.yml` runs gitleaks 8.24.3 from its release tarball, checked by `sha256sum -c` against the release's own checksums file, and nothing restores an Actions cache.
  - **Same arguments as the action.** They match `gitleaks-action@ff98106e` `src/gitleaks.js` `Scan()`: `detect --redact -v --exit-code=2 --report-format=sarif --report-path=results.sarif --log-level=debug`, plus `--log-opts`.
  - **A run never interpolates `${{ }}` into the script:** the event values reach the step only as environment variables.
  - **Local check.** gitleaks 8.30.1 accepts the same arguments; the 8.24.3 binary is Linux-only, so I could not run that version here.
  - **The test.** `test_ci_installs.py` now names each action in `ACTIONS` with its reason, refuses `gitleaks-action` and `actions/cache`, and refuses a `curl` or `wget` with no `sha256sum -c`.
- **M6: fixed for option clusters, not for the `-S` string itself; see B1.** Every spelling from round 1 is now refused, plus `--sp`, `--split=`, `-C dir -S`, `-iu X`, `-iC/ -S`, `env env -iS`, `sudo env -iS` and the abbreviated longs. An unreadable option is refused (`-iZ`, `--i`). A legitimate `env -i ls`, `-u HOME ls` or `-P /usr/bin ls` is allowed.
- **N1 fixed.** A base `git show` failure now sets the read incomplete, and an incomplete read makes every dispatch a deploy (killed mutant).
- **N2 fixed.** A quoted `name:` is read whole, and anything it cannot match is UNKNOWN through the M2 rule anyway.
- **N3 fixed.** The owner row runs `shasum -a 256 -c` on the patch before `git apply`.
- **R1 and R3: refused**, with reasons, in `docs/plans/assumptions-queue-1021.md`. That is not in `docs/refusals.md`; see N6.
- **R2:** filed as #401.

### BLOCKING
- **B1** `.claude/hooks/bash_guard.py:1557` (patched; `judge_text("env " + text, ...)`): the string `-S` carries is judged with shell rules, but `env` splits it by its own rules.
  - **`env -S` has escapes the guard never reads:** `\_` separates arguments, `\t`, `\n`, `\v`, `\f` and `\r` become whitespace, and `${NAME}` expands from the environment.
  - **Verified with macOS `env`:**
    - `env -S 'echo\_single'` prints `single`;
    - `env -S 'printf\_<%s>\n\_x\_y'` runs printf with arguments `x` and `y`;
    - `env -S 'ec${NOPE_UNSET_1021}ho via-brace-expansion'` runs echo;
    - `env -S'-S echo\tT1\tT2'` prints `T1 T2`.
  - **Allowed by the patched guard, each of which runs `fly deploy` or a dispatch:**
    - `env -S 'fly\_deploy'`
    - `env -S 'fl${X}y deploy'`
    - `env -S'sh -c fly\_deploy'`
    - `env -S'-iS fly\_deploy'`
    - `env -S'-S fly\tdeploy'`
    - `env -S'-iS gh\_workflow\_run\_release.yml'`
  - **Why it blocks:**
    - It is a one-word, fail-open path around the guard's own D-185 `fly deploy` refusal: an agent deploying unreviewed code with the owner's Fly login.
    - It lies inside the code this patch changes, for the issue (#400) the patch is meant to close.
    - Applying the patch costs the owner a re-pin and a new session, so a second patch for the same issue would cost that again.
    - It is not a regression: the old guard allows these too.
  - **Remedy, failing closed:** refuse a `-S` string that holds a `\` or a `$` (`ENV_UNREAD`, or a sibling message), or translate env's escapes before judging. Translation would mean `\_` and `\t\n\v\f\r` become separators, `${...}` is unread, `\c` ends the string, and `\\`, `\'`, `\"`, `\#` and `\$` become literals. Add the six spellings above as must-block cases to `test_bash_guard_env_split.py`. Re-verify by me.

### MINOR
- **M7** `scripts/deploy_gate.py:453,456`: the gate lower-cases the command word before checking `GH_COMMANDS`, but gh resolves aliases case-sensitively.
  - **Verified** in an isolated `GH_CONFIG_DIR`: shell aliases named `Workflow`, `RUN`, `Run` and `Api` ran (`RAN-Api`) on `gh Api repos/o/r/pulls`.
  - **Allowed by the gate:** `gh Workflow`, `gh RUN`, `gh Api repos/o/r/pulls`.
  - **Remedy:** check the word as written (`given[0]`, not lower-cased) against `GH_COMMANDS`.
- **M8** `scripts/deploy_gate.py:423-432`: an option before the command word that the gate takes as a flag shifts what it reads.
  - **How:** cobra reads an unknown `-z`/`--zz` before the command as taking a value. So in gh, `gh -z workflow zz` and `gh --zz workflow zz` ran the alias `zz` (`RAN-zz -z workflow`), while the gate reads `workflow zz` and allows both.
  - **Remedy:** an option before the first positional that is not in `GH_VALUED` or `-h`/`--help`/`--version` is UNKNOWN.
- **M9** `scripts/deploy_gate.py:400`: `gh extension exec <name>` runs an extension, and `extension` is in `GH_COMMANDS`, so `gh extension exec x` and `gh extension exec x release.yml` are allowed. `gh ext exec x` is refused, because `ext` is not in the list.
  - **Remedy:** `extension exec` (and `extensions exec`) is UNKNOWN.
- **M7-M9 stay MINOR:** each needs an alias or an extension that exists already (set before the session, while the verdicts were current, or written into gh's config), and a dispatch on main still ships only reviewed code. Fix them on the branch with B1's round, or add them to #401.

### NIT
- **N4** `docs/owner-actions.md:22`: the command holds unescaped `|` (`| shasum -a 256 -c`, `|| true`) inside a table cell. A rendered table cuts it there (the #387 review's N1). Escape it as `\|`, or hold the command in a script.
- **N5** `.github/workflows/ci.yml` (patched `secret-scan` step):
  - **New-ref push.** On a push whose `before` is all zeros, the step scans `-1` where the action scanned every pushed commit. CI pushes only to `main`, which is never created, so this does not change what is scanned today.
  - **The `curl` check.** `tests/unit/test_ci_installs.py:171` accepts a whole run block if any `sha256sum -c` appears in it, so a second, unchecked `curl` in the same block would pass.
- **N6** R1 and R3 are refused only in `docs/plans/assumptions-queue-1021.md`. AGENTS.md section 5 keeps refusals in `docs/refusals.md`.

### Gates (round 2)
- [x] Secret scan: no leaks (patched worktree)
- [x] No lock or third-party import change in `9bf45eb..78ba0a0`; round 1's `pip-audit` and slopsquat results stand
- [ ] Default-deny preserved for the guard's `env -S`: B1
- [x] Settings pin equals the patched guard (`48068c55e8d5...`, both hooks)
- [x] gitleaks sha from the release's own checksums file; arguments match the action
- [x] `GH_COMMANDS`: a word outside it fails closed, except for case (M7)

### Acceptance criteria evidence (round 2)
- **#390.** These spellings are refused:
  - round 1's: `tests/unit/test_deploy_gate_dispatch.py:96-160,198-212,236-244`;
  - round 1's M1-M3 cases: added in `1400be6` and green at `78ba0a0`.
  - Open: M7-M9.
- **#392.** `tests/unit/test_ci_installs.py` (`test_no_workflow_restores_a_cache_and_every_pip_install_is_hash_checked`, `test_the_secret_scan_runs_gitleaks_from_a_checked_release`) is red at `78ba0a0` and green with the patch.
- **#400.** `tests/unit/test_bash_guard_env_split.py` is red at `78ba0a0` and green with the patch. Open: B1.

## Round 3 (2026-10-22, head 275acbf, patch sha256 4ac3b340...)

**Independent:** yes. A fresh Security-Reviewer seat took this round over, because the seat that ran rounds 1 and 2 stopped part-way through round 3. I wrote none of the gate change, the tests, the patch or the issues, and I did not run rounds 1 or 2.

**Reviewed head:** 275acbf721529864dd3429d6b39f62b4a814ed4f + owner patch `build/owner-run-queue-1021.patch` sha256 `4ac3b3409b9b6d48ac36776b5eb4cdd1734ab2f8fa8b780f0318af7478c7fc2d`

**Verdict: BLOCKING.** One BLOCKING, B2. It is B1's class, and round 2's remedy left it out. The six spellings round 2 named are fixed, and so are M7-M9 and N4-N6. M10 is new, a MINOR outside the change.

### Method
- **The seat.** I worked in my own worktree at `275acbf` (`$TMPDIR/sr4-bundle-1021`), with its own venv built by `make install` (`--require-hashes` from `dev.lock` and `build.lock`). I touched neither the main checkout nor `wt-bundle`. At the end I reversed the patch (`git apply -R`) and removed the worktree by its literal path.
- **The patch.** Its sha256 matched `4ac3b340...`. `git apply --check` was clean, and then I applied it. It touches 4 files: `.claude/hooks/bash_guard.py` (+59/-4), `.claude/settings.json` (the two pins only), `ci.yml` and `contract-tests.yml`.
- **Before the patch:** `test_bash_guard_env_split.py` and `test_ci_installs.py` gave 29 failed and 56 passed.
  - The 29 failures are 27 env-split cases, the hook-exit test included, and both `test_ci_installs` tests.
  - Each of the six round-2 B1 spellings is among the red cases.
- **After the patch:**
  - the two agent-half files: 85 passed;
  - `test_deploy_gate_dispatch`, `test_deploy_gate_base_policy`, `test_bash_guard_bounds`, `test_bash_guard_conformance_timeout`, `test_nightly_hosted`, the three `test_review_need_*` files and the two agent-half files: 971 passed;
  - `conformance/test-ci-yaml.py`: PASS (27 steps, 3 workflows);
  - `conformance/run-all.py`: PASS (33 tests, `test-bash-guard` included, run against the patched guard);
  - `make check-records`: PASS;
  - `make secrets`: no leaks;
  - ruff, on the changed Python: clean.
- **No lock or import change.** `78ba0a0..275acbf` changes neither `pyproject.toml` nor `requirements/`, so round 1's `pip-audit` and slopsquat results stand.
- **The pin.** The patched guard's sha256 is `a2137e8ff11675d8b9b2531c195fb9715c224b177f9283201b43334b5bd27541`. Both hooks in the patched `.claude/settings.json` pin that value, and `python3 -I .claude/hooks/guard_pin.py --check` gives `guard-pin PASS ... a2137e8ff116`.
- **Probes.**
  - **Through the guard.** I judged 67 strings through the patched guard's `judge_call`, in a directory no brief governs. Nothing was executed.
  - **Real `env`, harmless commands only.** I ran macOS `/usr/bin/env -S` on `printf`, with each raw separator in turn (below).
- **Mutants.** 9 mutants, all killed (below). The guard mutants ran in a scratch mirror under `cl/hooks/`. The gate mutants ran in the worktree, and the gate was restored byte-identical (sha256 compared, `git status` clean apart from the patch).

### Round-2 items
- **B1: fixed for every spelling round 2 named, in every place a `-S` string is read.**
  - **One reading point.** The patched guard reads an `env` option at a single point, `.claude/hooks/bash_guard.py:1555` (`_env_option`, `:1596-1617`). That covers a clustered short option (`-iS`, `-i0vS`), a glued value (`-S'...'`, `-iS'...'`), a separate value, the long form (`--split-string X`, `--split-string=X`) and an abbreviated long one (`--s`, `--sp`, `--split=`, `--spl=`). It also covers `-S` after other options and their values (`-u X`, `-uX`, `-C /tmp`, `-C/`, `-P /usr/bin`, `--unset X`, `--chdir=/`, `A=b`, `-i -- env -S`).
  - **The check.** Every `text` that reading returns meets the backslash-and-`$` check at `:1562-1563` (`ENV_S_UNREAD`, `:543`) before it is judged. An option the guard cannot read is refused at `:1556-1557` (`ENV_UNREAD`).
  - **The tests.** The six round-2 spellings are must-block cases at `tests/unit/test_bash_guard_env_split.py:100-105`, beside `env -S "fly\_deploy"`, `--split-string='fly\_deploy'` and `-iS 'echo\_x'`. All of them are refused with `#400`.
  - **The probes.** All of these are refused too:
    - `sudo`, `nohup`, `timeout 5`, `nice -n 5`, `command`, `exec` and `time` in front of `env -S 'fly\_deploy'`;
    - `/usr/bin/env`, `\env`, `"env"`, `e''nv` and `env env`;
    - `xargs env` and `echo | xargs env`;
    - `sh -c`, `bash -c` and `eval` of `env -S 'fly\_deploy'`;
    - `env -S $'fly\\_deploy'`, `env -S fly\\_deploy` and `env -S "fly\\_deploy"`.
  - **The other `-S` reader.** The guard has one more: the `-i` scope check (`_env_options`). It judges nothing.
  - **What it costs.** `env -S 'ls -l'`, `env -iS 'echo hi'`, `env -i ls`, `env -u HOME ls`, `env -- ls` and `env -C /tmp ls` are still allowed.
  - **What stays open:** B2, below.
- **M7 fixed.** `scripts/deploy_gate.py:468,478` compares the command word as written (`given[0]`) against `GH_COMMANDS`.
  - **Tests:** `tests/unit/test_deploy_gate_dispatch.py:157-159` (`gh Api ...`, `gh Workflow`, `gh RUN`).
  - **Also probed:** `gh ALIAS set x y` and `gh Extension exec x` are UNKNOWN.
- **M8 fixed.** `_unread_leading_option` (`scripts/deploy_gate.py:439-451`, called at `:478`) makes UNKNOWN any option before the command word that is not `-h`, `--help`, `--version` or a `GH_VALUED` flag with its value.
  - **Tests:** `:161-163` (`gh -z workflow zz`, `gh --zz workflow zz`, `gh -Ra/b ...`), and on the allowed side `:185-188` (`gh -R a/b pr list`, `gh --repo=a/b issue view 1`, `gh --help`, `gh extension list`).
  - **Also probed:** `gh -f workflow zz`, `gh --repo workflow zz`, `gh -X POST zz`, `gh -hz workflow` and `gh -R=a/b Api x` are UNKNOWN. A `GH_VALUED` flag in front, which cobra also takes as valued, ends at an alias word, and the alias word is not in `GH_COMMANDS`.
- **M9 fixed.** `scripts/deploy_gate.py:480` makes `extension exec` UNKNOWN.
  - **Tests:** `:165-166`.
  - **Also probed:** `gh extensions exec x`, `gh ext exec x`, `gh extension -R a/b exec x` and `gh extension --zz exec x` are UNKNOWN.
- **N4 fixed.** In `docs/owner-actions.md:22`, `\|` and `\|\|` are escaped. A GFM parser (markdown-it, with tables on) renders the file as 12 rows of 5 cells. The row's command cell renders as `... | shasum -a 256 -c && (git worktree remove ... || true) && ...`, with every pipe intact, and the row names the new sha `4ac3b340...`.
- **N5 fixed.**
  - **The push range.** The patched `ci.yml:115-119` scans the pushed commits from first^ to last, whatever `before` is. That matches the action's `Scan()`: `-1` for a single commit, and "No commits to scan" when there are none. The event values reach the step only as `env:` variables.
  - **The test.** `tests/unit/test_ci_installs.py:200-217` (`download_problems`) needs a later `sha256sum -c` line that names the very file each `curl`/`wget` wrote. The cases at `:332-343` cover a second unchecked download, a check written before the download, a download straight into a pipe, and a check of the wrong file. Three of the four cases pass the round-2 rule and are found only by the new one: the second download, the check written first, and the wrong file. The pipe case is found by both rules.
  - **One remaining NIT:** N7, below.
- **N6 fixed.** R-2 and R-3 are now rows in `docs/refusals.md:28-29`, each with its reason, who ruled and a re-open trigger, and each renders as 5 cells. `docs/plans/assumptions-queue-1021.md` points to them. Both are ruled by the run's lead, and the owner may overrule them; the owner's merge of this bundle is that confirmation.

### BLOCKING
- **B2** `.claude/hooks/bash_guard.py:1562` (patched): a raw whitespace character that env splits on, and that the shell does not, passes the guard.
  - **What the check sees.** It refuses a `\` or a `$`, but a raw VT, FF or CR is neither. The text is then judged as `env ` + text with shell rules, and the shell does not split words on VT, FF or CR. A raw LF is a command separator to the shell, so the guard reads `env fly` and `deploy` apart, and allows both.
  - **What `env -S` does.** It splits on every one of them. Verified with macOS `/usr/bin/env -S`: `printf<SEP><%s><SEP>A<SEP>B` prints `<A><B>` for SEP = VT, FF, CR, LF and TAB.
  - **Allowed by the patched guard:**
    - `env -S $'fly\vdeploy'` (one line to type: the guard decodes `$'...'` into a raw VT);
    - `env -S $'fly\fdeploy'`, `$'fly\rdeploy'`, `$'fly\ndeploy'`, `$'fly\x0bdeploy'` and `$'fly\013deploy'`;
    - `env --split-string=$'fly\fdeploy'`;
    - `env -iS'fly<VT>deploy'`, and `env -S 'fly<VT>deploy'` with the raw character inside quotes;
    - `env -S 'sh -c fly<VT>deploy'` and `env -S 'gh<VT>workflow<VT>run<VT>release.yml'`.
    - A raw TAB is refused, because the shell splits on it too.
  - **Why it blocks:**
    - It is the same one-word, fail-open path around the guard's own D-185 `fly deploy` refusal that B1 named.
    - It lies inside the code this patch changes, for the issue (#400) the patch is meant to close.
    - The patch costs the owner a re-pin and a new session.
    - It is not a regression: the unpatched guard allows the same strings.
    - Round 2's remedy listed env's escapes, `\t\n\v\f\r`, but not the raw characters, so the author followed it as written. The miss is the review's.
  - **Remedy, failing closed:** refuse a `-S` string that holds a `\`, a `$`, or any character that is not printable other than a space.
    - I planted that check in a scratch copy of the patched guard: `any(c in "\\$" or (not c.isprintable() and c != " ") for c in text)` at `:1562`.
    - With it, every raw-separator string above is refused, every must-block probe is refused except the out-of-scope ones (M10, and the two controls with no `env` in them), the six allowed spellings stay allowed, and the 42 `test_bash_guard_env_split.py` tests pass.
    - Add as must-block cases: `env -S $'fly\vdeploy'`, `env -S $'fly\fdeploy'`, `env -S $'fly\rdeploy'` and `env -S $'fly\ndeploy'`, plus one with a raw VT inside single quotes.
  - **Count:** this is the second BLOCKING round on #400's `env -S` reading. A third on the same finding ends the loop (`/fix-issue` step 6).

### MINOR
- **M10** (outside the change; not a regression): `find . -exec env fly deploy \;` and `find . -exec env -S 'fly deploy' \;` are allowed by the patched guard and by the unpatched one, while `find . -exec fly deploy \;` is refused.
  - **Why.** `find -exec` is not in `WRAPPERS` (`.claude/hooks/bash_guard.py:390`), so the `env` behind `-exec` is never unwrapped. The program after `-exec` is judged, but not through the wrapper walk.
  - **Why only MINOR.** It is a fail-open path around D-185 like B2, but outside the code this patch changes.
  - **Remedy:** file it as an issue now. The owner re-pins the guard for B2 anyway, so a fix in the same patch saves a second re-pin.

### NIT
- **N7** `tests/unit/test_ci_installs.py:215`: `target in later` matches a substring, so a check of `aa.tgz` vouches for a download to `a.tgz`. Compare whole words, for example the second field of the checksum line. It does not affect today's `ci.yml`.

### Mutants (round 3)
- **Guard**, in a scratch mirror, against `test_bash_guard_env_split.py` (5 of 5 killed):
  - the backslash dropped;
  - the `$` dropped;
  - the check only for a word starting `-S`;
  - the check only for a separate value (`used == 2`);
  - the check removed.
- **Gate**, in the worktree, against `test_deploy_gate_dispatch.py` (4 of 4 killed; restored byte-identical, and the baseline after the restore is 103 passed):
  - M7: `given[0]` back to `pos[0]`;
  - M8: `_unread_leading_option` not called;
  - M8: an unknown leading option skipped instead of UNKNOWN;
  - M9: `extension exec` allowed.

### Gates (round 3)
- [x] Patch sha256 `4ac3b340...` matched; `git apply --check` clean
- [x] Secret scan: no leaks (patched worktree)
- [x] No lock or third-party import change in `78ba0a0..275acbf`
- [ ] Default-deny preserved for the guard's `env -S`: B2
- [x] Settings pin equals the patched guard (`a2137e8ff116`, both hooks; `guard_pin.py --check` PASS)
- [x] `conformance/run-all.py` and `conformance/test-ci-yaml.py` PASS
- [x] `GH_COMMANDS`: a word outside it fails closed, case included (M7), and so do an unread leading option (M8) and `extension exec` (M9)

### Acceptance criteria evidence (round 3)
- **#390.**
  - Round 1's spellings are refused: `tests/unit/test_deploy_gate_dispatch.py:96-160`.
  - Round 2's M7-M9 cases are at `:157-166`, with their allowed counterparts at `:185-188`. They are red at `5d4be8f` and green at `f3d4256` onward (`scripts/deploy_gate.py:439-451,468,478-481`).
- **#392.** `tests/unit/test_ci_installs.py` (`test_no_workflow_restores_a_cache_and_every_pip_install_is_hash_checked`, `test_the_secret_scan_runs_gitleaks_from_a_checked_release`, and `test_every_download_is_checked_by_the_file_it_wrote` at `:342`) is red at `275acbf` without the patch and green with it.
- **#400.** `tests/unit/test_bash_guard_env_split.py` is red at `275acbf` without the patch and green with it. The B1 cases are at `:100-105`. **Open: B2.**

### Risks queued
- **R4** M10 (`find -exec` in front of a wrapper) needs an issue.
- **R5** #401 still holds round 1's M4 remainder and round 1's R2. Unchanged by this round.
