---
record_type: review
id: m13-wave-4-rereview
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W4 — combined review seat, re-review of the fixes

**How this record was produced.** This is the same independent seat that wrote
`docs/reviews/m13-wave-4-review.md`, working under the same rules. It read its policy from the
protected base ref (`cda57b1`). It was read-only on the repository apart from this one new file, and
it ran no state-changing git command.

**The diff reviewed.** `m13-w4-r2.diff`: 570 lines, 9 files, the whole of W4 including the fixes.
It replaces `m13-w4.diff`.

**The private tree.** The diff was applied to a fresh `git archive cda57b1` export in the session
scratchpad, together with a copy of `advisor.db` and the first-round review record. The working tree
was never used: it also holds uncommitted Stage 4.0 changes that are outside this wave.

**How md5 was used.** The six touched source and test files were hashed before any probe or mutant,
and each check confirmed them unchanged afterwards:
- the baseline and the probe
- the 33 mutants
- the `xcodebuild`

Every `file:line` below refers to that tree.

## Baseline at the reviewed tree

| Check | Result |
|---|---|
| `swift test` | **214 tests, 0 failures** (211 plus the three added by the fixes) |
| `pytest tests/unit` (repo venv, with `advisor.db`) | **861 passed**, 7 skipped (860 plus the new contract test) |
| `pytest tests/unit/test_ios_client_contract.py` | **16 passed**, matching the coordinator |
| `scripts/check_records.py --root .` | PASS, 89 records (before this record was added) |
| `xcodebuild`, generic iOS Simulator, `CODE_SIGNING_ALLOWED=NO` | **BUILD SUCCEEDED**, run by this seat this time. It compiles `ContentView` against the new required `ranked:` argument, which no Python test can check |

**Boundary probe.** A temporary test file ran on the private tree and was then deleted. The only
`ZZProbe` files left afterwards are build products under `.build`.

| Input | Output |
|---|---|
| `money(0.9949)`, `money(0.99499)`, `money(0.99)` | `0.99` |
| `money(0.995)`, `money(0.999)`, `money(1.0)` | `1` |
| `money(14.99)` | `15` |
| `priceTag(0)`, `priceTag(-0.0)`, `priceTag(-1)`, `priceTag(.nan)` | `—` |
| `priceTag(0.0004)`, `priceTag(0.0005)`, `priceTag(0.00099)` | `<$0.001/1M` |
| `priceTag(0.001)` | `$0.001/1M` |
| `priceTag(0.0015)` | `$0.002/1M` |
| `figuresLine(161.7, "ECI", ranked: false)` | `161.7 ECI  ·  $2.06/1M` in both languages |
| `figuresLine(161.7, "ECI", ranked: true)` | `$2.06/1M` |
| `figuresLine(nan / -5 / 2e6, "ECI", ranked: false)` | price only. A hostile score is still refused by `number()` |
| `figuresLine(1504.2, "elo", ranked: false)` | `Score 1504.2 Elo` / `Puan 1504.2 Elo`, followed by the price |

## Verdict: PASS WITH FINDINGS

All eleven first-round findings are discharged, and I confirm every disposition. **MAJOR-1 is closed
with proof:**
- My C1 and C2 now go RED.
- Four further mutants against the new contract test go RED as well: C3, C4, C5 and C7.

**What remains is three NITs, and none of them gates the close of W4:**
- two mutants that survive in corners that legitimate data does not reach
- one sentence in D-140 that credits a council with more than its record shows

---

## Disposition of each first-round finding

### MAJOR-1: DISCHARGED

The fix is `tests/unit/test_ios_client_contract.py:704-742`
(`test_every_score_on_screen_goes_through_the_figures_line`).

**Half 1 (`:716-730`)** pins, inside each struct body, the full call with the view's own values:
- `PickRow`: `figuresLine(score: pick.score, … ranked: rankText != nil)` at
  `ContentView.swift:690-693`
