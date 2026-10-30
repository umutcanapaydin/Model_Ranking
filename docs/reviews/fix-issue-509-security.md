---
record_type: review
id: fix-issue-509-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — fix-issue-509

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` routed the branch to `security` for a policy edit: `scripts/deploy_gate.py`, `scripts/brief_fields.py`, #283)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this branch before.
**Date:** 2026-10-30
**Release range:** 53c49e9..d7780fc (`025e407` red test, alone; `d7780fc` fix), cut from #511's head
**Reviewed head:** d7780fc8f3273d041b22887759bed0bf6a253f2b
**Risk tier:** HIGH (a deploy-gate control change; tightening only, pre-approved by D-231 clause 1)

## Verdict
MINOR

The branch closes R1 of `docs/reviews/integration-fixes-1030-security.md` on every path I probed. A forged, missing or
malformed base object no longer exempts a tool, hides a deploy command, or hides a deploy workflow. I found nothing that
loosens the gate, so D-231 clause 1 holds. Three things are MINOR. The refuse-everything answer also fires in an
offline partial clone, which is not forged (M1). The fail-closed branch for a base workflow folder whose TREE does not
hash is right, but no test holds it: under its mutant, a forged tree lets a deploy dispatch through and all 272 tests
stay green (M2). And four smaller mutants survive (M3). The three new tests are red at `53c49e9`, and each fails when its
behaviour is removed (N1, N2, N3, N5).

Worked in my own worktree, `scratchpad/sec-509`, at `d7780fc` (detached), with its own venv from `make install` and
`advisor.db` copied in (D-174). Probes ran against copies of the gate at `d7780fc` ("new") and `2d29b9c` ("old") in
`scratchpad/probe509/`, outside every tree, on fresh fixture repositories. Every mutant was restored byte for byte by the
runner, and `git status` stayed clean.

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/brief_fields.py:136-149 with scripts/deploy_gate.py:168-169 and :544-548 — the refuse-everything answer
  also fires in a state that is not forged. A `--filter=blob:none` partial clone whose branch changed the brief never has
  the base's brief blob locally. Offline, `cat-file --batch` cannot fetch it lazily, so it reports `missing` and
  `root_at` raises `Unverified`. Every Bash call the guard judges is then refused, including `ls` and the `git fetch`
  that would repair it.
  Evidence (probe `partial5`, origin directory moved away):
  ```
  old [ls] exit 0
  new [ls] exit 2 fatal: ... does not appear to be a git repository ... could not fetch 5bf5d5a4 from promisor remote
  deploy-check: policy: unreadable (docs/project-brief.md at 63cb80e926e0 cannot be read as that commit holds it:
    object 5bf5d5a4b896ec8f3f3957499ed5cae4d385cd27 cannot be read as a blob)
  ```
  A committed symlink at `docs/project-brief.md` (mode `120000`) also refuses every command, with no forgery (probe
  `symlink`).
  It is MINOR, not BLOCKING. The direction is closed, so nothing becomes exploitable. The case is outside this project's
  setup: the main tree is a full clone and CI is not a session. And `missing` must stay in the refuse-everything class.
  With the base brief's blob deleted, the OLD gate let `fly deploy` through (exit 0, probe `missing`), so downgrading
  `missing` to "policy unreadable" would reopen that path. What falls short is the scope the row in
  `docs/plans/assumptions-1030.md` gives: "Only a forged, missing or malformed object triggers it". A partial clone's
  promisor-missing object and a committed symlink also trigger it. And the message names no remedy.
  Remedy (wording only, no loosening):
  - When the reader reports `missing` and a promisor remote is configured, have the refusal say so: "a partial clone
    cannot read the base's brief offline: run `git fetch` in your own terminal".
  - When an object does not hash, have it say "run `git fsck`, then re-fetch".
  - Add the partial-clone and symlink cases to the assumptions row.
- **M2** scripts/deploy_gate.py:714-716 — `_workflow_texts` marks the read incomplete when
  `brief_fields.verified_files` raises for a whole folder. That happens when the folder's TREE, or a tree on the way to
  it, does not hash or is missing. The code is right: probe `workflow_tree` forges the base's `.github/workflows` tree so
  that `release.yml` names a harmless blob, and `gh workflow run release` goes from exit 0 (old) to exit 2 (new). But no
  test holds it. Mutant N16 removes `complete = False` there, and the same probe then exits 0 while all 272 tests in
  `-k "deploy_gate or closure or review_need or brief_fields"` pass:
  ```
  new [gh workflow run release] exit 2 'BLOCKED: ... a workflow file at the protected base could not be read ...'
  n16 [gh workflow run release] exit 0 ''
  ```
  This is part of #509's own criterion (each tree hashed, failing closed). It is MINOR, not BLOCKING, because the code
  is correct at the reviewed head. It is graded as #493's untested fail-closed line M4 was. But it is the shape AGENTS.md
  section 3 names: a fault that would stay green with no test. Remedy: one test in tests/unit/test_deploy_gate_509.py
  that forges the base's `.github/workflows` tree (as `test_deploy_gate_493._forge` does for a tree), and expects
  `gh workflow run release` to exit 2 and `ls` to exit 0.
- **M3** scripts/brief_fields.py — four more mutants survive the 272 tests. Each is right by hand or fails closed, so
  none is a defect:
  - N7: the check at :207 that a directory on the way is the bytes `40000` is dropped. A zero-padded tree would then be
    read through. It still hashes, so the content is verified, but the strictness is unproven.
  - N12: a subtree read error inside the folder walk at :250-252 is skipped. A forged NESTED tree under
    `.github/workflows/` or `scripts/ci/` would then be skipped quietly. GitHub runs no workflow from a subdirectory,
    so the reach is low.
  - N14: the commit's `tree` regex at :181 is narrowed to 40 hex. A SHA-256 repository would then refuse every
    command; I probed SHA-256 by hand and it works.
  - N13b: the commit read through `rev-parse` output only. This survives because `_commit`'s `rev-parse ...^{commit}`
    already hashes the commit, so it is defence in depth, not a gap.

  Remedy: a SHA-256 fixture test and a nested forged-tree test. The zero-padded case is optional.

### PASS
- **Probe 1 (forged base pin), closed.** scripts/deploy_gate.py:317 reads the pin through `verified_blob` →
  `brief_fields.verified_file`; a pin blob that does not hash reads as no pin, so nothing is exempt. Held by
  tests/unit/test_deploy_gate_509.py:31 (red at `53c49e9`: fails at :39).
- **Probe 2 (forged base brief), closed.** Rewriting the loose blob of `main:docs/project-brief.md` to drop `Deploy
  commands`: old `fly deploy` exit 0, new exit 2 (`... any command: ... does not hash to its id`). Held by
  tests/unit/test_deploy_gate_509.py:43 (red: fails at :52).
- **The workflow read, closed.** A forged workflow BLOB is held by tests/unit/test_deploy_gate_509.py:55 (red: fails at
  :73). A forged `.github/workflows` TREE (probe `workflow_tree`): old `gh workflow run release` exit 0, new exit 2
  (`a workflow file at the protected base could not be read`), and `ls` stays 0.
- **The dispatch test, judged as asked: its assertions are unchanged, and it still tests what it claims.**
  tests/unit/test_deploy_gate_dispatch.py:247-266 keeps the five `assert` lines at `53c49e9` byte for byte. The
  injection moved from `git show` to `brief_fields.batch_read`, keyed on the blob id of `.github/workflows/a.yml`.
  HEAD is the base in this fixture, so that id is the base's blob. The injected string (`cannot be read as a blob`) is
  what the reader returns for a real missing object. The test still proves round 1's N1:
  - the failing file is named and the read is incomplete;
  - the files after it are still read (`len(texts["z.yml"]) == 2`);
  - every dispatch, but not `ls`, becomes a deploy.

  Two mutants confirm it bites. N4 (removing `complete = complete and not failed`) and N9 (letting a failing file abort
  its folder) are both KILLED by it. The only path it reaches less than the old `git show` injection did is the
  folder-level branch, which M2 covers.
- **Every other forged or missing path fails closed** (probes, old → new, `fly deploy`):
  - the base brief's blob deleted: 0 → 2. The old gate read the brief as absent, which is a second fail-open this
    branch closes.
  - the base `docs` tree forged: 0 → 2.
  - the base COMMIT object forged to name HEAD's tree: 0 → 2. `_commit`'s `rev-parse <rev>^{commit}`
    (scripts/brief_fields.py:166-174) fails on git's own hash check, and that is raised as `Unverified`, never read as
    "no base". This is the opposite of #493's B1, where the same failure was read as "no head".
  - a zero-padded `040000 docs` committed at the base: 2 → 2, and every command is refused, as the assumptions row says
    for "malformed".
  - an annotated tag: `root_at("probe-tag")` peels to the commit, and a forged tag object is refused (`Unverified`).
- **SHA-256.** In a `--object-format=sha256` fixture the base brief reads (`deploy-check: policy: the brief at
  23c75bc4ca98 ...`), `fly deploy` is refused for want of verdicts, `ls` passes, and a forged blob refuses every command.
  `batch_read` picks the digest from the id's length (scripts/brief_fields.py:146), and `tree_entries` uses
  `len(oid) // 2`. No test reaches it (M3, N14).
