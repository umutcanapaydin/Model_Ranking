---
record_type: review
id: m11-council-product
status: ratified
seat: independent
date: 2026-08-24
---
# M11 Council — Product & Delivery seat

**Seat:** independent. This seat wrote none of the code under review. Policy was read from the
protected base ref (`git show HEAD:AGENTS.md`, V4C-06); nothing in the working tree was treated as
a rule. No file in this repository was modified. Every claim below cites a file, a line, or a
command that was run.

**How the product was exercised.** `fastapi.testclient` against `advisor.db` with
`APP_BUILD=review-probe`, `/health` reporting `evidence: servable`. All 27 combinations of the nine
surfaces × three budgets were fetched and kept (`/v1/recommendations`), plus `/v1/categories`,
`/v1/budgets`, and the CLI subscription path
(`python -m app.workflows.recommend --db advisor.db --task coding --budget medium --subscription`).
The iOS client was read as source, not run — `ios/ModelRanking/ContentView.swift` (551 lines) is the
entire user interface.

---

## The one thing I would change first

**Put a budget control on the screen, and serve the subscription answer.**

`ios/ModelRanking/ContentView.swift:29` reads:

```swift
private let budget = "unlimited"
```

It is a `private let`, never mutated, passed straight to the engine at `:382`. There is no budget
control anywhere in the app. The word "budget" reaches the reader exactly once, inside
`"See all 58 — 25 fit your budget"` (`:199-204`) — a branch that can only fire when
`eligibleCount < ranking.count`, which under `budget=unlimited` is the case the engine is built to
avoid. Measured: at `unlimited`, `eligible_count` equals `len(ranking)` on 9 of 9 surfaces. The
sentence refers to a budget the reader was never asked for and cannot change.

This matters more than any of the CFO's five items, and here is why. The product's own one-line
description (`AGENTS.md` §1) is *"deterministic, **budget-aware** recommendations"*. `REQ-REC` is
built on it. `/v1/budgets` was added at M11-W3 under its own ADR (D-134) to publish the caps.
W-044's remedy — the "N fit your budget" sentence — was shipped as a screen fix. `scripts/simulator_session.sh`
instructs the owner, in step 4 of the walk it prints: *"Switch the budget. Does 'See all N — M fit
your budget' agree with what you see?"* **There is nothing to switch.** Eleven milestones of budget
machinery are reachable only by typing a URL.

So today the three answers on screen mean:

| Badge | What the reader assumes | What it actually is |
|---|---|---|
| BEST QUALITY | best I can afford | highest score at any price |
| BEST VALUE | best value for my money | cheapest on the Pareto frontier, no budget constraint |
| BUDGET PICK | the cheap one for my budget | cheapest above a fixed quality floor, no budget constraint |

And the second half of the same finding: `src/app/workflows/subscribe.py` (599 lines) answers the
question the CFO actually has — *"which subscription should I buy for $X a month?"* — in dollars per
month, against the curated plan table `data/plans.yaml` that its own header calls **THE MOAT**. It
is not exposed on any HTTP route. I checked every route in `src/app/adapter/main.py`: `/health`,
`/v1/categories`, `/v1/budgets`, `/v1/recommendations`. The subscription recommender is reachable
only through `recommend.py --subscription` on a terminal. It works — I ran it — and it is the only
part of this product a non-technical buyer could act on without a developer account.

Meanwhile the app prices everything in `$/1M` (`ContentView.swift:540`), a unit that exists only for
people who buy tokens through an API, for models like `o3`, `Devstral` and `GLM-5.2` that a CFO
cannot purchase at all.

**The product answers a question its stated user did not ask, at a price they cannot pay, against a
budget they cannot set.** That is one finding, not three, and it is the first thing to fix.

---

## 1. Is the core promise intact under its own disclosures?

No. It is past the line, and not for the reason the project would guess.

### Measured disclosure load

Words of caveat versus words of answer, on one screen, counted from the served payload:

| Query | Disclosure blocks | Caveat words | Answer words (`why` + `trade_off`) |
|---|---|---|---|
| `coding` / low | 8 | 176 | 47 |
| `agentic-coding` / low | 8 | 155 | 60 |
| `abstract` / low | 8 | 185 | 46 |
| `everyday` / low | 8 | 166 | 40 |

