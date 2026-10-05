"""#139: `make ui-test` starts its engine from a copy of the artifact the service serves (D-175).

It defaulted to the checkout's `advisor.db`, which on the owner's Mac was a copy from 2026-09-24,
older than the refinement boards, so the UI test drove the combined list on boards the phone no
longer gets. Each test runs a copy of `scripts/ui_test.sh` in a scratch layout of the repository,
with a stub `xcodebuild` that fails at once: the script stops after copying the artifact it chose,
and no build, simulator or engine is ever started.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SERVED = Path("Library/Application Support/model-ranking/engine/data/advisor.db")


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
    python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    python.chmod(0o755)
    (repo / "advisor.db").write_text("the checkout's copy", encoding="utf-8")
    home = tmp_path / "home"
    if served:
        (home / SERVED).parent.mkdir(parents=True)
        (home / SERVED).write_text("the served artifact", encoding="utf-8")
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
    return (tmp_path / "out" / "advisor.db").read_text(encoding="utf-8")


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("curl") is None, reason="needs bash and curl")
def test_ui_test_starts_from_the_served_artifact_when_there_is_one(tmp_path: Path) -> None:
    assert _chosen(tmp_path, _layout(tmp_path, served=True)) == "the served artifact"


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("curl") is None, reason="needs bash and curl")
def test_ui_test_falls_back_to_the_checkout_and_obeys_its_variable(tmp_path: Path) -> None:
    env = _layout(tmp_path, served=False)
    assert _chosen(tmp_path, env) == "the checkout's copy"
    named = tmp_path / "named.db"
    named.write_text("the named artifact", encoding="utf-8")
    env = {**_layout(tmp_path / "again", served=True), "MODEL_RANKING_DB": str(named)}
    assert _chosen(tmp_path / "again", env) == "the named artifact"
    assert os.environ.get("MODEL_RANKING_DB") != str(named)
