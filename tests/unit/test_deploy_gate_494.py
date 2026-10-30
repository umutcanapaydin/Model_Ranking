"""#494 (the #444 security review's M1 to M3 and R2): the deploy surface, derived from every spelling of a command.

`deploy_surface` decides which files the DevFlow exemption may never reach: what the brief's deploy commands start.
A declared command matched only when it was written exactly as the git path, so `./scripts/x.sh`, a mixed-case
path, an absolute path, or a workflow dispatched by its stem or its `name:` left the file it starts exemptible. A
declaration the gate cannot read to its files -- none at all, or `make <target>`, whose recipe it does not read --
exempts nothing. The exemption also compared a symlink entry at the pin by its link text.
"""

from __future__ import annotations

import subprocess
import zlib
from pathlib import Path

import pytest

from .test_deploy_gate_444 import _module, _upgrade_shipping
from .test_deploy_gate_pin import Repo, _installed

WORKFLOW = "name: Ship it\non: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: echo hi\n"


def _brief(*commands: str) -> str:
    listed = ", ".join(f"`{c}`" for c in commands)
    return "- **Working mode:** `light`\n" + (f"- **Deploy commands:** {listed}\n" if commands else "")


@pytest.mark.parametrize(("rel", "text", "command"), [
    ("scripts/ship_it.sh", "echo ship\n", "./scripts/ship_it.sh"),
    ("scripts/ship_it.sh", "echo ship\n", "bash ./scripts/ship_it.sh"),
    ("scripts/Ship_It.sh", "echo ship\n", "scripts/Ship_It.sh"),
    ("scripts/ship_it.sh", "echo ship\n", "{root}/scripts/ship_it.sh"),
    (".github/workflows/release.yml", WORKFLOW, "gh workflow run release"),
    (".github/workflows/release.yml", WORKFLOW, "gh workflow run 'Ship it'"),
], ids=["dot-slash", "bash-dot-slash", "mixed-case", "absolute", "workflow-stem", "workflow-name"])
def test_every_spelling_of_a_deploy_command_puts_what_it_starts_on_the_surface(
        tmp_path: Path, rel: str, text: str, command: str) -> None:
    """M1: each of these spellings starts `rel`, and an upgrade that shipped `rel` byte for byte exempted it."""
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, rel, text, brief=_brief(command.format(root=repo.root)))
    code, out = repo.check()
    assert code != 0, out
    assert rel in out, out


@pytest.mark.parametrize("brief", [_brief(), _brief("make ship")], ids=["no-deploy-command", "make-target"])
def test_a_declaration_the_gate_cannot_read_to_its_files_exempts_nothing(tmp_path: Path, brief: str) -> None:
    """M1: with no deploy command declared, or one that runs a recipe the gate does not read (`make <target>`), the
    surface is unknown, so a tooling file an upgrade shipped unchanged is code (fail closed)."""
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=brief)
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_readable_declaration_still_exempts_a_plain_tooling_file(tmp_path: Path) -> None:
    """The control: every spelling above, declared together, leaves a file none of them starts DevFlow's."""
    repo = _installed(tmp_path)
    brief = _brief("./scripts/ship_it.sh", f"{repo.root}/scripts/deploy_hosted_engine.sh", "gh workflow run release",
                   "fly deploy")
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=brief)
    code, out = repo.check()
    assert code == 0, out


def _objects_loose(repo: Repo) -> None:
    assert not list((repo.root / ".git" / "objects" / "pack").glob("*.pack")), "the fixture's objects are loose"


