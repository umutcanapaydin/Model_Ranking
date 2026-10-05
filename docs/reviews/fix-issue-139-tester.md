---
record_type: review
id: fix-issue-139-tester
status: ratified
seat: independent
process_version: v6.6
date: 2026-10-05
---
# Issue 139 independent Tester review

**Reviewer:** Tester, a new separate session; wrote none of the fix or its tests, and is not the
seat of round 1 (`docs/reviews/fix-issue-139-tester-round-1.md`).
**Independent:** yes
**Date:** 2026-10-05
**Commit range:** 3426626..6ce92ce (`2aebd3d` red, `fc869ae` fix, `8fcd299` round 1's test red,
`521d4c6` the refusal with round 1's R1 and R2, `6ce92ce` round 1's record), branch
`fix/issue-139-ui-test-served-artifact`. This record is the verdict of record.
**Risk tier:** LOW (a developer script; it decides which data a UI test runs on).

**Method.** Profile, `AGENTS.md` and `.agents/rules/issues.md` read from the base `3426626`. The
acceptance criterion is the triage comment: "`scripts/ui_test.sh` prefers the service's artifact, or
refuses one without the refinement boards. Stays: `MODEL_RANKING_DB` still overrides. Done when a
test that plants an old artifact sees the refusal", with the body's "with a message naming the
command that builds one". Red: the tree of `8fcd299` extracted with `git archive` (its
`scripts/ui_test.sh` is the one of `fc869ae`; the commit adds only the test) and run with this
worktree's venv. Gate: `make check-fast` at the head. Faults: one exact unique replacement per
mutant (`scripts/ui_test.sh`, one in `scripts/install_engine_service.sh`), the whole suite run
(`pytest -n auto`, artifact required), the original bytes written back and the sha256 compared; the
survivors run again with the tests written here. Every test of the script replaces the whole
environment (`tests/unit/test_ui_test_script.py:47-64`): `HOME` under `tmp_path`, `PATH` led by a
stub `xcodebuild` that exits 1, a free loopback port from the OS, `UI_TEST_OUT` under `tmp_path`.
The script stops at "the build failed" (`scripts/ui_test.sh:77`) before any engine starts. `make
ui-test`, a real `xcodebuild`, the simulator and the owner's `~/Library/Application Support` were
never touched; nothing reached the network.

## Verdict
MINOR

The fix does what the issue asks: the service's artifact is preferred, `MODEL_RANKING_DB` still
overrides, and an artifact without the refinement boards is refused with exit 2, before the copy,
with a message naming the refresh command. Round 1's T1, R1 and R2 are closed. But the committed
refusal test reaches the refusal through the check's error path, not through a missing slice: 4 of
17 mutants survive the suite, among them a check that says `ok` whenever its query runs (T1), the
command dropped from the message (T2), and a check that reads the checkout's copy instead of the
artifact the engine starts from (T3). Three tests are written below; with them, 17 of 17.

## Acceptance-criterion coverage
- Prefers the service's artifact when it exists: `tests/unit/test_ui_test_script.py:78`. GREEN at the
  head; Q14, Q17 killed. In the issue's own case (an old checkout copy beside a current served one)
  only T3's test.
- `MODEL_RANKING_DB` still overrides, over a served artifact too; the checkout's copy is the fallback:
  `tests/unit/test_ui_test_script.py:83`. Q16 killed.
- Refuses an artifact without the refinement boards; a test plants an old artifact and sees the
  refusal: `tests/unit/test_ui_test_refuses_an_old_artifact.py:16`. RED on `8fcd299`
  (`AssertionError: the old artifact was taken: the script went on to build`), GREEN at `6ce92ce`;
  the test file is unchanged between the two. Q4, Q5, Q6, Q11 killed; Q1, Q2 survive (T1).
- The message names the command that builds one: no test (T2).
- The served path is the installer's (round 1's R1): `tests/unit/test_ui_test_script.py:93` reads
  `BASE`, `DEPLOY` and `MODEL_RANKING_DB` out of `scripts/install_engine_service.sh:24-25`, `:72`.
  Q14, Q15 killed.

## Suite result
- `make check-fast` at `6ce92ce`: PASS, six legs; test leg 1785 passed, 25 skipped.
- The three tests written here: 3 passed at the head; `ruff check` clean. On the tree of `8fcd299`
  (before the refusal) the two refusal tests are RED.

## Mutants

