"""The iOS deployment target is declared twice, so something has to compare them.

`ios/Package.swift` (which `swift test` compiles against) and
`ios/ModelRanking.xcodeproj/project.pbxproj` (which the app ships from) each name an iOS floor.
The first version of `Package.swift`'s comment claimed the pair "cannot silently drift" — and the
independent seat measured that nothing compared them at all. That is this project's most-recorded
defect, a record asserting a control which is not there, written into the manifest of the wave
whose subject was code nothing executes.

The comment now says what it is, and this file is what makes the original claim true. It lives on
the Python side because that is the gate that always runs: `swift test` is skipped where there is
no toolchain, and a drift check that only runs on a Mac with Xcode is a drift check that CI cannot
perform.
"""

from __future__ import annotations

import re
from pathlib import Path

IOS = Path(__file__).resolve().parents[2] / "ios"


def _package_ios_floor() -> str:
    manifest = (IOS / "Package.swift").read_text(encoding="utf-8")
    match = re.search(r"\.iOS\(\.v(\d+)\)", manifest)
    assert match, "Package.swift declares no iOS platform at all"
    return match.group(1)


def _xcodeproj_ios_floors() -> set[str]:
    pbxproj = (IOS / "ModelRanking.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    floors = set(re.findall(r"IPHONEOS_DEPLOYMENT_TARGET = ([\d.]+);", pbxproj))
    assert floors, "the project file declares no IPHONEOS_DEPLOYMENT_TARGET"
    return floors


def test_the_package_and_the_app_agree_on_the_ios_floor() -> None:
    """Drift here means `swift test` compiles the Engine under different availability rules than
    the app ships under — so a tier could be stripped from one and present in the other, and every
    test would stay green against code nobody runs."""
    package = _package_ios_floor()
    project = _xcodeproj_ios_floors()

    assert project == {f"{package}.0"} or project == {package}, (
        f"Package.swift declares iOS {package} and the project declares {sorted(project)}. "
        "The tests and the app would compile the same sources under different availability rules"
    )


def test_the_project_does_not_declare_two_different_floors_for_itself() -> None:
    """Debug and Release drifting from each other is the same defect one level in."""
    floors = _xcodeproj_ios_floors()

    assert len(floors) == 1, f"the project file names more than one iOS floor: {sorted(floors)}"
