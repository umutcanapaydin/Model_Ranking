---
record_type: plan
id: m14-plan
status: draft
process_version: v5.0
date: 2026-09-18
---
# M14 Plan — The catalogue starts answering the questions people actually ask

**Status:** **§5 RULED BY THE OWNER, 2026-09-18. W1 dispatch is authorized.** The five decisions
below carry his answers inline. One of them (D-143) adds a wave and is recorded as its own ADR.
**Date:** 2026-09-18 · **Risk tier:** **HIGH** overall (a new external source, a tenth ranked
surface, and the first time the product records what its readers asked for) · **Mode:** A0.5 +
D-117 · **Process baseline:** GP v5.0 · **Review depth:** D-122 · **K.7:** every wave review is a
separate session and a file (D-133), dated after the code it reviews (D-137).
**Quarterly obligation:** 14 % 3 ≠ 0 — no handover is due at this closure.

**Prerequisite:** M13 is closed agent-side and **unsigned**. M14 must not open over an unsigned
milestone (the rule M13 itself was held to). Sign M13 first, or waive it explicitly here.

---

## 0. Why this milestone exists

On 2026-09-18 a question was typed into this app for the first time in its life. It was
`Image enchantment` — a misspelling, meaning *which model best polishes a profile photo*. Three
things happened, and only the third is a problem:

1. **The on-device model understood it.** Tier 1 ran inside the simulator, matched a misspelled
   word the wording tier has no term for, and recognised the question as image editing.
2. **It refused honestly.** It emitted the decline sentinel and the screen said the catalogue does
   not measure this. The control built at M11-W3 and disclosed at M13-W3 worked exactly as designed.
3. **There was nothing to answer with.** From the reader's side, a correct refusal is still a
   refusal. **That is what this milestone is for.**

The routing problem is solved. The catalogue problem has not been started.

### What is already true, measured rather than assumed

- **This particular gap is a COVERAGE gap, not a measurement gap** (handover §5, Finding 1). Image
  editing is publicly benchmarked with Elo. **LMArena is `cc-by-4.0` and clean**; Artificial
  Analysis's arena grants no redistribution right, which under this project's free-and-legal rule is
  operationally a prohibition (Finding 5). The remedy is ingestion, not invention.
- **A general-capability axis is real in our data** (PC1 = 0.806 on the largest complete block; 0 of
  2000 permutations came near it) **and it does not predict a held-out board well enough to print**
  (DeepSWE leave-one-out −0.104, worse than the mean). D-142 clause 5 keeps that bar.
- **`assistant` is already an Elo surface.** Adding a second Elo board is a shape this pipeline has
  shipped, not a new one. `src/app/clients/arena.py` exists.
- **The router hint for this surface already exists — as a REFUSAL.**
  `CategoryHints.unmeasuredHints[0]` reads *"edit a photo or a picture, make an image look better,
  draw or generate an image"*. Measuring editing without measuring generation and leaving that line
  whole would make the product claim one by refusing the other. §2 W2 owns the split.

### The trap this milestone exists to avoid

**Shipping a tenth surface that cannot rank anybody.** Every threshold in `CategorySpec` is sized on
the **ranked population** — models that reconcile to the registry *and* carry a price median — not
on the board. Calibrating against the board has produced wrong thresholds three times (W-037).
Image-editing models may price differently from text models, or not reconcile at all. **W1 measures
the ranked population before W2 is allowed to define a surface over it**, and if that count is too
small the honest outcome is to say so rather than to ship a ranking of four models.

---

## 1. Acceptance criteria (new REQ-IDs — copied into `docs/prd.md` AT THE WAVE THAT OWNS THEM)

