"""M18-W1 (#87, D-171) -- the app's engine address is set per build, and the app may reach the home network.

The address comes from the build setting `ENGINE_URL` (loopback in `ios/Config/Engine.xcconfig`; the
owner's Mac in a git-ignored `Engine.local.xcconfig`), through the Info plist key `EngineURL`, to
`EngineClient.localDefault`. The partial plist adds only the local-networking exception and the text
iOS shows when it asks for local-network access.
"""

from __future__ import annotations

import plistlib
from pathlib import Path

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
                   if "PRODUCT_BUNDLE_IDENTIFIER = com.ilgar.modelranking;" in block]
    assert len(app_configs) == 2, "the app target's Debug and Release"
    for block in app_configs:
        assert "INFOPLIST_FILE = Config/Info.plist;" in block
    assert project.count("baseConfigurationReference") >= 2
    assert "path = Config/Engine.xcconfig;" in project
