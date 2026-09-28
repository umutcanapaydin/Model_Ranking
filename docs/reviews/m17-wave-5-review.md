---
record_type: review
id: m17-wave-5-review
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-28
---
# M17-W5 Code Review: the question selects the boards, and the combined list on the screen

**Reviewer:** Code-Reviewer seat, fresh eyes. I wrote none of this wave's code, tests or records.
**Independent:** yes
**Date:** 2026-09-28
**Commit range:** `c02fe0d..d4d7e8c`: 15 commits, including the merge of `main` (`9979324`), whose
content is already on the base. The diff covers 17 files, +1232 / -12. I read it as a whole.
**Risk tier:** HIGH (`docs/plans/m17-wave-5-plan.md:11`)
**Model routing (HIGH, advisory):**
- Author family: Claude (commit trailers `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second family is available to this seat.
- Fresh context: this seat had none of the authoring context.

**What I read first.** `git diff --stat c02fe0d..d4d7e8c -- .claude .agents AGENTS.md
permission-matrix.md` is empty, so the policy I applied is the base ref's. I read these, in order:
- `.claude/agents/Code-Reviewer.md`, `AGENTS.md`, `.agents/rules/practices.md`, and
  `permission-matrix.md` §11;
- the wave plan and `m17-plan.md` §W5 (`:82-88`);
- D-168 and its note (`docs/decisions.md:3151-3202`), D-167 and its amendment (`:3088-3149`),
  D-160 (`:2771`), D-126 (`:1022`), D-104 (`:308`), D-147 (`:2056`), D-112 (`:486`), D-115 (`:592`),
  D-138 (`:1626`) and D-150 (clause 2).

I read the code before the commit messages.

**How I worked.**
- **Gate.** I ran `make check-fast` at `d4d7e8c` on a clean tree. **PASS** in 46.8 s:
  - lint, typecheck and records: PASS;
  - test: 1511 passed, 23 skipped;
  - swift-test: 338 tests, exactly the manifest;
  - client-decls: PASS, 15 client files in 4 configurations. That gate type-checks
    `ContentView.swift` against the iOS SDK, so the view compiles even though `swift test` does not
    build it.
- **Mutants.** Each mutant was applied in place and restored by copy. Each restore was verified
  with sha256 against the pre-mutation hash:
  - `Router.swift` 9ec23f37…
  - `Refinements.swift` fe7c45da…
  - `AnswerPlan.swift` 1171bf38…
  - `ContentView.swift` 22a2ac1b…
  - `main.py` 04f1b87d…

  `PYTHONDONTWRITEBYTECODE=1` was set throughout. One `.pyc` that a `make` leg rewrote was deleted.
  The tree is clean apart from this file.
  - **Killed (10).**
    - S1: the boundary checks against the whole table instead of the surface's allowed entries.
    - S2: the boundary ignores the kind.
    - S3: a declined question keeps its refinements.
    - S4: `Refinements.boards` ignores the surface.
    - S5: `maxAdded = 3`.
    - S6: the plan offers boards the standings lack.
    - S7: the plan combines an unmeasured question.
    - S8: the restore chips appear without the combine check.
    - P1: `primary_board` serves the benchmark's name.
    - P2: a refinement names a board nobody serves.
  - **Survived (4).**
    - S9: `removed` is not narrowed to the offered refinements. This is equivalent: only offered
      chips are drawn.
    - S10: the refinement fields' `anyOf` is replaced by a free `String` schema. It passed every
      gate: 338 Swift tests, 41 Python tests and client-decls (**M3**).
    - P3: `removedRefinements = []` is deleted from `ask()`. It passed the whole `make check-fast`
      (**R1**).
    - P4: the restore-chips branch of the view is disabled (**R1**).
- **Measured** on the worktree's `advisor.db`, opened read-only (sha256 005855fa…, unchanged). It
  holds 63 boards and 308 models.
  - All 16 refinement boards are served, with 138 to 189 models each.
  - All 8 refinable surfaces' primary boards are served.
  - The 367 allowed combinations hold 30 to 189 shared models.
  - The cards were read through `TestClient` on a copy of the artifact.
- **Screens.** I read the simulator screenshots and accessibility dumps in the scratch
  `ui-shots/w5/`: `01-fr-0`, `01-fr-detail-0`, `04-detail-0`, and `03-code-0.txt`.
- **Probe record.** I recomputed the record's figures from the authors' raw run files in the
  scratchpad. I did not re-run the model.
- **Network.** None. I did not call `build()` and did not set `RUN_CONTRACT_TESTS`. I was the only
  seat in the worktree.

## Verdict
BLOCKING

**What holds.**
- **The boundary is right.** Nothing the on-device model writes can reach a board choice or the
  screen. `ModelOutputBoundary` keeps a refinement only when it is a declared table entry of the
  right kind that the chosen surface allows. Every one of those checks is pinned by a killed mutant.
- **Nothing new leaves the phone.** The only new request is the parameterless `/v1/boards` fetch.
- **The D-126 gates were widened narrowly.** Each widening carries a type pin and a construction
  tripwire.

**What blocks.** The screen side departs from three settled things without a ruling:
- the combined list drops the D-112 effort disclosure that the cards it replaces carry (**B1**);
- a coding question refined by `software` loses Ruling A's second answer (**B2**);
- `/v1/categories` gains a field that no ADR names (**B3**).

Each has a small fix or needs one owner ruling.

## Findings

### BLOCKING (must fix before this wave closes)

- **B1** `ios/ModelRanking/ContentView.swift:149-238`, `:1202-1244`. **The combined list replaces
  the cards and drops the disclosures they carried. The D-112 effort-mix notice is lost on every
  combination measured.**

  **What the branch hides.** When more than one board is chosen, the `.combined` branch
  (`:149-150`) replaces the whole `ForEach(ordered)` block (`:165-236`). That block holds:
  - `disclosures(answer)` (`:211`);
  - the ordering note (`:218`);
  - the effort line (`:223-233`).

  Neither the list nor `CombinedDetail` reads `Standing.effort` or `BoardStandings.rankingEffort`.
  In `ContentView.swift`, `grep -n effort` finds only the cards' lines.

  **What the ADRs require.** D-112 is ratified by the owner (`docs/decisions.md:494`). It says the
  answer carries the effort-mix notice whenever the compared models' evidence comes from different
  efforts. The D-167 amendment (`:3132`) added `effort` to every standing *"so the phone can
  disclose an unequal comparison as the surfaces do"*. This wave is the first consumer of those
  fields, and it discloses nothing.

  **Measured on the artifact.**
  - Every primary board a refinement can join has no `ranking_effort` and stands at mixed
    efforts. For example, `swebench` has 27 unspecified, 7 high and 4 medium; `arena_document` has
    22 unspecified, 7 high, 3 xhigh, 1 max and 1 medium.
  - I checked coding+software, assistant+French, document+Japanese+legal and expert+science. In
    each, the shared models stand at more than one effort on every chosen board.
  - The cards these lists replace carry `effort_mix_notice` on 6 of the 8 refinable surfaces:
    coding, assistant, document, mathematics, web-dev and factuality.

  **This is the common path, not an edge case.**
  - The probe selects more than one board on 14 of 40 questions (record §5).
  - Both maths questions carry `mathematical` in both runs.

  **A second disclosure is lost the same way.** `epoch_eci` (everyday) and `epoch_webdev` (web-dev)
  publish no `evidence_date`. The detail shows `observed_at` in its place (`:1217`), unlabelled. It
  is the day the engine read the board, not the day anything was measured, and the cards say so
  through `evidence_dating_note`.

  **Why the gate stays green.** The REQ-APP-003 gate asks only that `disclosures(` is called
  somewhere. Its own docstring concedes it cannot see a branch
  (`tests/unit/test_ios_client_contract.py:94-106`).

  **Why it blocks.** A ratified owner decision stops holding on the product's new main answer,
  without a ruling or a supersession (the profile's BLOCKING list, seed B.2). The M17-W4 review
  blocked on the same ADR for the same reason.

  **The fix, either of:**
  - disclose on the combined view and pin it with an `AnswerPlan`-level test. The fields are
    already decoded. For example: an effort sentence when the shared models' `effort` differs on
    any chosen board, and a label on an observation date;
  - put the omission to the owner and record the ruling as a dated note on D-168.

- **B2** `ios/ModelRanking/Engine/Refinements.swift:76-78`, `ContentView.swift:149-165`. **A coding
  question refined by `software` loses Ruling A's second answer.**

  **What happens.** `software` may refine `coding` (`:77`). For a question routed to `coding` with
  `software`, `answerPlan` combines `coding`'s primary board (`swebench`) with the Arena software
  slice. On the artifact that list holds 30 models. The combined branch then hides both answers the
  engine returned for `task=coding`. The reader sees one numbered list built on SWE-bench Verified,
  and the `agentic-coding` answer (DeepSWE) is not on the screen at all.

  **What the rulings require.**
  - D-115 is ratified (`docs/decisions.md:592-621`). The owner *"ruled that the buyer sees both"*.
  - REQ-APP-002 (`docs/prd.md:386`): `task=coding` shows both surfaces, with neither presented as
    the winner.
  - D-168 does not mention Ruling A.

  **This is the expected path, not a stray one.** The independent question set expects
  `coding + software` for both of its coding questions, and run 2 produced it for one of them.

  **Why it blocks.** A ratified ruling is reversed on one path without a ruling.

  **The fix, either of:**
  - the smallest: take `coding` out of `software`'s surfaces, as `agentic-coding` already is, with
    a boundary test;
  - an owner ruling recorded on D-168.

- **B3** `src/app/adapter/main.py:1343-1346`, `tests/unit/test_uncertainty_contract.py:313-318`.
  **`/v1/categories` gains `primary_board`, and no ADR or K.8 entry names it.**

  **No consumer breaks.** The field is additive, and it is optional on the client
  (`Models.swift:65`).

  **But the precedent is to name it.** Every field added to this discovery resource is named in its
  ADR: D-138 (`docs/decisions.md:1679`, *"The three new fields are additive on a discovery
  resource"*), D-153 and D-162.

  **Here nothing names it.**
  - The frozen key set was widened in the feature commit `eb46b52`, citing D-168.
  - D-168 mentions neither the route nor the field. `grep -n primary_board docs/` is empty.
  - The plan's K.8 section (`m17-wave-5-plan.md:38-47`) lists no `/v1` change.

  **Why it blocks.** The profile's BLOCKING list includes "public contract widened without ADR"
  (seed B.1), and §11 includes a K.8 contract miss.

  **The fix is cheap.**
  - A dated note on D-168 naming the field. It is the surface's `primary_source`, a `/v1/boards`
    id; the benchmark's name cannot serve, because two boards publish SWE-bench Verified (#53).
  - A K.8 line in the plan.

### MINOR (the author fixes each in this wave or files it as an issue)

- **M1** `ios/ModelRanking/ContentView.swift:268`, `ios/ModelRanking/Engine/Combine.swift:76-79`.
  **Tied models in the combined list are numbered 1, 2, 3, so the main answer's #1 is often decided
  by the alphabetical order of model ids.**

  The view numbers entries `item.offset + 1`. Combine breaks an equal sum by id, which D-167 clause
  3 permits for the ORDER. The on-screen number then presents that order as a ranking. On the
  artifact the top places are tied in 3 of the 5 combinations I computed. On document+French,
  Claude Opus 5 and Claude Fable 5.1 tie at a rank sum of 3; this is the pair shown as "1" and "2"
  in `01-fr-0.png`, and 16 of the 34 models share a sum with another model. On web-dev+software the
  top two tie at 4. On coding+software the top three tie at 5, and `claude-4-sonnet` is "1" by id.

  The number is also computed in the view. D-160 clause 2 gives position arithmetic to one named
  file. The name-based tripwire cannot see `offset` (already #60).

  The fix: a combined place computed in `Combine.swift` with competition ranking, carried on
  `CombinedEntry`, so tied models share a number, and a test for it.

- **M2** `docs/decisions.md:3195-3202`, `docs/research/m17-w5-refinement-probe-2026-09-28.md:24-28`,
  `:90-91`, `:107`, `:113-122`. **The records' numbers disagree with each other and with the runs.**

  **The D-168 note mixes two schemas.** Its figures come from the runs made with the kind field
  still in the schema (`final-v2-run1/2`: language 38, domain 36-37, both 34-35). Its "15 to 16 of
  the 17" takes the numerator from the merged runs and the denominator from the with-kinds count.
  The shipped schema measures lower, as the record's own table says (`:84-91`): language 37,
  domain 34-35, both refinements right on 31-33, and 15-16 clean of 19.

  A reader of the ADR gets the better figure for a configuration that did not ship.

  **The record contradicts itself.** §1 says 17 questions are in Turkish and 17 need no
  refinement; the table says "of 18" and "of 19". §5's median is 102.5 over the 14 lists, not 107.
  The sizes, 32 to 188, reproduce exactly.

  **"Method, re-runnable" is not true from the repository.** Both question sets and the harness live
  only in the scratchpad. D-147 clause 5's held-out discipline also needs the set kept, so a later
  wave knows what it must not tune against.

  **The plan has no fact-to-field map.** It builds a screen without the map D-150 clause 2 asks for.
  I checked each fact myself; see the PASS section.

  The fix: a dated correction line on D-168, the record's counts reconciled, and both question
  sets committed beside `scripts/router_probe/`.

- **M3** `ios/ModelRanking/Engine/Router.swift:424-435`, `:442-446`, `:514-517`,
  `docs/decisions.md:3169-3172`. **The schema half of the refinement boundary is pinned by nothing,
  the ADR describes a schema the code does not build, and the instructions contradict the table.**

  **Nothing pins the schema.** Mutant S10 replaced each refinement field's `anyOf` with a free
  `String` and survived every gate. No free text reaches a choice, because the boundary (tested)
  drops it. But D-168 clause 2's first layer can vanish silently.

  **The ADR describes another schema.** Clause 2 says the fields are *"restricted to those the
  chosen surface allows"*. The schema offers every declared value on every surface, and the
  restriction is applied only after generation. The code comment at `:516` says so; the ADR does
  not.

  **The instructions contradict the table.** They still tell the model to decline *"medical or
  legal questions"* (`:444-445`), while the table adds `medicine` and `legal` domains
  (`Refinements.swift:67-72`). The independent set expects legal questions answered with `legal`,
  and the model did so. The instructions and the table no longer agree about what is measured.

  The fix: a test that reads the refinement `anyOf` from `ModelRouter`, the way `anyOf:\s*known`
  is already held (`tests/unit/test_router_hints.py:124`); a correction line on clause 2; and the
  decline sentence reworded, with the probe re-run.

- **M4** `ios/ModelRanking/ContentView.swift:1209-1216`, `:322`. **The detail screen names the
  boards by their internal labels, and it states the shared count twice.**

  **Internal labels.** Readers see, in both languages, *"Arena text
  (industry_writing_and_literature_and_language)"* (`04-detail-0.png`). The chip that added it
  reads "Writing and language". The published field is used, so this is not a D-150 breach. But a
  reader cannot match a chip to its board. This is a new instance of #63 item 2 (internal ids shown
  to readers), on a screen #63 predates.

  **The count twice.** `combinedNote` and `sharedCount` say the same count one line apart
  (`:1209-1211`).

  **The chip's control.** VoiceOver reads the chip's remove control as "Close"
  (`03-code-0.txt`), which does not say what it removes.

  The fix: a label per refinement board from the table the chips already use, and one of the two
  count sentences. Or fold these into #63 with a comment there.

- **M5** `tests/unit/test_refinements.py:46-49`, `:60-63`, `:87-92`,
  `ios/EngineTests/RefinementBoundaryTests.swift:83-88`. **Four table tests are weaker than their
  names.**

  First, `test_each_surface_names_its_primary_board` compares the route with the expression the
  route serves (`spec.primary_source`). It cannot say whether that id is a board `/v1/boards`
  publishes. If it is not, every refinement on that surface silently falls back to the cards. All 8
  are served today, as measured. An `artifact`-marked check against the served payload (D-163)
  would hold it.

  Second, `test_every_refinement_names_a_board_the_engine_serves` checks the declared
  `ARENA_SLICES`, not `/v1/boards`, which the plan names (P1).

  Third, `test_a_vision_slice_refines_only_the_vision_surface` asserts nothing since the kinds left
  the table. This is the only leftover of the withdrawn dimension in the code or tests. Keep it as a
  guard for the future, but say so in its docstring.

  Fourth, `testTheWordingTierNeverRefines` passes trivially wherever `NLContextualEmbedding` has no
  assets (`outcome?.refinements ?? []`). The manual tier (`Router.swift:644`) has no test at all;
  it carries no refinement by construction.

### PASS (what looks good)

- **No free text from the model reaches a board or the screen.**
  - The surface must be in `known` (`Router.swift:549`).
  - Each refinement must be the declared entry of its own kind that the surface allows
    (`:531-536`). S1, S2 and S3 are killed.
  - `Refinement` is not `Decodable`. It is constructed only in the table
    (`test_router_hints.py:163-168`), and the egress gate's `.init(` ban also refuses the
    `Refinement.init(` and `.init(value:` spellings.
  - `refinementName` falls back to a declared value, never to model text.
  - `Refinements.boards` re-checks the surface (`Refinements.swift:104`), so a later path that
    assigns `outcome.refinements` directly still cannot add a board the surface disallows (S4
    killed).
- **Nothing derived from the question leaves the device (D-160 clause 1).**
  - The one new request is `client.boards()`, with no arguments (`ContentView.swift:751`). It
    passes the data-flow gate unchanged (`test_router_hints.py:170-241`).
  - It is fetched on the store's daily cadence whatever the question is. A refinement never
    triggers a load.
  - `EngineClient.swift`, `StandingsStore.swift`, `Combine.swift`, `scripts/` and
    `test_ios_client_contract.py` are unchanged across the range. So the egress, file-system,
    position and sort gates cover what they covered in W4, and client-decls now type-checks 15
    files including the two new ones.
- **The task-language rule is built in, not only prompted.** The table has no English and no
  Turkish (the app's two languages), and a language refines only the five chat-like surfaces. So a
  Turkish question about Python can add no language board whatever the model says. The prompt
  (`Router.swift:453-456`) and the probe cover the rest: 16 of 18 Turkish questions were right.
- **The owner's rulings are applied as ruled.**
  - (1) A surface plus declared refinements.
  - (2) `Combine.swift` is untouched, so D-167 clause 3 stays exact, and the detail states the
    shared count (`ContentView.swift:1211`).
  - (3) `combine` de-duplicates by board id only. The table cannot select two boards of one
    benchmark, so #53 does not arise in this wave.
  - (4) Cards for one board, the combined list for several (`AnswerPlan.swift:37-55`).
  - (5) Languages other than English, and domains only (`test_refinements.py:38-43`,
    `RefinementsTests.swift:56-60`).
- **The withdrawn "kind" dimension is gone from the code.** `RefinementKind` has two cases. The
  schema, the guidance, the names table and the prompt name only language and domain. The plan
  (deleted before merge) and D-168 clause 1 carry amendment notes rather than edits.
- **Every screen fact comes from a published field (D-150 clause 2), except as noted in M1 and M4.**
  - Name, vendor and price come from `/v1/boards` `models[]`.
  - Board, date and attribution come from `boards[]`. The date is unlabelled (B1).
  - Places come from `standings[].position`.
  - The shared count is the combination's own length.
- **Red came first.** Each of the five red commits holds tests only: `bb716b4`, `131ff2f`, `0951d52`,
  `3a7dcd5` and `d10b3bd`. The two defects the simulator found have red tests (`d10b3bd`) before
  their fix (`d4d7e8c`). Test edits in green commits are either the gate widening D-168 needed
  (`189e6e1`) or the kinds' removal (`9423642`), and each says so.
- **No drive-bys, no swallowed failures, no AI attribution.**
  - Every file is in the plan's scope.
  - `try?` on the schema and the response falls back to the next tier, as the surface always did.
  - `docs/decisions.md` is appended only.

## Producers of hardened invariant(s)

This wave hardens five invariants:
1. only declared refinements reach a board choice (D-104, D-126, D-168 clause 2);
2. nothing question-derived leaves the device (D-160 clause 1);
3. `RoutingOutcome` carries no free text (D-126);
4. the wording and manual tiers never refine (D-168 clause 4);
5. one board keeps the cards (D-168 clause 7).

| producer | invariant | citing test | gap |
|---|---|---|---|
| `ModelOutputBoundary.outcome/refinements` (`Router.swift:531-554`) | 1, 3 | `RefinementBoundaryTests` (11), `test_the_router_never_produces_anything_but_a_category_id` | none (S1-S3 killed) |
| `ModelRouter.route` schema (`Router.swift:424-470`) | 1 | none | the refinement `anyOf` is unpinned (**M3**, S10 survived) |
| `SimilarityRouter` / manual fallback (`Router.swift:389`, `:644`) | 4 | `testTheWordingTierNeverRefines` | vacuous without embedding assets; manual untested (**M5**) |
| `Refinements.boards` (`Refinements.swift:100`) | 1 | `RefinementsTests` (7), `testTheOutcomeNamesTheBoardsItSelects` | none (S4, S5 killed) |
| `answerPlan` (`AnswerPlan.swift:32`) | 5 | `AnswerPlanTests` (14) | none (S6-S8 killed) |
| `ContentView` wiring (`:142-158`, `:709`, `:751`) | 2, 5 | `test_nothing_typed_by_the_reader_reaches_the_engine` (egress half only) | state and branches unpinned (**R1**, P3/P4 survived); disclosures dropped (**B1**) |
| `/v1/categories` `primary_board` (`main.py:1346`) | the first board | `test_each_surface_names_its_primary_board` | tautological (**M5**); no ADR (**B3**) |

## Acceptance criteria evidence

- **P0**:
  - D-168 → `docs/decisions.md:3151-3202`, committed in `4d9f6f8` before any test.
  - the plan → `d22e607`.
  - the note on kinds → `c506a4a`.
- **P1**:
  - every entry names a served board → `tests/unit/test_refinements.py:46-49` (against the declared
    slices, **M5**)
  - surfaces and reason for each → `:52-57`
  - vision only on vision → `:60-63` (vacuous, **M5**)
  - languages and domains only → `:38-43`, `ios/EngineTests/RefinementsTests.swift:56-60`
  - primary, then at most two, in the declared order → `RefinementsTests.swift:17-23`, `:25-32`
  - the surface's restriction → `:34-39`
  - no board twice → `:41-46`
- **P2**:
  - a value outside the table dropped → `ios/EngineTests/RefinementBoundaryTests.swift:24-29`
  - another kind's value dropped → `:31-37`
  - a value the surface disallows dropped → `:39-46`
  - `none` adds nothing → `:48-54`, `:79-81`
  - a decline carries none → `:56-62`
  - an unknown surface refused → `:64-67`
  - the choices offered → `:69-77` (the function, not the schema; **M3**)
  - the wording tier → `:83-88`
  - nothing new sent → `tests/unit/test_router_hints.py:147-168`, `:170-241`, plus the unchanged
    `EGRESS` gate and client-decls, both run PASS
- **P3**:
  - one board shows the cards, several the combined list → `ios/EngineTests/AnswerPlanTests.swift:41-53`
  - boards, shared count, refinements → `:49-52`
  - removal recombines and can be restored → `:68-83`
  - missing boards → `:85-114`
  - an empty list is said → `:116-125`
  - both languages → `:127-135`
  - the detail's boards, dates and attribution and the "product's own" sentence → the view,
    `ContentView.swift:1202-1244` and `Language.swift` `combinedNote`. These are type-checked by
    client-decls and seen on the simulator, and no test cites them.
- **P4**:
  - probe → `docs/research/m17-w5-refinement-probe-2026-09-28.md` §2-§4 (inconsistent, **M2**)
  - combined list sizes → §5 (reproduced, apart from the median)
  - security pass → not in this range; the plan runs it before merge (`:12-13`).

## K.8 contract drift check

`grep -n` at `d4d7e8c`:
```
ios/ModelRanking/Engine/Router.swift:34:struct RoutingOutcome: Equatable {
ios/ModelRanking/Engine/Router.swift:207:protocol QuestionRouter {
ios/ModelRanking/Engine/Router.swift:488:enum ModelOutputBoundary {
ios/ModelRanking/Engine/Router.swift:507:    static func schemaChoices(for known: [String]) -> [String] {
ios/ModelRanking/Engine/Router.swift:517:    static func refinementChoices(for kind: RefinementKind) -> [String] {
ios/ModelRanking/Engine/Router.swift:531:    static func refinements(_ raw: [RefinementKind: String], for surface: String) -> [Refinement] {
ios/ModelRanking/Engine/Router.swift:538:    static func outcome(
ios/ModelRanking/ContentView.swift:675:    private func submit() {
tests/unit/test_ios_client_contract.py:171:SCORE_ARITHMETIC_PERMITTED = {"Uncertainty.swift": "D-138"}
tests/unit/test_ios_client_contract.py:176:POSITION_ARITHMETIC_PERMITTED: dict[str, str] = {"Combine.swift": "D-167"}
ios/ModelRanking/Engine/Combine.swift:43:func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
ios/ModelRanking/Engine/AnswerPlan.swift:32:func answerPlan(
ios/ModelRanking/Engine/Refinements.swift:27:struct Refinement: Equatable, Hashable {
ios/ModelRanking/Engine/Refinements.swift:100:    static func boards(primary: String, surface: String, chosen: [Refinement]) -> [String] {
ios/ModelRanking/Engine/EngineClient.swift:200:    func boards() async throws -> FetchedStandings {
ios/ModelRanking/Engine/Models.swift:65:    let primaryBoard: String?
src/app/adapter/main.py:1346:                "primary_board": spec.primary_source,
tests/unit/test_uncertainty_contract.py:317:    "primary_board",
```
- **Unchanged apart from line shifts:** the plan's symbols (`RoutingOutcome`, `QuestionRouter`,
  `ModelOutputBoundary`, `schemaChoices`, `submit`).
- **`POSITION_ARITHMETIC_PERMITTED`** is `{"Combine.swift": "D-167"}`, as #61 restored it. The
  plan's grep, dated `cce2ced`, shows `{}`, which predates #65.
- **`outcome(for:within:)`** gains a defaulted `refinements:` argument. Every existing caller still
  compiles.
- **`/v1/categories`** gains `primary_board`, which the K.8 section does not list (**B3**).

**Verdict: drifted (B3 only).**

## K.9 candidates spotted outside this wave's scope

- **K1** `tests/unit/test_ios_client_contract.py:94-120`. **The REQ-APP-003 gate cannot see a
  branch.** It asks that `disclosures(` is called somewhere in `ContentView.swift`, and W5 added a
  branch that bypasses the call on the main answer, with the gate green (B1). Now that the screen
  chooses between two presentations in `AnswerPlan`, a disclosure requirement can be held there as
  data, for example a `CombinedView` field the view must render, instead of as text. Process bug.
- **K2** `docs/prd.md:386-389`. **The prd rows REQ-APP-002, -003 and -005 describe a screen with
  only cards.** REQ-APP-003 says MET, citing the text gate above. REQ-APP-005 still says
  "orderings are rendered as received", while D-160 and D-167 now let the phone build an ordering.
  The milestone closure should restate them for the combined path, whatever B1 and B2 resolve to.
  Doc drift.

## Risks queued to next M

- **R1** `ios/ModelRanking/ContentView.swift:142-158`, `:709`. **The view's state and branches are
  held by no gate.** Two view mutants passed everything. Deleting `removedRefinements = []` (a
  removal then carries into the next question) passed the whole `make check-fast`, and disabling
  the restore-chips branch passed the client gates. These are exactly the class of the two defects the scratch simulator run found (`d10b3bd`,
  `d4d7e8c`). It is real the next time `ContentView` changes without that run. W-038 (no iOS UI
  test target) is the root.
- **R2** `ios/ModelRanking/ContentView.swift:144-148`, `ios/ModelRanking/Engine/Combine.swift:68`.
  **The plan is recomputed on every render.** `answerPlan`, and so `combine`, runs in the view body
  on every render, including each keystroke in the question field. The rank step is quadratic per
  board: about 36,000 comparisons per render for the 189-model `arena` board. The restore path
  calls `combine` a second time. It is real if typing lags on an older phone. Memoise the plan on
  `(routing, standings, removed)`.
- **R3** `ios/ModelRanking/ContentView.swift:748-756`. **The answer waits for the standings.** The
  standings fetch runs before the recommendation in `load()`. On the day's first load, and on every
  load after a day offline (a failed fetch keeps its old time, `StandingsStore.swift:76-78`), the
  answer waits for a ~500 KB download or its timeout. It is real on a slow connection.
