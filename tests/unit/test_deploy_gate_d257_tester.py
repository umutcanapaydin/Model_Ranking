"""Tester delta for #639 (D-257): the gaps fault injection found in the author's tests.

Each test fails when the line it names is broken: `conformance/` in REGISTER_CITE, the symlink and traversal refusals
of `_tree_file`, the later file read at the range's end (not the working tree), and the later file's working-tree
reader that wave-check uses.
# covers D-257
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_731_tester import _brief, _commit, _gate, _git, _write
from .test_deploy_gate_d257 import CITING, GATE, _edit
from .test_deploy_gate_d257 import _repo as _gate_repo
from .test_findings_later import LATER, WAVE, _check, _repo


def test_a_register_citing_a_conformance_test_makes_it_code() -> None:
    cited = GATE.register_tests("| INV-9 | x | D-9 | `conformance/test-commit-identity.py::test_a` |")
    assert cited == ["conformance/test-commit-identity.py"]
    assert GATE.expand_invariants(["r.md"], {"r.md": b"`conformance/test-x.py`"}.get) == [
        "r.md", "conformance/test-x.py"]


def test_the_tree_reader_refuses_a_symlink_a_parent_path_and_an_absolute_path(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "r.md").write_text("`tests/a.py`", encoding="utf-8")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("`tests/b.py`", encoding="utf-8")
    (tmp_path / "docs" / "link.md").symlink_to(outside)
    assert GATE._tree_file(tmp_path, "docs/r.md") == b"`tests/a.py`"
    assert GATE._tree_file(tmp_path, "docs/link.md") is None
    assert GATE._tree_file(tmp_path, f"../{outside.name}") is None
    assert GATE._tree_file(tmp_path, str(outside)) is None


def test_a_later_row_only_in_the_working_tree_does_not_answer_a_finding(tmp_path: Path) -> None:
    proj, base, fix = _repo(tmp_path, None)
    (proj / "docs" / "later.md").write_text(LATER, encoding="utf-8")  # untracked: the range's end holds none
    rc, out = _check(tmp_path, proj, base, f"| security M1 | fixed {fix[:7]} |\n| security R1 | later |\n")
    assert rc == 1 and "R1" in out and "docs/later.md" in out, out


def test_wave_check_reads_the_later_file_of_the_working_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert WAVE.later_keys() == set()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "later.md").write_text(LATER, encoding="utf-8")
    assert WAVE.later_keys() == {"fix-issue-12-security.md r1"}
    assert WAVE.later_problem(WAVE.later_keys(), "fix-issue-12-security.md", "security", "R1") is None
    assert "docs/later.md" in (WAVE.later_problem(set(), "fix-issue-12-security.md", "security", "R1") or "")


def test_a_parent_relative_import_resolves_one_directory_up_per_extra_dot() -> None:
    # covers D-257 (Security M31 on #639)
    assert GATE._imported_tests("tests/unit/test_a.py", "from ..sub.h import y\n") == ["tests/sub/h.py"]
    assert GATE._imported_tests("tests/unit/test_a.py", "from .h import y\n") == ["tests/unit/h.py"]
    assert GATE._imported_tests("tests/unit/test_a.py", "from ...x import y\n") == []  # leaves tests/


@pytest.mark.parametrize("reason", ["LARGE: a big one", "LATER", "L", "MEDIUM, user-visible"])
def test_only_a_reason_that_starts_low_makes_a_later_key(reason: str) -> None:
    # covers D-257 (Security M32 on #639)
    table = "| finding | what | why |\n|---|---|---|\n"
    assert WAVE.later_rows(table + f"| `a.md R1` | x | {reason} |\n") == set()


def test_one_base_without_the_register_keeps_the_form_off(tmp_path: Path) -> None:
    # covers D-257 (Security M30 on #639): the form is on only when EVERY protected base names a register.
    from .test_d257_security_findings import GLOB_LINE

    root, env = _gate_repo(tmp_path, CITING)
    _git(root, env, "checkout", "-q", "main")
    _write(root, "docs/project-brief.md", _brief("- **Deploy commands:** `./deploy.sh prod`", GLOB_LINE))
    tip = _commit(root, env, "docs: main's tip names globs only")
    _write(root, "docs/reviews/release-security.md",
           f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {tip}\n")
    _write(root, "docs/reviews/release-tester.md",
           f"# v\n**Independent:** yes\n\n## Verdict\nPASS\n\n**Reviewed head:** {tip}\n")
    _commit(root, env, "docs: the verdicts at main's tip")
    _git(root, env, "checkout", "-q", "change")
    _edit(root, env, "tests/test_app.py")
    rc, out = _gate(root, env, "--check")
    assert rc == 1 and "tests/test_app.py" in out, out
