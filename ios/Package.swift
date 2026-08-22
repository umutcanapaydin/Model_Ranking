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
    // macOS is where `swift test` runs.
    //
    // **The rationale first written here was wrong, and the independent seat disproved it by
    // measurement.** It claimed the macOS floor had to be 26 or the `FoundationModels` tier would
    // be stripped and the tests would pass against code the app does not ship. Lowering it to
    // `.macOS(.v14)` leaves the suite green AND the tier still compiled — `#if canImport` and
    // `@available` do that work, not the manifest floor. The claim was plausible, load-bearing in
    // its own comment, and false: a record stating the opposite of the code, which is the defect
    // this project has recorded more times than any other.
    //
    // The floor stays at 26 because that is the toolchain this is developed and run on, and a
    // manifest that understates its platform is a different lie. It is NOT what keeps the tier
    // compiled.
    //
    // The iOS line is likewise NOT a drift guard — nothing compares it to the project's
    // `IPHONEOS_DEPLOYMENT_TARGET`, and the first version of this comment said it was (W-059).
    // It is declared because a library needs a platform, and it is set to the app's target so the
    // two at least START in agreement.
    platforms: [.macOS(.v26), .iOS(.v18)],
    products: [.library(name: "ModelRankingEngine", targets: ["ModelRankingEngine"])],
    targets: [
        .target(
            name: "ModelRankingEngine",
            path: "ModelRanking/Engine",
            // The SAME FILES compiled in a DIFFERENT language mode is a narrower guarantee than
            // "compiles what the app ships", and the independent seat is what made the difference
            // legible: `swift-tools-version: 6.2` puts the target in Swift 6 mode while the
            // project sets `SWIFT_VERSION = 5.0`. Nothing in the Engine is conditionally compiled
            // today, so nothing diverged — but "no divergence today" is a measurement, not a
            // property, and the claim in this manifest was the stronger one.
            //
            // Pinned to the app's mode so the claim is true of the COMPILATION and not only of the
            // file list. `tests/unit/test_ios_platform_drift.py` compares the two and fails when
            // they part, so this pin cannot silently rot the way the comment above it once did.
            // The TEST target stays in the newer mode: strict concurrency on the test code is free
            // and does not change what the Engine is built as.
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .testTarget(
            name: "ModelRankingEngineTests",
            dependencies: ["ModelRankingEngine"],
            path: "EngineTests"
        ),
    ]
)