Three to four words of hedge for every word of advice, on every surface, at every budget. The
client renders up to five of those blocks as identical orange warning triangles in a single stack
— `Label(notice, systemImage: "exclamationmark.triangle").font(.caption).foregroundStyle(.orange)`
(`ContentView.swift:248-259`) — with no ordering by severity and no visual distinction between
"this benchmark has no dates, ever" and "your primary source went quiet six months ago".

### The disclosures are not too many. They are the same few facts, repeated, and two of them are permanent

**Six of nine surfaces carry a `source_health.notice` that can never clear.** Measured:

| Surface | `source_health.stale` | Reason |
|---|---|---|
| coding | true | `swebench` last published 179 days ago — **a real, actionable fact** |
| agentic-coding | true | source "publishes no parseable evaluation date" |
| everyday | true | source "publishes no parseable evaluation date" |
| computer-use | true | source "publishes no parseable evaluation date" |
| abstract | true | source "publishes no parseable evaluation date" |
| web-dev | true | source "publishes no parseable evaluation date" |
| assistant, expert, mathematics | false | — |

Five of those six are flagged not because the evidence is old but because the board **does not
publish dates at all**. The sentence served is *"Evidence behind ARC-AGI may be out of date past the
90-day window: epoch_arc_agi publishes no parseable evaluation date. The ranking may not reflect
current models."* That is a structural property of the source, dressed as a transient warning. It
will still be there in a year. A warning that cannot be cleared is a label, and a reader who meets
it on two thirds of the surfaces learns to skip orange triangles — which is exactly where the one
genuine staleness fact (coding, 179 days) is sitting, fourth from the top of the stack.

### Three freshness mechanisms in one payload, giving three different answers

Inside a single `answer` object for `coding`:

- `stale_notice: null`
- `source_health.stale: true`, with a 179-day notice
- `evidence_dating: "dated"` / on other surfaces `"undated"` with its own note

`stale_notice` is **null on all 27 queries I ran.** It cannot fire on this artifact:
`src/app/workflows/recommend.py:246-274` computes age as `MAX(observed_at) − MAX(run_date)` — the
database's own ingest time against the board's newest run. A database that is never re-ingested
cannot report itself stale, which the docstring states as an accepted limitation. So REQ-REC-006's
notice is a field that exists, is serialized, is rendered by the client at `ContentView.swift:249`,
and has never been seen by anyone. Meanwhile `_source_health_json` (`main.py:577+`) does the same
job on the wall clock and answers `true`. Two disclosures about one question, disagreeing, side by
side, and one of them structurally silent.

On `everyday`, the reader gets both of these in the same orange stack:

> *"Evidence behind Epoch Capabilities Index may be out of date past the 90-day window: epoch_eci
> publishes no parseable evaluation date. The ranking may not reflect current models."*

> *"This answer's benchmark publishes no evaluation dates, only model release dates. Its scores
> cannot be aged, so freshness is unknown rather than recent."*

The same fact, twice, and the first version overstates it: with no date to compare, "may be out of
date past the 90-day window" is a claim the engine cannot support. The second sentence is the
correct one and is better written.

On `abstract` / low the effort fact appears **three times**: once in `effort_mix_notice`, then again
in `best_value.effort_note`, then again in `budget_pick.effort_note` — all saying the scores came
from a run at max effort.

**Eight disclosure blocks carry about four distinct facts.**

### What is NOT disclosed, and it is the larger confound

The `coding` ranking mixes **eleven different agent harnesses** in one list, all shown to the
reader as one column of comparable numbers:

`inspect_ai`, `mini-SWE-agent`, `live-SWE-agent`, `OpenHands`, `Agentless-1.5`, `Tools`,
`unknown-agent`, `Prometheus-v1.2.1`, `Sonar Foundation Agent`, `Aime-coder v1`,
`EPAM AI/Run Developer Agent v20250719`.

