"""#587 (run 1102's release delta security review, R14): prune_merged read the default branch by its short name.

`origin/main` given to `merge-base` goes through git's name lookup, where `refs/tags/origin/main` wins over
`refs/remotes/origin/main`. A tag spelled like the default branch, at an unmerged branch's tip, made that branch read
as merged; with HEAD holding it (a stacked child checked out), `git branch -d` agreed and the branch was deleted
although its work is not on the default branch.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "prune_merged.py"
ID = ("-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false")


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return env


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *ID, *args], cwd=cwd, capture_output=True, text=True, env=_env(), check=False)
    assert done.returncode == 0, (args, done.stderr)
    return done.stdout.strip()


def _repo(tmp_path: Path, default_ref_name: str) -> Path:
    """A clone whose branch `feat` was pushed, then deleted on origin unmerged; HEAD is `stack`, cut from `feat`;
    a tag named `default_ref_name` sits at `feat`'s tip."""
    origin, proj = tmp_path / "origin.git", tmp_path / "proj"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True, env=_env())
    subprocess.run(["git", "clone", "-q", str(origin), str(proj)], check=True, env=_env(), capture_output=True)
    _git(proj, "checkout", "-q", "-b", "main")
    (proj / "a.txt").write_text("a\n", encoding="utf-8")
    _git(proj, "add", "a.txt")
    _git(proj, "commit", "-q", "-m", "a")
    _git(proj, "push", "-q", "-u", "origin", "main")
    # No refs/remotes/origin/HEAD, and none made by the script's fetch (git 2.48+ makes one unless told not to): the
    # script then falls to its short-name candidates. With origin/HEAD present, `symbolic-ref --short` already
    # disambiguates (`remotes/origin/main`), so this is the shape R14 is reachable in.
    _git(proj, "config", "remote.origin.followRemoteHEAD", "never")
    subprocess.run(["git", "remote", "set-head", "origin", "-d"], cwd=proj, capture_output=True, env=_env(), check=False)
    _git(proj, "checkout", "-q", "-b", "feat")
    (proj / "f.txt").write_text("f\n", encoding="utf-8")
    _git(proj, "add", "f.txt")
    _git(proj, "commit", "-q", "-m", "unmerged work")
    _git(proj, "push", "-q", "-u", "origin", "feat")
    _git(proj, "checkout", "-q", "-b", "stack")
    _git(proj, "push", "-q", "origin", "--delete", "feat")       # upstream gone, never merged
    _git(proj, "tag", default_ref_name, "feat")
    return proj


def _prune(proj: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT)], cwd=proj, capture_output=True, text=True, env=_env(),
                          timeout=120, check=False)


def test_587_a_tag_named_like_the_default_branch_does_not_make_an_unmerged_branch_merged(tmp_path: Path) -> None:
    proj = _repo(tmp_path, "origin/main")
    done = _prune(proj)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _git(proj, "branch", "--list", "feat"), done.stdout
    assert "kept feat" in done.stdout and "not on" in done.stdout, done.stdout


def test_587_a_tag_named_origin_head_does_not_stand_in_either(tmp_path: Path) -> None:
    proj = _repo(tmp_path, "origin/HEAD")
    done = _prune(proj)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _git(proj, "branch", "--list", "feat"), done.stdout
