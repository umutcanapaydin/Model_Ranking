# Product Requirements (PRD) — model_ranking

> Re-structured requirements with REQ-IDs. Tests and PRs cite these IDs forever (seed A.1). Per-area prefixes: REQ-ING (ingestion), REQ-CAN (canonical registry), REQ-RANK (ranking), REQ-REC (recommendation).
>
> Format conventions:
> - Each REQ has: ID, Statement, Acceptance criteria, Customer source, Status.
> - First restructure into REQ-IDs (this file), then re-read for Open Questions in §9 (seed A.3 — separate passes).

---

## 1. Project context

model_ranking is the backend/data engine of an "AI advisor" product: it aggregates free-and-legally-usable LLM benchmark scores and API pricing from public sources, reconciles model names into a canonical registry, and produces per-use-case, budget-aware recommendations in three labeled answers (Best Quality / Best Value / Budget Pick). The end product is an iOS app for consumers and developers who do not know which AI model or subscription fits their needs; this repo delivers the data pipeline, the ranking store, and the deterministic recommendation engine that the app will consume. Owner: Umut Can Apaydın (ILGAR). M1 scope is the coding category with three sources; later milestones add categories, sources, and the subscription-plan table.

## 2. Customer artifacts referenced

| Artifact | Date | Version | Where |
|---|---|---|---|
| LLM Benchmark App research (AI #1) | 2026-08-06 | v1 | owner archive: llmbenchmarkappresearch.md |
| Mobile AI advisor research (AI #2) | 2026-08-06 | v1 | owner archive: llmaibenchmarkingmobileappresearch.md |
| Critical comparison + verdict | 2026-08-06 | v1 | owner archive: research-comparison-verdict.md |
| Spike prototype (pipeline.py, recommend.py) | 2026-08-06 | spike-L0 | Cowork session workspace; NOT imported (D-102) |

---

## 3. Data ingestion (REQ-ING)

### REQ-ING-001 — Ingest LiteLLM pricing data

**Statement:** The pipeline fetches LiteLLM's `model_prices_and_context_window.json` from its canonical GitHub raw URL and stores per-alias input/output token prices and context window into the database.
**Acceptance:**
- A pipeline run persists ≥500 priced chat-model aliases with input and output $/1M-token values.
- Entries without both input and output cost are skipped, not stored as zero.
- Each stored row carries `source`, `source_url`, and `observed_at`.
**Customer source:** research §5.2 (programmatic pricing sources).
**Status:** proposed

### REQ-ING-002 — Ingest SWE-bench Verified leaderboard

**Statement:** The pipeline fetches the SWE-bench site leaderboard JSON from its GitHub repository and stores every Verified entry as a score record.
**Acceptance:**
- All Verified entries present in the source file are stored with `% resolved`, run date, and raw entry name.
- The agent/harness name is parsed and stored WITH each score (a score is a model+harness pair, never model alone).
- Rows from other leaderboards (Lite, Multimodal, …) are not mixed into Verified results.
**Customer source:** research §3.1; comparison report §2 (harness retention).
**Status:** proposed

### REQ-ING-003 — Ingest Aider polyglot leaderboard

**Statement:** The pipeline fetches Aider's `polyglot_leaderboard.yml` from GitHub and stores pass_rate_2 scores plus per-run cost.
**Acceptance:**
- All entries with a parseable model name are stored with score, run date, and `total_cost`.
- The known staleness of this source (updates stalled ~Nov 2025) is recorded as a source-health flag, not silently ignored.
**Customer source:** research §3.1 (Aider: coding + cost per run).
**Status:** proposed

### REQ-ING-004 — Provenance on every record

**Statement:** Every ingested record carries provenance and versioning fields so "as of" questions and audits are answerable.
**Acceptance:**
- Every pricing and score row has non-null `source`, `observed_at`.
- A repeated pipeline run replaces the working set deterministically (same input → same output; no duplicate accumulation).
- No ingestion path scrapes an HTML page; only documented raw-data endpoints are used (D-101).
**Customer source:** research B §8 (versioned records); comparison verdict §6.
**Status:** proposed

## 4. Canonical model registry (REQ-CAN)

### REQ-CAN-001 — Alias reconciliation to canonical models

**Statement:** Model names from all sources are mapped to a canonical model ID via an ordered first-match rule table (vendor, display name, regex).
**Acceptance:**
- The same underlying model arriving under different aliases (e.g. `claude-4-5-opus`, `Claude 4.5 Opus medium`) maps to ONE canonical ID.
- Unmatched names are dropped with a count reported, never guessed.
**Customer source:** research B §6 step 1; spike finding (alias mapping is the core IP).
**Status:** proposed

### REQ-CAN-002 — Variant-before-parent rule ordering

**Statement:** Sub-variant rules (mini/nano/codex/chat…) precede parent-family rules so a variant's price or score never leaks into the parent model.
**Acceptance:**
- A regression test proves a `*-nano` alias does NOT match its parent family rule (the exact spike bug, reproduced red→green).
- Rule-order is covered by a test that fails if a parent rule precedes its variants.
**Customer source:** spike finding 2026-08-06 (GPT-5-nano price leaked into GPT-5).
**Status:** proposed

### REQ-CAN-003 — Median price per canonical model

**Statement:** Each canonical model's reference price is the median across its alias/provider prices, not the minimum.
**Acceptance:**
- A model with multiple provider prices stores the median input and output $/1M.
- A unit test demonstrates an outlier cheap alias does not become the model's reference price.
**Customer source:** spike finding (MIN picked wrong variant); research B §7.
**Status:** proposed

## 5. Ranking (REQ-RANK)

### REQ-RANK-001 — Coding ranking table

**Statement:** The system produces a coding ranking: best SWE-bench Verified score per canonical model, joined with Aider score (when present) and median prices.
**Acceptance:**
- Output contains ≥20 canonical models with score, harness, evidence date, input/output/blended price.
- Blended price = input×0.75 + output×0.25, documented in output.
**Customer source:** research §3.2 (coding = richest category); M1 scope.
**Status:** proposed

### REQ-RANK-002 — Machine-readable export

**Statement:** Rankings export as CSV and JSON artifacts suitable for the future app/API layer.
**Acceptance:**
- One pipeline command yields `coding_ranking.csv` and `coding_ranking.json` with identical rows.
- Export includes a dataset-level `generated_from` note listing sources and observation timestamps.
**Customer source:** research §7 (serving pre-computed rankings).
**Status:** proposed

## 6. Recommendation engine (REQ-REC)

### REQ-REC-001 — Three labeled answers

**Statement:** For the coding use case and a budget level, the engine returns exactly three labeled picks: Best Quality, Best Value, Budget Pick.
**Acceptance:**
- Each pick includes: model, vendor, score(s), prices, evidence date, harness, confidence grade, and a "why / trade-off" explanation.
- Output is deterministic: same database state + same inputs → same picks.
**Customer source:** research B §1 (three clearly labeled answers).
**Status:** proposed

### REQ-REC-002 — Budget constraint filtering

**Statement:** Budget levels (low/medium/unlimited) filter candidates by blended price BEFORE any scoring; ineligible models never appear.
**Acceptance:**
- With a low budget, no pick has blended price above the low threshold.
- Thresholds are named constants covered by a test.
**Customer source:** research B §6 step 4 (hard constraints first).
**Status:** proposed

### REQ-REC-003 — Pareto non-dominance

**Statement:** Value picks come from the quality–cost Pareto frontier; the engine never uses a bare `score ÷ price` ratio.
**Acceptance:**
- A test proves no recommended model is simultaneously worse AND more expensive than another eligible model.
- The value pick rule (within N points of leader, cheapest) is a documented, tested constant.
**Customer source:** research B §6 step 5.
**Status:** proposed

### REQ-REC-004 — Confidence grading and honesty

**Statement:** Each pick carries a confidence grade derived from independent-source count, and near-ties are disclosed rather than hidden.
**Acceptance:**
- Two independent benchmark sources → High; one → Medium; the mapping is tested.
- When #1 and #2 are within the close-call threshold, the output says so explicitly (tested).
**Customer source:** research B §6 step 3; comparison verdict §6.
**Status:** proposed

---

## 7. Non-functional requirements

- **Performance:** full pipeline run (3 sources, ingest→rank) completes in <60s on a laptop; recommendation query <1s.
- **Security / legal:** no scraping; documented data endpoints only; every source's license recorded (D-101); no secrets in repo (gitleaks); no PII anywhere in M1.
- **Observability:** each pipeline run logs per-source row counts and drop counts; source-health flags (staleness) are visible in run output.
- **Operability:** single command (`make` target) runs the pipeline; SQLite file is disposable and rebuildable from sources at any time.

## 8. Out of scope (explicit — M1)

- iOS/SwiftUI app — later milestone; this repo is the engine.
- Arena/LMArena HF dataset + OpenRouter + Epoch ingestion — next milestones (M2 candidates; network-blocked in the build sandbox, fine on owner machine/CI).
- Artificial Analysis data — requires paid Commercial license first (verified 2026-08-06); do not integrate.
- Consumer subscription-plan table (ChatGPT Plus vs Gemini Pro…) — M2/M3 candidate; unique data asset, needs curation workflow.
- Non-coding categories (chat, writing, image…) — after the engine is proven on coding.
- Any LLM in the scoring/recommendation path (D-104) and any chat feature.
- User accounts, telemetry, deployment — no deploy target chosen yet (OQ-3).

## 9. Open Questions

### OQ-1 — When do Arena + OpenRouter sources come in?
**Asked of:** owner
**Status:** open
**Asked on:** 2026-08-06
They are the natural M2 scope (chat/everyday category needs Arena). Decide at M1 closure.

### OQ-2 — Subscription-plan table milestone
**Asked of:** owner
**Status:** open
**Asked on:** 2026-08-06
The "which $20 plan" answer needs a manually curated plan table with a verification workflow. Which milestone owns it?

### OQ-3 — Hosting / deploy target
**Asked of:** owner
**Status:** open
**Asked on:** 2026-08-06
Research suggests Supabase or Cloudflare Workers for the serving layer. No decision needed before the API milestone.

---

## 10. M3 — Subscription-plan table (REQ-SUB / REQ-REC / REQ-GP / REQ-CAL)

> Added 2026-08-15 from the signed m3-plan.md §2 (Q1-Q4 locked by the owner the same day).
> Note (doc drift, recorded): M2's REQ-ING-005..008 / REQ-CAT-001..003 / REQ-REC-005..006 /
> REQ-CI-001 were specified in the signed m2-plan.md §2 and never copied here; their canonical
> statements remain in that signed plan. New REQs land in BOTH from M3 on.

### REQ-SUB-001 — Plan schema with mandatory provenance

**Statement:** `plans` + `plan_models` tables: provider, plan name, monthly USD price (CHECK > 0), currency, region, limits verbatim, source_url, last_verified; included-model names link to canonical models via the registry, unmatched names stay NULL and are counted.
**Acceptance:** schema enforces price > 0; every row carries source_url + last_verified; reconcile_plans counts drops (never guesses).
**Status:** accepted (m3-plan signed)

### REQ-SUB-002 — Curated seed dataset, live-verified

**Statement:** `data/plans.yaml` ships ≥6 plans across ≥4 providers (OpenAI, Anthropic, Google, Perplexity — owner Q1), USD/US-first (owner Q2), every value probed against a live source on entry day; curated-file validation FAILS LOUD (skip-and-count is for fetched sources, not authored data).
**Acceptance:** the real seed file parses, ingests transactionally, and meets the counts above (citing test: tests/unit/test_plans_ingest.py::test_seed_dataset_meets_req_sub_002).
**Status:** accepted (m3-plan signed)

### REQ-SUB-003 — Staleness is disclosed, never hidden

**Statement:** a plan row older than the staleness window (30 days — owner Q3, stored as data) is flagged in exports and recommendation output.
**Status:** accepted (m3-plan signed; flag computation W2, output wiring W3 with REQ-REC-008)

### REQ-SUB-004 — Re-verification cadence

**Statement:** a weekly scheduled CI job (owner Q4) fails/reminds when any plan row exceeds the staleness window.
**Status:** accepted (m3-plan signed; wired in W2)

### REQ-REC-007 — Subscription recommendation

**Statement:** `recommend --subscription` returns three labeled plan picks (quality/value/budget) reusing the budget/quality logic, where a plan's linked models carry the category scores.
**Status:** accepted (m3-plan signed; W3)

### REQ-REC-008 — Stale-plan disclosure in output

**Statement:** recommendation output disclosing stale plan rows, same honesty contract as stale_notice.
**Status:** accepted (m3-plan signed; W3)

### REQ-GP-001 — GP v4.3.1 install correctness

**Statement:** `make install-check` green: PROJECT paths complete, GP-INTERNAL files absent, gates wired (make check + pre-commit + CI).
**Status:** DONE (M3-W0, commit d703a77)

### REQ-CAL-001 — Elo threshold recalibration

**Statement:** assistant-category thresholds recalibrated against live CI data as a data edit in categories.py, rationale recorded.
**Status:** accepted (m3-plan signed; W3)
