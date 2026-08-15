---
record_type: register
id: fixpack-1
status: ratified
date: 2026-08-11
---
# Fixpack FP-M2-1 — Arena live fetch: page-cap abort + rate limit (red-test intake)

**Intake (live evidence, owner terminal 2026-08-11):**
1. `SourceError: arena fetch aborted: > 5000 rows in text/latest` — the W2 anti-truncation
   guard fired correctly: the `latest` split carries ALL category slices, not just the overall
   board (dataset card lists 22 subsets; category slicing lives INSIDE each split).
2. Follow-up run: `429 Too Many Requests` — HF rate-limited the ~50-request burst.
3. Collateral: the demo pipeline died at arena BEFORE reconcile → both recommends returned
   "no eligible model" (data was ingested per-source but never canonicalized).

**Fix (arena.py):**
- PRIMARY: documented `/filter` endpoint with server-side `where "category"='full'`
  (syntax verified against HF dataset-viewer docs) → a few hundred rows, no cap pressure.
- 429 → exponential backoff (Retry-After honored, ≤3 retries, capped 30s).
- FALLBACK: `/filter` failure (endpoint drift) → old `/rows` pagination, whose page-cap
  abort is PRESERVED as a regression test — still loud, never truncating.

**Red→green tests (tests/unit/test_arena_client.py, respx):** filter-primary + where-param
asserted · pagination-to-total · 429-backoff-then-success (sleep observed) · 429-exhaustion
loud fail · filter-failure fallback · fallback page-cap regression. Suite: 106 unit + 5 gated,
ruff/black/mypy clean. Fault-injection: filter path disabled → 4 tests RED, md5 revert.

**Deploy gate (owner, out-of-sandbox verification — V3C-98):** rerun the SAME commands
(RUN_CONTRACT_TESTS=1 pytest tests/integration -v + the 5-source pipeline script). Expect:
arena contract PASSES with ≥20 rows; pipeline prints `arena: N kayıt`; assistant recommend
returns three picks. If HF still 429s, wait ~2 min (burst budget) and retry once.

**Lesson (EXPERIENCE):** the guard that "failed" the run is the guard WORKING — a silent
truncation would have shipped a wrong leaderboard; the loud abort shipped a fixpack instead.

---

# Fixpack FP-M2-2 — Arena: wrong category value + multi-snapshot ratings

**Intake (owner's live run #3 + primary-source probes, 2026-08-11):** with FP-M2-1 applied
(`arena.py` 81→105 stmts confirmed), the Arena contract still failed. Probing the live API:
1. `/filter where "category"='full'` → **num_rows_total: 0**. The value `'full'` came from the
   M2-W2 FIXTURE I authored; live data uses **`'overall'`**. The fallback then paged the whole
   21 259-row split and aborted at the cap — both guards behaving correctly on bad input.
2. `/filter where "category"='overall'` → **386 rows**, spanning MULTIPLE
   `leaderboard_publish_date` values (2026-06-10 and 2026-08-10 both observed live).
   With keep-best-score dedupe, a model's OLD-but-higher rating would have been published as
   its current one — a silent correctness defect, invisible to every fixture-based test.

**Fix:** `OVERALL_CATEGORY = "overall"` (+ `WHERE_OVERALL`); parse keeps ONLY the newest
publish date present in the payload, then dedupes within that snapshot; dropped snapshot rows
are counted into `skipped` (never silent). All fixtures across 5 test files corrected to the
live value.

**Red→green tests:** `test_only_newest_snapshot_is_kept` (old 1500 loses to new 1450 — the exact
defect), `test_filter_endpoint_is_primary_with_overall_where` (+ asserts the live value),
existing suite migrated. 107 unit + 5 gated green; ruff/black/mypy clean. Fault-injection:
category reverted to 'full' → 2 RED; snapshot filter disabled → 1 RED; both md5-reverted.

**Decision made on the owner's behalf (no council convened — primary source settled it):**
"latest" means the NEWEST SNAPSHOT, not per-model best across snapshots. A model absent from the
newest board does not rank. Rationale: coherent provenance (one run_date) and no stale-high
ratings. Revisit if users want historical trend views (M3+ candidate).

**Lesson (EXPERIENCE):** every fixture value invented without touching the live source is an
UNTESTED ASSUMPTION wearing a test's clothing. Two green waves rode on `'full'`. Doctrine:
when a fixture encodes a remote VALUE (not just shape), one live probe must confirm it before
the wave closes — the contract test proved shape, never values.
