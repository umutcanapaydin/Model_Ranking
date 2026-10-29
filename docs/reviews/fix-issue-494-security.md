---
record_type: review
id: fix-issue-494-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-29
---
# Security Review — fix-issue-494

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need-branch` routed the branch to `security` for a policy edit: `conformance/test-deploy-shipped.py`, `scripts/deploy_gate.py`, #283)
**Independent:** yes. I wrote neither the red test nor the fix, and I have not reviewed this code before.
**Date:** 2026-10-29
**Release range:** a2650e0..60afb68 (`ec5d662` red tests, `7118f1b` the fix, `60afb68` round 2: B1 and R1)
**Reviewed head:** 60afb68b8605a058b2e325cb9a7a3bf34f9b87b6
**Risk tier:** HIGH (a deploy-gate policy change; a control change that must only tighten)

## Verdict
MINOR

The gate code tightens. Nothing that a deploy starts is exempt now that was not exempt before. On the real tree the
derived surface is the same at a2650e0 and at 7118f1b. The one blocking finding is in a test, not in the gate: the
fixture change in `tests/unit/test_deploy_gate_pin.py` declares a safety-surface file as the deploy command. After
that change the two tests that held `scripts/deploy_hosted_engine.sh` on `SAFETY_SURFACE` can no longer fail
(B1). The fix is one line, and I probed it (see B1).

Worked in my own worktree at `7118f1b` (scratchpad `wt494`), plus a second worktree at `a2650e0` for the base
comparisons. Both use my own venv, installed from `requirements/dev.lock` with `--require-hashes` (D-174). I read the
policy (this profile, `docs/reviews/fix-issue-444-security.md`, D-229) at `origin/main`, and this profile is the same
on the branch. Probes ran in throwaway repositories in the scratchpad. Every temporary mutation was restored by copy.
`git status` was clean in both worktrees when I finished, and I removed both.

## Findings

### BLOCKING
- **B1** tests/unit/test_deploy_gate_pin.py:58-59 — test integrity of a security invariant. To stay green
  under the new fail-closed `not decl` branch, `_installed` now declares `scripts/deploy_hosted_engine.sh` as the
  deploy command. That file is already on `SAFETY_SURFACE` (scripts/deploy_gate.py:214-215). It is now on the
  derived deploy surface as well, so the two tests that proved its `SAFETY_SURFACE` membership pass with that entry
  removed: `test_a_deploy_script_is_code_even_byte_identical_to_the_pinned_commit` (:111) and
  `test_every_deploy_surface_is_code_even_byte_identical_to_the_pinned_commit[scripts/deploy_hosted_engine.sh]`
  (:187, the test whose own comment at :182 says it exists "so a surface dropped from the gate's set fails this
  test").
  Evidence: mutant `scripts/deploy_gate.py:214-215` with `"scripts/deploy_hosted_engine.sh"` dropped from
  `SAFETY_SURFACE`:
  at a2650e0 (`test_deploy_gate_pin.py` + `_444.py`): `2 failed, 19 passed` (the two tests above);
  at 7118f1b (every `tests/unit` test matching `deploy_gate or deploy_hosted or deploy_shipped`): `254 passed`.
  This is not exploitable today, because the real brief declares the script (docs/project-brief.md:107). But the
  invariant now rests on the brief, which a later edit can change, and AGENTS.md section 3 lists a weakened
  security-invariant test at HIGH as BLOCKING. `conformance/test-deploy-shipped.py:59` is NOT affected: it declares
  `scripts/deploy.sh`, a path its fixture never creates, so its surface is empty as before, and its safety-surface case
  uses `.claude/settings.json`.
  Remedy (probed): declare a command that names no safety-surface file, for example
  `- **Deploy commands:** \`fly deploy\`` at :59. With that line, `test_deploy_gate_pin.py`, `_444.py` and `_494.py`
  give `33 passed`, and the mutant above gives `2 failed, 31 passed` (the same two tests fail again).

