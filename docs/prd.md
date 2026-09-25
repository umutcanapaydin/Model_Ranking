# Product Requirements (PRD) — model_ranking

> Re-structured requirements with REQ-IDs. Tests and PRs cite these IDs forever (seed A.1). Per-area prefixes: REQ-ING (ingestion), REQ-CAN (canonical registry), REQ-RANK (ranking), REQ-REC (recommendation).
>
> Format conventions:
> - Each REQ has: ID, Statement, Acceptance criteria, Customer source, Status.
> - **A status opens with one of four words** (#28, re-read against the tree on 2026-09-25):
>   **MET** (built, and the cited test exercises it), **PARTIAL** (what is missing is named),
>   **OPEN** (not built), **SUPERSEDED** (by the ADR or requirement named). A test cited as
>   `file.py:NN` is under `tests/unit/`, and `File.swift:NN` under `ios/EngineTests/`, unless a
>   path says otherwise. A status says where the requirement stands now; how it got there is in
>   git and the ADRs. `tests/unit/test_prd_status.py` refuses any other opening word.
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
**Status:** **MET.** Evidence: test_litellm_ingest.py:44, :61; test_schema.py:20; tests/integration/test_litellm_contract.py:19 (the ≥500 live check, network).

### REQ-ING-002 — Ingest SWE-bench Verified leaderboard

**Statement:** The pipeline fetches the SWE-bench site leaderboard JSON from its GitHub repository and stores every Verified entry as a score record.
**Acceptance:**
- All Verified entries present in the source file are stored with `% resolved`, run date, and raw entry name.
- The agent/harness name is parsed and stored WITH each score (a score is a model+harness pair, never model alone).
- Rows from other leaderboards (Lite, Multimodal, …) are not mixed into Verified results.
**Customer source:** research §3.1; comparison report §2 (harness retention).
**Status:** **MET.** Evidence: test_swebench_ingest.py:46, :58, :67; tests/integration/test_scores_contract.py:15. Separate licence risk: W-129 (accepted). The SWE-bench leaderboard JSON is CC BY-NC and must be resolved before any commercial launch.

### REQ-ING-003 — Ingest Aider polyglot leaderboard

**Statement:** The pipeline fetches Aider's `polyglot_leaderboard.yml` from GitHub and stores pass_rate_2 scores plus per-run cost.
**Acceptance:**
- All entries with a parseable model name are stored with score, run date, and `total_cost`.
- The known staleness of this source (updates stalled ~Nov 2025) is recorded as a source-health flag, not silently ignored.
**Customer source:** research §3.1 (Aider: coding + cost per run).
**Status:** **MET.** Evidence: test_aider_ingest.py:54, :68; tests/integration/test_scores_contract.py:24.

### REQ-ING-004 — Provenance on every record

**Statement:** Every ingested record carries provenance and versioning fields so "as of" questions and audits are answerable.
**Acceptance:**
- Every pricing and score row has non-null `source`, `observed_at`.
- A repeated pipeline run replaces the working set deterministically (same input → same output; no duplicate accumulation).
- No ingestion path scrapes an HTML page; only documented raw-data endpoints are used (D-101).
**Customer source:** research B §8 (versioned records); comparison verdict §6.
**Status:** **MET.** Evidence: test_schema.py:31; test_aider_ingest.py:77; test_litellm_ingest.py:61; test_arena_client.py:175. The no-scraping clause holds by construction: every client parses a JSON/YAML/CSV endpoint, and HTML is refused (test_arena_slices.py:539, test_epoch_bundle_fetch.py:78). No single test asserts "no HTML page is ever fetched".

## 4. Canonical model registry (REQ-CAN)

### REQ-CAN-001 — Alias reconciliation to canonical models

**Statement:** Model names from all sources are mapped to a canonical model ID via an ordered first-match rule table (vendor, display name, regex).
**Acceptance:**
- The same underlying model arriving under different aliases (e.g. `claude-4-5-opus`, `Claude 4.5 Opus medium`) maps to ONE canonical ID.
- Unmatched names are dropped with a count reported, never guessed.
- **Superseded in part by D-157 (M16-W4):** a name no curated rule matches is registered under a derived id when that id has both a price and a score (`registry.derive_identity`); the rest are still dropped and counted. Cited by `tests/unit/test_registry_derived.py`.
**Customer source:** research B §6 step 1; spike finding (alias mapping is the core IP).
**Status:** **MET.** Evidence: test_registry.py:16, :24; test_registry_derived.py:86, :101, :109. D-157 supersedes the "never guessed" clause. An unmatched name with both a price and a score now gets a derived id. D-157's status is still **proposed**.

### REQ-CAN-002 — Variant-before-parent rule ordering

**Statement:** Sub-variant rules (mini/nano/codex/chat…) precede parent-family rules so a variant's price or score never leaks into the parent model.
**Acceptance:**
- A regression test proves a `*-nano` alias does NOT match its parent family rule (the exact spike bug, reproduced red→green).
- Rule-order is covered by a test that fails if a parent rule precedes its variants.
**Customer source:** spike finding 2026-08-06 (GPT-5-nano price leaked into GPT-5).
**Status:** **MET.** Evidence: test_registry.py:29, :97; test_registry_derived.py:50.

### REQ-CAN-003 — Median price per canonical model

**Statement:** Each canonical model's reference price is the median across its alias/provider prices, not the minimum.
**Acceptance:**
- A model with multiple provider prices stores the median input and output $/1M.
- A unit test demonstrates an outlier cheap alias does not become the model's reference price.
**Customer source:** spike finding (MIN picked wrong variant); research B §7.
**Status:** **MET.** Evidence: test_rank.py:81.

## 5. Ranking (REQ-RANK)

### REQ-RANK-001 — Coding ranking table

**Statement:** The system produces a coding ranking: best SWE-bench Verified score per canonical model, joined with Aider score (when present) and median prices.
**Acceptance:**
- Output contains ≥20 canonical models with score, harness, evidence date, input/output/blended price.
- Blended price = input×0.75 + output×0.25, documented in output.
**Customer source:** research §3.2 (coding = richest category); M1 scope.
**Status:** **MET.** Evidence: test_rank.py:92, :106 (blend asserted at test_rank.py:103). No test asserts the "≥20 canonical models" count. The shipped `advisor.db` ranks 55 models on `coding` (measured read-only on 2026-09-25).

### REQ-RANK-002 — Machine-readable export

**Statement:** Rankings export as CSV and JSON artifacts suitable for the future app/API layer.
**Acceptance:**
- One pipeline command yields `coding_ranking.csv` and `coding_ranking.json` with identical rows.
- Export includes a dataset-level `generated_from` note listing sources and observation timestamps.
**Customer source:** research §7 (serving pre-computed rankings).
**Status:** **MET.** Evidence: test_rank.py:242; test_serializer_parity.py:155.

## 6. Recommendation engine (REQ-REC)

### REQ-REC-001 — Three labeled answers

**Statement:** For the coding use case and a budget level, the engine returns exactly three labeled picks: Best Quality, Best Value, Budget Pick.
**Acceptance:**
- Each pick includes: model, vendor, score(s), prices, evidence date, harness, confidence grade, and a "why / trade-off" explanation.
- Output is deterministic: same database state + same inputs → same picks.
**Customer source:** research B §1 (three clearly labeled answers).
**Status:** **MET.** Evidence: test_recommend.py:121; tests/integration/test_cli_e2e.py:106.

### REQ-REC-002 — Budget constraint filtering

**Statement:** Budget levels (low/medium/unlimited) filter candidates by blended price BEFORE any scoring; ineligible models never appear.
**Acceptance:**
- With a low budget, no pick has blended price above the low threshold.
- Thresholds are named constants covered by a test.
**Customer source:** research B §6 step 4 (hard constraints first).
**Status:** **MET.** Evidence: test_recommend.py:187; tests/integration/test_cli_e2e.py:122. The app no longer offers a budget (REQ-BGT-001 retired). The engine keeps `BUDGETS` (recommend.py:42), and `/v1/budgets` publishes it.

### REQ-REC-003 — Pareto non-dominance

**Statement:** Value picks come from the quality–cost Pareto frontier; the engine never uses a bare `score ÷ price` ratio.
**Acceptance:**
- A test proves no recommended model is simultaneously worse AND more expensive than another eligible model.
- The value pick rule (within N points of leader, cheapest) is a documented, tested constant.
**Customer source:** research B §6 step 5.
**Status:** **MET.** Evidence: test_recommend.py:219, :246; test_pareto_dominance.py:130. REQ-FIX-001 sharpens the dominance rule (equality on one axis).

### REQ-REC-004 — Confidence grading and honesty

**Statement:** Each pick carries a confidence grade derived from independent-source count, and near-ties are disclosed rather than hidden.
**Acceptance:**
- Two independent benchmark sources → High; one → Medium; the mapping is tested.
- When #1 and #2 are within the close-call threshold, the output says so explicitly (tested).
**Customer source:** research B §6 step 3; comparison verdict §6.
**Status:** **MET.** Evidence: test_recommend.py:273, :317, :338. D-139 amends the rule: an old or undated second board does not upgrade the grade. The screen shows evidence breadth instead (REQ-UNC-002).

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
**Status:** **MET.** Evidence: test_plans_ingest.py:234, :143, :75.

### REQ-SUB-002 — Curated seed dataset, live-verified

**Statement:** `data/plans.yaml` ships ≥6 plans across ≥4 providers (OpenAI, Anthropic, Google, Perplexity — owner Q1), USD/US-first (owner Q2), every value probed against a live source on entry day; curated-file validation FAILS LOUD (skip-and-count is for fetched sources, not authored data).
**Acceptance:** the real seed file parses, ingests transactionally, and meets the counts above (citing test: tests/unit/test_plans_ingest.py::test_seed_dataset_meets_req_sub_002).
**Status:** **MET.** Evidence: test_plans_ingest.py:165, :199; test_plans_staleness.py:94.

### REQ-SUB-003 — Staleness is disclosed, never hidden

**Statement:** a plan row older than the staleness window (30 days — owner Q3, stored as data) is flagged in exports and recommendation output.
**Status:** **MET.** Evidence: test_plans_staleness.py:48, :67; test_subscribe.py:206.

### REQ-SUB-004 — Re-verification cadence

**Statement:** a weekly scheduled CI job (owner Q4) fails/reminds when any plan row exceeds the staleness window.
**Status:** **MET.** Evidence: test_plans_staleness.py:81; `.github/workflows/contract-tests.yml:17` (weekly cron), `:89` (plans check). No test asserts that the workflow runs the **plans** check. Only Epoch's step is pinned (test_epoch_staleness.py:62).

### REQ-REC-007 — Subscription recommendation

**Statement:** `recommend --subscription` returns three labeled plan picks (quality/value/budget) reusing the budget/quality logic, where a plan's linked models carry the category scores.
**Status:** **MET.** Evidence: test_subscribe.py:135, :260.

### REQ-REC-008 — Stale-plan disclosure in output

**Statement:** recommendation output disclosing stale plan rows, same honesty contract as stale_notice.
**Status:** **MET.** Evidence: test_subscribe.py:206; test_rosters.py:308.

### REQ-GP-001 — GP v4.3.1 install correctness

**Statement:** `make install-check` green: PROJECT paths complete, GP-INTERNAL files absent, gates wired (make check + pre-commit + CI).
**Status:** **SUPERSEDED** by D-113 (GP v5.0), then D-155 (DevFlow v6.0) and D-161 (v6.4). The GP v4.3.1 install no longer applies. Today's equivalent is `make install-check`, a leg of `make check` (Makefile:108).

### REQ-CAL-001 — Elo threshold recalibration

**Statement:** assistant-category thresholds recalibrated against live data as a data edit in categories.py, rationale recorded.
**Acceptance:** thresholds derived from the live board's distribution, not assumed; method + evidence committed.
**Citing test:** tests/unit/test_recommend_assistant.py::test_assistant_budget_floor_uses_elo (asserts the shipped floor).
**Status:** **MET.** Evidence: test_recommend_assistant.py:169, :111. D-148/D-159 supersede the hand-set `min_quality` 1400 clause: the floor is now derived from the board. `close_call` 8 and `value_window` 30 still stand (categories.py:103-107).

## 11. M4 — Make the plan answers real (REQ-CAN / REQ-ING / REQ-SUB / REQ-REC)

> Added 2026-08-15 at M4 closure, closing quality-gate finding F-1: the M4 REQ-IDs were specified
> in the signed `docs/plans/m4-plan.md` §2 and had not been copied here. Canonical criterion text
> lives in the signed plan; this section is the PRD's index of it, with the shipped status.
> Full trace (criterion → implementing file:line → citing test) is `docs/coverage-by-req.md`.

### REQ-CAN-004 — Registry expansion with a self-defending rule table

**Statement:** adding a canonicalization rule is a cheap, tested, reviewable act; the rule table proves variant-before-parent ordering and sibling non-collision, and carries rules for the families live sources currently drop.
**Acceptance:** every rule canonicalizes to itself; no duplicate ids or patterns; a live-name corpus resolves to the right model; plan-name drops fall to 0.
**Status:** **MET.** Evidence: test_registry.py:211, :229.

### REQ-ING-009 — Provider model rosters as a second documented source

**Statement:** a provider's own model-availability page is ingested as a SEPARATE source with its own provenance and `last_verified`; a plan links to a roster model only through the registry, never guessed; a roster naming an unknown plan aborts.
**Acceptance:** roster links carry `link_source`/`source_url`/`last_verified`; plan-page links win ties; the recommendation text states WHICH source named the model.
**Status:** **MET.** Evidence: test_rosters.py:187, :295.

### REQ-SUB-005 — Plan coverage is a measured number

**Statement:** how many curated plans can actually be ranked, per category, and for the rest WHY — separated into "no link at all" (curation gap) and "linked but no score on this benchmark" (benchmark gap).
**Acceptance:** computed by the pipeline, printed by a CLI, wired into CI; zero coverage in a category exits non-zero.
**Status:** **MET.** Evidence: test_coverage.py:178, :311, :340; test_ci_coverage_gate.py:46.

### REQ-ING-012 — One runnable production entry point builds the evidence database

**Statement:** a single command in `src/` builds the artifact end to end — schema, plans, rosters, every remote source, reconciliation, and the price medians — and is typed, linted, tested and covered like the rest of the product.
**Acceptance:** the entry point produces an artifact that serves real answers, and the counts it reports are read back OUT of the built file rather than reported by the writers that filled it.
**Why it did not exist before:** until M7 the pipeline was a heredoc inside `.github/workflows/contract-tests.yml`, invisible to every tool and run by a cron that never fired. That is the root of W-023.
**Status:** **MET.** Evidence: test_build.py:118, :136, :300.

### REQ-ING-013 — A partial build is a failed build

**Statement:** the builder exits non-zero and names the operator action on any hollow stage — an unreachable source, a source below its declared row floor, a collapsed reconciliation, empty price medians — and leaves no artifact behind.
**Acceptance:** each failure mode forced by fault injection; each exits non-zero; no partially-populated database survives a failed run.
**Why the floor matters:** `rank.py` JOINs `px_median`. An empty table yields zero rows and `/v1` answers 200 with no picks — a confident wrong answer that passes every existence check, including `/health`.
**Status:** **MET.** Evidence: test_build.py:154, :160, :167; test_build_artifact_safety.py:116, :133. D-144/D-156 amend the "unreachable source fails" clause. A source with last-good data under 30 days old is carried (REQ-REF-009). It fails only when there is nothing to carry.

### REQ-ING-011 — Source health is computed, not noticed

**Statement:** how old each source's newest evidence is, reported on every run; unknown age fails TOWARD disclosure. **(a)** measure and report; **(b)** state plainly whether a fresher documented coding benchmark exists AND, if it does, ingest it.
**Acceptance:** per-source age with the same 90-day window the engine discloses on (two clocks, stated); the investigation's verdict recorded either way.
**Status:** **MET.** Evidence: test_coverage.py:217, :297. Part (b) was delivered as REQ-ING-010 and REQ-ING-011b (Epoch ingested).

### REQ-ING-010 — Epoch AI ingestion

**Statement:** ingest Epoch AI's documented CSV bundle as a source, provenance mandatory, loud-fail like every other source.
**Status:** **MET.** Evidence: test_epoch_workflow.py:39; test_epoch_ingest.py:99; test_epoch_bundle_fetch.py:38. D-158 amends acquisition: the refresh now fetches the bundle itself. **Duplicate:** this ID appears again at line 332 with a different status.
**M16-W4 (D-158):** the nightly refresh fetches the bundle itself (`src/app/clients/epoch_bundle.py`, `refresh --fetch-epoch`), with the archive handled as untrusted input. Cited by `tests/unit/test_epoch_bundle_fetch.py`.

### REQ-REC-009 — Equivalent plans are named, not hidden

**Statement (RESTATED at M4-W4 — see D-110):** where several plans within the budget rank on the same model at the same score, the answer declares them indistinguishable, names the cheapest with its price and the monthly spread, and says which members are linked via a roster rather than their own plan page.
**Supersedes:** the signed criterion "`--subscription` returns ≥3 DISTINCT plans in `orta` and `sinirsiz` on live data", which is unachievable honestly — 4 of the 5 scoreable plans rank on the same model (measured 2026-08-15).
**Acceptance:** groups computed for every plan a label picked; built from budget-filtered rows only; keyed on plan_id, never display name.
**Status:** **MET.** Evidence: test_subscribe.py:422; test_serializer_parity.py:322. The restated criterion was ratified by D-110 (owner-signed 2026-08-15). The PRD line still says "awaits the owner's signature".

### REQ-REC-010 — Scores are rounded at the output boundary

**Statement:** every score reaching the JSON contract or a user-facing string is rounded to 1 decimal, exactly once, at the boundary; ranking, Pareto and threshold comparisons keep the raw value; prose deltas are computed from the ROUNDED numbers so the text cannot contradict the fields.
**Acceptance:** raw floats never reach the contract (tested through the real CLI); rounding inside the ranking is a test failure.
**Status:** **MET.** Evidence: test_subscribe.py:368; test_recommend_assistant.py:207.

### REQ-SUB-006 — Google AI Plus re-probe

**Statement:** re-probe the price M3 excluded as disputed; the row enters only on dated evidence, otherwise the exclusion is re-recorded.
**Acceptance:** the entry states WHY the dispute resolved; the model list comes from the provider's own page, never from a price tracker.
**Status:** **MET.** Evidence: test_plans_ingest.py:181.

## 12. M5 — Rescue the coding category (implementation trace pending owner gate)

> Added 2026-08-16 from the signed `docs/plans/m5-plan.md`. Historical M4 deferral text above is
> preserved as the record of that gate. This newer section supersedes it for current implementation
> status, but no M5 item is recorded as owner-accepted until the milestone verification session.

| REQ-ID | Implemented behavior and evidence | Current status |
|---|---|---|
| REQ-ING-010 | Local allowlisted Epoch CSV ingestion with required provenance and an independent acquisition clock. Citing tests: `test_epoch_ingest.py`, `test_epoch_workflow.py`, `test_deepswe_workflow.py`, `test_epoch_staleness.py`. | **MET.** Evidence: test_epoch_workflow.py:39, :120; test_epoch_staleness.py:19. Duplicate of line 299, which carries a different status. |
| REQ-ING-011b | Selected-row evidence partitions coding as 2 fresh / 3 stale / 5 unscored and agentic-coding as 6 undated / 4 unscored; source-global dates remain telemetry. Citing tests: `test_coverage.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_coverage.py:230, :251; test_epoch_workflow.py:128. |
| REQ-CAN-005 | Effort is parsed, validated, stored, and reconciled; unknown/conflicting rows are counted. Citing tests: `test_schema.py`, `test_effort.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_effort.py:31, :49; test_serializer_parity.py:213 (W-010). |
| REQ-REC-011 | Model and plan output name ranked effort and compare only same-harness/same-source higher effort. Citing test: `test_effort.py`. | **MET.** Evidence: test_effort.py:252, :279. |
| REQ-SUB-007 | Pinned baseline coding 1/10; Epoch coding 5/10; DeepSWE agentic-coding 6/10; cross-category union 6/10. Citing tests: `test_m5_board_measurement.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_m5_board_measurement.py:43, :127; test_deepswe_workflow.py:161. A pinned M5-era measurement. The numbers describe that snapshot, not today's artifact. |
| REQ-LIC-001 | Required Epoch citation is in ranking exports, both recommendation payload source lists, and README. Citing tests: `test_categories.py`, `test_recommend.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_recommend.py:136; test_refresh_attribution_fingerprint.py:61. Separate licence risk: W-129 (accepted). |
| REQ-REC-012 | Board measurement carries both Gemini results and states the disagreement. Citing test: `test_m5_board_measurement.py`. | **MET.** Evidence: test_m5_board_measurement.py:94. |
| REQ-REC-013 | `excluded_by_budget` counts scoreable plans removed by the cap and `budget_notice` narrates it, separate from unscored/equivalent plans. Citing tests: `test_subscribe.py`, `test_deepswe_workflow.py`; contract proposed in D-111. | **MET.** Evidence: test_subscribe.py:166. D-111 was ratified on 2026-08-16. |

## 13. M6 — The HTTP API (REQ-API / REQ-REC / REQ-LIC / REQ-SUB)

> Added 2026-08-16 from the signed `docs/plans/m6-plan.md` §2, per the M3 rule that new REQs land in
> BOTH the plan and this file. **Status for every row below is SPECIFIED — nothing is implemented.**
> The milestone freezes the owner's Ruling A into a public contract: a coding request returns BOTH
> the `coding` and the `agentic-coding` answer, and neither is presented as leading the other
> (recorded as D-115 when the milestone ratifies it).

| REQ-ID | Statement | Status |
|---|---|---|
| REQ-API-001 | A versioned, read-only HTTP surface: `GET /v1/recommendations`, `GET /v1/categories`, and the existing `/health` with its L.7 build stamp unchanged. M6 ships no mutating route, and a citing test asserts that absence — V3C-12 server-side authz is satisfied by having no mutating surface, never by claiming one is protected. | **MET.** Evidence: test_api_v1.py:509, :518. The surface has since gained `/v1/budgets` (D-134), which :518 also asserts. |
| REQ-API-002 | Ruling A: `task=coding` returns two answers, neither flagged as primary, emitted in a documented non-semantic order, with the envelope stating that the order carries no meaning. An explicit `task=agentic-coding` returns that surface alone. Citing test asserts two members AND that no field ranks them. | **MET.** Evidence: test_api_v1.py:199, :242, :281. |
| REQ-API-003 | Rendering parity: `close_call`, `stale_notice`, `effort_mix_notice`, the D-111 budget notice, D-110 equivalence and per-pick `effort` appear in the JSON payload, the CSV export and the CLI output, all derived from ONE serializer. Citing test compares all three renderings of a single run field-for-field. A disclosure present in one and absent from another is BLOCKING. | **PARTIAL.** Missing: API and CLI parity is proven field by field. The "CSV export" leg is not: `export_ranking` (rank.py) writes ranking rows, effort and attribution, but none of `close_call`, `stale_notice`, `effort_mix_notice`, the budget notice or equivalence. Either reword the CSV clause or add a CSV recommendation rendering. Evidence so far: test_serializer_parity.py:52, :64, :74, :298, :351. |
| REQ-API-004 | An answer whose evidence carries no evaluation date says so IN THE PAYLOAD, not only in the coverage report (INV-24; the `agentic-coding` case). | **MET.** Evidence: test_api_v1.py:297; test_uncertainty_contract.py:206. |
| REQ-API-005 | Error contract: unknown task, unknown budget and a missing database each produce a stable documented error shape that fails loud and closed and leaks no filesystem path into the response body. **AMENDED 2026-08-17 (owner):** an unhealthy source is DISCLOSED in a 200 answer, never refused — refusing over stale evidence would contradict the honesty doctrine, and the fail direction for a disclosure control is toward saying more. Explicitly not a 503. | **MET.** Evidence: test_api_v1.py:600, :617, :311. |
| REQ-API-006 | Security baseline for the surface (V3C-11/12/13/51/56): CORS is an allowlist and never allow-all-with-credentials; security config is validated at startup and the process refuses to serve in production if it is wrong; the API's database handle is read-only; no plaintext credential in source. | **MET.** Evidence: test_api_config.py:35, :170, :251; test_readonly_uri.py:57. |
| REQ-REC-014 | `equivalent_plans` carries group structure, so a machine consumer can tell which pick each plan is equivalent to and at what price. | **MET.** Evidence: test_serializer_parity.py:180, :322. |
| REQ-LIC-002 | The CSV half of `export_ranking` carries the same attribution and blend note the JSON half already carries. | **MET.** Evidence: test_serializer_parity.py:124, :264. |
| REQ-SUB-008 | The roster-link staleness sentence reads the roster's OWN persisted window, not the curated plan table's. Citing test proves the two windows can diverge and that the correct one is used. | **MET.** Evidence: test_roster_window.py:34. |

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
| REQ-APP-001 | A SwiftUI app runs in the iOS Simulator, asks the engine for a recommendation and renders the real answer. No mock data in the shipping target, and no fixture JSON compiled in. | **MET.** Evidence: test_ios_client_contract.py:304. The live Simulator run (`dev-a9dc034`) is a one-off. No gate can repeat it. |
| REQ-APP-002 | Ruling A survives the client: `task=coding` shows BOTH surfaces with neither presented as the winner — no default tab, no first-position emphasis, no client-side sort. | **PARTIAL.** Missing: Still true: no UI test proves "no default tab, no first-position emphasis". **New:** the row's "in the order the engine sent" is no longer true. Since W-064 (M11-W3) the client puts the reader's *selected* surface first (Router.swift:511 `orderAnswers`, ContentView.swift:119; OwnerSessionDefectTests.swift:93). No ADR records this change to Ruling A in the client. Evidence so far: test_ios_client_contract.py:237 (a tripwire on spellings). |
| REQ-APP-003 | Every disclosure the API sends is visible: `unavailable_reason`, `source_health` notices, `stale_notice`, `evidence_dating_note`, `effort_mix_notice`, `close_call`, `ranking_effort` and the ordering note. | **MET.** Evidence: test_ios_client_contract.py:58, :92. |
| REQ-APP-004 | The app degrades honestly: engine unreachable, 503, an empty answer and a slow response each produce a stated condition — never a blank screen and never an endless spinner. | **MET.** Evidence: test_ios_client_contract.py:369, :411; EngineClientTests.swift:245; test_unavailable_after_boot.py:69. The "unreachable 503" caveat is closed by REQ-IOS-003 (W-039 FIXED). Timeouts are checked in source and against a stubbed URLSession, not on a device. |
| REQ-APP-005 | The app computes no ranking value of its own. Scores, prices and orderings are rendered as received (Trap 1; protects D-104, D-105, D-109). | **PARTIAL.** Missing: Still true: arithmetic laundered through a local binding, and formatter rounding, are invisible to the regex gate. The Engine-layer Swift tests (W-038 fix) do not cover views. Evidence so far: test_ios_client_contract.py:138, :172. |
| REQ-API-010 | Any contract gap the client finds is recorded as a finding against `/v1` before any client-side workaround. **Declared class: PROCESS** — its obligation is about the record trail, not about running code. | **MET.** Evidence: test_contract_change_provenance.py:38, :60, :79. **ID collision:** line 432 uses the same ID for a different requirement. |

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
| REQ-REF-001 | One command performs one refresh cycle: build into a temporary artifact, compare it against the live one, publish only if it should be. It never leaves the live artifact worse than it found it, including when killed mid-run. | **MET.** Evidence: test_refresh.py:159, :1348; test_nightly_refresh.py:213. |
| REQ-REF-002 | "Changed" is decided on the CONTENT THAT WOULD BE SERVED — not file bytes, not timestamps. An unchanged upstream produces no publish and says so. | **MET.** Evidence: test_refresh.py:88; test_refresh_boards.py:79. |
| REQ-REF-003 | A refresh REFUSES to publish an artifact that is worse than the live one: fewer surfaces answering, or materially less evidence behind any surface. The refusal is a first-class outcome with its own exit code, not an error. | **MET.** Evidence: test_refresh.py:660; test_floor_served.py:357. |
| REQ-REF-004 | Every cycle leaves a durable record of what it did and why — published, unchanged, refused or failed — carrying the numbers it decided on. | **MET.** Evidence: test_refresh.py:802; test_nightly_refresh.py:278. |
| REQ-REF-005 | A refresh runs every 12 hours without a human, and a human can find out that it stopped running at all. **Silence must not be indistinguishable from success.** | **SUPERSEDED** by D-151 (once a night, 23:00-01:00) and D-154 (the engine runs it as a child process; the launchd job is retired with `scripts/retire_refresh.sh`). Replaced by REQ-REF-008. The "find out it stopped" half is now `/health` (test_nightly_refresh.py:278). `deploy/com.hcs.modelranking.refresh.plist` stays until the owner retires it. D-154's status is still **proposed**. |
| REQ-REF-006 | The running engine serves a replaced artifact without a restart, and a request in flight during the swap completes on consistent data. | **MET.** Evidence: test_refresh.py:253, :1400. |
| REQ-REF-007 | Ingestion never runs on the serving host (D-116). The refresh produces an artifact and hands it over; it does not reach into a serving process. | **PARTIAL.** Missing: Still true: the physical half is unmet because nothing is deployed. Since D-154 the refresh even runs as a child of the serving engine on the same Mac; production refuses the switch (test_nightly_refresh.py:320). W-125 (accepted): the serving process still loads the parsers and `httpx`. Evidence so far: test_refresh.py:293; test_nightly_refresh.py:352. |

## M10 — the router (REQ-RTR) and the guards, added at W1

D-126 ruled the router at M8 — *"the router picks the QUESTION; the engine answers it"*, and it may
never say a model is good — and it was never given a REQ-ID or a wave until the owner asked where
it had gone. These are written here at W1, before any code.

**Measured before planning:** the on-device options cost **zero app bytes** and send nothing off the
phone. `FoundationModels` needs iOS 26 and an Apple Intelligence-eligible device; `NLEmbedding`
needs iOS 13 and covers every device this app targets (deployment target 18.0).

| REQ-ID | Requirement | Status |
|---|---|---|
| REQ-RTR-001 | A user types a question in their own words and the app opens the surface that answers it. The router's choice is SHOWN and changeable with one tap (D-126). | **PARTIAL.** Missing: No test cites REQ-RTR-001. "Changeable with one tap" holds only when the wording tier answered. Otherwise it takes two taps (`Change`, then the surface), as REQ-ASK-002's own status admits. Evidence so far: FrontDoorTests.swift:136, :174; RouterBoundaryTests.swift:147. |
| REQ-RTR-002 | **The router can only ever yield one of the nine category ids.** A recommendation, a model name, prose or an injected instruction is discarded and the user gets the manual fallback, correctable from the `Change` sheet (the chips became that sheet at M13-W3). Where the framework allows it the closed set is a SCHEMA constraint, not a prompt instruction. | **MET.** Evidence: RouterBoundaryTests.swift:106, :243; test_router_hints.py:114. |
| REQ-RTR-003 | The router is never required. Unreachable, ineligible, disabled, slow or wrong — the product still works through the `Change` sheet (a chip until M13-W3), and says which happened. | **MET.** Evidence: RouterBoundaryTests.swift:53, :94; FrontDoorTests.swift:539. |
| REQ-RTR-004 | Nothing typed reaches the ENGINE, and nothing the engine serves is influenced by the router beyond which surface is opened. The scoring path is untouched (D-104). | **MET.** Evidence: test_router_hints.py:160; EngineClientTests.swift:435. |
| REQ-RTR-005 | *(verified against the real on-device model by the owner on 2026-08-23 — it warned.)* A question the catalogue does not measure routes to `assistant` **and says so** — that it is not measured here and is being answered with the general chat ranking. | **PARTIAL.** Missing: W-123 (accepted, owned by M18): 5 of 16 ordinary questions still reach a measured surface with `unmeasured = false`. Evidence so far: RouterBoundaryTests.swift:131, :170; test_router_hints.py:97; FrontDoorTests.swift:388. |
| REQ-GRD-001 | A refresh REFUSES a candidate whose evidence moved upward in a way ordinary upstream movement does not produce. It refuses; it never judges and publishes. | **MET.** Evidence: test_refresh.py:1509; test_floor_served.py:265, :357. |
| REQ-GRD-002 | No refresh can be made to allocate without bound by an upstream: every paginating client caps total accumulated rows and bytes. | **MET.** Evidence: test_arena_client.py:198. |
| REQ-GRD-003 | The refresh states its environment assumptions as CHECKS, not assumptions. | **MET.** Evidence: test_refresh.py:1636. |
| REQ-EVI-002 | The population the engine actually ranks — reconciled AND priced — has a NAME in the code, and calibration must call it. | **MET.** Evidence: test_ranked_population.py:179. |
| REQ-REV-001 | K.7 is executable in a single-agent lane: a wave-close review row that passes must cite a review record declaring `seat: independent`, and a cited review record that does not exist fails in every era. | **MET.** Evidence: test_review_seat_gate.py:44. |
| REQ-IOS-001 | The Engine layer is executed by a gate: `Router`, `EngineClient` and their boundaries have tests that run from the command line and are wired into `make check` and `runner`. | **MET.** Evidence: `swift-test` is a leg of `make check` (Makefile:108); ios/EngineTests (268 tests); test_swift_test_manifest.py:57. The row says "18 tests". There are now 268. |
| REQ-IOS-002 | The router's boundary is proven IN SWIFT: no path yields an id outside the nine, every tier can be absent without blocking the screen, and an unmeasured question reaches the surface flagged as unmeasured. | **MET.** Evidence: RouterBoundaryTests.swift:106, :170, :185. |
| REQ-IOS-003 | The 503 the client is required to render honestly can be PRODUCED on demand, so the branch that renders it is reachable by a test. | **MET.** Evidence: test_unavailable_after_boot.py:69. |
| REQ-API-010 | `/v1` gives ONE account of a query: the `ranking` array and the `picks` array cannot disagree about what was ranked. | **MET.** Evidence: test_budgets_endpoint.py:55. **ID collision** with line 384 (a different requirement under the same ID). |
| REQ-RUN-001 | The product has been operated by a person against a running engine, and what was asked and what came back is written down — including anything that looked wrong. | **MET.** Evidence: OwnerSessionDefectTests.swift:39, :93, :131 (the W-063/064/065 tests). A process criterion, met by the 2026-08-22 owner session. |
| REQ-RUN-002 | The 12-hour refresh has completed at least two unattended cycles on the schedule, and the status file it left is read back and reported. | **SUPERSEDED** by D-151, D-154 (the 12-hour launchd schedule is retired). The intent is still unobserved for the replacement: no record shows two unattended nightly engine cycles. `advisor.db.refresh.json` holds one cycle, at 2026-09-23T22:16Z: outcome `refused`, `consecutive_refusals` 2. If the owner still wants that observation, it is open work. |
| REQ-GOV-001 | Every ADR cited anywhere in this repository exists; `C2b` counts something it can actually reach. | **MET.** Evidence: test_adr_citations.py:80; test_c2b_counter.py:57. |
| REQ-LOC-002 | Text matching in the client is correct under a Turkish locale, pinned by a test that SETS the locale rather than inheriting it. | **MET.** Evidence: OwnerSessionDefectTests.swift:286, :235. |
| REQ-CMP-001 | Every number a reader meets carries, beside it, something that says what it means without domain knowledge — including a RANK where the scale is arbitrary. | **MET.** Evidence: OwnerSessionDefectTests.swift:305, :322, :340. Amended by D-140/D-143: ECI shows its rank range only. |
| REQ-CMP-002 | Price is expressed in a unit a person outside this industry uses, without removing the exact figure. | **MET.** Evidence: OwnerSessionDefectTests.swift:352, :374; LanguageTests.swift:168. |
| REQ-CMP-003 | Every surface name says what the surface measures, in words a non-specialist would choose. No two surfaces begin with the same word. | **MET.** Evidence: test_category_titles.py:37, :57. |
| REQ-DSC-001 | A limitation that is a property of a SOURCE is stated once per source; a limitation that is a STATE of the data keeps its warning treatment (D-135). Every fact remains reachable. | **MET.** Evidence: OwnerSessionDefectTests.swift:393, :407. |
| REQ-BGT-001 | A reader can choose a budget in the app, and the answer changes when they do. | **SUPERSEDED** by **No ADR.** Retired by the signed m13-plan §2 W3 (council ballot E). D-134 keeps `/v1/budgets` for other consumers. The PRD says the picker's tests were deleted, yet EngineClientTests.swift:419 still claims to be "REQ-BGT-001's other half". The test is still valid for EngineClient, but the label is stale. |
| REQ-LOC-001 | `/v1` returns the FACTS behind each sentence; the client composes the sentence, in English or Turkish, from those facts alone. | **PARTIAL.** Missing: Still true: three engine notices reach the screen as English prose, not composed from facts: `stale_notice`/`source_health.notice`, `evidence_dating_note` and `effort_mix_notice` (ContentView.swift:518-521; Language.swift:12-15; D-136 scope). Reason codes and the tie sentence are now localised. Evidence so far: test_why_facts.py:52, :64; LanguageTests.swift:33, :45. |

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
| REQ-FIX-001 | Pareto dominance admits equality on one axis: a row is dominated when another is at least as good on BOTH quality and cost and strictly better on at least one. Both the model engine and the subscription engine agree. | **MET.** Evidence: test_pareto_dominance.py:130, :138. |
| REQ-FIX-002 | Startup refuses an evidence database the serving path cannot read. A database carrying `scores`, `pricing` and a non-empty `px_median` but missing a table a ranking joins is REFUSED, not admitted. | **MET.** Evidence: test_startup_schema_validation.py:65, :78. |
| REQ-FIX-003 | A change that alters the attribution a reader is shown changes the refresh fingerprint, so the artifact publishes. Attribution is a licence obligation (REQ-LIC-001), not a display detail. | **MET.** Evidence: test_refresh_attribution_fingerprint.py:61. |
| REQ-FIX-004 | `runner` cannot report a leg it did not run as a pass. An absent environment is `SKIPPED`, and any skip prevents the all-green claim. | **MET.** Evidence: test_runner_accounting.py:65. |

## M13 — say only what we know (REQ-UNC), added at W2

The display is made honest BEFORE it is redesigned. W3 removes the controls that currently slow a
reader down; these are the statements that stop the remaining numbers from overstating.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-UNC-001 | Where the engine's own `close_call` margin says two models are indistinguishable, the screen does not present them as ordered. Every position is shown as the range of places the margin allows (`#1–27 of 50` for today's `expert` leader), so two models inside the margin of each other always have overlapping ranges; how many the benchmark cannot separate from the leader is stated once per ranking. **Amended 2026-09-15 by the owner**: the plan's text said "render a shared band" (council ruling D1), and the W2 review measured bands printing 47 within-margin pairs (45 on raw scores) as ordered. | **MET.** Evidence: UncertaintyTests.swift:32; test_uncertainty_contract.py:56. |
| REQ-UNC-002 | Nothing on screen calls a coverage count a confidence. The reader is told how many independent benchmarks measured the pick, and how old the oldest of them is. Verified by: a pick whose secondary is more than 180 days old carries that age. | **MET.** Evidence: test_secondary_evidence_age.py:84; test_uncertainty_contract.py:89; UncertaintyTests.swift:235. |
| REQ-UNC-003 | Every score source carries a date, or the product names the one that does not. | **MET.** Evidence: test_board_run_dates.py:51; test_uncertainty_contract.py:206. The caveat "the shipping artifact predates the fix" is obsolete: the artifact is rebuilt nightly. |