| ID | Fault (in `scripts/ui_test.sh` unless named) | Suite as committed | With the tests written here |
|---|---|---|---|
| Q1 | the check prints `ok` whenever its query runs | SURVIVED | KILLED (T1, T2 tests) |
| Q2 | the check tests the cursor, not a row (`ok` whenever the query runs) | SURVIVED | KILLED (T1, T2 tests) |
| Q3 | the check prints `ok` before it opens anything | KILLED (`refuses_an_old_artifact.py:16`, `test_ui_test_script.py:78`, `:83`) | not run |
| Q4 | the refusal exits 0 | KILLED (`refuses_an_old_artifact.py:16`) | not run |
| Q5 | the refusal only warns and goes on | KILLED (`refuses_an_old_artifact.py:16`) | not run |
| Q6 | the artifact copied before the check | KILLED (`refuses_an_old_artifact.py:16`) | not run |
| Q7 | wrong table (`pricing`) | KILLED (`test_ui_test_script.py:78`, `:83`) | not run |
| Q8 | wrong column (`benchmark`) | KILLED (`test_ui_test_script.py:78`, `:83`) | not run |
| Q9 | the board labels in place of the source ids | KILLED (`test_ui_test_script.py:78`, `:83`) | not run |
| Q10 | the lookup inverted (`NOT IN`) | KILLED (`test_ui_test_script.py:78`, `:83`) | not run |
| Q11 | an error in the check (no output) treated as a pass | KILLED (`refuses_an_old_artifact.py:16`) | not run |
| Q12 | the check reads the checkout's copy, not the chosen artifact | SURVIVED | KILLED (T3 test) |
| Q13 | the refusal no longer names the command that builds an artifact | SURVIVED | KILLED (T2 test) |
| Q14 | the served path misspelt in the script | KILLED (`test_ui_test_script.py:78`, `:93`) | not run |
| Q15 | `scripts/install_engine_service.sh`: the installer serves another path | KILLED (`test_ui_test_script.py:93`, `test_engine_service.py`) | not run |
| Q16 | precedence: the served artifact before `MODEL_RANKING_DB` | KILLED (`test_ui_test_script.py:83`) | not run |
| Q17 | the served artifact never preferred | KILLED (`test_ui_test_script.py:78`) | not run |

As committed, 13 of 17 killed; with the tests written here, 17 of 17.

## Findings
- **T1** The refusal test's old artifact is not the shape of an old artifact. Its `scores` table has
  no `source` column (`tests/unit/test_ui_test_refuses_an_old_artifact.py:24`), so the check's query
  fails (`no such column: source`), prints nothing, and the script refuses on the error path. The
  docstring calls it "the shape of the owner's 2026-09-24 copy", but every real artifact has a
  `source` column. A check that answers `ok` whenever its query runs (Q1, Q2) passes the whole suite
  and would take any old artifact. Written: `test_ui_test_refuses_an_old_artifact_of_the_real_schema`,
  an artifact built by `app.workflows.schema.connect` with Arena's text board (`arena`) and no slice.
  RED on Q1, Q2 and on the tree of `8fcd299`; GREEN at the head.
- **T2** The body's "with a message naming the command that builds one" has no test: the committed
  test asserts only "refinement" (`:32`), and with the command's line removed (Q13) the suite stays
  green. Written: `test_the_refusal_names_the_command_that_builds_a_current_artifact`. RED on Q1, Q2,
  Q13 and on the tree of `8fcd299`; GREEN at the head.
