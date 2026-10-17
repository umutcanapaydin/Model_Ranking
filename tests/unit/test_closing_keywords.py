"""#255 (D-206 clause 6): `make closing-keywords RANGE=A..B` lists every issue the commit messages in a range
would close when they reach the default branch.

GitHub closes an issue that a closing keyword directly precedes in a commit message on the default branch,
whatever the pull request's body says, and `gh pr view --json closingIssuesReferences` reads only the body
and the manual links. So `fix: #194's model names ...` (35a8563) closed #194 with the PR's field empty, and
#222 went the same way seconds later (26a334a). The keyword set is GitHub's: close, closes, closed, fix,
fixes, fixed, resolve, resolves, resolved, in any case, with or without a colon, before `#N`,
`owner/repo#N` or an issue URL.

The target is advisory (not a leg of `make check`): it exits 1 when it finds any, 0 when it finds none, and
2 when the range is empty or cannot be read -- a range with no commits behind it graded nothing.

The shapes are judged by the script's own parser; the exit codes, the planted history and the fail-closed
paths through the script itself, in a repository each test builds.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "closing_keywords.py"


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("closing_keywords", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=f", "-c", "user.email=f@x", "-c", "commit.gpgsign=false", *args],
        cwd=root, capture_output=True, text=True, check=True, env=_env())
    return done.stdout.strip()


def _commit(root: Path, message: str) -> str:
    (root / "f.txt").write_text(message, encoding="utf-8")
    _git(root, "add", "f.txt")
    _git(root, "commit", "-q", "--allow-empty", "-m", message)
    return _git(root, "rev-parse", "--short", "HEAD")


def _repo(root: Path) -> Path:
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "base")
    return root


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", check=False, env=_env())


# --- the keyword shapes ------------------------------------------------------------------------------------

@pytest.mark.parametrize("keyword", ["close", "closes", "closed", "fix", "fixes", "fixed",
                                     "resolve", "resolves", "resolved"])
def test_every_github_closing_keyword_closes(keyword: str) -> None:
    assert _module().closed_by(f"docs: something\n\n{keyword} #12") == ["#12"]


@pytest.mark.parametrize("message", ["FIXES #12", "Closes #12", "rEsOlVeD #12"])
def test_the_keyword_closes_in_any_case(message: str) -> None:
    assert _module().closed_by(message) == ["#12"]


@pytest.mark.parametrize("message", ["Fixes: #12", "closes:#12", "Resolved:  #12"])
def test_the_keyword_closes_with_a_colon(message: str) -> None:
    assert _module().closed_by(message) == ["#12"]


def test_a_conventional_commit_subject_naming_the_issue_closes_it() -> None:
    """The shape that closed #194 and #222: `fix: #N's ...` reads as `fix #N`."""
    subject = "fix: #194's model names in the fact doubt and #218's Turkish signals"
    assert _module().closed_by(subject) == ["#194"]


def test_another_repositorys_issue_closes_as_owner_repo_number() -> None:
    assert _module().closed_by("fixes octo-org/some.repo#7") == ["octo-org/some.repo#7"]


def test_an_issue_url_after_the_keyword_closes() -> None:
    assert _module().closed_by("resolves https://github.com/octo/repo/issues/7") == ["octo/repo#7"]


def test_the_keyword_in_a_body_line_closes() -> None:
    assert _module().closed_by("feat: a thing\n\nSome prose.\nCloses #12.\n") == ["#12"]


def test_every_keyword_in_one_message_is_listed_once() -> None:
    assert _module().closed_by("fix #1 and closes #2; fixed #1 again") == ["#1", "#2"]


def test_only_the_reference_right_after_the_keyword_closes() -> None:
    """GitHub links one reference per keyword: `Closes #1, #2` closes #1 alone."""
    assert _module().closed_by("Closes #1, #2") == ["#1"]


# --- what must stay quiet ----------------------------------------------------------------------------------