## M13 — the question is the front door (REQ-ASK), added at W3

The owner's report, translated from Turkish: *"it felt like a search bar, not an AI"*. The question
field becomes the only input on the home screen; the two strips of controls above it go, and the
correction they offered survives as a `Change` sheet.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-ASK-001 | The question field is reliably focusable, raises a keyboard, and can be submitted without one. | **PARTIAL.** Missing: Still true: the software keyboard, typing, Return and the send button have not been verified on a simulator or device. The owner's check is pending (the M13 closure marks it ◐). Evidence so far: FrontDoorTests.swift:118 (SubmissionTests); test_ios_client_contract.py:614. |
| REQ-ASK-002 | The screen shows what it understood, and it can be corrected in one tap: `"prove a theorem" → Mathematics` renders with the reader's own words, and a correction reaches every one of the nine surfaces. | **PARTIAL.** Missing: "Corrected in one tap" holds only when the wording tier answered. The model tier and below-floor questions need two taps (the row's own text says so). Evidence so far: FrontDoorTests.swift:136, :174, :500. |
| REQ-ASK-003 | A question the catalogue does not measure returns a ranking AND a statement, above it, of what that ranking cannot tell the reader. It is never silently answered as if measured; `tier = manual` may not carry `unmeasured = false`. | **PARTIAL.** Missing: W-123 (accepted, owned by M18): ordinary questions are still answered as measured (5 of 16 on held-out sets). Evidence so far: FrontDoorTests.swift:201 (UnmeasuredQuestionTests); RouterBoundaryTests.swift:53. |
| REQ-ASK-004 | A slower response for a previous selection can never overwrite the current one. | **MET.** Evidence: FrontDoorTests.swift:67, :105; test_ios_client_contract.py:614. |