- `RankedRow`: `figuresLine(score: row.score, … ranked: rank != nil)` at `:738-741`

**Half 2 (`:734-742`)** requires every `.score` that is not a key path to be a composer's `score:`
argument. `grep` finds exactly two such uses in `ContentView.swift`, at `:691` and `:739`, and both
are that argument.

**Mutant results.** Every mutant below fails this test, and the unmutated file passes:
- my C1 and C2
- the coordinator's `ranked: true` mutant, re-run here as C3
- C4, the same change on `RankedRow`
- C5, a second hand-built `Text("\(row.score)")` placed beside the correct call
- C7, a `String(format:)` score on the card

One narrow hole remains (C6, see NEW-3).

### MINOR-2: DISCHARGED

`ios/EngineTests/ScoresTests.swift:108-111` asserts the exact strings in both languages. **P2**
(`yaklaşık $0.01`) now fails `testAPriceBelowACentSaysSoInsteadOfPrintingZero`.

### MINOR-3: DISCHARGED

`Router.swift:664` now prints whole dollars from 0.995, and the comment at `:660-661` gives the
reason. `ScoresTests.swift:99-104` pins 0.75 in both languages, and `:115-119` pins 0.99, 0.999 and
1.0.

The mutants:
- **M3** (boundary at 0.5) now fails.
- **M5**, which restores the pre-fix boundary of 1, fails the new test at `:115`.

The probe shows the edge falls cleanly: 0.99499 prints `0.99`, and 0.995 prints `$1`.

### MINOR-4: DISCHARGED

`Scores.swift:67-68` returns `—` for zero and anything that is not a positive price, and
`<$0.001/1M` below 0.001. The test is `ScoresTests.swift:88-93`. **T1** and **T2** both fail it.
Zero now reads `—`, beside the page line's `price unavailable`, so the two lines on a card agree.

### MINOR-5: DISCHARGED as a record

- The prd row (`docs/prd.md:490`) now says the comparability clause is met **per metric family**.
- It names `coding` and `agentic-coding` as the two surfaces that share a form, told apart by their
  section titles.
- It queues the benchmark name on the figures line to M14.
- The test is renamed to say what it proves: `testNoTwoMetricFamiliesAreRenderedInTheSameForm`,
  `ScoresTests.swift:29-38`.

I accept this: C1 ruled the bounded form, and the record now claims exactly what the code does.

### MINOR-6: DISCHARGED

The Elo and unknown-metric tests now also assert Turkish (`ScoresTests.swift:20`, `:52`). With
bounded (`:10-14`) and ECI (`:24-27`), every family is asserted in both languages, as the prd row
says.

### MINOR-7: DISCHARGED

- `docs/decisions.md:1697` now reads "W1 consumed this one, in `3440abe`".
- The same paragraph notes that plan §7, row 1 says W2.
- `:1701` now reads 328 days, which matches `recommend.py:252`.

### MINOR-8: DISCHARGED

**The fix.** `figuresLine` gained a required `ranked: Bool` (`Scores.swift:83-90`). With no rank
beside it, a rank-only metric keeps the engine's number and label.

**Every caller passes an honest value:**
- `PickRow` uses `rankText != nil` (`ContentView.swift:662`, `:692`).
- `RankedRow` uses `rank != nil` (`:740`).
- Both `RankedRow` call sites pass a real rank: the preview at `:347-352`, and the full list at
  `:768`.

**The tests.** `ScoresTests.swift:68-79` covers both languages. It also covers the case where the
fallback must not change a score that can already be shown. **F1** (ignore `ranked`) and **F3**
(fall back to a bare `Score N`) both fail it.

The argument has no default, so a forgotten caller cannot compile. The `xcodebuild` above confirms
that the two real callers do.

### NIT-9: DISCHARGED, with one sentence left over (NEW-1)