Best Quality (Gemini 3.5 Flash, `inspect_ai`) is compared against Best Value (MiniMax M2.5,
`mini-SWE-agent`) with **no harness-mix notice of any kind.** `grep -n harness src/app/workflows/recommend.py`
returns three hits, none of which is a disclosure; the only mix notice the engine builds is
`effort_mix_notice`. `AGENTS.md` §2 — the customer glossary, read from the base ref — states: *"a
coding score always names its agent harness"*. The app never shows the harness at all
(`harness` appears zero times in `ContentView.swift`; it is decoded at `Models.swift:128,180` and
dropped).

So the product writes a paragraph about the effort confound and says nothing about the harness
confound, in the one category where its own glossary says the harness is inseparable from the
score. That asymmetry is not a disclosure problem; it is a credibility problem, and it is the kind
a reviewer who knows the domain will find first.

### Against the product's own framing

D-126 is the clearest statement of identity this project has: *"We do not do benchmarking. We are
like a weather app for the AI world."* A weather app says **22°, rain after four**. It does not
append the calibration log of the station, twice, in different words, one of which is wrong.

The disclosure discipline built in M5–M7 is correct in substance and unmanaged in presentation.
Nobody has ever been accountable for the total.

### Defects found while doing this

1. **`"but 1x cheaper."`** — `computer-use` / low, `budget_pick` = GPT-5 mini at $0.69 blended,
   leader Gemini 3 Flash at $0.98. `recommend.py:370` formats `quality.blended / cheap.blended`
   with `:.0f`; 1.42 renders as `1`. The reader is told they give up 2.7 points **for no saving.**
   Any ratio under 1.5 produces this.
2. **`ORDERING_NOTE` contains the wrong noun and is served unconditionally.**
   `src/app/adapter/main.py:76-80`: *"They rank different sets of **plans** on different evidence"* —
   it means models. And it ships on every response, including `task=expert&budget=low`, which
   returns one answer and no coding surface, where *"neither coding surface leads the other"* is
   nonsense. Rendered at `ContentView.swift:125`.
3. **`m12-inputs.md` item 2 is understated.** The record says *"The payload carries
   `evidence_source_url`, which is the BENCHMARK's source"*. It does not.
   `grep -c evidence_source_url` across all 27 responses returns **0**; the field is not in
   `PUBLIC_ANSWER_FIELDS` and not in the pick allowlist (`main.py:723+`). `/v1` publishes only the
   `sources` attribution strings, and the client never renders those either. The CFO's "Go to Page"
   has no data behind it at all, benchmark or vendor.
4. **`subscribe.py:15` docstring:** *"User-facing strings are Turkish by design (owner's market —
   .language-allow)."* There are no Turkish strings left in the file. The comment contradicts
   `AGENTS.md` §5 (V4C-79) and would mislead the M12 localisation work, which is being planned
   against exactly this module's assumptions.
5. **`ios/ModelRanking/Engine/EngineClient.swift:60`** ships to an end user:
   *"Start it with `make run` in the engine repository, then try again."* — plus the raw
   `URLError.localizedDescription`. `:66-68` ships a paragraph about `NSAllowsArbitraryLoads`.
   `:75-76` appends `String(describing:)` of a `DecodingError`. These are developer notes in a
   `ContentUnavailableView`.
6. **The full ranking has no empty state.** `ContentView.swift:503-507` renders zero rows when the
   filter matches nothing; the home preview has *"No model here matches "x"."* (`:219`) and the full
   list does not.

---

## 2. The comprehensibility inventory — every place the reader meets domain knowledge

The CFO reported five. Below is the complete set, walked screen zone by screen zone from the
served payload and `ContentView.swift`. **Twenty-eight rows.** The five reported items are marked
★.

