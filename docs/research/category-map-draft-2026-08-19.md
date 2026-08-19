---
record_type: register
id: category-map-draft-2026-08-19
status: draft
date: 2026-08-19
---
# Category map — draft for the owner to cut

**What this is.** A proposal mapping the evidence we can actually keep fresh onto questions people
actually ask. Not a list of benchmarks: D-126 says a category exists to answer a user's question,
and the supply side is only qualified once it is machine-fetchable and stays fetchable.

**How to read the coverage column.** It is the number of MODELS the source scores. A category with
20 models can be answered; one with 5 is a screen that will often say "nothing fits your budget"
for reasons that have nothing to do with the user. Coverage is the difference between a category
and a disappointment.

**Nothing here is decided.** The owner cuts, merges and renames. The one thing that is not a matter
of taste is the bottom section: benchmarks that must NOT become categories.

---

## The finding that should be read first

**`assistant` — the category that is empty today — can be filled without Arena.**

It has answered nothing since M7 because its only source is Arena, which has been returning an
upstream 500 for days (**W-024**). But the Epoch bundle already on disk carries `mmlu_external` at
**249 models** and `epoch_capabilities_index` at **819**. Everyday-question quality does not have to
come from Arena.

That does not retire W-024 — Arena's human-preference Elo measures something MMLU does not, and the
honest move is to serve what we have and keep saying Arena is down. But the product's most common
question stops being unanswerable.

---

## Tier 1 — strong coverage, ship first

| Category | User asks | Evidence | Models |
|---|---|---|---|
| **Everyday questions** | "which is good and cheap for daily use" | `epoch_capabilities_index`, `mmlu_external`, `simplebench` | **819 / 249 / 93** |
| **Mathematics** | "help with maths / exam problems" | `otis_mock_aime`, `gsm8k`, `math_level_5`, `frontiermath` | **238 / 235 / 108 / 101** |
| **Expert reasoning** | "hard science and analysis questions" | `gpqa_diamond`, `critpt`, `hle` | **263 / 139 / 51** |
| **Computer use** | "use my computer / terminal for me" | `terminalbench`, `os_world` | **204 / 58** |
| **Coding** *(exists)* | "write and fix code" | SWE-bench Verified (live), `aider_polyglot`, `scicode` | **173 / 77 / 129** |
| **Abstract reasoning** | "puzzles, patterns, lateral thinking" | `arc_agi`, `arc_agi_2`, `chess_puzzles` | **191 / 172 / 161** |
| **Web development** | "build me a web page / front end" | `webdev_arena` | **109** |
| **Image generation** | "make me an image" | Arena mirror `text-to-image` | **76** |
| **Image editing** | "improve my profile picture" | Arena mirror `image-edit` | **53** |

## Tier 2 — real questions, thinner evidence

| Category | User asks | Evidence | Models |
|---|---|---|---|
| **Video generation** | "make a short video" | Arena mirror `text-to-video`, `image-to-video` | **45** |
| **Agentic coding** *(exists)* | "work across my whole repo" | `deepswe`, `cursorbench`, `frontierswe` | **50 / 31 / 15** |
| **Long-running agents** | "go away and finish this task" | `vending_bench_2`, `apex_agents`, `metr_time_horizons`, `balrog` | **57 / 55 / 50 / 36** |
| **Factual accuracy** | "will it make things up" | `simpleqa_verified` | **77** |
| **Long context** | "read this whole book / codebase" | `fictionlivebench` (120k token score) | **62** |
| **Video understanding** | "watch this and tell me" | `video_mme` | **50** |
| **Writing** | "write well, not just correctly" | `lech_mazur_writing` | **49** |
| **Research** | "research a topic with sources" | `deepresearchbench` | **37** |
| **Vision / screenshots** | "read this screen or diagram" | Arena mirror `vision`, `vpct` | **20 / 38** |
| **Security** | "find vulnerabilities" | `cybench`, `exploitbench` | **22 / 20** |

## Tier 3 — interesting, too thin to ship as a category today

`gdpval` (11) economically valuable work · `the_agent_company` (16) office tasks · `cad_eval` (15)
CAD · `geobench` (32) geography · `spatialviz` (8) and `mindcube` (5) spatial reasoning ·
`osworld_2` (10) · `rli` (12) · `algotune` (18) · `cl_bench` (23) · `blueprint_bench_2` (21).

Worth keeping as EVIDENCE inside a broader category rather than as headings of their own — a
category with eight models will spend most of its life apologising.

---

## Must NOT become categories

`bool_q` (206), `wino_grande` (145), `piqa` (140), `hella_swag` (135), `lambada` (80),
`open_book_qa` (71), `trivia_qa` (115), `arc_ai2` (145), `science_qa` (104), `superglue` (11),
`common_sense_qa_2` (10), `adversarial_nli` (19).

These have high model counts and are the WRONG kind of thing. They are academic instruments, most
of them near-saturated, and **nobody has ever asked which model is best at WinoGrande**. Publishing
them as headings would fill the menu with questions no user is asking, which is the exact problem
D-126's router exists to solve — and doing it on the supply side would make the router's job harder,
not easier.

They may still serve as secondary evidence where a category needs a second independent source
(REQ-REC-004's confidence rule pays for that).

---

## What this map costs

**Not acquisition.** Everything in Tier 1 and Tier 2 is either already on the owner's disk (Epoch,
77 files) or behind the keyless MIT mirror verified on 2026-08-19.

**It costs ingestion and mapping.** Each benchmark needs its score column named — they differ per
file (`EM`, `Score`, `Accuracy`, `mean_score`, `Arena Score`, `Pass@1`) — and each category needs a
`CategorySpec` with a primary benchmark, a metric, a quality floor and a value window. The floors
are the part that needs judgement: `coding` uses 65 points on a percentage scale, and an Elo
category cannot borrow that number (D-105).

**And it costs a decision about the pricing axis**, which no amount of benchmark data fixes: image,
video and speech are not priced per token. On the subscription axis every category shares dollars
per month, which is why tool selection is the home screen.

---

## The questions the owner has to answer

1. **How many categories ship in the first version?** Nine Tier-1 categories is a menu; twenty is a
   directory. The router makes a large menu survivable, but the router does not exist yet.
2. **Do we keep `assistant` as one category, or split it?** "Everyday questions" and "expert
   reasoning" are different needs with different evidence, and merging them means one of the two
   answers is wrong.
3. **Which Tier-3 items become evidence inside a Tier-1 category** rather than being dropped.
