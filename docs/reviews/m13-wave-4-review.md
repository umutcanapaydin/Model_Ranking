---
record_type: review
id: m13-wave-4-review
status: ratified
seat: independent
date: 2026-09-15
---
# M13-W4 — combined review seat (Code-Reviewer + Tester)

**How this record was produced.** This seat is the single combined reviewer that V3C-78 calls for
at MED tier (plan §2 W4). It did not author any of the wave's code. It read its policy from the
protected base ref (`HEAD` = `cda57b1`): `subagent-profiles/Code-Reviewer.md`,
`subagent-profiles/Tester.md`, `AGENTS.md`, and the format of `docs/reviews/m13-wave-3-rereview.md`.
It was read-only on the repository apart from this one new file, and it ran no state-changing git
command. The frozen diff was applied to a fresh `git archive cda57b1` export in the session
scratchpad, together with a copy of `advisor.db`. The five source files of that private tree were
checked with `diff -q` and are byte-identical to the working tree. Every probe and every mutant ran
on the private copy and never on the working tree. Every `file:line` below refers to the tree with
the diff applied.

**The diff reviewed.** `m13-w4.diff`, 406 lines across 8 files. It applies cleanly to `cda57b1`:
- `ios/ModelRanking/Engine/Scores.swift` (new)
- `ios/EngineTests/ScoresTests.swift` (new)
- `ios/ModelRanking/ContentView.swift`
- `ios/ModelRanking/Engine/Router.swift`
- `ios/ModelRanking/Engine/Language.swift`
- `docs/decisions.md`
- `docs/prd.md`
- `.language-allow`

## Baseline at the reviewed tree

| Check | Result |
|---|---|
| `swift test` (private tree) | **211 tests, 0 failures** |
| `pytest tests/unit` (repo venv, with `advisor.db`) | **860 passed**, 7 skipped. The coordinator reports 869 for `make check`. The W3 re-review found the same gap, in files outside this diff |
| `scripts/check_records.py --root .` | PASS, 88 records (before this record was added) |
| `xcodebuild` | Not re-run by this seat. The coordinator reports success, and the two screenshots show the build running |
| Screenshots | `w4_home_small.png` (coding, Turkish) and `w4_math_small.png` (mathematics, Turkish) show `Puan 83.5 / 100`, `Puan 100 / 100`, `UYGUN FİYATLI SEÇİM` and `yaklaşık $0.13`. **No screenshot shows an ECI surface (`everyday`) or an Elo surface**, so the rank-only card and the `Elo` form have not been seen in the running app |

**Boundary probe.** A temporary test file was run on the private tree, deleted afterwards, and its
deletion confirmed.

| Input | Output |
|---|---|
| `money(0.995)` | `"0.99"` |
| `money(0.9951)`, `money(0.999)` | `"1.00"`, so the page line reads `about $1.00 per 1,500 pages of text` |
| `money(1.0)` | `"1"` |
| `money(0.01)` | `"0.01"` |
| `money(0.009)`, `money(0.0099999)` | `nil`, so the page line reads `under $0.01 per 1,500 pages of text` |
| `money(14.99)` | `"15"` |
| `priceInPages(15.0)` | `about $0.01 per page of text` |
| `priceInPages(-0.0)`, `priceInPages(0)` | `price unavailable` |
| `priceTag(0)` | `$0/1M` |
| `priceTag(0.0004)`, `priceTag(0.0005)` | `$0/1M` |
| `priceTag(-0.0)` | `$-0/1M` |
| `priceTag(1e19)` | `$10000000000000000000/1M` |
| `scoreText(99.96, "% correct")` | `Score 100.0 / 100`. The engine cannot send this value, because D-109 rounds scores to one decimal |
| `scoreText(100.04, "% correct")` | `nil` |
| `scoreText(1_000_001, "elo")`, `scoreText(.nan, "elo")` | `nil` |
| `scoreText(161.7, "Eci")` | `nil` |
| `scoreText(72, "points")` | `72 points` / `72 puan` |
| `scoreText(5, "")` | `"5 "`, with a trailing space |
| `figuresLine(.nan, "elo", .nan)` | `—` |