| What the reader sees | What it assumes they know | What it could say |
|---|---|---|
| ★ Chip: `Abstract reasoning` (`categories.py:156`) | that this means unseen visual puzzles, not "philosophy" | `Puzzles & pattern finding` |
| ★ Chip: `Agentic coding` (`:70`) | what an "agent" is in this industry | `Coding on its own` |
| ★ Chips: `Everyday assistant / chat` (`:52`) **and** `Everyday questions` (`:96`) | that two chips beginning with the same word measure different things — the owner and the lead agent both confused these | `Chat` and `General knowledge` |
| ★ Chip: `Expert reasoning` (`:110`) | that "expert" means PhD-level science, not "for experts" | `Hard science questions` |
| ★ Chip: `Computer use` (`:141`) | that this means driving a terminal unattended | `Operating a computer` |
| ★ `161.7 ECI` (`everyday` picks) | the scale — there is none published; 161.7 out of what? | `#1 of 58 · Epoch's overall capability index` |
| ★ `1504.2 elo` (`assistant`, `web-dev`) | chess rating maths; that 1504 vs 1476 is small | `#1 of 65 · head-to-head human preference rating` |
| ★ `$1.03/1M` → in-app `$2.95/1M` (`ContentView.swift:540`) | that "1M" means tokens, and what a token costs to use | `$2.95 per million tokens — about $3 for 1,500 pages of text` |
| `83.5 % resolved` | fine as English (CFO confirmed), but not that it means *real GitHub issues* | `solved 83.5% of real software bugs` |
| `94.4 % correct` (`expert`, `mathematics`, `abstract`) | which questions | `answered 94.4% of PhD-level science questions` |
| `64.3 % resolved` (`computer-use`), `72.8 points` (`agentic-coding`) | that "% resolved" and "points" are the same thing worded twice — `metric` says `% resolved`, `why` says `points` | one unit per surface, everywhere |
| Benchmark name in the footnote: `SWE-bench Verified`, `DeepSWE`, `GPQA Diamond`, `ARC-AGI`, `TerminalBench`, `WebDev Arena`, `Arena text`, `Epoch Capabilities Index` (`ContentView.swift:133-139`) | that these are independent public tests, not our own products | `measured by SWE-bench, an independent public test of 500 real bug fixes` |
| **`AIME (mock)`** (`categories.py:125`) reaching the screen verbatim | that "mock" is the name of a real Epoch board (OTIS Mock AIME), not that our data is fake | `AIME-style competition maths (Epoch's practice set)` |
| `"44 models ranked on SWE-bench Verified, at high effort"` (`:133-139`) | what "effort" is as a model setting | `"44 models tested, all at the same setting"` |
| `BEST QUALITY` / `BEST VALUE` / `BUDGET PICK` (`ContentView.swift:433`, from `best_quality` etc.) | that "value" means score-per-dollar, not "good value overall"; that "budget" is a fixed floor, not *your* budget | `Highest scoring` / `Best score for the money` / `Cheapest that is still good enough` |
| 71 model names: `o3`, `o4-mini`, `Devstral`, `GLM-5.2`, `Kimi K2.6`, `Grok 4.20`, `MiniMax M2.7`, `Qwen3.8 Max`, `GPT-5 chat` | the entire vendor version-numbering landscape; and, crucially, **whether any of these can be bought** | availability: *in ChatGPT Plus* / *API only — needs a developer account* |
| Vendor captions: `Zhipu`, `MiniMax`, `Alibaba`, `xAI` (`ContentView.swift:464,485`) | who these companies are | keep, but pair with availability |
| `Claude Opus 4.7`, `Claude 4.5 Opus`, `Claude Opus 4.6` **in the same list** | that two of these are the same naming scheme written backwards | one canonical order in the alias table |
| `"On the Pareto frontier, the cheapest model within 6 points of the leader."` (`recommend.py:341`) | Pareto optimality | `"the cheapest model that is still within 6 points of the best"` |
| `"Cheapest model that clears the 65 points minimum-quality bar."` (`:356`) | where 65 came from and what a "quality bar" is | `"the cheapest model we would still call good at this — anything below 65 we would not recommend"` |
| `"WARNING: no model in this budget clears the 50 points minimum-quality bar; this is the cheapest available and you are trading quality away."` (`:358-361`) | all of the above, in capitals, as the *reason for a recommendation* | `"Nothing cheap here is good enough. This is the cheapest, and it is not good."` |
| `"3.5 points below the leader, and 82% cheaper."` / `"9.3 points below the leader, but 10x cheaper."` (`:347,370`) | that "points" are on a scale never stated, and — see defect 1 — that `1x cheaper` means *the same price* | `"a little worse at this, and one fifth of the cost"` |
| `"DeepSeek V4 Pro is only 1.1 points behind — the gap is within the margin of error and either choice is defensible."` (`close_call`) | "margin of error", "defensible" | `"DeepSeek V4 Pro is close enough that either is a fine choice."` |
| `"Note: this category does not compare at a fixed effort level, and the scores in this answer come from different levels (high, unspecified)…"` (`effort_mix_notice`) | that models have an "effort" dial; that `unspecified` is a value | `"These models were not all tested the same way, so small differences may not be real."` |
| `"This model was ranked at high effort; at max effort it reaches 67.2 points."` (`effort_note`) | all of the above, plus which one we used | fold into the mix notice; do not repeat per pick |
| `"Evidence behind ARC-AGI may be out of date past the 90-day window: epoch_arc_agi publishes no parseable evaluation date."` (`source_health.notice`) | `epoch_arc_agi` — **an internal source id**; "90-day window"; "parseable" | `"This test does not publish when it ran, so we cannot tell you how fresh these numbers are."` |
| `"This answer's benchmark publishes no evaluation dates, only model release dates."` (`evidence_dating_note`) | benchmark vs. model release date | same sentence as the row above — pick one |
| `"Pricing data: BerriAI/litellm (MIT) and OpenRouter public model catalog (attribution required)"`; `"Epoch AI, 'AI Benchmarking Hub'… [online resource]. (CC-BY-4.0)"` (`sources`) | GitHub org names, SPDX licence identifiers, academic citation form | `"Prices from LiteLLM and OpenRouter. Scores from Epoch AI."` with the citation on an About screen |
| `"Answers are ordered alphabetically by surface id. The order carries no meaning: neither coding surface leads the other. They rank different sets of plans on different evidence…"` (`main.py:76-80`) | "surface id"; and it says *plans* when it means models | `"Both coding answers are shown. Neither is ranked above the other."` |
| `"This surface has no evidence to rank: nothing on DeepSWE reached the ranking in the served database, so no budget was applied."` (`main.py:972-975`) | "surface", "the served database", "reached the ranking" | `"We have no measurements for this yet."` |
| `"No model on this surface's benchmark fits the requested budget, so this answer ranks nothing. It is shown rather than hidden."` (`:983-986`) | why we are explaining our own editorial policy to a buyer | `"Nothing fits this budget. Try a higher one."` |
| `"See all 44"` (`ContentView.swift:199-204`) | that these 44 are *not* filtered by budget, and that no rank number is shown anywhere | `"See all 44 models"` with `#1…#44` on the rows |
| `"Which model?"` (nav title, `:53`) and `"What do you want an AI to do?"` (`:80`) | that the app knows about exactly nine things | one line under the field naming what it covers |
| `"This is not something we measure directly, so it is answered with the general assistant ranking."` (`Router.swift:43-44`) | "measure", "ranking", and that the confident answer below it is therefore not about their question | `"We do not have measurements for that. Here is our general chat ranking instead."` — and grey out the picks |
| `"Start it with \`make run\` in the engine repository, then try again."` (`EngineClient.swift:60`) | that they own a repository | `"The service is not reachable. Try again shortly."` |
| `"…Do NOT add NSAllowsArbitraryLoads — that permits cleartext to every host…"` (`:66-68`) | iOS App Transport Security | remove from the user-facing string entirely |

