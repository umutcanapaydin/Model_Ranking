"""The release Tester of 2026-10-31, on #505 (D-231 clause 2): a guard of the comparison that no test held.

Fault injection at `290557c`: with `--work-tree=<root>` dropped from the untracked listing in `_new_files`, every
test of the deploy gate stayed green. The guard's `--judge` judges the folder it runs in, and `GIT_WORK_TREE` in
the environment points git's listing at another tree, as `core.worktree` does (`_redirected` refuses only that
setting). This test is red with the guard removed and green on the code as it is.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .test_deploy_gate_pin import GATE, _env, _installed


def test_a_work_tree_named_in_the_environment_does_not_hide_a_new_file_from_the_judge(tmp_path: Path) -> None:
    """#505 (the #505 review's M2, by the environment): the untracked listing names its own tree, so a new code
    file in the folder judged is a change, whatever `GIT_WORK_TREE` says."""
    repo = _installed(tmp_path)
    clean = tmp_path / "clean"
    repo.git("worktree", "add", "-q", "--detach", str(clean), "HEAD")
    repo.write("src/new.py", "x = 3\n")
    gate = subprocess.run([sys.executable, str(GATE), "--judge"], cwd=repo.root, capture_output=True, text=True,
                          input=json.dumps({"commands": [["fly", "deploy"]]}),
                          env={**_env(), "GIT_WORK_TREE": str(clean)}, timeout=120)
    out = gate.stdout + gate.stderr
    assert gate.returncode != 0, out
    assert "src/new.py" in out, out
