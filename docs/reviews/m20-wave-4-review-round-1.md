---
record_type: review
id: m20-wave-4-review-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 4 Code Review (the combined list is the answer, #212, #208, #199)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `2e6bd28..36dad00`, the wave's own commits `1e0d0a7` (red), `b805c30`, `f97018b`,
`6ab7389`, `b9c34cf` (red), `452dc48`, `992fc35`, `36dad00`, each read with `git show`. W1 to W3's
commits in the range (`d47126e`, `81b1c42`, `7408af2`, `fb773fe`) were reviewed separately and are
not judged here.
**Risk tier:** MEDIUM (plan §3: screen code and its tests)

## Verdict
BLOCKING

The family plan works. It reads the family, uses the words only where the on-device model did not read
the question, keeps an engine older than M20 on today's plan, and drops the loud stale warning for a
small note. But the sentence every family list carries says its models are "ranked on all N boards".
Under D-188 that is false: a model needs only half of the boards. That sentence is now on the default
answer to most questions (B1). #199 was not delivered (M1). Eight of twelve planted faults pass every
Engine test, among them Ruling A's paired outcome and removing or restoring a refinement on a family
(M2).

## How it was checked

- Read plan §1 row W4, §2 W4 and D-188 (clauses 4 to 6) before the code. Then read the wave's diff of
  `AnswerPlan.swift`, `ContentView.swift`, `Language.swift`, `Notices.swift`, `FamilyPlanTests.swift`
  and `ScreenPathTests.swift`, and the code they call (`combineFamily`, `Refinements.familyBoards`,
  `Refinements.read`, `CombinedDetail`, `app.workflows.families`).
- Copied `ios/` to the scratchpad, outside the worktree. The copy's `AnswerPlan.swift` has the same
  sha256 as the worktree's (`bb1b2ed2…df97`). Baseline: `swift test --filter
  'FamilyPlanTests|AnswerPlanTests|LanguageTests|UITextLanguageTests'`, 51 passed.
- Planted 12 faults in the copy's `AnswerPlan.swift` with a Python script. It ran `swift test --filter
  'FamilyPlanTests|AnswerPlanTests|QuestionFamilyTests'` for each, restored the file by bytes, and
  checked the sha256 after every plant. All 12 restores matched `bb1b2ed2…`. The results are under M2.
- Ran a scratch probe test (in the copy, deleted afterwards) that calls the real `answerPlan` on
  `FamilyPlanTests`' own coding fixture and prints the list's disclosures (B1).
- `tests/unit/test_router_hints.py`, `test_ios_client_contract.py`: 96 passed.
  `test_client_decl_gate.py`, `test_refinements.py`, `test_ios_visual_contract.py`,
  `test_swift_test_manifest.py`: 64 passed, 1 skipped (needs `advisor.db`).
- Read `gh issue view 199` and `gh issue view 208` (read-only). No simulator, no `make ui-test`.
- The worktree has no tracked changes apart from this file.

## Findings

### BLOCKING

- **B1** `ios/ModelRanking/Engine/Language.swift:615-621`, reached from
  `ios/ModelRanking/Engine/AnswerPlan.swift:38` and `:183-186`, and repeated at
  `ios/ModelRanking/ContentView.swift:1522`. **Every family list says its models are ranked on every
  board, which is false under D-188.** `familyPlan` builds a `CombinedView`, and its disclosures
  include `.productsOwnOrder(models: sharedCount, boards: list.boards.count)`. That case is said by
  `combinedNote`: "The app's own list: N models ranked on all M boards, ordered by their places on
  each." The Turkish says the same: "M panonun hepsinde yer alan N model" ("N models that appear on
  all M boards"). D-188 clause 2 lets a model in when half of the boards rank it. `FamilyList.coverage`
  says how many boards that is, but `familyPlan` drops it (`AnswerPlan.swift:178-186`).
  **Failure scenario.** The probe ran the real `answerPlan` on `FamilyPlanTests`' coding fixture.
  Each of the three models is ranked on two of the three boards:
  ```
  PROBE: The app's own list: 3 models ranked on all 3 boards, ordered by their places on each. No leaderboard publishes this order.
  PROBE entry: a ["swebench", "arena_text_coding"]
  PROBE entry: b ["swebench", "aider"]
  PROBE entry: c ["aider", "arena_text_coding"]
  ```
  On the served boards, `coding` has 58 models from four boards (D-188 clause 2). The screen would say
  all 58 are on all four. This is the default answer on the 10 of the 14 surfaces whose family has more than one board. REQ-APP-003 makes this
  sentence a duty ("how many models the boards share"), and D-160 clause 3 says it must describe the
  order truthfully. Plan row W4 asks for "built from N boards" with each board's date. The main list
  shows no date: the dates are one tap away, under "See the boards" (`ContentView.swift:1529`).
  The older-boards note gives no date either, and its English uses the singular "it counts" when it
  names several boards (`Language.swift:686-691`). **Fix.** Add a family disclosure case that carries
  the board count, the coverage and each board's date, for example `.familyOrder(boards:, coverage:,
  dates:)`, said in both languages: "Built from 4 boards (SWE-bench, 25 Jun; …); a model ranked by at
  least 2 of them is placed by its mean position." Use it in `familyPlan` and in `CombinedDetail` in
  place of `combinedNote`, and put each date in the older-boards note, in the plural where several
  boards are named. Pin the sentence with a `FamilyPlanTests` test on the plan's disclosures.

### MINOR

- **M1** `ios/UITests/ScreenPathTests.swift:14-20`. **#199 was not delivered, and no record defers
  it.** Plan §2 W4 says the UI target's scripted routing, and the reading each test expects, move into
  one fixture that an Engine test also reads. Issue #199's bar is a planted reading change that fails
  `swift test`. The routing table is still a private dictionary inside the UI target, and this wave
  added one more entry to it (`:16-17`, the vision question). No fixture file exists, and no Engine test
  reads one. `git grep '#199'` finds only the plan and EXPERIENCE.md. **Failure scenario.** A reading
  change flips `"Which model reads my photos best?"` from a search to a held question. `swift test` and
  `make check-fast` stay green, and `testAQuestionThatSelectsOneBoardShowsTheCards` goes red only when
  someone runs `make ui-test` on the owner's Mac. That is the M19 failure #199 was filed for. **Fix.**
  Move the table into a JSON fixture under `ios/` that `ScreenPathTests` loads and `ReadingTests`
  reads, and run the planted change once. Or amend plan §2 W4 to move #199 to M21, with the reason.

- **M2** `ios/EngineTests/FamilyPlanTests.swift`, `ios/ModelRanking/Engine/AnswerPlan.swift:161-194`,
  `ios/ModelRanking/ContentView.swift:190-200`. **The Engine tests miss most of the family path's
  branches.** Of the 12 planted faults, 4 were caught and 8 passed every test:

  | Fault planted in `AnswerPlan.swift` | Result |
  |---|---|
  | F1 the words are never read (`chosen = outcome.refinements`) | caught |
  | F2 `offered` keeps a refinement the surface does not allow | **passed** |
  | F3 no `.restorable` on a one-board family (`assistant` + French, every chip removed) | **passed** |
  | F4 the older boards inverted | caught |
  | F5 `pairedOutcome` keeps the routed surface instead of the paired one | **passed** |
  | F6 `pairedOutcome` drops the tier (always `.similarity`) | **passed** |
  | F7 `PlanMemo.plan` passes `family: nil` (the screen falls back to one board) | **passed** |
  | F8 an empty family list is shown instead of the cards | **passed** |
  | F9 the family cut to its primary board | caught |
  | F10 removed refinements ignored (a removed chip removes nothing) | **passed** |
  | F11 the old rule: words read when the model chose none | caught |
  | F12 the phone copy's age dropped from a family list | **passed** |

  Ruling A's "both lists or neither" rule, and the choice of the paired surface, are view code
  (`ContentView.swift:190-200`) that `swift test` never runs. The UI tests do not cover the gap either.
  `testCodingGetsTwoFamilyListsAndThePrimaryAnswersAreOneTapAway` waits for one `combinedList`
  (`ScreenPathTests.swift:115`) and never counts two. `testTheQuestionSaysWhoReadsIt` checks
  `hasPrefix("Apple Intelligence")` (`:141`), which both captions pass, so it cannot show the caption
  follows the state, as #208's scope asks. **Failure scenario.** F10 ships: on "Translate my letter
  into French" the reader taps the French chip off, and the French board still counts. **Fix.** Add
  `FamilyPlanTests` for remove and restore on a one-board and on a multi-board family, for a refinement
  the surface does not allow, for `pairedOutcome`'s surface and tier, for the memo's returned plan with
  a family, and for an empty list and `phoneCopyDays`. Move the pair rule into an Engine function, for
  example `codingPlans(routed:answers:) -> (CombinedView, CombinedView)?`, and test it. In the UI test,
  assert that exactly two `combinedList` elements exist, and that the caption equals the string for the
  launch's `OnDeviceState`.

- **M3** `ios/ModelRanking/ContentView.swift:370-371`. **A family list with no refinement shows an
  empty "Also counted" row.** Before this wave a combined list existed only when a refinement was
  chosen, so "Also counted" always had chips after it. Now most lists have none: coding, and an
  everyday question with no language word. The label is drawn anyway, followed by an empty horizontal
  scroll view. **Failure scenario.** "Which model writes code best?": both coding lists open with
  "Also counted" and nothing after it. **Fix.** Draw the label and the chips only when
  `!view.refinements.isEmpty`. B1's "built from N boards" line can take that place.

- **M4** `ios/ModelRanking/ContentView.swift:186` with `AnswerPlan.swift:130` and `select(_:)` at
  `ContentView.swift:984-995`. **The combined list is not the default on a surface the reader picks,
  or at launch.** `select` sets `routing = nil`, and `answerPlan` returns `.cards` without an outcome.
  So a surface chosen from "Change" or from an alternative, and the launch screen ("Showing: Coding"),
  show only the primary board's answer, with no toggle to the combined list. D-188 clause 5 and plan
  row W4 say "the default answer on every surface". **Failure scenario.** The reader opens the app and
  sees SWE-bench's cards for coding, not the product's own list. They tap "Change", pick Mathematics,
  and see one board again. **Fix.** Plan the selected `task` with an outcome of its own (no
  refinements, no words), so the family list is the default there too. Or record in D-188 clause 5 and
  the PRD that the default applies to asked questions only.

- **M5** `ios/ModelRanking/ContentView.swift:1070-1086` and `:534-537`,
  `ios/ModelRanking/Engine/Language.swift:592-598`. **The glow and the caption follow their state
  only at first appearance, and only as two values.** `IntelligenceGlow` reads `still` once, in
  `onAppear`. If the reader turns Reduce Motion on while the screen is open, the `repeatForever`
  rotation keeps turning, because nothing stops it. The caption is a yes/no on `.available`. A phone
  that can never run the model (`.notEligible`, every iPhone below the 15 Pro) reads "Apple
  Intelligence off", as if the reader had turned it off, and so does a phone still downloading the
  model. `OnDeviceState.help` already says each case correctly (`FrontDoor.swift:174-190`). **Fix.**
  Drive the angle from `TimelineView(.animation(paused: still))`, or reset `turn` in a transaction
  without animation in `.onChange(of: still)`. Make the caption a function of `OnDeviceState`, with one
  string per case in both languages.

- **M6** `docs/prd.md:424` and `:611-613`, `ios/EngineTests/FamilyPlanTests.swift:1`. **The PRD has
  no rows for the wave's REQ-IDs, and one row now says the opposite of the code.** Plan row W4 scopes
  REQ-CMB-005, REQ-APP-007 and REQ-APP-008. `git grep` finds none of them in `docs/prd.md`.
  `FamilyPlanTests.swift:1` cites REQ-CMB-005, a row that does not exist, and no test cites
  REQ-APP-007 or REQ-APP-008. REQ-APP-002 still says Ruling A's two coding surfaces are shown as
  cards and "never folded into one list", with the cards as its evidence. Coding now shows two family
  lists by default. REQ-CMB-002 and REQ-CMB-003 still say "on screen at M20-W4". **Failure scenario.**
  The closure's PRD check finds W4's criteria unrecorded, and REQ-APP-002 cites cards as evidence for
  a screen that no longer shows them first. **Fix.** Add the three rows (the default family list with
  "built from N boards", the glow and caption, the one-tap primary answer and Ruling A's two lists),
  each with its evidence. Update REQ-APP-002 for the two family lists, and REQ-CMB-002 and REQ-CMB-003
  to say what is now on screen.

- **M7** `ios/ModelRanking/ContentView.swift:374-378` and `:411-425`. **Coding's two lists share
  one "Show all" state and draw the access filter twice.** Both `combinedSection`s bind
  `showingAllCombined` and `onlyAPIOrOpenWeights`. A tap on "Show all 58" under the first list also
  opens the second (18 models on agentic-coding's served boards). One preference shows up as two switches, and the
  identifiers `combinedList`, `accessFilter`, `showAllCombined` and `seeTheBoards` each appear twice.
  **Failure scenario.** The reader expands the coding list to see one model. The agentic list below
  expands too, and pushes the primary-answer toggle and the ordering note further down. **Fix.** Keep
  the expanded state per surface (a `Set<String>` of surface ids). Draw the access filter once above
  both lists. Give each section's identifiers a suffix with its surface.

### PASS (what looks good)

- `answerPlan` keeps an engine with no `boards` (or an empty list) on today's plan
  (`AnswerPlan.swift:132`; `FamilyPlanTests.testAnEngineOlderThanM20KeepsTodaysPlan`). A family the
  standings lack throws in `combineFamily` and falls back to the cards (`:171-173`).
- D-188 clause 6 holds as amended. Where the model tier read the question, its choice stands, none
  included; otherwise the words choose (`:165`, killed by F1 and F11). `Refinements.read` is called
  only in `AnswerPlan.swift`, and the gate `test_only_the_answer_plan_reads_refinements_from_the_words`
  passes.
- An older board is a `.property`-weight note under the list. The loud `staleBoard` warning is not
  given to a family list (`:185`; `testAnOldFamilyBoardIsASmallNoteNotTheLoudWarning`, killed by F4).
- The primary toggle resets on every new question (`ContentView.swift:924`), and the paired plan has
  its own memo, so the two coding plans do not evict each other.
- Privacy: nothing typed reaches the engine. The question is used only in `planInputs` and
  `Refinements.read`, on the device. `EngineClient`, `load()` and the request are unchanged, and
  `test_router_hints.py` and `test_ios_client_contract.py` pass (D-126, D-160, D-167 clause 1).
- Accessibility: the glow is `accessibilityHidden` and never takes a tap. The caption is a `Text` at
  `.caption2`, which scales with Dynamic Type. The toggle is a `Button` whose label is its sentence, in
  both languages (`UITextLanguageTests`).
- `36dad00` is right to pick the paired surface as the one not routed, and to show both lists or
  neither.

## Acceptance criteria evidence

- Combined list by default: `AnswerPlan.swift:131-135`, `ContentView.swift:201-209`;
  `FamilyPlanTests.swift:37-44`. Not for a selected surface or at launch (M4).
- "Built from N boards" with dates: **not met** (B1).
- An older board as a small note on its own line: `AnswerPlan.swift:39`, `Notices.swift:260-261`;
  `FamilyPlanTests.swift:84-98`.
- One tap to each board's place: `ContentView.swift:428-443` → `CombinedDetail` (`:1540-1552`).
- Single-board answer one tap away: `ContentView.swift:353-360`, `:201-213`;
  `ScreenPathTests.swift` (the coding toggle test, simulator only).
- Ruling A, two lists and neither leads: `ContentView.swift:187-209`; no Engine test (M2).
- #208: `ContentView.swift:533-545`, `Language.swift:592-598`; partly met (M5).
- #199: **not met** (M1).

## K.8 contract drift check

```
$ grep -n 'combineFamily(\|FamilyList\b' ios/ModelRanking/Engine/AnswerPlan.swift ios/ModelRanking/Engine/Combine.swift
ios/ModelRanking/Engine/AnswerPlan.swift:171:    guard let list = try? combineFamily(standings, boards: boards, asOf: asOf), !list.entries.isEmpty else {
ios/ModelRanking/Engine/Combine.swift:126:struct FamilyList: Equatable {
ios/ModelRanking/Engine/Combine.swift:146:func combineFamily(_ standings: Standings, boards family: [String], asOf today: Date) throws -> FamilyList {
$ grep -n '"primary_board"\|"boards":' src/app/adapter/main.py
1355:                "primary_board": spec.primary_source,
1359:                "boards": list(FAMILIES[spec.id]),
```
- `AnswerPlan.swift:178-181` maps `FamilyEntry` to `CombinedEntry`, as plan §5 says. `primary_board`
  keeps its meaning. Verdict: OK. (`familyPlan` takes the primary as `family[0]` and never reads
  `primaryBoard`. W1's `test_every_surface_has_a_family_led_by_its_primary_board` is what holds the two
  equal.)

## K.9 candidates spotted outside this wave's scope

- **K1** `docs/prd.md:427`. REQ-APP-005 still describes the old rule: `Combine.swift` "orders the
  models every chosen board ranks by the sum of their positions". Since W2, the family list uses
  half-coverage and the mean percentile. The record now states the opposite of the code that W4 puts
  on screen. Bug (record). Fix: restate it as D-188 clauses 2 and 3.
- **K2** `ios/ModelRanking/ContentView.swift:1515-1556`. `CombinedDetail` draws every entry, with every
  position, in a non-lazy `VStack`. Before M20 a combined list was the intersection, a few dozen rows.
  A family list is up to 215 models (`web-dev`, D-188 clause 2), each with up to four positions. Fix:
  `LazyVStack`, and per-model detail if a reader needs to find one model. Enhancement.
- **K3** `ios/ModelRanking/ContentView.swift:79`. `onDevice` is read once, when the view is built. A
  model that finishes downloading, or Apple Intelligence turned on during the session, leaves the glow
  and caption wrong until the next launch. The help line has the same issue. Fix: read the state
  again on `scenePhase` becoming active. Bug, minor.

## Risks queued to next M

- **R1** `ContentView.swift:349` judges the day as `Calendar.current.startOfDay(for: Date())` (local).
  `isStale` counts whole UTC days (`Combine.swift:195-198`). East of UTC (the owner is at UTC+3), a
  board crosses the 90-day line one day late. A test of `planInputs`' day at 00:30 local in Istanbul,
  against a board dated exactly 91 days before, would show whether this is real.
- **R2** The glow is a `repeatForever` angular gradient under a blur, on the home screen, for as long
  as the app is open on a device with Apple Intelligence. Its GPU and energy cost is unmeasured. An
  Instruments energy trace on the owner's phone, with the glow on and off, would show whether it
  matters.
