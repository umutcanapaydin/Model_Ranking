---
record_type: review
id: m18-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# M18-W2 Code Review: screen quality

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `d080060..3ad7dc1`, 12 commits, 49 files, +2638 / -157. `d080060` is the merge-base
with `origin/main`; the range holds no merge.
**Risk tier:** HIGH (`docs/plans/m18-wave-2-plan.md:11-14`; `m18-plan.md:54` says MED). The wave
touches `ios/ModelRanking/Engine/EngineClient.swift` (a security glob) and adds a Debug-only launch
hook. D-172: no security seat on the wave; this seat checked the fail direction of every gate the
wave added or changed instead.
**Model routing (HIGH, advisory):** author-family: claude (`GP-Agent: claude-code/local-lane`) /
reviewer-family: claude-opus (fallback: no second family available to this seat)
**Fresh context:** I started with none of the authoring context. I read the base-ref policy, then
both plans and D-175/D-176, then the code diff, and only then the commit messages and #63's thread.
The one-line commit subjects were visible in `git log` from the start.

**Summary.** The wave does what its plan says, and the code I read is correct where it matters most:
`combine` gives the same ranks in O(n log n), the response is streamed and cut at its route's
ceiling, the release gate refuses a launch-argument read, and the notices are composed in both
languages with the same numbers and no source ids. Every fix I mutated was held, except in four
places. Nothing blocks. Eight MINORs:
1. **M1.** No test holds #56's own property: a mutant that buffers the whole stream and checks its
   size afterwards passes every test and pin.
2. **M2.** An answer whose evidence could not be read is now said, in both languages, as "no
   evidence to rank ... a gap in the evidence, not a result". The engine's sentence was true; the
   app's is not. REQ-APP-003 and REQ-LOC-001 are marked MET over it.
3. **M3.** #72's phone-copy half (the milestone plan's "or a stale phone copy") was dropped without
   an amendment or a decision.
4. **M4.** The view half of #67 and #72 is held by text pins that pass a `nil` health and a
   disclosure list inside a branch, the defect class #67 names.
5. **M5.** The Release gate refuses launch arguments; the launch environment passes it.
6. **M6.** `UITests.local.xcconfig` is described as git-ignored and is not.
7. **M7.** The "Change" UI test taps the second button in the whole tree and asserts no choice.
8. **M8.** Two record slips: a stale `:518` in REQ-API-001, and REQ-LOC-001 named by no test.

**Policy.** `.claude/agents/Code-Reviewer.md` and `.agents/rules/practices.md` were read from
`d080060`. `git diff --stat d080060 3ad7dc1 -- .claude .agents permission-matrix.md .github
Dockerfile fly.toml` is empty. `docs/decisions.md` only gains lines (112 added, 0 removed): D-175
and D-176, each with status, context, decision, mitigation and revisit.

**How I worked.** Everything ran in this seat's detached worktree at `3ad7dc1`. The worktree's
`.venv` is a link to the author's, so I backdated this tree's `pyproject.toml` mtime (content
unchanged) so that `make install` would not reinstall into it, and ran Python with
`PYTHONPATH` set to this tree's `src`.
1. **Gates at `3ad7dc1`.** `make check-fast`: **PASS, rc 0**, six legs.
   1. pytest: **1658 passed, 25 skipped**; coverage floor PASS, 42 modules.
   2. lint, typecheck (strict mypy) and the records leg (check-records, wave-check-all,
      conformance and the rest): PASS.
   3. `client_decl_gate.py`: self-test, then PASS, 18 files in 4 configurations. Release 2201
      declarations, Debug 2206: the five Debug-only ones are `LaunchRouting.swift`'s.
   4. `swift test --parallel` judged by `swift_xunit_gate.py`: **415 tests**, exactly the manifest.
2. **Mutants: 17 in-place edits**, each restored with `git checkout --` on its file and checked with
   `git diff --quiet`.
   1. **11 broke a fix, and a test or gate went red:** the binary search taking `<=` (205
      failures in the property oracle); `data.count <= ceiling`; the `EngineError` rethrow removed;
      the stale board dropped from `CombinedView.disclosures`; the memo's equality short-cut
      removed; the value-window filter in `PickCard.reasons` disabled; the Turkish page grouping
      back to `,`; the card notices' staleness back to the engine's English; the `#if DEBUG` around
      the launch-argument read removed (rc 1, both Release configurations); the app target syncing
      `UITests`; the UI target typed as a framework.
   2. **4 survived, and they are findings:** buffer-then-check in `EngineClient.read` (**M1**);
      `primaryHealth: nil` in the view (**M4**); the combined disclosures inside
      `if showingAllCombined` (**M4**); a Release launch-environment read (**M5**).
   3. **2 were probes:** the UI target also syncing `ModelRanking` passes the folder gate, which is
      harmless (the gate reads that folder); and a temporary Swift test, deleted after, printing
      what the app says for an answer the engine could not read (**M2**).