### MINOR
- **M1** scripts/deploy_gate.py:271, :288-300, :313-315 — the derived surface is still read word by word, and
  several spellings resolve to nothing. They fail OPEN: they give an empty contribution, not `None`. This is
  pre-existing and not loosened: base and head agree on every probe below. Probed with `deploy_surface` from each tree
  on a throwaway repository: `cd scripts && ./ship.sh`, `$PWD/scripts/ship.sh`, `python -m scripts.ship`,
  `run-parts scripts/deploy` (a directory word), `just deploy` (a recipe runner `UNREAD_RECIPES` does not name),
  `bash -c 'make ship'` (make inside a `-c` string). Each gives `[]` at both heads. `env make ship` and
  `sudo make ship` now give `None`, which is correct. Also, a workflow a declared `gh workflow run` starts may itself
  run `make deploy`. The workflow file joins the surface, but the Makefile and what it runs do not. `UNREAD_RECIPES` is
  a named list with a reason (AGENTS.md section 3.5), but it fails open: a runner nobody named is read as plain words.
  Minor because the repository's four declared commands are all in forms the code reads (same surface at both heads,
  below), so the risk is latent. Remedy, in the fail-closed direction: invert the list into the programs whose
  arguments are read directly, and return `None` for any other program. Also return `None` for a path-like declared
  word (one holding `/`, `$` or `~`) that names no file git lists. The conformance fixture's `scripts/deploy.sh`
  would then need to exist.

### PASS
- **Q1, no loosening (including through `deploy_workflows` and `deploy_in`).**
  - `deploy_surface` (:303-321) only adds `None` branches: `not decl`, `unread`, `files is None`.
  - The new `named` (:319) covers everything the old `{word if "/" in word and (root / word).is_file()}` did that
    `changed_since` can list. A file git does not list (ignored and untracked) is never a changed path, because
    `changed_since` uses `--exclude-standard` as `_files` does. It also adds `./`, `a/../`, absolute, mixed-case and
    slash-less root words.
  - `deploy_workflows` (:706-711): a dispatched name either maps to every file whose `_names` hold it, or stays as
    written, so the returned name sets are a superset of the old ones. In `deploy_in` (:503-510) `deploys` can only
    grow and `bool(workflows)` is unchanged. It now also refuses `gh workflow run release.yml` when the brief declares
    the dispatch by stem, which the old code let through (`start & deploys` was empty).
  - The only path that left the surface: `.github/workflows/<stem>` without an extension, when a `<stem>.yml` exists
    (probe with `gh workflow run release`: base `['.github/workflows/release', 'scripts/ci/release']`, head
    `['.github/workflows/release.yml', 'scripts/ci/release.yml']`). That is a placeholder path, not a file the
    dispatch starts: GitHub runs only `.yml`/`.yaml` from that directory, and `gh` resolves the stem to the `.yml`
    file. The `scripts/ci/` variant is `SAFETY_SURFACE_DIRS` anyway.
  - Real tree, `deploy_surface` from each tree on the 7118f1b checkout: both give
    `['.github/workflows/nightly-hosted.yml', 'scripts/ci/nightly-hosted.yml', 'scripts/deploy_hosted_engine.sh',
    'scripts/nightly_hosted.sh']`.
- **Q1, R2.** `verified_blob` (:361-362) now accepts only `100644`/`100755` at the leaf and `40000` for a
  directory. Every other mode is refused, including `120000`, `160000` and legacy `100664`. That is strictly narrower.
- **Q1, steering.** `declared()` (:440-457) still unions the base brief with the tree's, and `_workflow_texts` still
  unions the base workflows with the tree's. A branch can add `make ...` (making the surface `None`) or more words.
  Both only tighten.
