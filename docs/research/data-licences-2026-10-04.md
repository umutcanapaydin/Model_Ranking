---
record_type: license-review
id: data-licences-2026-10-04
status: draft
process_version: v6.6
date: 2026-10-04
---
# Data licences for a first release beyond the owner's Mac (#88, W-129)

> **This is a risk flag, not legal advice.** It states what each publisher's terms say, read
> literally, and what each option costs the product. The owner rules. Their ruling becomes an ADR
> before any deploy (Stage 5).

**How this was built.** The source list comes from the code: `rank.py` (`SOURCE_ATTRIBUTION`,
`ATTRIBUTIONS`), `sources.py`, `board_tables.py`, `categories.py`, `access.py`, the clients and
`data/`. It was cross-checked against the served artifact with read-only queries
(`sqlite3 'file:advisor.db?mode=ro'`, artifact observed 2026-09-30). Every web claim was read on
**2026-10-04** at the URL given.

**What the artifact serves, and where.**

- `/v1/recommendations`: one surface's picks, each with its **score**, secondary score and blended
  price. Its `sources` list carries the attribution strings.
- `/v1/boards`: every board's **positions** (no scores), each board's `attribution`, a top-level
  `attributions` list (pricing included), and each model's blended price and `accessibility`.
- The app shows `board.attribution` only on the combined-list detail screen
  (`ios/ModelRanking/ContentView.swift:1452`). I found no app code that shows an answer's `sources`.
- The subscription plans (`plans`, `plan_models` tables) are in the artifact but are on no `/v1`
  route and not in the app. Only the CLI (`recommend --subscription`) reads them.
- Not served: `data/m5-swebench-baseline.json` (a measurement script reads it) and
  `data/epoch-source.yaml` (acquisition metadata).

**Surface → source** (`categories.py`; "models" = models with a price and a score on that board):

| surface | primary source | models | secondary |
|---|---|---|---|
| `coding` | `swebench` + `epoch_swe_bench_verified` (same benchmark, best row wins) | 54 (38 have a `swebench` row, 32 an Epoch row, 22 only `swebench`) | `aider` (32) |
| `assistant` | `arena` | 189 | — |
| `agentic-coding` | `epoch_deepswe_external` | 18 at `high` (25 on the board) | — |
| `everyday` | `epoch_eci` | 149 | `epoch_mmlu` (52), display only |
| `expert` | `epoch_gpqa` | 150 | — |
| `mathematics` | `epoch_aime` | 140 | — |
| `computer-use` | `epoch_terminalbench` | 42 | — |
| `abstract` | `epoch_arc_agi` | 71 | — |
| `web-dev` | `epoch_webdev` | 91 | — |
| `document` / `factuality` / `vision` / `search` / `search_factuality` | `arena_document` / `arena_factuality` / `arena_vision` / `arena_search` / `arena_search_factuality` | 34 / 108 / 88 / 28 / 27 | — |

The app's refinements (`ios/ModelRanking/Engine/Refinements.swift`) add 16 Arena text slices
(8 languages, 8 domains) to `assistant`, `everyday`, `document`, `factuality`, `expert`, and in one
case each `web-dev` and `mathematics`. The other 19 Arena slices, the 6 Agent Arena boards and 5
Epoch-run boards (SimpleQA, FrontierMath 1-3 and 4, chess, mystery) are published on `/v1/boards`
but no surface or refinement reads them yet.

---

## A. The table

"Permits" means a written grant covers the use. "Does not" means the terms refuse it, or grant
only a narrower use. "Unclear" means no terms were found, or the terms do not clearly reach this use.
(a) = the owner's private use on their own devices. (b) = a free public app. (c) = a paid app.

