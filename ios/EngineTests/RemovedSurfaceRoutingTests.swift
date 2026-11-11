import XCTest
@testable import ModelRankingEngine

/// D-249 clause 5: METR's time horizons left the app, and `long-tasks` with them. A question about a long unattended
/// job now reads as the nearest surface the router finds among the ones served, in both languages, and the surface
/// keeps no hint, example or name. Every line is made up for this test; none is from a live held-out set.
final class RemovedSurfaceRoutingTests: OfflineTestCase {
    private let served = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                          "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                          "search", "search_factuality",
                          "text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit"]

    private let longJobQuestions = ["which model can work on a long task for hours on its own",
                                    "give an agent a job that would take me a whole day",
                                    "hangi model saatlerce süren uzun bir görevi tek başına yapabilir"]

    /// The surface is gone from both tiers' descriptions.
    func testLongTasksKeepsNoHintAndNoExamples() {
        XCTAssertNil(CategoryHints.byID["long-tasks"])
        XCTAssertNil(CategoryHints.examples["long-tasks"])
        XCTAssertNil(CategoryHints.examplesTurkish["long-tasks"])
    }

    /// A long-job question names no removed surface on its words.
    func testALongJobQuestionNamesNoRemovedSurface() {
        for question in longJobQuestions {
            XCTAssertNotEqual(CategoryHints.namedSurface(question, within: served + ["long-tasks"]), "long-tasks",
                              question)
        }
    }

    /// With no on-device model, a long-job question reaches a surface the engine serves, never the removed one.
    func testALongJobQuestionReadsAsTheNearestServedSurface() async {
        for question in longJobQuestions {
            let outcome = await TieredRouter(model: nil).route(question, within: served)
            XCTAssertTrue(served.contains(outcome.categoryID), "\(question) -> \(outcome.categoryID)")
        }
    }
}
