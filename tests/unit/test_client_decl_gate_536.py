"""#536 (the #535 security review's R1): #535's rebinding of `Date.<=` to Foundation came with no Xcode change on
record, and the gate had been green the same morning, so its cause stayed unexplained. `make client-decls` names,
on its PASS and FAIL lines, the `swiftc --version` and each SDK's version and build it compiled with, so the next
binding that moves names the toolchain that moved it.

A stand-in `xcrun` answers the version questions and canned dumps stand in for the compiler, so this runs on CI.
What the gate allows is unchanged: a toolchain whose versions cannot be read still passes or fails as before.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("client_decl_gate_536", ROOT / "scripts" / "client_decl_gate.py")
assert _spec is not None and _spec.loader is not None
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

SWIFTC = "swift-driver version: 9.1 Apple Swift version 9.9 (swiftlang-9.9.0.1.1 clang-9900.1.1.1)"
ANSWERS = {
    ("swiftc", "--version"): SWIFTC + "\nTarget: arm64-apple-macosx99.0\n",
    ("--sdk", "iphonesimulator", "--show-sdk-version"): "99.1\n",
    ("--sdk", "iphonesimulator", "--show-sdk-build-version"): "99Z1\n",
    ("--sdk", "iphoneos", "--show-sdk-version"): "99.2\n",
    ("--sdk", "iphoneos", "--show-sdk-build-version"): "99Z2\n",
}
NAMED = (SWIFTC, "iphonesimulator 99.1 (99Z1)", "iphoneos 99.2 (99Z2)")


class _Done:
    def __init__(self, stdout: str) -> None:
        self.stdout, self.stderr, self.returncode = stdout, "", 0


def _gate(monkeypatch: pytest.MonkeyPatch, refused: list[str], readable: bool = True) -> None:
    """The gate on canned dumps, with a stand-in `xcrun` that answers `ANSWERS` (or fails every one)."""
    def run(argv: list[str], **_: object) -> _Done:
        if not readable:
            raise subprocess.CalledProcessError(1, argv)
        return _Done(ANSWERS[tuple(argv[1:])])

    names = {path.name for path in gate.CLIENT.rglob("*.swift")}
    monkeypatch.setattr(gate.shutil, "which", lambda _: "/usr/bin/xcrun")
    monkeypatch.setattr(gate.subprocess, "run", run)
    monkeypatch.setattr(gate, "self_test", lambda: [])
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: ("ast", 0))
    monkeypatch.setattr(gate, "references", lambda ast: {name: set() for name in names})
    monkeypatch.setattr(gate, "problems", lambda found: list(refused))
    monkeypatch.setattr(gate, "unseen_permissions", lambda found: [])
    monkeypatch.setattr(gate, "release_problems", lambda found: [])


def test_the_pass_line_names_the_swiftc_and_each_sdk_it_compiled_with(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _gate(monkeypatch, refused=[])
    assert gate.main() == 0
    passed = [line for line in capsys.readouterr().out.splitlines() if line.startswith("client-decls PASS")]
    assert len(passed) == 1 and all(name in passed[0] for name in NAMED), passed


def test_every_fail_line_names_the_swiftc_and_each_sdk_it_compiled_with(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _gate(monkeypatch, refused=["ContentView.swift:1: Foundation.URLSession is the network"])
    assert gate.main() == 1
    failed = [line for line in capsys.readouterr().out.splitlines() if line.startswith("client-decls FAIL")]
    assert failed and all(name in line for line in failed for name in NAMED), failed


def test_a_failed_self_test_names_the_toolchain_too(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _gate(monkeypatch, refused=[])
    monkeypatch.setattr(gate, "self_test", lambda: ["ContentView.swift: URL.decoded was not refused"])
    assert gate.main() == 1
    failed = [line for line in capsys.readouterr().out.splitlines() if line.startswith("client-decls FAIL")]
    assert failed and all(name in line for line in failed for name in NAMED), failed


@pytest.mark.parametrize("refused", [[], ["ContentView.swift:1: Foundation.URLSession is the network"]])
def test_versions_that_cannot_be_read_change_no_verdict(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], refused: list[str]) -> None:
    """The line is evidence, not a rule: an `xcrun` that cannot answer leaves the verdict as it was, and says so."""
    _gate(monkeypatch, refused=refused, readable=False)
    assert gate.main() == (1 if refused else 0)
    verdicts = [line for line in capsys.readouterr().out.splitlines()
                if line.startswith(("client-decls PASS", "client-decls FAIL"))]
    assert verdicts and all("swiftc unread" in line for line in verdicts), verdicts
