# M5 W1 Primary-board Measurement

**Status:** AWAITING OWNER BOARD SIGNATURE  
**Measured:** 2026-08-16  
**Decision basis:** `docs/plans/m5-plan.md` W1 and the owner-approved plan-level freshness ruling

## Method

The measurement ran the project's real selection path: curated plans and rosters were ingested,
plan links and benchmark names were reconciled through the ordered registry, coverage was computed,
and `subscribe.plan_ranking()` selected each plan's highest scoring evidence row. Freshness is the
age of that selected row, never the newest unrelated row in the source. The four exhaustive states
are fresh (`<60` days), stale (`>=60` days), undated, and unscored.

Epoch was also reproduced through the shipped W1 path (`EpochClient` -> `ingest_epoch` ->
`reconcile_plans` / `reconcile` -> `plan_evidence_health`). The other candidate boards are W1
measurements over their real CSV shapes; they are not claimed as shipped ingestion paths.

The pre-Epoch coding baseline is 1/10 scoreable. The selected row is Google AI Pro via Gemini 3 Pro,
77.4, `live-SWE-agent`, evaluated 2025-11-20 (269 days old). The source itself has a newer row, which
demonstrates why source-global newest dates cannot stand in for selected-plan evidence.

## Candidate results

| Candidate | CSV rows | Scoreable plans | Selected-evidence freshness | Date meaning |
|---|---:|---:|---|---|
| Epoch SWE-bench Verified | 35 (33 stored, 2 older duplicates skipped) | 5/10 | **2 fresh, 3 stale, 5 unscored** | Real `Started at` evaluation timestamps |
| DeepSWE | 50 | 6/10 | **6 undated, 4 unscored** | Only model `Release date`; not evidence age |
| FrontierCode | 25 | 3/10 | **3 undated, 7 unscored** | Only model `Release date`; not evidence age |
| TerminalBench | 204 | 5/10 | **5 stale, 5 unscored** | Real `Run date`; selected rows are 2026-03-13 |
| Aider polyglot | 77 | 0/10 | **10 unscored** | Real evaluation dates, no curated-plan match |

### Epoch selected rows

- Fresh (52 days): Perplexity Pro and Perplexity Max select GLM-5.2, 78.7, `inspect_ai`,
  evaluated 2026-06-25. Their roster links are explicit and reconcile to `glm-5.2`.
- Stale (173 days): Google AI Plus, Pro, and Ultra select Gemini 3.1 Pro, 75.6198,
  `inspect_ai`, evaluated 2026-02-24.
- Unscored: ChatGPT Go, ChatGPT Plus, ChatGPT Pro, Claude Pro, and Claude Max.

The Epoch source-global health row is 52 days old, but that aggregate must remain labelled source
telemetry: it does not make the three Google plans fresh.

### Effort consequence

DeepSWE's apparent 6/10 advantage exists at one comparable effort level only: `high` gives 6/10;
`max`, `xhigh`, `medium`, and `low` each give 3/10. The current unfiltered MAX behavior mixes effort
levels and is not an honest board policy. W2 must store effort explicitly before DeepSWE can rank.

FrontierCode also contains a direct conflict: `claude-opus-5_max` has an explicit `Reasoning effort`
value of `medium`. The future parser must state precedence and count such conflicts.

## Gemini contradiction (REQ-REC-012)

Epoch reports `gemini-3.1-pro-preview-customtools` at 0.756198. DeepSWE reports
`gemini-3.1-pro-preview` at 0.117517 under `mini-swe-agent` and `high` effort: a 6.4348x difference.

A range-read of Epoch's `.eval` journal confirms task `swe_bench_verified`, agent `bash`, solver
`bash_agent`, edit tools `text_editor` and `apply_patch`, 484 samples, inspect_ai 0.3.174, and
benchmark version 2.0.2. This proves a configuration difference. It does **not** prove that the
tool interface caused the score gap: the local bundle has no `.eval` file, DeepSWE exposes no
equivalent tool-interface log, and no controlled same-board customtools/default pair is available.

Verdict: the contradiction is unresolved causally. Both scores and the harness/effort disagreement
must be disclosed; silently selecting either number fails REQ-REC-012.

## Recommendation and owner gate

**Recommended:** keep Epoch SWE-bench Verified as the primary `coding` evidence, and add DeepSWE at
the single `high` effort level as a separate `agentic-coding` category/evidence surface. This keeps
real evaluation dates on the existing category while exposing DeepSWE's extra ChatGPT/Claude reach
without pretending its release dates are evaluation dates or averaging unlike harnesses.

If only one board is authorized, choose Epoch: DeepSWE adds only one scoreable plan (6/10 vs 5/10)
but all six are undated, the Gemini result is unexplained, and effort must be modelled first.

Owner choice required before W3:

1. Epoch primary + separate DeepSWE-high agentic-coding surface (**recommended**).
2. Epoch primary only.
3. DeepSWE-high primary, explicitly undated.
4. Another named board/policy (requires a signed plan amendment).
