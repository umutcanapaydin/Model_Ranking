---
record_type: closure
id: closure-report-m15
status: draft
process_version: v5.0
date: 2026-09-22
---
# Closure Report — M15: what we can answer, measured, and the screen that holds what M14 took away

> **Read §0 first.** It is what needs you. Everything below it is evidence for the claims in it.
> Every figure was measured at the closing tree: `8640202` plus the closure commit.

## 0. What needs the owner

1. **Rule on D-150 clause 2 (K.8).** K.8 reached its third acceptance and `check_records` passes
   only because W-112's row names D-150, whose clause 2 is still `proposed` (W4 review MINOR-3).
   The proposal: the rule held all three times, so keep it, and add a line to the plan template
   mapping every fact a new screen shows to its `/v1` field. **Recommendation: ratify.** If you
   refuse it, W-112 loses its marker and K.8 goes back under review.
2. **One correction you have already ruled on, stated here because it is about what you were told.**
   The first description of the Swift floor fix said a derived floor would catch a deleted test. It
   cannot. You ruled again on the correct description (a committed list of test names); D-150
   carries both texts.
3. **Nothing to build by hand this time.** `make check` does not compile `ContentView.swift` (M14's
   standing risk), so the agent built the app target of this exact tree with Xcode for the iPhone 17
   Pro simulator: `** BUILD SUCCEEDED **`, 2026-09-22. Opening it once on a device is still the only
   check of what a reader sees.
4. **Sign.** On your instruction the closure is committed and pushed under the agent's identity
   with its trailers (D-117); your sign-off is the line at the bottom of this report.

## 1. What M15 shipped

| | |
|---|---|
| **Every board of the licensed dataset, measured** | 22 boards on one footing: distinct models, the population the engine can rank, both candidate floor rules (W1). It answered W-094, and you ruled one floor rule for every surface (D-148). |
| **The detail screen** | Opened from any pick and any ranking row: the score, the unit the card hides, the benchmark and its date, the price in both forms, the tie margin (W2). W-105 closed. |
| **Three new surfaces** | `vision` (reading images), `search`, `search_factuality` — fourteen in all. Chosen by W1's count, not by the plan (W3). |
| **A router that can reach them** | W3's hints broke seven probe routes; D-147 routes on six example questions per surface. 21/21 on the probe, 18/22 on questions written before any tuning. |
| **A stronger privacy gate, honestly bounded** | Rebuilt three times after four seats. It reads raw source plus a normalized view, and permits file access only as exact expressions: 54 of 54 attempts die (W-121). It is still a gate over spellings; checking what the compiler resolves is M16-W1 (W-122). |
| **Two gates that run off your machine** | ruff pinned, CI lints what `make lint` lints, and the 45 artifact tests skip by name on a fresh clone while `make test` refuses to skip on yours (W-108). |

## 2. What it cost, and what it did not do

- **Two tie margins were wrong and are corrected.** A calibration script counted board NAMES as
  models, so `vision` read 64 where there are 41, and a model was paired with its own snapshot.
  On your ruling: `vision` 7.8 / 31.2 (was 8.1 / 32.3), `search_factuality` 4.9 / 19.5 (was
  4.2 / 17.0). No floor or anchor moved (W-113).
- **The HIGH wave closed with no review** (W-120, a K.7 bypass). Reviewed retroactively at W4:
  BLOCKING, two test gaps, both fixed (W-117).
- **Not done, and scheduled with your rulings:** D-144's carry-forward (W-116, M16); the floor on
  the detail screen (W-112, M16); the router's floor under D-147's scoring, which lets "what time
  is it" route to `vision` (W-118, M16-W1); the search call missing from the search surfaces' price
  (W-119, M16, "state it"); the Swift test list (W-111, M16).
- **The gap register said almost nothing:** one entry, your own test. It cannot say what people
  ask until strangers use the app (`docs/research/m15-gap-register-first-read.md`).
- Nothing deployed, eighth milestone.

## 3. The independent seats, and what they caught

