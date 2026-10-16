---
record_type: review
id: enhancement-issue-289-golden-security
status: draft
seat: independent
process_version: v7.1
date: 2026-10-16
---
# Security Review: enhancement #289, a golden question set (branch `enhancement/issue-289-golden`)

**Reviewer:** Security-Reviewer subagent (`.claude/agents/Security-Reviewer.md`, read from `main`)
**Independent:** yes. I wrote none of this change's code, tests, fixtures or records.
**Seat and method:** a fresh Security-Reviewer seat, Claude model family (Opus). Own worktree detached at
`d67bc4d` under a `mktemp -d` directory with its own venv (`make install`), per D-174. The author tree was
read with git only and the owner's launchd service was not touched. No `advisor.db` was copied or built.
Policy read from `main` (`main:docs/security-invariants.md`, `main:docs/security-baseline.md`,
`main:permission-matrix.md`). I read the whole diff, then ran 14 fault injections in place. Each file was
restored byte-identical (md5 checked against a list taken before the first mutant). The worktree was removed
when the review was done.
**Date:** 2026-10-16
**Release range:** `d99d0e7..d67bc4d` (4 commits: `25daf9a`, `b223e16`, `79a01fe`, `d67bc4d`)
**Reviewed head:** d67bc4db7e9bf5c2209ebcc33c714ba87cb2d83c
**Risk tier:** LOW. The brief declares no HIGH paths. The range changes no product code: nothing under
`src/`, no app or Engine source, no route, no dependency, no CI, hook or gate-definition file. `make review-need`
fired because there is new gate-style code (`scripts/golden_questions.py --check`) that parses JSON. That JSON
is committed to the repository and comes from the project's own public, read-only `/v1` payloads. It is not
input an attacker controls at runtime.

## Verdict

PASS WITH FINDINGS: BLOCKING 0 · MAJOR 0 · MINOR 2 · NIT 2.

The fixtures carry no secret and no PII, and they reach the test bundle only, never the app. The deriver
only reads and writes JSON. It runs no code from its input, writes one file in the folder it is given, and
fails closed on the inputs it checks. The two MINORs are control-hygiene gaps, not exposures. The new
`.language-allow` entry is wider than it needs to be. And the deriver's error exit code has no test, so a
mutant that makes it pass on a broken snapshot survives the Python suite.

## Findings

### BLOCKING
- none

### MAJOR
- none

### MINOR
- **M1** `.language-allow:153` (`ios/.build/`), read by `scripts/check_records.py:1448` and `:1463`. L1
  walks the working tree (`root.rglob("*")`) and skips any path that starts with an allowlisted prefix. It
  calls `_skip(..., root=root)` without `pkg`, so the derived `.gitignore` exclusion (`_ignored()`,
  `check_records.py:713`) never applies to it, and `SKIP_DIRS` (`:708`) holds `build` but not `.build`.
  The entry is needed: probe F1 (entry removed after `swift test`) makes L1 report
  `ios/.build/arm64-apple-macosx/debug/ModelRankingEngine_ModelRankingEngineTests.bundle/Golden/golden-questions.json`.
  But it exempts more than that copy. Probe F2 put a Turkish `ios/.build/planted.md` in the tree with the
  entry present, and L1 stayed silent. Any file under `ios/.build/` is exempt whether or not it is tracked,
  so a file force-added there (`git add -f`) would never be read by L1. Today `git ls-files ios/.build` is
  empty, so nothing is hidden. This is a hand-kept entry beside a fact that `.gitignore:54` already holds
  (AGENTS.md section 3.5), which is why I rate it MINOR and not an exposure. **Remedy:** L1 should skip what
  git ignores and does not track. Pass the derived `_ignored(root)` set to L1's `_skip`, which is also what
  its docstring ("in a tracked file") claims. Then drop the `ios/.build/` entry. That is a gate-definition
  change, so it is the owner's (AGENTS.md section 3, Escalate NOW). Until then, an interim control is a
  one-line assertion that `git ls-files ios/.build` is empty, so the exempt prefix can never hold a tracked file.
