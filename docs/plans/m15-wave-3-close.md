---
record_type: wave
id: m15-wave-3-close
status: draft
process_version: v5.0
date: 2026-09-22
---
# Wave-Close Checklist — M15 Wave 3, the surfaces the measurement chose (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**Three surfaces from W1's measurement: `vision`, `search`, `search_factuality`.** Each ranks only
its own board on its own Elo scale, with thresholds from the rules the product ships, attribution,
Turkish titles, and a router that can reach it (D-147, after the hints broke seven probe routes).

**This record is written at M15-W4, after the wave was committed (`d8cd650`), and its review ran
after the commit too.** A HIGH wave closed with no review, no Tester pass and no record; that is a
K.7 bypass and it is W-120. Stated rather than back-dated.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m15-plan.md` §2 W3 "(risk: **HIGH**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Router probe red (11/18) → D-147 → 21/21 probe, 18/22 held-out, `docs/reviews/m15-router-recalibration.md`. `make check` at `d8cd650`: 951 passed / 12 skipped, Swift 257 | ✅ |
| 3 | Review per tier: HIGH → independent Code-Reviewer AND Tester | `docs/reviews/m15-wave-3-review.md` (`seat: independent`, 2026-09-22, **retroactive**): **BLOCKING**, 2 BLOCKING / 3 MAJOR / 6 MINOR / 2 NIT, 16 mutants, 5 survived. Dispositions below; both BLOCKINGs fixed and their mutants re-run dead (W-117) | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | `docs/reviews/m15-closure-security-review.md` (`seat: independent`), which discharges D-141 for this wave — **after the commit, not before it** (its MINOR-3) | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | The seat's 16 mutants (row 3). After the fixes: M7 (`vision` on the chat board) and M9 (`vision` floor 60→20) re-run and die; M5 and M8 (thresholds moved) die on `tests/unit/test_categories.py::test_the_m15_surfaces_ship_the_thresholds_their_calibration_record_states`. M16 (image-reading questions back in the decline hint) still survives: W-118, M16-W1 | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-SUR-002: `tests/unit/test_categories.py::test_a_board_only_reaches_its_own_surface_through_the_ranking_query`, now over every Arena surface (W-117); routing: `ios/EngineTests/FrontDoorTests.swift::testTheTwoNewSurfacesAreReachableByAsking`, real router, **qualified** by review m-4 (its questions paraphrase the examples; held-out questions move into Swift in M16). REQ-SUR-003: `tests/unit/test_arena_client.py::test_an_unregistered_board_is_refused_and_never_defaulted` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None new in this wave; the D-126 gate it ran under (`tests/unit/test_router_hints.py`) was rebuilt at W4 (W-121) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | W-114 is the opposite failure: a file WRITTEN from a stale copy deleted eleven strings. Fixed, with `tests/unit/test_ios_client_contract.py::test_every_screen_string_the_client_calls_exists` | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Producers of a board's rows: `src/app/clients/arena.py::ARENA_BOARDS`, one source id and one benchmark each, asserted over the whole table in `tests/unit/test_arena_client.py` | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Delivered: three surfaces, D-147. **Dropped without a record at the time:** D-144's carry-forward (W-116, found at W4, owner deferred to M16). Deferred with a record: the router floor (W-118), the search price disclosure (W-119), the real-API contract test (added at W4, `tests/integration/test_arena_openrouter_contract.py`) | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | `git diff --stat 93686df d8cd650`: 28 files, +779/-54, larger than 400 with the router examples and the probe; **VARIANCE noted** — about half is D-147 and `scripts/router_probe/` | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `BYPASSED: K.7 at the wave's close (W-120), discharged retroactively · gates at d8cd650: pytest 951/12, swift 257 · outcome: committed d8cd650, findings fixed at W4` | ✅ |

## The review's findings, disposed

| Finding | Disposition |
|---|---|
| B-1 isolation test missed the new surfaces | FIXED, W-117 |
| B-2 floor assertion loosened to admit them | FIXED, W-117 (pinned per board) |
| M-1 router floor not re-measured under D-147 | ACCEPTED to M16-W1 on the owner's ruling, W-118 |
| M-2 search call not priced | ACCEPTED to M16 on the owner's ruling (state it), W-119 |
| M-3 no review, no close | FIXED retroactively, W-120; this record |
| m-1 thresholds unpinned | FIXED: `PINNED_M15_THRESHOLDS` in `tests/unit/test_categories.py` |
| m-2 no real-API contract test | FIXED: `test_every_m15_arena_board_satisfies_the_parser_contract`, run live once (3 passed) |
| m-3, m-4 router regression and held-out tests | M16-W1 with W-118 |
| m-5 calibration not reproducible from the repo | FIXED: command lines in `docs/reviews/m15-category-calibration.md`, record ratified |
| m-6 W-113 test did not reach `main()` | FIXED (W-113 row, corrected) |

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-22 · Wave commit range:
`93686df..d8cd650`, findings fixed in the M15-W4 tree

## Wave footprint — RECORD ONLY

```
Touched:        src/app/clients/arena.py · src/app/workflows/{categories,sources,rank}.py
                ios/ModelRanking/Engine/{Router,Language}.swift · ios/EngineTests/FrontDoorTests.swift
                scripts/calibrate_board.py · scripts/router_probe/ (new) · tests/unit/*
                docs/reviews/{m15-category-calibration,m15-router-recalibration}.md · docs/decisions.md (D-147)
K.8 contracts:  /v1/categories gains three surfaces through the existing shape; no field added.
```
