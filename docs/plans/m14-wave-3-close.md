---
record_type: wave
id: m14-wave-3-close
status: draft
process_version: v5.0
date: 2026-09-20
---
# Wave-Close Checklist — M14 Wave 3 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The gap register.** A question the router declines is kept on the phone, with a count, and the
owner can read the list — most-asked first — from a tray button. Nothing recorded leaves the device.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m14-plan.md` §2 W3 "(risk: **MED**)", reviewed as HIGH | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device` red on the first draft's `outcome.unmeasured` gate after `recordsGap` landed, green after; Python `912 passed, 13 skipped` | ✅ |
| 3 | Review per tier: MED reviewed as HIGH → Code-Reviewer + Security | `docs/reviews/m14-wave-3-4-review.md` (`seat: independent`), dispositions appended. **Tester seat not convened — ledger L1** | WAIVED |
| 4 | *(plan-tag)* pulled-forward security pass | Run inside the same seat, section (B) of `docs/reviews/m14-wave-3-4-review.md`; S-1..S-3 fixed | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | The seat's two sorting mutants (C5) now fail `test_the_client_applies_no_ordering_of_its_own`; a `.manual` outcome recorded as a gap fails `GapRegisterHardeningTests.testOnlyARoutedUnmeasuredQuestionIsAGap` (Swift, owner's run) | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-GAP-001 → `FrontDoorTests.swift::GapRegisterHardeningTests` + `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device`; REQ-GAP-002 → `FrontDoorTests.swift::GapRegisterTests`; both in `docs/prd.md` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | "Nothing typed leaves the device" extended to the register: `test_the_gap_register_stays_on_the_device` refuses a network API in `FrontDoor.swift` and `client.` calls carrying `gaps` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; every mutant ran on a copy of `tests/unit/test_ios_client_contract.py` or `ios/ModelRanking/Engine/Uncertainty.swift`. No commit made — L3 | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Producers of a register entry: `GapRegister.record` (only caller `ContentView.ask`, gated by `recordsGap`); writers of the file: `GapRegisterStore.save` only | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Planned: record, keep on device, owner screen. Delivered: all three. Deferred: the owner reading it on a running app (`docs/plans/m14-plan.md` §4) — owner | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | About 260 lines with the review fixes, `ios/ModelRanking/Engine/FrontDoor.swift`, `ios/ModelRanking/ContentView.swift`, tests | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 912 passed / 13 skipped, ruff check src tests, tree-sitter parse of every Swift file · Swift compile and make check: owner's runner, L4 · outcome: uncommitted, unsigned` | WAIVED |

## Ledger rows

- **L1 — Tester seat not convened.** One independent seat did Code-Reviewer and Security together.
  Owning milestone: M14 closure (Stage 4.0).
- **L3 — no commit.** The owner makes the commits; `commit_m13_m14.sh` carries them.
- **L4 — Swift not compiled by the author.** No Swift compiler in either lane; the owner's `make
  check` through the runner is the measurement.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-20 · Wave commit range:
`c0b71c6..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/Engine/FrontDoor.swift · ios/ModelRanking/ContentView.swift
                ios/ModelRanking/Engine/Language.swift (three UI strings)
                ios/EngineTests/FrontDoorTests.swift
                tests/unit/{test_router_hints,test_ios_client_contract}.py
                docs/{prd,warnings.ledger}.md · docs/reviews/m14-wave-3-4-review.md

K.8 contracts:  none. The register is a file on the phone (Application Support/GapRegister/,
                excluded from backup, complete file protection); no server or /v1 change.
```
