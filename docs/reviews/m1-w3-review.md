# M1 Wave 3 — Combined Code-Reviewer + Tester report (fresh eyes, LOW tier)

Reviewer: independent subagent. Date: 2026-08-10. Verified by execution (canonicalize probes
against real alias corpus, tie-order experiment, median/export edge probes).

## FIRST VERDICT: FAIL — 2 BLOCKING, 4 MINOR → all fixed same-wave → re-verified PASS

## BLOCKING (both fixed)
1. mypy strict failed on in-scope tests (unused type-ignores; export_ranking meta arg-type)
   → helpers typed (sqlite3.Connection), meta annotated. `mypy src tests` now clean (28 files).
2. Registry false-matched REAL aliases onto wrong canonical IDs (spike-bug class):
   gpt-5-pro→gpt-5, gemini-2.5-flash-lite→flash, grok-4-fast/grok-4.1→grok-4,
   R1-Distill→r1, glm-4.5-air/v→glm-4.5, qwen3-coder-flash→qwen3-coder,
   gpt-5.1-codex-max→5.1-codex, gpt-5.2-pro→5.2, devstral-small→devstral,
   claude-opus-4-1→claude-4-opus.
   → 5 explicit new canonical models (gpt-5-pro, gemini-2.5-flash-lite, grok-4-fast,
   claude-4.1-opus) + tightened lookaheads; unlisted siblings now DROP (conservative);
   regression test test_sibling_variants_never_leak_into_parent_families covers the full list.
   Follow-up fall-throughs caught while fixing: gpt-5.1/5.2 parents needed codex/pro exclusion;
   grok-4 needed date-suffix-vs-version disambiguation (grok-4-0709 keeps, grok-4.1 drops).

## MINOR (all addressed)
3. Tie at MAX score picked nondeterministically (LIMIT 1, no ORDER BY; harness/date could
   desync) → ROW_NUMBER window (run_date DESC, harness ASC) + determinism test.
4. test_model_without_price_is_excluded was vacuous → reseeded with a real score-only model.
5. scores NULL model_id not asserted in DB → asserted + dropped_names surfaced in report.
6. Even-count median + empty-export untested → both tested.

## Accepted without change
- CSV "" vs JSON null rendering for missing fields (JSON is the machine-consumer artifact).
- gemini-3.1-pro → gemini-3-pro sub-version collapse (mirrors tested gpt-5.1-nano policy).

## Carried forward
- W4/M2: median counts every (alias,source) row equally — revisit at multi-source pricing.
- Closure: walk ReconcileReport.dropped_names (drop-list is now data, not just a count).
