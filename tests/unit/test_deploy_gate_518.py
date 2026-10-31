"""#518: the verified reader's paths that fail closed but no test held (the #511, #509 and #505 security reviews).

Each test below fails with the mutant named in its docstring; none of these was open, but each invariant could be
dropped silently.
"""

from __future__ import annotations

import subprocess
import zlib
from pathlib import Path

import pytest

from .test_deploy_gate_444 import _module
from .test_deploy_gate_505 import _at_new_head, _seen
from .test_deploy_gate_pin import Repo, _env, _installed


def _cat(repo: Repo, kind: str, oid: str) -> bytes:
    return subprocess.run(["git", "cat-file", kind, oid], cwd=repo.root, capture_output=True, check=True).stdout


def _forge(repo: Repo, oid: str, kind: str, body: bytes) -> None:
    loose = repo.root / ".git" / "objects" / oid[:2] / oid[2:]
    assert loose.is_file(), "the fixture's objects are loose"
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"%s %d\0" % (kind.encode(), len(body)) + body))


def test_a_sha256_repository_is_read_and_its_forgeries_refused(tmp_path: Path) -> None:
    """#511 R1, #509 N14: the `{40,64}` ids and the digest chosen by the id's length."""
    root = tmp_path / "sha256"
    root.mkdir()
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false"]
    subprocess.run([*git, "init", "-q", "--object-format=sha256", "-b", "main"], cwd=root, check=True, env=_env())
    (root / "docs").mkdir()
    (root / "docs" / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run([*git, "add", "-A"], cwd=root, check=True, env=_env())
    subprocess.run([*git, "commit", "-q", "-m", "one"], cwd=root, check=True, env=_env())
    gate = _module("deploy_gate")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    assert len(head) == 64
    assert gate.brief_fields.verified_file(root, head, "docs/a.txt") == b"one\n"
    blob = subprocess.run(["git", "rev-parse", "HEAD:docs/a.txt"], cwd=root, capture_output=True, text=True,
                          check=True).stdout.strip()
    loose = root / ".git" / "objects" / blob[:2] / blob[2:]
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"blob 4\0two\n"))
    with pytest.raises(gate.brief_fields.Unverified):
        gate.brief_fields.verified_file(root, head, "docs/a.txt")


def test_a_directory_on_the_way_spelled_040000_is_not_read(tmp_path: Path) -> None:
    """#511 R2, #509 N7: only `40000`, as git writes it, is a directory on the way to a file the gate trusts."""
    repo = Repo(tmp_path / "padded")
    repo.write("a/b.txt", "x\n")
    repo.commit("one")
    inner = repo.git("rev-parse", "HEAD:a")
    root = subprocess.run(["git", "hash-object", "-w", "-t", "tree", "--literally", "--stdin"], cwd=repo.root,
                          input=b"040000 a\0" + bytes.fromhex(inner), capture_output=True, check=True).stdout.decode().strip()
    padded = repo.git("commit-tree", root, "-m", "padded")
    gate = _module("deploy_gate")
    assert gate.brief_fields.verified_file(repo.root, "HEAD", "a/b.txt") == b"x\n", "the control"
    with pytest.raises(gate.brief_fields.Unverified):
        gate.brief_fields.verified_file(repo.root, padded, "a/b.txt")


def test_a_nested_tree_that_does_not_hash_under_a_folder_is_raised_not_skipped(tmp_path: Path) -> None:
    """#509 N12: `verified_files` reads a folder's subtrees; one that does not hash fails the whole folder."""
    repo = Repo(tmp_path / "nested")
    repo.write("w/inner/a.yml", "a: 1\n")
    repo.write("w/b.yml", "b: 1\n")
    repo.commit("one")
    gate = _module("deploy_gate")
    files, failed = gate.brief_fields.verified_files(repo.root, "HEAD", "w", (".yml",))
    assert set(files) == {"w/inner/a.yml", "w/b.yml"} and not failed, "the control"
    inner = repo.git("rev-parse", "HEAD:w/inner")
    _forge(repo, inner, "tree", _cat(repo, "tree", inner).replace(b"a.yml", b"c.yml"))
    with pytest.raises(gate.brief_fields.Unverified):
        gate.brief_fields.verified_files(repo.root, "HEAD", "w", (".yml",))


def test_a_deeper_gitignore_takes_precedence_over_a_shallower_one(tmp_path: Path) -> None:
    """#505 R1 (precedence reversed): `src/.gitignore` re-includes what the root's ignores, as git reads it."""
    repo = _installed(tmp_path)
    _at_new_head(repo, {".gitignore": "*.gen.py\n", "src/.gitignore": "!keep.gen.py\n"})
    repo.write("src/drop.gen.py", "x = 1\n")
    assert repo.check()[0] == 0, "the control: the root's pattern ignores it"
    repo.write("src/keep.gen.py", "x = 2\n")
    _seen(repo, "src/keep.gen.py")


def test_a_submodule_not_checked_out_at_its_recorded_commit_is_a_change(tmp_path: Path) -> None:
    """#505 R1 (a submodule always the same): a gitlink differs unless the checkout there is at its commit."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    recorded = repo.git("rev-parse", "HEAD")
    repo.git("update-index", "--add", "--cacheinfo", f"160000,{recorded},src/vendored")
    repo.git("commit", "-q", "-m", "a submodule")  # not `commit()`: its `add -A` would drop the gitlink again
    head = repo.git("rev-parse", "HEAD")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts")
    repo.git("checkout", "-q", "-b", "after")
    _seen(repo, "src/vendored")