## Verdict: PASS WITH FINDINGS

The engine half of REQ-CMP-004 is correct against C1, and it is well defended: every one of the
eleven mutants on `scoreText`, `scoreForm`, `figuresLine` and `priceTag` fails a test. The rename
is complete in every string a reader sees. The money fix does what it claims.

**One MAJOR finding must be discharged before W4 closes, not deferred.**
- **What it is.** Nothing proves that the screen calls this logic. Two mutants in `ContentView`
  stay green across all 860 Python tests (C1 and C2), and the Swift package does not compile
  `ContentView`. One of them prints `Score 161.7`, the exact form the council refused.
- **Why it cannot wait.** It is the same gap the W2 and W3 testers each found. V3C-72 makes the
  missing test mandatory in this wave, and `AGENTS.md:35` lists "stay-green fault with no test" as
  an escalate-now item. **The coordinator should treat it as escalated.**

---

## Findings

### MAJOR-1: nothing pins `figuresLine` in `PickRow` or `RankedRow`

**Where:** `ios/ModelRanking/ContentView.swift:686-688` (`PickRow`) and `:734-736` (`RankedRow`).

**What the prd row claims.** `docs/prd.md:490` says REQ-CMP-004 is "rendered by `PickRow` and
`RankedRow`". No test anywhere asserts it:
- `grep -rn figuresLine tests/ ios/EngineTests/` matches only `ScoresTests.swift`.
- `tests/unit/test_ios_client_contract.py:508-553` pins `PickRow(… ranges: ranges …)` but not the
  figures line.

**What the mutants showed.**
- **Mutant C1** replaced `RankedRow`'s call with `Text("\(row.score) \(UIText.metric(…))  ·  …")`.
  That is `161.7 ECI` again, in every ranking row.
- **Mutant C2** replaced `PickRow`'s call with `Text("Score \(pick.score)  ·  …")`. That is bare
  `Score 161.7` beside bare `Score 83.5`, the form D-140 exists to refuse.
- **Both stayed GREEN:** 860 passed.

**The test it needs.** Add it to `tests/unit/test_ios_client_contract.py`, in the style of the
existing `test_the_screen_calls_the_uncertainty_functions_it_depends_on`:
1. Both the `struct PickRow` body and the `struct RankedRow` body contain `figuresLine(` with
   `score:`, `metric:` and `blendedPerM:` taken from their own `pick.` / `row.`.
2. No line of `ContentView.swift` outside comments interpolates `\(pick.score)` or `\(row.score)`
   into a `Text`.

Each half fails on one of the two mutants above.

### MINOR-2: the Turkish sub-cent assertion accepts a false claim

**Where:** `ios/EngineTests/ScoresTests.swift:79` checks only `turkish.contains("$0.01")`.

**Mutant P2** changed `ios/ModelRanking/Engine/Language.swift:196` to
`"… sayfa metin için yaklaşık $0.01"`, which tells a reader that a $0.004 model costs about a cent.
It stayed GREEN.

The English half, at `:78`, asserts the word `under` and kills the English equivalent (P1). The
Turkish half should be exact:
`XCTAssertEqual(priceInPages(0.004, in: .turkish), "1,500 sayfa metin için $0.01'den az")`.

### MINOR-3: the $1 boundary of `money` is untested

**Where:** `ios/ModelRanking/Engine/Router.swift:661`.

**Mutant M3** moved the boundary from `value >= 1` to `value >= 0.5`, so a $0.75 price would read
`about $1`. It stayed GREEN. The tests use only 0.13, 0.004, 1.03 and 10.0.

The probe also shows that 0.9951 to 0.999 render as `$1.00`, while 1.0 renders as `$1`: two forms
for the same amount.

**Test needed:** `priceInPages(0.75) == "about $0.75 per 1,500 pages of text"`, plus one pinned
value between 0.995 and 1.

### MINOR-4: `priceTag` prints a positive price as `$0/1M`, and -0.0 as `$-0/1M`

**Where:** `ios/ModelRanking/Engine/Scores.swift:61-69`.
- `maximumFractionDigits = 3` rounds anything below $0.0005/1M to `$0/1M`.
- The `>= 0` guard admits `-0.0`.

