# Wave-Close Checklist — M2 Wave 1 (OpenRouter pricing + median-of-medians)

| # | Check | Evidence | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier | m2-plan:12 LOW; input-parsing → guards + review | ✅ |
| 2 | Dev-test loop | pytest 104p+5s; ruff/black/mypy(src+tests) clean | ✅ |
| 3 | Review (LOW → ONE combined; batched W1+W2 pair, separate verdicts — economy variance, ledgered) | docs/reviews/m2-w1w2-review.md — W1 PASS, 2 MINOR applied | ✅ |
| 4 | HIGH slice security | N/A | WAIVED (N/A, plan) |
| 5 | Fault-injection | F1 median flattened → RED (outlier-source test); md5 revert OK | ✅ |
| 6 | Criteria cite tests | REQ-ING-005: test_openrouter_ingest.py (7 tests incl. price edges); REQ-ING-006: test_rank.py::test_median_of_per_source_medians_beats_outlier_source; REQ-ING-004: replace+independence tests | ✅ |
| 7 | Security invariants | zero/bool/neg price → None (+tests); IntegrityError→SourceError on pricing path | ✅ |
| 8 | No git checkout/restore | attested; in-place md5 reverts | ✅ |
| 9c | Producer list | N/A | WAIVED (N/A) |
| 9b | Scope & checkpoint | W1.1-1.3 delivered + review fixes (edge tests, keep-first comment). Checkpoint commit: OWNER WAIVER (m2-plan amendment 1) | ✅ |
| 9a | Economy | ~230 lines (≤400); ≈55k tokens | ✅ |
| 9 | Run summary | gates: pytest/ruff/black/mypy/review/fault ×1 · SKIPPED: live contract (sandbox network — runs in CI, plan §0) · outcome: shipped | ✅ |

Filled by: Claude · 2026-08-11 · commit range: milestone-boundary (owner waiver)
