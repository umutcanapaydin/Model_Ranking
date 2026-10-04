---
record_type: review
id: m18-wave-3-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-04
---
# Wave 3 Tester Review, second seat (m18)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or records.
It is not the first Tester seat, and it is none of the three Code-Reviewer seats.
**Independent:** yes
**Date:** 2026-10-04
**Commit range:** `93040ac..a4c898f`, 16 commits. `a4c898f` is the fix round for the first Tester's
BLOCKING verdict (`docs/reviews/m18-wave-3-tester-round-1.md`, then at `m18-wave-3-tester.md`, T1 to T9). By `/close-wave`, a BLOCKING Tester
verdict means a fix round and then a new Tester. This is that new seat.
- Since `b6ab027`, the head the first seat tested, the range changes no app code. It adds tests (the
  fix round), the PRD, the plan, D-169's text, the research record, run files and review records.
  `git diff --stat b6ab027..a4c898f -- ios/ModelRanking scripts/router_probe/*.swift src` is empty.

**Risk tier:** HIGH (`docs/plans/m18-wave-3-plan.md:13-15`).
**Code-Reviewer verdict:** PASS WITH MINOR (`docs/reviews/m18-wave-3-review.md`, round 3, the verdict
of record). By D-172 there is no security seat on the wave.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from `.claude/agents/Tester.md`. It then read the first Tester's
  record, the fix round, the plans, D-169 with its amendment, D-175, the code, the tests and the
  reviews. It did not read the first seat's fault harness; it wrote its own faults from the record's
  descriptions.

**Base-pinned policy:** `git diff --stat 93040ac a4c898f -- .claude .agents permission-matrix.md
.github AGENTS.md CLAUDE.md` is empty, so the profile read in the worktree is the base's. No commit
carries an attribution line. Nothing in the range asks anything of this seat.

## Verdict
MINOR

**T1 is closed.** `Language.swift` is back above its base.

| `Language.swift` | base `93040ac` | `b6ab027` (before the fix) | head `a4c898f` |
|---|---:|---:|---:|
| lines | 82.48 % (86 of 491 missed) | 79.88 % (102 of 507 missed) | **83.04 %** (86 of 507 missed) |
| functions | 66.23 % | 62.96 % | 67.90 % |
| regions | 75.77 % | 73.32 % | 76.55 % |

The four D-169 sentences (`Language.swift:674-693`) now run in both languages: each line shows 5 to 7
executions in `llvm-cov show`.

**The first seat's faults are dead.** This seat re-injected all 33 of them: the 29 survivors behind T2
to T8, and L1 to L4 behind T1. Each now fails a test. U4b, U5 and U6 fail the Python client gate
(`test_ios_client_contract.py:1265`), and each still compiles (`make client-decls` rc 0).

**This seat's own faults found four gaps (T10 to T13).** It wrote 29 faults on the code the first
seat did not cover: the boundary's mapping of `request`, `recordsGap`, the held branch,
`confirm`/`decline`, the card's two taps, and the image rule's `vision` gate.
- 1 is equivalent (X14, N1).
- Of the other 28, the wave's tests kill 18. **10 survived.**
- This seat's tests kill all 10. They are uncommitted in this worktree, and the patch is
  `docs/reviews/m18-wave-3-tester-2.patch`.

**Advisory kill rate.**
- This seat's own faults at `a4c898f`: **18 of 28, 64.3 %**. With this seat's tests: 28 of 28.
- All 61 non-equivalent faults this seat ran (33 re-injected, 28 own): **51 of 61, 83.6 %**. With
  this seat's tests: 61 of 61.

**Why MINOR and not BLOCKING.** Every acceptance criterion has a citing test that passes. No touched
module lost coverage. Each gap is a fault that stayed green, and each comes with a test that is green
at `a4c898f` and red on its fault. This follows the first seat's grading of T2 to T8.

**`make check-fast`:** PASS at `a4c898f` (rc 0). PASS again with this seat's tests (rc 0).

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `a4c898f`. Line numbers are at `a4c898f`; this seat's new tests sit
at the end of their files, so no PRD citation moves.

