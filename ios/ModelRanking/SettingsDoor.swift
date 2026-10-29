import SwiftUI

/// #484 (D-230): the one way out of the app that is not the engine, the system's own Settings page for this app,
/// where Apple Intelligence is turned on. Its address is the system's constant, never text, and nothing the reader
/// typed reaches it. The file is pinned whole by `scripts/client_decl_gate.py` (`SETTINGS_DOOR_SHA256`) and its two
/// expressions by `tests/unit/test_router_hints.py` (`EGRESS_EXACT`), so a second address here is a reviewed edit.
enum SettingsDoor {
    @MainActor static func showSettings() {
        guard let settings = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(settings)
    }
}
