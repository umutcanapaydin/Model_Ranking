---
record_type: wave
id: m13-wave-4-close
status: draft
process_version: v5.0
date: 2026-09-15
---
# Wave-Close Checklist — M13 Wave 4 (v4.1; V3C-69 + V3C-90/OD-4 + V4C-13 + V4C-40)

**The card says what a number is out of.** A bounded percentage reads `Score 83.5 / 100`, and an
Elo rating reads `Score 1504.2 Elo`. An ECI score is not printed; its rank range carries the
position, as the council's C1 ruling asked (D-140). The pick nobody budgeted for is no longer
called a budget pick. A price below a dollar no longer rounds to `$0`: the W3 simulator screenshot
had shown "about $0 per 1,500 pages of text" for a model at $0.13/1M. The detail screen and vendor
links moved to M14 under council ruling F2.

| # | Check | Evidence (fresh referent) | ✅/WAIVED |
|---|---|---|---|
| 1 | Risk tier recorded for this wave in the plan | `docs/plans/m13-plan.md` §2 — "W4 — The card, and what a tap opens (risk: **MED**)" | ✅ |
| 2 | Per-agent dev-test loop ran (implement → test → self-review → fix) | `make check` exit 0 at **the W4 tree itself**, 870 Python / 214 Swift. It was measured on a private copy built from `cda57b1` plus the W4 diff, because the working tree already carries the Stage 4.0 fixes, which are W5's. `xcodebuild` (iOS Simulator) exit 0 after the fix round. The W4 patch was first applied to a PRIVATE copy of `ios/` and passed 192 Swift tests there and `xcodebuild`, before it touched the repository. `apply_w4.py` refuses any edit whose old text has moved, and its dry run passed twice against the W3 tree. The running app on the simulator shows `Puan 83.5 / 100` and `UYGUN FİYATLI SEÇİM` on coding. On mathematics, DeepSeek V4 Flash reads `Puan 94.4 / 100 · $0.13/1M` and `1,500 sayfa metin için yaklaşık $0.13`, where the W3 build had printed `yaklaşık $0` | ✅ |
| 3 | Review per tier: LOW/MED → ONE combined reviewer | `docs/reviews/m13-wave-4-review.md` (`seat: independent`): **PASS WITH FINDINGS**, 1 MAJOR, 7 MINOR, 3 NIT. Then `docs/reviews/m13-wave-4-rereview.md` (`seat: independent`), on a fresh private tree with its own `xcodebuild`: **PASS WITH FINDINGS**, all eleven dispositions confirmed and three new NITs, each fixed in the wave (ledger L6) | ✅ |
| 4 | *(plan-tag)* HIGH slice: pulled-forward security pass | **WAIVED** — ledger L1. The wave is MED and client-only; the milestone's Stage 4.0 review covers it (`docs/reviews/m13-security-review.md`, `docs/closure-checklist.md` §B.2a) | WAIVED |
| 5 | Tester fault-injection: break → RED → reverted byte-identical; every stay-GREEN fault got a new test | `docs/reviews/m13-wave-4-review.md`, round 1: 18 of 22 mutants killed (81.8%). The four stay-GREEN survivors each got a test: C1 and C2 by `test_every_score_on_screen_goes_through_the_figures_line`, P2 by the exact Turkish sub-cent assertion, M3 by `testTheDollarBoundaryPrintsOneAmountOneWay`. `docs/reviews/m13-wave-4-rereview.md`, round 2 on a fresh tree: 31 of 33 (93.9%), every revert byte-identical by md5, all four round-1 survivors dead. Its two survivors each got a test after the round and were shown RED by the author: F2 fails `testARankOnlyScoreWithNoRankBesideItKeepsTheEnginesNumber` (`"150 % correct  ·  $2.06/1M"`), and C6 fails the contract test at `ContentView.swift:736` | ✅ |
| 6 | Every acceptance criterion has a citing test entering through the LIVE entrypoint | REQ-CMP-004: `ios/EngineTests/ScoresTests.swift::ScoreFormTests`, one test per metric family, each in both languages, against `figuresLine`. The two call sites that make it live are pinned by `tests/unit/test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line` (review MAJOR-1). The rename: `PickLabelTests`. The price: `CheapPriceTests` | ✅ |
| 7 | New/changed security invariants added with their NEGATIVE test | None. Client display only: the wave changes nothing under `src/`. The display invariant it adds is pinned by `tests/unit/test_ios_client_contract.py::test_every_score_on_screen_goes_through_the_figures_line`, shown RED on four mutants (C1, C2, `ranked: true`, C6) | ✅ |
| 8 | No `git checkout`/`restore` on uncommitted work this wave | None run. The patch was applied by `apply_w4.py`, which refuses any edit whose old text has moved. The commit is staged from the verified W4 tree with `git update-index --cacheinfo`, so nothing in the working tree is restored or overwritten | ✅ |
| 9c | Invariant hardening: producer list enumerated FROM CODE | The invariant is REQ-CMP-004: no score is shown in a form that invites a cross-scale comparison. Producers of a displayed score, by grep over `ios/ModelRanking`: `PickRow` and `RankedRow`, both through `figuresLine`. `Format.scoreAndPrice`, the only other producer, is deleted. The list is now enforced rather than enumerated: the contract test fails on any served `.score` outside a composer's `score:` argument | ✅ |
| 9b | Scope: planned vs delivered vs deferred | **Planned (plan §2 W4, after F2):** the score forms and renaming `BUDGET PICK`. **Delivered:** both. **Added:** the `$0` price defect seen on the W3 simulator; D-139, written late for council ruling A3 (ledger L2). **Deferred:** the detail screen and vendor links, to M14 (F2) | ✅ |
| 9a | Economy: diff within ~≤400 changed lines OR variance noted | Within, measured on the final diff: about 183 product lines (`Scores.swift` 85, `ContentView.swift` +30/−37, `Router.swift` +17/−3, `Language.swift` +9/−2), 157 test lines (`ScoresTests.swift` 121, the contract test 36) and 52 record lines. The review fix round added about 45 product and 90 test lines of that | ✅ |
| 9 | Skipped/waived/BYPASSED ledger + run summary | `gates run: make check, xcodebuild (iOS Simulator, CODE_SIGNING_ALLOWED=NO), swift test, simulator session · gates SKIPPED: none at the leg level; 12 conditional pytest skips · outcome: shipped` | ✅ |

