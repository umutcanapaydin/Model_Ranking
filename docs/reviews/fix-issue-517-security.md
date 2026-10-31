---
record_type: review
id: fix-issue-517-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-31
---
# Security Review — fix-issue-517

**Reviewer:** Security-Reviewer subagent (light mode; a deploy-gate control change under D-232 clause 1, the owner's ruling of 2026-10-31: tightening only)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-31
**Release range:** 290557c..bf3f0af (`01c0d53` D-232, `8545e53` red test alone, `bf3f0af` fix)
**Reviewed head:** 9ca56c4d9ba05444e8df2c409d09cad8a3e079e5
**Risk tier:** HIGH (the deploy gate's base-pinned policy; the brief's `Paths that make a change HIGH:` is `none`, and
the tier comes from the control class)

## Verdict
MINOR

Round 2 (9ca56c4): MINOR. M2 and R2 are fixed and held by tests. M1 is open as #533 (the owner's guard), R3 is filed as #534,
and R1 is refused as advisory. Round 1's text follows unchanged; round 2 is at the end.

Round 1 (bf3f0af): MINOR. The fix does what D-232 clause 1 says and only tightens. `Deploy commands:` and `Working mode:` are read at the
merge-base and at the default branch's tip, and the gate takes the union. The workflows are read at both. The issue's
probe is closed, and so is the case where the tip says heavy. Nothing that the old gate refused is now allowed: the tip
is always a descendant of the merge-base, and each consumer takes the union (declared commands, modes, workflow texts).
The fix has two limits, both pre-existing and neither a regression. First, the tip is only as fixed as the ref it comes
from, and the Bash guard still lets an agent move that ref two ways (M1). Second, the DevFlow pin is still read at the
merge-base alone, and the ADR's reason for that is wrong (M2). Both are gate bypasses that stay green with no test, so
both need an issue now (Escalate NOW class).

Worked in `/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/sec-517`
at `bf3f0af` (detached) and `.../scratchpad/sec-522` at `d29e91d`. Each has its own venv from `make install` and its
own copy of `advisor.db` (D-174). The probes ran in pytest `tmp_path` repositories (`scratchpad/sec522probe/`), never
on the shared refs. Both trees were left clean.

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/brief_fields.py:334-339; .claude/hooks/bash_guard.py:3036-3095 (`_moves_default`): the tip comes
  from the same ref as the merge-base, so an agent that can move that ref reopens #517 in full. Both reads then land
  on the old commit, and the union is one commit. The guard blocks `update-ref`, `symbolic-ref`, `set-head`,
  `branch -f/main`, `remote.origin.fetch` and a refspec onto a default ref. I fed the guard JSON payloads, and it
  ALLOWS these two chains:
  1. `git -c remote.evil.fetch=+refs/heads/stale:refs/remotes/origin/main fetch evil`, after `git remote add evil
     <any repo, even this one>`, or `git config remote.evil.fetch '+refs/heads/*:refs/remotes/origin/*'` followed by
     `git fetch evil`. This rewrites `origin/main`.
  2. `git branch -rd origin/HEAD origin/main`, then `git branch -D main`, then `git worktree add -b main <dir>
     <old sha>`. This recreates the last default branch the gate falls back to.
  Evidence: on the `_history` fixture of `tests/unit/test_deploy_gate_517.py`, with a branch cut from the commit before
  the declaration, `deploy_gate.py "fly deploy"` exits 2 untouched and exits **0** after either chain. The deletions and
  the `-b main` would be visible in the session. The fetch is one ordinary-looking command. It is MINOR here because
  it is in the guard, not in this diff, it bypassed the merge-base equally before #517, and `.claude/` is the owner's to
  change. **Remedy (a new issue, guard-side):** refuse a fetch refspec from ANY remote's config whose destination is a
  default ref (`remote.<any>.fetch` set by `-c`, `git config` or `GIT_CONFIG_*`, as `remote.origin.fetch` already is).
  Refuse `git worktree add -b/-B` naming a protected branch. Refuse `git branch -d -r` of `origin/HEAD` and
  `origin/main`, or make the gate refuse when a remote-tracking default ref is missing but a local `main` is present.
- **M2** scripts/deploy_gate.py:396-410 (`devflow_pin` reads `protected_base`, the merge-base only); docs/decisions.md:6375-6376
  (D-232 clause 1: "an older pin there exempts less, never more"). The claim is false. An older pin does not exempt
  less. It exempts *other* bytes, the older DevFlow's. Suppose a branch is cut from a main commit before an upgrade, and
  it carries the reviewed tree with one non-safety tooling file put back to the older pin's bytes. That file is then
  "DevFlow's, unchanged", so the deploy goes ahead with no delta review. The rest of #517's class, a policy input read
  at a commit the change chooses, stays open for the pin.
  Evidence (`_installed`, then v9.10 upgrades `scripts/tool.py`, pins it, and the verdicts are written at that head):
  ```
  PROBE control (branch from the tip, tool.py back to v9.9 bytes): 1
  PROBE diff vs reviewed: ['scripts/tool.py']
  PROBE branch cut before the upgrade: 0 ['deploy-check: security: ... PASS at 248d992, no code changed since ...']
  ```
  It is MINOR because it is pre-existing, the safety surface is never exempt, and only DevFlow's own earlier bytes
  qualify. **Remedy:** exempt a file only when it equals the pinned bytes at BOTH bases (the intersection), so a pin at
  the tip and a pin at the merge-base must agree. Correct the ADR sentence in a superseding entry. One test: the probe
  above, expecting exit 1.

### PASS
- `protected_bases` (scripts/brief_fields.py:330-340) takes the tip from the same ref as the merge-base. It resolves it
  with `--verify --quiet --end-of-options <ref>^{commit}` and adds it only when it differs, so a branch cut from the
  tip costs nothing extra. The tip is always an ancestor-or-equal descendant of the merge-base, so the union can only
  add declarations, modes and workflows.
- `_policy` (scripts/deploy_gate.py:165-184) fails closed as a whole. If either base's brief is `Unverified` or
  unreadable, the policy is None, so every declared deploy is refused and `--check` fails. In a normal session the tip
  commit is fetched with its objects, so I found no new refuse-all case. Shallow clones fail the merge-base first, as
  before. In this repository `origin/HEAD` -> `origin/main` = `main` = `290557c`.
- Heavy-mode tip: `verdicts` (:630, :656-663) owes a Tester verdict for each mode in the union, and lets the milestone
  security verdict stand only when no base and not the tree says light. `test_the_tips_mode_is_read_too` holds it.
- `declared` (:657-667) adds each base's commands to the tree's. `_workflow_texts` (:875-890) reads both bases, and a
  base workflow git cannot verify still makes the read incomplete (fail closed). With no default branch the loop is
  empty and `complete` stays True, as before the change.
- Performance: one extra verified blob read and one extra pair of folder reads, only when the tip differs.
  `deploy_gate.py --check` on the real tree took 2.7 s in total.
- Callers: `closure_check.py` reaches the base only through `deploy_gate.changed_since`, which inherits M2 and nothing
  else. `review_need.py:223` reads the brief at the range's base, a commit chosen by the caller. That is the same
  class, but it is advisory routing behind the deploy gate (R1). `policy_root` (:187-191) now has no caller in
  `scripts/`.
- Commit order: `01c0d53` ADR, `8545e53` red test alone (2 files: the ADR and the test), `bf3f0af` fix. Both tests
  pass at bf3f0af, and the 212 tests in `tests/unit/test_deploy_gate*.py` pass at d29e91d.

## Gates passed
- [x] Secret scan green (`make secrets` at d29e91d, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no new import)
- [x] Default-deny preserved for new external surfaces (no new surface; the change only adds refusals)
- [x] Permission-matrix not violated (no protected-path edit; no `.claude/`, `.githooks/` or workflow file touched)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path)
- [x] SAST (bandit is not in the lock; I read the diff by hand: no new subprocess, shell, eval or deserialisation; the
  one new git call has a fixed argv with `--end-of-options`). Conformance at d29e91d, run by me: "conformance PASS: 33
  test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #517: a branch cut before `Deploy commands:` was declared still has its deploy guarded → scripts/brief_fields.py:330-340,
  scripts/deploy_gate.py:171-179, :662-663; tests/unit/test_deploy_gate_517.py:42-53
