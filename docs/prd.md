# Product Requirements (PRD) — model_ranking

> Re-structured requirements with REQ-IDs. Tests and PRs cite these IDs forever (seed A.1). Per-area prefixes: REQ-ING (ingestion), REQ-CAN (canonical registry), REQ-RANK (ranking), REQ-REC (recommendation).
>
> Format conventions:
> - Each REQ has: ID, Statement, Acceptance criteria, Customer source, Status.
> - **A status opens with one of four words** (#28, re-read against the tree on 2026-09-25):
>   **MET** (built, and the cited test exercises it), **PARTIAL** (what is missing is named),
>   **OPEN** (not built), **SUPERSEDED** (by the ADR or requirement named). A status says where
>   the requirement stands now; how it got there is in git and the ADRs.
>   `tests/unit/test_prd_status.py` refuses any other opening word.
> - **Evidence in Python or Swift is cited by name, never by line** (#131): `<file>.py::<test_name>`, a second test of
>   the same file as `::<other_test>`, a class of tests by its class name, and a place inside a
>   test as "in `::<test_name>`". A Python test file is under `tests/unit/` and a Swift one under
>   `ios/EngineTests/`, unless a path says otherwise. A make target is named as `make <target>`.
>   `tests/unit/test_prd_citations.py` checks each name is declared in its file, refuses a line
>   pointer into Python or Swift, and refuses a `make` target the Makefile does not define. A line
>   pointer that shifted onto another test passed the old check (M18-W7, #126). Pointers into
>   workflow and record files (`ci.yml:7`, a plan's line) keep their line numbers and stay outside it.
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
**Status:** **MET.** Evidence: test_litellm_ingest.py::test_parse_skips_unpriced_and_nonchat_entries, ::test_ingest_stores_rows_with_provenance; test_schema.py::test_pricing_rejects_zero_prices; tests/integration/test_litellm_contract.py::test_real_litellm_payload_satisfies_parser_contract (the ≥500 live check, network).

### REQ-ING-002 — Ingest SWE-bench Verified leaderboard

**Statement:** The pipeline fetches the SWE-bench site leaderboard JSON from its GitHub repository and stores every Verified entry as a score record.
**Acceptance:**
- All Verified entries present in the source file are stored with `% resolved`, run date, and raw entry name.
- The agent/harness name is parsed and stored WITH each score (a score is a model+harness pair, never model alone).
- Rows from other leaderboards (Lite, Multimodal, …) are not mixed into Verified results.
**Customer source:** research §3.1; comparison report §2 (harness retention).
**Status:** **MET.** Evidence: test_swebench_ingest.py::test_only_verified_board_is_parsed, ::test_harness_is_retained_with_every_score, ::test_run_date_and_cost_are_stored; tests/integration/test_scores_contract.py::test_real_swebench_payload_satisfies_parser_contract. Separate licence risk: W-129 (accepted). The SWE-bench leaderboard JSON is CC BY-NC and must be resolved before any commercial launch.

### REQ-ING-003 — Ingest Aider polyglot leaderboard

**Statement:** The pipeline fetches Aider's `polyglot_leaderboard.yml` from GitHub and stores pass_rate_2 scores plus per-run cost.
**Acceptance:**
- All entries with a parseable model name are stored with score, run date, and `total_cost`.
- The known staleness of this source (updates stalled ~Nov 2025) is recorded as a source-health flag, not silently ignored.
**Customer source:** research §3.1 (Aider: coding + cost per run).
**Status:** **MET.** Evidence: test_aider_ingest.py::test_staleness_flag_fires_when_source_is_old, ::test_ingest_surfaces_health_in_report; tests/integration/test_scores_contract.py::test_real_aider_payload_satisfies_parser_contract.

### REQ-ING-004 — Provenance on every record

**Statement:** Every ingested record carries provenance and versioning fields so "as of" questions and audits are answerable.
**Acceptance:**
- Every pricing and score row has non-null `source`, `observed_at`.
- A repeated pipeline run replaces the working set deterministically (same input → same output; no duplicate accumulation).
- No ingestion path scrapes an HTML page; only documented raw-data endpoints are used (D-101).
**Customer source:** research B §8 (versioned records); comparison verdict §6.
**Status:** **MET.** Evidence: test_schema.py::test_pricing_requires_provenance; test_aider_ingest.py::test_ingest_rerun_replaces_working_set; test_litellm_ingest.py::test_ingest_stores_rows_with_provenance; test_arena_client.py::test_ingest_persists_the_exact_filtered_surface_as_provenance. The no-scraping clause holds by construction: every client parses a JSON/YAML/CSV endpoint, and HTML is refused (test_arena_slices.py::test_a_file_that_is_not_parquet_is_a_source_error, test_epoch_bundle_fetch.py::test_a_body_that_is_not_a_zip_is_refused). No single test asserts "no HTML page is ever fetched".

## 4. Canonical model registry (REQ-CAN)

### REQ-CAN-001 — Alias reconciliation to canonical models

**Statement:** Model names from all sources are mapped to a canonical model ID. A curated, ordered first-match rule table (vendor, display name, regex) is applied first and always wins; a name no rule matches is normalised by a closed grammar and registered as a DERIVED model when that id has both a price and a score (D-157).
**Acceptance:**
- The same underlying model arriving under different aliases (e.g. `claude-4-5-opus`, `Claude 4.5 Opus medium`) maps to ONE canonical ID.
- A name a curated rule matches keeps that rule's model, and a derived id never takes a curated one.
- The grammar removes only a closed list of decorations, so a variant never merges into its parent and two different products never derive one id; a fine-tune and a moving, undated alias never derive (D-157, D-166).
- A name with only a price or only a score, and a name the grammar refuses, is dropped and counted; the refresh record and `/health` name the derived models and the most frequent unmatched names.
**Customer source:** research B §6 step 1; spike finding (alias mapping is the core IP).
**Status:** **MET.** Evidence: test_registry.py::test_first_match_wins_maps_aliases_to_one_canonical_id, ::test_reconcile_maps_and_counts_drops; test_registry_derived.py::test_a_name_with_a_price_and_a_score_is_registered_as_derived, ::test_a_name_with_only_a_price_or_only_a_score_is_not_registered, ::test_the_curated_rules_win, ::test_different_products_never_derive_one_id, ::test_a_fine_tune_is_never_derived, ::test_a_curated_id_is_never_taken_by_a_derived_one; test_moving_aliases.py::test_a_moving_alias_derives_no_model, ::test_reconcile_registers_no_model_from_an_alias_and_counts_it_dropped; test_registry_disclosure.py::test_a_cycle_records_the_models_it_derived_and_the_names_it_could_not_match, ::test_health_counts_the_derived_models_and_names_the_top_unmatched. M19-W1: a release with one snapshot is one model, dated or not, and one with two stays two (#129: test_registry.py::test_a_release_with_one_snapshot_is_one_model, ::test_a_release_with_two_snapshots_stays_two_models); an effort is never a model of its own (#130: test_registry_derived.py::test_a_dash_effort_is_an_effort_only_where_no_product_takes_the_word).

### REQ-CAN-002 — Variant-before-parent rule ordering

**Statement:** Sub-variant rules (mini/nano/codex/chat…) precede parent-family rules so a variant's price or score never leaks into the parent model.
**Acceptance:**
- A regression test proves a `*-nano` alias does NOT match its parent family rule (the exact spike bug, reproduced red→green).
- Rule-order is covered by a test that fails if a parent rule precedes its variants.
**Customer source:** spike finding 2026-08-06 (GPT-5-nano price leaked into GPT-5).
**Status:** **MET.** Evidence: test_registry.py::test_variant_never_leaks_into_parent, ::test_rule_order_variants_precede_parents; test_registry_derived.py::test_a_variant_or_a_dated_release_never_merges_into_its_parent. M19-W1 (#162): each GPT-5 minor release's mini, nano, chat and codex variant is a model of its own (test_registry.py::test_each_gpt5_minor_release_is_a_model_of_its_own).

### REQ-CAN-003 — Median price per canonical model

**Statement:** Each canonical model's reference price is the median across its alias/provider prices, not the minimum.
**Acceptance:**
- A model with multiple provider prices stores the median input and output $/1M.
- A unit test demonstrates an outlier cheap alias does not become the model's reference price.
**Customer source:** spike finding (MIN picked wrong variant); research B §7.
**Status:** **MET.** Evidence: test_rank.py::test_median_not_min_beats_outlier.

## 5. Ranking (REQ-RANK)

### REQ-RANK-001 — Coding ranking table

**Statement:** The system produces a coding ranking: best SWE-bench Verified score per canonical model, joined with Aider score (when present) and median prices.
**Acceptance:**
- Output contains ≥20 canonical models with score, harness, evidence date, input/output/blended price.
- Blended price = input×0.75 + output×0.25, documented in output.
**Customer source:** research §3.2 (coding = richest category); M1 scope.
**Status:** **MET.** Evidence: test_rank.py::test_ranking_takes_best_score_and_its_harness (which asserts the blend), ::test_model_without_price_is_excluded. No test asserts the "≥20 canonical models" count. The shipped `advisor.db` ranks 55 models on `coding` (measured read-only on 2026-09-25).

### REQ-RANK-002 — Machine-readable export

**Statement:** Rankings export as CSV and JSON artifacts suitable for the future app/API layer.
**Acceptance:**
- One pipeline command yields `coding_ranking.csv` and `coding_ranking.json` with identical rows.
- Export includes a dataset-level `generated_from` note listing sources and observation timestamps.
**Customer source:** research §7 (serving pre-computed rankings).
**Status:** **MET.** Evidence: test_rank.py::test_export_csv_and_json_identical_rows; test_serializer_parity.py::test_the_two_export_halves_carry_the_same_rows.

## 6. Recommendation engine (REQ-REC)

### REQ-REC-001 — Three labeled answers

**Statement:** For the coding use case and a budget level, the engine returns exactly three labeled picks: Best Quality, Best Value, Budget Pick.
**Acceptance:**
- Each pick includes: model, vendor, score(s), prices, evidence date, harness, confidence grade, and a "why / trade-off" explanation.
- Output is deterministic: same database state + same inputs → same picks.
**Customer source:** research B §1 (three clearly labeled answers).
**Status:** **MET.** Evidence: test_recommend.py::test_three_labeled_deterministic_picks; tests/integration/test_cli_e2e.py::test_cli_end_to_end_three_picks.

### REQ-REC-002 — Budget constraint filtering

**Statement:** Budget levels (low/medium/unlimited) filter candidates by blended price BEFORE any scoring; ineligible models never appear.
**Acceptance:**
- With a low budget, no pick has blended price above the low threshold.
- Thresholds are named constants covered by a test.
**Customer source:** research B §6 step 4 (hard constraints first).
**Status:** **MET.** Evidence: test_recommend.py::test_budget_filter_is_hard_constraint; tests/integration/test_cli_e2e.py::test_cli_budget_filters_through_entry_point. The app no longer offers a budget (REQ-BGT-001 retired). The engine keeps `BUDGETS` (recommend.py::BUDGETS), and `/v1/budgets` publishes it.

### REQ-REC-003 — Pareto non-dominance

**Statement:** Value picks come from the quality–cost Pareto frontier; the engine never uses a bare `score ÷ price` ratio.
**Acceptance:**
- A test proves no recommended model is simultaneously worse AND more expensive than another eligible model.
- The value pick rule (within N points of leader, cheapest) is a documented, tested constant.
**Customer source:** research B §6 step 5.
**Status:** **MET.** Evidence: test_recommend.py::test_pareto_non_dominance, ::test_value_pick_rule_within_window_cheapest; test_pareto_dominance.py::test_model_engine_frontier. REQ-FIX-001 sharpens the dominance rule (equality on one axis).

### REQ-REC-004 — Confidence grading and honesty

**Statement:** Each pick carries a confidence grade derived from independent-source count, and near-ties are disclosed rather than hidden.
**Acceptance:**
- Two independent benchmark sources → High; one → Medium; the mapping is tested.
- When #1 and #2 are within the close-call threshold, the output says so explicitly (tested).
**Customer source:** research B §6 step 3; comparison verdict §6.
**Status:** **MET.** Evidence: test_recommend.py::test_confidence_grades_by_source_count, ::test_a_stale_secondary_does_not_grade_up, ::test_close_call_is_disclosed. D-139 amends the rule: an old or undated second board does not upgrade the grade. The screen shows evidence breadth instead (REQ-UNC-002).

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

## M2 — a second category and two more sources (REQ-ING / REQ-CAT / REQ-REC / REQ-CI), written at M18-W5

Specified in the signed `docs/plans/m2-plan.md` §2 and never copied here until #33. The criteria are
the plan's; where the rule has moved since, the row says so.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-ING-005 | OpenRouter's `/api/v1/models` catalogue is ingested as a second pricing source: no auth, input and output $/1M, provenance on every row, and an unpriced or free model is skipped rather than stored as zero. | **MET.** Evidence: test_openrouter_ingest.py::test_parse_converts_string_prices_to_per_million, ::test_free_models_never_stored_as_zero, ::test_ingest_stores_with_provenance_and_replaces; tests/integration/test_arena_openrouter_contract.py::test_real_openrouter_catalog_satisfies_parser_contract (at least 100 priced models on the live catalogue, `RUN_CONTRACT_TESTS=1`). |
| REQ-ING-006 | A model's reference price is the median of its per-source medians, so a source with many cheap aliases cannot outweigh another source. | **MET.** Evidence: test_rank.py::test_median_of_per_source_medians_beats_outlier_source. |
| REQ-ING-007 | The Arena leaderboard dataset is ingested: the text board's overall slice becomes Elo score rows with harness `arena-crowd`, and the snapshot they came from is recorded. | **MET.** Evidence: test_arena_ingest.py::test_prefers_overall_category_slice, ::test_elo_stored_with_metric_and_harness, ::test_only_newest_snapshot_is_kept; test_arena_client.py::test_ingest_persists_the_exact_filtered_surface_as_provenance; tests/integration/test_arena_openrouter_contract.py::test_real_arena_latest_satisfies_parser_contract (live). The dataset publishes no version number: the snapshot is each row's publish date, and the dataset, config and split fetched are stored as provenance. |
| REQ-ING-008 | Every export names the sources whose data it carries, Arena under CC-BY-4.0 among them, each with its `observed_at` (D-101). | **MET.** Evidence: test_categories.py::test_export_carries_attribution, ::test_every_source_the_build_ingests_can_be_attributed; test_arena_ingest.py::test_attribution_constant_names_license. The plan said "all sources"; since the M5-W4 review an export names only the sources it carries, so it makes no false provenance claim (test_categories.py::test_export_carries_attribution). |
| REQ-CAT-001 | Which benchmark each use case ranks on is a map held as data, not code branches: adding a category is adding an entry (D-105). | **MET.** Evidence: test_categories.py::test_categories_are_data_not_code. The plan named two categories; the map now holds fourteen, each added as an entry. |
| REQ-CAT-002 | The `assistant` surface ranks on Arena Elo, and the live board yields at least 20 rows. | **MET.** Evidence: test_categories.py::test_assistant_ranking_orders_by_elo; tests/integration/test_arena_openrouter_contract.py::test_real_arena_latest_satisfies_parser_contract (live). |
| REQ-CAT-003 | No cross-scale averaging: a category ranks only on its primary benchmark's scale (D-105). | **MET.** Evidence: test_categories.py::test_no_cross_scale_averaging_structural, ::test_a_category_ranks_on_the_board_it_names_and_reads_the_metric_that_board_publishes. |
| REQ-REC-005 | `recommend --task assistant\|coding` returns three labelled answers per category, worded on that category's own scale; coding's behaviour is unchanged. | **MET.** Evidence: test_recommend_assistant.py::test_assistant_task_three_picks_on_elo_scale, ::test_assistant_value_window_uses_elo_threshold, ::test_coding_task_unchanged_regression; test_categories.py::test_coding_regression_lock_via_category_layer; tests/integration/test_cli_e2e.py::test_cli_task_assistant_through_entry_point. |
| REQ-REC-006 | If a category's primary source is stale, the output says so (`stale_notice`). | **MET.** Evidence: test_recommend_assistant.py::test_stale_primary_source_is_disclosed. |
| REQ-CI-001 | A GitHub Actions job runs the unit suite on every push; the contract tests run as a manual or scheduled job with `RUN_CONTRACT_TESTS=1`. | **MET.** Evidence: `.github/workflows/ci.yml:7-10`, `:54` (`pytest` on every pull request and every push to `main`); `.github/workflows/contract-tests.yml:15-17` (on demand and a Monday cron), `:39-60` (pushes and pull requests that touch a parser), `:110` (`RUN_CONTRACT_TESTS: "1"`); the live tests skip without it (tests/integration/test_arena_openrouter_contract.py::pytestmark). A branch pushed with no pull request does not run CI. No test reads the triggers; test_ci_argument_drift.py::test_every_flag_value_ci_passes_is_one_the_code_accepts checks only the arguments CI passes. |

---

## 10. M3 — Subscription-plan table (REQ-SUB / REQ-REC / REQ-GP / REQ-CAL)

> Added 2026-08-15 from the signed m3-plan.md §2 (Q1-Q4 locked by the owner the same day).
> Note (doc drift, recorded): M2's REQ-ING-005..008 / REQ-CAT-001..003 / REQ-REC-005..006 /
> REQ-CI-001 were specified in the signed m2-plan.md §2 and copied here only at M18-W5 (#33),
> in the M2 section above. New REQs land in BOTH from M3 on.

### REQ-SUB-001 — Plan schema with mandatory provenance

**Statement:** `plans` + `plan_models` tables: provider, plan name, monthly USD price (CHECK > 0), currency, region, limits verbatim, source_url, last_verified; included-model names link to canonical models via the registry, unmatched names stay NULL and are counted.
**Acceptance:** schema enforces price > 0; every row carries source_url + last_verified; reconcile_plans counts drops (never guesses).
**Status:** **MET.** Evidence: test_plans_ingest.py::test_schema_check_rejects_nonpositive_price_at_sqlite_layer, ::test_reconcile_plans_links_explicit_names_and_counts_drops, ::test_invalid_row_fails_loud.

### REQ-SUB-002 — Curated seed dataset, live-verified

**Statement:** `data/plans.yaml` ships ≥6 plans across ≥4 providers (OpenAI, Anthropic, Google, Perplexity — owner Q1), USD/US-first (owner Q2), every value probed against a live source on entry day; curated-file validation FAILS LOUD (skip-and-count is for fetched sources, not authored data).
**Acceptance:** the real seed file parses, ingests transactionally, and meets the counts above (citing test: tests/unit/test_plans_ingest.py::test_seed_dataset_meets_req_sub_002).
**Status:** **MET.** Evidence: test_plans_ingest.py::test_seed_dataset_meets_req_sub_002, ::test_seed_dataset_ingests_and_reconciles_end_to_end; test_plans_staleness.py::test_shipped_seed_is_fresh_on_entry_day.

### REQ-SUB-003 — Staleness is disclosed, never hidden

**Statement:** a plan row older than the staleness window (30 days — owner Q3, stored as data) is flagged in exports and recommendation output.
**Status:** **MET.** Evidence: test_plans_staleness.py::test_stale_plans_is_deterministic_vs_ingest_stamp, ::test_window_is_read_from_data_not_code; test_subscribe.py::test_stale_plan_rows_disclosed_in_output.

### REQ-SUB-004 — Re-verification cadence

**Statement:** a weekly scheduled CI job (owner Q4) fails/reminds when any plan row exceeds the staleness window.
**Status:** **MET.** Evidence: test_plans_staleness.py::test_cli_exit_codes_through_real_entrypoint; `.github/workflows/contract-tests.yml:17` (weekly cron), `:89` (plans check). No test asserts that the workflow runs the **plans** check. Epoch's step was removed from CI by D-158 clause 4, and test_epoch_staleness.py::test_ci_no_longer_ages_the_epoch_bundle holds that it stays removed.

### REQ-REC-007 — Subscription recommendation

**Statement:** `recommend --subscription` returns three labeled plan picks (quality/value/budget) reusing the budget/quality logic, where a plan's linked models carry the category scores.
**Status:** **MET.** Evidence: test_subscribe.py::test_three_labeled_plan_picks_unlimited_budget, ::test_cli_subscription_through_real_entrypoint.

### REQ-REC-008 — Stale-plan disclosure in output

**Statement:** recommendation output disclosing stale plan rows, same honesty contract as stale_notice.
**Status:** **MET.** Evidence: test_subscribe.py::test_stale_plan_rows_disclosed_in_output; test_rosters.py::test_selected_stale_roster_clock_is_disclosed_through_cli.

### REQ-GP-001 — GP v4.3.1 install correctness

**Statement:** `make install-check` green: PROJECT paths complete, GP-INTERNAL files absent, gates wired (make check + pre-commit + CI).
**Status:** **SUPERSEDED** by D-113 (GP v5.0), then D-155 (DevFlow v6.0) and D-161 (v6.4). The GP v4.3.1 install no longer applies. Today's equivalent is `make install-check`, a leg of `make check`.

### REQ-CAL-001 — Elo threshold recalibration

**Statement:** the `assistant` surface's thresholds come from its live board, never assumed. Its tie margin (`close_call`, 8 Elo) and value window (`value_window`, 30 Elo) are a data edit in `categories.py`, with method and evidence in `docs/reviews/m3-elo-calibration.md`. Its floor is not a number kept by hand: like every surface's, it is the top third of its board's rows, derived from the served artifact wherever it is read (D-148 clause 1, D-159).
**Acceptance:** the shipped margin and window are the calibrated values, and moving either fails a test; the Budget Pick clears the floor derived from the board, on the Elo scale.
**Citing tests:** tests/unit/test_recommend_assistant.py::test_close_call_threshold_is_the_calibrated_elo_value and ::test_assistant_budget_floor_uses_elo.
**Status:** **MET.** Evidence: test_recommend_assistant.py::test_close_call_threshold_is_the_calibrated_elo_value, ::test_assistant_value_window_uses_elo_threshold, ::test_assistant_budget_floor_uses_elo, ::test_assistant_quality_floor_unmet_warns_on_elo_scale; test_floors.py::test_the_floor_is_the_top_third_of_the_rows; test_floor_served.py::test_the_published_floor_moves_with_the_board, ::test_the_budget_pick_clears_the_floor_of_the_board_it_reads.

## 11. M4 — Make the plan answers real (REQ-CAN / REQ-ING / REQ-SUB / REQ-REC)

> Added 2026-08-15 at M4 closure, closing quality-gate finding F-1: the M4 REQ-IDs were specified
> in the signed `docs/plans/m4-plan.md` §2 and had not been copied here. Canonical criterion text
> lives in the signed plan; this section is the PRD's index of it, with the shipped status.
> Full trace (criterion → implementing file:line → citing test) is `docs/coverage-by-req.md`.

### REQ-CAN-004 — Registry expansion with a self-defending rule table

**Statement:** adding a canonicalization rule is a cheap, tested, reviewable act; the rule table proves variant-before-parent ordering and sibling non-collision, and carries rules for the families live sources currently drop.
**Acceptance:** every rule canonicalizes to itself; no duplicate ids or patterns; a live-name corpus resolves to the right model; plan-name drops fall to 0.
**Status:** **MET.** Evidence: test_registry.py::test_every_rule_canonicalizes_to_itself, ::test_no_duplicate_canonical_ids_or_patterns.

### REQ-ING-009 — Provider model rosters as a second documented source

**Statement:** a provider's own model-availability page is ingested as a SEPARATE source with its own provenance and `last_verified`; a plan links to a roster model only through the registry, never guessed; a roster naming an unknown plan aborts.
**Acceptance:** roster links carry `link_source`/`source_url`/`last_verified`; plan-page links win ties; the recommendation text states WHICH source named the model.
**Status:** **MET.** Evidence: test_rosters.py::test_shipped_roster_file_is_valid_and_fresh_on_entry_day, ::test_recommendation_text_states_which_source_named_the_model.

### REQ-SUB-005 — Plan coverage is a measured number

**Statement:** how many curated plans can actually be ranked, per category, and for the rest WHY — separated into "no link at all" (curation gap) and "linked but no score on this benchmark" (benchmark gap).
**Acceptance:** computed by the pipeline, printed by a CLI, wired into CI; zero coverage in a category exits non-zero.
**Status:** **MET.** Evidence: test_coverage.py::test_coverage_counts_and_explains_every_unscoreable_plan, ::test_cli_reports_json_and_fails_loud_on_zero_coverage, ::test_coverage_is_read_only; test_ci_coverage_gate.py::test_a_surface_that_scores_nothing_with_NO_declared_absence_fails.

### REQ-ING-012 — One runnable production entry point builds the evidence database

**Statement:** a single command in `src/` builds the artifact end to end — schema, plans, rosters, every remote source, reconciliation, and the price medians — and is typed, linted, tested and covered like the rest of the product.
**Acceptance:** the entry point produces an artifact that serves real answers, and the counts it reports are read back OUT of the built file rather than reported by the writers that filled it.
**Why it did not exist before:** until M7 the pipeline was a heredoc inside `.github/workflows/contract-tests.yml`, invisible to every tool and run by a cron that never fired. That is the root of W-023.
**Status:** **MET.** Evidence: test_build.py::test_build_produces_an_artifact_that_can_actually_answer, ::test_counts_are_read_back_from_the_database_not_from_the_writers, ::test_cli_artifact_reopened_from_disk_holds_what_the_payload_claims.

### REQ-ING-013 — A partial build is a failed build

**Statement:** the builder exits non-zero and names the operator action on any hollow stage — a collapsed reconciliation, empty price medians, an empty curated stage, or a source it cannot stand in for — and leaves no artifact behind. A source that is unreachable, or stores fewer rows than its declared floor, keeps its last good rows from the live artifact when they arrived in a served cycle less than 30 days ago (D-144, D-156; REQ-REF-009). With nothing to carry — no live artifact, or last good data older than 30 days — a required source fails the build, and an optional one is named with the surfaces it leaves without evidence (exit 3).
**Acceptance:** each failure mode forced by fault injection; each exits non-zero; no partially-populated database survives a failed run; carried rows are the live artifact's own, and expired data is never carried.
**Why the floor matters:** `rank.py` JOINs `px_median`. An empty table yields zero rows and `/v1` answers 200 with no picks — a confident wrong answer that passes every existence check, including `/health`.
**Status:** **MET.** Evidence: test_build.py::test_a_source_that_stores_nothing_fails_the_build, ::test_an_unreachable_source_fails_the_build_rather_than_being_skipped, ::test_an_unbuilt_px_median_fails_the_build, ::test_a_failed_optional_source_names_the_surface_it_blinds, ::test_a_collapsed_registry_fails_the_build; test_build_artifact_safety.py::test_a_failed_rebuild_leaves_the_previous_artifact_untouched, ::test_a_failed_first_build_leaves_no_file_at_the_target; test_carry_forward.py::test_a_failed_required_source_is_carried_instead_of_failing_the_build, ::test_a_source_older_than_a_month_is_not_carried, ::test_an_expired_optional_source_drops_its_list_and_says_so, ::test_with_no_live_artifact_a_failed_required_source_still_fails.

### REQ-ING-011 — Source health is computed, not noticed

**Statement:** how old each source's newest evidence is, reported on every run; unknown age fails TOWARD disclosure. **(a)** measure and report; **(b)** state plainly whether a fresher documented coding benchmark exists AND, if it does, ingest it.
**Acceptance:** per-source age with the same 90-day window the engine discloses on (two clocks, stated); the investigation's verdict recorded either way.
**Status:** **MET.** Evidence: test_coverage.py::test_source_health_flags_a_source_that_went_quiet, ::test_stale_window_matches_the_engines_disclosure_window. Part (b) was delivered as REQ-ING-010 and REQ-ING-011b (Epoch ingested).

### REQ-ING-010 — Epoch AI ingestion

**Statement:** ingest Epoch AI's documented CSV bundle as a source, provenance mandatory, loud-fail like every other source.
**Status:** **MET.** Evidence: test_epoch_workflow.py::test_epoch_ingest_is_wired_with_independent_provenance; test_epoch_ingest.py::test_client_reads_only_the_allowlisted_local_csv; test_epoch_bundle_fetch.py::test_a_bundle_unpacks_into_its_directory; test_epoch_workflow.py::test_epoch_workflow_refuses_to_drop_its_verification_clock; test_epoch_staleness.py::test_shipped_epoch_clock_is_source_specific_and_fresh_on_entry_day. D-158 amends acquisition: the refresh now fetches the bundle itself. Its second row, in the M6 table, was folded in here at M18-W5 (#33).
**M16-W4 (D-158):** the nightly refresh fetches the bundle itself (`src/app/clients/epoch_bundle.py`, `refresh --fetch-epoch`), with the archive handled as untrusted input. Cited by `tests/unit/test_epoch_bundle_fetch.py`.

### REQ-REC-009 — Equivalent plans are named, not hidden

**Statement (RESTATED at M4-W4 — see D-110):** where several plans within the budget rank on the same model at the same score, the answer declares them indistinguishable, names the cheapest with its price and the monthly spread, and says which members are linked via a roster rather than their own plan page.
**Supersedes:** the signed criterion "`--subscription` returns ≥3 DISTINCT plans in `orta` and `sinirsiz` on live data", which is unachievable honestly — 4 of the 5 scoreable plans rank on the same model (measured 2026-08-15).
**Acceptance:** groups computed for every plan a label picked; built from budget-filtered rows only; keyed on plan_id, never display name.
**Status:** **MET.** Evidence: test_subscribe.py::test_equivalent_plans_are_named_when_the_three_labels_collapse; test_serializer_parity.py::test_each_equivalence_group_names_the_pick_it_belongs_to. The restated criterion was ratified by D-110 (owner-signed 2026-08-15). The PRD line still says "awaits the owner's signature".

### REQ-REC-010 — Scores are rounded at the output boundary

**Statement:** every score reaching the JSON contract or a user-facing string is rounded to 1 decimal, exactly once, at the boundary; ranking, Pareto and threshold comparisons keep the raw value; prose deltas are computed from the ROUNDED numbers so the text cannot contradict the fields.
**Acceptance:** raw floats never reach the contract (tested through the real CLI); rounding inside the ranking is a test failure.
**Status:** **MET.** Evidence: test_subscribe.py::test_scores_are_rounded_at_the_output_boundary_not_in_the_math; test_recommend_assistant.py::test_elo_scores_are_rounded_in_the_output.

### REQ-SUB-006 — Google AI Plus re-probe

**Statement:** re-probe the price M3 excluded as disputed; the row enters only on dated evidence, otherwise the exclusion is re-recorded.
**Acceptance:** the entry states WHY the dispute resolved; the model list comes from the provider's own page, never from a price tracker.
**Status:** **MET.** Evidence: test_plans_ingest.py::test_sub_dollar_price_survives_the_seed_exactly.

## 12. M5 — Rescue the coding category (implementation trace pending owner gate)

> Added 2026-08-16 from the signed `docs/plans/m5-plan.md`. Historical M4 deferral text above is
> preserved as the record of that gate. This newer section supersedes it for current implementation
> status, but no M5 item is recorded as owner-accepted until the milestone verification session.

| REQ-ID | Implemented behavior and evidence | Current status |
|---|---|---|
| REQ-ING-011b | Selected-row evidence partitions coding as 2 fresh / 3 stale / 5 unscored and agentic-coding as 6 undated / 4 unscored; source-global dates remain telemetry. Citing tests: `test_coverage.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_coverage.py::test_plan_evidence_health_partitions_every_plan_once, ::test_plan_evidence_health_uses_selected_row_not_source_max; test_epoch_workflow.py::test_real_epoch_board_reproduces_plan_level_freshness_distribution. |
| REQ-CAN-005 | Effort is parsed, validated, stored, and reconciled; unknown/conflicting rows are counted. Citing tests: `test_schema.py`, `test_effort.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_effort.py::test_effort_suffix_family_is_removed_before_base_registry_rule, ::test_explicit_effort_wins_suffix_conflict_and_unknown_is_visible; test_serializer_parity.py::test_an_unclassifiable_effort_suffix_is_counted_not_silently_defaulted (W-010). |
| REQ-REC-011 | Model and plan output name ranked effort and compare only same-harness/same-source higher effort. Citing test: `test_effort.py`. | **MET.** Evidence: test_effort.py::test_live_recommendation_ranks_high_and_discloses_higher_effort, ::test_live_subscription_answer_carries_the_same_effort_contract. |
| REQ-SUB-007 | Pinned baseline coding 1/10; Epoch coding 5/10; DeepSWE agentic-coding 6/10; cross-category union 6/10. Citing tests: `test_m5_board_measurement.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_m5_board_measurement.py::test_real_five_board_measurement_replays_the_signed_engine_results, ::test_complete_baseline_snapshot_rejects_truncation_and_provenance_drift; test_deepswe_workflow.py::test_real_board_reproduces_signed_coverage_and_undated_health. A pinned M5-era measurement. The numbers describe that snapshot, not today's artifact. |
| REQ-LIC-001 | Required Epoch citation is in ranking exports, both recommendation payload source lists, and README. Citing tests: `test_categories.py`, `test_recommend.py`, `test_deepswe_workflow.py`. | **MET.** Evidence: test_recommend.py::test_req_lic_001_epoch_citation_ships_where_epoch_data_is_served; test_refresh_attribution_fingerprint.py::test_a_changed_evidence_source_changes_the_digest. Since #124, a board Epoch compiles from another publisher credits that source (test_attribution_terms.py::test_an_external_board_credits_its_original_source). Separate licence risk: W-129 (accepted). |
| REQ-REC-012 | Board measurement carries both Gemini results and states the disagreement. Citing test: `test_m5_board_measurement.py`. | **MET.** Evidence: test_m5_board_measurement.py::test_gemini_contradiction_is_preserved_in_the_decision_record. |
| REQ-REC-013 | `excluded_by_budget` counts scoreable plans removed by the cap and `budget_notice` narrates it, separate from unscored/equivalent plans. Citing tests: `test_subscribe.py`, `test_deepswe_workflow.py`; contract proposed in D-111. | **MET.** Evidence: test_subscribe.py::test_budget_notice_counts_only_scoreable_plans_excluded_by_price. D-111 was ratified on 2026-08-16. |

## 13. M6 — The HTTP API (REQ-API / REQ-REC / REQ-LIC / REQ-SUB)

> Added 2026-08-16 from the signed `docs/plans/m6-plan.md` §2, per the M3 rule that new REQs land in
> BOTH the plan and this file. **Status for every row below is SPECIFIED — nothing is implemented.**
> The milestone freezes the owner's Ruling A into a public contract: a coding request returns BOTH
> the `coding` and the `agentic-coding` answer, and neither is presented as leading the other
> (recorded as D-115 when the milestone ratifies it).

| REQ-ID | Statement | Status |
|---|---|---|
| REQ-API-001 | A versioned, read-only HTTP surface: `GET /v1/recommendations`, `GET /v1/categories`, and the existing `/health` with its L.7 build stamp unchanged. M6 ships no mutating route, and a citing test asserts that absence — V3C-12 server-side authz is satisfied by having no mutating surface, never by claiming one is protected. | **MET.** Evidence: test_api_v1.py::test_no_mutating_route_exists, ::test_the_shipped_surface_is_exactly_the_declared_surface. The surface has since gained `/v1/budgets` (D-134) and `/v1/boards` (D-167), and ::test_the_shipped_surface_is_exactly_the_declared_surface asserts all five routes. M18-W4 builds `/v1/boards` once per artifact and compresses an answer of 1 KB or more on request (D-173 clause 5; the middleware is app-wide, and test_board_standings.py::test_a_replaced_artifact_is_built_again, ::test_a_client_that_accepts_gzip_gets_the_boards_compressed hold it on `/v1/boards`). M18-W2 adds three fields to each answer, each additive: `close_call_fact`, `unavailable_reason_code` and `source_health`'s `reason` (D-176; test_why_facts.py::test_every_close_call_on_the_artifact_carries_the_values_it_quotes). Since D-182 (M19-W2, #138) each pick also carries its model's id, additively (test_api_v1.py::test_each_pick_carries_the_id_of_the_model_it_ranks), and the app makes one card per id (AnswerPlanTests.swift::testTwoModelsThatShareEveryShownValueAreTwoCards). |
| REQ-API-002 | Ruling A: `task=coding` returns two answers, neither flagged as primary, emitted in a documented non-semantic order, with the envelope stating that the order carries no meaning. An explicit `task=agentic-coding` returns that surface alone. Citing test asserts two members AND that no field ranks them. | **MET.** Evidence: test_api_v1.py::test_coding_returns_both_surfaces_and_nothing_ranks_them, ::test_the_ordering_note_does_not_rank_the_surfaces, ::test_the_two_coding_answers_are_structurally_symmetric. |
| REQ-API-003 | Rendering parity: `close_call`, `stale_notice`, `effort_mix_notice`, the D-111 budget notice, D-110 equivalence and per-pick `effort` appear in the JSON payload, the CSV export and the CLI output, all derived from ONE serializer. Citing test compares all three renderings of a single run field-for-field. A disclosure present in one and absent from another is BLOCKING. | **PARTIAL.** Missing: API and CLI parity is proven field by field. The "CSV export" leg is not: `export_ranking` (rank.py) writes ranking rows, effort and attribution, but none of `close_call`, `stale_notice`, `effort_mix_notice`, the budget notice or equivalence. Either reword the CSV clause or add a CSV recommendation rendering. Evidence so far: test_serializer_parity.py::test_every_recommendation_field_reaches_the_v1_answer, ::test_every_pick_field_reaches_the_v1_answer, ::test_the_cli_and_the_api_render_the_same_run_identically, ::test_a_present_disclosure_survives_serialization, ::test_the_subscription_cli_rendering_carries_every_engine_field. |
| REQ-API-004 | An answer whose evidence carries no evaluation date says so IN THE PAYLOAD, not only in the coverage report (INV-24; the `agentic-coding` case). | **MET.** Evidence: test_api_v1.py::test_each_coding_surface_states_its_own_weakness; test_uncertainty_contract.py::test_an_undated_surface_names_its_benchmark_on_the_live_route. |
| REQ-API-005 | Error contract: unknown task, unknown budget and a missing database each produce a stable documented error shape that fails loud and closed and leaks no filesystem path into the response body. **AMENDED 2026-08-17 (owner):** an unhealthy source is DISCLOSED in a 200 answer, never refused — refusing over stale evidence would contradict the honesty doctrine, and the fail direction for a disclosure control is toward saying more. Explicitly not a 503. | **MET.** Evidence: test_api_v1.py::test_unknown_task_fails_closed_with_the_stable_shape, ::test_missing_database_fails_closed_and_leaks_no_path, ::test_an_unhealthy_source_is_disclosed_on_a_wall_clock. |
| REQ-API-006 | Security baseline for the surface (V3C-11/12/13/51/56): CORS is an allowlist and never allow-all-with-credentials; security config is validated at startup and the process refuses to serve in production if it is wrong; the API's database handle is read-only; no plaintext credential in source. | **MET.** Evidence: test_api_config.py::test_a_wildcard_origin_is_refused_not_warned_about, ::test_a_production_process_refuses_to_import_with_broken_config, ::test_credentials_are_never_allowed_across_origins; test_readonly_uri.py::test_read_only_still_refuses_a_write_on_an_ordinary_path. |
| REQ-REC-014 | `equivalent_plans` carries group structure, so a machine consumer can tell which pick each plan is equivalent to and at what price. | **MET.** Evidence: test_serializer_parity.py::test_equivalent_plans_carries_group_structure, ::test_each_equivalence_group_names_the_pick_it_belongs_to. |
| REQ-LIC-002 | The CSV half of `export_ranking` carries the same attribution and blend note the JSON half already carries. | **MET.** Evidence: test_serializer_parity.py::test_the_csv_export_carries_the_same_attribution_as_the_json, ::test_the_csv_cites_exactly_what_the_json_cites_no_more. |
| REQ-SUB-008 | The roster-link staleness sentence reads the roster's OWN persisted window, not the curated plan table's. Citing test proves the two windows can diverge and that the correct one is used. | **MET.** Evidence: test_roster_window.py::test_the_roster_window_is_persisted_separately_from_the_plan_window. |

**Red-test intakes carried into M6 against existing REQs (not new requirements):** W-010 against
REQ-CAN-005 (the effort counter under-reports suffix-bearing rows it cannot classify), plus W-005
(YAML alias-expansion guard) and W-009 (two migration entry points) as hardening the API boundary
creates. Each is reproduced with a failing test before it is fixed.

## M7 — the artifact is built, and serving never writes it (REQ-API-007..009), written at M18-W5

Specified in the signed `docs/plans/m7-plan.md` §1, which said to copy them here at W1; they were
not copied until #33. M7's other criteria are REQ-ING-012/013 (§11) and REQ-CAN-003 (§4).

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-API-007 | The serving path performs no write to the evidence database and holds no full-database copy. `serving_snapshot` is deleted, not merely unused. | **MET.** Evidence: test_api_v1.py::test_the_api_never_writes_to_the_database, ::test_the_routes_m17_added_or_changed_never_write_the_database; test_api_config.py::test_w017_is_closed_by_deletion_not_by_a_bounded_copy; test_readonly_uri.py::test_nothing_opens_a_database_but_the_named_writers_and_the_read_only_opener. |
| REQ-API-008 | A serving process whose evidence database has an unbuilt or empty `px_median` refuses to answer, with the operator-facing remedy named. It never returns 200 with zero picks. | **MET.** Evidence: test_unbuilt_evidence.py::test_the_startup_probe_refuses_an_artifact_with_no_price_medians; test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty; test_board_standings.py::test_an_artifact_the_route_cannot_read_is_unavailable; test_recommend.py::test_an_unbuilt_database_is_refused_rather_than_answered_empty; tests/integration/test_cli_e2e.py::test_cli_an_unbuilt_artifact_exits_2_not_1. The remedy is named to the operator, at startup and by the CLI, and kept out of the public 503 body (test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty). |
| REQ-API-009 | The deployed service answers a real query with correct CONTENT — both coding surfaces, neither leading (D-115, Ruling A) — from a host, over the network, unauthenticated. | **PARTIAL.** Missing: any run over a network. Nothing is deployed (D-123 is undischarged; W-030 is escalated). Evidence so far: `scripts/journey.py` passed 4/4 against a local container at M7-W4 (`docs/plans/m7-plan.md:166-169`; `docs/coverage-by-req.md:39`). No gate runs it. |

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
| REQ-APP-001 | A SwiftUI app runs in the iOS Simulator, asks the engine for a recommendation and renders the real answer. No mock data in the shipping target, and no fixture JSON compiled in. | **MET.** Evidence: test_ios_client_contract.py::test_the_shipping_client_carries_no_canned_payload. The live Simulator run (`dev-a9dc034`) is a one-off. No gate can repeat it. |
| REQ-APP-002 | Ruling A survives the client: `task=coding` shows BOTH surfaces with neither presented as the winner — no default tab, no first-position emphasis, no client-side sort. Since D-168 a question can select several boards and get the product's own combined list; a coding request takes no refinement (D-168 note 2), so Ruling A's two surfaces are never folded into one list. | **PARTIAL.** The UI target (D-175) shows both coding answers on screen, with the note that their order means nothing, and no such note on a one-answer surface (ScreenPathTests.swift::testCodingShowsBothAnswersAndSaysTheirOrderMeansNothing). Missing: since W-064 (M11-W3) the client puts the reader's *selected* surface first (Router.swift `orderAnswers`; OwnerSessionDefectTests.swift::testTheSelectedSurfaceIsShownFirst), and no ADR records that change to Ruling A in the client. Evidence so far: test_refinements.py::test_no_refinement_refines_a_surface_a_coding_request_answers_on; RefinementBoundaryTests.swift::testAValueTheSurfaceDoesNotAllowIsDropped; test_ios_client_contract.py::test_the_client_applies_no_ordering_of_its_own (a tripwire on spellings). |
| REQ-APP-003 | Every disclosure the API sends is visible: `unavailable_reason`, `source_health` notices, `stale_notice`, `evidence_dating_note`, `effort_mix_notice`, `close_call`, `ranking_effort` and the ordering note. On the combined list (D-168) the same duty holds for what the phone composes: the efforts its models stand at (D-112), each board's date and attribution, how many models the boards share, and the sentence that no leaderboard publishes this order. | **MET.** The combined list's disclosures are fields of its plan since M18-W2 (#67), its stale board included (#72), held by tests on the plan; the view renders them whole, a gate refuses one said by hand, and the UI target sees them on screen (#69, D-175). Evidence: test_ios_client_contract.py::test_the_client_renders_every_optional_field_the_answer_carries, ::test_the_disclosure_view_is_actually_reached_from_the_rendered_screen, ::test_the_combined_list_renders_the_disclosures_its_plan_carries; AnswerPlanTests.swift::testSeveralBoardsShowTheCombinedList, ::testTheCombinedListSaysWhichEffortsItsModelsStandAt, ::testTheCombinedListCarriesEveryDisclosureItOwes, ::testAStaleBoardIsSaidOnTheCombinedListAsLoudlyAsOnTheCards, ::testAnOldPhoneCopyIsSaidOnTheCombinedList, ::testThePlanIsGivenTheRoutedSurfacesOwnHealth, ::testTheEffortNoteNamesEveryEffortInBothLanguages, ::testABoardThatPublishesNoEvaluationDateIsDatedByTheDayItWasRead; LanguageTests.swift::testTheCombinedListSaysItIsTheProductsOwnInBothLanguages, ::testTheDetailsSentencesSayTheirFactsInBothLanguages; NoticesTests.swift::testAnEmptyAnswerSaysWhichOfItsThreeReasons, ::testTheEnginesThreeEmptyAnswersAreEachSaidTruly, ::testEveryNoticeOfTheCodingScreenReachesTheReaderInTurkish; StandingsStoreTests.swift::testAKeptCopyServedAfterAFailedFetchCarriesItsAge; ScreenPathTests.swift::testTheCombinedListShowsTenRowsAndTheRestOnRequest; test_empty_answer_reasons.py::test_each_reason_carries_its_code, ::test_an_unreadable_artifact_says_so_by_code. The view's half is pinned by value and by brace depth (review M4); it is seen whole only by `make ui-test`, which no gate runs (D-175). |
| REQ-APP-004 | The app degrades honestly: engine unreachable, 503, an empty answer and a slow response each produce a stated condition — never a blank screen and never an endless spinner. | **MET.** Evidence: test_ios_client_contract.py::test_the_client_bounds_how_long_it_will_wait, ::test_every_failure_the_client_names_reaches_the_screen_with_a_sentence; EngineClientTests.swift::testATimeoutIsNotReportedAsAnUnreachableEngine; test_unavailable_after_boot.py::test_the_503_says_the_evidence_is_unavailable_rather_than_naming_the_query. The "unreachable 503" caveat is closed by REQ-IOS-003 (W-039 FIXED). Timeouts are checked in source and against a stubbed URLSession, not on a device. |
| REQ-APP-005 | The app computes no ranking value of its own, with the one exception D-160, D-167 and D-168 permit: `Combine.swift` orders the models every chosen board ranks by the sum of their positions, ties sharing a place, and the screen says the order is the product's own. Scores and prices are rendered as received (Trap 1; protects D-104, D-105, D-109). | **PARTIAL.** Missing: formatter rounding is invisible to the checks; a number passed through `Any` or text is not followed, and the served facts reach the phone that way (gap G-2, #171); the Engine-layer Swift tests do not cover views. Since D-181 (#60) arithmetic on any number a type's own declaration decodes, by the operators and numeric methods D-181 clause 3 lists, through the names clause 2 lists (D-181 is the one list), and a second sort under a permitted name, the standard library's or Foundation's, fail the declaration gate on the compiled module; other operators, methods and names are gap G-2 (#173) (test_client_decl_gate.py::test_arithmetic_on_a_served_number_is_refused_whatever_carries_it, ::test_a_second_sort_under_a_permitted_name_is_refused, ::test_foundations_sort_is_counted_as_a_sort); the price in pages (REQ-CMP-002) is the one conversion of a served price, permitted in `priceInPages` only (::test_the_price_in_pages_is_permitted_where_it_is_computed). Evidence so far: CombinePropertyTests.swift::testGeneratedCombinationsMatchIndependentGroupedReference; CombineTests.swift::testTiedModelsShareAPlace, ::testAnEqualSumIsBrokenByIdEvenWhenTheNamesSortTheOtherWay; test_ios_client_contract.py::test_the_client_performs_no_arithmetic_on_a_number_the_engine_sent, ::test_position_arithmetic_happens_only_where_an_adr_permits_it, ::test_the_client_applies_no_ordering_of_its_own. |
| REQ-APP-006 | *(added at the M18 closure, from D-175's decision on #78)* On the combined list, the reader may keep only the models with an API or open weights. The filter reads the accessibility `/v1/boards` serves; a model with no published access, or a value this build does not know, is not claimed. It hides rows and never re-ranks: each row keeps its place among all the shared models, and the screen says how many it shows of how many. | **MET.** Evidence: AnswerPlanTests.swift::testTheFilterKeepsModelsWithAnAPIOrOpenWeights, ::testFilteringKeepsEachModelsPlace; ScreenPathTests.swift::testTheAccessFilterHidesRowsAndSaysHowMany (`make ui-test`, run on the owner's Mac only, D-175). |
| REQ-API-010 | Any contract gap the client finds is recorded as a finding against `/v1` before any client-side workaround. **Declared class: PROCESS** — its obligation is about the record trail, not about running code. | **MET.** Evidence: test_contract_change_provenance.py::test_the_permission_to_move_the_contract_exists_and_is_claimed_exactly_once, ::test_a_field_the_payload_publishes_is_a_field_an_adr_accounted_for, ::test_no_record_claims_the_revision_window_is_unspent_while_it_is_spent. |

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
| REQ-REF-001 | One command performs one refresh cycle: build into a temporary artifact, compare it against the live one, publish only if it should be. It never leaves the live artifact worse than it found it, including when killed mid-run. | **MET.** Evidence: test_refresh.py::test_a_builder_that_raises_leaves_the_live_artifact_untouched, ::test_a_sigkilled_cycle_leaves_the_live_artifact_byte_identical; test_nightly_refresh.py::test_a_cycle_killed_mid_publish_leaves_the_live_artifact_and_the_lock_usable. |
| REQ-REF-002 | "Changed" is decided on the CONTENT THAT WOULD BE SERVED — not file bytes, not timestamps. An unchanged upstream produces no publish and says so. | **MET.** Evidence: test_refresh.py::test_a_moved_timestamp_is_not_a_change; test_refresh_boards.py::test_the_fingerprint_moves_with_a_board_and_only_with_it. |
| REQ-REF-003 | A refresh REFUSES to publish an artifact that is worse than the live one: fewer surfaces answering, or materially less evidence behind any surface. The refusal is a first-class outcome with its own exit code, not an error. | **MET.** Evidence: test_refresh.py::test_a_candidate_that_blinds_a_surface_is_refused; test_floor_served.py::test_a_board_that_loses_a_quarter_of_its_names_is_refused. Since D-179 a board's rows are compared by the model each links to, and what the guards are for still refuses (test_refresh_board_ids.py::test_what_the_board_guards_are_for_still_refuses), while a re-spelling does not (::test_a_board_whose_rows_are_only_re_spelled_moves_no_guard). |
| REQ-REF-004 | Every cycle leaves a durable record of what it did and why — published, unchanged, refused or failed — carrying the numbers it decided on. | **MET.** Evidence: test_refresh.py::test_the_record_names_the_surface_that_caused_a_refusal; test_nightly_refresh.py::test_health_reports_the_last_recorded_cycle_and_the_next_run. |
| REQ-REF-005 | A refresh runs every 12 hours without a human, and a human can find out that it stopped running at all. **Silence must not be indistinguishable from success.** | **SUPERSEDED** by D-151 (once a night, 23:00-01:00) and D-154 (the engine runs it as a child process; the launchd job and its installers are removed, D-173 clause 7). Replaced by REQ-REF-008. The "find out it stopped" half is now `/health` (test_nightly_refresh.py::test_health_reports_the_last_recorded_cycle_and_the_next_run). |
| REQ-REF-006 | The running engine serves a replaced artifact without a restart, and a request in flight during the swap completes on consistent data. | **MET.** Evidence: test_refresh.py::test_the_engine_serves_a_replaced_artifact_without_a_restart, ::test_a_reader_open_before_the_swap_finishes_on_consistent_data. |
| REQ-REF-007 | Ingestion never runs on the serving host (D-116). The refresh produces an artifact and hands it over; it does not reach into a serving process. | **PARTIAL.** Missing: Still true: the physical half is unmet because nothing is deployed. Since D-154 the refresh even runs as a child of the serving engine on the same Mac; production refuses the switch (test_nightly_refresh.py::test_production_refuses_to_boot_with_the_switch_on). W-125 (accepted): the serving process still loads the parsers and `httpx`. Evidence so far: test_refresh.py::test_the_refresh_never_imports_the_serving_adapter; test_nightly_refresh.py::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers. |

## M10 — the router (REQ-RTR) and the guards, added at W1

D-126 ruled the router at M8 — *"the router picks the QUESTION; the engine answers it"*, and it may
never say a model is good — and it was never given a REQ-ID or a wave until the owner asked where
it had gone. These are written here at W1, before any code.

**Measured before planning:** the on-device options cost **zero app bytes** and send nothing off the
phone. `FoundationModels` needs iOS 26 and an Apple Intelligence-eligible device; `NLEmbedding`
needs iOS 13 and covers every device this app targets (deployment target 18.0).

| REQ-ID | Requirement | Status |
|---|---|---|
| REQ-RTR-001 | A user types a question in their own words and the app opens the surface that answers it. The router's choice is SHOWN and changeable with one tap (D-126). | **PARTIAL.** Missing: No test cites REQ-RTR-001. "Changeable with one tap" holds only when the wording tier answered. Otherwise it takes two taps (`Change`, then the surface), as REQ-ASK-002's own status admits. Evidence so far: FrontDoorTests.swift::EchoTests, ::testTheCorrectionReachesEverySurfaceTheEngineServes; RouterBoundaryTests.swift::testTheSimilarityTierRoutesAPlainCodingQuestionToACodingSurface. |
| REQ-RTR-002 | **The router can only ever yield one of the nine category ids.** A recommendation, a model name, prose or an injected instruction is discarded and the user gets the manual fallback, correctable from the `Change` sheet (the chips became that sheet at M13-W3). Where the framework allows it the closed set is a SCHEMA constraint, not a prompt instruction. | **MET.** Evidence: RouterBoundaryTests.swift::testTheDefaultRouterNeverYieldsAnIdOutsideTheKnownSet, ::testAnIdTheEngineDidNotServeIsRefused; test_router_hints.py::test_the_router_validates_against_the_ids_the_engine_serves. |
| REQ-RTR-003 | The router is never required. Unreachable, ineligible, disabled, slow or wrong — the product still works through the `Change` sheet (a chip until M13-W3), and says which happened. | **MET.** Evidence: RouterBoundaryTests.swift::testWithNoTierAtAllTheReaderStillGetsASurface, ::testTheModelTierIsNotConsultedWhenTheDeviceHasNone; FrontDoorTests.swift::testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier. |
| REQ-RTR-004 | Nothing typed reaches the ENGINE, and nothing the engine serves is influenced by the router beyond which surface is opened. The scoring path is untouched (D-104). | **MET.** Evidence: test_router_hints.py::test_nothing_typed_by_the_reader_reaches_the_engine; EngineClientTests.swift::testNothingTheReaderTypedIsEverSent. |
| REQ-RTR-005 | *(verified against the real on-device model by the owner on 2026-08-23 — it warned.)* A question the catalogue does not measure routes to `assistant` **and says so** — that it is not measured here and is being answered with the general chat ranking. | **PARTIAL.** Missing: W-123 (accepted, owned by M19 with #66): 5 of 16 ordinary questions still reach a measured surface with `unmeasured = false`. Evidence so far: RouterBoundaryTests.swift::testAnUnmeasuredOutcomeDisclosesItselfRatherThanImplyingAMeasurement, ::testAQuestionBelowTheFloorIsFlaggedUnmeasured; test_router_hints.py::test_the_unmeasured_fallback_is_a_surface_the_engine_actually_serves; FrontDoorTests.swift::testAnOrdinaryQuestionLandsOnGeneralHelpRatherThanAMeasuredSurface. M18-W3 (#113): a request to make an image the model routed to `vision` is answered as unmeasured (ReadingTests.swift::testARequestToMakeAnImageRoutedToVisionIsUnmeasured). M19-W4 (D-184): the rule reaches every surface but code, on both tiers, and a question the tier sent to code keeps its surface (ReadingTests.swift::testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted; ReadingTests.swift::testTheImageRuleNeverOverridesAnotherSurface). On fresh held-out sets, 8 and 8 of 20 such requests were answered as unmeasured with the model, 18 and 18 without it (`docs/research/m19-w4-question-reading-probe.md` §4). |
| REQ-GRD-001 | A refresh REFUSES a candidate whose evidence moved upward in a way ordinary upstream movement does not produce. It refuses; it never judges and publishes. | **MET.** Evidence: test_refresh.py::test_a_surface_filling_with_models_nobody_has_seen_is_refused; test_floor_served.py::test_a_board_flooded_with_rows_it_has_never_seen_is_refused, ::test_a_board_that_loses_a_quarter_of_its_names_is_refused. |
| REQ-ANM-001 | No such requirement was written. `docs/plans/m10-wave-4-close.md:37` lists it among the M10 ids added here, in the place of the upward-anomaly refusal, which the M10 plan (§2, row 5) and this file name REQ-GRD-001. | **SUPERSEDED.** By REQ-GRD-001, the row above: the id is a misnaming of it. No version of this file ever carried REQ-ANM-001 (`git log -S 'REQ-ANM'` finds only the close record's commit). |
| REQ-GRD-002 | No refresh can be made to allocate without bound by an upstream: every paginating client caps total accumulated rows and bytes. | **MET.** Evidence: test_arena_client.py::test_the_total_merged_rows_are_bounded_not_only_the_page_count. |
| REQ-GRD-003 | The refresh states its environment assumptions as CHECKS, not assumptions. | **MET.** Evidence: test_refresh.py::test_a_clock_that_cannot_be_reasoned_about_stops_the_cycle. |
| REQ-EVI-002 | The population the engine actually ranks — reconciled AND priced — has a NAME in the code, and calibration must call it. | **MET.** Evidence: test_ranked_population.py::test_every_threshold_producing_script_imports_the_named_accessor. |
| REQ-REV-001 | K.7 is executable in a single-agent lane: a wave-close review row that passes must cite a review record declaring `seat: independent`, and a cited review record that does not exist fails in every era. | **MET.** Evidence: test_review_seat_gate.py::test_a_self_review_cannot_close_a_wave_green. |
| REQ-IOS-001 | The Engine layer is executed by a gate: `Router`, `EngineClient` and their boundaries have tests that run from the command line and are wired into `make check` and `runner`. | **MET.** Evidence: `swift-test` is a leg of `make check`; ios/EngineTests (268 tests); test_swift_test_manifest.py::test_the_manifest_lists_exactly_the_tests_the_sources_declare. The row says "18 tests". There are now 268. |
| REQ-IOS-002 | The router's boundary is proven IN SWIFT: no path yields an id outside the nine, every tier can be absent without blocking the screen, and an unmeasured question reaches the surface flagged as unmeasured. | **MET.** Evidence: RouterBoundaryTests.swift::testTheDefaultRouterNeverYieldsAnIdOutsideTheKnownSet, ::testAQuestionBelowTheFloorIsFlaggedUnmeasured, ::testAQuestionAboveTheFloorIsNotFlaggedUnmeasured. |
| REQ-IOS-003 | The 503 the client is required to render honestly can be PRODUCED on demand, so the branch that renders it is reachable by a test. | **MET.** Evidence: test_unavailable_after_boot.py::test_the_503_says_the_evidence_is_unavailable_rather_than_naming_the_query. |
| REQ-API-011 | `/v1` gives ONE account of a query: the `ranking` array and the `picks` array cannot disagree about what was ranked. | **MET.** Evidence: test_budgets_endpoint.py::test_the_published_cap_reproduces_the_engines_own_eligible_count. Numbered REQ-API-010 until #33; M11's plan and closure report use that number. |
| REQ-RUN-001 | The product has been operated by a person against a running engine, and what was asked and what came back is written down — including anything that looked wrong. | **MET.** Evidence: OwnerSessionDefectTests.swift::testTheModelTierCanExpressThatNothingMeasuresTheQuestion, ::testTheSelectedSurfaceIsShownFirst, ::testThePreviewDoesNotRepeatAModelAlreadyShownAsAPick (the W-063/064/065 tests). A process criterion, met by the 2026-08-22 owner session. |
| REQ-RUN-002 | The 12-hour refresh has completed at least two unattended cycles on the schedule, and the status file it left is read back and reported. | **SUPERSEDED** by D-151, D-154 (the 12-hour launchd schedule is retired). The intent is still unobserved for the replacement: no record shows two unattended nightly engine cycles. `advisor.db.refresh.json` holds one cycle, at 2026-09-23T22:16Z: outcome `refused`, `consecutive_refusals` 2. If the owner still wants that observation, it is open work. |
| REQ-GOV-001 | Every ADR cited anywhere in this repository exists; `C2b` counts something it can actually reach. | **MET.** Evidence: test_adr_citations.py::test_every_cited_adr_exists; test_c2b_counter.py::test_three_acceptances_of_one_control_fire. |
| REQ-LOC-002 | Text matching in the client is correct under a Turkish locale, pinned by a test that SETS the locale rather than inheriting it. | **MET.** Evidence: OwnerSessionDefectTests.swift::testTheFilterLocaleIsPinnedAndIsNotTheReadersLocale, ::testTheFilterFoldsCaseTheSameWayInEveryLocale. |
| REQ-CMP-001 | Every number a reader meets carries, beside it, something that says what it means without domain knowledge — including a RANK where the scale is arbitrary. | **MET.** Evidence: OwnerSessionDefectTests.swift::testTheRankIsThePositionInTheEnginesOwnOrdering, ::testTheTwoScalesTheOwnerCouldNotReadAreExplained, ::testAnUnknownMetricExplainsNothingRatherThanGuessing. Amended by D-140/D-143: ECI shows its rank range only. |
| REQ-CMP-002 | Price is expressed in a unit a person outside this industry uses, without removing the exact figure. | **MET.** Evidence: OwnerSessionDefectTests.swift::testACheapModelIsPricedInWholePagesRatherThanFractionsOfACent, ::testTheExactPriceIsNeverReplaced; LanguageTests.swift::testTheScaleExplanationAndThePriceSpeakTurkishToo. |
| REQ-CMP-003 | Every surface name says what the surface measures, in words a non-specialist would choose. No two surfaces begin with the same word. | **MET.** Evidence: test_category_titles.py::test_no_two_titles_begin_with_the_same_word, ::test_no_title_uses_a_word_that_only_this_industry_knows. |
| REQ-DSC-001 | A limitation that is a property of a SOURCE is stated once per source; a limitation that is a STATE of the data keeps its warning treatment (D-135). Every fact remains reachable. | **MET.** Evidence: OwnerSessionDefectTests.swift::testEveryFactSurvivesClassification, ::testAnUndatedSourceSaysItOnceRatherThanTwice. |
| REQ-BGT-001 | A reader can choose a budget in the app, and the answer changes when they do. | **SUPERSEDED** by the signed m13-plan §2 W3 ("Remove both top strips"), on the owner's directive and the council's unanimous vote (`docs/second-opinion.md` Q4). The M13 closure report the owner ratified on 2026-09-20 records the budget client code deleted with its tests. No ADR records the retirement. The app asks every question at `unlimited` (`ios/ModelRanking/ContentView.swift::budget`); D-134 keeps `/v1/budgets` for other consumers. |
| REQ-LOC-001 | `/v1` returns the FACTS behind each sentence; the client composes the sentence, in English or Turkish, from those facts alone. | **MET.** The notices joined the pick sentences at M18-W2 (D-176): staleness, undated evidence, the effort mix, the close call (`close_call_fact`), the ordering note, the ranked-on line, an empty answer by its reason code (D-176 clause 7), effort names, and the failure screen (#96). Where a fact is missing the engine's English is shown, D-136's fallback; the engine's own refusal is shown as sent. Evidence: test_why_facts.py::test_every_pick_carries_a_fact_for_its_sentence, ::test_every_number_the_sentence_quotes_is_in_the_fact, ::test_every_close_call_on_the_artifact_carries_the_values_it_quotes; test_recommend.py::test_the_served_close_call_carries_its_fact; LanguageTests.swift::testEveryReasonTheEngineCanEmitHasBothSentences, ::testBothLanguagesQuoteTheSameNumbers, ::testEveryFailureSaysWhatHappenedInBothLanguages; NoticesTests.swift::testAStaleBoardIsSaidInBothLanguagesWithoutItsSourceIds, ::testAnEmptyAnswerSaysWhichOfItsThreeReasons, ::testTheEnginesThreeEmptyAnswersAreEachSaidTruly, ::testEveryNoticeOfTheCodingScreenReachesTheReaderInTurkish, ::testWithoutTheFactsTheEnginesOwnSentenceIsShown; test_empty_answer_reasons.py::test_each_reason_carries_its_code. On the screen: ScreenPathTests.swift::testATurkishReaderIsAskedBackInTurkish (#133). |

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
| REQ-FIX-001 | Pareto dominance admits equality on one axis: a row is dominated when another is at least as good on BOTH quality and cost and strictly better on at least one. Both the model engine and the subscription engine agree. | **MET.** Evidence: test_pareto_dominance.py::test_model_engine_frontier, ::test_subscription_engine_frontier. |
| REQ-FIX-002 | Startup refuses an evidence database the serving path cannot read. A database carrying `scores`, `pricing` and a non-empty `px_median` but missing a table a ranking joins is REFUSED, not admitted. | **MET.** Evidence: test_startup_schema_validation.py::test_a_database_without_models_is_refused, ::test_a_servable_artifact_is_accepted. |
| REQ-FIX-003 | A change that alters the attribution a reader is shown changes the refresh fingerprint, so the artifact publishes. Attribution is a licence obligation (REQ-LIC-001), not a display detail. | **MET.** Evidence: test_refresh_attribution_fingerprint.py::test_a_changed_evidence_source_changes_the_digest. |
| REQ-FIX-004 | `runner` cannot report a leg it did not run as a pass. An absent environment is `SKIPPED`, and any skip prevents the all-green claim. | **MET.** Evidence: test_runner_accounting.py::test_a_skip_prevents_the_all_pass_claim. |

## M13 — say only what we know (REQ-UNC), added at W2

The display is made honest BEFORE it is redesigned. W3 removes the controls that currently slow a
reader down; these are the statements that stop the remaining numbers from overstating.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-UNC-001 | Where the engine's own `close_call` margin says two models are indistinguishable, the screen does not present them as ordered. Every position is shown as the range of places the margin allows (`#1–27 of 50` for today's `expert` leader), so two models inside the margin of each other always have overlapping ranges; how many the benchmark cannot separate from the leader is stated once per ranking. **Amended 2026-09-15 by the owner**: the plan's text said "render a shared band" (council ruling D1), and the W2 review measured bands printing 47 within-margin pairs (45 on raw scores) as ordered. | **MET.** Evidence: UncertaintyTests.swift::testTwoModelsInsideTheMarginOfEachOtherAlwaysOverlap; test_uncertainty_contract.py::test_the_served_margin_reproduces_the_engines_own_close_call_decision. |
| REQ-UNC-002 | Nothing on screen calls a coverage count a confidence. The reader is told how many independent benchmarks measured the pick, and how old the oldest of them is. Verified by: a pick whose secondary is more than 180 days old carries that age. | **MET.** Evidence: test_secondary_evidence_age.py::test_a_secondary_older_than_the_threshold_does_not_upgrade; test_uncertainty_contract.py::test_the_published_age_is_the_one_that_decided_the_count; UncertaintyTests.swift::testTwoCurrentBenchmarksStateTheSecondOnesAge. |
| REQ-UNC-003 | Every score source carries a date, or the product names the one that does not. | **MET.** Evidence: test_board_run_dates.py::test_a_board_with_an_evaluation_date_declares_it; test_uncertainty_contract.py::test_an_undated_surface_names_its_benchmark_on_the_live_route. The caveat "the shipping artifact predates the fix" is obsolete: the artifact is rebuilt nightly. |

## M13 — the question is the front door (REQ-ASK), added at W3

The owner's report, translated from Turkish: *"it felt like a search bar, not an AI"*. The question
field becomes the only input on the home screen; the two strips of controls above it go, and the
correction they offered survives as a `Change` sheet.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-ASK-001 | The question field is reliably focusable, raises a keyboard, and can be submitted without one. | **PARTIAL.** Missing: Still true: the software keyboard, typing, Return and the send button have not been verified on a simulator or device. The owner's check is pending (the M13 closure marks it ◐). Evidence so far: FrontDoorTests.swift::SubmissionTests (SubmissionTests); test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on. |
| REQ-ASK-002 | The screen shows what it understood, and it can be corrected in one tap: `"prove a theorem" → Mathematics` renders with the reader's own words, and a correction reaches every one of the nine surfaces. | **PARTIAL.** Missing: "Corrected in one tap" holds only when the wording tier answered. The model tier and below-floor questions need two taps (the row's own text says so). Evidence so far: FrontDoorTests.swift::EchoTests, ::testTheCorrectionReachesEverySurfaceTheEngineServes, ::AlternativeSurfaceTests. |
| REQ-ASK-003 | A question the catalogue does not measure returns a ranking AND a statement, above it, of what that ranking cannot tell the reader. It is never silently answered as if measured; `tier = manual` may not carry `unmeasured = false`. Input that is not a model search at all is REQ-ASK-005's instead (D-169). | **PARTIAL.** Missing: W-123 (accepted, owned by M19 with #66): ordinary questions are still answered as measured (5 of 16 on held-out sets; M18-W3's reading caught 1 of 10 knowledge questions). Evidence so far: FrontDoorTests.swift::UnmeasuredQuestionTests (UnmeasuredQuestionTests); RouterBoundaryTests.swift::testWithNoTierAtAllTheReaderStillGetsASurface. |
| REQ-ASK-005 | Input that is not a search for a model (an attempt to instruct the model, a knowledge question, chit-chat or nonsense, content pasted for the app to act on) gets a guiding note with an example and no ranking, or, where the app is not sure, a one-tap question back; it sends no request and is not recorded as a gap (D-169, amended at M18-W3). | **PARTIAL.** Missing: the catch bar of D-169 clause 6. On M19-W4's fresh held-out set (`docs/research/m19-w4-question-reading-probe.md` §4, D-184), no genuine search got the note and 2 and 1 of 40 were asked (bounds held), but 25 and 27 of 50 not-a-search inputs were caught, against 40 (18 and 21 before); knowledge questions 6 and 6 of 20 (1 and 3 before), against a bar of 14 (#66). Evidence so far: ReadingTests.swift::testAQuestionOfFactIsRead, ::testAQuestionOfFactIsAskedAndWithTheModelsDoubtIsTheNote, ::testSmallTalkAsPeopleTypeItIsRead, ::testATaskWithItsContentAsPeopleTypeItIsRead, ::testAnInstructionAsPeopleTypeItIsRead; ReadingTests.swift::testTextWithNoWordInAnyLanguageIsRead, ::testContentPastedInToBeActedOnIsRead, ::testAnInstructionToTheAppIsRead, ::testSmallTalkIsRead, ::testTheDecisionTable, ::testTheModelsDoubtAloneIsAQuestionBack, ::testSmallTalkIsANoteWhateverTheModelSays; ScreenPathTests.swift::testADoubtIsAskedAndNoIsTheNote, ::testAHeldSecondQuestionClearsTheFirstAnswer, ::testATurkishReaderIsAskedBackInTurkish, ::testPastedContentTheModelDoubtsIsTheNote, ::testFindAModelAnswersTheQuestionAsRouted, ::testAnInstructionToTheAppIsAskedWhateverTheModelSays, ::testNoWordIsTheNote, ::testChangeFromTheNoteShowsTheChosenRanking. |
| REQ-ASK-004 | A slower response for a previous selection can never overwrite the current one. | **MET.** Evidence: FrontDoorTests.swift::RequestGateTests, ::testASelectionMadeWhileAQuestionRoutesWins; test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on. |

## M13 — the card says what a number is out of (REQ-CMP-004), added at W4

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-CMP-004 | A score is shown with its ceiling where one exists (`Score 83.5 / 100`), with its scale NAME where the scale is unbounded but published (`Score 1504.2 Elo`), and as a rank alone where neither exists (ECI). No two surfaces' scores are presented as comparable. | **SUPERSEDED** by D-143 (out of 100); D-162 (the anchor is the floor). Replaced by the amended row at line 493. **Duplicate ID** with a different status. |
| REQ-CMP-004 **(amended M14-W4 by D-143; the row above is the M13 rule and no longer describes the product)** | An Elo score is shown out of 100 against the surface's anchor (its floor, D-162), not as `Score 1504.2 Elo`; a bounded percentage is shown as it was; ECI is still rank-only. The scale NAME is not put in front of the reader on a card or a row. | **M14-W4.** `ios/ModelRanking/Engine/Scores.swift::scoreText`. Cited by `ios/EngineTests/ScoresTests.swift::OutOf100Tests`. The M14 closure seat found the row above still stating the superseded rule (MAJOR-5); it is kept, marked, because M13's records cite it. |

## M14 — the catalogue answers questions people ask (D-142)

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SRC-010 | *(amended at M14, m14-plan §4)* An LMArena board's licence is on record, and its source registration cites it, before any of its data is served. For the LMArena boards that is the dataset-level CC-BY-4.0 grant reviewed at D-101; no per-board review is owed. | **MET.** Evidence: test_arena_client.py::test_every_registered_arena_board_is_attributed_and_floored. The M14-W1 record found the image-editing board is a config of the dataset already read under that grant (`docs/plans/m14-wave-1-close.md:32`). No image-editing data is served (REQ-IMG-002). M19-W1 (#124) holds each source's credit to its publisher's current terms, the part the licence ruling (#88) does not decide: an external board names its original source (test_attribution_terms.py::test_an_external_board_credits_its_original_source), each Creative Commons notice links its material and licence (::test_a_creative_commons_source_links_its_material_and_its_licence), and SWE-bench and Aider each carry their own licence (::test_swebench_and_aider_are_each_credited_under_their_own_licence). |
| REQ-SRC-011 | Each LMArena board is stored under its own source id AND its own benchmark label, taken from the registered board table and never defaulted; an unregistered source id is refused. No two boards share either identifier. | **MET.** Evidence: test_arena_client.py::test_ingest_stores_each_board_under_its_own_benchmark, ::test_ingest_refuses_a_source_no_board_claims, ::test_each_board_carries_its_own_source_id_and_benchmark. |
| REQ-IMG-001 | The ranked population of the image-editing surface is COUNTED and published in the wave record before any threshold is chosen. | **MET.** Evidence: `docs/plans/m14-wave-1-close.md:46`: 0 of the board's 55 models reconcile to the registry or carry a price, and the plan's stop condition fired. A process criterion with no citing test; the counting script is pinned by test_calibrate_board.py::test_main_counts_models_and_pairs_models_on_a_board_with_two_names_for_one. |
| REQ-IMG-002 | A tenth surface, image editing, ranks on its own native scale; no score is blended across boards (D-105). | **OPEN.** Never built. It stopped when REQ-IMG-001 counted a ranked population of zero (an image model is priced per image, which `px_median` cannot hold), and it is carried with the image-pricing question (W-105; `docs/plans/m16-plan.md:53`). |
| REQ-IMG-003 | The router routes an image-editing question to that surface, and still refuses image GENERATION. | **OPEN.** Never built: there is no image-editing surface to route to (REQ-IMG-002). The refusal half holds in part. The similarity tier declines a request to make an image (FrontDoorTests.swift::testAQuestionAboutReadingAnImageReachesVisionRatherThanTheImageDecline). The on-device model does not decline one, so a rule in code answers one it routed to `vision` as unmeasured (M18-W3, ReadingTests.swift::testARequestToMakeAnImageRoutedToVisionIsUnmeasured). On a held-out set the rule as first built caught 10 of 15, against a bar of 11. The rule M18 shipped, narrowed by the code reviews, caught 7 of 15 on the same set, then spent, and 3 more were ranked on `web-dev` as if measured (`docs/research/m18-w3-question-reading-probe-2026-10-04.md` §5, §6). M19-W4 (D-184): the rule reaches every surface but code, with the Turkish forms it missed (ReadingTests.swift::testARequestToMakeAnImageIsUnmeasuredWhereverItWasRouted, ::testARequestToMakeAnImageAsPeopleTypeItIsRead). On fresh held-out sets it answers 8 and 8 of 20 requests to make an image as unmeasured with the model (2 and 1 before; bar 14) and 18 and 18 without it (14 before; bar 18), and overrode none of the 20 held-out questions that only mention images; after the code reviews, beyond `vision` it reads only a request for a new image or a change to the asker's own, so a question about an image in a website or a file keeps its surface (ReadingTests.swift::testAQuestionAboutAnImageInASiteOrAFileKeepsItsSurface) (#113, open; `docs/research/m19-w4-question-reading-probe.md` §4). |
| REQ-SUR-001 | Two surfaces, `document` and `factuality`, rank only their own board, each on its own Elo scale (D-105), with floors set by the rule the product ships (D-145). | **MET.** Evidence: test_categories.py::test_the_two_board_surfaces_rank_only_their_own_board, ::test_a_board_only_reaches_its_own_surface_through_the_ranking_query. D-148/D-159 supersede "floors set by D-145": the floor is derived from the board. |
| REQ-GAP-001 | A question the router declines is recorded on the device with its text and a count; a router failure (manual tier) is not a gap; nothing recorded leaves the device; the stored entry is bounded in characters and in bytes. Input read as not a model search, or held for the reader to say, is not recorded (D-169). | **MET.** Evidence: FrontDoorTests.swift::GapRegisterTests, ::GapRegisterHardeningTests; test_router_hints.py::test_the_gap_register_stays_on_the_device. The "nothing leaves the device" clause is enforced by a gate over spellings (the limit W-122 records). The D-169 clause (M18-W3): ReadingTests.swift::testOnlyASearchIsKeptInTheGapRegister; a gate on the screen's held branch, test_ios_client_contract.py::test_the_front_door_is_wired_to_the_logic_it_depends_on. Since D-180 (M19-W2, #85) the compiled module holds it too, by the routes D-180 names: neither privacy sink holds anything another file can change, reads state another file sets, or calls what another file declares unless it is listed; the code a sink runs elsewhere reads no shared mutable state; only the engine's answer and the store's file build standings, only the engine client builds a client on an address of its own, and only the store builds or saves to a store; a kept type is extended nowhere else and conforms to no app protocol; no file touches memory unsafely (test_client_decl_gate.py::test_a_sink_holding_or_reading_shared_mutable_state_is_refused, ::test_standings_built_outside_the_two_sinks_are_refused, ::test_only_the_engine_client_builds_a_client_on_an_address_of_its_own, ::test_a_sink_holds_nothing_another_file_can_change, ::test_a_sink_calls_nothing_another_file_declares_but_what_is_listed, ::test_the_code_a_sink_runs_reads_no_shared_mutable_state, ::test_only_the_store_builds_a_store_or_saves_to_one, ::test_a_kept_type_is_extended_only_in_its_own_file_and_conforms_to_no_protocol_the_app_declares, ::test_no_file_touches_memory_unsafely). Routes no rule names are gap G-1 (#172); the date the standings file keeps comes from its caller (#170). |
| REQ-GAP-002 | The owner can read the register in the app, most-asked first, and clear it. | **MET.** Evidence: FrontDoorTests.swift::testTheOwnerReadsTheMostAskedFirst, ::testTheRegisterIsBounded (`clear()` exercised in ::testTheRegisterIsBounded). The PRD still lists the owner reading the register on a running app as "pending". |
| REQ-SCR-001 | Every card and row shows a score out of 100 where an honest conversion exists; on an anchored Elo surface no card sentence names Elo. | **MET.** Evidence: ScoresTests.swift::testAnEloRatingAtItsAnchorReadsFiftyOutOfAHundred, ::OutOf100SentenceTests. |
| REQ-SCR-002 | The conversion is per surface and strictly monotonic: it never reorders a ranking. | **MET.** Evidence: ScoresTests.swift::testTheConversionNeverReordersOnAnyAnchor. |
| REQ-SCR-003 | *(amended by D-162, #15)* An Elo surface's anchor is the floor it recommends from, derived from the served board, so 50 out of 100 is "at the bar"; never the board's maximum. | **MET.** Evidence: test_floor_served.py::test_every_elo_surface_anchors_its_score_at_its_served_floor, ::test_the_anchor_moves_with_the_board, ::test_with_no_artifact_no_anchor_is_invented. Amended by D-162. |
| REQ-SCR-004 | Ties are exactly the engine's: rank ranges use the native margin, and the tie note states that margin on the /100 scale. | **MET.** Evidence: ScoresTests.swift::testTheLeaderNoteSpeaksPointsWhenAnchored. |

## M15 — the detail screen (REQ-DTL), added at W2

**REQ-DTL-001/002 were carried from the M13 council's ruling F2 and moved into M14 by the M13
closure report, where they were not built** — while the M14 plan leaned on them as the mitigation
for taking the metric name off every card (D-143). The M14 closure seat found the screen did not
exist (`docs/warnings.ledger.md` W-105). They are written as criteria here, with citing tests, so
the next milestone cannot inherit them as prose again.

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-DTL-001 | A reader can open one model from a pick OR from any row of the ranking and see, for that model on that surface: the score as the card shows it, the price in both the per-million and the per-pages form, and the surface's tie margin. Nothing on the screen is computed by the client. | **MET.** Evidence: DetailTests.swift::DetailFactTests (DetailFactTests), ::testPriceIsStatedTwiceOnPurpose; test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself. |
| REQ-DTL-002 | The metric's name and the engine's own number on the board's own scale are available on that screen wherever the card does not show them — the converted Elo surfaces and rank-only ECI — with the board named and its result dated, or named as undated. | **MET.** Evidence: DetailTests.swift::testTheUnitTheCardHidesComesBackHere, ::testAPercentageIsNotRestatedAsAMeasuredValue, ::testARankOnlyMetricStillStatesItsNumberHere, ::testAnUndatedBoardSaysItIsUndated. |

## M15 — the surfaces the measurement chose (REQ-SUR), added at W3

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-SUR-002 | Three surfaces — `vision`, `search`, `search_factuality` — each rank ONLY their own board, on their own Elo scale (D-105), with every threshold derived by the rules the product ships and recorded before the surface is served. Each is reachable by a question asked in a reader's own words. | **MET.** Evidence: test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query, ::test_every_surface_names_the_source_its_board_arrives_on, ::test_the_m15_surfaces_ship_the_thresholds_their_calibration_record_states; FrontDoorTests.swift::testTheTwoNewSurfacesAreReachableByAsking; test_floor_served.py::test_every_elo_surface_anchors_its_score_at_its_served_floor. **Stale citation:** the test `test_every_elo_surface_publishes_its_pinned_score_anchor`, once in `test_uncertainty_contract.py`, no longer exists (removed with D-162). Its successor is test_floor_served.py::test_every_elo_surface_anchors_its_score_at_its_served_floor. D-159 supersedes the "thresholds recorded before served" clause for floors. |
| REQ-SUR-003 | A board the engine cannot recommend from is REFUSED, with the count that refused it on record — never served with a threshold invented to make it fit. | **MET.** Evidence: test_arena_client.py::test_an_unregistered_board_is_refused_and_never_defaulted, ::test_every_registered_arena_board_is_attributed_and_floored. |


## M16 — what the engine publishes about a price and a floor (REQ-FLR, REQ-PRC), added at W1

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-FLR-001 | `/v1/categories` publishes each surface's `min_quality` (since D-159 derived from the served board by `src/app/workflows/floors.py`; `null` with no artifact) on that surface's own scale, as its own field. On an Elo surface `score_anchor` is the same number since D-162 (#15): the anchor follows the floor, never the other way round. | **MET.** Evidence: test_uncertainty_contract.py::test_every_surface_publishes_the_floor_it_recommends_from; test_floor_served.py::test_every_surface_publishes_the_floor_derived_from_its_served_board, ::test_the_published_floor_moves_with_the_board, ::test_with_no_artifact_no_floor_is_invented. |
| REQ-FLR-002 | The detail screen shows that floor as the line below which the product does not recommend, in both languages, composed in the Engine from the served fact. | **MET.** Evidence: DetailTests.swift::testTheFloorIsShownOnTheCardsScale, ::testNoFloorIsInventedWhenTheEngineSendsNone, ::testARankOnlyFloorIsStatedInItsOwnUnit. |
| REQ-PRC-001 | A surface whose price leaves something out says so on `/v1/categories` as a CODE (`price_excludes`), not as a sentence, and only the surfaces it applies to carry it (D-153, D-129: the app owns its languages). | **MET.** Evidence: test_uncertainty_contract.py::test_only_the_search_surfaces_say_the_search_call_is_not_in_the_price. |
| REQ-PRC-002 | Wherever the app shows a price for `search` or `search_factuality`, it also says that a search call is not in it. | **MET.** Evidence: test_ios_client_contract.py::test_every_place_that_prints_a_search_price_says_what_it_leaves_out; DetailTests.swift::testTheSearchSurfacesSayTheSearchCallIsNotInThePrice, ::testNoCodeOrAnUnknownCodeSaysNothing; EngineClientTests.swift::testTheFloorAndThePriceExclusionDecode. |
| REQ-REF-008 | The engine refreshes its own artifact once a night inside 23:00-01:00 local and once at startup when no good cycle is on record within a day, through `refresh.py`'s entry point only, in a child process a hang, crash or kill of which cannot block or end the server; it is off by default and refused outside a development environment (D-151, D-154, D-116). | **MET.** Evidence: test_nightly_refresh.py::test_the_run_falls_inside_the_window_and_never_in_the_past, ::test_a_cycle_that_hangs_is_killed_at_the_timeout, ::test_the_server_answers_while_a_cycle_hangs, ::test_production_refuses_to_boot_with_the_switch_on. |
| REQ-REF-009 | A source that fails a cycle keeps serving its last good data -- every source, the required ones included -- for 30 days from when it last arrived in a served cycle; past that, an optional source's surfaces drop and the refresh publishes the rest rather than refusing, and a required source fails the cycle and says it expired (D-156 clause 3). Carried rows meet the store's rules: a date is a calendar date, and a source whose live rows hold a score that is not finite is not carried (M18-W5, #92). What is carried or expired, and how old, is on `/health` and in the refresh record; `/v1` and the app do not change (D-144 as ruled, D-156). | **MET.** Evidence: test_carry_forward.py::test_a_failed_required_source_is_carried_instead_of_failing_the_build, ::test_a_source_older_than_a_month_is_not_carried; test_refresh_carry.py::test_the_2026_09_20_incident_publishes_the_fresh_data_and_carries_the_failed_source, ::test_a_required_source_past_its_age_fails_the_cycle_and_says_it_expired; test_nightly_refresh.py::test_health_names_each_carried_and_expired_source_with_its_age, ::test_health_says_nothing_is_carried_when_nothing_is. |


## M18 — the app on the owner's iPhone (REQ-DEV), added at W1

| REQ-ID | Criterion | Status |
|---|---|---|
| REQ-DEV-001 | The app runs on the owner's iPhone against his engine on his home network. It is opt-in and loopback stays the default: the engine binds loopback unless the installer is told otherwise, a reinstall keeps the mode it finds, and with no Host list a request arriving on a network address is refused. An exposed engine refuses a Host not on its list. The app's engine address is set per build, loopback when unset, and shown under a failure to reach it; `ios/app.sh`'s simulator build is always loopback. Nothing new leaves the phone (D-171, D-126). | **PARTIAL.** Missing: the run on the owner's own iPhone (`docs/owner-iphone.md`), which only the owner can do. Evidence so far: test_engine_host.py::test_a_host_not_on_the_list_is_refused, ::test_a_bind_beyond_loopback_needs_a_list_of_hosts, ::test_without_a_list_a_request_arriving_on_a_network_address_is_refused, ::test_the_host_is_compared_without_case_on_both_sides, ::test_an_empty_host_is_refused_when_a_list_is_set, ::test_an_ipv6_host_is_compared_without_its_brackets_or_port, ::test_without_a_list_a_connection_with_no_local_address_is_not_called_a_network_one, ::test_every_path_is_behind_the_host_check, ::test_the_app_matches_the_code_the_engine_sends_for_an_unknown_host; test_engine_service.py::test_the_wrapper_binds_loopback_and_names_its_hosts_by_default, ::test_the_home_network_is_opt_in_and_names_the_macs_own_names, ::test_the_launchers_preflight_refuses_a_bind_beyond_loopback_without_hosts, ::test_a_reinstall_keeps_the_home_network_unless_told_to_close_it, ::test_only_writing_the_wrapper_reads_the_mode_it_finds, ::test_make_run_binds_loopback, ::test_the_app_script_builds_for_the_simulators_loopback_whatever_the_owners_override, ::test_a_plain_reinstall_writes_the_mode_it_found_and_says_so, ::test_a_deploy_reads_no_live_wrapper, ::test_no_lan_closes_the_home_network_on_the_install_the_owner_runs; test_engine_address.py::test_the_partial_plist_carries_the_address_and_only_the_local_network_exception, ::test_the_client_asks_for_the_key_the_plist_carries, ::test_the_bundle_id_is_set_where_the_owner_can_override_it, ::test_the_failure_screen_shows_the_address_the_app_asked; EngineClientTests.swift::testTheHostIsComparedWithoutCase, ::testAnUnreachableEngineNamesTheAddressItTried, ::testABuildsEngineAddressIsUsedWhenItIsAnHttpUrlWithAHost, ::testAFailureToReachTheEngineShowsTheAddressItAsked, ::testAFailureWhoseCauseIsTheAddressShowsIt, ::testTheAddressLineIsInTheReadersLanguage, ::testAnythingElseFallsBackToLoopback; LanguageTests.swift::testTheEngineAddressLineSpeaksBothLanguages. |
