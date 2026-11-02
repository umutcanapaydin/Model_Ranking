"""#562 (the v7.3.1 upgrade's release delta security review, M16): `.deps-accept` -- the advisories `make deps`
accepts, "only the owner adds an entry" -- was a RECORD to the deploy gate and routed to no review, so an agent's
waiver of a vulnerable dependency could reach a deploy unreviewed. Now it is treated as `data/accepted-cuts.yaml` is
(D-221 clause 4): an exception to a safety control, so a change to it is a policy edit (a security review in either
mode) and code to the deploy gate.
# covers #562
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from .test_deploy_gate_pin import _installed
from .test_review_need_base_policy import Repo, _brief

ROOT = Path(__file__).resolve().parents[2]
ENTRY = "PYSEC-2099-1 #562 2026-12-31 a waiver the agent wrote\n"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(f"{name}_562", ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT / "scripts"))
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(("mode", "want"), [("light", "review-need: security"),
                                            ("heavy", "review-need: code-reviewer+security")])
def test_a_change_to_the_waiver_file_goes_to_a_security_review(tmp_path: Path, mode: str, want: str) -> None:
    """covers #562: a range that edits only `.deps-accept` is a policy edit, in either mode."""
    repo = Repo(tmp_path / mode, _brief(mode))
    repo.write(".deps-accept", ENTRY)
    repo.commit("deps: a waiver")
    _, last, out = repo.need()
    assert last == want, out
    assert "policy edit: .deps-accept" in out, out


def test_the_deploy_gate_counts_the_waiver_file_as_code() -> None:
    """covers #562: not a record the gate ignores."""
    gate = _script("deploy_gate")
    assert not gate.is_deploy_record(".deps-accept")
    assert gate.change_class(".deps-accept") == "code"


def test_a_waiver_added_after_the_verdicts_makes_them_stale(tmp_path: Path) -> None:
    """covers #562: through the real entry point, `make deploy-check`'s question -- a waiver committed after both
    verdicts' reviewed head is a change they did not see."""
    repo = _installed(tmp_path)
    assert repo.check()[0] == 0, "the control: the verdicts are current"
    repo.write(".deps-accept", ENTRY)
    repo.commit("deps: a waiver after the review")
    code, out = repo.check()
    assert code != 0 and ".deps-accept" in out, out


def test_review_need_names_the_file_deps_accept_reads() -> None:
    """covers #562: the routed path is the one `scripts/deps_accept.py` reads, derived rather than retyped."""
    deps_accept = _script("deps_accept")
    assert str(deps_accept.FILE.relative_to(deps_accept.ROOT)) in _script("review_need").EXCEPTION_FILES
