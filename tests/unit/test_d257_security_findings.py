"""The Security-Reviewer's M1-M3 on #639 (D-257; `docs/reviews/enhancement-issue-639-process-light-security.md`).

M1: whether the register form is in force is read from the protected bases only, so a change cannot switch it on by
naming a register on the brief's line itself. M2: under the register form only a test FILE is a record; a conftest,
`tests/skips.py`, a package `__init__` or a fixture stays code, since it can drop or change what a cited test runs.
M3: `later` answers only a non-BLOCKING finding whose row in `docs/later.md` gives a LOW reason.
# covers D-257
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_731_tester import _brief, _commit, _gate, _git, _write
from .test_deploy_gate_d257 import CITING, DERIVED, GATE, REGISTER, _edit, _repo
from .test_findings_later import WAVE

GLOB_LINE = "- **Security-invariant tests:** `tests/test_tenant_*.py`"


def test_a_change_cannot_switch_the_register_form_on_for_itself(tmp_path: Path) -> None:
    root, env = _repo(tmp_path, CITING, base_line=False)
    # main (the base) names only a glob; the change names the register too, a file the base already holds.
    _git(root, env, "checkout", "-q", "main")
    _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", GLOB_LINE))
    base = _commit(root, env, "docs: a glob-only line at the base")
    _write(root, "docs/reviews/release-security.md",
           f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {base}\n")
    _write(root, "docs/reviews/release-tester.md",
           f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {base}\n")
    _commit(root, env, "docs: the verdicts at the glob-only base")
    _git(root, env, "checkout", "-q", "-B", "change")
    _write(root, "docs/project-brief.md",
           _brief("- **Deploy commands:** `./deploy.sh prod`", f"{GLOB_LINE}, `{REGISTER}`"))
    _commit(root, env, "docs: the change names the register")
    _edit(root, env, "tests/test_app.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/test_app.py" in out, out


@pytest.mark.parametrize("path", ["tests/conftest.py", "tests/unit/conftest.py", "tests/skips.py",
                                  "tests/__init__.py", "tests/fixtures/scores.json", "tests/unit/_helpers.py"])
def test_under_the_register_a_test_support_file_stays_code(path: str) -> None:
    assert GATE.change_class(path, DERIVED) == "code"


def test_a_conftest_change_is_refused_with_ci_red(tmp_path: Path) -> None:
    root, env = _repo(tmp_path, CITING)
    _edit(root, env, "tests/conftest.py", "collect_ignore = ['test_tenant_scope.py']\n")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/conftest.py" in out, out


TABLE = "| finding | what | why later |\n|---|---|---|\n"


def test_a_row_whose_reason_is_not_low_is_no_later_key() -> None:
    assert WAVE.later_rows(TABLE + "| `a.md R1` | x | MEDIUM, user-visible |\n") == set()
    assert WAVE.later_rows(TABLE + "| `a.md R1` | x | LOW: nobody sees it |\n") == {"a.md r1"}


def test_a_blocking_finding_cannot_be_answered_later() -> None:
    rows = WAVE.later_rows(TABLE + "| `fix-issue-9-security.md B1` | x | LOW: says the author |\n")
    assert rows == {"fix-issue-9-security.md b1"}
    why = WAVE.later_problem(rows, "fix-issue-9-security.md", "security", "B1")
    assert why and "BLOCKING" in why


def test_a_test_module_a_cited_test_imports_is_code_too() -> None:
    files = {
        "r.md": b"| INV-1 | x | D-1 | `tests/unit/test_scope.py::test_a` |",
        "tests/unit/test_scope.py": b"from .test_api_v1 import client\nfrom tests.unit.test_build import built\n",
        "tests/unit/test_api_v1.py": b"from .test_router_hints import hints\n",
        "tests/unit/test_build.py": b"import os\n",
        "tests/unit/test_router_hints.py": b"x = 1\n",
    }
    expanded = GATE.expand_invariants(["r.md"], files.get)
    assert expanded is not None
    for rel in ("tests/unit/test_api_v1.py", "tests/unit/test_build.py", "tests/unit/test_router_hints.py"):
        assert rel in expanded, expanded
        assert GATE.change_class(rel, expanded) == "code"
    assert GATE.change_class("tests/unit/test_other.py", expanded) == "record"
