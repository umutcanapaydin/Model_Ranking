//  #199 (M21-W2): the UI target's scripted routing, and the reading each screen test waits for, live in
//  one fixture (`ios/UITests/ScreenPaths.json`) that `ScreenPathTests` launches with and this test reads.
//  So a change to how a question is read that would flip a screen path fails `swift test`, inside
//  `make check-fast`, not only `make ui-test` on the owner's Mac.

import Foundation
import XCTest

@testable import ModelRankingEngine

final class ScreenPathFixtureTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    private struct Path: Decodable {
        let q: String
        let model: [String: String]?
        let reading: String
        let surface: String?
        let refinements: [String]?
    }

    private func paths() throws -> [Path] {
        let url = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("UITests/ScreenPaths.json")
        return try JSONDecoder().decode([Path].self, from: Data(contentsOf: url))
    }

    func testEveryScreenPathIsReadAsItsUITestWaitsFor() async throws {
        let paths = try paths()
        XCTAssertGreaterThanOrEqual(paths.count, 9, "the fixture was not read")
        let table = Dictionary(uniqueKeysWithValues: paths.compactMap { path in path.model.map { (path.q, $0) } })
        let router = TieredRouter(model: ScriptedModelRouter(answers: table), similarity: SimilarityRouter())
        for path in paths {
            let outcome = await router.route(path.q, within: known)
            XCTAssertEqual("\(outcome.reading)", path.reading, path.q)
            if let surface = path.surface { XCTAssertEqual(outcome.categoryID, surface, path.q) }
            if let refinements = path.refinements { XCTAssertEqual(outcome.refinements.map(\.value), refinements, path.q) }
        }
    }
}
