---
record_type: review
id: fix-issue-563-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — fix-issue-563

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` says `security`: a policy edit of `scripts/deploy_gate.py`, #283)
**Independent:** yes. This seat wrote none of the range and read it in its own work tree, detached at the commit under review, with its own venv.
**Date:** 2026-11-02
**Release range:** 9ec7a46..73cd898
**Reviewed head:** 73cd89847e64019d14e0cfe7859ff27e7ae27994
**Risk tier:** MEDIUM. The brief's `Paths that make a change HIGH:` is `none` (docs/project-brief.md:110), but the change edits a deploy-gate control, so this review reads it as a control (fail direction, what can steer it). No auth, PII, payment or migration path is touched, so the §11 senior-review line does not apply.

## Verdict
MINOR

## Findings

### BLOCKING
- none

### MINOR
- **M1** tests/unit/test_deploy_gate_563.py:60-73 — no test covers the strict side of the URL check that the fix depends on. The tests prove that a well-formed origin is named and that a missing origin is not green. No case shows that a look-alike origin is refused (`https://github.com.evil.com/o/r`, `https://github.com@evil.com/o/r`, `https://evil.com/github.com/o/r`, `https://github.com/o/r/x`). The `ssh://git@github.com/` form named in scripts/deploy_gate.py:394-397 is not covered either. Failure scenario: a later edit loosens `_GITHUB_URL` (deploy_gate.py:396-397) to something like `github\.com[/:](.+?)`. Every current test still passes, and `-R` then names a host or path the origin never meant. Not exploitable today: the regex is tight (probes below), and origin's URL is guard-protected (R2). Remedy: add a parametrized negative case asserting `ci_green` is False and `gh` is not called, plus `ssh://git@github.com/o/r.git` on the positive side.

### PASS
- **Q1. Who can still choose the repository.** The fix makes no source worse, and it removes two.
  - `GH_REPO` and `GH_HOST` are dropped from the environment (deploy_gate.py:422). `-R` would override `GH_REPO` anyway. Because the host is spelled `github.com/` in `-R` (:423), `GH_HOST` cannot apply either.
  - `gh repo set-default` writes `remote.<x>.gh-resolved` in `.git/config`. The Bash guard does not refuse that key: its `REMOTE_KEY` covers only `url`, `fetch` and `insteadOf`, .claude/hooks/bash_guard.py:517. The old code obeyed `gh-resolved`, and gh's own remote order (upstream, github, origin, then others) could also pick another remote, such as this repository's `devflow` remote (SADCAIVibe/DevFlow). With `-R`, neither reaches `gh` any more.
  - `remote.origin.url` remains. It is the same trust anchor the gate already uses for its base, since `origin/main` and `origin/HEAD` come from fetches of origin, and the Bash guard already refuses changing it. That covers `git remote set-url/add/rename/remove origin`, `git config` / `-c` / `GIT_CONFIG_*` on any `remote.*.url` or `url.*.insteadOf`, and any write into `.git/config` (bash_guard.py:177-181, :585, :1716, :2238). The guard proved this during this review by refusing even a `git remote add origin` in a scratch repository. The old code read the same `.git/config` through gh's remote resolution, so this is not a regression.
  - `url.<base>.insteadOf` cannot change what the gate reads. `git config --get remote.origin.url` (:418) returns the stored value, not the rewritten one. A rewrite changes only where git itself fetches and pushes. The guard refuses setting it, and its documented residual ("a remote's settings in a config file this does not open", bash_guard.py:311-314) is the gate's base, not this fix.
  - All caller `GIT_*` variables are removed at import (deploy_gate.py:155-157), so `GIT_CONFIG_*`, `GIT_DIR` and `GIT_CONFIG_GLOBAL` cannot redirect the config read.
  - `GH_ENTERPRISE_TOKEN` and `GITHUB_ENTERPRISE_TOKEN` apply only to non-github.com hosts, and the host is fixed. `GITHUB_REPOSITORY` is not a gh repository override, and `-R` outranks everything. `GH_TOKEN` is kept. A token decides only what the caller may see, never which repository's runs are returned.
  - A `gh` alias named `run` does not override the core command. Probed with gh 2.100.0 and an isolated `GH_CONFIG_DIR` whose `config.yml` held `aliases: run: "!echo ALIASED"`: `gh run list -R github.com/o/r` still made the API call (`https://api.github.com/repos/o/r/actions/runs?...&head_sha=00`). Extensions cannot shadow core commands either.
  - What remains is environment-level and pre-existing; see R2.