| criterion (phase, issue) | citing test (file:line) | entry | status |
|---|---|---|---|
| P0: the plan, D-169 brought in and amended, the sets and the baseline | `docs/plans/m18-wave-3-plan.md`; D-169 and its amendment in `docs/decisions.md` | records | MET (read) |
| P1 #66: each signal tested on its own; none fires on a genuine tuning question but the one named | `ReadingTests.swift:12`, `:22`, `:30`, `:44`, `:59`, `:91`, `:101`, `:110`, `:125`; the named one in `:178` (`:210`); the bounds in `:356`, `:366`, `:373`, `:382`, `:395`, `:403`, `:415` | unit | GREEN. 33 of 33 re-injected faults die |
| P2 #66: `RoutingOutcome` carries the reading | `test_router_hints.py` `test_the_router_never_produces_anything_but_a_category_id` (the field and its closed enum) | source pin | GREEN |
| P2 #66: the boundary maps the model's field | `ReadingTests.swift:227`, `:441`; `RefinementBoundaryTests.swift:105`; `test_router_hints.py:674`; **new** `ReadingTests.swift:496` | unit, `TieredRouter.route` | GREEN. Gap T10, closed by `:496` |
| P2 #66: the decision table | `ReadingTests.swift:165`, `:241`, `:248`, `:255`, `:263`, `:269`, `:279`, `:288`, `:426` | unit, `TieredRouter.route` | GREEN |
| P2 #66: the note and the question back on screen, held by UI tests | `ScreenPathTests.swift:132`, `:146`, `:153`, `:169`, `:175`, `:182`; gate `test_ios_client_contract.py:806`, `:1265`; **new** `:1288` | the app (first seat's `make ui-test`, 16 of 16, at `b6ab027`); source pins | GREEN. Gaps T11, T12, closed by `:1288` |
| P3 #73, #113: wording tuned, at most three variants each | research record §3 | records | MET (read) |
| P4 #66, #73, #113: the bars, twice, on held-out sets | research record §4 to §6; D-169 amendment | records | #73 MET. #66's catch bar and both #113 bars missed and stated for the owner. Unchanged by the fix round |
| REQ-ASK-005 (D-169) | the PRD's list: `ReadingTests.swift:12`, `:30`, `:59`, `:91`, `:165`, `:248`, `:288`; `ScreenPathTests.swift:132` to `:182`; also `ReadingTests.swift:457` (T1) | unit, the app | GREEN. PARTIAL in the PRD (the catch bar); I agree |
| REQ-ASK-003, the carve-out | `FrontDoorTests.swift:201`; `RouterBoundaryTests.swift:53`; `ReadingTests.swift:296`, `:426` | `TieredRouter.route` | GREEN |
| REQ-GAP-001, D-169 clause 5 | `ReadingTests.swift:334`, `:441`; `FrontDoorTests.swift:643`, `:719`; gate `test_ios_client_contract.py:806`; **new** `ReadingTests.swift:496` | unit, gate | GREEN. Gap T10 (a declined search was not shown to be kept), closed |
| REQ-RTR-005, #113's rule | `ReadingTests.swift:296`, `:310`, `:415`, `:426`; `RouterBoundaryTests.swift:131`, `:170`; `FrontDoorTests.swift:388` | `TieredRouter.route` | GREEN. X23 to X28 on the `vision` gate all die |
| REQ-IMG-003, the refusal half | `FrontDoorTests.swift:347`; `ReadingTests.swift:296` | `TieredRouter.route` | GREEN. The PRD now gives the shipped 7 of 15 and the 3 on `web-dev` (T9's first half, in `8a18324`) |
| Milestone W3 criterion (`m18-plan.md:32`) | the rows above; research record | | #73 met. #66 and #113 short of their bars, stated |

**The PRD's citations.** The 16 PRD rows the range adds or changes carry 79 `file:line` citations.
- 78 point at tests. Each lands on the `def`, `func` or `class` line of the test it names.
- The 79th is REQ-BGT-001's code pointer, `ios/ModelRanking/ContentView.swift:77`. It now lands on
  `private let budget = "unlimited"`. **T9's pointer is fixed.**
- The W3 rows (REQ-ASK-005, REQ-ASK-003, REQ-RTR-005, REQ-IMG-003, REQ-GAP-001) are among them.

## Red→green on reported symptoms

The reported symptoms here are the first seat's T1 to T9. Each fix-round test is green at `a4c898f`
and red on its fault, in place, in this worktree.

| symptom | red | green at `a4c898f` |
|---|---|---|
| T1: `Language.swift` lost coverage; L1 to L4 passed every test | 79.88 % at `b6ab027`; L1 to L4 each fail `ReadingTests.swift:457` | 83.04 % |
| T2: W3, W7, W8, W11, S2, S3 | each fails `:356`, `:366` or `:373` | pass |
| T3: P3 to P7, P9, V1, V3, V5 | each fails `:382` or `:395` | pass |
| T4: I3, I7 | each fails `:403` | pass |
| T5: M2, M3, M10, M12, M17 | each fails `:415` (M3 also `:426`) | pass |
| T6: R11, R3 | each fails `:426` | pass |
| T7: B3, B5 | B3 fails `:441`; B5 fails `test_router_hints.py:674` | pass |
| T8: U4b, U5, U6 | each fails `test_ios_client_contract.py:1265` | pass |
| T9: REQ-BGT-001's pointer, REQ-IMG-003's number | read | fixed (pointer in `a4c898f`; number in `8a18324`) |

**The fix round landed the first seat's tests as written.** The added lines of `a4c898f` under `ios/`
and `tests/`, sorted, equal the added lines of the first seat's patch, sorted.

**Weakened or deleted tests.** `a4c898f` removes no line from any test file. The seven removed lines
before it were read by the first seat; none weakened a test.

## Suite result
- **`make check-fast` at `a4c898f`: PASS, rc 0, 69.8 s.** lint, typecheck, records: PASS. test:
  **1659 passed, 25 skipped**; coverage-floor PASS, 42 modules. client-decls: PASS. swift-test
  (parallel): PASS, **460 tests**, exactly the manifest.
- **`make swift-test` (serial) at `a4c898f`: PASS, rc 0**, 460 tests, each in the manifest.
- **With this seat's tests: `make check-fast` PASS, rc 0, 62.6 s.** 1661 Python passed, 25 skipped;
  **461** Swift tests, exactly the manifest. The held-out gate
  (`test_no_held_out_question_is_written_into_the_code_or_its_tests`) passes.
- **`make ui-test` was not run by this seat.** The guard blocks `xcodebuild` and `simctl`. The app code
  and the UI tests are byte-identical to `b6ab027`, where the first seat ran it: 16 of 16.
- **Coverage on touched code.** `swift test --enable-code-coverage` on `git archive` copies of
  `93040ac`, `b6ab027` and `a4c898f` (428, 450 and 460 tests, all passing), read with `llvm-cov report`.

| module (lines) | base `93040ac` | head `a4c898f` |
|---|---:|---:|
| `Reading.swift` (new) | n/a | 100 % |
| `Router.swift` | 97.96 % | 98.15 % |
| `FrontDoor.swift` | 99.45 % | 99.45 % |
| `ScriptedRouting.swift` | 100 % | 100 % |
| `Language.swift` | 82.48 % | 83.04 % |

No touched module is below its base. This seat's tests add no source line, so they cannot lower it.
`ContentView.swift` is outside the Swift package; the UI run and the client gate are its evidence.

## Mocks / contract tests
- **`ScriptedModelRouter`** (`ScriptedRouting.swift:16`) stays the one stand-in for the on-device
  model. Its answer goes through `ModelOutputBoundary`. This seat's Swift test uses it, with the file's
  own `NoSimilarity`.
- **The real model** is measured by the probe on the owner's Mac (D-175 clause 3), not by tests. T13's
  pin holds that the model is told what its two verdicts mean; it does not hold the wording.
- **No new external integration.** No `/v1` change.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **T10** `ios/ModelRanking/Engine/Router.swift:590`, `:597`. **Only "something else" should be a doubt, and nothing held that beside a decline, or with no verdict.**
   1. X3 makes every decline a doubt, whatever the verdict. Every Swift and Python test passed.
   2. On a phone with Apple Intelligence, every question the model declines would then be asked back:
      a request to make an image, cooking, travel. That is the unmeasured answer REQ-ASK-003 and
      REQ-RTR-005 promise. And the gap register (REQ-GAP-001) would keep none of them until the reader
      taps "Find a model".
   3. X2 reads a missing verdict as a doubt. It also passed every test. The schema requires the field,
      so this is the smaller case, but `try?` turns a field that fails to decode into nil.
   4. The first seat's T7 test holds "something else" beside a decline. Nothing held "a model search"
      or no verdict there.
   5. **The fix:** `testOnlySomethingElseIsADoubtOnEitherBranch` (`ReadingTests.swift:496`). It reads
      both branches with "a model search" and with no verdict, and routes a declined search through
      `TieredRouter` to check it is unmeasured, a search, and kept. It kills X2 and X3.
- **T11** `ios/ModelRanking/ContentView.swift:842`. **The held branch's `routing = nil` is held by nothing.**
   1. X13 drops it. Every Python test passed, and `make client-decls` compiled it.
   2. The routing notice and the alternatives row (`ContentView.swift:531-561`) read `routing` alone,
      not `held`. So after a search, a held question would show the old question's notice ("Below is
      the general chat ranking…") and its "Or:" surface buttons above the note or the question back.
   3. That breaks D-169 clause 4 ("the previous question's ranking goes too") and the amendment
      ("while it waits, no surface is shown").
   4. No UI test would see it. Each one asks a single question on a fresh launch, where `routing` is
      already nil.
   5. **The fix:** `test_a_held_question_clears_the_old_answer_and_its_two_taps_do_what_they_say`
      (`test_ios_client_contract.py:1288`) pins `routing = nil` in the held branch. It kills X13.
- **T12** `ContentView.swift:879-882`, `:903`, `:906`. **The question back's two taps, and the lock "Find a model" takes, are pinned by no gate.**
   1. The gate pins the bodies of `confirm` and `decline` (`:806`). It does not pin the buttons that
      call them, or `confirm`'s lock.
   2. Three faults fail only `make ui-test`, by reading the UI tests (this seat could not run them):
      X18, "Find a model" calls `decline` (`ScreenPathTests.swift:153`); X19, "No" calls `confirm`
      (`:132`); X20, "Find a model" does nothing (`:153`).
   3. Three faults fail nothing at all:
      - X17 drops `defer { routingInFlight = false }` from `confirm`. After "Find a model", the field
        stays locked and the spinner turns for good (`:460`, `:475`). The reader cannot ask again
        until the app restarts.
      - X16 drops `routingInFlight = true` from `confirm`. The field is open while the answer loads,
        and `confirm`'s `defer` can unlock it while a newer question still routes: the double route
        the review's M3 closed.
      - X21 shows both buttons in English on the Turkish screen. That is #63 finding 2's class. The UI
        tests run in English only.
   4. **The fix:** the same test (`test_ios_client_contract.py:1288`). It pins each button to its
      action in the reader's language, and `confirm`'s lock and unlock. It kills X16 to X21.
- **T13** `ios/ModelRanking/Engine/Router.swift:485-494`. **The paragraph that tells the model what its verdict means is held by nothing.**
   1. X9 deletes the instructions' last paragraph. Every Swift and Python test passed.
   2. The model would keep only the field's one-line guidance. The paragraph is where genuine
      searches written as tasks ("fix a bug in my python repo") are named as searches. That guards the
      false-positive bound of D-169 clause 6.
   3. The probe measures the wording on the owner's Mac (D-175 clause 3). No gate checks the paragraph
      is there.
   4. **The fix:** `test_the_model_is_told_what_each_of_its_two_verdicts_means`
      (`test_router_hints.py:690`). It pins that the instructions name both closed values, through the
      boundary's own constants. It holds presence and the link, not the wording. It kills X9.

## Notes (no change required by this verdict)

- **N1** **Equivalent: X14.** It drops `asked = typed` from the held branch (`ContentView.swift:841`).
  `asked` is read in one place only, the echo line (`:512`), and only when `held` is nil and `routing`
  is set. The held branch sets `routing` to nil. The one path that sets `routing` again, `apply`, sets
  `asked` first (`:860`). So the store is never read.
- **N2** **The first seat's tests carry weight beyond their own faults.** X24 (the image rule on the
  model tier only) is killed by `ReadingTests.swift:426` alone, and X6 in part by `:441`. Both are
  fix-round tests.
