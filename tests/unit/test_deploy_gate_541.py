"""#541 (the fixes-1031 delta security review's M2, and the release delta review's M12): more spellings in a dispatched
deploy workflow left the script they start exempt. `_UNREAD_IN_WORKFLOW` named the ways to change directory one by
one (`cd`, `pushd`, `working-directory:`, `env -C`, `env --chdir`), and a file was on the surface only when the
workflow wrote its path from the checkout's top, so every other way -- an `env` long option that is a prefix of
`--chdir`, `env -S`, `sudo -D`, a PATH entry or `$GITHUB_PATH`, a checkout's `path:`, `os.chdir` in `python -c`, a
module run by `-m` -- started a tree file the gate did not see.

D-237: the class is closed by what every such spelling still writes, the file's name. Every file git lists whose
name, or whose name less its last suffix (a module), is a word of the dispatched workflow's text is on the surface,
under whatever prefix it lies.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_494 import _brief
from .test_deploy_gate_522 import STEP, _reviewed_workflow
from .test_deploy_gate_pin import _installed

SPELLINGS = {
    # The issue's four.
    "env-chdir-prefix-equals": "      - run: env --c=scripts ./ship_it.sh\n",
    "env-chdir-prefix": "      - run: env --chd scripts ./ship_it.sh\n",
    "env-split-string": "      - run: env -S'-C scripts ./ship_it.sh'\n",
    "path-assignment": "      - run: PATH=\"$PWD/scripts:$PATH\" ship_it.sh\n",
    "github-path": "      - run: echo \"$PWD/scripts\" >> \"$GITHUB_PATH\"\n      - run: ship_it.sh\n",
    # The release delta review's M12.
    "sudo-D": "      - run: sudo -D scripts ./ship_it.sh\n",
    "sudo-chdir-equals": "      - run: sudo --chdir=scripts ./ship_it.sh\n",
    "checkout-path": "      - uses: actions/checkout@v4\n        with:\n          path: sub\n      - run: sub/scripts/ship_it.sh\n",
    "python-chdir": "      - run: python -c \"import os; os.chdir('scripts'); os.system('./ship_it.sh')\"\n",
    # The same class, spelled in ways no list names.
    "export-path": "      - run: |\n          export PATH=scripts:$PATH\n          ship_it.sh\n",
    "env-option-cluster": "      - run: env -vS'-C scripts ./ship_it.sh'\n",
    "quoted-pieces": "      - run: sudo -D scripts ./'ship'_it.sh\n",
    "expansion-inside": "      - run: sudo -D scripts ./ship_${EMPTY}it.sh\n",
}


@pytest.mark.parametrize("step", list(SPELLINGS.values()), ids=list(SPELLINGS))
def test_a_script_started_under_another_prefix_is_not_exempt(tmp_path: Path, step: str) -> None:
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/ship_it.sh", "echo ship\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ship_it.sh" in out, out


@pytest.mark.parametrize("step", [
    "      - run: python -m scripts.ship_it\n",
    "      - run: python -c 'import sys; sys.path.insert(0, \"scripts\"); import ship_it'\n",
], ids=["module", "import"])
def test_a_module_started_by_its_name_is_not_exempt(tmp_path: Path, step: str) -> None:
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/ship_it.py", "print('ship')\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ship_it.py" in out, out


@pytest.mark.parametrize("step", [
    "      - run: sudo -D scripts ./ship_it.sh\n",
    "      - run: sudo -D scripts ./toolbox.sh && ./my_tool.sh\n",
], ids=["another-name", "inside-a-longer-name"])
def test_a_name_the_workflow_does_not_write_stays_devflows(tmp_path: Path, step: str) -> None:
    """Stays quiet (writing-a-control §2): a workflow that starts a script under another prefix does not take every
    tooling file with it; `scripts/tool.py`, whose name it never writes (`toolbox`, `my_tool` are other names), is
    still exempt."""
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/tool.py", "VERSION = 2\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code == 0, out
