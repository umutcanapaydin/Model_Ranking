---
record_type: wave
id: m14-wave-5-close
status: draft
process_version: v5.0
date: 2026-09-21
---
# Wave-Close Checklist — M14 Wave 5, closure (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**Closure.** The Stage 4.0 independent seat read the whole milestone, returned **BLOCKING** on two
findings no gate in the tree could see, and both are fixed with the mutant that exposed them re-run.
This record closes the wave that fixed them and carries the milestone into the owner's signature.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m14-plan.md` §2 W5 "(risk: **LOW**)" — closure only; the two fixes it carries are MED, reviewed as the seat's own re-run | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Red-first on both blockers: the seat's `URLSession` mutant in `ios/ModelRanking/ContentView.swift` fails `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device` and passes when reverted; the `spec.min_quality` mutant in `src/app/adapter/main.py` fails `tests/unit/test_uncertainty_contract.py::test_the_served_anchor_does_not_follow_a_moved_floor` | ✅ |
| 3 | Review per tier: milestone closure → Stage 4.0 independent seat | `docs/reviews/m14-closure-review.md` (`seat: independent`, 2026-09-21): 1 BLOCKING, 8 MAJOR, 11 MINOR, 2 NIT, 11 mutants, all dispositioned in that record | ✅ |
| 4 | *(plan-tag)* Security pass at closure (BLOCKING, before deploy) | The seat's B-1 was the security finding and it is fixed; the D-126 boundary test now covers `ios/ModelRanking/ContentView.swift` as well as `FrontDoor.swift`. The two waived per-wave passes are counted in `docs/warnings.ledger.md` W-106 | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | Four mutants re-run by the author on copies: view-level egress (now dies), served anchor from the floor (now dies), `document.primary_source` → `arena` (now dies), bogus frontmatter in `docs/research/` (now dies) | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | `docs/coverage-by-req.md` §M14, twelve rows, each naming the test and what it would fail on | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | REQ-GAP-001's negative test widened to the whole view; `tests/unit/test_refresh_job_install.py` is the negative half of "the job can be installed" | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; every mutant ran on a copy and was restored byte-identically | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Egress producers in the client: `ios/ModelRanking/Engine/EngineClient.swift` only — the ban in `tests/unit/test_router_hints.py` now enumerates the five spellings that could add another. Anchor producers: `src/app/workflows/categories.py::CategorySpec.score_anchor` → `/v1/categories` | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: the seat, both blockers, six MAJOR fixes, the closure records. Escalated to M15: `docs/warnings.ledger.md` W-105, W-106, W-108 | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | ~390 lines, almost all tests and records; the code change is two comments and `scripts/enable_refresh.sh` | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: pytest 918 passed / 13 skipped, ruff check src tests, check_records, wave_check_all, conformance_gate, tree-sitter parse of every Swift file · Swift compile and the full make check: the owner's runner, L1 · outcome: uncommitted, unsigned` | WAIVED |

## Ledger rows

- **L1 — Swift not compiled by the author.** No Swift toolchain in either agent lane. Two Swift
  changes this wave: one new test (`testTheTwoNewSurfacesAreReachableByAsking`) and nothing else.
  The owner's `make check` is the measurement, and the new test is the one thing in this milestone
  that could legitimately come back red — it runs the real embedding router against the two new
  surfaces' hints (`docs/warnings.ledger.md` W-103).
- **L2 — three escalations leave the milestone unresolved on purpose:** W-105 (four carried
  requirements with no home, including the detail screen that does not exist), W-106 (five waived
  security passes and D-141 still proposed), W-108 (two gates that only reproduce on the owner's
  machine). Each names M15 and each needs an owner ruling, listed in `docs/plans/m15-plan.md` §0.

Filled by: lead agent (Claude Code, cloud lane, D-117) · Date: 2026-09-21 · Wave commit range:
`fc7fe5b..<uncommitted>`

## Wave footprint — RECORD ONLY

```
Touched:        tests/unit/{test_router_hints,test_categories,test_uncertainty_contract}.py
                tests/unit/test_refresh_job_install.py (new)
                scripts/enable_refresh.sh · scripts/install_refresh_wrapper.sh (new)
                src/app/workflows/categories.py (comment) · src/app/adapter/main.py (comment)
                ios/EngineTests/FrontDoorTests.swift
                .governed-records · docs/research/question-coverage-2026-09-18.md (frontmatter)
                docs/{decisions,prd,warnings.ledger}.md · docs/coverage-by-req.md
                docs/reviews/m14-closure-review.md (new) · docs/closure-report-m14.md (new)
                docs/retrospectives/m14-retrospective.md (new) · docs/EXPERIENCE.md
                docs/plans/{m14-wave-5-close,m15-plan}.md (new) · note.txt

K.8 contracts:  none this wave. `/v1/categories`'s `score_anchor` (D-146) is unchanged; only the
                comment beside it and the test that proves it is not the floor.
```
