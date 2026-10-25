"""#139, D-222: `make ui-test` starts its engine from a copy of the artifact MODEL_RANKING_DB names, else
the checkout's `advisor.db` (D-175).

It once preferred the artifact the Mac's engine service served; that service is retired (#427), so its
folder is no longer read. An artifact older than the screen is refused instead (#139). Each test runs a copy of `scripts/ui_test.sh` in a scratch layout of the repository,
with a stub `xcodebuild` that fails at once: the script stops after copying the artifact it chose,
and no build, simulator or engine is ever started.
"""

from __future__ import annotations

import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
#: Where the retired Mac service kept its artifact (D-222): planted to show it is no longer read.
SERVED = Path("Library/Application Support/model-ranking/engine/data/advisor.db")


def _artifact(path: Path, name: str) -> None:
    """Enough of an artifact for the script's check (#139): a row of a declared Arena slice, and a
    mark that says which artifact the engine would have started from."""
    from app.workflows.board_tables import ARENA_SLICES

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE scores (model_id TEXT, source TEXT, score REAL)")
        db.execute("INSERT INTO scores VALUES ('m', ?, 1.0)", (ARENA_SLICES[0].source_name,))
        db.execute("CREATE TABLE mark (name TEXT)")
        db.execute("INSERT INTO mark VALUES (?)", (name,))
    db.close()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _layout(tmp_path: Path, *, served: bool) -> dict[str, str]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "ui_test.sh", repo / "scripts" / "ui_test.sh")
    python = repo / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")  # this suite's own
    python.chmod(0o755)
    _artifact(repo / "advisor.db", "the checkout's copy")
    home = tmp_path / "home"
    if served:
        _artifact(home / SERVED, "the served artifact")
    stubs = tmp_path / "bin"
    stubs.mkdir()
    (stubs / "xcodebuild").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (stubs / "xcodebuild").chmod(0o755)
    return {"PATH": f"{stubs}:/usr/bin:/bin", "HOME": str(home), "UI_TEST_PORT": str(_free_port()),
            "UI_TEST_OUT": str(tmp_path / "out")}


def _chosen(tmp_path: Path, env: dict[str, str]) -> str:
    run = subprocess.run(["bash", str(tmp_path / "repo" / "scripts" / "ui_test.sh")], env=env,
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 1 and "the build failed" in run.stdout, run.stdout + run.stderr
    with sqlite3.connect(tmp_path / "out" / "advisor.db") as db:
        (name,) = db.execute("SELECT name FROM mark").fetchone()
    db.close()
    return str(name)


@pytest.mark.needs("bash_curl")
def test_ui_test_starts_from_the_checkout_and_reads_no_retired_service_folder(tmp_path: Path) -> None:
    """D-222 (#427): the Mac's service folder is no longer an engine's; a copy left there is not read."""
    assert _chosen(tmp_path, _layout(tmp_path, served=True)) == "the checkout's copy"
    assert _chosen(tmp_path / "bare", _layout(tmp_path / "bare", served=False)) == "the checkout's copy"


@pytest.mark.needs("bash_curl")
def test_ui_test_obeys_its_variable(tmp_path: Path) -> None:
    named = tmp_path / "named.db"
    _artifact(named, "the named artifact")
    env = {**_layout(tmp_path / "again", served=True), "MODEL_RANKING_DB": str(named)}
    assert _chosen(tmp_path / "again", env) == "the named artifact"
    assert os.environ.get("MODEL_RANKING_DB") != str(named)
