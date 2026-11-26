"""Tester delta for #639 (D-257): the gaps fault injection found in the author's tests.

Each test fails when the line it names is broken: `conformance/` in REGISTER_CITE, the symlink and traversal refusals
of `_tree_file`, the later file read at the range's end (not the working tree), and the later file's working-tree
reader that wave-check uses.
# covers D-257
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .test_deploy_gate_d257 import GATE
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
