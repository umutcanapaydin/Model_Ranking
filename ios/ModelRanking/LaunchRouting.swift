//  D-175 clause 3 -- the one place the app reads its launch arguments, and only in a Debug build.
//  A Release build compiles the second branch, and `make client-decls` refuses one that reads them.

import Foundation

extension TieredRouter {
    /// The router the screen uses: the platform's tiers, or -- in a Debug build launched by a UI
    /// test with `-UITestRouting` -- the scripted model tier.
    static func forThisLaunch() -> TieredRouter {
        #if DEBUG
        if let scripted = ScriptedModelRouter.from(arguments: ProcessInfo.processInfo.arguments) {
            return TieredRouter(model: scripted)
        }
        #endif
        return TieredRouter()
    }
}
