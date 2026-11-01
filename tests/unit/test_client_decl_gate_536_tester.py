"""The release delta Tester of `integration/fixes-1101` (2026-11-01): #536 on the two FAIL lines its tests never reach.

#536: `make client-decls` names the swiftc and SDK versions it compiled with "on its PASS and FAIL lines". The range's
tests (`test_client_decl_gate_536.py`) reach the PASS line, the self-test's FAIL and a refused binding's FAIL; their
stand-in dump always type-checks and covers every file, so the toolchain could leave the other two FAIL lines (the
client does not type-check; a file produced no tree) with every test green: faults F-C4 and F-C5.
"""

from __future__ import annotations

import pytest

from .test_client_decl_gate_536 import NAMED, _gate, gate


def _fail_lines(capsys: pytest.CaptureFixture[str]) -> list[str]:
    return [line for line in capsys.readouterr().out.splitlines() if line.startswith("client-decls FAIL")]


# covers #536
def test_a_client_that_does_not_type_check_names_the_toolchain(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _gate(monkeypatch, refused=[])
    monkeypatch.setattr(gate, "dump_ast", lambda sdk_name, flags, folder=gate.CLIENT: ("error: no such type", 1))
    assert gate.main() == 1
    failed = _fail_lines(capsys)
    assert failed and all("does not type-check" in line for line in failed), failed
    assert all(name in line for line in failed for name in NAMED), failed


# covers #536
def test_a_file_that_produced_no_tree_names_the_toolchain(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _gate(monkeypatch, refused=[])
    monkeypatch.setattr(gate, "references", lambda ast: {})
    assert gate.main() == 1
    failed = _fail_lines(capsys)
    assert failed and all("produced no tree" in line for line in failed), failed
    assert all(name in line for line in failed for name in NAMED), failed
