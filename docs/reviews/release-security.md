---
record_type: review
id: release-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-24
---
# Security Review — deploy delta for release v0.1.0 (Stage 5.1, light mode: #421 / PR #422, #406)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`), Stage 5.1, light mode, dispatched by `/going-live` for the delta before the v0.1.0 hosted deploy
**Independent:** yes. I wrote none of this range's code, tests, records or earlier reviews.
**Date:** 2026-10-24
**Release range:** `9208fd8d86c2cb0fc7b95011337fad642768a27f..471dd79d740f5054d7cc4c7916ca8d4162bfc199` (11 commits). `9208fd8` is the reviewed head of the verdict this one extends. The code the deploy gate counts is three files: `.github/workflows/ci.yml` (`b2d0e3c`, the owner's, #406), `tests/unit/test_ci_needs.py` (`7c1730a`, the owner's plant update), and `tests/unit/test_carry_forward.py` (`3cd571d` red, `d316142` fix, #421, merged as `b7ae3a8` / #422). The rest is docs: #420's release record and owner-actions rows (`f1929cd`, `32a471a`, merge `53782f1`, merge `0bdf2eb`), the previous security verdict (`8a5f958`), the process log, and the release Tester's delta verdict (`471dd79`).
**Reviewed head:** 471dd79d740f5054d7cc4c7916ca8d4162bfc199
**Risk tier:** LOW. The delta changes one CI limit and two test files. No `src/` file, no route, no dependency, no auth, PII, payment or migration path, and no path the brief declares HIGH. The §11 senior-review trigger does not fire.
**Seat:** worktree `review/release-security-422` at `471dd79`, under `$TMPDIR`. I did not run `make install`. The two changed test files ran with the main clone's interpreter, read-only, with `PYTHONPATH` set to my worktree's `src` and `PYTHONDONTWRITEBYTECODE=1` (checked: `app.__file__` resolves into the worktree). I made no edit or commit in the main checkout and no network call. I sent nothing to the launchd service, Fly or GitHub.

> **This record extends** the release delta verdict of 2026-10-23 (`660af4b..9208fd8`, PASS WITH FINDINGS, BLOCKING 0, MINOR 4, reviewed head `9208fd8`). That verdict extends the release verdict at `660af4b`. Both texts stay in git: `git show 9208fd8:docs/reviews/release-security.md` and `git show 660af4b:docs/reviews/release-security.md`. Their MINORs (#410, #411, #412, #417, #418, #419) and queued risks are carried unchanged. This delta touches none of their files.

## Verdict
PASS: BLOCKING 0 · MAJOR 0 · MINOR 0 · NIT 0 · new risks queued 0.

Nothing in the delta changes the product's attack surface.

**The workflow change is the timeout alone.** `git diff 9208fd8..471dd79 -- .github/workflows/ci.yml` is one line: `ci.yml:38`, `timeout-minutes: 15` → `30`. At head, the rest of the workflow is unchanged:
- the triggers stay `pull_request` and `push` (`ci.yml:14-16`), with no `pull_request_target`;
- `permissions: contents: read` (`ci.yml:24-25`);
- the file references no `secrets.` at all;
- the suite still runs inside `unshare --net` with only loopback up and `MODEL_RANKING_REQUIRE_OFFLINE=1` (`ci.yml:65-68`);
- #392's hashed installs (`--require-hashes` at `ci.yml:56`, `:133`, `:167`) are intact.

A longer limit costs runner time on a hung test. It grants no new capability.

**Neither test change weakens a security-relevant assertion.**
- `test_ci_needs.py:56-57` and `:82-83` only update the planted text to match the workflow's new limit. `_planted` (`:44-46`) still asserts that the plant occurs exactly once in the real workflow, so the plant cannot pass vacuously. The #122 network-namespace plant and the contract and epoch plants are unchanged.
- `test_carry_forward.py:40-43` restamps the fixture's `CARRY_TABLES` (a module constant: `scores`, `pricing`, `access`, `build.py:246`) at `NOW` minus one day. Before the fix, the fixture's rows were stamped ahead of `NOW` by the wall clock, which was the defect.
- The expiry tests still prove expiry. Each sets its own age after `_live` (`:92-94` by arrival, `:269-276` and `:307-317` by row stamp), so the restamp makes their starting state realistic and does not loosen them.
- The tests named by INV-23 (`test_the_carry_opens_the_served_artifact_read_only`) and INV-5 (`test_carried_rows_meet_the_rules_every_client_row_meets`, `test_a_carried_date_is_validated_not_cut_and_no_infinity_is_carried`) in `docs/security-invariants.md` keep their names and bodies.
- The new guard test (`:416-427`) fails closed on an empty fixture (`assert stamps`).
- Both files pass at head: `36 passed`.

**No policy file a gate reads changed.** The range's docs are `docs/owner-actions.md`, `docs/process-log.md`, `docs/releases/v0.1.0.md`, `docs/reviews/release-security.md` and `docs/reviews/release-tester.md`. The brief, `docs/security-invariants.md`, `docs/security-baseline.md`, `permission-matrix.md` and `docs/decisions.md` are untouched. The 2026-10-24 owner-actions row records the owner's own `ci.yml` change. It matches `b2d0e3c` exactly, and its `sed` targets line 38 only.

## Findings

### BLOCKING
- none

### MINOR
- none

### PASS
- **Workflow authority held.** The `ci.yml` change is the owner's commit (`b2d0e3c`, no `GP-Agent` trailer, merged through PR #422's merge `b7ae3a8`). No agent commit in the range touches `.github/workflows/**`, `.claude/` or `.githooks/`. Every agent commit carries `GP-Agent` and `GP-Task` trailers. No commit carries AI attribution.
- **The red test came first.** #421's red test (`3cd571d`) precedes its fix (`d316142`), and the fix is test-only. The product's carry logic (`src/app/workflows/build.py`) is unchanged, so the carry window and the expiry bounds reviewed at `660af4b` still hold.
- **No new imports or dependencies.** The only import change is `CARRY_TABLES` from the project's own `app.workflows.build` (`test_carry_forward.py:21`). No lock or `pyproject.toml` change.
- **No destructive operations.** No `reset --hard`, force push, `rm -rf` or `DROP` in any commit of the range.

## Gates passed
- [x] Secret scan green: `make gate` on the merge of main into the release branch, `no leaks found` (dispatcher). Re-run here on the exact range: `gitleaks git --log-opts=9208fd8..471dd79`, `8 commits scanned`, `no leaks found`.
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found` (dispatcher). No dependency or lock changed in the range.
- [x] `make slopsquat` green: PASS (dispatcher). No new third-party import.
- [x] Default-deny preserved for new external surfaces: none added. No `src/` change.
- [x] Permission-matrix not violated: the workflow edit is the owner's (§5, D-218 clause 6). No agent write under `.github/workflows/**`, `.claude/` or `.githooks/`.
- [x] Prompt-injection hygiene: not applicable (LOW tier, no new consumer of untrusted content). No diff content tried to alter policy.
- [x] Auth/PII checks and the human-review trigger: not applicable (no HIGH path, no auth, PII, payment or migration code).
- [x] SAST: not applicable at LOW tier. No production code changed. Conformance PASS (33) on the same tree (dispatcher).

## Acceptance criteria evidence
- #421 (the carry tests no longer age): `tests/unit/test_carry_forward.py:40-43` (the fixture is stamped on `NOW`) and `tests/unit/test_carry_forward.py:416-427` (the guard that the fixture's stamps fall inside the carry window of `NOW`, failing closed on an empty fixture).
- #406 (the test job's limit is 30 minutes): `.github/workflows/ci.yml:38`, with `tests/unit/test_ci_needs.py:56-57` and `:82-83` keeping the CI-needs plants anchored on the real workflow (`:44-46`).

## Risks queued
- none new. The queued risks of the verdicts at `9208fd8` and `660af4b` are carried unchanged.