**The inconsistency.** On the same card, the figures line would then read `$0/1M` above
`under $0.01 per 1,500 pages of text`. That is the wave's own defect class, a model that is not
free printed as free. It has moved from the page line to the price tag rather than been removed.
Two related points:
- For a price of exactly 0, the tag says `$0/1M` while the page line says `price unavailable`.
- The behaviour was carried over verbatim from the old `Format.trim`, so it is inherited, not
  introduced.

**Reachability.** Only for prices below $0.0005/1M. This seat did not check whether any served
price is that low. D-109 rounds scores, not prices.

**Tests needed:** `priceTag(0.0004) != "$0/1M"` and `priceTag(-0.0) == "—"`.

### MINOR-5: "No two surfaces' scores are presented as comparable" is tested as "no two families"

**Where:** `ios/EngineTests/ScoresTests.swift:28-36`. The test checks two suffixes, one per family.

**What the screen does.** The home screen renders every answer for the question
(`ContentView.swift:119`, `ForEach(ordered)`), and `task=coding` expands to two surfaces. Those are
`coding` (SWE-bench Verified) and `agentic-coding` (DeepSWE), both `% resolved`
(`src/app/workflows/categories.py:71`, `:101`). They render one above the other:
- both as `Score N / 100`
- both with the identical scale line "the share of real tasks it finished"
  (`Router.swift:612`)

Only the section title separates them.

**Why this is MINOR, not a code defect.** C1 ruled the bounded form, so the code follows the
ruling. But the prd row (`docs/prd.md:490`) marks the clause met, and the test that cites it proves
something narrower than the clause.

**Fix:** state in the row that the clause is met per metric family. Then either accept the section
title as what separates surfaces, or queue the benchmark name into the figures line for M14.

### MINOR-6: the prd row claims more than the tests show

**Where:** `docs/prd.md:490`.

**The overclaim.** The row says "one test per metric family in both languages". That is not what
the tests do:
- The Elo test (`ScoresTests.swift:16-21`) is English only.
- The unknown-metric test (`:48-50`) is English only.
- The bounded test (`:10-14`) and the ECI test (`:23-26`) are in both languages.

The "rendered by `PickRow` and `RankedRow`" half is unproven (MAJOR-1).

### MINOR-7: D-139 contradicts its own citation, and uses the wrong day count

**Which wave (`docs/decisions.md:1694`, `:1697`).** D-139 says it was "implemented in `3440abe`"
and that "W2 consumed this one". But `3440abe` is the **M13-W1** commit, and its `--stat` shows
exactly this work: `recommend.py` +116, and `test_secondary_evidence_age.py` created. So the
citation is right and "W2" is wrong. Plan §7, row 1 says "IMPLEMENTED (W2)" as well, so the plan
shares the error.

**The day count (`:1700`).** D-139 says "332 days before the artifact's anchor". The source of the
measurement says **328**: `src/app/workflows/recommend.py:252` and
`tests/unit/test_secondary_evidence_age.py:6`. The 332 comes from plan §0, which does not measure
against the anchor.

Both are one-word fixes. The ADR is not committed yet.

### MINOR-8: an ECI card whose pick is missing from the ranking shows no score and no rank

**Where:** `ContentView.swift:663-671`. The rank appears only when `rankOf` finds the pick in
`ranking`, and `PickRow.ranking` defaults to `[]` (`:621`).

**What the reader would see.** If the pick is not found, an ECI card now shows the scale line and
the price, and nothing that places the model: `figuresLine(161.7, "ECI", …)` is `$2.06/1M`. Before
W4 the card showed `161.7 ECI`.

**Reachability.** Only if the engine serves a pick that is absent from its own ranking. The home
screen passes `answer.ranking` (`:136`).

No test holds C1's "rank alone" property as "never nothing". Queue it with MAJOR-1's source test, or
to M14's detail screen.

### NIT-9: D-140 credits a vote to a council that did not cast it

**Where:** `docs/decisions.md:1727`.

