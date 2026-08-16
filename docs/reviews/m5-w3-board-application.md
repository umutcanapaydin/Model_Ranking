# M5 W3 — Signed DeepSWE board application and coverage measurement

**Date:** 2026-08-16  
**Input:** owner-mounted Epoch bundle, local allowlist only  
**Engine path:** `DeepSWEClient -> ingest_deepswe -> reconcile/reconcile_plans ->`
`plan_coverage/plan_ranking/plan_evidence_health`  
**Decision applied:** keep Epoch SWE-bench Verified on `coding`; add DeepSWE at `high` as the
separate `agentic-coding` category.

## Published before/after

| Surface | Before | After | Delta | Evidence-date meaning |
|---|---:|---:|---:|---|
| Original pre-M5 `coding` coverage | 1/10 | — | — | Existing SWE-bench evidence |
| Epoch-backed `coding` (W1, unchanged by W3) | 1/10 | **5/10** | **+4 plans** | 2 fresh, 3 stale, 5 unscored |
| New `agentic-coding` category | 0/10 | **6/10** | **+6 plans** | 6 undated, 4 unscored |
| Unique plans covered by either coding surface | 5/10 | **6/10** | **+1 plan** | Categories overlap on five plans |

The two category numerators must not be added. DeepSWE's six plans overlap Epoch on Google AI
Plus/Pro/Ultra and Perplexity Pro/Max; its one additional unique plan is ChatGPT Pro. The union is
therefore **6/10, not 10/10 or 11/10**.

## DeepSWE ingest result

- CSV records: 50.
- Stored score rows: 49.
- Skipped: 1, and that row is explicitly counted as unknown effort.
- Effort conflicts: 0 on this board.
- Stored effort distribution: high 13, low 8, max 9, medium 9, xhigh 10.
- Reconciliation drop list: `muse-spark-1.1` and `kimi-k3_max` remain unmatched and counted; no
  registry rule is guessed for them.
- Every stored `run_date` is NULL. The CSV's `Release date` describes model release, not evaluation
  execution, and is never promoted to evidence age.
- Source telemetry consequently reports 49 rows, `newest_run_date=null`, `age_days=null`,
  `stale=true`. The independent bundle acquisition clock remains `last_verified=2026-08-15` and
  cannot make undated evaluations fresh.

## Selected `high` evidence

| Plan | Selected model | High score | Comparable higher evidence |
|---|---|---:|---|
| Perplexity Max | Claude Opus 5 | 72.8 | max 73.6 |
| ChatGPT Pro | GPT-5.6 Sol | 69.4 | max 72.7 |
| Perplexity Pro | GPT-5.6 Terra | 53.8 | max 69.6 |
| Google AI Plus | Gemini 3.1 Pro | 11.8 | none on the same harness and source |
| Google AI Pro | Gemini 3.1 Pro | 11.8 | none on the same harness and source |
| Google AI Ultra | Gemini 3.1 Pro | 11.8 | none on the same harness and source |

All six rows use `mini-swe-agent`, `effort=high`, and source `epoch_deepswe_external`. Higher-effort
values are allowed only from the same harness and source identity.

## Freshness and contradiction disclosure

- `coding`: **2 fresh / 3 stale / 0 undated / 5 unscored**.
- `agentic-coding`: **0 fresh / 0 stale / 6 undated / 4 unscored**.
- Source health and selected-plan health are separate JSON sections. A source acquisition date or a
  release date does not substitute for a selected evaluation date.
- Gemini 3.1 Pro remains the measured disagreement: Epoch SWE-bench `inspect_ai/customtools`
  publishes **75.6**, while DeepSWE `mini-swe-agent/high` publishes **11.8**. W1 found a harness/tool
  configuration difference but no causal proof. W3 therefore preserves both numbers on separate
  categories and does not silently choose one as universal truth.

## Reproduction and acceptance lock

`tests/unit/test_deepswe_workflow.py::test_real_board_reproduces_signed_coverage_and_undated_health`
runs the first-class client and ingest path over the owner-mounted bundle, loads the shipped
plans/rosters, reconciles through the registry, checks both categories and exact six-plan coverage,
checks the four-state partition, and executes the coverage CLI JSON boundary. The intentionally
source-scoped fixture does not ingest Arena, so the CLI's overall exit is 1 for the unrelated empty
`assistant` category; the asserted W3 category results themselves are non-zero and exact.
