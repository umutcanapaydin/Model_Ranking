---
record_type: wave
id: m15-wave-2-close
status: draft
process_version: v5.0
date: 2026-09-21
---
# Wave-Close Checklist — M15 Wave 2, the detail screen (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**Where a number comes from.** D-143 took the metric's name off every card and row on the owner's
ruling, and the M14 closure seat found the screen that was supposed to hold it did not exist
(W-105). It exists now: opened from any pick and from any row of the full ranking, composed in the
Engine from served facts, in both languages.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m15-plan.md` §2 W2 "(risk: **MED**, gated on §0.1)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first before the seat: a mutant stopping the ranking rows opening the screen fails `tests/unit/test_ios_client_contract.py::test_the_detail_screen_is_reachable_and_composes_nothing_itself`, green when reverted. `919 passed, 13 skipped` | ✅ |
| 3 | Review per tier: MED → independent Code-Reviewer | `docs/reviews/m15-wave-2-review.md` (`seat: independent`, 2026-09-21): **BLOCKING**, 2 BLOCKING / 8 MAJOR / 6 MINOR / 3 NIT, **37 mutants run, 26 survived the reviewed tree**. All dispositioned in that record; 12 fixed with the seat's own mutants re-run, 3 escalated | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | **WAIVED — `docs/warnings.ledger.md` W-106.** MED tier; the security-relevant half was reviewed inside the seat (B-1, the egress ban) and fixed. The standing waiver count stays at five and is the owner's to rule on | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted | The seat's surviving mutants re-run by the author after the fixes: egress inside `detailFacts` (dies), the row's door with `anchor: nil` (dies), `anchor:`/`closeCallMargin:` swapped (dies), a hand-built `Verdict` fact (dies), an invented "Independently verified" line (dies), a line contradicting the D-105 caveat (dies). Each reverted byte-identically | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-DTL-001 and REQ-DTL-002 in `docs/prd.md` §M15, each citing `ios/EngineTests/DetailTests.swift::DetailFactTests` for what the screen SAYS and `tests/unit/test_ios_client_contract.py` for the wiring `swift test` cannot see. **Qualified by W-111:** the Swift half runs only on the owner's machine and the floor that protects it is his to set | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | D-126's egress ban rewritten from a two-file list to every file under `ios/ModelRanking` with one named exemption (W-110); negative test verified red on the seat's mutant | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; every mutant ran on a copy and was restored | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Producers of a line on this screen: `ios/ModelRanking/Engine/Detail.swift::detailFacts` only — the view renders `fact.label`, `fact.value`, `fact.note`, `subject.model`, `subject.vendor` and `UIText.detailCaveat`, and the contract test now refuses any other `Text(...)` in it. Producers of an egress: `ios/ModelRanking/Engine/EngineClient.swift` only, enumerated by the ban | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: the screen, both doors, REQ-DTL-001/002 as criteria, W-105's detail half closed. Deferred with a record: the surface's floor (W-112, needs an ADR because `/v1` does not publish it). Escalated: the Swift floor (W-111) | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | ~430 lines including the review round: `Detail.swift` (new), `DetailTests.swift` (new), `ContentView.swift`, two test files, records. **VARIANCE noted:** about a third is the review round | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 919 passed / 13 skipped, ruff check src tests, check_records, wave_check_all, conformance_gate, tree-sitter parse of every Swift file · Swift compile and the full make check: the owner's runner, L1 · outcome: uncommitted, unsigned` | WAIVED |

## Ledger rows

- **L1 — Swift not compiled by the author.** No toolchain in either lane. Three Swift files changed
  and one is new; `ios/EngineTests/DetailTests.swift` carries 15 tests that have never run.
  **The owner's runner is the measurement, and W-111 is why it matters more than usual this wave:**
  the floor currently accepts a run that does not include them.
- **L2 — the wave was built before the owner's ruling.** `docs/plans/m15-plan.md` §0.1 asks him to
  choose between building the screen and dropping the unit for good; the recommendation was to
  build, he said to carry on, and this is the recommendation carried out. If he rules the other way
  the wave reverts as one commit.
- **L3 — no commit.** The owner makes the commits.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-21 · Wave commit range:
`855b44a..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/Engine/Detail.swift (new) · ios/EngineTests/DetailTests.swift (new)
                ios/ModelRanking/Engine/{Language,Models}.swift · ios/ModelRanking/ContentView.swift
                tests/unit/{test_ios_client_contract,test_router_hints}.py
                .language-allow · docs/prd.md (§M15) · docs/warnings.ledger.md (W-105, W-110..W-112)
                docs/plans/m15-plan.md (§2 W2 amendment) · docs/reviews/m15-wave-2-review.md (new)

K.8 contracts:  none. The screen reads facts `/v1` already publishes. The one fact it wanted and
                could not have — the surface's floor — is W-112, queued as an ADR rather than
                added quietly.
```
