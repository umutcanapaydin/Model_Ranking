"""#264: `make install` refuses a venv another tree owns.

An agent's worktrees once had `.venv` as a symlink to the main clone's. `make install` in one of
them ran `pip install -e .` through the link, which rewrote the main venv's editable path to the
worktree; when the worktree was deleted, the main clone's venv imported nothing from `app`, and the
owner's deploy stopped. The same link made a worktree's tests import the main clone's code.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _owner() -> ModuleType:  # loaded lazily, so this file collects before the script exists
    spec = importlib.util.spec_from_file_location("venv_owner", ROOT / "scripts" / "venv_owner.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _venv(path: Path, editable_url: str | None = None) -> Path:
    site = path / "lib" / "python3.12" / "site-packages"
    site.mkdir(parents=True)
    (path / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    if editable_url is not None:
        info = site / "model_ranking-0.1.0.dist-info"
        info.mkdir()
        (info / "direct_url.json").write_text(json.dumps({"dir_info": {"editable": True}, "url": editable_url}),
                                              encoding="utf-8")
    return path


def test_a_tree_with_no_venv_or_its_own_venv_passes(tmp_path: Path) -> None:
    tree = tmp_path / "tree"
    tree.mkdir()
    assert _owner().problems(tree, tree / ".venv") == []
    _venv(tree / ".venv", (tree.resolve()).as_uri())
    assert _owner().problems(tree, tree / ".venv") == []


def test_a_venv_that_is_a_link_is_refused(tmp_path: Path) -> None:
    """The owner's case: the worktree's `.venv` was a link to the main clone's."""
    main, worktree = tmp_path / "main", tmp_path / "worktree"
    _venv(main / ".venv", main.resolve().as_uri())
    worktree.mkdir()
    (worktree / ".venv").symlink_to(main / ".venv")
    problems = _owner().problems(worktree, worktree / ".venv")
    assert problems and "link" in problems[0], problems


def test_a_venv_whose_editable_install_names_another_tree_is_refused(tmp_path: Path) -> None:
    """A copied or moved venv: installing into it again would still be safe, but its tests import
    another tree's code until then, so it is refused and named."""
    other, tree = tmp_path / "other", tmp_path / "tree"
    other.mkdir()
    _venv(tree / ".venv", other.resolve().as_uri())
    problems = _owner().problems(tree, tree / ".venv")
    assert problems and str(other.resolve()) in problems[0], problems


def test_the_cli_exits_non_zero_with_the_reason(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main, worktree = tmp_path / "main", tmp_path / "worktree"
    _venv(main / ".venv")
    worktree.mkdir()
    (worktree / ".venv").symlink_to(main / ".venv")
    assert _owner().main([str(worktree / ".venv"), "--tree", str(worktree)]) == 1
    assert "#264" in capsys.readouterr().err


def test_make_install_checks_the_venv_before_pip_writes_into_it() -> None:
    """The check runs in the recipe that installs, ahead of both pip commands."""
    recipe = re.search(r"^\$\(VENV\)/\.installed:.*?\n((?:\t.*\n)+)", (ROOT / "Makefile").read_text(encoding="utf-8"),
                       re.MULTILINE)
    assert recipe is not None
    lines = recipe.group(1).splitlines()
    assert "scripts/venv_owner.py" in lines[0], lines
    assert sum("$(PIP) install" in line for line in lines[1:]) == 2, lines


def test_a_windows_editable_url_keeps_its_drive_letter() -> None:
    """Round 2's M2: pip writes `file:///C:/...` on Windows; read without the drive, every reinstall was refused."""
    assert _owner().editable_path("file:///C:/Users/owner/model_ranking") == Path("C:/Users/owner/model_ranking")
    assert _owner().editable_path("file:///Users/owner/model%20ranking") == Path("/Users/owner/model ranking")


def test_the_same_tree_reached_by_a_path_in_another_case_is_its_own(tmp_path: Path) -> None:
    """Round 2's M2: on the owner's Mac the file system ignores case, and the check told them to remove a venv
    the tree owned."""
    tree = tmp_path / "Tree"
    tree.mkdir()
    other_case = tmp_path / "TREE"
    if not other_case.exists():
        pytest.skip("this file system tells the cases apart")
    _venv(tree / ".venv", tree.resolve().as_uri())
    assert _owner().problems(other_case, other_case / ".venv") == []


def test_every_make_install_checks_the_venv_not_only_the_one_that_installs() -> None:
    """Round 2's R1: a worktree linked to another tree's venv runs its tests on that tree's code, so the check
    runs on every `make install` (the prerequisite of `make test`), not only when pip runs."""
    recipe = re.search(r"^install:.*?\n((?:\t.*\n)+)", (ROOT / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    assert recipe is not None
    assert "scripts/venv_owner.py" in recipe.group(1).splitlines()[0], recipe.group(1)