| REQ-ID | Criterion | Verified by |
|---|---|---|
| REQ-SRC-010 | The image-editing board's licence is reviewed and recorded before any of its data is served | `docs/license-review-lmarena.md`, Stage-0 gate |
| REQ-SRC-011 | The ingest refuses a board it cannot attribute, and says which field is missing | new client tests + `test_sources.py` |
| REQ-IMG-001 | The ranked population of the image-editing surface is COUNTED and published in the wave record, before thresholds are chosen | W1 close, measured against `advisor.db` on a copy |
| REQ-IMG-002 | A tenth surface ranks on its own native scale; no score is blended across boards (D-105) | `test_categories.py`, `test_rank.py` |
| REQ-IMG-003 | The router routes an image-editing question to it, and **still refuses image GENERATION** | `FrontDoorTests.UnmeasuredQuestionTests`, `test_router_hints.py` |
| REQ-GAP-001 | Every decline sentinel is recorded on the device, with the question, and NOTHING leaves the device | `RouterBoundaryTests`, plus the D-126 data-flow assertion extended to the new store |
| REQ-GAP-002 | The owner can read the gap register in the app, ordered by how often each gap was hit | `FrontDoorTests`, and a run |
| REQ-SCR-001 | Every ranking row carries a score, and no card or row shows the metric's name | `ScoresTests.swift`, `test_ios_client_contract.py` source contract |
| REQ-SCR-002 | The conversion is per surface and strictly monotonic: it never reorders a ranking | property test over every served board |
| REQ-SCR-003 | No surface's 100 is taken from the current board's maximum | `test_categories.py`, and a mutant that swaps the pinned anchor for the board max must fail |
| REQ-SCR-004 | The tie margin is converted with the score, and rank ranges are re-derived from it | `UncertaintyTests.swift`, property over every margin |

---

## 2. Waves

### W1 — The licence, the board, and the population (risk: **HIGH**)

No product surface ships in this wave. It answers the two questions that decide whether W2 is
possible at all.

- Stage-0 licence review for the LMArena image-editing board, recorded as
  `docs/license-review-lmarena.md`. **If the grant is not clean, the wave stops here and the
  milestone re-plans** — this is the Finding 5 trap and it has already caught one source.
- An ingest client for the board, in the shape of `clients/arena.py`, registered in
  `workflows/sources.py` with its attribution.
- **Then count.** How many models on that board reconcile to the registry AND carry a price median?
  That number goes in the wave record before anybody picks a threshold (REQ-IMG-001).

### W2 — The tenth and eleventh surfaces, from the boards we already pay for (risk: **HIGH**)

**Re-planned 2026-09-18 after W1.** The wave was written around image editing; the owner's amended
ruling puts two text-model boards first, because they need no pricing work at all.

**Measured before choosing, as W1's stop condition requires.** Ranked population — models on the
board that reconcile to the registry AND carry a price median — counted against `advisor.db`:

| Board | Reader's question | Ranked population |
|---|---|---|
| `document` | *which one is best with documents* | **27** |
| `text_factuality` | *which one makes things up least* | **20** |
| `search_factuality` | *which one is most accurate when it searches* | 24, **but see below** |

For scale, the shipping `coding` surface ranks 44. These are not thin boards.

**`search_factuality` is deliberately NOT in this wave.** Its entries are named `gpt-5.5-search`,
`claude-opus-4-6-search`: retrieval SKUs sold separately and priced differently. Reconciling the
SCORE to the base model is defensible — it is that model doing the task — but the PRICE would then
be the base model's, which is the W-092 defect shape on a third axis and the boundary MINOR-2 in the
W1 review already named. It ships when the SKU axis is decided, alongside the image price basis.

- Two `CategorySpec` entries, each ranking on its own native Elo scale, thresholds calibrated on the
  population measured above and written up the way `docs/reviews/m8-category-calibration.md` is.
- Reader-facing titles in the words a person uses, not the board's name.
- `CategoryHints.byID` gains both. The hint list is guarded by `test_router_hints.py`, which fails
  until a served surface has a hint — that guard working is the gate for this wave.
- Registry drift surfaced by the same measurement and fixed here: 8 models on these boards
  (`muse-spark` family, `gpt-6-astra`, `kimi-k3`, `gemma-4`, `qwen3.7-plus`, `glm-5.3`) have no rule
  and no price. They are ordinary drift, counted, and a rule is only added where live data carries
  BOTH a score and a price — the standard the rule table already sets for itself.
