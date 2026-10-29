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