| # | source id(s) | upstream | feeds | licence or terms (URL) | (a) | (b) | (c) | attribution required → ours meets it? | checked |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 47 ids: `arena`, `arena_document`, `arena_factuality`, `arena_vision`, `arena_search`, `arena_search_factuality`, 26 `arena_text_*`, 9 `arena_vision_*`, 6 `arena_agent*` | LMArena, `lmarena-ai/leaderboard-dataset` on Hugging Face | 6 surfaces, 16 refinements, 47 boards | **CC-BY-4.0**, dataset card [huggingface.co/datasets/lmarena-ai/leaderboard-dataset](https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset). See note 1 on Arena's site terms | permits | permits | permits | CC BY §3(a). **Partly** (note 1) | 2026-10-04 |
| 2 | `epoch_eci`, `epoch_gpqa`, `epoch_aime`, `epoch_swe_bench_verified`, `epoch_simpleqa`, `epoch_frontiermath`, `epoch_frontiermath_t4`, `epoch_chess`, `epoch_mystery`; `epoch_access` (`model_metadata.csv` → `accessibility`) | Epoch AI, boards Epoch ran itself | `everyday`, `expert`, `mathematics`, half of `coding`; 5 boards; the accessibility filter | **CC BY 4.0**: "free to use, distribute, and reproduce provided the source and authors are credited". [epoch.ai/data/ai-benchmarking-dashboard](https://epoch.ai/data/ai-benchmarking-dashboard), [epoch.ai/benchmarks/use-this-data](https://epoch.ai/benchmarks/use-this-data), bundle `README.md` | permits | permits | permits | Epoch's citation + CC BY §3(a). **Partly** (note 2) | 2026-10-04 |
| 3 | `epoch_arc_agi` | ARC Prize (Epoch `arc_agi_external.csv`; its `Source` column cites arcprize.org/leaderboard) | `abstract` (sole evidence) | **ARC Prize Terms**, last updated 2024-06-03, [arcprize.org/terms](https://arcprize.org/terms) (note 3) | permits (personal, non-commercial use is granted) | **does not** | **does not** | Only if permission is granted: "identify us as the owners or licensors". **No**: ours credits Epoch only | 2026-10-04 |
| 4 | `epoch_deepswe_external` | Datacurve, DeepSWE (Epoch `deepswe_external.csv`, `Source` = deepswe.datacurve.ai) | `agentic-coding` (sole evidence) | **Not found** for the scores (note 4) | unclear | unclear | unclear | None found. Epoch asks users to "credit the original sources". **No**: ours credits Epoch only | 2026-10-04 |
| 5 | `epoch_terminalbench` | Terminal-Bench 2.0 (Epoch `terminalbench_external.csv`, `Source` = tbench.ai leaderboard) | `computer-use` (sole evidence) | Leaderboard page: **none stated**. Raw submissions: **Apache-2.0** (note 5) | unclear | unclear | unclear | None on the page. **No**: ours credits Epoch only | 2026-10-04 |
| 6 | `epoch_webdev` | LMArena WebDev, copied by Epoch from arena.ai (`Source` = arena.ai/leaderboard) | `web-dev` (sole evidence) | Epoch's copy cites Arena's **website**, which is under Arena's Terms of Use (note 1). The same board is in the CC-BY dataset (`webdev` config) | unclear | unclear | unclear | **No**: ours credits Epoch only | 2026-10-04 |
| 7 | `epoch_mmlu` | Stanford CRFM HELM Lite (80 rows) + 25 model technical reports (Epoch `mmlu_external.csv`) | `everyday` secondary (display only, never ordering) | **Not found** for HELM results (note 6). Papers not checked one by one | unclear | unclear | unclear | **No**: ours credits Epoch only | 2026-10-04 |
| 8 | `swebench` | SWE-bench site repo, `data/leaderboards.json` | `coding` (shared with row 2) | **CC BY-NC 4.0**, [LICENSE](https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/master/LICENSE) (note 7) | permits | unclear (depends on "NonCommercial") | **does not** | CC BY-NC §3(a). **No** (note 7) | 2026-10-04 |
| 9 | `aider` | Aider repo, `polyglot_leaderboard.yml` | `coding` secondary | **Apache-2.0**, [LICENSE.txt](https://github.com/Aider-AI/aider/blob/main/LICENSE.txt) (GitHub API: `Apache-2.0`). No NOTICE file at the repo root | permits | permits | permits | Apache-2.0 §4 (copy of the licence, keep notices). **Partly**: ours names it and its licence; no licence copy | 2026-10-04 |
| 10 | `litellm` (pricing) | BerriAI/litellm, `model_prices_and_context_window.json` | the price of all 313 priced models | **MIT** for everything outside `enterprise/`, [LICENSE](https://raw.githubusercontent.com/BerriAI/litellm/main/LICENSE). The JSON is at the repo root | permits | permits | permits | MIT: include the copyright and permission notice "in all copies or substantial portions". **Partly**: ours names it and MIT; no notice text. We serve medians, not the file | 2026-10-04 |
| 11 | `openrouter` (pricing) | OpenRouter `GET /api/v1/models` (public, no key; HTTP 200 today) | a second price in the median for 168 of 313 models | **ToS**, last updated 2026-08-31, [openrouter.ai/terms](https://openrouter.ai/terms). No licence for `/models` (note 8) | unclear | unclear | unclear | None found for `/models`. Ours says "(attribution required)", which I could not find in the terms | 2026-10-04 |
| 12 | `plans` rows for OpenAI, Anthropic, Google (8 plans, 22 plan-page model links) | chatgpt.com/pricing, claude.com/pricing, one.google.com, hand-transcribed (`data/plans.yaml`) | CLI subscription answer only | Vendor site terms (note 9) | unclear | unclear | unclear | None found. Each row keeps its `source_url` in the artifact; not served | 2026-10-04 |
| 13 | `plans` rows for Perplexity (2 plans) + `rosters.yaml` (18 roster links) | perplexity.ai and its help centre, hand-transcribed | CLI subscription answer only | **Perplexity ToS**, last updated 2026-01-23, [perplexity.ai/hub/legal/terms-of-service](https://www.perplexity.ai/hub/legal/terms-of-service) (note 9) | unclear | **does not** (literal §5.2(a)) | **does not** (§5.2(a), (e)) | None found | 2026-10-04 |

**Counts (13 sources).** (a) private: 6 permit, 0 do not, 7 unclear. (b) free app: 4 permit, 2 do
not, 7 unclear. (c) paid app: 4 permit, 3 do not, 6 unclear. The four that permit all three uses:
LMArena's dataset, Epoch's own boards, Aider and LiteLLM.

### Notes

1. **LMArena.** The card's front matter says `license: cc-by-4.0`. The card states no attribution
   wording of its own. CC BY 4.0 §3(a)(1) asks for: the creator, a copyright notice, a notice
   referring to the licence, a notice referring to the warranty disclaimer, a link to the material
   where practicable, a statement of any modification, and the licence text or link. §3(a)(2) lets
   this be done "in any reasonable manner based on the medium", for example a link to a page that
   holds it ([legal code](https://creativecommons.org/licenses/by/4.0/legalcode.txt)).
   Ours is `Arena leaderboard data © LMArena — lmarena-ai/leaderboard-dataset (CC-BY-4.0)`. It has
   the creator, a © line, the dataset name and the licence name. It has no link to the dataset, no
   link to the licence, and no warranty notice. The combined-list screen says the list is the
   product's own combination (D-160 clause 3), which is a modification statement there only.
   **Arena's site terms** ([help.arena.ai/articles/5629909088-terms-of-use](https://help.arena.ai/articles/5629909088-terms-of-use),
   last updated 2026-02-23): §1 limits use of the Service to "personal or internal business use".
   §5(i) bars anyone to "license, sell, rent, lease, transfer, assign, reproduce, mirror,
   distribute, host, otherwise commercially exploit … the Service, the Output". The terms do not
   mention the Hugging Face dataset, open licences or Creative Commons. The product reads the
   dataset, not the site.
2. **Epoch (own boards).** Today's bundle `README.md` gives the citation as
   "Epoch AI, ‘Capabilities & benchmarking’. Published online at epoch.ai. Retrieved from
   ‘https://epoch.ai/benchmarks’ [online resource]." The web page gives the same title, retrieved
   from `https://epoch.ai/benchmarks/use-this-data`, plus an access date. Ours
   (`board_tables.py:28`, and `README.md` "Data attribution") still says **‘AI Benchmarking Hub’**,
   the title from an older bundle. Ours adds "(CC-BY-4.0)" but no licence link. Epoch-run boards
   carry `Log viewer`/`Logs` columns and no `Source` column, which fits "Epoch ran it". Epoch also
   says "Benchmark questions and answers are the property of their respective creators"; the
   product serves scores, not questions.
3. **ARC Prize.** §2 grants a licence to "access the Services; and download or print a copy of any
   portion of the Content … solely for your personal, non-commercial use or internal business
   purpose." It continues: "Except as set out in this section …, no part of the Services and no
   Content or Marks may be copied, reproduced, aggregated, republished, uploaded, posted, publicly
   displayed, … distributed, sold, licensed, or otherwise exploited for any commercial purpose
   whatsoever, without our express prior written permission." Requests go to
   **team@arcprize.org**. Prohibited activities: "Systematically retrieve data or other content
   from the Services to create or compile, directly or indirectly, a collection, compilation,
   database, or directory without written permission from us." The leaderboard and the testing
   policy pages ([arcprize.org/leaderboard](https://arcprize.org/leaderboard),
   [arcprize.org/policy](https://arcprize.org/policy)) state no data licence. The policy page says
   public testing results are published to Hugging Face. ARC Prize's Hugging Face datasets
   `arcprize/arc_agi_v1_public_eval` (75 model folders) and `arcprize/arc_agi_v2_public_eval` (72) are
   tagged **MIT**, last modified 2026-06-04
   ([v1](https://huggingface.co/datasets/arcprize/arc_agi_v1_public_eval)). They hold public-eval
   results, not the leaderboard's scores.
4. **DeepSWE.** [deepswe.datacurve.ai](https://deepswe.datacurve.ai/) and its
   [/data/v1.1](https://deepswe.datacurve.ai/data/v1.1) page state no licence, terms or citation;
   the footer says "© 2026 Datacurve". The repo
   [github.com/datacurve-ai/deep-swe](https://github.com/datacurve-ai/deep-swe) is Apache-2.0, but
   its `PROVENANCE.md` says that licence "covers only Datacurve AI Inc.'s original contributions
   (task specifications, evaluation harness, verifiers, and curation)". The repo holds tasks, not
   leaderboard results. A Datacurve "Contributor Terms of Service" exists for its Shipd platform; it
   does not concern this data.
5. **Terminal-Bench.** The leaderboard page
   ([tbench.ai/leaderboard/terminal-bench/2.0](https://www.tbench.ai/leaderboard/terminal-bench/2.0))
   states no licence or terms. The raw submissions dataset
   [harborframework/terminal-bench-2-leaderboard](https://huggingface.co/datasets/harborframework/terminal-bench-2-leaderboard)
   is tagged **apache-2.0** and says "SUBMISSIONS CLOSED" (last modified 2026-05-15). The code repo
   `laude-institute/terminal-bench` is Apache-2.0.
6. **MMLU (HELM).** `stanford-crfm/helm` is Apache-2.0 for code; its README asks software users to
   cite the HELM paper. The results site
   ([crfm.stanford.edu/helm/lite/latest](https://crfm.stanford.edu/helm/lite/latest/)) renders by
   script and showed no terms to my reader. 25 other rows' sources are model technical reports.
7. **SWE-bench.** The site repo's `LICENSE` opens "Attribution-NonCommercial 4.0 International".
   GitHub's API reports it as `NOASSERTION`. The upstream `SWE-bench/experiments` repo has no
   licence GitHub can detect. CC BY-NC 4.0 §1(i): "NonCommercial means not primarily intended for
   or directed towards commercial advantage or monetary compensation"
   ([legal code](https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt)). Ours is
   `Coding scores: swebench.com leaderboard (SWE-bench) and Aider polyglot leaderboard (Apache-2.0)`.
   It names swebench.com, but the only licence it names is Aider's. It does not say CC BY-NC and
   has no link.
8. **OpenRouter.** §12: "Materials" includes "compilation, information, data"; "Except as
   expressly authorized by OpenRouter, you may not make use of the Materials." §7 bars using
   automated means "to scrape or copy any information on the Site or the Services" and accessing
   the Service "for purposes of reselling API access to Models or otherwise developing a competing
   service". The models API page has no licence text. OpenRouter's **CC BY 4.0** grant covers only
   its Data API endpoints (`rankings-daily`, `app-rankings`, `benchmarks`, `classifications/task`),
   per [the Data API page](https://openrouter.ai/docs/cookbook/administration/data-api). The code
   comment `clients/openrouter.py:4` says "attribution required per OpenRouter terms"; I found no
   such clause in the ToS.
9. **Vendor pages (plans, rosters).** Prices and model names were typed by hand; `limits` is text
   quoted or condensed from the page. `plans.yaml` records that pages were read through the
   `r.jina.ai` reader on 2026-09-23 because direct fetches got HTTP 403.
   - OpenAI ([terms-of-use](https://openai.com/policies/terms-of-use/), read through r.jina.ai,
     direct fetch 403; "Effective: January 1, 2026"): the terms cover "associated software
     applications and websites"; users may not "Modify, copy, lease, sell or distribute any of our
     Services" or "Automatically or programmatically extract data or Output".
   - Anthropic ([consumer-terms](https://www.anthropic.com/legal/consumer-terms), read through
     r.jina.ai): covers "associated apps, software, and websites"; bars "crawl, scrape, or otherwise
     harvest data or information from our Services other than as permitted under these Terms".
   - Google ([policies.google.com/terms](https://policies.google.com/terms), effective 2026-07-30):
     "You may use Google's content as allowed by these terms … but we retain any intellectual
     property rights"; automated access against robots.txt is barred.
   - Perplexity (read through r.jina.ai): §5.1 permits use "for your personal, non-commercial use
     only". §5.2(a) bars to "download, modify, copy, distribute, transmit, display, perform,
     reproduce, duplicate, publish … any information contained on, or obtained from or through, the
     Services". §5.2(e) bars exploiting the Services "for any commercial purpose". §5.2(i) bars
     automated or "any manual process" to extract data.

---

## B. Sources that do not permit a free or a paid app, with options and costs

Rows 3, 8 and 13 refuse (b) or (c). Rows 4–7 and 11–12 are unclear, so they are listed too.

**One cost applies to every "keep for private use only" option.** Today there is one artifact. Private
only means two artifacts (or one build flag): the owner's, with every source, and a public one
without these. The public one then pays the "drop" or "replace" cost below.

**What "drop" does to a surface.** A surface whose only source is gone answers that it has no
evidence, rather than an empty list (D-121's disclosure, `sources.py`). The board also leaves
`/v1/boards`.

### B1. `swebench` (CC BY-NC 4.0): (b) unclear, (c) does not

| option | cost to the product |
|---|---|
| Drop | `coding` keeps only Epoch's own SWE-bench Verified board. Ranked models fall from 54 to 32. The 22 lost models have only a `swebench` row (for example `minimax-m2.5`). 16 models lose their `swebench` row and keep Epoch's score. The current top 3 already come from Epoch. Board `swebench` leaves `/v1/boards`. |
| Ask the publisher | The SWE-bench team (site repo `swe-bench/swe-bench.github.io`). No contact address established. |
| Private use only | None for the owner. The public build pays the "drop" cost. |
| Replace | **Epoch's `swe_bench_verified.csv` (CC BY 4.0)**, named in the research record. It is already in the artifact as `epoch_swe_bench_verified`: 33 models, 32 priced, newest evaluation 2026-06-25 (the `swebench` rows' newest is 2026-02-26). So "replace" costs the same as "drop", plus moving `coding`'s `primary_source` (used for disclosure). |

### B2. `epoch_arc_agi` (ARC Prize terms): (b) and (c) do not

| option | cost to the product |
|---|---|
| Drop | `abstract` ("Puzzles & pattern finding") has no evidence: 71 models lose it. No refinement uses it. |
| Ask the publisher | ARC Prize, **team@arcprize.org** (the terms name it for any other use). If granted, the terms require naming ARC Prize as owner and showing its notices. |
| Private use only | None for the owner. The public build loses `abstract`. |
| Replace | **No like-for-like clean board found.** Nearest: ARC Prize's own Hugging Face public-eval results (MIT; 75 model folders for v1, 72 for v2; last change 2026-06-04). They use a different task set from the leaderboard and need a new parser. Epoch-run boards already in the artifact (`epoch_mystery` 64 models, `epoch_chess` 113) are CC BY but measure other things. |

### B3. `epoch_deepswe_external` (DeepSWE, no licence found): unclear

| option | cost to the product |
|---|---|
| Drop | `agentic-coding` has no evidence (18 ranked models). A coding question then answers on `coding` alone, not on both surfaces (Ruling A). |
| Ask the publisher | Datacurve (deepswe.datacurve.ai; repo `datacurve-ai/deep-swe`). No contact address established. |
| Private use only | None for the owner. The public build loses `agentic-coding`. |
| Replace | **No clean replacement found.** The other agentic-coding boards in the bundle (CursorBench, FrontierCode, FrontierSWE) are also `_external`. Epoch's own MirrorCode has 8 models. |

### B4. `epoch_terminalbench` (no licence on the leaderboard page): unclear

| option | cost to the product |
|---|---|
| Drop | `computer-use` ("Operating a computer") has no evidence: 42 models. |
| Ask the publisher | The Terminal-Bench team (tbench.ai). No contact address established. |
| Private use only | None for the owner. The public build loses `computer-use`. |
| Replace | **First-hand raw submissions, `harborframework/terminal-bench-2-leaderboard` (Apache-2.0).** Scores must be computed from per-trial results (research record: effort L). The board is frozen either way: submissions closed 2026-05-14. Apache-2.0 asks for a licence copy and kept notices. |

### B5. `epoch_webdev` (Epoch's copy of Arena's website): unclear

| option | cost to the product |
|---|---|
| Drop | `web-dev` has no evidence: 91 models. |
| Ask the publisher | Not needed if replaced. |
| Private use only | None for the owner. The public build loses `web-dev` unless replaced. |
| Replace | **LMArena's own `webdev` config in the same CC-BY dataset** the other 47 Arena boards come from (584 rows in `latest`, categories included). Same grant and same attribution string as row 1. The research record already says "move to that". It needs a new board declaration, and `web-dev`'s window and tie margin were measured on Epoch's copy. |

### B6. `epoch_mmlu` (HELM + papers, no data licence found): unclear

| option | cost to the product |
|---|---|
| Drop | `everyday` loses its secondary score column (52 models). Ordering does not change: secondaries never order. Board leaves `/v1/boards`. |
| Ask the publisher | About 26 publishers (HELM plus 25 report authors). Impractical. |
| Private use only | None for the owner. |
| Replace | No like-for-like clean board. MMLU has no 2026 model (research record), so a secondary could also stay empty. |

### B7. `openrouter` (ToS, no licence for `/models`): unclear

| option | cost to the product |
|---|---|
| Drop | No model loses its price: LiteLLM prices all 313. The blended price of 168 models becomes LiteLLM's alone instead of the median of two sources. |
| Ask the publisher | OpenRouter. |
| Private use only | None for the owner. |
| Replace | Not needed for coverage (LiteLLM, MIT). The research record lists models.dev (MIT) as another metadata and price source. |

### B8. Plans and rosters (vendor terms): Perplexity rows do not permit (b)/(c); the others are unclear

| option | cost to the product |
|---|---|
| Drop from a public build | **Nothing the app or `/v1` shows.** Only the CLI subscription answer uses them. |
| Ask the publisher | OpenAI, Anthropic, Google, Perplexity. |
| Private use only | None today: it already is CLI-only. |
| Replace | None. These are the vendors' own prices. |

---

## C. What the owner must decide

The standing ruling (W-129, 2026-09-23: keep them for now) covers private use. These questions
settle a public release. The answers become the ADR.

1. **Is the first public release free or paid?** If free: will it earn money in any way (ads, in-app
   purchases, a later paid tier)? This settles whether SWE-bench's "NonCommercial" can apply.
2. **SWE-bench for `coding`:** keep it for private use only and serve Epoch's SWE-bench board in
   public builds, or something else? (Epoch's board is already in the artifact. Public `coding` would
   rank 32 models instead of 54.)
3. **ARC-AGI (`abstract`):** in a public build, drop the surface, write to ARC Prize
   (team@arcprize.org), or try ARC Prize's MIT public-eval data (a different task set)?
4. **A board whose terms say nothing:** may it go in a public build? Options: only with written
   permission; only through a first-hand licensed copy; or keep. This one rule settles WebDev
   (a CC-BY copy exists), TerminalBench (an Apache-2.0 copy exists), MMLU (none; display only),
   OpenRouter (LiteLLM covers every price) and the vendor plan pages (CLI only).
5. **DeepSWE (`agentic-coding`):** no licence found and no clean replacement. Write to Datacurve, or
   leave the surface out of public builds?
6. **Attribution in a public build:** where must it appear? Today the app shows it only on the
   combined-list detail screen. The gaps in A (no links, the old Epoch title, no upstream credit for
   Epoch's external boards, SWE-bench's licence not named) are facts for that ruling.

---

## D. What I could not establish

- Whether Arena's site terms (§1, §5(i)) reach the Hugging Face dataset published under CC-BY-4.0.
  The terms do not mention it.
- A licence for DeepSWE's leaderboard scores. Looked at: the home page, `/data/v1.1`, the GitHub
  repo (LICENSE, PROVENANCE.md, README). No contact address found.
- A licence or terms for the tbench.ai leaderboard page. Also whether Epoch's copy came from the
  page or from the Apache-2.0 raw dataset (its `Source` column cites the page).
- A data licence for HELM results. The HELM site would not render terms to my reader. The 25 model
  reports were not checked one by one.
- Whether OpenRouter's public, documented `/models` endpoint counts as "expressly authorized" use
  under §12.
- Whether a free app counts as "NonCommercial" under CC BY-NC. It depends on facts the owner sets.
- Whether the licence conditions (CC BY §3(a), Apache-2.0 §4, the MIT notice) reach what the product
  serves. It serves positions, scores and price medians, not the files.
- Whether Epoch's ECI is free of upstream licences. Epoch builds it from 58 benchmarks, some of them
  `_external`, but does not mark it `_external`.
- Whether vendor site terms reach hand-typed prices and model names. Also: OpenAI's, Anthropic's,
  Perplexity's and the exact ARC Prize wording were read through the `r.jina.ai` reader (OpenAI's
  site returned HTTP 403). Anthropic's effective date was not captured.
- Contact addresses for SWE-bench, Datacurve and Terminal-Bench.