- **M2** `scripts/golden_questions.py:211-213`. When the snapshot or the golden file cannot be derived from,
  `--check` returns 1, and nothing tests that exit code. Probe F7 changed `return 1` to `return 0` in that
  `except` branch and all 19 tests in `tests/unit/test_golden_questions.py` passed. Combined with an emptied
  `categories.json`, `--check` printed `golden-questions FAIL: the snapshot holds no categories, boards or
  models` and exited 0, and
  `test_the_committed_golden_file_is_as_the_snapshot_derives_it` (`tests/unit/test_golden_questions.py:112-113`)
  passed. The real script fails that test in the same state, so this is a missing negative test, not a live
  defect. The Swift test would still catch a snapshot it cannot decode, but `swift test` runs only on macOS
  and never in Python-only CI. **Remedy:** add a test that runs `main(["--check", "--folder", <copy with an
  emptied or unparseable categories.json>])` and expects 1, and one for a golden file that is not a list.

### NIT
- **N1** `tests/unit/test_golden_questions.py:169-170`. The check that the resource belongs to the test
  target only is a text pin that depends on target order. Probe F4 put `.testTarget(...)` first and moved
  `resources: [.copy("Golden")]` onto the `ModelRankingEngine` library target after it, and the test passed.
  The app is not exposed by this: the `.xcodeproj` never reads `Package.swift` (it uses
  `PBXFileSystemSynchronizedRootGroup`s for `ModelRanking/` and `UITests/` only, and no `EngineTests` or
  `Golden` reference is in `project.pbxproj`). Any JSON under `ios/ModelRanking/` is caught by
  `tests/unit/test_ios_client_contract.py::test_the_shipping_client_carries_no_canned_payload` (`CLIENT`,
  `:31`). Probe F3, the same move with the order kept, is killed. Remedy, optional: find the
  `resources:` argument inside the span of the `.testTarget(` call itself rather than comparing two indexes.
- **N2** `scripts/golden_questions.py:120` (`if not top3`) and `:197` (`not isinstance(entries, list)`). The
  Python tests do not reach either guard (probes F11 and F9 survive). Both stay fail-closed in practice. The
  Swift test asserts a non-empty `expectedTop3` (`ios/EngineTests/GoldenQuestionTests.swift:121`), and a
  non-list golden file raises an uncaught `AttributeError`, which exits non-zero. Remedy: one case each in
  `test_the_derivation_fails_closed`.

### PASS
- **Secrets and PII.** gitleaks over the range found no leaks, and neither did `make secrets` over the
  tree. The fixtures hold model ids, display names, vendors, prices, board positions, dates and the
  attribution and licence block the engine serves. There is no email address, no URL with a query string,
  and no token-shaped string other than board and category ids. `snapshot.json` names the public HTTPS host
  `model-ranking.fly.dev`, which the app already has as its hosted constant.
- **REQ-APP-001 holds.** The Golden folder is a `.copy` resource of `ModelRankingEngineTests` only
  (`ios/Package.swift:63-67`). No JSON was added under `ios/ModelRanking/`, and `project.pbxproj` is
  unchanged in the range. Removing the resource (probe F14, the pre-change `Package.swift`) fails the Swift
  build (`GoldenQuestionTests.swift:62`, `Bundle.module` missing), so it fails closed and does not skip.
- **No code from the input runs.** `golden_questions.py` uses the standard library only (`argparse`,
  `datetime`, `json`, `math`, `pathlib`, `sys`). It has no subprocess, eval, pickle, YAML or network call.
  It writes exactly one file, `<folder>/golden-questions.json` (`:221`), and only when `--check` is not given.
  The Swift test parses the fixtures with the same `Decodable` types the app uses for live payloads, routes
  with `TieredRouter(model: nil)` (no model and no network, under `OfflineTestCase`), and writes its report
  to the gitignored `build/` (`GoldenQuestionTests.swift:195`, `.gitignore:37`).
- **The derivation fails closed where it is tested.** Probes F5 (empty-snapshot guard off), F6 (`--check`
  comparison off), F8 (size bound off) and F10 (unknown-surface guard off) are each killed.