3. **Engine probes on today's artifact**, read-only through `TestClient`: every surface's notices
   and facts, the boards payload size (513,532 bytes) and its accessibility values.
4. **Read only:** issues #56, #63, #67, #69, #70, #72, #74, #78, #95, #96, #112, #113.
5. **Not done, by this seat's rules:** no `xcodebuild`, `simctl` or simulator, so no `make ui-test`
   (**R1**); no installer, `launchctl`, socket, commit, push or GitHub write.
6. **Tree:** clean apart from this file.

## Verdict
PASS WITH FINDINGS

**No BLOCKING, eight MINOR (M1–M8), three K.9 (K1–K3), two risks (R1, R2).** I recommend fixing
M2, M4 and M5 in this wave: M2 is a sentence the app now makes up on a real engine path, and M4
and M5 are gates this wave added that do not yet refuse what they name.

## Findings

### BLOCKING (must fix before this wave closes)
- none

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/EngineTests/EngineClientTests.swift:552-604`, `:227`; `ios/ModelRanking/Engine/EngineClient.swift:323-339`; `tests/unit/test_ios_client_contract.py:564`. **No test holds #56's property, that the read stops at the ceiling while it streams.**

  P5's acceptance check is "A response is cut off at its route's byte ceiling while it streams",
  and #56's expected behaviour is "Reading stops at a per-route byte ceiling". The code does that.
  Nothing would notice if it stopped doing it. Mutant: `read` appends every byte, then checks
  `data.count <= ceiling` after the loop, and the declared-length guard is deleted. That is a whole
  read with a size check afterwards, the defect #56 names. Results:
  1. `swift test --filter 'ResponseCeilingTests|EngineClientDecisionTests|BoardsRequestTests'`:
     **17 tests, 0 failures**;
  2. `test_every_response_is_read_through_its_routes_ceiling` and the redirect pin: **2 passed**.

  Why: `StubProtocol` answers with `headerFields: nil` and one `didLoad` of the whole body. So
  `expectedContentLength` is -1, the declared-length branch (`:325`) never runs, and a streamed
  read cannot be told from a whole one. The Python pin holds the call's shape (`session.bytes`,
  `read(bytes, …, upTo: byteCeiling(for: path))`), not what `read` does inside.

  What does hold, by mutant: an off-by-one ceiling, and the `EngineError` rethrow removed (each
  fails 2 ceiling tests); `session.data(` or a second session call (the pin, as the author showed).

  One more point. An oversized refusal (a non-200 body over the ceiling) becomes `undecodable`, so
  the status is lost and the screen's remedy is "Updating the app is the fix". That is
  fail-closed, and acceptable, but it is not stated anywhere.

  **The fix:**
  1. Add a stub case that sends `Content-Length` above the ceiling, and assert the refusal arrives
     with no body delivered.
  2. Add a stub that delivers the body in chunks and records whether `stopLoading` ran before the
     last chunk (the cancel).
  3. State the refusal-to-`undecodable` choice in the `read` doc comment.

- **M2** `ios/ModelRanking/ContentView.swift:202`, `:715-719`; `ios/ModelRanking/Engine/Notices.swift:37-41`, `:143-160`; `src/app/adapter/main.py:1137`, `:1149`. **An answer whose evidence could not be read is said as an evidence gap, in both languages.**

  The engine has three reasons for an empty answer, not two:
  1. nothing reached the ranking;
  2. nothing fits the budget;
  3. `"This surface's evidence could not be read."` (`main.py:1149`), on a `sqlite3.DatabaseError`
     while serving. Its `source_health` then has `sources: []` and the notice "This surface's
     evidence could not be read; freshness is unknown." (`:1137`).

  The app composes both sentences without a fact:
  1. `emptyAnswer` runs only when `picks` and `ranking` are both empty (`ContentView.swift:202`),
     and passes `rankedNothing: answer.ranking.isEmpty` (`:718`), which is therefore always true.
     Reason 2 arrives with a non-empty ranking and never reaches this view. So the
     `rankedNothing: false` branch is dead, and reason 3 is said as reason 1.
  2. `staleSentence` says any stale health with no sources as "No evidence source for X is in the
     served data" (`Notices.swift:37-41`).

  A temporary Swift test, deleted after, decoded that answer and printed what the screen would say:
  ```
  english reason: This surface has no evidence to rank: nothing on SWE-bench Verified reached the ranking in the served data. This is a gap in the evidence, not a result.
  english notices: ["No evidence source for SWE-bench Verified is in the served data, so how fresh it is cannot be told."]
  turkish reason: Bu alanın sıralayacak kanıtı yok: ... Bu bir sonuç değil, kanıttaki bir boşluk.
  ```
  Before this wave, the screen showed the engine's true sentence (in English). Now it shows a false
  cause in both languages. This breaks three things:
  1. D-176 clause 4, "an unknown kind … shows the engine's English";
  2. REQ-APP-003's "`unavailable_reason` … is visible", which this wave marks MET (`docs/prd.md:418`);
  3. the M7-W1 finding `main.py:1165-1175` records, "a false cause served beside the true one".

  `NoticesTests.swift:109` holds a two-way distinction the screen never makes.

  **The fix:**
  1. Either serve a reason code beside `unavailable_reason` (additive, and needs an ADR line in
     D-176), or show the engine's English unless the answer is the known no-evidence case.
  2. Do the same for a no-source health whose notice is not the engine's no-source notice.
  3. Pin both with a test fed the engine's three empty answers.
  4. Until it lands, REQ-APP-003 and REQ-LOC-001 are PARTIAL.

- **M3** `docs/plans/m18-plan.md:67`; `docs/plans/m18-wave-2-plan.md:27`, `:62`; `ios/ModelRanking/Engine/StandingsStore.swift:79-89`. **#72's phone-copy half was dropped without an amendment or a decision.**

  The signed milestone plan's W2 bullet reads "A stale board (or a stale phone copy) is said on the
  combined list". #72's thread records why: the M17 milestone review (M2) widened it, because after
  a failed `/v1/boards` fetch, `StandingsStore.current` serves stored standings of any age
  (`:89`) with no notice.

  The wave plan narrowed this to "a stale board" (`:27`, `:62`), and D-175 records no decision on
  it. Nothing in the app reads `fetchedAt` outside the store (`grep -rn fetchedAt
  ios/ModelRanking` finds only `StandingsStore.swift`). The surface's own board is covered. That
  was #72's offered direction 1, so not judging the refinement boards per board is within the
  issue.

  **The fix:**
  1. Either add a `.stalePhoneCopy(age)` disclosure to `CombinedView` when the kept copy is older
     than `maxAge`, held like `.staleBoard`;
  2. or amend the plan, and keep #72 open (or file the phone-copy half) rather than close it.

- **M4** `ios/ModelRanking/ContentView.swift:176`, `:385`; `tests/unit/test_ios_client_contract.py:124-146`. **The view half of #67 and #72 passes a `nil` health and a branch-wrapped disclosure list: #67's own defect class.**

  P4 is met on the plan. `AnswerPlanTests.swift:164`, `:181` and `:197` hold every
  `CombinedDisclosure`, and the mutant that drops the stale board fails two of them. The view
  side is held by a text pin, and two mutants of `ContentView.swift` pass the text pins:
  1. `primaryHealth: nil` in place of the answer's `sourceHealth` (`:176`): **56 passed** across
     `test_ios_client_contract`, `test_ios_visual_contract`, `test_router_hints` and
     `test_engine_address`. The pin (`:139`) asks for the label `primaryHealth:`, not its value.
  2. The disclosure list (`:385`) wrapped in `if showingAllCombined { … }`: **34 passed** in
     `test_ios_client_contract` and `test_ios_visual_contract`. The regex finds the call wherever
     it sits in the section.

  Coverage of each:
  1. Only `make ui-test`, which no gate runs, would catch (2): `ScreenPathTests.swift:97` reads
     "The app's own list".
  2. Nothing catches (1). No UI test reaches a stale board, because the scripted French path's
     `assistant` board is fresh today.

  #67's issue asks that "a disclosure requirement fails when a path to the main answer skips it",
  and REQ-APP-003 is marked MET on "a gate refuses one said by hand".

  **The fix:**
  1. Move the health lookup into an Engine function that the plan test drives, or pin the
     argument's value, not its label.
  2. Make the pin refuse the call under any conditional inside `combinedSection`, for example by
     brace depth.
  3. Or say in REQ-APP-003 that the view half rests on `make ui-test`.

- **M5** `scripts/client_decl_gate.py:323`, `:392`; `ios/ModelRanking/LaunchRouting.swift:9-16`; `tests/unit/test_client_decl_gate.py:85`. **The Release gate refuses launch arguments; the launch environment passes.**

  D-175 clause 3 says Release builds carry no hook to steer the app from outside. `DEBUG_ONLY`
  names `ProcessInfo.arguments`, `CommandLine.arguments` and `CommandLine.unsafeArgv`.
  `XCUIApplication.launchEnvironment` is as easy to set as `launchArguments`. The mutant:
  `forThisLaunch` reads `ProcessInfo.processInfo.environment["UITestRouting"]` after the
  `#endif` and hands it to `ScriptedModelRouter`. Results:
  1. `client_decl_gate.py`: **PASS, rc 0** (Release 2207 declarations);
  2. the text gates: **57 passed**.

  Controls:
  1. The same read through launch arguments, with `#if DEBUG` removed, is refused in both Release
     configurations, rc 1.
  2. `getenv` is refused already: it resolves in `_DarwinFoundation3`, which is not on the module
     list. I checked this with a probe dump outside the tree.

  A Release build also honours `-language` through `@AppStorage("language")` (the argument domain
  of `UserDefaults`). That is by design, and `test_router_hints.py` allows exactly one
  `@AppStorage`.

  **The fix:**
  1. Add `ProcessInfo.environment` to `DEBUG_ONLY`, with a canned case beside
     `test_client_decl_gate.py:85`.
  2. Write the `-language` exception into D-175's "as built" note.

- **M6** `ios/Config/UITests.xcconfig:2-4`; `.gitignore:72`. **The UI target's local override is described as git-ignored and is not.**

  The xcconfig says a personal team can override its settings "in a git-ignored file", and it
  includes `UITests.local.xcconfig`. `.gitignore` ignores only `Engine.local.xcconfig`, and
  `git check-ignore ios/Config/UITests.local.xcconfig` returns 1. A team id written there would be
  committed, which is #93's rule. The Engine half is held (`test_engine_address.py:27`).

  **The fix:** add the line to `.gitignore`, with the same assertion.

- **M7** `ios/UITests/ScreenPathTests.swift:126-132`; `ios/ModelRanking/ContentView.swift:581`. **The "Change" UI test taps an arbitrary button and asserts no choice.**

  `testChangeOpensTheChooserAndAChoiceIsShown` taps `app.buttons.element(boundBy: 1)`, the second
  button in the whole tree, then asserts only that `change` exists. The chooser is a
  medium-detent sheet (`.presentationDetents([.medium, .large])`), so the home screen and its
  toolbar stay in the tree and on screen above it. That has two consequences:
  1. index 1 need not be a surface;
  2. `change` can exist while the sheet is still up.

  Nothing asserts that a surface was chosen, or is shown, which is what the test's name and P1's
  "Change" path claim. I read this; I could not run it (**R1**).

  **The fix:**
  1. Give each choice an identifier (`surface.coding`, `surface.vision`, and so on).
  2. Tap one that differs from the current surface.
  3. Assert that the chooser's navigation bar is gone and that the chosen surface is shown.

- **M8** `docs/prd.md:377`, `:480`. **Two record slips.**
  1. REQ-API-001 cites `test_api_v1.py:512, :521`, then says "which :518 also asserts". `:518` is
     now an assertion in the test before; the budgets test is `:521`. `3ad7dc1` re-pointed the
     citations and missed this one in the prose.
  2. REQ-LOC-001 moves to MET, but no test names it (`git grep REQ-LOC-001 -- tests ios` is
     empty). The D-176 tests cite D-176 and #63 only. Seed E.2 asks for a citing comment. Add it to
     `NoticesTests.swift`'s header and to `test_why_facts.py:135`.

### PASS (what looks good)

- **#74 is correct and O(n log n).** `countBelow` is a standard lower bound over the board's
  sorted shared positions (`Combine.swift:74`, `:100`). Strict `<` matches the old
  `filter { $0.position < … }.count`, ties included. The `<=` mutant fails 205 assertions in
  `CombinePropertyTests`' independent oracle. `common` is a `Set`, and no other step is quadratic.
  The new sort is permitted by name (`SORTING_PERMITTED`, `("Combine.swift", "placed")`).
- **#56's code is right by reading.**
  1. There is one session call (`EngineClient.swift:275`), and its delegate is passed. A task
     delegate is retained by its task, so it cannot be dropped.
  2. The URLError mapping (timeout, ATS, offline, unreachable) is unchanged. It now also covers an
     error thrown mid-stream, because `read` runs inside the same `do`.
  3. `EngineError` is rethrown before the URLError catch, so a refusal is not flattened.
  4. The ceilings are 256 KiB, 1 MiB and 4 MiB, against 4,300, 47,920 and 513,532 bytes served
     today (I measured the boards payload: 513,532 bytes). A route nobody sized gets the smallest.
  5. A compressed body is bounded too: the bytes counted are the ones `URLSession` hands over,
     after any decompression.
- **D-176's engine half is exact.** `close_call_fact` is set beside the sentence from the same
  `shown` (`recommend.py:527`), so the fact and the prose cannot disagree. It is in
  `PUBLIC_ANSWER_FIELDS` and `ANSWER_KEYS`, and the ADR records the payload move. On today's
  artifact, five surfaces carry a close call (assistant 5.2 Elo, expert 0.2, mathematics 0.8,
  abstract level, vision 5.4 Elo), and each fact's model is in its answer's ranking. So the app
  composes all five.
- **The Turkish says what the English says.** I compared every pair in `Notices.swift`, the
  failure screen, the blurbs, the filter, the range note and tied places, and the #95 prompt
  against `Info.plist`. The same numbers appear in both (also held by `NoticesTests.swift:158`). No
  source id is said, and no formal register remains: a grep for `-sunuz`, `-iniz`, `-ın`,
  `dokunun` and similar forms over the client finds none. `orderingSentence`'s copy is held equal
  to `ORDERING_NOTE`. #96's engine refusal shown as sent is the issue's own instruction.
- **The fallbacks hold where facts are missing.** A stale `stale_notice` beside a quiet
  `source_health` cannot happen today: both windows are 90 days, and the source holding the latest
  run is never younger by the wall clock than by the artifact's own clock. A close-call model outside the ranking, an unknown dating kind, and fewer than two
  efforts each show the engine's English. M2 is the exception.
- **#63 matches D-175's decisions, one by one.**
  1. Finding 1 is `pickCards`. The value-window reason is dropped only on a card that is the
     best, and a floor warning stays (`AnswerPlanTests.swift:307`, `:333`).
  2. Findings 5–8 and 11–14 are in the P3 commits, each with a test or a UI capture.
  3. Finding 9 is `rangeNote` and `tiedPlaces`.
  4. Finding A is ten rows.
  5. Findings 10 and B are filed as #112 and #113.
  6. P2's reproduction table is in #63's thread (2026-10-04).
- **#70.** `PlanMemo` re-plans only when the routing, primary board, removed refinements, health
  or standings stamp change. The stamp is bumped at the one write to `standings`
  (`ContentView.swift:897-898`). Strictly, the memo is consulted in `body`, not filled in
  `.onChange`. The cost #70 names is paid once per change, which is what the issue asked.
- **#78.** The filter's values match the served artifact: `API access` 104; `Open weights …` 120;
  `None` 87; `Hosted access (no API)` 1. It hides rows without re-ranking them, and says "N of M
  shown".
- **The UI harness is careful with the owner's machine.** `ui_test.sh` binds the engine to
  127.0.0.1 on its own port (8090, not the service's 8080) and serves a copy of the artifact. It
  refuses a port that already answers, and stops the engine on exit with a plain `kill`. It is in
  no gate, as D-175 says.
- **The folder gate reads every target now**, and fails closed on a target it cannot parse
  (`len(targets) == count == len(synced)`).
- **Discipline.**
  1. All 12 commits carry `GP-Task: M18-W2`, and none carries an attribution line.
  2. No `noqa` and no `type: ignore` were added. `AGENTS.md` is unchanged, at 127 lines.
  3. Every changed file maps to a phase or to an issue in the plan's table. There are no drive-bys.
  4. All 105 PRD citations this wave added or moved land on a test or definition line.

## Producers of hardened invariant(s)

| producer | invariant | citing test | gap |
|---|---|---|---|
| `EngineClient.fetch` → `read(_:declared:upTo:)` (`EngineClient.swift:275`, `:323`) | a response is read only up to its route's ceiling (#56) | `EngineClientTests.swift:573`, `:583`, `:593`, `:600`; `test_ios_client_contract.py:564` | stop-while-streaming and the declared-length branch (**M1**) |
| `EngineClient.boards()` → `FetchedStandings` | the same, 4 MiB | `EngineClientTests.swift:537` (older) | none |
| `LaunchRouting.forThisLaunch` (`LaunchRouting.swift:9`) | a Release build reads no launch input (D-175 cl. 3) | `client_decl_gate.py:392` on the Mac; `test_client_decl_gate.py:85` (canned, CI) | the launch environment (**M5**); CI sees only the canned case |
| `ScriptedModelRouter.route` (`ScriptedRouting.swift:20`) | a scripted answer passes `ModelOutputBoundary` | `RouterBoundaryTests.swift:283`, `:291`, `:297` | none |
| `CombinedView.disclosures` (`AnswerPlan.swift:29`) | the combined list owes its disclosures, a stale board first (#67, #72) | `AnswerPlanTests.swift:164`, `:181`, `:197` | the phone copy's age (**M3**) |
| `combinedSection` (`ContentView.swift:385`) and the health it passes (`:176`) | the view renders the plan's disclosures whole | `test_ios_client_contract.py:124`; `ScreenPathTests.swift:97` (local only) | a branch or a `nil` passes (**M4**) |
| `answerDisclosures` (`Notices.swift:198`) | card notices composed from facts, English when a fact is missing (D-176) | `NoticesTests.swift:28`–`:229` | none found |
| `emptyAnswer` → `unavailableSentence` (`ContentView.swift:715`) | the empty-answer reason, in the reader's language | `NoticesTests.swift:109` | the third reason is said falsely (**M2**) |
| `staleSentence` with no sources (`Notices.swift:37`) | staleness from `source_health` | `NoticesTests.swift:66` | the read-failure health (**M2**) |
| `EngineError.errorDescription(_:)` / `recovery(_:)` (`Language.swift:711`, `:724`) | the failure screen in both languages (#96) | `LanguageTests.swift:514`, `:525`; `FailureScreenTests.swift:40` (local) | none |
| `recommend()` → `close_call_fact` (`recommend.py:527`) | present exactly when `close_call` is; same values | `test_recommend.py:315`, `:398`; `test_why_facts.py:135`, `:152` | none |

## Acceptance criteria evidence

Per phase, against `m18-wave-2-plan.md:58-64`:
- **P0** → `docs/plans/m18-wave-2-plan.md`; D-175 `docs/decisions.md:3491`, D-176 `:3565`. Met.
- **P1 (#69)** → the target `ios/UITests/`, `ios/Config/UITests.xcconfig`, the scheme, `scripts/ui_test.sh`
  and `Makefile:255`. The paths: ask `ScreenPathTests.swift:60`, the combined list and the chip
  `:68`, the boards row `:84`, the detail `:134`, "Change" `:126`, and the failure screen
  `FailureScreenTests.swift:21`. Scripted routing: `RouterBoundaryTests.swift:283`, `:303`; the
  Release gate `client_decl_gate.py:323`, `:392` → `test_client_decl_gate.py:85`. "Each of
  M17-W5's two defects fails a test when re-introduced" is the author's statement (`82fec62`),
  not repeated here (**R1**). Met, with **M5**, **M6** and **M7**.
- **P2 (#63)** → `ScreenAuditTests.swift`, and the 14-row table on #63 (2026-10-04). Met.
- **P3 (#63, #95, #96)** → the D-175 decision list (`decisions.md:3531`); D-176.
  1. Notices: `NoticesTests.swift:28`, `:206`, `:229`.
  2. Wording, formats and register: `LanguageTests.swift:551`, `:556`, `:565`.
  3. Findings 9 and 13: `:585`, `:604`.
  4. Finding 1: `AnswerPlanTests.swift:307`, `:333`.
  5. The blend and the ordering copy: `test_ios_client_contract.py:149`, `:162`.
  6. #95: `test_engine_address.py:87`.
  7. #96: `LanguageTests.swift:514`, `:525`.

  Met, with **M2**.
- **P4 (#67, #72)** → `AnswerPlan.swift:29-35` → `AnswerPlanTests.swift:164`, `:181`, `:197`;
  `test_ios_client_contract.py:124`. Met on the plan; **M3**, **M4**.
- **P5 (#70, #74, #56)** →
  1. #70: `AnswerPlan.swift:199` → `AnswerPlanTests.swift:216`, `:223`.
  2. #74: `Combine.swift:74`, `:100` → `CombinePropertyTests` (oracle) and `:140` (cost).
  3. #56: `EngineClient.swift:192`, `:275`, `:323` → `EngineClientTests.swift:573`–`:600`, and
     `test_ios_client_contract.py:564`.

  Met in code; **M1**.
- **P6 (#78)** → `AnswerPlan.swift:228`, `:235`, `ContentView.swift:315-317` →
  `AnswerPlanTests.swift:367`, `:378`, `ScreenPathTests.swift:114`; decision `decisions.md:3558`.
  Met.
- **REQ-APP-003 MET** (`prd.md:418`) and **REQ-LOC-001 MET** (`prd.md:480`): the citations
  resolve, but M2 contradicts both on the read-failure path, and M4 qualifies REQ-APP-003's "a
  gate refuses one said by hand". I would hold both at PARTIAL until M2 is fixed.
- The milestone's W2 criterion (`m18-plan.md:31`): #63 reproduced and dispositioned, and a
  committed UI test drives the screen. Met; REQ-APP-002 stays PARTIAL (**K3**).

## Every file in the diff

`git diff --stat d080060 3ad7dc1`, 49 files. I read every file's diff in full. In `docs/prd.md`,
the citation moves were checked by script.
1. **Records (5).** `docs/decisions.md` (D-175, D-176); `docs/plans/m18-wave-2-plan.md` (new);
   `docs/prd.md` (REQ-APP-003 and REQ-LOC-001 to MET, 20 citation moves, **M8**);
   `.language-allow` (five Turkish-bearing paths, each with its reason); `Makefile` (`ui-test`).
2. **The UI target (8).**
   1. `project.pbxproj`: the target, its synced `UITests` folder, a dependency on the app, and
      the `tr` region.
   2. Two shared schemes. The app's scheme keeps `ios/app.sh`'s `-scheme ModelRanking` working
      now that a shared scheme exists.
   3. `UITests.xcconfig` (**M6**).
   4. `ScreenPathTests`, `FailureScreenTests` and `ScreenAuditTests` (**M7**).
   5. `scripts/ui_test.sh`.
3. **The app (16).**
   1. `ContentView.swift`: all of the wiring (**M2**, **M4**).
   2. `AnswerPlan.swift`: `PickCard`, the disclosures, the memo and the filter.
   3. `Combine.swift`: #74.
   4. `EngineClient.swift`: #56 (**M1**).
   5. `Notices.swift`: new (**M2**).
   6. `Language.swift`: #96, the blurbs and the register.
   7. `Detail.swift`: finding 8 and the blend.
   8. `Scores.swift`: `named:`.
   9. `Uncertainty.swift`: `readableDate` and `rangeNote`. `readableDate` indexes months only
      after `isoDate` has checked 1–12.
   10. `Router.swift`: page grouping per language.
   11. `FrontDoor.swift`: the register.
   12. `Models.swift`: the fact and `Equatable`.
   13. `ScriptedRouting.swift` and `LaunchRouting.swift`: D-175 cl. 3 (**M5**).
   14. `tr.lproj/InfoPlist.strings`: #95.
   15. `ios/EngineTests/test-manifest.txt`: +48 tests.
4. **Swift tests (9).** `AnswerPlan`, `CombineProperty`, `Detail`, `EngineClient`, `Language`,
   `Notices` (new), `RouterBoundary`, `Scores` and `Uncertainty`. The edits to existing assertions
   follow the intended wording changes ("Score 65.0 / 100" → "65.0 / 100", dates in words). None
   is weakened.
5. **Engine and gates (11).**
   1. `recommend.py`, `main.py`: D-176.
   2. `client_decl_gate.py` (**M5**).
   3. The tests: `test_api_v1`, `test_recommend`, `test_why_facts`, `test_client_decl_gate`,
      `test_engine_address`, `test_ios_client_contract` (**M1**, **M4**), `test_ios_visual_contract`
      and `test_router_hints` (synced folders).

## K.8 contract drift check

`git grep -n` at `3ad7dc1`, for the plan's four symbols (`m18-wave-2-plan.md:68-73`) and the ones
this wave added:
```
ios/ModelRanking/Engine/Combine.swift:47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
ios/ModelRanking/Engine/AnswerPlan.swift:111:func answerPlan(
ios/ModelRanking/Engine/Router.swift:602:struct TieredRouter {
ios/ModelRanking/Engine/EngineClient.swift:165:    static let localDefault = engineURL(from: Bundle.main.object(forInfoDictionaryKey: "EngineURL") as? String)
ios/ModelRanking/Engine/EngineClient.swift:192:    static func byteCeiling(for path: String) -> Int {
ios/ModelRanking/Engine/AnswerPlan.swift:167:func pickCards(_ picks: [Pick]) -> [PickCard] {
ios/ModelRanking/Engine/AnswerPlan.swift:199:final class PlanMemo {
ios/ModelRanking/Engine/Notices.swift:198:func answerDisclosures(_ answer: Answer, anchor: Double?, _ language: Language) -> [Disclosure] {
ios/ModelRanking/Engine/ScriptedRouting.swift:16:struct ScriptedModelRouter: QuestionRouter {
ios/ModelRanking/LaunchRouting.swift:9:    static func forThisLaunch() -> TieredRouter {
scripts/client_decl_gate.py:323:DEBUG_ONLY = ("ProcessInfo.arguments", "CommandLine.arguments", "CommandLine.unsafeArgv")
src/app/adapter/main.py:933:        "close_call_fact",  # D-176
src/app/workflows/recommend.py:527:            close_call_fact = {"model": frontier[1].model, "behind_by": shown, "unit": spec.score_unit}
```
1. `combine`, `TieredRouter` and `localDefault` are unchanged at the lines the plan recorded.
2. `answerPlan` moved from `:86` to `:111`, and gained one defaulted parameter (`primaryHealth`).
   Every caller still compiles, and the memo passes it.
3. `/v1` gains `close_call_fact`, additively. The plan allowed that only with an ADR written in
   this wave, and D-176 is that ADR ("Moves the `/v1` answer payload, additively"). No route
   changed.

**Verdict: OK.** Nothing drifted silently.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/adapter/main.py:1491`; `ios/ModelRanking/ContentView.swift:266-270`. **The ordering note says "neither coding surface leads the other" under every surface's answer.** The engine sends `ORDERING_NOTE` on every `/v1/recommendations`; my probe found it non-empty for all 14 tasks. The screen shows it under the first answer whenever it is non-empty. So Assistant, Vision and the rest tell the reader that two coding surfaces are unordered. This predates the wave (the base showed `Text(orderingNote)` the same way). D-176 clause 3 kept "the engine decides whether", and the engine always says yes. This is a bug: send the note only for `task=coding`, or show it only when there is more than one answer.
- **K2** `ios/ModelRanking/Engine/Notices.swift:104-116`, `:134-140`; `ios/ModelRanking/Engine/Language.swift:620-628`; `ios/ModelRanking/Engine/Detail.swift` (effort level). **Effort names reach Turkish sentences untranslated.** "high", "max", "xhigh" and "unspecified" appear inside the Turkish effort-mix notice, the ranked-on line, the combined effort note and the detail's value. 10 of the 14 surfaces carry an effort-mix notice today. This is an enhancement: map the closed vocabulary to Turkish, falling back to the served word for anything unknown.
- **K3** `docs/prd.md:417`. **REQ-APP-002 still says "no UI test proves no default tab, no first-position emphasis (#69)".** The UI target exists now, and no case drives `task=coding`'s two answers. This is an enhancement: one `ScreenPathTests` case, then restate the row.

## Risks queued to next M

- **R1** `scripts/ui_test.sh`; `82fec62`, `00be65b`, `3edef25`, `b5e08e0`. **Every screen-level claim in this wave rests on `make ui-test` runs that no gate repeats and this seat could not.** That covers P1's "each of M17-W5's two defects fails a test when re-introduced", the 7- and 8-test passes the commits cite, and REQ-APP-003's `ScreenPathTests.swift:97`. D-175 keeps the target out of every gate. What would show it is real: the Tester running `make ui-test` at `3ad7dc1`, then once with each M17-W5 defect re-introduced, and once with M7's tap replaced by a named surface.
- **R2** `ios/ModelRanking/tr.lproj/InfoPlist.strings`; `tests/unit/test_engine_address.py:87`. **#95 is held by a file test only.** iOS shows the local-network prompt on a device, not for loopback in the simulator, so nothing has shown the Turkish text reaching the bundle. What would show it is real: the owner's iPhone run (`docs/owner-iphone.md`), with the phone set to Turkish, showing the English prompt.

*Filled by: Code-Reviewer seat (independent) · Date: 2026-10-04 · Commit range: `d080060..3ad7dc1`*
