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
**Status:** **CLOSED 2026-08-17 by D-116** (Fly.io; the evidence database is a shipped artifact, not a managed datastore). Open for 11 days short of a year of project time and through five milestones, because the decision existed in a plan and its ID pointed at the wrong ADR.
**Asked on:** 2026-08-06
Research suggests Supabase or Cloudflare Workers for the serving layer. No decision needed before the API milestone.

> **Update 2026-08-16 (M6 planning).** "No decision needed before the API milestone" has expired —
> M6 *is* the API milestone. The deferral also hid a defect: `docs/plans/m4-plan.md` records Fly.io
> as the owner's preference and cites an ADR ID that collides with the ratified D-110, so the deploy
> target is simultaneously "recorded" in a plan and "not chosen yet" here. **A preference in a plan
> is not an ADR.** M6-W4 closes this with a real ID (D-116) that supersedes the collision, and this
> question moves to closed with that ID next to it. Recording a preference again would not close it.

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

**Statement:** assistant-category thresholds recalibrated against live data as a data edit in categories.py, rationale recorded.
**Acceptance:** thresholds derived from the live board's distribution, not assumed; method + evidence committed.
**Citing test:** tests/unit/test_recommend_assistant.py::test_assistant_budget_floor_uses_elo (asserts the shipped floor).
**Status:** DONE (M3 closure, 2026-08-15 — docs/reviews/m3-elo-calibration.md; min_quality 1300→1400, close_call 5→8, value_window 30 kept-and-justified)

## 11. M4 — Make the plan answers real (REQ-CAN / REQ-ING / REQ-SUB / REQ-REC)

> Added 2026-08-15 at M4 closure, closing quality-gate finding F-1: the M4 REQ-IDs were specified
> in the signed `docs/plans/m4-plan.md` §2 and had not been copied here. Canonical criterion text
> lives in the signed plan; this section is the PRD's index of it, with the shipped status.
> Full trace (criterion → implementing file:line → citing test) is `docs/coverage-by-req.md`.

### REQ-CAN-004 — Registry expansion with a self-defending rule table

**Statement:** adding a canonicalization rule is a cheap, tested, reviewable act; the rule table proves variant-before-parent ordering and sibling non-collision, and carries rules for the families live sources currently drop.
**Acceptance:** every rule canonicalizes to itself; no duplicate ids or patterns; a live-name corpus resolves to the right model; plan-name drops fall to 0.
**Status:** DONE (M4-W1, commit 17eec69 — plan-name drops 2→0; droplist record docs/reviews/m4-w1-registry-droplist.md)

### REQ-ING-009 — Provider model rosters as a second documented source

**Statement:** a provider's own model-availability page is ingested as a SEPARATE source with its own provenance and `last_verified`; a plan links to a roster model only through the registry, never guessed; a roster naming an unknown plan aborts.
**Acceptance:** roster links carry `link_source`/`source_url`/`last_verified`; plan-page links win ties; the recommendation text states WHICH source named the model.
**Status:** DONE (M4-W2, commit bc9c6de — assistant coverage 3/9 → 5/9; data/rosters.yaml carries the probe log for the providers that publish no roster)

### REQ-SUB-005 — Plan coverage is a measured number

**Statement:** how many curated plans can actually be ranked, per category, and for the rest WHY — separated into "no link at all" (curation gap) and "linked but no score on this benchmark" (benchmark gap).
**Acceptance:** computed by the pipeline, printed by a CLI, wired into CI; zero coverage in a category exits non-zero.
**Status:** DONE (M4-W3, commit ee5a582 — read-only by mechanism since M4 closure, `mode=ro`)

### REQ-ING-012 — One runnable production entry point builds the evidence database

**Statement:** a single command in `src/` builds the artifact end to end — schema, plans, rosters, every remote source, reconciliation, and the price medians — and is typed, linted, tested and covered like the rest of the product.
**Acceptance:** the entry point produces an artifact that serves real answers, and the counts it reports are read back OUT of the built file rather than reported by the writers that filled it.
**Why it did not exist before:** until M7 the pipeline was a heredoc inside `.github/workflows/contract-tests.yml`, invisible to every tool and run by a cron that never fired. That is the root of W-023.
**Status:** M7-W1.

