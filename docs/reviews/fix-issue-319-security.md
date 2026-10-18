---
record_type: review
id: fix-issue-319-security
status: draft
seat: independent
process_version: v7.2
date: 2026-10-18
---
# Security Review — fix-issue-319

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`), light mode. `make review-need` routed this change to `security` because it edits a policy script (#283).
**Independent:** yes. I wrote none of this range's code, tests or records.
**Date:** 2026-10-18
**Release range:** `586537e53a8ebb57a6a14cebf345399a236be320..c2383178241fecc12777626716fdaace328bf2ad` (2 commits, branch `fix/issue-319-policy-scripts`). Issue #319; owner approval: D-209 clause 5 (`docs/decisions.md`).
**Reviewed head:** c2383178241fecc12777626716fdaace328bf2ad
**Risk tier:** MEDIUM. This is gate and policy code (`scripts/review_need.py`). The brief declares no HIGH paths (`Paths that make a change HIGH:` is `none`), and the change touches no auth, PII, payment or migration path, so no senior review is triggered.

I reviewed it in a detached worktree at the head, with its own venv (`make install`). Probes ran in throwaway repositories. The mutants were planted in the worktree and reverted; `git status` was clean afterwards.

## Verdict
PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 4 · NIT 3.

**Nothing is looser than the old list.** The three policy modules still always count: `found = set(POLICY_SCRIPTS)` (`scripts/review_need.py:152`) is unconditional, `changed` is read with `-z` so it matches exactly, and the `.md` filter cannot drop a `.py`. Readers are the union of the base and the end, so the change under review can only add readers, never remove one:
- a reader the change renames still routes to `security` (probe A), and so does one it deletes (B);
- a reader stripped of its token routes to `security`, because the base still names it (C);
- a new reader routes to `security`, because the end names it (D2).

Both new git calls fail closed. A failing `git grep` raises `RuntimeError` (`:156-157`), and a failing `git diff -U0` raises `CalledProcessError` through `git()` (`:113`). `main` catches both and exits 2 (`CANNOT RUN`); I checked both with a `git` shim (probes FC).

On this repository the derived reader set is exactly what a Python scan of the same directories finds: `bash_guard.py`, `brief_fields.py`, `closure_check.py`, `deploy_gate.py`, `review_need.py`, `wave_check.py`. Performance is not a concern: `make review-need RANGE=HEAD~5..HEAD` takes 0.50 s, and the full range takes 0.49 s.

The findings are about the new derivation's own reach. None of them is a regression against the hand-kept list. M1 is the one to fix before merge: it is a one-flag change, and it is the case where the change under review steers its own routing.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/review_need.py:166` (`policy_lines`): the change under review can blind the new line scan with its own `.gitattributes` (base-pinned policy, AGENTS.md §5). `git diff` reads attributes from the checked-out tree, which is the change's head. A change that adds `Makefile -diff` (or `docs/plans/* -diff`) beside a rewrite of the `review-need` recipe (or a plan's `security-globs:` line) makes git print `Binary files differ`. No `+` or `-` line is left to scan, and light mode routes it to `none`. The same edit without the attribute routes to `security` (probe O1 against O2 and O3).
  Fix: `git("diff", "--text", "--no-textconv", "--no-ext-diff", "-U0", "--no-renames", rng, ...)`, plus a test that commits `.gitattributes` with `Makefile -diff` next to a recipe edit.
  Reproduce: in a throwaway repo with a light brief and `Makefile` = `review-need:\n\tpython3 scripts/review_need.py\n`, commit `.gitattributes` = `Makefile -diff` and change the recipe line. Then run `python3 <worktree>/scripts/review_need.py --range HEAD~1..HEAD`, which prints `review-need: none`.
- **M2** `tests/unit/test_review_need_derived_policy.py`: the tests do not pin half of the derivation. Six mutants of `scripts/review_need.py` survive all 14 tests (in `test_review_need_derived_policy.py` and `test_review_need_base_policy.py`) and `conformance/test-review-need-mode.py`:
  - (b) reading readers at the base only;
  - (c) reading them at the end only, which drops exactly the "strip the token to hide" case C;
  - (d) ignoring `git grep` errors (`if grep.returncode not in (0, 1)` → `if False`), so the fail-closed path is untested;
  - (e2) dropping `.githooks` from `POLICY_READER_DIRS`;
  - (g) scanning only added lines (`line[:1] in "+-"` → `== "+"`), so deleting a `security-globs:` line is untested;
  - (k) dropping `brief_fields.POLICY_FIELDS` from the tokens.
  Fix: add one test for each of these: a reader whose token the change removes, a new reader added in the range, a `git` shim on `PATH` that fails `grep` (expect exit 2), a `.githooks/` reader, a plan whose `security-globs:` line is deleted, and a script naming `Deploy commands`.
  Reproduce: apply each mutant with `sed`, then run `.venv/bin/python -m pytest -q -n0 tests/unit/test_review_need_derived_policy.py tests/unit/test_review_need_base_policy.py`, which prints `14 passed`.
- **M3** `scripts/review_need.py:154,167` (quoted paths): `git grep -l` without `-z` prints non-ASCII paths C-quoted (`HEAD:"scripts/caf\303\251.py"`), so they never equal the `-z` names in `changed`. `policy_lines` also skips quoted `--- "a/..."` headers, so `current` stays `""` (or stays on the previous file). As a result, a reader at `scripts/café.py` that names `deploy_gate` routes to `none` (probe H), and so does `docs/plans/mé-plan.md` changing its `security-globs:` (probe I).
  Fix: `git grep -z -l` and split on `\0`. For the diff, take the file list from `git diff --name-only -z` over `LINE_POLICY_PATHS`, then diff each file on its own.
  Reproduce: `git -C <tmp> grep -l deploy_gate HEAD -- scripts` prints the quoted name.
