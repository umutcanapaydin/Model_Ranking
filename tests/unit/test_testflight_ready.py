"""M19-W5: what an upload to TestFlight needs from the app's tree, read as files (no Xcode here).

App Store Connect refuses an upload with no app icon, and a 1024-pixel icon with an alpha channel;
it asks for the reasons behind each "required reason" API the app calls (a privacy manifest); and it
asks every build about encryption unless the Info plist answers. A Release build must reach the
hosted engine, over HTTPS, at the name the deployment answers to (fly.toml, #94).
"""

from __future__ import annotations

import json
import plistlib
import re
import struct
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
APP = REPO / "ios" / "ModelRanking"
CONFIG = REPO / "ios" / "Config"

#: Each required-reason API category, the source spellings that use it, and the reason this app has.
#: A use in the source with no line in the manifest fails, so a new one cannot be waved through.
REQUIRED_REASONS = {
    "NSPrivacyAccessedAPICategoryUserDefaults": (r"@AppStorage|UserDefaults", "CA92.1"),
    "NSPrivacyAccessedAPICategoryFileTimestamp": (r"modificationDate|creationDate|attributesOfItem", "C617.1"),
    "NSPrivacyAccessedAPICategorySystemBootTime": (r"systemUptime|mach_absolute_time", "35F9.1"),
    "NSPrivacyAccessedAPICategoryDiskSpace": (r"volumeAvailableCapacity|systemFreeSize", "E174.1"),
}


def _xcconfig(name: str) -> dict[str, str]:
    settings = {}
    for line in (CONFIG / name).read_text(encoding="utf-8").splitlines():
        line = line.split("//", 1)[0] if not line.lstrip().startswith("ENGINE_URL") else line
        if "=" in line and not line.lstrip().startswith(("//", "#")):
            key, value = line.split("=", 1)
            settings[key.strip()] = value.strip()
    return settings


def test_the_app_has_a_1024_icon_with_no_alpha_channel() -> None:
    icon_set = APP / "Assets.xcassets" / "AppIcon.appiconset"
    images = json.loads((icon_set / "Contents.json").read_text(encoding="utf-8"))["images"]
    big = [image for image in images if image.get("size") == "1024x1024" and image.get("filename")]
    assert big, images
    png = (icon_set / big[0]["filename"]).read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height, _depth, colour = struct.unpack(">IIBB", png[16:26])
    assert (width, height) == (1024, 1024)
    assert colour == 2, "an RGB image with no alpha channel: App Store Connect refuses alpha in the icon"
    assert _xcconfig("Engine.xcconfig").get("ASSETCATALOG_COMPILER_APPICON_NAME") == "AppIcon"


def test_the_privacy_manifest_gives_a_reason_for_every_required_reason_api_the_app_calls() -> None:
    manifest = plistlib.loads((APP / "PrivacyInfo.xcprivacy").read_bytes())
    assert manifest["NSPrivacyTracking"] is False and manifest["NSPrivacyTrackingDomains"] == []
    declared = {entry["NSPrivacyAccessedAPIType"]: entry["NSPrivacyAccessedAPITypeReasons"]
                for entry in manifest["NSPrivacyAccessedAPITypes"]}
    source = "\n".join(path.read_text(encoding="utf-8") for path in APP.rglob("*.swift"))
    used = {category for category, (pattern, _reason) in REQUIRED_REASONS.items() if re.search(pattern, source)}
    assert "NSPrivacyAccessedAPICategoryUserDefaults" in used, "the scan reads the app's source"
    assert set(declared) == used, (declared, used)
    for category in used:
        assert declared[category] == [REQUIRED_REASONS[category][1]], (category, declared[category])
    # D-126: the reader's text never leaves the phone, so the app collects nothing.
    assert manifest["NSPrivacyCollectedDataTypes"] == []


def test_every_build_answers_the_encryption_question() -> None:
    """The app uses HTTPS only, which is exempt: the answer is in the plist, not asked per build."""
    info = plistlib.loads((CONFIG / "Info.plist").read_bytes())
    assert info["ITSAppUsesNonExemptEncryption"] is False


def test_a_release_build_reaches_the_hosted_engine_over_https() -> None:
    app = tomllib.loads((REPO / "fly.toml").read_text(encoding="utf-8"))["app"]
    release = _xcconfig("Engine.xcconfig").get("ENGINE_URL[config=Release]", "")
    assert release.replace("$()", "") == f"https://{app}.fly.dev", release
    assert _xcconfig("Engine.xcconfig")["ENGINE_URL"].replace("$()", "") == "http://127.0.0.1:8080"
