"""#509: the deploy gate read the protected base's pin file, brief and workflows as git's object store gave them.

#493 hashes the reviewed head's commit and trees; the files whose CONTENT the gate trusts at the base -- the DevFlow
pin, the brief's `Deploy commands:` and the workflows a dispatch runs -- were read with `git show`, which does not
hash a loose blob. One forged loose object (the reach #493 assumes) then exempted a changed tool as DevFlow's, or
hid the deploy commands so the guard did not see a deploy at all (the delta review of `integration/fixes-1030`, R1).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .test_deploy_gate_493 import _cat, _forge
from .test_deploy_gate_494 import _brief, _objects_loose
from .test_deploy_gate_pin import GATE, Repo, _env, _installed


def _deploy(repo: Repo, command: str) -> tuple[int, str]:
    done = subprocess.run([sys.executable, str(GATE), command], cwd=repo.root, capture_output=True, text=True,
                          env=_env(), timeout=120)
    return done.returncode, done.stdout + done.stderr


def _forge_at_main(repo: Repo, rel: str, text: str) -> None:
    _objects_loose(repo)
    _forge(repo, repo.git("rev-parse", f"main:{rel}"), "blob", text.encode())


def test_a_forged_base_pin_does_not_exempt_a_changed_tool(tmp_path: Path) -> None:
    """Probe 1: the base's pin blob rewritten to name the agent's own commit."""
    repo = _installed(tmp_path)
    repo.write("scripts/tool.py", "VERSION = 1  # the agent's change\n")
    agent = repo.commit("a change")
    assert repo.check()[0] != 0, "the control: the change is seen"
    _forge_at_main(repo, "docs/devflow-pin.txt", f"v9.9 {agent}\n")
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/tool.py" in out, out


def test_a_forged_base_brief_does_not_hide_a_deploy(tmp_path: Path) -> None:
    """Probe 2: the tree's brief and the base's brief blob both without `Deploy commands:`."""
    repo = _installed(tmp_path)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.write("docs/project-brief.md", _brief())
    repo.commit("a product change, no deploy command")
    assert _deploy(repo, "fly deploy")[0] == 2, "the control: the base's brief still declares it"
    _forge_at_main(repo, "docs/project-brief.md", _brief())
    code, out = _deploy(repo, "fly deploy")
    assert code == 2, out


def test_a_forged_base_workflow_does_not_hide_a_deploy_dispatch(tmp_path: Path) -> None:
    """The third read the review named: a dispatch runs the base's copy of a workflow."""
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    deploys = "name: Release\non: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: fly deploy\n"
    repo.write(".github/workflows/release.yml", deploys)
    repo.commit("a deploy workflow")
    repo.git("checkout", "-q", "work")
    repo.git("merge", "-q", "main")
    harmless = deploys.replace("fly deploy", "echo hi")
    repo.write(".github/workflows/release.yml", harmless)
    repo.write("src/app.py", "x = 2  # a product change\n")
    repo.commit("a product change")
    assert _deploy(repo, "gh workflow run release")[0] == 2, "the control: the base's copy deploys"
    blob = repo.git("rev-parse", "main:.github/workflows/release.yml")
    assert _cat(repo, "blob", blob) == deploys.encode()
    _forge_at_main(repo, ".github/workflows/release.yml", harmless)
    code, out = _deploy(repo, "gh workflow run release")
    assert code == 2, out