### REQ-ING-013 — A partial build is a failed build

**Statement:** the builder exits non-zero and names the operator action on any hollow stage — an unreachable source, a source below its declared row floor, a collapsed reconciliation, empty price medians — and leaves no artifact behind.
**Acceptance:** each failure mode forced by fault injection; each exits non-zero; no partially-populated database survives a failed run.
**Why the floor matters:** `rank.py` JOINs `px_median`. An empty table yields zero rows and `/v1` answers 200 with no picks — a confident wrong answer that passes every existence check, including `/health`.
**Status:** M7-W1.

### REQ-ING-011 — Source health is computed, not noticed

**Statement:** how old each source's newest evidence is, reported on every run; unknown age fails TOWARD disclosure. **(a)** measure and report; **(b)** state plainly whether a fresher documented coding benchmark exists AND, if it does, ingest it.
**Acceptance:** per-source age with the same 90-day window the engine discloses on (two clocks, stated); the investigation's verdict recorded either way.
**Status:** (a) DONE (M4-W3). **(b) DEFERRED to M5** — a fresher documented source DOES exist (Epoch AI CC-BY bundle; Terminal-Bench 2.0 on HF), both proxy-403 from the build sandbox; evidence in docs/reviews/m4-w3-source-health.md §3.

### REQ-ING-010 — Epoch AI ingestion

**Statement:** ingest Epoch AI's documented CSV bundle as a source, provenance mandatory, loud-fail like every other source.
**Status:** **DEFERRED to M5** (criteria diff, owner-accepted at the M4 gate). epoch.ai is proxy-403 from this container; no parser was written against an unseen shape (the FP-M2-2 rule). Unblock = one out-of-sandbox fetch; the command was delivered to the owner 2026-08-15.

### REQ-REC-009 — Equivalent plans are named, not hidden

**Statement (RESTATED at M4-W4 — see D-110):** where several plans within the budget rank on the same model at the same score, the answer declares them indistinguishable, names the cheapest with its price and the monthly spread, and says which members are linked via a roster rather than their own plan page.
**Supersedes:** the signed criterion "`--subscription` returns ≥3 DISTINCT plans in `orta` and `sinirsiz` on live data", which is unachievable honestly — 4 of the 5 scoreable plans rank on the same model (measured 2026-08-15).
**Acceptance:** groups computed for every plan a label picked; built from budget-filtered rows only; keyed on plan_id, never display name.
**Status:** SHIPPED (M4-W4, commit 20312a1); **criterion restatement awaits the owner's signature at the M4 gate.**

### REQ-REC-010 — Scores are rounded at the output boundary

**Statement:** every score reaching the JSON contract or a user-facing string is rounded to 1 decimal, exactly once, at the boundary; ranking, Pareto and threshold comparisons keep the raw value; prose deltas are computed from the ROUNDED numbers so the text cannot contradict the fields.
**Acceptance:** raw floats never reach the contract (tested through the real CLI); rounding inside the ranking is a test failure.
**Status:** DONE (M4-W4 — D-109)

### REQ-SUB-006 — Google AI Plus re-probe

**Statement:** re-probe the price M3 excluded as disputed; the row enters only on dated evidence, otherwise the exclusion is re-recorded.
**Acceptance:** the entry states WHY the dispute resolved; the model list comes from the provider's own page, never from a price tracker.
**Status:** DONE (M4-W4 — $4.99; the "dispute" was a 2026-06-08 price cut, i.e. two trackers dated either side of one change)

## 12. M5 — Rescue the coding category (implementation trace pending owner gate)

> Added 2026-08-16 from the signed `docs/plans/m5-plan.md`. Historical M4 deferral text above is
> preserved as the record of that gate. This newer section supersedes it for current implementation
> status, but no M5 item is recorded as owner-accepted until the milestone verification session.

