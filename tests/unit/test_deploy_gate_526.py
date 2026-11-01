"""#526 (D-234, the owner's ruling of 2026-11-01): the deploy gate refuses while its caller has any `GIT_*` set.

The release Tester's M11: with `GIT_WORK_TREE` pointing at a clean checkout, `make deploy-check` and
`deploy_gate.py "fly deploy"` judged that checkout and passed over a product change. Each variable here points at the
repository being judged itself (or is harmless), so the only reason left to refuse is that it is set: git reads more
`GIT_*` variables than a list of the redirecting ones would keep up with.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from .test_deploy_gate_pin import GATE, Repo, _env, _installed


def _same_repo(repo: Repo) -> dict[str, str]:
    git = repo.root / ".git"
    return {
        "GIT_WORK_TREE": str(repo.root),
        "GIT_DIR": str(git),
        "GIT_INDEX_FILE": str(git / "index"),
        "GIT_OBJECT_DIRECTORY": str(git / "objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(git / "objects"),
        "GIT_CONFIG_COUNT": "0",
        "GIT_CONFIG_PARAMETERS": "",
        "GIT_EDITOR": "true",
        "GIT_NO_REPLACE_OBJECTS": "1",
    }


NAMES = ("GIT_WORK_TREE", "GIT_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
         "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_EDITOR", "GIT_NO_REPLACE_OBJECTS")


def _run(repo: Repo, argv: list[str], extra: dict[str, str], stdin: str | None = None) -> tuple[int, str]:
    done = subprocess.run([sys.executable, str(GATE), *argv], cwd=repo.root, capture_output=True, text=True,
                          input=stdin, env={**_env(), **extra}, timeout=120)
    return done.returncode, done.stdout + done.stderr


def test_the_reviewed_tree_passes_with_no_git_variable(tmp_path: Path) -> None:
    """The control: the tree every case below judges passes, so a refusal there is the variable's."""
    repo = _installed(tmp_path)
    assert _run(repo, ["--check"], {})[0] == 0
    assert _run(repo, ["fly deploy"], {})[0] == 0


@pytest.mark.parametrize("name", NAMES)
def test_deploy_check_fails_while_a_git_variable_is_set(tmp_path: Path, name: str) -> None:
    repo = _installed(tmp_path)
    code, out = _run(repo, ["--check"], {name: _same_repo(repo)[name]})
    assert code == 1, out
    assert name in out and "deploy-check FAIL" in out, out


@pytest.mark.parametrize("name", NAMES)
def test_a_deploy_is_refused_while_a_git_variable_is_set(tmp_path: Path, name: str) -> None:
    repo = _installed(tmp_path)
    extra = {name: _same_repo(repo)[name]}
    code, out = _run(repo, ["fly deploy"], extra)
    assert code == 2 and name in out, out
    code, out = _run(repo, ["--judge"], extra, json.dumps({"commands": [["fly", "deploy"]]}))
    assert code == 2 and name in out, out


def test_the_refusal_names_every_variable_and_how_to_clear_them(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    code, out = _run(repo, ["--check"], {"GIT_DIR": str(repo.root / ".git"), "GIT_EDITOR": "true"})
    assert code == 1, out
    assert "GIT_DIR" in out and "GIT_EDITOR" in out and "unset GIT_DIR GIT_EDITOR" in out, out


def test_a_command_that_is_not_a_deploy_is_not_refused_for_a_git_variable(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    assert _run(repo, ["ls -la"], {"GIT_DIR": str(repo.root / ".git")})[0] == 0
    payload = json.dumps({"commands": [["git", "status"]]})
    assert _run(repo, ["--judge"], {"GIT_DIR": str(repo.root / ".git")}, payload)[0] == 0
