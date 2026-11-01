"""#530 (the release Security-Reviewer's M11, the remaining path of #488): a git-ignored `Engine.local.xcconfig`
may set anything, and Xcode hands Info.plist's preprocessor more than `INFOPLIST_PREPROCESSOR_DEFINITIONS`: a local
`INFOPLIST_OTHER_PREPROCESSOR_FLAGS = -DENGINE_LOCAL_NETWORKING=1` gave a Release simulator build
`NSAllowsLocalNetworking`. `test_testflight_ready.py` holds `Engine.xcconfig`'s text to every setting in
`INFOPLIST_PREPROCESSOR`, where CI runs; these two hold the list and the reading against the Xcode on this Mac:
every Info.plist setting Xcode's own specifications declare is classified, and Xcode itself resolves a planted
local file to a Release build that preprocesses Info.plist with nothing of the file's.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from .test_testflight_ready import INFOPLIST_PREPROCESSOR, REPO

#: Every other Info.plist setting Xcode declares, and why it gives Info.plist's preprocessor nothing.
NOT_PREPROCESSOR = {
    "INFOPLIST_FILE": "which source is read: the app target sets it, and a target's setting outranks any xcconfig",
    "INFOPLIST_PATH": "where the built plist is written, in the product",
    "INFOPLIST_OUTPUT_FORMAT": "XML or binary, chosen after the preprocessor has run",
    "INFOPLIST_EXPAND_BUILD_SETTINGS": "fills `$(NAME)` inside values after the preprocessor; it adds no key",
    "INFOPLIST_ENABLE_CFBUNDLEICONS_MERGE": "merges the asset catalog's icon keys, not the source's",
}
#: What a hostile local file sets each one to, in Release and in every narrower Release condition.
HOSTILE = {
    "INFOPLIST_PREPROCESS": "NO",
    "INFOPLIST_PREPROCESSOR_DEFINITIONS": "ENGINE_LOCAL_NETWORKING=1",
    "INFOPLIST_OTHER_PREPROCESSOR_FLAGS": "-DENGINE_LOCAL_NETWORKING=1",
    "INFOPLIST_PREFIX_HEADER": "Config/local-networking.h",
}
DECLARED = re.compile(r'\bName\s*=\s*"?(INFOPLIST_\w+)')


@pytest.mark.needs("xcode")  # reads the active Xcode's build-system specifications
def test_every_info_plist_setting_xcode_declares_is_classified() -> None:
    """The list is enumerated (Xcode reads these settings in compiled code, so no spec says which feed the
    preprocessor); this derives what it must cover. A setting a later Xcode adds fails here until it is placed in
    `INFOPLIST_PREPROCESSOR` or, with its reason, in `NOT_PREPROCESSOR`. No generated key may carry the exception."""
    developer = Path(subprocess.run(["xcode-select", "-p"], capture_output=True, text=True, check=True,
                                    timeout=60).stdout.strip())
    specs = list((developer.parent / "SharedFrameworks").rglob("*.xcspec"))
    declared = {name for spec in specs for name in DECLARED.findall(spec.read_text(encoding="utf-8", errors="replace"))}
    assert set(INFOPLIST_PREPROCESSOR) <= declared, ("not read from Xcode's specifications", len(specs), sorted(declared))
    keys = {name for name in declared if name.startswith("INFOPLIST_KEY_")}
    assert keys and not [key for key in keys if "TransportSecurity" in key or "LocalNetworking" in key], sorted(keys)
    unplaced = declared - keys - set(INFOPLIST_PREPROCESSOR) - set(NOT_PREPROCESSOR)
    assert not unplaced, f"classify each in INFOPLIST_PREPROCESSOR or NOT_PREPROCESSOR: {sorted(unplaced)}"


def _resolved(project: Path, configuration: str, sdk: str) -> dict[str, str]:
    shown = subprocess.run(["xcodebuild", "-project", str(project), "-target", "ModelRanking", "-configuration",
                            configuration, "-sdk", sdk, "-showBuildSettings", "-json"],
                           capture_output=True, text=True, check=True, timeout=300)
    (target,) = json.loads(shown.stdout)
    settings: dict[str, str] = target["buildSettings"]
    return settings


@pytest.mark.needs("xcode")  # Xcode resolves the build settings
def test_xcode_resolves_a_hostile_local_file_to_a_release_build_with_none_of_it(tmp_path: Path) -> None:
    """The text test reads "the last matching line wins" into `Engine.xcconfig`; this asks Xcode. A local file sets
    each preprocessor setting, unconditioned and under narrower Release conditions; a Release build, simulator or
    device, resolves each to its one safe value, and a Debug build resolves the file's (so the plant took)."""
    ios = tmp_path / "ios"
    shutil.copytree(REPO / "ios" / "ModelRanking.xcodeproj", ios / "ModelRanking.xcodeproj")
    shutil.copytree(REPO / "ios" / "Config", ios / "Config")
    (ios / "Config" / "Engine.local.xcconfig").write_text("".join(
        f"{name}{condition} = {value}\n" for name, value in HOSTILE.items()
        for condition in ("", "[config=Release]", "[config=Release][sdk=iphone*]", "[sdk=*][config=Release][arch=*]")
    ), encoding="utf-8")
    project = ios / "ModelRanking.xcodeproj"
    for sdk in ("iphonesimulator", "iphoneos"):
        release = _resolved(project, "Release", sdk)
        assert {name: release.get(name, "") for name in INFOPLIST_PREPROCESSOR} == INFOPLIST_PREPROCESSOR, sdk
    debug = _resolved(project, "Debug", "iphonesimulator")
    assert debug.get("INFOPLIST_OTHER_PREPROCESSOR_FLAGS") == HOSTILE["INFOPLIST_OTHER_PREPROCESSOR_FLAGS"], debug