| REQ-ID | Implemented behavior and evidence | Current status |
|---|---|---|
| REQ-ING-010 | Local allowlisted Epoch CSV ingestion with required provenance and an independent acquisition clock. Citing tests: `test_epoch_ingest.py`, `test_epoch_workflow.py`, `test_deepswe_workflow.py`, `test_epoch_staleness.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-ING-011b | Selected-row evidence partitions coding as 2 fresh / 3 stale / 5 unscored and agentic-coding as 6 undated / 4 unscored; source-global dates remain telemetry. Citing tests: `test_coverage.py`, `test_deepswe_workflow.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-CAN-005 | Effort is parsed, validated, stored, and reconciled; unknown/conflicting rows are counted. Citing tests: `test_schema.py`, `test_effort.py`, `test_deepswe_workflow.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-REC-011 | Model and plan output name ranked effort and compare only same-harness/same-source higher effort. Citing test: `test_effort.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-SUB-007 | Pinned baseline coding 1/10; Epoch coding 5/10; DeepSWE agentic-coding 6/10; cross-category union 6/10. Citing tests: `test_m5_board_measurement.py`, `test_deepswe_workflow.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-LIC-001 | Required Epoch citation is in ranking exports, both recommendation payload source lists, and README. Citing tests: `test_categories.py`, `test_recommend.py`, `test_deepswe_workflow.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-REC-012 | Board measurement carries both Gemini results and states the disagreement. Citing test: `test_m5_board_measurement.py`. | IMPLEMENTED; pending M5 owner gate |
| REQ-REC-013 | `excluded_by_budget` counts scoreable plans removed by the cap and `budget_notice` narrates it, separate from unscored/equivalent plans. Citing tests: `test_subscribe.py`, `test_deepswe_workflow.py`; contract proposed in D-111. | IMPLEMENTED; pending D-111 owner ratification at M5 gate |

## 13. M6 — The HTTP API (REQ-API / REQ-REC / REQ-LIC / REQ-SUB)

> Added 2026-08-16 from the signed `docs/plans/m6-plan.md` §2, per the M3 rule that new REQs land in
> BOTH the plan and this file. **Status for every row below is SPECIFIED — nothing is implemented.**
> The milestone freezes the owner's Ruling A into a public contract: a coding request returns BOTH
> the `coding` and the `agentic-coding` answer, and neither is presented as leading the other
> (recorded as D-115 when the milestone ratifies it).

| REQ-ID | Statement | Status |
|---|---|---|
| REQ-API-001 | A versioned, read-only HTTP surface: `GET /v1/recommendations`, `GET /v1/categories`, and the existing `/health` with its L.7 build stamp unchanged. M6 ships no mutating route, and a citing test asserts that absence — V3C-12 server-side authz is satisfied by having no mutating surface, never by claiming one is protected. | SPECIFIED (m6-plan signed) |
| REQ-API-002 | Ruling A: `task=coding` returns two answers, neither flagged as primary, emitted in a documented non-semantic order, with the envelope stating that the order carries no meaning. An explicit `task=agentic-coding` returns that surface alone. Citing test asserts two members AND that no field ranks them. | SPECIFIED (m6-plan signed) |
| REQ-API-003 | Rendering parity: `close_call`, `stale_notice`, `effort_mix_notice`, the D-111 budget notice, D-110 equivalence and per-pick `effort` appear in the JSON payload, the CSV export and the CLI output, all derived from ONE serializer. Citing test compares all three renderings of a single run field-for-field. A disclosure present in one and absent from another is BLOCKING. | SPECIFIED (m6-plan signed) |
| REQ-API-004 | An answer whose evidence carries no evaluation date says so IN THE PAYLOAD, not only in the coverage report (INV-24; the `agentic-coding` case). | SPECIFIED (m6-plan signed; M5 security deferral) |
| REQ-API-005 | Error contract: unknown task, unknown budget and a missing database each produce a stable documented error shape that fails loud and closed and leaks no filesystem path into the response body. **AMENDED 2026-08-17 (owner):** an unhealthy source is DISCLOSED in a 200 answer, never refused — refusing over stale evidence would contradict the honesty doctrine, and the fail direction for a disclosure control is toward saying more. Explicitly not a 503. | SPECIFIED, amended (m6-plan §2) |
| REQ-API-006 | Security baseline for the surface (V3C-11/12/13/51/56): CORS is an allowlist and never allow-all-with-credentials; security config is validated at startup and the process refuses to serve in production if it is wrong; the API's database handle is read-only; no plaintext credential in source. | SPECIFIED (m6-plan signed) |
| REQ-REC-014 | `equivalent_plans` carries group structure, so a machine consumer can tell which pick each plan is equivalent to and at what price. | SPECIFIED (m6-plan signed; closes W-002) |
| REQ-LIC-002 | The CSV half of `export_ranking` carries the same attribution and blend note the JSON half already carries. | SPECIFIED (m6-plan signed; M5 security deferral) |
| REQ-SUB-008 | The roster-link staleness sentence reads the roster's OWN persisted window, not the curated plan table's. Citing test proves the two windows can diverge and that the correct one is used. | SPECIFIED (m6-plan signed; closes W-008) |

