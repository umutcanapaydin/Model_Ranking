---
record_type: wave
id: m12-wave-3-close
status: ratified
process_version: v5.0
date: 2026-08-25
---
# Wave-Close Checklist — M12 Wave 3 (the budget picker)

> **STATUS: CLOSED 2026-08-25.** The smallest wave of the milestone, and the one that makes a
> milestone of earlier work mean something. Until today the product called itself budget-aware and
> `ContentView.swift` held `private let budget = "unlimited"`.

## What the wave delivered

- **Three budget choices** under the category strip, with the caps `/v1/budgets` publishes — so the
  app does not hardcode what `low` means (D-134's whole purpose).
- **The captions carry the cap**: `Cheaper · under $2/1M`. A control showing only "Low" would be a
  second vocabulary a reader has to learn, which is the M12 finding applied to a new control
  before it ships rather than after.
- **`unlimited` stays the default.** A reader who has not said what they can spend has not asked
  to be limited.
- `scripts/simulator_session.sh` stops instructing the owner to use a control that did not exist.

**Measured at the closing tree:** `make check` exit **0** · **747 Python passed / 12 skipped** ·
**97 Swift tests** (88 at wave start) · `check_records` PASS across 70 records · `wave-check-all`
PASS · **3 mutants, 3 killed**.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m12-plan.md` §3 records W3 **LOW** — one control, over a payload built and tested at M11 | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → screenshot the running app → test the half a screenshot cannot show. `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/Router.swift`, `ios/EngineTests/EngineClientTests.swift` | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-council-product.md`, `seat: independent` — this wave is its lead finding **WAIVED — ledger row W-087.** Corrected at M12-W5: that review is dated 2026-08-24 and every commit in this wave is 2026-08-25, so it shaped the wave but did not read it (D-137). The independent read happened at Stage 4.0 and found two BLOCKING defects. | WAIVED |
| 4 | Fault injection — V3C-72 | 3 mutants, 3 killed on `ios/ModelRanking/Engine/EngineClient.swift` and `Router.swift`; md5 restore verified | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-BGT-001: `BudgetOptionTests` and `BudgetIsSentTests` in `ios/EngineTests/` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-BGT-001 | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · 747 passed / 12 skipped · 97 Swift · `scripts/check_records.py` PASS (70) · `scripts/wave_check_all.py` PASS · `scripts/conformance_gate.py` PASS | ✅ |
| 8 | ADRs for decisions made | None. `docs/decisions.md` D-134 (M11-W3) already ruled that the caps are published as a sibling resource; this wave is the consumer that ruling was for | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-083 raised and **FIXED**; **W-040 re-scoped** | ✅ |
| 10 | Plan promises delivered | `docs/plans/m12-plan.md` §W3 — all three items | ✅ |

## The finding this wave should be remembered for

**A milestone of work served a control that did not exist.** At M11-W3 this project published
`/v1/budgets` under a new ADR, wrote tests proving the served cap reproduces the served
`eligible_count` across three surfaces and two budgets on real data, rendered "See all 58 — 25 fit
your budget", and put "switch the budget" into the owner's own session script. Every one of those
is correct. None of them was reachable, because the app held the budget as a constant.

**It was found by a council seat reading one line.** Not by the tests, which were right; not by the
owner's two sessions, because a control that is absent shows nothing to notice; not by the author,
who had just spent a wave on the payload behind it. This is the M11 council's through-line — *a
thing asserted somewhere and exercised nowhere, each half locally correct* — arriving in the same
milestone that named it.

And the half worth testing separately: **a picker that updates state and sends the old value looks
identical on screen.** `BudgetIsSentTests` asserts the choice reaches the engine, because the
defect being fixed was precisely a value that never left the client.

## What is NOT closed

- **W-040 is re-scoped, not closed.** Whether the unfiltered ranking is too long is still the
  owner's judgement from the app — but until today every judgement he could have made was against
  the widest possible list.
- W-074 (no shell linting) — declined, open.

---

Touched: `docs/plans/m12-wave-3-close.md`, `docs/prd.md`, `docs/warnings.ledger.md`, `ios/EngineTests/EngineClientTests.swift`, `ios/EngineTests/OwnerSessionDefectTests.swift`, `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/EngineClient.swift`, `ios/ModelRanking/Engine/Models.swift`, `ios/ModelRanking/Engine/Router.swift`, `Makefile`, `scripts/simulator_session.sh`

K.8 contracts: the client now consumes `/v1/budgets`, which D-134 added at M11-W3 for exactly this. `BudgetOption` and `BudgetList` are NEW decodables over an existing payload; no engine surface moved. Frozen surfaces untouched: the `/v1` answer payload, D-104, D-127.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Wave commit range: `b63a89b..HEAD`
