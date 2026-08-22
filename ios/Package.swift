// swift-tools-version: 6.2
//
//  W-038, open since M8-W2: 1,093 lines of Swift and nothing in this repository executed a single
//  one of them. `runner` compiled the app and never ran it, and `ModelRankingTests/` was an empty
//  directory the project file did not reference.
//
//  This package exists so `swift test` compiles THE SAME FILES THE APP SHIPS. The target `path`
//  points at `ModelRanking/Engine` — the sources the `.xcodeproj` builds — so there is no second
//  copy to drift, and the project file is not modified at all. A test suite that runs against a
//  duplicate of the code is a test suite that passes while the product is broken.
//
//  **Deliberately scoped to the Engine layer, and the record says so rather than implying the iOS
//  half is covered.** `ContentView.swift` and `ModelRankingApp.swift` are SwiftUI and stay
//  unexecuted. The Engine is where a defect changes what a reader is TOLD: which surface a
//  question routes to, whether a redirect is followed off-host, whether a malformed payload
//  renders as a blank screen.

import PackageDescription

let package = Package(
    name: "ModelRankingEngine",
    // macOS is where `swift test` runs. The floor is 26 because `FoundationModels` is compiled in
    // under `#if canImport` and its tier is `@available(macOS 26.0, *)` — a lower floor would build
    // the file with that whole tier stripped, and the tests would pass against code the app does
    // not ship. iOS 18 is the app target and is declared so the platform pair cannot silently drift.
    platforms: [.macOS(.v26), .iOS(.v18)],
    products: [.library(name: "ModelRankingEngine", targets: ["ModelRankingEngine"])],
    targets: [
        .target(name: "ModelRankingEngine", path: "ModelRanking/Engine"),
        .testTarget(
            name: "ModelRankingEngineTests",
            dependencies: ["ModelRankingEngine"],
            path: "EngineTests"
        ),
    ]
)
