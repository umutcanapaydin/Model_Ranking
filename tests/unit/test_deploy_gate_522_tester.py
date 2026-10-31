"""D-232 clause 2 (#522), the release Tester, delta round 2026-10-31b: three parts of `_UNREAD_IN_WORKFLOW` that no
test held.

Each spelling below stayed exemptible under one fault that every deploy-gate test passed with:
- `pushd` dropped from the change-of-directory words (`UNREAD_RECIPES | {"cd", "pushd"}`);
- `--chdir` dropped from the `env` alternative (only `-C` was tested);
- `/` added to the runner's look-behind, so a runner written with its path inside a `-c` string (`bash -c
  '/usr/bin/make ship'`) is no longer seen; the first-word basename check covers only `run: /usr/bin/make`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_494 import _brief
from .test_deploy_gate_522 import STEP, _reviewed_workflow
from .test_deploy_gate_pin import _installed


@pytest.mark.parametrize("step", [
    "      - run: |\n          pushd scripts\n          ./ship_it.sh\n",
    "      - run: env --chdir scripts ./ship_it.sh\n",
    "      - run: env --chdir=scripts ./ship_it.sh\n",
    "      - run: bash -c '/usr/bin/make ship'\n",
    "      - run: sh -c \"./make ship\"\n",
], ids=["pushd-then-relative", "env-chdir", "env-chdir-equals", "make-by-path-in-bash-c", "make-dot-slash-in-sh-c"])
def test_what_a_dispatched_workflow_starts_through_these_is_not_exempt(tmp_path: Path, step: str) -> None:
    """# covers D-232 clause 2, #522: each red under the fault its id names (see the module docstring)."""
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/ship_it.sh", "echo ship\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ship_it.sh" in out, out
