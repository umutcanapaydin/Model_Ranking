"""#304 (D-206 clause 5): rule L1 skips what git ignores AND does not track, and nothing else.

L1 walked the working tree without the `.gitignore`-derived exclusion (`_ignored()`), so SwiftPM's
build output under `ios/.build/` failed it and #289 allowlisted the whole directory in
`.language-allow` -- an entry that also exempted any file a commit put there. The fix reads git's own
list of untracked ignored files, so the entry can go. Each test builds a real git repository: the
exclusion is git's, and a double of git would grade nothing.

Fail direction: a tracked file under an ignored path is still read; outside a work tree, or when git
cannot list the files, nothing is skipped (the old behaviour, noisier, never quieter)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.unit.test_language_rule_escapes import ROOT, _check_records

TURKISH = "bu satir Turkce bir harf tasiyor: \u015fey\n"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _flagged(root: Path) -> set[str]:
    return {f.path.as_posix() for f in _check_records().language_rule(root) if f.rule == "L1"}


def _repo(tmp_path: Path) -> Path:
    """A work tree whose `.gitignore` ignores `out/`, holding Turkish in three places."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text("out/\n", encoding="utf-8")
    (repo / "out").mkdir()
    (repo / "out" / "built.md").write_text(TURKISH, encoding="utf-8")  # ignored, untracked
    (repo / "out" / "kept.md").write_text(TURKISH, encoding="utf-8")  # ignored, TRACKED
    (repo / "loose.md").write_text(TURKISH, encoding="utf-8")  # untracked, not ignored
    _git(repo, "add", ".gitignore")
    _git(repo, "add", "-f", "out/kept.md")
    return repo


def test_an_untracked_ignored_file_is_not_read(tmp_path: Path) -> None:
    flagged = _flagged(_repo(tmp_path))
    assert "out/built.md" not in flagged, flagged


def test_a_tracked_file_under_an_ignored_directory_is_still_read(tmp_path: Path) -> None:
    flagged = _flagged(_repo(tmp_path))
    assert "out/kept.md" in flagged, flagged


def test_an_untracked_file_git_does_not_ignore_is_still_read(tmp_path: Path) -> None:
    flagged = _flagged(_repo(tmp_path))
    assert "loose.md" in flagged, flagged


def test_outside_a_git_work_tree_everything_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plain = tmp_path / "plain"
    (plain / "out").mkdir(parents=True)
    (plain / ".gitignore").write_text("out/\n", encoding="utf-8")
    (plain / "out" / "built.md").write_text(TURKISH, encoding="utf-8")
    # No repository above it either, wherever the temporary directory happens to live.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert "out/built.md" in _flagged(plain)


def test_when_git_is_not_installed_everything_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    empty = tmp_path / "no-git-here"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    assert "out/built.md" in _flagged(repo)


def test_when_git_errors_everything_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    # A git that cannot read the repository (a broken index) exits non-zero.
    (repo / ".git" / "index").write_bytes(b"not an index")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    assert "out/built.md" in _flagged(repo)


def test_the_ios_build_entry_has_left_the_allowlist() -> None:
    entries = [
        ln.split("#")[0].strip()
        for ln in (ROOT / ".language-allow").read_text(encoding="utf-8").splitlines()
    ]
    assert not any(
        e.startswith("ios/.build") for e in entries
    ), "the ios/.build/ entry is still in .language-allow"