def test_a_forged_pinned_tree_is_not_read_as_the_pinned_bytes(tmp_path: Path) -> None:
    """M2: only the blob's hash was held by a test. Forge the pinned commit's root tree alone -- its `scripts` entry
    pointing at a real tree that holds the agent's bytes -- and the changed tool must not read as DevFlow's."""
    repo = _installed(tmp_path)
    pinned = repo.git("show", "main:docs/devflow-pin.txt").split()[1]
    changed = "VERSION = 1  # the agent's change\n"
    repo.write("scripts/tool.py", changed)
    repo.commit("a change")
    _objects_loose(repo)
    forged_scripts = repo.git("rev-parse", "HEAD:scripts")
    root_tree = repo.git("rev-parse", f"{pinned}^{{tree}}")
    body = subprocess.run(["git", "cat-file", "tree", root_tree], cwd=repo.root, capture_output=True,
                          check=True).stdout
    original = bytes.fromhex(repo.git("rev-parse", f"{pinned}:scripts"))
    assert body.count(original) == 1
    forged = body.replace(original, bytes.fromhex(forged_scripts))
    loose = repo.root / ".git" / "objects" / root_tree[:2] / root_tree[2:]
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"tree %d\0" % len(forged) + forged))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_forged_pinned_commit_is_not_read_as_the_pinned_tree(tmp_path: Path) -> None:
    """#510: the pinned commit is an ancestor of the reviewed head, which #493's walk does not reach, so the hash check
    on it is its only guard. Forge its object to name the agent's tree and the changed tool must not read as DevFlow's."""
    repo = _installed(tmp_path)
    pinned = repo.git("show", "main:docs/devflow-pin.txt").split()[1]
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    repo.commit("a change")
    _objects_loose(repo)
    body = subprocess.run(["git", "cat-file", "commit", pinned], cwd=repo.root, capture_output=True,
                          check=True).stdout
    original = repo.git("rev-parse", f"{pinned}^{{tree}}").encode()
    assert body.startswith(b"tree " + original + b"\n")
    forged = body.replace(original, repo.git("rev-parse", "HEAD^{tree}").encode(), 1)
    loose = repo.root / ".git" / "objects" / pinned[:2] / pinned[2:]
    loose.chmod(0o644)
    loose.write_bytes(zlib.compress(b"commit %d\0" % len(forged) + forged))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_base_workflow_that_cannot_be_read_exempts_nothing(tmp_path: Path) -> None:
    """M3: when a workflow at the protected base cannot be shown, the surface is unknown and nothing is exempt."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write(".github/workflows/other.yml", "on: push\njobs:\n  a:\n    steps:\n      - run: echo hi\n")
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=_brief("fly deploy"))
    assert repo.check()[0] == 0, "the control: every workflow readable, the tool is DevFlow's"
    _objects_loose(repo)
    blob = repo.git("rev-parse", "main:.github/workflows/other.yml")
    (repo.root / ".git" / "objects" / blob[:2] / blob[2:]).unlink()
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_symlink_entry_at_the_pin_is_not_read_as_a_file(tmp_path: Path) -> None:
    """R2: an entry of mode 120000 at the pin was compared by its link text. Only modes 100644 and 100755 are files."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    text = "VERSION = 2\n"
    blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=repo.root, input=text, capture_output=True,
                          text=True, check=True).stdout.strip()
    repo.git("update-index", "--cacheinfo", f"120000,{blob},scripts/tool.py")
    repo.git("commit", "-q", "-m", "DevFlow v9.10 ships tool.py as a link")
    shipped = repo.git("rev-parse", "HEAD")
    repo.git("reset", "-q")  # the index back to HEAD's entries; the work tree keeps the regular file
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.git("add", "docs/devflow-pin.txt")
    repo.git("commit", "-q", "-m", "pin v9.10")
    repo.git("checkout", "-q", "-b", "after-upgrade")
    repo.git("rm", "-q", "--cached", "scripts/tool.py")
    repo.write("scripts/tool.py", text)
    repo.commit("tool.py as a regular file with the link's text")
    assert (repo.root / "scripts" / "tool.py").read_text(encoding="utf-8") == text
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_tree_git_cannot_list_exempts_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The #494 security review's R1: when git cannot list the tree, the surface is unknown (None), never a crash."""
    repo = _installed(tmp_path)
    gate = _module("deploy_gate")
    assert gate.deploy_surface(repo.root) is not None, "the control: git lists the tree"
    gate._SURFACES.clear()
    monkeypatch.setattr(gate, "_files", lambda root: None)
    assert gate.deploy_surface(repo.root) is None
