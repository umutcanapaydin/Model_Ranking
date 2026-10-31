"""#517: the protected base was the merge-base of HEAD, whose history the change under evaluation chooses.

A branch cut from a default-branch commit before `Deploy commands:` was declared, with the deploy line also gone from
its own brief, read no declared command anywhere: `deploy_gate.py "fly deploy"` exited 0 and the guard saw no deploy,
with no forged object at all (the #509 security review's R1). D-232 clause 1: the policy is read at the merge-base and
at the default branch's tip, and the gate takes the union.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_pin import GATE, Repo, _env, _installed

UNDECLARED = "- **Working mode:** `light`\n"
DECLARED = "- **Working mode:** `light`\n- **Deploy commands:** `fly deploy`\n"


def _deploy(repo: Repo, command: str) -> tuple[int, str]:
    done = subprocess.run([sys.executable, str(GATE), command], cwd=repo.root, capture_output=True, text=True,
                          env=_env(), timeout=120)
    return done.returncode, done.stdout + done.stderr


def _history(tmp_path: Path) -> tuple[Repo, str]:
    """main: a commit with no deploy command, then the brief declares `fly deploy`, then both verdicts there."""
    repo = Repo(tmp_path / "repo")
    repo.write("docs/project-brief.md", UNDECLARED)
    repo.write("src/app.py", "x = 1\n")
    before = repo.commit("before any deploy command")
    repo.write("docs/project-brief.md", DECLARED)
    head = repo.commit("declare the deploy")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts")
    return repo, before


def test_a_branch_cut_before_the_declaration_still_has_its_deploy_guarded(tmp_path: Path) -> None:
    repo, before = _history(tmp_path)
    repo.git("checkout", "-q", "-b", "work")
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change")
    assert _deploy(repo, "fly deploy")[0] == 2, "the control: from the tip's history the deploy is guarded"
    repo.git("checkout", "-q", "-b", "old", before)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change on old history")
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, out


def test_the_tips_mode_is_read_too(tmp_path: Path) -> None:
    """The union covers `Working mode:`: a tip that says heavy owes the milestone Tester even where the merge-base
    and the tree say light."""
    repo, before = _history(tmp_path)
    repo.write("docs/project-brief.md", DECLARED.replace("light", "heavy"))
    repo.commit("heavy mode")
    repo.git("checkout", "-q", "-b", "old", before)
    code, out = repo.check()
    assert code != 0, out
    assert "heavy" in out, out


def test_a_branch_cut_before_an_upgrade_cannot_restore_the_older_pins_bytes(tmp_path: Path) -> None:
    """The #517 review's M2 (D-233): the older pin at the merge-base held the tool's old bytes, so a branch cut before
    the upgrade, carrying the newer verdict files, reverted the tool unreviewed."""
    repo = _installed(tmp_path)
    before = repo.git("rev-parse", "main")
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2  # DevFlow's fix\n")
    repo.git("checkout", "-q", "main")
    head = repo.git("rev-parse", "HEAD")
    for name in ("release-security.md", "release-tester.md"):
        repo.write(f"docs/reviews/{name}", f"# R\n\n**Independent:** yes\n**Reviewed head:** {head}\n\n## Verdict\nPASS\n")
    repo.commit("verdicts after the upgrade")
    verdicts = {name: (repo.root / "docs" / "reviews" / name).read_text(encoding="utf-8")
                for name in ("release-security.md", "release-tester.md")}
    repo.git("checkout", "-q", "-b", "old", before)
    for name, text in verdicts.items():
        repo.write(f"docs/reviews/{name}", text)
    repo.commit("the newer verdicts on the older tool")
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_deploy_workflow_only_the_tip_holds_is_still_one(tmp_path: Path) -> None:
    """The #517 review's R2: the tip's workflow copies are read too, so a dispatch of a workflow added on the default
    branch after the change's fork point is judged a deploy."""
    repo, before = _history(tmp_path)
    repo.write(".github/workflows/release.yml", "name: Release\non: workflow_dispatch\njobs:\n  a:\n    steps:\n"
                                                "      - run: fly deploy\n")
    repo.commit("a deploy workflow on the tip")
    repo.git("checkout", "-q", "-b", "old", before)
    repo.write("docs/project-brief.md", DECLARED)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change on old history")
    code, out = _deploy(repo, "gh workflow run release")
    assert code == 2, out
