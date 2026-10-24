---
record_type: review
id: fix-issue-410-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-24
---
# Security Review — fix-issue-410

**Reviewer:** Security-Reviewer subagent (light mode, inside run v020; `review-need` routed the branch to `security` for a policy edit: `scripts/deploy_gate.py`, `conformance/test-deploy-shipped.py`)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-24
**Release range:** `180644c..c912a80` (merge-base of `integration/run-v020` and `fix/issue-410-gate-exemption`; `ae02816` red test, `c912a80` the fix); round 2: `a3bc7d8..831f072` (`6233e49` red test, `831f072` the fix)
**Reviewed head:** 831f072eaadd1922d78953e9981da059c0e7a1fa
**Risk tier:** MEDIUM. The change edits the deploy gate, a safety control whose failure direction is CLOSED (`docs/security-baseline.md`, "Control-class fail direction"). The brief declares no HIGH paths (`docs/project-brief.md:110`), and nothing here touches auth, PII, payment or a migration, so no senior-review line is owed.

## Verdict
MINOR: BLOCKING 0 · MINOR 4 · risks queued 2 (round 2, at `831f072`; round 1 at `c912a80` was BLOCKING 2 · MINOR 3 · risks queued 2).

### Round 2 (re-verification of B1 and B2, `a3bc7d8..831f072`)

Range: `6233e49` (red test for B1) and `831f072` (the fix), fast-forwarded into this seat's worktree. Same seat, same method as round 1.

- **B1: resolved.** `scripts/deploy_gate.py:96-99` sets `GIT_NO_REPLACE_OBJECTS=1` at import. The gate passes no `env=` to any `subprocess.run`, so every git it starts inherits it, including the calls through `brief_fields`. `scripts/brief_fields.py:87` also passes `--no-replace-objects` for its other importers. Evidence: my round-1 probe repositories, rerun on the fixed gate. The pinned-bytes forgery (`refs/replace/<pinned v9.9>` pointing at a parentless commit holding the change) went from rc=0 on the round-1 gate to **rc=1**. The base forgery (the `main` tip replaced by a commit whose parent is the branch head, with `merge-base main HEAD` returning HEAD) went from rc=0 to **rc=1**. `git --no-replace-objects merge-base` returns the real tip. `tests/unit/test_deploy_gate_pin.py::test_a_replace_ref_does_not_forge_the_pinned_bytes` fails on the round-1 gate and passes on the fix, so it is a real red-to-green test. The owner-actions row (`docs/owner-actions.md:30`) now asks the guard to refuse `git replace`, `update-ref refs/replace/*`, and a fetch or push into `refs/replace/`.
- **B2: resolved.** `conformance/test-deploy-shipped.py:96-111` now moves the pin to the commit holding the change in the safety-surface case and in the scaffold case. Evidence (my two round-1 mutants, on the fix's tree):
  - No safety-surface check: conformance FAIL (`the safety surface changed, even byte-identical to the pinned commit: refused: exit 0`), and the unit tests give 1 failed (`test_a_deploy_script_is_code_even_byte_identical_to_the_pinned_commit`).
  - No `DEVFLOW_TOOLING` restriction: conformance FAIL (`a product scaffold file byte-identical to the pinned commit: still code, refused: exit 0`), and the unit tests give 1 failed (`test_a_product_file_byte_identical_to_the_pinned_commit_is_still_code`).
  - Unmutated: conformance PASS with 7 cases, unit tests 9 passed.
- **M4 (new, MINOR)** `tests/unit/test_deploy_gate_pin.py::test_a_replace_ref_does_not_forge_the_protected_base` cannot fail. It passes on the round-1 gate, which honours replace refs (run: the round-1 `scripts/` with the new test file gave 1 failed, 8 passed, and the only failure was the pinned-bytes test). It replaces the merge-base with a commit that descends from it. That makes the history a cycle rather than moving the base, so the forgery it names is never set up. Today the protection is covered because both fixes are in place and the pinned-bytes test catches the loss of the `os.environ` line. But a later change that kept `--no-replace-objects` only on `cat-file` would reopen the base forgery, and no test would fail. It is MINOR because the behaviour is correct at `831f072` (probe above). Remedy: build the fake base as the round-1 probe did. Use `git commit-tree -p <branch head> -m x <main tip>^{tree}`, then `git replace <main tip> <that commit>`. Assert that `git merge-base main HEAD` returns the branch head with replace refs honoured, so the test proves the forgery is real. Then confirm the test fails on `c912a80`'s `scripts/`.
- Not a lost polarity, noted only: a gate mutant that reads the pin at `HEAD` still passes conformance, because every conformance case commits on `main`. `test_a_pin_edited_on_the_branch_is_not_read` catches it. A branch case in DevFlow's conformance test would make the shipped control carry this polarity itself (round 1's B2 remedy, last sentence).
- M1, M2, M3, R1 and R2 stand as written in round 1. None is BLOCKING. File each as an issue. M4 is a one-test change worth taking on this branch.

