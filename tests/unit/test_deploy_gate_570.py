"""#570 (the #556 security review's R1): `make deploy-check`'s D-239 line counted a CRLF workflow's run commands twice.

The tree's copy is read as text, with its line endings normalised; a protected base's copy is read from its blob,
with them kept. The two copies then differ, and the count ran over each, so one run command read `2`. The count is
over copies that differ after `\\r\\n` is read as `\\n`; every distinct copy is still read for findings.
# covers #570
"""

from __future__ import annotations

from pathlib import Path

from .test_deploy_gate_522 import STEP
from .test_deploy_gate_549 import BRIEF, _reviewed_workflow
from .test_deploy_gate_556 import _d239_line
from .test_deploy_gate_pin import _installed


def test_570_a_crlf_workflow_counts_each_run_command_once(tmp_path: Path) -> None:
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format("      - run: scripts/ship_it.sh\n").replace("\n", "\r\n"))
    repo.write("docs/project-brief.md", BRIEF)
    repo.commit("the brief dispatches the workflow")
    assert b"\r\n" in (repo.root / ".github/workflows/release.yml").read_bytes(), "the control: CRLF on disk"
    _code, out = repo.check()
    line = _d239_line(out)
    assert "release.yml read" in line and "1 run command(s)" in line, out