**Red-test intakes carried into M6 against existing REQs (not new requirements):** W-010 against
REQ-CAN-005 (the effort counter under-reports suffix-bearing rows it cannot classify), plus W-005
(YAML alias-expansion guard) and W-009 (two migration entry points) as hardening the API boundary
creates. Each is reproduced with a failing test before it is fixed.

## M8 — the iOS client (REQ-APP), added at the wave rather than at closure

The engine's first consumer that is not a test. These were proposed in `docs/plans/m8-plan.md` §1
and belong here from the wave they are worked in, to avoid the F-1 drift the M4 gate raised.

**A standing limitation, stated once and true of every row below: this repository has no iOS test
target** (W-038). Where a criterion says "citing test", the test runs on the PYTHON side and gates
the seam between the two — it derives what the app requires from the Swift source and asserts the
engine satisfies it. That gates the contract, not the rendering. The Swift itself is unexecuted by
any gate, and a row whose only reachable evidence is a screenshot says so.

| REQ-ID | Requirement | Status |
|---|---|---|
| REQ-APP-001 | A SwiftUI app runs in the iOS Simulator, asks the engine for a recommendation and renders the real answer. No mock data in the shipping target, and no fixture JSON compiled in. | **MET** — verified against a live engine on the Simulator, `dev-a9dc034`; a citing test asserts the client carries no embedded payload. |
| REQ-APP-002 | Ruling A survives the client: `task=coding` shows BOTH surfaces with neither presented as the winner — no default tab, no first-position emphasis, no client-side sort. | **PARTIAL, downgraded 2026-08-19 after an independent tester walked through the gate.** Both surfaces render as peer sections in the order the engine sent. The citing test is a TRIPWIRE ON SPELLINGS (`sorted`/`reversed`/`shuffled`/`sort(`/`max(by:)`/`min(by:)`/`swapAt`), not a proof of absence: a hand-rolled comparison passes it, and **nothing tests the 'no default tab, no first-position emphasis' half at all.** A real proof needs a UI test asserting the two surfaces render as peers, which requires the iOS test target that does not exist (**W-038**). |
| REQ-APP-003 | Every disclosure the API sends is visible: `unavailable_reason`, `source_health` notices, `stale_notice`, `evidence_dating_note`, `effort_mix_notice`, `close_call`, `ranking_effort` and the ordering note. | **MET** — a citing test derives the disclosure field set from `Models.swift` and fails when the client stops referencing one. `ranking_effort` was found MISSING by that test and is now rendered. |
| REQ-APP-004 | The app degrades honestly: engine unreachable, 503, an empty answer and a slow response each produce a stated condition — never a blank screen and never an endless spinner. | **MET, with one case unreachable.** Verified LIVE for engine-unreachable: the engine was stopped, the app relaunched, and it stated the condition, the remedy and a retry action. `timedOut` and `offline` are new named cases, bounded by a 10-second request and resource timeout — `URLSession.shared` waits 60 seconds, which is the endless spinner this row forbids — and they are gated structurally rather than exercised. **The 503 cannot be reached at all:** M7's startup probe refuses to boot on an unbuilt artifact, so the condition that produces it has already stopped the process. Recorded as **W-039** rather than claimed as covered. |
| REQ-APP-005 | The app computes no ranking value of its own. Scores, prices and orderings are rendered as received (Trap 1; protects D-104, D-105, D-109). | **PARTIAL, downgraded 2026-08-19.** The citing test catches arithmetic applied DIRECTLY to a served property. An independent tester computed a savings percentage by first copying two served values into local bindings, and passed — no regex over operators can see that, and formatter-based rounding (`maximumFractionDigits`) is invisible to it too. Claiming MET on a grep was the error; the honest state is that the obvious form is gated and the laundered form is not, until **W-038** is closed. |
| REQ-API-010 | Any contract gap the client finds is recorded as a finding against `/v1` before any client-side workaround. **Declared class: PROCESS** — its obligation is about the record trail, not about running code. | **MET, 2026-08-19.** A process criterion CAN have a failable test once you stop testing the process and test its ARTEFACT: the frozen field set and the decision record must agree about what moved and under whose permission. `tests/unit/test_contract_change_provenance.py` asserts that D-124's one-time window is claimed by exactly one ADR, that a field the payload publishes is a field an ADR accounted for, and that no record ASSERTS the window is unspent while D-125 has spent it. It fails in both directions and it caught a real surviving false claim in `docs/closure-report-m8.md` on its first run. Closes **W-043**. |