- **Q3, the new tests fail when their behaviour is removed.** One mutant per branch, `tests/unit/test_deploy_gate_494.py`:
  - drop `not decl` → `[no-deploy-command]` fails
  - drop `unread` → `[make-target]` fails
  - drop `not complete` → `test_a_base_workflow_that_cannot_be_read_exempts_nothing` fails (M3)
  - the old literal `named` → `[dot-slash]` fails
  - no absolute-path handling → `[absolute]` fails
  - no `normpath` → `[dot-slash]` fails
  - case-sensitive `_files` → `[mixed-case]` fails
  - the old `files = set(dispatched)` → `[workflow-stem]` fails
  - the old mode test → `test_a_symlink_entry_at_the_pin_is_not_read_as_a_file` fails (R2)
  - tree hashes unchecked, or commit and tree hashes unchecked (the #444 review's M2 mutant) →
    `test_a_forged_pinned_tree_is_not_read_as_the_pinned_bytes` fails (M2)
  - `surface is not None and rel in surface` → fails

  Only the `files is None` mutant survives (R1).
- **Red commit.** With `scripts/deploy_gate.py` from a2650e0, 9 of the 12 tests in `test_deploy_gate_494.py` fail:
  all M1 spellings, both fail-closed cases, and R2. The control case, M2 and M3 pass at base. That is expected,
  because #494 says the code was already right there and only the tests were missing.
- **Q2, the conformance fixture.** `conformance/test-deploy-shipped.py:59` does not weaken what the test proves (see
  B1). `test-deploy-shipped PASS: 7 cases` at head.
- No new import (`os`, `subprocess` were already imported). No secret, no destructive operation, and no
  `.github/workflows/**`, `.claude/`, `.githooks/`, `pyproject.toml` or lock edit. Both commits carry
  `GP-Agent: claude-code` / `GP-Task: issue-494` and no AI attribution.

## Gates passed
- [x] Secret scan green (dispatcher: `secrets: scanning the 1356 file(s) git tracks ... no leaks found` on 7118f1b)
- [x] `make deps` (pip-audit) green (dispatcher: `deps: No known vulnerabilities found`)
- [x] `make slopsquat` green (dispatcher: `slopsquat: PASS 11.5 h ago on this same manifest`; no dependency file in the range)
- [x] Default-deny preserved for new external surfaces (no new surface; the exemption only narrows)
- [x] Permission-matrix not violated (no workflow, `.claude/` or `.githooks/` edit)
- [x] Prompt-injection hygiene (n/a: no untrusted text reaches a model)
- [x] Auth/PII checks + human review trigger fired (n/a: no auth/PII/payment/migration path; control change, see R2)
- [x] SAST (`ruff check --select S` on `scripts/deploy_gate.py` and `tests/unit/test_deploy_gate_494.py`: all checks passed; `conformance/test-deploy-shipped.py` S603/S607 at :44/:48 are pre-existing and identical at a2650e0, and `conformance/` is outside `make lint`; bandit is not in the lock; dispatcher: `conformance PASS: 33 test(s) ... 0 failing`)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #494 M1 (`./x`, `bash ./x`, mixed case, absolute) → scripts/deploy_gate.py:274-300, :319; tests/unit/test_deploy_gate_494.py:29-44 (`dot-slash`, `bash-dot-slash`, `mixed-case`, `absolute`)
- #494 M1 (a workflow dispatched by stem or `name:`) → scripts/deploy_gate.py:706-711, :318-321; tests/unit/test_deploy_gate_494.py:29-44 (`workflow-stem`, `workflow-name`)
- #494 M1 (`make <target>`, empty `Deploy commands:` fail closed) → scripts/deploy_gate.py:271, :313-316; tests/unit/test_deploy_gate_494.py:47-55; control :58-64
- #494 M2 (a forged pinned tree) → scripts/deploy_gate.py `_object`/`verified_blob`; tests/unit/test_deploy_gate_494.py:72-93
- #494 M3 (an unreadable base workflow exempts nothing) → scripts/deploy_gate.py:315; tests/unit/test_deploy_gate_494.py:96-108
- #494 R2 (only 100644/100755 at the pin) → scripts/deploy_gate.py:361-362; tests/unit/test_deploy_gate_494.py:111-132
- Not met: the fixture change weakens the existing safety-surface tests (B1).

## Risks queued
- **R1** scripts/deploy_gate.py:315 — the `files is None` branch (git cannot list the tree) has no test. With the
  check removed, all 12 tests in `test_deploy_gate_494.py` pass. Without the check, `_named_files` would raise
  `AttributeError` on `None.get`, and the gate would exit non-zero. So it still fails closed, but by a crash. A fake
  `git` that fails `ls-files` would hold it.
- **R2** docs/decisions.md D-229 clause 3 pre-answers the Escalate-NOW class `control-change` for #444, #456 and #457
  only. #494 is #444's follow-up and only tightens, but no ADR names it. The PR body should put this under
  "For the owner", or the owner should rule on it, before merge.
- **R3** The #444 review's R1 (`changed_since` runs `git diff` through the unverified object store, so a forged tree
  reachable from the reviewed head hides a change before any exemption is consulted) is unchanged by this range and
  still open.

