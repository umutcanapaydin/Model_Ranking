---
record_type: register
id: second-opinion
status: draft
date: 2026-09-05
---
# Second opinion — every open question, stated so a stranger can answer it

**What this file is.** The owner asked for every question the lead agent would put to him, written
out in full, so that he can take them to somebody else — another AI, an advisor, a person — and get
an independent answer without this conversation in front of them.

**So it is written for a reader who knows nothing.** Every question carries its own context, the
measurement behind it, what each option costs, and the chair's recommendation stated separately so
it can be disagreed with. Nothing here says "as discussed."

**How to use it.** Read §0 for the product in one page. Then answer the questions that matter to
you; they are ordered by what blocks M13, not by size. **Q1–Q6 block the M13 plan.** Q7–Q14 are
real but can be decided inside a wave. Q15–Q22 are standing debt the owner has already been told
about at least once.

**Provenance.** Questions marked **[council]** were voted on blind by five independent seats on
2026-08-31; the tally is given. Questions marked **[measured]** carry a number produced this week
rather than recalled. Questions marked **[unverified]** are stated as open precisely because nobody
has checked them.

---

## 0. The product in one page

`model_ranking` aggregates free-and-legal LLM benchmark and pricing data and serves deterministic,
budget-aware model recommendations. An iOS client renders them. Twelve milestones are closed; M12
awaits the owner's signature. Nothing is deployed and nothing bills.

- **74 models** — OpenAI 20, Anthropic 13, Google 8, DeepSeek 6, Alibaba 6, xAI 5, Zhipu 5,
  MiniMax 5, Moonshot 3, Mistral 2, ByteDance 1. **Zero image, audio or video models.**
- **9 surfaces** — coding, agentic-coding, assistant (Chat), everyday (General knowledge), expert
  (Hard science), mathematics, computer-use, abstract (Puzzles), web-dev.
- **4 metrics, not on a common scale** — `% resolved` (0–100), `elo` (~1400–1712), `ECI`
  (~161.7 leader, no fixed maximum), `% correct` (0–100).
- **14 sources** — litellm, openrouter, swebench, aider, arena, and nine Epoch feeds.
- **A budget picker** — Cheaper (< $2.00/1M blended), Mid-priced (< $8.00/1M), Any price.
- **A router** (`ios/ModelRanking/Engine/Router.swift`) with three tiers: `model` (Apple
  Intelligence on-device, constrained by a generation schema to the nine surface ids), `similarity`
  (sentence embeddings against hand-written hints), `manual` (the reader taps a chip).

**The doctrine that governs every answer below.** This project's repeated, expensive lesson is that
it must never present something unmeasured as measured. D-104: no LLM in the scoring path — the
client chooses words, the engine decides every number. If a fact and a sentence disagree, the fact
is right and the sentence is the defect.

---

# Part I — questions that block the M13 plan

## Q1. What replaces `% resolved` on the card? **[council] [measured]**

**Context.** A result card currently reads:

```
Claude Opus 4.7 · Anthropic
83.5 % resolved · $10/1M
#1 of 44 · the share of real tasks it finished · about $10 per 1,500 pages of text
```

The owner's directive: *"Remove the `%94 resolved` type thing. Just write Score and be done."*

**What was measured.** The four metrics are not commensurable. `elo` runs ~1400–1712 and has no
zero; `ECI` has no fixed maximum and the leader sits at ~161.7; the two percentage metrics are
bounded at 100 and both saturate — `mathematics` has **three models tied at exactly 100.0**.

**The council tally: A5 (other) ×4, A3 (rank only) ×1. A1, A2 and A4 received zero votes.**

The decisive objection, made independently by two seats: under a bare "Score" label the app prints
`Score 161.7` on one surface and `Score 83.5` on another, and a reader will compare them. The
differing metric names were the only thing preventing that comparison. Removing them is not a
simplification; it manufactures a false comparison.

**Options.**

