---
record_type: review
id: fix-issue-444-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-29
---
# Security Review — fix-issue-444

**Reviewer:** Security-Reviewer subagent (light mode, run night-1028; `review-need` routed the branch to `security` for a policy edit: `scripts/deploy_gate.py`, `scripts/review_need.py`)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-29
**Release range:** 8999ccf..fba96ba (`6e7bdb9` red tests, `fba96ba` fix and process-log entry)
**Reviewed head:** fba96ba886dcd6bbee4ad464dc1e9db7f123fe45
**Risk tier:** HIGH (a deploy-gate policy change, a control-change under D-229 clause 3: tightening only)

## Verdict
MINOR

No path is exempt that was exempt-free before: every new condition in `shipped_unchanged` is an added `return False`,
and the byte source changed only from `git cat-file -p <pin>:<rel>` to a hash-checked walk that returns the same bytes
on every tree shape the old call returned bytes for. Nothing is loosened. The derived surface and the hash walk are
narrower than the issue describes (M1-M3 below), and one pre-existing bypass of the same class as R2 is queued as R1
for escalation.

Worked in `/private/var/folders/qf/hmdttd7d5cb6nl3jt1myygqw0000gn/T/wt-sec-444` at `fba96ba`, own venv `.venv-sec`
(D-174) installed from `requirements/dev.lock` with `--require-hashes`. Probes lived outside the tree (scratchpad), and
every temporary mutation of `scripts/deploy_gate.py` was restored by copy (`git status` clean apart from this file).

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/deploy_gate.py:277,284 and :278 with :665-671 — `deploy_surface` derives its set by literal string
  match, so several forms of a declared deploy command add nothing to it, and the file they start stays exempt when
  an upgrade ships it byte-identical. Probed on the #444 fixture (`_upgrade_shipping` with the brief's
  `Deploy commands:` changed). Each of these PASSED `--check` with an upgrade that changed the started file:
  `./scripts/ship_it.sh` and `bash ./scripts/ship_it.sh` (the set holds `./scripts/ship_it.sh`, not the git path);
  `scripts/Ship_It.sh` (`declared()` lower-cases every word, so the set holds `scripts/ship_it.sh` and never matches
  a mixed-case git path); `gh workflow run release` and `gh workflow run "Release it"` (`deploy_workflows` keys on the
  dispatched word, a stem or a `name:`, and only `deploy_in` maps it back to a file through `_names`). An absolute
  path or `make <target>` (the Makefile is `DEVFLOW_TOOLING_FILES`) would miss the same way, and a brief with no
  `Deploy commands:` at either end yields an empty set, not None. Not a loosening: before #444 none of these were
  covered at all, and this repository's four declared commands are all in the literal form the code handles (on the
  real tree the set is `.github/workflows/nightly-hosted.yml`, `scripts/ci/nightly-hosted.yml`,
  `scripts/deploy_hosted_engine.sh`, `scripts/nightly_hosted.sh`). Minor because the fail direction is OPEN for a
  safety-class control (AGENTS.md section 5), latent only. Remedy: normalise each named word with
  `os.path.normpath` relative to `root` and compare case-preserving (keep the original words for this use), map
  every dispatched word through `_names` to its file, and treat a `make` program word as naming the `Makefile`.
- **M2** tests/unit/test_deploy_gate_444.py:84 — the R2 claim "the commit, every tree on the path and the blob" is
  held only for the blob. Mutant: `scripts/deploy_gate.py:298` changed to
  `if done.returncode != 0 or (kind == "blob" and named != oid):` (commit and tree hashes no longer checked);
  `test_deploy_gate_444.py` + `test_deploy_gate_pin.py`: 20 passed. The code itself is right: a probe that forges
  only the pinned commit's `scripts` tree (not shared with the reviewed head) to name a genuine blob holding the
  agent's bytes is refused by the fix (`scripts/tool.py` listed). Remedy: add that probe as a test.
- **M3** scripts/deploy_gate.py:260,278 — the fail-closed branch (a workflow at the protected base cannot be read, so
  `deploy_surface` is None and nothing is exempt) has no test. Mutant: `if surface is not None and rel in surface:`;
  the same 20 tests pass. AGENTS.md section 3.5 asks that an errored derived set fail closed; it does, unproven.
  Remedy: a test that makes `git show <base>:.github/workflows/x.yml` fail (for example a fake `git` earlier on PATH,
  or an unreadable object) and expects the changed upgrade file listed.

### PASS
- **Q1, no loosening.** `shipped_unchanged` (scripts/deploy_gate.py:252-263) keeps every old refusal (safety surface,
  not tooling, no pin, not a file) and adds three. `verified_blob` vs the old `cat-file -p <pin>:<rel>`: same bytes
  for a regular blob and for a 120000 entry (both return the link text); None for a gitlink at the leaf (`cat-file
  blob <commit>` fails), for a tree at the leaf, and for any non-tree intermediate; a tag id as the pin now yields
  None (the old call peeled it). `review_need.EXCEPTION_FILES` only gains an entry (scripts/review_need.py:92). The
  `==` -> `in` change in tests/unit/test_accepted_cuts.py:302 still pins `data/accepted-cuts.yaml`; the new entry is
  held by test_deploy_gate_444.py:111.
- **Q2, not steerable by the change.** `declared()` (scripts/deploy_gate.py:403-420) unions the base brief's commands
  with the tree's, and `_workflow_texts` (:604-634) unions the base's workflow files with the tree's, so the change
  can only add to the surface. With the base unreadable, `declared` falls back to the tree brief alone, but then
  `verdicts()` refuses every deploy (:372-374) and `devflow_pin` has no base either. The hand-kept `SAFETY_SURFACE`
  (:214-216) is still checked first.
