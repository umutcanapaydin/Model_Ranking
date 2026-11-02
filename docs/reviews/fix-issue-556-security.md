---
record_type: review
id: fix-issue-556-security
status: draft
seat: independent
process_version: v7.3.1
date: 2026-11-02
---
# Security Review — fix-issue-556

**Reviewer:** Security-Reviewer subagent (light mode; `make review-need` says `security`: a policy edit of `scripts/deploy_gate.py`, #283)
**Independent:** yes. This seat wrote none of the range: it read the code and probed it in its own detached work tree (`wt-sec-556` at 7f35a71) with its own venv.
**Date:** 2026-11-02
**Release range:** 9ec7a46..7f35a71
**Reviewed head:** 94265ca95cb116b3eaeecc460d78d107be3abec5
**Risk tier:** MEDIUM. The brief declares no HIGH paths (`docs/project-brief.md:110`), but the range edits a fail-closed deploy control (D-239), so the review covers the control's fail direction in full. No auth, PII, payment or migration path is touched, so no senior-review line is owed.

## Verdict
PASS

The fix does not loosen D-239. What it refuses, and when it fails closed, is unchanged. The one new output, a PASS evidence line, is never what decides whether the check fails. One wording defect (**M1**): the line can say a workflow was "read" when no copy of it exists.

## Findings

### BLOCKING
- none

### MINOR
- **M1** `scripts/deploy_gate.py:1089`, `:1286-1289` (with `:1664`): the PASS line says `<name> read` for every name `deploy_workflows` returns. That includes a dispatched name no file answers to (`files |= dispatched - {...}` at `:1664`), and that name has no text to read. Scenario, probed: a brief declaring `gh workflow run ghost` with no `ghost.yml` in the tree or at a base prints `deploy-check: workflows: ghost read, 0 run command(s), no start of a file without its name (D-239)`, and `deploy-check PASS`. The outcome matches the pre-fix gate (D-239 found nothing before too, and whether such a dispatch should refuse is outside this range). The defect is in the line. #556 exists so that a PASS carries true evidence, and this line claims a read that did not happen. It is not exploitable: the line never turns a FAIL into a PASS. Remedy: name only the workflows that have text, and list a dispatched name with no copy separately (for example `ghost: no copy in the tree or at a base`). Add a test that pins that wording.

### PASS
- **Q1. `dict.fromkeys` de-duplication cannot change what D-239 refuses** (`scripts/deploy_gate.py:1091`). Everything read per text is a function of `(name, text, root, files)` and nothing else: `_run_values` (`:869-895`) is pure over `text`; `_run_commands`/`_unnamed_shapes` read only the words; `_workflow_names(root, text, files)` and `_linked(root, path)` read the same root and the same `files` for every copy. Two copies that compare equal as `str` therefore yield identical findings. Before the fix those duplicates were already removed by `list(dict.fromkeys(found))` (`:1103`), which keeps first-occurrence order. So for any sequence (say `[A, B, A]`) the old list `fA+fB+fA` de-duplicates to the same list the new code builds as `fA+fB`. Copies whose bytes differ but whose strings are equal do occur: the tree copy goes through `read_text` with universal newlines (`:1618`), and both reads replace invalid UTF-8 with U+FFFD (`:1618`, `:1630`). Those cases are harmless, because the pre-fix gate also analysed only the decoded `str`. No byte-level difference was ever visible to D-239, so skipping an equal string hides nothing. Probes: P1 (base copy `scripts/*.sh`, tree copy clean, on a branch) → exit 1, `1 start(s)`; P2 (tree copy `$X`, base copy clean) → exit 1; P5 (identical bad copies, two shapes) → exit 1, `2 start(s)`, both named once. The 57 tests of `test_deploy_gate_549.py`, `test_deploy_gate_base_policy.py` and `test_deploy_gate_556.py` pass at 7f35a71. Their refusal cases run on `main`, where tree and base are identical, which exercises the de-duplication path.
- **Q2. The pass line cannot be printed for a check that did not run, and it never decides a verdict.** The branch is chosen by `unnamed`, the return value of `unnamed_starts`: `None` → the fail-closed refusal (`:1275`); non-empty → the refusal (`:1279`); `[]` → the new line (`:1285-1289`). The line's `why` is the literal `None`, the same pass the old code gave by appending nothing. `_UNNAMED_READ` is only read inside the `[]` branch. It is written at `:1104` in the same block as `_UNNAMED[key] = list(...)` (`:1103`), and never on the `None` path (`:1085-1087`), where the function returns before reaching it. Both caches use one key, `str(root)` (`:1081`, `:1286`). A stale or missing entry can only change the wording of a line whose `why` is already `None`: it cannot turn a FAIL or a `None` into a pass. Both consumers, `_judge` (`:1721-1722`) and `check` (`:1734-1736`), act only on a truthy `why`. The new summary starts with `workflows:`, not `release note`, so the `HOW_TO_CLOSE` logic is unaffected. No other caller indexes `verdicts()` by position (grep: `scripts/` has only these two; the tests index `[0]`, the policy line, which is still first).
- **Q3. The base-policy assertions are not weakened** (`tests/unit/test_deploy_gate_base_policy.py:84`, `:121`). They remain exact list equality over every `why`, now one element longer. Any non-None `why` still fails them, and so does any missing or extra line. They now also require that the D-239 line is present and passes, which is strictly more than before.
- **Q4. Nothing else in the range loosens the gate.** The diff (`git diff 9ec7a46..7f35a71`) touches `scripts/deploy_gate.py` (+16/-2, all reviewed above), two test files and `docs/process-log.md`. It makes no change to `.github/`, `.claude/`, `.githooks/` or `Makefile`, adds no new import in `scripts/`, and does not change the fail-closed condition (`:1085`), `_workflow_texts` (`:1608-1631`), `deploy_workflows` or the refusal text.
- Secret hygiene: `make secrets` (gitleaks) "no leaks found" on the reviewed tree. The diff holds no credential or high-entropy string.

## Gates passed
- [x] Secret scan green (`make secrets` at 7f35a71: no leaks found)
- [x] `make deps` (pip-audit) green: no dependency change in the range (no edit to `pyproject.toml` or `requirements/`), so not re-run
- [x] `make slopsquat` green (`slopsquat PASS: 20 declared dependency(ies), 0 suspect`); the range adds only stdlib and test-local imports
- [x] Default-deny preserved for new external surfaces: no new surface
- [x] Permission-matrix not violated: no destructive operation, no CI/hook edit
- [x] Prompt-injection hygiene: not applicable (no untrusted text reaches an LLM)
- [x] Auth/PII checks + human review trigger: not applicable (no auth/PII/payment/migration path)
- [x] SAST: no new sink. The added code only counts and formats strings (`:1089-1104`, `:1285-1289`)

## Acceptance criteria evidence (PASS verdict requires file:line per criterion)
- #556 "one PASS line naming the workflows read and the count of run commands" → `scripts/deploy_gate.py:1284-1289`; tested at `tests/unit/test_deploy_gate_556.py:26` (2 commands → `2 run command(s)`), `:34` (1 → `1`), `:42` (no dispatched workflow). The count's wording is subject to **M1** and **R1**.
- D-239 refusals unchanged → `scripts/deploy_gate.py:1091`, `:1103`; probes P1, P2, P5 above; `tests/unit/test_deploy_gate_549.py` green.

## Risks queued
- **R1** `scripts/deploy_gate.py:1091`, `:1094`, `:1618`: the count sums run commands over every *distinct* copy (tree, merge-base, tip), and copies that differ only in line endings count as distinct. The tree copy is newline-normalised by `read_text` while the base copy keeps its `\r\n`. Probe P4: a CRLF-committed `release.yml` with one run command prints `2 run command(s)`. This matches the process log's own warning that "the first measured number here was wrong". It is evidence accuracy, not a loosening. Remedy: normalise newlines before the `dict.fromkeys`, or say in the line that the count covers each copy read.
- **R2** `scripts/deploy_gate.py:1286`: the fallback `([], 0)` for a missing `_UNNAMED_READ` entry prints "no dispatched deploy workflow". That claims a fact rather than saying the read was not recorded. The production path cannot reach it (both caches are written together at `:1103-1104`), but a caller that clears only `_UNNAMED` (as `tests/unit/test_deploy_gate_549.py:199` does) can leave the two out of step. A neutral default (`workflows read: not recorded`) would fail toward honesty.
- **R3** `tests/unit/test_deploy_gate_556.py:40`: the "control" asserts a property of the helper string `_brief("fly deploy")`, not of the brief the fixture actually committed (`tests/unit/test_deploy_gate_pin.py:59`). If the fixture's brief later gains a dispatch, the control stays green while the test reads a different case. Read the committed brief instead. This is test quality, for the Code-Reviewer and Tester seats.

## Round 2

**Date:** 2026-11-02 · **Range re-read:** 7f35a71..94265ca95cb116b3eaeecc460d78d107be3abec5 (`scripts/deploy_gate.py` +14/-4, `tests/unit/test_deploy_gate_556.py` +13/-1, `docs/process-log.md`, this file) · **Verdict:** PASS (replaces MINOR above)

Re-verified in the same seat's work tree, detached at 94265ca with its own venv. The 58 tests of `test_deploy_gate_549.py`, `test_deploy_gate_base_policy.py` and `test_deploy_gate_556.py` pass. The probes P1 to P5 were re-run unchanged, and an in-process probe covered R2 and the fail-closed path.

- **M1 — fixed.** `scripts/deploy_gate.py:1293-1297` splits the names into those with text (`read`) and those without (`absent`), and prints the latter as `; dispatched with no copy to read: <name>`. Probe P3 (`gh workflow run ghost`, no `ghost.yml`) now prints `workflows: no dispatched deploy workflow read; dispatched with no copy to read: ghost, no start of a file without its name (D-239)`. The word "read" is no longer attached to `ghost`. The fix is pinned by `tests/unit/test_deploy_gate_556.py:46-54`, which asserts both `dispatched with no copy to read: ghost` and the absence of `ghost read`.
- **R2 — fixed.** `scripts/deploy_gate.py:1288-1290`: a missing `_UNNAMED_READ` entry now prints `...; what was read is not recorded`, not a claimed fact. In-process probe: `unnamed_starts(root)` → `[]`, then `_UNNAMED_READ.clear()`, then `verdicts(root)` gives `(None, 'workflows: no start of a file without its name (D-239); what was read is not recorded')`. With `_UNNAMED[root] = None` it gives a truthy `why`, `workflows: cannot be read for a file started without its name`, so the fail-closed path is unchanged (`:1275`).
- **R3 — fixed.** `tests/unit/test_deploy_gate_556.py:40-41`: the control now reads the brief the fixture committed (`repo.root / "docs" / "project-brief.md"`), not the helper string.
- **R1 — filed as #570.** Unchanged in code. Probe P4 still prints `2 run command(s)` for one CRLF-committed command. This is evidence accuracy, not a loosening.
- **Fail direction of the new code.** The new branch is still reached only when `unnamed == []` (`:1275`, `:1279`), and every summary it builds carries `why = None`, exactly as round 1 found. P1, P2 and P5 still refuse (exit 1). The added `_workflow_texts(root)` call (`:1293`) only labels names. It is the same reader `unnamed_starts` already ran, so it adds no new failure mode. An `OSError` there would raise out of `check`/`judge` with a non-zero exit, never a silent pass.
- **R4 — queued, not blocking.** `scripts/deploy_gate.py:1293`: the read/absent split comes from a second read of the workflows, not from the read that was counted (`:1089-1104`). A workflow file created or removed between the two reads could be labelled differently from what was actually counted. The cost is wording only, the same class as M1, and needs a change to the tree during one `make deploy-check`. Remedy, if wanted: record the names that had text in `_UNNAMED_READ` at `:1104` and drop the second read.