| Record | Verdict | What no gate had caught |
|---|---|---|
| `docs/reviews/m15-wave-1-review.md` | PASS WITH FINDINGS, 0/2/6 | The survey named the wrong rule as "the one shipped" |
| `docs/reviews/m15-wave-2-review.md` | BLOCKING, 2/8/6/3 | A `URLSession` POST in the new screen passed the egress ban (W-110) |
| `docs/reviews/m15-closure-security-review.md` | PASS WITH FINDINGS, 0/1/5 | 10 of 12 privacy mutants passed the gate |
| `docs/reviews/m15-wave-3-review.md` | BLOCKING, 2/3/6/2 | `vision` pointed at the chat board passed every test |
| `docs/reviews/m15-wave-4-review.md` | PASS WITH FINDINGS, 0/3/5/4 | 11 new bypasses of the rebuilt gate; the false floor claim; a test that could not fail |
| `docs/reviews/m15-wave-4-rereview.md` | BLOCKING, 2/3/3/2 | 27 more ways past the privacy gate (markdown links, Handoff, file export); all closed, the class carried as W-122 |

Every finding is dispositioned in its wave close (`docs/plans/m15-wave-{1,2,3,4}-close.md`) and
the ledger (W-110..W-122).

## 4. Evidence

- **Gates at the closing tree:** `make check` exit 0 on the owner's Mac: pytest 956 passed / 15
  skipped (three live contract tests skip without `RUN_CONTRACT_TESTS=1`), coverage floor PASS, `check_records` PASS, `wave_check_all` PASS, `conformance_gate`
  PASS, `swift-test PASS: 258 test(s) (floor 258)`; Xcode Debug build of the app target, iPhone 17
  Pro simulator: BUILD SUCCEEDED. Live contract tests for the three new boards:
  3 passed (`RUN_CONTRACT_TESTS=1`).
- **Criteria trace:** `docs/coverage-by-req.md` §M15 — six rows, one PARTIAL (a stranger's wording
  reaching the new surfaces), one carried (REQ-IMG-002/003).
- **Decisions this milestone:** D-141 accepted, D-147, D-148, D-149, D-150 (clause 1 accepted as
  amended, clause 2 proposed).
- **Commits:** `17e6554` (W1), `93686df` (W2 + UI refresh), `d8cd650` (W3 + D-147), `8640202` (W4
  checkpoint + D-149), plus the closure commit. Range `855b44a..8640202`: 60 files,
  +4557/-174; the closure adds ~400 changed lines and ~800 new.

## 5. Carried into M16

`docs/plans/m16-plan.md`: one application with "update now" (D-149); the floors re-derived under
D-148; carry-forward (D-144); the floor on `/v1` and the detail screen (W-112); the search price
disclosure (W-119); the router's floor and held-out tests (W-118); the Swift test list (W-111); the
privacy gate on resolved declarations (W-122); and,
droppable, what people ask, from public prompt collections.

## 6. Architecture delta

M15 added no new component; it widened three existing ones. **The engine** reads three more
LMArena boards through the one client it already had: each board is a row in `ARENA_BOARDS` with
its own source id, benchmark label and truncation floor, and a surface is a `CategorySpec` naming
exactly one board, so a ranking never mixes scales (D-105). **The app** gained a detail screen that
composes nothing: `Detail.swift` turns facts `/v1` already publishes into labelled lines, and the
view only renders them, which keeps D-138 (one file does arithmetic on a score) and makes the
screen testable without Xcode. **The router** stopped comparing a question with one sentence per
surface and compares it with six example questions, scoring each surface by its two closest; that
made the new surfaces reachable, and it also moved every similarity onto a new scale, which is why
the 0.15 floor under it is now wrong (W-118). What a maintainer must know: the privacy promise on
the screen is held by a text gate over the client's source, not by the compiler — it now reads raw
text precisely because every smarter version of it was fooled — and anything that adds a way for
text to leave the phone must go through `EngineClient.swift` or change that gate in a reviewed edit.

---
*Generated from raw referents at closure. Owner sign-off: `<initials/date>`.*