## M9 — the refresh (REQ-REF), added at W1

The product claims to tell people what is true about AI tools right now. Until M9 its evidence was
as fresh as the last time a human remembered to run a command. These were proposed in
`docs/plans/m9-plan.md` §1 and are written here at W1, not at closure.

**Measured before the milestone was planned, and it changed the plan:** the running engine already
picks up a replaced artifact with no restart — the adapter opens a read-only connection per request,
so an atomic swap lands on the next request and a request in flight finishes on the inode it
started on. REQ-REF-006 therefore PINS existing behaviour rather than requiring new code.

| REQ-ID | Requirement | Status |
|---|---|---|
| REQ-REF-001 | One command performs one refresh cycle: build into a temporary artifact, compare it against the live one, publish only if it should be. It never leaves the live artifact worse than it found it, including when killed mid-run. | **MET (W1).** `python -m app.workflows.refresh`. The live artifact is proven byte-identical after a failed build, a raising builder, an unreadable candidate and a build that FAILS while leaving something readable — that last one is the case the obvious test misses. No `.candidate` file survives any outcome. |
| REQ-REF-002 | "Changed" is decided on the CONTENT THAT WOULD BE SERVED — not file bytes, not timestamps. An unchanged upstream produces no publish and says so. | **MET (W1).** Derived through `category_ranking`, the same function that serves, so it cannot drift from what is published. Proven insensitive to `observed_at` and to sub-precision noise; proven sensitive to a score, a one-cent price move, a model rename, a harness or effort change, a surface going blind, and the same evidence moving between surfaces. Verified against live sources: two consecutive cycles published once. |
| REQ-REF-003 | A refresh REFUSES to publish an artifact that is worse than the live one: fewer surfaces answering, or materially less evidence behind any surface. The refusal is a first-class outcome with its own exit code, not an error. | **MET (W2), D-128.** Exit 3. Refuses a blinded surface and a loss of more than a quarter of any surface, NAMING which. Deliberately does not refuse a surface growing, prices moving, or scores falling — a model getting worse is news, not damage. |
| REQ-REF-004 | Every cycle leaves a durable record of what it did and why — published, unchanged, refused or failed — carrying the numbers it decided on. | **MET (W2), D-129.** `<artifact>.refresh.json`, written on every path including failures, scratch-then-renamed so a reader never catches it torn. `runner` reads it and reports staleness, because a refresh that stopped is invisible unless something compares its timestamp to the clock. |
| REQ-REF-005 | A refresh runs every 12 hours without a human, and a human can find out that it stopped running at all. **Silence must not be indistinguishable from success.** | **W3.** |
| REQ-REF-006 | The running engine serves a replaced artifact without a restart, and a request in flight during the swap completes on consistent data. | **MET (W1), and it PINS behaviour that already existed.** Measured by hand before the milestone was planned, now asserted through `TestClient`: an artifact replaced under a live app changes the next response. The test exists because making the adapter hold one long-lived connection is a reasonable-looking optimisation that would silently break every future refresh. |
| REQ-REF-007 | Ingestion never runs on the serving host (D-116). The refresh produces an artifact and hands it over; it does not reach into a serving process. | **W3 for the operational half; the STRUCTURAL half is MET at W1** — an AST check asserts `refresh.py` imports nothing from `app.adapter`. Written at W1 because the temptation was live: the adapter has an `open_readonly` helper this module wanted, and borrowing it would have put the boundary in prose only. |