- **N3** **Not done by this seat, by its rules.** No installer, `launchctl`, Docker, simulator, commit
  or push. No network in a test. No crash construct in any fault. No fault ended in a signal; every
  kill is an assertion or a gate's refusal, never a compile error. The on-device model was not run.

## K.9 candidates spotted outside this wave's scope

- **K11** `ios/ModelRanking/ContentView.swift:827-918`. **The held reading's logic lives in the view, where only regex pins and an ungated UI target can reach it.**
  The held branch, `confirm`, `decline` and the card's taps are SwiftUI code. The Swift package does
  not compile `ContentView.swift`. So their behaviour is held by regex pins on the source (`:806`,
  `:1265`, `:1288`) and by `make ui-test`, which no gate runs (D-175). Seven of this seat's ten
  survivors, and the first seat's T8, live there. A pin holds text: a refactor that keeps the
  behaviour can fail it. This is an enhancement: move the held state and its moves into an Engine
  type, so Swift tests drive them.
- **K12** `ios/UITests/ScreenPathTests.swift`. **Every UI test runs in English and asks one question on a fresh launch.**
  None drives the Turkish screen, a second question, or a tap after "Find a model". X13, X17 and X21
  are of that class, and so are #63 finding 2 and the first seat's K10. This is an enhancement: one UI
  test in Turkish, and one that asks twice.

