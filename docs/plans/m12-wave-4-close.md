---
record_type: wave
id: m12-wave-4-close
status: draft
process_version: v5.0
date: 2026-08-25
---
# Wave-Close Checklist — M12 Wave 4 (Turkish)

> **STATUS: CLOSED 2026-08-25.** The contract move, and the largest piece of the milestone. `/v1`
> publishes the FACTS behind each pick sentence; the client writes the sentence, in either
> language, from those facts alone.

## What the wave delivered

- **D-136** — the payload moves once, additively: `why_fact` and `trade_off_fact` beside the prose
  they explain.
- **The prose is DERIVED**, not parallel. `trade_off_facts()` computes once and
  `trade_off_sentence()` composes from it — after the derivation test caught the two halves
  disagreeing on its first run.
- **`ios/ModelRanking/Engine/Language.swift`** — both languages composed from the facts, plus the
  screen's own chrome as a string table. The distinction is the point: a table for text carrying
  no values, composition for sentences that quote numbers.
- **A flag switch** that survives a relaunch, and **Turkish across the whole screen** — titles,
  surfaces, budgets, pick badges, placeholders, scales, prices, units.
- **`L1` reads prose** (GPF-008 closed in the field, fourth occurrence).

**Measured at the closing tree:** `make check` exit **0** · **781 Python passed / 12 skipped**
(747 at wave start) · **121 Swift tests** (97 at start) · `check_records` PASS across 71 records ·
`wave-check-all` PASS · **6 mutants, 6 killed**.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded — V3C-78 | `docs/plans/m12-plan.md` §3 records W4 **HIGH** — a contract move, and 551 unexecuted SwiftUI lines behind it | ✅ |
| 2 | Dev-test loop ran — V3C-68 | Implement → screenshot the running app in BOTH languages → fix what the screenshot showed → test. `English units inside Turkish sentences` was found that way | ✅ |
| 3 | Review per tier — V3C-78 / K.7 | `docs/reviews/m11-council-senior-mobile.md`, `seat: independent` — its recommendation shaped where the composition lives | ✅ |
| 4 | Fault injection — V3C-72 | 6 mutants, 6 killed over `ios/ModelRanking/Engine/Language.swift`, `src/app/workflows/recommend.py`, `src/app/adapter/main.py`; md5 restore verified | ✅ |
| 5 | Every criterion has a citing test able to fail — V3C-02 | REQ-LOC-001: `tests/unit/test_why_facts.py` (34 cases) and `ios/EngineTests/LanguageTests.swift` | ✅ |
| 6 | New REQ-IDs in the PRD at the wave | `docs/prd.md` REQ-LOC-001 | ✅ |
| 7 | Gates green at the closing tree | `make check` exit 0 · 781 passed / 12 skipped · 121 Swift · `scripts/check_records.py` PASS (71) · `scripts/wave_check_all.py` PASS | ✅ |
| 8 | ADRs for decisions made | `docs/decisions.md` **D-136** — the payload's second recorded move, additive, with its scope stated | ✅ |
| 9 | Warnings ledger current | `docs/warnings.ledger.md` — W-084, W-085, W-086 raised and **FIXED**; GPF-008 closed in the field | ✅ |
| 10 | Plan promises delivered | `docs/plans/m12-plan.md` §W4. The notices are NOT localised and D-136 says so in its own scope paragraph | ✅ |

## The three findings this wave should be remembered for

**1. Two parallel computations that agree today are two sources of truth.** D-136's whole claim is
that the prose is derived from the fact. The first implementation computed both from the same
inputs in two places — and did not even manage to agree today: the sentence said `3x cheaper`
beside a fact carrying `3.1`, so a client composing from the fact would have written a different
sentence than the engine shipped. Two more followed (`84` beside `84.4`, `6` beside `6.0`). The
derivation test caught all three on its first run, which is the only reason this wave did not ship
a silent divergence between two languages.

**2. Rounding the claim is not the same as rounding the display.** The budget-pick sentence printed
`84 points` for a floor of `84.4`. Fixing the disagreement by rounding the FACT was the obvious
move and the wrong one: the bar really is 84.4, and `84` states a bar the engine does not apply.
The claim stopped being rounded instead.

**3. A test that pins WHERE logic lives fails when it moves and passes when it is deleted from the
place it moved to.** Third occurrence in two waves — a literal phrase, a 600-character window, and
a grep for a comparison that had moved into a tested function. Each cost a red gate. Pin the claim
and the audience, never the offset.

## What is NOT closed

- **The notices are not localised** — staleness, effort mix, undated evidence, near-ties,
  unavailable surfaces. D-136 scopes them out in its own text rather than leaving a Turkish reader
  to discover it. They are disclosures, they are longer, and doing them badly is worse than later.
- **The Turkish flag was never tapped by a human.** The switch is proven by tests and by forcing
  the stored setting; synthetic taps do not land reliably on this control.
- W-074 (no shell linting) — declined by the owner, open.

---

Touched: `docs/decisions.md`, `docs/gp-field-findings.md`, `docs/plans/m12-wave-4-close.md`, `docs/prd.md`, `docs/warnings.ledger.md`, `ios/EngineTests/LanguageTests.swift`, `ios/ModelRanking/ContentView.swift`, `ios/ModelRanking/Engine/EngineClient.swift`, `ios/ModelRanking/Engine/Language.swift`, `ios/ModelRanking/Engine/Models.swift`, `ios/ModelRanking/Engine/Router.swift`, `Makefile`, `scripts/check_records.py`, `src/app/adapter/main.py`, `src/app/workflows/recommend.py`, `tests/unit/test_ios_client_contract.py`, `tests/unit/test_why_facts.py`

K.8 contracts: **the `/v1` answer payload MOVED** — `why_fact` and `trade_off_fact` are new, additive, under D-136; every existing field is byte-identical. `PUBLIC_PICK_FIELDS` grew by two. `L1`'s scope narrowed to prose. Frozen surfaces untouched: D-104 (the engine still decides every number; the client only chooses words), D-127, the refresh exit codes.

Filled by: the lead agent (Claude, Claude Code CLI) · Date: 2026-08-25 · Wave commit range: `2e6c09d..HEAD`
