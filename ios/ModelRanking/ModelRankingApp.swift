//  ModelRankingApp.swift — the entry point.
//
//  M8-W1. The app renders answers the engine computes; it holds no ranking logic of its own
//  (M8 plan, Trap 1). Nothing here is mocked: if the engine is not running, the screen says so.

import SwiftUI

@main
struct ModelRankingApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
