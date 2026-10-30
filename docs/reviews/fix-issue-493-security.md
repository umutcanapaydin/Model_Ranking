---
record_type: review
id: fix-issue-493-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-29
---
# Security Review — fix-issue-493

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` routed the branch to `security` for a policy edit: `scripts/deploy_gate.py`, #283)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-29
**Release range:** a2650e0..5848127 (`6846467` red tests, `844b898` fix, `5848127` round-2 fix)
**Reviewed head:** 5848127330951750861b8008ca5cd7e10c38e610
**Risk tier:** HIGH (a deploy-gate control change; tightening only, by the owner's direction of 2026-10-29 on #493 and #500)

## Verdict
MINOR

Round 2 (5848127): B1 is fixed and held by a test, and M2, M3 and R3 are closed. M1's code is right but no test holds
it (round 2's M4). R1 is now #505 and R2 is #506, both escalated to the owner. Round 1's text follows unchanged; round 2 is
at the end.

Round 1 (844b898): BLOCKING. The branch only tightens: every new path in `current()` is an added refusal, the index-flag check does what #500 asks,
and a forged tree at any depth under the reviewed commit is now refused. But the owner's direction for #493 names "the
reviewed head's commit and every tree under it", and the commit check fails OPEN: a forged reviewed-head COMMIT
object still makes `--check` print PASS (B1). It is the same attack as #493, one object up, with the same reach. The fix
is a one-line change (below). The other findings are MINOR or pre-existing and queued.

Worked in `/private/tmp/claude-501/-Users-umutcanapaydin-Desktop-ILGAR-model-ranking/cbf5c80e-9000-4990-acff-ddcfbf8972cf/scratchpad/sec493`
at `844b898` (detached), with my own venv `venv-sec493` installed from `requirements/dev.lock` with `--require-hashes`
(D-174). I read the policy from `origin/main` (`a2650e0`). Probes lived in `scratchpad/probe493/`, outside the tree.
Every temporary change to `scripts/deploy_gate.py` (old gate, mutants, candidate remedy) was restored by copy, and
`git status` stayed clean.

## Findings

### BLOCKING
- **B1** scripts/deploy_gate.py:252-260 — `_unhashed` resolves the head with `rev-parse --verify --quiet <head>^{commit}`.
  When the reviewed head's commit object is forged, git's own hash check makes that call fail. `_unhashed` reads the
  empty answer as "a head this clone does not have" (:259-260) and returns None. But `changed_since`'s
  `git diff --name-only <head>` (:195) does NOT hash the commit, so it runs on the forged commit's tree. A safety-class
  control fails OPEN here (AGENTS.md section 5), and the #493 criterion ("the reviewed head's commit and every tree
  under it are hash-checked", the owner's direction) is not met for the commit. OWASP A08 (software and data integrity
  failures). It is BLOCKING because it is exploitable now, with exactly the reach #493 assumes (write one object under
  `.git/objects`), and no test holds it.
  Evidence (the `_installed` fixture; change `src/app.py` and commit, then rewrite the reviewed head's loose commit
  object so its `tree` line names HEAD's tree):
  ```
  rev-parse 128 '' 'error: hash mismatch 56ecaddb5df3445bbd0fdc619eeaac64407c66b6\nfatal: Needed a single revision\n'
  diff 0 '' ''
  gate exit 0 ['deploy-check: security: docs/reviews/release-security.md PASS at 56ecadd, no code changed since (working tree included)']
  ```
  The same branch also lets a verdict whose `**Reviewed head:**` is a TREE id skip the check, because `git diff`
  accepts a tree-ish. The probe swapped the reviewed commit's root tree id into both verdicts and forged its `src`
  subtree: `--check` exit 0. Writing the verdict is an edit anyone can see, so this variant adds little reach of its
  own, but it is the same fail-open line. The old gate (a2650e0) passes the forged commit too, so this is not a
  regression. It is a gap in the fix of the issue it claims to close.
  **Remedy:** resolve the head without peeling, so that `_batch_read(..., "commit")` hashes it and checks its type.
  Change :253 to `"--end-of-options", head]`. I tried this on a copy: the forged commit is refused
  (`the comparison with cd080f3 cannot be trusted`), the tree-id head is refused, and all 135 tests in
  `tests/unit/test_deploy_gate*.py` pass. Add the forged-commit case to `tests/unit/test_deploy_gate_493.py`. It also
  kills mutant E (M3).

### MINOR
- **M1** scripts/closure_check.py:86-90 (comment :67-69, docstring :89) — `code_changed_since` calls
  `deploy_gate.changed_since` without `compare_problem`. A light-mode closure check now passes a tree that the deploy
  gate refuses, which contradicts its own claim that "the two never disagree about one verdict". It is MINOR because
  the deploy gate still runs at every deploy and `make deploy-check` asks the same question. Remedy: put the check
  inside `changed_since` itself (return None, or raise, when `compare_problem` names one), so that every caller gets
  it from the one place the comment promises.
- **M2** scripts/deploy_gate.py:240 — `_subtrees` recurses only into an entry whose mode is the bytes `40000`. Git reads
  a mode by its octal value and type bits, so a zero-padded `040000` entry is a tree to `git diff` but not to the walk.
  Probe: the reviewed commit carries a root tree with `040000 src` (written with `hash-object --literally`, then
  committed). Its `src` subtree is then forged to name the agent's blob, and `--check` exits 0 while plain `git diff`
  lists nothing. It is MINOR because the malformed tree has to be in the commit the reviewer read. It does not show in a
  diff, but `git fsck` flags it (`zeroPaddedFilemode`). Remedy: recurse when `int(mode, 8) & 0o170000 == 0o040000`, or
  refuse any entry whose mode is not one of `100644`, `100755`, `120000`, `40000`, `160000` (fail closed).
- **M3** tests/unit/test_deploy_gate_493.py — four of nine mutants survive all 25 tests in `test_deploy_gate_493.py`,
  `_pin.py` and `_444.py`:
  - E: commit hashing off at :229 (`kind == "tree" and ...`). This is B1's case, and with B1 open that code cannot be
    reached anyway.
  - F: `_flagged` None turned into a pass at :288.
  - G: the walk stops below the root's children at :273.
  - H: an unstartable `git` turned into a pass at :257.

  The killed mutants are A (`S` dropped), B (lower-case dropped), C (no subtrees), D (no tree hash) and I (a tree read
  error skipped). So the forged-depth-1 test and both flag tests fail when their behaviour is removed, but the
  fail-closed branches (AGENTS.md section 3.5) and depth beyond 1 are unproven. Run by hand at depth 2 (`src/pkg/mod.py`),
  the code is right: refused. Remedy: add a forged commit (B1), a forged depth-2 tree, and a `git` that fails for
  `ls-files` (a fake `git` earlier on PATH).

### PASS
- **Replace refs: in scope, and covered.** `GIT_NO_REPLACE_OBJECTS=1` (scripts/deploy_gate.py:100) is set at import, so
  it applies to every git the gate starts. That includes `changed_since`'s `git diff`, which has no
  `--no-replace-objects` flag, and `closure_check.py`, which imports the module (:70). Probe: `git replace <reviewed
  head> HEAD` (plain `git show <head>:src/app.py` showed the replacement), then `--check` exited 1 with `src/app.py`
  listed.
- #500 as the owner chose it, option (a): `_flagged` (:207-216) reads `ls-files -v -z` and flags lower-case tags
  (assume-unchanged, including `s` for both bits) and `S`. It fails closed when git cannot list the index (:287-288).
  `-z` keeps names with newlines intact.
- The tree walk (:246-281) hashes every tree reachable from the root once (`seen`), for SHA-1 and SHA-256 alike
  (:228-229). It catches `ValueError` (which includes a header that does not decode) and `OSError` (fail closed), and
  kills its `cat-file` child in `finally`. A forged depth-2 tree is refused (probe). Cost on the real tree: 89 trees,
  `--check` in 0.2 s.
- **Sparse checkout: refused, and that is correct, not a false positive.** A sparse tree is not the reviewed tree, and
  a deploy from it ships less than was reviewed. Nothing in the project uses sparse checkout or index flags
  (`git grep`), and the main tree's index has no flagged entry and no `core.fsmonitor`, `core.checkStat`,
  `core.trustctime` or `filter.*` config. The real tree's `--check` is unchanged by the fix. Its hint is wrong there:
  see R3.
- `core.worktree` pointed at a clean copy is refused (probe, exit 1).
- The red commit is red: with `scripts/deploy_gate.py` from a2650e0, 3 of the 4 cases in `test_deploy_gate_493.py`
  fail (the control passes). At 844b898 all 25 deploy-gate tests in the three files pass.
- No new third-party import (`hashlib`, `subprocess` and `re` are stdlib). No secret, no destructive operation, and no
  `.github/`, `.claude/` or `.githooks/` edit. Both commits carry `GP-Agent:` and `GP-Task:` trailers and no AI
  attribution.

## Gates passed
- [x] Secret scan green (`make secrets` on 844b898, from the dispatcher: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat: PASS"; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief's
  `Paths that make a change HIGH:` is `none`)
- [x] SAST (`ruff check --select S` on both files: one S101 at scripts/deploy_gate.py:221, an `assert` used only for
  type narrowing. `Popen` with `PIPE` always sets both streams, and under `-O` the `AttributeError` would propagate and
  exit non-zero, which fails closed. bandit is not in the lock. Conformance from the dispatcher: "PASS: 33 test(s), 0
  failing")

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #493, a forged tree under the reviewed head is refused → scripts/deploy_gate.py:235-281, :439-442;
  tests/unit/test_deploy_gate_493.py:25 (depth 1 only, M3)
- #493, the reviewed head's commit is hash-checked (the owner's direction) → NOT MET: scripts/deploy_gate.py:252-260
  fails open (B1); no test
- #500, an assume-unchanged or skip-worktree entry is refused, fail closed → scripts/deploy_gate.py:207-216, :284-291;
  tests/unit/test_deploy_gate_493.py:47-56 (both flags); the fail-closed branch is untested (M3)
- Control, the reviewed tree still passes → tests/unit/test_deploy_gate_493.py:59

## Risks queued
- **R1** scripts/deploy_gate.py:190-204 (`changed_since`). These are pre-existing, in the same class as #500 (the
  working-tree side trusts git state the change can write), and outside the owner's chosen option (a). Each one passed
  `--check` with exit 0 on the fixture and a product change to `src/app.py` or a new `src/` file:
  1. A `core.fsmonitor` hook that reports nothing changed. `ls-files -v` shows `H`, `-f` shows `h`, and
     `-c core.fsmonitor=false` restores the diff.
  2. A same-size edit with its mtime restored, inside the second of the last index refresh. This needs no config at
     all on this machine's git 2.54. With `core.checkStat=minimal` and `core.trustctime=false` it works at any time.
     It is the practical form of "a forged index entry with matching stat info".
  3. A clean filter set through `.git/info/attributes` and `filter.<x>.clean`.
  4. A new untracked code file hidden by `.git/info/exclude` or `core.excludesFile`.
  5. A new untracked code file hidden by an untracked nested `.gitignore` that ignores itself (`src/pkg/.gitignore`
     holding `*`).

  The Bash guard judges some of these (`core.fsmonitor`, filters) when an agent types them, but a script that writes
  `.git/config` directly has the same reach as #493. Each is a gate bypass that stays green with no test: a separate
  issue, Escalate NOW (AGENTS.md section 3). Remedy: #500's option (b), which compares content without the index or
  git's config. Walk the tree, hash each regular file as a blob against the verified reviewed tree, and list untracked
  files against the protected base's ignore rules only. Interim: run every gate git with `-c core.fsmonitor=false
  -c core.untrackedCache=false`, and refuse when `filter.*`, `core.checkStat`, `core.trustctime`, `core.excludesFile`,
  or a non-empty `.git/info/attributes` or `.git/info/exclude` is present.
- **R2** scripts/deploy_gate.py:195 — `git diff --name-only` runs with git's default rename detection, so
  `git mv src/app.py docs/app.md` plus a commit prints only `docs/app.md`, which is a record. Deleting code passes
  (probe, exit 0). Pre-existing, so a separate issue, Escalate NOW. Remedy: `--no-renames`.
- **R3** scripts/deploy_gate.py:290-291 — in a sparse checkout the refusal is right, but the hint
  (`git update-index --no-skip-worktree`) is wrong advice there: `git sparse-checkout disable` is the fix. Wording
  only. No project path uses sparse checkout.
- **R4** scripts/deploy_gate.py:252-281 with :195 — `_unhashed` reads the objects in one process and `git diff` reads
  them again in another, so an object swapped between the two reads is not covered (time of check versus time of use).
  Low. Remedy, with R1: compare against trees the gate parsed itself.

## Round 2 — re-verification at 5848127 (fix diff 844b898..5848127)

Worked in my own worktree, `scratchpad/sec493r2`, at `5848127` (detached), with a fresh venv `venv-sec493r2` installed
from `requirements/dev.lock` with `--require-hashes` and `advisor.db` copied in. The policy is still read from
`origin/main` (`a2650e0`). Round 1's probes were re-run unchanged from `scratchpad/probe493/`. Every mutant was restored
by copy, and `git status` stayed clean.

**Verdict after round 2: MINOR.**

- **B1 — fixed.** scripts/deploy_gate.py:255-259 resolves the name with `rev-parse --verify --quiet
  --end-of-options <head>` (no peel), and `_batch_read(..., "commit")` (:267) hashes the commit and checks its type.
  Round 1's forged-commit probe is now refused (`the comparison with 85811d0 cannot be trusted`, exit 1). The tree-id
  head is refused both without and with a forged subtree (exit 1 both). Held by
  tests/unit/test_deploy_gate_493.py:78 (`test_a_forged_reviewed_commit_does_not_hide_a_change`). Mutants that bring
  back `^{commit}` and that switch off commit hashing (round 1's E) are both KILLED.
- **M1 — code fixed, untested (see M4).** scripts/deploy_gate.py:194-195: `changed_since` returns None when
  `compare_problem` names a problem. Checked by hand: `closure_check.code_changed_since` returns None with a
  skip-worktree entry and `['src/app.py']` once it is cleared. But the mutant that removes those two lines SURVIVES
  all 229 deploy-gate and closure tests: the gate refuses through `current()` anyway, and no test calls
  `changed_since` or `closure_check` with a flagged index or a forged object.
- **M2 — fixed.** scripts/deploy_gate.py:243 tests the type bits (`int(mode, 8) & 0o170000 == 0o040000`), which is how
  git's `canon_mode` reads a directory. A mode with non-octal digits raises `ValueError`, which `_unhashed` catches
  (fail closed). Gitlinks (`160000`) and links (`120000`) are not walked, as before. Round 1's zero-padded probe is
  refused (exit 1), and its control passes. Held by tests/unit/test_deploy_gate_493.py:110; the mutant with the old
  spelling is KILLED.
- **M3 — fixed.** Mutants F (`_flagged` None turned into a pass), G (one level) and H (an unstartable git turned into a
  pass) are KILLED, by tests/unit/test_deploy_gate_493.py:126, :100 and :126 respectively. Round 1's killed mutants
  A and B stay killed.
- **R3 — fixed.** scripts/deploy_gate.py:297-298 names `git sparse-checkout disable`. The sparse probe is still
  refused (correct).
- R1 is #505 and R2 is #506, escalated to the owner and out of this branch's scope. R4 is noted in the PR. Replace refs
  are still refused (probe, exit 1).
- Tests: all 229 tests selected by `-k "deploy_gate or closure"` in `tests/unit/` pass at 5848127. `make check-fast`
  in the worktree: "check-fast PASS in 334.4s" (every leg, records, test and swift-test included).

### MINOR (round 2)
- **M4** tests/unit/test_deploy_gate_493.py — M1's two lines (scripts/deploy_gate.py:194-195) have no citing test.
  Mutant: delete them, and 229 passed. Remedy: one test calling `deploy_gate.changed_since` (or
  `closure_check.code_changed_since` with that tree as cwd) on the `_installed` fixture with `--skip-worktree` set on
  a changed `src/app.py`, expecting None.

### Risks queued (round 2)
- **R5** scripts/deploy_gate.py:255-267 — a full 40-hex reviewed head that is absent from the clone (the squash-merge
  case) now stops at `compare_problem` with "the reviewed head's object <sha> cannot be read as a commit". The gate's
  explanatory message ("not in this clone's history -- a squash merge or a deleted branch dropped it ... record a head
  that is", :452-455) no longer appears for it. The behaviour still fails closed, so only the wording changes; an
  abbreviated head still gets the old message. Remedy: have `_batch_read` report `missing` as "not in this clone's
  history", or let `compare_problem` return None for a missing object and leave the refusal to `changed_since`.
