"""Tester round 2, #139: the refusal seen on an old artifact of the real schema, and the owner's Mac.

The committed refusal test plants a `scores` table with no `source` column, so the script's check
fails on its query and prints nothing: the refusal it sees is the error path, and a check that says
`ok` whenever its query runs passes it. Here the old artifact is built by the real schema
(`app.workflows.schema.connect`) and holds Arena's text board, `arena`, and none of its slices.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.workflows.schema import connect

from .test_ui_test_script import _chosen, _layout

NEEDS = pytest.mark.needs("bash_curl")


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


@NEEDS
def test_the_refusal_says_whether_the_artifact_is_old_or_unreadable(tmp_path: Path) -> None:
    """The second fix Tester's R1: every failure of the check was said as "older than the screen".
    An artifact of the real schema without slice boards is old; a file the check cannot read is not
    an artifact this code reads. Both are refused, each said for what it is."""
    assert "older than the screen" in _refused(tmp_path)
    env = _layout(tmp_path / "unreadable", served=False)
    (tmp_path / "unreadable" / "repo" / "advisor.db").write_text("not a database", encoding="utf-8")
    run = subprocess.run(["bash", str(tmp_path / "unreadable" / "repo" / "scripts" / "ui_test.sh")], env=env,
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 2 and "could not read whether" in run.stdout, run.stdout + run.stderr
