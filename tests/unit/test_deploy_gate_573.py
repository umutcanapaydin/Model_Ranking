"""#573 (the #563 security review's R1): once the brief writes `Security-invariant tests:`, every test the line does
not name counts as test-and-CI, which re-opens no verdict while CI is green. The deploy gate's own control tests --
the tests of a policy module (`deploy_gate`, `review_need`, `brief_fields`) -- would then change the gate unreviewed.
A test of a policy module is code whatever the line says.
# covers #573
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def _script(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_573", ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _script("deploy_gate")


@pytest.mark.parametrize("path", ["tests/unit/test_deploy_gate_563.py", "tests/unit/test_review_need_572.py",
                                  "tests/unit/test_brief_fields.py", "conformance/test-review-need.py",
                                  "conformance/test-deploy-gate.py"])
@pytest.mark.parametrize("invariants", [[], ["tests/test_tenant_*.py"]], ids=["none", "a-glob"])
def test_573_a_test_of_a_policy_module_is_code_whatever_the_line_says(path: str, invariants: list[str]) -> None:
    assert GATE.change_class(path, invariants) == "code"


def test_573_any_other_test_still_counts_as_test_and_ci() -> None:
    """The control: the line keeps its meaning for every test that is not a policy module's."""
    assert GATE.change_class("tests/unit/test_api_scores.py", []) == "test-and-ci"
    assert GATE.change_class("conformance/test-prune-merged.py", []) == "test-and-ci"


def test_573_the_policy_modules_are_one_list() -> None:
    """Derived, not retyped: review_need routes the same modules the gate treats as policy."""
    assert _script("review_need").POLICY_MODULES == GATE.POLICY_MODULES
