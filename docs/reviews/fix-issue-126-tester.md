---
record_type: review
id: fix-issue-126-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 126 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..95419f5 (`8015a8c` red test, `95419f5` fix).
**Risk tier:** LOW (test doubles and PRD pointers; no production code changed).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `0198eb3`. The
acceptance criterion is the issue body: "one shared test file of tier stubs (a model tier, an
answering wording tier, a silent one, a hanging one), used by every test that builds a
`TieredRouter`". Red: the tree of `8015a8c` extracted with `git archive` into the scratchpad and its
gate run with this worktree's venv. Gate: `make check-fast` at the head. Faults: one exact unique
replacement per mutant, the original bytes written back and the sha256 compared; a stub mutant ran
the whole Swift suite (`swift test --parallel` in `ios/`), a gate mutant
`tests/unit/test_ios_client_contract.py`. PRD: every pointer into the four changed test files (41:
28 re-pointed, 13 left) resolved at `0198eb3` and at `95419f5` to the declaration on its line, and
the two compared (a scratchpad script; `git show` for the base).

## Verdict
MINOR

The shared file holds the four tiers the issue names and two more, every `TieredRouter` the tests
build uses them (or the real `SimilarityRouter`, the app's `ScriptedModelRouter`, or the defaults),
and each stub's behaviour is held by a test that fails when it changes. Two things stay open: one PRD
pointer the removed lines moved was not re-pointed and now lands on a doc comment (R1), and the gate
that refuses a stub elsewhere misses three declaration shapes (T1). Both are shown by tests written
below.

## Acceptance-criterion coverage
- One shared file of tier stubs, and no `QuestionRouter` stub in another test file:
  `tests/unit/test_ios_client_contract.py:1405` (`test_the_swift_tests_share_one_set_of_tier_stubs`)
  (P1, P2, P3 killed). A generic stub, one conforming in an extension, or one conforming on the next
  line: only T1's test (below).
- Every test that builds a `TieredRouter` uses them: `grep -n "TieredRouter(" ios/EngineTests` lists
  23 lines, each building it with a shared stub, `SimilarityRouter()`, `ScriptedModelRouter`, `nil` or
  the defaults.
- Each stub does what its name says, held by the suite:
  1. `HangingTier` answering at once fails `SlowTierTests.testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier` (B1, also alone);
  2. `SilentTier` answering fails three tests (B2);
  3. `FixedTier`, `SpyTier`, `DecliningModelTier`, `AnsweringWordingTier` each fail at least one (B3 to B6).
- Red to green: on `8015a8c` the gate fails on its first assertion,
  `TierStubs.swift declares []; the shared tiers are missing` (R2); it passes at `95419f5`.
- PRD: all 28 re-pointed pointers name, at `95419f5`, the test or class of tests they named at
  `0198eb3`, among them `REQ-RTR-003` `RouterBoundaryTests.swift:53 -> :30`
  (`testWithNoTierAtAllTheReaderStillGetsASurface`), `REQ-RTR-003` `FrontDoorTests.swift:539 -> :514`
  (`testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier`), `REQ-IOS-002`
  `RouterBoundaryTests.swift:185 -> :162` (`testAQuestionAboveTheFloorIsNotFlaggedUnmeasured`),
  `REQ-GAP-001` `FrontDoorTests.swift:719 -> :694` (`GapRegisterHardeningTests`) and `REQ-SUR-002`
  `FrontDoorTests.swift:327 -> :302` (`testTheTwoNewSurfacesAreReachableByAsking`). Of the 13 left
  as they were, 12 still land where they did; one does not (R1).

## Suite result
- `make check-fast` at `95419f5`: PASS in 79.3s, six legs; test leg 1797 passed, 25 skipped; swift
  leg 462 tests, exactly the manifest. `SlowTierTests` (#149) passed in every run but B1, where its
  failure was the mutant's: it fails alone under B1 and passes alone at the head.

## Mutants

| ID | Fault | Run | Result |
|---|---|---|---|
| P1 | `final class PlantedTier: QuestionRouter, @unchecked Sendable` in `ReadingTests.swift` | gate | KILLED |
| P2 | `actor PlantedActorTier: QuestionRouter` in `ReadingTests.swift` | gate | KILLED |
| P3 | a nested `struct Silent: QuestionRouter` inside a test method (`RefinementBoundaryTests.swift`) | gate | KILLED |
| P4 | `struct PlantedTier<Answer>: QuestionRouter` | gate | SURVIVED; KILLED by T1's test |
| P5 | `struct PlantedTier {}` with `extension PlantedTier: QuestionRouter` | gate | SURVIVED; KILLED by T1's test |
| P6 | `struct PlantedTier:` with `QuestionRouter {` on the next line | gate | SURVIVED; KILLED by T1's test |
| B1 | `HangingTier` answers at once (its sleep removed) | Swift suite | KILLED (`SlowTierTests`) |
| B2 | `SilentTier` answers `coding` | Swift suite | KILLED (three tests) |
| B3 | `FixedTier` answers `nil` whatever it was given | Swift suite | KILLED (both `SlowTierTests`) |
| B4 | `SpyTier` records nothing | Swift suite | KILLED (two `RouterBoundaryTests`) |
| B5 | `DecliningModelTier` answers `nil` instead of the decline | Swift suite | KILLED (`testTheModelTiersDeclineIsCarriedThroughToTheNotice`) |
| B6 | `AnsweringWordingTier` answers as the model tier | Swift suite | KILLED (`testTheWordingTiersAnswerIsReadAndKeepsItsTier`) |

As committed: 9 of 12 killed; with T1's test, 12 of 12.

## Findings
- **R1** One PRD pointer the fix moved was left behind. `REQ-GAP-002` reads
  "FrontDoorTests.swift:652, :663 (`clear()` exercised at :693)". At `0198eb3` line 693 was
  `register.clear()` inside `testTheRegisterIsBounded`; the 25 lines removed above it put that call
  on line 668, and line 693 is now the doc comment of `GapRegisterHardeningTests`. The citation gate
  asks of an `at :N` pointer only that the line exists, so every gate passed, and the commit's "all
  430 pointers were checked" missed it. The author re-points it to `:668`. Written this review and
  appended to `tests/unit/test_prd_citations.py`: RED at `95419f5`
  ("FrontDoorTests.swift:693 does not hold" the call), GREEN with the pointer at `:668`;
  `ruff check` clean. Removed again; the author adds it with the re-pointing. Full text:

```python
def test_a_place_the_prd_points_into_holds_the_code_it_names() -> None:
    """#126 (the fix Tester's R1): a pointer the PRD places inside a test (`` `clear()` exercised at
    :693 ``) need only exist for the gate above, so when #126 removed lines above it, it moved onto a
    doc comment and every gate passed. The code it names must stand on the line it names."""
    by_name = tracked()
    places = 0
    for row in PRD.read_text(encoding="utf-8").splitlines():
        for match in re.finditer(r"`([^`]+)`[^`(]{0,40}?\bat\s+:(\d+)", row):
            named = list(NAMED_FILE.finditer(row[: match.start()]))
            assert named, f"no file named before {match.group(0)!r}"
            (path,) = by_name[named[-1].group(1)]
            line = (ROOT / path).read_text(encoding="utf-8").splitlines()[int(match.group(2)) - 1]
            places += 1
            assert match.group(1) in line, (
                f"{named[-1].group(1)}:{match.group(2)} does not hold `{match.group(1)}`: {line.strip()!r}"
            )
    assert places, "no pointer into a test's body was read; the pattern matches nothing"
```

- **T1** The gate reads a stub only as `struct|class|enum|actor Name: ... QuestionRouter` on one
  line of a file directly in `EngineTests`. A generic stub (P4), one that conforms in an extension
  (P5) and one whose conformance runs onto the next line (P6) pass it, and so would a stub in a
  subfolder of `EngineTests` (`glob`, not `rglob`; read, not run, since it needs a new file). Written
  this review and appended to `tests/unit/test_ios_client_contract.py`: RED on P1 to P6, GREEN at
  `95419f5`; `ruff check` clean. Removed again; the author adds it or folds it into the gate. Full
  text:

```python
def test_no_test_file_declares_a_tier_stub_in_any_shape() -> None:
    """#126 (the fix Tester's T1): the stub gate above reads a declaration only as `struct Name:
    ... QuestionRouter` on one line, so a generic stub (`struct Name<T>: QuestionRouter`), one that
    conforms in an extension, or one whose conformance runs onto the next line passed it. Here every
    test source, in any folder, is read with its line comments removed, and a conformance to
    `QuestionRouter` outside `TierStubs.swift` fails."""
    tests = CLIENT.parent / "EngineTests"
    home = tests / "TierStubs.swift"
    conforms = re.compile(r"\b(?:struct|class|enum|actor|extension)\s+[\w.]+\s*(?:<[^>{]*>)?"
                          r"\s*:[^{]*\bQuestionRouter\b")
    assert conforms.search(home.read_text(encoding="utf-8")), "the pattern finds no shared stub"
    sources = sorted(path for path in tests.rglob("*.swift") if path != home)
    assert len(sources) >= 10, f"read {len(sources)} test sources; was EngineTests read?"
    found = []
    for path in sources:
        code = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
        found += [f"{path.name}: {' '.join(m.group(0).split())[:60]}" for m in conforms.finditer(code)]
    assert not found, f"tier stubs declared outside TierStubs.swift: {found}"
```

- **R2** The red commit's gate failed on its first assertion, the missing shared file, so the
  assertion the fix rests on, no stub outside `TierStubs.swift`, never ran red. Read at `0198eb3`
  with the gate's own pattern it lists nine private stubs (`DecliningModel`, `Silent`, `Fixed`,
  `Hanging` in `FrontDoorTests.swift`; `NoSimilarity`, `Answering` in `ReadingTests.swift`; `Silent`
  in `RefinementBoundaryTests.swift`; `StubRouter`, `SpyRouter` in `RouterBoundaryTests.swift`), so
  it would have failed. No action asked.

## Clean-up evidence
- Every mutant and test run: original bytes written back and sha256 compared (`TierStubs.swift`
  49d1b6d3b1ae..., `ReadingTests.swift` f24c5a820b27..., `RefinementBoundaryTests.swift`
  d14f3f5c9849..., `test_ios_client_contract.py` fed39858af33..., `test_prd_citations.py`
  d2b4e63b341f..., `docs/prd.md` c5904a4a178d...). No mismatch.
- `git hash-object` equals `HEAD:<path>` for those six files and for `FrontDoorTests.swift` and
  `RouterBoundaryTests.swift`. The red tree was extracted into the scratchpad. No checkout,
  restore, stash, reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| R1 | fixed: REQ-GAP-002's `clear()` pointer moves from `:693` to `:668`, where it stands; the seat's `test_a_place_the_prd_points_into_holds_the_code_it_names` is committed as written. The author's by-name check compared declarations only, so it could not see a pointer into a test's body |
| T1 | fixed: the seat's `test_no_test_file_declares_a_tier_stub_in_any_shape`, committed as written beside the first gate |
| R2 | accepted: the issue is a refactor, so the red is the gate that found no shared file and eight private stubs |
