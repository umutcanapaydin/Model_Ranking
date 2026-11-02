"""#556 (the fixes-1101 rest review's R4): when D-239's check found no start of a file without its name, `make
deploy-check` printed nothing for it, so a PASS carried no evidence that the dispatched deploy workflows were read.
Now it prints one line naming the workflows read and how many run commands it read in them.
# covers #556, D-239
"""

from __future__ import annotations

from pathlib import Path

from .test_deploy_gate_494 import _brief
from .test_deploy_gate_549 import _dispatched
from .test_deploy_gate_pin import _installed


def _d239_line(out: str) -> str:
    return next((line for line in out.splitlines() if line.startswith("deploy-check: workflows:")), "")


def test_a_pass_names_the_workflows_read_and_counts_their_run_commands(tmp_path: Path) -> None:
    """covers #556: two run commands in one step of the dispatched `release.yml` are read and counted."""
    repo = _dispatched(tmp_path, "      - run: |\n          scripts/ship_it.sh\n          echo done\n")
    code, out = repo.check()
    assert code == 0, out
    line = _d239_line(out)
    assert "release.yml" in line and "2 run command(s)" in line and "no start of a file without its name" in line, out


def test_the_count_follows_the_workflow(tmp_path: Path) -> None:
    """covers #556: the count is measured, not a constant -- one command reads 1."""
    repo = _dispatched(tmp_path, "      - run: scripts/ship_it.sh\n")
    code, out = repo.check()
    assert code == 0, out
    assert "1 run command(s)" in _d239_line(out), out


def test_a_brief_that_dispatches_no_workflow_says_so(tmp_path: Path) -> None:
    """covers #556: with no dispatched deploy workflow there is nothing to read, and the line says that too."""
    repo = _installed(tmp_path)
    assert "gh workflow run" not in _brief("fly deploy"), "the control: this brief dispatches no workflow"
    _code, out = repo.check()
    assert "no dispatched deploy workflow" in _d239_line(out), out
