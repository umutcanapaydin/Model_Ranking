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


#: A setting's line: its name, with any bracketed conditions (`ENGINE_URL[config=Release]`), then its
#: value. A line that opens with `//` is a comment; `/$()/` keeps a URL's slashes from being one.
SETTING = re.compile(r"^\s*([A-Za-z_]\w*(?:\[[^\]]*\])*)\s*=\s*(.*?)\s*$")


def _xcconfig(name: str) -> dict[str, str]:
    lines = (CONFIG / name).read_text(encoding="utf-8").splitlines()
    found = (SETTING.match(line) for line in lines if not line.lstrip().startswith("//"))
    return {match.group(1): match.group(2) for match in found if match}


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


def test_the_iphone_guide_sets_the_home_address_for_debug_builds_only() -> None:
    """The M19-W5 review's M6: the guide had the owner write `ENGINE_URL = http://<Mac>` in the local
    config, which overrides the Release address too, so a TestFlight build would ask the owner's Mac."""
    guide = (REPO / "docs" / "owner-iphone.md").read_text(encoding="utf-8")
    assert "ENGINE_URL[config=Debug] = http:/$()/My-Mac.local:8080" in guide
    assert not re.search(r"^\s*ENGINE_URL\s*=", guide, re.MULTILINE), "an unconditional ENGINE_URL in the guide"


def test_a_release_build_reaches_the_hosted_engine_whatever_the_local_config_says() -> None:
    """The M19 security review's S1: in an xcconfig the last matching setting wins, and
    `Engine.local.xcconfig` was included after the Release line, so the owner's own `ENGINE_URL` (as
    the iPhone guide had him write it) sent a TestFlight archive to his Mac over plain http."""
    lines = (CONFIG / "Engine.xcconfig").read_text(encoding="utf-8").splitlines()
    include = next(i for i, line in enumerate(lines) if line.startswith('#include? "Engine.local.xcconfig"'))
    release = next(i for i, line in enumerate(lines) if line.startswith("ENGINE_URL[config=Release]"))
    assert release > include, "the Release address must come after the local file, which may set ENGINE_URL"


def test_the_shared_scheme_archives_the_app_in_release() -> None:
    """The second W5 review's M3: the runbook archives with Product → Archive, and the shared scheme
    built nothing for archiving and had no Archive action, so an archive would hold no app."""
    import xml.etree.ElementTree as ET

    scheme = ET.parse(REPO / "ios" / "ModelRanking.xcodeproj" / "xcshareddata" / "xcschemes" / "ModelRanking.xcscheme")
    app = [entry for entry in scheme.iter("BuildActionEntry")
           if any(ref.get("BuildableName") == "ModelRanking.app" for ref in entry.iter("BuildableReference"))]
    assert app and app[0].get("buildForArchiving") == "YES"
    archive = scheme.find("ArchiveAction")
    assert archive is not None and archive.get("buildConfiguration") == "Release"


def test_nothing_after_the_release_address_can_replace_it() -> None:
    """The second W5 review's M4: a later ENGINE_URL of any condition, or a later include, would win
    over the Release address as the local file once did."""
    lines = (CONFIG / "Engine.xcconfig").read_text(encoding="utf-8").splitlines()
    release = next(i for i, line in enumerate(lines) if line.startswith("ENGINE_URL[config=Release]"))
    after = [line for line in lines[release + 1:] if line.strip() and not line.lstrip().startswith("//")]
    assert not any(line.lstrip().startswith(("ENGINE_URL", "#include")) for line in after), after


# --- The W5 Tester seat (docs/reviews/m19-wave-5-tester.md) ------------------------------------------------

#: An app-target build configuration based on Engine.xcconfig, and the settings it sets itself.
_ENGINE_CONFIG = re.compile(
    r"/\* (?P<name>\w+) \*/ = \{\s*isa = XCBuildConfiguration;\s*"
    r"baseConfigurationReference = \w+ /\* Engine\.xcconfig \*/;\s*buildSettings = \{(?P<settings>.*?)\n\t\t\t\};",
    re.DOTALL,
)


def test_no_target_setting_overrides_what_the_engine_config_or_the_local_file_sets() -> None:
    """D-185 clause 4 and the runbook's step 2.1. A target's own build setting outranks its xcconfig, so
    an `ENGINE_URL` set on the app target sends every archive there, whatever Engine.xcconfig says, and
    one set to "" drops the icon. Planted in the project's Release configuration (the Tester's X1, X2),
    each passed every test, which read the xcconfig alone. The local file's `DEVELOPMENT_TEAM` and
    `PRODUCT_BUNDLE_IDENTIFIER` would be overridden the same way."""
    project = (REPO / "ios" / "ModelRanking.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
    configs = {match["name"]: match["settings"] for match in _ENGINE_CONFIG.finditer(project)}
    assert set(configs) == {"Debug", "Release"}, sorted(configs)
    owned = {name.split("[")[0] for name in _xcconfig("Engine.xcconfig")} | {"DEVELOPMENT_TEAM", "PRODUCT_BUNDLE_IDENTIFIER"}
    assert {"ENGINE_URL", "ASSETCATALOG_COMPILER_APPICON_NAME"} <= owned
    for name, settings in configs.items():
        keys = {line.split("=", 1)[0].strip().strip('"').split("[")[0] for line in settings.splitlines() if "=" in line}
        assert not keys & owned, (name, sorted(keys & owned))