- **The set stays apart from the held-out sets (D-191).** The test's glob covers every tracked held-out
  file: all 21 `scripts/router_probe/*.json` sit at its top level, and the judgement sheet is read too.
  Probe F12 copied a held-out question into the golden set, and
  `test_the_golden_set_is_apart_from_the_held_out_sets` failed. Probe F13 pointed the glob at a missing
  folder, and the `len(pool) > 100` guard (`tests/unit/test_golden_questions.py:154`) failed, so the
  comparison cannot pass without reading anything.
- **Suites.** Python: `.venv/bin/python -m pytest -q -p no:cacheprovider` gave 3097 passed, 81 skipped, 0
  failed (the skips need `advisor.db` or the Epoch bundle). Swift: `swift test --filter GoldenQuestionTests`
  ran 3 tests with 0 failures and reported "golden set: 36 of 42 asserted questions pass (6 known misses),
  7 disputed, 49 in all".
- **Fault injection: 14 probes, each restored byte-identical (md5).** Killed: F1, F3, F5, F6, F8, F10, F12,
  F13, F14. Survived: F2 (M1), F4 (N1), F7 (M2), F9 and F11 (N2).

## Gates passed
- [x] Secret scan green: gitleaks on `d99d0e7..d67bc4d` reported no leaks, and `make secrets` on the seat tree
  reported no leaks found.
- [x] `make deps` (pip-audit, strict, four locks): no known vulnerabilities.
- [x] `make slopsquat`: PASS, 20 declared dependencies, 0 suspect. No new dependency: the Python imports are
  stdlib plus `pytest`, and the Swift imports are Foundation, NaturalLanguage and XCTest.
- [x] Default-deny preserved for new external surfaces: no route, endpoint or egress was added.
- [x] Permission matrix not violated: no destructive operation, and no CI, hook, guard or gate-definition file
  in the range (`git diff --stat` over `src`, `.github`, `.claude`, `.githooks`, `Makefile`, `pyproject.toml`
  and `requirements` is empty).
- [x] Prompt-injection hygiene: nothing in the fixtures is executed or followed, and no LLM reads them.
- [ ] Auth/PII checks: not applicable (no auth, PII, payment or migration path).
- [x] SAST: bandit and semgrep are not installed on this seat, so I reviewed the 227-line stdlib script by
  hand against the bandit classes (subprocess, eval/exec, pickle, YAML load, temp files, network). Nothing
  applies.

## Acceptance criteria evidence
- REQ-APP-001 (no fixture in the app) → `ios/Package.swift:63-67` (test target only);
  `tests/unit/test_golden_questions.py:165-171`; `tests/unit/test_ios_client_contract.py::test_the_shipping_client_carries_no_canned_payload`;
  probe F14.
- D-202 clause 2 (golden set, derived top 3, never hand-edited) → `scripts/golden_questions.py:215-218`;
  `tests/unit/test_golden_questions.py::test_a_hand_edited_top_three_fails_the_check_and_rederiving_restores_it` (F6 killed).
- D-191 (apart from the held-out sets) → `tests/unit/test_golden_questions.py:146-162` (F12, F13 killed).
- Fail-closed derivation → `scripts/golden_questions.py:161-167`, `:115-121`;
  `tests/unit/test_golden_questions.py::test_the_derivation_fails_closed`, `::test_an_empty_snapshot_is_an_error_not_an_empty_answer`
  (F5, F8, F10 killed; the gaps are M2 and N2).

## Risks queued
- **R1** M1's remedy is a gate edit to `scripts/check_records.py`, which is the owner's. If it is not made
  in this PR, file it as an issue and say in the PR body that `ios/.build/` is exempt from L1, tracked
  files included.
- **R2** The fixtures add about 560 KB of third-party benchmark data to the repository, including SWE-bench
  (CC-BY-NC-4.0) and Epoch AI. Their attribution and licence block travels with them (`boards.json`
  `credits`, `attributions`). This is the same payload the hosted engine already publishes, not the raw
  Epoch bundle that `.gitignore` keeps out. Whether committing it suits each source's licence is for the
  owner's licence review, not this seat (outside security scope).