- D-232 clause 1: the tip's `Working mode:` is read too → scripts/deploy_gate.py:630, :656-663;
  tests/unit/test_deploy_gate_517.py:56-63
- D-232 clause 1: the base workflows are read at both → scripts/deploy_gate.py:875-890 (no test of its own: a dispatched
  workflow that exists only at the tip, R2)
- Every path closed → NOT where the ref itself can be moved (M1), and not for the pin (M2)

## Risks queued
- **R1** scripts/review_need.py:221-227: the HIGH paths and the mode are read at `range_base(rng)`, a commit chosen by
  the caller. A range that starts at an older commit reads an older HIGH-path list. This is advisory (the deploy gate
  still requires the release verdicts); queue it with M1's issue.
- **R2** tests/unit/test_deploy_gate_517.py: there is no test for the tip's workflow copies (a deploy workflow, or a
  `run:` line of a declared command, present only at the tip). I ran the mutant `bases = protected_bases(root)[:1]` at :875 (the merge-base alone): it
  survives all 203 tests in `tests/unit/test_deploy_gate*.py` at bf3f0af.
- **R3** scripts/brief_fields.py:334: the first ref that has a merge-base wins. If `origin/HEAD` names a stale branch
  (for example after a default-branch rename), `origin/main`'s tip is never read. A union over every existing
  DEFAULT_BRANCHES tip would hold. This is pre-existing and not reachable in this repository today.

