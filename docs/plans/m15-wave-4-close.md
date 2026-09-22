---
record_type: wave
id: m15-wave-4-close
status: draft
process_version: v5.0
date: 2026-09-22
---
# Wave-Close Checklist — M15 Wave 4, closure (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The closure wave, and it was not a paperwork wave.** It fixed what the Stage 4.0 security seat
found (the privacy gate, non-finite ratings, the wording of the promise), made two gates reproduce
off the owner's machine (W-108), resolved W-113, reviewed W3 retroactively and fixed its two
BLOCKING test gaps, rebuilt the privacy gate a second time after its own review, and wrote the
milestone's records. Code landed in two parts: the checkpoint `8640202` and the uncommitted closure.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m15-plan.md` §2 W4 "(risk: **LOW**)". **Re-tiered by its content (V4C-50):** it rewrote a security invariant's gate, so it was reviewed at Code-Reviewer + Tester depth | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red-first: W-113 test red on each old behaviour restored in `main()`; `PINNED_ROW_FLOORS` red on floor 60→20; the isolation test red on `vision` → chat board; the privacy gate red on 54 of 54 attempts (script in the scratchpad, each file restored and hash-checked). `make check`: pytest 956 / 15, Swift 258 | ✅ |
| 3 | Review per tier: independent Code-Reviewer + Tester | `docs/reviews/m15-wave-4-review.md` (`seat: independent`, 2026-09-22): **PASS WITH FINDINGS**, 0 BLOCKING / 3 MAJOR / 5 MINOR / 4 NIT, 29 mutants, 13 survived. The fix round it caused was re-reviewed: `docs/reviews/m15-wave-4-rereview.md` (`seat: independent`, 2026-09-22): **BLOCKING**, 2 BLOCKING / 3 MAJOR / 3 MINOR / 2 NIT — the Python half held (11 of 12 mutants died, the twelfth now pinned); 27 new ways past the privacy gate. The plausible ones are closed and every attempt re-run dead (W-121); what a text gate cannot close is W-122, M16-W1 | ✅ |
| 4 | *(plan-tag)* pulled-forward security pass | Not owed at LOW; the wave's security content is the Stage 4.0 seat's remedy, `docs/reviews/m15-closure-security-review.md`, and row 3's seats re-ran that seat's mutants | ✅ |
| 5 | Tester fault-injection: break → RED → reverted | Row 3's seat: all 10 Stage 4.0 privacy mutants die on the checkpoint's gate, 0 of its 11 new ones did; after the second rebuild all 23, the re-review's 27 (as replicated by the author) and four more die: 54 of 54 (`docs/warnings.ledger.md` W-121). Threshold mutants C1/C2 and the W3 seat's M5/M7/M8/M9 die on the new pins | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | `docs/coverage-by-req.md` §M15, six rows; REQ-GAP-001 re-traced through `tests/unit/test_router_hints.py::test_the_gap_register_stays_on_the_device` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | D-126's gate rebuilt (W-121): raw-source scan, import allowlist anywhere in the text, exact-expression permissions, one typed `@AppStorage`, backup exclusion only `true`, no source outside the synchronized folder (`ios/ModelRanking.xcodeproj/project.pbxproj`). Non-finite and out-of-band ratings refused: `tests/unit/test_arena_client.py::test_a_rating_that_is_not_a_finite_number_is_refused_and_counted` | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None; every mutant ran on the file in place and was restored from a byte copy with a hash check, or in a reviewer's private copy | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | Ways off the device: enumerated as `EGRESS` over every file under `ios/ModelRanking`, with `EngineClient.swift` the one door and FrontDoor's seven exact expressions the only other permissions (`tests/unit/test_router_hints.py`) | ✅ |
| 9b | Scope: planned vs delivered vs deferred | Plan §2 W4: security seat, closure report, retrospective, EXPERIENCE, M16 plan — all delivered (`docs/closure-report-m15.md`). Added by findings: W-113, W-117, W-121, the retroactive W1/W3 closes. Deferred on the owner's rulings: W-111, W-112, W-116, W-118, W-119 to M16; the gate's class to M16-W1 (W-122) | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | `git diff --stat d8cd650 8640202`: 24 files, +913/-47; the closure adds ~400 changed and ~800 new lines, most of it records. **VARIANCE noted:** two review rounds and a retroactive one | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check (pytest 956/15, Swift 258), live contract tests 3/3, Xcode app build SUCCEEDED · outcome: checkpoint 8640202, closure committed and pushed on the owner's instruction, owner signs` | ✅ |

## The W4 review's findings, disposed

| Finding | Disposition |
|---|---|
| MAJOR-1 eleven bypasses of the rebuilt gate | FIXED on the owner's ruling to do it in M15, W-121 |
| MAJOR-2 D-150 clause 1 accepted on a false claim | FIXED: the owner ruled again on the correct description; D-150 amended, W-111 corrected |
| MAJOR-3 W-113's test could not fail | FIXED: `tests/unit/test_calibrate_board.py` runs `main()`; W-113 row corrected |
| MINOR-1 `categories.py` contradicts itself on margin sizing | FIXED: header scoped to the M8 surfaces; D-148 clause 2 checked in M16-W3 |
| MINOR-2 corrected thresholds unpinned | FIXED: `PINNED_M15_THRESHOLDS` |
| MINOR-3 C2b discharged by a proposed clause | Owner rules D-150 clause 2 at sign-off (`docs/closure-report-m15.md` §0.1) |
| MINOR-4 security MINOR-1 remedy partial | FIXED: `ELO_BAND` refuses finite ratings no Elo board carries; `/health` probe not added (M16 with D-149) |
| MINOR-5 survey keep-best untested | M16-W3, with the survey mode (`docs/plans/m16-plan.md`) |
| N-1..N-3 | FIXED (comments, calibration record, probe paths under `build/`) |
| N-4 W-108's "904 passed" | Historical: the figure was true for its tree; three tests were added after it |
| Re-review BLOCKING-1/2, MAJOR-2 (markdown links, hand-off surfaces, crash messages) | FIXED, W-121 |
| Re-review MAJOR-1 (spellings split by backticks, comments, aliases) | FIXED for every listed spelling by a second, normalized view and a `typealias` ban; the class is W-122 |
| Re-review MAJOR-3 (W-121's residual understated) | FIXED: W-121 restated, W-122 opened |
| Re-review MINOR-1 (deliberate obfuscation) | W-122 |
| Re-review MINOR-2 (false positives) | Accepted as the gate's cost: `self.init(` and `super.init(` are now exempt; `.padding(.init(…))` and prose such as "print (" still fail, and the message says why |
| Re-review MINOR-3, NITs | FIXED: `ELO_BAND` pinned; comment indent; trailing line |

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-22 · Wave commit range:
`d8cd650..8640202` plus the uncommitted closure

## Wave footprint — RECORD ONLY

```
Touched:        tests/unit/{test_router_hints,test_arena_client,test_categories,test_calibrate_board}.py
                tests/integration/test_arena_openrouter_contract.py · tests/conftest.py
                src/app/clients/arena.py · src/app/workflows/categories.py · scripts/calibrate_board.py
                scripts/survey_boards.py · scripts/router_probe/probe.swift · pyproject.toml · Makefile
                .github/workflows/ci.yml (owner-authorised, W-108) · ios/ModelRanking/Engine/{FrontDoor,Language,Router}.swift
                ios/EngineTests/FrontDoorTests.swift · docs/ (records)
K.8 contracts:  none. No /v1 field added; the two it needs are M16-W1 ADRs.
```
