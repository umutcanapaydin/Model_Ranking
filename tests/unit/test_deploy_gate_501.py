"""#501: `deploy_surface` read a declared command's words as paths, so some spellings started a file it never named.

What a declared deploy command starts is code even when an upgrade shipped it byte for byte (#444 M3). The surface
named only the words that were paths git lists, so a command that reaches its script another way -- through `cd`, an
expansion, an interpreter, a recipe runner, `bash -c`, or a dispatched workflow that runs `make` -- left that script
exemptible (the #494 security review's M1). D-231 clause 1: the gate reads a declared command only through the
programs it knows; any other program, and a path-like word that names no file git lists, exempts nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_494 import _brief
from .test_deploy_gate_pin import _installed

MAKES = "name: Release\non: workflow_dispatch\njobs:\n  a:\n    steps:\n      - run: make ship\n"


@pytest.mark.parametrize(("rel", "command"), [
    ("scripts/ship_it.sh", "cd scripts && ./ship_it.sh"),
    ("scripts/ship_it.sh", "$PWD/scripts/ship_it.sh"),
    ("scripts/ship_it.py", "python -m scripts.ship_it"),
    ("scripts/ship/__main__.py", "python3 scripts/ship"),
    ("scripts/ship_it.sh", "just ship"),
    ("scripts/ship_it.sh", "bash -c 'make ship'"),
    ("scripts/ship_it.sh", "fly deploy --build-secret run=$PWD/scripts/ship_it.sh"),
    # The #501 review's M1, M3, R1, R2: a second command after the first, a shell given a word that names no file,
    # a workflow dispatched by an id, and an assignment that makes the shell run a script first.
    ("scripts/ship_it.sh", "fly deploy && make ship"),
    ("scripts/ship_it.sh", "fly deploy; make ship"),
    ("scripts/ship_it.sh", "fly deploy | python -m scripts.ship_it"),
    ("scripts/ship_it.sh", "bash ship"),
    ("scripts/ship_it.sh", "gh workflow run 12345"),
    ("scripts/ship_it.sh", "BASH_ENV=scripts/ship_it.sh bash scripts/deploy_hosted_engine.sh"),
], ids=["cd-then-relative", "expansion", "python-module", "directory", "just-recipe", "bash-c", "known-program-expansion",
        "and-then", "semicolon", "pipe", "shell-bare-word", "workflow-id", "assignment-first"])
def test_a_command_read_through_no_known_program_exempts_nothing(tmp_path: Path, rel: str, command: str) -> None:
    repo = _installed(tmp_path)
    _upgrade_shipping(repo, rel, "echo ship\n", brief=_brief(command))
    code, out = repo.check()
    assert code != 0, out
    assert rel in out, out


@pytest.mark.parametrize("runner", ["make", "just"])
def test_a_dispatched_workflow_that_runs_a_recipe_exempts_nothing(tmp_path: Path, runner: str) -> None:
    repo = _installed(tmp_path)
    repo.git("checkout", "-q", "main")
    repo.write(".github/workflows/release.yml", MAKES.replace("make", runner))
    repo.commit("a workflow that runs make")
    _upgrade_shipping(repo, "scripts/ship_it.sh", "echo ship\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ship_it.sh" in out, out


@pytest.mark.parametrize("command", ["fly deploy", "scripts/deploy_hosted_engine.sh",
                                     "bash scripts/deploy_hosted_engine.sh", "gh workflow run release"])
def test_a_known_program_still_leaves_a_plain_tooling_file_devflows(tmp_path: Path, command: str) -> None:
    """The control: each program D-231 names, reading a script git lists, still exempts a file it does not start."""
    repo = _installed(tmp_path)
    # `fly deploy` is the fixture's own declaration, so its brief is not written again.
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=None if command == "fly deploy" else _brief(command))
    code, out = repo.check()
    assert code == 0, out
