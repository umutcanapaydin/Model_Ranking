# Wave-Close Checklist — M1 Wave 2 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

Wave scope: SWE-bench Verified + Aider polyglot ingestion (m1-plan.md §3 W2).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded | m1-plan.md:4 — LOW; input-parsing diff → parser guards (bool/None/non-list) + reviewer pass | ✅ |
| 2 | Per-agent dev-test loop | pytest 37 passed + 3 env-gated (2026-08-10); live contract ×3 PASS; ruff + black + mypy-strict clean | ✅ |
| 3 | Review per tier (LOW → ONE combined, fresh eyes) | docs/reviews/m1-w2-review.md — PASS, 5 MINOR; countersign: reviewer reproduced dup-name IntegrityError + non-list AttributeError by execution (rows 2, 6) | ✅ |
| 4 | *(plan-tag)* HIGH slice security pass | N/A — no HIGH tag on W2 | WAIVED (N/A, plan) |
| 5 | Fault-injection (break → RED → md5 revert) | F1 Verified-filter dropped: 5 tests RED; F2 harness retention dropped: 1 test RED; both reverts md5-identical; suite green after | ✅ |
| 6 | Criteria have citing tests through live entry | REQ-ING-002: test_swebench_ingest.py::test_only_verified_board_is_parsed, ::test_harness_is_retained_with_every_score, ::test_run_date_and_cost_are_stored, ::test_ingest_stores_with_provenance_and_replaces (real ingest_swebench + sqlite); live ≥100 rows: test_scores_contract.py. REQ-ING-003: test_aider_ingest.py::test_ingest_surfaces_health_in_report (+5). REQ-ING-004: rerun-replacement tests both sources | ✅ |
| 7 | New security invariants + NEGATIVE test | IntegrityError→SourceError wrap keeps old working set on failure (test_duplicate_entry_names_keep_best_score covers the trigger path); malformed-payload negative tests ×4 | ✅ |
| 8 | No git checkout/restore on uncommitted work | attested — no git commands; fault reverts in-place sed + md5 | ✅ |
| 9c | Invariant hardening producer list | N/A | WAIVED (N/A) |
| 9b | Scope & checkpoint | Planned W2.1-W2.3 delivered in full; extra (reviewer findings): dup-name dedupe keep-best, non-list guards, date validation, run_date/cost tests. Deferred: none. Owner checkpoint commit `wip(m1-w2)` OWED (repo still not opened — carried) | ✅ (commit OWED) |
| 9a | Economy | Diff ≈ 380 added lines (≤400); W2 spend ≈ plan's 60k line | ✅ |
| 9 | Run summary + skipped ledger | gates run: pytest(unit+contract), ruff, black, mypy(strict), fresh-eyes review, fault-injection ×2 · SKIPPED: make-check-via-venv + gitleaks (host-side; same as W1, ~3 min) · new dep: pyyaml (canonical PyPI pkg, 6.0.3, slopsquat-checked; types-pyyaml dev) — plan-covered (W2 Aider YAML), ledgered per permission-matrix §2 · tokens: ≈65k · outcome: shipped | ✅ |

**Reviewer MINOR ledger:** applied — dup-name dedupe (keep max, count skipped) + regression test; non-list leaderboards/results guards + test; run_date/cost assertions; aider date validation via fromisoformat; IntegrityError→SourceError wrap. Accepted w/o change — cost-semantics asymmetry documented here: aider nulls cost ≤ 0 (0.0 = unreported), swebench stores 0.0 verbatim (null = unreported). Carried to W3: canonicalization must re-split raw_name via split_harness (model-ish remainder is not stored separately); run_date is validated-or-null TEXT; stale sources still rank (W4 shows health flag — OQ for closure).

Filled by: Claude (lead agent) · Date: 2026-08-10 · Wave commit range: pending owner's first commit