## Risks queued to next M

- No new risk. The first seat's R7 and R8 stand: #113's rule does nothing on the wording tier, and
  #66's catch rate without Apple Intelligence is a third of the bar. The reviews' R3 to R6 stand as the
  third review wrote them.

## Fault injection (HIGH: mandatory)

**Harness:** scratch `build/t2/mut.py` and `build/t2/faults.py`, under the worktree's ignored
`build/`. For each fault it does the following:
1. It checks the file equals `HEAD`: `git hash-object` must equal `git rev-parse HEAD:<file>`.
2. It records the file's sha256 and keeps its bytes.
3. It makes exact string edits, each required to match exactly once. A dry run checked every edit
   first.
4. It runs the checks. Every process starts in its own session and is killed with SIGKILL on a
   timeout; none timed out.
   - An engine fault: `swift test --filter` on the reading, boundary, routing, gap and language
     classes, and the Python gates that read the Swift (`test_router_hints.py`,
     `test_ios_client_contract.py`, `test_ios_visual_contract.py`). If nothing fails: the whole Swift
     suite (460 tests) and the whole Python suite (`-n auto`, `MODEL_RANKING_REQUIRE_ARTIFACT=1`).
   - A screen fault: the same Python gates plus `test_engine_address.py` and `test_client_decl_gate.py`,
     then `make client-decls` (to prove the fault compiles). If nothing fails: the whole Python suite.
