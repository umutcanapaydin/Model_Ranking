"""The release delta Tester of `integration/fixes-1101` (2026-11-01): D-237 for a file whose name has capitals.

D-237 (#541): every file git lists whose name a dispatched deploy workflow writes is on the deploy surface, under any
prefix. `_files` keys the tree by lower-cased path, so `_named_by_name` lower-cases the text it reads; every range
test names a lower-case file (`ship_it.sh`). Fault F-N7 (the text not lower-cased) stayed green, and with it a script
spelled with capitals and started under another prefix, written exactly as git lists it, left the surface.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_444 import _upgrade_shipping
from .test_deploy_gate_494 import _brief
from .test_deploy_gate_522 import STEP, _reviewed_workflow
from .test_deploy_gate_pin import _installed


# covers D-237, #541
@pytest.mark.parametrize("step", [
    "      - run: env --chd scripts ./ShipIt.sh\n",
    "      - run: sudo -D scripts ./ShipIt.sh\n",
    "      - run: |\n          export PATH=scripts:$PATH\n          ShipIt.sh\n",
], ids=["env-chdir-prefix", "sudo-D", "export-path"])
def test_a_script_with_capitals_in_its_name_started_under_another_prefix_is_not_exempt(tmp_path: Path,
                                                                                       step: str) -> None:
    repo = _installed(tmp_path)
    _reviewed_workflow(repo, STEP.format(step))
    _upgrade_shipping(repo, "scripts/ShipIt.sh", "echo ship\n", brief=_brief("gh workflow run release"))
    code, out = repo.check()
    assert code != 0, out
    assert "scripts/ShipIt.sh" in out, out
