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
| REQ-APP-005 | The app computes no ranking value of its own. Scores, prices and orderings are rendered as received (Trap 1; protects D-104, D-105, D-109). | **PARTIAL, downgraded 2026-08-19.** The citing test catches arithmetic applied DIRECTLY to a served property. An independent tester computed a savings percentage by first copying two served values into local bindings, and passed — no regex over operators can see that, and formatter-based rounding (`maximumFractionDigits`) is invisible to it too. Claiming MET on a grep was the error; the honest state is that the obvious form is gated and the laundered form is not, until **W-038** is closed. **Amended at M13-W2 (D-138):** one crossing is permitted by name. `rankRanges` compares served scores against the engine's published margin and prints no new number; `tests/unit/test_ios_client_contract.py::test_score_arithmetic_happens_only_where_an_adr_permits_it` names that file with its ADR and fails on a second file. |
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
| REQ-REF-005 | A refresh runs every 12 hours without a human, and a human can find out that it stopped running at all. **Silence must not be indistinguishable from success.** | **MET agent-side (W3), D-130; ONE owner command away from live.** `deploy/com.hcs.modelranking.refresh.plist` — `launchd` with `StartInterval`, chosen because `cron` does not fire a trigger missed while the machine slept, and on a 12-hour interval that is a SKIPPED cycle rather than a late one. **The agent does not install it:** loading a background job onto someone's machine is the owner's action, and the plist documents the two commands. The finding-out half is live now — `runner` reports cycle age, ARTIFACT age, consecutive refusals, and escalates at two. |
| REQ-REF-006 | The running engine serves a replaced artifact without a restart, and a request in flight during the swap completes on consistent data. | **MET (W1), and it PINS behaviour that already existed.** Measured by hand before the milestone was planned, now asserted through `TestClient`: an artifact replaced under a live app changes the next response. The test exists because making the adapter hold one long-lived connection is a reasonable-looking optimisation that would silently break every future refresh. |
| REQ-REF-007 | Ingestion never runs on the serving host (D-116). The refresh produces an artifact and hands it over; it does not reach into a serving process. | **PARTIAL, and stated rather than claimed.** The STRUCTURAL half is enforced and tested: an AST check asserts `refresh.py` imports nothing from `app.adapter`, and the refresh only ever hands over a file. The PHYSICAL half cannot be met today — nothing is deployed, so the owner's Mac is both the serving host and the only host there is. The separation becomes physical when D-123 discharges; until then this row is honest about being half a requirement. |

## M10 — the router (REQ-RTR) and the guards, added at W1

D-126 ruled the router at M8 — *"the router picks the QUESTION; the engine answers it"*, and it may
never say a model is good — and it was never given a REQ-ID or a wave until the owner asked where
it had gone. These are written here at W1, before any code.

**Measured before planning:** the on-device options cost **zero app bytes** and send nothing off the
phone. `FoundationModels` needs iOS 26 and an Apple Intelligence-eligible device; `NLEmbedding`
needs iOS 13 and covers every device this app targets (deployment target 18.0).