**And the inverse list — computed, published, and never shown to anybody** (verified: zero
references outside `ios/ModelRanking/Engine/Models.swift`): `harness`, `effort`, `effort_note`,
`higher_effort`, `higher_effort_score`, `confidence`, `confidence_basis`, `input_per_m`,
`output_per_m`, `secondary_score`, `evidence_date`, `frontier_size`, `sources`,
`source_health.sources[]`, `evidence_dating`, `surfaces_are_ranked`. Sixteen fields.

Two of those are worth naming individually.

- **`evidence_date` is never rendered on a row.** So in the `coding` list, `Gemini 3.5 Flash`
  (measured 2026-06-01) sits three rows above `Claude 4.5 Opus` (measured **2025-12-15**) with
  nothing to distinguish them. The freshness disclosure exists only as a global orange sentence
  about the *source*, never as a fact about the number the reader is looking at. The one place a
  date would actually change a decision is the one place it does not appear.
- **`surfaces_are_ranked: false`** is the engine's explicit anti-inference flag, added so a client
  could not present the surface order as a ranking. The client decodes it (`Models.swift:25`) and
  ignores it.

---

## 3. Who is this for, and does the product agree with itself?

`docs/prd.md` §1 names the user once, in a subordinate clause: *"consumers and developers who do not
know which AI model or subscription fits their needs."* That is **two users and two products**, and
the sentence has never been revisited. Eleven milestones later the product serves neither cleanly.