- **Q2. URL regex** (deploy_gate.py:396-397). Probed 26 inputs through `_github_repo`. Accepted: the https, ssh:// and scp forms, with optional `.git` and trailing `/`. Refused (None): `github.com.evil.com`, `github.com@evil.com`, `evil.com/github.com/...`, `o/r/x`, `u:t@github.com`, `ssh://git@github.com:22/`, `HTTPS://`, `?x`, `#x`, `%2F`, `git@github.com:o/r/../x`, `github.com//r`, `ssh://evil@github.com/`, and an embedded newline. Because `.strip()` runs first, Python's `$`-before-final-newline adds nothing. The character class `[A-Za-z0-9_.-]` excludes `@ : / ? # %` and whitespace, so no second host or path can be appended. It does accept `..` (`../r`, `o/..`). Probed with gh 2.100.0: `gh run list -R github.com/../r` and `-R github.com/o/..` both exit 1 with `path component ".." would traverse the URL path` before any request. That makes them not green, and they reach no other repository anyway. A leading `-` in an owner is harmless: the value is the separate argv element after `-R` and begins with `github.com/`. Owner and repo names that GitHub would not allow simply 404, which is not green.
- **Q3. Fail direction.** Every failure path reads as not green, so a test change counts as code:
  - origin missing or not GitHub: :419-421, and `gh` is never started;
  - `gh` non-zero or HEAD empty: :426 (`[]`);
  - an empty list, a non-list, an unfinished run, or a conclusion other than success or skipped: :427-429. The `any(... == "success")` at :429 runs only after `all(isinstance(x, dict))`, through `and`;
  - `OSError` (no `gh`), `SubprocessError` (the 8 s timeout and git's 30 s), and `ValueError` (bad JSON; strict `.decode()` raising `UnicodeDecodeError`, a `ValueError`) are all caught at :430-431.
  - Not green makes `test-and-ci` count as `code` (:379) and adds the note (:375-378).
  - This seat ran the red test against the base's `scripts/` in a scratch copy: all 4 cases FAIL at 9ec7a46, and all pass at 73cd898.
- **Q4. Fixture edits.** tests/unit/test_deploy_gate_731_tester.py:84 and :132, and conformance/test-deploy-classes.py:62-63, only add `origin https://github.com/o/r.git`, which the new rule needs before it will ask `gh` at all. No assertion was removed or relaxed. The not-green polarities stay in place: `MIXED_GH` in the tester file, and `r.ci("failure")` and `r.ci(None)` at conformance/test-deploy-classes.py:166-169. Their stubs answer whatever `-R` is passed, so they do not test pinning. Pinning is test_deploy_gate_563.py's job, and it asserts `-R github.com/o/r`, `GH_REPO=unset` and `GH_HOST=unset` (:65). Run here: `pytest tests/unit/test_deploy_gate_563.py tests/unit/test_deploy_gate_731_tester.py` 11 passed; `conformance/test-deploy-classes.py` PASS, 75 cases.
- **Q5. Unimplemented third remedy line.** Nothing is open today. The brief has no `Security-invariant tests:` line (D-241 clause 7; absent at 9ec7a46 and at 73cd898). `policy_invariant_tests` returns None unless the tree's brief and every protected base's brief carry the line (deploy_gate.py:247-260). So `change_class` makes every test `code` (:278), `tests` at :373 is empty, and `ci_green` is never called in this project. That is also why #563 is dormant. The latent part is R1.
- Secrets: the diff has no credentials. `GH_TOKEN` appears only as a variable name in prose. No new import and no dependency change, so `make deps` and `make slopsquat` have nothing new to grade. Subprocess calls use list argv with no shell. No destructive operation is in the range.

## Gates passed
- [x] Secret scan: the diff was read in full and holds no key, token or credential (`make secrets` belongs to the branch's `make gate`)
- [x] `make deps`: no dependency change in the range
- [x] `make slopsquat`: no new import
- [x] Default-deny preserved: no new external surface; the control fails closed on every path (Q3)
- [x] Permission-matrix not violated: no workflow, hook, `.claude/` or `.githooks/` file is touched
- [x] Prompt-injection hygiene: `gh`'s output is parsed as JSON data only, never executed
- [ ] Auth/PII checks + human review trigger: n/a, no auth, PII, payment or migration path
- [x] SAST: subprocess with list argv and an explicit `env`, no `shell=True`; nothing new for bandit beyond the S603/S607 class D-241 clause 6 already ruled on

## Acceptance criteria evidence
- #563 "pin `-R`": scripts/deploy_gate.py:418, :423 → tests/unit/test_deploy_gate_563.py:57-65 (asserts `-R github.com/o/r`)
- #563 "drop `GH_*` from its environment" (`GH_REPO` and `GH_HOST`): scripts/deploy_gate.py:422, :425 → tests/unit/test_deploy_gate_563.py:62-65 (`GH_REPO=unset`, `GH_HOST=unset` with both set to hostile values)
- #563 fail closed when no repository can be named: scripts/deploy_gate.py:419-421 → tests/unit/test_deploy_gate_563.py:68-73 (False, `gh` never called)
- #563 "check which tests the `Security-invariant tests:` line names": not implemented; see Q5 and R1

## Risks queued
- **R1** scripts/deploy_gate.py:270-283 — this applies when the owner writes the `Security-invariant tests:` line, which D-241 clause 7 deferred. The tests of the controls themselves are not code by path: 38 files in `tests/unit/` match `deploy_gate|guard|brief_fields|review_need`, among them `test_deploy_gate_563.py`. They become `test-and-ci` unless the line names them, and `conformance/` is `test-and-ci` by rule (:280). Scenario: the line is written as `tests/test_tenant_*.py`. A later change deletes the `-R` assertion at test_deploy_gate_563.py:65 and the loose-regex negative case M1 asks for. CI goes green (the weakened test still passes), and the change re-opens neither release verdict, so the next loosening of `ci_green` can ship with its guarding test already gone. Remedy, at the time the line is written: name the control tests (at least `tests/unit/test_deploy_gate_*.py`, the guard's and `brief_fields`' tests), and record the choice in that ADR. This is the issue's third remedy line, made concrete.
- **R2** scripts/deploy_gate.py:422-425 — pre-existing and unchanged by this fix: `gh` is still resolved from `PATH`, and its configuration from `GH_CONFIG_DIR`, `XDG_CONFIG_HOME` or `HOME`. A gh config can set `http_unix_socket`; probed with gh 2.100.0, it routes the API call through the named socket. `HTTPS_PROXY`, `SSL_CERT_FILE` and `SSL_CERT_DIR` can route it through a proxy the caller trusts. Any of these, written outside the repository and present in the environment the gate runs in, can answer "green" for any `-R`. They need write access to the user's environment or home configuration, which the change under evaluation does not have. Hardening options, if the class is ever made live (R1): call `gh` by an absolute path resolved once, and drop the proxy, CA and config-dir variables the way `GH_REPO` and `GH_HOST` are dropped.
