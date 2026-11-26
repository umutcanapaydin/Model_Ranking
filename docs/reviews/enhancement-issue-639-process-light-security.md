---
record_type: review
id: enhancement-issue-639-process-light-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-26
---
# Security Review — enhancement-issue-639-process-light

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` says `security`: a policy edit of `scripts/deploy_gate.py` and `scripts/brief_fields.py`, #283). The profile, `AGENTS.md`, `permission-matrix.md` and `docs/security-baseline.md` were read at `main` (`ac6d905`), not from the range.
**Independent:** yes. This seat wrote none of the range and read it in its own work tree (`review/639-process-light-security` at `4a6b9b4`, under the scratchpad) with its own venv.
**Date:** 2026-11-26
**Release range:** ac6d905..4a6b9b4 (`8da2f0b` D-257 and the plan; `2a22cbc` and `b4c6c5f` the red tests; `99a9cb5` the deploy gate; `e4af737` `later`; `dcea4bc` the rule text; `10fe73e` and `4a6b9b4` the release Tester's tests and verdict)
**Reviewed head:** 4a6b9b48324ffbf95da252141a447a3a0a11559d
**Risk tier:** MEDIUM. The brief's `Paths that make a change HIGH:` is `none` (`docs/project-brief.md:110`), but the change relaxes a deploy-gate control, so it is read as a control: its fail direction, and what the change under evaluation can steer. No auth, PII, payment or migration path is touched, so the §11 senior-review trigger does not fire.

## Verdict
MINOR -- no BLOCKING. No path lets a change to `src/`, `ios/` product code, `scripts/`, the image's files or a cited security-invariant test deploy without a delta review. Four MINOR findings: a brief edit can switch the derived mode on over a glob-form base (M1, not reachable here), the cited tests' harness is a record (M2), `later` accepts a BLOCKING id and states no severity (M3), and one `docs/later.md` row is user-visible by its own words (M4).

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/deploy_gate.py:376` -- base-pinned policy, partly: whether the register form is in force (`derived`) is read from the UNION of the tree's and the bases' lines, so the change under evaluation can turn it on. Over a base whose line names globs only, a change that edits the brief (a record) to add any existing `.md` file citing one test turns every uncited test from test-and-CI into a record, and a test change then deploys with CI red. Probed in a throwaway repository with the d257 harness: base line `tests/test_tenant_*.py`, the change adds `docs/notes.md` (already at base) to the line and edits `tests/test_app.py`, CI red: `deploy-check PASS`; without the brief edit: refused (`1 code file(s) changed since`). Not reachable in this project: `main` carries no line today (`policy_invariant_tests` returns None, every test code), and once #640 merges every base carries the register form, so `derived` is already true. Not user-visible. Remedy: decide `derived` from the bases' lines only (return it from `policy_invariant_tests`), with that probe as its test.
- **M2** `scripts/deploy_gate.py:385-386` with `docs/security-invariants.md` -- the cited tests' harness is a record. `tests/conftest.py`, `tests/skips.py` (the one place a test may skip, its `NEEDS` table), `tests/__init__.py` and the `tests/fixtures/` files cited tests read are uncited, so a change to them re-opens no verdict, CI green or red. Probed: a change whose `tests/conftest.py` sets `collect_ignore = ['test_tenant_scope.py']` (the cited test) passes `deploy-check` with CI red. That is the d8710b5 route (D-257's rationale) by a side door: an invariant test silenced with no delta. It ships nothing by itself (any later `src/` change still re-opens both verdicts), hence MINOR. Remedy: cite `tests/conftest.py` and `tests/skips.py` in the register (the register's own test then keeps them cited), or derive, as code, every `conftest.py` and the `tests/` modules a cited test imports.
- **M3** `scripts/wave_check.py:83`, `:112-117`; `scripts/pr_check.py:209-215` -- `later` is checked by key only. `pr_check` reads BLOCKING sections too (`SECTIONS`, `scripts/pr_check.py:68`), and `later_problem` accepts a `B1` as readily as an `R1`: with a row `fix-issue-9-security.md B1` whose reason reads "MEDIUM, user-visible", `later_problem` returns None. Nothing asks the row, or the finding, to be LOW. The row is still visible in the PR diff and in `docs/later.md`, so nothing is hidden, and the human merging sees both; editing `docs/later.md` in the same PR is acceptable on that ground. A severity guard is owed for the cheap cases: refuse `later` for an id from a BLOCKING section (`B<n>`), and require the row's third cell to start with `LOW`, so the author states the class in writing where a reviewer can contest it.
- **M4** `docs/later.md:11` -- the row `release-security.md R37` (was #631) says "a user would see a long name". D-257 clause 4: a finding a user can see is at least MEDIUM and stays an issue. Latent (no source has produced such an id), but user-visible when it fires, by the row's own words. Remedy: drop the row and reopen #631 as MEDIUM, or rewrite the reason if the name would in fact never reach a screen (`src/app/workflows/registry.py:930`).

### PASS
- **What re-opens a verdict.** `change_class` (`scripts/deploy_gate.py:365-387`) checks the derived invariants BEFORE `is_deploy_record`, so the register (`docs/security-invariants.md`) is code although it is under `docs/`; a cited test is code; a policy-module test stays code (`_POLICY_TEST`); `src/`, `ios/` product files, `data/`, `scripts/`, `Makefile`, `pyproject.toml`, the locks, `Dockerfile` and `fly.toml` fall through to code. Every file `.dockerignore` lets into the image (`Dockerfile`, `pyproject.toml`, `requirements/serve.lock`, `requirements/build.lock`, `src`) is code. `git ls-files` matched against `TEST_PATH` outside `tests/`, `conformance/` and the tooling dirs yields only `ios/EngineTests/` and `ios/UITests/` -- test targets, not the app; nothing under `src/` or `data/` matches.
- **Register edits and base pinning.** Each base's register is read at that base, from the base's own brief line, through `verified_blob` (`scripts/deploy_gate.py:316-318`, `:337-346`); the union means a change can add a citation but not drop one (`tests/unit/test_deploy_gate_d257.py:127-132`). A base whose register is unreadable or cites nothing fails closed (`:344-345`), and a mismatch between `protected_bases` and the policy roots returns None (`:334-335`). A tree brief without the line returns None (every test code). Moving a cited test is its old path's deletion, which is code.
- **Traversal and links.** `_tree_file` refuses an absolute path, a `..` part and a symlink (`:308-313`; the Tester's `test_deploy_gate_d257_tester.py`); a refused tree register falls back to the entry itself as code while the bases' citations stand. A citation can only ADD a spelling to the code list (glob metacharacters widen it; `..` inside is the Tester's L19), never remove one.
- **The allow-lists as records.** `.language-allow` and `.skill-refs-allow` are read only by `scripts/check_records.py` (the English rule) and `conformance/test-documented-skills.py`; neither ships, and neither feeds a secret, dependency, guard or deploy check. Exact-path match (`:187`, `:263`).
- **`later` key matching** is exact set membership on a normalised first cell (`wave_check.py:91-117`), read at the range's end in `pr_check` (`git show <end>:./docs/later.md`), not loose.
- **D-257's text keeps the do-not-touch list.** The range touches no `.github/`, `.claude/`, `.githooks/`, `permission-matrix.md`, `Makefile`, `conformance/`, `pyproject.toml`, lock, `Dockerfile` or `fly.toml` (`git diff --stat` over them: empty). AGENTS.md §3 Git authority, §3.3 red-first, §5 and the commit-identity rule are unchanged; the deploy gate still runs every deploy; secret-scan and dep-audit are untouched; ADRs stay owed for a data source and a licence (D-257 clause 3, `docs/decisions.md:7185`).
- **Commits.** All eight carry the owner's identity with `GP-Agent: claude-code` and `GP-Task: #639`, no AI attribution; no destructive command in any diff; `gitleaks git --log-opts=ac6d905..4a6b9b4`: `no leaks found`.

## Gates passed
- [x] Secret scan: `make gate` at `dcea4bc` (secrets inside it) and `gitleaks` over `ac6d905..4a6b9b4` here: no leaks
- [x] `make deps`: green inside the gate; no dependency change in the range
- [x] `make slopsquat`: `slopsquat PASS: 20 declared dependency(ies), 0 suspect`; standard-library imports only
- [x] Default-deny preserved: no external surface; the derivation fails closed at every base (M1 is the one place the tree steers a relaxation, unreachable here)
- [x] Permission-matrix not violated: no workflow, hook, `.claude/` or `.githooks/` file touched
- [ ] Prompt-injection hygiene: n/a, no LLM or fetched content; the register is parsed by one regex as data
- [ ] Auth/PII checks + human review trigger: n/a, no auth, PII, payment or migration path
- [x] SAST: no subprocess, `eval` or deserialisation added; `pr_check` adds one `git show` with list argv through the existing `git()` helper

## Acceptance criteria evidence
- D-257 clause 2, an uncited test is a record: `scripts/deploy_gate.py:385-386` → `tests/unit/test_deploy_gate_d257.py:60-64`, `:113-117` (passes with CI red)
- D-257 clause 2, the register and the cited tests stay code: `scripts/deploy_gate.py:376-378` → `tests/unit/test_deploy_gate_d257.py:66-69`, `:120-124`
- D-257 clause 2, a change cannot drop a citation: `scripts/deploy_gate.py:337-346` → `tests/unit/test_deploy_gate_d257.py:127-132`
- D-257 clause 2, an empty or unreadable derivation fails closed: `scripts/deploy_gate.py:291-305`, `:344-345` → `tests/unit/test_deploy_gate_d257.py:55-58`, `:135-144`
- D-257 clause 2, the allow-lists are records: `scripts/deploy_gate.py:187`, `:263` → `tests/unit/test_deploy_gate_d257.py:79-82`
- D-257 clause 4, `later` only with a row: `scripts/wave_check.py:112-117`, `scripts/pr_check.py:209-215` → `tests/unit/test_findings_later.py:94-104`
- 50 tests (`test_deploy_gate_d257.py`, `test_deploy_gate_d257_tester.py`, `test_findings_later.py`, `test_security_invariants.py`) pass in the seat's venv at `4a6b9b4`

## Risks queued
- **R1** `AGENTS.md:92` -- "The Tester and the Security-Reviewer review user-facing code only ... never docs, tests or records" reads as if a cited test or a register edit needs no review, while the deploy gate (rightly) refuses one until a delta closes it. The gate decides, so nothing deploys; an agent reading only the sentence may be surprised. Remedy: add "except the register and the tests it cites" to the sentence. LOW.
- **R2** `docs/later.md:3-7` -- a row "leaves this file when its fix merges, or when the owner promotes it", and no check says which: a row deleted in a PR closes a finding with no fix and no issue, where closing an issue at least leaves a closed issue. Git keeps the row. LOW.
