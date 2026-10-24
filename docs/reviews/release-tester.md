---
record_type: review
id: release-tester
status: draft
seat: independent
process_version: v7.2
date: 2026-10-23
---
# Release Tester Review

This is a delta verdict. It extends the verdict of 2026-10-23 (MINOR, reviewed head `471bd73`, written at `660af4b`),
which stays in git history; its findings M1-M3 and its known open gaps are carried unchanged. It is the light-mode
Tester for release v0.1.0, dispatched by `/going-live` before the hosted deploy.

**Reviewer:** Tester subagent (`.claude/agents/Tester.md`, `AGENTS.md` and `.agents/rules/practices.md` read from
`main`). I had fresh eyes and wrote none of the range's product code or tests. The only tests I wrote are the ones
this review lists under "Tests added".
**Independent:** yes
**Date:** 2026-10-23
**Commit range:** `471bd736a0995715dc62838f13e4b0fcbf4d4f1a..55cf42e612615c86c579c938ba50fbebf527700f` (main's tip,
the merge of PR #416), plus this review's two test commits `91eff48` and `9d3cf0e`. The code delta is #416 alone:
`9bdce37` (D-220), `520520c` (red tests), `bf278b0` (fix). The rest of the range is docs.
**Reviewed head:** 9d3cf0e2371c1900463a50970a1b2fca8e24964c
**Risk tier:** HIGH. #416 changes a data-safety guard: the D-159/D-164 board-loss limits (INV-54).
**Seat:** my own worktree on `review/release-tester-415`, cut from `55cf42e`, with its own `.venv` (`make install`,
`make hooks`) and a copy of the main clone's `advisor.db`; a second detached worktree at `520520c` ran the red
commit's tests against the pre-fix code. No launchd service, Fly, owner data directory or network was touched;
every probe ran in-process on fixtures the tests build. Scratch files stayed outside the repository.
**Cross-model routing:** author family Claude / reviewer family Claude; no second family was available in this seat.
Fresh context: this seat read the code, the tests, #415 and D-220, not the implementer's session.

## Verdict
MINOR -- nothing BLOCKING is open. Every acceptance criterion of #415 and D-220 has a passing citing test. Ten of
27 hand-made faults stayed green on the suite #416 shipped, among them the committed cuts file never reaching the
nightly guard; this review closed all ten, and one uncovered pair of fail-closed branches, with tests. Three
faults stay green and are equivalent on every recorded name (M2). Three MINOR findings (M1-M3) are new.

## Acceptance-criterion coverage
**(1) An unlinked row is compared by its spelling key, numbered per key; a re-spelling is a rename, a flood refuses**
- `tests/unit/test_refresh_board_ids.py:154` -- a case and punctuation re-spelling of every unlinked row moves no
  guard. GREEN; red at `520520c`; red on F01, F04.
- `tests/unit/test_refresh_board_ids.py:166` -- a changed letter is still a name lost (INV-54). GREEN; red on F05.
- `tests/unit/test_refresh_board_ids.py:180` -- re-spellings beside their old names are new rows, so the flood
  guard fires. GREEN; red on F06.
- `tests/unit/test_refresh_board_ids.py:195` -- `+` is part of the key (`Command R+` is not `Command R`). GREEN;
  red at `520520c`; red on F02.
- `tests/unit/test_refresh_board_ids.py:380` -- an unlinked key never equals a linked model. Red on F07, where
  `UnlinkedRow` is a tuple again.
- `tests/unit/test_refresh_boards.py:80`, `tests/unit/test_uncovered_boards.py` (`epoch_chess` fingerprint) --
  the published row shape. Red on F03 (digits dropped from the key) and F05.

**(2) A bracketed name the grammar or curated rules refuse is read as its slug; names that resolved before are
unchanged**
- `tests/unit/test_arena_respelling.py:40` -- each of the 104 recorded pairs resolves as its slug did. GREEN; 68 of
  the 104 pairs fail at `520520c`; red on F22 (70 tests).
- `tests/unit/test_arena_respelling.py:50` -- four of the 31 measured lost links come back. GREEN; red at `520520c`.
- `tests/unit/test_arena_respelling.py:55` -- a curated alias in display spelling reaches its rule. GREEN; red on
  F21.
- `tests/unit/test_arena_respelling.py:68`, `:76`, and `tests/unit/test_registry.py` -- names that resolved before,
  a trailing effort, and a moving alias (D-166). GREEN; `test_registry.py` is red on F24 (the curated lookup reading
  the bracket first).
- `tests/unit/test_arena_respelling.py:86` (added) -- an effort parenthesis never lands in a model id. Red on F25.

**(3) `data/accepted-cuts.yaml` excuses exactly the named rows on the named board; a malformed file fails closed**
- `tests/unit/test_accepted_cuts.py:51`, `:57`, `:61`, `:67`, `:73` -- the control, the cut, rows outside it, another
  board, an unlinked row. GREEN; red on F08, F09, F12.
- `tests/unit/test_accepted_cuts.py:80` -- the committed file holds `epoch_chess`'s 94 names and nothing else. GREEN.
- `tests/unit/test_accepted_cuts.py:95`, `:120` (added), `:126` (added), `:217` (added) -- the schema fails closed:
  15 malformed shapes, broken YAML, an unreadable path. GREEN; red on F13-F18, F28, F29.
- `tests/unit/test_accepted_cuts.py:150` (added) -- a named row excuses one row, not every row of its model or key.
  Red on F10 and F11.
- `tests/unit/test_accepted_cuts.py:188` (added) -- through `refresh()`, the file on disk is what the nightly guard
  applies: published with it, refused without it. Red on F20.
- `tests/unit/test_accepted_cuts.py:197` (added) -- through `refresh()`, a malformed file stops the night, records
  `EXIT_FAILED` and leaves the live artifact byte-identical. Red on F16, F19, F20.

**(4) INV-54 amended, its cited tests asserting what it says**
- All 11 tests `docs/security-invariants.md` cites for INV-54 exist and pass (`test_refresh_board_ids.py:131`,
  `:166`, `:180`; `test_accepted_cuts.py:61`, `:95`; `test_floor_served.py:162`, `:265`, `:357`;
  `test_refresh_boards.py:80`, `:115`, `:127`). Each new clause has a cited test that fails when it is removed (F05,
  F06, F09, F13-F18).

## Red to green on reported symptoms
- #415, LMArena's rename and Epoch's chess re-run: `520520c`'s tests, run against `520520c`'s own code, gave 88
  failed (73 in `test_arena_respelling.py`, 13 in `test_accepted_cuts.py`, 2 in `test_refresh_board_ids.py`)
  and 77 passed. The fix commit `bf278b0` makes them pass, and they pass at `55cf42e`. The red is real:
  failures are wrong resolutions and refused boards, not import errors, except in `test_accepted_cuts.py`, whose API
  did not exist before the fix.

## Suite result
- `make check` at `9d3cf0e`: PASS, exit 0 (pytest 4624 passed, 37 skipped; swift-test 727; client-decls PASS).
- Full pytest at `9d3cf0e` (check-fast's test leg, offline sandbox, artifact required): PASS. Each fault run over the
  whole suite: 4569 passed, 91 skipped.
- **Coverage on touched code:** `workflows/refresh.py` 95.7% at `471bd73` -> 96.1% at `9d3cf0e`;
  `workflows/registry.py` 99.5% -> 99.5%. Before `9d3cf0e`, `refresh.py:296-297` and `:324-325` (the two
  fail-closed branches of the cuts file) ran under no test; now none of the lines #416 added is uncovered.

## Fault-injection table
Each fault was one exact string replacement, reverted in place by the reverse replacement; md5 was checked equal to
the pre-injection hash after every revert (`refresh.py` `7ed144fe...`, `registry.py` `142d94c8...`), and `git status`
showed only test files changed. "Before" is the suite #416 shipped; "after" is the suite at `9d3cf0e`.

| ID | Fault | File | Before | After |
|---|---|---|---|---|
| F01 | key not lowercased | refresh.py | RED | RED |
| F02 | key drops `+` | refresh.py | RED | RED |
| F03 | key drops digits | refresh.py | RED | RED |
| F04 | key is the raw name | refresh.py | RED | RED |
| F05 | key is a constant | refresh.py | RED | RED |
| F06 | rows of one key not numbered | refresh.py | RED | RED |
| F07 | `UnlinkedRow` a NamedTuple | refresh.py | RED | RED |
| F08 | `_excused` returns 0 | refresh.py | RED | RED |
| F09 | `_excused` excuses every lost row | refresh.py | RED | RED |
| F10 | `_excused` excuses every copy of a named model | refresh.py | **GREEN** | RED |
| F11 | `_excused` excuses every row of a named key | refresh.py | **GREEN** | RED |
| F12 | one board's cut excuses any board | refresh.py | RED | RED |
| F13 | an entry may carry extra keys | refresh.py | **GREEN** | RED |
| F14 | an unknown board accepted | refresh.py | RED | RED |
| F15 | a board named twice accepted | refresh.py | **GREEN** | RED |
| F16 | the decision not checked as an ADR id | refresh.py | **GREEN** | RED |
| F17 | the reason not checked | refresh.py | **GREEN** | RED |
| F18 | `cuts` need not be a list | refresh.py | **GREEN** | RED |
| F19 | a malformed file read as no cuts (fail open) | refresh.py | **GREEN** | RED |
| F20 | `degradations` ignores the committed file | refresh.py | **GREEN** | RED |
| F21 | no bracket fallback for curated rules | registry.py | RED | RED |
| F22 | no bracket fallback for the grammar | registry.py | RED | RED |
| F23 | the grammar reads the bracket first | registry.py | GREEN | GREEN (M2) |
| F24 | the curated lookup reads the bracket first | registry.py | RED | RED |
| F25 | no effort exemption in `_unbracketed` | registry.py | **GREEN** | RED |
| F26 | a media name read as dash tokens too | registry.py | GREEN | GREEN (M2) |
| F27 | the bracket fallback past a refusal reason | registry.py | GREEN | GREEN (M2) |
| F28 | broken YAML escapes as `YAMLError` | refresh.py | (uncovered) | RED |
| F29 | an unreadable path escapes as `OSError` | refresh.py | (uncovered) | RED |

Tally: 29 faults. 14 were red on #416's suite; 12 more are red with this review's tests; 3 stay green. A probe over
the 1,972 parenthesised names in `tests/` found no name on which F23, F26 or F27 changes a resolution, so no test can
separate them on recorded data. F25 has two such names (`GPT 5 (2025-08-07) (medium)`, from `test_registry.py`).

**Mutation kill-rate (advisory).** No mutation runner is wired for this stack. Of the 29 hand-made faults, 26 are
killed at `9d3cf0e` (14 of 27 on #416's own suite).

## Test integrity
- No test was deleted, skipped or xfailed in the range (`git diff 471bd73..55cf42e -- tests`).
- `test_refresh_board_ids.py:166` changed meaning: at `471bd73` it asserted that a case-only re-spelling of an
  unlinked row is a loss; it now asserts that a changed letter is. That is D-220 clause 4, as the owner ruled on
  #415, and `:154` asserts the new case-only behaviour. Not a weakening.
- `test_refresh_boards.py:80` and `test_uncovered_boards.py` compare `UnlinkedRow("m0", 0)` where they compared
  `"m0"`: the same assertion on the new row type, as strict as before.

## Mocks / contract tests
- No new integration. `tests/fixtures/arena_respelling/text-2026-10-22.json` is recorded from LMArena's
  2026-10-22 file, which this seat did not fetch again (no network), so the pairs' provenance is the implementer's.

## BLOCKING
- none open. Found and closed in this review: the green faults F10, F11, F13, F15-F20 and F25, and the uncovered
  fail-closed branches `refresh.py:296-297` and `:324-325` (tests in "Tests added"). F20 mattered most: no test
  showed that the committed file reaches the nightly guard, so a regression there would have refused
  `epoch_chess` again with the whole suite green.

## MINOR (the author fixes each in this wave or files it as an issue)
- **M1** `data/accepted-cuts.yaml` and `src/app/workflows/refresh.py` (`_excused`) -- the cut is accepted
  "once" (D-220 clause 3, #415's ruling), but nothing retires it. If Epoch later publishes a named row again and then
  drops it, the entry excuses that loss too. Remove the entry once the first refresh publishes, or file it.
- **M2** `tests/unit/test_arena_respelling.py:68` -- "a name that resolved before resolves as before" asserts only
  that the name derives at all, not to the same id. F23, F26 and F27 stay green because no recorded name tells them
  apart. Assert the id the name had before #416 (for example against `registry._derive`), or file it.
- **M3** `tests/unit/test_accepted_cuts.py:1` -- the module docstring cites "D-220 clause 2" for the accepted cut,
  which is clause 3.

## Tests added this review
- `tests/unit/test_accepted_cuts.py:120` -- D-220 clause 3: nine schema shapes fail closed. Red on F13, F15-F18.
- `tests/unit/test_accepted_cuts.py:126` -- a malformed file on disk raises, a missing one excuses nothing. Red on F18,
  F19.
- `tests/unit/test_accepted_cuts.py:150` -- a named row excuses one row, linked and unlinked. Red on F10, F11.
- `tests/unit/test_accepted_cuts.py:188` -- through `refresh()`, the file on disk decides the night. Red on F20.
- `tests/unit/test_accepted_cuts.py:197` -- through `refresh()`, a malformed file fails the night and leaves the live
  artifact. Red on F16, F19, F20.
- `tests/unit/test_accepted_cuts.py:217` -- broken YAML and an unreadable path raise the cuts error. Red on F28, F29.
- `tests/unit/test_arena_respelling.py:86` -- D-220 clause 2 beside #38: an effort never lands in a model id. Red on
  F25.

## make check
`make check` in this seat's worktree at `9d3cf0e`, run serially as the merge gate: exit 0. Lint, typecheck, pytest
(4624 passed, 37 skipped, offline sandbox, artifact required), the records legs, conformance, swift-test (727) and
client-decls all PASS.
