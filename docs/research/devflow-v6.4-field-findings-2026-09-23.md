---
record_type: field-findings
id: devflow-v6.4-field-findings-2026-09-23
status: draft
process_version: v6.4
date: 2026-09-23
---
# DevFlow v6.4 — field findings from upgrading an installation (model_ranking)

**For the DevFlow developer agent.** Defects in DevFlow v6.4's own machinery, found while
upgrading this project from v6.0 by `UPGRADING.md`'s method (D-161 in this project's
`docs/decisions.md`). The v6.0 findings are in `docs/research/devflow-v6-field-findings-2026-09-23.md`;
this record lists only what is new. Each item: what happens, how to reproduce it, a suggested fix,
and the project-side workaround.

## 1. `closure_check.py` ignores `process_version` — HIGH

**What.** `UPGRADING.md` promises that "earlier records are graded by the rules of the version they
declare". `scripts/wave_check.py` keeps that promise; `scripts/closure_check.py` does not, and
`make closes` is a prerequisite of v6.4's `check:`. Every closure report written before today's
template fails it: here all fifteen, M1-M15, including M15's, which declares `process_version: v5.0`.

**Reproduce.** Any installation with a closure report older than v6.4: `make closes`.

**Fix.** Grade a closure report by the version it declares, as `wave_check.py` does, and count a
report that declares none as history rather than as today's.

**Workaround here.** `closes` is not in this project's `check:`; `wave-check-all` already grades
the wave closes, and a closure report is checked at its own closure by `make closure-check`.

## 2. `UPGRADING.md`'s apply command fails whole on a tree that followed a v6.0 finding — MEDIUM

**What.** `git diff v6.0 v6.4 | git apply -3 --exclude='.github/workflows/*'` refuses the entire
diff (`src/__init__.py: does not exist in index`) in a project that removed `src/__init__.py`, which
the v6.0 findings (A1) recommend. It refuses again on a deletion of a file the project changed
(`note.txt`, `docs/handovers/*`).

**Fix.** Name the `--exclude=` escape in `UPGRADING.md` §2, with the files a project is expected to
own (`src/`, the product's tests, anything the project wrote under a shipped name).

## 3. `make secrets` reads, and prints, untracked files — MEDIUM

**What.** `gitleaks detect --source . --no-git -v` scans the whole working tree, untracked and
ignored files included, and `-v` prints each match. A developer's local notes holding a key fail
the gate, and their secrets land in the terminal, in an agent's context, and in any log of the
pre-push hook, which v6.4 now runs on every push.

**Fix.** Scan what can be pushed: `gitleaks git` over the range being pushed, or the tracked tree
(`git ls-files`), with `--redact`.

**Workaround here.** The pre-push hook (`make hooks`) is left for the owner to turn on; the secret
scan runs on a clean export of the branch.

## 4. `slopsquat_check.py` imports `tomllib` at the top — LOW

**What.** The module imports `tomllib` unconditionally and again inside a `try` whose `except
ImportError` prints "needs Python >= 3.11". On Python 3.10 the top import fails first, so the
message it was written to print never appears. A project whose `ruff` covers `scripts/` also gets
F401 and B904.

**Fix.** Drop the top-level import; `raise SystemExit(2) from None`.

## 5. A project's own `check_fast.py` must speak `--plan` — LOW

**What.** `conformance/test-check-fast.py` runs `scripts/check_fast.py --plan`. A project that
adopted `check-fast` before v6.4 shipped it (this one did, after the owner's other project) fails
the test until it adds the flag. Worth one line under "What changed for you".
