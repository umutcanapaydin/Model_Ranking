---
record_type: review
id: fix-issue-506-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — fix-issue-506

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need RANGE=2d29b9c..0e5ac5d` routed the change to `security` for a policy edit: `scripts/deploy_gate.py`, #283)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before. I reviewed it in my own worktree at 0e5ac5d with its own venv (D-174).
**Date:** 2026-10-30
**Release range:** 2d29b9c..0e5ac5d (`aab6906` red test, `0e5ac5d` fix and process-log entry)
**Reviewed head:** 0e5ac5df5b42ab2e22b09a6206db914545b9ff90
**Risk tier:** HIGH (a deploy-gate control change; tightening only, pre-approved by D-231 clause 1)

## Verdict
PASS

The fix closes #506 on every path I could build: committed, staged, unstaged (a plain `mv`, and a plain `mv` plus
`git add -N`), and under every clone-local config I tried, `diff.renames=copies` included. Each new test fails when
the flag is removed. The change only adds paths to the list the gate refuses on, so it cannot loosen anything. The
issue names no other bypass. One untested path is queued (R1).

## Findings

### BLOCKING
- none

### MINOR
- none

### PASS
- **The fix itself.** scripts/deploy_gate.py:199 adds `--no-renames` to `git diff --name-only <head>` in
  `changed_since` (:190-207). The command-line option overrides `diff.renames` from any config level. It also turns
  off copy detection, which is a stronger form of rename detection, so `diff.renames=copies` cannot bring the hiding
  back. The deleted side of a rename (`src/app.py`) is listed. `is_deploy_record` (:133-142) classifies it as code.
  `shipped_unchanged` (:341-360) returns False for it because `target.is_file()` is false for a deleted file, so it
  cannot be exempted as unchanged DevFlow tooling either.
- **Every path, probed** in a scratch repository against the exact fixed command plus the gate's
  `ls-files --others --exclude-standard`:
  - committed rename (`git mv` + commit): both paths listed;
  - staged rename (`git mv`, not committed): both listed;
  - unstaged plain `mv src/app.py docs/app.md`: `src/app.py` listed by the diff, `docs/app.md` by `ls-files`;
  - plain `mv` plus `git add -N docs/app.md` (intent-to-add): with renames on, ONLY `docs/app.md` is listed (the
    #506 hiding, on a third path); with `--no-renames`, both are listed (see R1);
  - `git mv` followed by `git rm --cached docs/app.md`: both listed;
  - a copy into `docs/` with the source edited or deleted, under `diff.renames=copies`: both sides listed.
- **Other clone-local config that could change the listing**, each set in the clone's `.git/config` and tested
  against the fixed command: `diff.renames` (`true`, `copies`), `diff.relative=true`, `color.diff=always`,
  `color.ui=always`, `diff.noprefix`, `diff.mnemonicPrefix`, `diff.orderFile`, `core.quotePath=false`, and
  `diff.ignoreSubmodules=all` with `src/app.py` replaced by a gitlink. None removed `src/app.py` from the output or
  added escape codes to it. The config classes already filed (#505: fsmonitor, stat data, attribute filters,
  `info/exclude`) were not re-tested.
- **Fail direction unchanged.** A git error still raises `CalledProcessError` (`check=True`), which becomes None at
  :204-205, and the caller refuses. A quoted path (non-ASCII, or a control character) begins with `"`, so it is not a
  record and counts as code. That direction is closed and is not changed by this commit.
- **Mutation check.** Two mutants: the byte-for-byte revert of scripts/deploy_gate.py to `aab6906`, and removing only
  `"--no-renames"`. With each, all three cases in tests/unit/test_deploy_gate_506.py fail (:17-27 committed and
  uncommitted, :30-39 `diff.renames=copies`). Afterwards I restored the file byte for byte from a copy and checked
  that `git status` was clean. The assertion `"src/app.py" in out` (:27, :39) ties each test to the hidden path, not
  only to the exit code. Test 1 also asserts the control: the unchanged tree passes first (:20).
- **Related diffs elsewhere use rename-safe forms.** `commit_gate.py:122`, `review_need.py:103` (`PLAIN_DIFF`) and
  :226, `.githooks/post-rewrite:42` and `wave_check.py:697` all pass `--no-renames`. `wave_check.py:610` uses `-M`
  but keeps both sides of a rename. `wave_check.py:533` (`--diff-filter=A`) can only make a check apply, never skip
  one. `closure_check.py:70,86-90` imports `changed_since`, so it gets the fix too.
- **Commit hygiene.** Red test first and alone (`aab6906`), then the fix. Both commits carry the owner's identity and
  the `GP-Agent:` / `GP-Task: issue-506` trailers. No AI attribution. The process-log entry is in English.

## Gates passed
- [x] Secret scan green (`make secrets` on 0e5ac5d, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green (run by me: "No known vulnerabilities found")
- [x] `make slopsquat` green (run by me: "slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no dependency file or new import in the range)
- [x] `conformance` green (`make conformance`, run by me: "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)")
- [x] Default-deny preserved for new external surfaces (no new surface)
- [x] Permission-matrix not violated (no protected-path edit; no destructive command in either commit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief's `Paths that make a change HIGH:` is `none`, so no senior-review line is owed)
- [x] SAST (`ruff check` on both files with the project's `S` (flake8-bandit) rules selected, pyproject.toml:75: "All checks passed!"; `bandit` itself is not installed in the venv)

Also run: `pytest tests/unit/test_deploy_gate_506.py tests/unit/test_deploy_gate*.py` at 0e5ac5d: 157 passed. The
global coverage floor message is expected for a subset run.

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #506 "both sides of a rename are listed" → scripts/deploy_gate.py:199; tests/unit/test_deploy_gate_506.py:17-27 (committed and staged `git mv src/app.py docs/app.md`, exit != 0, `src/app.py` named)
- #506 / D-231 clause 1 "a `diff.renames` setting the change can write does not hide it" → scripts/deploy_gate.py:199; tests/unit/test_deploy_gate_506.py:30-39
- D-231 clause 1 "only to tighten" → scripts/deploy_gate.py:197-205 (one flag added to the diff; nothing removed from the list, no exemption added)

## Risks queued
- **R1** tests/unit/test_deploy_gate_506.py:17 — the `uncommitted` case is a STAGED rename (`git mv` stages it).
  A third path shows the same hiding with renames on: a plain `mv src/app.py docs/app.md` followed by
  `git add -N docs/app.md` (intent-to-add) lists only `docs/app.md` (probed). The fix covers it, because the same
  flag at scripts/deploy_gate.py:199 lists both paths, and dropping that flag already fails the existing tests. So
  this is only a missing regression pin. A test-only follow-up would add an `intent-to-add` case to the parametrize.
  Not blocking: no code path is open.
