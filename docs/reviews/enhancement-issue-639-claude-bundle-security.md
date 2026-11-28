---
record_type: review
id: enhancement-issue-639-claude-bundle-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-28
---
# Security Review — the D-257 `.claude/` owner bundle (#639)

**Reviewer:** Security-Reviewer subagent. An owner bundle owes a review before it is applied (`scripts/owner_bundle.py:106-114`). D-257, the gate code and the profile were read at `main` (`ccdc91c`, #640 merged), not from the patch.
**Independent:** yes. This seat wrote none of the patch. It read it in its own work tree (`review/639-bundle-security` at `ccdc91c`, under the scratchpad) and did not apply it: the guard forbids writing `.claude/`, and nothing in the patch runs.
**Date:** 2026-11-28
**Reviewed patch:** f1c3580985c1de65c77481181ed64ea4c7e893e2585dffa0419f378076f41089 (round 2; round 1 read `ee882e4f21cdc13be97be95fe63adddda6cb980ceb930846e75a053a4a66daec`)
**Base:** ccdc91c
**Risk tier:** MEDIUM. The patch is prose only. It changes reviewer profiles and skills, which steer what reviewers read and how findings get dispositions. No auth, PII, payment or migration path is touched, so the §11 senior-review trigger does not fire.

## Verdict
PASS (round 2, patch f1c3580985c1: M1 and M2 resolved, R2 and R3 resolved, R1 handled by process; round 1 was MINOR)

Round 1, as it read: MINOR. There is no BLOCKING finding. `shasum -a 256` matches the patch's name, and `git apply --check` is clean at `ccdc91c`. The patch touches 9 Markdown files and 13 hunks, all under `.claude/skills/*/SKILL.md` and `.claude/agents/{Tester,Security-Reviewer}.md`. It touches no hook, settings file, guard, `.githooks/` or `.github/` file, and it has no binary hunk. Gitleaks on the patch reported no leaks. Nothing on the do-not-touch list is loosened: direct pushes to main, the PR and merge-commit flow, the `.github/workflows` and `.claude/` write bans, the permission matrix, the Bash guard, red-first tests, the deploy gate, secret scanning and dependency audits, and licence and data-source ADRs. The gate code decides every deploy, and no edit tells an agent to skip a review that the gate still requires. Two passages are still looser than the code they describe (M1, M2).

## Findings

### BLOCKING
- none

### MINOR
- **M1** `.claude/agents/Security-Reviewer.md` moment 2 and `.claude/skills/going-live/SKILL.md` "A hotfix" (patch hunks 1 and 8): the deploy delta is said to be "owed only for user-facing code", with the exempt list "docs, records and a test `docs/security-invariants.md` does not cite". This is looser than `change_class` in three ways.
  - (a) The gate treats all of `.claude/`, `.githooks/`, `scripts/`, `conformance/`, `.github/` and the `Makefile` as code (`scripts/deploy_gate.py:184`, D-257 clause 2: "`scripts/` stays code as a whole"). These paths are not user-facing under clause 1, but they still re-open both verdicts. This bundle is one example: once applied, its `.claude/` files re-open them.
  - (b) Under the register form, only a test FILE is a record (`:193`, `:431`; Security M31 on #639). A conftest, `tests/skips.py`, a package `__init__`, a helper or a fixture stays code, and so does a test of a policy module (`_POLICY_TEST`, `:404`).
  - (c) A register that cites no test, or cannot be read, fails closed: every test is code (`:331`). The prose says none of this.

  The gate fails closed, so nothing deploys unreviewed. The risk is a delta reviewer, told by its own profile that a conftest or `scripts/` change is "not owed", who moves its `**Reviewed head:**` without reading the change. That is the d8710b5 or M31 route that D-257's rationale names. No user sees this. Remedy: "owed whenever the deploy gate classes a changed path as code (`make deploy-check` lists them); docs, records and an uncited test FILE re-open no verdict, while a conftest, helper, fixture, policy-module test, `scripts/` and `.claude/` do". In the Tester profile (hunk 3), "a test ... does not cite" should likewise read "a test file ... does not cite".
- **M2** `.claude/skills/pre-merge/SKILL.md` §7 (patch hunk 11) shortens AGENTS.md §7 (`AGENTS.md:130`) and D-257 clause 6 from "what is red (every red check, required or not)" to "what is red". A red advisory check, such as a scan or `make ci-liveness`, could then be left out of the final report. The `AGENTS.md` §7 pointer still carries the full wording, which is why this is MINOR. No user sees this. Remedy: keep "(every red check, required or not)".

### PASS
- **Clause 4 matches the gate.** The `fix-issue` hunk states the key as `<verdict file> <id>`, with a reason that starts `LOW` and a BLOCKING finding never `later`. This is what `later_rows` and `later_problem` enforce (`scripts/wave_check.py:88`, `:101`, `:116-117`), as `pr_check.py:209-215` and `wave_check.py:1369` read them. "LOW and no user can see it" is stricter than the gate, which cannot test visibility. A finding a user can see is at least MEDIUM in all five hunks that mention it.
- **Clause 3 keeps every licence and data-source ADR.** In `log-decision` step 0, a data source, a licence, the architecture, the release or version policy, and relaxing a control all still require an ADR. "Retiring" a control in the description is a subset of relaxing one. The ADR-before-code rule (`wave_check.py`, #201) is untouched.
- **Clause 1:** the Tester's light-mode scope (src/, ios/, the published data, and the deploy gate and the files that feed it) is clause 1's list. Heavy mode and the cited tests stay in scope.
- **Clause 6:** a PR body's findings table and Risks are untouched. Pre-merge §8 still governs the body.
- No hunk changes the Security-Reviewer's checklist (sections 1-8), its BLOCKING taxonomy, the §11 senior-review line, or any Escalate-NOW item.

## Gates passed
- [x] The patch's sha256 equals `ee882e4f21cdc13be97be95fe63adddda6cb980ceb930846e75a053a4a66daec`.
- [x] `git apply --check` is clean at `ccdc91c`.
- [x] Secret scan: gitleaks found no leaks in the patch.
- [x] `make deps` and `make slopsquat`: not applicable. The patch adds no import and no dependency.
- [x] No hook, settings file, guard, `.githooks/` or `.github/` path is touched.
- [x] The permission matrix is not violated. The default-deny deploy gate is unchanged.
- [x] Prompt-injection hygiene: the patch is policy text that the owner applies. Nothing under review was taken as an instruction to this seat.
- [ ] SAST: not applicable. The patch is prose only.

## Acceptance criteria evidence
- D-257 clause 1 → patch hunk 3 (`.claude/agents/Tester.md:9`), against `docs/decisions.md` D-257 clause 1.
- D-257 clause 2 → hunks 1 and 8, which are looser than `scripts/deploy_gate.py:184,193,331,404,431` (M1).
- D-257 clause 3 → hunk 9 (`.claude/skills/log-decision/SKILL.md:3,6-7`).
- D-257 clause 4 → hunks 2, 4, 5, 6, 7, 10 and 12, against `scripts/wave_check.py:84-120` and `scripts/pr_check.py:200-215`.
- D-257 clause 6 → hunk 11 (`.claude/skills/pre-merge/SKILL.md:156-157`), which is looser than `AGENTS.md:130` (M2).

## Risks queued
- **R1** Applying the bundle changes `.claude/`, which the deploy gate treats as code (`scripts/deploy_gate.py:184`). Both deploy verdicts then owe a delta before the next night's deploy. The owner-actions row for the apply should say so.
- **R2** `/file-issue`'s new line ("a LOW finding no user can see is not filed") does not restate that an Escalate-NOW event (AGENTS.md §3), such as a fault that stays green with no test, is never a LOW `docs/later.md` row. The AGENTS.md rule still binds. This is LOW: the reader of `/file-issue` meets that rule at session start.
- **R3** The fix/file/refuse bullets of `/close-wave` step 6 have no `later` bullet giving its disposition and key. Only the lead sentence mentions it. `make wave-check` enforces the key (`wave_check.py:1369`). This is LOW: heavy mode only, and the gate holds it.

## Round 2

**Patch:** `f1c3580985c1de65c77481181ed64ea4c7e893e2585dffa0419f378076f41089`. The sha256 matches, `git apply --check` is clean at `ccdc91c`, and gitleaks found no leaks. The same 9 `.md` files are touched, now with 14 edits. No hook, settings file, guard, `.githooks/` or `.github/` path is touched. I compared the patch's `+`/`-` lines with round 1's: only the passages below changed.

- **M1: resolved.** Security-Reviewer moment 2 and going-live "A hotfix" now say the delta is owed "for every change the deploy gate counts as code", and that `make deploy-check` says which. The gate is the authority, so no reviewer reads its own exemption into a `scripts/` or `.claude/` change.
  - The exempt set is now docs, records, and a test file that the register does not cite and no cited test imports. This matches `change_class` (`scripts/deploy_gate.py:431`, `TEST_FILE` `:193`) and the import closure (`_imported_tests` `:298`, `_with_imports` via `expand_invariants` `:329-344`).
  - `scripts/`, `.claude/`, test support files and policy tests are named as code (`:184`, `:404`).
  - going-live adds the fail-closed rule for an unreadable register (`:331`). It does not mention the other fail-closed case, a register that cites no test. That is not a loosening: the same sentence makes `make deploy-check` decide.
  - The Tester profile now says "test file … and no cited test imports" and "`make deploy-check` decides".
- **M2: resolved.** pre-merge §7 now reads "what is red (every red check, required or not)", as `AGENTS.md:130` and D-257 clause 6 do.
- **R1: handled by process.** The owner applies the bundle on a branch, and the Tester's and the Security-Reviewer's deploy deltas run on that branch before it merges. The `.claude/` change then never reaches a deploy unreviewed. The gate refuses it anyway (`:184`).
- **R2: resolved.** file-issue now adds "an Escalate-NOW event (AGENTS.md §3) never is" a `docs/later.md` row.
- **R3: resolved.** close-wave step 6 gains a `later` bullet: keyed `<verdict file> <id>`, the reason starting `LOW`, never for a BLOCKING finding. This matches `scripts/wave_check.py:88`, `:101` and `:116-117`.

### Round 2 findings
- none

### Round 2 risks queued
- none
