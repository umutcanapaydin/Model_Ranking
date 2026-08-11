# M1 Wave 1 — Combined Code-Reviewer + Tester report (fresh eyes, LOW tier)

Reviewer: independent subagent (did not author the wave). Date: 2026-08-10.
Verification by execution: re-ran pytest (12p/1s pre-fix), ruff, mypy; verified
transaction rollback by direct experiment.

## VERDICT: PASS — 0 BLOCKING, 9 MINOR

## Findings (all MINOR) and disposition
1. No rollback test for mid-transaction failure → APPLIED (test_failed_insert_rolls_back_delete)
2. Stray src/__init__.py breaks plain `mypy src` → APPLIED (removed; moved to _to_delete/ on device)
3. isinstance(x, int|float) admits bool → prices like JSON `true` stored → APPLIED (_is_price TypeGuard + tests)
4. fetch_raw error mapping had zero network-free coverage → APPLIED (respx tests ×3)
5. False "avoids cycle" comment + needless local import → APPLIED (top-level import)
6. Provenance NOT NULL tested for one column only → APPLIED (parametrized ×3)
7. Re-run test asserted count only, not replacement → APPLIED (observed_at stamp assertion)
8. LiteLLMClient never statically checked against RawSource → APPLIED (TYPE_CHECKING conformance)
9. Negative-price path untested → APPLIED (test_parse_skips_bool_and_negative_prices)

## Contract risks flagged for W2-W4 (K.8 freeze)
- scores UNIQUE lacked metric+harness → **schema widened THIS wave, before freeze**
- reset_source allowlist covers pricing/scores only; px_median/models rebuilds need their own path (W3)
- no FK enforcement / PRAGMA foreign_keys; W3 reconciliation enforces referential integrity itself
- SourceReport.skipped conflates skip reasons (W4 observability wants a breakdown)
- RawSource carries no timeout contract — every W2 client must set its own timeout (litellm: 30s)
- context reads max_input_tokens only; expect sparse context downstream

## Criterion trace (post-fix state)
REQ-ING-001 (skip-no-price, $/1M conversion, provenance, ≥500 gated live-PASS) — citing tests in
tests/unit/test_litellm_ingest.py + tests/integration/test_litellm_contract.py.
REQ-ING-004 partial (3-column NOT NULL, deterministic replacement, rollback) — tests/unit/test_schema.py,
tests/unit/test_litellm_ingest.py. No scraping: litellm.py uses the documented raw JSON endpoint (by inspection).
