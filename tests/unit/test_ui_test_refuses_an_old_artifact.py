"""Tester, #139: the triage's "Done when a test that plants an old artifact sees the refusal"."""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from .test_ui_test_script import _layout


@pytest.mark.needs("bash_curl")
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
