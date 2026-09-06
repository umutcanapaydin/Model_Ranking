---
record_type: review
id: m13-wave-1-tester
status: ratified
seat: independent
date: 2026-09-06
---
# M13-W1 — Tester seat (fault injection, V3C-72)

**Provenance, as in the sibling record.** Performed by a separate session that did not author the
code, working from the frozen diff and `subagent-profiles/Tester.md` at the base ref. The seat was
READ-ONLY on the repository by instruction and mutated only copies under its own temp directory;
`revert-clean: True` on all 42 trials, verified by md5. It could not write this file. The findings
are its own, transcribed without softening.

**Baseline:** 810 passed / 7 skipped; the five wave files 51 passed; `ruff` and `mypy` clean;
coverage 96% on the four touched modules.

**Mutation kill-rate at submission: 29 of 39 source mutants killed (74%). All ten survivors listed.**

## Verdict at submission: BLOCKING

### BLOCKING-1 — REQ-FIX-004 was proven for the library, not for `runner`. The criterion names `runner`.

Six wiring mutants survived the entire suite. The decisive one reverted the exit gate to
`if [ -z "$FAILED" ]; then` and reproduced the original defect verbatim — `skipped : build`, then
the all-green claim, exit 0 — with 810 tests green. Two more:

- keeping `skip "build"` **and** re-adding `record "build" 0` beside it: the presence-grep only
  checked that the `skip` literal existed;
- commenting out the `.` source line: the path string still appeared in the explanatory comment
  above it, so the "does runner source the library" test passed against a `runner` with no
  accounting at all.

The seat's summary: *everything the library does is genuinely tested; nothing tested that `runner`
uses it.*

**Disposition: FIXED.** `tests/unit/test_runner_accounting.py` now extracts `runner`'s OWN wrappers
and its OWN exit gate and executes them under bash. Extraction rather than invocation because a real
run costs `make check`, and a control whose test is too slow to run is precisely what this criterion
is about. **Verified by replaying the seat's own mutant**: reverting the gate on a copy now fails
three tests. The presence-grep was joined by a same-branch check that forbids `record` inside a
`skip` branch, and the source-line assertion now pins the executable statement rather than the path.

## MAJOR findings and their disposition

| # | Finding | Disposition |
|---|---|---|
| M1 | `test_the_real_artifact_is_accepted` gates on a gitignored `advisor.db`, so REQ-FIX-002's false-positive guard never runs in CI | **FIXED** — built from the canonical seed, runs unconditionally |
| M2 | Truncating the probe loop to the first surface (`[:1]`) survived the full suite; "all nine" is the stated mechanism and nothing pinned it | **FIXED** — `test_every_advertised_surface_is_probed` spies on the call and asserts the full set |
| M3 | `if gap <= close_pts:` → `if True:` survived: `CLOSE_CALL_PTS` was asserted as a CONSTANT, never as a THRESHOLD, so REQ-REC-004's negative direction had no test | **FIXED** — `test_a_gap_wider_than_the_threshold_is_not_disclosed_as_a_close_call`, two frontier rows 9.2 points apart, asserts silence |

## MINOR findings and their disposition

| Finding | Disposition |
|---|---|
| Mutants O1/O2: dropping the `(price, model)` tail of the frontier sort key survived both engines | **FIXED, and the fix found something** — see below |
| CWD-relative `LIB`/`RUNNER` paths; from `/tmp` the file failed 11 of 11 | **FIXED** |
| `LEGACY_PROBE_SCHEMA` declares `value` not `score`; `assert "models" in problem` passed only because SQLite reports a missing table before a missing column | **FIXED** |
| REQ-FIX-003 had no test through the real entry point | **FIXED** — `("scores", "source", "arena")` added to `test_refresh.py`'s parametrised cycle |
| `test_a_non_database_is_still_refused` lands on the outer handler, not the branch its docstring names | **Open**, MINOR, pre-existing |

**What closing O1/O2 turned up.** The obvious test — three equal-score rows at different prices,
assert the price ordering — cannot exist. Under correct dominance two frontier rows can only tie on
score if they also tie on price, so `blended_per_m` can never break a tie that `-score` left open:
**the price term of the sort key is now unreachable by construction.** It is deliberately kept (it
states the intended ordering and matches `min(value_pool, key=(price, model))` two functions away)
and the fact is recorded in the test file so the next reader does not spend an hour on a test that
cannot be written. Only the `model` term is reachable, and it is now pinned in both engines.

## Answers the seat gave to the questions it was set

- **Is the modified `test_close_call_is_disclosed` still a real test?** Yes — the close-call no-op
  mutant kills it, and the coverage it gave up survives in a pre-existing test. No test was weakened
  or deleted to go green (V3C-86 clean).
- **Is "any skip prevents the all-green claim" asserted in its strong form?** At the library, yes.
  At the instrument, it was not — BLOCKING-1.
- **Are the reflection-built fixtures nonsense?** Robust in the direction that matters: a new field
  of an unhandled type fails the fixture loudly; a misspelled override makes the digest tests fail
  rather than pass.
- **Criteria with no citing test able to fail?** None outright; REQ-FIX-004's was the one that could
  not fail for the criterion as written.

## Standing note the seat asked to be carried forward

`_ranked_row_count` and `_largest_surface_row_count` both swallow `sqlite3.Error` into `None` — the
same "check that says yes" shape M13 exists to remove. Not this wave's code; carried to W5.
