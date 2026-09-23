"""`make check-fast` -- DevFlow v6.6's `scripts/check_fast.py`, with this project's own legs.

The script is DevFlow's, unchanged. What this project adds lives in `stack.mk`: the iOS client check
and the Swift suite each get a leg of their own, and the Swift suite runs in its parallel form. These
tests hold that configuration against the real Makefile, so a setting that silently matches nothing,
or a gate that falls out of every leg, is red here and not only in the conformance run.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_fast.py"


def _mod() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_fast", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan() -> dict[str, list[str]]:
    result = subprocess.run([sys.executable, str(SCRIPT), "--plan"], cwd=ROOT, capture_output=True,
                            encoding="utf-8", check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    plan = {}
    for line in result.stdout.splitlines():
        name, sep, targets = line.partition(":")
        if sep and not name.startswith("check-fast"):
            plan[name.strip()] = targets.split()
    assert plan, "fails closed: the plan printed no leg"
    return plan


def test_the_project_legs_are_seen_and_every_gate_runs_once() -> None:
    plan = _plan()
    assert plan["client-decls"] == ["client-decls"]
    assert plan["swift-test"] == ["swift-test=swift-test-parallel"]
    shown = [t.split("=")[0] for targets in plan.values() for t in targets]
    prereqs = _mod().check_prerequisites((ROOT / "Makefile").read_text(encoding="utf-8"))
    assert sorted(shown) == sorted(prereqs)


def test_the_coverage_floor_runs_after_the_tests_it_reads() -> None:
    """W-041's floor reads the coverage.json pytest writes. Under v6.6 a separate `check:`
    prerequisite would land in the records leg, beside the tests, and read the previous run's file;
    so it runs inside the `test` recipe, after pytest, and is no leg of its own."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\ntest: ", 1)[1].split("\n\n", 1)[0]
    assert recipe.index("pytest") < recipe.index("module_coverage_floor.py")
    assert "coverage-floor" not in _mod().check_prerequisites(makefile)


def test_a_setting_that_names_no_check_prerequisite_fails() -> None:
    _, _, problems = _mod().settings(["lint", "test"], ["client-decls"], ["swift-test=swift-test-parallel"])
    assert len(problems) == 2


def test_an_empty_check_line_fails_closed() -> None:
    with pytest.raises(ValueError):
        _mod().check_prerequisites("gate: check\n")
