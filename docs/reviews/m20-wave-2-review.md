---
record_type: review
id: m20-wave-2-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 2 Code Review (many boards into one list, #210)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `1c8c9e0` (red), `d42a313` (fix), `7ee9801` (red), `4f7fd8a` (fix), read as
`git show 1c8c9e0 d42a313` plus `git diff 0f4fe14 4f7fd8a` (W1 merged in at `0f4fe14`)
**Risk tier:** HIGH (`ios/ModelRanking/Engine/Combine.swift`)

## Verdict
MINOR

`combineFamily` does what D-188 clauses 2 to 4 say. It reads positions only. Its arithmetic stays in
`Combine.swift`. Its one sort is permitted by both ordering gates. On the served boards it gives
exactly the eleven counts D-188 clause 2 records. It is fast for 25,000 positions spread over a few
boards. The findings fall into three groups:
- **What the rule does (M1, M2, M4).** On today's boards, a stale board can outvote the only fresh one,
  and the plan says it never can. A model that only stale boards rank loses nothing to the half
  weight. These are the owner's questions, and W4's screen text depends on the answers.
- **What the tests check (M3, M6).** Three planted faults pass every test.
- **Cost and records (M5, M7).**

## How it was checked

- Read plan §1, §2 W2 and §5, and D-188 (`docs/decisions.md:4396-4436`), before the code.
- Ran `swift test --filter FamilyCombineTests` in a copy of `ios/` outside the worktree. The copy's
  `Combine.swift` has the same sha256 as the worktree's (`01c64ff4…`). Result: 10 passed.
- Ran `scripts/client_decl_gate.py`: `client-decls PASS` in all four configurations. Ran
  `tests/unit/test_ios_client_contract.py`: 51 passed.
- Combined every family in `src/app/workflows/families.py` from the served `/v1/boards` payload, as of
  2026-10-08 12:00 UTC, with a scratch Swift test that calls the shipping `combineFamily`. Every entry
  count matches D-188 clause 2 (coding 58, agentic-coding 18, everyday 130, expert 124, mathematics
  125, computer-use 85, abstract 80, web-dev 215, document 197, factuality 134, search 28). A Python
  copy of the rule gives the same lists. With exact fractions, it agrees with the nine-place rounding
  on every pair of models (0 disagreements).
- Planted four faults in the copy's `Combine.swift`. Each was restored by bytes and checked by sha256
  (`01c64ff4…`, match). Results:
  - P1, the weight added to the numerator only: every test passed.
  - P2, the row index read in place of the position: every test passed.
  - P3, `freshForDays = 30`: every test passed.
  - P5, no shared place: 2 tests failed.
- Deleted the copy and the scratch scripts afterwards. `git status` in the worktree shows only this file.

## Findings

### BLOCKING
None

### MINOR

- **M1** `docs/plans/m20-plan.md:73-75`, against `ios/ModelRanking/Engine/Combine.swift:161,166-167`
  and `ios/EngineTests/FamilyCombineTests.swift:166-205`: the plan lists four property tests, and the
  fourth is "a stale board can never move a model past one that leads on every fresh board". The wave
  ships three. The fourth was dropped without amending the plan, and the rule breaks it: half a weight
  is still a weight.
  **Failure, on today's boards:**
  - In `coding`, Arena's coding slice is the only fresh board. Claude 4.6 Opus leads it (#3), and
    Claude 4.7 Opus is #8. Claude 4.7 Opus is still placed first overall, on the stale
    `epoch_swe_bench_verified` (#1).
  - In `computer-use`, GPT-5.6 Sol leads GPT-5.5 on `arena_agent`, the only fresh board (10 against
    13). GPT-5.5 is still placed first of the two, on stale Terminal-Bench (#1).
  - Pairs that break the property: coding 164, everyday 475, web-dev 825, computer-use 22, agentic
    coding 13, expert 104, abstract 3.

  The owner approves the plan by merging it, so the owner would approve a promise the code does not
  keep.
  **Fix:** this is the owner's choice.
  - (a) Keep the rule. Amend plan §2 W2 and D-188 clause 4 to say a stale board can outvote a fresh
    one, and record the coding #1 as the measured example. Replace the property with a true one: an
    oracle that computes each weighted mean in exact fractions and checks the order against it.
  - (b) Change the rule so that fresh boards decide first.

- **M2** `ios/ModelRanking/Engine/Combine.swift:166-167, 174`: a mean over one board is that board's
  percentile, whatever its weight. So the half weight does nothing to a model that only stale or
  undated boards rank. The same holds for any model whose boards are all stale.
  **Failure, on today's boards:**
  - `computer-use`: 40 of 85 entries rest on stale Terminal-Bench alone, including place 4 (Claude 4.7
    Opus, Terminal-Bench #3).
  - `web-dev`: place 2 (GPT-6 Astra) rests on the undated `epoch_webdev` alone, as do 17 more entries.
  - `everyday`: 11 of 130 entries.

  W4's planned note ("it weighs half here", plan §2 W4) would be false for every one of those rows.
  **Fix:** this is the owner's choice. Either say in D-188 clause 4, and in W4's note, that the weight
  only matters between boards that rank the same model, or change the rule (for example, a stale board
  counts as half a board toward coverage). Add a test that pins whichever is chosen.

- **M3** `ios/EngineTests/FamilyCombineTests.swift:83-104, 150-164`: the tests do not pin the weighting
  arithmetic, positions shared on a board, or the 90-day line. P1, P2 and P3 above passed every test.
  - The two weighting tests (`:83`, `:98`) check only which of two models comes first. That order
    stays the same if the weight goes into the numerator only.
  - The generator always writes positions 1, 2, 3 and so on (`:157-158`), so a shared position, or a
    gap, never occurs. Position and row index are then the same number. The served boards have shared
    positions on 14 of 63 boards (`epoch_chess` has 69).
  - The generator's dates are 2026-05-01 and 2026-09-20 (`:160`). Both are far from the 90-day line,
    and it never makes an undated board or a family board the standings lack.

  **Failure:** someone could swap position for row index, or change the 90-day line to anything from
  19 to 105 days, and every test would still pass.
  **Fix:**
  - An example test: one model on one fresh board at 0.4, against a model on a fresh board at 0.2 and
    a stale board at 1.0. The correct rule puts the first model first (0.4 against 0.467). P1 puts the
    second first (0.35).
  - An example test with a tie, `[(a, 1), (b, 1), (c, 3)]`.
  - Tests at 90 and 91 days (see M6).
  - In the generator: shared positions, an undated date, a missing board id, and the exact-fraction
    oracle from M1.

- **M4** `ios/ModelRanking/Engine/Combine.swift:165`, D-188 clause 3 (`docs/decisions.md:4422`): D-188
  does not say what percentile a shared position gets. The code uses the board's own position, which is
  the best place in the tied group. So a group tied at the bottom never reaches the bottom.
  **Failure:**
  - A probe board of five: a is #1, and b, c, d and e share #2. The four tied for last get 0.25, as if
    they were second. b, c and d are placed ahead of a, which is first on that board and last on the
    other.
  - On the served boards, the 16 models sharing last place on `epoch_chess` (104 of 119) get 0.87.
  - Using the middle of each tied group instead would change the top ten of `coding`, `mathematics`,
    `abstract` and `factuality` (6, 6, 4 and 6 of their top-20 places).

  **Fix:** record the choice in D-188 clause 3. Either "a shared position counts as its group's best
  place", or the middle of the group: `((position - 1) + (tied - 1) / 2) / (size - 1)`. Pin it with
  M3's tie test.

- **M5** `ios/ModelRanking/Engine/Combine.swift:149, 161`: finding the family's boards takes time that
  grows with the square of the family's size. Each family id scans all the boards with
  `first(where:)`, and each board scans the `stale` array with `contains`.
  **Failure:**
  - A family of 25,000 boards with one position each (25,000 positions) took 33.7 s in a debug
    build.
  - By comparison, 25,000 positions in two boards took 0.09 s, and in one board 0.13 s.

  From W3 the family arrives on `/v1/categories`, which may be up to 256 KiB
  (`EngineClient.swift:196`). That is room for tens of thousands of ids, so a broken engine could
  freeze the screen. This is #74's failure again, by a new path.
  **Fix:** build the lookup by board id once, and make `stale` a `Set`. Add a cost test beside
  `CombineCostTests` (`ios/EngineTests/CombinePropertyTests.swift:139`).

- **M6** `ios/ModelRanking/Engine/Combine.swift:191-196`: the age is measured in seconds from midnight
  UTC of the evidence day. So a board turns stale one second into its 90th day.
  **Failure:**
  - A board dated 2026-07-10 is 90 days old on 2026-10-08, which is not "older than 90 days" (D-188
    clause 4, REQ-CMB-003). It is stale at 00:00:01 UTC and weighs half for that whole day.
  - The engine's source-health check calls the same board fresh (`age > window_days`,
    `src/app/workflows/coverage.py:254`). The same board, on the same day, would be fresh in the
    engine's notice and stale on the phone.

  **Fix:** compare whole UTC days, and call a board stale when its age in days is over 90. Add tests at
  90 and 91 days.

- **M7** `docs/plans/m20-plan.md:149-150`, `ios/EngineTests/FamilyCombineTests.swift:41`,
  `docs/prd.md:611`: some records disagree with the code.
  - Plan §5 (K.8) says `combine` gains the coverage rule and the weight, and `CombinedEntry` gains
    each board's weight. The wave instead adds a second function, `combineFamily`, with new types
    `FamilyEntry` and `FamilyList`. The stale boards are named on `FamilyList`, not given per entry,
    and the old `combine` stays. The plan was not amended.
  - The test `testAModelNeedsHalfTheFamilyAndAtLeastTwoBoards` names the "at least two" rule that
    `4f7fd8a` dropped, and REQ-CMB-002 cites it by that name.

  **Failure:** W4 will build on plan §5 and look for a per-board weight on `CombinedEntry` that does
  not exist. A reader of the PRD row sees a test named for a rule the code no longer has.
  **Fix:** amend plan §5 to name `combineFamily`, `FamilyList.staleBoards`, and how long the old
  `combine` stays. Rename the test (for example `testAModelNeedsHalfTheFamilyRoundedUp`) in the file,
  `test-manifest.txt` and `docs/prd.md:611`.

## What looks good

- Positions only, never a score (D-105). The new code reads `standing.position`, `standing.model`,
  the board's size and `evidenceDate`. `Standing` has no score field (`Models.swift:378-389`).
- D-181: arithmetic on positions stays in `Combine.swift`. `client-decls PASS` in four
  configurations. The added sort is permitted once in each gate, under D-188 clause 3
  (`scripts/client_decl_gate.py:306`, `tests/unit/test_ios_client_contract.py:437`).
- Each board counts a model once (`Combine.swift:163-164`). A position past the board's size is
  capped at 1.0 (`:165`). A one-model board has no division by zero (`:162`).
- W1's R1 is fixed. A family board the standings lack is left out and does not count toward coverage
  (`Combine.swift:149-151`, test `:116-123`). A family with no board kept throws `noBoards`.
- Rounding to nine places keeps equal means equal whatever the board order, and on the served boards
  it never joins two different means.

## Hardened-invariant producers

This is not an invariant-hardening wave. For the D-105/D-181 invariant ("positions only, and only in
`Combine.swift`"), the one new producer is `combineFamily` (`Combine.swift:143-188`). The test that
covers it is the D-181 gate (`client_decl_gate.py`, PASS). The gap: no test plants arithmetic on a
position outside `Combine.swift` for the new path. The existing gate mutants cover that class
(D-181, "Measured").

## Acceptance criteria evidence

- REQ-CMB-002, coverage of half rounded up and at least one: `Combine.swift:154, 173` +
  `FamilyCombineTests.swift:41-62` (cites REQ-CMB-002 at `:1`). Measured on the served boards: all
  eleven D-188 counts reproduced.
- REQ-CMB-002, the mean percentile `(position - 1) / (size - 1)`: `Combine.swift:162-167, 174` +
  `FamilyCombineTests.swift:65-79` (weaknesses in M3).
- REQ-CMB-002, equal means share a place and are ordered by id: `Combine.swift:176-185` +
  `FamilyCombineTests.swift:76-77`.
- REQ-CMB-002, an empty board or one the standings lack is left out: `Combine.swift:149-151` +
  `FamilyCombineTests.swift:116-123, 176-184`.
- REQ-CMB-003, a board past 90 days or undated weighs half, and the list names it:
  `Combine.swift:153, 161, 191-196` + `FamilyCombineTests.swift:83-104` (the boundary in M6, the
  arithmetic in M3).
- Plan §2 W2 properties: board order `:166-174`, empty board `:176-184`, better on every board
  `:186-205`. The fourth property is missing (M1).

## K.8 contract drift check

```
$ grep -n "^func combine\|^struct CombinedEntry\|^struct FamilyEntry\|^struct FamilyList" ios/ModelRanking/Engine/Combine.swift
25:struct CombinedEntry: Equatable {
47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
118:struct FamilyEntry: Equatable {
126:struct FamilyList: Equatable {
143:func combineFamily(_ standings: Standings, boards family: [String], asOf today: Date) throws -> FamilyList {
$ grep -n "struct BoardStandings" ios/ModelRanking/Engine/Models.swift
352:struct BoardStandings: Codable, Equatable, Identifiable {
$ grep -n '"means"\|"means.keys"' scripts/client_decl_gate.py tests/unit/test_ios_client_contract.py
scripts/client_decl_gate.py:306:    ("Combine.swift", "sorted", "means"): 1,
tests/unit/test_ios_client_contract.py:437:    ("Combine.swift", "means.keys"): (
```

- `combine` and `CombinedEntry` are unchanged. The new rule is a new function and new types, with no
  caller in `ios/ModelRanking` yet. `/v1/boards` is unchanged.
- Verdict: drifted from plan §5's wording, but compatible with the code. Nothing that already exists
  changed meaning. See M7.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/coverage.py:205` and `:254`: the engine has two different 90-day lines. A
  plan's evidence is stale at 90 days (`age < window_days` is fresh), and a source is stale only past
  90 days (`age > window_days`). On day 90 one board is both. This is a bug: pick one line (D-188
  clause 4 says "older than 90 days") and test both callers at 90 and 91.

## Risks queued to next M

- **R1** On today's boards, Arena is the only full-weight board in five families: `coding`,
  `agentic-coding`, `everyday`, `computer-use` and `web-dev`.
  - Stale: `aider`, `swebench`, `epoch_swe_bench_verified` and `epoch_terminalbench` are past 90
    days.
  - Undated, so they weigh half for good: `epoch_eci`, `epoch_mmlu`, `epoch_webdev`,
    `epoch_deepswe_external` and `epoch_arc_agi`. `src/app/workflows/standings.py:122` sends no date
    when no row is dated.

  D-188 clause 1 holds a family to one board per source so that one source cannot outvote the others.
  The weight brings that back through another door. It is real if #195's labelled set shows these five
  lists following Arena's slice, or if W4's screen shows "weighs half" against most of a family's
  boards.
- **R2** `ios/ModelRanking/Engine/Combine.swift:182`: if one standing names a model missing from
  `models`, the whole family's list throws `unknownModel`. With coverage of one on two-board families,
  every model on either board now enters, so one bad row on any board blanks the surface. W1's R1 was
  the same kind of failure. The served payload has none today, since the engine builds both lists
  from one table. It is real if a payload ever ships a standing whose model is not in `models`. The
  fix would be to leave such a row out, as a missing board is.
