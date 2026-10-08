---
record_type: review
id: m20-wave-1-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# Wave 1 Tester Review (m20)

**Reviewer:** Tester subagent, fresh eyes. This seat wrote none of the wave's code, tests or records.
It is not the wave's Code-Reviewer, and it is not the Stage 5.1 security seat.
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `a53d0ce..e05f4b7`. W1's own commits are `1074c85` (red), `928440d` (fix), `ab14584`
(the review's tests, red) and `6921a75` (the review's fixes), plus merges of the plan branch. The diff
read is `git diff a53d0ce e05f4b7 -- src tests ios docs/decisions.md`: 8 files, +247 / -3.
**Risk tier:** HIGH (`docs/plans/m20-plan.md:50`, `src/app/adapter/main.py` changes).
**Code-Reviewer verdict:** MINOR, M1 to M6, K1, R1 (`docs/reviews/m20-wave-1-review.md`). Not
BLOCKING, so this seat runs. Its M1 to M3 and M5 are fixed in `6921a75`; its M4 is a hold.
**Model routing (HIGH, advisory):** author family: Claude (`GP-Agent: claude-code/local-lane`) /
reviewer family: Claude (Opus 5.5). Fallback reason: no second model family is available to this seat.
**Base-pinned policy:** `.claude/agents/Tester.md` has the same sha256 (`64b0a75dac85...`) on
`origin/main` and in the tree. The range touches neither `.claude/` nor `.agents/`.

## Verdict
MINOR

Every acceptance criterion has a citing test that passes, and both red commits were red on their
own trees. Fault injection found five holes. Three of them (a facet of Arena's text vote beside
`arena`, and two kinds of wrong reason on a refinement board) are now closed by tests written in this
review. Two stay open as findings: a board moved between families is caught by no test (M4), and the
`search` pair looks like one vote counted twice (M1), which is a ruling for the owner, not a test.

## Acceptance-criterion coverage (REQUIRED)

REQ-CMB-001 (`docs/prd.md:610`; plan `docs/plans/m20-plan.md:42`, §2 W1). The module docstring of
`tests/unit/test_families.py:1` cites it. The tests added here cite it on each test.

- `/v1/categories` names each surface's family, the primary first, through the live route →
  `tests/unit/test_families.py:65` `test_the_categories_name_each_surfaces_family` (TestClient on
  `adapter.app`, a seeded artifact): the served `boards` equals `FAMILIES` in order, and its first
  board is `primary_board` - GREEN.