| REQ-ID | Requirement | Status |
|---|---|---|
| REQ-RTR-001 | A user types a question in their own words and the app opens the surface that answers it. The router's choice is SHOWN and changeable with one tap (D-126). | **W1.** |
| REQ-RTR-002 | **The router can only ever yield one of the nine category ids.** A recommendation, a model name, prose or an injected instruction is discarded and the user gets the manual fallback, correctable from the `Change` sheet (the chips became that sheet at M13-W3). Where the framework allows it the closed set is a SCHEMA constraint, not a prompt instruction. | **W1.** |
| REQ-RTR-003 | The router is never required. Unreachable, ineligible, disabled, slow or wrong — the product still works through the `Change` sheet (a chip until M13-W3), and says which happened. | **W1.** "Slow" became enforced at M13-W3: `TieredRouter.modelTimeout` hands a question to the wording tier after eight seconds. |
| REQ-RTR-004 | Nothing typed reaches the ENGINE, and nothing the engine serves is influenced by the router beyond which surface is opened. The scoring path is untouched (D-104). | **W1.** |
| REQ-RTR-005 | *(verified against the real on-device model by the owner on 2026-08-23 — it warned.)* A question the catalogue does not measure routes to `assistant` **and says so** — that it is not measured here and is being answered with the general chat ranking. | **W1.** |
| REQ-GRD-001 | A refresh REFUSES a candidate whose evidence moved upward in a way ordinary upstream movement does not produce. It refuses; it never judges and publishes. | **MET (W2), D-132.** Two axes — more than a quarter of a surface's models being names never seen before, and a median price moving more than a quarter in either direction — with ordinary movement MEASURED at 0% on both before either threshold was chosen. A surface returning from blind is exempt, and a single genuine launch publishes. |
| REQ-GRD-002 | No refresh can be made to allocate without bound by an upstream: every paginating client caps total accumulated rows and bytes. | **W3 DONE.** `_MAX_MERGED_ROWS = 2_000` in `arena.py::_paginate`, raised loudly. Set to 2,000 and not 5,000 because `_MAX_PAGES * _PAGE` is exactly 5,000 — the first bound written was arithmetically unreachable. `tests/unit/test_arena_client.py`. |
| REQ-GRD-003 | The refresh states its environment assumptions as CHECKS, not assumptions. | **W3 DONE.** `refresh.py::environment_problems` refuses a group/world-writable target directory and a non-finite or non-positive clock; `write_status` substitutes the wall clock when the reported one is not finite, because the record reporting a NaN clock crashed on serialising it. `tests/unit/test_refresh.py`. |
| REQ-EVI-002 | The population the engine actually ranks — reconciled AND priced — has a NAME in the code, and calibration must call it. | **W3 DONE.** `rank.py::ranked_population` names it; `scripts/arena_calibration.py` reaches it and REFUSES to size a threshold without an artifact rather than falling back to the board. `tests/unit/test_ranked_population.py` — including the gate that fails any future script sizing a threshold without importing it (V4C-49). |
| REQ-REV-001 | K.7 is executable in a single-agent lane: a wave-close review row that passes must cite a review record declaring `seat: independent`, and a cited review record that does not exist fails in every era. | **M11-W1 DONE.** `scripts/wave_check.py::review_seat_problems`, `scripts/check_records.py` (`seat` schema), D-133. Citing test: `tests/unit/test_review_seat_gate.py`. |
| REQ-IOS-001 | The Engine layer is executed by a gate: `Router`, `EngineClient` and their boundaries have tests that run from the command line and are wired into `make check` and `runner`. | **M11-W2 DONE.** `ios/Package.swift` compiles the SHIPPING sources (target `path` = `ModelRanking/Engine`, no second copy). 18 tests in `ios/EngineTests/`. `make swift-test` is in `check:` and in `runner`. |
| REQ-IOS-002 | The router's boundary is proven IN SWIFT: no path yields an id outside the nine, every tier can be absent without blocking the screen, and an unmeasured question reaches the surface flagged as unmeasured. | **M11-W2 DONE, after the independent review found the third clause was NOT.** `ios/EngineTests/RouterBoundaryTests.swift`. Two seams had to open: `TieredRouter.model` (the fallback chain was unreachable from a test on a machine that has FoundationModels) and `SimilarityRouter.floor` (a mutant setting `unmeasured` permanently false, and one raising the floor to a value cosine can never reach, both survived all 18 tests — the only unmeasured assertion was on a struct the test built by hand). Both sides of the floor are now driven, and the review's surviving mutants are killed 8 of 8. |
| REQ-IOS-003 | The 503 the client is required to render honestly can be PRODUCED on demand, so the branch that renders it is reachable by a test. | **M11-W3 DONE.** `tests/unit/test_unavailable_after_boot.py` — the artifact is replaced after boot, which is what a refresh publish does. W-039's claim that no live path exists was measured false. |
| REQ-API-010 | `/v1` gives ONE account of a query: the `ranking` array and the `picks` array cannot disagree about what was ranked. | **M11-W3 DONE.** `/v1/budgets` publishes the caps (D-134). `tests/unit/test_budgets_endpoint.py` filters the served ranking by the served cap and asserts it equals the served `eligible_count`, on real data across three surfaces and two budgets — the endpoint is checked against the engine, not against itself. |
| REQ-RUN-001 | The product has been operated by a person against a running engine, and what was asked and what came back is written down — including anything that looked wrong. | **M11-W3 MET.** The owner walked the app on 2026-08-22 and found **three defects in one session**, none of which any gate had caught across eleven milestones: W-063 (the on-device router could not decline, so unmeasured questions came back as confident measured matches), W-064 (the selected surface was not shown first), W-065 (the preview repeated the picks; the category strip reset on every selection). Screenshots at `~/Desktop/ss for test`. All three became RED tests before any fix; six mutants, six killed. |
| REQ-RUN-002 | The 12-hour refresh has completed at least two unattended cycles on the schedule, and the status file it left is read back and reported. | **PARTLY MET, and the split is the point.** The schedule is installed and launchd has executed a REAL cycle — `runs = 1`, `last exit code = 0`, and it **published**: `outcome: published`, reason *"the served content changed"*, nine surfaces answering, the artifact replaced under a running engine without breaking it (714 tests green afterwards on the new artifact). So the production path is proven end to end. What is NOT met is the literal criterion: that cycle was kickstarted by the owner, and *"two cycles ON THE SCHEDULE"* means two 12-hourly firings. Owner ruling 2026-08-24: trigger it on demand, verify the schedule later. Tracked as W-054. |
| REQ-GOV-001 | Every ADR cited anywhere in this repository exists; `C2b` counts something it can actually reach. | **M12-W1 DONE.** D-119 and D-120 written (26 files cited D-120 as a frozen contract and it had no record). `tests/unit/test_adr_citations.py` fails any citation to an unwritten ADR in the project band, and any unexplained gap in the numbering. `C2b` groups on CONTROL identifiers and is dischargeable by naming the ADR that reviewed the control: `tests/unit/test_c2b_counter.py`, 9 tests, plus the `--self-test` probe rewritten because it proved a version of the rule the field could not produce. |
| REQ-LOC-002 | Text matching in the client is correct under a Turkish locale, pinned by a test that SETS the locale rather than inheriting it. | **M12-W1 DONE.** `Router.swift::matchesFilter` folds through a pinned `filterLocale`, not the reader's. `ios/EngineTests/OwnerSessionDefectTests.swift` — and the test that matters asserts the CHOICE, because a mutant restoring `Locale.current` survived every behavioural test on a machine whose process locale happens to fold like English. |
| REQ-CMP-001 | Every number a reader meets carries, beside it, something that says what it means without domain knowledge — including a RANK where the scale is arbitrary. | **M12-W2 DONE.** `rankOf` and `scaleExplanation` in `ios/ModelRanking/Engine/Router.swift`; rendered under every pick. `161.7 ECI` now reads `#1 of 58 · an overall capability index — the scale has no fixed maximum`. The exact number is never replaced. **Amended at M13-W4 (D-140):** for ECI alone the number is no longer printed, and its rank range is; the payload still carries it. An unknown metric explains nothing rather than guessing: a missing explanation is a gap, a wrong one is a lie. |
| REQ-CMP-002 | Price is expressed in a unit a person outside this industry uses, without removing the exact figure. | **M12-W2 DONE.** `priceInPages` — `$10/1M` gains `about $10 per 1,500 pages of text`. Below a cent a page the wording switches to what a whole book costs, because `about $0.00 per page` would be worse than the original. |
| REQ-CMP-003 | Every surface name says what the surface measures, in words a non-specialist would choose. No two surfaces begin with the same word. | **M12-W2 DONE.** Six renamed in `src/app/workflows/categories.py`; `Agentic coding` unchanged BY OWNER RULING and the reverted rename is recorded in `tests/unit/test_category_titles.py`. The collision test caught the lead agent breaking that ruling on the council's advice. |
| REQ-DSC-001 | A limitation that is a property of a SOURCE is stated once per source; a limitation that is a STATE of the data keeps its warning treatment (D-135). Every fact remains reachable. | **M12-W2 DONE.** `classifyDisclosures` classifies without parsing text — `age_days == null` is structural, a number is a state — and deduplicates the two fields that told five surfaces the same fact twice in the same orange. `testEveryFactSurvivesClassification` is D-135's own test and must never be deleted. |
| REQ-BGT-001 | A reader can choose a budget in the app, and the answer changes when they do. | **RETIRED at M13-W3** by the signed plan (§2 W3, "remove both top strips"), on the 2026-08-31 council's ballot E, unanimous for removing the strip (`docs/handovers/handover_m13-start.md` §6), second-opinion Q4, and the owner's own note. The app now asks every surface at `unlimited`, and `/v1/budgets` stays on the engine for other consumers (D-134, REQ-API-010). The evidence below — the strip, `BudgetOption` and its tests — was deleted with the code, and what it said was true of M12. **Was: M12-W3 DONE.** `ContentView.swift` — `budget` is `@State` and the strip offers the caps `/v1/budgets` publishes (D-134), so the app does not hardcode what `low` means. `ios/EngineTests/` proves the CHOSEN budget is what the engine is asked, which is the half a picker can silently get wrong: updating state and sending the old value looks identical on screen. `unlimited` stays the default — a reader who has not said what they can spend has not asked to be limited. |
| REQ-LOC-001 | `/v1` returns the FACTS behind each sentence; the client composes the sentence, in English or Turkish, from those facts alone. | **M12-W4 DONE for the pick sentences; the notices are NOT localised and D-136 says so.** `why_fact` and `trade_off_fact` are published (D-136); `ios/ModelRanking/Engine/Language.swift` composes both languages from them, and `tests/unit/test_why_facts.py` asserts every number the English prose quotes is in the fact — which is what makes it one source of truth instead of two that agree today. It caught the pair disagreeing on its first run. |