## Round 2 — re-verification of B1 and R1 at 60afb68

**Reviewed head:** 60afb68b8605a058b2e325cb9a7a3bf34f9b87b6 (fix diff 7118f1b..60afb68: tests only, `tests/unit/test_deploy_gate_pin.py` and `tests/unit/test_deploy_gate_494.py`; `scripts/deploy_gate.py`, the conformance test, `pyproject.toml` and `requirements/` unchanged)
**Verdict:** MINOR (B1 and R1 closed; M1 stays, filed as #501)

I worked in a fresh worktree at `60afb68`. I used my round-1 venv, which is my own and was built from `requirements/dev.lock` with
`--require-hashes`, and the lock did not change in the range. I reinstalled the project editable from the new tree.
Tests ran by direct `pytest` (no `make check-fast`, so no `advisor.db` was needed). Mutations were restored by copy, and
`git status` was clean afterwards.

- **B1 closed.** `tests/unit/test_deploy_gate_pin.py:57-59`: `_installed` now declares `fly deploy`, which names no file in the fixture. The same mutant as round 1 (`"scripts/deploy_hosted_engine.sh"` dropped from `SAFETY_SURFACE`, scripts/deploy_gate.py:214-215), over `test_deploy_gate_pin.py`, `_444.py` and `_494.py`, gives `2 failed, 32 passed`. The two that fail are `test_a_deploy_script_is_code_even_byte_identical_to_the_pinned_commit` and `test_every_deploy_surface_is_code_even_byte_identical_to_the_pinned_commit[scripts/deploy_hosted_engine.sh]`, the same two that held it at a2650e0. The M3 test's brief also moved to `fly deploy` (tests/unit/test_deploy_gate_494.py:101), and the `not complete` mutant still fails it. No other fixture declares a safety-surface file as its deploy command. The control case at :58-64 declares one (by absolute path) only to assert that `scripts/tool.py` stays exempt.
- **R1 closed.** `tests/unit/test_deploy_gate_494.py:135-142`, `test_a_tree_git_cannot_list_exempts_nothing`. It loads the tree's own gate through `_module` (ROOT-relative), runs a control while git lists the tree (`is not None`), clears `_SURFACES`, and monkeypatches `_files` to `None`. With `files is None` dropped from :315, the test fails: `1 failed, 12 passed`. It fails by `AttributeError` rather than by the assertion, but either way the test goes red. The cache it leaves holds `None` for a unique tmp root, and no other test reads it.
- **Every round-1 mutant still fails a test** in `test_deploy_gate_494.py`: `no-decl`, `unread`, `complete`, `files-none` (now killed), `literal-named`, `no-abs`, `no-normpath`, `no-case`, `dispatch-old`, `mode-old`, `tree-unchecked`, `commit-tree-unchecked`, `surface-ignored`. None survives.
- **Clean run.** `test_deploy_gate_494.py`, `_pin.py`, `_444.py`, `_dispatch.py`, `_base_policy.py`: `144 passed`. `conformance/test-deploy-shipped.py`: `PASS: 7 cases`.
- **Commit hygiene.** `60afb68` carries `GP-Agent: claude-code` / `GP-Task: issue-494`, with no AI attribution.
- **Dispositions.** M1 is filed as #501 (open). R2 goes under "For the owner" in the PR body (author's commitment; the PR body is not in this range, so I have not seen it). R3 is #493 (open). Nothing new was found in the round-2 diff.