5. It writes the original bytes back **in place**, never with `git checkout` or `restore`.
6. It asserts sha256 equals the pre-edit hash, `git hash-object` equals HEAD's blob, and
   `git status` shows the file clean.

**73 runs**: 62 at `a4c898f`, then the 11 survivors again with this seat's tests in place. Every run
says `restored: true` and clean. After the last run, every tracked file matched the sha256 baseline
taken before the first fault (`shasum -c`), but the four test files this seat edited. Every screen
fault compiled (`make client-decls` rc 0 on all 22 runs).

**Restore hashes** (sha256 prefix, pre = post, and the HEAD blob `git hash-object` matched):

| file | runs | sha256 (pre = post) | HEAD blob |
|---|---:|---|---|
| `ios/ModelRanking/Engine/Reading.swift` | 22 | `1eea49b27cac` | `fd659a4161` |
| `ios/ModelRanking/Engine/Router.swift` | 23 | `f7dd224faf76` | `20552faf11` |
| `ios/ModelRanking/ContentView.swift` | 22 | `e3aaf221f87f` | `80472701c2` |
| `ios/ModelRanking/Engine/Language.swift` | 4 | `2add43661cfe` | `3fde5793a1` |
| `ios/ModelRanking/Engine/FrontDoor.swift` | 2 | `91e529b4d47b` | `c79f1b17e0` |

**The first seat's faults, re-injected** (ids kept; each rebuilt from its record's description). All
33 KILLED at `a4c898f`. A cited line is the killing test's `func` or `def` line.

