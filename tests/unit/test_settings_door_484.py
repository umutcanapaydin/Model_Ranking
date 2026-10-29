"""#484 (D-230): the Apple Intelligence guide's "Open Settings" button, and the one door out of the app it needs.

D-229 clause 1 asked for the button where turning Apple Intelligence on is the remedy. Opening the system's Settings
page needs a URL made from a string and `UIApplication.shared.open`, both refused outside the engine client (D-126,
#107). D-230 makes them one named exception: one file, `SettingsDoor.swift`, pinned whole by the compiled gate
(`scripts/client_decl_gate.py`, `SETTINGS_DOOR_SHA256`) and permitted as one exact expression by the text gate
(`tests/unit/test_router_hints.py`, `EGRESS_EXACT`). The address is the system's own constant, never text.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from .test_deploy_gate_444 import _module
from .test_router_hints import EGRESS_EXACT, EGRESS_PERMITTED, _code

CLIENT = Path(__file__).resolve().parents[2] / "ios" / "ModelRanking"
DOOR = "SettingsDoor.swift"
#: The door's body as ONE expression: the guard that makes the URL and the call that opens it (the #484 review's M1).
EXPRESSIONS = {"guard let settings = URL(string: UIApplication.openSettingsURLString) else { return }\n"
               "        UIApplication.shared.open(settings)"}


def test_the_guide_opens_settings_where_turning_it_on_is_the_remedy() -> None:
    """D-229 clause 1: the sheet shows the button exactly when `OnDeviceGuide.opensSettings` says Settings holds the
    remedy, and the button goes through the one door."""
    code = _code((CLIENT / "ContentView.swift").read_text(encoding="utf-8"))
    sheet = code[code.index("private var intelligenceGuideSheet"):code.index("private var creditsSheet")]
    guard, button = sheet.find("if guide.opensSettings {"), sheet.find(
        "Button(UIText.openSettings(language)) { SettingsDoor.showSettings() }")
    assert 0 <= guard < button, sheet


def test_the_settings_door_is_one_file_pinned_whole() -> None:
    """D-230: the compiled gate allows the door's symbols in that file alone, and only while its bytes are the
    pinned ones, so a second address there is a reviewed edit of the gate."""
    gate = _module("client_decl_gate")
    assert gate.SETTINGS_DOOR == DOOR
    assert hashlib.sha256((CLIENT / DOOR).read_bytes()).hexdigest() == gate.SETTINGS_DOOR_SHA256
    assert gate.settings_door_problem(CLIENT) is None


def test_a_changed_settings_door_is_refused(tmp_path: Path) -> None:
    """The control's other half: the same file with one character changed is refused by the compiled gate."""
    gate = _module("client_decl_gate")
    (tmp_path / DOOR).write_bytes((CLIENT / DOOR).read_bytes().replace(b"open(settings)", b"open(settings) "))
    problem = gate.settings_door_problem(tmp_path)
    assert problem is not None and DOOR in problem, problem


def test_the_text_gate_permits_the_door_as_one_exact_expression() -> None:
    """D-230: never a pattern over the whole file, the way `EngineClient.swift` is permitted."""
    assert {snippet for (name, snippet) in EGRESS_EXACT if name == DOOR} == EXPRESSIONS
    assert not [key for key in EGRESS_PERMITTED if key[0] == DOOR]


def _door() -> dict[str, set[str]]:
    """A compiled client of one file, the door, as `references` reports the shipping one."""
    gate = _module("client_decl_gate")
    return {DOOR: set(gate.SETTINGS_DOOR_ALLOWED) | {"SwiftUI.<imported>", "main.SettingsDoor.showSettings("}}


def test_the_compiled_gate_grants_the_door_only_while_its_bytes_are_pinned(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The #484 review's M3 (mutants C, D, E), without Xcode: the pinned door passes; a changed or an unreadable door
    is reported, and its declarations are refused as they would be in any other file."""
    gate = _module("client_decl_gate")
    monkeypatch.setattr(gate, "CLIENT", tmp_path)
    (tmp_path / DOOR).write_bytes((CLIENT / DOOR).read_bytes())
    assert gate.problems(_door()) == [], "the control: the pinned door"
    (tmp_path / DOOR).write_bytes((CLIENT / DOOR).read_bytes() + b"\n")
    changed = gate.problems(_door())
    (tmp_path / DOOR).unlink()
    unreadable = gate.problems(_door())
    for bad in (changed, unreadable):
        assert any("D-230" in line for line in bad), bad
        assert any("UIApplication" in line for line in bad), ("the exemption is withheld", bad)


def test_a_door_declaration_the_client_no_longer_uses_fails_the_gate() -> None:
    """The #484 review's M3 (mutant B): each of the door's declarations must be seen on the shipping client."""
    gate = _module("client_decl_gate")
    missing = gate.unseen_permissions({DOOR: set()})
    assert all(any(decl.split(".", 1)[1] in line for line in missing) for decl in gate.SETTINGS_DOOR_ALLOWED), missing
    seen = gate.unseen_permissions({DOOR: set(gate.SETTINGS_DOOR_ALLOWED)})
    assert not [line for line in seen if DOOR in line], seen
