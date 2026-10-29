"""#410 (D-223 clause 5): the deploy gate's "DevFlow file, unchanged" exemption reads DevFlow's commit from the
protected base, never from what an agent can write.

The v0.1.0 release security review's M1: the exemption read the version from the untracked `.gp/installed` and
compared against `refs/tags/<version>`, both writable by an agent, so a changed file plus a forged tag and marker
passed the gate. Now the exemption compares a file with the commit `docs/devflow-pin.txt` names AS THE PROTECTED BASE
HOLDS IT (the merge-base with the default branch, which an agent's branch cannot move), and the product's deploy
scripts are safety surface, code whatever their bytes. An upgrade the owner merges moves the pin, so it owes no delta.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts" / "deploy_gate.py"


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@x", "-c", "commit.gpgsign=false", *args],
                              cwd=self.root, check=True, capture_output=True, text=True, env=_env(),
                              timeout=60).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.root / rel).write_text(text, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def check(self) -> tuple[int, str]:
        done = subprocess.run([sys.executable, str(GATE), "--check"], cwd=self.root, capture_output=True, text=True,
                              env=_env(), timeout=120)
        return done.returncode, done.stdout + done.stderr


def _installed(tmp_path: Path) -> Repo:
    """DevFlow v9.9's tooling on main, its commit pinned, both verdicts at that head."""
    repo = Repo(tmp_path / "repo")
    # #494: a declaration the gate can read to its files; with none, nothing is exempt.
    repo.write("docs/project-brief.md", "- **Working mode:** `light`\n"
                                        "- **Deploy commands:** `scripts/deploy_hosted_engine.sh`\n")
    repo.write("scripts/tool.py", "VERSION = 1\n")
    repo.write("scripts/deploy_hosted_engine.sh", "echo deploy\n")
    repo.write("src/app.py", "x = 1\n")
    repo.write(".gp/installed", "gp_version: v9.9\n")
    shipped = repo.commit("DevFlow v9.9")
    repo.git("tag", "v9.9")
    repo.write("docs/devflow-pin.txt", f"v9.9 {shipped}\n")
    head = repo.commit("pin v9.9")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts")
    repo.git("checkout", "-q", "-b", "work")
    return repo


def test_the_reviewed_tree_passes(tmp_path: Path) -> None:
    assert _installed(tmp_path).check()[0] == 0


def test_a_forged_tag_and_marker_do_not_exempt_a_changed_tooling_file(tmp_path: Path) -> None:
    """The review's probe: change a DevFlow file on a branch, tag that commit, point the marker at the tag."""
    repo = _installed(tmp_path)
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    repo.commit("a change")
    assert repo.check()[0] != 0
    repo.git("tag", "v9.99", "HEAD")
    repo.write(".gp/installed", "gp_version: v9.99\n")
    code, out = repo.check()
    assert code != 0, out


