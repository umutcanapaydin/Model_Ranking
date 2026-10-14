"""The hardening wave's first review (`docs/reviews/backlog-hardening-review-round-1.md`): each finding, planted.

Every plant goes into a copy under `tmp_path`; the app's files are never written."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.unit import test_ios_client_contract as contract
from tests.unit import test_ios_visual_contract as visual
from tests.unit import test_swift_tests_offline as offline
from tests.unit.test_language_rule_escapes import _flagged
from tests.unit.test_wave_check_backlog_order import WITH_D2, _branch
from tests.unit.test_wave_check_m21_rules import _commit, _module

ROOT = Path(__file__).resolve().parents[2]


def test_the_offline_base_pins_read_its_built_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M1: both pins on `OfflineTestCase.swift` read it raw, and a block-commented copy of its tearDown above
    a live one that asserts nothing passed them."""
    shutil.copytree(offline.TESTS, tmp_path / "EngineTests")
    base = tmp_path / "EngineTests" / offline.BASE
    code = base.read_text(encoding="utf-8")  # raw: a plant in a copy
    start = code.index("    override func tearDown() {")
    end = code.index("\n    }\n", start) + len("\n    }\n")
    base.write_text(code[:start] + "    /*\n" + code[start:end] + "    */\n"
                    + "    override func tearDown() {\n        super.tearDown()\n    }\n" + code[end:], encoding="utf-8")
    monkeypatch.setattr(offline, "TESTS", tmp_path / "EngineTests")
    for pin in (offline.test_the_base_checks_every_test_and_calls_through,
                offline.test_the_base_fails_a_test_whose_requests_it_recorded):
        with pytest.raises(AssertionError):
            pin()


def test_a_pin_moved_by_275_refuses_a_line_comment_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M2: `_swift` keeps `//` comments, so a `//` copy of a required line satisfied a pin #275 moved to it."""
    shutil.copytree(visual.CLIENT, tmp_path / "ModelRanking")
    view = tmp_path / "ModelRanking" / "ContentView.swift"
    code = view.read_text(encoding="utf-8")  # raw: a plant in a copy
    line = "Text(UIText.openEvidence(language))"
    assert code.count(line) == 1
    view.write_text(code.replace(line, f"Text(\"\") // {line}"), encoding="utf-8")
    monkeypatch.setattr(visual, "CLIENT", tmp_path / "ModelRanking")
    with pytest.raises(AssertionError):
        visual.test_the_model_card_is_the_detail_navigation_label()


def test_a_question_a_record_wraps_or_spaces_or_ticks_is_found() -> None:
    """M3: Markdown wraps lines, doubles spaces and quotes in backticks; the record scan read none of it.
    Made-up questions, never real ones."""
    long = "which model would best plan a three day hike in the alps"
    short = "best model for haiku"
    wrapped = long.replace(" a three", "\na three").replace(" hike", "  hike")
    assert contract._record_matches({long}, {"docs/a.md": f"The probe asked: {wrapped}."}) == {"docs/a.md": 1}
    assert contract._record_matches({short}, {"docs/b.md": f"It read `{short}` as a search."}) == {"docs/b.md": 1}
    assert contract._record_matches({short}, {"docs/c.md": f"the {short} and more"}) == {}


def test_l1_reads_a_raw_string_escape_and_an_escaped_backtick_opens_no_span(tmp_path: Path) -> None:
    """N2: Swift's raw-string escape `\\#u{...}` was not decoded, and an escaped backtick, decoded before the
    code spans were stripped, wrapped raw Turkish in a span."""
    flagged = _flagged(tmp_path, {
        "Raw.swift": 'let line = #"bu bir \\#u{15F}ey"#\n',
        "tick.json": '["\\u0060\\u015fey\\u0060"]\n',
    })
    assert flagged == {"Raw.swift", "tick.json"}, flagged


def test_the_backlog_rule_names_the_range_it_read_and_counts_tests_as_code(tmp_path: Path) -> None:
    """N3: the message named no range, so a stale `origin/main` read as a finding about merged work. K1: a
    decision first written beside its own tests passed."""
    root = _branch(tmp_path)
    _commit(root, "rule and its tests", "2026-10-10T13:00:00",
            {"docs/decisions.md": WITH_D2, "tests/unit/test_two.py": "def test_two():\n    pass\n"})
    problems, _ = _module("wave_check").branch_adr_problems(root)
    assert any("D-2" in p and "..HEAD" in p for p in problems), problems


def test_the_rebound_read_pin_fails_on_the_egress_rule_itself() -> None:
    """N5: `pytest.raises(AssertionError)` with no match let any assertion in the gate satisfy it."""
    source = (ROOT / "tests/unit/test_router_hints.py").read_text(encoding="utf-8")  # raw: not Swift
    start = source.index("def test_a_url_rebound_between_a_stores_guard_and_its_read_is_refused(")
    body = source[start:source.index("\ndef ", start + 1)]
    assert "pytest.raises(AssertionError, match=" in body, "the pin accepts any assertion"


def test_the_declared_names_scan_reads_swift_as_built(tmp_path: Path) -> None:
    """N1: `declared_names` read a Swift test raw through a parameter, which the #275 guard cannot see, so a
    test declared only inside a block comment counted as declared."""
    from tests.unit import test_security_invariants as invariants

    probe = tmp_path / "ProbeTests.swift"
    probe.write_text("/* func testOnlyInAComment() {} */\nfunc testLive() {}\n", encoding="utf-8")
    invariants.declared_names.cache_clear()
    assert invariants.declared_names(probe) == frozenset({"testLive"})
