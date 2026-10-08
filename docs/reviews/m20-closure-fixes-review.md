---
record_type: review
id: m20-closure-fixes-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 closure fixes -- Code review

**Reviewer:** Code-Reviewer subagent (fresh eyes; I wrote none of the code, tests or records in the range)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `1a8ebcf..38b9a7b`, read with its red commit and fix: `e1ae742` and `1a8ebcf` (the M20
closure security seat's S1 to S4), `188f61e` and `fe2b906` (the M20 repo review's M1), `38b9a7b` (records
only, checked against the code)
**Risk tier:** HIGH

## Verdict
MINOR

**Method.**
- Read each commit with `git show` and the code around it: `main.py`, `families.py`, `Refinements.swift`,
  `AnswerPlan.swift`, `Combine.swift`, `Models.swift`, `ContentView.swift`, and D-188.
- Ran the gates. `tests/unit/test_rate_limit.py`, `test_families.py` and `test_uncertainty_contract.py`:
  58 passed. `test_router_hints.py`, `test_ios_client_contract.py` and `test_refinements.py`: 104 passed,
  1 skipped. In a scratch copy of `ios/`, `swift test` on `QuestionFamilyTests`, `FamilyPlanTests`,
  `PayloadDecodingTests` and `FamilyCombineTests`: 74 tests, 0 failures.
- Planted faults. Python mutants were byte-restored and checked by sha256 (`main.py` `d136171c7b7e`,
  `families.py` `bcb9577e2cae` before and after); `git status` stayed clean. Swift mutants ran on the
  scratch copy against the whole Engine suite, 584 tests. In that copy,
  `ReadingTests.testNoGenuineTuningQuestionTripsASignal` always fails because it reads
  `scripts/router_probe/`, which lies outside `ios/`. That failure comes from the copy, not from a
  mutant.
- Ran a probe (`ZZReviewProbe`, scratch only) to show two edge cases of the family path.