def test_a_moved_tag_does_not_exempt_a_changed_tooling_file(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    repo.commit("a change")
    repo.git("tag", "-f", "v9.9", "HEAD")
    code, out = repo.check()
    assert code != 0, out


def test_a_pin_edited_on_the_branch_is_not_read(tmp_path: Path) -> None:
    """The pin is read at the merge-base with main: a branch that rewrites it changes nothing the gate reads."""
    repo = _installed(tmp_path)
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    forged = repo.commit("a change")
    repo.write("docs/devflow-pin.txt", f"v9.9 {forged}\n")
    repo.commit("re-pin")
    code, out = repo.check()
    assert code != 0, out


def test_a_deploy_script_is_code_even_byte_identical_to_the_pinned_commit(tmp_path: Path) -> None:
    """The product's deploy scripts join the safety surface: an edit made and pinned upstream still owes a review."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write("scripts/deploy_hosted_engine.sh", "echo deploy --somewhere-else\n")
    shipped = repo.commit("DevFlow v9.10 ships the deploy script")
    repo.git("tag", "v9.10")
    repo.write(".gp/installed", "gp_version: v9.10\n")
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.commit("pin v9.10")
    repo.git("checkout", "-q", "-b", "after-upgrade")
    code, out = repo.check()
    assert code != 0, out


def test_an_upgrade_the_owner_merged_owes_no_delta(tmp_path: Path) -> None:
    """The quiet case (v7.2's ruling): DevFlow's new tooling, pinned on main, is not code to the gate."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write("scripts/tool.py", "VERSION = 2\n")
    shipped = repo.commit("DevFlow v9.10")
    repo.git("tag", "v9.10")
    repo.write(".gp/installed", "gp_version: v9.10\n")
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.commit("pin v9.10")
    repo.git("checkout", "-q", "-b", "after-upgrade")
    code, out = repo.check()
    assert code == 0, out


def test_a_replace_ref_does_not_forge_the_pinned_bytes(tmp_path: Path) -> None:
    """#410 round 1's B1: `git replace <pinned> <forged>` made `cat-file` read the forged commit's bytes."""
    repo = _installed(tmp_path)
    pinned = repo.git("show", "main:docs/devflow-pin.txt").split()[1]
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    forged = repo.commit("a change")
    repo.git("replace", pinned, forged)
    code, out = repo.check()
    assert code != 0, out


def test_a_replace_ref_does_not_forge_the_protected_base(tmp_path: Path) -> None:
    """B1's second form: replace main's commit with one whose pin names the agent's commit."""
    repo = _installed(tmp_path)
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    forged = repo.commit("a change")
    repo.write("docs/devflow-pin.txt", f"v9.9 {forged}\n")
    repo.commit("a pin of my own")
    # Round 2's M4: a stand-in for main's tip that holds the branch's tree and descends from the branch's head, so
    # with replace refs honoured the merge-base becomes the branch's own commit and its pin is read.
    main_tip = repo.git("rev-parse", "main")
    stand_in = repo.git("commit-tree", "-p", "HEAD", "-m", "a forged base", "HEAD^{tree}")
    repo.git("replace", main_tip, stand_in)
    code, out = repo.check()
    assert code != 0, out


def test_a_product_file_byte_identical_to_the_pinned_commit_is_still_code(tmp_path: Path) -> None:
    """Round 1's B2: only DevFlow's tooling can be exempt; a product file the pinned commit happens to hold is not."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write("src/app.py", "x = 2\n")
    shipped = repo.commit("a commit that holds a product change")
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.commit("pin it")
    repo.git("checkout", "-q", "-b", "after")
    code, out = repo.check()
    assert code != 0, out


#: D-223 clause 5 (#410): every deploy surface the issue's remedy named, written out here rather than read from
#: `SAFETY_SURFACE`, so a surface dropped from the gate's set fails this test instead of shrinking it.
DEPLOY_SURFACES = ["scripts/deploy_hosted_engine.sh", "scripts/nightly_hosted.sh", "scripts/ci/nightly-hosted.yml"]


@pytest.mark.parametrize("rel", DEPLOY_SURFACES)
def test_every_deploy_surface_is_code_even_byte_identical_to_the_pinned_commit(tmp_path: Path, rel: str) -> None:
    """The release Tester for v0.2.0: with `scripts/nightly_hosted.sh` or `scripts/ci/` dropped from the safety
    surface the suite stayed green, since only `deploy_hosted_engine.sh` was planted. Each surface, changed on main
    and pinned there as an upgrade would pin it, still owes a review: the gate refuses. The same setup with a plain
    tooling file passes (`test_an_upgrade_the_owner_merged_owes_no_delta`), so only the safety surface refuses here.
    # covers D-223 clause 5, #410"""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write(rel, "echo deploy --somewhere-else\n")
    shipped = repo.commit(f"DevFlow v9.10 ships {rel}")
    repo.write("docs/devflow-pin.txt", f"v9.10 {shipped}\n")
    repo.commit("pin v9.10")
    repo.git("checkout", "-q", "-b", "after-upgrade")
    code, out = repo.check()
    assert code != 0, out
    assert rel in out, out