### Round 1 (at `c912a80`)

The fix removes the tag and marker reads, and a pin rewritten on the branch is refused. But the pinned bytes and the protected base can still be forged with one ref write that the guard allows (B1, demonstrated end to end), so #410's finding stays open. The conformance test also lost two polarities it had at the base (B2, demonstrated by mutation).

## Method

- Policy read from the base ref: the profile, `AGENTS.md`, `docs/security-baseline.md` and `permission-matrix.md` at `main` (`3564a80`).
- Seat: a worktree at `c912a80` on `review/fix-issue-410-security`. `make install` was not run. Tests ran with the main clone's `.venv` read-only, `PYTHONPATH` set to the worktree's `src` and `scripts`. Every probe ran in a `mktemp -d` throwaway repository. The main checkout, launchd, Fly and GitHub were not touched. The only network call was a read-only `git ls-remote` against DevFlow's public repository.
- To test the guard, I sent JSON tool calls on stdin to the pinned `.claude/hooks/bash_guard.py` (sha256 `728db666f6c2`). It only judges the commands and runs nothing.

## Findings

### BLOCKING

- **B1** `scripts/deploy_gate.py:251`, `scripts/deploy_gate.py:231`, `scripts/brief_fields.py:86` (used by `protected_base`, `scripts/brief_fields.py:113-119`). Git's replace refs can still forge both the pinned bytes and the protected base. Category: OWASP A08 (software and data integrity failures). It is BLOCKING because the safety control fails OPEN (`permission-matrix.md` §11, "Control-class fail direction misapplied"), and the change does not meet D-223 clause 5 ("accept the exemption only against [the pin]").
  `git cat-file -p <pin>:<path>`, `git show <base>:docs/devflow-pin.txt` and `git merge-base` all read `refs/replace/*`. The guard refuses `git replace` but allows `git update-ref refs/replace/<sha> <x>`, `git fetch . <x>:refs/replace/<sha>` and `git push . <x>:refs/replace/<sha>`; each returned exit 0 from the pinned guard. Both forgeries below run against this head's `deploy_gate.py --check`:
  Evidence (pinned bytes): a repository built like `tests/unit/test_deploy_gate_pin.py::_installed`, plus a changed `scripts/tool.py` committed on `work`. The gate refused (`1 file(s) changed since the reviewed head ... scripts/tool.py`). Then `git commit-tree <work-commit>^{tree}` and `git update-ref refs/replace/<pinned v9.9 commit> <that commit>` gave `deploy-check PASS ... rc=0`. With `GIT_NO_REPLACE_OBJECTS=1` the same tree gave `rc=1`.
  Evidence (protected base): on the branch, `docs/devflow-pin.txt` re-pinned to the agent's commit was refused (`rc=1`). Then `git commit-tree -p HEAD <main-tip>^{tree}` and `git update-ref refs/replace/<main tip> <that commit>` made `git merge-base main HEAD` return HEAD. The gate reported `policy: the brief at c016b607b718` (the branch head) and `deploy-check PASS ... rc=0`. In this clone the base comes from `origin/HEAD` and `origin/main`. A replace ref keys on the object id, not the ref name, so replacing the `origin/main` tip works the same way. That moves the brief the gate reads as policy as well, not only the pin.
  Remedy: run every git call in the gate and in `brief_fields._git` without replace objects. Either pass `git --no-replace-objects ...`, or set `GIT_NO_REPLACE_OBJECTS=1` in the environment of those subprocess calls (`deploy_gate.py:188-191`, `:231`, `:251`, and `_workflow_texts`). Add red tests for both forgeries above. Extend the owner-actions row at `docs/owner-actions.md:30`: the guard should refuse a ref written under `refs/replace/` by `update-ref`, a `fetch` refspec or a `push .` refspec. The row now targets tags, which the gate no longer reads.

