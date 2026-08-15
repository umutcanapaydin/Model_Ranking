# Wave-Close Checklist — M3 Wave 1 (plan schema + live-verified seed; v4.1 template)

> Wave scope: m3-plan.md §3 W1 (REQ-SUB-001/-002).

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier: **LOW** (curated public data; no authz/secrets/crypto/egress; new parser input is an in-repo authored file) | m3-plan.md:10 | ✅ |
| 2 | Dev-test loop ran: implement → 17 tests → review-fix → 20 tests; full gate green (ruff, black, mypy 42 files, **127 passed + 5 gated-skip**, check-records) | this session run log, 2026-08-15 | ✅ |
| 3 | LOW → ONE combined fresh-eyes reviewer. Verdict FAIL → 1 BLOCKING + 4 MINOR, **all closed in-wave**: B1 black gate red on plans.py → formatted, gate re-pinned green; M1 `.inf` price passed validation → `math.isfinite` gate + citing test; M2 DDL CHECK had no citing test → SQLite-layer test added; M3 imprecise limits wording in plans.yaml (Claude rows) → corrected to "plan cards…"; M4 validator mutated caller dict → copy-on-validate + regression test. Countersign: reviewer proved atomicity empirically (mid-INSERT violation → old set survives) and CHECK>0 via direct INSERT probe | review transcript; tests test_infinite_price_fails_loud, test_schema_check_rejects_nonpositive_price_at_sqlite_layer, test_validator_does_not_mutate_input | ✅ |
| 4 | *(plan-tag)* HIGH slice security pass | N/A — LOW wave | ✅ |
| 5 | Fault-injection: (a) `price <= 0` gate removed → 2 tests RED, restored md5-identical (d3e7d6…d9); (b) seed chatgpt-plus price → 0 → 2 seed tests RED, restored md5-identical (43abc3…1c). Both faults RED = controls live | reviewer fault-injection log | ✅ |
| 6 | Criteria → citing tests through the LIVE entrypoint: REQ-SUB-001 (schema CHECK: test_schema_check_rejects…; provenance: test_invalid_row_fails_loud[last_verified/source_url]; drops counted: test_reconcile_plans_links…); REQ-SUB-002 (REAL seed file: test_seed_dataset_meets_req_sub_002 + …ingests_and_reconciles_end_to_end — named in prd.md §10) | tests/unit/test_plans_ingest.py (20 tests) | ✅ |
| 7 | Security invariants: no new ⛔ surface; parser input is in-repo authored YAML via yaml.safe_load (no object construction); all SQL parameterized (reviewer-verified, zero f-string SQL) | review §3 | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work; in-place md5 reverts only | row 5 | ✅ |
| 9c | Invariant hardening | N/A | ✅ |
| 9b | Scope row: PLANNED = schema + yaml format + parser + seed (live-probed) + registry linkage. DELIVERED = all, plus PRD §10 (M3 REQs; M2 REQ-drift noted in-file) and review-driven hardening (isfinite, DDL test, no-mutate). DEFERRED = none. NOTE: seed values for pages that don't render USD amounts to our fetcher (ChatGPT, Google) were cross-checked against two independent 2026 trackers each and recorded in plans.yaml header comments; **Google AI Plus EXCLUDED — sources dispute $4.99 vs $7.99** (re-probe next verification pass); owner re-verifies all rows out-of-sandbox at the milestone gate | data/plans.yaml header; m3-plan.md §3 W1 | ✅ |
| 9a | Economy: diff ≈ 6 files, ~600 added lines (schema+module+tests+data) — within ~≤400? EXCEEDED (WARN, not block): ~200 of it is the curated data file + PRD text, not logic. Token spend within plan §5 W1 ≈ 80k line | git diff --stat | ✅ |
| 9 | RUN LINE — gates run: ruff · black · mypy(src+tests) · pytest(127+5skip) · check-records · outcome: **shipped**. SKIPPED: live contract tests (standing sandbox rule → CI/owner); install-check not re-run this wave (no manifest-relevant file moved; runs in make check at W-close commit anyway). Ledger: Google AI Plus row withheld (price dispute — see 9b); GPT-5.6 / GPT-5.6 Sol Pro have no registry rules yet → plan links DROP+COUNT by design, registry extension queued as an M4 candidate (needs a benchmark/pricing source naming them first) | this row | ✅ |

**Escaped-blocker tripwire:** none.

Filled by: Claude (Cowork lead agent, D-106) · Date: 2026-08-15 · Wave commit range: `d703a77..HEAD` (this commit)