- One declared table, every surface, primary first → `tests/unit/test_families.py:30` - GREEN.
- Every declared board in a family or named outside with a reason, failing closed →
  `tests/unit/test_families.py:44`, with `:75` (the declared set equals the attributable set, the
  review's M4) - GREEN.
- Every board the **live** `/v1/boards` serves is placed (plan §2 W1's gate) → was read only from the
  declarations; the seeded artifact the route tests use serves 2 boards. **Wrote**
  `tests/unit/test_families.py:193`, which writes every declared Arena slice into the seeded artifact
  and checks `/v1/boards` against the families the live `/v1/categories` names - GREEN (M5).
- A family holds at most one board of each source (D-188 clause 1) → `tests/unit/test_families.py:92`
  (prefix-based) and, **written here**, `:174` (derived from the declared configs) - GREEN (M2).
- A board outside is named with its true reason (D-188 clause 1) → `:114` one way; **written here**,
  `:129` the other way - GREEN (M3).
- Each surface's second benchmark is in its family → `:105` - GREEN.
- Additive, no field changes meaning → `tests/unit/test_uncertainty_contract.py:324`
  (`test_every_surface_publishes_exactly_the_agreed_field_set`, the set at `:316-321`) and
  `tests/unit/test_ios_payload_contract.py:135` - GREEN.
- The phone decodes `boards` as optional, absent from an older engine →
  `ios/EngineTests/EngineClientTests.swift:174`
  `testTheFamilyDecodesAndIsAbsentFromAnOlderEngine`, in the manifest, passed in this run's
  `swift-test` leg (`build/swift-xunit.xml`) - GREEN.

## Red→green on reported symptoms

Both red commits were run on their own trees (`git archive <sha> | tar -x` into the scratchpad, then
pytest with that tree's `src` first on the path; no checkout):
- `1074c85`: 3 failed, 1 passed (`…led_by_its_primary_board`, `…named_outside_with_its_reason`,
  `…name_each_surfaces_family`). GREEN at `928440d` onward.
- `ab14584`: 3 failed, 5 passed. The review's M1 to M3 tests are red; its M4 (declared = attributable)
  and M5 (the Swift decode) are holds, as the commit message says. GREEN at `6921a75`.

## Suite result

- `make check-fast` (before this file and the last lint fix): typecheck, records, test, client-decls
  and swift-test PASS; lint FAIL on one line of my own new test (SIM300), fixed. Re-run after this
  file: see the last line of this section.
- `test` leg: 2190 passed, 25 skipped. `swift-test` leg: 510 tests, exactly the manifest's.
- Coverage on touched code: `families.py` is data and is wholly imported; the one new line in
  `main.py` (`:1359`) is run by every `/v1/categories` test. No drop.
- Final `make check-fast`: all six legs PASS (lint, typecheck, records, test, client-decls, swift-test).

## Mocks / contract tests

- No new integration. The live-route test seeds through the existing `test_api_v1._seeded_db`
  fixture and writes rows the way the build writes them; it adds no mock.

## Fault injection

Each fault was planted by exact string replacement, run against the families, contract, refinement,
`/v1` API, payload, category-title and W-125 server-import tests (and, for every survivor, the whole
unit suite with `-n 8`), then restored by bytes and checked by sha256: `families.py` `cbb3053dea18…`,
`main.py` `0d3d18496c64…`, `test_families.py` `f51c012f3dbf…` (as committed; the T rows ran on
`2f0df4dbc796…`, the file with my first two tests). Every restore matched. `git status` shows only my
test file and this record. Script: the scratchpad's `w20-tester-faults.py`.

| # | Fault planted | Before this review | After |
|---|---|---|---|
| F1 | board moved: `aider` from `coding` to `agentic-coding` | caught: `…second_benchmark_is_in_its_family` | caught |
| F2 | board moved: `epoch_frontiermath_t4` from `mathematics` to `abstract` | **survived** (whole suite) | **survived** (M4) |
| F3 | board moved: `epoch_simpleqa` from `factuality` to `expert` | **survived** (whole suite) | **survived** (M4) |
| F4 | facet beside parent: `arena_text_multi_turn` into `assistant`, out of OUTSIDE | caught: `…counts_one_board_twice_through_its_facets` | caught by both facet tests |
| F5 | facet beside parent: `arena_vision_ocr` into `vision` | caught: same | caught by both |
| F6 | facet beside parent: `arena_agent_steerability` into `computer-use` | caught: same | caught by both |
| F7 | facet beside parent: `arena_factuality` (config `text_factuality`) into `everyday` beside `arena` | **survived** (whole suite) | caught: `:174` (M2) |
| F8 | primary not first: `mathematics` | caught: `…led_by_its_primary_board`, `…name_each_surfaces_family` | caught |
| F9 | primary not first: `search_factuality` | caught: same two | caught |
| F10 | reason changed: `arena_text_chinese` given `_NO_LANGUAGE` | **survived** (whole suite) | caught: `:129` (M3) |
| F11 | reason changed: `_DOMAIN` reworded to "a facet … no surface measures" | **survived** (whole suite) | caught: `:129` (M3) |
| F12 | reason changed: vision languages claim "a refinement the question adds" | caught: `:114` | caught: `:114`, `:129` |
| F13 | reason blanked: creative writing | caught: `…named_outside_with_its_reason` | caught |
| F14 | a family board (`arena_text_coding`) also named outside | caught: same | caught |
| L1 | `arena_text_polish` dropped from OUTSIDE | caught: `:44` | caught: `:44`, `:193` |
| M1 | `boards` dropped from `/v1/categories` | caught: field-set, payload contract, `…name_each_surfaces_family` | caught |
| M2 | `boards` sorted | caught: `…name_each_surfaces_family` | caught |
| M3 | `boards` reversed | caught: same | caught |
| M4 | `boards` renamed `board_ids` | caught: three tests | caught |
| M5 | `boards` cut to the primary | caught: `…name_each_surfaces_family` | caught |
| M6 | `boards` without the primary | caught: same | caught |
| T1 | gate: `_declared_boards` reads no Arena slices | caught: three tests (the `> 50` floor, the M4 equality) | caught |
| T2 | gate: `_parent` made a no-op | survived alone (a weakened gate, by construction) | alone survived; with F4: caught by `:174` |
| T3 | gate: the refinement regex reads nothing | caught: the `> 10` floor | caught |
| T4 | gate: served family compared as sets | survived alone | alone survived; with M2: caught (`[0] == primary_board`) |
| T5 | gate: the "in a family and outside" check dropped | survived alone | alone survived; with F14: **survived** |

Single faults: 17 of 25 caught before this review, 20 of 25 after (21 of 26 with L1). The two code
survivors left are F2 and F3 (M4). The three T rows weaken the gate itself, so alone they stay green
by construction; paired with the code fault each one hides, T2 and T4 are now caught and T5 is not
(one assertion guards that rule; noted, not a finding).

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `src/app/workflows/families.py:35-36`: `search` and `search_factuality` each hold
  `arena_search` and `arena_search_factuality`. The module counts a config named `<config>_<facet>` as a
  facet of that config's vote (the `agent_*` configs, `_AGENT_FACET`), and `search_factuality` is
  named that way. On the served boards they rank the same 27 models with a rank correlation of 0.92,
  the same as `arena_agent` against its own steerability facet (0.921), which stands outside.
  **Failure:** D-188 clause 1 says a family holds at most one board of each source. Here two views of
  one vote make up the whole family, so W2's combined list for "search" is one vote averaged with
  itself, and the wave's facet test (`tests/unit/test_families.py:84-89`) cannot see it, since it
  knows only three prefixes. **Fix:** a ruling, then one edit. Either each of these surfaces keeps
  one board (as `vision` does) and the other board moves outside with a facet reason, or D-188
  records that a factuality config is a vote of its own and `_arena_votes`
  (`tests/unit/test_families.py:145`) says so. Either way, empty `_OPEN_ONE_VOTE_TWICE`
  (`tests/unit/test_families.py:171`). The test fails when the set is no longer needed, so it
  cannot outlive the question.

- **M2** `tests/unit/test_families.py:84-89`: the wave's facet test reads a board's source from three
  hand-kept prefixes (`arena_text_`, `arena_vision_`, `arena_agent_`). **Failure:** F7 planted
  `arena_factuality`, which is drawn from Arena's text vote (config `text_factuality`), beside `arena`
  in `everyday`. The whole unit suite stayed green, and Arena text then held two of three weights.
  **Fix:** written in this review, uncommitted: `test_no_family_holds_two_boards_of_one_arena_vote`
  (`:174`) works out each board's vote from the declared configs (`ARENA_BOARDS`, `ARENA_SLICES`). It
  fails closed if that finds no facets. Commit it.

- **M3** `tests/unit/test_families.py:114-123`: the review's M3 test checks one direction only: a
  reason may not claim a refinement the table lacks. **Failure:** F10 (`arena_text_chinese` given
  "names no one language") and F11 (every domain board given a facet reason) stayed green on the whole
  suite. W3 reads these reasons to find the boards a question adds, so it would lose a language or
  all eight domains and no test would fail. **Fix:** written in this review, uncommitted:
  `test_a_board_the_refinement_table_adds_stands_outside_and_says_so` (`:129`) checks that every
  board `Refinements.swift` adds stands outside every family, and that its reason says the question
  adds it (equality, read through `test_refinements._entries()`). Commit it.

- **M4** `src/app/workflows/families.py:22-37`, `docs/decisions.md` D-188 clause 1: no test sees a
  board moved between families. F2 (FrontierMath Tier 4 into `abstract`) and F3 (SimpleQA into
  `expert`) stayed green on the whole suite. A move breaks no rule a test can derive. Only the owner's
  approval of D-188 can catch it, and D-188 does not list the families. The plan says it does ("D-188
  first. It records the families", `docs/plans/m20-plan.md:53`). D-188 gives only their measured
  counts. **Failure:** the owner approves D-188 without seeing which boards stand in which family. A
  later edit can move a board and change what W2 combines, and no test and no record changes.
  **Fix:** list each family, primary first, in D-188 clause 1 (or a table under it). Then add a test
  that the table in D-188 equals `FAMILIES`, like `test_adr_citations.py` reads `decisions.md`, so a
  move must change the record too.

- **M5** `tests/unit/test_families.py:44-82`: plan §2 W1's gate is "every board `/v1/boards` serves",
  and no test read that route. The route tests' seeded artifact serves two boards. **Failure:** low
  today, because the review's M4 hold ties the declared set to the attributable set, which is all
  `board_standings` will serve. But the criterion's second half was proven only from declarations,
  never through the live entry point. **Fix:** written in this review, uncommitted:
  `test_every_board_the_live_route_serves_is_in_a_family_or_named_outside` (`:193`). It writes every
  declared Arena slice into the seeded artifact, then checks the live `/v1/boards` against the
  families the live `/v1/categories` names. L1 shows it goes red. Commit it.

## Tests added/extended this review

All in `tests/unit/test_families.py`, uncommitted (sha256 `2e4f6ee2a6e3…`, +96 lines):
- `:129` `test_a_board_the_refinement_table_adds_stands_outside_and_says_so`: REQ-CMB-001, D-188
  clause 1 (the reason of a refinement board); kills F10 and F11.
- `:145` `_arena_votes`, `:171` `_OPEN_ONE_VOTE_TWICE`, `:174`
  `test_no_family_holds_two_boards_of_one_arena_vote`: REQ-CMB-001, D-188 clause 1 (one board per
  source); kills F7 and T2 with F4; holds M1 open by name.
- `:193` `test_every_board_the_live_route_serves_is_in_a_family_or_named_outside`: REQ-CMB-001 through
  the live `/v1/boards` and `/v1/categories`; kills L1.
