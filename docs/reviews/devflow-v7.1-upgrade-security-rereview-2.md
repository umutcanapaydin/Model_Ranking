---
record_type: review
id: devflow-v7.1-upgrade-security-rereview-2
status: draft
process_version: v7.1
date: 2026-10-16
seat: independent
---
# Security Re-review 2 -- DevFlow v7.1 upgrade, round 3 delta (draft PR #281)

**Reviewer:** Security-Reviewer subagent. This is the same seat as `devflow-v7.1-upgrade-security.md` and
`-rereview.md`.
**Independent:** yes
**Date:** 2026-10-16
**Release range:** b4dc1f3..b39bbe8
**Reviewed head:** b39bbe89e84adddef563cb609d05bf8d15738bb3
**Risk tier:** MEDIUM. The delta changes the Bash guard, its pin and its tests.

**Seat:** the seat is the independent Security-Reviewer, from the Claude model family (Opus). It wrote none of
the fix. Policy came from `main`.

**Method:**
- **Worktrees.** A fresh detached worktree at `b39bbe8` with its own venv. `advisor.db` was copied read-only,
  and its md5 `495755d5…` was unchanged. Worktrees at `b4dc1f3` and `7bdb7c5` gave the differential.
- **Differential.** 157 payloads went through each tree's whole PreToolUse hook: the 131 from earlier rounds
  and 26 new ones. Each hook ran with its own pin, and commands were judged, never run.
- **Mutants.** 3 guard mutants ran in a `git archive` export and were re-pinned, so the behavioural tests
  decided each one. Every file was restored, and its md5 checked.
- **Gates.** `make check`, then `make secrets`, `make deps` and `make slopsquat`.

The worktrees and the export were removed afterwards. This file is the only write in the author's tree.

## Answers

1. **B1-R is closed.** `bash_guard.py:735-748` now marks each assignment before a program word as `UNKNOWN`.
   All six round-2 repros exit 2: `HOME=$(mktemp -d) true && rm -rf "$HOME"`, the `TMPDIR` form, the `PWD`
   form and the rest. Spellings the fix invites also behave correctly:
   - Refused: `env HOME=$(mktemp -d) true && rm -rf "$HOME"` and `X=1 if true; then rm -rf $HOME; fi`.
   - Rightly allowed, because the shell really sets the variable in each case:
     - `export HOME=$(mktemp -d) && rm -rf "$HOME"`;
     - the `declare` and `readonly` forms;
     - a bare `HOME=$(mktemp -d); rm -rf "$HOME"`;
     - `(X=$(mktemp -d); rm -rf $X)`.
   - Mutants: putting `_assign` back on the prefix fails 6 tests, and dropping the bare-line `_assign` fails 7.
     Both are killed.

   **But the same class remains**, outside the prefix case. See B1-S.
2. **R3's test holds.** `test_rm_rf_of_scratch_too_large_to_walk_is_refused` (`tests/unit/test_bash_guard_bounds.py:394-404`)
   first allows the directory with the full budget, then refuses it with `MAX_WALK = 2`. Mutant N8
   (`except _Unwalked: return False`) now fails it.
3. **Nothing held at `b4dc1f3` is weaker.** Over the 131 earlier payloads, `b39bbe8` differs from `b4dc1f3` only
   by refusing more: the six B1-R calls. One row moved only because the harness ran from a different
   directory (`mv ../sec`).
4. **The pin is right.** The sha256 `8788704f5cefc5326cad1f631e08ab29b8b3a05ac3e25c7dedf04ec97914c6a9` is the
   value in both PreToolUse hooks, and no `fda573c6` remains. Both hooks exit 2 with no python, with the guard
   missing, and on a payload that is not JSON. All four hooks keep `onFailure: block`.
5. **Gates (my worktree):**
   - `make check`: exit 0. The legs:
     - session-check PASS;
     - ruff clean;
     - mypy: 49 files, no issues;
     - pytest: 3132 passed, 27 skipped, coverage 92.19%;
     - coverage-floor PASS;
     - check_records PASS, self-test 0;
     - install-check PASS;
     - shell-dialect PASS;
     - wave-check-all PASS;
     - conformance: 26 PASS;
     - swift-test: 637, plus SlowTier 7 of 7;
     - client-decls PASS.
   - `make secrets`: exit 0, 1207 files, no leaks. Gitleaks over `b4dc1f3..b39bbe8`: no leaks.
   - `make deps`: exit 0, no known vulnerabilities.
   - `make slopsquat`: exit 0, 20 declared, 0 suspect.

