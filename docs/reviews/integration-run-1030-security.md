---
record_type: review
id: integration-run-1030-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — integration/run-1030 (delta review of the stacked fixes #515, #516, #520, #521, #519, #523, #524)

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need RANGE=8e67df4..91890d6` → `security`: a policy edit in `conformance/test-deploy-shipped.py`, `scripts/brief_fields.py`, `scripts/deploy_gate.py` and `docs/plans/assumptions-1030.md`, #283)
**Independent:** yes. I wrote none of this code. I have not reviewed these branches before.
**Date:** 2026-10-31
**Release range:** 8e67df4..91890d6. `8e67df4` is the head of `integration/fixes-1030` (PR #512). The range has seven merge commits in first-parent order: `2d29b9c` #515, `d378a77` #516, `c1a870a` #520, `b828468` #521, `7309045` #519, `50979d7` #523 and `91890d6` #524. There was no rebase, and the range holds 29 commits.
**Reviewed head:** 91890d699d4ba39242d4daf619e827ca3a357f3d
**Risk tier:** HIGH (a deploy-gate control change; D-231 rules it tightening only). The brief's `Paths that make a change HIGH:` is `none`, so §11's senior-review trigger does not fire.

## Verdict
PASS

The combination loosens nothing. Only `91890d6` needed hand resolution in code: `git show --remerge-diff` shows conflicts in
`scripts/brief_fields.py` and `scripts/deploy_gate.py` and nowhere else. Each one was resolved as the merge message says:

1. #505's content comparison replaces #506's `git diff --no-renames` line in `changed_since` (scripts/deploy_gate.py:220-233).
2. `brief_fields` keeps #505's `verified_tree` and `verified_blobs` (scripts/brief_fields.py:236, :267) together with #509's
   `verified_files(..., suffixes)` (:288, filter at :311).
3. `_workflow_texts` keeps #509 review R2's `(".yml", ".yaml")` filter under #505's variable name `place`
   (scripts/deploy_gate.py:872).

Two three-way checks confirm it:
- `git diff dcf8c6a 91890d6 -- scripts/brief_fields.py` (#509's tip against the final file) adds only #505's two readers.
- `git diff 83b18ac 91890d6 -- scripts/ conformance/` (#505's tip against the final tree) adds only #509's review hunks
  (`dcf8c6a`) and #503's `scripts/ui_test.sh`.

#501 and #505 were cut before `dcf8c6a`. All three of #509's review fixes survive, and each one's test still kills its
mutant. #506's tests still kill a mutant that would let a rename hide. On the real tree, the content comparison and git's
own diff list the same 30 code files. No finding.

I worked in my own worktree, `scratchpad/sec-run`, at `91890d6` (detached). It had its own `.venv` from `make install`
and a copy of `advisor.db` (D-174). I read the policy (this profile, D-231, `docs/plans/assumptions-1030.md` and the five
stacked verdicts) at the reviewed head. That head is the integration branch, whose base `8e67df4` carries none of these
edits. My mutants and probes were driven by scripts in `scratchpad/sec-mut`. Every mutant was an exact single-occurrence
replacement, restored byte for byte and checked by hash. Probe repositories were created under `scratchpad/sec-mut`.
`git status` in the worktree stayed clean after every run.

## Findings

### BLOCKING
- none

### MINOR
- none

### PASS
- **#509's review fixes survive the two merges cut before them.** Each one's mutant is still KILLED at `91890d6`:
  - R2's suffix filter in `verified_files` (scripts/brief_fields.py:311). Removing it fails
    `tests/unit/test_deploy_gate_509.py::test_a_link_beside_the_base_workflows_is_not_read_as_one` (:98).
  - The suffixes argument in `_workflow_texts` (scripts/deploy_gate.py:872). Dropping it fails the same test.
  - M2: a base workflows tree that does not hash leaves the read incomplete (scripts/deploy_gate.py:874). Removing
    `complete = False` fails `::test_a_forged_base_workflows_tree_makes_every_dispatch_a_deploy` (:84).
  - M1: the refuse-all message names the repair (scripts/deploy_gate.py:705-706, `git fetch origin` then
    `git fsck --full`). #509's review asked for a wording change only, and no test was asked for. The text is present
    verbatim.
- **#506's tests now run against #505's code, and they still hold renames.**
  - Mutant N1: `_differs` treats a head path that no longer exists on disk as unchanged (scripts/deploy_gate.py:245).
    This is exactly the "only the new name is listed" shape. It fails
    `tests/unit/test_deploy_gate_506.py::test_a_code_file_renamed_into_a_record_path_is_still_a_change[committed]` (:18).
  - Mutant N2: the new names are dropped from `changed_since` (`| new`, :230). It fails
    `test_deploy_gate_505.py::test_info_exclude_does_not_hide_a_new_code_file` (:60).
  - #506's `diff.renames=copies` case (:35) passes against code that no longer reads git's diff config at all, as it
    should. The rename is listed by both of its sides, by content.
- **Other seam mutants (all KILLED).**
  - `compare_problem` skipped in `changed_since` (:220) → `test_deploy_gate_493.py::test_changed_since_itself_refuses_a_comparison_it_cannot_trust` (:143).
  - Index-only (staged) new entries dropped from `_new_files` (:305) → `test_deploy_gate_505.py::test_a_staged_new_file_is_seen_though_others_does_not_list_it` (:101).
  - Commit hashing off in `batch_read` (scripts/brief_fields.py:147) → `test_deploy_gate_493.py::test_a_forged_reviewed_commit_does_not_hide_a_change` (:78).
- **#510's test on the pinned commit, after #511's one reader.** Two independent guards now refuse a forged pinned
  commit:
  - `brief_fields._commit` peels `rev^{commit}` (scripts/brief_fields.py:166-174), and git's peel hashes the commit.
  - `batch_read` checks the hash itself (:147).

  Removing either guard alone leaves every #494 test green, because the other still refuses. Removing both fails
  `tests/unit/test_deploy_gate_494.py::test_a_forged_pinned_commit_is_not_read_as_the_pinned_tree` (:96). So the
  property is held. This is what was missing at #512 (that verdict's M1), when `_object` was the only guard.
- **The real tree.**
  - `changed_since(<repo>, c29392c)` and `git diff --no-renames --name-only c29392c HEAD`, with records and DevFlow's
    unchanged files removed, list the same 30 files, none extra on either side.
  - `.venv/`, `advisor.db` and `coverage.json` in the worktree are not reported. The committed `.gitignore` files at the
    reviewed head ignore them.
  - `deploy_gate.py --check` exits 1 only because the release verdicts are stale (30 code files since `c29392c` and
    `3cddbdd`). That is the expected fail-closed answer, and it takes 0.6 s (D-231's revisit trigger on speed: not met).
- **Tests at 91890d6.**
  - The eleven `tests/unit/test_deploy_gate*.py` files: 201 passed.
  - `-k "deploy_gate or closure or brief_fields or review_need"`: 313 passed.
  - `conformance/test-deploy-shipped.py`: PASS, 7 cases.
- **Test edits to existing controls weaken no assertion.**
  - The fixture and declaration changes in `test_deploy_gate_494.py:32`, `test_deploy_gate_pin.py:62-64` and
    `conformance/test-deploy-shipped.py:58-60` match the #501 row of `docs/plans/assumptions-1030.md`.
  - `test_deploy_gate_dispatch.py:247-264` moves only its fault injection to the verified reader. Its four assertions
    are unchanged (the #509 row).
- **#503** (`scripts/ui_test.sh:90-106`) adds `xcrun simctl uninstall` of the app's bundle id on the named simulator
  (`UI_TEST_DEVICE`, default `iPhone 17 Pro`), and it is never run on a physical device. It is not destructive outside
  the simulator, and it has no gate surface.
- **The process log.**
  - The range deletes no line.
  - Every line each of the seven branches added is present verbatim: 0 missing for each of `2d29b9c^2` through
    `91890d6^2`.
  - No `## ` heading appears twice.
  - #512's entry and the run's seven 2026-10-30 entries appear once each, in merge order (#510, #506, #511, #509, #503,
    #501, #505) at docs/process-log.md:1584, :1592, :1598, :1605, :1612, :1620, :1627 and :1635, with eight `Lesson:` tags.
- **Hygiene.**
  - All 29 commits carry `GP-Agent:`. None carries an AI attribution.
  - The range touches no `.github/`, `.claude/`, `.githooks/`, `Dockerfile` or `deploy/` path.
  - `pyproject.toml` and `requirements/` are unchanged, and no new third-party import appears: the new imports are
    `hashlib`, `tempfile`, `collections.abc`, `typing` and test-local helpers.
  - No secret, and no destructive operation.
  - `GIT_NO_REPLACE_OBJECTS=1` is still set at import (scripts/deploy_gate.py:102).

## Gates passed
- [x] Secret scan green (`make secrets` at 91890d6, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no new import)
- [x] Default-deny preserved for new external surfaces (no new surface; the gate only refuses more)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model; base files are parsed, never followed)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; HIGH paths `none`)
- [x] SAST: `ruff check --select S` on both gate files finds one S101 at scripts/brief_fields.py:138. It is the
  type-narrowing `assert` that the #493 and #509 verdicts already accepted. `make conformance` at 91890d6: "conformance
  PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- The `91890d6` resolution keeps #505's comparison, #509's `suffixes` and R2's filter →
  scripts/deploy_gate.py:220-233, :872; scripts/brief_fields.py:236, :267, :288-317 (three-way diffs above)
- #509's review fixes survive and are held → tests/unit/test_deploy_gate_509.py:84, :98 (each kills its mutant at
  91890d6); the message at scripts/deploy_gate.py:705-706
- #506's rename case still fails closed on #505's code → scripts/deploy_gate.py:245-265, :230;
  tests/unit/test_deploy_gate_506.py:18, :35 (mutant N1 killed)
- #510's pinned-commit hash is held after #511 → scripts/brief_fields.py:147, :166-174;
  tests/unit/test_deploy_gate_494.py:96 (the compound mutant is killed)
- No process-log entry is lost or doubled → docs/process-log.md:1584-1641 (above)

## Risks queued
- none
