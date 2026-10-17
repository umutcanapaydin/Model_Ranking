"""#254: an amend that stages only docs onto a code commit was gated by `check-docs`.

`.githooks/commit-msg` reads the staged paths against the current `HEAD`, which during `git commit --amend` is the
commit being replaced, so it sees only the amend's own delta. `.githooks/post-rewrite` (git runs it with `amend`
after the amend is made) asks `scripts/commit_gate.py` again for the amended commit against its first parent, and
runs that target when commit-msg's run did not cover it. It cannot refuse the amend: it says so when the target
is red, and pre-push's `make gate` stops the push.

Every test goes through a real `git commit --amend` (or `git rebase`) in a repository of its own, with a stub
`make` that records what it was asked and fails `check-fast` when told to.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RED = "test: the thing fails, red -- #1 (M30-W1)"


def _repo(tmp_path: Path, fail: str = "") -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "repo"
    (repo / ".githooks").mkdir(parents=True)
    (repo / "scripts").mkdir()
    for hook in ("commit-msg", "post-rewrite"):
        shutil.copy(ROOT / ".githooks" / hook, repo / ".githooks" / hook)
    shutil.copy(ROOT / "scripts" / "commit_gate.py", repo / "scripts" / "commit_gate.py")
    log = tmp_path / "make.log"
    stub = tmp_path / "bin"
    stub.mkdir()
    refuse = f'[ "$1" = "{fail}" ] && exit 2\n' if fail else ""
    (stub / "make").write_text(f"#!/bin/sh\necho \"$*\" >> '{log}'\n{refuse}exit 0\n", encoding="utf-8")
    (stub / "make").chmod(0o755)
    env = {**os.environ, "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    env["GIT"] = shutil.which("git", path=os.environ["PATH"]) or "git"
    for args in (["init", "-q", "-b", "main"], ["config", "core.hooksPath", ".githooks"]):
        subprocess.run([env["GIT"], *args], cwd=repo, env=env, check=True, capture_output=True, timeout=30)
    # The scaffolding is the root commit, made without the hooks, so each test's log starts empty.
    for args in (["add", "-A"], ["commit", "-q", "--no-verify", "-m", "chore: scaffolding"]):
        subprocess.run([env["GIT"], *args], cwd=repo, env=env, check=True, capture_output=True, timeout=30)
    return repo, log, env


def _git(repo: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([env["GIT"], *args], cwd=repo, env=env, capture_output=True, text=True, timeout=60,
                          check=False)


def _write(repo: Path, path: str) -> None:
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    with (repo / path).open("a", encoding="utf-8") as handle:
        handle.write(f"{path}\n")


def _commit(repo: Path, env: dict[str, str], path: str, subject: str = "") -> subprocess.CompletedProcess[str]:
    _write(repo, path)
    _git(repo, env, "add", path)
    return _git(repo, env, "commit", "-q", "-m", subject or path)


def _amend(repo: Path, env: dict[str, str], path: str, *extra: str) -> subprocess.CompletedProcess[str]:
    _write(repo, path)
    _git(repo, env, "add", path)
    return _git(repo, env, "commit", "-q", "--amend", "--no-edit", *extra)


def _logged(log: Path) -> list[str]:
    return log.read_text(encoding="utf-8").split() if log.exists() else []


def test_a_docs_only_amend_onto_a_code_commit_runs_check_fast(tmp_path: Path) -> None:
    """The issue's reproduction: commit-msg ran check-docs for the amend, so the hook runs check-fast."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "src/a.py", "fix: code change").returncode == 0
    done = _amend(repo, env, "notes.md")
    assert done.returncode == 0, done
    assert _logged(log) == ["check-fast", "check-docs", "check-fast"]
    assert "#254" in done.stdout + done.stderr


def test_an_amend_commit_msg_already_covered_runs_nothing_more(tmp_path: Path) -> None:
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "src/a.py", "fix: x").returncode == 0
    assert _amend(repo, env, "src/b.py").returncode == 0          # code onto code: commit-msg ran check-fast
    assert _git(repo, env, "commit", "-q", "--amend", "-m", "fix: y").returncode == 0   # reworded: check-fast
    assert _commit(repo, env, "docs/notes.md", "docs: notes").returncode == 0
    assert _amend(repo, env, "docs/more.md").returncode == 0      # docs onto docs: check-docs is enough
    assert _logged(log) == ["check-fast", "check-fast", "check-fast", "check-docs", "check-docs"]


def test_a_docs_only_amend_onto_a_red_commit_runs_check_red_not_check_fast(tmp_path: Path) -> None:
    """A declared red test commit is meant to fail its tests: the commit needs check-red, as commit-msg says."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "tests/unit/test_x.py", RED).returncode == 0
    assert _amend(repo, env, "notes.md").returncode == 0
    assert _logged(log) == ["check-red", "check-docs", "check-red"]


def test_a_red_target_is_said_and_the_amend_stands(tmp_path: Path) -> None:
    """The hook cannot refuse: git made the amend before it ran. It says the target is red."""
    repo, log, env = _repo(tmp_path, fail="check-fast")
    assert _git(repo, env, "add", ".").returncode == 0
    _write(repo, "src/a.py")
    _git(repo, env, "add", "src/a.py")
    assert _git(repo, env, "commit", "-q", "--no-verify", "-m", "fix: x").returncode == 0
    done = _amend(repo, env, "notes.md")
    assert done.returncode == 0, done
    assert _logged(log) == ["check-docs", "check-fast"]
    assert "FAILED" in done.stderr and "pre-push" in done.stderr, done.stderr
    shown = _git(repo, env, "show", "--name-only", "--format=", "HEAD").stdout.split()
    assert shown == ["notes.md", "src/a.py"]


def test_an_odd_file_name_is_read_as_commit_msg_reads_it(tmp_path: Path) -> None:
    """Paths go NUL-separated: a quoted name would end in `"` and read as code, so a docs amend whose delta git
    would quote was taken for check-fast and skipped."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "src/a.py", "fix: x").returncode == 0
    assert _amend(repo, env, 'docs/né "q".md').returncode == 0
    assert _logged(log) == ["check-fast", "check-docs", "check-fast"]


def test_a_rebase_runs_nothing(tmp_path: Path) -> None:
    """Out of scope: git runs post-rewrite with `rebase` too, and the hook leaves it to pre-push."""
    repo, log, env = _repo(tmp_path)
    assert _commit(repo, env, "src/a.py", "fix: a").returncode == 0
    _git(repo, env, "checkout", "-q", "-b", "side", "HEAD~1")
    assert _commit(repo, env, "notes.md", "docs: n").returncode == 0
    done = _git(repo, env, "rebase", "-q", "main")
    assert done.returncode == 0, done
    assert _logged(log) == ["check-fast", "check-docs"]


def test_the_hook_is_executable_posix_sh() -> None:
    hook = ROOT / ".githooks" / "post-rewrite"
    assert hook.read_text(encoding="utf-8").startswith("#!/bin/sh\n")
    assert os.access(hook, os.X_OK)
