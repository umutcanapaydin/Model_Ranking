---
record_type: plan
id: m15-plan
status: draft
process_version: v5.0
date: 2026-09-21
---
# M15 Plan — what people actually ask, and the screen that holds what M14 took away

**One sentence: M15 turns the product's coverage from a guess into a measurement, and pays the four
debts M14 closed with.** The gap register (M14-W3) starts reporting, the LMArena dataset's remaining
boards are read where they answer a real question, and the detail screen the card lost its unit to
finally exists.

**Cap:** 4 waves, ~2k net lines (`docs/closure-checklist.md` §B.0 cadence).

---

## 0. What the owner rules before W1 starts

Each of these is a question only he can answer, each has a recommendation, and each blocks something.

1. **The detail screen (W-105).** M14 took the metric name off every card and row on your ruling.
   The plan's mitigation — "it stays on the detail screen" — turned out to name a screen that does
   not exist. It is also where your own note puts the price ("hidden layer attribute").
   **Recommendation: build it in W2**, holding the unit, the price, the benchmark's name and its
   date. The alternative is to rule that the unit is gone for good and amend REQ-DTL-001/002 away.
2. **D-141, bypassed five times (W-106).** Ratify it and a HIGH wave cannot close without its
   security pass or a waiver written where the counter reads it; refuse it and W-090's
   `C2b-reviewed` marker comes off. **Recommendation: ratify.** M14 waived it twice more, and the
   closure seat found two things a security pass is exactly shaped to find.
3. **The two gates that only run on your machine (W-108).** CI lints less than `make lint` does, and
   45 tests need a database that is gitignored. **Recommendation: pin the ruff version in
   `pyproject.toml`, widen CI's lint to match the Makefile, and ship a tiny seeded artifact for the
   tests that need one.** All three touch `.github/` or the toolchain, which is your surface.
4. **Which floor rule is right for all eleven surfaces (W-094).** Today nine surfaces were
   calibrated on the ranked population and the two M14 surfaces on the whole board, by your D-145
   ruling, and the comment above the thresholds still states the opposite of the shipped numbers.
   **Recommendation: measure both rules on all eleven and rule once, in W1**, so one sentence
   describes the product.
5. **How far to go on coverage this milestone.** The full vision — 400–500 lists, a real-question
   corpus, our own leaderboards — is several milestones of work. **Recommendation: M15 buys the
   cheap half** (the dataset boards we already license, plus the first read of the gap register) and
   leaves corpus mining to M16 with a measurement in hand rather than an intuition.

---

## 1. What M15 inherits, with its evidence

| Debt | Where it came from | Owner ruling needed |
|---|---|---|
| The detail screen; REQ-DTL-001/002, REQ-IMG-002/003 homeless | `docs/warnings.ledger.md` W-105 | §0.1 |
| D-141 and five uncounted security-pass waivers | W-106; `docs/decisions.md` D-141 | §0.2 |
| `make lint` / `make test` only reproduce on one machine | W-108 | §0.3 |
| One floor rule for eleven surfaces | W-094 | §0.4 |
| Per-source carry-forward, ~30-day drop | `docs/decisions.md` D-144, as the owner amended it | no — build it |
| `search_factuality` and the retrieval boards | `docs/plans/m14-plan.md` §2 W2, deferred on retrieval-SKU pricing | in W1's measurement |
| Image pricing basis (per-image vs per-token) | `docs/plans/m14-wave-1-close.md` | comes back with W1's numbers |
| The app / harness split | the owner's note, M13 | ruled 2026-09-22: merge, not split (D-149); built in M16 |

---

## 2. The waves

### W1 — What we can answer, measured (risk: **MED**)

The milestone's measurement wave. Nothing ships to a reader.

- **Read the gap register for the first time.** It has been recording since M14-W3. Whatever it says
  is the first evidence this project has ever had about what its own readers ask and it does not
  measure. If it is empty, that is a finding too, and the wave says so rather than inventing demand.
- **Measure every remaining board of the dataset already licensed** — 22 boards, two read — on the
  same footing: distinct models, ranked population (reconciled AND priced), leader, spread, and the
  floor under BOTH candidate rules (W-094). One table, reproducible by `scripts/calibrate_board.py`.
- **Answer the retrieval-pricing question with numbers**, not a position: what a search-SKU model
  costs per query and whether the engine's per-token price can honestly rank it. Same for image
  pricing, which M14-W1 left open.
- **Output:** one record the owner rules from, and a shortlist of boards worth a surface.

### W2 — The detail screen (risk: **MED**, gated on §0.1)

- The screen a card opens into: the model, its score out of 100, **its unit and what the unit is**,
  the benchmark's name and date, the price in the form a reader can check, and the surface's floor.
  **AMENDED 2026-09-21 at the W2 review (M-4, W-112): the floor is NOT on the screen**, because
  `/v1/categories` does not publish `min_quality` and §3 below says a fact `/v1` does not carry is
  an ADR rather than a quiet addition. Everything else in this line shipped. The floor comes back
  with the owner's ruling, or the line goes.
- REQ-DTL-001/002 get real criteria and citing tests, and W-105 closes.
- `ContentView.swift` grows again, and it is the file with the least proof in the project — so this
  wave extends the source-contract tests as it goes rather than after, and the D-126 egress ban
  (W-099) covers every new file by name.

### W3 — The surfaces W1's measurement supports (risk: **HIGH**)

- New surfaces, chosen by W1's table, not by this plan: the candidates are `search_factuality`,
  `agent_tool_hallucination`, `agent_steerability` and `vision`, and the measurement decides.
- Same rules as M14-W2: one board, one source id, one benchmark label, refused if unattributed; the
  router gets a hint worded away from its neighbours AND a positive routing test (W-103's shape).
- **D-144 is built here**: a per-source carry-forward with the owner's ~30-day drop, so one
  upstream outage stops blanking a whole cycle.

### W4 — Closure (risk: **LOW**)

Stage 4.0 seat, closure report, retrospective, EXPERIENCE, the M16 plan — and a scoped proposal for
the app/harness split, written but not built. **Superseded 2026-09-22:** the owner ruled for one
application that also refreshes (D-149); W4 records it and M16 builds it.

---

## 3. Shared contracts (K.8)

- **D-104, D-105, D-126 untouched.** A score is never blended across boards; nothing typed leaves
  the device; the router still may not say a model is good.
- **`/v1` may gain fields, not change them**, and any new field needs its own ADR before it ships —
  D-146 is the precedent and the reason.
- `ios/ModelRanking/Engine/Uncertainty.swift` stays the only file allowed arithmetic on a served
  score (D-138).
- The detail screen is a READER of facts the engine already publishes. If it needs a fact `/v1` does
  not carry, that is an ADR, not a quiet addition.

---

## 4. Definition of done

- `make check` exit 0 on the owner's machine, with `SWIFT_TEST_FLOOR` at the count it prints.
- Every wave close cites an independent review dated after the code it reviews.
- **Every new surface has a positive routing test that runs the real embedding router** (W-103).
- W-105, W-106, W-108 and W-094 each end the milestone FIXED or ruled — not carried a third time.
- The gap register's first read is in a record, whatever it says.
- The criteria table in §1/§2 is diffed line by line at closure, not read (M14's retrospective).
