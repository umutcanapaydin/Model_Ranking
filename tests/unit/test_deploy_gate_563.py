"""#563 (the v7.3.1 upgrade's security delta, R13, dormant): `deploy_gate.ci_green` ran `gh run list` with no `-R`, so
`GH_REPO`, `GH_HOST` or `gh repo set-default` could point it at another repository's CI, and a green run there would
let a test-and-CI change pass without re-opening the verdicts. Now it names this repository, read from `origin`'s URL,
and drops `GH_REPO` and `GH_HOST` from `gh`'s environment; an origin it cannot read is not green.
# covers #563
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GREEN = '[{"status": "completed", "conclusion": "success"}]'


def _gate():
    spec = importlib.util.spec_from_file_location("deploy_gate_563", ROOT / "scripts" / "deploy_gate.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path, origin: str | None) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp_path), "PATH": "/usr/bin:/bin",
           "GIT_AUTHOR_NAME": "o", "GIT_AUTHOR_EMAIL": "o@x", "GIT_COMMITTER_NAME": "o", "GIT_COMMITTER_EMAIL": "o@x"}
    for args in (["init", "-q", "-b", "main"], ["commit", "-q", "--allow-empty", "-m", "one"]):
        subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)
    if origin:
        subprocess.run(["git", "remote", "add", "origin", origin], cwd=root, env=env, check=True, capture_output=True)
    return root


def _stub_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A `gh` first on PATH that records its arguments and `GH_REPO`, and answers green only for `-R github.com/o/r`:
    the CI of any other repository is never asked here."""
    bin_dir, log = tmp_path / "bin", tmp_path / "gh-calls.txt"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(
        "#!/bin/sh\n"
        f'echo "args=$* GH_REPO=${{GH_REPO:-unset}} GH_HOST=${{GH_HOST:-unset}}" >> "{log}"\n'
        'case " $* " in *" -R github.com/o/r "*) ' f"echo '{GREEN}' ;; *) echo '[]' ;; esac\n", encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")
    return log


@pytest.mark.parametrize("origin", ["https://github.com/o/r.git", "git@github.com:o/r.git", "https://github.com/o/r"])
def test_ci_green_asks_this_repository_whatever_gh_repo_says(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                             origin: str) -> None:
    """covers #563: with `GH_REPO` and `GH_HOST` pointing elsewhere, the call names origin's repository and carries
    neither variable."""
    log = _stub_gh(tmp_path, monkeypatch)
    monkeypatch.setenv("GH_REPO", "evil/other")
    monkeypatch.setenv("GH_HOST", "evil.example")
    assert _gate().ci_green(_repo(tmp_path, origin)) is True
    call = log.read_text(encoding="utf-8")
    assert "-R github.com/o/r" in call and "GH_REPO=unset" in call and "GH_HOST=unset" in call, call


def test_an_origin_it_cannot_read_is_not_green(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """covers #563: no origin, so no repository to name -- not green, and `gh` is not asked at all."""
    log = _stub_gh(tmp_path, monkeypatch)
    assert _gate().ci_green(_repo(tmp_path, None)) is False
    assert not log.exists()
