---
record_type: review
id: m20-wave-1-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-08
---
# M20 Wave 1 Code Review (each surface's family of boards, #209)

**Reviewer:** Code-Reviewer subagent (fresh eyes; did not author the wave)
**Independent:** yes
**Date:** 2026-10-08
**Commit range:** `origin/plan/m20..4ab765a` (red `1074c85`, fix `928440d`, merge of the plan branch `4ab765a`)
**Risk tier:** HIGH (`src/app/adapter/main.py`)

## Verdict
MINOR

The code does what the plan asks. The gate fails closed and reads the build's own declarations.
The server still loads no client. `/v1` changed by one added field. All 13 planted faults were
caught. The findings are about the data in the table: which boards stand in which family. Three of
them (M1, M2, M6) change what W2 will combine, so fix them in this wave, before W2 builds on the
table.

## How it was checked

- Read `docs/plans/m20-plan.md` §1, §2 W1 and §5, and D-188 (`docs/decisions.md:4396`) before the code.
- Read every board's declaration in `src/app/workflows/sources.py:122-391` and
  `src/app/workflows/board_tables.py:45-183`, and each surface's title and secondary benchmark in
  `src/app/workflows/categories.py`.
- Built the `/v1/boards` payload from the served `advisor.db` copy (`board_standings`). It serves 63
  boards. Every one is in a family or in `OUTSIDE_FAMILIES`, and every family board is served.
