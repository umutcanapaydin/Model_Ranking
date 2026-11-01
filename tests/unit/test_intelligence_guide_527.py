"""#527 (D-235, amending D-175 clause 3): a UI test reaches the Apple Intelligence guide and taps its Open Settings button.

On the simulator Apple Intelligence runs, so the guide never appeared and its button (#484, D-230) was held only by
`test_settings_door_484.py`, which reads the source. D-235 adds one Debug-only launch argument,
`-UITestIntelligence unavailable`, read beside `-UITestRouting` in `LaunchRouting.swift`, that makes the app report the
on-device model as unavailable. `make client-decls` refuses a Release build that reads its launch arguments at all; this
file holds the text half where there is no Xcode: the argument is read only inside `#if DEBUG`, the screen takes its
state from that read on both of its reads, and the UI test exists, runs in `make ui-test`'s engine-up pass, launches
with the argument and taps the button.
"""

from __future__ import annotations

import re
from pathlib import Path

from .test_router_hints import _code

IOS = Path(__file__).resolve().parents[2] / "ios"
CLIENT = IOS / "ModelRanking"
LAUNCH = CLIENT / "LaunchRouting.swift"
VIEW = CLIENT / "ContentView.swift"
UI_TEST = IOS / "UITests" / "IntelligenceGuideTests.swift"
UI_RUNNER = IOS.parent / "scripts" / "ui_test.sh"
FLAG = '"-UITestIntelligence"'
#: The launch-aware state read: the one the screen must use, so the argument reaches the guide.
LAUNCH_STATE = "TieredRouter.onDeviceStateForThisLaunch()"


def _debug_only(code: str) -> list[bool]:
    """For each line of `code` (comments already removed), whether only a Debug build compiles it: it lies in the
    first branch of an `#if DEBUG`, at any depth. An `#else` or `#elseif` of that `#if` is not Debug-only."""
    stack: list[bool] = []
    lines: list[bool] = []
    for line in code.split("\n"):
        directive = re.match(r"\s*#(if|elseif|else|endif)\b\s*(.*?)\s*$", line)
        if directive:
            kind, condition = directive.groups()
            if kind == "if":
                stack.append(condition == "DEBUG")
            elif kind in ("elseif", "else") and stack:
                stack[-1] = False
            elif kind == "endif" and stack:
                stack.pop()
            lines.append(True)
        else:
            lines.append(any(stack))
    return lines


def _reads_outside_debug(sources: dict[str, str]) -> list[str]:
    """`file:line` of every line that names the flag or reads the launch arguments outside `#if DEBUG`, in
    `{file name: Swift source}`."""
    found: list[str] = []
    for name, swift in sources.items():
        code = _code(swift)
        for number, (line, debug) in enumerate(zip(code.split("\n"), _debug_only(code), strict=True), start=1):
            if not debug and (FLAG in line or "ProcessInfo.processInfo.arguments" in line):
                found.append(f"{name}:{number}")
    return found


def _client() -> dict[str, str]:
    return {str(p.relative_to(CLIENT)): p.read_text(encoding="utf-8") for p in CLIENT.rglob("*.swift")}  # raw: read through `_code`


def test_the_argument_is_read_beside_the_scripted_routing_and_only_in_a_debug_build() -> None:
    """D-235: `LaunchRouting.swift` reads `-UITestIntelligence`, and nothing in the client names it or reads the
    launch arguments outside `#if DEBUG`."""
    sources = _client()
    naming = sorted(name for name, swift in sources.items() if FLAG in _code(swift))
    assert naming == ["LaunchRouting.swift"], naming
    assert _reads_outside_debug(sources) == []
    code = _code(LAUNCH.read_text(encoding="utf-8"))  # raw: read through `_code`
    flagged = [debug for line, debug in zip(code.split("\n"), _debug_only(code), strict=True) if FLAG in line]
    assert flagged and all(flagged), "the flag is not read inside #if DEBUG"
    assert "static func onDeviceStateForThisLaunch() -> OnDeviceState" in code


def test_a_read_outside_debug_is_refused() -> None:
    """The control's other half: the same read in an `#else`, at file scope, or under another condition is found."""
    planted = {
        "Else.swift": f"#if DEBUG\nlet a = 1\n#else\nlet b = args.contains({FLAG})\n#endif\n",
        "Bare.swift": "let c = ProcessInfo.processInfo.arguments\n",
        "Other.swift": f"#if targetEnvironment(simulator)\nlet d = {FLAG}\n#endif\n",
        "Kept.swift": f"#if DEBUG\n#if os(iOS)\nlet e = {FLAG}\n#endif\n#endif\n",
    }
    assert _reads_outside_debug(planted) == ["Else.swift:4", "Bare.swift:1", "Other.swift:2"]


def test_the_screen_takes_the_model_state_from_the_launch_aware_read() -> None:
    """Both of the screen's reads, at launch and each time the app comes back to the front (#220), go through the
    launch-aware read, so the argument is not undone the first time the scene becomes active."""
    code = _code(VIEW.read_text(encoding="utf-8"))  # raw: read through `_code`
    assert "TieredRouter.onDeviceState()" not in code
    assert code.count(LAUNCH_STATE) == 2, code.count(LAUNCH_STATE)


def test_a_ui_test_launches_with_the_argument_and_taps_open_settings() -> None:
    """D-235 and D-175 clause 4: the UI test opens the guide, taps the button, and asserts on the accessibility tree
    that the Settings app came to the front, never on pixels."""
    code = _code(UI_TEST.read_text(encoding="utf-8"))  # raw: read through `_code`
    assert re.search(r'launchArguments = \[[^\]]*"-UITestIntelligence", "unavailable"', code), "not launched unavailable"
    assert 'app.buttons["aiCaption"]' in code and ".tap()" in code
    open_settings = code.find('app.buttons["Open Settings"]')
    foreground = code.find('XCUIApplication(bundleIdentifier: "com.apple.Preferences")')
    assert 0 <= open_settings < foreground, "the test does not tap Open Settings before looking for Settings"
    assert ".wait(for: .runningForeground" in code[foreground:]


def test_make_ui_test_runs_the_guide_test_with_the_engine_up() -> None:
    """The guide is behind the question card, which needs the engine's first answer: the class runs in the pass
    `make ui-test` runs with the engine up, so neither of its skips names it."""
    class_name = UI_TEST.stem
    assert f"final class {class_name}: XCTestCase" in _code(UI_TEST.read_text(encoding="utf-8"))  # raw: read through `_code`
    runner = UI_RUNNER.read_text(encoding="utf-8")  # raw: not Swift
    skipped = set(re.findall(r'-skip-testing:"?ModelRankingUITests/(?:\$OFFLINE|(\w+))', runner)) | {"FailureScreenTests"}
    assert class_name not in skipped, skipped
    assert 'OFFLINE="FailureScreenTests"' in runner
