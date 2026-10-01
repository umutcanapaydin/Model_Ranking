"""M18-W1 (#87, D-171, REQ-DEV-001) -- the app's engine address is set per build, and the app may reach the home network.

The address comes from the build setting `ENGINE_URL` (loopback in `ios/Config/Engine.xcconfig`; the
owner's Mac in a git-ignored `Engine.local.xcconfig`), through the Info plist key `EngineURL`, to
`EngineClient.localDefault`. The partial plist adds only the local-networking exception and the text
iOS shows when it asks for local-network access.
"""

from __future__ import annotations

import plistlib
import re
from pathlib import Path

from .test_router_hints import _code

IOS = Path(__file__).resolve().parents[2] / "ios"
PROJECT = IOS / "ModelRanking.xcodeproj" / "project.pbxproj"


def test_the_default_engine_is_loopback_and_the_owners_address_stays_on_his_mac() -> None:
    xcconfig = (IOS / "Config" / "Engine.xcconfig").read_text(encoding="utf-8")
    settings = [line for line in xcconfig.splitlines() if line.strip() and not line.lstrip().startswith("//")]
    assert "ENGINE_URL = http:/$()/127.0.0.1:8080" in settings, settings
    assert '#include? "Engine.local.xcconfig"' in settings, "the owner's override is an optional include"
    ignored = (IOS.parent / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "ios/Config/Engine.local.xcconfig" in ignored, "the owner's address must not be committed"


def test_the_partial_plist_carries_the_address_and_only_the_local_network_exception() -> None:
    info = plistlib.loads((IOS / "Config" / "Info.plist").read_bytes())
    assert info["EngineURL"] == "$(ENGINE_URL)"
    assert info["NSAppTransportSecurity"] == {"NSAllowsLocalNetworking": True}, (
        "only local networking; never arbitrary loads"
    )
    assert info["NSLocalNetworkUsageDescription"].strip()


def test_the_app_target_reads_the_xcconfig_and_the_partial_plist_in_every_configuration() -> None:
    project = PROJECT.read_text(encoding="utf-8")
    app_configs = [block for block in project.split("isa = XCBuildConfiguration;")
                   if "INFOPLIST_FILE = Config/Info.plist;" in block]
    assert len(app_configs) == 2, "the app target's Debug and Release"
    assert project.count("baseConfigurationReference") >= 2
    assert "path = Config/Engine.xcconfig;" in project


def test_the_client_asks_for_the_key_the_plist_carries() -> None:
    """W1 review M4: the key is one fact in two files. Reading nothing, or a misspelt key, passed every
    gate; the phone would then talk to its own loopback."""
    info = plistlib.loads((IOS / "Config" / "Info.plist").read_bytes())
    client = (IOS / "ModelRanking" / "Engine" / "EngineClient.swift").read_text(encoding="utf-8")
    found = re.search(
        r'static let localDefault = engineURL\(from: Bundle\.main\.object\(forInfoDictionaryKey: "(\w+)"\) as\? String\)',
        client,
    )
    assert found, "localDefault no longer reads the Info plist"
    assert found.group(1) in info and info[found.group(1)] == "$(ENGINE_URL)"


def test_the_bundle_id_is_set_where_the_owner_can_override_it() -> None:
    """W1 review M3: Xcode's Signing screen writes into the tracked project; the owner's team and a
    bundle id his Apple ID accepts belong in the git-ignored override, which a project-level value
    would beat."""
    project = PROJECT.read_text(encoding="utf-8")
    assert "PRODUCT_BUNDLE_IDENTIFIER" not in project
    xcconfig = (IOS / "Config" / "Engine.xcconfig").read_text(encoding="utf-8")
    assert "PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking" in xcconfig.splitlines()




def test_the_failure_screen_shows_the_address_the_app_asked() -> None:
    """W1 second review B2: the address lived only in a diagnostic no view showed, so a mistyped
    ENGINE_URL on the phone looked like an engine that was down. ContentView is not executed by any
    test (ios/Package.swift), so the view's use of the composed line is pinned here; the line itself is
    tested in EngineClientTests and LanguageTests."""
    view = (IOS / "ModelRanking" / "ContentView.swift").read_text(encoding="utf-8")
    start = view.index("private func failure(")
    # W1 Tester T3: block comments too, so `/* ... */` around the line cannot satisfy the pin.
    failure = _code(re.sub(r"/\*.*?\*/", "", view[start : view.index("// MARK:", start)], flags=re.S))
    # W1 third review M11: the line is shown, not only computed -- `let _ = error.addressNote(...)`
    # compiled and passed when the pin asked only for the call.
    shown = re.search(r"if let (\w+) = error\.addressNote\(client\.baseURL, language\) \{\s*Text\(\1\)", failure)
    assert shown, "the failure view does not show the address line"