- **B2** `conformance/test-deploy-shipped.py:96-99` and `:104-109`. The conformance test lost two polarities it had at the base. A gate mutant that weakens the safety control now passes. This is a security-invariant test weakened (AGENTS.md §3, Escalate NOW), and it is BLOCKING by the triage rule (default UP).
  In both cases the pin is never moved to the commit that holds the new bytes. The file is therefore refused because it differs from the pin, whichever rule the case names. `git tag -f v9.10` at `:98` no longer does anything.
  Evidence (mutation, at `c912a80`):
  - With `if rel in SAFETY_SURFACE or rel.startswith(SAFETY_SURFACE_DIRS)` replaced by `if False` (`deploy_gate.py:243`), conformance gives `PASS: 7 cases` and the unit tests give 5 passed, 1 failed. Only the deploy-script test catches it, so nothing tests the membership of `bash_guard.py`, `settings.json`, `deploy_gate.py` or `brief_fields.py`.
  - With the `DEVFLOW_TOOLING` restriction (`deploy_gate.py:244`) removed, conformance gives `PASS: 7 cases` and the unit tests give 6 passed. That lets any product file (`src/`, `tests/`, `pyproject.toml`) that matches the pinned bytes skip review, and no test catches it.
  - At the base `180644c`, the same two mutants fail conformance: `the safety surface changed, even byte-identical to the tag: refused: exit 0` and `a product scaffold file byte-identical to the tag: still code, refused: exit 0`.
  - A mutant that reads the pin at `HEAD` instead of the base also passes conformance, because every case commits on `main`, so the base is HEAD. Only `test_a_pin_edited_on_the_branch_is_not_read` catches it.
  Remedy: in the safety-surface case and the scaffold case, rewrite `docs/devflow-pin.txt` to the commit that holds the new bytes, as the upgrade case at `:83` does. The only reason left to refuse is then the rule under test. Add one conformance case on a branch, where the base is not HEAD and a pin rewritten on the branch is refused. Then re-run the three mutants above and confirm each one fails.

### MINOR

- **M1** `scripts/deploy_gate.py:224`. Nothing checks where the pin came from. Any `v<label> <40 hex>` is accepted. The version label is never compared with anything, and nothing checks that the commit is DevFlow's. An upgrade PR shows the owner only a hash. A pin that names a commit on an agent's pushed branch would exempt whatever bytes that commit holds at tooling paths, and the diff never shows those bytes. It is MINOR because the pin reaches the base only through a human merge. I verified this PR's pin: `git ls-remote https://github.com/SADCAIVibe/DevFlow.git 'refs/tags/v7.2*'` returns `49f66343b2edab5aef44adbbdf151a96550a085e refs/tags/v7.2`. The commit is "Merge pull request #22 from SADCAIVibe/release/v7.2", it is not an ancestor of `main`, and the main clone's `.gp/installed` says `v7.2`. Remedy: route `docs/devflow-pin.txt` as a policy path in `scripts/review_need.py`, so a pin change always reaches this seat. Have the seat or `/pre-merge` check the pin against `git ls-remote <DevFlow> refs/tags/<label>`. Refuse a pin whose commit is reachable from the project's own history.
- **M2** `scripts/deploy_gate.py:248`, `:255`. `target.is_file()` and `read_bytes()` follow a symlink in the working tree. A tooling path replaced by a symlink to a file outside the repository that holds the pinned bytes counts as "DevFlow's, unchanged". Git records that as a type change (100644 to 120000), and the bytes it points at can change between the gate's check and the command that uses them. Remedy: treat `target.is_symlink()` as code (return False). Add a unit case.
- **M3** `scripts/deploy_gate.py:208-210`. The safety surface is a hand-kept list that sits beside the brief's `Deploy commands:` (`docs/project-brief.md:107`), which is a finding under AGENTS.md §3.5. Once the owner copies `scripts/ci/nightly-hosted.yml` to `.github/workflows/nightly-hosted.yml`, that installed workflow is what `gh workflow run nightly-hosted.yml` runs. It falls under `.github/`, which counts as tooling, and the safety surface does not cover it. A deploy script added to the brief later would not be covered either. Exposure is low today: the exemption needs the pinned DevFlow commit to ship the same path, and v7.2 ships none of the three. Remedy: derive the deploy part of the safety surface from the brief. Every path-form program in `Deploy commands:`, and `.github/workflows/<name>` plus `scripts/ci/<name>` for each `gh workflow run <name>`, should be safety surface. Add a test that compares the derived set with the brief and fails closed on an empty set.

### PASS