| id | the fault | killed by |
|---|---|---|
| W3 | noWord: the four-letter minimum raised to five | ReadingTests.swift:356 |
| W7 | isWord: the no-vowel bound 5 -> 6 | ReadingTests.swift:356 |
| W8 | isWord: the no-vowel bound 5 -> 4 | ReadingTests.swift:356 |
| W11 | isWord: a script beyond Latin is no longer a word by itself | ReadingTests.swift:366 |
| S2 | smallTalk: the six-word bound removed | ReadingTests.swift:373 |
| S3 | smallTalk: the bound 6 -> 3 | ReadingTests.swift:373 |
| P3 | pasted: no content needed after the colon | ReadingTests.swift:382 |
| P4 | pasted: the 1...8 words-before bound removed | ReadingTests.swift:382 |
| P5 | pasted: a named model or "which" before the colon no longer a search | ReadingTests.swift:382 |
| P6 | pasted: the English verb anywhere before the colon | ReadingTests.swift:382 |
| P7 | pasted: the English verb only as the first word | ReadingTests.swift:382 |
| P9 | pasted: the Turkish verb anywhere before the colon | ReadingTests.swift:382 |
| V1 | isTurkishVerb: the aorist counts with no question particle | ReadingTests.swift:395 |
| V3 | isTurkishVerb: the ability form dropped | ReadingTests.swift:395 |
| V5 | isTurkishVerb: the aorist joined to its particle dropped | ReadingTests.swift:395 |
| I3 | instructs: the object no longer required | ReadingTests.swift:403 |
| I7 | instructs: "komut"/"istem" by bare prefix | ReadingTests.swift:403 |
| M2 | image: the "arka plan" branch removed | ReadingTests.swift:415 |
| M3 | image: "draw me" removed | ReadingTests.swift:415, :426 |
| M10 | image: an image noun after "into" no longer makes | ReadingTests.swift:415 |
| M12 | image: the modifier just past the window not read | ReadingTests.swift:415 |
| M17 | image: the Turkish making verb by bare prefix | ReadingTests.swift:415 |
| R11 | route: the wording tier's answer not read | ReadingTests.swift:426 |
| R3 | image rule: the override claims the model tier | ReadingTests.swift:426 |
| B3 | boundary: the verdict dropped on the decline branch | ReadingTests.swift:441 |
| B5 | the model tier hands the boundary `request: nil` | test_router_hints.py:674 |
| U4b | the ranking rendered under the held card | test_ios_client_contract.py:1265 (the Python client gate) |
| U5 | the card's two faces swapped | test_ios_client_contract.py:1265 (the Python client gate) |
| U6 | a "Showing:" line above a held question | test_ios_client_contract.py:1265 (the Python client gate) |
| L1 | the Turkish note is the English one | ReadingTests.swift:457 |
| L2 | the Turkish question back is the English one | ReadingTests.swift:457 |
| L3 | the note's example dropped (English) | ReadingTests.swift:457 |
| L4 | "Find a model" and "No" say the same in Turkish | ReadingTests.swift:457 |

**This seat's own faults (X).** "Every test" means the 460 Swift tests and 1659 Python tests at
`a4c898f`. "(new)" marks this seat's test, which kills the fault when it is in place.

