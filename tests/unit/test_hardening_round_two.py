"""The hardening wave's second review (`docs/reviews/backlog-hardening-review-round-2.md`): each finding,
planted. Every plant goes into a copy under `tmp_path`; the app's files are never written."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from tests.unit import test_router_hints as hints
from tests.unit import test_swift_tests_offline as offline
from tests.unit.test_ios_client_contract import _record_matches
from tests.unit.test_swift_reads import explained
from tests.unit.test_wave_check_backlog_order import WITH_D2, _branch
from tests.unit.test_wave_check_m21_rules import _commit, _module


def test_a_hook_whose_super_call_is_only_a_comment_skips_the_base(tmp_path: Path,
                                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """N1: the super check read the subclasses raw, so `// super.tearDown()` passed as a call."""
    shutil.copytree(offline.TESTS, tmp_path / "EngineTests")
    path = tmp_path / "EngineTests" / "StandingsStoreTests.swift"
    code = path.read_text(encoding="utf-8")  # raw: a plant in a copy
    call = re.search(r"\n(\s+)(super\.(?:tearDown|setUp)\(\))", code)
    assert call, "the plant's file calls no super"
    path.write_text(code[:call.start(2)] + "// " + code[call.start(2):], encoding="utf-8")
    monkeypatch.setattr(offline, "TESTS", tmp_path / "EngineTests")
    with pytest.raises(AssertionError, match="overrides that skip the base"):
        offline.test_the_base_checks_every_test_and_calls_through()


@pytest.mark.parametrize(("line", "ok"), [
    ('    view = _swift(CLIENT / "ContentView.swift")', False),
    ('    view = _swift(CLIENT / "ContentView.swift")  # keeps //: the pin cuts its section at // MARK:', True),
    ('    view = _swift(CLIENT / "ContentView.swift")  # keeps //:', False),
    ('    view = _code((CLIENT / "ContentView.swift").read_text(encoding="utf-8"))', True),
])
def test_swift_which_keeps_line_comments_needs_its_reason(line: str, ok: bool) -> None:
    """N2: D-198 clause 4 allows `_swift` only where a pin cuts a line at its `//`; the guard took it anywhere."""
    assert explained(line) is ok


def test_a_backlog_adr_beside_a_build_file_is_refused(tmp_path: Path) -> None:
    """N4: only `tests/` was added to the code the rule reads, so a decision written beside a `Makefile`,
    `pyproject.toml` or `conformance/` change passed."""
    for name, rel in (("make", "Makefile"), ("toml", "pyproject.toml"), ("conf", "conformance/x.yml")):
        root = _branch(tmp_path / name)
        _commit(root, "rule and build", "2026-10-10T13:00:00", {"docs/decisions.md": WITH_D2, rel: "x\n"})
        problems, _ = _module("wave_check").branch_adr_problems(root)
        assert any("D-2" in p for p in problems), (rel, problems)


def test_a_question_quoted_in_a_wrapped_blockquote_is_found() -> None:
    """N5: a blockquote wraps with `> ` on each line, which the record scan read as words. Made up."""
    long = "which model would best plan a three day hike in the alps"
    quoted = "> The probe asked: which model would best plan\n> a three day hike in the alps\n"
    assert _record_matches({long}, {"docs/a.md": quoted}) == {"docs/a.md": 1}


def test_a_url_typed_through_its_module_is_egress() -> None:
    """N6: `var url: Foundation.URL` passed every text pin, where `var url: URL` is refused."""
    assert any(re.search(pattern, "    var url: Foundation.URL {") for pattern in hints.EGRESS)
