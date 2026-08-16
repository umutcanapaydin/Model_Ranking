---
record_type: wave
id: m1-wave-1-close
status: ratified
date: 2026-08-11
---
# Wave-Close Checklist — M1 Wave 1 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

Wave scope: schema + source Protocols + LiteLLM ingestion (m1-plan.md §3 W1).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded | docs/plans/m1-plan.md:4 — LOW; diff touches input-parsing → parser hardened (bool/negative guards) + reviewer pass; no authz/secrets/crypto/egress | ✅ |
| 2 | Per-agent dev-test loop ran | pytest 19 passed + 1 env-gated (2026-08-10 session run); ruff clean; mypy strict clean (`mypy src`) | ✅ |
| 3 | Review per tier (LOW → ONE combined reviewer, fresh eyes) | docs/reviews/m1-w1-review.md — VERDICT PASS, 9 MINOR findings (all applied or ledgered); countersign: reviewer independently re-ran tests/ruff/mypy and verified rollback semantics by direct experiment (rows 2, 6) | ✅ |
| 4 | *(plan-tag)* HIGH slice pulled-forward security pass | N/A — no HIGH tag on W1 in the signed plan | WAIVED (N/A, plan) |
| 5 | Tester fault-injection (break → RED → byte-identical revert) | F1 price-guard `>0→>=0`: 4 tests RED; F2 reset_source no-op: determinism test RED; both reverts md5-identical; suite green after (session log 2026-08-10). No stay-GREEN faults | ✅ |
| 6 | Criteria have citing tests through the live entry | REQ-ING-001: tests/unit/test_litellm_ingest.py::test_parse_skips_unpriced_and_nonchat_entries, ::test_parse_converts_to_per_million, ::test_ingest_stores_rows_with_provenance (through real ingest_litellm + real sqlite); ≥500-alias acceptance: tests/integration/test_litellm_contract.py (env-gated, PASSED live 2026-08-10). REQ-ING-004 (partial): ::test_ingest_rerun_is_deterministic, ::test_failed_insert_rolls_back_delete, test_schema.py::test_pricing_requires_provenance[3 cols] | ✅ |
| 7 | New security invariants + NEGATIVE test | reset_source table-allowlist (SQL-injection surface): test_schema.py::test_reset_source_rejects_unknown_table; zero-price CHECK: test_schema.py::test_pricing_rejects_zero_prices | ✅ |
| 8 | No git checkout/restore on uncommitted work | attested — no git commands run at all (A0.5: agents never run git); fault reverts were in-place sed + md5-verified | ✅ |
| 9c | Invariant hardening producer list | N/A — no shared auth/tenancy/money invariant touched | WAIVED (N/A) |
| 9b | Scope & checkpoint | Scope: planned W1.1-W1.4 → delivered in full; extra: schema UNIQUE widened to (raw_name,benchmark,metric,harness,source) + model_id indexes (reviewer contract-risk #1, pre-freeze). Deferred: none. Owner checkpoint commit `wip(m1-w1): checkpoint — NOT reviewed` OWED — git repo not yet created (owner announced he will open it; ledgered here, escalate at milestone if still absent) | ✅ (commit OWED) |
| 9a | Economy | Diff ≈ 330 added lines across 8 files (≤400); token spend within plan's W1≈60k line | ✅ |
| 9 | Run summary + skipped ledger | gates run: pytest(unit+gated contract), ruff, ruff-format/black, mypy(strict), fresh-eyes combined review, fault-injection ×2 · gates SKIPPED: make-check-via-venv (no venv in sandbox — same tools run directly; owner re-runs `make check` host-side, ~2 min), gitleaks (not installed in sandbox; hook runs host-side, ~1 min), owner checkpoint commit (no repo yet) · tokens/cost: ≈60k this wave · outcome: shipped | ✅ |

**Reviewer MINOR findings ledger:** applied — bool/negative price guard (+tests), rollback test, provenance NULL parametrized ×3, rerun replacement assertion, respx client error tests ×3, top-level import + false comment removed, stray `src/__init__.py` removed (moved to `_to_delete/`), scores UNIQUE widened pre-freeze, TYPE_CHECKING conformance check. Not applied (accepted, noted for W2/W4): SourceReport.skipped breakdown (W4 observability), RawSource timeout contract note (W2 clients must set their own timeout — carried into W2 dispatch prompt).

Filled by: Claude (lead agent) · Date: 2026-08-10 · Wave commit range: pending owner's first commit (files delivered to working tree)
