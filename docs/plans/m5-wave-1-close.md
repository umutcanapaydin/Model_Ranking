# Wave-Close Checklist — M5 Wave 1

> Filled from `docs/wave-checklist.template.md`. Scope: M5 plan §3 W1 — local Epoch ingestion,
> selected-plan freshness, five-board measurement, Gemini disclosure, and the decision record.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded; input parsing makes the effective tier HIGH | `docs/plans/m5-plan.md` §4 records W1 HIGH while retaining milestone LOW-MED | ✅ |
| 2 | Per-agent implement → test → self-review → fix loop ran | commits `0e38a6d`, `bc31b55`, `8fe1a1e`; final real-bundle scope 38 passed and full suite 221 passed / 5 expected network skips in `docs/reviews/m5-wave-1-tester.md` | ✅ |
| 3 | HIGH review: separate fresh Code Reviewer and Tester; reviewer countersigned two checklist facts | PASS in `docs/reviews/m5-wave-1-review.md` and `docs/reviews/m5-wave-1-tester.md`; reviewer independently recomputed baseline 180→173+7→1/10 and Epoch 2 fresh + 3 stale + 5 unscored | ✅ |
| 4 | HIGH pulled-forward security/data-boundary pass | URL refusal, local allowlist, mandatory provenance/clock, malformed-board loud failure, non-finite Gemini probes, and release-date isolation are evidenced in `docs/reviews/m5-wave-1-review.md` | ✅ |
| 5 | Fault injection on load-bearing behaviors | Tester made four named faults RED (60-day boundary, D-109 JSON, baseline integrity, newest-run dedupe), restored in place with identical SHA-256, then reran GREEN; `docs/reviews/m5-wave-1-tester.md` | ✅ |
| 6 | Every touched acceptance criterion has a live-entry citing test | REQ-ING-010 `tests/unit/test_epoch_workflow.py`; REQ-ING-011b `tests/unit/test_coverage.py`; REQ-SUB-007 and REQ-REC-012 `tests/unit/test_m5_board_measurement.py`; exact citations in both W1 review records | ✅ |
| 7 | New/changed security invariants have negative tests | M5 plan §4 data-boundary invariants; `tests/unit/test_epoch_ingest.py` rejects URL/bad clock/missing board/bad shape and `tests/unit/test_coverage.py` rejects malformed selected dates | ✅ |
| 8 | No checkout/restore on uncommitted work | Tester attests every mutation and revert used in-place patches plus pre/post hashes in `docs/reviews/m5-wave-1-tester.md` | ✅ |
| 9c | Shared security invariant producer enumeration | N/A — no auth, tenancy, or money invariant changed; data-boundary producers and per-producer tests are enumerated in `docs/reviews/m5-wave-1-review.md` | WAIVED — domain not touched |
| 9b | Scope and checkpoint | Planned W1 delivered in `265126d..ba6aef0`; no product deferral; checkpoint `0e38a6d`; board gate resolved after evidence by delegated selection of option 1 | ✅ |
| 9a | Economy | 16 files, +3302/−16 exceeds the advisory ~400-line valve because the pinned complete 1,105-line baseline and evidence/review artifacts dominate; milestone budget remains the signed ≈500k line | ✅ — variance recorded |
| 9 | RUN LINE — gates run: real-bundle scope (38) · full pytest (221 pass/5 skip) · ruff · black · mypy · four fault injections · independent producer replay · `make wave-check` · gates SKIPPED: five opt-in network contracts (no network; existing expected skips), `make test` install prerequisite (sandbox PyPI blocked before collection; exact installed pytest phase ran), auth/tenancy/money producer sweep (N/A) · tokens/cost: within signed M5 budget · outcome: **shipped** | This row; detailed outputs in both W1 review records | ✅ |

Escaped-blocker tripwire: no blocker escaped. Both fresh-eyes verdicts are PASS with no BLOCKING or
MINOR findings. No milestone security review is claimed here; that remains a closure gate.

Filled by: `Codex` · Date: `2026-08-16` · Wave commit range: `265126d..ba6aef0`
