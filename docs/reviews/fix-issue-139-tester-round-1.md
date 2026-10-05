---
record_type: review
id: fix-issue-139-tester-round-1
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 139 independent Tester review

**Reviewer:** Tester, a separate session; wrote none of the fix or its test.
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 3426626..fc869ae (`2aebd3d` red test, `fc869ae` fix), branch
`fix/issue-139-ui-test-served-artifact`.
**Risk tier:** LOW (a developer script; it decides which data a UI test runs on).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `3426626`. The
acceptance criterion is the triage comment: "Changes: `scripts/ui_test.sh` prefers the service's
artifact, or refuses one without the refinement boards. Stays: `MODEL_RANKING_DB` still overrides.
Done when a test that plants an old artifact sees the refusal." The issue body says the same: the
service's artifact when it exists, "Otherwise it refuses an artifact that lacks the refinement
boards, with a message naming the command that builds one". Red: the tree of `2aebd3d` extracted
with `git archive` (its `scripts/ui_test.sh` is byte-identical to the base) and run with this
worktree's venv. Gate: `make check-fast` at the head. Faults: one exact unique replacement per
mutant in `scripts/ui_test.sh`, the full suite run (`pytest -n auto`, artifact required), the
original bytes written back and the sha256 compared. `make ui-test` and a real `xcodebuild` were
never run; nothing reached the network.

## Verdict
BLOCKING

The half that prefers the service's artifact is correct and well proven: 8 of 9 mutants killed, red
to green shown. The half the triage makes the done-condition, the refusal of an old artifact, is
neither implemented nor tested. The test is written below (T1) and is RED at `fc869ae`. Production
code is the author's to change; this seat does not.

## Acceptance-criterion coverage
- Prefers the service's artifact when it exists:
  `tests/unit/test_ui_test_script.py:59` (`test_ui_test_starts_from_the_served_artifact_when_there_is_one`).
  RED on `2aebd3d`: `assert "the checkout's copy" == 'the served artifact'`. GREEN at `fc869ae`.
- `MODEL_RANKING_DB` still overrides, even with a served artifact present, and the checkout's copy is
  the fallback: `tests/unit/test_ui_test_script.py:64`. GREEN on both commits, as the red commit's
  message says. Q1, Q2, Q4, Q5 and Q7 show it bites.
- Refuses an artifact without the refinement boards; a test plants an old artifact and sees the
  refusal: MISSING. No refusal exists in `scripts/ui_test.sh` (`:18-21` choose a path, `:27` checks
  only that the file exists). T1.
- The scratch HOME: each test runs the script with a whole new environment
  (`tests/unit/test_ui_test_script.py:47-48`): `HOME` under `tmp_path`, `PATH` with a stub
  `xcodebuild` that exits 1 first, a free loopback port, `UI_TEST_OUT` under `tmp_path`. The script
  stops at `scripts/ui_test.sh:56` ("the build failed") before any engine starts. The served path is joined to the
  scratch HOME (`:21`, `:41-42`). Nothing under the owner's `~/Library/Application Support` is read.
- The path the script names is the one the service serves: `scripts/install_engine_service.sh:24-25`
  and `:72` give `$HOME/Library/Application Support/model-ranking/engine/data/advisor.db`, the same
  as `scripts/ui_test.sh:17` (see R1).

## Suite result
- `make check-fast` at `fc869ae`: PASS, six legs; test leg 1783 passed, 25 skipped.

## Mutants

| ID | Fault in `scripts/ui_test.sh` | Result | Killed by |
|---|---|---|---|
| Q1 | precedence swapped: the served artifact before `MODEL_RANKING_DB` | KILLED | `:64` |
| Q2 | `MODEL_RANKING_DB` ignored | KILLED | `:64` |
| Q3 | served path misspelt (`engine/advisor.db`) | KILLED | `:59` |
| Q4 | the served artifact chosen even when absent | KILLED | `:64` |
| Q5 | the checkout fallback points elsewhere | KILLED | `:64` |
| Q6 | the copy always takes the checkout's file | KILLED | `:59`, `:64` |
| Q7 | the `MODEL_RANKING_DB` test inverted (`-z`) | KILLED | `:59`, `:64` |
| Q8 | the line naming the copied artifact removed | SURVIVED (not in the criterion) | none |
| Q9 | served only when it is a directory | KILLED | `:59` |

