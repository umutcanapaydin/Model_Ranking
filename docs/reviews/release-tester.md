---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.2
date: 2026-10-24
---
# Release Tester Review

This is a delta verdict. It extends the verdict of 2026-10-23 (MINOR, reviewed head `9d3cf0e`, written at
`9208fd8`), which stays in git history; its findings M1-M3 and its known open gaps are carried unchanged. It is the
light-mode Tester for release v0.1.0, dispatched by `/going-live` before the hosted deploy.

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`, `AGENTS.md` and `.agents/rules/practices.md` read from
`main`). I had fresh eyes and wrote none of the range's code or tests; this review adds no test.
**Independent:** yes
**Date:** 2026-10-24
**Commit range:** `9d3cf0e2371c1900463a50970a1b2fca8e24964c..0bdf2eb` (main's tip, the merge of PR #420). The code
delta is three files: `.github/workflows/ci.yml` (`b2d0e3c`, the owner's, #406), `tests/unit/test_ci_needs.py`
(`7c1730a`, the owner's, #406), and `tests/unit/test_carry_forward.py` (PR #422 for #421: red `3cd571d`, fix
`d316142`). `src/` is unchanged across the range (`git diff --quiet 9d3cf0e 0bdf2eb -- src`). The rest is docs.
**Reviewed head:** 0bdf2eb2fa3f92439b29e6b58a71948b9722e15d
**Risk tier:** LOW. A CI limit and a test fixture's clock; no product code moves.
**Seat:** my own worktree on `review/release-tester-422`, cut from `0bdf2eb`, with its own `.venv` (`make install`)
and a copy of the main clone's `advisor.db` for the artifact tests. No launchd service, Fly, owner data directory or
network was touched. The workflow file was read, never edited: the #406 fault was planted on the test side.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: this seat read the diff, the tests, #406 and #421, not the implementer's session.

## Verdict
PASS -- both acceptance criteria have a passing citing test, the #421 symptom reproduces red on the pre-fix fixture
and is green after it, no assertion was weakened, deleted or skipped, and every injected fault went red.

## Acceptance-criterion coverage
**#421 (1): the carry tests no longer depend on the wall clock passing a fixed date**
- `tests/unit/test_carry_forward.py:40-43` -- `_live()` (`:34`) restamps every `CARRY_TABLES` row at `NOW` minus one day
  after the build. `tests/unit/test_carry_forward.py:416` asserts every stamp's age from `NOW` is in
  `[0, CARRY_MAX_AGE)`, "whatever today's date is". GREEN on 2026-10-24, one day past the date that broke it.
- The one test that stamps with the real clock, `:160` (the CLI path), takes both its `--last-ok` record and
  `main`'s own clock from now, so it does not age either. The other importer of this module,
  `tests/unit/test_datacurve_move.py:138`, uses `NOW` and `_iso` only, not `_live`.

**#421 (2): the guard fails if `_live` goes back to wall-clock stamps**
- `tests/unit/test_carry_forward.py:416` -- RED on F1 below (the restamp removed), with `:341`,
  `test_a_live_artifact_from_before_the_access_table_still_carries`, the symptom.

**#406: the CI limit and its pinned test agree**
- `.github/workflows/ci.yml:38` is `timeout-minutes: 30`. `tests/unit/test_ci_needs.py:56` and `:82` plant on
  `runs-on: ubuntu-latest\n    timeout-minutes: 30\n`, and `_planted` (`:44-46`) asserts the anchor occurs exactly
  once in the workflow, so the limit and the test cannot drift apart silently. GREEN; RED on F2a.

## Red to green on reported symptoms
- #421 -- `3cd571d`'s test file, run against the unchanged `src/`: 2 failed
  (`test_a_live_artifact_from_before_the_access_table_still_carries`, `test_the_live_fixture_is_stamped_on_the_tests_clock`),
  23 passed. At `0bdf2eb`: 25 passed.
- #406 -- a cancelled CI run, not a test symptom; nothing to reproduce locally. The limit's agreement is proven above.

## Suite result
- `tests/unit/test_carry_forward.py tests/unit/test_ci_needs.py`: 36 passed (the 60% coverage floor is not
  meaningful for a two-file run and is not counted).
- `make check`: see "make check" below.
- Coverage on touched code: no product code was touched.

## Fault-injection table
Each fault was one atomic sequence in this worktree: md5 recorded, the exact string replaced, the file run, the
string replaced back, and the md5 compared. All three files ended byte-identical (`git status` clean).

| ID | Fault | Result |
|---|---|---|
| F1 | `_live()` no longer restamps (the `for table in CARRY_TABLES: UPDATE ...` loop removed) | RED: 2 failed, the guard `:416` and the symptom test |
| F2a | the plants at `test_ci_needs.py:56-57,82-83` pinned to `timeout-minutes: 15` while CI says 30 | RED: 2 failed, `_planted`'s anchor assert (`:45`) |
| F2b | the macos-runner plant's new runner set back to `ubuntu-latest` (a plant that flips nothing) | RED: 1 failed, `[macos-runner]` |

**Mutation kill-rate (advisory).** No mutation runner is wired for this stack. Hand-made faults: 3 of 3 killed.

## Test integrity
- `tests/unit/test_carry_forward.py`: the range adds lines only (an import, the restamp, the guard). No assertion
  changed, no skip or xfail was added. `d316142` replaced the red test's literal `("scores", "pricing", "access")`
  with `CARRY_TABLES`, which names the same three tables (`src/app/workflows/build.py:246`), so the guard is derived
  from the code, not narrowed.
- `tests/unit/test_ci_needs.py`: four lines change only the plant anchors' `15` to `30`. The expected flipped
  sets, the `pytest.raises(ValueError, match="runner")` and the `_planted` count assert are unchanged.

## Mocks / contract tests
- No integration is touched.

## BLOCKING
- none

## MINOR (the author fixes each in this wave or files it as an issue)
- none new. M1-M3 of the `9d3cf0e` verdict are carried unchanged.

## Tests added this review
- none

## make check
`make check` in this seat's worktree at `0bdf2eb`, run serially as the merge gate: exit 0. Lint, typecheck,
pytest (4625 passed, 37 skipped, offline sandbox, artifact required), coverage floor, the records legs,
conformance (33), swift-test (727, and SlowTierTests 7 of 7) and client-decls all PASS. The first run stopped at
W-108 because the fresh worktree had no `advisor.db`; it passed once the main clone's copy was put in the worktree,
as the `9d3cf0e` seat did.