**The mismatch.** D-140 says "the council refused a bare 'Score' 4–1", while its "Decided by" line
(`:1721`) names the three-seat §7 council. The records disagree:
- The 4–1 vote was cast by the **five-seat** pre-plan council (`docs/handovers/handover_m13-start.md:317`
  and plan line 34).
- Plan line 56 says instead that every seat refused the literal form.

**Fix:** name which council voted 4–1.

### NIT-10: the Elo example in C1 and in the plan criterion has no decimal

Plan §7, row 3 and plan §1, row 12 both write `Score 1504 Elo`. The code, D-140 and the prd row
print `Score 1504.2 Elo`. The decimal is D-109's rounding, and the difference is harmless. But D-140
presents as C1 a form that C1 did not write. One sentence in D-140 would say so.

### NIT-11: stale comments in the file that implements D-140

- `ContentView.swift:691-694` still says "The exact number is never replaced — it gains a
  companion. `161.7 ECI` is unreadable…". It sits directly under the call that now removes the ECI
  number (D-140 amends exactly that).
- `ContentView.swift:585` still lists "Budget Pick" as a label.
- Also noted, but predating W4: at `Router.swift:644-649`, the `priceInPages` summary sits at the
  top of `money`'s doc comment.

---

## Checks that passed

- **`Format` is fully removed.** It appears only in the explanatory comment at
  `ContentView.swift:802-804`. No Swift or Python source references `Format.` or `scoreAndPrice`.
  The POSIX rule it carried survives in `priceTag` (`Scores.swift:64`) and is pinned by
  `ScoresTests.swift:59-62`.
- **Every caller of `money` is accounted for.**
  - There are exactly two callers: `Router.swift:676` and `Language.swift:195`. Both sit behind
    `blendedPerM.isFinite, blendedPerM > 0` and `perPage < 0.01`, so `money` only ever sees
    0 < x < 15.
  - `String(format: "%.2f")` takes no locale. It printed `0.13` on this `en_TR` machine.
  - `under $0.01` appears only for 0 < price < $0.01/1M, where it is a true statement.
  - The older tests still pass: `LanguageTests.swift:173-184`, `:276-283`, `:372-392` and
    `OwnerSessionDefectTests.swift:348-374`. None of them had pinned `$0`.
- **The rename is complete in every string a reader sees.**
  - `Language.swift:310-311` holds the new labels, and the engine id is unchanged
    (`recommend.py:552`, `subscribe.py:94`).
  - The remaining "budget" mentions are:
    - the engine's own vocabulary in `docs/prd.md:13` and `:120`, and in `recommend.py:10`
    - historical quotes at `Router.swift:401` and `OwnerSessionDefectTests.swift:145`
    - NIT-11
    - the `seeAll` clause at `Language.swift:295-296` ("fit your budget" / `bütçenize uyuyor`).
      It is shown only when `eligibleCount < ranking.count`, and the W3 comment at
      `ContentView.swift:369-372` says the two agree at `unlimited`. This seat did not verify that.
- **`scoreText` matches C1 and D-140.**
  - The ceiling guard refuses values above 100 (`Scores.swift:47`).
  - Hostile values go through `number()` (`:43`, `Language.swift:220-241`), which refuses NaN,
    ±inf, negatives and anything above 1e6.
  - An unknown metric keeps the engine's label, localised by the existing `localisedUnit` table
    (`:53-54`).
  - The Turkish word is `Puan`.
  - An ECI card places the model by its rank range plus the scale line (`ContentView.swift:663-674`,
    seen in principle on the math screenshot as `51 model içinde #1–28`). The exception is MINOR-8.
- **Records.**
  - The REQ-CMP-001 amendment (`docs/prd.md:81`) is honest about the cost.
  - The `.language-allow` entry has a written reason.
  - `check_records.py` passes.
  - Adding D-139 and D-140 keeps `tests/unit/test_adr_citations.py` green, inside the 860.

## Trial table (fault injection, private copy only)

**Method.** Each mutant ran as one atomic sequence:
1. Record the file's md5.
2. Apply one exact string-replace.
3. Run the whole suite: `swift test` for Engine files, `pytest tests/unit` for `ContentView`,
   which the Swift package does not compile.
