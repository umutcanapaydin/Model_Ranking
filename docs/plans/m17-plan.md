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

**Cap:** 5 waves, ~2k net lines. W5 is the one to drop if the milestone runs long.

---

## 0. What the owner rules before the wave that needs it

1. **The floors on fresh data (W-128), before W1.** D-148's floor is the top third of a board's
   rows, and six floors move on the fresh boards (`docs/plans/m16-wave-4-close.md` §9b). Options:
   re-derive them at each deliberate publish, from a table you read; or derive them in the build
   every night. **Recommendation:** at each deliberate publish. A floor that moves at night moves a
   Budget Pick with nobody looking, which is what D-148 §0.3 exists to prevent.
2. **The tie-margin rule (W-127), before W1.** Six Elo surfaces size their margins by interval
   overlap, which D-148 clause 2 does not name. **Recommendation:** amend clause 2 to name the
   interval rule for Elo boards; that rule measures what a board cannot tell apart.
3. **How a combined list says it is the product's own, before W3.** This is M16's carried question.
   **Recommendation:** every combined answer names the boards it used and their dates, says that the
   list is combined rather than published by any board, and ranks by position on each board, never
   by an average of raw scores (D-105).
4. **What leaves the phone, before W4.** D-104 says the typed question never leaves the device. The
   on-device model would turn it into a structured intent (task, domain, language, input size,
   constraints). **Recommendation:** only that intent's CODES reach the engine, from a closed list the
   engine publishes; free text never does. Under its own ADR, with the privacy gate extended to it.

---

## 1. What M17 inherits, with its evidence

| Debt | Where it came from | Owner ruling needed |
|---|---|---|
| The first artifact with derived models, published by hand | D-157; `docs/research/m16-w4-derived-registry-2026-09-23.md` | yours — after the launchd step |
| The launchd job retired (or reinstalled) | D-151, D-154; M16-W4 review MAJOR-1 | yours |
| The CI step that ages `data/epoch-source.yaml` removed | D-158 clause 4; the diff in PR #6 | yours (a workflow change) |
| Floors on fresh data | W-128 | §0.1 |
| The tie-margin rule | W-127 | §0.2 |
| About thirteen derived ids on reused or moving names | `docs/reviews/m16-wave-4-rereview.md` MINOR-1 | no — curated rules in W2 |
| What people ask, from public prompt collections | W-123 (moved from M16-W4) | which collections, after W5 lists them |
| The serving process loads the parsers; a stuck child after a hard kill | W-125, W-126 | no |
| Three data sources whose licences may not permit a commercial product | W-129 | kept and recorded; resolved before a commercial launch |
| Sources not yet read, ranked | `docs/research/source-expansion-2026-09-23.md` §6 | no |

---

## 2. The waves

### W1 — Arena's category slices (risk: **MED**)

The Arena data the product already licenses and downloads has 29 category slices, and the engine
reads only `overall`. W1 reads the ones that answer questions no surface answers today: legal and
government, medicine, finance, creative writing, instruction following, multi-turn, hard prompts, the
ten languages, and on vision `ocr` and `diagram`. They become BOARDS the engine can combine (W3), not
new surfaces yet. Same client, same licence, each slice declared with its own row floor and date.

### W2 — Epoch's own boards, and curation where derivation cannot see (risk: **MED**)

Epoch's CC-BY boards the engine does not read yet (`docs/research/source-expansion-2026-09-23.md`
§2.1), and `model_metadata.csv` as a FILTER, not a board: open weights, commercial use. Curated rules
for the derived ids that sit on reused or moving names (`claude-3.5-sonnet`, `deepseek-chat`, ...).

### W3 — The combination contract in the engine (risk: **HIGH**)

A `/v1` route that takes an intent's codes and answers with a list combined from several boards:
primary boards, secondary boards, and metadata filters, combined by RANK on each board, never by
averaging raw scores (D-105). Each answer names its boards and their dates (§0.3). ADR first, then
the route, then the tests that fail when two scales are mixed or a board goes unnamed.

### W4 — The question, read on the device (risk: **HIGH**)

Apple Intelligence (the on-device Foundation Models framework) fills a schema-constrained intent
from the typed question. The app sends only the intent's codes (§0.4) and shows the combined list
with the boards it used. The privacy gate on resolved declarations extends to the new path. The
router stays: it is the fallback when the on-device model is unavailable.

### W5 — What people ask, from outside (risk: **MED**, droppable)

M16's old W4: list public prompt collections with their licences (§1, W-123), classify a sample
against the surfaces and the intent schema, and report what share lands where. A record, not a
surface. Then closure: Stage 4.0 security seat, closure report, retrospective, EXPERIENCE, M18 plan.

---

## 3. Shared contracts (K.8)

- **D-104, D-105, D-126 untouched.** Nothing typed leaves the device; a score is never blended across
  scales; the router may not say a model is good.
- **`/v1` may gain routes and fields, not change them**, each under its ADR written before the wave
  that serves it.
- `ios/ModelRanking/Engine/Uncertainty.swift` stays the only file allowed arithmetic on a served score
  (D-138).
- A combined list is the product's own list and says so (§0.3); it never presents itself as a board's.

---

## 4. Definition of done

- `make check` exit 0 on the owner's machine; `make check-fast` is the working gate.
- Every wave close is written at the wave's close, cites an independent review dated after the code
  it reviews, and **no PR is merged while its review or `/pre-merge` is pending**: its body says
  "review pending, do not merge" on its first line until they are in (M16 retrospective, seed 1).
- The HIGH waves (W3, W4) have their security pass before their merge.
- W-127 and W-128 end the milestone FIXED or ruled.
- The launchd job is retired on the owner's machine, or the closure report says why not.