**Ledger rows**

- **L1 — the pulled-forward security pass does not apply to a MED wave.** It is recorded as WAIVED
  so the row cannot read as a pass. The Stage 4.0 review covers the whole milestone surface,
  this wave included.
- **L2 — D-139 was written late.** Plan §5 says each council answer becomes an ADR at the wave that
  consumes it. W2 consumed ruling A3 (a stale second board does not upgrade the count) and wrote no
  ADR. W4 noticed the gap while writing D-140. It is recorded as a process deviation, not as a
  decision that changed.
- **L3 — D-140's cost.** For ECI, the exact number is replaced on the card and in the ranking rows by
  its rank range. This amends REQ-CMP-001, and the prd row says so. The number stays in the payload.
  Where no rank can be shown, the engine's number stays too (review MINOR-8).
- **L4 — review MAJOR-1 is escalate-now by class.** A stay-green fault with no test: either call site
  could print a bare score and every test passed. It was closed inside the wave with a test shown
  RED on three mutants, and the owner is told in the session report and the closure report.
- **L5 — review MINOR-5 is queued to M14.** `coding` and `agentic-coding` both use `% resolved`, so
  they share a form and only their section titles separate them. The prd row now says the clause is
  met per metric family. Putting the benchmark's name on the figures line is M14's.
- **L6 — the re-review's three NITs were fixed after its read**, and the seat has not read the fixes.
  NEW-1: D-140 and the `Scores.swift` header credited the 4–1 vote and "every seat" to the wrong
  council. NEW-2: a test now kills F2, the fallback without its rank-only condition. NEW-3: the
  contract test holds a `\.score` key path to `.map(`, which kills C6, `row[keyPath: \.score]`.

Filled by: lead agent (Claude Code, local lane, D-117) · Date: 2026-09-15 · Wave commit range:
`cda57b1..HEAD`

## Wave footprint — RECORD ONLY

```
Touched:        ios/ModelRanking/Engine/{Scores,Router,Language}.swift · ios/ModelRanking/ContentView.swift
                ios/EngineTests/ScoresTests.swift · docs/{decisions,prd}.md · .language-allow
K.8 contracts:  `money()` now returns `String?` (two callers, both updated) · `Format` deleted in
                favour of `figuresLine` / `priceTag` · `UIText.pickLabel("budget_pick")`
```
