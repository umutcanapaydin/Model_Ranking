"""#534 (the #517 security review's R3): `brief_fields.protected_bases` walked `DEFAULT_BRANCHES` (`origin/HEAD` first)
and answered with the first ref that had a merge-base, so an `origin/HEAD` left at an old commit stood for the
default branch and hid `origin/main`'s tip: a branch cut before `Deploy commands:` was declared read no declaration.
Now every default-branch ref that exists gives its merge-base with HEAD and its tip, and the gate reads the union
(D-232 clause 1): more bases, never fewer.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .test_deploy_gate_517 import _deploy, _history
from .test_deploy_gate_pin import Repo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import brief_fields


def _stale_origin_head(tmp_path: Path, symbolic: bool) -> tuple[Repo, str, str]:
    """main declares `fly deploy` at its tip, and so does `origin/main`; `origin/HEAD` is left at the commit before."""
    repo, before = _history(tmp_path)
    tip = repo.git("rev-parse", "main")
    repo.git("update-ref", "refs/remotes/origin/main", tip)
    if symbolic:
        repo.git("update-ref", "refs/remotes/origin/old", before)
        repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/old")
    else:
        repo.git("update-ref", "refs/remotes/origin/HEAD", before)
    repo.git("checkout", "-q", "-b", "old", before)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change on old history")
    return repo, before, tip


@pytest.mark.parametrize("symbolic", [False, True], ids=["plain", "symbolic"])
def test_a_stale_origin_head_does_not_hide_origin_main(tmp_path: Path, symbolic: bool) -> None:
    repo, _, tip = _stale_origin_head(tmp_path, symbolic)
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, f"a stale origin/HEAD let the deploy pass unguarded: {out}"
    assert tip in brief_fields.protected_bases(repo.root), "origin/main's tip is not read"


def test_every_default_branch_ref_gives_its_bases_and_the_merge_base_comes_first(tmp_path: Path) -> None:
    """Never fewer: with the refs in agreement the answer is the one it was, the merge-base and the tip; with them
    apart, each one's merge-base and tip, once each, a merge-base first (the gate's message names it so)."""
    repo, before = _history(tmp_path)
    tip = repo.git("rev-parse", "main")
    repo.git("checkout", "-q", "-b", "work")
    repo.write("src/app.py", "x = 3\n")
    repo.commit("work")
    base = repo.git("merge-base", "main", "HEAD")
    assert brief_fields.protected_bases(repo.root) == [base]  # the tip is the merge-base here
    repo.git("update-ref", "refs/remotes/origin/HEAD", before)
    bases = brief_fields.protected_bases(repo.root)
    assert bases[0] == before and set(bases) == {before, tip} and len(bases) == len(set(bases)), bases


def test_no_default_branch_is_no_base(tmp_path: Path) -> None:
    repo, _ = _history(tmp_path)
    repo.git("checkout", "-q", "-b", "work")
    repo.git("branch", "-D", "main")
    assert brief_fields.protected_bases(repo.root) == []
