---
record_type: review
id: fix-issue-127-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 127 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..a32ebdf (`685ac32` red test, `a32ebdf` the walk).
**Risk tier:** LOW (tests only; no production code changed).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `0198eb3`. The
acceptance criterion is the issue body: "one test that walks every `UIText` sentence in both
languages and fails on one that is empty or the same in Turkish as in English (unless it is a
name)". Red: the tree of `685ac32` extracted with `git archive` into the scratchpad and its gate run
with this worktree's venv. Gate: `make check-fast` at the head. Faults: one exact unique replacement
per mutant in `Language.swift`, `Refinements.swift`, the Swift table or the Python gate, the original
bytes written back and the sha256 compared. A Swift mutant ran the whole suite,
`swift test --parallel` in `ios/` (464 tests each run); a gate mutant ran
`tests/unit/test_ios_client_contract.py`. Coverage: one `swift test --enable-code-coverage` run at
the head, read from `.build/debug/codecov/ModelRankingEngine.json`. `SlowTierTests` (#149) did not
fail in any run.

## Verdict
MINOR

The walk does what it says for every function, and its gate is derived from `Language.swift` and
fails closed. Two holes stay green. The table gives each function one input, so five faults that put
English on the Turkish screen survive the whole suite: two branches never walked (`boardDate` with no
date, `seeAll` with no budget) and three English frames around a translated value (T1); the
`.unknown` sentence still runs in no test at all. And the gate reads one file and one declaration
shape (T2). Both missing tests are written below, red on their mutants, green at the head.

## Acceptance-criterion coverage
- Every `UIText` function composed in both languages, failing on an empty or blank sentence or a
  Turkish one equal to its English: `ios/EngineTests/UITextLanguageTests.swift:80`
  (`testEveryScreenSentenceIsSaidInBothLanguages`) (S1, S2, S3, S9 killed). Each function's other
  branches, and a frame around a translated value: only T1's test (below).
- A sentence added without a row, or a row naming no sentence, fails:
  `tests/unit/test_ios_client_contract.py:1405`
  (`test_every_screen_sentence_has_a_row_in_the_language_test`) (G1, G2, G3, G4a, G4b, G7 killed).
  A sentence in another file, or a generic one: only T2's test (below).
- "Unless it is a name": the walk has no exception, and none is needed: all 58 functions differ at
  the head.
- Red to green: on `685ac32` the gate fails listing all 58 functions (the walk does not exist), and
  passes at `a32ebdf` (R1).
- What the issue counted: at `93040ac` 86 of `Language.swift`'s lines ran in no test. At `a32ebdf`
  the whole suite executes 498 of its 507 coverable lines. Of `UIText`'s, four regions still run in
  no test: `boardDate`'s `.unknown` branch (lines 649-650), the unreadable-date fallback `?? served`
  (642, 645) and `refinementName`'s unknown fallback (587). T1's test walks each of them.

## Suite result
- `make check-fast` at `a32ebdf`: PASS in 74.2s, six legs; test leg 1797 passed, 25 skipped; swift
  leg 464 tests, exactly the manifest.

## Mutants

| ID | Fault | Run | Result |
|---|---|---|---|
| S1 | `askBackNo`: Turkish "No" | Swift suite | KILLED (the walk; `ReadingFaultTests`) |
| S2 | `loading`: Turkish empty | Swift suite | KILLED (the walk) |
| S3 | `heroTitle`: English blank | Swift suite | KILLED (the walk) |
| S4 | `boardDate(.measured)`: English frame around the Turkish date | Swift suite | SURVIVED; KILLED by T1's test |
| S5 | `boardDate(.readOn)`: English frame around the Turkish date | Swift suite | SURVIVED; KILLED by T1's test |
| S6 | `boardDate(.unknown)`: Turkish "No date" | Swift suite | SURVIVED; KILLED by T1's test |
| S7 | `combinedEffortNote`: English frame around the Turkish effort names | Swift suite | SURVIVED; KILLED by T1's test |
| S8 | `seeAll` with no budget: Turkish "See all 12" | Swift suite | SURVIVED; KILLED by T1's test |
| S9 | `placeOn`: Turkish is the English | Swift suite | KILLED (the walk; `CombinedListLanguageTests`) |
| G1 | a sentence added to the extension with no row | gate | KILLED |
| G2 | a row naming no function | gate | KILLED |
| G3 | the gate reads only `enum UIText`, not its extension | gate | KILLED (the floor of 40) |
| G4a | `Language.swift` read as empty | gate | KILLED (`read 0 UIText functions`) |
| G4b | read as empty, and the floor removed | gate | KILLED (every row then names no function) |
| G5 | a sentence in an `extension UIText` in `Refinements.swift`, no row | gate | SURVIVED; KILLED by T2's test |
| G6 | a generic sentence, `static func addedLater<T: ...>(`, no row | gate | SURVIVED; KILLED by T2's test |
| G7 | `public enum UIText: Sendable {`: the opening line changes | gate | KILLED (fails closed: 23 read) |

As committed: 11 of 17 killed; with T1's and T2's tests, 17 of 17.

## Findings
- **T1** The walk gives each function one input, so it misses the sentences a function says on
  its other branches, and it cannot see an English frame around a value the language changes. With
  a known date, effort or refinement, the Turkish sentence differs from the English even when only
  the value was translated (S4, S5, S7); and `boardDate(.unknown)` and `seeAll` with no budget are
  never composed (S6, S8). All five put English on the Turkish screen, the issue's own worry, and
  the whole suite stays green. Written this review in `ios/EngineTests/UITextLanguageTests.swift`,
  with its line in `test-manifest.txt`: RED on S4 to S8, GREEN at `a32ebdf` with
  `make swift-test-parallel` (465 tests, exactly the manifest) and the gate. Removed again so the
  worktree holds only this record; the author adds it to the branch. Full text, inside
  `UITextLanguageTests`:

```swift
    /// The fix Tester's T1 (#127). The table gives each function one input, so a sentence's other
    /// branches went unwalked, and a sentence that carries a value the language changes (a date, an
    /// effort, a refinement's name) differed from its English even with an English frame around the
    /// Turkish value. Here every other branch is walked, each with a value both languages print
    /// alike: a date this build cannot read, an effort and a refinement it does not know.
    func testEveryBranchAndFrameIsSaidInBothLanguages() {
        let unnamed = Refinement(value: "zz-unnamed", kind: .language, board: "zz", surfaces: [], reason: "")
        let frames: [(String, (Language) -> String?)] = [
            ("boardDate", { UIText.boardDate(.measured("zz-day"), $0) }),
            ("boardDate", { UIText.boardDate(.readOn("zz-day"), $0) }),
            ("boardDate", { UIText.boardDate(.unknown, $0) }),
            ("combinedEffortNote", { UIText.combinedEffortNote(efforts: ["zz-effort"], $0) }),
            ("boardEfforts", { UIText.boardEfforts(["zz-effort"], $0) }),
            ("chipAction", { UIText.chipAction(unnamed, removed: false, $0) }),
            ("chipAction", { UIText.chipAction(unnamed, removed: true, $0) }),
            ("seeAll", { UIText.seeAll(12, eligible: nil, $0) }),
            ("seeAll", { UIText.seeAll(12, eligible: 12, $0) }),
            ("pickLabel", { UIText.pickLabel("best_value", $0) }),
            ("pickLabel", { UIText.pickLabel("budget_pick", $0) }),
        ]
        for (index, (name, compose)) in frames.enumerated() {
            let english = compose(.english)
            let turkish = compose(.turkish)
            XCTAssertFalse((turkish ?? "").trimmingCharacters(in: .whitespaces).isEmpty, "\(name) #\(index): no Turkish")
            XCTAssertNotEqual(turkish, english, "\(name) #\(index): the Turkish reader is given the English")
        }
    }
```

  The manifest line, before `testEveryScreenSentenceIsSaidInBothLanguages`:
  `ModelRankingEngineTests.UITextLanguageTests/testEveryBranchAndFrameIsSaidInBothLanguages`.
- **T2** The gate reads the tree it names and no more: `Language.swift` alone, and a function only
  as `static func name(`. A sentence declared in an `extension UIText` in another app file (G5), or
  a generic one (G6), passes it with no row (AGENTS.md section 3.5: does it read the tree you think
  it reads). Written this review, appended to `tests/unit/test_ios_client_contract.py`: RED on G5
  and G6, GREEN at `a32ebdf`, `ruff check` clean. Removed again; the author adds it to the branch or
  folds its reading into the gate. Full text:

```python
def test_every_uitext_sentence_anywhere_in_the_app_has_a_row() -> None:
    """#127 (the fix Tester's T2): the sentence gate above reads `Language.swift` alone, and a
    function only as `static func name(`. A sentence declared in an `extension UIText` in another
    app file, or a generic one (`static func name<T>(`), passed it with no row. Here every `UIText`
    body in the app's sources is read, and every function declared in it."""
    declared: dict[str, str] = {}
    for path in sorted(CLIENT.rglob("*.swift")):
        if ".build" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for opening in re.finditer(r"^(?:\w+ )*(?:enum|extension) UIText\b[^{\n]*\{$", text, re.M):
            body = text[opening.end():]
            closing = re.search(r"^\}$", body, re.M)
            assert closing, f"{path.name}: a UIText body never closes"
            for name in re.findall(r"\bfunc\s+(\w+)\s*[<(]", body[: closing.end()]):
                declared[name] = path.name
    assert len(declared) >= 40, f"read {len(declared)} UIText functions; were the sources read?"
    table = CLIENT.parent / "EngineTests/UITextLanguageTests.swift"
    rows = set(re.findall(r'\("(\w+)", \{', table.read_text(encoding="utf-8")))
    missing = sorted(f"{name} ({where})" for name, where in declared.items() if name not in rows)
    assert not missing, f"sentences no test composes in both languages: {missing}"
```

- **R1** The red commit's gate failed because the walk did not exist yet (it listed all 58
  functions), not on a sentence. For an enhancement that adds the test this is the right red; the
  walk's own red is shown by S1, S2, S3 and S9.

## Clean-up evidence
- Every mutant and test run: original bytes written back and sha256 compared (`Language.swift`
  2add43661cfe..., `Refinements.swift` a5fc7a348b7c..., `UITextLanguageTests.swift`
  f164d5a3825d..., `test-manifest.txt` 805aa10a2726..., `test_ios_client_contract.py`
  42fbd1ac0ecd...). No mismatch.
- `git hash-object` equals `HEAD:<path>` for each of those five files. The red tree was extracted
  into the scratchpad, not this worktree. No checkout, restore, stash, reset or commit. Build
  output went to the ignored `build/` and `ios/.build/`. `git status --short` lists only this
  record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `testEveryBranchAndFrameIsSaidInBothLanguages`, committed as written with its manifest line |
| T2 | fixed: the seat's `test_every_uitext_sentence_anywhere_in_the_app_has_a_row`, committed as written beside the first gate |
| R1 | accepted: the issue asks for a test, so the red is the gate that found every sentence without one, before the test existed |