@pytest.mark.parametrize("message", [
    "docs: for #255, the advisory target",
    "see #12 and #13",
    "ref #12",
    "the fix for #12 lands later",
    "prefixes #12",
    "unfixed #12",
    "a closing #12 note",
    "please leave #12 open",
    "fix: the gate (#12)",
    "fixes repo#12",
    "fixes #",
])
def test_a_message_that_only_mentions_an_issue_closes_nothing(message: str) -> None:
    assert _module().closed_by(message) == []


# --- the range, through the script ---------------------------------------------------------------------------

def test_a_planted_closing_commit_is_listed_and_exits_one(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _commit(root, "docs: for #40, a note")
    sha = _commit(root, "fix: #194's model names")
    _commit(root, "test: more\n\nResolves octo/repo#9")
    done = _run(root, "--range", "HEAD~3..HEAD")
    assert done.returncode == 1, done.stdout + done.stderr
    lines = done.stdout.strip().splitlines()
    assert lines[-1] == "closing-keywords: #194 octo/repo#9"
    assert any(line.startswith("#194") and sha in line for line in lines)
    assert not any("#40" in line for line in lines)


def test_a_clean_range_exits_zero_and_names_what_it_read(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _commit(root, "docs: for #40, a note")
    _commit(root, "test: see #41 -- red")
    done = _run(root, "--range", "HEAD~2..HEAD")
    assert done.returncode == 0, done.stdout + done.stderr
    assert done.stdout.strip().splitlines()[-1] == "closing-keywords: none"
    assert re.search(r"range: HEAD~2\.\.HEAD \([0-9a-f]{7,}\.\.[0-9a-f]{7,}\), 2 commits", done.stdout)


def test_a_merge_commits_own_message_is_read(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    _git(root, "checkout", "-q", "-b", "side")
    _commit(root, "docs: side work")
    _git(root, "checkout", "-q", "main")
    _commit(root, "docs: main work")
    _git(root, "merge", "-q", "--no-ff", "side", "-m", "Merge side; closes #77")
    done = _run(root, "--range", "HEAD~1..HEAD")
    assert done.returncode == 1, done.stdout + done.stderr
    assert done.stdout.strip().splitlines()[-1] == "closing-keywords: #77"


# --- fail closed --------------------------------------------------------------------------------------------

def test_an_empty_range_is_an_error_never_a_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    done = _run(root, "--range", "HEAD..HEAD")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "no commits" in done.stdout + done.stderr


def test_an_unreadable_range_is_an_error_never_a_pass(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    done = _run(root, "--range", "no-such-ref..HEAD")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "cannot read" in done.stdout + done.stderr


def test_a_range_that_is_not_a_range_is_an_error(tmp_path: Path) -> None:
    """`HEAD` alone would read the whole history, which no merge brings in."""
    root = _repo(tmp_path)
    done = _run(root, "--range", "HEAD")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "not a range" in done.stdout + done.stderr


def test_no_range_given_is_an_error(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    done = _run(root)
    assert done.returncode == 2, done.stdout + done.stderr
    assert "no range given" in done.stdout + done.stderr


def test_outside_a_repository_is_an_error(tmp_path: Path) -> None:
    done = _run(tmp_path, "--range", "HEAD~1..HEAD")
    assert done.returncode == 2, done.stdout + done.stderr
    assert "cannot read" in done.stdout + done.stderr


# --- the make target ----------------------------------------------------------------------------------------

def test_the_make_target_runs_the_script_with_the_range_and_is_phony() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    phony = re.search(r"^\.PHONY:(.*)$", makefile, re.M)
    assert phony is not None and "closing-keywords" in phony.group(1).split()
    assert re.search(r"^closing-keywords:[^\n]*## ", makefile, re.M), "the target has no help annotation"
    done = subprocess.run(["make", "-n", "closing-keywords", "RANGE=A..B"], cwd=ROOT, capture_output=True,
                          text=True, check=False)
    assert "scripts/closing_keywords.py --range A..B" in done.stdout, done.stdout + done.stderr


def test_the_make_target_is_advisory_not_a_leg_of_check() -> None:
    """D-206 clause 6."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for leg in ("check", "check-fast", "gate"):
        rule = re.search(rf"^{leg}:([^#\n]*)", makefile, re.M)
        assert rule is not None
        assert "closing-keywords" not in rule.group(1).split()
