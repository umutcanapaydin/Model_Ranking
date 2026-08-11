# Wave-Close Checklist — M1 Wave 3 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

Wave scope: canonical registry + reconciliation + median prices + coding ranking + export (m1-plan.md §3 W3).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded | m1-plan.md:4 — LOW; curated-rule input-parsing → reviewer regex audit + regression suite | ✅ |
| 2 | Per-agent dev-test loop | pytest 52 passed + 3 env-gated; live contracts ×3 PASS; ruff + black clean; mypy strict clean on src AND tests | ✅ |
| 3 | Review per tier (LOW → ONE combined, fresh eyes) | docs/reviews/m1-w3-review.md — first verdict **FAIL (2 BLOCKING)**; both fixed same-wave; countersign: reviewer verified false matches + tie nondeterminism by execution | ✅ (post-fix) |
| 4 | *(plan-tag)* HIGH slice security pass | N/A — no HIGH tag on W3 | WAIVED (N/A, plan) |
| 5 | Fault-injection (break → RED → md5 revert) | F1 nano rule disabled: 2 tests RED; F2 median→min: 3 tests RED; reverts md5-identical; suite green after | ✅ |
| 6 | Criteria have citing tests through live entry | REQ-CAN-001: test_registry.py::test_reconcile_maps_and_counts_drops (+dropped_names); REQ-CAN-002: ::test_variant_never_leaks_into_parent, ::test_sibling_variants_never_leak_into_parent_families, ::test_rule_order_variants_precede_parents, ::test_date_suffixed_alias_is_dropped_not_misversioned; REQ-CAN-003: test_rank.py::test_median_not_min_beats_outlier, ::test_even_count_median_is_middle_mean; REQ-RANK-001: ::test_ranking_takes_best_score_and_its_harness, ::test_model_without_price_is_excluded (de-vacuoused), ::test_tied_best_scores_pick_deterministically; REQ-RANK-002: ::test_export_csv_and_json_identical_rows, ::test_export_empty_ranking_does_not_crash | ✅ |
| 7 | New security invariants + NEGATIVE test | none new (no authz/secrets surface); conservative-drop invariant has negative tests (unlisted siblings must return None) | ✅ |
| 8 | No git checkout/restore on uncommitted work | attested — in-place edits only, md5-verified fault reverts | ✅ |
| 9c | Invariant hardening producer list | N/A | WAIVED (N/A) |
| 9b | Scope & checkpoint | Planned W3.1-W3.4 delivered; extra (review BLOCKING fixes): 5 new canonical models (gpt-5-pro, gemini-2.5-flash-lite, grok-4-fast, claude-4.1-opus), 12 tightened lookaheads, dropped-NAMES in ReconcileReport, deterministic tie-break (ROW_NUMBER), mypy-on-tests now green. Deferred: none. Owner checkpoint commit `wip(m1-w3)` OWED (repo pending — carried) | ✅ (commit OWED) |
| 9a | Economy | Diff ≈ 420 added lines — WARN: slightly over the ~400 guideline (variance: review BLOCKING fixes added rules+tests; accepted, not blocked per V3C-85) | ✅ (WARN noted) |
| 9 | Run summary + skipped ledger | gates run: pytest, ruff, black, mypy(src+tests), fresh-eyes review (FAIL→fix→re-verify), fault-injection ×2, live contracts ×3 · SKIPPED: make-check-via-venv + gitleaks (host-side, carried) · tokens: ≈95k · outcome: shipped | ✅ |

**Review disposition:** BLOCKING-1 (mypy on tests) fixed — typed helpers, meta annotation. BLOCKING-2 (real-alias false matches) fixed — verified case-by-case against the reviewer's alias list, all green. MINOR-3 tie-break fixed with window function + test. MINOR-4 exclusion test made real (score-only model seeded). MINOR-5 scores-NULL + dropped_names asserted. MINOR-6 even-median + empty-export tests added. Accepted w/o change: CSV ""-vs-JSON-null rendering (documented; consumers read JSON as source of truth). Carried to W4/closure: median weights every (alias,source) row equally — revisit when multi-source pricing lands (M2); registry drop-list review is now data (`dropped_names`) — closure walks it.

Filled by: Claude (lead agent) · Date: 2026-08-10 · Wave commit range: pending owner's first commit
