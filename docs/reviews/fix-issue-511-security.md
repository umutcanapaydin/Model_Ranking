---
record_type: review
id: fix-issue-511-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — fix-issue-511

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` routed the branch to `security` for a policy edit: `scripts/deploy_gate.py`, #283)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this branch before.
**Date:** 2026-10-30
**Release range:** 2d29b9c..53c49e9 (`d59244d` red test, alone; `53c49e9` fix)
**Reviewed head:** 53c49e919bd48de68a636e7a753210ddac8cc488
**Risk tier:** HIGH (a deploy-gate control change; tightening only, pre-approved by D-231 clause 1)

## Verdict
PASS

#511 asks for one verified object reader in place of two, with no change in what is refused. The branch delivers that.
`_object`, which ran `git cat-file <kind>` once per object, hashed SHA-1 only and read fixed 20-byte entries, is gone.
`verified_blob` now reads through the same `_batch_read` that `_unhashed` (#493) uses, and parses each tree with the one
`_entries`. It keeps #494 R2's strictness at the pin: the last entry must be `100644` or `100755`, and a directory on
the way must be the bytes `40000`. It gains SHA-256 support, and `--no-replace-objects` on the read, which
`GIT_NO_REPLACE_OBJECTS=1` at import already implied. Nothing is loosened.

Worked in my own worktree, `scratchpad/sec-511`, at `53c49e9` (detached), with its own venv from `make install` and
`advisor.db` copied in (D-174). Every mutant was restored byte for byte, and `git status` stayed clean.

## Findings

### BLOCKING
- none

### MINOR
- none

### PASS
- **The red test is red, and alone.** `d59244d` adds only tests/unit/test_deploy_gate_511.py. With
  scripts/deploy_gate.py from `2d29b9c`, 2 of its 3 tests fail (:24 and :37). The third (:44) is the strictness
  control, and it passes before and after, as intended.
- **`_unhashed`'s behaviour is unchanged.** The only edits are `_open_batch` and `_close_batch`, which carry the same
  argv and the same teardown (scripts/deploy_gate.py:238-248, :278, :300), and `_subtrees`, now built on `_entries`.
  `_subtrees` still recurses by the type bits (`int(mode, 8) & 0o170000 == 0o040000`, :261-264), which keeps #493's
  M2. All 269 tests selected by `-k "deploy_gate or closure or review_need"` pass at 53c49e9.
- **`verified_blob` is as strict, or stricter** (scripts/deploy_gate.py:435-466):
  - The commit is read as a `commit` and hashed, with no peeling: a tag or tree id is refused.
  - Each tree is hashed, and the blob is hashed.
  - `ValueError` from a malformed header or tree and `OSError` both return None (fail closed).
  - The batch child is killed in `finally`.

  Mutants on the 269-test selection (the first two were also run on the full `tests/unit`):
  - KILLED: a link (`120000`) accepted as the pin's file (A1, by the #494 test); the blob hash switched off in
    `_batch_read` (A3); tree read errors skipped in `verified_blob` (A4); the blob read without `_batch_read` (A6).
  - SURVIVED: any directory spelling on the way at the pin (A2), and the commit's `tree` regex narrowed back to 40 hex
    (A5). Both mutants fail in the closed direction or are not exploitable (R1, R2), so neither is a defect.
- No new import, no secret, no destructive operation, and no `.github/`, `.claude/` or `.githooks/` edit. Both
  commits carry `GP-Agent:` and `GP-Task: issue-511` and no AI attribution.

## Gates passed
- [x] Secret scan green (`make secrets`, run by me at d7780fc, which contains this range: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief's
  `Paths that make a change HIGH:` is `none`)
- [x] SAST: `ruff check --select S scripts/deploy_gate.py` reports one S101 at :224, the pre-existing `assert` in
  `_batch_read` that #493's review accepted. `make conformance` at d7780fc: "conformance PASS: 33 test(s) derived from
  conformance/, 0 failing"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #511, one verified reader: `verified_blob` reads through `_batch_read` → scripts/deploy_gate.py:444, :450, :461;
  tests/unit/test_deploy_gate_511.py:24
- #511, one tree parser: `_entries`, used by `_subtrees` and `verified_blob` → scripts/deploy_gate.py:251-264, :453;
  tests/unit/test_deploy_gate_511.py:37
- #511, the existing tests stay green and their mutants stay killed → 269 passed; the link mutant is KILLED;
  tests/unit/test_deploy_gate_511.py:44 (the strictness control)

## Risks queued
- **R1** scripts/deploy_gate.py:445 and :453 — SHA-256 support (`{40,64}` and `len(oid) // 2`) is new in
  `verified_blob`, and no test reaches it. Mutant A5 survives. The mutant's direction is closed: in a SHA-256 repository
  nothing would be exempt. #509 moves this code, and I probed it there by hand on a `--object-format=sha256` fixture,
  where it works. Remedy: one SHA-256 fixture test of `verified_blob` (or of #509's `verified_file`).
- **R2** scripts/deploy_gate.py:458 — the rule that a directory on the way must be the bytes `40000` has no test.
  Mutant A2 survives. Loosening it would read the pin's file through a zero-padded `040000` tree that still hashes.
  The content would still be verified, so it is not exploitable, but the strictness the docstring claims is unproven.
  Remedy: a fixture whose pinned commit spells the directory `040000` (`hash-object --literally`), expecting None.