## Round 2 — re-verification at 9ca56c4 (fix diff bf3f0af..9ca56c4)

**Reviewed head:** 9ca56c4d9ba05444e8df2c409d09cad8a3e079e5 (the code is identical in `scripts/deploy_gate.py`'s pin
and base paths at 6d2e10d, where I re-ran everything; `git diff 9ca56c4 6d2e10d -- scripts/deploy_gate.py` touches
only #522's lines 515-578)

Round-2 verdict: MINOR. M2 and R2 are fixed and held by tests. M1 stays open: the defect is in the guard, which
is the owner's to change, and it is filed as #533. R3 is filed as #534, and the dispatcher refused R1 as advisory
(as I rated it). Nothing in this round loosens the gate.

- **M2 — fixed.** scripts/deploy_gate.py:402-413 (`devflow_pins`) reads the pin at every protected base, and is None
  (nothing exempt) when any base has no pin or an unreadable one. :433-437 (`shipped_unchanged`) exempts a file only
  when every pin holds its bytes. The pin list cannot be empty, because a non-empty `bases` and `all(found)` give one
  pin per base, so `all(...)` is never vacuous. My round-1 probe now refuses (`branch cut before the upgrade: 1 ...
  1 code file(s) changed since`), and the control still refuses (1). Mutant `for pinned in pins[:1]` (the merge-base
  pin alone) is KILLED by `tests/unit/test_deploy_gate_517.py::test_a_branch_cut_before_an_upgrade_cannot_restore_the_older_pins_bytes`.
  D-233 (docs/decisions.md, `c013b53`) supersedes the false sentence and marks D-232 accordingly. One stale comment
  remains: scripts/deploy_gate.py:396-397 still says the pin is "Read at the protected base only". That is cosmetic.
- **R2 — fixed.** `::test_a_deploy_workflow_only_the_tip_holds_is_still_one`. Mutant `bases = protected_bases(root)[:1]`
  at :905 (`_workflow_texts`) is KILLED (1 failed, 3 passed).
- **M1 — open, filed as #533** (the Bash guard's ref moves; `.claude/` is the owner's). Unchanged by this round.
- **R1** refused as advisory by the dispatcher; **R3** filed as #534.
- The merge also carries #535 (`scripts/client_decl_gate.py`, one allowlisted `Date.<=`), which was reviewed
  separately. It is no security surface for this verdict.
- Tests: all 223 tests in `tests/unit/test_deploy_gate*.py` pass at 6d2e10d. Gates at 6d2e10d, run by me: `make secrets` "no leaks found"; `make deps` "No known vulnerabilities found"; `make slopsquat` "slopsquat PASS: 20 declared dependency(ies), 0 suspect"; conformance "conformance PASS: 33 test(s) derived from conformance/, 0 failing, 0 caller-liveness finding(s)".

Round-2 acceptance criteria evidence:
- #517 M2 (D-233): a file is DevFlow's only when both pins hold its bytes → scripts/deploy_gate.py:402-413, :433-437;
  tests/unit/test_deploy_gate_517.py:67-86
- #517 R2: the tip's workflow copies are read → scripts/deploy_gate.py:905-907; tests/unit/test_deploy_gate_517.py:89-101