- The M10 calibration probe is re-run so no existing surface question falls out.

### W3 — The gap register (risk: **MED**)

The decline sentinel is the product's own demand signal and it is currently discarded (D-142 §3).

- Every `__none__` is recorded on the device with the question as typed and a count.
- **Nothing leaves the device.** REQ-RTR-004's data-flow test is extended to the new store; a mutant
  that ships a recorded question to the engine must fail it. This is the wave where D-126 is most
  likely to be broken by accident, which is why it is tagged MED and reviewed as though HIGH.
- A screen the owner can read, ordered by frequency: *this is what people asked for and we do not
  have it.* That list is the input to M15's coverage work.

### W4 — One score, out of 100 (risk: **HIGH**)

D-143. Tagged HIGH rather than MED: it touches the scoring path on every surface, every row and
every card, and the last time this project changed what a number MEANS it needed four review rounds.

- A per-surface conversion to 0–100, strictly monotonic, in `Uncertainty.swift` (D-138) — or D-138 is
  amended in this wave and its gate updated with it.
- **The anchor is data, not code.** Each `CategorySpec` carries what 100 means for its scale. A
  bounded percentage is the identity. Elo converts by its expectation against a **pinned** reference
  rating. A ceiling read from the current board's maximum is refused by a test, because it moves a
  model's score when a different model is added.
- **ECI is decided in this wave or it keeps rank-only.** D-143 deliberately does not decide it, and
  the wave may not invent an anchor for the sake of consistency.
- The tie margin converts with the score, and the rank ranges are re-derived from the converted
  margin. A property test over every margin, as REQ-UNC-001 already has.
