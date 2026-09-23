---
record_type: register
id: source-expansion-2026-09-23
status: ratified
process_version: v6.0
date: 2026-09-23
---
# More data, fresher data: a survey of sources for combining benchmarks

**The question.** The owner wants data that is both **current** and **plentiful**, because nobody
can know in advance what people will ask. The app's main feature is that Apple Intelligence reads
a question and the engine then **combines several boards** into a list that no single leaderboard
publishes, for example "best model for legal-document summarisation under $X". This document
lists every board already on disk, then the boards available elsewhere, and ranks what to add.

**Method.** The Epoch bundle was downloaded on 2026-09-23 and every CSV was counted by script
(§2). Other sources were tested live on 2026-09-23 by fetching their data endpoints and reading
their licence or terms pages; three parallel research lanes did this, plus direct spot checks.
Anything not confirmed is marked **UNVERIFIED**. None of this is legal advice. Licence flags read
the published terms literally, against the project's own "free and legally usable" rule.

Licence flags used throughout: **PERMITTED** (the terms allow commercial redistribution with
attribution), **UNCLEAR** (no data licence, or an undocumented endpoint), **FORBIDDEN** (the
terms say non-commercial, no redistribution, or no database compilation).

---

## 0. Summary

1. **The cheapest large gain is inside a file the product already downloads.** The LMArena `text`
   config (CC-BY-4.0, published 2026-09-13) carries **29 category slices**, and the product reads
   only `overall`. The slices include `industry_legal_and_government` (375 models),
   `industry_medicine_and_healthcare`, `industry_business_and_management_and_financial_operations`,
   `creative_writing`, `instruction_following`, `multi_turn`, `longer_query`, `coding`, `math`,
   `expert` and **10 language slices**. `vision` adds `ocr`, `diagram`, `homework` and more;
   `webdev` adds `webdev-react` and `webdev-html`. Same parser, same licence. The legal slice alone
   answers most of the owner's example.
2. **The Epoch bundle has 80 boards, 42 of them with at least ten 2026 models, and the product
   reads 7 of those.** The best unread ones for "questions we cannot predict":
   - GDP.pdf: professional PDFs, legal among its 10 domains.
   - APEX-Agents: banking, consulting and law agents.
   - OSWorld 2.0: real GUI computer use.
   - SimpleQA Verified: hallucination, run by Epoch, so CC-BY.
   - FrontierMath T1-3 v2.
   - CursorBench.
   - HLE.
   - CL-bench: "apply my rulebook".
   - `model_metadata.csv`: open-weights and commercial-use class for 1,075 models.
3. **Three findings should be dealt with before anything is added** (§1):
   - (a) The **new Epoch zip changed the ECI layout**. `epoch_capabilities_index.csv` is gone and
     the `everyday` surface's primary board now sits at `epoch_capabilities_index/eci_scores.csv`,
     with a different schema and 268 models against 521.
   - (b) Epoch states that `*_external.csv` data "**retains its original licensing**". Its CC-BY
     does not launder third-party boards, and **ARC Prize's terms forbid commercial reuse** (the
     `abstract` surface).
   - (c) The **SWE-bench leaderboard JSON the `coding` surface reads is CC BY-NC 4.0**.
4. **Several sources elsewhere are fresh and cleanly licensed.** LMArena's other configs (agent,
   image, video), τ²-bench (MIT), BFCL (Apache-2.0, but 9 months stale), Vectara hallucination
   (Apache-2.0, updated 2026-09-22), HealthBench Professional and ClinicalBenchmarks (CC BY 4.0,
   JSON), EQ-Bench creative writing (MIT declared), MTEB (CC0), models.dev (MIT), Epoch
   `all_ai_models.csv` (CC-BY), and the OpenRouter **Data API** (CC BY 4.0, key needed). LiteLLM,
   which the product already reads, carries **per-image, per-second and per-character prices**.
   That unblocks the image, video and speech boards that rank zero today.
5. **Several sources are forbidden or unusable under their terms**:
   - Artificial Analysis: every tier, and §2.5 bans ranking or selection products outright.
   - Vals.ai: the best legal, tax and finance boards, but all rights reserved and no data access.
   - Scale SEAL.
   - Vellum.
   - ARC Prize direct.
   - MathArena (NC-SA).
   - NoLiMa (non-commercial).
   - TR-MMLU (NC).
   - FinanceBench (NC).
   - lechmazur's repos (no licence).
   - fal.ai and Replicate pricing.
6. **Two gaps have no clean, fresh source.** **Long context** (every board is stale, unlicensed or
   HTML-only) and **latency/throughput** (OpenRouter returns nulls unauthenticated, and the
   licence of those endpoints is unclear). **Turkish** has no clean, fresh board either; the
   closest is the Arena `non_english` slice.

---

## 1. Three findings that come before any addition

### 1.1 The Epoch zip changed shape between 2026-08-15 and 2026-09-23

The owner's copy (the bundle fetched 2026-08-15,
77 files) has `epoch_capabilities_index.csv` at the root, with columns
`Model version, ECI Score, Release date, …`. That is the file `sources.py:269` declares.
Today's zip has **no such file**:

| | 2026-08-15 zip | 2026-09-23 zip |
|---|---|---|
| ECI location | `epoch_capabilities_index.csv` | `epoch_capabilities_index/eci_scores.csv` (+ `edi_scores.csv`, `processed_data_for_eci.csv`, `eci_bootstraps.json`) |
| key | `Model version` | `Model` (display-style name). The `model_versions` column is **empty on every row** |
| scored rows | 521 of 819 | 268 (with `eci_ci_low` / `eci_ci_high`) |
| removed | `additional_eci_data/eci_benchmark_difficulties_and_slopes.csv` | — |
| added | — | `benchmark_metadata.csv`, `model_metadata.csv`, `dtbench`, `ebr_bench`, `lmca`, `frontiermath_erdos`, `frontiermath_tier_4_v2`, `frontiermath_tiers_1_3_v2` |

**Consequence.** The next bundle refresh breaks the `everyday` surface's primary board. REQ-ING-013
should make that a loud failure. The new ECI can still be joined to model versions through
`processed_data_for_eci.csv`, which has both `Model` and `model_version`. The new
`benchmark_metadata.csv` is itself useful: it declares every board's `score_column`, `scale`,
`random_baseline`, `score_ceiling` and `superseded_by`, so board declarations could be read from
it rather than written by hand.

### 1.2 Epoch's CC-BY covers Epoch's own runs, not the `_external` files