- **Q3, tree parsing.** Entry layout `<mode> SP <name> NUL <20 raw bytes>` is read right: the first space after the
  entry start ends the mode (modes hold no space), so names with spaces parse; raw-hash bytes that happen to be 0x20
  or 0x00 are never scanned because the cursor jumps past them (:318-320). Mode 40000 for trees; a zero-padded
  `040000` (malformed, fsck-warned) and 160000 fail closed at both depths; 120000 at the leaf compares the link
  text, as before (see R2). SHA-256 repositories fail closed: the 40-hex regex at :307 and in `devflow_pin` (:230)
  never match a 64-hex id, so nothing is exempt. A malformed but correctly-hashed tree would raise `ValueError` at
  :318, uncaught; reaching it needs a preimage at a pinned id, and the crash exits non-zero (fail closed).
- **Q4, the `_SURFACES` cache.** Keyed by `str(root)` like `_PINS`; within one `--check`, `--judge` or
  `closure_check.py` process the base and the brief do not change, and a cached None keeps the run fail-closed. The
  only in-process importer is `scripts/closure_check.py:70`, a short-lived CLI. Safe.
- **Q5, the real tree.** `deploy_gate.py --check` at fba96ba: security MINOR at 718cae4 and tester MINOR at 07a7fc6,
  24 code files changed since each, FAIL. Running `changed_since` from the 8999ccf gate and from the fba96ba gate on
  this tree gives the identical 24-path list for both heads: the change moves nothing on the real tree (no tooling
  file there is currently pin-identical and different from the reviewed heads).
- R2's core holds: `_object` (:289-300) hashes `"<kind> <len>\0" + body` with SHA-1 against the requested id;
  `GIT_NO_REPLACE_OBJECTS=1` (:100) still applies to every git the gate starts. M2's symlink check uses
  `Path.is_symlink()` (lstat) before `is_file()` follows anything (:257).
- The red commit is red: with `scripts/deploy_gate.py` and `scripts/review_need.py` from 8999ccf, 7 of the 8
  `test_deploy_gate_444.py` cases fail (the control case passes); at fba96ba all pass.
- No new third-party import (`hashlib` is stdlib); no secret, no destructive operation, no workflow edit; both commits
  carry `GP-Agent:`/`GP-Task:` trailers and no AI attribution.

## Gates passed
- [x] Secret scan green (`scripts/secrets_scan.py`, gitleaks over tracked files: "no leaks found")
- [x] `make deps` (pip-audit) green (`pip_audit --strict` over the four `requirements/*.lock`: "No known vulnerabilities found")
- [x] `make slopsquat` green (`slopsquat PASS: 20 declared dependency(ies), 0 suspect`; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface; the exemption only narrows)
- [x] Permission-matrix not violated (no `.github/workflows/**`, `.claude/`, `.githooks/` edit; R1 left to the owner)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth/PII/payment/migration path; the control change is pre-approved by D-229 clause 3, tightening only, and none found loosened)
- [x] SAST (`ruff check --select S` on both scripts: all checks passed; bandit is not installed in the lock; conformance: `conformance PASS: 33 test(s) ... 0 failing`)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #444 M2 (no symlink exempt) → scripts/deploy_gate.py:257; tests/unit/test_deploy_gate_444.py:30
- #444 M3 (what the deploy commands start is code, fail closed on an unreadable workflow) → scripts/deploy_gate.py:259-260, :269-286; tests/unit/test_deploy_gate_444.py:65 (three cases), :76 (control); fail-closed branch untested (M3 above)
- #444 R2 (commit, trees, blob hashed against their ids) → scripts/deploy_gate.py:289-328; tests/unit/test_deploy_gate_444.py:84 (blob only; M2 above)
- #444 M1 (the pin routes to security, held equal to the gate's path) → scripts/review_need.py:92; tests/unit/test_deploy_gate_444.py:101, :111

## Risks queued
- **R1** scripts/deploy_gate.py:195 (`changed_since`) — pre-existing, same class as R2, not introduced here, and it
  makes R2's fix bypassable: `git diff --name-only <reviewed head>` reads the reviewed head's trees through the same
  unverified object store. Forging one loose TREE object reachable from the reviewed head, so that it names the
  agent's new blob, hides the change from `git diff` itself, before any exemption is consulted. Probe on the
  `_installed` fixture: change `src/app.py` (product code, never exempt), commit, rewrite the loose object of the
  reviewed head's `src` tree to name the new blob, then `--check` prints
  `security: ... PASS at <head>, no code changed since` and exits 0. The same probe on the shared `scripts` tree hides
  a tooling change. Needs write access to `.git/objects`, which R2 already treats as in reach. A gate bypass that
  stays green with no test: escalate (AGENTS.md section 3, Escalate NOW) and file an issue; a likely remedy is to
  verify the reviewed head's commit and trees the way `verified_blob` does (or diff against trees read through
  `_object`), or to run `git fsck --connectivity-only`/`--strict` on the reviewed head before trusting the diff.
- **R2** scripts/deploy_gate.py:325-328 — a 120000 (symlink) entry at the pin compares its link text with a regular
  file's bytes, so a regular file whose content equals the link target would read as unchanged. Same as before #444,
  and the pin `49f66343` ships no 120000 or 160000 entry today; worth a refusal of non-regular leaf modes (only
  `100644`/`100755`) the next time this function is touched.
- **R3** #444's own R1 (refs written by a program the guard does not list) is the owner's Bash guard and stays open;
  `protected_base` and therefore the pin and the base brief still rest on refs.
