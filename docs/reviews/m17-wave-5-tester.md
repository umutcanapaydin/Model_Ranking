---
record_type: review
id: m17-wave-5-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-09-28
---
# Wave 5 Tester Review (m17)

**Reviewer:** Tester subagent (fresh eyes). This seat wrote none of the wave's code, tests or
records. It is not either of the wave's Code-Reviewers, and it is not the security seat.
**Independent:** yes
**Date:** 2026-09-28
**Commit range:** `c02fe0d..4039fd4`: the whole wave, including the merge of `main` (`9979324`,
whose content is already on the base), both review verdicts (`6590ce8`, `64b970d`) and the fixes
after the second review (`4039fd4`).
**Risk tier:** HIGH (`docs/plans/m17-wave-5-plan.md:11`)
**Code-Reviewer verdict:** PASS-WITH-MINORS (`docs/reviews/m17-wave-5-review.md`, `64b970d`). It
supersedes the first reviewer's BLOCKING verdict (`6590ce8`), so this seat runs.
**Model routing (HIGH, advisory):**
- Author family: Claude (every commit carries `GP-Agent: claude-code/local-lane`).
- Reviewer family: Claude (Opus 5.5).
- Fallback reason: no second model family is available to this seat.
- Fresh context: this seat started from the role file, `practices.md`, `permission-matrix.md` §11,
  the plan, D-168 and its notes, the committed reviews and the diff. It has no memory of any
  authoring or reviewing session.
**Base-pinned policy:** `git diff --stat c02fe0d..4039fd4 -- .claude .agents AGENTS.md
permission-matrix.md .github` is empty, so every rule applied here is the base ref's.

## Verdict
PASS-WITH-MINORS

**Every acceptance criterion of P1 to P3 has a citing test that goes red when its behaviour is
removed, and P4's record reproduces where I checked it.** 73 mutants on the wave's load-bearing code: 59 killed, 5 equivalent in practice, and 9
that survive and are not equivalent:
- 3 are the on-device model's session call and its instructions. The plan puts these outside the
  suite by design, and the probe record measures them (P4).
- 2 are text-pin spellings of #60's class, not raised again.
- 4 are this verdict's two MINOR findings.

**Nothing blocks.**
- The boundary holds on every machine. A value the table does not declare, a value of another kind
  and a value the surface does not allow are each dropped, and each drop is killed by its own test.
- The Ruling A test derived from `CODING_INTENT` fires on both coding surfaces.
- The source pin fires on a refinement built in either the wording tier or the manual tier, and so
  do the Swift tests on their own on this Mac.
- `answerPlan`'s three branches, the effort notice, the date label and the place rule are each held.
- `primary_board` is held on the route, in the payload contract and in the phone's decoding key.
- No touched Python module loses coverage.
- `make check-fast` passes.