| id | file | the fault | result at `a4c898f` | killed by |
|---|---|---|---|---|
| X1 | Router | boundary: only "a model search" is a search; no verdict or an unknown one is a doubt | KILLED | ReadingTests.swift:227 |
| X2 | Router | boundary: a missing verdict (nil) is a doubt | SURVIVED (every test) → T10 | ReadingTests.swift:496 (new) |
| X3 | Router | boundary: every decline is a doubt, whatever the verdict | SURVIVED (every test) → T10 | ReadingTests.swift:496 (new) |
| X4 | Router | boundary: every surface answer is a doubt | KILLED | ReadingTests.swift:227, :255, :269, :279, :296 |
| X5 | Router | boundary: the two closed choices in the other order | KILLED | ReadingTests.swift:227; RefinementBoundaryTests.swift:105 |
| X6 | Router | boundary: "something else" renamed "not a search" | KILLED | ReadingTests.swift:227, :241, :248, :279, :441; RefinementBoundaryTests.swift:105 |
| X7 | Router | schema: the verdict generated first | KILLED | RefinementBoundaryTests.swift:105 |
| X8 | Router | schema: a third, "not sure" verdict offered | KILLED | RefinementBoundaryTests.swift:105 |
| X9 | Router | instructions: the paragraph that defines the verdict removed | SURVIVED (every test) → T13 | test_router_hints.py:690 (new) |
| X10 | FrontDoor | recordsGap: a note is kept, only a doubt is not | KILLED | ReadingTests.swift:334 |
| X11 | FrontDoor | recordsGap: every search kept, measured or not | KILLED | FrontDoorTests.swift:721; ReadingTests.swift:334, :441 |
| X12 | ContentView | held branch: only a note is held; a doubt is answered unasked | KILLED | test_ios_client_contract.py:806 |
| X13 | ContentView | held branch: `routing = nil` dropped (the old notice shows over the card) | SURVIVED (every Python test; compiles) → T11 | test_ios_client_contract.py:1288 (new) |
| X14 | ContentView | held branch: `asked = typed` dropped | SURVIVED, equivalent (N1) | N1 |
| X15 | ContentView | held branch: the reading not held | KILLED | test_ios_client_contract.py:806 |
| X16 | ContentView | confirm: the field not locked while it answers | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X17 | ContentView | confirm: the field never unlocked after it answers | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X18 | ContentView | card: "Find a model" calls `decline` | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X19 | ContentView | card: "No" calls `confirm` | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X20 | ContentView | card: "Find a model" does nothing | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X21 | ContentView | card: both buttons in English on the Turkish screen | SURVIVED (every Python test; compiles) → T12 | test_ios_client_contract.py:1288 (new) |
| X22 | ContentView | confirm: answers without reading the outcome as a search | KILLED | test_ios_client_contract.py:806 |
| X23 | Router | vision gate: the rule reads `assistant`, not `vision` | KILLED | ReadingTests.swift:296, :426 |
| X24 | Router | vision gate: the rule on the model tier only | KILLED | ReadingTests.swift:426 |
| X25 | Router | vision gate: the measured condition inverted | KILLED | ReadingTests.swift:296, :426 |
| X26 | Router | vision gate: the override says measured | KILLED | ReadingTests.swift:296, :426 |
| X27 | Router | vision gate: the override keeps the `vision` surface | KILLED | ReadingTests.swift:296, :426 |
| X28 | Router | vision gate: the image rule never fires (tested on the surface id) | KILLED | ReadingTests.swift:296, :426 |
| X29 | Router | read: a doubt needs both pasted content and an instruction | KILLED | ReadingTests.swift:241, :255, :279 |

## Tests added/extended this review

**In this worktree, uncommitted** (`git diff`: 4 files, +80, tests and the Swift manifest only). The
whole diff is `docs/reviews/m18-wave-3-tester-2.patch`. Each new test sits at the end of its file.

| test (file:line) | closes | red on (in place, one fault at a time) |
|---|---|---|
| `ios/EngineTests/ReadingTests.swift:496` `testOnlySomethingElseIsADoubtOnEitherBranch` (class `ReadingVerdictFaultTests`, `:489`) | T10, REQ-ASK-005, REQ-GAP-001 | X2, X3 |
| `tests/unit/test_ios_client_contract.py:1288` `test_a_held_question_clears_the_old_answer_and_its_two_taps_do_what_they_say` | T11, T12, REQ-ASK-005, D-169 clause 4 | X13, X16, X17, X18, X19, X20, X21 |
| `tests/unit/test_router_hints.py:690` `test_the_model_is_told_what_each_of_its_two_verdicts_means` | T13, REQ-ASK-005 | X9 |
| `ios/EngineTests/test-manifest.txt` | the new Swift test, from `swift test --list-tests \| sort` | n/a |

- **Green:** each passes at `a4c898f`. `make check-fast` PASS with them: 1661 Python passed, 25
  skipped; 461 Swift tests, exactly the manifest; `ruff check` clean.
- **Red:** each was run against each fault it is written for, in place, with the bytes written back
  after. Each failed by assertion. The harness's Swift filter did not name the new class, so X2 and X3
  went on to the whole suite: 461 tests, the new test failing with 4 and 6 assertion failures.
- **No held-out question** is in any of them; the held-out gate passes.

*Filled by: Tester seat 2 (independent) · Date: 2026-10-04 · Commit range: `93040ac..a4c898f`*