`docs/decisions.md:1727-1728` now credits the 4–1 vote to the five-seat council that preceded the
plan, and cites the handover.

### NIT-10: DISCHARGED

`docs/decisions.md:1734-1736` says that C1 wrote `Score 1504 Elo`, and why the decimal stays.

### NIT-11: DISCHARGED

- `ContentView.swift:585` now reads "Affordable Pick".
- `:696-698` now says REQ-CMP-001 is amended for ECI by D-140.

---

## New findings

### NEW-1 (NIT): D-140 still credits the §7 council with a unanimity its record does not show

**D-140's claim.** `docs/decisions.md:1729` says that "every seat of the three-seat §7 council that
ruled C1 endorsed the intent".

**What the records show:**
- Plan §7 (`docs/plans/m13-plan.md:237-238`) says the three seats "ruled blind, in parallel, each on
  the questions matching its lens". Not every seat ruled on question 3.
- The "every seat agreed with its direction" finding is the **five-seat** council's tally
  (`docs/handovers/handover_m13-start.md:311-313`).

**The same claim in code.** The header of `Scores.swift:10` still says "Every council seat refused
the literal form", beside a 4–1 vote. This sentence was already in the first-round diff, and I
missed it then.

**Fix:** two sentences. Say that the five-seat council endorsed the intent, and that the §7 council
ruled C1.

### NEW-2 (NIT): mutant F2 survives, because the fallback's rank-only restriction is untested

**The mutant.** Dropping `scoreForm(for: metric) == .rankOnly` from `Scores.swift:87` stays GREEN.

**What it would change.** An unranked bounded score that `scoreText` refused, meaning one above 100,
would print as `150 % correct`.

**Reachability.** A score above 100 is hostile, and every real call site passes a rank. So this is
a corner, not a live defect.

**The test that kills it:**
`XCTAssertEqual(figuresLine(score: 150, metric: "% correct", blendedPerM: 2.06, .english, ranked: false), "$2.06/1M")`.

### NEW-3 (NIT): mutant C6 survives, because half 2 of the contract test exempts every key path

**The mutant.** Adding `Text("\(row[keyPath: \.score])")` to `RankedRow` stays GREEN.
`test_ios_client_contract.py:735-736` skips every `\.score`, because the rank ranges legitimately
use `ranking.map(\.score)`.

**Why it is only a NIT.** Nobody writes a score that way by accident, so the hole is narrow.

**Tightening it:** allow `\.score` only where it directly follows `.map(`.

---

## Trial table (fault injection, private copy only)

**Method.** Each mutant ran as one atomic sequence:
1. Hash the file.
2. Apply one exact string-replace, after checking that it occurs once.
3. Run the whole suite: `swift test` for Engine files, `pytest tests/unit` for `ContentView`.
4. Revert in place by writing back the original bytes held in memory, with no git.
5. Re-hash the file.

The harness would stop on any unclean revert, and none occurred.

The pre-injection hashes were:

| File | md5 prefix |
|---|---|
| `Scores.swift` | `b8e7a205` |
| `Router.swift` | `119a01af` |
| `Language.swift` | `964967d8` |
| `ContentView.swift` | `4309eb4f` |

