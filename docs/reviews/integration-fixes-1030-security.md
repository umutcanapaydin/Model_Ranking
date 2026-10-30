---
record_type: review
id: integration-fixes-1030-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-30
---
# Security Review — integration/fixes-1030 (delta review of the stacked fixes #504, #507, #508)

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need RANGE=origin/main..HEAD` routed the stack to `security`: gate code changed in `scripts/client_decl_gate.py` and `scripts/deploy_gate.py`, and a policy edit in `scripts/deploy_gate.py`, #283)
**Independent:** yes. I wrote none of this code. I have not reviewed these branches before.
**Date:** 2026-10-30
**Release range:** origin/main (421d7c8)..ac0cd8c (merge commits `8d5bfcc` #504, `0e177f3` #507, `ac0cd8c` #508; no rebase)
**Reviewed head:** ac0cd8c8f27a728683eea493acabdf717c2ce482
**Risk tier:** HIGH (a deploy-gate control change; tightening only). The brief's `Paths that make a change HIGH:` is `none`, so §11's senior-review trigger does not fire.

## Verdict
MINOR

The combination breaks nothing. Git merged `scripts/deploy_gate.py` without a conflict, and `git show --remerge-diff` of
all three merges shows that only `docs/process-log.md` was resolved by hand. #507's integrity check runs before
everything #502 added: `current()` calls `compare_problem` (scripts/deploy_gate.py:483) before `changed_since`,
`changed_since` calls it again first (:194), and only after that does `shipped_unchanged` reach `deploy_surface`, `_files`
or `verified_blob`. Every mutant I tried on the seam is killed, except one (M1). M1 is a gap that predates the stack, in a
test and not in the code. One pre-existing fail-open of #493's own class is not covered by any open issue (R1). It is not
caused or widened by this stack, and it is Escalate NOW.

I worked in my own worktree, `scratchpad/sec-int`, at `ac0cd8c` (detached), with its own `.venv` from `make install`
and a copy of `advisor.db` (D-174). For the base comparisons I used a second worktree, `scratchpad/sec-int-main`, at
`421d7c8`. I read the policy (this profile, both stacked verdicts, `fix-issue-494-security.md`) at `origin/main`.
Probes were throwaway test files, removed after each run. I restored every mutant byte for byte (checked by comparing
bytes), and `git status` stayed clean in both worktrees.

## Findings

### BLOCKING
- none

### MINOR
- **M1** scripts/deploy_gate.py:421-432 (`_object`), used for the pinned commit at :435-440 — nothing holds the hash
  check on the PINNED COMMIT. Mutant: `named != oid` becomes `(kind != "commit" and named != oid)` (:430). It survives all
  43 tests in `test_deploy_gate_493.py`, `_494.py`, `_pin.py` and `_444.py`, and `conformance/test-deploy-shipped.py` (PASS).
  The combination matters here. The pinned commit is an ANCESTOR of the reviewed head, and #507's `_unhashed`
  (:249-287) hashes only the reviewed head's commit and its trees. So `_object`'s check is the only guard on that
  object. Probe: on the `_installed` fixture, change `scripts/tool.py` and commit. Then rewrite the pinned commit's loose
  object so that its `tree` line names HEAD's tree. The real gate refuses (`--check` exit 1, `scripts/tool.py` listed).
  Under the mutant, `--check` exits 0 (`no code changed since`). The code is right. The test is missing, so the
  invariant can be dropped silently. This predates the stack (the test files are unchanged in the range), and it is
  MINOR because the code holds today. Remedy: one test in `tests/unit/test_deploy_gate_494.py` beside
  `test_a_forged_pinned_tree_is_not_read_as_the_pinned_bytes`, which forges the pinned commit object as above and
  expects a non-zero exit with `scripts/tool.py` in the output. File it as an issue if it does not land on this branch.

### PASS
- **Ordering at the seam.** The integrity check comes first on every path that #502's exemption code can reach.
  `shipped_unchanged` (:340-361) is called only from `changed_since` (:207), after `compare_problem` (:194-195). The one
  external caller, `scripts/closure_check.py:70,90`, goes through `changed_since`, so it gets the check too. So a
  skip-worktree or assume-unchanged entry in the index is refused before `_files` (:370-381) reads that index
  (`--cached`). A forged tree under the reviewed head is refused before any exemption is considered.
- **Mutants on the merged code (all KILLED except M1).**
  - `compare_problem` removed from `current()` → `test_deploy_gate_493.py::test_a_forged_tree_under_the_reviewed_head_does_not_hide_a_change`.
  - Removed from `changed_since` → `::test_changed_since_itself_refuses_a_comparison_it_cannot_trust`.
  - Removed from both → the forged-tree test.
  - `_batch_read` hashing only trees → `::test_a_forged_reviewed_commit_does_not_hide_a_change`.
  - `S` dropped from `_flagged` → `::test_an_index_flag_does_not_hide_an_uncommitted_change[--skip-worktree]`.
  - `_object` not hashing trees → `test_deploy_gate_494.py::test_a_forged_pinned_tree_is_not_read_as_the_pinned_bytes`.
  - The surface ignored in `shipped_unchanged` → `::test_every_spelling_..._on_the_surface[dot-slash]`.
  - A `None` surface read as "nothing on it" → `::test_a_declaration_the_gate_cannot_read_to_its_files_exempts_nothing[no-deploy-command]`.
  - `files is None` dropped → `::test_a_tree_git_cannot_list_exempts_nothing`.

  None of #502's tests passes for the wrong reason now that #507's refusals come first. They assert that the changed
  path appears in the output (`assert rel in out`). `compare_problem`'s message does not carry that path, so an earlier
  refusal would turn them red, and they stay green at `ac0cd8c`.
- **Tests at ac0cd8c.**
  - The four deploy-gate files: 43 passed.
  - `-k "deploy_gate or closure"` over `tests/unit`: 243 passed.
  - `conformance/test-deploy-shipped.py`: PASS, 7 cases.
  - `test_settings_door_484.py`, `test_client_decl_gate.py`, `test_router_hints.py` and `test_testflight_ready.py`: 346 passed.
- **The real tree.** `deploy_gate.py --check` at `ac0cd8c` does not report "cannot be trusted": the index carries no
  flags, and every object hashes. It fails only because the release verdicts are stale (22 code files changed since
  `c29392c` and `3cddbdd`). That is the expected fail-closed answer, and a release delta review owes it.
- **Replace refs** stay off for every git the gate starts (`GIT_NO_REPLACE_OBJECTS=1`, :100, set at import). This is
  unchanged by the merge.
- **iOS.** #504 and #508 touch separate files (`ios/Config/*` against `ios/ModelRanking/SettingsDoor.swift`,
  `ContentView.swift`, `FrontDoor.swift`). Neither touches the other's surface. `SettingsDoor.swift` still hashes to
  `SETTINGS_DOOR_SHA256` (`4281544835…`, scripts/client_decl_gate.py:606), so the door's exception applies to that file
  alone. The Release `INFOPLIST_PREPROCESSOR_DEFINITIONS` is empty (ios/Config/Engine.xcconfig:30), so no Release build
  carries `NSAllowsLocalNetworking`.
- **The process-log merge.** Each branch's added lines are all present verbatim (0 missing for #488, #493 and #484), and
  the diff against `origin/main` deletes no line. No `## ` heading appears twice. The order is #494, #488, #493, #484
  (docs/process-log.md:1553, :1561, :1569, :1576). The merges' second parents are the branch tips `d523685`, `7754dce` and
  `887c4f7`.
- **Hygiene.** Every commit in the range carries `GP-Agent: claude-code` and `GP-Task:`, with no AI attribution. No
  `.github/`, `.claude/` or `.githooks/` edit, no dependency change (`pyproject.toml` and `requirements/` are unchanged),
  no secret, and no destructive operation.

## Gates passed
- [x] Secret scan green (`make secrets` at ac0cd8c: "no leaks found")
- [x] `make deps` (pip-audit) green ("No known vulnerabilities found")
- [x] `make slopsquat` green ("slopsquat PASS: 20 declared dependency(ies), 0 suspect"; no new import)
- [x] Default-deny preserved for new external surfaces (one new egress, the Settings door: the system constant only,
  pinned by hash; D-230)
- [x] Permission-matrix not violated (no protected-path edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth, PII, payment or migration path; HIGH paths `none`)
- [x] SAST (`ruff check --select S` on both gate files: one S101 at scripts/deploy_gate.py:224, an `assert` used for type
  narrowing, already accepted in the #493 verdict. `make conformance`: "PASS: 33 test(s) ... 0 failing")

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- The combination keeps #507's refusals ahead of #502's exemption → scripts/deploy_gate.py:194-195, :483-486;
  tests/unit/test_deploy_gate_493.py:26, :143 (each kills its mutant on the merged code)
- #502's surface behaviour is intact after the merge → tests/unit/test_deploy_gate_494.py (all 12 pass, and their
  mutants are killed: see PASS)
- The DevFlow exemption stays closed to a forged pinned object → scripts/deploy_gate.py:421-461; the tree is held by
  tests/unit/test_deploy_gate_494.py:72, the blob by tests/unit/test_deploy_gate_444.py:88, and the commit by no
  test (M1)
- No process-log entry is lost or duplicated → docs/process-log.md:1553-1582 (above)

## Risks queued
- **R1** scripts/deploy_gate.py:325 (`devflow_pin` → `git_show(root, base, DEVFLOW_PIN)`), :546 (`declared` → the
  policy root), scripts/brief_fields.py:103 (`root_at` → `git show <base>:docs/project-brief.md`), and
  scripts/deploy_gate.py:765 (base workflows). The gate reads the CONTENT of blobs at the protected base through git's
  unverified object store. #507's docstring (:252) says "Blobs need no check: the diff compares their ids". That holds
  for the diff, but not for these reads. While the pin file or the brief is unchanged since the reviewed head, its blob
  is in the reviewed head's tree too, so it is the same object. This is the reach #493 assumes: one loose object
  written under `.git/objects`. Two probes on the `_installed` fixture, each run at `421d7c8` (main) and at `ac0cd8c`
  with the same result:
  1. Change `scripts/tool.py` and commit it as the agent's commit `A`. Rewrite the loose blob of
     `main:docs/devflow-pin.txt` to read `v9.9 A`. `--check` then exits 0 (`no code changed since`), so the changed
     tool is exempt as "DevFlow's".
  2. Change `src/app.py`, drop `Deploy commands` from the tree's brief, and rewrite the loose blob of
     `main:docs/project-brief.md` the same way. `deploy_gate.py "fly deploy"` then exits 0 with no output. Unforged,
     it exits 2 (`BLOCKED ... src/app.py`). The deploy is not recognised at all. `make deploy-check` still fails here,
     but the guard does not.

  This predates the stack, which neither causes nor widens it. No open issue names it: #493 covers only trees, #505 the
  working-tree side, #500 the index flags. So it is not BLOCKING for this merge. It is a gate bypass that stays green
  with no test: file it as a new issue, Escalate NOW (AGENTS.md section 3). Remedy: read every base blob whose content
  the gate trusts through a verified path. That means the pin file, the brief, and the base workflows, both in
  `deploy_gate` and in `brief_fields.root_at`. Use `verified_blob`, or `_batch_read`, from the base commit (its commit,
  each tree and the blob hashed). Refuse (fail closed) when one does not hash. Add one test per probe above.
- **R2** scripts/deploy_gate.py:222-247 compared with :421-461 — the stack now carries two object-verification
  implementations, and they differ:
  - `_batch_read` and `_subtrees` take SHA-1 and SHA-256, and read a tree mode by its type bits.
  - `_object` and `verified_blob` take SHA-1 only. They read 20-byte entries (:451) and the literal mode `40000` (:458).

  Both fail closed: in a SHA-256 repository, or for a zero-padded `040000` at the pin, nothing is exempt. But two
  hand-kept copies of one rule is the shape §3.5 calls a finding, and R1's fix would add a third caller. Remedy: one
  verified-read helper, used by `_unhashed`, `verified_blob` and R1's base reads.
- **R3** scripts/deploy_gate.py:483 and :194 — `compare_problem` runs twice per verdict: once in `current()`, and again
  inside `changed_since`. With two verdicts, that is four index listings and four tree walks per gate call. That costs
  0.2 s each on the real tree, so this is cost only, not correctness. Leave it, or let `current()` rely on
  `changed_since` and keep the clearer message.