**Evidence that it does not agree with itself:**

1. **The budget is hardcoded** (`ContentView.swift:29`). The half of the promise aimed at somebody
   with a wallet is not reachable.
2. **The subscription recommender is not served.** 599 lines, its own REQ-SUB family, a curated
   moat, and no route.
3. **Two incompatible budget scales share three names.** Model budgets are blended `$/1M`:
   low = 2.0, medium = 8.0 (`/v1/budgets`). Plan budgets are dollars **per month**: low = 10,
   medium = 25 (`data/plans.yaml`, `subscribe.py:155-165`, reading `cap_dusuk` / `cap_orta`). Same
   three ids, two scales differing by three orders of magnitude and a different unit of time.
4. **The nine surfaces are split down the middle.** `everyday`, `assistant`, `mathematics` are
   consumer questions. `agentic-coding`, `computer-use`, `abstract`, `coding` are developer and
   researcher questions — a consumer does not choose a model by TerminalBench. The one control the
   consumer needs (price they can pay) is absent; the controls the developer needs (harness,
   effort, input/output split, evidence date) are computed and hidden.
5. **The subscription answer, when I ran it, disqualifies every plan a consumer has heard of.**
   `--task coding --budget medium` returns `unscored_plans: ["ChatGPT Go", "ChatGPT Plus",
   "ChatGPT Pro", "Claude Max", "Claude Pro"]` and recommends **Perplexity Pro** and **Google AI
   Plus**. The reason is honest and correct — those pages name no explicit models, and M1 rule 4
   forbids guessing — but it lives in a bare array with no sentence attached. A buyer shown that
   screen concludes ChatGPT Plus lost. It did not compete. Best Quality is *Perplexity Pro*, scored
   by **GLM-5.2**, via a `scored_via: "roster"` link. This is defensible engineering and an
   indefensible thing to put in front of a CFO without a sentence explaining it.
6. **Two of nine surfaces can no longer separate their leaders** (W-035, still ACCEPTED). On
   `mathematics` three models tie at exactly 100.0; on `expert` the top twelve span less than the
   board's own standard error. `close_call` fires honestly and the answer is *"either choice is
   defensible"* — which, on a surface where that is permanently true, is a surface that cannot give
   advice.
7. **`docs/feature-catalog.md` — "Single canonical source for what the customer sees" — is still
   the unfilled template.** Section headings and *"Fill per project."* Eleven milestones, 61
   governed records, and the one artifact whose job was to hold the customer's view was never
   started.

That last point is the answer to M11's carried question. The project asks *"what would we have to
measure to catch the next one of these before a user does?"* The instrument already existed as a
slot in the docs tree. Nothing made filling it a gate, so it was never filled, and every closure
report passed without noticing. **A record type with no check behind it is the documentation
equivalent of the control-not-in-the-path failure this project has now recorded five times.** The
cheapest fix is not a new gate: it is to make `feature-catalog.md` the file that a wave-close row
must cite whenever a served string changes — the same shape `wave_check.py::review_seat_problems`
already enforces for reviews.

**Is there a coherent user?** There is one coherent product hiding inside two half-served ones. The
coherent one is: *"I am about to pay for an AI. Which one, and what will it cost me a month?"* That
user needs the plan engine, a budget control in dollars per month, availability on every model row,
and about four of the nine surfaces. The developer product — harness, effort, per-token pricing,
evidence dates, the full 44-row list — is already built and already hidden, and would be a good
second screen behind a "details" disclosure. It should not be the default.