The zip README says only "Epoch AI's data is free to use … under the Creative Commons Attribution
license". The benchmarking-hub page adds a sentence the repo has not recorded
([epoch.ai/data/ai-benchmarking-dashboard](https://epoch.ai/data/ai-benchmarking-dashboard)):

> "This hub also includes data sourced from external projects, which retains its original
> licensing. Users are responsible for complying with the license terms of the specific data they
> use, and should credit the original sources as indicated."

What this means for boards the product ingests today:

| surface | board | upstream | upstream terms | flag |
|---|---|---|---|---|
| `abstract` | `arc_agi_external.csv` | arcprize.org | [arcprize.org/terms](https://arcprize.org/terms): content may not be "copied, reproduced, aggregated, republished … or otherwise exploited for any commercial purpose whatsoever, without our express prior written permission". It also bans systematic retrieval to "compile … a database" | **FORBIDDEN** |
| `coding` (primary, direct) | `https://swe-bench.github.io/data/leaderboards.json` (`swebench.py:16`) | SWE-bench site repo | LICENSE file is **"Attribution-NonCommercial 4.0 International"** (verified by fetching `LICENSE`) | **FORBIDDEN** for commercial use. The Epoch-run `swe_bench_verified.csv` (CC-BY, 33 models, evaluated to 2026-06-25) is a clean replacement |
| `computer-use` | `terminalbench_external.csv` | tbench.ai | the raw submissions dataset `harborframework/terminal-bench-2-leaderboard` is Apache-2.0. **Submissions closed 2026-05-14**, so the board is frozen | PERMITTED-ish, and **stale by design** |
| `web-dev` | `webdev_arena_external.csv` | LMArena | the same board is in `lmarena-ai/leaderboard-dataset` (`webdev`), CC-BY-4.0 | PERMITTED, but read it first-hand |
| `everyday` (secondary) | `mmlu_external.csv` | HELM plus papers | HELM results have no stated data licence | UNCLEAR (low value anyway: no 2026 model) |
| `agentic-coding` | `deepswe_external.csv` | deepswe.datacurve.ai | not checked | **UNVERIFIED** |

In the bundle as a whole, `scicode_external.csv` is sourced from **artificialanalysis.ai** on all
174 rows, and `critpt_external.csv` uses AA's naming style (source UNVERIFIED). AA's terms forbid
exactly this use (§3). **Do not ingest either without clearing it.**

Scores are arguably unprotectable facts, and a compilation licence is not the same thing as a
database right. Those are arguments for a lawyer, not for this document. Under the project's own
rule, "we may not legally republish it" is "the only reason that counts" (D-142 §2). **The owner
needs to rule** on how `_external` boards are licensed: a per-board upstream licence register, or
explicit permission sought from each upstream.

### 1.3 The largest untapped supply is the Arena data the product already licenses

`lmarena-ai/leaderboard-dataset` was measured on 2026-09-23 through the datasets-server
statistics endpoint. `text/latest` has 10,606 rows: 29 categories × about 400 models, published
2026-09-13.

| group | categories (models) |
|---|---|
| domain ("industry_*") | legal_and_government (375), medicine_and_healthcare (371), business_and_management_and_financial_operations (395), software_and_it_services (402), writing_and_literature_and_language (401), life_and_physical_and_social_science (400), entertainment_and_sports_and_media (400), mathematical (379) |
| task | creative_writing (400), instruction_following (402), coding (397), math (384), expert (352), hard_prompts (402), hard_prompts_english (400), multi_turn (400), longer_query (380) |
| language | english (402), non_english (402), chinese (373), russian (366), german (299), spanish (283), french (281), japanese (265), korean (269), polish (222). **No Turkish** |
| method variants | overall, exclude_ties |

`vision/latest` has overall, english (152), chinese (117), **ocr (108)**, **diagram (108)**,
homework (102), creative_writing_vision (90), humor (84), entity_recognition (48), captioning
and creative_writing (34 each). `webdev/latest` has overall, webdev (128), webdev-html (127),
webdev-react (112) and image_to_webdev (50). `document` has only `overall` (44).

These slices are thinner in votes than `overall`, so their confidence intervals are wider. The
engine already carries `rating_lower` / `rating_upper` and should use them per slice.

---

## 2. The Epoch bundle, every file

**What was measured.** `https://epoch.ai/data/benchmark_data.zip`, downloaded 2026-09-23 and unzipped at
a local unpack of the bundle. It contains 80 benchmark CSVs, `benchmark_metadata.csv`, `model_metadata.csv`,
`README.md` and a directory `epoch_capabilities_index/` holding 3 CSVs and 1 JSON. The numbers
below come from a script (a counting script run in the research session) and are not copied from the README. How they
were counted:

- **rows**: CSV rows. **models**: distinct `Model version` values with a non-empty score.
- **2026**: distinct scored models with `Release date` >= 2026-01-01. This is the best freshness
  signal the bundle offers.
- **newest rel**: newest model *release* date. **newest eval**: newest value in the board's
  evaluation-date column (`Started at`, `Date of evaluation`, `Run date`, `Date added`,
  `Evaluation date`, `Graded at`, `Last updated`, `Date`), or blank when the board has none.
- **score**: the column `benchmark_metadata.csv` names, or the first score-like column for boards
  that metadata leaves blank.
- **Lic**: **E** = Epoch ran the evaluation itself (a non-`_external` file), so the CC-BY-4.0 grant
  covers it. **X** = aggregated from a third party, and per epoch.ai the file "retains its original
  licensing" (see §1.2). The upstream publisher is taken from the file's `Source` column.
- **Verdict**: **A** = ingest next. **B** = worth ingesting for breadth, but thin, stale or niche.
  **C** = skip (legacy academic board, saturated, superseded, or under ~10 models). **IN** = already
  ingested.

### 2.1 Epoch-run boards (Lic E, CC-BY-4.0, the cleanest data in the bundle)

| file | rows | models | 2026 | newest rel | newest eval | score | measures | user question it helps answer | verdict |
|---|---|---|---|---|---|---|---|---|---|
| gpqa_diamond.csv | 313 | 313 | 116 | 2026-09-03 | 2026-09-02 | Best score | PhD-level science MCQ | "expert science/medicine/chemistry question" | **IN** (expert) |
| otis_mock_aime_2024_2025.csv | 291 | 291 | 118 | 2026-09-03 | 2026-09-17 | Best score | competition math | "solve my math problem" | **IN** (mathematics) |
| swe_bench_verified.csv | 35 | 33 | 17 | 2026-06-16 | 2026-06-25 | Best score | GitHub issue fixing | "fix a bug in my repo" | **IN** (as a fallback) |
| simpleqa_verified.csv | 80 | 80 | 52 | 2026-09-03 | 2026-09-02 | Best score | short-fact recall without search, i.e. hallucination rate | "which model makes up facts least", "accurate answers" | **A**: a second, eval-dated board for the `factuality` surface |
| frontiermath_tiers_1_3_v2.csv | 108 | 108 | 72 | 2026-09-03 | 2026-09-18 | Best score | research-level mathematics | "hard or advanced math, proofs, research" | **A**: fresher and harder than mock AIME |
| frontiermath_tier_4_v2.csv | 64 | 64 | 51 | 2026-09-03 | 2026-09-18 | Best score | hardest research math | same, at the top end | B (secondary to Tiers 1-3) |
| chess_puzzles.csv | 224 | 224 | 122 | 2026-09-03 | 2026-09-18 | Best score | chess tactics | "play or analyse chess", "game strategy" | B (niche, but fresh and large) |
| mystery_game_puzzles.csv | 129 | 129 | 93 | 2026-09-03 | 2026-09-18 | Best score | deductive puzzle solving | "logic puzzles, riddles, detective-style reasoning" | B |
| ebr_bench.csv | 21 | 21 | 16 | 2026-09-03 | 2026-09-08 | Best score | playing the board game *Earthborne Rangers* (per epoch.ai) | "board games / rule-following in games" | C (niche) |
| mirrorcode.csv | 8 | 8 | 8 | 2026-09-03 | 2026-09-10 | Best score | week-long reimplementation of whole programs (Epoch and METR) | "build a whole program autonomously" | C for now (8 models) |
| math_level_5.csv | 108 | 108 | 0 | 2025-10-15 | 2025-10-30 | Best score | competition math, saturated (top 0.98) | none: saturated | C |
| frontiermath.csv / frontiermath_tier_4.csv | 101 / 72 | 101 / 72 | 26 / 27 | 2026-05-28 | 2026-06-08 | Best score | superseded, per `superseded_by` | none | C (superseded) |
| frontiermath_erdos.csv | 5 | 5 | 5 | 2026-09-03 | 2026-09-01 | mean_score | open Erdős problems | none (5 models) | C |
| epoch_capabilities_index/eci_scores.csv | 268 | 268 | 74 | 2026-09-09 | — | eci (+ CI) | composite general capability | "best all-round model" | **IN, but the schema changed** (§1.1) |
| epoch_capabilities_index/edi_scores.csv | 58 benchmarks | — | — | — | — | edi, slope | the difficulty of each benchmark | internal: weighting boards when combining them (§5) | useful as metadata |
| epoch_capabilities_index/processed_data_for_eci.csv | 2,780 | — | — | — | — | performance | long table of model × benchmark (58 benchmarks) | internal: joins `Model` to `model_version` | useful as a join table |
| model_metadata.csv | 1,089 | 1,075 | — | — | — | — | accessibility per model: API 511, open weights unrestricted 253, restricted-use 120, non-commercial 28, hosted-only 12, unreleased 10 | "open-source model I can self-host", "can I use it commercially" | **A** as a filter attribute, not as a board |

### 2.2 Aggregated boards (Lic X: the upstream licence governs, see §1.2)

Grouped by what they answer. The upstream is taken from each file's `Source` column.

**Agents, professional work and documents: the "legal/finance/business" questions**

| file | rows | models | 2026 | newest rel | newest eval | score | measures | question | upstream | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| gdp_pdf_external.csv | 49 | 47 | 42 | 2026-09-02 | — | GDP.pdf score (top 0.307) | grounded reasoning over professional PDFs in 10 domains: finance, legal, healthcare, insurance, real estate, HR and others ([surgehq.ai](https://surgehq.ai/benchmarks/gdp-pdf), [arXiv 2607.11192](https://arxiv.org/html/2607.11192)) | "analyse this contract/report PDF", "legal or financial document work" | Surge AI; the dataset is on HF, **licence UNVERIFIED** | **A** (the single most on-point board for the owner's legal example) |
| apex_agents_external.csv | 33 | 33 | 32 | 2026-09-03 | — | Pass@1 | long-horizon professional-services tasks (banking, consulting, law) (Mercor APEX-Agents) | "agent for analyst, consultant or lawyer work" | Mercor, **licence UNVERIFIED** | **A** |
| gdpval_external.csv | 11 | 11 | 0 | 2025-12-11 | — | win rate vs experts | occupational deliverables across 44 occupations (OpenAI GDPval) | "do my job's deliverable" | OpenAI | B (stale, 11 models) |
| rli_external.csv | 15 | 15 | 8 | 2026-09-03 | — | automation rate | real freelance projects (Remote Labor Index, Scale/CAIS) | "can AI do this freelance job end to end" | Scale/CAIS | B |
| cl_bench_external.csv | 23 | 23 | 9 | 2026-03-31 | — | Overall (+4 subscores) | learning new rules and procedures from supplied context | "follow my company handbook or rulebook", "apply these regulations" | Tencent, UNVERIFIED | B+ (strong fit for "use my documents") |
| cl_bench_life_external.csv | 17 | 17 | 12 | 2026-04-24 | — | Overall | reasoning over fragmented personal records (chats, activity logs) | "personal assistant over my messages or notes" | Tencent, UNVERIFIED | B |
| deepresearchbench_external.csv | 41 | 41 | 17 | 2026-05-28 | — | Average score | web deep-research agents (FutureSearch) | "research this topic and write a report" | futuresearch.ai | B+ (pairs with Arena search) |
| vending_bench_2_external.csv | 62 | 62 | 45 | 2026-09-03 | — | $ balance (−31 … 15,515) | long-horizon business management (Andon Labs) | "run a small business or long autonomous task" | andonlabs.com | B (unbounded $ scale; rank only) |
| the_agent_company_external.csv | 16 | 14 | 0 | 2025-09-29 | 2025-10-13 | % Resolved | simulated software-company office tasks | "office automation" | TheAgentCompany GitHub | C (stale) |
| metr_time_horizons_external.csv | 50 | 50 | 6 | 2026-04-07 | — | average_score (+ time horizon) | length of autonomous task achievable at 50% | "how long can it work unattended" | METR | B |

**Computer use / terminal / coding**

| file | rows | models | 2026 | newest rel | newest eval | score | measures | question | upstream | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| terminalbench_external.csv | 204 | 60 | 16 | 2026-04-23 | 2026-05-14 | Accuracy mean | shell/terminal agent tasks | "do this in my terminal" | tbench.ai | **IN** (`computer-use` primary, **but it is a terminal board, not a GUI board**) |
| osworld_2_external.csv | 16 | 14 | 14 | 2026-07-24 | — | Binary accuracy | GUI computer use (OSWorld 2.0) | "operate my computer or apps for me" | xlang.ai | **A** (the real computer-use board; pairs with TerminalBench) |
| os_world_external.csv | 58 | 10 | 2 | 2026-02-17 | 2026-02-03 | Score | GUI computer use (OSWorld v1; agent rows) | same | os-world.github.io | B (10 models) |
| deepswe_external.csv | 69 | 69 | 69 | 2026-09-03 | — | Pass@1 | agentic SWE | "coding agent" | datacurve.ai | **IN** (agentic-coding) |
| cursorbench_external.csv | 47 | 47 | 47 | 2026-09-21 | — | Score (+ cost/tokens/steps per task) | agentic coding inside Cursor | "best model in my IDE" | cursor.com | **A** (fresh; carries cost per task) |
| frontiercode_external.csv | 41 | 37 | 36 | 2026-09-10 | — | Main score | frontier agentic coding (Cognition) | "hard coding agent tasks" | cognition.com | A- |
| frontierswe_external.csv | 13 | 13 | 13 | 2026-09-03 | — | Score (0.04–0.66) | long-horizon SWE: implementation, performance, research | "large engineering project" | frontierswe.com | B (13 models) |
| aider_polyglot_external.csv | 77 | 72 | 0 | 2025-12-01 | 2025-10-03 | Percent correct | multi-language code editing | "code in language X" | aider.chat | **IN** directly from Aider (Apache-2.0); Aider itself is stale (last entry 2025-10-03) |
| scicode_external.csv | 174 | 171 | 123 | 2026-09-21 | — | Score | scientific-computing code | "write scientific/research code" | **artificialanalysis.ai** (174 of 174 rows) | **licence RED**: AA terms (§3) |
| weirdml_external.csv | 173 | 172 | 75 | 2026-09-03 | — | Accuracy | unusual ML-engineering tasks | "data science / ML code" | htihle.github.io | A- |
| ale_bench_external.csv | 116 | 116 | 68 | 2026-09-09 | — | Performance (138–2951, AtCoder-rating-like) | algorithm-engineering / optimisation contests | "optimisation, competitive programming" | Sakana AI, UNVERIFIED | B |
| gso_external.csv | 38 | 38 | 11 | 2026-06-30 | 2026-07-12 | OPT@1 | making code faster | "optimise my code's performance" | gso-bench.github.io | B |
| algotune_external.csv | 18 | 18 | 3 | 2026-03-05 | — | speedup | numerical code speed-ups | same | UNVERIFIED | C |
| gbaeval_external.csv | 23 | 23 | 23 | 2026-07-24 | 2026-07-26 | Overall | building a Game Boy Advance emulator from scratch | "build a big program from scratch" | gbaeval.com | C (niche) |
| posttrainbench_external.csv | 12 | 12 | 12 | 2026-07-24 | — | Average | agents that post-train LLMs | "ML research engineering" | UNVERIFIED | C |
| cad_eval_external.csv | 15 | 15 | 0 | 2025-04-16 | — | Overall pass | OpenSCAD CAD generation | "3D/CAD modelling" | CadEval | C (stale) |
| cybench_external.csv / exploitbench_external.csv | 22 / 20 | 22 / 9 | 1 / 8 | 2026-02 / 2026-04 | — | % solved | offensive cybersecurity | "security testing" | Cybench / UNVERIFIED | C (dual-use; product-policy decision) |
| webdev_arena_external.csv | 131 | 125 | 84 | 2026-09-09 | (page refresh 2026-01-05) | Arena Score | web-app building, human votes | "build me a website" | arena.ai (LMArena) | **IN** (web-dev). The same board exists first-hand in the LMArena CC-BY dataset, so move to that |

**Reasoning, knowledge, science**

| file | rows | models | 2026 | newest rel | score | measures | question | upstream | verdict |
|---|---|---|---|---|---|---|---|---|---|
| arc_agi_2_external.csv | 227 | 203 | 107 | 2026-09-03 | Score (+ cost/task) | abstract visual reasoning, v2 | "novel puzzles, IQ-style reasoning" | arcprize.org | would be **A** on capability (v1 tops out at 0.985), but **FORBIDDEN upstream** (ARC Prize terms, §1.2) |
| arc_agi_external.csv | 247 | 214 | 108 | 2026-09-03 | Score | abstract reasoning, v1 | same | arcprize.org | **IN, and FORBIDDEN upstream** (§1.2) |
| hle_external.csv | 54 | 49 | 12 | 2026-09-03 | Accuracy (+ calibration error) | Humanity's Last Exam | "hardest expert questions", "is it overconfident" | Scale/CAIS | A- (second board for `expert`) |
| critpt_external.csv | 182 | 182 | 126 | 2026-09-21 | Accuracy | research-level physics | "physics problems" | model names follow AA's naming style (e.g. "(Non-reasoning)"); **source UNVERIFIED, possibly AA** | B (licence check first) |
| simplebench_external.csv | 104 | 103 | 36 | 2026-08-12 | AVG@5 | trick-question common sense | "everyday reasoning, not fooled by trick questions" | simple-bench.com, lmcouncil.ai | A- (for `everyday`) |
| lmca_external.csv | 172 | 172 | 105 | 2026-09-09 | Score (2.8–65.5) | conceptual argumentation, expert-rated ([CRI](https://conceptualreasoning.ai)) | "philosophy, argument and essay reasoning" | conceptualreasoning.ai (Anthropic collaboration) | B |
| dtbench_external.csv | 210 | 210 | 105 | 2026-09-09 | Accuracy | decision theory, Newcomb-like problems | "decision-making under uncertainty" | conceptualreasoning.ai | C/B (niche) |
| proofbench_external.csv | 68 | 68 | 54 | 2026-09-21 | Accuracy (+ latency s, cost/test) | mathematical proof writing | "write or check a proof" | **vals.ai** | A- (math). It also carries latency, one of the few latency signals |
| forecastbench_external.csv | 82 | 82 | 22 | 2026-07-16 | Overall | forecasting real events | "predict or forecast" | forecastbench.org | B |
| btf3_external.csv | 15 | 13 | 13 | 2026-09-03 | Pooled score (direction **UNVERIFIED**) | forecasting (FutureSearch) | same | futuresearch.ai | C |
| enigma_eval_external.csv | 46 | 46 | 11 | 2026-07-09 | Accuracy | multimodal puzzle-hunt puzzles | "hard puzzles" | labs.scale.com | B |
| surface_evolver_bench_external.csv | 28 | 28 | 27 | 2026-09-09 | Mean score | physics/geometry simulation with Surface Evolver | niche | yhenon.github.io | C |
| balrog_external.csv | 41 | 40 | 6 | 2026-09-03 | Average progress (eval 2026-09-20) | game-playing agents (NetHack, Crafter …) | "play games" | balrogai.com | B |
| mmlu_external.csv | 249 | 137 | 0 | 2024-12-26 | EM | general knowledge, saturated | general knowledge | HELM plus papers | **IN** (secondary for `everyday`); no 2026 models, so replacing it is worth considering |
| bbh, arc_ai2, bool_q, common_sense_qa_2, gsm8k, hella_swag, lambada, open_book_qa, piqa, science_qa, superglue, trivia_qa, wino_grande, adversarial_nli (`*_external.csv`) | 10–235 | 7–137 | **0** | ≤ 2024-12 | various | 2016–2022 academic NLP | nobody asks these | papers and HELM | **C, all 14** |

**Multimodal: vision, video, spatial**

| file | rows | models | 2026 | newest rel | score | measures | question | verdict |
|---|---|---|---|---|---|---|---|---|
| video_mme_external.csv | 50 | 50 | 0 | 2025-06-18 | Overall (no subs; short/medium/long splits) | video understanding | "summarise or understand this video" | B: the only video-understanding board, but stale |
| blueprint_bench_2_external.csv | 26 | 26 | 24 | 2026-09-03 | Score | photos to floor plan, spatial reasoning (Andon Labs) | "floor plans, interior layout from photos" | B |
| geobench_external.csv | 32 | 31 | 0 | 2025-12-17 | ACW Country % | photo geolocation | "where was this photo taken" | C (stale) |
| vpct_external.csv | 38 | 38 | 0 | 2025-12-17 | Correct | visual physics prediction | niche | C |
| mindcube / spatialviz_bench | 5 / 8 | 5 / 8 | 0 | 2025 | Overall | spatial mental models | niche | C |

**Writing, long context, general mixes**

| file | rows | models | 2026 | newest rel | score | measures | question | upstream | verdict |
|---|---|---|---|---|---|---|---|---|---|
| fictionlivebench_external.csv | 62 | 62 | 1 | 2026-01-27 | per context length 0–192k (metadata uses 16k; the file puts 120k first) | long-context comprehension of stories | "read or summarise a long document or book", "big contracts" | fiction.live | **A for capability, but stale in Epoch (1 model from 2026)**; check upstream (§3) |
| lech_mazur_writing_external.csv | 49 | 49 | 0 | 2025-08-07 | Mean score (6–8.6 of 10) | creative short-story writing | "write a story, marketing copy" | github.com/lechmazur/writing | B: stale here, fetch upstream (§3) |
| live_bench_external.csv | 64 | 53 | 0 | 2025-11-13 | Global avg + reasoning / coding / math / data-analysis / language / IF | contamination-free mix; **the "Data analysis" and "IF" subscores are unique** | "spreadsheet/data analysis", "follows my instructions exactly" | livebench.ai | B: stale here, check upstream (§3) |

### 2.3 What the inventory says

1. **Of the 80 boards, 42 carry at least ten 2026 models.** The project reads 7 of them. The rest
   are still unread capability, most of it fresh, and most of it outside what the 14 surfaces
   measure (professional PDFs, professional-services agents, GUI computer use, research math,
   physics, ML engineering, forecasting, hallucination).
2. **About 20 boards are dead weight.** They are 2016–2022 academic sets with no 2026 model, or
   superseded or tiny boards. Skipping them loses nothing.
3. **Three of the owner's example needs are in the bundle already.** For "legal document
   summarisation": GDP.pdf (professional PDFs, legal among the 10 domains), CL-bench (applying
   supplied rules) and Fiction.LiveBench (long context). They would sit next to Arena `document`
   and `text_factuality` / SimpleQA Verified. Long context is the weak link: Fiction.LiveBench in
   this bundle has only 1 model from 2026.
4. **Cost per task already appears in several boards**: ARC-AGI (cost/task), CursorBench
   (cost/tokens/steps), DeepSWE (mean cost), ProofBench (cost/test and **latency**), Surface
   Evolver, OSWorld 2.0 and ALE-Bench. That is a second, *measured* price axis ("cost to finish
   the task", not "$/M tokens"). It suits budget questions better than list prices, and the engine
   ignores it today.

---

## 3. Other sources: text-model capability boards

Effort: **S** = a new row in an existing parser or a flat CSV/JSON. **M** = a new parser, or
aggregation across files. **L** = scores must be computed from raw data.

### 3.1 Aggregator leaderboards

| source | machine-readable access (tested) | licence for commercial reuse | freshness | coverage and question | effort |
|---|---|---|---|---|---|
| **Artificial Analysis** [artificialanalysis.ai](https://artificialanalysis.ai) | `GET /api/v2/language/models/free` with `x-api-key` (401 without). Free tier = indices, speed, TTFT and price only; 100 req/day | **FORBIDDEN.** [Data Platform Terms v1.1](https://artificialanalysiscdn.com/legal/ProDataPlatformTerms.pdf), 2026-08-19. §2.4(c): no one may "Embed or otherwise make raw Data available through any customer-facing product". §2.4(d): may not "Combine Data with data from third-party sources to create a product". §2.5: no use in a product "whose primary purpose is benchmarking, ranking, comparison … or model/provider selection guidance, without Company's prior written consent". Free tier = "Internal use only with attribution" | fresh (not measured, key needed) | everything, including speech, image and speed | n/a |
| **LiveBench** [livebench.ai](https://livebench.ai) | Documented HF `livebench/model_judgment` is **frozen at 2025-04-07**. Fresh data exists only as undocumented site files, e.g. `https://livebench.ai/table_2026_06_25.csv` (200, 63 models × 23 task columns, including 2026 frontier models) | Site: **CC BY-SA 4.0**, so commercial use is PERMITTED; ShareAlike applies to adaptations | the site CSV is dated 2026-06-25 | reasoning, coding, agentic coding, math, **data analysis**, language, **instruction following** | S technically; **the access path breaks the "documented endpoint" rule**, so ask the maintainers for a documented path |
| **Stanford HELM** [crfm.stanford.edu/helm](https://crfm.stanford.edu/helm) | Documented public GCS bucket `crfm-helm-public/<project>/benchmark_output/releases/<ver>/groups/json/*.json` | **UNCLEAR.** Code Apache-2.0; no data licence stated | Capabilities v1.15.0 (2025-11-24, 68 models, to GPT-5.1 / Gemini 3 Pro preview); MedHELM v4.0.0 (2026-01-19, 13 models); Safety and AIR-Bench 2025-11-24. **No 2026 frontier models** | general, medical, safety, finance | M |
| **Open LLM Leaderboard** | `open-llm-leaderboard/contents` parquet, 4,576 rows | UNCLEAR (no data licence) | **retired March 2025** | open-weights models only | S, but little value |
| **Vellum** | no API, CSV or JSON | **FORBIDDEN** ([terms](https://www.vellum.ai/terms-of-use) §3.3: no scraping, no "benefit of a third party", no competing product) | fresh | mixed provider-reported and self-run | n/a |
| **Scale SEAL / Scale Labs** [labs.scale.com/leaderboard](https://labs.scale.com/leaderboard) | no results API; "robots.txt" disallows `/api/` | **FORBIDDEN** ([terms](https://scale.com/legal/terms): "for your own internal purposes") | fresh (HLE, MultiChallenge, SWE-Bench Pro, PRBench Legal/Finance, MCP Atlas) | reachable only indirectly, via Epoch `_external` (same upstream-licence problem) | n/a |
| **Vals.ai** [vals.ai/benchmarks](https://www.vals.ai/benchmarks) | none (gated enterprise platform) | **FORBIDDEN by default** ("All rights reserved", no licence) | **very fresh** (2026-09-21/22): LegalBench (147 models), Legal Research Bench, Harvey Legal Agent, Finance Agent v2, Excel Modeling, Tax Agent Bench, MedCode, MedScribe | **the best legal, tax and finance signal anywhere**, and the only way to use it is a licensing agreement | n/a (owner decision: ask Vals) |
| **OpenRouter Data API** [docs](https://openrouter.ai/docs/cookbook/administration/data-api) | `/api/v1/datasets/rankings-daily` (top 50 models by tokens per day since 2025-01-01), `/app-rankings`, `/classifications/task`. Bearer key needed, 500/day | **PERMITTED**: "licensed under … CC BY 4.0. You may copy, redistribute, and build on it, including commercially". Not to be re-served as a competing free API. The `/benchmarks` endpoint re-serves AA and Design Arena scores, so treat it as UNCLEAR | live | **usage share**: "what people actually use", per task class | S (but it is the project's first secret; see the source survey of 2026-08-19 §2) |
| **OpenRouter models / endpoints API** (already read for pricing) | `/api/v1/models/{author}/{slug}/endpoints` returns per-provider uptime; **latency and throughput are null without a key** | UNCLEAR, leaning restrictive: [ToS](https://openrouter.ai/terms) §7 and §12 ("Except as expressly authorized … you may not make use of the Materials") | live | uptime; latency with a key (UNVERIFIED) | M |

### 3.2 Capability-specific boards

| capability | source | access (tested) | licence | freshness | effort |
|---|---|---|---|---|---|
| **tool use / function calling** | **BFCL v4** [gorilla.cs.berkeley.edu](https://gorilla.cs.berkeley.edu/leaderboard.html) | `https://gorilla.cs.berkeley.edu/data_overall.csv` (200, 108 rows, 37 cols incl. cost, latency, multi-turn, web search, memory) plus sibling CSVs on the `gh-pages` branch | **PERMITTED** (repo Apache-2.0; the gh-pages branch has no LICENSE of its own) | CSV last changed 2025-12-17: has Opus 4.5, GPT-5.2, Gemini 3 Pro, **not** 2026 models (≈9 months stale) | S |
| **customer-service / tool agents** | **τ²-bench** [taubench.com](https://taubench.com) | `https://raw.githubusercontent.com/sierra-research/tau2-bench/main/web/leaderboard/public/submissions/manifest.json` (29 text, 21 voice, 16 legacy) → per-model "submission.json" (pass^k per domain, cost) | **PERMITTED** (MIT, repo-wide) | pushed 2026-09-19. Airline/retail/telecom have models to 2026-02/03; the newest frontier models (Opus 5, GPT-5.6) have **banking_knowledge only** | M |
| **hallucination when summarising** | **Vectara HHEM** [github](https://github.com/vectara/hallucination-leaderboard) | Markdown table in raw `README.md` (~108 models, "Last updated on September 22, 2026"); per-model JSON on HF `vectara/results` has no licence | **PERMITTED** (Apache-2.0, repo) | fresh (GPT-5.6-sol, Opus 4.7, Gemini 3.1 Pro; Opus 5 / Fable not seen, UNVERIFIED) | S. Parsing a raw Markdown file is not HTML scraping, but it is fragile |
| **medical** | **HealthBench Professional** + **ClinicalBenchmarks** (Arcophos) | `https://healthbenchprofessional.com/data/leaderboard.json` (22 models, `"license": "CC BY 4.0"`, updated 2026-09-08, verified) and `https://clinicalbenchmarks.ai/data/benchmarks.json` (17 health benchmarks, 2026-09-10) | **PERMITTED, with a caveat**: a compilation of mostly vendor-reported scores, some from Vals and AA. Use the `sources` field to drop those rows | fresh (Claude Fable 5, GPT-6 Astra) | S |
| **creative writing, emotional intelligence** | **EQ-Bench site** ([EQ-bench/EQ-bench-site](https://github.com/EQ-bench/EQ-bench-site)) | `creative_writing.js` (Creative Writing v3, 133 models, 2026-09-07), `eqbench3.js` (78), `eqbench4/eqbench4_data.js` (2026-07-26): CSV/JSON wrapped in JS | PERMITTED on a weak basis: README front matter says `license: mit`, and there is no LICENSE file. **Confirm by email.** The cleaner alternative is `EQ-bench/eqbench3` (MIT LICENSE, 76 models, 2026-05-10) | fresh | S–M |
| creative writing, others | lechmazur/writing, confabulations, nyt-connections … | clean CSVs, updated to 2026-09 | **FORBIDDEN/UNCLEAR: no licence on any lechmazur repo** (default copyright). Ask the author | fresh | S if permitted |
| **embeddings / RAG** | **MTEB** | `https://github.com/embeddings-benchmark/results` / HF `mteb/results` (≈703 models; aggregate with the `mteb` package) | **PERMITTED (CC0-1.0)** | daily (2026-09-22) | M–L. A different product category (embedding models, not chat) |
| **OCR / document parsing** | **OmniDocBench** | tables inside raw README.md (~170 rows) | PERMITTED (Apache-2.0) | README updated 2026-09-11 (GPT-5.2, Gemini 3; no Claude) | M (fragile parse) |
| OCR / IDP | IDP Leaderboard (Nanonets) | HF the `nanonets/idp-leaderboard-results` dataset's index file (23 models incl. Opus 4.6, GPT-5.4, Gemini 3.1 Pro) | **UNCLEAR** (no dataset licence; ask Nanonets) | 2026-03-24 | S if cleared |
| OCR | olmOCR-Bench / CC-OCR / OCRBench v2 / OCR Arena | README tables or HTML | PERMITTED / PERMITTED / UNCLEAR / none | OCR pipelines, stale or HTML-only | low value |
| **long context** | RULER (Apache-2.0, README table, stale: Qwen3 era), **NoLiMa (FORBIDDEN: Adobe non-commercial)**, LongBench v2 (HTML, no licence), HELMET (sheet, stale), OpenAI MRCR (no results file), Context Arena (undocumented API, no terms), Fiction.LiveBench upstream (HTML only; the Epoch copy is stale and `_external`) | — | — | **no source is fresh, machine-readable and licensed.** This is the weakest link for "long legal documents" | — |
| **multilingual** | Arena language slices (§1.3) | — | PERMITTED | fresh | S |
| multilingual | EuroEval | `https://raw.githubusercontent.com/EuroEval/leaderboards/main/leaderboards/<lang>_all.csv` (≈38 languages; european_all 129 models) | PERMITTED (MIT), **but the repo was archived 2026-04-20**; live data sits in an unlicensed HF bucket | stale since 2026-04 | S |
| Turkish | Cetvel (KUIS-AI) | Space files `results/zero-shot/<model>.json` (33) | PERMITTED (MIT) | open models only, 2026-01 | S, but little value |
| Turkish | TR-MMLU leaderboard (alibayram) | HF dataset, 66 rows | **FORBIDDEN (CC-BY-NC-4.0)** | — | — |
| translation | WMT25 | raw jsonl | UNCLEAR (no licence) | one-off 2025 | L |
| legal | LegalBench | no results board outside Vals and HELM Lite | — | — | — |
| finance | FinanceBench | — | **FORBIDDEN (CC-BY-NC)**, and stale | — | — |
| **refusals / permissiveness** | **SpeechMap** ([xlr8harder/speechmap-data](https://github.com/xlr8harder/speechmap-data)) | per-model compliance jsonl (622 files); compute the rates | **PERMITTED (Apache-2.0)** | pushed 2026-09-17, includes 2026 frontier models | M |
| safety | HELM Safety / AIR-Bench | GCS JSON | UNCLEAR | 2025-11 | M |
| **math** | MathArena | HF `MathArena/*_outputs` | **FORBIDDEN (CC-BY-NC-SA-4.0)** | fresh | — |
| abstract reasoning | ARC Prize direct | undocumented `https://arcprize.org/media/data/models.json` (284 models) | **FORBIDDEN** (§1.2) | fresh | — |
| coding | LiveCodeBench | `https://livecodebench.github.io/performances_generation.json` | UNCLEAR (no licence) | stale (mid-2025) | — |
| coding | SWE-bench Pro, SWE-rebench | no results file | — | — | — |
| coding | Aider (already read) | `polyglot_leaderboard.yml` | PERMITTED (Apache-2.0) | **stale: last entry 2025-10-03** | — |

## 4. Other sources: multimodal, pricing, speed, and metadata

| need | source | access (tested) | licence | freshness | effort |
|---|---|---|---|---|---|
| **image and video generation and editing** | **LMArena** `text_to_image` (78 models), `image_edit` (55), `text_to_video` (48), `image_to_video` (48), `video_edit` (10) | same datasets-server and parquet as today | **PERMITTED (CC-BY-4.0)** | 2026-08-27 … 2026-09-14 | S to ingest. **Ranking needs per-unit pricing (next row)** |
| **non-token pricing** | **LiteLLM** (already read) | same JSON: `image_generation` 398 entries (377 priced), `image_edit` 31, `video_generation` 42, `audio_speech` 35, `audio_transcription` 90. Fields: `output_cost_per_image` (320), `output_cost_per_second` (124, plus 720p/1080p/4k variants), `input_cost_per_character` (35) | **PERMITTED (MIT)** | pushed 2026-09-23 | M (normalising units; D-105 still forbids mixing them with $/M-token) |
| non-token pricing | OpenRouter `?output_modalities=all` (613 models: image 44, video 29, speech 18, transcription 22) | image priced per token; video shows 0 | UNCLEAR | — | — |
| non-token pricing | fal.ai / Replicate | key required | **FORBIDDEN** (terms ban compiling a database or scraping) | — | — |
| agents (multi-metric) | LMArena `agent` + 5 `agent_*` configs (46 models) | same dataset | PERMITTED | 2026-09-15 | S (a `score` column, not `rating`; see m15 survey) |
| **speech-to-text** | **HF Open ASR Leaderboard** | `https://huggingface.co/datasets/hf-audio/open-asr-leaderboard-results/resolve/main/english_short_latest.csv` (67 models incl. ElevenLabs, AssemblyAI, Parakeet, Whisper; WER, RTFx, licence, size) plus multilingual and long-form CSVs | **UNCLEAR** (no licence on the results datasets; code Apache-2.0). Ask HF | weekly (2026-09-22) | S |
| **text-to-speech** | **TTS Arena V2** | `tts-agi-tts-arena-v2.hf.space/api/leaderboard?type=tts` (41 rows, Elo, CI, open flag) | **UNCLEAR** (Apache-2.0 code, undocumented route, no data licence) | live (Space 2026-09-05) | S if cleared |
| image, video, speech (Artificial Analysis arenas) | — | — | **FORBIDDEN** | — | — |
| image, video (mirror) | oolong-tea-2026/arena-ai-leaderboards | daily | MIT on the repo, but it **scrapes arena.ai HTML through a proxy with an LLM**; the MIT licence cannot relicense Arena's data. **Replace it with the official CC-BY dataset** (this reverses the 2026-08-19 survey's §1) | — | — |
| GenAI-Arena | — | Space build error, dead since 2025 | — | — | — |
| **latency / throughput** | OpenRouter endpoints (nulls unauthenticated); AA (FORBIDDEN); LLMPerf (archived 2024); Unify (404); optimum llm-perf (2024-12) | — | — | **no clean, live source.** Partial substitutes inside licensed boards: BFCL `Latency`, ProofBench `Latency (seconds)` (Epoch external) | — |
| **open weights, licence, size** | **Epoch `model_metadata.csv`** (in the bundle, 1,075 models) and **`https://epoch.ai/data/all_ai_models.csv`** (3,620 rows, 2026-09-21; accessibility and parameters) | CSV | **PERMITTED (CC-BY)**, Epoch's own data | weekly | S |
| open weights, licence, size | HF Hub API `https://huggingface.co/api/models/{id}` | JSON (licence tag, `safetensors.total` parameters, downloads, gated) | UNCLEAR, low risk (factual repo metadata) | live | S per model |
| **context window, modalities, tool support** | **models.dev** `https://models.dev/api.json` | 223 providers, 8,080 entries: context/output limits, input/output modalities, `tool_call`, `structured_output`, `reasoning`, `open_weights`, knowledge cutoff, cost | **PERMITTED (MIT)** (repo moved to anomalyco/models.dev) | 2026-09-22 | S |
| same | LiteLLM (already read) | `max_input_tokens` (3,418), `supports_vision`, `supports_function_calling`, `supports_pdf_input`, `supports_computer_use`, `supports_web_search` … | PERMITTED | daily | S |
| **computer use** | OSWorld-Verified | raw `osworld_verified_results.xlsx` (1,077 rows) | UNCLEAR (no licence on the site repo) | 2026-08-07 | M |
| computer use | Online-Mind2Web | Space CSV (13 rows, 2026-08-04) | PERMITTED (Apache-2.0) | small | S |
| computer use | Terminal-Bench 2 raw | HF `harborframework/terminal-bench-2-leaderboard` | PERMITTED (Apache-2.0) | **frozen 2026-05-14** | L |
| games | Kaggle Game Arena | none documented | UNVERIFIED | — | — |

---

## 5. A capability taxonomy for routing questions to boards

**What it is for.** The Foundation Models framework on the device already maps a question to one
of the surface ids under a generation schema (`question-coverage-2026-09-18.md` §3). To
*combine* boards, the schema can emit a small structure instead of a single id. The **engine**
turns that structure into boards, weights and filters. The model still chooses only *which
measurements apply*, never *which model is good*, so the D-104 / D-126 boundary holds. Every
field is an enum, so a schema-constrained generator can fill it:

```
Intent {
  task:        TASK id                      (exactly 1)
  modifiers:   [MODIFIER id]                (0..3)
  domain:      legal | medical | finance | science | software | education | creative | personal | none
  language:    en | tr | de | fr | es | ja | ko | zh | ru | pl | other | none
  input_scale: short | long_document | many_documents | codebase | none
  constraints: { max_usd_per_m?, max_cost_per_task?, open_weights?, commercial_use_ok?, min_context_tokens?, needs_tools?, needs_vision? }
}
```

**How the engine combines boards.** It never averages raw scores (D-105).

1. **Filter, then order.** Keep models that clear the top-third floor (D-148) on every *primary*
   board and on as many *secondary* boards as they appear on. Apply constraint filters from
   metadata. Order the survivors by price, or by cost per task where a board publishes it. This
   is the current engine shape widened to N boards.
2. **Rank aggregation, when a single ordering is wanted.** Take each board's percentile rank
   within its own population, weight it (primary > secondary; Epoch's `edi_scores.csv` difficulty
   can break ties), and compute only over models present on at least k of the chosen boards.
   Disclose k and the missing boards per model.

### 5.1 TASK → primary boards (✅ = licence-clean and on hand or S effort; ⚠ = needs a licence decision; ✗ = no clean source)

| TASK id | example phrasings | primary boards | secondary boards |
|---|---|---|---|
| chat_general | "best assistant", "everyday questions" | ✅ Arena text `overall`, ✅ Epoch ECI | ⚠ SimpleBench |
| writing_creative | "story, poem, ad copy" | ✅ Arena `creative_writing` | ✅ EQ-Bench Creative Writing v3 (confirm MIT), ⚠ lechmazur/writing |
| writing_professional | "email, report, cover letter" | ✅ Arena `industry_writing_and_literature_and_language`, ✅ Arena document | ⚠ GDP.pdf, ⚠ GDPval |
| summarise_or_analyse_document | "summarise or compare this contract/PDF" | ✅ Arena document | ⚠ GDP.pdf, ✅ Vectara HHEM, ⚠ CL-bench |
| factual_qa | "accurate answers, doesn't make things up" | ✅ Arena `text_factuality`, ✅ Epoch SimpleQA Verified | ✅ Vectara HHEM, ⚠ HLE |
| web_research | "research the market for …" | ✅ Arena search, ✅ Arena search_factuality | ⚠ DeepResearch Bench |
| expert_reasoning | "chemistry/physics question" | ✅ GPQA Diamond, ✅ Arena `expert` | ⚠ HLE, ⚠ CritPt (possibly AA-sourced) |
| math | "solve, prove" | ✅ mock AIME, ✅ FrontierMath T1-3 v2, ✅ Arena `math` | ⚠ ProofBench (vals.ai upstream) |
| coding_edit | "fix this bug, write a function" | ✅ Epoch SWE-bench Verified (replace the NC site feed), ✅ Arena `coding` | Aider (stale) |
| coding_agent | "build this in my repo or IDE" | ⚠ DeepSWE, ⚠ CursorBench, ⚠ FrontierCode | TerminalBench (frozen) |
| web_dev | "build me a website" | ✅ Arena `webdev` first-hand (+ `webdev-react`, `webdev-html`, `image_to_webdev`) | — |
| data_analysis | "analyse my spreadsheet / SQL" | ⚠ LiveBench data-analysis (documented path needed) | ⚠ WeirdML |
| computer_use | "operate my computer or browser" | ⚠ OSWorld 2.0 (Epoch ext.), ⚠ OSWorld-Verified | ✅ Online-Mind2Web (13 rows) |
| tool_use_agent | "call my APIs, support bot" | ✅ τ²-bench, ✅ BFCL (stale) | ✅ Arena `agent`, `agent_tool_hallucination` |
| professional_agent | "do analyst, consultant or lawyer work" | ⚠ APEX-Agents, ⚠ GDP.pdf | ⚠ RLI, ⚠ GDPval |
| long_autonomy | "work unattended for hours" | ⚠ METR time horizons, ✅ MirrorCode (8 models) | ⚠ Vending-Bench 2 |
| vision_understanding | "read this screenshot or chart" | ✅ Arena vision (+ `ocr`, `diagram`, `homework`) | OmniDocBench |
| video_understanding | "summarise this video" | ⚠ Video-MME (stale) | — |
| image_generation / image_edit | "make an image, fix my photo" | ✅ Arena `text_to_image`, `image_edit` (needs LiteLLM per-image pricing) | — |
| video_generation | "make a video" | ✅ Arena `text_to_video`, `image_to_video`, `video_edit` | — |
| speech_to_text / text_to_speech | "transcribe, voice-over" | ⚠ Open ASR Leaderboard, ⚠ TTS Arena V2 | — |
| translation / non-English | "answer in German", "translate" | ✅ Arena language slices (10 languages + `non_english`) | EuroEval (archived) |
| embeddings | "embedding model for search" | ✅ MTEB (a different model category) | — |
| medical | "health question" | ✅ Arena `industry_medicine_and_healthcare`, ✅ HealthBench Professional | ClinicalBenchmarks (filter by source) |
| forecasting | "predict" | ⚠ ForecastBench | — |
| puzzles_games | "riddles, chess" | ✅ Chess Puzzles, ✅ Mystery Game Puzzles | ⚠ ARC-AGI-2 (FORBIDDEN upstream), ⚠ EnigmaEval |
| refusal_tolerance | "won't refuse my request" | ✅ SpeechMap | — |
| security | "pentest, CTF" | ⚠ Cybench, ExploitBench: **needs a product-policy ruling** (dual use) | — |

### 5.2 MODIFIER → secondary boards

| MODIFIER | adds | example |
|---|---|---|
| domain_legal | ✅ Arena `industry_legal_and_government` (375 models) | "legal", "contract", "compliance" |
| domain_finance | ✅ Arena `industry_business_and_management_and_financial_operations` | "tax table", "budget" |
| domain_medical | ✅ Arena `industry_medicine_and_healthcare`, ✅ HealthBench Professional | — |
| long_context | ✗ **no clean, fresh board**. Constraint fallback: `min_context_tokens` from models.dev or LiteLLM; Arena `longer_query` is a weak proxy | "300-page contract" |
| grounded_no_hallucination | ✅ SimpleQA Verified, ✅ Arena factuality, ✅ Vectara HHEM | "must not invent case law" |
| instruction_following | ✅ Arena `instruction_following` | "exactly this format" |
| multi_turn | ✅ Arena `multi_turn` | "long conversation" |
| hard | ✅ Arena `hard_prompts` | "complex request" |
| uses_my_rules | ⚠ CL-bench | "apply our handbook" |
| cheap_per_task | cost-per-task columns (ARC, CursorBench, DeepSWE, ProofBench, τ²) | "cheapest that can do it" |
| fast | ✗ no clean latency source (BFCL latency is partial) | "real-time" |
| open_weights / self_host / commercial_use_ok | ✅ Epoch accessibility, ✅ models.dev `open_weights`, HF Hub licence | "run it locally" |

The `language` field selects the Arena language slice. Turkish (`tr`) has **no slice**. The
honest fallback is `non_english`, and the card should say so.

### 5.3 The owner's example, routed

"best model for legal document summarisation under $X" becomes
`task=summarise_or_analyse_document, domain=legal, input_scale=long_document, modifiers=[domain_legal, grounded_no_hallucination, long_context], constraints.max_usd_per_m=X`

| role | today | after the top-10 below |
|---|---|---|
| primary | Arena document | Arena document + **Arena `industry_legal_and_government`** |
| secondary | Arena factuality | + **SimpleQA Verified**, **Vectara HHEM** (summarisation hallucination); GDP.pdf and CL-bench only once their licences are cleared |
| long context | — | ✗ constraint only: `min_context_tokens` ≥ document size (models.dev) |
| filter | price ≤ X | price ≤ X, plus `commercial_use_ok` |

What the card should say: *"No leaderboard measures legal summarisation directly. These models are
top-third with human raters on legal and government prompts AND on document tasks, AND among the
lowest hallucination rates when summarising, AND they fit your document. Ordered by price."*
Each constituent board stays visible with its own date.

---

## 6. Ranked recommendation: the top 10 additions

Scored as **(question coverage × freshness × licence clarity) ÷ effort**, each factor on 1–3
(effort S=1, M=2, L=3). The ranking is a judgment built on the measurements above, not a formula
applied blindly; ties are ordered by how many user questions the addition touches.

**Priority 0: fixes, not additions.** (a) Replace the SWE-bench site feed (CC BY-NC) with Epoch's
own `swe_bench_verified.csv`. (b) Rule on `arc_agi_external.csv` (ARC Prize terms) and, more
broadly, on Epoch `_external` licensing. (c) Adapt to the new ECI layout before the next bundle
refresh (§1.1).

| # | addition | cov | fresh | legal | effort | score | what it unlocks |
|---|---|---|---|---|---|---|---|
| 1 | **Arena category slices**: `text` 29, `vision` 11, `webdev` 5, from the file already fetched | 3 | 3 | 3 | S | 27 | legal, medical, finance, creative writing, instruction following, multi-turn, hard prompts, coding, math, expert, 10 languages, OCR, diagrams. **About 40 new lists** |
| 2 | **Epoch-run CC-BY boards**: SimpleQA Verified, FrontierMath T1-3 v2 (+T4 v2), Chess Puzzles, Mystery Game Puzzles, SWE-bench Verified (Epoch), plus `model_metadata.csv` accessibility | 2 | 3 | 3 | S | 18 | hallucination, research math, puzzles; **open-weights and commercial-use filter** |
| 3 | **Vectara HHEM** (Apache-2.0, 2026-09-22) | 2 | 3 | 3 | S | 18 | "doesn't make things up when summarising". A direct part of the legal example |
| 4 | **models.dev** (MIT) + Epoch `all_ai_models.csv` (CC-BY) as metadata | 2 | 3 | 3 | S | 18 (a filter, not a board) | `min_context_tokens`, `needs_tools`, `needs_vision`, `open_weights` constraints; the only honest handle on long context today |
| 5 | **LiteLLM non-token pricing** (source already read) + **Arena `text_to_image`, `image_edit`, `text_to_video`, `image_to_video`, `video_edit`** | 3 | 3 | 3 | M | 13.5 | the owner's "improve my profile photo" example, plus video. Turns five zero-rank boards into ranked ones |
| 6 | **HealthBench Professional / ClinicalBenchmarks** (CC BY 4.0 JSON) | 2 | 3 | 2 | S | 12 | medical questions (with Arena's medicine slice) |
| 7 | **τ²-bench** (MIT) + **BFCL** (Apache-2.0) | 2 | 2 | 3 | S–M | 8–12 | tool use, customer-service agents, API-calling bots |
| 8 | **EQ-Bench Creative Writing v3 / EQ-Bench 3** (MIT declared; confirm by email) | 2 | 3 | 2 | S–M | 8–12 | a second board for creative writing and emotional intelligence |
| 9 | **Arena `agent` + `agent_*` configs** (CC-BY) | 2 | 3 | 3 | M (score, not rating) | 9 | "agent that doesn't hallucinate tools", steerability, recovery |
| 10 | **Epoch `_external` boards with a checkable upstream, once #0(b) is ruled**: GDP.pdf, APEX-Agents, OSWorld 2.0, CursorBench, HLE, CL-bench, SimpleBench | 3 | 3 | 1 (UNCLEAR until each upstream is checked) | S | 9 | professional PDFs (legal/finance), professional agents, GUI computer use, IDE coding. **The highest coverage in the bundle, gated by licence** |

**Next after the top 10:** MTEB (CC0; a new product category, M–L), SpeechMap (Apache-2.0, M),
OpenRouter Data API usage share (CC BY 4.0; needs the project's first secret), OmniDocBench (M),
Online-Mind2Web (S, small).

**Worth an email, because each unlocks a whole surface nobody else can supply legally:**

| contact | surface it unlocks |
|---|---|
| Vals.ai | legal, tax, finance, medical coding |
| HF Open ASR team | speech-to-text |
| TTS Arena | text-to-speech |
| LiveBench | a documented CSV path (data analysis, instruction following) |
| lechmazur | writing, confabulations |
| Nanonets IDP | document extraction |
| Surge AI | GDP.pdf results licence |
| Mercor | APEX-Agents |

**Not recommended at any effort:** Artificial Analysis, Scale SEAL, Vellum, MathArena, NoLiMa,
TR-MMLU, FinanceBench, fal.ai and Replicate pricing, and the oolong-tea Arena mirror.

## 7. Risks

**Licensing**

- **Aggregators do not launder licences.** This applies to Epoch `_external` files, the OpenRouter
  `/benchmarks` endpoint (it re-serves AA) and ClinicalBenchmarks (it contains AA and Vals rows).
  Each row's *upstream* terms govern. **AA-derived numbers are the sharpest case**: AA §2.5
  forbids ranking and selection products even with a paid licence unless AA consents in writing.
  `scicode_external.csv` is 100% AA-sourced.
- **A licence on a code repository is not always a data licence.** Several PERMITTED flags above
  rest on a repo-wide LICENSE covering results files (BFCL, Vectara, OmniDocBench, τ²-bench). That
  is the normal reading, and it is still weaker than an explicit data licence. EQ-Bench's rests on
  README front matter alone.
- **No licence means all rights reserved.** lechmazur's repos, LongBench v2, IDP, Open ASR results
  and the OSWorld site all fall here.
- **Undocumented endpoints** (LiveBench site CSVs, TTS Arena API, Context Arena, ARC JSON) conflict
  with the project's "documented raw-data endpoints only" rule even where the licence is fine.
- **Terms change.** AA revised its terms on 2026-08-19 and 2026-09-15. Record `last_verified` per
  source (as `data/epoch-source.yaml` already does) and re-check the terms on the same clock as
  staleness.

**Mixing scales**

- The boards publish Elo (Arena, relative to the population and moving), fractions, percentages,
  dollars (Vending-Bench, −31 … 15,515), AtCoder-like ratings (ALE-Bench), and Brier-type scores
  whose **direction is not stated** (BTF-3). Combine them only through ranks or floors within each
  board (D-105).
- **Populations differ.** A model absent from a board is *untested*, not *bad*. Rank aggregation
  over sparse overlap is where a derived number becomes unfalsifiable. The leave-one-out result
  that killed the derived layer (DeepSWE −0.104) is the bar every combination must clear.
- **Rows are configurations.** Many Epoch boards list one model several times, at reasoning
  effort, harness or agent level (e.g. `_xhigh`, "(Non-reasoning)", agent scaffolds on
  TerminalBench and OSWorld). Price must attach to the same configuration that was scored.
- **Arena slices are thinner than `overall`.** Their confidence intervals are wider, so use
  `rating_lower` and `rating_upper` per slice. `*_style_control` variants are a second answer to
  one question (M15 survey), so pick one.
- **Vendor-reported and independent numbers mix.** This happens in ClinicalBenchmarks, in Epoch
  rows sourced from system cards, and on Vellum. Keep provenance per row and consider down-ranking
  self-reported numbers.

**Stale and frozen boards**

- **Frozen**: Terminal-Bench 2 (submissions closed 2026-05-14; it is the `computer-use` primary,
  and it is a *terminal* board, not a GUI board), OpenAI simple-evals (July 2025), Open LLM
  Leaderboard (March 2025), EuroEval GitHub (April 2026).
- **Stale**: BFCL (2025-12), Aider (2025-10), HELM (2025-11 / 2026-01), Epoch's copies of LiveBench
  (2025-11), Fiction.LiveBench (1 model from 2026), Lech Mazur writing (2025-08), Video-MME
  (2025-06), and every long-context board.
- **Saturated**: MMLU, MATH L5, GSM8K and ARC-AGI v1 (top 0.985). A top-third floor on a saturated
  board admits nearly everyone.
- **Schema drift**: §1.1 is a live example. A partial or renamed file must fail the build
  (REQ-ING-013), not silently shrink a surface.

**Routing**

- The on-device model can output a structurally valid but *wrong* combination, for example
  `domain=legal` for a tax question. The card must list the boards used, so a reader can see what
  was measured. Log decline and low-confidence intents to the on-device demand register (D-142 §3).
- **Coverage honesty.** For long context, latency and Turkish, the right output is a named gap,
  not a proxy that is presented as a measurement.

---

## Appendix: reproduction and provenance

- Epoch inventory: a counting script over a local unpack of the bundle fetched 2026-09-23, compared with the owner-fetched bundle of 2026-08-15.
- Arena categories: `https://datasets-server.huggingface.co/statistics?dataset=lmarena-ai/leaderboard-dataset&config={text,vision,webdev,document}&split=latest` (2026-09-23).
- Spot-checked directly: SWE-bench site `LICENSE` (CC BY-NC 4.0); `https://arcprize.org/terms`; Epoch hub external-data sentence; `https://healthbenchprofessional.com/data/leaderboard.json` (licence field, 2026-09-08); τ²-bench "manifest.json"; BFCL "data_overall.csv" (200); Vectara README "Last updated on September 22, 2026".
- Everything else in §3–§4 was tested on 2026-09-23 by three research lanes using curl, the GitHub API, the HF API and datasets-server. Items they could not confirm are marked UNVERIFIED inline.
- Repo context read: `README.md`, `docs/prd.md` (REQ-ING), `src/app/workflows/sources.py`, `src/app/workflows/categories.py`, `src/app/clients/{arena,swebench}.py`, `docs/decisions.md` (D-142 and the M1 source ADR), `docs/research/{source-survey-2026-08-19,question-coverage-2026-09-18,m15-board-survey-2026-09-21}.md`.
