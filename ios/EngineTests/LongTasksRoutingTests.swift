import NaturalLanguage
import XCTest
@testable import ModelRankingEngine

/// #379 (D-218 clause 2, D-219): METR's time horizons open `long-tasks`, the length of task a model finishes on its
/// own. A question about handing an AI a job that takes a person hours reaches it; one about writing code or clicking
/// through an app stays where it was. Every line is made up for this test; none is from a live held-out set.
final class LongTasksRoutingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality",
                         "text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit",
                         "long-tasks"]

    private func requireTheEmbedding(_ language: NLLanguage) throws {
        struct NoEmbedding: Error {}
        guard NLContextualEmbedding(language: language)?.hasAvailableAssets ?? false else {
            XCTFail("the embedding's assets are not on this machine, so the wording tier is not measured here")
            throw NoEmbedding()
        }
    }

    /// The surface has a routing hint for the model tier and six examples in each language for the wording tier.
    func testLongTasksIsDescribedForBothTiers() {
        XCTAssertNotNil(CategoryHints.byID["long-tasks"])
        XCTAssertEqual(CategoryHints.examples["long-tasks"]?.count, 6)
        XCTAssertEqual(CategoryHints.examplesTurkish["long-tasks"]?.count, 6)
    }

    /// Its Turkish name, the line saying what it is for in both languages, and its scale in words.
    func testLongTasksHasATurkishNameALineAndAScaleInBothLanguages() {
        XCTAssertEqual(UIText.surface(id: "long-tasks", engineTitle: "Long tasks", .turkish), "Uzun görevler")
        let english = UIText.surfaceBlurb("long-tasks", .english), turkish = UIText.surfaceBlurb("long-tasks", .turkish)
        XCTAssertNotNil(english)
        XCTAssertNotNil(turkish)
        XCTAssertNotEqual(english, turkish)
        XCTAssertNotNil(scaleExplanation(for: "minutes"))
        XCTAssertNotNil(scaleExplanation(for: "minutes", in: .turkish))
        XCTAssertEqual(localisedUnit("minutes", in: .turkish), "dakika")
        XCTAssertEqual(scoreText(1044.78, metric: "minutes", .english), "1044.8 minutes")
    }

    /// The probe: a question that names a long job on its own reaches the surface on its words, in both languages.
    func testAQuestionAboutAJobThatTakesHoursReachesLongTasksOnItsWords() {
        for question in ["which model can work on a long task for hours on its own",
                         "hangi model saatlerce süren uzun bir görevi tek başına yapabilir"] {
            XCTAssertEqual(CategoryHints.namedSurface(question, within: known), "long-tasks", question)
        }
    }

    /// The wording tier, on a device with no on-device model: a question in a reader's own words reaches it.
    func testTheWordingTierAnswersALongTaskQuestionFromItsBoard() async throws {
        try requireTheEmbedding(.english)
        let outcome = await TieredRouter(model: nil).route("give an agent a job that would take me a whole day",
                                                           within: known)
        XCTAssertEqual(outcome.categoryID, "long-tasks")
        XCTAssertFalse(outcome.unmeasured)
    }

    /// An engine that serves no `long-tasks` (an older one) is never sent a question to it.
    func testAnEngineWithoutLongTasksIsNeverSentToIt() async {
        let older = known.filter { $0 != "long-tasks" }
        let question = "which model can work on a long task for hours on its own"
        XCTAssertNotEqual(CategoryHints.namedSurface(question, within: older), "long-tasks")
        let outcome = await TieredRouter(model: nil).route(question, within: older)
        XCTAssertTrue(older.contains(outcome.categoryID), question)
    }
}
