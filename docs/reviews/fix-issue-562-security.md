---
record_type: review
id: fix-issue-562-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — fix-issue-562

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` says `security`: policy edits of `scripts/review_need.py` and `scripts/deploy_gate.py`, #283)
**Independent:** yes. This seat wrote none of the range: it read and probed it in its own detached work tree (`wt-sec-562`, its own `.venv` from `make install`), and the fix's author was another session.
**Date:** 2026-11-02
**Release range:** 9ec7a46..c212fe1
**Reviewed head:** c212fe136d6751be0edea0817d0c090800ad0022
**Risk tier:** MEDIUM. The fix changes gate and policy code: which review a change gets, and what the deploy gate counts as code. It touches no auth, PII, payment or migration path. The brief declares no HIGH paths (`docs/project-brief.md:110`), so no senior-review line is owed.

## Verdict
MINOR

The fix closes #562 (M16) in the strict direction. Every reader that classifies paths now treats `.deps-accept` as policy (review-need) or as code (the deploy gate, and `closure_check.py` through it). No spelling of the path escapes. The conformance change is the minimum needed to match the new rule. Nothing in the range loosens a gate. One MINOR remains: the reader script's docstring still says the old rule. Two risks are queued.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/deps_accept.py:12-13`, `.deps-accept:4`. **The waiver's own documentation still states the rule this fix removed.** The docstring says *"the owner's merge is the review, and a change to this file routes to no security review (the owner's trim)"*. The file header says *"the owner's merge is the review"*. After `c212fe1`, a change to the file is a policy edit with a security review in either mode (`scripts/review_need.py:110`, `:214`, `:313-316`), and the deploy gate counts it as code (`scripts/deploy_gate.py:239`). Failure scenario: the next agent, or the next upgrade's porter, learns the control from the reader rather than from `review_need.py`. They see a rule that says this routing is upstream's deliberate choice, and they "restore" upstream's routing (see R2). The text is not exploitable on its own, because the gates read code, not prose. Remedy: one sentence in each place, naming #562 and the policy-edit routing. `scripts/deps_accept.py` is DevFlow-shipped, but `shipped_unchanged` never exempts an edited file (`scripts/deploy_gate.py:589-598`), so editing it only makes it code to the gate, the strict side.

### PASS
- **Q1. Every classifier now sees the waiver as policy or code.**
  - `review_need.EXCEPTION_FILES` holds `.deps-accept` (`scripts/review_need.py:110`). `policy_edits` matches the paths that `git diff --name-only --no-renames` prints (`:244-245`, `:214`), and any policy edit returns `security` in light mode and `code-reviewer+security` in heavy mode (`:313-316`).
  - `deploy_gate.is_deploy_record` no longer lists the file (`scripts/deploy_gate.py:239`), so `change_class` returns `code` (`:271-284`), and `changed_since` (`:346-381`) counts a committed, uncommitted or untracked edit as code.
  - `shipped_unchanged` cannot exempt it either way: `.deps-accept` is in neither `DEVFLOW_TOOLING` nor `DEVFLOW_TOOLING_FILES` (`:557-559`, `:598`).
  - `closure_check.py` reads the same function (`scripts/closure_check.py:70`, `:86-91`). `wave_check.py` recomputes through `review_need.py` (`scripts/wave_check.py:859`).
  - `review_need.RECORDS` (`:122`) is defined and never read. `check_fast.py`'s `RECORDS` is a name for one of its legs, not a classification of paths.
  - I loaded the base and head `deploy_gate` side by side. At base, `.deps-accept` was `record`; at head it is `code`. `./.deps-accept` and `.Deps-Accept` were `code` at both.
  - Probes against the head's `review_need.py`, in throwaway repos built with the test's `Repo` helper:

    | Change | light | heavy |
    |---|---|---|
    | `.deps-accept` edited | `security` | `code-reviewer+security` |
    | `.deps-accept` deleted | `security` | `code-reviewer+security` |
    | `ios/.deps-accept` added | `none` | `none` |

  - **Other spellings.** git prints only repository-relative paths, so `./.deps-accept` never reaches either reader. `--no-renames` lists a rename's deleted side, `.deps-accept`, so a rename is routed. A file under a subdirectory is not an escape: `scripts/deps_accept.py:26-27` reads only `ROOT / ".deps-accept"`. On this case-insensitive checkout (`core.ignorecase=true`), a differently cased write lands in the tracked file, and git reports it as `.deps-accept`.
- **Q2. The conformance case is the minimum change and is stricter than before.** `conformance/test-review-need-mode.py:200-206` replaced its expectation of `none` with `change class: record` by `code-reviewer+security` with `policy edit: .deps-accept`. Only that case changed (diff of `9ec7a46..c212fe1`). `make conformance`: 51 tests PASS. No shipped file is hash-pinned. `make install-check` checks that paths are present against `INSTALL-MANIFEST.md`, and `.install-lock` holds directory file counts. `docs/devflow-pin.txt` is not in the range. The edited conformance file and both scripts now differ from the pinned DevFlow bytes, so the deploy gate counts them as code, the strict side. `scripts/deploy_gate.py` is in `SAFETY_SURFACE` and is code in any case (`:565`). At the next upgrade, upstream's copy of this conformance case will fail against the project's `review_need.py`. That fails closed and forces the decision (R2).
- **Q3. Other routes for a waiver** (detail in R1):
  - pip-audit 2.10.1 reads no ignore list from the environment or from `pyproject.toml`. Its only waiver is the `--ignore-vuln` flag (`.venv/.../pip_audit/_cli.py:376-380`). Its environment defaults cover format, service, OSV URL, description, spinner and output only (`:235-373`).
  - The Makefile includes no `.env` and exports no `PIP_AUDIT_*` (`Makefile:32`, `:57`).
  - CI's `Run pip-audit` does not read `.deps-accept` at all (`.github/workflows/ci.yml:143-147`). Today a waiver therefore reaches only the local `make deps` and `make gate`. The CI audit still blocks a waived advisory until the owner applies the UPGRADING patch (`UPGRADING.md:279-280`).
  - The remaining routes are an `--ignore-vuln` written into `Makefile:434-436`, `stack.mk`, or `scripts/deps_accept.py` itself. Each is code to the deploy gate, so each needs the pre-deploy delta review.
- **Q4. Nothing in the range loosens a gate.** The range has five files: two strict edits (an exception file added, a record removed), the stricter conformance case, a new test, and a process-log entry. It does not change `.claude/`, `.githooks/`, `.github/`, the Makefile, the brief or the decisions.
- **The fix's tests, through the real entry points.** `tests/unit/test_deps_accept_562.py:34-42` routes the change in both modes. `:45-49` checks the gate's class. `:52-60` is `make deploy-check`'s question: a waiver committed after both verdicts makes them stale. `:63-66` holds the routed path equal to `deps_accept.FILE`, derived rather than retyped, in line with AGENTS.md §3.5.
- **Test runs on this head, in this tree.** The three suites `test_deps_accept_562.py`, `test_accepted_cuts.py` and `test_deploy_gate_444.py`: 72 passed. Every unit test matching `review_need`, `deploy_gate`, `closure`, `deps_accept` or `wave_check`: 648 passed.

## Gates passed
- [x] Secret scan green (`make secrets`: "no leaks found", on `c212fe1`)
- [x] `make deps` (pip-audit) green: "No known vulnerabilities found". `.deps-accept` holds no entry (`.deps-accept:1-6`), so nothing is ignored.
- [x] `make slopsquat` green: "20 declared dependency(ies), 0 suspect". The range adds no import outside the stdlib, pytest and the repository's own test helpers.
- [x] Default-deny preserved for new external surfaces (none added)
- [x] Permission-matrix not violated: no destructive operation and no owner-file write in the range
- [x] Prompt-injection hygiene: not applicable (no untrusted content is consumed). Policy is read from the base: the brief at the merge-base (`scripts/review_need.py`'s `brief read at` line).
- [x] Auth/PII checks + human review trigger: not applicable (no HIGH path, and no auth, PII, payment or migration code)
- [x] SAST: the range adds no subprocess, parser or network call to product code. The test uses the existing `Repo` and `_installed` helpers.
- [x] `conformance`: 51 tests PASS

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #562, "a change to `.deps-accept` routes to `security` in `make review-need`": `scripts/review_need.py:110`, `:214`, `:313-316`. Tested by `tests/unit/test_deps_accept_562.py:34-42` and `conformance/test-review-need-mode.py:200-206`.
- #562, "the deploy gate counts it as code, as `data/accepted-cuts.yaml` is (D-221 clause 4)": `scripts/deploy_gate.py:239`, `:277`, `:381`. Tested by `tests/unit/test_deps_accept_562.py:45-49` and `:52-60` (`make deploy-check` through `_installed`).
- #562, "the routed path is the one the reader reads": `scripts/deps_accept.py:27`. Tested by `tests/unit/test_deps_accept_562.py:63-66`.

## Risks queued
- **R1** `Makefile:434-436`, `scripts/deps_accept.py:85-87`, `stack.mk`. **In light mode, a waiver written somewhere other than `.deps-accept` still gets no per-change review.** I probed the head's `review_need.py`:

  | Change | light | heavy |
  |---|---|---|
  | `--ignore-vuln PYSEC-2099-1` added to the Makefile's `deps:` recipe | `none` | `code-reviewer` |
  | `scripts/deps_accept.py` made to print a fixed `--ignore-vuln` | `none` | `code-reviewer` |

  Neither line names a `POLICY_TOKENS` entry (`scripts/review_need.py:115-116`). Failure scenario: in a run with `Merges: do not wait`, an agent "fixes" a red `make deps` by editing the recipe. The change stacks with no security seat, and only the owner's merge reads it. It does not reach a deploy unreviewed, because both files are code to the deploy gate and the pre-deploy delta review reads them. That is why this is a queued risk, not a finding. Light mode's per-change scope (the owner's ruling, 2026-10-17) also covers all gate code this way. Remedy, if the owner wants the same rule for every spelling of a waiver: add `deps_accept` and `ignore-vuln` to `POLICY_TOKENS`, so a Makefile line or a script naming either one becomes a policy edit.
- **R2** `docs/decisions.md` (no entry). **This project rule overrides upstream's v7.3 A20 trim, and no ADR records it.** Project rules on the deploy gate survive upgrades because the upgrade's security delta checks the ported tree against the ADRs (D-241 clause 2, `docs/decisions.md:6668`). The process-log entry names this exact risk in its Lesson. The next upgrade's conformance case will fail closed (Q2), but the record that tells the porter to keep the project's side is a decision, not a test. Remedy: one ADR clause (`/log-decision`), or a line in the run's capture, naming `.deps-accept` among the project's exception files, beside D-221 clause 4 and #444.
