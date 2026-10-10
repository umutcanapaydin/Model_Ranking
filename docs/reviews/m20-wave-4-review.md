---
record_type: review
id: m20-wave-4-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 4 Code Review, second round (the combined list is the answer, #212, #208)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave or its fixes)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `2e6bd28..f6f632f`. This round judges the answer to round 1
(`docs/reviews/m20-wave-4-review-round-1.md`): `4ea8548` (red tests), `9e05bb1` (the fix) and
`7a3aa3e` (a UI test's expected sentence), each read with `git show`, against the wave's earlier
commits `1e0d0a7`..`36dad00`. W1 to W3 came in by merges and closed separately.
**Risk tier:** HIGH
**Model routing:** author family Claude (claude-code/local-lane), reviewer family Claude. No second
family was available to this seat. Fresh context: this seat read none of the authoring sessions.

## Verdict
MINOR

Every round-1 finding is closed. The family note now gives the board count, each board's date and the
coverage, in both languages, and the code does the same. The boards' screen uses the same sentence
(`orderNote`). All 8 faults that round 1 planted and that survived are now caught. The pair rule,
the chosen surface and the memo now live in Engine code under test. Three new MINOR defects remain:
- The note says a model is "placed by its mean position". The code places it by its mean percentile.
  On boards of different lengths the order can contradict the sentence (M1).
- During a reload, a surface chosen from "Change" is shown next to the previous answers' coding pair,
  or a coding list is shown alone (M2).
- 6 of the 12 faults planted in the new code pass every test. The note's numbers, its Turkish and the
  caption's state mapping are not pinned (M3).

M1 is MINOR, not BLOCKING. Round 1's B1 was a false claim about which models are listed, and that
claim is now true. M1 is a wrong word for the method, and the fix is one word in each language. Round
1 itself proposed "mean position", and the author adopted it.

## How it was checked

- Read round 1, D-188 (clauses 1 to 6, clause 5 as amended), plan §2 W4 and both plan diffs, then the
  fix diffs to `AnswerPlan.swift`, `Language.swift`, `Notices.swift`, `ContentView.swift`,
  `FamilyPlanTests.swift`, `LanguageTests.swift`, `UITextLanguageTests.swift`, `ScreenPathTests.swift`
  and `docs/prd.md`, and the code they call (`combineFamily`, `readableDate`, `OnDeviceState`,
  `select`, `apply`, `load`).
- Copied `ios/` to `scratchpad/r2w4/ios`, outside the worktree. The copy's sha256 matches the
  worktree's: `AnswerPlan.swift` `d0577ac2…6217`, `Language.swift` `4c68ea30…006a`. Baseline:
  `swift test --filter 'FamilyPlanTests|AnswerPlanTests|LanguageTests|UITextLanguageTests|FamilyCombineTests'`,
  84 passed.
- `scratchpad/r2w4/plant.py` planted 20 faults, one at a time, with the same filter. After each run
  it restored the file by bytes and checked its sha256. All 20 restores matched the hashes above.
  The table is under M3.
- A probe test in a second copy (`scratchpad/r2w4p`, never in the worktree) called the real
  `answerPlan` on two boards of 10 and 200 rows. It printed the note in both languages, the older-boards
  note, and the result of `pairedSurface` and `familyLists` for the state a reload leaves on screen
  (M1, M2).
- `tests/unit/test_router_hints.py`, `test_ios_client_contract.py`, `test_swift_test_manifest.py`,
  `test_refinements.py`: 107 passed, 1 skipped (needs `advisor.db`).
- Read-only `gh issue view` for 199, 219 and 220. No simulator and no `make ui-test`. The worktree
  has no tracked change apart from this file.

## Round 1, finding by finding

| Round 1 | Closed? | Evidence |
|---|---|---|
| B1 "ranked on all N boards" | **Yes** (residual wording: M1) | `CombinedView.coverage` and `.familyOrder` (`AnswerPlan.swift:31-45`, `:66-68`), set from `list.coverage` (`:220`). `familyNote` (`Language.swift:710-719`) gives the count, each date and the coverage. `olderBoards` dates each board and is plural for several (`:698-705`). `orderNote` is used on the boards' screen (`ContentView.swift:1548`). Probe: "Our own list, built from 2 boards (Board A, 20 September 2026; Board B, undated, read 7 October 2026). 208 models; a model ranked by at least 1 of them …". Faults P1 and P5 were caught |
| M1 #199 | Yes | Moved to M21 W2 with its reason: `docs/plans/m20-plan.md:111-113`, `m21-plan.md` W2. #199 is OPEN |
| M2 Engine tests miss branches | Yes | All 8 round-1 survivors (F2, F3, F5, F6, F7, F8, F10, F12) are now caught (table under M3). `pairedSurface`, `familyLists` and `chosenOutcome` are Engine functions (`AnswerPlan.swift:233-251`). The UI test asserts `combinedList.paired` is on screen (`ScreenPathTests.swift:118`; `bringIntoView` asserts, `:82`) |
| M3 empty "Also counted" | Yes | `ContentView.swift:387-390` |
| M4 chosen surface, launch | Yes, with a new defect (M2) | `chosenByReader` (`ContentView.swift:72`, `:192`, `:1014`); the launch screen's cards are recorded in D-188 clause 5 and REQ-CMB-005 |
| M5 glow, caption | Yes | `TimelineView(.animation(minimumInterval: 1/30, paused: still))` with angle 0 when still (`ContentView.swift:1102-1103`); one caption per `OnDeviceState` (`Language.swift:593-611`) |
| M6 PRD rows | Yes | `docs/prd.md:614-616`; REQ-APP-002, REQ-APP-005, REQ-CMB-002 and REQ-CMB-003 updated (`:424`, `:427`, `:611-612`); every test the rows cite exists |
| M7 shared controls | Yes | `expandedLists: Set<String>` (`ContentView.swift:69`, `:380`, `:435`); one access filter (`:393-399`); `.paired` suffixes (`:379`, `:385`, `:404`, `:446`, `:464`) |
| K1 REQ-APP-005 | Yes | `docs/prd.md:427` says "mean percentile position" |
| K2 | Filed | #219, OPEN |
| K3, R2 | Filed | #220, OPEN |
| R1 the plan's day | Yes | `utcDay` (`ContentView.swift:358-364`) against `isStale`'s UTC day (`Combine.swift:191-199`) |

## Findings

### BLOCKING

None

### MINOR

- **M1** `ios/ModelRanking/Engine/Language.swift:714` and `:717`, and the doc comment at
  `ios/ModelRanking/Engine/AnswerPlan.swift:67`. **The family note says a model is placed by its
  mean position. The code places it by its mean percentile.** `combineFamily` averages
  `(position - 1) / (size - 1)` (`Combine.swift:140`, `:165`), as D-188 clause 3 and REQ-APP-005 say.
  The English says "placed by its mean position on those boards". The Turkish says
  `o panolardaki ortalama sırasıyla yerleşir` ("is placed by its average rank on those boards"). The two orders
  differ whenever the boards differ in length, which is true of every served family (`coding`'s primary
  board ranks 40 models, Arena's coding board about 200). D-160 clause 3 requires the sentence to
  describe the order truthfully.
  **Failure scenario.** In the probe, the real `answerPlan` ran on a 10-row and a 200-row board:
  ```
  PROBE entry y place 62 positions ["A:1", "B:120"] meanPosition 60.5
  PROBE entry x place 105 positions ["A:10", "B:1"] meanPosition 5.5
  ```
  A reader taps "See the boards" and sees x at 10th and 1st, and y at 1st and 120th. The sentence
  above says the mean position decides, yet x is 43 places below y.
  **Fix.** Say the percentile in both languages. English: "is placed by the mean of its relative
  positions (its place on each board as a share of that board's length)". Turkish:
  `her panodaki göreli sırasının (sırasının o panonun uzunluğuna oranı) ortalamasıyla yerleşir`
  ("is placed by the mean of its relative rank on each board (its rank as a share of that board's
  length)"). Correct the
  doc comment too, and pin both sentences exactly in a test (M3).

- **M2** `ios/ModelRanking/ContentView.swift:192-204`, with `select` at `:1012-1020` and `apply` at
  `:936-943`. **A surface chosen from "Change" is planned before its answers arrive, so the reload
  shows the wrong pair, or one coding list alone.** `select` sets `chosenByReader = true` and
  `task = id`, then starts `load()`. During the reload, `load` keeps the old answers on screen
  (`:1027-1028`). So `shown` is the new surface, but `ordered` still holds the old answers, and
  `pairedSurface` pairs the new surface with one of the old ones. `apply` avoids this for a question:
  it sets `routing` only after `load()` returns (`:938-942`). But a question asked after a "Change"
  hits the same window, because `chosenByReader` is still true while `apply` awaits the load.
  **Failure scenario.** The probe ran the Engine composition the view uses:
  ```
  PROBE paired(routed: mathematics, old answers coding pair): agentic-coding
  PROBE paired(routed: coding, old answers [mathematics]): nil
  PROBE one list alone: true
  ```
  - From coding, the reader picks Mathematics. Until the engine answers, the screen shows a
    "Mathematics" list and an "Agentic coding" list, with the note that their order means nothing.
  - From Mathematics, the reader picks Coding. Until the engine answers, coding's list stands alone
    with no title. Ruling A forbids one coding list alone, and REQ-APP-008 says "both or neither".

  Each lasts for two round trips to Fly.io.
  **Fix.** Plan a chosen surface only once its answers are on screen. Put the rule in the Engine,
  where a test can hold it: `pairedSurface` and `familyLists` return `nil` when the answers do not
  include the planned surface. Also set `chosenByReader = false` in `apply` before `task` changes.
  Add a `FamilyPlanTests` case with stale answers (`routed: "coding"`, `answers: ["mathematics"]`).

- **M3** `ios/EngineTests/FamilyPlanTests.swift:117-133`, `ios/EngineTests/LanguageTests.swift:598-612`,
  `ios/UITests/ScreenPathTests.swift:140-145`. **The tests do not pin the new note's numbers, its
  Turkish, the "undated" marker or the caption's state mapping.** Of the 20 faults planted, the 8 that
  survived round 1 and 6 of the 12 aimed at the new code were caught. The other 6 passed every test:

  | Fault planted | Result |
  |---|---|
  | F2, F3, F5, F6, F7, F8, F10, F12 (round 1's survivors) | **all caught** |
  | P1 a family list falls back to the intersection sentence (`coverage: nil`) | caught |
  | P2 `pairedSurface` returns the routed surface | caught |
  | P3 `familyLists` returns one coding list alone | caught |
  | P4 a chosen surface is unmeasured (cards) | caught |
  | P5 the boards' screen says the intersection sentence | caught |
  | P6 the older-boards note is plural for one board | caught |
  | P7 the Turkish older-boards plural inverted | **passed** |
  | P8 the Turkish note gives the board count as the coverage ("en az 4 panoda", "on at least 4 boards") | **passed** |
  | P9 an undated board's date loses "undated, read" | **passed** |
  | P10 the `.familyOrder` disclosure counts boards as models | **passed** |
  | P11 the English note gives the board count as the model count | **passed** |
  | P12 the `.turnedOff` and `.notEligible` captions swapped | **passed** |

  P10 and P11 pass because the only fixture has 3 models on 3 boards. P8 is round 1's B1 again, in
  Turkish: the Turkish note is checked only for being unlike the English. P12 passes because
  `LanguageTests` checks only that the five captions differ, never which state gets which caption.
  REQ-APP-007 cites that test as its evidence. The UI test still checks `hasPrefix("Apple
  Intelligence")`, and the new `.notEligible` caption ("No Apple Intelligence on this device …")
  fails that check. Run the UI test where the model cannot run, for example on an iOS 18 simulator
  (the deployment target; `onDeviceState()` returns `.notEligible` before iOS 26,
  `Router.swift:989-995`), and it goes red for a correct screen.
  **Failure scenario.** A later edit makes the Turkish note say "en az 4 panoda" ("on at least 4
  boards") on coding, whose models need 2. `swift test` stays green, and the Turkish reader is told the
  stricter rule that B1 removed.
  **Fix.** Use a fixture whose model count, board count and coverage all differ (for example, 5 models,
  4 boards, coverage 2). Assert the exact English and Turkish sentences, as `LanguageTests` does for
  `rangeNote`. Assert "undated" and "tarihsiz" ("undated") for `.readOn`, the Turkish plural
  `sayılıyorlar` ("they count") and singular `sayılıyor` ("it counts"), and each state's caption in
  both languages. In the UI test, compare the caption with `UIText.onDeviceCaption(state, .english)`
  for the launch's state, or at least accept every caption.

## Producers of the invariants this wave hardens

- **Ruling A, both lists or neither.** Producers: `familyLists` (`AnswerPlan.swift:240-245`), cited by
  `FamilyPlanTests.testCodingShowsBothFamilyListsOrNeither` (P3 caught); `pairedSurface`
  (`:233-235`), cited by `testThePairedOutcomeIsTheOtherSurfaceAtTheRoutedTier` (P2 caught); the
  view's inputs to both, `shown` and `ordered` (`ContentView.swift:157-159`, `:192-198`), cited by no
  test. Gaps: M2.
- **Nothing typed reaches the engine.** Producers: `planInputs(question:)` (`ContentView.swift:342-356`)
  feeds only `PlanMemo` and `answerPlan`. A chosen surface passes no words (`:193`). `EngineClient` is
  unchanged in the range (`git diff --stat 2e6bd28..f6f632f -- ios/` does not list it). Cited by
  `test_router_hints.py` and `test_ios_client_contract.py` (passed). Gaps: none.
- **The family sentence tells the truth.** Producers: `familyNote`, `olderBoards`, `shortBoardDate`
  (`Language.swift:698-730`) and `orderNote` (`AnswerPlan.swift:89-95`). Cited by
  `testAFamilyListSaysItsBoardsTheirDatesAndTheCoverage` and
  `testTheOlderBoardsNoteIsSaidInBothLanguagesWithEachDate`. Gaps: M1, M3.

## Acceptance criteria evidence

- Combined list by default, for every question and every chosen surface: `AnswerPlan.swift:166-169`,
  `:249-251`; `ContentView.swift:192-194`; `FamilyPlanTests.swift:37-44`, `:197-206`. The launch
  screen shows cards, as D-188 clause 5 now says.
- "Built from N boards", each with its date and the coverage: `Language.swift:710-719`;
  `FamilyPlanTests.swift:117-133`. Wording of the method: M1.
- An older board is a small dated note: `AnswerPlan.swift:216`, `Notices.swift:263-264`;
  `FamilyPlanTests.swift:84-113`.
- One tap to each board's place: `ContentView.swift:449-464` → `CombinedDetail` (`:1548`).
- The primary answer is one tap away and one tap back: `ContentView.swift:205-218`, `:367-373`;
  `ScreenPathTests.swift:113-138` (simulator only).
- Ruling A, two lists, both or neither: `AnswerPlan.swift:240-245`; `FamilyPlanTests.swift:182-193`.
  The window during a reload: M2.
- #208, glow and caption: `ContentView.swift:555-565`, `:1096-1112`; `Language.swift:593-611`;
  `LanguageTests.swift:598-612`. The state mapping is unpinned (M3).

## K.8 contract drift check

```
$ grep -n 'combineFamily(\|struct FamilyList\|let coverage' ios/ModelRanking/Engine/AnswerPlan.swift ios/ModelRanking/Engine/Combine.swift
ios/ModelRanking/Engine/AnswerPlan.swift:205:    guard let list = try? combineFamily(standings, boards: boards, asOf: asOf), !list.entries.isEmpty else {
ios/ModelRanking/Engine/Combine.swift:126:struct FamilyList: Equatable {
ios/ModelRanking/Engine/Combine.swift:129:    let coverage: Int
ios/ModelRanking/Engine/Combine.swift:146:func combineFamily(_ standings: Standings, boards family: [String], asOf today: Date) throws -> FamilyList {
ios/ModelRanking/Engine/Combine.swift:156:    let coverage = max(1, (boards.count + 1) / 2)
```
- `CombinedView.coverage` carries `FamilyList.coverage` unchanged (`AnswerPlan.swift:220`). The
  `/v1` request and `EngineClient` are untouched. Verdict: OK.

## K.9 candidates spotted outside this wave's scope

- **K1** #219 and #220 (GitHub issues). Both bodies say "Found in … `docs/reviews/m20-wave-4-review.md`
  (K2 / K3 and R2)". `f6f632f` renamed that review to `m20-wave-4-review-round-1.md`, and this file
  now holds the second round, which has no K2, K3 or R2. Anyone following the link finds the wrong
  record. Bug (record). Fix: change each issue's "Found in" line to `m20-wave-4-review-round-1.md`.

## Risks queued to next M

- **R1** `ios/ModelRanking/ContentView.swift:1102`. Round 1's glow was a `repeatForever` animation,
  which the render server interpolates. The fix moved the glow into a `TimelineView` that runs
  SwiftUI's body for the stroke and its blur 30 times a second, on the main thread, whenever the home
  screen is visible on a phone with Apple Intelligence. That includes while the reader scrolls a
  58-row list. #220 plans to measure the glow's energy. Its measurement should also record scroll
  hitches with the glow on and off (Instruments, SwiftUI and Hitches templates, on the owner's
  phone). Hitches only with the glow on would show the risk is real.