| # | Location | Mutant | Result | Killed by | revert-clean |
|---|---|---|---|---|---|
| S1 | `Scores.swift:47` | ceiling guard removed | RED | `testAPercentageAboveItsCeiling…` | yes |
| S2 | `Scores.swift:52` | ECI prints `Score 161.7` | RED | `testAnECIScore…`, `testARankOnlyScoreWithNoRank…`, `testTheFiguresLine…` | yes |
| S3 | `Scores.swift:44` | Turkish word lost | RED | `testABoundedPercentage…`, `testAnEloRating…` | yes |
| S4 | `Scores.swift:50` | Elo given ` / 100` | RED | `testAnEloRating…`, `testNoTwoMetricFamilies…` | yes |
| S5 | `Scores.swift:54` | unknown metric returns nil | RED | `testAnUnknownMetricKeepsTheEnginesOwnLabel` | yes |
| S6 | `Scores.swift:43` | raw `"\(score)"` replaces the `number()` guard | RED | `testAScoreTheAppCannotReadIsNotPrinted` | yes |
| S7 | `Scores.swift:90` | figures line drops the price | RED | `testTheFiguresLine…`, `testARankOnlyScore…` | yes |
| S8 | `Scores.swift:70` | price tag localised to `tr_TR` | RED | `testThePriceIsNotLocalised` and three more | yes |
| S9 | `Scores.swift:32` | ECI becomes a named scale | RED | `testAnECIScore…` and two more | yes |
| S10 | `Scores.swift:29` | metric lookup case-sensitive | RED | `testAnECIScore…`, `testTheFiguresLine…` | yes |
| S11 | `Scores.swift:47` | `<= 100` becomes `< 100` | RED | `testABoundedPercentage…` | yes |
| F1 | `Scores.swift:87` | fallback ignores `ranked` | RED | `testTheFiguresLineAlwaysCarriesThePrice` | yes |
| F2 | `Scores.swift:87` | fallback not limited to rank-only | **GREEN** | none. **NEW-2** | yes |
| F3 | `Scores.swift:88` | fallback prints bare `Score N` | RED | `testARankOnlyScoreWithNoRankBesideItKeepsTheEnginesNumber` | yes |
| T1 | `Scores.swift:68` | `<$0.001` guard removed | RED | `testThePriceTagNeverPrintsZeroForAPriceThatIsNot` | yes |
| T2 | `Scores.swift:67` | zero admitted to the tag | RED | `testThePriceTagNeverPrints…` | yes |
| M1 | `Router.swift:664` | whole dollars everywhere | RED | three `CheapPriceTests` | yes |
| M2 | `Router.swift:667` | sub-cent printed as `0.00` | RED | `testAPriceBelowACentSaysSo…` | yes |
| M3 | `Router.swift:664` | boundary at $0.50 (**survived round 1**) | RED | `testAPriceBelowADollarKeepsItsCents`, `testTheDollarBoundary…` | yes |
| M4 | `Router.swift:664` | cents kept up to $15 | RED | `testAWholeDollarPriceIsUnchanged`, `testTheDollarBoundary…` | yes |
| M5 | `Router.swift:664` | boundary back at $1 (pre-fix) | RED | `testTheDollarBoundaryPrintsOneAmountOneWay` | yes |
| P1 | `Router.swift:680` | English sub-cent reads `$0` | RED | `testAPriceBelowACentSaysSo…` | yes |
| P2 | `Language.swift:196` | Turkish sub-cent claims `yaklaşık $0.01` (**survived round 1**) | RED | `testAPriceBelowACentSaysSo…` | yes |
| P3 | `Language.swift:198` | Turkish cheap price reads `$0` | RED | `testAPriceBelowADollarKeepsItsCents` | yes |
| L1 | `Language.swift:310` | English label reverts | RED | `testTheCheapestAcceptablePick…` | yes |
| L2 | `Language.swift:311` | Turkish label reverts | RED | `testTheCheapestAcceptablePick…` | yes |
| C1 | `ContentView.swift:738` | `RankedRow` bypasses `figuresLine` (**survived round 1**) | RED | `test_every_score_on_screen_goes_through_the_figures_line` | yes |
| C2 | `ContentView.swift:690` | `PickRow` prints bare `Score 161.7` (**survived round 1**) | RED | same | yes |
| C3 | `ContentView.swift:692` | `PickRow` passes `ranked: true` | RED | same | yes |
| C4 | `ContentView.swift:740` | `RankedRow` passes `ranked: true` | RED | same | yes |
| C5 | `RankedRow` | extra `Text("\(row.score)")` beside the call | RED | same (half 2) | yes |
| C6 | `RankedRow` | score laundered through `row[keyPath: \.score]` | **GREEN** | none. **NEW-3** | yes |
| C7 | `PickRow` | `Text(String(format: "%.1f", pick.score))` | RED | same (half 2) | yes |