- **The modes stay as strict as #511 left them.** A directory on the way must be the bytes `40000`
  (scripts/brief_fields.py:207). The last entry must be `100644` or `100755` (:220). Links, submodules and zero-padded
  modes are `Unverified`, which `verified_blob` turns into None (scripts/deploy_gate.py:404-410). So the pin keeps
  #494 R2's strictness exactly, and the brief and the workflows gain it.
- **`_unhashed` (#493) keeps its behaviour.** Its body is unchanged except that `brief_fields.open_batch`,
  `batch_read` and `close_batch` replace the moved copies, and the moved code is byte for byte the same. Its type-bit
  walk (scripts/deploy_gate.py:238-241) still reads trees through `brief_fields.tree_entries`. All 272 tests selected by
  `-k "deploy_gate or closure or review_need or brief_fields"` pass at d7780fc, `test_deploy_gate_493.py` among them.
- **It does not brick a normal session.** `ls` exits 0 in each of these cases:
  - a full clone;
  - no default branch at all (`fly deploy` is still refused: `no merge-base`);
  - a `--depth 1` shallow clone;
  - a partial clone whose base blob is local, or that is online;
  - `git` missing from PATH (`_git` returns 127, so there is no base and no `Unverified`).

  The only non-forged triggers are M1's. The guard bounds every gate call at 20 s (.claude/hooks/bash_guard.py:3460),
  so a lazy fetch that hangs fails closed and stays bounded.
- **Callers of `root_at`.** scripts/review_need.py:139-142 and :223-227 are the only other callers;
  scripts/closure_check.py does not call it. `Unverified` subclasses `RuntimeError`, which `review_need`'s `main`
  already turns into a refusal (:318). So a forged brief at a range's base or end now fails `make review-need` closed,
  where it used to read the forged text. Nothing behaves worse. An unknown name such as `root_at("nope")` is now
  reported as `Unverified` with "cannot be read as that commit holds it" (wording only, R3).
- **Mutants** on the 272-test selection, each restored byte for byte after its run:
  - KILLED: the unverified-brief branch in `deploy_in` removed (N1); `Unverified` read as a plain `RuntimeError` in
    `_policy` (N2); the pin read back through `git show` (N3); failed files ignored (N4); the blob hash switched off
    (N5); the tree hash switched off (N6); the last-entry mode check dropped (N8); a failing file aborting its folder
    (N9); a failing file skipped quietly (N10); `root_at` swallowing `Unverified` (N15).
  - SURVIVED: N11 (a folder that is not a directory), which is redundant, since reading a blob as a tree is refused
    anyway; N7, N12, N14 and N13b (M3); and N16 (M2).
- No new third-party import (`hashlib`, `collections.abc` and `typing` are in the standard library), no secret, no
  destructive operation, and no `.github/`, `.claude/` or `.githooks/` edit. Both commits carry `GP-Agent:` and
  `GP-Task: issue-509` and no AI attribution. The red commit `025e407` holds the test file alone.

## Gates passed
- [x] Secret scan green (`make secrets` at d7780fc, run by me: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface; the gate only refuses more)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model; the base's files are parsed, never followed)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; the brief's
  `Paths that make a change HIGH:` is `none`)