8 of 9 killed. Q8's line is the commit's own addition, not the issue's; no test is asked for it.
No mutant can stand in for the refusal: there is no refusal code to break (T1).

## Findings
- **T1** BLOCKING. The triage's done-condition, "a test that plants an old artifact sees the
  refusal", is unmet: the script has no refusal and the branch no such test. Written this review and
  RED at `fc869ae`: with no served artifact, an old artifact in the checkout (Arena's text board, none
  of its slices) is copied and the script goes on to the build
  (`AssertionError: the old artifact was taken: the script went on to build`). `ruff check` clean.
  Removed again so the worktree holds only this record. The author implements the refusal, adopts
  this test (the message wording and the exit status may follow the script's own refusals, which
  exit 2), and makes it GREEN. The message must name the command that builds an artifact, per the
  issue body. Full text, as `tests/unit/test_ui_test_refuses_an_old_artifact.py`:

```python
"""Tester, #139: the triage's "Done when a test that plants an old artifact sees the refusal"."""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from .test_ui_test_script import _layout


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("curl") is None, reason="needs bash and curl")
def test_ui_test_refuses_an_artifact_without_the_refinement_boards(tmp_path: Path) -> None:
    """#139: with no served artifact, `make ui-test` "refuses an artifact that lacks the refinement
    boards, with a message naming the command that builds one". The planted artifact is the shape of
    the owner's 2026-09-24 copy: Arena's text board, none of its slices."""
    env = _layout(tmp_path, served=False)
    old = tmp_path / "repo" / "advisor.db"
    old.unlink()
    with sqlite3.connect(old) as db:
        db.execute("CREATE TABLE scores (model_id TEXT, benchmark TEXT, score REAL)")
        db.execute("INSERT INTO scores VALUES ('m', 'Arena text', 1.0)")
    db.close()
    run = subprocess.run(["bash", str(tmp_path / "repo" / "scripts" / "ui_test.sh")], env=env,
                         capture_output=True, text=True, timeout=60, check=False)
    out = run.stdout + run.stderr
    assert "the build failed" not in out, "the old artifact was taken: the script went on to build"
    assert run.returncode == 2, out
    assert "refinement" in out, out
    assert not (tmp_path / "out" / "advisor.db").exists(), "the old artifact was copied for the engine"
```

- **R1** The served artifact's path is kept by hand in three places: the installer
  (`scripts/install_engine_service.sh:24-25`, `:72`), the script (`scripts/ui_test.sh:17`) and the
  test (`tests/unit/test_ui_test_script.py:21`). Q3 dies only because the test repeats the script's
  literal. If the service's data directory moves, the installer's own tests
  (`tests/unit/test_engine_service.py:36`) move with it, and `make ui-test` quietly falls back to the
  checkout's copy: the defect this issue exists for. AGENTS.md section 3.5 asks for one source or a
  gate comparing them; the cheapest is the test reading the installer's path.
- **R2** Once the refusal exists, `tests/unit/test_ui_test_script.py:38` plants a text file as the
  checkout's artifact, and the fallback test (`:64`) will be refused. It must plant an artifact that
  carries the refinement boards.

## Clean-up evidence
- Every mutant: original bytes written back, sha256 equal before and after (`scripts/ui_test.sh`
  f0cbbb81...db2367).
- `git hash-object` equals `HEAD:<path>` for `scripts/ui_test.sh` (512ab0ec) and
  `tests/unit/test_ui_test_script.py` (098b32f0). T1's test file deleted. No checkout, restore,
  stash, reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat. This record is round 1; a new seat
reads the fix.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's test committed red (`8fcd299`), then the refusal (`521d4c6`) |
| R1 | fixed `521d4c6`: a test reads the served path from the installer and holds the script and the tests to it |
| R2 | fixed `521d4c6`: the script's tests plant real artifacts and run the suite's own interpreter for the check |
