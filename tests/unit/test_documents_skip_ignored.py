"""#325: `conformance/lib_record.documents()` grades the documents a clone ships, not scratch git ignores.

A gitignored, untracked `build/x.md` with a dangling reference turned `make check` red, while the files the
references resolve against already came from git. An ignored file is not graded; a tracked one under the same
ignore rule is, and so is an untracked one nothing ignores. Without git the walk stays whole (noisier, never
quieter).
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _lib() -> ModuleType:
    spec = importlib.util.spec_from_file_location("lib_record_325", ROOT / "conformance" / "lib_record.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", *args], cwd=root, check=True,
                   capture_output=True, env=env)


def _tree(root: Path) -> None:
    (root / "build").mkdir()
    (root / ".gitignore").write_text("build/\n", encoding="utf-8")
    (root / "README.md").write_text("see `docs/a.md`\n", encoding="utf-8")
    (root / "build" / "tracked.md").write_text("tracked under an ignore rule\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", ".gitignore", "README.md")
    _git(root, "add", "-f", "build/tracked.md")
    _git(root, "commit", "-qm", "base")
    (root / "build" / "scratch.md").write_text("see `docs/nothing-here.md`\n", encoding="utf-8")
    (root / "notes.md").write_text("an untracked note nothing ignores\n", encoding="utf-8")


def test_an_ignored_untracked_document_is_not_graded_and_the_rest_are(tmp_path: Path) -> None:
    _tree(tmp_path)
    found = {p.relative_to(tmp_path).as_posix() for p in _lib().documents(tmp_path)}
    assert "build/scratch.md" not in found
    assert {"README.md", "build/tracked.md", "notes.md"} <= found


def test_without_git_every_document_is_graded(tmp_path: Path) -> None:
    (tmp_path / "build").mkdir()
    (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")
    (tmp_path / "build" / "scratch.md").write_text("x\n", encoding="utf-8")
    found = {p.relative_to(tmp_path).as_posix() for p in _lib().documents(tmp_path)}
    assert "build/scratch.md" in found
