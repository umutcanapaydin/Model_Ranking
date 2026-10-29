"""#493 and #500: the deploy gate compares the working tree with a reviewed head only through git state it has checked.

`changed_since` runs `git diff --name-only <reviewed head>`. Git reads that head's commit and trees from the object store
without hashing them, so a loose tree forged under the reviewed head hid a product change (#493, the #444 security
review's R1). And git does not look at a file whose index entry carries the assume-unchanged or skip-worktree bit, so
one `git update-index` call hid an uncommitted change (#500). Either way the gate printed "no code changed since".
"""

from __future__ import annotations

import subprocess
import zlib
from pathlib import Path

import pytest

from .test_deploy_gate_444 import _module
from .test_deploy_gate_pin import Repo, _installed


def _reviewed_head(repo: Repo) -> str:
    text = (repo.root / "docs" / "reviews" / "release-security.md").read_text(encoding="utf-8")
    return text.split("**Reviewed head:** ")[1].split()[0]


def test_a_forged_tree_under_the_reviewed_head_does_not_hide_a_change(tmp_path: Path) -> None:
    """#493: point the reviewed head's `src` tree at the agent's blob, and `src/app.py` left the diff. (Git itself
    refuses a forged ROOT tree, which it hashes as it parses the commit; a tree below it, it does not.)"""
    repo = _installed(tmp_path)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change")
    assert repo.check()[0] != 0, "the control: the change is seen"
    head = _reviewed_head(repo)
    src = repo.git("rev-parse", f"{head}:src")
    body = subprocess.run(["git", "cat-file", "tree", src], cwd=repo.root, capture_output=True, check=True).stdout
    original = bytes.fromhex(repo.git("rev-parse", f"{head}:src/app.py"))
    assert body.count(original) == 1
    forged = body.replace(original, bytes.fromhex(repo.git("rev-parse", "HEAD:src/app.py")))
    loose = repo.root / ".git" / "objects" / src[:2] / src[2:]
    assert loose.is_file(), "the fixture's objects are loose"
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"tree %d\0" % len(forged) + forged))
    code, out = repo.check()
    assert code != 0, out
    assert "does not hash" in out, out


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_an_index_flag_does_not_hide_an_uncommitted_change(tmp_path: Path, flag: str) -> None:
    """#500: git does not look at a file whose index entry carries this bit, so its change left the diff."""
    repo = _installed(tmp_path)
    repo.write("src/app.py", "x = 2  # a product change\n")
    assert repo.check()[0] != 0, "the control: the change is seen"
    repo.git("update-index", flag, "src/app.py")
    code, out = repo.check()
    assert code != 0, out
    assert "src/app.py" in out, out


def test_the_reviewed_tree_with_no_flag_and_no_forgery_still_passes(tmp_path: Path) -> None:
    """The control: every object hashes and no entry is flagged, so the reviewed tree passes as before."""
    code, out = _installed(tmp_path).check()
    assert code == 0, out


def _forge(repo: Repo, oid: str, kind: str, body: bytes) -> None:
    """Overwrite the loose object `oid` with `body`, which no longer hashes to it."""
    loose = repo.root / ".git" / "objects" / oid[:2] / oid[2:]
    assert loose.is_file(), "the fixture's objects are loose"
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"%s %d\0" % (kind.encode(), len(body)) + body))


def _cat(repo: Repo, kind: str, oid: str) -> bytes:
    return subprocess.run(["git", "cat-file", kind, oid], cwd=repo.root, capture_output=True, check=True).stdout


def test_a_forged_reviewed_commit_does_not_hide_a_change(tmp_path: Path) -> None:
    """The #493 review's B1: peeling `<head>^{commit}` parsed the forged commit, failed, and read as "no such head",
    while `git diff` used the forged commit's tree unhashed. Point the reviewed commit at the agent's tree."""
    repo = _installed(tmp_path)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change")
    head = _reviewed_head(repo)
    body = _cat(repo, "commit", head)
    forged = body.replace(repo.git("rev-parse", f"{head}^{{tree}}").encode(), repo.git("rev-parse", "HEAD^{tree}").encode())
    assert forged != body
    _forge(repo, head, "commit", forged)
    code, out = repo.check()
    assert code != 0, out
    assert "does not hash" in out, out


def _deep(tmp_path: Path) -> tuple[Repo, str]:
    repo = Repo(tmp_path / "deep")
    repo.write("a/b/c.py", "x = 1\n")
    return repo, repo.commit("deep")


def test_a_forged_tree_two_levels_down_is_found(tmp_path: Path) -> None:
    """The #493 review's M3 (mutant G): the walk goes below the root's children."""
    repo, head = _deep(tmp_path)
    gate = _module("deploy_gate")
    assert gate._unhashed(repo.root, head) is None, "the control: every object hashes"
    deep = repo.git("rev-parse", f"{head}:a/b")
    _forge(repo, deep, "tree", _cat(repo, "tree", deep).replace(b"c.py", b"d.py"))
    assert "does not hash" in (gate._unhashed(repo.root, head) or "")


def test_a_zero_padded_tree_mode_is_walked(tmp_path: Path) -> None:
    """The #493 review's M2: git reads an entry of mode `040000` as a tree, so the walk must too."""
    repo, _ = _deep(tmp_path)
    inner = repo.git("rev-parse", "HEAD:a/b")
    padded = b"040000 b\0" + bytes.fromhex(inner)
    a = subprocess.run(["git", "hash-object", "-w", "-t", "tree", "--literally", "--stdin"], cwd=repo.root,
                       input=padded, capture_output=True, check=True).stdout.decode().strip()
    root = subprocess.run(["git", "hash-object", "-w", "-t", "tree", "--literally", "--stdin"], cwd=repo.root,
                          input=b"40000 a\0" + bytes.fromhex(a), capture_output=True, check=True).stdout.decode().strip()
    head = repo.git("commit-tree", root, "-m", "padded")
    gate = _module("deploy_gate")
    assert gate._unhashed(repo.root, head) is None, "the control: every object hashes"
    _forge(repo, inner, "tree", _cat(repo, "tree", inner).replace(b"c.py", b"d.py"))
    assert "does not hash" in (gate._unhashed(repo.root, head) or "")


def test_an_index_git_cannot_list_or_objects_it_cannot_read_fail_closed(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The #493 review's M3 (mutants F, H): no index listing, or no git to read the objects, is a refusal."""
    repo, head = _deep(tmp_path)
    gate = _module("deploy_gate")
    assert gate.compare_problem(repo.root, head) is None, "the control"
    with monkeypatch.context() as patch:
        patch.setattr(gate, "_flagged", lambda root: None)
        assert gate.compare_problem(repo.root, head) == "git cannot list the index"

    def no_git(*args: object, **kwargs: object) -> None:
        raise OSError("no git")

    monkeypatch.setattr(gate.subprocess, "Popen", no_git)
    assert gate._unhashed(repo.root, head) == "objects cannot be read by git"