## Kill rate

**31 of 33 mutants killed (93.9%).** Round 1 was 18 of 22 (81.8%).

**All four round-1 survivors now die:** M3, P2, C1 and C2.

| Target | Killed |
|---|---|
| `scoreText` / `scoreForm` / `priceTag` | 13 / 13 |
| `figuresLine` fallback | 2 / 3 |
| `money` | 5 / 5 |
| `priceInPages` | 3 / 3 |
| `pickLabel` | 2 / 2 |
| `ContentView` wiring | 6 / 7 |

## Per-criterion verdict

| Criterion | Code | Citing test | Verdict |
|---|---|---|---|
| REQ-CMP-004: a bounded metric reads `Score N / 100`, never above its ceiling | `Scores.swift:30`, `:46-48` | `ScoresTests.swift:10-14` (EN+TR), `:40-42` | MET |
| REQ-CMP-004: Elo reads `Score N Elo`, with no ceiling | `Scores.swift:31`, `:49-50` | `ScoresTests.swift:16-22` (EN+TR) | MET |
| REQ-CMP-004: ECI prints no number where a rank is shown | `Scores.swift:32`, `:51-52`, `:83-90` | `ScoresTests.swift:24-27`, `:55-64` | MET |
| REQ-CMP-004: a rank-only metric with no rank keeps the engine's number | `Scores.swift:86-89`; `ContentView.swift:662`, `:692`, `:740` | `ScoresTests.swift:68-79` (EN+TR) | MET (NEW-2 is a corner) |
| REQ-CMP-004: an unknown metric keeps the engine's label | `Scores.swift:53-54` | `ScoresTests.swift:50-53` (EN+TR) | MET |
| REQ-CMP-004: a hostile score is not printed | `Scores.swift:43` | `ScoresTests.swift:44-48` | MET |
| REQ-CMP-004: comparability, met per metric family | `Scores.swift:28-35`; `docs/prd.md:490` | `ScoresTests.swift:29-38` | MET as recorded |
| REQ-CMP-004: rendered by `PickRow` and `RankedRow` | `ContentView.swift:690-693`, `:738-741` | `tests/unit/test_ios_client_contract.py:704-742` | MET (NEW-3 is a narrow hole) |
| The price is always on the figures line, never localised, and never `$0` for a real price | `Scores.swift:66-75`, `:90` | `ScoresTests.swift:55-64`, `:81-84`, `:88-93` | MET |
| A cheap price keeps its cents, reads "under" below a cent, and prints one amount one way at $1 | `Router.swift:662-668`, `:679-682`; `Language.swift:195-198` | `ScoresTests.swift:99-104`, `:108-111`, `:115-119`, `:121-124` | MET |
| `budget_pick` reads `AFFORDABLE PICK` / `UYGUN FİYATLI SEÇİM` | `Language.swift:310-311` | `ScoresTests.swift:129-136`, `:138-141` | MET |
| Records: D-139, D-140, prd, `.language-allow` | `docs/decisions.md:1692-1747`; `docs/prd.md:81`, `:490`; `.language-allow:67-68` | `check_records.py` PASS; `test_adr_citations.py` green inside the 861 | MET (NEW-1 is one sentence) |

## Still queued outside this wave (K.9, carried from round 1)

- Plan §7, row 1 still says "IMPLEMENTED (W2)". D-139 now records the discrepancy, but the plan
  itself is unchanged.
- The `seeAll` budget clause (`Language.swift:295-296`) remains unverified at `unlimited`.
- No screenshot yet shows an ECI surface (`everyday`) or an Elo surface (`assistant`).