- The metric name leaves the card and the rows. It stays available on the detail screen
  (REQ-DTL-001/002, the M13 council's ruling F2), which is where a reader who wants the unit finds it.
- Price re-enters here as a detail-screen attribute (§5 ruling 2). `/v1` does not move.
- **AMENDED 2026-09-20 at the W3/W4 review (D-146, proposed).** (a) Rank ranges stay on the engine's
  native margin: the conversion is monotonic, so the ties are identical, and a margin converted at
  one point of a curved scale is wrong at every other; the tie SENTENCE is restated in points on the
  /100 scale instead. (b) `/v1/categories` gains `score_anchor`, which the line above forbids; D-146,
  accepted by the owner 2026-09-20, allows it. (c) The anchor is its own `CategorySpec` field, not `min_quality`.
  (d) The last two bullets were not delivered in W4: W-098.

### W5 — Closure (risk: **LOW**)

Stage 4.0 independent seat, closure report, retrospective, EXPERIENCE, note.txt.

---

## 3. Shared contracts (K.8)

- **D-104, D-105, D-126 are untouched.** The router still may not say a model is good; scores are
  still never blended across boards; nothing typed leaves the device on any tier.
- **D-136 holds and is the answer to "the app should answer, not list":** `/v1` publishes the facts
  and the app writes the sentence. A tenth surface makes more questions answerable; it does not
  change who composes the sentence.
- `Uncertainty.swift` remains the only file allowed to do arithmetic on a served score (D-138).
- `/v1`'s payload shape does not move in W1–W3. A new surface is new DATA in an existing contract.

---

## 4. Definition of done

- `make check` exit 0, with `SWIFT_TEST_FLOOR` raised to the count it prints (W-091, owner's).
- Every wave close cites an independent review dated after the code it reviews.
- The licence is on record and the source registration cites it. For the LMArena boards that is the dataset-level CC-BY-4.0 grant reviewed at D-101 and cited in `src/app/clients/arena.py`; no per-board review is owed (M14-W2 review m5).
- The ranked-population count is in the W1 record, whatever it says.
- The gap register has been read by the owner on a running app at least once.

---

## 5. Decisions the owner made, 2026-09-18, in session

1. **Sign M13, or waive the prerequisite.** Also carried in from M13 §0 and still open: the refresh
   job (`launchctl kickstart`, exit 78, artifact dated 2026-08-27), D-141, and `SWIFT_TEST_FLOOR`.
   **RULED: sign M13 now.** The signature, `make check` and the milestone commit are the owner's own
   commands and are pending at the time this plan was ruled on. W1 may proceed in parallel; **no M14
   wave commit lands before M13's milestone commit does.**
2. **Price and budget** — your note reads *"we will remove cheaper, midprice and any price; we add
   it as a hidden-layer attribute."* Half of it already happened: M13-W3 deleted the budget strip
   and its client code; `/v1/budgets` was kept. What is left to rule on is the **server** side — the
   `budget` parameter, `eligible_count`, and `budget_pick`. Deleting them is a `/v1` contract change
   (K.8) and therefore yours. **Recommendation: keep the endpoint, stop asking the reader, and let
   price re-enter as an attribute on the detail screen.**
   **RULED: keep the endpoint, stop asking the reader.** `/v1/budgets`, `budget` and `eligible_count`
   stay in the contract untouched. The product does not ask a reader for a budget. Price returns as
   an attribute on the detail screen. No K.8 change in M14.
3. **The score in the ranking rows** — your note reads *"showing points in the ranking would be
   good; we will not put too much 'resolved' and so on."* M13-W4 shipped `Score 83.5 / 100` on the
   card. Does this extend to every ranking row, or does the row stay a name and a rank?
   **RULED, and it went further than the question asked: every row shows a score, and every score is
   converted to one 0–100 scale.** The owner's words, translated from Turkish: *"the aim here is that
   the end user should not have to know how the ranking and the scoring are done, or what the unit
   is. Let it show on all of them, but let us convert it — a simple conversion to how much it is out
   of 100 — and show that. 'Resolved' and the other measurement units: if somebody knows that much
   already, let them go and read the thousands of benchmarks, they will understand it from there.
   Ours has to be simpler. So we reduce it to a single scoring."* This amends D-140 and
   REQ-CMP-004 and is recorded as **D-143**. It owns W4 and it is the largest single change in this
   milestone.
4. **Splitting the app from the harnesses.** Your note asks for it, and D-142 makes it more
   pressing, not less: the ingest side is about to grow faster than the product side. **It is also a
   repository-level change that would touch every gate, every path in `.governed-records`, and the
   CI.** Recommendation: **do not do it inside M14.** Let W1 measure what a second source costs in
   practice, and make the split its own milestone with its own plan. Rule if you disagree.
   **RULED: not in M14. Its own milestone.**
5. **How far does "every benchmark in the world" go first?** D-142 sets the direction; this asks for
   the first step. Recommendation: **one surface, end to end, in M14** — the one your own question
   landed on. A second and third follow in M15 from the gap register's own ordering, which is
   evidence rather than guesswork.
   **RULED 2026-09-18 (first answer): one surface, end to end — image editing.**

   **AMENDED the same day, after W1 measured the population at zero.** The owner was shown that
   the image-editing surface is blocked on a price basis this product does not have, and that the
   SAME already-licensed dataset carries boards of ordinary text models — already in the registry,
   already priced. He ruled: **open the text-model boards first, and hold the image pricing
   decision.** Image editing is not cancelled; it waits behind a decision he chose not to make yet,
   and the gap register (W3) is what will inform it.

6. **The image price basis — HELD, by the owner, 2026-09-18.** The question stands as W1 left it:
   extend pricing to a per-image basis, or drop the rule that the engine only ranks models somebody
   can buy. He chose to defer rather than answer, with the reasoning that the gap register should
   inform it. **W2 no longer waits on it.**

---

## 6. What this milestone is NOT

- **It is not the derived layer.** D-142 clause 4 reopens the research; clause 5 says a derived
  estimate does not reach a card until it beats printing the mean on a held-out board. No wave here
  ships one.
- **It is not a rewrite of the router.** Tier 1 works. Tier 2 is the product for every device below
  an iPhone 15 Pro and stays first-class.
- **It is not the device build or the non-localhost engine.** note.txt lists both for M14; they are
  deferred to a wave of their own or to M15, because a milestone that changes the deployment and the
  catalogue at once cannot attribute a regression to either.