- Fail-closed on every path asked about: no protected base (`protected_base` returns None, so the pin is None, `deploy_gate.py:222-225`); no pin at the base or a `git show` error or timeout (`git_show` returns None, `:229-235`); a malformed pin (`re.fullmatch` misses, `:224`); a pinned commit absent from the clone (`cat-file` exits non-zero, `:255`). A negative answer is cached as None, so the cache can only fail closed. Until this PR reaches `main`, no pin exists at the base and every DevFlow-only change owes a delta, which is the safe direction.
- `_PINS` (`:215`) is keyed on the root and lives for one process. The guard runs `deploy_gate.py` once per Bash call, and the in-process importer (`scripts/closure_check.py:70`) is a one-shot CLI. The cache cannot outlive a base change.
- textconv: `git show <rev>:<path>` does not apply a textconv driver unless `--textconv` is passed. Probed: with `.gitattributes` `diff=x` and `diff.x.textconv` set, `git show` printed the raw blob and `git show --textconv` printed the filtered one. `cat-file -p` is raw. No `PLAIN_DIFF`-style flag is needed for these two reads. B1 covers the replace-object read, which is the one that matters.
- Symlink or submodule at the pin path in the base: a symlink blob prints its link text and a gitlink errors. Both miss the regex, so the pin is None (fail closed). The base is reached only through a human merge.
- The tag and `.gp/installed` reads are gone (`deploy_gate.py:238-255`). The red tests `tests/unit/test_deploy_gate_pin.py:75`, `:87` and `:96` cover the forged tag, the moved tag and the pin rewritten on the branch, and all six unit tests pass at the head.
- Safety-surface completeness against the pinned v7.2 tree: of the files DevFlow ships, those on the deploy path are `deploy_gate.py`, `brief_fields.py`, `bash_guard.py` and `settings.json`, and all four are listed. The product deploy scripts (`deploy_hosted_engine.sh`, `nightly_hosted.sh`, `scripts/ci/nightly-hosted.yml`) are not in v7.2, so the exemption cannot reach them without a forged pin. Listing them is defence in depth. The image contents (`Dockerfile`, `fly.toml`, `src/`, `requirements/`) are outside the tooling roots and always count as code.

## Gates passed
- [x] Secret scan green: `python3 scripts/secrets_scan.py` at `c912a80`, `no leaks found`
- [x] `make deps` (pip-audit) green: the dispatcher's line from the integration branch (`No known vulnerabilities found`). The range adds no dependency or import (`re` and `subprocess` were already imported)
- [x] `make slopsquat` green: the dispatcher's line (PASS). No new import
- [x] Default-deny preserved for new external surfaces: no route, endpoint or network surface is added
- [ ] Permission-matrix not violated: the guard allows `refs/replace/` writes that move the deploy gate's base (B1); the fix is in the gate and the owner's guard
- [n/a] Prompt-injection hygiene: no untrusted content is consumed
- [n/a] Auth/PII checks + human review trigger: no auth, PII, payment or migration path
- [x] SAST: `bandit` is not installed in the seat's venv. `ruff --select S` on the three changed code files shows only S603/S607 on the conformance helper's unchanged `subprocess` lines (`conformance/test-deploy-shipped.py:44`, `:48`)
- [x] Conformance: `conformance/test-deploy-shipped.py` PASS, 7 cases, at the head. But see B2: it no longer fails on two mutants it caught at the base

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- D-223 clause 5 (a): pin DevFlow's commit in a tracked record, read at the protected base: `docs/devflow-pin.txt:1`, `scripts/deploy_gate.py:211-226`, test `tests/unit/test_deploy_gate_pin.py:96`. **Not met while B1 stands**: a replace ref forges the base and the pinned bytes.
- D-223 clause 5 (b): accept the exemption only against the pin, with no tag and no marker: `scripts/deploy_gate.py:238-255`, tests `tests/unit/test_deploy_gate_pin.py:75`, `:87`, `:122`. **Not met while B1 stands.**
- D-223 clause 5 (c): the product's deploy scripts join the safety surface: `scripts/deploy_gate.py:208-210`, test `tests/unit/test_deploy_gate_pin.py:107`. Met for the two scripts and `scripts/ci/`. M3 covers the installed workflow.
- D-223 clause 5 (d): the guard's refusal of `refs/tags/v*` writes is an owner-actions row: `docs/owner-actions.md:30`. Met. B1's remedy widens it to `refs/replace/`.

## Risks queued
- **R1** The guard's documented #318 gap: `.claude/hooks/bash_guard.py` lists "a ref written by a program this does not list" as unseen. A `python -c` write to `.git/refs/remotes/origin/*` or `.git/refs/replace/*` therefore still moves the protected base, which every policy read in the gate rests on (the brief, the workflows, and now the pin). B1's `--no-replace-objects` closes the replace half inside the gate. The remote-ref half has no local anchor that cannot be forged. CI re-running the gate on the merged tree is the backstop. Owner's file: no agent change.
- **R2** Git does not verify the hash of a loose object when it reads one. Probed with git 2.54.0: a crafted zlib file written at `.git/objects/49/f66343...` in an empty repository was served by `git cat-file -p 49f66343...` as `forged`. In a clone where the pinned commit is absent (a fresh clone without DevFlow's tags), a program the guard does not list could plant a commit, tree and blob at the pinned ids. The gate would then read them as DevFlow's. In this clone the pinned commit and its tree are packed, and a packed object is looked up before a loose one. Remedy direction: before trusting a pinned path, check its Merkle chain (hash the raw commit, then each tree on the path, then the blob, against the ids that name them). Alternatively, fail closed unless the pinned object is packed or `git fsck` verifies it.