## M13 — the instrument (REQ-FIX), added at W1 before any code

Four defects, every one of them reproduced against the shipping functions before this section was
written. Three were found by an independent second-opinion review that read the code without the
council's brief; the fourth affects how this repository reports its own health, which is why it is
here rather than in a tooling backlog.

**The through-line:** each of these is a check that says yes to something it should refuse. A
frontier that keeps a dominated row, a startup probe that admits a database the serving path cannot
read, a fingerprint blind to a change the reader sees, and a runner that scores an unrun leg as a
pass. This project has paid for that shape before — W-023 and W-058, both "healthy to every
existence check, answering nothing".

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-FIX-001 | Pareto dominance admits equality on one axis: a row is dominated when another is at least as good on BOTH quality and cost and strictly better on at least one. Both the model engine and the subscription engine agree. | **M13-W1.** |
| REQ-FIX-002 | Startup refuses an evidence database the serving path cannot read. A database carrying `scores`, `pricing` and a non-empty `px_median` but missing a table a ranking joins is REFUSED, not admitted. | **M13-W1.** |
| REQ-FIX-003 | A change that alters the attribution a reader is shown changes the refresh fingerprint, so the artifact publishes. Attribution is a licence obligation (REQ-LIC-001), not a display detail. | **M13-W1.** |
| REQ-FIX-004 | `runner` cannot report a leg it did not run as a pass. An absent environment is `SKIPPED`, and any skip prevents the all-green claim. | **M13-W1.** |