- [x] SAST: `ruff check --select S` on both files. One S101 at scripts/brief_fields.py:138: the `assert` moved with
  `batch_read`, the same narrowing #493's review accepted, and under `-O` it fails closed. bandit is not in the lock.
  `make conformance` at d7780fc: "conformance PASS: 33 test(s) derived from conformance/, 0 failing"

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #509, probe 1: a forged base pin exempts nothing → scripts/deploy_gate.py:317; tests/unit/test_deploy_gate_509.py:31
- #509, probe 2: a forged base brief does not hide a deploy → scripts/brief_fields.py:97-113, scripts/deploy_gate.py:156-172,
  :544-548; tests/unit/test_deploy_gate_509.py:43
- #509, the base workflows are read verified, failing closed → scripts/brief_fields.py:236-262, scripts/deploy_gate.py:708-720;
  tests/unit/test_deploy_gate_509.py:55 (a blob); tests/unit/test_deploy_gate_dispatch.py:247 (a file that fails);
  the TREE branch, scripts/deploy_gate.py:714-716, has no test (M2)
- #509, the commit, each tree and the blob hashed → scripts/brief_fields.py:166-216; held by the forged-commit and
  forged-tree probes. The tree hash is held through the shared `batch_read` (mutant N6, KILLED); the commit
  is hashed twice (N13b, see M3)