---

## 4. The shortest path to being useful to somebody who is not the owner

Ordered. Deployment is not on this list, per the owner's sequencing (local → his phone → App Store).

1. **Add the budget control** (`ContentView.swift:29` → a three-way picker fed by `/v1/budgets`,
   which already publishes the caps). No engine change. This is the smallest edit in the list and
   it turns three badges from decoration into advice. It also makes the `"See all 58 — 25 fit your
   budget"` branch reachable for the first time.
2. **Rename the five surfaces**, exactly as `m12-inputs.md` §3 proposes, and fix the
   `Everyday…`/`Everyday…` collision. Data-only change in `categories.py`; `title` already flows
   through `/v1/categories` and `ContentView.swift:304`. Costs nothing and removes five of the
   twenty-eight inventory rows.
3. **Add the plain line beside every number.** Rank first (`#3 of 21` — it needs no scale and the
   engine already knows the ordering), then the one-sentence gloss, then price in pages
   (`about $3 for 1,500 pages`). This is the contract move the owner already decided
   (`m12-inputs.md` §1): the engine returns `rank`, `rank_of`, and `metric_gloss` as **facts**;
   the client composes the sentence. Doing it now serves item 5 and item 4 and lays the localisation
   groundwork in the same change, which is the whole argument of D-13x-to-be.
4. **Collapse the disclosure stack from eight blocks to three, ranked.** One line about freshness
   (choose `source_health` OR `evidence_dating`, not both; retire `stale_notice` or re-anchor it to
   the wall clock so it can fire), one about comparability (fold the per-pick `effort_note`s into
   the single mix notice, and **add the missing harness-mix notice for `coding`**), one about
   near-ties. Give the genuinely actionable one — *"our main coding source last published 179 days
   ago"* — a different weight from the permanent ones. Move `sources` and licence text to an About
   screen.
5. **Serve the subscription answer** (`/v1/plans` or a `kind=` parameter), with a sentence for
   `unscored_plans` — *"ChatGPT Plus does not publish which models it includes, so we cannot score
   it"* — and monthly-dollar budgets whose ids do **not** collide with the token budgets.
6. **Put availability on every model row.** Not a "Go to Page" link first — the underlying question
   is *can I buy this at all*. `plan_models` already carries plan→model links for the plans in
   `data/plans.yaml`; that is enough to mark a row *"in ChatGPT Plus"* versus *"API only"*. The
   vendor URL map (`m12-inputs.md` §2) is the second half and needs curation; do the availability
   flag first because it changes decisions and the link only changes convenience.
7. **Fix the four small defects that make the product look wrong**: `1x cheaper`, the `plans`/models
   noun in `ORDERING_NOTE`, the developer text in `EngineClient.swift:60-76`, and the missing empty
   state in the full-ranking list.
8. **Fill `docs/feature-catalog.md`** with the current screen text and wire it into wave close, so
   the next comprehensibility finding is caught by the project rather than by a stranger.

Items 1, 2 and 7 are, together, well under a day and change what a stranger sees more than M9 and
M10 combined. Item 3 is the milestone.

---

## 5. What I would cut