**What remains, both MINOR:**
- **M1:** D-168 clause 5 (#53: both publishers count) has no citing test. It is latent, because no
  two boards a question can select today share a benchmark.
- **M2:** three sentences in the Engine layer that carry held data to the detail screen and to the
  empty list have no test.

## Acceptance-criterion coverage (REQUIRED)

Every test named here is GREEN at `4039fd4`. Mutant ids are defined under "Fault injection".

**P0: records**
- D-168 → `docs/decisions.md:3151-3204`, with its notes at `:3206-3239`.
- The plan → `docs/plans/m17-wave-5-plan.md`, with the amendment note, the K.8 addition (`:51-56`) and
  the fact-to-field map (`:58-71`).

**P1: the refinement table** (`tests/unit/test_refinements.py`, `ios/EngineTests/RefinementsTests.swift`)
- **Every entry names a board the engine serves:**
  - against the declared slices, `test_refinements.py:46`;
  - against the served artifact (D-163), `:73`, which ran in the gate with
    `MODEL_RANKING_REQUIRE_ARTIFACT=1`.
  - GREEN. RT3 (a board id the engine does not serve) is killed by both.
- **Every refinement declares surfaces that exist, each with a reason:** `:52`. GREEN. RT5 (an entry
  without a reason) and RT6 (an unknown surface) are killed.
- **Vision slices refine only the vision surface:** `:91`. GREEN. The table holds no vision slice
  today, but the guard is not vacuous: RT4 (an `arena_vision_ocr` entry refining `assistant`) is
  killed by it.
- **A refinement is a language or a domain (owner ruling):** `test_refinements.py:38` and
  `RefinementsTests.swift:56`. GREEN.
- **Primary first, then at most two in the declared order:** `RefinementsTests.swift:13`, `:17` and
  `:25`. GREEN. RB1 (`maxAdded = 3`), RB4 (the order they came in) and RB6 (the primary left out) are
  killed.
- **The surface's restriction:** `:34`, and `allowed(for:)` at `:48`. GREEN. RB2 and RB5 are killed.
- **No board chosen twice:** `:41`. GREEN. RB3 is killed.
- **Values are unique within a kind, and never the way out:** `test_refinements.py:100`. GREEN.
- **A coding request takes no refinement (D-168 note 2, D-115 Ruling A):** `test_refinements.py:60`,
  which reads the surfaces from the route's own `CODING_INTENT` (`src/app/adapter/main.py:82`).
  GREEN.
  - RT1 (`software` refines `coding`, the reviewer's N10) and RT2 (`chinese` refines
    `agentic-coding`) are killed.
  - RT7 writes a `coding` entry as `.init(value: …)`, a spelling the table parser at `:21-34` cannot
    see. It is still killed: by the D-126 egress tripwire, which bans `.init(` anywhere in the
    client (`tests/unit/test_router_hints.py:358`, raised at `:470`).

**P2: the schema and its boundary** (`ios/EngineTests/RefinementBoundaryTests.swift`, `tests/unit/test_router_hints.py`)
- **Kept only when declared, of its own kind and allowed by the surface:**
  - `RefinementBoundaryTests.swift:16`, `:24`, `:31` and `:39`. GREEN.
  - MB1 (no surface check), MB2 (no kind check) and MB7 (checked against a fixed surface) are killed.
  - FR2 builds a `Refinement` from the model's own text, spelled `Refinement.init(`. It is killed by
    `:24`, `:31` and `:39`.
- **`none` adds nothing:** `:48`. GREEN.
- **A decline carries no refinement:** `:56`. GREEN. MB3 is killed.
- **An unknown surface is refused:** `:64` and `test_router_hints.py:120`. GREEN. MB6 is killed.
- **The schema offers each kind's declared values and the way out:** `:69` and `:79`. GREEN. MB4 (every
  kind's values offered) and MB5 (no way out) are killed.
- **The schema itself is built from those sets (D-168 note 6):** `test_router_hints.py:120-145`.
  GREEN.
  - SP1 (the whole table), SP2 (`anyOf: known`), SP3 (a free `String`, the reviewer's N11) and SP5 (the
    language choices on the domain field) are killed.
  - SP4 and SP6 survive: #60's class, see "Fault injection".
- **The wording and manual tiers never refine (clause 4):** `RefinementBoundaryTests.swift:83` and
  `:93`, and the source pin `test_router_hints.py:147`. GREEN.
  - TW1 (the wording tier) and TM1 (the manual tier) are killed by the pin.
  - The same edits run against the Swift tests alone (TW1s, TM1s) are killed too. The wording tier's
    test asserts on this Mac because the embedding assets load here.
- **`RoutingOutcome` carries no free text, and only the table constructs a `Refinement`:**
  `test_router_hints.py:169`. GREEN. FR1 (the model's text in a `Refinement(`) is killed.
- **Nothing new is sent:**
  - `test_router_hints.py:207` and `tests/unit/test_ios_client_contract.py` are unchanged in the
    range, and both pass.
  - `client-decls` passes: 15 files in 4 configurations.
  - The chip's action only changes `removedRefinements`, which is view state; it reaches no
    `client.` call.

**P3: the screen, in the Engine layer's view models** (`ios/EngineTests/AnswerPlanTests.swift` and others)
- **One board shows the cards, several show the combined list (D-168 clause 7, owner ruling):**
  `AnswerPlanTests.swift:41` and `:45`. GREEN. AP1 is killed.
- **Anything missing shows the cards:** `:37`, `:55`, `:60`, `:64` and `:111`. GREEN. AP2 (an
  unmeasured question combined) is killed.
- **A refinement whose board the standings lack is left out, and not offered to restore:** `:101`
  and `:85`. GREEN. AP3 and AP10 are killed.
- **Removing a refinement recombines on the device, and every removal leaves chips to restore:**
  `:68`, `:78` and `:94`. GREEN. AP4, AP5, AP8, AP9 and AP11 are killed.
- **The detail names each board:** `ios/EngineTests/LanguageTests.swift:449`. GREEN. AP22 (the
  reviewer's N8), AP23 and L5 are killed.
- **The detail gives each board's date, saying what it means (note 4):** `AnswerPlanTests.swift:180`.
  GREEN. AP18 (the reviewer's N7), AP20 and L4 are killed.
- **The detail gives each board's attribution:** `ios/EngineTests/CombineTests.swift:125`. GREEN.
- **The shared count (#54):** `AnswerPlanTests.swift:45` and `:116`. GREEN. AP21 is killed.
- **The "product's own list" sentence (D-160 clause 3; the second review's M8):**
  `LanguageTests.swift:466`, both languages. GREEN. L1 (the count dropped) and L2 (the Turkish
  disclaimer dropped) are killed. M8 is resolved.
- **The effort notice (D-112, note 4):** `AnswerPlanTests.swift:143`, `:155`, `:164` and `:173`.
  GREEN. AP12 to AP14 (the reviewer's N3 to N5), AP16, AP17 and L3 (N9) are killed.
- **Tied models share a place (note 3):** `CombineTests.swift:30`, and the property test's
  independent oracle (`ios/EngineTests/CombinePropertyTests.swift:60-68`, run by `:79`). GREEN.
  - CP1 (`index + 1`, N1) and CP2 (dense places, N2) are killed.
  - CP3 (a tie tested against the first model only) is killed by the property test alone.
- **D-167 clause 3 exactly (#54):** `CombineTests.swift:41` and `AnswerPlanTests.swift:116`. GREEN.
- **Two boards of one benchmark each count (D-168 clause 5, #53):** no citing test. CB53 survives:
  **M1**.
- **The detail's per-board effort line, each model's place on each board, and the empty-list
  sentence:** no test. L6, L7 and L8 survive: **M2**.

**`primary_board` (D-168 note 1, the plan's K.8 addition)**
- **The value is the surface's board id:** `test_refinements.py:121`. GREEN. PB1 (the reviewer's N13)
  is killed.
- **The served key set:** `tests/unit/test_uncertainty_contract.py:317`. GREEN.
- **Every key the phone decodes is served:** `tests/unit/test_ios_payload_contract.py:135`. GREEN.
  - PB2 (the field dropped from the route) is killed by this test and by `:121`.
  - PB3 (the phone decodes another key) is killed by `:135`.
  - Pointing the key at another served field instead cannot compile. `Category`'s `CodingKeys` name
    every served key (`ios/ModelRanking/Engine/Models.swift:67-80`), and Swift refuses a duplicate
    raw value.

**P4: measured and recorded**
- **The record:** `docs/research/m17-w5-refinement-probe-2026-09-28.md`, with the harness
  `scripts/router_probe/RefinementProbe.swift` and both question sets committed.
- **A spot check.** I did not run the model. From the raw run files in the scratchpad, scored
  against `refinement_heldout_questions.json`:
  - the shipped runs (`md-run1-v2.json`, `md-run2-v2.json`) give surfaces 26 and 28 and languages
    37 and 37;
  - the runs before the decline rewording (`ld-v2-run1.json`, `ld-v2-run2.json`) give surfaces 28
    and 28.
  - Both rows match §4. The second Code-Reviewer recomputed the rest.
- **Rules that only the model can show:** clause 3 (the task's language, not the question's) and
  note 5 (medical and legal questions are answered) are prompt text. Their only evidence is the
  record: §4's 15 of 17 Turkish questions, and the decline wording measured as changing nothing. That
  is what the plan's risk section accepts. MR2 and MR3 show that no test holds them.
- **The security pass:** not in this range; the plan runs it before merge (`:12-13`).

## Red→green on reported symptoms
- **The first review's B2** (a coding request takes no refinement):
  `test_no_refinement_refines_a_surface_a_coding_request_answers_on` FAILS at `17ae833` (the red
  commit) on a `git archive` copy, and passes at `4039fd4`.
- **The owner's ruling that a refinement is a language or a domain:**
  `test_the_table_holds_languages_and_domains_only` FAILS at `3a7dcd5`.
- **The first review's B1, M1 and M4, and the chip lost on the simulator** (`17ae833`, `d10b3bd`):
  - Red by compilation at both commits. At `d10b3bd`: "`AnswerPlan` has no member `restorable`"
    (`AnswerPlanTests.swift:82`, `:89`). At `17ae833`: `boardTitle` and `chipAction` are not
    found (`LanguageTests.swift:452`, `:460`).
  - Each behaviour is now assertion-held: AP11, AP12 to AP18, CP1, CP2, AP22 and L3 are killed by an
    XCTest assertion, never by a compile error.
- **M8** (`4039fd4`) adds a test for a sentence that already existed. It needs no red; L1 and L2 show
  that it bites.
- **Weakened or deleted tests** (`git diff c02fe0d..4039fd4 -- tests ios/EngineTests scripts`, removed
  lines only):
  - The old pin `anyOf:\s*known` is replaced by a stricter pin on code with its comments removed. The
    old pin matched only a doc comment; the second reviewer confirmed this.
  - The `RoutingOutcome` field set gains `refinements`, with a pin on its type.
  - No test was deleted or skipped. The manifest gains 42 names and loses none.

## Suite result
- **`make check-fast` at `4039fd4`, clean tree, `PYTHONDONTWRITEBYTECODE=1`: PASS in 74.2 s.**
  - lint, typecheck and records pass.
  - test: **1514 passed, 23 skipped**. The 23 are the network contract tests and the Epoch bundle
    tests. coverage-floor passes: 41 modules, floor 60 %, 1 exempt.
  - swift-test: **348 tests, exactly the manifest's**.
  - client-decls passes: 15 files in 4 configurations.
- **Python coverage on touched code** (permission-matrix §11).
  - Measured with `pytest tests/unit -n auto --cov=src/app --cov-branch`, lines and branches
    combined. The base is a `git archive` of `c02fe0d` and the head one of `4039fd4`, both in
    scratch with the same `advisor.db` (sha256 005855fa…), so no artifact test skips at either end.
  - The one touched module, `src/app/adapter/main.py`: **97.06 % → 97.06 %**. There are 402
    statements with 12 missing, and 108 branches with 3 missing, at both ends. The new line sits
    inside a dict literal.
  - **No module dropped** in a per-file comparison across `src/app`. Total: 91.48 % → 91.48 %.
- **Swift line coverage on the touched Engine files** (`swift test --enable-code-coverage` in a
  scratch copy of `4039fd4`; informational, since §11 reads Python modules):
  - `Refinements.swift`: 100 %.
  - `AnswerPlan.swift`: 98.6 %. The one unexecuted region is the `?? board.benchmark` fallback at
    `:51`.
  - `Combine.swift`: 91.9 %. The unexecuted regions are default-value autoclosures at `:57`, `:81`,
    `:87` and `:89`.
  - `Router.swift`: 98.0 %.
  - In the new section of `Language.swift`, eight functions and one `case` never run. Three of the
    functions carry facts:
    `combinedEmpty` (`:556`), `boardEfforts` (`:584`) and `placeOn` (`:623`); see **M2**. The others
    are labels: `combinedTitle`, `alsoCounting`, `removedRefinements`, `seeTheBoards`,
    `boardsBehind`, and the `.unknown` date text.
- **The suite asks the on-device model on this Mac.** The model tier's lines (`Router.swift:418-471`)
  ran six times per run. The one unexecuted line is `:461`, the `return nil` after a failed
  `respond`.
  - They are reached by the pre-existing M15-W3 test
    `RouterBoundaryTests.swift:105` (`testTheDefaultRouterNeverYieldsAnIdOutsideTheKnownSet`), which
    routes six questions through the real `TieredRouter()`.
  - So the shipped schema builds on this Mac and the model answers against it.
  - It also means that every `swift test` run in this review asked the model those six questions.
    That was 70 runs: the gate, the coverage run and 68 mutant runs. This seat wrote no probe and made
    no call of its own.
- **Clean-up.**
  - `git status` is clean apart from this file.
  - All 538 tracked files under `src tests ios scripts docs` match the pre-run sha256 baseline
    (`tester-w5/sha-baseline.txt`, `sha-after.txt`).
  - One pre-existing `.pyc` was rewritten despite `PYTHONDONTWRITEBYTECODE=1`
    (`src/app/adapter/__pycache__/main.cpython-314.pyc`). I deleted it. No new `__pycache__` was
    left.

## Fault injection (HIGH: mandatory)
- **Harness.** `tester-w5/mut.py`. For each mutant it:
  1. makes exact byte edits in place, each of which must match exactly once;
  2. runs the command;
  3. writes the pre-edit bytes back in place;
  4. asserts that the sha256 equals the pre-edit hash.

  All 87 runs restored with matching hashes (`mutants.log`, `mutants-full.log`,
  `mutants-extra.log`):
  - `Router.swift` d107473c…
  - `Refinements.swift` a5fc7a34…
  - `AnswerPlan.swift` 06f5af5a…
  - `Combine.swift` 3e63eca5…
  - `Language.swift` 276b27b6…
  - `Models.swift` 591c2a24…
  - `main.py` 04f1b87d…
- **Commands.**
  - A Swift mutant ran the Engine test classes the wave touches, then the Python tests that read the
    Swift sources.
  - A pin mutant ran them the other way round.
  - A Python mutant ran the whole unit suite.
  - **Every survivor was then run against the whole of `swift test`, the whole unit suite
    (`-n auto`) and `client-decls`.**
  - Every Swift kill is an XCTest assertion, never a compile error.
- **Killed: 59 of 73.**

| file | mutants | killed | survived |
|---|---:|---:|---|
| `Router.swift` (the boundary, the schema, the tiers) | 21 | 16 | SP4, SP6 (#60's class); MR1, MR2, MR3 (the model call) |
| `Refinements.swift` (`boards`, `allowed`, the table) | 14 | 13 | RB7 (equivalent) |
| `AnswerPlan.swift` | 23 | 19 | AP6, AP7, AP15, AP19 (equivalent) |
| `Combine.swift` (the place rule, clause 5) | 4 | 3 | CB53 (**M1**) |
| `Language.swift` | 8 | 5 | L6, L7, L8 (**M2**) |
| `main.py`, `Models.swift` (`primary_board`) | 3 | 3 | none |

- **The earlier reviewers' mutants, re-run, all killed:** N1 (CP1), N2 (CP2), N3 to N5 (AP12 to AP14),
  N7 (AP18), N8 (AP22), N9 (L3), N10 (RT1), N11 (SP3) and N13 (PB1).
- **Survived, equivalent in practice (5), not findings:**
  - **RB7** (`continue` → `break` in `Refinements.boards`). `ModelOutputBoundary.refinements` gives
    at most one refinement per kind (`Router.swift:531-536`), and no refinement's board is a primary
    board, so the loop never has a second candidate to skip to.
  - **AP6** (`removed` not intersected with the offered refinements). The view looks up only the
    refinements it shows (`ContentView.swift`, `refinementChips`), so an extra entry is never read.
  - **AP7** (`kept.isEmpty` dropped from the restore branch). This is reachable only if a kept
    refinement adds no board. That needs a refinement the surface disallows, which the boundary never
    emits, or one whose board is the primary, which no table entry has.
  - **AP15** (empty efforts not filtered). `scores.effort` is `NOT NULL DEFAULT 'unspecified'`
    (`src/app/workflows/schema.py:61`), and the artifact serves no empty effort among 7,135
    standings.
    - Its first full run failed one Python test, `test_fetch_bounds.py:239`. That test cannot read
      `AnswerPlan.swift`, and the Python leg passed on a re-run: **K1**.
  - **AP19** (the read date keeps its full timestamp). The route already cuts `observed_at` to ten
    characters (`src/app/workflows/standings.py:122`).
- **Survived, outside the suite by the plan's design (3), not findings.** The plan's risk section:
  "Only the session call itself is untested, as today."
  - **MR1:** every kind is read from the `domain` property (`Router.swift:466`). The boundary still
    drops a value of the wrong kind (MB2 is killed), so nothing undeclared reaches a board. Only which
    refinements are chosen would change.
  - **MR2:** medical and legal questions are listed among the declines again (`:444`, note 5). The
    record measured the rewording as changing nothing.
  - **MR3:** the task-language sentence and field description are removed (`:456`, clause 3).
    Measured only by the probe.
- **Survived, #60's class (2), not raised again.** The schema pins at `test_router_hints.py:132` and
  `:139` are regular expressions that stop at the closing parenthesis of the call, so a suffix passes
  them.
  - **SP4:** `refinementChoices(for: kind).filter { $0 != ModelOutputBoundary.noRefinement }` takes
    the way out away from both refinement fields. The on-device model would have to name a language
    and a domain for every question. The boundary would still hold each to a declared entry the
    surface allows.
  - **SP6:** `.filter { $0 != ModelOutputBoundary.declineSentinel }` does the same to the surface
    field.
    - The on-device model could no longer decline.
    - The pin before this wave could not see the suffix either: it matched only a comment.
  - This is evidence for #60. The cheap guard is to anchor both patterns on the `)))` that closes the
    call.
- **Survived, findings:** CB53 (**M1**), and L6, L7 and L8 (**M2**).

**Kill rate, non-equivalent mutants:** 59 of 68, **87 %**. Leaving out the three model-call mutants
the plan puts outside the suite: 59 of 65, **91 %**.

## Mocks / contract tests
- **The engine's `/v1/categories`, seen by the phone:**
  - The contract is `tests/unit/test_ios_payload_contract.py:135`. It derives the phone's keys from
    `Models.swift` and drives the real route through `TestClient`.
  - It now covers `primary_board` (PB2 and PB3 are killed).
  - OK.
- **The engine's `/v1/boards`:**
  - The canonical stub is W4's `StubProtocol` (`ios/EngineTests/EngineClientTests.swift`). The wave
    adds no parallel stub.
  - `answerPlan` takes `Standings` values directly, which are data, not a double.
  - OK.
- **The on-device model:**
  - It has no double. The boundary is a pure function (`ModelOutputBoundary.outcome`), tested on
    every machine.
  - The session call runs only in `RouterBoundaryTests.swift:105`, and only where the model is
    available. That test asserts membership only; see **R1**.
  - No new external integration.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `ios/ModelRanking/Engine/Combine.swift:47-56`; `docs/decisions.md:3178-3179`. **D-168 clause
  5 (#53, owner ruling: two boards of one benchmark each count when both are chosen) has no citing
  test, and a mutant that removes it keeps every gate green.**
  1. **The mutant, CB53.** After the lookup, `combine` keeps only the first board of each benchmark
     (`boardsAll.filter { named.insert($0.benchmark).inserted }`). It passes the whole of
     `swift test`, the whole unit suite and `client-decls`. Every Swift fixture names its boards
     `"B \(id)"`, so no test ever combines two boards of one benchmark. The only mention of #53 in a
     test is the docstring at `test_refinements.py:123`, which is about ids.
  2. **Why MINOR.** The clause is latent: it cannot happen with this table. On the artifact, the
     seven primary boards a refinement can join and the sixteen refinement boards have 23 distinct
     benchmark names: "Arena text", "Arena document", "GPQA Diamond", …, and "Arena text (french)"
     and the like. So no question can select two boards of one benchmark, and CB53 changes no
     reachable answer today.
  3. **Why it matters anyway.** The owner ruled #53 in this wave, and the next table change (a
     second publisher of one benchmark) would meet no test. The clause also says the detail "names
     both". But `boardTitle` (`AnswerPlan.swift:48-53`) gives two primary-style boards of one
     benchmark the same name, which is untested and unreachable too.
  4. **The fix.** Add one `CombineTests` case with two boards of different ids and the same
     `benchmark`: both appear in `list.boards`, and each entry carries two positions. Cite D-168
     clause 5. It kills CB53.
- **M2** `ios/ModelRanking/Engine/Language.swift:556-560`, `:584-588`, `:623-625`. **Three sentences in
  the Engine layer carry facts to the detail screen or to the empty list, and none has a test.** Each
  mutant passes the whole of `swift test`, the whole unit suite and `client-decls`:
  1. **L6.** `boardEfforts` drops the efforts it names, so the detail's per-board line reads only
     "Effort levels of the models in this list". This is the per-board half of D-168 note 4
     (`docs/decisions.md:3217-3218`).
  2. **L7.** `placeOn` drops the position, so each board in the detail reads "on Arena text" with no
     number. This is the plan's fact-to-field row "a model's place on each board, in the detail"
     (`docs/plans/m17-wave-5-plan.md:70`).
  3. **L8.** `combinedEmpty` becomes empty, so a list no model survives says nothing where it
     should say that no model is ranked on every board. This is D-167 clause 3 exactly (#54);
     `AnswerPlanTests.swift:117` says "an empty list is said, not filled".

  **Why MINOR, not BLOCKING.** The Engine layer holds the data each sentence prints: the per-board
  efforts (`AnswerPlanTests.swift:143`), the positions (`CombineTests.swift:125`) and the count 0
  (`:116`). The disclosures the ADRs require also survive each mutant on the same screen:
  1. the main list's effort note names every effort (L3 is killed);
  2. the "product's own list" sentence gives the count, 0 included (L1 is killed).

  These are Engine functions that `swift test` compiles, not view branches, so they are not #69's
  evidence. **The fix:** one test in the shape of `LanguageTests.swift:466`, asserting each
  sentence in both languages and citing D-112, D-167 clause 3 and the plan's map. It kills L6 to L8.

## K.9 candidates spotted outside this wave's scope
- **K1** `tests/unit/test_fetch_bounds.py:239`
  (`test_without_a_deadline_of_its_own_a_fetch_takes_four_timeouts_at_most`). **It failed once in the
  parallel unit suite and passed on the re-run, with nothing it reads changed.**
  1. **The failure** (`tester-w5/outputs/AP15-full.pyunit.txt`): it expected a "deadline" error
     and got "probe fetch failed: timed out". That is the per-read timeout winning the race against
     the overall deadline. It came right after a full `swift test` build.
  2. **How it differs from #71.** #71 is `test_fetch_bounds`'s `header_drip` test failing with
     EBADF. This is another test in the same file, with another symptom, and plausibly the same
     cause: timing under a loaded parallel suite.
  3. **The disposition.** Add it to #71 as a second instance, or file it on its own.

## Risks queued to next M
- **R1** `ios/ModelRanking/Engine/Router.swift:434-436`; `ios/EngineTests/RouterBoundaryTests.swift:105-116`.
  **The wave makes schema construction able to fail, and a failure is silent.**
  1. **What changed.** Before the wave, the model tier used `GenerationSchema(type:description:anyOf:)`,
     which does not throw. It now builds a `DynamicGenerationSchema` root with
     `guard let schema = try? GenerationSchema(root:dependencies:) else { return nil }`.
  2. **What a failure would do.** If that construction ever throws, every question on every device
     falls through to the wording tier (`:631-639`). The model tier and every refinement would
     vanish. It could throw on a duplicate property, for example a future `RefinementKind` whose raw
     value is `surface`, or on an empty set of choices.
  3. **Why no test sees it.** The only test that reaches the real tier asserts membership
     (`served.contains(outcome.categoryID)`), which the wording tier also satisfies.
  4. **It is latent today.** No input makes the construction throw, and the coverage run shows the
     model answering all six of that test's questions through the new schema.
  5. **The cheap guard.** Build the schema in a static function and assert that it builds on macOS
     26. That needs no model call. Alternatively, where `ModelRouter.state == .available`, assert that
     the tier is `.model`.

## Tests added/extended this review
- None in the repository. This seat may modify only this file.
- Scratch, not committed. All paths are under
  `/private/tmp/claude-501/-Users-umutcanapaydin/a67ca254-76b9-4a88-94bb-cec8e0afaa95/scratchpad/tester-w5/`:
  - the mutants: `mut.py`, `make_specs.py`, `specs*.json`, `mutants.log`, `mutants-full.log`,
    `mutants-extra.log` and `outputs/`;
  - coverage: `cov-base.json` and `cov-head.json` (from `tree-base/` and `tree-head/`), and
    `swift-cov.txt`;
  - the red commits: `red-17ae833/`, `red-d10b3bd/`, `red-3a7dcd5/`, `red-*.swift.txt`;
  - `check-fast.log`, `sha-baseline.txt`, `sha-after.txt`, `pycache-before.txt` and
    `pycache-after.txt`.
