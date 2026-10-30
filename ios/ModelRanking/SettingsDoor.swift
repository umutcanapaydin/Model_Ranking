import SwiftUI

/// #484 (D-230): the one way out of the app that is not the engine. It opens the Settings app at this app's own page;
/// iOS offers no public link to the Apple Intelligence page, so the guide's steps go on from there. Its address is the
/// system's constant, never text, and nothing the reader typed reaches it. The file is pinned whole by
/// `scripts/client_decl_gate.py` (`SETTINGS_DOOR_SHA256`) and its body as one expression by
/// `tests/unit/test_router_hints.py` (`EGRESS_EXACT`), so a second address here is a reviewed edit.
enum SettingsDoor {
    @MainActor static func showSettings() {
        guard let settings = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(settings)
    }
}
