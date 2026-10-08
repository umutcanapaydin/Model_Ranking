---
record_type: wave
id: m20-wave-2-close
status: draft
process_version: v6.6
date: 2026-10-08
---
# Wave-Close Checklist — M20 Wave 2, many boards into one list

**One issue, as the milestone plan's W2 names it: #210.**

**What the phone can now do** (D-188 clauses 2 to 4, proposed).
- `combineFamily` combines a family of boards into one list by position, never by score (D-105). A
  model needs at least half of the family's boards, rounded up, and at least one. Its place is the mean
  of its percentile positions across the boards that rank it. Ties share a place and are broken by
  model id.
- Every board counts the same. A board more than 90 whole UTC days old, or undated, is named under the
  list. The first proposal's half weight went at the review: on the served boards it let Arena alone
  decide five families.
- A board the standings lack, or a model missing from the model list, is left out rather than failing
  the list.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m20-plan.md` §2 W2: **HIGH**, since `ios/ModelRanking/Engine/Combine.swift` is a security glob and the one file allowed arithmetic on positions (D-160 clause 2) | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | Every fix red first, a `test:` commit before its `fix:` commit: #210 (`1c8c9e0`, `d42a313`), the coverage measured at W1's review (`7ee9801`, `4f7fd8a`), the review (`fb0adfe`, `bc7f9f5`). The Tester ran each red commit on its own tree: each fails only on its own tests (`docs/reviews/m20-wave-2-tester.md`) | ✅ |
| 3 | Code-Reviewer and Tester as separate subagents, neither BLOCKING, each `**Independent:** yes` | `docs/reviews/m20-wave-2-review.md` (`70b8849`): **MINOR**, M1–M7, K1, R1, R2. `docs/reviews/m20-wave-2-tester.md` (`d47126e`): **MINOR**, M1–M4. Each seat had its own worktree, behind stubs refusing `fly`, `docker`, `launchctl`, `simctl` and `xcodebuild` | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass on this slice DONE | No pass per wave since D-172 (`docs/decisions.md`). The M20 closure seat reads this slice | N/A |
| 5 | Tester fault-injection, restore byte-identical | The Tester planted 32 faults in `combineFamily` and `isStale`: 18 caught as delivered, 31 with its 12 tests (`d47126e`); the one left changes code no input reaches (`Combine.swift`'s `continue` behind its filter). The review planted 4; the three that passed die on `fb0adfe`. Every file restored byte-identical (sha256) | ✅ |
| 6 | Every acceptance criterion touched has a citing test through the live entry point | REQ-CMB-002 and REQ-CMB-003 through `combineFamily` on standings shaped as `/v1/boards` serves them (`ios/EngineTests/FamilyCombineTests.swift`), including the property tests (permuting boards, an empty board, a model better everywhere). The Tester checked all 14 families on the served boards against an exact-fraction version of the rule | ✅ |
| 7 | New/changed security invariants with their NEGATIVE test | None changed. The new sort on means is the one permitted in `scripts/client_decl_gate.py` and `tests/unit/test_ios_client_contract.py` (Ruling A's tripwire) | N/A |
| 8 | No `git checkout`/`restore` on uncommitted work | None, and no stash. Every plant was made from Python and restored from saved bytes (`docs/reviews/m20-wave-2-tester.md`) | ✅ |
| 9c | Invariant hardening: producer list enumerated from code | The one producer of a combined position is `Combine.swift` (`combine`, `combineFamily`); the client-declaration gate refuses arithmetic on positions anywhere else | ✅ |
| 9b | Scope & draft PR | Delivered: #210. Filed: #216 (review K1). Draft PR on `wave/m20-w2` against `main`, stacked on `wave/m20-w1` | ✅ |
| 9a | Economy | `git diff --shortstat 1389d7d HEAD`: 10 files, 984 insertions(+), 11 deletions(-), of which the code is `Combine.swift` (96); the rest are tests (348), the two verdicts and the records | ✅ |
| 9 | Skipped/waived/bypassed ledger + run summary | `gates run: make check-fast (every commit) · make swift-test · make client-decls · make wave-check · gates SKIPPED: none · tokens/cost: not measured · outcome: shipped as a draft PR`. `make ui-test` was not run: no screen changed in this range (the screen is W4's). The per-wave security pass is not run by rule (D-172). Bypass: none | ✅ |

Filled by: lead agent (Claude Code, local lane) · Date: 2026-10-08 · Wave commit range: `1389d7d..HEAD`

## Review findings — each one fixed here, filed, or refused

| finding | disposition |
|---|---|
| review M1 | fixed `a9a52d6` |
| review M2 | fixed `bc7f9f5` |
| review M3 | fixed `fb0adfe` |
| review M4 | fixed `bc7f9f5` |
| review M5 | fixed `bc7f9f5` |
| review M6 | fixed `bc7f9f5` |
| review M7 | fixed `bc7f9f5` |
| review K1 | #216 |
| review R1 | fixed `bc7f9f5` |
| review R2 | fixed `bc7f9f5` |
| tester M1 | fixed `d47126e` |
| tester M2 | fixed `d47126e` |
| tester M3 | fixed `d47126e` |
| tester M4 | fixed `d47126e` |

## Wave footprint — RECORD ONLY, no rule attached

```
Touched:        docs/decisions.md docs/plans/m20-plan.md docs/prd.md docs/reviews/m20-wave-2-review.md docs/reviews/m20-wave-2-tester.md ios/EngineTests/FamilyCombineTests.swift ios/EngineTests/test-manifest.txt ios/ModelRanking/Engine/Combine.swift scripts/client_decl_gate.py tests/unit/test_ios_client_contract.py docs/plans/m20-wave-2-close.md
Mutant set author: the Tester seat (32) and the review seat (4); the author's plants are supporting evidence only
Observed RED:   the Tester's 13 reachable survivors die on its 12 tests (`d47126e`); the review's three on `fb0adfe` (a half weight, a shared position, the 90-day line)
Owner instruction: "Yes, of course, let's do it in M20; it's our biggest strength" (owner, 2026-10-08, translated from Turkish), on the app composing its own list per question from many boards
K.8 contracts:  no /v1 field or route changes; `combineFamily` and `FamilyList` are new in the Engine; D-188 clauses 2 to 4 amend D-167 clause 3 for families
Stopped at three attempts: NONE
Hand-kept lists: the permitted sorts in `scripts/client_decl_gate.py` and `tests/unit/test_ios_client_contract.py` (one entry each for the means)
```
