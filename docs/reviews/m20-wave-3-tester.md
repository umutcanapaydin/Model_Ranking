---
record_type: review
id: m20-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# Wave 3 Tester Review (m20): the question picks its family (#211, #206)

**Tester:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer, and it is not the Stage 5.1 security seat.
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `1389d7d..1adde33`. W3's own commits (`git log --no-merges 1389d7d..1adde33` on the
wave's five files) are `4df0cfc` (red), `7c12a7b` (fix), `7408af2` (the review's tests, red),
`fb773fe` (the review's fixes), `40cfcce` (the second round's tests, red) and `1adde33` (the second
round's fixes). W1 and W2 are merged into the range and close separately.
**Risk tier:** HIGH (`docs/plans/m20-plan.md:82-84`: `Router.swift` is a security glob).
**Code-Reviewer verdict:** round 1 BLOCKING (`docs/reviews/m20-wave-3-review.md`), round 2 MINOR,
M1 to M7 (`docs/reviews/m20-wave-3-review-round-2.md`). Not BLOCKING, so this seat runs. The second
round's M1 to M6 are answered in `40cfcce`/`1adde33`; M7 is the plan's W4 section.
**Model routing (HIGH, advisory):** author family: Claude (`GP-Agent: claude-code/local-lane`) /
reviewer family: Claude (Opus 5.5). Fallback reason: no second model family is available to this seat.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75dac85...`) on
`origin/main` and in the tree. The range touches neither `.claude/` nor `.agents/`.

## Verdict
MINOR

## Summary

Every part of REQ-CMB-004 that W3 delivers has a citing test that passes, and #206 has one. The
first red commit was red on its own tests only. Fault injection planted 30 faults: the wave's tests
caught 21 and missed 9. This review adds four tests (three Swift, one gate) that catch all 9, and
each passes on the shipped code. Two defects in the word reader stay open (M1, M2): both are the
class the two review rounds already removed elsewhere (a domain word with a second reading), and
both reach a reader only once W4 wires `Refinements.read`. One red commit did not compile (M3).

## Acceptance-criterion coverage (REQUIRED)

- **REQ-CMB-004, "the surface brings its family, then at most two refinements the surface allows,
  languages first"** (`Refinements.familyBoards`, `ios/ModelRanking/Engine/Refinements.swift:99-111`)
  → `ios/EngineTests/QuestionFamilyTests.swift:17-72` (seven tests, the file's header cites
  REQ-CMB-004) — asserts the family order, the surface's allowed list, the cap of two, languages
  before domains, a refinement already in the family taking no place, a board named twice, and the
  primary kept with no family — GREEN. Faults F1 to F6 each went red.
- **REQ-CMB-004, "with no on-device model, the words choose the refinement, at most one per kind,
  only words with one reading"** (`Refinements.read`, `Refinements.swift:185-226`) →
  `QuestionFamilyTests.swift:75-173` (nine tests) — GREEN; F7 to F9 and F12 to F17 went red. F10,
  F11, F18, F19 and F20 stayed green; closed by `QuestionFamilyTests.swift:180` and `:192` (T1).
- **REQ-CMB-004, "nothing about the question leaves the phone"** → the functions are pure (no I/O);
  the existing client network gates (`make client-decls`, `tests/unit/test_ios_client_contract.py`)
  pass. GREEN.
- **D-188 clause 6, "the answer plan is the one reader, a gate holds it"** →
  `tests/unit/test_router_hints.py:356` — GREEN, but three compiling spellings passed it (T2);
  closed by `tests/unit/test_router_hints.py:375`.
- **#206, "a short Turkish question made of model names is a general question"**
  (`CategoryHints.comparesModelsOnly`, `ios/ModelRanking/Engine/Router.swift:403-411`, used at
  `:541-544`) → `ios/EngineTests/KeywordRoutingTests.swift:235` — GREEN; R2 to R6 went red. R1
  (the outcome labelled as the on-device model's) stayed green; closed by
  `KeywordRoutingTests.swift:257` (T3).
- The PRD row (`docs/prd.md:613`) says PARTIAL: the functions exist and hold, and W4's answer plan
  is what reaches them. That is accurate: nothing in `ios/ModelRanking/` calls `familyBoards` or
  `Refinements.read` at `1adde33`.

## Red→green on reported symptoms

Each red commit was built from `git archive <commit> ios scripts/router_probe` into its own scratch
folder and run with `swift test --parallel` (the full Engine suite).

- `4df0cfc` (red, #211): compiles; exactly five tests fail, all in `QuestionFamilyTests`
  (`testTheFamilyComesFirstThenTheRefinements`, `testARefinementTheSurfaceDoesNotAllowAddsNothing`,
  `testAtMostTwoRefinementsAndNoneTwice`, `testTheWordsOfALanguageOrADomainChooseTheRefinement`,
  `testAWordWithASecondReadingIsNoRefinement`). Red on its own tests only. GREEN at `7c12a7b`.
- `7408af2` (the first review's tests, red, #206): **does not compile.**
  `KeywordRoutingTests.swift:237` and `:243` call `CategoryHints.comparesModelsOnly`, which
  `fb773fe` adds, so no Swift test runs. See M3.
- `40cfcce` (the second round's tests, red): compiles; exactly four tests fail, each one the commit
  adds or extends: `KeywordRoutingTests/testAShortTurkishQuestionMadeOfModelNamesIsAGeneralQuestion`
  (the tier names), `QuestionFamilyTests/testANationalityAfterInIsNoLanguage`,
  `testTheWordsChooseOneOfEachKindTheFirstNamed` and `testMoreWordsWithASecondMeaningAreNoDomain`.
  Its fifth new test, `testEachContextWordThatMakesALanguageIsHeld`, is green there as intended: it
  holds rules `fb773fe` already had (the second round's M5). Red on its own tests only; GREEN at
  `1adde33`.
- #206's symptom (`claude mu chatgpt mi` placed on `coding` by the embedding): R6 (the shortcut
  turned off in a scratch copy of `1adde33`) turns `testAShortTurkishQuestionMadeOfModelNamesIsAGeneralQuestion`
  red on this Mac, where the English embedding loads, so the test reproduces the symptom.

## Suite result

- `make check-fast` at `1adde33` before this review's tests: PASS in 101.9 s (lint, typecheck,
  records, test, client-decls, swift-test=swift-test-parallel).
- `swift test --filter QuestionFamilyTests|KeywordRoutingTests` at `1adde33`: 31 tests, 0 failures.
- With this review's tests: `swift test --filter "QuestionFamilyTests|KeywordRoutingTests/testAQuestionMadeOfModelNamesIsAMatchOnWording"`:
  19 tests, 0 failures; `pytest tests/unit/test_router_hints.py -k "word_reader or answer_plan_reads"`:
  2 passed. `make check-fast` with them and this record: PASS in 164.5 s (every leg, the swift-test leg reading
  the manifest with the three new names).
- Coverage on touched code: no Swift coverage tool is wired for the Engine package; the planted
  faults below stand in for it.

## Mocks / contract tests

- No integration is added or changed. The functions read no network; `familyBoards` takes the family
  `/v1/categories` already serves (W1's contract tests).

## Fault injection

Each fault was planted in a scratch copy of `ios/` outside the worktree (from `git archive 1adde33`),
run with `swift test --filter`, and restored by writing the original bytes back; the sha256 was then
checked against the original (`Refinements.swift` `dea2a823...`, `Router.swift` `3b27e948...`; both
matched after every plant, and both match the worktree). Filters: F1 to F16
`QuestionFamilyTests|RefinementsTests|RefinementBoundaryTests|AnswerPlanTests`; F17 to F20
`QuestionFamilyTests` (the only suite that calls `Refinements.read`); R1 and R6 the whole
`KeywordRoutingTests`; R2 to R5 its #206 test. The gate plants (G) were appended to a scratch copy of
`ContentView.swift` beside a scratch copy of the gate file, run with `pytest -k`, and restored the same
way. G1 and G2 were also compiled and run in the scratch package: each returned the reader's answer
(`german`, `french`).

| id | fault | the wave's tests | this review's tests |
|---|---|---|---|
| F1 | a board the family names twice kept twice | red (`testABoardTheFamilyNamesTwiceCountsOnce`) | — |
| F2 | an empty family drops the primary | red (`testAnEngineWithNoFamilyLeavesThePrimaryBoardFirst`) | — |
| F3 | the surface's allowed list ignored | red (2 tests) | — |
| F4 | no cap of two | red (3 tests) | — |
| F5 | a refinement already in the family takes a place | red (`testARefinementAlreadyInTheFamilyLeavesRoomForTwoMore`) | — |
| F6 | domains before languages | red (6 tests) | — |
| F7 | the last named of a kind wins | red (`testTheWordsChooseOneOfEachKindTheFirstNamed`) | — |
| F8 | table order, not the question's | red (same) | — |
| F9 | a name before "language"/"translation" no longer counts | red (2 tests) | — |
| F10 | "to"/"from" count with no translation word | **green** | red (`testToOrFromMakesALanguageOnlyInAQuestionThatAsksToTranslate`) |
| F11 | "to" no longer makes a language | **green** | red (same) |
| F12 | a noun after the name no longer blocks it | red (`testANationalityAfterInIsNoLanguage`) | — |
| F13 | an English name read anywhere | red (4 tests) | — |
| F14 | `notStarting` removed | red | — |
| F15 | `notAfter` removed | red (3 tests) | — |
| F16 | a starred guard read as a whole word | red | — |
| F17 | whole words read as stems | red (2 tests) | — |
| F18 | "learning" dropped from `languageBefore` | **green** | red (`testTheRemainingContextWordsAndGuardsAreHeld`) |
| F19 | the "bilgisayar" ("computer") guard on "bilim" ("science") dropped | **green** | red (same) |
| F20 | the writing guards on codes, scripts, queries, functions dropped | **green** | red (same) |
| R1 | the #206 outcome labelled as the on-device model's (`tier: .model`) | **green** | red (`testAQuestionMadeOfModelNamesIsAMatchOnWording`) |
| R2 | no Turkish particle needed | red | — |
| R3 | no model name needed | red | — |
| R4 | tier names dropped | red | — |
| R5 | a version's one letter dropped ("gpt 4o") | red | — |
| R6 | the #206 shortcut turned off | red | — |
| G1 | `typealias WordReader = Refinements; WordReader.read(q)` in `ContentView.swift` | **green** | red (`test_no_other_name_reaches_the_word_reader`) |
| G2 | `Refinements.self.read(q)` in `ContentView.swift` | **green** | red (same) |
| G3 | `Refinements.read(q)` in `ContentView.swift` (control) | red | red |
| G4 | ``Refinements.`read`(q)`` in `ContentView.swift` | **green** | red (same) |

**Counts:** 30 planted (26 Swift, 4 gate). The wave's tests caught 21 and missed 9 (F10, F11, F18,
F19, F20, R1, G1, G2, G4). With this review's tests all 30 are caught; each of the 9 was re-planted
against them and went red, and each file was restored and its sha256 checked.

## Findings

### BLOCKING
- None

### MINOR

- **M1** `ios/ModelRanking/Engine/Refinements.swift:147` (`"software": Words(stems: ["yazilim"], words: ["software"])`)
  with `:172-175` (`notAfter`), against `ios/ModelRanking/Engine/Router.swift:350`. **"AI software" is
  read as the software domain.** The router already knows that "software" after "ai", "zeka" or
  "chatbot" is not a software question (`notAfter["software"] = ["ai", "zeka", "chatbot"]`,
  `notAfter["yazilim"] = ["zeka"]`); the word reader has no such guard. Probes on `1adde33`:
  - "best ai software for writing essays" → `software` (and `writing` is dropped: one domain per kind,
    the first named);
  - "which ai software is best for essays" → `software`;
  - `hangi yapay zeka yazılımı daha iyi` ("which AI software is better") → `software`;
  - `yapay zeka yazılımı ile şiir yaz` ("write a poem with AI software") → `software`;
  - "best chatbot software for poems" → `software`.
  **Failure scenario.** Once W4 wires `read`, a reader with Apple Intelligence off asks "best ai
  software for writing essays" on `everyday`. Arena's software-and-IT slice joins the family at equal
  weight in place of the writing slice the question names, and the list shows a "software" refinement
  nobody asked for. D-188 clause 6 says a domain word with a second meaning is not read. **Fix.** Add
  `"software": ["ai", "chatbot"]` and `"yazilim": ["zeka"]` to `Refinements.notAfter`, as the router
  has them, and add the five probes as negative tests ("best ai software for writing essays" →
  `writing`).

- **M2** `ios/ModelRanking/Engine/Refinements.swift:141` (`"saglik"`, Turkish for "health") against the
  comment at `:128`. **The Turkish word for health is read where the English one was dropped.** The
  first review's M3 removed "health" because of "battery health" and "health check"; the Turkish
  whole word stayed. Probes on `1adde33`:
  - `kubernetes sağlık kontrolü betiği` ("kubernetes health check script") → `medicine`;
  - `sunucu sağlık durumu` ("server health status") → `medicine`;
  - `pil sağlık durumu` ("battery health status") → `medicine`.
  **Failure scenario.** As in M1: a DevOps or phone question gains Arena's medicine-and-healthcare
  slice once W4 wires `read`. **Fix.** Drop `saglik`, or keep it and block it before `kontrol*` and
  `durum*` (`notBefore`, which already reads a trailing `*`). Add the three probes as negative tests.

- **M3** commit `7408af2`; `ios/EngineTests/KeywordRoutingTests.swift:237` and `:243` at that commit.
  **A red commit that does not compile.** Built from `git archive 7408af2`, the test target fails with
  `type 'CategoryHints' has no member 'comparesModelsOnly'`, which `fb773fe` adds. No Swift test runs,
  so the commit shows the whole suite red, not its own tests: its seven other new tests (in
  `QuestionFamilyTests`, the first review's M1 to M5) were never seen failing for their own
  reason.
  **Failure scenario.** A red test that would have passed on the old code (a test that proves nothing)
  goes unnoticed, because nothing ran. **Fix.** In a Swift red commit, add a stub for each new symbol
  (`static func comparesModelsOnly(_ question: String) -> Bool { false }`) so the target compiles and
  only the new tests fail; `4df0cfc` did this. Nothing to redo for this wave: the fix commit's tests
  pass, and the planted faults above show what each test holds.

- **T1** `ios/EngineTests/QuestionFamilyTests.swift:129-140` (`testEachContextWordThatMakesALanguageIsHeld`).
  **Five rules no test held** (F10, F11, F18, F19, F20). The second round's fix added `languageEnds`,
  after which "switching from german cars to japanese ones" reads nothing whether or not the question
  asks to translate ("cars" and "ones" end no language), so the test written for the second round's S2
  no longer holds the translation condition. "to" before a language, "learning", the "bilgisayar"
  guard, and four of the seven writing guards had no test. **Failure scenario.** A later edit drops one
  and "upgrading from german to japanese cars" reads `german`, or "translate this to french" reads
  nothing. **Fix (done in this review).** `testToOrFromMakesALanguageOnlyInAQuestionThatAsksToTranslate`
  (`:180`) and `testTheRemainingContextWordsAndGuardsAreHeld` (`:192`), both in the manifest. Closed.

- **T2** `tests/unit/test_router_hints.py:356-372`. **The one-reader gate passes three spellings that
  compile.** The fix commit's subject says "the one-reader gate by any spelling". A type alias
  (`typealias WordReader = Refinements`, then `WordReader.read(q)`), the metatype
  (`Refinements.self.read(q)`) and a backticked name (``Refinements.`read`(q)``) each passed the gate
  when planted in a scratch `ContentView.swift`; the first two were built and returned the reader's
  answer. **Failure scenario.** W4 or later wraps the reader under another name, and the words'
  refinements reach a second place (a chip, a log) with the gate green. **Fix (done in this review).**
  `test_no_other_name_reaches_the_word_reader` (`:375`) forbids each of the three spellings in the
  client; the client uses none today. It went red on each plant. Closed.

- **T3** `ios/EngineTests/KeywordRoutingTests.swift:235-252`. **The #206 outcome's tier is untested.**
  `RoutingTier` is shown to the reader ("a keyword-grade match presented as an understanding of the
  question is a small lie", `Router.swift:22-23`). R1 labelled the #206 outcome as the on-device
  model's and stayed green. **Failure scenario.** A refactor returns `.model` on this path, and a
  question the phone matched on wording is presented as understood. **Fix (done in this review).**
  `testAQuestionMadeOfModelNamesIsAMatchOnWording` (`:257`) asserts `.similarity`, and that with no
  `everyday` served the question gets the manual, unmeasured fallback rather than an embedding's
  guess. Closed.

## K.9 candidates spotted outside this wave's scope
- None

## Risks queued to next M
- **R1** `ios/ModelRanking/Engine/AnswerPlan.swift:130-134`, `docs/prd.md:613`. **M1 and M2 go live
  with W4.** Neither defect reaches a reader at `1adde33`, because nothing calls `Refinements.read`;
  W4's wiring makes both live. **Failure scenario.** W4 closes on its own tests, which exercise the
  wiring with clean questions, and the two collisions ship. **Fix.** Fix M1 and M2 (or file them) before
  W4's answer plan calls `read`, and have W4's Tester re-run the probes in M1 and M2 through the
  answer plan.

## Tests added/extended this review
- `ios/EngineTests/QuestionFamilyTests.swift:180` `testToOrFromMakesALanguageOnlyInAQuestionThatAsksToTranslate`
  — REQ-CMB-004, D-188 clause 6 (F10, F11).
- `ios/EngineTests/QuestionFamilyTests.swift:192` `testTheRemainingContextWordsAndGuardsAreHeld` —
  REQ-CMB-004, D-188 clause 6 (F18, F19, F20).
- `ios/EngineTests/KeywordRoutingTests.swift:257` `testAQuestionMadeOfModelNamesIsAMatchOnWording` —
  #206 (R1).
- `tests/unit/test_router_hints.py:375` `test_no_other_name_reaches_the_word_reader` — D-188 clause 6
  (G1, G2, G4).
- `ios/EngineTests/test-manifest.txt`: the three Swift names, in byte order (`LC_ALL=C sort -c` passes).
