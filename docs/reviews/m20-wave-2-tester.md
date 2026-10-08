---
record_type: review
id: m20-wave-2-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 2 Tester Review (many boards into one list, #210)

**Reviewer:** Tester subagent (fresh eyes; did not author the wave and was not its Code-Reviewer)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** the wave's own commits `1c8c9e0` (red), `d42a313` (fix), `7ee9801` (red), `4f7fd8a` (fix),
`fb0adfe` (red), `bc7f9f5` (fix); tested at `14c9ac7`
**Risk tier:** HIGH (`ios/ModelRanking/Engine/Combine.swift`)

## Verdict
MINOR

Every criterion has citing tests that pass, and each red commit fails only on its own tests. But 14 of
32 planted faults passed the wave's 13 tests. The worst: replacing the mean with a sum passes every
test, and the mean is the core of D-188 clause 3. I wrote 12 tests (uncommitted, in the worktree).
With them, 31 of 32 faults fail a test. The one that still passes is equivalent: it changes code that
cannot run. The author commits the tests to close M1 to M4.

## How it was checked

- Read `.claude/agents/Tester.md`, `.agents/rules/practices.md`, D-188 (`docs/decisions.md:4396`),
  REQ-CMB-002 and REQ-CMB-003 (`docs/prd.md:611-612`) and the Code-Reviewer's verdict
  (`docs/reviews/m20-wave-2-review.md`, MINOR) before the tests.
- I planted the faults in a copy of `ios/` outside the worktree
  (`scratchpad/w20b-fi/ios`), with a script that does one exact string replacement in `Combine.swift`.
  It refuses an anchor that does not match exactly once. For each fault it runs
  `swift test --filter FamilyCombineTests`, writes the original bytes back, and checks the sha256.
  Every restore matched `9545a43fb0e5…`, the worktree's hash.
- I ran each red commit's `ios/` from `git archive <commit> ios` into a scratch folder, with no
  checkout, through `swift test --parallel`.
- Served boards: I combined every family in `src/app/workflows/families.py` from
  `scratchpad/served-boards.json` as of 2026-10-08 12:00 UTC. I used a scratch test in the copy that
  calls the shipping `combineFamily`, and compared it with a Python version of the rule in exact
  fractions.
- Ran `make check-fast` in the worktree with the new tests.

## Acceptance-criterion coverage (REQUIRED)

- REQ-CMB-002 (coverage, the mean percentile, shared places ordered by id, missing boards and models
  left out). `ios/EngineTests/FamilyCombineTests.swift` cites it at `:1`. The tests are `:42` (coverage),
  `:66` (the percentile), `:110` (a shared position), `:120` (a model the list lacks), `:127` (positions
  in family order), `:136` (a missing board), `:268` (no board kept) and the three properties at
  `:308`, `:318` and `:329`. All are GREEN.
  - Gaps: the mean itself (M1), a tie of three (M2), the rounding and the input guards (M3), and the
    review's M5 cost (M4). Tests now exist for each, at `:150-266`, and each cites REQ-CMB-002 on its own line.
- REQ-CMB-003 (every board counts the same; past 90 days or undated, named). Cited at `:1`. The tests
  are `:83` (old), `:92` (undated) and `:101` (90 and 91 days). All are GREEN.
  - Gap: an unreadable date (M3). Test added at `:246`.
- Served boards: every family matches the exact-fraction version (entries, places, coverage and
  named boards), with 0 of 14 differing. The counts are those of D-188 clause 2: coding 58,
  agentic-coding 18, everyday 130, expert 124, mathematics 125, computer-use 85, abstract 80, web-dev 215,
  document 197, factuality 134, search 28, search_factuality 27. Boards named today: coding 3 of 4,
  agentic-coding 2 of 3, everyday 2 of 3, abstract 1 of 3, expert 1 of 3, computer-use 1 of 2 and
  web-dev 1 of 2.

## Red→green on reported symptoms

Each red commit's tree was run on its own (`swift test --parallel`, the whole Engine suite):

- `1c8c9e0`: 6 of 518 failed, all among the 9 tests this commit added, against its stub. The 3
  properties passed against the stub (see below). A seventh failure,
  `ReadingTests/testNoGenuineTuningQuestionTripsASignal`, came from my archive, not the commit. The test
  reads `scripts/router_probe/`, which my first archive of `ios/` alone left out. With that folder
  added, `ReadingTests` passes (11 of 11).
- `7ee9801`: 3 of 520 failed. All are tests this commit added or changed:
  `testAFamilyBoardTheStandingsLackIsLeftOut`, `testAModelNeedsHalfTheFamilyAndAtLeastTwoBoards` and
  `testAnUnknownBoardOrModelIsRefused`.
- `fb0adfe`: 4 of 523 failed. All are tests this commit added or rewrote:
  `testAModelTheModelListLacksIsLeftOut` (R2), `testAnOldBoardCountsTheSameAndIsNamed` (M2, R1),
  `testAnUndatedBoardCountsTheSameAndIsNamed` and `testTheNinetyDayLine` (M6).
  - `testASharedPositionCountsAsThatPosition` (M4) was green on the red. That is right: M4 asked
    for the existing choice to be recorded, not changed. F08 fails it.
  - The review's M5 had no red test at all (M4 below).
- The tree after the last fix (`14c9ac7`) is green: `make check-fast`, below. I did not run the
  earlier fix commits on their own.

Two commits changed existing assertions, and neither weakens a test:
- The fix `4f7fd8a` replaced "a and b are the first two" with "a, b, c in that order, a and b sharing
  a place". The large board's other models now enter under the new coverage, and the new assertion
  still pins the tie and its order (F15 and F16 fail it).
- The red `fb0adfe` removed the half-weight assertions and the `unknownModel` refusal. D-188 clause 4
  and R2 changed the rule, and the replacements assert the new rule.

Three of `1c8c9e0`'s nine tests, the properties, were green against its stub, which returns an empty
list. Two have since failed under planted faults: `:318` under F03 and F21, and `:329` under F05 and
F31. `testTheBoardsOrderChangesNothing` (`:308`) has never been red: it fails under none of the 32
faults. Even F25, the one fault that makes the order matter, passes it in all 60 seeds, so `:215` now
pins the rounding instead.

## Suite result

- `make check-fast` at `14c9ac7` plus the new tests: **PASS in 149.2 s**. Six legs: lint, typecheck,
  records, test, swift-test (`swift-test-parallel`, 535 tests, each in the manifest) and
  client-decls. An earlier run with 11 of the 12 new tests also passed (200.2 s).
- `swift test --filter FamilyCombineTests` in the copy: 25 tests, 0 failures. The cost test's
  `combineFamily` call takes 0.14 s.
- Coverage on touched code: line coverage was not measured. The fault table stands in for it. Every
  branch a fault touched now fails a test, except the unreachable `continue` at `Combine.swift:181`
  (F23).

## Mutation table

32 faults planted in `combineFamily` and `isStale`. "Before" is the wave's 13 tests. "After" adds
the 12 tests written in this review. Line numbers are those of the file with the new tests.

| id | fault | before | after (the test that fails) |
|---|---|---|---|
| F01 | coverage `count / 2` (rounded down) | killed (`:42`) | killed |
| F02 | coverage at least two | killed (3 tests) | killed |
| F03 | coverage over the family's ids, missing boards counted | killed (`:136`, `:318`) | killed |
| F04 | coverage `>` in place of `>=` | killed (3 tests) | killed |
| F05 | percentile from `position`, not `position - 1` | killed (`:329` only) | killed |
| F06 | percentile over `size`, not `size - 1` | killed (`:66`) | killed |
| F07 | no cap at the board's size | **survived** | killed (`:187`) |
| F08 | the row index in place of the position | killed (`:110`) | killed |
| F09 | 90-day line at `>=` | killed (`:101`) | killed |
| F10 | `freshForDays = 30` | killed (`:101`) | killed |
| F11 | `freshForDays = 120` | killed (`:83`, `:101`) | killed |
| F12 | age in seconds from midnight (the review's M6) | killed (`:101`) | killed |
| F13 | an undated board not named | killed (`:92`) | killed |
| F14 | an unreadable date not named (undated still named) | **survived** | killed (`:246`) |
| F15 | ties ordered by id descending | killed (`:66`) | killed |
| F16 | no shared place | killed (4 tests) | killed |
| F17 | a tie's place is its index (1, 1, 2) | **survived** | killed (`:160`) |
| F18 | a board named twice counts twice | **survived** | killed (`:169`) |
| F19 | a model listed twice on a board counts twice | **survived** | killed (`:177`) |
| F20 | a board the standings lack throws | killed (`:136`, `:268`) | killed |
| F21 | a board that ranks no model is kept and counted | killed (`:318`) | killed |
| F22 | a model the list lacks is not filtered before placing | **survived** | killed (`:195`) |
| F23 | `continue` at `Combine.swift:181` throws instead | survived | survived: equivalent, the filter at `:172` makes `:181` unreachable |
| F24 | means compared to two places | **survived** | killed (`:231`) |
| F25 | means compared unrounded (scale 1e18) | **survived** | killed (`:215`) |
| F26 | the sum, not the mean | **survived** | killed (`:150`) |
| F27 | the mean over every kept board (a missing rank counts as 0) | **survived** | killed (`:150`) |
| F28 | the fresh boards named in place of the stale | killed (3 tests) | killed |
| F29 | `FamilyList.boards` keeps the boards that rank no model | **survived** | killed (`:207`) |
| F30 | a board id sent twice: the last copy wins | **survived** | killed (`:239`) |
| F31 | a worse mean placed first | killed (4 tests) | killed |
| F32 | the pre-fix scan per family id (the review's M5) | **survived** | killed (`:256`) |

Before: 18 of 32 killed. After: 31 of 32 killed, and the one survivor is equivalent. Every restore
was checked by sha256 (`9545a43fb0e5…`, match, 33 runs). Script: `scratchpad/w20b-tester-mutants.py`.

## Mocks / contract tests

- No integration in this wave. `combineFamily` is pure, and the tests build their `Standings` with
  one local helper (`FamilyCombineTests.swift:19-34`). The served-board run above stands in for a
  contract: the shipping function on the served payload, against an exact version of the rule.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/EngineTests/FamilyCombineTests.swift:66-80` against
  `ios/ModelRanking/Engine/Combine.swift:173`: nothing tests the MEAN of D-188 clause 3. F26 (the sum)
  and F27 (dividing by every kept board) pass all 13 tests. In `:66`, a, b and c each stand on both
  boards, so a sum and a mean give them the same order.
  **Failure:** a later change drops `/ Double(list.count)`, or divides by `boards.count`. Then a model
  ranked by fewer boards is placed ahead of one that does better on average, and every test stays
  green. On today's boards this changes the top ten of `web-dev` (2 models) and of `abstract`,
  `document`, `factuality` and `mathematics` (1 each). `computer-use` has 82 of its 85 entries resting
  on one board.
  **Fix:** commit `testTheMeanIsOverTheBoardsThatRankTheModel` (`:150`). It has one model at 0.375 over
  two boards against one at 0.5 on one board, pins the whole order and the places, and fails under F26 and F27.
  Add it to REQ-CMB-002's evidence (`docs/prd.md:611`).

- **M2** `ios/ModelRanking/Engine/Combine.swift:182-183`, tested only by `FamilyCombineTests.swift:110`:
  three or more models sharing a place are never tested. F17 (`tied ? index : index + 1`) passes all 13
  tests.
  **Failure:** three models sharing first place are shown as 1, 1, 2, which says one of them is second
  when none is. The served boards have 46 groups of three or more models sharing a position
  (`epoch_chess` alone has 69 shared positions).
  **Fix:** commit `testThreeModelsSharingAPositionShareOnePlace` (`:160`), which expects 1, 1, 1, 4.

- **M3** `ios/ModelRanking/Engine/Combine.swift:148, 151, 164, 165, 170-173, 186, 192`: nothing tests
  the input guards or the nine-place comparison. F07, F14, F18, F19, F22, F24, F25, F29 and F30 each
  pass all 13 tests. The fixtures never send a board id twice, a model twice on one board, a position
  past the board's size, an unreadable date, a model the list lacks sorted ahead of a known one, or
  means that differ only in floating-point noise.
  **Failure, one per guard:**
  - **Board named twice (`:148`).** From W3 the family comes from `/v1/categories`. If a two-board
    family arrives with one id repeated, the coverage rises from 1 to 2 without the dedup, and the
    union becomes the intersection that D-188 clause 2 replaced.
  - **Unrounded means (`:173`).** Without the rounding, a and b get different places although both
    average 0.2: a's 0.1 + 0.2 + 0.3 is not b's 0.3 + 0.2 + 0.1 in floating point. The comment at
    `:170` promises this cannot happen. The board-order property (`:308`) did not catch it in 60 seeds.
  - **Model the list lacks (`:172`).** Without the filter, a model the list lacks that sorts first
    shifts every place after it by one. If it ties with the next model, `entries[index - 1]` at `:183`
    reads past the end and traps.
  **Fix:** commit the nine tests at `:169`, `:177`, `:187`, `:195`, `:207`, `:215`, `:231`, `:239` and
  `:246`. Each one fails under its fault, as the table shows.

- **M4** `ios/ModelRanking/Engine/Combine.swift:150-152`: the Code-Reviewer's M5, fixed in `bc7f9f5`,
  shipped without the cost test the review asked for. F32 puts back the pre-fix scan
  (`standings.boards.first(where:)` for each id), and it passes all 13 tests. The largest family any
  test builds has six boards.
  **Failure:** a later change reintroduces the scan, and a family list near the 256 KiB cap freezes
  the screen (33.7 s for 25,000 boards, as the review measured). No test sees it. This is #74's
  failure again.
  **Fix:** commit `testAFamilyOfManyBoardsCombinesWithoutFreezing` (`:256`). It runs 25,000 undated
  boards against a 5 s bound, beside `CombineCostTests`. The shipping code takes 0.14 s, F32 fails it,
  and the boards are undated so that the time measured is the lookup's.

## Tests added/extended this review

All in `ios/EngineTests/FamilyCombineTests.swift`, uncommitted. The 12 names are added to
`ios/EngineTests/test-manifest.txt`, which stays sorted (535 lines).
- `:150` `testTheMeanIsOverTheBoardsThatRankTheModel`: REQ-CMB-002, the mean (M1)
- `:160` `testThreeModelsSharingAPositionShareOnePlace`: REQ-CMB-002, shared places (M2)
- `:169` `testABoardNamedTwiceCountsOnce`: REQ-CMB-002, coverage (M3)
- `:177` `testAModelListedTwiceOnABoardCountsOnce`: REQ-CMB-002, coverage (M3)
- `:187` `testAPositionPastTheBoardsSizeCountsAsItsLast`: REQ-CMB-002, the percentile (M3)
- `:195` `testAModelTheModelListLacksTakesNoPlace`: REQ-CMB-002, R2's places (M3)
- `:207` `testABoardThatRanksNoModelIsNotAmongTheListsBoards`: REQ-CMB-002, the list's boards (M3)
- `:215` `testEqualMeansSummedInADifferentOrderShareAPlace`: REQ-CMB-002, the nine-place comparison (M3)
- `:231` `testMeansAThousandthApartStayApart`: REQ-CMB-002, the nine-place comparison (M3)
- `:239` `testABoardIdSentTwiceIsReadAtItsFirstCopy`: REQ-CMB-002, the M5 lookup keeps the first copy (M3)
- `:246` `testAnUnreadableDateIsNamed`: REQ-CMB-003, an unreadable date (M3)
- `:256` `testAFamilyOfManyBoardsCombinesWithoutFreezing`: REQ-CMB-002, the review's M5 (M4)

The worktree shows only these two test files and this record as changed. The fault copy, the
red-commit trees, the probe and the oracle are all under `scratchpad/`, outside the worktree.