| Cut | Measured cost / return |
|---|---|
| **Aider polyglot as a secondary benchmark** | Its only effect is lifting `confidence` from Medium to High. Measured: **3 of 90 picks** across all 27 queries; 36 of 1,245 ranking rows carry a `secondary_score`. And `confidence` is never displayed. An entire client, contract test, ingest path, `secondary_*` fields in two payload arrays, and a source whose own health flag says it stalled in Nov 2025 — buying an invisible grade on 3.3% of picks. |
| **`confidence` / `confidence_basis`** | 87 of 90 picks read `Medium` / `one independent benchmark (X)`. A field that is the same value 97% of the time carries no information, and nothing renders it. If it survives the Aider cut it should be deleted with it. |
| **`epoch_mmlu`** | 136 rows ingested. Reaches **3 of 58** `everyday` models as a secondary score. Shown to nobody. |
| **`frontier_size`** | Served on every answer, never rendered, and meaningless without the word "Pareto". |
| **One of `evidence_dating_note` / `source_health.notice`** | They state the same fact in different words on the same screen, and the second overstates it. |
| **`stale_notice` as currently anchored** | Cannot fire on any served artifact (`recommend.py:246-274`). Either re-anchor it to the wall clock — at which point it duplicates `source_health` and one of the two should go — or delete the field. A disclosure that has never once been seen is not a disclosure. |
| **The unfiltered 44/58/65-row ranking, at its current prominence** | W-040 has been ESCALATED since M8. It is an unbounded array on an unauthenticated GET (~20 KB measured, up to ~3.5 MB at the process ceiling), it is not budget-filtered, it has no rank numbers, and W-069 showed it actively misleading the owner — he read three coding-named models at the bottom of a filtered list and concluded the filter was broken. Keep the data behind a "show everything" affordance; do not put an unfiltered 65-row list one tap from the home screen of a product for people who do not know what a benchmark is. |
| **`ORDERING_NOTE` on single-answer responses** | Two of its three sentences are false when only one surface is returned. |
| **The `expert` and `mathematics` surfaces, as separate top-level chips** | W-035, ACCEPTED since M8 and re-assigned twice. Both benchmarks are at their ceiling and cannot separate their leaders; `close_call` fires permanently. Two of nine chips lead to a screen whose honest answer is *"these are all the same"*. Merging them into one *Hard questions* surface, or demoting them behind the others, costs less than sourcing a second benchmark for each. |

**What I would not cut, and would defend:** `close_call`, `why`, `trade_off`, and the
`unavailable_reason` branch that distinguishes *"no evidence"* from *"nothing fits your budget"*
(`main.py:951-986`). Those four are the product. They are the only places where the engine explains
a decision rather than reporting a measurement, and every one of them survives translation into
plain English without losing its meaning. The rewrite in §2 makes them shorter, not fewer.

---

## What I could not judge without more users

1. **Whether nine surfaces is too many.** One person found two of them confusable. I can show that
   two are at their measurement ceiling and that four are developer questions, but whether a
   consumer wants three chips or nine is a question about demand, and I have one data point.
2. **Whether "Best Value" is the pick people actually take.** The engine spends most of its
   sophistication on the Pareto frontier. Nobody knows whether readers choose it, or default to the
   top of the list, or to the cheapest. That is one instrumented number away and cannot be reasoned
   to.
3. **Whether disclosure builds trust or erodes it in this audience.** My finding is that eight
   blocks carrying four facts is too many; I am confident about the redundancy and the permanence
   and much less confident about where the floor is. A reader who is told nothing may trust less,
   not more. Two people and a printout of two variants would settle it.
4. **Whether the CFO wants a model or a subscription.** I have argued he wants a subscription. He
   was shown a model recommender and produced five items about wording, not one about "I cannot buy
   any of these" — which either means the framing is right and I am wrong, or means he did not get
   far enough in to notice. **This is the single highest-value question to ask him, and it is one
   question.**
5. **Whether the ASK field is used at all.** The router is the largest piece of client engineering
   in the product (`Router.swift`, three tiers, a Swift test suite, its own ADR). Whether anyone
   types into it rather than tapping a chip is unknown, and it determines whether M12 should invest
   there or leave it.
6. **Whether Turkish is the second language that matters**, or whether the first non-owner audience
   is Turkish-speaking at all. The contract move in §3 above is right regardless — prose in an API
   is a trap whichever language comes second — but the ordering of *which* language depends on who
   the next five users are.

---

**Verdict: the engine is sound and the product is not finished.** Nothing in the scoring path needs
changing and D-104 is intact. What is missing is that no one has ever been accountable for the
whole of what a reader sees, and the two symptoms of that are the twenty-eight-row inventory above
and a budget control that does not exist in a product whose one-line description is
"budget-aware".

Filled by: the Product & Delivery seat (independent) · Date: 2026-08-24 · Tree: `advisor.db` at
`/health` `evidence: servable`, 27 `/v1/recommendations` queries + `/v1/categories` +
`/v1/budgets` + the `--subscription` CLI path.
