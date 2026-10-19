"""#328: the guard test's fixture commits start no background git maintenance.

`git commit` starts `git maintenance run --auto --quiet --detach`, which takes
`.git/objects/maintenance.lock` after the commit has returned. `conformance/test-bash-guard.py` copies the
fixture project with `shutil.copytree` right after building it; a lock that vanishes mid-copy raised
`shutil.Error` and killed the test in CI (#339 and #343, run bug-night). The fixture's `git()` turns
automatic maintenance off, so nothing writes into the project's `.git` once a commit returns.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "conformance" / "test-bash-guard.py"


def _guard_test() -> ModuleType:
    spec = importlib.util.spec_from_file_location("guard_test_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_git_turns_automatic_maintenance_off(tmp_path: Path) -> None:
    guard_test = _guard_test()
    proj, _head = guard_test.fixture(tmp_path)
    assert guard_test.git(proj, "config", "--get", "maintenance.auto") == "false"
    assert guard_test.git(proj, "config", "--get", "gc.auto") == "0"
