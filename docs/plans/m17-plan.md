---
record_type: plan
id: m17-plan
status: draft
process_version: v6.0
date: 2026-09-23
---
# M17 Plan — lists nobody publishes

**One sentence: M17 widens what the engine measures and lets a question, read on the device, reach
a combination of boards, so the product can answer with a list that no single leaderboard
publishes.** The owner (2026-09-23, translated from Turkish): *"we cannot know what people will ask
... we will try to understand the question with different benchmarking data and bring out the
lists and data that are not in any list but can come out of combining them -- that is the app's
biggest feature."*

**Cap:** 5 waves, ~2k net lines. W3 is the one to drop if the milestone runs long.

---

## 0. Ruled by the owner, 2026-09-23 (in session, before any wave)

1. **Floors: derived from the board in every build (D-159)**, chosen over re-deriving at each
   deliberate publish. A Budget Pick may change overnight when a board grows; D-128/D-132 still guard.
2. **Tie margins: the interval rule is written into D-148** (amendment, W-127 FIXED). No number moves.
3. **A combined list is shown PLAIN** (D-160 clause 3), chosen over naming the boards on the list: the
   boards it came from and their dates are on the detail screen.
4. **Nothing leaves the phone** (D-160), chosen over sending the intent's codes. The engine publishes
   each board's standings; the phone's on-device model reads the question, and the phone combines the
   boards by position. D-138's arithmetic permission gains one named file.

---

## 1. What M17 inherits, with its evidence

| Debt | Where it came from | Owner ruling needed |
|---|---|---|
| The first artifact with derived models, published by hand | D-157; `docs/research/m16-w4-derived-registry-2026-09-23.md` | yours — after the launchd step |
| The launchd job retired (or reinstalled) | D-151, D-154; M16-W4 review MAJOR-1 | yours |
| The CI step that ages `data/epoch-source.yaml` removed | D-158 clause 4; the diff in PR #6 | yours (a workflow change) |
| Floors on fresh data | W-128 | ruled: D-159, built in W1 |
| The tie-margin rule | W-127 | ruled: D-148 amended; FIXED |
| About thirteen derived ids on reused or moving names | `docs/reviews/m16-wave-4-rereview.md` MINOR-1 | no — curated rules in W2 |
| What people ask, from public prompt collections | W-123 (moved from M16-W4) | M18 |
| The serving process loads the parsers; a stuck child after a hard kill | W-125, W-126 | no |
| Three data sources whose licences may not permit a commercial product | W-129 | kept and recorded; resolved before a commercial launch |
| Sources not yet read, ranked | `docs/research/source-expansion-2026-09-23.md` §6 | no |

---

## 2. The waves

### W1 — Floors from the board, every build (risk: **MED**)

D-159. The build derives each surface's floor under D-148 clause 1 through the one function
`survey_boards.py --floors` already uses; the artifact carries it; `/v1/categories` serves it.
`categories.py` keeps the rule, not the number, and `tests/unit/test_floor_rule.py` becomes a test of
the derivation. Closes W-128.

### W2 — Arena's category slices (risk: **MED**)

The Arena data the product already licenses and downloads has 29 category slices, and the engine
reads only `overall`. W2 reads the ones that answer questions no surface answers today: legal and
government, medicine, finance, creative writing, instruction following, multi-turn, hard prompts, the
ten languages, and on vision `ocr` and `diagram`. They become BOARDS a combination can use (W4), not
new surfaces. Same client, same licence, each slice declared with its own row floor and date.

### W3 — Epoch's own boards, and curation where derivation cannot see (risk: **MED**)

Epoch's CC-BY boards the engine does not read yet (`docs/research/source-expansion-2026-09-23.md`
§2.1), and `model_metadata.csv` as a FILTER, not a board: open weights, commercial use. Curated rules
for the derived ids that sit on reused or moving names (`claude-3.5-sonnet`, `deepseek-chat`, ...).

### W4 — Board standings to the phone, and the combination on it (risk: **HIGH**)

D-160 clauses 1-2. An additive `/v1` route publishes each board's standings (identity, date, each
model's position and price); the question never shapes the request. The Engine layer on the phone
combines chosen boards by POSITION, never by averaging raw scores (D-105), in one file the arithmetic
gate permits by D-160. The tests fail when two scales are mixed, when a board goes unnamed on the
detail screen, or when anything about the question reaches a request.

### W5 — The question, read on the device (risk: **HIGH**)

Apple Intelligence (the on-device Foundation Models framework) fills a schema-constrained intent
(task, domain, language, input size, constraints) that selects the boards W4 combines. The list is
shown plain; the detail screen names the boards and their dates (D-160 clause 3). The router (D-147)
stands in when the on-device model is unavailable. Then closure: Stage 4.0 security seat, closure
report, retrospective, EXPERIENCE, M18 plan.

**Moved to M18:** "what people ask" from public prompt collections (W-123), which the cap no longer
fits once W4 and W5 moved onto the phone.

---

## 3. Shared contracts (K.8)

- **D-104, D-105, D-126 untouched, D-160 added.** Nothing typed, and nothing derived from it, leaves
  the device; a score is never blended across scales; the on-device model maps a question to an
  intent and never states a score, a price or availability; the router may not say a model is good.
- **`/v1` may gain routes and fields, not change them**, each under its ADR written before the wave
  that serves it.
- Arithmetic on served numbers happens in the files D-138 and D-160 name, and nowhere else.
- A combined list is the product's own list; the detail screen says so (D-160 clause 3).

---

## 4. Definition of done

- `make check` exit 0 on the owner's machine; `make check-fast` is the working gate.
- Every wave close is written at the wave's close, cites an independent review dated after the code
  it reviews, and **no PR is merged while its review or `/pre-merge` is pending**: its body says
  "review pending, do not merge" on its first line until they are in (M16 retrospective, seed 1).
- The HIGH waves (W4, W5) have their security pass before their merge.
- W-127 and W-128 end the milestone FIXED or ruled.
- The launchd job is retired on the owner's machine, or the closure report says why not.
