# M5 W1 Primary-board Measurement

**Status:** AWAITING OWNER BOARD SIGNATURE  
**Measured:** 2026-08-16  
**Decision basis:** `docs/plans/m5-plan.md` W1 and the owner-approved plan-level freshness ruling

## Method

The committed, deterministic producer is `python -m app.workflows.board_measurement`. It consumes
the five owner-mounted CSVs without network access, creates a separate disposable SQLite database
for every candidate, and runs `reconcile_plans()` / `reconcile()` / `plan_coverage()` /
`plan_ranking()` / `plan_evidence_health()`. The existing baseline and Epoch use the shipped
`ingest_swebench()` and `EpochClient -> ingest_epoch()` paths respectively. The remaining boards use
explicit W1 measurement adapters; they do not add production source policy or the W2 effort schema.
Each candidate is mapped onto the current coding benchmark/metric fields only inside its isolated
comparison database so the existing category predicates execute. The record interprets coverage
and selected-evidence dates, not cross-board score ordering or semantic equivalence.
The result table below was regenerated with:

```bash
PYTHONPATH=src .venv/bin/python \
  -m app.workflows.board_measurement \
  --bundle-dir /path/to/unpacked/epoch_data \
  --plans data/plans.yaml --rosters data/rosters.yaml \
  --baseline data/m5-swebench-baseline.json \
  --today 2026-08-16 --last-verified 2026-08-15
```

Freshness is the age of the selected row, never the newest unrelated source row. The four states are
fresh (`<60` days), stale (`>=60` days), undated, and unscored. DeepSWE is pre-filtered to its
explicit `high` effort for this W1 comparison; its other 37 rows remain counted as filtered input.
Release dates on DeepSWE and FrontierCode are intentionally stored as no evaluation date.

The before snapshot is the complete 180-row Verified board extract from pinned SWE-bench commit
`f42505b21a0eb31a9cc1204caafcbe0da6c1a259` (retrieved 2026-08-16), whose raw SHA-256 is
`fa4b61d3167dfe99e1a834e007a38372c5bac07b7627f8e2c3904fb48cd4a006`. It preserves every field
the shipped parser consumes and produces 173 stored rows plus 7 counted duplicates. The producer
rejects provenance, row-count, field-set, or parser-count drift before measuring the 1/10 baseline.

The pre-Epoch coding baseline is 1/10 scoreable. The selected row is Google AI Pro via Gemini 3 Pro,
77.4, `live-SWE-agent`, evaluated 2025-11-20 (269 days old). The source itself has a newer row, which
demonstrates why source-global newest dates cannot stand in for selected-plan evidence.

## Candidate results

| Candidate | CSV rows | Scoreable plans | Selected-evidence freshness | Date meaning |
|---|---:|---:|---|---|
| Epoch SWE-bench Verified | 35 (33 stored, 2 older duplicates skipped) | 5/10 | **2 fresh, 3 stale, 5 unscored** | Real `Started at` evaluation timestamps |
| DeepSWE | 50 (13 high-effort stored, 37 explicitly filtered) | 6/10 | **6 undated, 4 unscored** | Only model `Release date`; not evidence age |
| FrontierCode | 25 (20 stored, 5 empty-name skipped) | 3/10 | **3 undated, 7 unscored** | Only model `Release date`; not evidence age |
| TerminalBench | 204 (181 stored, 23 empty/duplicate skipped) | 5/10 | **5 stale, 5 unscored** | Real `Run date`; selected rows are 2026-03-13 |
| Aider polyglot | 77 (71 stored, 6 empty/duplicate skipped) | 0/10 | **10 unscored** | Real evaluation dates, no curated-plan match |

### Epoch selected rows

- Fresh (52 days): Perplexity Pro and Perplexity Max select GLM-5.2, 78.7, `inspect_ai`,
  evaluated 2026-06-25. Their roster links are explicit and reconcile to `glm-5.2`.
- Stale (173 days): Google AI Plus, Pro, and Ultra select Gemini 3.1 Pro, 75.6,
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

Epoch reports `gemini-3.1-pro-preview-customtools` at 75.6% under `inspect_ai`. DeepSWE reports
`gemini-3.1-pro-preview` at 11.8% under `mini-swe-agent` and `high` effort: a 6.4x difference. The
producer retains the source fractions for comparison but applies D-109 once at JSON/string output.

A range-read of Epoch's `.eval` journal confirms task `swe_bench_verified`, agent `bash`, solver
`bash_agent`, edit tools `text_editor` and `apply_patch`, 484 samples, inspect_ai 0.3.174, and
benchmark version 2.0.2. This proves a configuration difference. It does **not** prove that the
tool interface caused the score gap: the local bundle has no `.eval` file, DeepSWE exposes no
equivalent tool-interface log, and no controlled same-board customtools/default pair is available.

The exact Epoch artifact referent is log id `8QQQWDgmmEsmQVUJWcxx4P`,
`https://epoch-benchmarks-staging-public.s3.us-east-2.amazonaws.com/inspect_ai_logs/8QQQWDgmmEsmQVUJWcxx4P.eval`.

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