## M13 — say only what we know (REQ-UNC), added at W2

The display is made honest BEFORE it is redesigned. W3 removes the controls that currently slow a
reader down; these are the statements that stop the remaining numbers from overstating.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-UNC-001 | Where the engine's own `close_call` margin says two models are indistinguishable, the screen does not present them as ordered. Every position is shown as the range of places the margin allows (`#1–27 of 50` for today's `expert` leader), so two models inside the margin of each other always have overlapping ranges; how many the benchmark cannot separate from the leader is stated once per ranking. **Amended 2026-09-15 by the owner**: the plan's text said "render a shared band" (council ruling D1), and the W2 review measured bands printing 47 within-margin pairs (45 on raw scores) as ordered. | **M13-W2.** The margin is published on `/v1/categories` (D-138); ranges are `ios/ModelRanking/Engine/Uncertainty.swift`; cited by `ios/EngineTests/UncertaintyTests.swift` (the overlap as a property over every shipping margin) and `tests/unit/test_uncertainty_contract.py`. |
| REQ-UNC-002 | Nothing on screen calls a coverage count a confidence. The reader is told how many independent benchmarks measured the pick, and how old the oldest of them is. Verified by: a pick whose secondary is more than 180 days old carries that age. | **M13-W2.** A second board older than 90 days no longer upgrades the count (council ruling A3, W2 first half). The pick states the primary's run date and the second board's age in days, which are both boards' ages; the second board's age is published under D-138 and composed by `evidenceBreadth`. |
| REQ-UNC-003 | Every score source carries a date, or the product names the one that does not. | **M13-W2.** `terminalbench`'s `Run date` is read. The boards that publish no evaluation date are named in `evidence_dating_note`, and an undated second board is named in the evidence line. **The shipping artifact predates the terminalbench fix** and shows it undated until the refresh rebuilds it. |

