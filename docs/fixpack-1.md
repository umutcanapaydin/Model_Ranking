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
