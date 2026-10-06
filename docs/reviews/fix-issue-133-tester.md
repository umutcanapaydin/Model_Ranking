---
record_type: review
id: fix-issue-133-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 133 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the change or its tests.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 0198eb3..7575645 (the change: two UI tests and the `askAgain` helper in
`ios/UITests/ScreenPathTests.swift`, and nine PRD line pointers moved), then the merge `a84099f`,
which takes #131's PRD (by name).
**Risk tier:** LOW (tests only; no production code changes).

**Method.** Profile, `AGENTS.md`, `.agents/rules/issues.md` and D-169, D-174 (as amended on
2026-10-05), D-175 and D-177 read from the base `0198eb3`. The acceptance criterion is the issue as
its triage pins it: one UI test on the Turkish screen that asks a question held for the reader, and
one that asks two questions in a row, the second held, so that X21 (the held card's buttons in
English on the Turkish screen) and T11 (the previous question's notice above a held card) are each
seen by a UI test. Worktree detached at `a84099f`, with its own venv and a copy of the served
`advisor.db`. Under D-174's 2026-10-05 amendment this seat ran `make ui-test` behind the stub that
refuses `launchctl` only, with `UI_TEST_ONLY=ScreenPathTests` and `MODEL_RANKING_DB` set to the
worktree's copy (so `~/Library/Application Support/model-ranking` was not read). Three runs: the
head, then two fault runs of two faults each, each fault in a different one of the two new tests.
Faults: exact unique replacements, the original bytes written back and the sha256 compared, by a
harness in the scratchpad. No test reached the network.

## Verdict
PASS

There is no separate red commit: the change is the tests. Its red to green is that each new test
fails on the fault the issue names, with the issue's symptom as its message, and passes on the
code. All six faults were killed, two of them by gates outside the UI target.

## Acceptance-criterion coverage
- The Turkish screen, held for the reader:
  `ScreenPathTests.swift::testATurkishReaderIsAskedBackInTurkish` (cites #133, K12, X21). GREEN at
  the head. With the held card's "Find a model" button given the English (X21's shape, F1), it
  fails on the symptom: `XCTAssertNotEqual failed: ("Find a model") is equal to ("Find a model") -
  askBack.find is in English on the Turkish screen`. With the note given the English (F3), it fails
  with `the note is in English on the Turkish screen`.
- A held second question clears the first answer:
  `ScreenPathTests.swift::testAHeldSecondQuestionClearsTheFirstAnswer` (cites #133, K12, T11, D-169
  clause 4). GREEN at the head. With the held branch of `ask()` keeping `routing` (T11's shape, F2),
  it fails on the symptom: `the first question's routing notice stays above the held one`.
- `askAgain` empties the field: when it does not (F4), the second question reaches the router as
  "Which model writes code best?what is the capital of australia", which the scripted table does
  not hold, and the test fails with `the second question was not held`. A test notices, though only
  through the routing table (K2).
- The file holds no Turkish (the tests compare with the English, L1): a Turkish literal planted in
  it fails `check_records` with `[L1] Turkish text in an English-only repository` (N1).
- The PRD at the merge: identical to #131's head (`git diff 8d7af40 a84099f -- docs/prd.md` is
  empty); the only file the merge adds to #131's tree is `ScreenPathTests.swift`. My comparison
  script (the #131 seat's) finds all 432 pointers of `main`'s PRD named at `a84099f` as they meant on
  `main`, 0 mismatches. A cited UI test renamed fails the PRD gate (N2). So the nine pointers the
  helper moved at `7575645` no longer exist; the names do not move.

## Suite result
- `make check-fast` at `a84099f`: PASS, six legs (lint, typecheck, records, test, client-decls,
  swift-test) in 59 s; test leg 1799 passed, 25 skipped. `SlowTierTests` passed; no re-run needed.
- `make ui-test` with `UI_TEST_ONLY=ScreenPathTests` at `a84099f`: 16 tests, 0 failures, in 199 s
  (3 min 50 s with the build); the two new tests passed in 15.8 s and 12.8 s.

## Mutants

| ID | Fault | Run | Result | Killed by |
|---|---|---|---|---|
| F1 | `ContentView.swift`: the held card's "Find a model" button in English (`askBackFind(.english)`) | UI A | KILLED | `testATurkishReaderIsAskedBackInTurkish` |
| F2 | `ContentView.swift`: the held branch of `ask()` keeps `routing` | UI A | KILLED | `testAHeldSecondQuestionClearsTheFirstAnswer` |
| F3 | `ContentView.swift`: the note in English (`notASearchNote(.english)`) | UI B | KILLED | `testATurkishReaderIsAskedBackInTurkish` |
| F4 | `ScreenPathTests.swift`: `askAgain` does not delete the old question | UI B | KILLED | `testAHeldSecondQuestionClearsTheFirstAnswer` |
| N1 | `ScreenPathTests.swift`: a Turkish literal in place of the English it compares with | records | KILLED | `check_records` L1 |
| N2 | `ScreenPathTests.swift`: `testNoWordIsTheNote` renamed (the PRD cites it) | pytest | KILLED | `test_prd_citations.py::test_every_prd_citation_names_its_test` |

6 of 6 killed. In each UI fault run exactly the two new tests failed and the other 14 passed
(16 tests, 2 failures each), so neither fault was seen by any older UI test.

## Findings
- **K1** Neither new test is cited in the PRD. Each cites #133 and the review findings it guards,
  and REQ-ASK-005 and REQ-LOC-001 are the rows they strengthen. The issue does not ask for it, and
  it does not change the verdict; the author may add the two names to those rows.
- **K2** F4 is caught only because the joined text is missing from the scripted routing table, and
  `askAgain` taps at 97 % of the field's width, which reaches the end of a one-line question only.
  Both hold for the one question the helper is used with today. Noted only.

## Tests added/extended this review
- none

## Clean-up evidence
- Every fault: original bytes written back, sha256 equal before and after
  (`ios/ModelRanking/ContentView.swift`, `ios/UITests/ScreenPathTests.swift`, checked again with
  `shasum -c` after each run).
- `git hash-object` equals `HEAD:<path>` for `ios/ModelRanking/ContentView.swift` (80472701) and
  `ios/UITests/ScreenPathTests.swift` (6dd878d0).
- After the last run nothing answers on 127.0.0.1:8090 and no engine process is left; `build/` is
  ignored. `launchctl`, the engine installer and remover, Docker and port 8080 were not used. No
  checkout, restore, stash, reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| K1 | fixed: REQ-ASK-005 cites both new UI tests, and REQ-LOC-001 the Turkish one |
| K2 | refused: `askAgain` exists for the second question, and the test that uses it fails when the field is not emptied ("not held"); a test of the helper alone would test the test |
