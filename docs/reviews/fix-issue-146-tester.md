---
record_type: review
id: fix-issue-146-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 146 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 3426626..dcc50a4 (`a9b672a` red test, `dcc50a4` fix), branch
`fix/issue-146-sweep-writing-and-journal`.
**Risk tier:** LOW (litter beside the artifact; the sweep's age rule is the load-bearing part).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `3426626`. The
acceptance criterion is the issue body as the triage comment pins it: "the sweep's list takes both,
with a test that plants each one a day old". Red: the tree of `a9b672a` extracted with `git archive`
into a scratch directory (its `refresh.py` is byte-identical to the base) and the new test run there
with this worktree's venv. Gate: `make check-fast` at the head. Faults: one exact unique replacement
per mutant, the full suite run (`pytest -n auto`, artifact required), the original bytes written back
and the sha256 compared, by a harness in the scratchpad. Nothing reached the network.

## Verdict
MINOR

The issue's criterion is proven red to green, and every mutant that touches the two new names or the
age rule is killed. One clause of the invariant the fix extends, INV-49's "only this artifact's
scratch", has no test that fails without it; the test is written below (T1).

## Acceptance-criterion coverage
- The sweep takes a killed cycle's `.writing` record scratch and its candidate's SQLite journal, each
  planted two days old: `tests/unit/test_epoch_bundle_fetch.py:370`
  (`test_a_killed_cycles_status_scratch_and_journal_are_swept_too`, cites #146). RED on `a9b672a`:
  `AssertionError: a killed cycle's scratch outlived the sweep`, listing
  `advisor.db.refresh.json.dead.writing` and `advisor.db.dead.candidate-journal`. GREEN at `dcc50a4`.
- A sibling's minutes-old scratch of both kinds is kept: the same test, its second assertion (`:397`).
- The names planted are the names the code makes. `write_status` uses
  `mkstemp(prefix=<artifact>.refresh.json., suffix=.writing)` (`src/app/workflows/refresh.py:822`).
  A probe with the venv's `sqlite3` on `advisor.db.abc123.candidate` inside an open write
  transaction listed `advisor.db.abc123.candidate-journal`, and `src/app` sets no `journal_mode`.
- The INV-49 row cites the new test, and `tests/unit/test_security_invariants.py` refuses a misspelt
  citation (M10).

## Suite result
- `make check-fast` at `dcc50a4`: PASS, six legs (lint, typecheck, records, test, client-decls,
  swift-test); test leg 1782 passed, 25 skipped.

## Mutants

| ID | Fault (in `src/app/workflows/refresh.py` unless named) | Result | Killed by |
|---|---|---|---|
| M1 | `"writing"` dropped from the sweep's list | KILLED | the #146 test |
| M2 | `"candidate-journal"` dropped | KILLED | the #146 test |
| M3 | `"candidate-journal"` written as `"journal"` (glob `<name>.*.journal`) | KILLED | the #146 test |
| M4 | age check removed (`< 0`) | KILLED | the #146 test and the W-124 sweep test |
| M5 | age check skipped for the two new kinds only | KILLED | the #146 test (sibling assertion) |
| M6 | glob widened to `*.{suffix}`: any artifact's scratch | SURVIVED, then KILLED by T1's test | `test_the_sweep_leaves_another_artifacts_day_old_scratch_alone` |
| M6b | glob `*db*.{suffix}`: a name that only shares letters | KILLED by T1's test | as M6 |
| M7 | the call `_sweep_stale_scratch(target)` removed | KILLED | both sweep tests |
| M8 | threshold three days instead of one | KILLED | both sweep tests |
| M9 | `"writing"` misspelt `"writting"` | KILLED | the #146 test |
| M10 | `docs/security-invariants.md`: INV-49 cites a misspelt test name | KILLED | `test_security_invariants.py::test_the_list_holds_together` |

With the suite as committed, 9 of 10 runs killed (M6 survived; M6b was run only with T1's test). With
T1's test added, 11 of 11.

## Findings
- **T1** INV-49 says "the sweep removes only this artifact's day-old scratch". No test fails when the
  glob drops the artifact's name (M6: full suite 1782 passed). The clause predates this fix, but the
  fix puts `.writing`, a generic suffix, into that sweep and cites its test under INV-49. Written
  this review, RED on M6 and on M6b (`AssertionError: the sweep took another artifact's scratch`),
  GREEN at `dcc50a4` and on `a9b672a`, `ruff check`, `ruff format --check` and `black --check`
  clean. It was removed again so the worktree holds only this record; the author adds it to the
  branch and cites it under INV-49. Full text, as `tests/unit/test_sweep_only_this_artifact.py`:

```python
"""Tester, #146 (INV-49): the sweep removes only THIS artifact's day-old scratch."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest


def test_the_sweep_leaves_another_artifacts_day_old_scratch_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV-49: "the sweep removes only this artifact's day-old scratch". `.writing` is a generic
    suffix, so a sweep that matched any artifact's name would take a neighbour's files too."""
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)
    old = time.time() - 2 * 86400
    neighbour = [
        live.parent / "other.db.refresh.json.dead.writing",
        live.parent / "other.db.dead.candidate-journal",
        live.parent / "other.db.dead.candidate",
    ]
    for path in neighbour:
        path.write_text("x", encoding="utf-8")
        os.utime(path, (old, old))

    refresh(live)
    assert all(p.exists() for p in neighbour), "the sweep took another artifact's scratch"
```

## Clean-up evidence
- Every mutant: original bytes written back, sha256 equal before and after
  (`refresh.py` 254654e1...eacf7, `security-invariants.md` 857e2812...4df3).
- `git hash-object` equals `HEAD:<path>` for `src/app/workflows/refresh.py` (77e0d865) and
  `docs/security-invariants.md` (24c5dabc). T1's test file deleted. No checkout, restore, stash,
  reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's test, `tests/unit/test_sweep_only_this_artifact.py`, committed and cited under INV-49; the seat's M6 shown red by the author too |
