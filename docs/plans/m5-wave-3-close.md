# Wave-Close Checklist — M5 Wave 3

> Filled from `docs/wave-checklist.template.md`. Scope: M5 plan §3 W3 — apply the delegated
> two-category board decision, ingest DeepSWE at `high`, and measure coverage and freshness through
> the real selection path.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded; new board ingestion and input parsing make W3 HIGH | `docs/plans/m5-plan.md` §4 records W3 HIGH | ✅ |
| 2 | Per-agent implement → test → self-review → fix loop ran | checkpoint `62a9166`, gate-fix commit `8fa555d`; focused 48 passed and full 247 passed / 5 expected skips in `docs/reviews/m5-wave-3-tester.md` | ✅ |
| 3 | HIGH review: separate fresh Code Reviewer and Tester; two facts countersigned | Code Reviewer PASS `docs/reviews/m5-wave-3-review.md` and Tester PASS `docs/reviews/m5-wave-3-tester.md`; both independently countersigned the real 50→49/1-unknown ingest and the coding 5 + agentic 6 with overlap/union 6 | ✅ |
| 4 | HIGH pulled-forward security/data-boundary pass | local allowlisted file-only source, URL rejection, mandatory provenance/verification clock, strict shape and finite score parsing, release-date isolation, unknown-effort skip/count, source-specific atomic replacement, and selected-row health are covered in both PASS records | ✅ |
| 5 | Fault injection on load-bearing behaviors | Tester killed 2/2 manual mutants: release date promoted to evidence date and unknown effort defaulted to `high`; both RED, then in-place byte-identical SHA-256 restore; `docs/reviews/m5-wave-3-tester.md` | ✅ |
| 6 | Every touched acceptance criterion has a live-entry citing test | REQ-ING-010/011b, CAN-005, REC-011, SUB-007, REC-012 and inherited ING-004 are mapped to live workflow/CLI tests in both W3 PASS records | ✅ |
| 7 | New/changed security invariants have negative tests | `tests/unit/test_deepswe_workflow.py` rejects missing/non-local boards and invalid clocks, preserves release-date isolation, counts unknown effort, and proves an ingest failure preserves the prior source working set | ✅ |
| 8 | No checkout/restore on uncommitted work | Tester mutated only an exact-ref disposable archive, reversed patches in place, and verified SHA-256 byte identity; original repo remained read-only | ✅ |
| 9c | Shared security invariant producer enumeration | N/A — no auth, tenancy, or money invariant changed; DeepSWE client/parser/store/reconcile/selection/coverage/JSON producers and citing tests are enumerated in both PASS records | WAIVED — domain not touched |
| 9b | Scope and checkpoint | planned W3 delivered in `de7cb0e..8fa555d`: separate `agentic-coding` DeepSWE-high ingestion, real 6/10 coverage, 0/0/6/4 selected-row health, source telemetry and wording update; attribution and carried ledger remain W4 as signed; checkpoint `62a9166` exists | ✅ |
| 9a | Economy | 8 files, +590/−6 exceeds the advisory ~400-line valve because the 264-line real-bundle acceptance suite and 241 lines of measurement/review evidence dominate; within signed W3 ≈70k / M5 ≈500k budget | ✅ — variance recorded |
| 9 | **RUN LINE — gates run:** exact-ref real-bundle focused 48 · full pytest 247 pass/5 skip · 91% coverage · ruff · black · mypy · records/selftest/install/pin · 2 fault injections · Code Review · Tester review · `make wave-check` · **gates SKIPPED:** five opt-in network contracts (existing expected skips; no network), mechanical mutation runner (not wired; HIGH advisory only), auth/tenancy/money sweep (N/A) · **tokens/cost:** within signed M5 budget · **outcome: shipped** | This row; exact commands, outputs and hashes in `docs/reviews/m5-wave-3-tester.md` | ✅ |

Escaped-blocker tripwire: the fresh Code Review found two repository-gate defects (missing language
allowlist records and trailing Markdown spaces). Both were fixed before the final Code Review PASS
and independent Tester PASS; no blocker escaped the wave and no MINOR remains.

Filled by: `Codex` · Date: `2026-08-16` · Wave commit range: `de7cb0e..8fa555d`
