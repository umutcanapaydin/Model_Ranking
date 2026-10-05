"""Tester (#131): a name cited in a test file must be a test, and a place written in the form the PRD
documents is checked like any other place."""

from __future__ import annotations

from pathlib import Path

import pytest

from . import test_prd_citations as citations

FILES = {"tests/unit/test_x.py": ["import os", "", "def _helper():", "    pass", "", "def test_a():", "    _helper()"]}
BY_NAME = {"test_x.py": ["tests/unit/test_x.py"]}


def test_a_helper_of_a_test_file_is_not_a_test() -> None:
    """#131: in a test file a name must be "a test, a class of tests, or the file's `pytestmark`".
    A helper is declared there too, and is not evidence."""
    read = FILES.__getitem__
    assert not citations.problems("Evidence: test_x.py::test_a", BY_NAME, read)
    assert citations.problems("Evidence: test_x.py::_helper", BY_NAME, read), "a helper passed as a test"


def test_a_place_in_the_form_the_prd_documents_is_checked_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#131: the PRD's header and the place check's docstring write a place as "in `::<test_name>`".
    A place written that way must have its code in the test it names, as one written "in ::name" does."""
    (tmp_path / "test_x.py").write_text("def test_a():\n    clear()\n\n\ndef test_b():\n    pass\n", encoding="utf-8")
    prd = tmp_path / "prd.md"
    prd.write_text("Evidence: test_x.py::test_a (`clear()` exercised in ::test_a), "
                   "::test_b (`clear()` exercised in `::test_b`)\n", encoding="utf-8")
    monkeypatch.setattr(citations, "ROOT", tmp_path)
    monkeypatch.setattr(citations, "PRD", prd)
    monkeypatch.setattr(citations, "tracked", lambda: {"test_x.py": ["test_x.py"]})
    with pytest.raises(AssertionError, match="does not hold"):
        citations.test_a_place_the_prd_points_into_holds_the_code_it_names()