## M13 — the card says what a number is out of (REQ-CMP-004), added at W4

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-CMP-004 | A score is shown with its ceiling where one exists (`Score 83.5 / 100`), with its scale NAME where the scale is unbounded but published (`Score 1504.2 Elo`), and as a rank alone where neither exists (ECI). No two surfaces' scores are presented as comparable. | **SUPERSEDED** by D-143 (out of 100); D-162 (the anchor is the floor). Replaced by the amended row at line 493. **Duplicate ID** with a different status. |
| REQ-CMP-004 **(amended M14-W4 by D-143; the row above is the M13 rule and no longer describes the product)** | An Elo score is shown out of 100 against the surface's anchor (its floor, D-162), not as `Score 1504.2 Elo`; a bounded percentage is shown as it was; ECI is still rank-only. The scale NAME is not put in front of the reader on a card or a row. | **M14-W4.** `ios/ModelRanking/Engine/Scores.swift::scoreText`. Cited by `ios/EngineTests/ScoresTests.swift::OutOf100Tests`. The M14 closure seat found the row above still stating the superseded rule (MAJOR-5); it is kept, marked, because M13's records cite it. |

## M14 — the catalogue answers questions people ask (D-142)

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SRC-011 | Each LMArena board is stored under its own source id AND its own benchmark label, taken from the registered board table and never defaulted; an unregistered source id is refused. No two boards share either identifier. | **MET.** Evidence: test_arena_client.py:377, :423, :223. |
| REQ-SUR-001 | Two surfaces, `document` and `factuality`, rank only their own board, each on its own Elo scale (D-105), with floors set by the rule the product ships (D-145). | **MET.** Evidence: test_categories.py:431, :446. D-148/D-159 supersede "floors set by D-145": the floor is derived from the board. |
| REQ-GAP-001 | A question the router declines is recorded on the device with its text and a count; a router failure (manual tier) is not a gap; nothing recorded leaves the device; the stored entry is bounded in characters and in bytes. | **MET.** Evidence: FrontDoorTests.swift:643, :719; test_router_hints.py:233. The "nothing leaves the device" clause is enforced by a gate over spellings (the limit W-122 records). |
| REQ-GAP-002 | The owner can read the register in the app, most-asked first, and clear it. | **MET.** Evidence: FrontDoorTests.swift:677, :688 (`clear()` exercised at :693). The PRD still lists the owner reading the register on a running app as "pending". |
| REQ-SCR-001 | Every card and row shows a score out of 100 where an honest conversion exists; on an anchored Elo surface no card sentence names Elo. | **MET.** Evidence: ScoresTests.swift:154, :240. |
| REQ-SCR-002 | The conversion is per surface and strictly monotonic: it never reorders a ranking. | **MET.** Evidence: ScoresTests.swift:210. |
| REQ-SCR-003 | *(amended by D-162, #15)* An Elo surface's anchor is the floor it recommends from, derived from the served board, so 50 out of 100 is "at the bar"; never the board's maximum. | **MET.** Evidence: test_floor_served.py:391, :411, :424. Amended by D-162. |
| REQ-SCR-004 | Ties are exactly the engine's: rank ranges use the native margin, and the tie note states that margin on the /100 scale. | **MET.** Evidence: ScoresTests.swift:284. |

## M15 — the detail screen (REQ-DTL), added at W2

**REQ-DTL-001/002 were carried from the M13 council's ruling F2 and moved into M14 by the M13
closure report, where they were not built** — while the M14 plan leaned on them as the mitigation
for taking the metric name off every card (D-143). The M14 closure seat found the screen did not
exist (`docs/warnings.ledger.md` W-105). They are written as criteria here, with citing tests, so
the next milestone cannot inherit them as prose again.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-DTL-001 | A reader can open one model from a pick OR from any row of the ranking and see, for that model on that surface: the score as the card shows it, the price in both the per-million and the per-pages form, and the surface's tie margin. Nothing on the screen is computed by the client. | **MET.** Evidence: DetailTests.swift:26 (DetailFactTests), :160; test_ios_client_contract.py:817. |
| REQ-DTL-002 | The metric's name and the engine's own number on the board's own scale are available on that screen wherever the card does not show them — the converted Elo surfaces and rank-only ECI — with the board named and its result dated, or named as undated. | **MET.** Evidence: DetailTests.swift:56, :73, :84, :96. |

## M15 — the surfaces the measurement chose (REQ-SUR), added at W3

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SUR-002 | Three surfaces — `vision`, `search`, `search_factuality` — each rank ONLY their own board, on their own Elo scale (D-105), with every threshold derived by the rules the product ships and recorded before the surface is served. Each is reachable by a question asked in a reader's own words. | **MET.** Evidence: test_categories.py:446, :388, :535; FrontDoorTests.swift:327; test_floor_served.py:391. **Stale citation:** `test_uncertainty_contract.py::test_every_elo_surface_publishes_its_pinned_score_anchor` no longer exists (removed with D-162). Its successor is test_floor_served.py:391. D-159 supersedes the "thresholds recorded before served" clause for floors. |
| REQ-SUR-003 | A board the engine cannot recommend from is REFUSED, with the count that refused it on record — never served with a threshold invented to make it fit. | **MET.** Evidence: test_arena_client.py:272, :344. |


## M16 — what the engine publishes about a price and a floor (REQ-FLR, REQ-PRC), added at W1

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-FLR-001 | `/v1/categories` publishes each surface's `min_quality` (since D-159 derived from the served board by `src/app/workflows/floors.py`; `null` with no artifact) on that surface's own scale, as its own field. On an Elo surface `score_anchor` is the same number since D-162 (#15): the anchor follows the floor, never the other way round. | **MET.** Evidence: test_uncertainty_contract.py:271; test_floor_served.py:50, :57, :69. |
| REQ-FLR-002 | The detail screen shows that floor as the line below which the product does not recommend, in both languages, composed in the Engine from the served fact. | **MET.** Evidence: DetailTests.swift:256, :267, :272. |
| REQ-PRC-001 | A surface whose price leaves something out says so on `/v1/categories` as a CODE (`price_excludes`), not as a sentence, and only the surfaces it applies to carry it (D-153, D-129: the app owns its languages). | **MET.** Evidence: test_uncertainty_contract.py:291. |
| REQ-PRC-002 | Wherever the app shows a price for `search` or `search_factuality`, it also says that a search call is not in it. | **MET.** Evidence: test_ios_client_contract.py:954; DetailTests.swift:282, :292; EngineClientTests.swift:166. |
| REQ-REF-008 | The engine refreshes its own artifact once a night inside 23:00-01:00 local and once at startup when no good cycle is on record within a day, through `refresh.py`'s entry point only, in a child process a hang, crash or kill of which cannot block or end the server; it is off by default and refused outside a development environment (D-151, D-154, D-116). | **MET.** Evidence: test_nightly_refresh.py:53, :186, :238, :320. D-154, which defines the mechanism, is still **proposed**. |
| REQ-REF-009 | A source that fails a cycle keeps serving its last good data -- every source, the required ones included -- for 30 days from when it last arrived in a served cycle; past that its surfaces drop and the refresh publishes the rest rather than refusing. What is carried or expired, and how old, is on `/health` and in the refresh record; `/v1` and the app do not change (D-144 as ruled, D-156). | **MET.** Evidence: test_carry_forward.py:60, :84; test_refresh_carry.py:89; test_nightly_refresh.py:557. |