| | What it does | What it costs |
|---|---|---|
| **A1** | Normalise every surface to 0–100 | Min-max makes the unit "fraction of the range our current 73-model sample happens to span" — it changes at every refresh and is not a property of the model. Elo has no zero; inventing one prints `Score 0` beside a model that wins ~25% of its head-to-heads |
| **A2** | Keep the native number, relabel it "Score" | Worst option on the ballot. `Score 100` reads as "perfect model" where `100.0 % correct` read as "saturated benchmark" |
| **A3** | Rank only, no number | Cannot distinguish `mathematics` (#1 and #4 separated by 0.0) from `abstract` (#1 at 98.0, last at 4.5). The project's own note: *"a sentence that has lost its number has not degraded; it has started lying"* |
| **A4** | A latent-axis (PC-1) composite | Computable for only 49–50 of 73 models, and it collapses the one axis the app most credibly measures (see Q2) |
| **A5** | Something else | — |

**Chair's recommendation.** Print the ceiling, not just the number: **`Score 83.5 / 100`**. Keep
the plain-language gloss underneath — it is the part that works and no seat criticised it. Where a
metric has no honest ceiling (ECI), show **rank only, no number**. Never compare across surfaces.

**The question for you.** Does `Score 83.5 / 100` satisfy what you meant by "just write Score", or
did you mean the number should go too?

---

## Q2. Is a single cross-surface score defensible at all? **[measured]**

**Context.** "Scoring must be single" can mean two very different things: one *label* per surface
(Q1), or one *number* across all nine surfaces. The second is a much bigger claim.

**What was measured.** The Measurement seat ran principal component analysis on the actual
74 × 14 matrix, on a copy of `advisor.db`.

- The matrix is **73 models × 12 benchmark columns, 50.2% filled**. **Exactly one model of 73 has
  all twelve columns.**
- On the largest complete block (49 models × 4 benchmarks) the **first component explains 0.806 of
  variance**, and 0 of 2000 column permutations came near it. **A single general-capability axis is
  real in our data.**
- **But the "top 3 components ≈ 97%" figure from the literature cannot be tested here.** A
  permutation null on the same block already produces cum-3 = 0.83 from pure noise. The 97% figure
  is largely an artifact of column count.
- **PC2 is Arena, and it is a genuinely separate axis** (loading −0.87 to −0.92, everything else
  near zero). Human preference is not general capability, and our own data says so. Any single
  score that folds Arena in destroys the axis the app measures most credibly.

**Chair's recommendation.** One score *per surface* — yes, the evidence supports collapsing a
surface's metric to one readable number. One score *across surfaces* — no, and specifically not one
that absorbs Arena.

**The question for you.** When you said "scoring must be single", did you mean one number per
result card, or one number per model across the whole app?

---

## Q3. When we have not measured something, what does the screen do? **[council]**

**Context.** You want: *"whatever he writes in that bar, a sensible model ordering is produced and
shown to him."* The chair proposed a three-layer rule whose third layer declines to show an
ordering when the question is out of scope. These cannot both be fully honoured.

**What was measured.** Two things changed the shape of this question.

1. **The chair's middle layer — a derived score for an unmeasured surface — failed on our own
   data.** Leave-one-out prediction from the latent axis to a held-out benchmark: ARC-AGI R² 0.813,
   TerminalBench 0.560, WebDev Arena 0.398, SWE-bench Verified 0.334, **DeepSWE −0.104**. A negative
   R² means the derived score predicts *worse than printing the population mean* — and that is the
   easy case, same modality, boards we already hold. **Council vote: layer 2 deleted, 5–0.**
2. **The app already does not decline.** `Router.swift:206-210` routes a below-floor question to the
   chat surface with `unmeasured: true`, and `ContentView.swift:121-130` renders an orange caveat
   above a complete ranking. The chair's layer 3 would have *removed* shipped behaviour.

**Council tally: B2 (measured or decline) ×3, B4 (B2 plus a mandated template) ×2. B1 — the chair's
proposal — zero votes.**

**Chair's recommendation.** You win on *show*, the doctrine wins on *say*, and they do not collide
because they govern different parts of the screen. An ordering always appears. A caption always
appears above it, and the caption names what the list cannot tell you. Two cases, two sentences:

> **We do not rank image models yet.** All 74 models here are measured on text work, so nothing in
> this list tells you which one edits a photo best — this is the general chat ranking.

> **We have not measured translation.** This is the general chat ranking, the closest thing we have
> measured. Treat it as a starting point, not as an answer to what you asked.

The Stranger seat added a third element and the chair agrees with it: end the caption with a button
— **"Ask us to add image models"** — that returns a receipt (*"Noted."*). That turns a dead end into
the only demand instrument this project has. See Q8 for the privacy cost.

**The question for you.** Is "always show a list, always caption it, offer a button to request
coverage" what you meant, or do you want the app to answer without any caption at all?

---

## Q4. The budget strip: what exactly goes? **[council] [measured]**

**Context.** Your directive: *"We do not want cheaper / mid-price / any price. We are simplifying
the app."* Your note adds that price could become a hidden attribute.

**What was measured.** On `mathematics`: best quality is 100.0 at **$7.69/1M**; best value is 94.4
at **$0.13/1M**. That is 5.6 points behind at **59× cheaper**. On `coding`: best value is 3.4 points
behind and 23% cheaper.

**Council tally: E3 ×3, E2 ×1, E5 ×1. E1 — price becomes a hidden attribute — zero votes.
Removing the strip itself: unanimous.**

The Product seat's phrasing: *"A ranking of which model is best is a thing anyone can read off a
leaderboard. Which model is 94% as good for 1.7% of the money is the answer nobody else is giving
him. Hiding price would delete the reason to open the app."*

The Measurement seat added an independent reason: **price is the only number in the payload measured
without error.** Every score carries noise the app does not quantify; `blended_per_m` does not.
Removing the highest-quality datum while keeping the noisiest ones is the wrong trade.

**Chair's recommendation.** Remove the strip. Keep every price figure on the card. Keep the
BEST VALUE and BUDGET PICK labels. Keep `/v1/budgets` — withdrawing a published sibling resource is
a compatibility break where hiding a UI control is not.

**Three questions for you.**
1. Do the price *numbers* stay on the card? (Council: yes, unanimously.)
2. Do BEST VALUE / BUDGET PICK survive?
3. Does `/v1/budgets` (D-134, REQ-API-010) stay served for non-iOS consumers?

---

## Q5. Tapping a model: where does it go? **[council] [measured]**

**Context.** Your directive: tapping a model must open that model's official web URL, and the
12-hour crawler should find those URLs.

**What was measured.** The Data seat pulled both live catalogues (OpenRouter 395 entries, LiteLLM
3,408) and joined them against the 955 alias rows in `advisor.db`:

| | Models |
|---|---|
| Official URL obtainable free from data we already fetch | **44 of 74 (59%)** |
| — via HuggingFace model card (`hugging_face_id`) | 20, open-weight only |
| — via vendor-domain LiteLLM `source` | 35, overlapping |
| **Need hand entry** | **30 of 74 (41%)** |

**The 30 are exactly the models the product exists to rank**: OpenAI 15, Anthropic 10, Alibaba 3,
DeepSeek 1, ByteDance 1 — every `claude-4.x`, `gpt-5`, `o3`.

Two traps found:
- **LiteLLM's `source` field is a pricing page and often a reseller's.** 14 point to Databricks
  pricing, 5 to Oracle, 3 to Fireworks. Tapping "claude-4.5-sonnet" would open a Databricks price
  list. Restricted to the vendor's own domain it covers 35 of 71.
- **OpenRouter's `links` field is not a URL** — its only key is a relative API path.

**Two seats independently proposed the same alternative.** Tapping should open a **model detail
screen**, not an external site. Every field it needs is already in the payload and thrown away by
the client: `harness`, `effort`, `higher_effort_score`, `confidence`, `confidence_basis`,
`evidence_date`, `input_per_m`/`output_per_m`. The official URL becomes a secondary link on that
screen — *"Open on anthropic.com"*. You get your link, one tap further in, and the product finishes
its sentence first.

The Mobile seat's refusal, which the chair endorses: **do not let a crawler decide which domain the
user's browser navigates to.** There are eleven vendors in the whole catalogue. Write down eleven
origins, check them once, version them in the repo, and have the client validate against that
allowlist before presenting. Invariant INV-23 already says URIs are derived, never concatenated.

**Two questions for you.**
1. Detail screen with the URL as a secondary link, or straight out to the browser?
2. Are you willing to hand-maintain ~30 vendor URLs, or should the feature ship covering only the
   44 that come free?

---

## Q6. What gets extended first? **[council] [measured]**

**Context.** Your directive: *"Extend the cluster — with only this much it is too barren. Think like
Google. We usually get our business done on the first page. We have to put the real, true answer in
front of people."*

**What was measured — and this is the largest single finding of the council.** Your own example
(*"which model best enhances a profile photo"*) does not need a new source. The dataset we already
ingest — `lmarena-ai/leaderboard-dataset`, **CC BY 4.0** — has an **`image_edit` config**: 93 rows,
publish date 2026-08-18, `gpt-image-2` at 1462.8 Elo on 199,275 votes. And
`ArenaClient.__init__(config="text")` **already takes `config` as a parameter**
(`src/app/clients/arena.py:76`). The attribution string is the one already in the catalogue.

Three of the four image benchmarks the chair originally listed would each need a new client and a
new licence review; Artificial Analysis would need a commercial contract we cannot have. The fourth
is a config string on a client shipped in M2.

**But the blocker is not licensing, it is the pricing schema.** The `pricing` table declares
`input_per_m` / `output_per_m` with `CHECK (> 0)`. Image models are priced **per image**. A tenth
surface would ship **unpriced** — which removes the BEST VALUE mechanic that Q4 just established as
the product's differentiator.

**And the corpus we already have has a clock problem.** Six of twelve score sources carry **no
`run_date` at all**: `epoch_eci` (521 rows — the spine of the `everyday` surface),
`epoch_terminalbench`, `epoch_arc_agi`, `epoch_webdev`, `epoch_mmlu`, `epoch_deepswe_external`.
Staleness is structurally unmeasurable for half the corpus. Worse, these nine Epoch feeds are not
crawled at all — they refresh only when the owner drops a new folder on his own Mac
(`src/app/workflows/sources.py:179`).

**Council tally: D1 (new modality) ×2, D5 (repair what we hold first) ×2, D3 (instrument demand
first) ×1.** This is the only ballot where the council genuinely split.

**Chair's recommendation.** Both, in this order: fix `run_date` on the six undated sources first,
then ship `image_edit`. Adding a tenth surface to a corpus with no clock multiplies a staleness we
cannot measure. But `image_edit` is a config string, not a project — the two fit in one wave.

**Three questions for you.**
1. Is an **unpriced** image surface acceptable, or must every surface carry price?
2. Do you accept fixing dates before adding a modality?
3. "Think like Google" — Google's first page works because click-through tells it which answer was
   right. We have no such signal. Do you want us to build one? (See Q8; it is not free.)

---

# Part II — real questions that can be decided inside a wave

## Q7. Which tier is the product? **[measured]**

**What was measured.** Apple Intelligence was off on the owner's Mac
(`.unavailable(.appleIntelligenceNotEnabled)`), so `ModelRouter` had **never once fired** in twelve
milestones. It is now enabled: host latency 1.33 s cold, 0.17 s warm on an M3.

**But the Mobile seat found the framing problem.** `IPHONEOS_DEPLOYMENT_TARGET = 18.0`, while Apple
Intelligence requires iPhone 15 Pro or newer. **Every iPhone 14 and below is permanently
ineligible, regardless of OS version.** For all of them `SimilarityRouter` *is* the product — the
tier the owner described as *"it felt like a search bar, not an AI."*

> The seat's conclusion, which inverts directive 2's framing: **`SimilarityRouter` is the product;
> `ModelRouter` is a quiet upgrade. M13 should be planned around making the similarity tier good,
> not around making the model tier fire.**

**Related, and cheap:** `ModelRouter.unavailableReason` produces the string "Apple Intelligence is
turned off" at `Router.swift:222`, is read once as a guard at `:238`, and is **displayed nowhere**.
The app knew why it had degraded and told nobody for twelve milestones.

**Questions.** (a) Do you accept that the similarity tier is the shipping experience? (b) Should
the app raise the deployment target so it only ships where the model tier can run, accepting a much
smaller addressable base? (c) Should `unavailableReason` be shown?

## Q8. Demand logging versus the on-device privacy promise **[council]**

Two seats found this independently and neither was asked to look for it. `Router.swift:13` states
*"nothing typed here leaves the device"*; `ContentView.ask()` sends the engine a surface id and
nothing else; there is no request logging in `main.py`; and the app has **no `PrivacyInfo.xcprivacy`
file at all**.

So "answer *which source next?* by counted demand" — the mechanism that makes Q3's decline
temporary and Q6's D3 possible — requires either shipping the typed question to a server, breaking
a load-bearing design commitment, or building a counter that never leaves the phone and therefore
never reaches whoever picks the next source.

**The version that works:** count on-device, submit **only** the surface id and the `unmeasured`
flag, never the text. That keeps the privacy manifest empty and still answers the question.

**Question.** On-device-only counters, or are you willing to collect aggregate telemetry? The answer
decides whether a privacy manifest and a consent surface are required before App Store submission.

## Q9. `aider` — drop it and lose "High confidence", or keep a 332-day-old benchmark? **[measured]**

**This one was found by a collision between two blind seats, and one of them was wrong.**

The Data seat recommended dropping `aider` on the grounds that no surface reads it —
`grep aider src/app/workflows/categories.py` returns nothing. The Measurement seat said `aider` is
what stamps **High confidence** on every coding pick. The chair checked: **the Measurement seat is
right.** The grep missed it because the field is spelled differently:

```
categories.py:74   secondary_benchmark="Aider polyglot"
recommend.py:207   confidence_of() returns "High" because a secondary score exists
```

So: **"High confidence — two independent benchmarks (SWE-bench Verified + Aider polyglot)" is
printed on the strength of a benchmark last run 2025-10-03 (332 days ago) covering 15 of 74
models.**

**Question.** Drop `aider` and let every coding pick fall to Medium confidence (arguably the honest
outcome), or keep it and disclose its age on the card?

## Q10. `confidence_of` is a coverage count wearing a statistical name **[measured]**

`recommend.py:207-214` returns "High" when a second benchmark exists and "Medium" when it does not.
It measures *how many boards we hold*, not *how sure we are*. Both `confidence` and
`confidence_basis` are published in `/v1`. For `everyday` the secondary that mints "High" is
`epoch_mmlu` — **3 models of 74**.

**Question.** Rename it to what it is (coverage), or make it an actual confidence measure?

## Q11. The ranked gaps are inside the project's own noise threshold **[measured]**

Using the project's own `close_call` values from `categories.py`:

| Surface | n | Models statistically tied with the leader |
|---|---|---|
| expert (Hard science) | 50 | **25 (50%)** |
| mathematics | 51 | **28 (55%)** |

**On six of nine surfaces, every adjacent pair in the top ten is inside the project's own noise
threshold.** `#1 of 50` means "one of twenty-five co-leaders". The existing `close_call` logic fires
only between the top two of the Pareto frontier, only as prose, and never below rank 1.

Collapsing to a single "Score" (Q1) makes this **worse**, because the differing units were the last
cue that these numbers were not fungible.

**Question.** Do we band tied models to the same displayed score? The thresholds are already
calibrated and in the code; this is cheap and it is what makes Q1 honest rather than merely simpler.

## Q12. The keyboard — ANSWERED, and it is an app defect **[measured 2026-09-05]**

**The owner's answer: both.** No software keyboard appeared, and he could not type on his Mac
keyboard either. That was reproduced.

**Two earlier conclusions in this project's own record were wrong and are corrected here.**

1. **"Synthetic events do not reach the Simulator" — wrong.** They do. The chair had derived tap
   coordinates from the Simulator *window* origin `(595, 39)`; the actual device screen is the
   window's `AXGroup 1` at `(619, 117)`, size `356 × 775`, scale `1206/356 = 3.388`. Every earlier
   tap missed by ~78 points. With corrected coordinates a tap on the language flag switched the UI
   to Turkish and a tap on the budget row switched to Mid-priced and changed the results.
2. **The Mobile seat's verdict "simulator configuration only" — overturned for the question field.**
   That seat read the code and correctly found no `@FocusState`, no `.disabled`, no
   `allowsHitTesting`, no tap interception in `Card`, and no conflict between the two `.searchable`
   modifiers. But **nobody had tapped the field.**

**What was measured, with `ConnectHardwareKeyboard = false`:**

| Target | Result |
|---|---|
| Language flag | Works — UI switches to Turkish |
| Budget button | Works — selection changes, results change |
| **Bottom `.searchable` filter** | **Gains focus** — caret appears, clear (X) button appears, nav bar collapses |
| **The question `TextField`** (`ContentView.swift:114`) | **No visible change whatsoever.** No caret, no keyboard, nothing |
| **Software keyboard, on the field that IS focused** | **Never appears** |

**So there are two separate defects, not one.**

- **Defect A — the question field gives the reader no feedback at all.** The field the owner wants
  to build the whole product around does nothing visible when tapped, while a field 700 points below
  it responds correctly. This is the more serious of the two.
- **Defect B — no software keyboard appears for a focused field**, with the hardware keyboard
  disconnected. **On a real iPhone there is no hardware keyboard**, so this is not a simulator
  detail — if it reproduces on device, the app cannot be typed into at all.

**What is still unresolved, stated as a boundary rather than a guess.** The chair could not
determine whether the question field *silently gains focus and only the keyboard is missing*, or
*never gains focus at all*. The two look identical from outside. Synthetic **keystrokes** (unlike
mouse events) do not reach the Simulator from this environment, so the typing path could not be
exercised either.

**The settling measurement, for whoever takes this next:** add a `@FocusState` to the question field
and log its transitions, or put a temporary `print` in `.onTapGesture` / `onSubmit`, then read
`xcrun simctl spawn booted log stream`. One build answers it.

**Interim workaround for the owner:** Simulator menu **I/O → Keyboard → Connect Hardware Keyboard**
(⇧⌘K). That restores Mac typing. It does **not** fix either defect and it suppresses the software
keyboard by design — do not mistake it for a fix.

## Q13. Two real layout defects, independent of the keyboard **[measured]**

1. **The bottom search bar overlaps content.** `ContentView.swift:186` compensates with
   `.padding(.bottom, 88)` and it is not enough — in the screenshot the "Filter by model name" bar
   sits translucently over the BEST VALUE card's last line and ghosts the BUDGET PICK badge below.
2. **The question box has no submit affordance.** `ask()` fires only from `.onSubmit`. With a
   hardware keyboard connected and window focus lost there is **no way at all** to submit a
   question. This becomes critical if the bar becomes the primary input.

**Question.** Are these M13 wave items or an immediate fixpack?

## Q14. Will a stranger notice when the model tier finally fires? **[council]**

The entire observable difference between the two tiers is one footnote string in the same font,
colour and position:

- similarity → *"Matched on wording, not on meaning — check the surface is right."*
- model → *"Matched your question to this surface on this device."*

The Stranger seat: *"'on this device' is about where the computation ran. The reader's question is
'did it understand me?' And the inversion: the similarity string is the more informative of the two.
Today's design rewards a successful route with **less** information."*

Its proposal — show that the words did not have to match:

> **"prove a theorem" → Mathematics**
> Not what you meant? **Hard science** · **Puzzles**

**Question.** Does the echo replace the tier disclosure, or sit alongside it?

---

# Part III — standing debt already raised at least once

## Q15. M12's signature
`docs/closure-report-m12.md` §0 says AWAITING THE OWNER'S SIGNATURE and the milestone commit has not
been made. M13 cannot open cleanly over an unsigned M12.

## Q16. The refresh has two independent faults **[measured]**
1. **launchd cannot spawn the job.** Last exit `78 : EX_CONFIG`; neither log file written since
   2026-08-27. The Python side is proven healthy — it was run under launchd's exact minimal
   environment against a copy and produced a documented outcome. Most likely the background item
   lost Desktop access after the reboot; unverified because TCC.db is unreadable.
2. **Even alive, it would refuse.** D-128's guard fires: computer-use's median price would move
   +33% ($2.58 → $3.44), over the 25% limit. Fault 1 hid fault 2 for days.

**Question.** Run `launchctl kickstart -p gui/$(id -u)/com.hcs.modelranking.refresh` and report the
exit code; and decide whether the D-128 refusal is upstream reality or a threshold that is too tight.

## Q17. Nothing is deployed, fifth milestone
D-123, W-030, W-031. TLS, `force_https`, Fly's proxy, volume permissions under uid 10001 and the
256 MB VM's OOM behaviour are **all unverified**, and the Stage 4.0 pass measured memory in a local
container, which is a good proxy and not the platform.

## Q18. The device build has never once succeeded **[measured]**
`DEVELOPMENT_TEAM` appears **zero** times in `ios/ModelRanking.xcodeproj/project.pbxproj`;
`CODE_SIGN_STYLE = Automatic` with no team. The app cannot be signed for a device, so
`.unavailable(.deviceNotEligible)` and `.unavailable(.modelNotReady)` — two of the four cases
`ModelRouter` enumerates — **have never been observed by anyone**. Needs an Apple Developer account.

## Q19. The app cannot work on a phone even if it were signed **[measured]**
`EngineClient.localDefault = URL(string: "http://127.0.0.1:8080")!` (`EngineClient.swift:144`). On a
phone, `127.0.0.1` is the phone. The app will show `unreachable` forever until a real host exists.
This makes Q17 a prerequisite for Q18, not a parallel track.

## Q20. `docs/license-review.md` does not exist **[measured]**
`AGENTS.md:62` (§3.6, the Stage-0 gate) requires a licence and commercial-use review at
`docs/license-review.md`. Only the template exists. The gate artifact for the rule the project keeps
invoking has never been written.

## Q21. Artificial Analysis must not be ingested under the free tier **[measured]**
Their Data API docs grant attribution on all tiers and point elsewhere for redistribution:
*"For redistribution rights or bespoke contract terms, contact the team."* **The absence of a grant
is operationally the same as a prohibition.** Their base terms URL returns HTTP 404, so nobody can
claim to have read them. LMArena by contrast is `cc-by-4.0` and clean.

## Q22. Two questions from your own notes that never got answered
1. *"The app and the harnesses need to be separated"* (owner, translated from Turkish) — do you mean
   splitting the repository (engine and iOS client separately), or separating developer tooling
   (`runner`, `ios/app.sh`, `scripts/simulator_session.sh`) from product code?
2. **What happens on the second visit?** The Stranger seat: nothing in the app gives a reader any
   reason to come back — no saved question, no "since you last looked, #1 changed". *"A ranking
   product's value is in the delta, and this app renders the delta as invisible."*

## Q23. W-074 and W-040, both open by your own decision
- **W-074** — no shell linting anywhere (`runner`, six scripts, `ios/app.sh`). Offered at M11,
  declined. Recorded as a decision, not an oversight. Still your call.
- **W-040** — is the unfiltered ranking too long? Deferred to your own use of the app, and now
  answerable because a budget can be chosen. If Q4 removes the budget strip, this question changes
  shape and should be re-asked.

---

## Appendix — what the council refused

Each seat was asked to name the one thing it would decline to build. Recorded verbatim in substance:

- **Measurement:** the derived-score layer, on the hold-out numbers; and option A2, which *"is not a
  simplification but a removal of the only thing stopping a reader comparing 1504.2 to 83.5."*
- **Product:** making price a hidden attribute. *"I will remove the control. I will not remove the
  number."*
- **Data & Licensing:** ingesting Artificial Analysis under the free tier; and implementing
  directive 4 as stated, because *"the crawler finds official URLs"* is false for 30 of 74 models.
- **Senior Mobile:** opening a URL that a crawler discovered, without a hand-curated eleven-entry
  vendor-origin allowlist checked on the client; and per-keystroke routing, which turns a 1.3 s
  on-device generation into a thermal budget.
- **Stranger:** directive 1 as literally worded. *"`Score 161.7` and `Score 83.5` on adjacent
  surfaces invites a comparison the data cannot support."*
