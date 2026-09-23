"""`make check-fast`'s Swift leg: a parallel run is judged from its xUnit report.

`swift test --parallel` does not print the `Executed N tests` line `make swift-test` counts, so the
fast leg reads `--xunit-output` instead. Every way the serial gate can fail, this one must fail too:
a failure, a skipped test (M16-W1 review M-3), fewer tests than the floor (a suite that stops being
discovered exits 0), a report that is missing or unreadable (fail closed), and a set of EXECUTED
tests that is not the manifest (D-150) -- stronger than the serial gate's discovered list.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "swift_xunit_gate.py"
MANIFEST = ["Suite.ATests/testOne", "Suite.ATests/testTwo", "Suite.BTests/testThree"]


def _gate() -> ModuleType:
    spec = importlib.util.spec_from_file_location("swift_xunit_gate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _report(tmp_path: Path, cases: list[str], *, failures: int = 0, skipped: str | None = None) -> Path:
    body = []
    for case in cases:
        classname, name = case.split("/")
        inner = "<skipped/>" if case == skipped else ""
        body.append(f'<testcase classname="{classname}" name="{name}" time="0.1">{inner}</testcase>')
    xml = (f'<testsuites><testsuite name="TestResults" errors="0" tests="{len(cases)}" '
           f'failures="{failures}" time="1">{"".join(body)}</testsuite></testsuites>')
    path = tmp_path / "xunit.xml"
    path.write_text(xml, encoding="utf-8")
    return path


def _manifest(tmp_path: Path, lines: list[str] = MANIFEST) -> Path:
    path = tmp_path / "manifest.txt"
    path.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")
    return path


def test_a_clean_run_of_exactly_the_manifest_passes(tmp_path: Path) -> None:
    problems = _gate().problems(_report(tmp_path, MANIFEST), _manifest(tmp_path))
    assert problems == []


def test_a_failure_fails(tmp_path: Path) -> None:
    assert _gate().problems(_report(tmp_path, MANIFEST, failures=1), _manifest(tmp_path))


def test_a_skipped_test_fails(tmp_path: Path) -> None:
    report = _report(tmp_path, MANIFEST, skipped=MANIFEST[0])
    assert any("SKIPPED" in p for p in _gate().problems(report, _manifest(tmp_path)))


def test_a_test_that_did_not_run_fails(tmp_path: Path) -> None:
    report = _report(tmp_path, MANIFEST[:2])
    assert any("did not run" in p for p in _gate().problems(report, _manifest(tmp_path)))


def test_a_test_that_is_not_in_the_manifest_fails(tmp_path: Path) -> None:
    report = _report(tmp_path, [*MANIFEST, "Suite.BTests/testFour"])
    assert any("not in the manifest" in p for p in _gate().problems(report, _manifest(tmp_path)))


@pytest.mark.parametrize("content", [None, "", "<not xml", "<testsuites/>"])
def test_a_missing_empty_or_unreadable_report_fails_closed(tmp_path: Path, content: str | None) -> None:
    report = tmp_path / "xunit.xml"
    if content is not None:
        report.write_text(content, encoding="utf-8")
    assert _gate().problems(report, _manifest(tmp_path))


def test_an_empty_manifest_fails_closed(tmp_path: Path) -> None:
    """A floor of zero passes a suite that ran nothing: the comparison must have something to hold."""
    assert _gate().problems(_report(tmp_path, []), _manifest(tmp_path, []))
