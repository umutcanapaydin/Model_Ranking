---
record_type: wave
id: m14-wave-4-close
status: draft
process_version: v5.0
date: 2026-09-20
---
# Wave-Close Checklist — M14 Wave 4 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**One score, out of 100 (D-143).** Percentages are shown as they are; an Elo score is shown as how
often people would prefer the model over one at the surface's pinned anchor; ECI stays rank-only.
The sentences on the card and the tie note speak the same /100 scale.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m14-plan.md` §2 W4 "(risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `test_every_score_on_screen_goes_through_the_figures_line` went red on the first `leader:` argument and was widened by name; Python `912 passed, 13 skipped` | ✅ |
| 3 | Review per tier: HIGH → Code-Reviewer + Tester separately | Code-Reviewer: `docs/reviews/m14-wave-3-4-review.md` (`seat: independent`), 1 BLOCKING / 4 MAJOR, dispositioned. **Tester seat not convened — ledger L1** | WAIVED |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | Section (B) of `docs/reviews/m14-wave-3-4-review.md`; S-4 (anchor bound) fixed | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | The seat's M-4 mutant (board-max anchor on the rows) now fails `tests/unit/test_ios_client_contract.py::test_the_screen_calls_the_uncertainty_functions_it_depends_on`; a recalibrated floor moving the anchor fails `test_a_recalibration_cannot_move_the_anchor` | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-SCR-001..004 in `docs/prd.md`, each cited; the anchor through `/v1/categories` in `tests/unit/test_uncertainty_contract.py::test_every_elo_surface_publishes_its_pinned_score_anchor` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | Anchor sanity: `ScoresTests.swift::testAnUnreasonableAnchorIsRefused` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; every mutant ran on a copy of `tests/unit/test_ios_client_contract.py` or `ios/ModelRanking/Engine/Uncertainty.swift`. No commit made — L3 | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | In `ios/ModelRanking/Engine/Uncertainty.swift`: producers of a displayed /100 number: `scoreOutOf100` via `scoreText` via `figuresLine` (PickRow, RankedRow); of a /100 distance: `distanceOutOf100` via `anchoredFact` and `leaderSentence`. Anchor producers: `CategorySpec.score_anchor` → `/v1/categories` only | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: conversion, pinned anchor, rows and cards, sentences. Amended: ties stay native (D-146 clause 3, `docs/decisions.md`). Not delivered: price and metric name on the detail screen — W-098. ECI: stays rank-only, as D-143 allows | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | **VARIANCE:** about 480 lines with the review round, across `ios/ModelRanking/Engine/{Uncertainty,Scores,Language,Models}.swift`, `ios/ModelRanking/ContentView.swift`, `src/app/workflows/categories.py`, tests | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 912 passed / 13 skipped, ruff check src tests, tree-sitter parse of every Swift file · Swift compile and make check: owner's runner, L4 · outcome: uncommitted; B-1 cleared by D-146 (accepted)` | WAIVED |

## Ledger rows

- **L1 — Tester seat not convened.** Owning milestone: M14 closure (Stage 4.0).
- **L2 — D-146 accepted by the owner 2026-09-20.** B-1 is cleared by that record.
- **L3 — no commit.** The owner makes the commits.
- **L4 — Swift not compiled by the author.** The owner's runner is the measurement.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-20 · Wave commit range:
`c0b71c6..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/Engine/{Uncertainty,Scores,Language,Models}.swift
                ios/ModelRanking/ContentView.swift · ios/EngineTests/ScoresTests.swift
                src/app/workflows/categories.py · src/app/adapter/main.py
                tests/unit/{test_uncertainty_contract,test_ios_client_contract}.py
                docs/{decisions,prd,warnings.ledger}.md · docs/plans/m14-plan.md

K.8 contracts:  /v1/categories gains optional `score_anchor` (number on Elo surfaces, null
                elsewhere) — D-146, accepted 2026-09-20. /v1/answers unchanged.
```
