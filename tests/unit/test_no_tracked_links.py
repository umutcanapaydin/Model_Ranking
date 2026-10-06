"""M18-W3 review B1 and K1: no symbolic link is tracked.

A worktree's `.venv` link (to another tree's virtualenv) was committed, because `.venv/` in
`.gitignore` matches only a directory. Merged, it would replace a checkout's real `.venv/` with a
dangling link, and `git archive` would ship it into the engine's deploy, where `python -m venv`
then fails. The index is read directly, so the check holds wherever git is.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.needs("git")
def test_no_symbolic_link_is_tracked() -> None:
    index = subprocess.run(["git", "ls-files", "-s"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    links = [line.split("\t", 1)[1] for line in index.splitlines() if line.startswith("120000 ")]
    assert not links, f"tracked symbolic links: {links}"


def test_the_ignore_file_catches_a_venv_link_too() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".venv" in lines, "`.venv/` alone misses a link named .venv"