- **M4** `scripts/review_need.py:90` (`POLICY_READER_DIRS`): the directories the derivation scans are themselves a hand-kept list (AGENTS.md §3.5). In light mode these route to `none`:
  - an edit to the policy's own conformance tests (`conformance/test-review-need-mode.py`, `test-deploy-shipped.py`, `test-milestone-security.py`; probe E), which touches "security-invariant test modified" (AGENTS.md §3, Escalate NOW);
  - a policy-naming recipe in `stack.mk` (G);
  - `.claude/settings.json` (K);
  - a reader in a new top-level directory (F).
  None of these was covered before, so this is not a loosening.
  Fix: derive the scanned set from `GATE_CODE` (scripts/, conformance/, .claude/, .githooks/, stack.mk), so one list decides both "gate code" and "where readers live", with the Makefile kept line-based.
  Reproduce: `git grep -l -E 'review_need|deploy_gate|brief_fields|review-need|deploy-check|security-globs' HEAD -- conformance stack.mk .claude/settings.json`.

### NIT
- **N1** `scripts/review_need.py:88` (token matching is name-based): a reader that builds a name (`__import__('review'+'_need')`, probe D) is not seen. Neither is one that spells a field label in another case (`'working mode'`, probe J; `brief_fields.field` matches case-insensitively, but `POLICY_PATTERN` does not), nor a reader stored as an LFS pointer. Consider `-i` for the field-label tokens. Separately, and outside this change: `review_need.py` itself runs from the change's tree (`make review-need`, and `wave_check.py:840` via `Path(__file__)`), so a change to the derivation is judged by the derivation it ships. The hard-coded `POLICY_SCRIPTS` makes such a change a policy edit only in versions that keep that line.
  Command: `grep -n "review_need.py" Makefile scripts/wave_check.py`.
- **N2** `scripts/review_need.py:154`: the `git grep -E` pattern is `re.escape` output (`review\-need`, `Working\ mode`). In POSIX ERE, a backslash before an ordinary character is undefined. It works with Apple Git 2.50, and it matched a Python scan of the whole tree, but `git grep -F` with one `-e <token>` per token is portable and needs no escaping.
  Command: `python3 -c "import sys; sys.path.insert(0,'scripts'); import review_need as r; print(r.POLICY_PATTERN.pattern)"`.
- **N3** `scripts/review_need.py:262` (pre-existing, outside #319): the untrusted-parser scan (`git diff -U0 ... ` over added lines) and the product-line count (`numstat` `-` for binary files) have the same `.gitattributes -diff` blind spot as M1. The `--text` fix in M1 belongs on that call too. File it if M1's fix does not cover it.
  Command: the M1 reproduction with `src/x.py -diff` and an added `json.loads(` line.

### PASS
- `found = set(POLICY_SCRIPTS)`: the #283 trio counts unconditionally (a mutant dropping it is killed).
- Base ∪ end reader set: a rename, a delete or a token strip cannot hide a reader (probes A, B, C), and a new reader is caught (D2).
- Fail-closed behaviour on both new git calls (probes FC: exit 2, `CANNOT RUN`).
- `--no-renames` on both diffs: a rename appears as delete plus add, so the old path still matches a base reader.
- Every `subprocess.run` uses an argument list, with no shell and no interpolated shell string. The pattern is passed as one argv element. `ruff --select S` is clean (S603/S607 are already allowed for this file in `pyproject.toml:128`).
- No new third-party import. The new test imports only `__future__`, `pathlib` and the sibling helper.

## Gates passed
- [x] Secret scan green (`make secrets` on c238317: `no leaks found`)
- [x] `make deps` (pip-audit) green: `No known vulnerabilities found`
- [x] `make slopsquat` green: `20 declared dependency(ies), 0 suspect` (no new import)
- [x] Default-deny preserved for new external surfaces: no route, endpoint or network path in the range
- [x] Permission-matrix not violated: no `.github/workflows`, `.claude/` or `.githooks/` edit, and no destructive operation in either commit
- [x] Prompt-injection hygiene: n/a, since nothing fetched or untrusted is interpreted. M1 is the base-pinned (change-steers-policy) instance of this class.
- [ ] Auth/PII checks + human review trigger: n/a (not HIGH; no auth/PII/payment/migration path)
- [x] SAST: `ruff check --select S scripts/review_need.py` reports `All checks passed!` (bandit is not installed in the venv); `conformance/run-all.py`: `33 test(s) ... 0 failing`

## Acceptance criteria evidence
- #319 / D-209 cl.5: a script that reads the policy is a policy script → `scripts/review_need.py:149-159` (`policy_readers`); test `tests/unit/test_review_need_derived_policy.py:24-31` (`wave_check.py`, `.claude/hooks/bash_guard.py`)
- #319: a Makefile line naming a policy reader is a policy edit, and an unrelated line is not → `scripts/review_need.py:162-173` (`policy_lines`); test `tests/unit/test_review_need_derived_policy.py:34-46`
- #319: a plan's `security-globs:` line is a policy edit → `scripts/review_need.py:91` (`LINE_POLICY_PATHS`); test `tests/unit/test_review_need_derived_policy.py:49-54`
- #283 kept: the three modules always count → `scripts/review_need.py:152`; tests in `tests/unit/test_review_need_base_policy.py` (mutant (a) killed)

## Risks queued
- **R1** M4's scope question (should every `GATE_CODE` path that names a policy token count as a policy edit, or only the scanned directories?) is the owner's call under D-209. If it is not fixed here, file it as an issue.
- **R2** N3, the same `.gitattributes` blind spot in the parser signal, is pre-existing. If M1's fix does not cover that call too, file it.