## Findings

### BLOCKING

- **B1-S** `.claude/hooks/bash_guard.py:689-703` (`_assign`), `:735-748` and `:1281-1284`.
  - **The defect.** `SCOPE` is one flat map, filled in reading order. The guard therefore keeps values that
    the shell discards, and misses writes that the shell makes. A subshell, a function body, a pipeline
    element and a loop each have their own scope in the shell, and `read`, `printf -v` and `for` write a
    variable the guard never sees.
  - **Measured.** `main` exits 2 on each call below. `b4dc1f3` and `b39bbe8` both exit 0. These are not
    regressions from round 2, only still open:
    - `(export HOME=$(mktemp -d); make test); rm -rf "$HOME"`. In the shell this is `rm -rf ~`;
    - `(HOME=$(mktemp -d)); rm -rf "$HOME"`;
    - `f() { HOME=$(mktemp -d); }; rm -rf "$HOME"`. The function never runs;
    - `d=/Users/…/Desktop; f() { local d=$(mktemp -d); }; f; rm -rf "$d"`;
    - `d=/Users/…/Desktop; (d=$(mktemp -d)); rm -rf "$d"`;
    - `d=/Users/x; d=$(mktemp -d) | cat; rm -rf "$d"`;
    - `d=$(mktemp -d); for d in /Users/…/Desktop; do :; done; rm -rf "$d"`;
    - `d=$(mktemp -d); read d < /tmp/list; rm -rf "$d"`;
    - `d=$(mktemp -d); printf -v d /Users/…; rm -rf "$d"`.
  - **Failure scenario.** The first call is the round-2 idiom, a throwaway HOME followed by cleanup, written
    with a subshell. It is as plausible as the prefix form, and it deletes the owner's home directory.
  - **Remedy, one change that ends the class.** Trust a variable's recorded value or `SCRATCH` only when the
    whole text is linear. The guard already decides that with `_linear` (`:987`): simple commands joined by
    `;`, `&&`, `||` and newlines, with no subshell, group, function, loop or pipe. In any other text, every
    variable is `UNKNOWN` to `_scratch`. Also mark as `UNKNOWN` each name that `read`, `printf -v`,
    `mapfile`/`readarray` or `getopts` writes. Add the nine calls above as refusals.
  - **The loop rule.** This is the third BLOCKING verdict on finding B1 (B1, then B1-R, then B1-S).
    `main:.claude/skills/close-wave/SKILL.md` step 3 says the loop ends here. The class should be filed as a
    `bug` and the change closed on the rest, or the structural remedy above applied once. Which of the two is
    the owner's call. I have not lowered the severity to fit the rule. Deleting `~` through a guard the owner
    relies on in auto mode is BLOCKING at any round.

### MINOR / NIT

None is new. R1 is #286, R2 is documented, and N2-N4 are unchanged from round 2.

**Verdict: BLOCKING** -- B1-R closed; R3 closed. 1 BLOCKING (B1-S, the third on B1, so the owner rules
between filing it under the loop rule and one structural fix), 0 MAJOR, 0 new MINOR, 0 new NIT.

## Dispositions

By the author, after the verdict.

| Finding | Disposition | Where |
|---|---|---|
| B1-S | **Filed** #287 (`bug`, `severity:medium`), `work-issue`. This is the third BLOCKING on B1, so the loop ends (`/close-wave` step 3). It is not a regression: `main`'s guard allows the same spellings. The owner's plan of 2026-10-16 carries it into the follow-up guard PR with v7.1.1's guard fixes, after #281 merges | #287 |

After this verdict, `ab8686f` took DevFlow v7.1.1's two conformance fixes (test-bash-guard and test-hook-claims set TMPDIR for their scratch cases). The change is test-only, and no guard or gate code changed.