4. Revert in place by writing back the original bytes.
5. Re-check the md5.

**A harness defect, recorded rather than hidden.** On the first run, S4 was reverted by
string-replacing the mutant text back. That text, `"\(word) \(value) / 100"`, is identical to the
real bounded line at `Scores.swift:48`, so the revert hit the wrong occurrence. The md5 check
reported `revert_clean: False`.

The consequences, and the repair:
- Every Swift result after S4 in that run was a BUILD-FAIL on a damaged file. All of them are
  **void** and are not counted.
- The private `Scores.swift` was restored by copying the frozen bytes from the working tree, with
  no git. Its md5 returned to `7d8811a9`.
- The harness was changed to revert from bytes held in memory and to stop on any unclean md5.
- S4 through C2 were then re-run.

After the re-run, all four source files match their pre-injection md5s, and the working tree was
never touched.

| # | File | Mutant | Result | Killed by | revert-clean |
|---|---|---|---|---|---|
| S1 | `Scores.swift:47` | ceiling guard removed | RED | `testAPercentageAboveItsCeilingIsNotPrintedAgainstIt` | yes (`7d8811a9`) |
| S2 | `Scores.swift:52` | ECI prints `Score 161.7` | RED | `testAnECIScore…`, `testTheFiguresLineAlwaysCarriesThePrice` | yes |
| S3 | `Scores.swift:44` | Turkish word becomes `Score` | RED | `testABoundedPercentageIsShownAgainstItsCeiling` | yes |
| S4 | `Scores.swift:50` | Elo given ` / 100` | RED | `testAnEloRating…`, `testNoTwoFamiliesAreRenderedInTheSameForm` | yes (run 2) |
| S5 | `Scores.swift:54` | unknown metric returns nil | RED | `testAnUnknownMetricKeepsTheEnginesOwnLabel` | yes |
| S6 | `Scores.swift:43` | `number()` guard replaced by raw `"\(score)"` | RED | `testAScoreTheAppCannotReadIsNotPrinted`, `testABoundedPercentage…` | yes |
| S7 | `Scores.swift:76` | figures line drops the price | RED | `testTheFiguresLineAlwaysCarriesThePrice` | yes |
| S8 | `Scores.swift:64` | price tag locale `tr_TR` | RED | `testThePriceIsNotLocalised`, `testTheFiguresLine…` | yes |
| S9 | `Scores.swift:32` | ECI becomes a named scale | RED | `testAnECIScore…`, `testTheFiguresLine…` | yes |
| S10 | `Scores.swift:29` | metric lookup case-sensitive | RED | `testAnECIScore…` (`"ECI"`), `testTheFiguresLine…` | yes |
| S11 | `Scores.swift:47` | `<= 100` becomes `< 100` | RED | `testABoundedPercentage…` (`100 / 100`) | yes |
| M1 | `Router.swift:661` | whole dollars everywhere (the pre-W4 behaviour) | RED | `testAPriceBelowADollarKeepsItsCents`, `testAPriceBelowACent…` | yes (`a0e12499`) |
| M2 | `Router.swift:664` | sub-cent printed as `0.00` | RED | `testAPriceBelowACentSaysSoInsteadOfPrintingZero` | yes |
| M3 | `Router.swift:661` | $1 boundary moved to $0.50 | **GREEN** | none. **Survivor: MINOR-3** | yes |
| M4 | `Router.swift:661` | cents kept up to $15 | RED | `testAWholeDollarPriceIsUnchanged` | yes |
| P1 | `Router.swift:677` | English sub-cent reads `about $0` | RED | `testAPriceBelowACentSaysSoInsteadOfPrintingZero` | yes |
| P2 | `Language.swift:196` | Turkish sub-cent claims `yaklaşık $0.01` | **GREEN** | none. **Survivor: MINOR-2** | yes (`964967d8`) |
| P3 | `Language.swift:198` | Turkish cheap price rounds to `$0` | RED | `testAPriceBelowADollarKeepsItsCents` | yes |
| L1 | `Language.swift:310` | English label reverts to `BUDGET PICK` | RED | `testTheCheapestAcceptablePickIsNotCalledABudgetPick` | yes |
| L2 | `Language.swift:311` | Turkish label reverts to `BÜTÇE SEÇİMİ` | RED | `testTheCheapestAcceptablePick…` | yes |
| C1 | `ContentView.swift:734` | `RankedRow` bypasses `figuresLine` | **GREEN** (860 passed) | none. **Survivor: MAJOR-1** | yes (`62c1f9c9`) |
| C2 | `ContentView.swift:686` | `PickRow` prints bare `Score 161.7` | **GREEN** (860 passed) | none. **Survivor: MAJOR-1** | yes |

