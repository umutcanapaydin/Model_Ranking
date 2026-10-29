"""#484 (D-230): the Apple Intelligence guide's "Open Settings" button, and the one door out of the app it needs.

D-229 clause 1 asked for the button where turning Apple Intelligence on is the remedy. Opening the system's Settings
page needs a URL made from a string and `UIApplication.shared.open`, both refused outside the engine client (D-126,
#107). D-230 makes them one named exception: one file, `SettingsDoor.swift`, pinned whole by the compiled gate
(`scripts/client_decl_gate.py`, `SETTINGS_DOOR_SHA256`) and permitted as two exact expressions by the text gate
(`tests/unit/test_router_hints.py`, `EGRESS_EXACT`). The address is the system's own constant, never text.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .test_deploy_gate_444 import _module
from .test_router_hints import EGRESS_EXACT, EGRESS_PERMITTED, _code

CLIENT = Path(__file__).resolve().parents[2] / "ios" / "ModelRanking"
DOOR = "SettingsDoor.swift"
EXPRESSIONS = {"URL(string: UIApplication.openSettingsURLString)", "UIApplication.shared.open(settings)"}


def test_the_guide_opens_settings_where_turning_it_on_is_the_remedy() -> None:
    """D-229 clause 1: the sheet shows the button exactly when `OnDeviceGuide.opensSettings` says Settings holds the
    remedy, and the button goes through the one door."""
    code = _code((CLIENT / "ContentView.swift").read_text(encoding="utf-8"))
    sheet = code[code.index("private var intelligenceGuideSheet"):code.index("private var creditsSheet")]
    guard, button = sheet.find("if guide.opensSettings {"), sheet.find(
        "Button(UIText.openSettings(language)) { SettingsDoor.open() }")
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


def test_the_text_gate_permits_the_door_as_two_exact_expressions() -> None:
    """D-230: never a pattern over the whole file, the way `EngineClient.swift` is permitted."""
    assert {snippet for (name, snippet) in EGRESS_EXACT if name == DOOR} == EXPRESSIONS
    assert not [key for key in EGRESS_PERMITTED if key[0] == DOOR]