## Risks queued
- **R1** scripts/brief_fields.py:265-271 (`protected_base`) — the base the gate reads its policy at is the merge-base of
  HEAD, and HEAD's history belongs to the change. This needs no forgery. A commit made with `git commit-tree` whose parent
  is an older main commit, from before `Deploy commands` was declared, carrying today's tree with the brief's deploy line
  removed, gives a merge-base at that old commit. Probe `stale_base`: `fly deploy` exits 0 under both the old and the new
  gate. A branch genuinely cut before the declaration does the same. Forging a commit that `merge-base` walks adds no
  reach beyond that, since the history is the change's own to write. This predates #509, which neither causes nor widens
  it. Remedy, tightening only: judge deploys against the union of the `Deploy commands` declared at the merge-base and at
  the default branch's tip (`origin/main`). New issue, Escalate NOW class (a gate bypass that stays green with no test).
- **R2** scripts/brief_fields.py:248-260 — `verified_files` reads and judges every entry under `WORKFLOW_DIRS`
  (`.github/workflows`, `scripts/ci`). A committed non-YAML symlink there therefore marks the base read incomplete, and
  every `gh workflow run` becomes a deploy (probe `ci_symlink`: old 0, new 2). The old code skipped non-`.yml` paths
  before reading. This fails closed and applies only to dispatches. Remedy: skip a non-directory entry whose name does
  not end in `.yml` or `.yaml` before reading it, and keep a failing `.yml` as `failed`.
- **R3** scripts/brief_fields.py:173 — every `rev-parse` failure is raised as `Unverified`, including a name that does
  not exist and a git older than 2.30 that rejects `--end-of-options`. In the gate the base is always a merge-base id,
  so only a missing or forged commit reaches it, which is correct. But a git without `--end-of-options` would refuse
  every Bash call. This machine runs 2.54. Remedy: on an `--end-of-options` usage error, raise `RuntimeError` (the
  policy is unreadable, so deploys are refused but `ls` is not), and fix the message for an unknown name.