## Kill rate

**18 of 22 valid mutants killed (81.8%).** The void first-run results are excluded.

| Target | Killed |
|---|---|
| `scoreText` / `scoreForm` / `figuresLine` / `priceTag` | 11 / 11 |
| `pickLabel` | 2 / 2 |
| `money` | 3 / 4 |
| `priceInPages` | 2 / 3 |
| `ContentView` wiring | **0 / 2** |

The gap is at the seam between the Engine and the view. That is where the W2 and W3 testers found
it too.

## Per-criterion verdict

| Criterion | Code | Citing test | Verdict |
|---|---|---|---|
| REQ-CMP-004: a bounded metric reads `Score N / 100`, never above its ceiling | `Scores.swift:30`, `:46-48` | `ScoresTests.swift:10-14` (EN+TR), `:38-40` | MET |
| REQ-CMP-004: Elo reads `Score N Elo`, with no ceiling | `Scores.swift:31`, `:49-50` | `ScoresTests.swift:16-21` (EN only, MINOR-6) | MET |
| REQ-CMP-004: ECI prints no number, only a rank | `Scores.swift:32`, `:51-52`; rank at `ContentView.swift:663-671` | `ScoresTests.swift:23-26` (EN+TR). The rank half is untested (MINOR-8) | MET in the Engine |
| REQ-CMP-004: an unknown metric keeps the engine's label | `Scores.swift:53-54` | `ScoresTests.swift:48-50` | MET |
| REQ-CMP-004: a hostile score is not printed | `Scores.swift:43` | `ScoresTests.swift:42-46` | MET |
| REQ-CMP-004: no two surfaces' scores are presented as comparable | `Scores.swift:28-35` | `ScoresTests.swift:28-36` tests families, not surfaces | **PARTIAL** (MINOR-5) |
| REQ-CMP-004: rendered by `PickRow` and `RankedRow` | `ContentView.swift:686-688`, `:734-736` | **none**. C1 and C2 survive | **UNPROVEN** (MAJOR-1) |
| The price is always on the figures line, never localised | `Scores.swift:61-77` | `ScoresTests.swift:52-57`, `:59-62` | MET. Edge case in MINOR-4 |
| A cheap price keeps its cents; below a cent it says "under" | `Router.swift:659-665`, `:676-679`; `Language.swift:195-198` | `ScoresTests.swift:68-71`, `:73-80`, `:82-85` | MET. Gaps in MINOR-2 and MINOR-3 |
| `budget_pick` reads `AFFORDABLE PICK` / `UYGUN FİYATLI SEÇİM`, and the engine id is unchanged | `Language.swift:310-311` | `ScoresTests.swift:90-97`, `:99-102` | MET |
| Records: D-139, D-140, the prd rows, `.language-allow` | `docs/decisions.md:1692-1745`; `docs/prd.md:81`, `:490`; `.language-allow:67-68` | `check_records.py` PASS; `test_adr_citations.py` green | MET with corrections (MINOR-6 and MINOR-7, NIT-9 and NIT-10) |

## Queued outside this wave (K.9)

- Before M13 closes, reconcile plan §7 row 1 ("IMPLEMENTED (W2)") with `3440abe`, the W1 commit.
- Check whether `eligibleCount < ranking.count` can occur at `unlimited`. If it can, the `seeAll`
  budget clause (`Language.swift:295-296`) tells a reader who set no budget about "your budget".
- Take a simulator screenshot of `everyday` (ECI) and `assistant` (Elo) before W4 closes, so that
  the two forms this wave introduced have been seen running.