| Planted fault | Result |
|---|---|
| `RATE_WEIGHTS` boards 30 -> 29 | killed (`test_the_boards_answer_counts_as_thirty_requests`) |
| `_limited` declared after `_known_host` again | killed (`test_a_wrong_host_is_refused_before_it_is_counted`) |
| `REFINED_BOARD["everyday"]` -> `epoch_mmlu` | killed (`test_a_refinement_takes_the_place_of_its_votes_board_and_never_joins_beside_it`) |
| log-once back to `count + weight == limit + 1` | **survived** (58 passed) -> M3 |
| judged by `count + 1`, stored by `weight` | **survived** (58 passed) -> M3 |
| one-board guard back to `list.boards.count > 1` | killed (`testAOneBoardFamilyWithALanguageIsThatLanguagesList`) |
| replacement falls through to the add path | killed (`testARefinementTakesThePlaceOfItsVotesBoard`) |
| family cap ignored | killed (`testAFamilyOfThousandsIsCutAndReadOnce`) |
| `PlanMemo` drops `refinedBoard:` | **survived** (584 run, only the copy's own failure) -> M5 |

## Findings

### BLOCKING
None

### MINOR

- **M1** `ios/ModelRanking/Engine/AnswerPlan.swift:222` (with `Refinements.swift:117-119`). **Two
  chips, one board: the domain's chip says it was counted when it was not.**
  - The fault. `familyBoards` now puts only the first allowed refinement in place of the
    `refined_board`, so "of a language and a domain, the language stands" (D-188 clause 6). But
    `familyPlan` still passes every `offered` refinement to the view as a chip. The screen shows
    each chip under "Also counted" (`Language.swift:641-642`).
  - The failure. `expert` with French and Legal (model tier, all boards in the standings) gives
    `boards=["epoch_gpqa", "arena_text_french", "epoch_mmlu"] chips=["french", "legal"]` (probe
    `testProbeTwoRefinementsTwoChipsOneBoard`). The reader reads "Also counted: French, Legal", but
    Legal's board is in no list. Tapping Legal's × changes nothing. Tapping French's × makes Legal
    count.
  - Why it matters. It is the false chip `AnswerPlan.swift:174-175` exists to prevent ("a chip for a
    board that is not counted would say it was"). Each tier gives one refinement of each kind, so
    every question that names both a language and a domain, on a surface with a `refined_board`, hits
    it.
  - The fix. Where `refinedBoard` names a board in the family, offer only the refinement that stands.
    That is the first one in `RefinementKind.allCases` order that the surface allows and whose board
    the standings hold. Keep the removed state as it is. Add a `FamilyPlanTests` case: `expert` with
    French and Legal must give `view.refinements == [french]`, and with French removed, the family's
    own list and the French chip to restore. Do this before build 3 is archived.

- **M2** `ios/ModelRanking/Engine/AnswerPlan.swift:212`. **The one-board exception is wider than
  D-188 clause 5 says: any family left with one board that is not its primary is now shown as a list.**
  - The fault. The guard `list.boards.count > 1 || list.boards.first?.id != family[0]` was meant for a
    refinement that took the family's only place. `combineFamily` drops every board the phone's
    standings lack or hold empty (`Combine.swift:152`). So a family whose primary is missing, and
    whose other boards are all missing but one, also passes the guard.
  - The failure. `everyday` (`epoch_eci`, `arena`, `epoch_mmlu`), with standings that hold only
    `arena` and no refinement, gives a one-board "combined" list of `arena` (probe
    `testProbePrimaryMissingLeavesOneOtherBoard`). Before `fe2b906` this was the cards. The view is
    built with `staleness: nil` (`:223`), so the primary's own health notice goes with them.
  - It contradicts the records. The docstring at `:194` ("A family that leaves one board is today's
    cards") and `docs/architecture.md` ("a family of one board is its cards") both say otherwise.
  - The fix.
    `guard list.boards.count > 1 || kept.contains(where: { $0.board == list.boards.first?.id }) else {`.
    Add a `FamilyPlanTests` case with the `everyday` family and standings that hold only `arena`:
    the plan must be `.cards`.

- **M3** `src/app/adapter/main.py:296` and `:299`; `tests/unit/test_rate_limit.py:307-315`. **Two
  wrong forms of the weight pass every gate.**
  - The cause. The S1 test asks for five boards in a row from zero. The counts it reaches are 30, 60,
    90, 120 and 150, and none of them falls between two thresholds.
  - Mutant one: `count + weight == limit + 1`, the pre-weight log rule. A client pushed past the
    limit by a boards answer is never logged, so the operator signal from the W5 review's M4 goes
    silent for the one route S1 is about.
  - Mutant two: judged by `count + 1` but stored by `weight`. At 91 to 119, a boards answer is served
    and the client is taken to 121-149. That is one more 0.5 MB answer a minute than the runbook's
    "at most four".
  - The fix. Add one test at limit 120. Send 100 light requests, then a boards request, and expect
    429 and exactly one "rate limited" line. Then send one light request and expect 429.

- **M4** `src/app/adapter/main.py:224-233` (`rate_limit_problems`), `:215`. **Any limit from 1 to 29
  refuses `/v1/boards` to every client, for good, and the boot check accepts it.**
  - The failure. `count + 30 > limit` holds from a count of zero, so every phone's standings fetch
    is a 429 all day. Its `Retry-After` promises that waiting will help. A new install then has no
    standings and no family list, which is the product's core answer.
  - The trigger. The owner lowers `MODEL_RANKING_RATE_LIMIT` in `fly.toml` to slow a scraper (the
    runbook invites changing it). The test fixture already runs at 3.
  - The fix. Either `rate_limit_problems` refuses a non-zero limit below `max(RATE_WEIGHTS.values())`
    (a strict boot then refuses it, like an unreadable limit), or `_over_limit` charges
    `min(weight, limit)`. Add a test for whichever is chosen.

- **M5** `ios/ModelRanking/Engine/AnswerPlan.swift:361` and `ios/ModelRanking/ContentView.swift:354`.
  **Nothing gates the wire from the decoded `refined_board` to the plan.**
  - The evidence. Dropping `refinedBoard: inputs.refinedBoard` from `PlanMemo.plan` leaves the whole
    Engine suite green. `ContentView.swift:354` lies outside the package, and no Python contract test
    names it (`grep` of `tests/unit` and `scripts` for `inputs.family`, `refinedBoard`: no match).
  - The failure. A refactor drops either line, and every gate passes. The phone then takes "the older
    way" without a word, and one vote counts twice again (the repo review's M1 comes back).
  - The fix.
    - A `FamilyPlanTests` case through `PlanMemo`: `Inputs` with `family: ["arena"]`,
      `refinedBoard: "arena"` and a Spanish question must give the Spanish board alone.
    - A source tripwire in `test_ios_client_contract.py` for
      `inputs.refinedBoard = info?.refinedBoard`, next to `inputs.family = info?.boards`.

- **M6** `ios/ModelRanking/Engine/Refinements.swift:97-100`, `ios/ModelRanking/Engine/AnswerPlan.swift:192-195`,
  `docs/plans/m20-plan.md:159`. **The records describe the code from before `fe2b906`.**
  - `familyBoards`' docstring still says "then at most `maxAdded` refinements ... A refinement the
    family already holds takes none of the places". With a `refined_board`, one refinement replaces
    a board and none is added.
  - `familyPlan`'s docstring still gives the one-board rule (see M2).
  - The plan's K.8 section says `/v1/categories` gains only `boards`. `refined_board` is a second
    additive field, recorded in D-188 clause 6 but not in the plan's contract list.
  - The failure. The next wave reads the docstring or the plan and writes against the old behaviour
    (the record-drift class this project counts most often).
  - The fix. Rewrite the two docstrings. Add `refined_board` to plan §5 as an amendment line.

## Producers of hardened invariants
- **INV-88 (the limiter).**
  - Producers: `_limited` (`main.py:791-813`, declared before `_known_host`, so it runs inside the
    Host check), `_over_limit` (`:279-299`, the weight and the log), `_client_key` (`:261-276`),
    `RATE_WEIGHTS` (`:215`).
  - Citing tests: `test_rate_limit.py::test_the_boards_answer_counts_as_thirty_requests`,
    `::test_a_wrong_host_is_refused_before_it_is_counted`, `::test_a_refusal_is_logged_once_a_minute`,
    `::test_retry_after_is_the_rest_of_the_minute`, `::test_the_limiter_fails_open`.
  - Gaps: M3 (the weight's threshold and log), M4 (a limit below the weight), G-9 (recorded).
- **INV-89 (the one word reader).**
  - Producer: `familyPlan`'s `Refinements.read` (`AnswerPlan.swift:200`).
  - Citing tests: `test_router_hints.py::test_only_the_answer_plan_reads_refinements_from_the_words`,
    `::test_no_other_name_reaches_the_word_reader`.
  - Gaps: none found. `fe2b906` adds no request field and leaves `EngineClient.swift` and
    `Router.swift` untouched. `refined_board` flows from the engine to the phone only, and nothing
    typed reaches the engine.

## What holds (PASS evidence)
- **One vote, one board in the count.**
  - `familyBoards` replaces `refined` by the first allowed refinement whose board is not already
    there, and returns without the add path (`Refinements.swift:117-119`).
  - The model tier and the word reader both feed `chosen` (`AnswerPlan.swift:200`).
  - A removed chip leaves `kept`, so the family's own board returns (`:204`).
  - Two refinements: the language stands (`QuestionFamilyTests.swift:227-240`).
  - The Python gate holds every family with every refinement it allows to distinct votes
    (`test_families.py:239-259`).
  - With no `refined_board` (an engine from before the closure), the add path runs. D-188 clause 6
    records this, and the runbook deploys the engine and checks `refined_board` before the archive
    (`docs/release-testflight.md`, build 3 steps 2 and 3).
- **The restore path.** `assistant` in Spanish with the chip removed gives `.restorable([spanish])`
  (`FamilyPlanTests.swift:347-361`).
- **The middleware order** is the same under `TestClient` and in production. The Dockerfile runs
  `uvicorn app.adapter.main:app` (`Dockerfile:59`), with no wrapper in front. The stack, outermost
  first, is `_no_sniff`, `_known_host`, `_limited`, CORS, GZip. The planted reorder is killed.
- **`Retry-After`** is `max(wait, 1)` whatever the weight (`main.py:810`).
- **S3.**
  - `max(position, 1) - 1` cannot trap (`Combine.swift:167`), and the `combine` (D-167) path ranks
    by counts, not by subtraction (`:73-77`).
  - `familyBoards` dedupes in one pass, with a set, and stops at 16. Both are killed when planted.
- **K.8.** `refined_board` is additive: `String?` decodes an absent key and `null`
  (`EngineClientTests.swift:189-202`). The field-set contract test asserts set equality
  (`test_uncertainty_contract.py:314-331`), so the field is gated. Evidence:
  ```
  src/app/adapter/main.py:1494:                "refined_board": REFINED_BOARD.get(spec.id),
  tests/unit/test_uncertainty_contract.py:322:    "refined_board",
  ios/ModelRanking/Engine/Models.swift:88:        case refinedBoard = "refined_board"
  ```
- **`38b9a7b`.** The runbook's `grep -c refined_board` prints 1 on the new engine's one-line JSON and
  0 on the old engine, as its "above 0" check needs. The 25-at-a-time header check stays inside a
  minute. Two places are contradicted by the code: the architecture's "of a language and a domain,
  the language stands" holds for the count but not for the chips (M1), and "a family of one board is
  its cards" is wider in the code (M2).

## K.9 candidates spotted outside this wave's scope
None

## Risks queued to next M
- **R1** `src/app/adapter/main.py:295`. The weight makes `/v1/boards` four answers a minute per IPv4
  address, and a refused boards request is still added to the count.
  - The risk. Behind carrier NAT, a fifth phone fetching standings in the same minute is refused.
    Its 30 also takes the shared address over the limit, so its questions are refused until the
    minute turns.
  - What would show it is real. 429 lines on `/v1/boards` in the Fly log once the app has more than
    a handful of testers on one carrier.
  - The fix to weigh then. Do not add the weight of a refused request, and keep the log-once rule
    (which my "refused request not counted" mutant broke), or key `/v1/boards` on its own budget.