- Applied D-188 clauses 1 and 2 (at least half of the family's boards, and at least two) to the
  served standings, to see what W2 would get from this table (M1, M6).
- Ran `tests/unit/test_families.py`, `test_uncertainty_contract.py`, `test_refinements.py` and
  `test_nightly_refresh.py::test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers`:
  28 passed.
- Planted 13 faults. Each was restored by bytes and checked by sha256. `git status` was clean after
  (families.py `d65f0e16…`, main.py `0d3d1849…`, board_tables.py `547941ec…`).

| Fault planted | Caught by |
|---|---|
| F1 a declared board dropped from `OUTSIDE_FAMILIES` | `test_every_declared_board_is_in_a_family_or_named_outside_with_its_reason` |
| F2 a board in a family and outside | same |
| F3 the primary not first (coding) | `test_every_surface_has_a_family_led_by_its_primary_board`, `test_the_categories_name_each_surfaces_family` |
| F4 an undeclared board in a family | `test_every_family_board_is_a_declared_board` |
| F5 a board twice in one family | `…led_by_its_primary_board`, `…named_outside_with_its_reason` |
| F6 a blank reason | `…named_outside_with_its_reason` |
| F7 `families.py` imports `app.clients.arena` | the W-125 server-import test |
| F8 the served family sorted | `test_the_categories_name_each_surfaces_family` |
| F9 the served family cut to the primary | same |
| F10 a surface with no family | three tests, including the field-set test |
| F11 a new Arena slice declared in `board_tables.py`, no family | `…named_outside_with_its_reason` |
| F12 an undeclared board named outside | same |
| F13 the `boards` key dropped | `test_the_categories_name_each_surfaces_family`, the field-set test |

## Findings

### BLOCKING
None

### MINOR

- **M1** `src/app/workflows/families.py:23` (and `:20`): one board's own facet is counted next to it,
  which the module's own rule forbids (`families.py:7-10`: counting facets "would let one source's
  facets outvote the others"). `everyday` holds `arena` and `arena_text_hard_prompts`. Both are Arena
  text, and on the served data they rank exactly the same 198 models. **Failure:** under D-188 clause 2,
  99 of the 198 models in `everyday`'s combined list get in only because Arena text and its own slice
  both rank them, with no ECI place. Arena text then holds 2 of 3 weights in every mean. `coding` does
  the same with one benchmark from two publishers (`swebench` and `epoch_swe_bench_verified`, both
  "SWE-bench Verified"), so SWE-bench Verified holds half of coding's weight. The agent facets are
  handled the right way (`_AGENT_FACET`, line 39), which shows the rule was meant. **Fix:** move
  `arena_text_hard_prompts` into `OUTSIDE_FAMILIES` with the agent-facet kind of reason. Say in D-188
  whether two publishers of one benchmark count once. Add a test that a family with boards from more
  than one source holds at most one board per source and benchmark.

- **M2** `src/app/workflows/families.py:24`, against `src/app/workflows/categories.py:141-145`: MMLU
  (`epoch_mmlu`) is in the wrong family. It stands in `expert` ("Hard science questions") and not in
  `everyday` ("General knowledge"). But `everyday` already names MMLU as its secondary benchmark.
  **Failure:** `/v1/categories` for `everyday` will show `secondary_benchmark: "MMLU"` with `boards`
  that leave MMLU out. `expert` will combine a broad, saturated knowledge test with GPQA Diamond.
  **Fix:** move `epoch_mmlu` to `everyday`. Add a test that each surface's secondary benchmark's board
  stands in its family. Coding's Aider passes that test today.

- **M3** `src/app/workflows/families.py:36-37, 64`: some reasons for boards outside every family are
  wrong. They say "a refinement the question adds (D-168)". That is false for `arena_text_english`,
  `arena_text_non_english`, `arena_vision_chinese`, `arena_vision_english` and
  `arena_text_creative_writing`. `ios/ModelRanking/Engine/Refinements.swift` has no entry for any of
  them: D-168's note of 2026-09-28 dropped English and the "kinds", and
  `tests/unit/test_refinements.py:91-97` says the table holds no vision slice. "non_english" is not a
  language at all. **Failure:** the reason is the record AGENTS.md §3.5 asks for. W3 (a language word
  adds its slice) will read these reasons and believe a path exists that does not. Five served boards
  then reach no answer, with no record saying so. **Fix:** give these boards a separate reason ("served
  as standings; no question adds it, D-168 note"). Add a test that every board whose reason says
  "refinement" is a board in `Refinements.swift`, using `test_refinements._entries()`.

- **M4** `tests/unit/test_families.py:17-27`: the gate lists the four kinds of declaration plus a
  citation table, instead of the set of boards that can be served. **Failure:** if a fifth kind of
  declaration is added (one more registry tuple, written by the build and attributed in
  `rank.SOURCE_ATTRIBUTION`), its board is served on `/v1/boards` but is in no family and not named
  outside, and every gate still passes. That is a hand-kept list next to the thing it guards
  (AGENTS.md §3.5). The plan's gate is "every board `/v1/boards` serves" (§2 W1).
  `boards.declared()` (`src/app/workflows/boards.py:28`) is a third, narrower meaning of "declared".
  **Fix:** add `assert _declared_boards() == set(rank.SOURCE_ATTRIBUTION)`. `board_standings`
  refuses any source outside that set, so it is the true set of boards that can be served, and the
  assert holds today (63 = 63, checked).

- **M5** `docs/decisions.md:4408-4410`, `docs/architecture.md:119`,
  `ios/ModelRanking/Engine/Models.swift:66-67`: the records do not fully match the code.
  (a) D-188 clause 1 does not state the rule the code uses: a board that narrows a question stands
  outside every family, with its reason. The PRD row (`docs/prd.md:610`) and `families.py:7-10` both
  rely on that rule, and the owner approves D-188, not the module's docstring.
  (b) The architecture row names D-188 in its text but not in its ADR column.
  (c) The Swift comment says a `nil` family "then combines the primary board alone". No code does
  that before W2, and no EngineTests case decodes `boards`, either present or missing.
  (d) The plan places the table "in `app.workflows.board_tables` beside `ARENA_SLICES`"; it is in a
  new module, `app.workflows.families`, and the plan was not amended.
  **Failure:** the owner approves a clause that leaves out the membership rule, and W2 inherits a
  promise in a comment. **Fix:** add one sentence to D-188 clause 1. Add D-188 to the architecture
  row's ADR column. Add a decode test next to `UncertaintyTests.decode` (`:329`), or reword the comment
  as W2's contract. Add a one-line note to the plan about the module.

- **M6** `src/app/workflows/families.py:26, 28-30, 32-33`, read with D-188 clause 2
  (`docs/decisions.md:4411-4412`): six families have only two boards (computer-use, web-dev,
  document, factuality, search, search_factuality). For them, "at least half and at least two" means
  "both boards", which is the D-167 clause 3 intersection that D-188 is meant to replace. On the served
  data, seven surfaces would have a combined list shorter than their primary board alone:

  | Surface | Boards | Models on the primary board | Models in the combined list |
  |---|---|---|---|
  | computer-use | 2 | 43 | 3 |
  | factuality | 2 | 116 | 55 |
  | web-dev | 2 | 94 | 76 |
  | expert | 3 | 154 | 124 |
  | mathematics | 4 | 144 | 125 |
  | vision | 3 | 94 | 82 |
  | search | 2 | 28 | 27 |

  TerminalBench (dated 2026-05-14) and Agent Arena share only `gpt-5.4`, `gpt-5.5` and
  `gemini-3.1-pro`; the model ids were checked, and none is split across boards by spelling. **Failure:** once W4 makes the combined list the default, "Operating a computer"
  answers with 3 models where today it answers with 43. **Fix:** in this wave, write this table into
  D-188 so the owner approves with the numbers in view. Then either give two-board families a third
  board, or amend clause 2 before W2 (for example, a two-board family needs one board).

## Hardened-invariant producers

Producers of the invariant "every served board is in a family or named outside, the primary first":
`FAMILIES` and `OUTSIDE_FAMILIES` (`families.py:19, 43`), the four declaration tables
(`sources.REMOTE_SOURCES`, `LOCAL_BUNDLES`, `EPOCH_BOARDS`, `board_tables.ARENA_SLICES`), and
`CATEGORIES[*].primary_source`. Tests that cover each one: `test_families.py` (all four tests;
F1-F6, F10-F12) and F11 for `ARENA_SLICES`. Gaps: a fifth kind of declaration (M4); a reason that
does not match the phone's refinement table (M3).

## Acceptance criteria evidence

- REQ-CMB-001: `/v1/categories` names each surface's family, the primary first.
  `src/app/adapter/main.py:1359` (`"boards": list(FAMILIES[spec.id])`) +
  `tests/unit/test_families.py:65-69` (cites REQ-CMB-001 at `:1`).
- One declared table in the engine: `src/app/workflows/families.py:19-34` +
  `tests/unit/test_families.py:30-35`.
- Every declared board is in a family or named outside with its reason, failing closed:
  `tests/unit/test_families.py:44-50`, with `:26` (`len(declared) > 50`).
- Every family board is declared: `tests/unit/test_families.py:38-41`. Checked against the served
  `advisor.db` too (63 served, 0 missing either way).
- Additive: `tests/unit/test_uncertainty_contract.py:319-320, 324-329` (`"boards"` at `:320`).
- The phone reads it as optional: `ios/ModelRanking/Engine/Models.swift:68, 83`. `[String]?` is
  synthesized with `decodeIfPresent`. No memberwise `Category(` call exists in `ios/`, so the new `let`
  breaks no call site.
- W-125: `families.py` imports nothing. The fresh-interpreter server-import test passes, and F7 shows it
  catches a client import here.

## K.8 contract drift check

```
$ grep -n '"primary_board"\|"boards"\|^from app.workflows.families' src/app/adapter/main.py
49:from app.workflows.families import FAMILIES
1355:                "primary_board": spec.primary_source,
1359:                "boards": list(FAMILIES[spec.id]),
$ grep -n "^func combine" ios/ModelRanking/Engine/Combine.swift
47:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
$ grep -n "^ARENA_SLICES" src/app/workflows/board_tables.py
130:ARENA_SLICES: tuple[ArenaSlice, ...] = (
```

- `/v1/categories`: one key added (`boards`). `primary_board` is unchanged in value and meaning. No
  other route changed. `/v1/boards` is untouched (`git diff` touches no line of `boards()` or
  `standings.py`).
- Verdict: OK. The change is additive, as plan §5 says.

## K.9 candidates spotted outside this wave's scope

- **K1** `src/app/workflows/boards.py:15`: it imports `ARENA_SLICES` from `app.clients.arena_slices`,
  not from `app.workflows.board_tables`, where W-125 moved the table. The server does not import
  `boards.py` today (only `refresh.py` does), so nothing breaks. But the first serving-side import of
  `boards.py` would load a client, and that would be caught only by the transitive test. This is an
  enhancement: import from `board_tables`.

## Risks queued to next M

- **R1** A family names a board that the served `/v1/boards` may not carry. Every Arena source is
  `required=False` (`sources.py:172` and after), and `public.LEFT_OUT` (`src/app/workflows/public.py:31`)
  can remove a source from the hosted artifact. If W2's "half of the family" counts declared boards
  rather than served ones, one Arena outage would empty `search`, `search_factuality`, `document` and
  `vision`. It would show as an empty combined list on a surface whose primary board is served. W2's
  property tests should include "a family board missing from `/v1/boards`".
