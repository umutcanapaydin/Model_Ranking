"""#545 (the fixes-1101 security review's B1): the protected base was found by SHORT names (`origin/HEAD`, `main`, ...),
and git resolves a short name to `refs/<name>` and `refs/tags/<name>` before `refs/heads/` or `refs/remotes/`. A tag or
ref the session plants under the default branch's name then chooses the commit whose brief judges its own deploy:
`deploy_gate.py "fly deploy"` read a brief from before `Deploy commands:` was declared and exited 0. Now every policy
reader names the default branch by its full ref.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .test_deploy_gate_517 import UNDECLARED, _deploy, _history
from .test_deploy_gate_pin import Repo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import review_need


def _work(tmp_path: Path) -> tuple[Repo, str]:
    """A branch cut from main's tip with a product change that also drops `Deploy commands:` from its own brief: its
    deploy is guarded only by the declaration at the protected base (the control)."""
    repo, before = _history(tmp_path)
    repo.git("checkout", "-q", "-b", "work")
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.write("docs/project-brief.md", UNDECLARED)
    repo.commit("a product change, and no deploy declared on the branch")
    assert _deploy(repo, "fly deploy")[0] == 2, "the control: the deploy is guarded from main's tip"
    return repo, before


@pytest.mark.parametrize("plant", [
    ("tag", "main"),                     # refs/tags/main resolves before refs/heads/main
    ("update-ref", "refs/main"),         # refs/main resolves before both
])
def test_a_planted_name_does_not_choose_the_protected_base(tmp_path: Path, plant: tuple[str, str]) -> None:
    repo, before = _work(tmp_path)
    kind, name = plant
    repo.git(*(["tag", name, before] if kind == "tag" else ["update-ref", name, before]))
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, f"a planted {name} at the commit before the declaration let the deploy pass: {out}"


def test_a_planted_tag_does_not_stand_for_origin(tmp_path: Path) -> None:
    """With origin's refs present, a tag named `origin/HEAD` was tried before the real `refs/remotes/origin/main`."""
    repo, before = _work(tmp_path)
    repo.git("update-ref", "refs/remotes/origin/main", repo.git("rev-parse", "main"))
    repo.git("tag", "origin/HEAD", before)
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, f"a tag named origin/HEAD chose the protected base: {out}"


def test_review_need_measures_from_the_real_default_branch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`review_need`'s default range is policy too (#283): it starts at the merge-base with the real `main`."""
    repo, before = _work(tmp_path)
    real = repo.git("merge-base", "refs/heads/main", "HEAD")
    repo.git("tag", "main", before)
    monkeypatch.chdir(repo.root)
    assert review_need.default_range() == f"{real}..HEAD"


def test_one_list_names_the_default_branch_for_every_policy_reader() -> None:
    """Derive, don't enumerate (AGENTS.md §3.5): review_need reads brief_fields' list, and every name in it is full."""
    import brief_fields

    assert all(ref.startswith(("refs/heads/", "refs/remotes/")) for ref in brief_fields.DEFAULT_BRANCHES)
    source = (Path(__file__).resolve().parents[2] / "scripts" / "review_need.py").read_text(encoding="utf-8")
    assert "brief_fields.DEFAULT_BRANCHES" in source and '"origin/HEAD"' not in source


def test_a_tag_spelled_as_a_missing_full_ref_does_not_stand_for_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The fixes-1101 security review's M2: a full name still went through git's name lookup, so with no
    `refs/remotes/origin/HEAD` (deleted, or never fetched) a tag spelled `refs/remotes/origin/HEAD` stood in for it."""
    repo, before = _work(tmp_path)
    real = repo.git("merge-base", "refs/heads/main", "HEAD")
    repo.git("tag", "refs/remotes/origin/HEAD", before)
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, f"a tag spelled refs/remotes/origin/HEAD chose the protected base: {out}"
    monkeypatch.chdir(repo.root)
    assert review_need.default_range() == f"{real}..HEAD"