## M13 — the question is the front door (REQ-ASK), added at W3

The owner's report, translated from Turkish: *"it felt like a search bar, not an AI"*. The question
field becomes the only input on the home screen; the two strips of controls above it go, and the
correction they offered survives as a `Change` sheet.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-ASK-001 | The question field is reliably focusable, raises a keyboard, and can be submitted without one. | **M13-W3 — PARTIAL.** Explicit focus state, a visible send button, submission from Return and from the button, no duplicate submissions. The submission rule is `FrontDoor.swift::canSubmit`, cited by `ios/EngineTests/FrontDoorTests.swift::SubmissionTests` and pinned in the view by the source-contract test. **Verified on the simulator: focus** (a caret on the first tap; the field gave no response before). **NOT verified: the software keyboard, typing, Return and the send button.** The simulator raised no keyboard for Safari's own address bar either, and synthetic keystrokes do not reach it from the agent's environment. The owner verifies both keyboard paths (plan §4). No sentence may say this was verified on a device (plan §7). |
| REQ-ASK-002 | The screen shows what it understood, and it can be corrected in one tap: `"prove a theorem" → Mathematics` renders with the reader's own words, and a correction reaches every one of the nine surfaces. | **M13-W3.** `echoLine` and `surfaceChoices` in `FrontDoor.swift`; cited by `FrontDoorTests.swift::EchoTests` and `AlternativeSurfaceTests`. **One tap** where the wording tier answered: it offers its next two surfaces when it matched, and its two closest when it declined. **Two taps** otherwise (`Change`, then the surface): the model tier returns a single choice, and a question below the similarity floor has nothing near it to offer. |
| REQ-ASK-003 | A question the catalogue does not measure returns a ranking AND a statement, above it, of what that ranking cannot tell the reader. It is never silently answered as if measured; `tier = manual` may not carry `unmeasured = false`. | **M13-W3.** `routingNotice` in `FrontDoor.swift`; `TieredRouter`'s manual outcome is now unmeasured; the wording tier declines through `CategoryHints.unmeasuredHints` (review BLOCKING-1: it used to answer a photo question from `everyday` as measured). **The trade-off, measured (re-review NEW-1):** wording cannot separate a question about a photo from a task that involves one, and no threshold divides the two, so some measured tasks are declined too. Each such decline offers the closest surfaces as one-tap alternatives. A false decline costs the reader a tap; the error REQ-ASK-003 forbids would cost them the truth. Cited by `FrontDoorTests.swift::UnmeasuredQuestionTests`, which route the wrong-modality and wrong-axis questions through the SHIPPING `SimilarityRouter`, and by the inverted `RouterBoundaryTests.testWithNoTierAtAllTheReaderStillGetsASurface`. |
| REQ-ASK-004 | A slower response for a previous selection can never overwrite the current one. | **M13-W3.** `RequestGate` in `FrontDoor.swift`, applied to every load result in `ContentView.load()` AND to the routing result in `ask()`, which a `Change` selection invalidates (review BLOCKING-2: a late routing result used to replace the reader's newer choice). Cited by `FrontDoorTests.swift::RequestGateTests` and the source-contract test. |

## M13 — the card says what a number is out of (REQ-CMP-004), added at W4

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-CMP-004 | A score is shown with its ceiling where one exists (`Score 83.5 / 100`), with its scale NAME where the scale is unbounded but published (`Score 1504.2 Elo`), and as a rank alone where neither exists (ECI). No two surfaces' scores are presented as comparable. | **M13-W4.** `ios/ModelRanking/Engine/Scores.swift::scoreText` and `figuresLine`, rendered by `PickRow` and `RankedRow`. Cited by `ios/EngineTests/ScoresTests.swift::ScoreFormTests`, with one test per metric family, each in both languages, and by `tests/unit/test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line`, which pins both call sites (W4 review MAJOR-1: replacing either call with a hand-built `Text` stayed green before it). **The comparability clause is met per METRIC FAMILY.** Two surfaces on the same family, `coding` and `agentic-coding` (both `% resolved`), share the form and are told apart by their section titles; putting the benchmark's name on the figures line is queued to M14 (W4 review MINOR-5). A rank-only metric with no rank to show keeps the engine's own number (MINOR-8). D-140. REQ-DTL-001/002 moved to M14 under council ruling F2. The same wave renames `budget_pick` to `AFFORDABLE PICK`, because no budget was set, and stops rendering a sub-dollar price as `$0` (`CheapPriceTests`). |
| REQ-CMP-004 **(amended M14-W4 by D-143; the row above is the M13 rule and no longer describes the product)** | An Elo score is shown out of 100 against the surface's pinned anchor, not as `Score 1504.2 Elo`; a bounded percentage is shown as it was; ECI is still rank-only. The scale NAME is not put in front of the reader on a card or a row. | **M14-W4.** `ios/ModelRanking/Engine/Scores.swift::scoreText`. Cited by `ios/EngineTests/ScoresTests.swift::OutOf100Tests`. The M14 closure seat found the row above still stating the superseded rule (MAJOR-5); it is kept, marked, because M13's records cite it. |

## M14 — the catalogue answers questions people ask (D-142)

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SRC-011 | Each LMArena board is stored under its own source id AND its own benchmark label, taken from the registered board table and never defaulted; an unregistered source id is refused. No two boards share either identifier. | **M14-W2.** `src/app/clients/arena.py::ARENA_BOARDS`, `src/app/workflows/ingest.py::ingest_arena`. Cited by `tests/unit/test_arena_client.py::test_ingest_stores_each_board_under_its_own_benchmark` (through the real entry point; kills the review's MAJOR-1 mutant), `test_ingest_refuses_a_source_no_board_claims`, `test_each_board_carries_its_own_source_id_and_benchmark`. |
| REQ-SUR-001 | Two surfaces, `document` and `factuality`, rank only their own board, each on its own Elo scale (D-105), with floors set by the rule the product ships (D-145). | **M14-W2.** `src/app/workflows/categories.py`. Cited by `tests/unit/test_categories.py::test_the_two_board_surfaces_rank_only_their_own_board`; both answer all three budgets on the live artifact (`docs/plans/m14-wave-2-close.md`). |
| REQ-GAP-001 | A question the router declines is recorded on the device with its text and a count; a router failure (manual tier) is not a gap; nothing recorded leaves the device; the stored entry is bounded in characters and in bytes. | **M14-W3.** `ios/ModelRanking/Engine/FrontDoor.swift::GapRegister`, `recordsGap`, `GapRegisterStore`. Cited by `ios/EngineTests/FrontDoorTests.swift::GapRegisterTests`, `GapRegisterHardeningTests`, and `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device`. |
| REQ-GAP-002 | The owner can read the register in the app, most-asked first, and clear it. | **M14-W3.** `ios/ModelRanking/ContentView.swift` `gapSheet`; order by `GapRegister.ordered`, cited by `FrontDoorTests.swift::GapRegisterTests`. Read on a running app: owner, pending (plan §4). |
| REQ-SCR-001 | Every card and row shows a score out of 100 where an honest conversion exists; on an anchored Elo surface no card sentence names Elo. | **M14-W4.** `ios/ModelRanking/Engine/Uncertainty.swift::scoreOutOf100`, `anchoredFact`; cited by `ios/EngineTests/ScoresTests.swift::OutOf100Tests`, `OutOf100SentenceTests`, and `tests/unit/test_ios_client_contract.py`. ECI stays rank-only (D-143). |
| REQ-SCR-002 | The conversion is per surface and strictly monotonic: it never reorders a ranking. | **M14-W4.** Cited by `ScoresTests.swift::testTheConversionNeverReordersOnAnyPinnedAnchor` (every pinned anchor, ±400 Elo at 0.1). |
| REQ-SCR-003 | No surface's anchor is taken from the current board, and a recalibration cannot move it. | **M14-W4.** `CategorySpec.score_anchor` (D-146). Cited by `tests/unit/test_uncertainty_contract.py::test_every_elo_surface_publishes_its_pinned_score_anchor`, `test_a_recalibration_cannot_move_the_anchor`, and the row pins in `test_ios_client_contract.py` (review M-4 mutant). |
| REQ-SCR-004 | Ties are exactly the engine's: rank ranges use the native margin, and the tie note states that margin on the /100 scale. | **M14-W4.** `Uncertainty.swift::leaderSentence`. Cited by `ScoresTests.swift::testTheLeaderNoteSpeaksPointsWhenAnchored`. Amended by D-146 clause 3 (accepted). |

## M15 — the detail screen (REQ-DTL), added at W2

**REQ-DTL-001/002 were carried from the M13 council's ruling F2 and moved into M14 by the M13
closure report, where they were not built** — while the M14 plan leaned on them as the mitigation
for taking the metric name off every card (D-143). The M14 closure seat found the screen did not
exist (`docs/warnings.ledger.md` W-105). They are written as criteria here, with citing tests, so
the next milestone cannot inherit them as prose again.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-DTL-001 | A reader can open one model from a pick OR from any row of the ranking and see, for that model on that surface: the score as the card shows it, the price in both the per-million and the per-pages form, and the surface's tie margin. Nothing on the screen is computed by the client. | **M15-W2.** `ios/ModelRanking/Engine/Detail.swift::detailFacts`, rendered by `ContentView.swift::ModelDetail`. Cited by `ios/EngineTests/DetailTests.swift::DetailFactTests` (price in both forms, the margin on the board's own scale) and `tests/unit/test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself`, shown RED on a mutant that stops the ranking rows opening it. |
| REQ-DTL-002 | The metric's name and the engine's own number on the board's own scale are available on that screen wherever the card does not show them — the converted Elo surfaces and rank-only ECI — with the board named and its result dated, or named as undated. | **M15-W2.** Same composer. Cited by `DetailTests.swift::testTheUnitTheCardHidesComesBackHere`, `::testARankOnlyMetricStillStatesItsNumberHere`, `::testAPercentageIsNotRestatedAsAMeasuredValue` (it does not repeat a unit the card already prints), `::testAnUndatedBoardSaysItIsUndated`. |

## M15 — the surfaces the measurement chose (REQ-SUR), added at W3

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SUR-002 | Three surfaces — `vision`, `search`, `search_factuality` — each rank ONLY their own board, on their own Elo scale (D-105), with every threshold derived by the rules the product ships and recorded before the surface is served. Each is reachable by a question asked in a reader's own words. | **M15-W3.** `src/app/workflows/categories.py`; thresholds in `docs/reviews/m15-category-calibration.md`. Cited by `tests/unit/test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query` (board isolation through `category_ranking`), `::test_every_surface_names_the_source_its_board_arrives_on` (the disclosure seam, all fourteen pairs), `tests/unit/test_uncertainty_contract.py::test_every_elo_surface_publishes_its_pinned_score_anchor`, and `ios/EngineTests/FrontDoorTests.swift::testTheTwoNewSurfacesAreReachableByAsking` extended to all three with the real embedding router. |
| REQ-SUR-003 | A board the engine cannot recommend from is REFUSED, with the count that refused it on record — never served with a threshold invented to make it fit. | **M15-W1/W3.** `docs/research/m15-board-survey-2026-09-21.md` (all 22 boards counted), `docs/reviews/m15-category-calibration.md` §"What was refused". Cited by `tests/unit/test_arena_client.py::test_an_unregistered_board_is_refused_and_never_defaulted` and `::test_every_registered_arena_board_is_attributed_and_floored`. |


## M16 — what the engine publishes about a price and a floor (REQ-FLR, REQ-PRC), added at W1

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-FLR-001 | `/v1/categories` publishes each surface's `min_quality` on that surface's own scale, as its own field — never derived from `score_anchor`, which holds the same value on every Elo surface today and moves for a different reason (D-152, D-146 clause 2). | **M16-W1 (engine half).** `src/app/adapter/main.py::categories`. Cited by `tests/unit/test_uncertainty_contract.py::test_every_surface_publishes_the_floor_it_recommends_from`, which moves one surface's FLOOR and not its anchor and is shown RED on three mutants: the field dropped, the field served from `score_anchor`, and the floor moved. |
| REQ-FLR-002 | The detail screen shows that floor as the line below which the product does not recommend, in both languages, composed in the Engine from the served fact. | **MET (M16-W2).** `ios/ModelRanking/Engine/Detail.swift::detailFacts` fact 8, through `scoreText` with the card's anchor. Cited by `ios/EngineTests/DetailTests.swift` `testTheFloorIsShownOnTheCardsScale`, `testNoFloorIsInventedWhenTheEngineSendsNone`, `testARankOnlyFloorIsStatedInItsOwnUnit`, and the Turkish-screen test; both detail doors pinned in `tests/unit/test_ios_client_contract.py`. W-112 FIXED. |
| REQ-PRC-001 | A surface whose price leaves something out says so on `/v1/categories` as a CODE (`price_excludes`), not as a sentence, and only the surfaces it applies to carry it (D-153, D-129: the app owns its languages). | **M16-W1 (engine half).** `src/app/workflows/categories.py::CategorySpec.price_excludes`, served by `categories()`. Cited by `tests/unit/test_uncertainty_contract.py::test_only_the_search_surfaces_say_the_search_call_is_not_in_the_price`, shown RED on a mutant that gives every surface the code. |
| REQ-PRC-002 | Wherever the app shows a price for `search` or `search_factuality`, it also says that a search call is not in it. | **MET (M16-W2).** One wording, `priceExclusion` (`Detail.swift`), on the pick card's price line, the detail screen, once under the home screen's ranking preview and once under the full ranking; each view is pinned by `tests/unit/test_ios_client_contract.py::test_every_place_that_prints_a_search_price_says_what_it_leaves_out`. Cited by `DetailTests` `testTheSearchSurfacesSayTheSearchCallIsNotInThePrice` and `testNoCodeOrAnUnknownCodeSaysNothing`, and `EngineClientTests` `testTheFloorAndThePriceExclusionDecode` on a payload copied from the live route. W-119 FIXED. |
| REQ-REF-008 | The engine refreshes its own artifact once a night inside 23:00-01:00 local and once at startup when no good cycle is on record within a day, through `refresh.py`'s entry point only, in a child process a hang, crash or kill of which cannot block or end the server; it is off by default and refused outside a development environment (D-151, D-154, D-116). | **M16-W2.** `src/app/adapter/nightly.py`, started in `main._lifespan`. Cited by `tests/unit/test_nightly_refresh.py`: the window and once-a-day arithmetic, the catch-up rule, a hanging child killed at the timeout, a raising and a failing child, one killed mid-publish (live artifact byte-identical, lock released), `/health` and `/v1/categories` answering while a child hangs through `TestClient(app)`, and production refusing to boot with the switch on. After the independent review and security pass: a killed, unstarted or crashed cycle reported on `/health`, no second cycle in one night, a late run on waking only on day-old data, the child's environment allowlisted and its output bounded, and the switch rechecked at start-up; the author's 19 mutants of `nightly.py` over three rounds all RED, besides the seat's own 23 (`docs/reviews/m16-wave-2-review.md`). |
| REQ-REF-009 | A source that fails a cycle keeps serving its last good data -- every source, the required ones included -- for 30 days from when it last arrived in a served cycle; past that its surfaces drop and the refresh publishes the rest rather than refusing. What is carried or expired, and how old, is on `/health` and in the refresh record; `/v1` and the app do not change (D-144 as ruled, D-156). | **M16-W3.** `src/app/workflows/build.py` (`Carry`, `CARRY_MAX_AGE`), `src/app/workflows/refresh.py` (reads the build's own `--report-out`; `_surfaces_fed_by` for the `degradations` exemption; `sources_last_ok`), `src/app/adapter/nightly.py` (`refresh_carried`, `refresh_expired`). Cited by `tests/unit/test_carry_forward.py` (build: carried, expired, fresh, no live artifact, Epoch, pricing, the CLI), `tests/unit/test_refresh_carry.py` (the 2026-09-20 incident through the real cycle, the 30 days not restarted by a carry, an expired surface published, a required source past its age failing) and `tests/unit/test_nightly_refresh.py` (`/health`). W-116 FIXED. |