- **T3** The issue's own case has no test: the service serves a current artifact and the checkout
  holds the old copy. Every committed layout makes the checkout's copy current, so a check that reads
  `$REPO/advisor.db` instead of `$DB` (Q12) passes; on the owner's Mac it would refuse every `make
  ui-test`, and with `MODEL_RANKING_DB` naming an old artifact beside a current checkout it would take
  the old one. Written: `test_a_current_served_artifact_is_taken_over_an_old_checkout_copy`. RED on
  Q12; GREEN at the head.
- **R1** Author's call; no test asked. Any failure of the check is reported as an old artifact: the
  check's stderr goes to `/dev/null` (`scripts/ui_test.sh:32`) and the message says the file "is older
  than the screen". Probe, a text file planted as the checkout's artifact: exit 2 with "holds none of
  Arena's slice boards ... it is older than the screen". Refusing is right ("any doubt refuses"); the
  words are wrong for a file that is not a database, or for a venv that cannot import `app`.

The three tests, in one file the author adds to the branch (removed again here so the worktree holds
only this record). Full text, as `tests/unit/test_ui_test_refuses_a_real_old_artifact.py`:

```python
"""Tester round 2, #139: the refusal seen on an old artifact of the real schema, and the owner's Mac.

The committed refusal test plants a `scores` table with no `source` column, so the script's check
fails on its query and prints nothing: the refusal it sees is the error path, and a check that says
`ok` whenever its query runs passes it. Here the old artifact is built by the real schema
(`app.workflows.schema.connect`) and holds Arena's text board, `arena`, and none of its slices.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from app.workflows.schema import connect

from .test_ui_test_script import _chosen, _layout

NEEDS = pytest.mark.skipif(shutil.which("bash") is None or shutil.which("curl") is None,
                           reason="needs bash and curl")


def _old(path: Path) -> None:
    """The owner's 2026-09-24 copy in shape: the real schema, Arena's text board, no slice board."""
    path.unlink(missing_ok=True)
    db = connect(str(path))
    db.execute(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, source, source_url, observed_at)"
        " VALUES ('m', 'Arena text', 'elo', 1400.0, 'arena-crowd', 'arena', 'https://lmarena.ai', '2026-09-24')"
    )
    db.commit()
    db.close()


def _refused(tmp_path: Path) -> str:
    env = _layout(tmp_path, served=False)
    _old(tmp_path / "repo" / "advisor.db")
    run = subprocess.run(["bash", str(tmp_path / "repo" / "scripts" / "ui_test.sh")], env=env,
                         capture_output=True, text=True, timeout=60, check=False)
    out = run.stdout + run.stderr
    assert "the build failed" not in out, "the old artifact was taken: the script went on to build"
    assert run.returncode == 2, out
    assert not (tmp_path / "out" / "advisor.db").exists(), "the old artifact was copied for the engine"
    return out


@NEEDS
def test_ui_test_refuses_an_old_artifact_of_the_real_schema(tmp_path: Path) -> None:
    """#139 triage: "Done when a test that plants an old artifact sees the refusal"."""
    assert "refinement" in _refused(tmp_path)


@NEEDS
def test_the_refusal_names_the_command_that_builds_a_current_artifact(tmp_path: Path) -> None:
    """#139 body: it refuses "with a message naming the command that builds one"."""
    out = _refused(tmp_path)
    db = str(tmp_path / "repo" / "advisor.db")
    assert f"python -m app.workflows.refresh --db {db} --fetch-epoch" in out, out


@NEEDS
def test_a_current_served_artifact_is_taken_over_an_old_checkout_copy(tmp_path: Path) -> None:
    """#139's own case, the owner's Mac: the service serves a current artifact and the checkout holds
    the 2026-09-24 copy. The script starts from the served one and refuses nothing."""
    env = _layout(tmp_path, served=True)
    _old(tmp_path / "repo" / "advisor.db")
    assert _chosen(tmp_path, env) == "the served artifact"
```

## Clean-up evidence
- Every mutant: the original bytes written back, sha256 equal before and after
  (`scripts/ui_test.sh` adfc2e60...56a6b, `scripts/install_engine_service.sh` 23500031...51203).
- `git hash-object` equals `HEAD:<path>` for `scripts/ui_test.sh` (40035ad8),
  `scripts/install_engine_service.sh` (a952d8d7), `tests/unit/test_ui_test_script.py` (e7da6fc7) and
  `tests/unit/test_ui_test_refuses_an_old_artifact.py` (e60b9a54). The written test file deleted. The
  red tree and the probe ran outside the worktree, in the session's scratch directory. No checkout,
  restore, stash, reset or commit. `git status --short` lists only this record.

## Dispositions, at the fix

Written by the author after the seat closed, not by the seat.

| finding | disposition |
|---|---|
| T1 | fixed: the seat's `test_ui_test_refuses_an_old_artifact_of_the_real_schema`, committed as written |
| T2 | fixed: the seat's `test_the_refusal_names_the_command_that_builds_a_current_artifact`, committed as written |
| T3 | fixed: the seat's `test_a_current_served_artifact_is_taken_over_an_old_checkout_copy`, committed as written |
| R1 | fixed: the refusal says "older than the screen" for an artifact without slice boards, and "could not read whether" for one the check cannot read; both exit 2 and name the build command. The author's `test_the_refusal_says_whether_the_artifact_is_old_or_unreadable` holds it |
