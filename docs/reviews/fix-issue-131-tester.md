---
record_type: review
id: fix-issue-131-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 131 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 95419f5..8d7af40 (`ec7970e` red test, `7a490e5` fix, `b68e786` and `8d7af40` merges
of #126's later commits). The branch is stacked on #126's; #126's own commits were reviewed by
their own seat and are not re-reviewed here, except where they move a PRD citation.
**Risk tier:** LOW (a records gate and a mechanical rewrite of the PRD's evidence cells).

**Method.** Profile, `AGENTS.md`, `.agents/rules/issues.md` and D-174, D-175, D-177 read from the
base `0198eb3`. The acceptance criterion is the issue body, which its triage pins: the PRD cites
evidence by name, `test_x.py::test_name`, the gate checks that each named test exists, and the line
numbers go. The thread adds the 13 workflow and record pointers the gate did not read. Worktree
detached at `8d7af40`, with its own venv and a copy of the served `advisor.db`, behind the stubs
that refuse `launchctl`, `simctl` and `xcodebuild`. Red: the tree of `ec7970e` extracted with
`git archive` into a scratch directory and the gate run there with this worktree's venv. The
conversion: a script of my own (not the author's), which reads every line pointer of an old PRD,
resolves it to the declaration on that line in the old tree (or the test that encloses a place),
pairs the old and new PRD lines, and compares the names in order. Faults: one exact unique
replacement per mutant, the gate's tests run, the original bytes written back and the sha256
compared, by a harness in the scratchpad. Nothing reached the network.

## Verdict
MINOR

The issue's criterion is proven red to green, the 430 converted names match what the old pointers
meant, and every mutant of a PRD citation is killed except a wrong directory (K1). Two holes in the
gate stay green: a helper in a test file passes as a test (T1, a test written), and a place
written in the form the PRD's own header documents is never checked (R1, a test written, red at
the head). The header also says "never by line" over 13 line pointers that remain (R2).

## Acceptance-criterion coverage
- A line pointer into a test is refused, and a citation by name is read:
  `tests/unit/test_prd_citations.py::test_a_test_is_cited_by_name_and_a_line_pointer_is_refused`
  (cites #131). RED at `ec7970e`: `AssertionError: a line pointer was accepted` (`assert []`), the
  symptom itself (the old gate accepts `test_x.py:3` because line 3 is a test), not a missing name.
  GREEN at the head.
- Each named test exists, in the file named:
  `::test_every_prd_citation_names_its_test` over the real PRD (M1 undeclared name, M2 a test of
  another file, M3 a base name two files share, all killed), and the planted cases in
  `::test_a_name_must_be_declared_in_its_file` and
  `::test_every_name_of_a_list_and_after_a_parenthetical_is_read`.
- The line numbers go, for Python, Swift and the Makefile: the same test over the PRD refuses
  `file.py:N` (M5), a bare `:N` after a name (M6), `at :N` (M7) and `Makefile:N` (M8); a `make`
  target the Makefile lacks is refused (M10). Planted cases in
  `::test_line_pointers_are_refused_and_make_targets_must_exist`.
- The conversion is right. My script read every pointer of the PRD on `main` (`0198eb3`) against
  `main`'s tree: 432 pointers (430 into Python or Swift, 2 `Makefile:117`), and all 432 name at the
  head exactly what they meant on `main`, 0 mismatches; both `Makefile:117` lines now name
  `make check`. Against the branch's own base `95419f5` (after #126 moved lines) one place differs:
  REQ-GAP-002's `clear()` "at :693" sat in `testTheRegisterRoundTripsThroughItsFile` there, a
  stale line #126 left; the head names `testTheRegisterIsBounded`, which holds `register.clear()`
  and is what `:693` meant on `main`. The head PRD cites 435 names: the 430 converted and 5 that
  were already by name on `main`.
- A sample of 10 names read against their requirement (seeded random): REQ-API-003
  `test_a_present_disclosure_survives_serialization`, REQ-APP-002
  `test_no_refinement_refines_a_surface_a_coding_request_answers_on`, REQ-REF-008
  `test_the_run_falls_inside_the_window_and_never_in_the_past`, REQ-RTR-005
  `testTheImageRuleNeverOverridesAnotherSurface`, REQ-FIX-001 `test_model_engine_frontier`,
  REQ-APP-003 `testThePlanIsGivenTheRoutedSurfacesOwnHealth` and
  `testAStaleBoardIsSaidOnTheCombinedListAsLoudlyAsOnTheCards`, REQ-LIC-001
  `test_a_changed_evidence_source_changes_the_digest`, REQ-ING-003
  `test_staleness_flag_fires_when_source_is_old`, REQ-REF-009
  `test_a_failed_required_source_is_carried_instead_of_failing_the_build`. Each is the test the
  old pointer named on `main`, and each name fits its row.
- A place's code stands in the test named:
  `::test_a_place_the_prd_points_into_holds_the_code_it_names` (M11 code moved out, M14 the place
  names another test, both killed), except in the documented form (R1).

## Suite result
- `make check-fast` at `8d7af40`: PASS, six legs (lint, typecheck, records, test, client-decls,
  swift-test) in 61 s; test leg 1799 passed, 25 skipped.

## Mutants

| ID | Fault | Result | Killed by |
|---|---|---|---|
| M1 | PRD: `test_rank.py::` a name not declared | KILLED | `test_every_prd_citation_names_its_test` |
| M2 | PRD: a test declared in `test_recommend.py`, cited under `test_rank.py` | KILLED | as M1 |
| M3 | PRD: `epoch.py::EPOCH_BUNDLE_URL` (two tracked `epoch.py`) | KILLED | as M1 (ambiguous) |
| M4 | PRD: the right name under a wrong directory (`tests/unit/test_litellm_contract.py`) | SURVIVED | none (K1) |
| M5 | PRD: `test_rank.py:81` written back | KILLED | as M1 |
| M6 | PRD: `, :106` after a name | KILLED | as M1 |
| M7 | PRD: the place written back as `at :668` | KILLED | as M1, and the place test |
| M8 | PRD: `(Makefile:117)` written back | KILLED | as M1 |
| M9 | PRD: a bare `::name` after `contract-tests.yml:17` (the name is declared in the line's earlier `.py`) | KILLED | as M1 |
| M10 | Makefile: `install-check` renamed, which the PRD names | KILLED | as M1 |
| M11 | `FrontDoorTests.swift`: `register.clear()` taken out of `testTheRegisterIsBounded` | KILLED | the place test |
| M12 | as M11, and an uncalled helper declared after the test holds `.clear()` | SURVIVED | none (K2) |
| M13 | PRD: a second place in the header's form, "`gone()` exercised in `` `::testTheOwnerReadsTheMostAskedFirst` ``" | SURVIVED | none; killed with R1's fix |
| M14 | PRD: the place names `testTheOwnerReadsTheMostAskedFirst` | KILLED | the place test |
| G1 | gate: the line-pointer refusal removed | KILLED | the #131 test and the line-pointer test |
| G2 | gate: a name never checked against its file | KILLED | three planted-case tests |
| G3 | gate: a test file read as a source file (any function counts) | SURVIVED, then KILLED by T1's test | `test_a_helper_of_a_test_file_is_not_a_test` |
| G4 | gate: an ambiguous base name takes its first path | KILLED | `test_every_name_of_a_list_and_after_a_parenthetical_is_read` |
| G5 | gate: a missing `make` target not reported | KILLED | the line-pointer test |

With the suite as committed, 15 of 19 killed. With T1's and R1's tests added and R1's one-line fix
applied, 17 of 19 (M4 and M12 are K1 and K2).

## Findings
- **T1** The gate's docstring says a name in a test file is "a test, a class of tests, or the file's
  `pytestmark`". No test fails when a test file is read with the source pattern, so any helper
  passes as a test (G3: 6 passed). Written this review, RED on G3 (`a helper passed as a test`),
  GREEN at the head; `ruff check` clean. Full text below, with R1's.
- **R1** A place written as the PRD's header documents it, "in `` `::<test_name>` ``" (and as the
  place test's own docstring writes it, "exercised in `` `::testName` ``"), is not read by the place
  check: its pattern wants `in ::name` with no backtick. M13 stayed green. Today the PRD's one
  place is written without the backtick, so nothing is wrong yet; the next place written by the
  header's rule goes unchecked. The test below is RED at the head and GREEN with this change to
  the pattern in `test_a_place_the_prd_points_into_holds_the_code_it_names`:
  `\bin\s+::(\w+)` to `` \bin\s+`?::(\w+) ``. With that change the gate's six tests and both of
  mine pass on the real PRD, and M13 is killed. Fix in this branch (the pattern, or the header and
  the docstring), and add the test.
- **R2** The PRD's new header says "**Evidence is cited by name, never by line**", and 13 line
  pointers into workflow and record files remain (`ci.yml:7-10`, `:54`; `contract-tests.yml:15-17`,
  `:39-60`, `:110`, `:17`, `:89`; `m14-wave-1-close.md:32`, `:46`; `m10-wave-4-close.md:37`;
  `m16-plan.md:53`; `m7-plan.md:166`; `coverage-by-req.md:39`), the 13 the issue's thread names.
  The gate's docstring says they stay outside it. Make the header say what holds: a test or a
  source name is cited by name; a workflow's or a record's pointer stays a line and is not checked.
- **K1** The gate resolves a file by its base name and ignores the path written before it, so
  `tests/unit/test_litellm_contract.py::...` passes for a file under `tests/integration/` (M4). #105's
  gate did the same; the name is still unique in the tree. Not this issue's criterion; the author
  may file it.
- **K2** The place check reads a test's body up to the next test's declaration, so in Swift a
  helper declared between two tests counts as part of the one above it (M12). Contrived, and not
  this issue's criterion; noted only.

T1's and R1's tests, as `tests/unit/test_prd_citations_tester.py` (removed again so the worktree
holds only this record; the author adds them to the branch):

```python
"""Tester (#131): a name cited in a test file must be a test, and a place written in the form the PRD
documents is checked like any other place."""

from __future__ import annotations

from pathlib import Path

import pytest

from . import test_prd_citations as citations

FILES = {"tests/unit/test_x.py": ["import os", "", "def _helper():", "    pass", "", "def test_a():", "    _helper()"]}
BY_NAME = {"test_x.py": ["tests/unit/test_x.py"]}


def test_a_helper_of_a_test_file_is_not_a_test() -> None:
    """#131: in a test file a name must be "a test, a class of tests, or the file's `pytestmark`".
    A helper is declared there too, and is not evidence."""
    read = FILES.__getitem__
    assert not citations.problems("Evidence: test_x.py::test_a", BY_NAME, read)
    assert citations.problems("Evidence: test_x.py::_helper", BY_NAME, read), "a helper passed as a test"


def test_a_place_in_the_form_the_prd_documents_is_checked_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#131: the PRD's header and the place check's docstring write a place as "in `::<test_name>`".
    A place written that way must have its code in the test it names, as one written "in ::name" does."""
    (tmp_path / "test_x.py").write_text("def test_a():\n    clear()\n\n\ndef test_b():\n    pass\n", encoding="utf-8")
    prd = tmp_path / "prd.md"
    prd.write_text("Evidence: test_x.py::test_a (`clear()` exercised in ::test_a), "
                   "::test_b (`clear()` exercised in `::test_b`)\n", encoding="utf-8")
    monkeypatch.setattr(citations, "ROOT", tmp_path)
    monkeypatch.setattr(citations, "PRD", prd)
    monkeypatch.setattr(citations, "tracked", lambda: {"test_x.py": ["test_x.py"]})
    with pytest.raises(AssertionError, match="does not hold"):
        citations.test_a_place_the_prd_points_into_holds_the_code_it_names()
```

Runs: at the head, 7 passed, 1 failed (`test_a_place_in_the_form_the_prd_documents_is_checked_too`,
R1's hole); on G3, `test_a_helper_of_a_test_file_is_not_a_test` fails too; with R1's pattern change,
8 passed.

## Tests added/extended this review
- `tests/unit/test_prd_citations_tester.py::test_a_helper_of_a_test_file_is_not_a_test` (T1), not
  committed; text above.
- `tests/unit/test_prd_citations_tester.py::test_a_place_in_the_form_the_prd_documents_is_checked_too`
  (R1), not committed; text above.

## Clean-up evidence
- Every mutant, and R1's candidate fix: original bytes written back, sha256 equal before and after
  (`docs/prd.md`, `Makefile`, `ios/EngineTests/FrontDoorTests.swift`,
  `tests/unit/test_prd_citations.py`, checked again with `shasum -c` after the runs).
- `git hash-object` equals `HEAD:<path>` for those four files: `docs/prd.md` (5c9957e7),
  `Makefile` (f5aee6ab), `ios/EngineTests/FrontDoorTests.swift` (65ae0e13),
  `tests/unit/test_prd_citations.py` (8e22761f). The Tester's test file deleted. The red tree and the comparison script live in the
  scratchpad. No checkout, restore, stash, reset or commit. `git status --short` lists only this
  record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `test_a_helper_of_a_test_file_is_not_a_test`, committed as written in `tests/unit/test_prd_citations_places_and_helpers.py` |
| R1 | fixed: the place check reads "in `::name`" with or without backticks; the seat's `test_a_place_in_the_form_the_prd_documents_is_checked_too` is committed as written beside the first |
| R2 | fixed: the PRD's format note says evidence in Python or Swift is cited by name, and that workflow and record pointers keep their lines outside the gate |
| K1 | refused: the PRD names files by base name, and the gate refuses a base name that is not exactly one tracked file; a directory written before it is prose the gate does not read, as before #131 |
| K2 | refused: a helper between two Swift tests serves the test above it, so counting it in that test's body is the reading a place inside a test means |
