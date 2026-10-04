---
record_type: review
id: m18-wave-3-tester-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 3 Tester Review (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records,
and it is none of the wave's three Code-Reviewer seats.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `93040ac..b6ab027`, 13 commits, 90 files, +33689 / -37. `wave/m18-w3` is stacked on
`wave/m18-w2` (#116, head `93040ac`), so the range is W3's own change. It holds no merge.
- 67 of the 90 files are run files, scorers and question sets.
- `b6ab027` is the fix round for the third review's M16 to M20. No review seat has read it. This seat
  is the first to test it.

**Risk tier:** HIGH (`docs/plans/m18-wave-3-plan.md:13-15`). The wave changes what the on-device
model's output decides (D-126), `RoutingOutcome`, and the screen.
**Code-Reviewer verdict:** PASS WITH MINOR (`docs/reviews/m18-wave-3-third-review.md`, at `5f0937b`).
The two rounds before it were BLOCKING; both are fixed. By D-172 there is no security seat on the
wave. The fault injection below is the HIGH tier's owed one.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`, read from `93040ac` with
  `git show`. It then read both plans, D-169 with its amendment, D-126, D-147, D-172, D-174, D-175,
  the PRD rows, the code, the tests, and last the three reviews. It has no memory of any authoring or
  reviewing session.

**Base-pinned policy:** `git diff --stat 93040ac b6ab027 -- .claude .agents permission-matrix.md
.github AGENTS.md CLAUDE.md` is empty. No commit carries an attribution line. Nothing in the range asks
anything of this seat.

## Verdict
BLOCKING

**One item blocks, T1, and this seat's test closes it.** Land the patch and T1 is gone.
- `Language.swift` is a touched module, and its line coverage fell from 82.48 % to 79.88 %. The
  four sentences D-169 puts on screen (the note, the question back and its two buttons) are run by
  no Swift test, and the Turkish ones by nothing at all.
- permission-matrix §11 lists "Coverage drop on touched module" as BLOCKING, and the Tester profile
  repeats it. The drop is behaviour, not a default value: four faults that change the words
  (L1 to L4) passed every Swift test and both Python gates that read the Swift.
- With `testTheNoteAndTheQuestionBackAreSaidInBothLanguages` the file is at 83.04 %, above its base.

**Everything else holds.**
1. Every acceptance criterion the wave touched has a citing test that passes at `b6ab027`, through
   the live entry point (`TieredRouter.route`, or the app on the simulator).
2. **R1 is closed.** `make ui-test` at `b6ab027`: 16 passed, 14 with the engine up and 2 with it
   down, as the author reported. Each of the four screen faults the review named turns a UI test red.
3. **R2 is measured.** Without the on-device model, the code's signals gave no note and no image
   override on 473 genuine rows, and one question back: the one the suite names.
4. The third review's M16, M17, M18 and M19 fixes are in the code. Each M16 to M18 test fails on the
   pre-fix `Reading.swift`, and each M19 mutant is now caught.
5. `make check-fast` passes at `b6ab027`, and again with this seat's tests in place.

**Eight MINORs (T2 to T9).** T2 to T8 are faults that stayed green. Each comes with a test that is
green at `b6ab027` and red on its fault. T9 is a records slip. The author lands each in this wave, or
files it.
- **T2:** the "no word" and small-talk bounds are held by nothing. A line in Cyrillic or Greek whose
  words are all long would get the note unasked if the script rule went.
- **T3:** six of the pasted-content rules, and three Turkish verb forms, are held by nothing.
- **T4:** the instruction signal's need for an object, and the third review's M17 fix for "komut"
  and "istem", are held by nothing.
- **T5:** five branches of the image rule are reached by no test.
- **T6:** no reading test drives an answering wording tier through `TieredRouter`. With that
  tier's answer left unread, no code signal applies to the questions it routes, and every test passes.
- **T7:** the model's "something else" is lost when the model also declines, and the model tier's
  hand-off of the field is pinned by nothing. A declined knowledge question would then be answered and
  kept in the gap register.
- **T8:** three faults on the held card fail only `make ui-test`, which no gate runs.
- **T9:** REQ-IMG-003 still gives 10 of 15; the code that ships gives 7 of 15 on that set (the third
  review's M20.1). One PRD pointer moved with this wave's lines.

**What was run.**
- `make check-fast` at `b6ab027`: rc 0. `make ui-test` at `b6ab027`: rc 0, 14 + 2.
- **104 faults** were injected, each in place, each restored and checked byte for byte (below): 89
  in the reading code, 4 in `Language.swift`, and 11 on the screen, 8 of them each followed by a
  `make ui-test` run.
  1. 3 are equivalent (N1).
  2. Of the other 101, the wave's own tests kill 71, `make ui-test` included.
  3. 30 survived the wave's tests. They are the subject of T1 to T7. T8 is three more that only
     `make ui-test` kills.
- **Advisory kill rate: 71 of 101 non-equivalent faults, 70.3 %.** Without `make ui-test`, which no
  gate runs: 68 of 101, 67.3 %. With this seat's tests in place: 101 of 101.

## Acceptance-criterion coverage (REQUIRED)

Every test named below is GREEN at `b6ab027`. Line numbers are at `b6ab027`; the new tests' lines are
in this worktree. Fault ids are defined under "Fault injection".

| criterion (phase, issue) | citing test (file:line) | entry | faults it kills | status |
|---|---|---|---|---|
| P0: the plan, D-169 brought in and amended, the sets and the baseline | `docs/plans/m18-wave-3-plan.md`; D-169 `docs/decisions.md:3270`, amendment `:3327` | records | n/a | MET (read) |
| P1 #66: each signal tested on its own; none fires on a genuine tuning question but the one named | `ReadingTests.swift:12`, `:22`, `:30`, `:44`, `:59`, `:91`, `:101`, `:110`, `:125`, `:178` (the named one at `:210`) | unit | W1, W2, W4 to W6, W9, W10, W12, S1, S4, S5, P1, P2, P8, P10, I1, I2, I4 to I6, I8, I9, V2, V4, M1, M4 to M9, M11, M13 to M16, M18 | GREEN. My R2 run agrees: 1 of 313 genuine tuning rows trips a signal, the named one. Gaps: T2 to T5 |
| P2 #66: `RoutingOutcome` carries the reading; the boundary maps the model's field; the decision table; the note and the question back on screen | `ReadingTests.swift:165`, `:227`, `:241`, `:248`, `:255`, `:263`, `:269`, `:279`, `:288`; `RefinementBoundaryTests.swift:105`; `test_router_hints.py:272`; `ScreenPathTests.swift:132`, `:146`, `:153`, `:169`, `:175`, `:182`; `test_ios_client_contract.py:806` | unit; `TieredRouter.route`; the app on the iPhone 17 Pro simulator against an engine on 127.0.0.1:8090 | D1 to D5, R1, R4, R7, R9, R10, R12 to R15, B1, B2, B4, B6, B7, U1 to U7 (UI), U1 to U4a, U7 to U10 (gate) | GREEN, 16 of 16 UI tests run by this seat. Gaps: T6, T7, T8 |
| P3 #73, #113: wording tuned on the tuning sets, three variants each | research record §3 | records | n/a | MET (read) |
| P4 #66, #73, #113: the bars on the held-out sets, twice | research record §4 to §6; D-169 amendment | records | n/a | #73 MET (34, 30 of 40). #66's catch bar and both #113 bars missed and stated. My recompute of all 260 post-fix rows with `b6ab027`'s code changes no reading (N3) |
| REQ-ASK-005 (new), D-169 | `ReadingTests.swift:12`, `:30`, `:59`, `:91`, `:165`, `:248`, `:288` (the PRD's list); `ScreenPathTests.swift:132`, `:146`, `:153`, `:169`, `:175`, `:182` | unit; `TieredRouter.route`; the app | as P1, P2 | GREEN. The PRD keeps it PARTIAL (the catch bar), and I agree |
| REQ-ASK-003, its carve-out for not-a-search input | `FrontDoorTests.swift:201`; `RouterBoundaryTests.swift:53`; `ReadingTests.swift:296` | `TieredRouter.route` with the real wording tier, and a scripted model | R4, R13 | GREEN |
| REQ-GAP-001, D-169 clause 5: not-a-search input is not kept | `ReadingTests.swift:334`; `test_ios_client_contract.py:806` (the held branch reaches no `gaps.`); `FrontDoorTests.swift:643`, `:719` | unit; text gate | G1, G2, G3, U8 | GREEN. Through `route` only the image case was asserted (`:305`); the new `ReadingTests.swift:441` adds a declined doubt. Gap: T7 |
| REQ-RTR-005, #113's rule | `ReadingTests.swift:296`, `:310`; `RouterBoundaryTests.swift:131`, `:170`; `FrontDoorTests.swift:388` | `TieredRouter.route` | R1, R4, R6, M5, M8 | GREEN. Gap: T6 (the wording tier) |
| REQ-IMG-003, the refusal half | `FrontDoorTests.swift:347`; `ReadingTests.swift:296` | the wording tier; `TieredRouter.route` | M5, R13 | GREEN. The PRD's number is not the shipped code's: T9 |
| REQ-APP-002, Ruling A's two coding answers on screen (#73's aim) | `ScreenPathTests.swift:214` | the app | n/a this wave | GREEN. #73 itself is wording, held by its measure, not a test (D-175 clause 3) |
| Milestone W3 criterion (`m18-plan.md:32`) | the rows above; research record | | | #73 met. #66 better than its baseline, short of its bar. #113 short of both bars. All three are stated for the owner |

**The PRD's evidence pointers.** `b6ab027` re-pointed the citations the third review named (M20).
- The rows this range adds or changes carry 77 `file:line` citations. Each lands on the `def`,
  `func` or `class` line of the test it names.
- The PRD as a whole carries 40 citations into files this range changed. 39 land on a test. The
  40th is a code pointer, REQ-BGT-001's `ContentView.swift:74`. This wave's three new lines moved it
  off the `budget` line, to `onDevice` (T9).

## Red→green on reported symptoms

No commit in the range is red-only: each phase carries its test with its fix. So this seat ran the
load-bearing tests against the code before each fix.

| symptom | red: the test on the pre-fix code | green at `b6ab027` |
|---|---|---|
| Third review M16: a photo read "into" text was overridden as a request to make one | `b6ab027`'s tests on `5f0937b`'s `Reading.swift`, in a scratch copy: `ReadingTests.swift:125` and `:310` fail on all seven of the review's lines | pass |
| Third review M17: a negated order, and `unutmayan`, `istemiyorum`, `komut satırı`, asked a genuine search | same run: `ReadingTests.swift:59` fails on all ten of the review's lines | pass |
| Third review M18: "CRDTs" read as no word; nonsense in capitals read as an acronym | same run: `ReadingTests.swift:101` fails on `CRDTs`; `:12` on `ASDF QWER`, `AAAAAAAA`, `SDFGHJ` | pass |
| Third review M19: "No" could record a gap or answer anyway; the held card's clearing in `apply` and `select` held by nothing | the review's own mutants, U8, U9, U3, U2: `test_ios_client_contract.py:806` fails on each. U2 and U3 also fail `make ui-test` (`ScreenPathTests.swift:182`, `:153`). The review saw all four pass | pass |
| #66: input that is not a search got a ranking | R13 (the model tier's answer unread) fails five tests; U4a (the held branch falls through to `apply`) fails six UI tests and the gate | pass |
| #113: a request to make an image was ranked as image reading | M5 and R13 fail `ReadingTests.swift:296` | pass |
| #73: coding questions missed `coding` | wording, measured by the probe on the owner's Mac; no test can show it red (D-175 clause 3) | research record §4 |

**Weakened or deleted tests.** I read every line the range removes under `tests/`,
`ios/EngineTests/` and `ios/UITests/`. There are seven.
1. The schema's field set gains `request`, and `RoutingOutcome`'s pinned fields gain `reading`. Both
   are stricter.
2. In `test_the_front_door_is_wired_to_the_logic_it_depends_on`, the old `body` (all of `ask`) is
   split into `asked` (`ask`) and `body` (the new `apply`). Each old assertion now reads the half
   that holds its code. None became vacuous: U1, U2, U3, U4a and U7 fail it.

No test was skipped, deleted or weakened.

## R1: the screen's held paths, run on the simulator

`make ui-test` at `b6ab027`, output to a file, exit code read: **rc 0, 16 passed.** With the engine
up, 14 of 14 (`ScreenPathTests`, 168.9 s). With it down, 2 of 2 (`FailureScreenTests`). The engine ran
on 127.0.0.1:8090 from a copy of the artifact (sha256 `5c6977a9c67c…`, unchanged after).

Then each fault, alone, followed by a full `make ui-test` run (all 16 tests each time):

| fault | the UI test that fails (file:line of the failing assertion) | the gate |
|---|---|---|
| U1: `confirm` reduced to `self.held = nil` | `testFindAModelAnswersTheQuestionAsRouted` (`:160`, "Find a model did not answer the question as routed") | fails (`:806`) |
| U2: `held = nil` removed from `select` | `testChangeFromTheNoteShowsTheChosenRanking` (`:190`, "the note stays over the chosen surface") | fails |
| U3: `held = nil` removed from `apply` | `testFindAModelAnswersTheQuestionAsRouted` (`:160`) | fails |
| U4a: the held branch in `ask` falls through to `apply`, so a ranking shows anyway | six: `testADoubtIsAskedAndNoIsTheNote` (`:134`), `testPastedContentTheModelDoubtsIsTheNote` (`:148`), `testFindAModelAnswersTheQuestionAsRouted` (`:155`), `testAnInstructionToTheAppIsAskedWhateverTheModelSays` (`:171`), `testNoWordIsTheNote` (`:177`), `testChangeFromTheNoteShowsTheChosenRanking` (`:184`) | fails |
| U4b: the held card shown, and the ranking under it anyway | `testADoubtIsAskedAndNoIsTheNote` (`:135`, "a ranking shows beside the question back") | **passes** (T8) |
| U5: the card's two faces swapped | the same six as U4a | **passes** (T8) |
| U6: a "Showing:" line above a held question | `testFindAModelAnswersTheQuestionAsRouted` (`:156`, "a surface is shown for a question not yet answered") | **passes** (T8) |
| U7: "No" leaves the question back up | `testADoubtIsAskedAndNoIsTheNote` (`:139`) | fails |

Every other UI test passed in each run (15 of 16 for one failure, 10 of 16 for six). So the UI target
is real: each held path has a test that sees its fault.

## R2: a phone without Apple Intelligence

**What was run.** A throwaway Swift test, in a scratch copy of `b6ab027` (never in this worktree),
deleted after its run. It read each set at run time and routed every row through
`TieredRouter(model: nil, similarity: SimilarityRouter())`, the shipping wording tier. It wrote only
the set, the row's index, its labels and the results, never a question, to a scratch file. This
record quotes no held-out question. `test_no_held_out_question_is_written_into_the_code_or_its_tests`
passes with this seat's tests in place.

**The genuine rows.** Every row of the surface, refinement, coding and image sets, and the `search`
or `genuine` rows of the not-a-search sets. 276 of the 473 were answered by the wording tier; the
other 197 (most of them Turkish) fell to the manual tier.

| sets | genuine rows | notes | questions back | image overrides |
|---|---:|---:|---:|---:|
| tuning (10 sets, the retired held-out sets included) | 313 | 0 | 1 | 0 |
| spent held-out: `notasearch_heldout_m18` | 40 | 0 | 0 | 0 |
| spent held-out: `image_heldout_m18` | 40 | 0 | 0 | 0 |
| spent held-out: `coding_heldout_m18` | 80 | 0 | 0 | 0 |
| **all** | **473** | **0** | **1** | **0** |

- The one question back is the colon doubt `ReadingTests.swift:210` names, from a retired set.
- **No image override, because the rule never fires on this tier.** The wording tier sent none of
  the 36 requests to make an image (15 + 15 + 6) to `vision`. So R2's worry, false overrides, is not
  real here. Its mirror is: see R7.
- The code's signals alone caught 13 of the 40 not-a-search inputs on the spent set: 3 notes and 10
  questions back. Knowledge questions: 0 of 10. See R8.

## Suite result
- **`make check-fast` at `b6ab027`: PASS, rc 0, in 67.6 s.** This seat's guard was first on PATH.
  1. lint, typecheck and records: PASS.
  2. test: **1657 passed, 25 skipped**. `coverage-floor`: PASS, 42 modules.
  3. client-decls: PASS, 19 files in 4 configurations.
  4. swift-test (parallel): PASS, **450 tests**, exactly the manifest.
- **`make ui-test` at `b6ab027`: PASS, rc 0**: 14 + 2 (above).
- **With this seat's tests added:** `make check-fast` PASS, rc 0: 1659 passed, 25 skipped; **460**
  Swift tests, exactly the manifest.
- **Coverage on touched code** (permission-matrix §11). Swift: `swift test --enable-code-coverage` on
  `git archive` copies of `93040ac` and `b6ab027` (450 tests at the head), read with `llvm-cov
  report`. The range changes no Python module; its Python files are tests.

| module (lines) | base `93040ac` | head `b6ab027` | head + this seat's tests |
|---|---|---|---|
| `Reading.swift` (new) | n/a | 99.36 % (2 lines unexecuted) | 100 % |
| `Router.swift` | 97.96 % | 98.15 % | 98.15 % |
| `FrontDoor.swift` | 99.45 % | 99.45 % | 99.45 % |
| `ScriptedRouting.swift` | 100 % | 100 % | 100 % |
| `Language.swift` | 82.48 % | **79.88 %** (T1) | 83.04 % |

The two unexecuted `Reading.swift` lines were the `arka plan` branch (`:163`, M2) and the aorist
joined to its particle (`:273`, V5). `ContentView.swift` is outside the Swift package; the UI run is
its evidence.

## Mocks / contract tests
- **`ScriptedModelRouter`** (`ScriptedRouting.swift:16`) is the canonical stand-in for the on-device
  model (D-175 clause 3). Its answer goes through `ModelOutputBoundary`, so a test cannot reach a
  verdict the boundary refuses. The wave's tests and UI table use it. B7 shows it carries `request`.
- **The real model** is measured by `ReadingProbe.swift` on the owner's Mac, not by tests. The schema
  it is given is held at `RefinementBoundaryTests.swift:105` (B6 dies). The one line that hands the
  model's verdict back to the boundary was held by nothing (B5): T7's pin holds it now.
- **The wording tier** has no shared stub. Each test file declares its own (K9). This seat's
  `Answering` follows the file's own `NoSimilarity`.
- **No new external integration.** No `/v1` change: a held reading sends no request.

## BLOCKING
- **T1** `ios/ModelRanking/Engine/Language.swift:672-693`; permission-matrix §11. **A touched module lost coverage: D-169's four sentences are run by no Swift test.**
   1. `notASearchNote`, `askBack`, `askBackFind` and `askBackNo` are new. No Swift test calls any of
      them. The UI tests find the card by its identifier, in English, and never read its words. The
      Turkish four run on no screen a test drives.
   2. `Language.swift` fell from 82.48 % to 79.88 % of lines (66.23 % to 62.96 % of functions).
   3. Four faults passed every Swift test and both Python gates that read the Swift: the Turkish note
      made the English one (L1); the Turkish and English question back swapped (L2); the note's one
      example dropped (L3), which D-169 clause 4 requires; "Model bul" on both Turkish buttons (L4).
      L1 and L2 are #63 finding 2, English on the Turkish screen.
   4. **The fix:** `testTheNoteAndTheQuestionBackAreSaidInBothLanguages` (`ReadingTests.swift:457`).
      It pins the English to D-169's own words, holds each Turkish sentence apart from its English,
      and holds the example's quotes in both languages. It kills L1 to L4 and takes the file to
      83.04 %.

## MINOR (the author fixes each in this wave or files it as an issue)

- **T2** `ios/ModelRanking/Engine/Reading.swift:32-38`, `:122-127`, `:294-305`. **The "no word" and small-talk bounds, and the rule for other scripts, are held by nothing.**
   1. W3 (four letters raised to five), W7 and W8 (the no-vowel bound moved either way), S2 (no
      word limit on small talk) and S3 (three words) each passed every Swift and Python test.
   2. W11 matters most. With the rule "a script beyond Latin is a word" removed, a line in Cyrillic
      or Greek whose words all have five letters or more reads as no word: the note, unasked, D-169's
      costliest class. The suite's own lines miss it. "Какая модель лучше для кода" passes on its
      short words, and "你好，哪个模型最好" passes through the acronym rule.
   3. **The fix:** `testTheBoundsOfNoWordAreTheDocumentedOnes` (`:356`),
      `testALineInAnotherScriptIsNotNoWordWhateverItsWordLengths` (`:366`) and
      `testSmallTalkIsAtMostSixWords` (`:373`). They kill W3, W7, W8, W11, S2 and S3.
- **T3** `Reading.swift:45-66`, `:260-277`. **Six pasted-content rules and three Turkish verb forms are held by nothing.**
   1. Under P4 (no 8-word bound), P5 (a named model before the colon no longer makes it a search),
      P6 (the English verb anywhere), P9 (the Turkish verb anywhere) and V1 (the aorist counts with no
      question particle), a genuine search is asked. Each passed every test.
   2. P5 is the second review's M12 fix. Its own test lines pass without it: "Best model to explain
      code:" has no order verb in its first two words, so the exclusion is never reached.
   3. Under P3 (no content needed after the colon), P7 (no "please" before the order), V3 (the ability
      form) and V5 (the aorist joined to its particle, `düzeltirmisin`), catches are lost or gained
      silently.
   4. **The fix:** `testPastedContentIsAShortOrderWithItsContent` (`:382`) and
      `testATurkishVerbCountsOnlyInARequestsForm` (`:395`). Five of their lines are genuine searches,
      and each must stay one. They kill P3 to P7, P9, V1, V3 and V5.
- **T4** `Reading.swift:78-112`. **The instruction signal's object, and the third review's M17 fix for "komut" and "istem", are held by nothing.**
   1. I3 (the object no longer needed) passed every test. Under it, two genuine searches are asked:
      `bana en iyi kodlama modelini göster` ("show me the best coding model"), and "Forget the price,
      which model writes the best code?".
   2. I7 puts back the pre-M17 prefix match for "komut" and "istem". It passed every test, because each
      of the review's lines also lacks a verb in a request's form, and fails on that. The fix was real;
      its test does not see it. Under I7, a genuine search is asked:
      `komut satırında çalışan bir kodlama modeli göster` ("show a coding model that runs on the
      command line").
   3. **The fix:** `testAnOrderNeedsItsObjectInTheSameSentence` (`:403`). It kills I3 and I7 (and I5).
- **T5** `Reading.swift:148-194`. **Five branches of the image rule are reached by no test.**
   1. M2 (`arka plan` with a removing verb), M3 ("draw me"), M10 (an image noun after "into", "into a
      poster"), M12 (a modifier just past the four-word window) and M17 (the Turkish verb by bare
      prefix) each passed every test. `Reading.swift:163` was never run.
   2. M17 is the costly one. `silik` (faded) starts like `sil` (delete). So a request to read a
      photo routed to `vision`, `fotoğraftaki silik yazıyı okuyan model hangisi` ("which model reads
      the faded writing in a photo"), would be overridden as unmeasured and kept in the gap register
      (the reviews' R4).
   3. **The fix:** `testTheImageRuleReadsEachOfItsForms` (`:415`). It kills M2, M3, M10, M12 and M17.
- **T6** `ios/ModelRanking/Engine/Router.swift:691`, `:710-713`. **No reading test drives an answering wording tier through `TieredRouter`.**
   1. R11 returns the wording tier's answer unread. Every test passed. The reading tests use a model,
      or a wording tier that never answers. The tests that route through the real wording tier
      (`UnmeasuredQuestionTests`, `FrontDoorTests.swift:201`) ask ordinary questions, which `read`
      leaves as they are.
   2. Under R11, on a phone without Apple Intelligence, no code signal applies to a question that tier
      routes: 276 of my 473 R2 rows. Nonsense and injections get a ranking there. That is the case
      D-169's amendment exists for ("signals decided in code apply on every tier").
   3. R3 makes the image override claim the model tier. It passed too. On the wording tier the
      notice then drops "Going by its wording" (M13-W3 review MINOR-5).
   4. **The fix:** `testTheWordingTiersAnswerIsReadAndKeepsItsTier` (`:426`), with a stub tier that
      answers. It kills R11 and R3.
- **T7** `Router.swift:590-597`, `:506-508`. **The model's "something else" is lost when it also declines, and the hand-off of the field is pinned by nothing.**
   1. B3 drops the verdict on the decline branch of `ModelOutputBoundary.outcome`. Every test passed:
      the boundary test uses a surface, never the decline.
   2. Under B3, a knowledge question the model declines and doubts reads as a search. It gets the chat
      ranking, and its text is kept in the gap register as a need, against D-169 clause 5. The
      research record says knowledge questions are #66's gap, so this is the likely case.
   3. B5 passes `request: nil` from `ModelRouter.route`. Every test passed, since no test can run the
      on-device model. Under B5 the schema asks the model for its verdict and the app throws it away.
   4. **The fix:** `testTheModelsDoubtCountsWhenItDeclines` (`ReadingTests.swift:441`), through
      `TieredRouter.route`, and the source pin
      `test_the_model_tier_hands_the_boundary_the_verdict_it_asked_for` (`test_router_hints.py:674`).
      They kill B3 and B5.
- **T8** `ios/ModelRanking/ContentView.swift:175-177`, `:507-511`, `:897-916`. **Three faults on the held card fail only `make ui-test`, which no gate runs (D-175).**
   1. U4b (the ranking rendered under the held card), U5 (the card's faces swapped) and U6 (a
      "Showing:" line above a held question) each passed every Python test and `make client-decls`.
      The Swift package does not compile `ContentView.swift`.
   2. This is the third review's M19.3 for the ranking under the card. The fix round pinned `apply`,
      `select` and "No", not these.
   3. **The fix:** `test_the_held_card_stands_alone_and_shows_the_face_its_reading_asks_for`
      (`test_ios_client_contract.py:1265`). It kills U4b, U5 and U6.
- **T9** `docs/prd.md:542`, `:479`; `docs/research/m18-w3-question-reading-probe-2026-10-04.md` §6. **REQ-IMG-003 gives the old code's number, and one pointer moved.**
   1. REQ-IMG-003 says the rule "on a held-out set ... caught 10 of 15". That was before the second
      review narrowed it. The third review's M20.1 asked for 7 of 15. `b6ab027` fixed M20's citations
      only.
   2. My recompute: every row of both post-fix runs, read again with `b6ab027`'s signals from the
      model verdict each row recorded. All 260 readings are unchanged, and the same 7 of 15 requests
      to make an image stay overridden. So 7 of 15, on a spent set, is the shipped code's number.
   3. §6 still does not say that 3 of the 15 got the `web-dev` ranking as if measured (M20.2's second
      half). The rule fires on all 3, but cannot reach `web-dev`.
   4. REQ-BGT-001 cites `ContentView.swift:74` for the `unlimited` budget. This wave's three new
      lines moved that line to `:77`; `:74` is now `onDevice`.
   5. **The fix:** the number, the sentence and the pointer. K7 (the third review) is the gate that
      would catch the pointer.

## Notes (no change required by this verdict)

- **N1** **Equivalent: R2, R5 and R8.**
   1. R2 drops `!outcome.unmeasured` from the image rule. A `vision` outcome is never unmeasured: the
      boundary and the wording tier set `unmeasured` only with the `assistant` fallback.
   2. R5 deletes `read.reading = outcome.reading` (`Router.swift:712`). It is a dead store; `:714`
      overwrites it, as the third review said.
   3. R8 reads the verdict on every tier. Only `ModelOutputBoundary` sets `reading`, so a non-model
      outcome always carries `.search`, and nil and false decide the same.
- **N2** **The review's mutants, re-run.** The third review's eight caught Swift mutants map onto
  R1, G1, D3, B4, R9, R7, B6 and M8, and each dies again. Its five screen mutants are my U8, U9, U3,
  U2 and U4b. Four now die in the gate; U4b dies on the simulator only (T8).
- **N3** **The research record re-scored for the head.** `b6ab027` changed `Reading.swift` after the
  last measured run (`postfix`, at `2d5f86a`). My recompute of all 260 post-fix rows changes no
  reading, and no image override. The §6 numbers stand for the code that ships (but T9's 10 of 15).
- **N4** **This seat's own setup slip, discarded.** My first head coverage run had no
  `scripts/router_probe/` in its scratch copy, so `testNoGenuineTuningQuestionTripsASignal` could not
  read its sets and failed. I re-ran it with the sets: 450 of 450. The figures above are from that run.
- **N5** **Not done by this seat, by its rules.** No installer, `launchctl`, commit or push. No crash
  construct in any probe or fault. The on-device model was not run. `ScreenAuditTests` was not run;
  it asserts nothing.

## K.9 candidates spotted outside this wave's scope

- **K9** `ios/EngineTests/*Tests.swift`. **The router stubs are private, one set per file.** Eight
  `QuestionRouter` stubs live in four files: `StubRouter`, `SpyRouter`, `DecliningModel`, two
  `Silent`s, `Fixed`, `Hanging`, `NoSimilarity`, and now this seat's `Answering`. There is a canonical
  model tier (`ScriptedModelRouter`) and no canonical wording tier. T6's gap grew in that space. This
  is an enhancement: one shared test file of tier stubs.
- **K10** `ios/ModelRanking/Engine/Language.swift`. **Many `UIText` sentences are run by no test in
  either language.** At `93040ac` 86 of 491 lines were unexecuted: the headline, the gap register's
  title and buttons, "Loading", the privacy line and more. T1 is this wave's share of it. #63 finding 2
  (English on the Turkish screen) can return there unseen. This is an enhancement: one test that walks
  every `UIText` sentence in both languages, as `testEveryComposedNoticeDiffersFromItsEnglish` does for
  the notices.

## Risks queued to next M

- **R7** `Router.swift:704-713`; #113. **On a phone without Apple Intelligence, #113's rule does
  nothing.** The wording tier sent none of 36 requests to make an image to `vision`, so the rule never
  fired (R2, above). On the spent image set it gave 5 of 15 a measured ranking (`abstract` 2, `web-dev`
  2, `assistant` 1); on the first image set 6 of 15. The rule cannot reach them: it reads only `vision`
  (the second review's B4). What would show it is real: the owner's question on #113 (the reviews' R5) carrying the
  numbers for both tiers.
- **R8** D-169 clause 6; the reviews' R5. **#66's catch rate without Apple Intelligence is a third of
  the bar.** The code's signals alone caught 13 of 40 on the spent set (3 notes, 10 questions back),
  against 32; knowledge questions 0 of 10. D-169 says the cost of that tier ("off-topic input still
  gets a ranking"), but not the number. What would show it is real: the owner deciding "whether to ship
  what holds" without it.
- The reviews' R1 is closed by this record. R2 is measured (above); its false-positive worry is not
  real on these sets. R3 to R6 stand as the third review wrote them.

## Fault injection (HIGH: mandatory)

**Harness:** scratch `w3t/mut.py`, with the faults in `reading_faults.json`, `ui_faults.json`,
`red_faults.json`, `lang_faults.json` and `ui_gate_faults.json`. For each fault it does the following:
1. It checks that the file it touches equals `HEAD`: `git hash-object` must equal
   `git rev-parse HEAD:<file>`.
2. It records the file's sha256 and saves its bytes.
3. It makes exact string edits, each required to match exactly once. Every edit was dry-run first
   for its match count.
4. It runs the checks:
   - a reading fault: `swift test --filter` on the reading, boundary, front-door and gap classes, and
     the two Python gates that read the Swift. If nothing fails: the whole Swift suite
     (`swift test --parallel`) and the whole Python suite (`-n auto`, with
     `MODEL_RANKING_REQUIRE_ARTIFACT=1`);
   - a screen fault: the client gate, then a full `make ui-test`, then (for U4b, U5, U6) the whole
     Python suite and `make client-decls`;
   - a `Language.swift` fault and V5: the whole Swift suite without this seat's class, and the two
     Python gates.
5. It writes the original bytes back **in place**, never with `git checkout` or `restore`.
6. It asserts two things: sha256 equals the pre-edit hash, and `git hash-object` equals HEAD's blob.
   It also records that `git status` shows the file clean.

**Every one of the 142 runs** says `restored: true` and clean. The runs: the 8 screen faults with
`make ui-test`; the 88 reading faults; 34 with this seat's tests in place (the 28 survivors, U4b, U5
and U6, and U8 to U10, first run there); V5 and L1 to L4; L1 to L4 again after the test was sharpened;
and U4b, U5 and U6 against the whole Python suite and `make client-decls`. After the last run, all 768 tracked files that this seat did not edit matched the sha256
baseline taken before the first fault (`shasum -c`; the 4 that differ are this seat's test files). The
artifact's sha256 was unchanged (`5c6977a9c67c…`). Every kill is a test assertion or a gate's refusal;
none is a compile error or a build failure.

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob that `git hash-object` matched):

| file | runs | sha256 (pre = post) | HEAD blob |
|---|---|---|---|
| `ios/ModelRanking/Engine/Reading.swift` | 85 | `1eea49b27cac` | `fd659a4161` |
| `ios/ModelRanking/Engine/Router.swift` | 28 | `f7dd224faf76` | `20552faf11` |
| `ios/ModelRanking/Engine/FrontDoor.swift` | 3 | `91e529b4d47b` | `c79f1b17e0` |
| `ios/ModelRanking/Engine/ScriptedRouting.swift` | 1 | `dcf37df71d60` | `74bab1e227` |
| `ios/ModelRanking/Engine/Language.swift` | 8 | `2add43661cfe` | `3fde5793a1` |
| `ios/ModelRanking/ContentView.swift` | 17 | `e3aaf221f87f` | `80472701c2` |

**The faults.** "Every Swift and Python test" means the 450 Swift tests and 1657 Python tests at
`b6ab027`. A cited line is the killing test's `func` or `def` line; "(new)" marks this seat's test,
which kills the fault when it is in place. Fault ids V1 to V5 are the Turkish verb forms.

| id | the fault | result | killed by |
|---|---|---|---|
| W1 | noWord: digits and punctuation alone are not no-word | KILLED | ReadingTests.swift:12 |
| W2 | noWord: the four-letter minimum lowered to two | KILLED | ReadingTests.swift:22 |
| W3 | noWord: the four-letter minimum raised to five (boundary) | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:356 (new) |
| W4 | isWord: the repeated/alternating-letter rule removed | KILLED | ReadingTests.swift:12 |
| W5 | isWord: the keyboard-run rule removed | KILLED | ReadingTests.swift:12, ReadingTests.swift:263 |
| W6 | isWord: the no-vowel rule removed | KILLED | ReadingTests.swift:12 |
| W7 | isWord: the no-vowel length bound 5 -> 6 (boundary) | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:356 (new) |
| W8 | isWord: the no-vowel length bound 5 -> 4 (boundary) | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:356 (new) |
| W9 | isWord: the acronym rule removed | KILLED | ReadingTests.swift:101 |
| W10 | isWord: the plural-s acronym drop removed (pre-M18) | KILLED | ReadingTests.swift:101 |
| W11 | isWord: scripts beyond Latin are no longer words by themselves | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:366 (new) |
| W12 | keyboard rows read one way only (reversed runs dropped) | KILLED | ReadingTests.swift:12 |
| S1 | smallTalk: any small-talk word suffices (allSatisfy -> contains) | KILLED | ReadingTests.swift:178, ReadingTests.swift:91 |
| S2 | smallTalk: the six-word bound removed | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:373 (new) |
| S3 | smallTalk: the bound 6 -> 3 (boundary) | SURVIVED (every Swift and Python test) → T2 | ReadingTests.swift:373 (new) |
| S4 | folds: the Turkish folding dropped | KILLED | ReadingTests.swift:125, ReadingTests.swift:59 |
| S5 | folds: the default folding dropped | KILLED | ReadingTests.swift:59 |
| P1 | pasted: three lines -> four | KILLED | ReadingTests.swift:30 |
| P2 | pasted: a code block no longer counts | KILLED | ReadingTests.swift:30 |
| P3 | pasted: content after the colon not required (>= 2 -> >= 0) | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P4 | pasted: the 1...8 words-before bound removed | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P5 | pasted: a named model or 'which' before the colon no longer makes it a search | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P6 | pasted: the English verb anywhere before the colon | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P7 | pasted: the English verb only as the first word (no 'please fix this:') | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P8 | pasted: the Turkish verb only as the last word | KILLED | ReadingTests.swift:110, ReadingTests.swift:30 |
| P9 | pasted: the Turkish verb anywhere before the colon | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:382 (new) |
| P10 | pasted: the Turkish verb by bare prefix (a noun from the verb counts) | KILLED | ReadingTests.swift:110 |
| I1 | instructs: role phrases ignored | KILLED | ReadingTests.swift:59 |
| I2 | instructs: an English order anywhere in its sentence (lead-in rule removed, pre-M17) | KILLED | ReadingTests.swift:59 |
| I3 | instructs: the object no longer required | SURVIVED (every Swift and Python test) → T4 | ReadingTests.swift:403 (new) |
| I4 | instructs: the verb no longer required | KILLED | ReadingTests.swift:178, ReadingTests.swift:59 |
| I5 | instructs: the whole text one sentence (verb and object may sit in two) | KILLED | ReadingTests.swift:59 |
| I6 | instructs: a Turkish verb by bare prefix (pre-M17) | KILLED | ReadingTests.swift:59 |
| I7 | instructs: 'komut'/'istem' objects by bare prefix (pre-M17) | SURVIVED (every Swift and Python test) → T4 | ReadingTests.swift:403 (new) |
| I8 | instructs: Turkish objects by whole word (`talimatları` no longer an object) | KILLED | ReadingTests.swift:59 |
| I9 | instructs: a Turkish order no longer counts | KILLED | ReadingTests.swift:59 |
| V1 | isTurkishVerb: the aorist counts without a question particle | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:395 (new) |
| V2 | isTurkishVerb: any suffix counts (bare prefix) | KILLED | ReadingTests.swift:110, ReadingTests.swift:59 |
| V3 | isTurkishVerb: the ability form dropped | SURVIVED (every Swift and Python test) → T3 | ReadingTests.swift:395 (new) |
| V4 | isTurkishVerb: the polite imperatives (-sene, -in) dropped | KILLED | ReadingTests.swift:110 |
| M1 | image: the 'background' branch removed | KILLED | ReadingTests.swift:125 |
| M2 | image: the Turkish 'arka plan' branch removed | SURVIVED (every Swift and Python test) → T5 | ReadingTests.swift:415 (new) |
| M3 | image: 'draw me' removed | SURVIVED (every Swift and Python test) → T5 | ReadingTests.swift:415, ReadingTests.swift:426 (new) |
| M4 | image: draw idioms not excluded | KILLED | ReadingTests.swift:125 |
| M5 | image: a form of `çiz` alone no longer counts | KILLED | ReadingTests.swift:125, ReadingTests.swift:296 |
| M6 | image: reading prepositions between the verb and the image ignored | KILLED | ReadingTests.swift:125 |
| M7 | image: a modifier after the image noun ignored | KILLED | ReadingTests.swift:125 |
| M8 | image: 'into' never reads (readInto ignored) | KILLED | ReadingTests.swift:125, ReadingTests.swift:310 |
| M9 | image: any 'into' reads (picture targets ignored) | KILLED | ReadingTests.swift:125, ReadingTests.swift:178 |
| M10 | image: an image noun after 'into' no longer makes ('into a poster' reads) | SURVIVED (every Swift and Python test) → T5 | ReadingTests.swift:415 (new) |
| M11 | image: the target must follow 'into' at once (prefix 4 -> 1) | KILLED | ReadingTests.swift:125, ReadingTests.swift:178 |
| M12 | image: the modifier word past the window not read (after = '' at the window's end) | SURVIVED (every Swift and Python test) → T5 | ReadingTests.swift:415 (new) |
| M13 | image: the English verb window 4 -> 2 | KILLED | ReadingTests.swift:125, ReadingTests.swift:178 |
| M14 | image: the Turkish window 4 -> 1 | KILLED | ReadingTests.swift:125 |
| M15 | image: the Turkish noun stems matched whole (suffixed forms missed) | KILLED | ReadingTests.swift:125 |
| M16 | image: 'resm-' as an image stem again (pre-B4) | KILLED | ReadingTests.swift:125 |
| M17 | image: the Turkish verb by bare prefix | SURVIVED (every Swift and Python test) → T5 | ReadingTests.swift:415 (new) |
| M18 | image: Turkish branch looks after the verb, not before | KILLED | ReadingTests.swift:125, ReadingTests.swift:178 |
| D1 | decision: small talk no longer decides alone | KILLED | ReadingTests.swift:165, ReadingTests.swift:288 |
| D2 | decision: no tier's verdict counts as 'not a search' | KILLED | ReadingTests.swift:165 |
| D3 | decision: the model's doubt alone is the note | KILLED | ReadingTests.swift:165, ReadingTests.swift:248 |
| D4 | decision: the code's doubt alone is the note | KILLED | ReadingTests.swift:165, ReadingTests.swift:255, ReadingTests.swift:279 |
| D5 | decision: both doubts only ask | KILLED | ReadingTests.swift:165, ReadingTests.swift:241, ReadingTests.swift:279 |
| R1 | image rule on any surface (vision condition dropped) | KILLED | ReadingTests.swift:310 |
| R2 | image rule: the !unmeasured condition dropped | SURVIVED, equivalent (N1) | N1 |
| R3 | image rule: the override claims the model tier whatever tier routed | SURVIVED (every Swift and Python test) → T6 | ReadingTests.swift:426 (new) |
| R4 | image rule: the override says the manual tier | KILLED | ReadingTests.swift:296 |
| R5 | image rule: the dead store of the reading removed | SURVIVED, equivalent (N1) | N1 |
| R6 | image rule: the override keeps the outcome's refinements | KILLED | test_router_hints.py:228 |
| R7 | read: the model's verdict never read | KILLED | ReadingTests.swift:241, ReadingTests.swift:248, ReadingTests.swift:279 |
| R8 | read: the verdict read on every tier (tier check dropped) | SURVIVED, equivalent (N1) | N1 |
| R9 | read: an instruction to the app no longer a doubt | KILLED | ReadingTests.swift:279 |
| R10 | read: pasted content no longer a doubt | KILLED | ReadingTests.swift:241, ReadingTests.swift:255 |
| R11 | route: the similarity tier's answer not read | SURVIVED (every Swift and Python test) → T6 | ReadingTests.swift:426 (new) |
| R12 | route: the manual fallback not read | KILLED | ReadingTests.swift:263 |
| R13 | route: the model tier's answer not read | KILLED | ReadingTests.swift:241, ReadingTests.swift:255, ReadingTests.swift:279, ReadingTests.swift:288, ReadingTests.swift:296 |
| R14 | read: no word not passed (false) | KILLED | ReadingTests.swift:263 |
| R15 | read: small talk not passed (false) | KILLED | ReadingTests.swift:288 |
| B1 | boundary: the model's 'something else' maps to the note, not a doubt | KILLED | ReadingTests.swift:227 |
| B2 | boundary: anything but 'a model search' is a doubt | KILLED | ReadingTests.swift:227 |
| B3 | boundary: the verdict dropped on the decline branch | SURVIVED (every Swift and Python test) → T7 | ReadingTests.swift:441 (new) |
| B4 | boundary: the verdict dropped on the surface branch | KILLED | ReadingTests.swift:227, ReadingTests.swift:241, ReadingTests.swift:248, ReadingTests.swift:279 |
| B5 | the model tier never hands the boundary its request field | SURVIVED (every Swift and Python test) → T7 | test_router_hints.py:674 (new) |
| B6 | schema: the request field not offered to the model | KILLED | RefinementBoundaryTests.swift:105 |
| B7 | scripted routing drops the request field | KILLED | ReadingTests.swift:241, ReadingTests.swift:248, ReadingTests.swift:279 |
| G1 | recordsGap: the reading ignored | KILLED | ReadingTests.swift:334 |
| G2 | recordsGap: a held doubt is kept too | KILLED | ReadingTests.swift:334 |
| G3 | recordsGap: the manual tier counted | KILLED | FrontDoorTests.swift:721 |
| V5 | isTurkishVerb: the aorist joined to its particle (`düzeltirmisin`) dropped | SURVIVED (every Swift test, and the two Python gates that read the Swift) → T3 | ReadingTests.swift:395 (new) |
| L1 | the Turkish note is the English one | SURVIVED (every Swift test, and the two Python gates that read the Swift) → T1 | ReadingTests.swift:457 (new) |
| L2 | the Turkish question back is the English one | SURVIVED (every Swift test, and the two Python gates that read the Swift) → T1 | ReadingTests.swift:457 (new) |
| L3 | the note's example dropped (English) | SURVIVED (every Swift test, and the two Python gates that read the Swift) → T1 | ReadingTests.swift:457 (new) |
| L4 | 'Find a model' and 'No' say the same in Turkish | SURVIVED (every Swift test, and the two Python gates that read the Swift) → T1 | ReadingTests.swift:457 (new) |
| U1 | confirm reduced to self.held = nil | KILLED | `make ui-test`: ScreenPathTests.swift:153; gate: test_ios_client_contract.py:806 |
| U2 | held = nil removed from select | KILLED | `make ui-test`: ScreenPathTests.swift:182; gate: test_ios_client_contract.py:806 |
| U3 | held = nil removed from apply | KILLED | `make ui-test`: ScreenPathTests.swift:153; gate: test_ios_client_contract.py:806 |
| U4a | the held branch in ask falls through to apply: a ranking anyway | KILLED | `make ui-test`: ScreenPathTests.swift:132, ScreenPathTests.swift:146, ScreenPathTests.swift:153, ScreenPathTests.swift:169, ScreenPathTests.swift:175, ScreenPathTests.swift:182; gate: test_ios_client_contract.py:806 |
| U4b | the held card shown, and the ranking under it anyway | KILLED by `make ui-test` only; every Python test and `make client-decls` passed → T8 | `make ui-test`: ScreenPathTests.swift:132; new pin: test_ios_client_contract.py:1265 |
| U5 | the card's two faces swapped: a doubt gets the note, the note asks | KILLED by `make ui-test` only; every Python test and `make client-decls` passed → T8 | `make ui-test`: ScreenPathTests.swift:132, ScreenPathTests.swift:146, ScreenPathTests.swift:153, ScreenPathTests.swift:169, ScreenPathTests.swift:175, ScreenPathTests.swift:182; new pin: test_ios_client_contract.py:1265 |
| U6 | a surface shown above a held question (the echo row's held branch removed) | KILLED by `make ui-test` only; every Python test and `make client-decls` passed → T8 | `make ui-test`: ScreenPathTests.swift:153; new pin: test_ios_client_contract.py:1265 |
| U7 | No leaves the question back up (decline sets unsure) | KILLED | `make ui-test`: ScreenPathTests.swift:132; gate: test_ios_client_contract.py:806 |
| U8 | third review M19 replay: No records a gap | KILLED | gate: test_ios_client_contract.py:806 |
| U9 | third review M19 replay: No answers anyway (calls confirm) | KILLED | gate: test_ios_client_contract.py:806 |
| U10 | Find a model while another question routes (the in-flight guard removed) | KILLED | gate: test_ios_client_contract.py:806 |

## Tests added/extended this review

**In this worktree, uncommitted** (`git diff`: 4 files, +187, all tests and the Swift manifest). The
whole diff is also `docs/reviews/m18-wave-3-tester.patch`. Each new test sits at the end of its file,
so no `file:line` citation in the PRD moves.

| test (file:line) | closes | red on (in place, one fault at a time) |
|---|---|---|
| `ios/EngineTests/ReadingTests.swift:457` `testTheNoteAndTheQuestionBackAreSaidInBothLanguages` | T1, REQ-ASK-005, D-169 clause 4 | L1, L2, L3, L4 |
| `ReadingTests.swift:356` `testTheBoundsOfNoWordAreTheDocumentedOnes` | T2 | W3, W7, W8 |
| `ReadingTests.swift:366` `testALineInAnotherScriptIsNotNoWordWhateverItsWordLengths` | T2 | W11 |
| `ReadingTests.swift:373` `testSmallTalkIsAtMostSixWords` | T2 | S2, S3 |
| `ReadingTests.swift:382` `testPastedContentIsAShortOrderWithItsContent` | T3 | P3, P4, P5, P6, P7, P9 |
| `ReadingTests.swift:395` `testATurkishVerbCountsOnlyInARequestsForm` | T3 | V1, V3, V5 |
| `ReadingTests.swift:403` `testAnOrderNeedsItsObjectInTheSameSentence` | T4, the third review's M17 | I3, I7 |
| `ReadingTests.swift:415` `testTheImageRuleReadsEachOfItsForms` | T5, REQ-RTR-005 | M2, M3, M10, M12, M17 |
| `ReadingTests.swift:426` `testTheWordingTiersAnswerIsReadAndKeepsItsTier`, with its stub `Answering` at `:479` | T6, D-169 amendment (every tier), REQ-ASK-003 | R3, R11 |
| `ReadingTests.swift:441` `testTheModelsDoubtCountsWhenItDeclines` | T7, REQ-GAP-001 (D-169 clause 5) | B3 |
| `tests/unit/test_router_hints.py:674` `test_the_model_tier_hands_the_boundary_the_verdict_it_asked_for` | T7, D-126 | B5 |
| `tests/unit/test_ios_client_contract.py:1265` `test_the_held_card_stands_alone_and_shows_the_face_its_reading_asks_for` | T8, D-169 clause 4 | U4b, U5, U6 |
| `ios/EngineTests/test-manifest.txt` | the ten Swift tests above, regenerated with `swift test --list-tests \| sort` | n/a |

- **Green:** each test passes at `b6ab027`. `make check-fast` PASS with them in place: 1659 Python
  passed, 25 skipped; 460 Swift tests, exactly the manifest; `ruff check` clean; client-decls PASS.
- **Red:** each was run against each fault it is written for, in place in this worktree, with the
  fault's bytes written back after (above). Each failed by assertion.
- **No held-out question** is in any of them. The live gate passes with them in place.

*Filled by: Tester seat (independent) · Date: 2026-10-04 · Commit range: `93040ac..b6ab027`*
