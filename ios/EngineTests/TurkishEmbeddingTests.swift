import XCTest
import NaturalLanguage
@testable import ModelRankingEngine

/// #222 (the reading wave of 2026-10-14): a confidently Turkish question that names no surface is read
/// by the wording tier against Turkish examples, through the same multilingual embedding, instead of
/// falling to "not measured". Every line is from the wave's own tuning sentences
/// (`scripts/router_probe/turkish_tuning_questions.json`) or the review's own
/// (`docs/reviews/backlog-reading-review.md`), never from a held-out set. Turkish letters
/// are written as escapes, so this file stays ASCII (rule L1).
final class TurkishEmbeddingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    private var embeddingLoads: Bool {
        NLContextualEmbedding(language: .turkish)?.hasAvailableAssets ?? false
    }

    /// The review's N7: where the assets do not load, these tests fail rather than pass asserting nothing.
    /// A skip is no way out: `make swift-test` fails a skipped test (M16-W1, M-3).
    private func requireTheEmbedding() throws {
        struct NoEmbedding: Error {}
        guard embeddingLoads else {
            XCTFail("the embedding's assets are not on this machine, so #222's routing is not measured here")
            throw NoEmbedding()
        }
    }

    func testATurkishSearchThatNamesNoSurfaceReachesItsSurface() async throws {
        try requireTheEmbedding()
        for (question, surface) in [
            ("h\u{00FC}cre zar\u{0131}ndan iyonlar nas\u{0131}l ge\u{00E7}er", "expert"),
            ("bug\u{00FC}nk\u{00FC} dolar kuru ne", "search"),
            ("annemin do\u{011F}um g\u{00FC}n\u{00FC} i\u{00E7}in g\u{00FC}zel bir mesaj yazar m\u{0131}s\u{0131}n", "assistant"),
            ("bu haberin do\u{011F}ru olup olmad\u{0131}\u{011F}\u{0131}n\u{0131} kontrol et", "factuality"),
        ] {
            XCTAssertTrue(SimilarityRouter.readsTurkish(question.lowercased()), question)
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), "no keyword: \(question)")
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertEqual(outcome.categoryID, surface, question)
            XCTAssertFalse(outcome.unmeasured, question)
            XCTAssertEqual(outcome.tier, .similarity, question)
        }
    }

    /// The review's M1: a Turkish question about models in general keeps `everyday`, as before #222,
    /// whether it names a brand or asks for the best model; its names pull the embedding off the task.
    /// The review's N6: where the engine serves no `everyday`, the embedding answers instead.
    func testATurkishQuestionAboutModelsInGeneralKeepsEveryday() async throws {
        try requireTheEmbedding()
        for question in ["gemini mi gpt mi \u{00F6}dev", "\u{00E7}eviri i\u{00E7}in claude mu", "en iyi model hangisi bence", "hangi model daha iyi sence"] {
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
            XCTAssertFalse(outcome.unmeasured, question)
            let unserved = await SimilarityRouter().route(question, within: known.filter { $0 != "everyday" })
            XCTAssertNotNil(unserved, question)
            XCTAssertEqual(unserved?.unmeasured, false, question)
        }
    }

    /// The review's M2: the recogniser knows no Azerbaijani or Turkmen and reads them as Turkish. A letter
    /// Turkish never writes keeps them out, so they decline as before.
    func testALetterTurkishNeverWritesIsNotTurkish() async {
        for question in ["m\u{0259}n\u{0259} bir \u{015F}eir yaz", "ma\u{0148}a bir hat \u{00FD}az"] {
            XCTAssertFalse(SimilarityRouter.readsTurkish(question), question)
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertNil(outcome, question)
        }
        XCTAssertTrue(SimilarityRouter.readsTurkish("y\u{00FC}kledi\u{011F}im foto\u{011F}rafta ne var"))
    }

    /// The review's N3: a request to change an image is answered from `vision` through the Turkish
    /// decline groups. Without them it read as `assistant` in the tuning run.
    func testATurkishRequestToChangeAnImageIsAnsweredFromVision() async throws {
        try requireTheEmbedding()
        let question = "selfiemdeki k\u{0131}rm\u{0131}z\u{0131} g\u{00F6}zleri d\u{00FC}zelt"
        XCTAssertNil(CategoryHints.namedSurface(question, within: known))
        let outcome = await SimilarityRouter().route(question, within: known)
        XCTAssertEqual(outcome?.categoryID, "vision")
    }

    /// The review's N2: the model's "none of these" on a question it read as a search goes to the wording
    /// tier (D-187 clause 4), which now reads a Turkish question too.
    func testTheModelsDeclineOnATurkishSearchGoesToTheTurkishPath() async throws {
        try requireTheEmbedding()
        let question = "h\u{00FC}cre zar\u{0131}ndan iyonlar nas\u{0131}l ge\u{00E7}er"
        let declined = await TieredRouter(
            model: ScriptedModelRouter(answers: [question: ["request": "a model search",
                                                            "surface": ModelOutputBoundary.declineSentinel]]),
            similarity: SimilarityRouter()
        ).route(question, within: known)
        XCTAssertEqual(declined.categoryID, "expert")
        XCTAssertFalse(declined.unmeasured)
        XCTAssertEqual(declined.tier, .similarity)
    }

    /// Turkish is the one other language read: a question the recogniser is sure is German still
    /// declines, and the caller drops to the manual fallback.
    func testAnotherLanguageStillDeclines() async {
        let german = "welches sprachmodell schreibt die sch\u{00F6}nsten gedichte f\u{00FC}r meine gro\u{00DF}mutter"
        XCTAssertFalse(SimilarityRouter.readsEnglish(german))
        XCTAssertFalse(SimilarityRouter.readsTurkish(german))
        let outcome = await SimilarityRouter().route(german, within: known)
        XCTAssertNil(outcome)
    }

    /// The Turkish examples cover the surfaces the English ones do, and the decline groups match one
    /// for one: a surface the Turkish reader cannot reach would be a silent gap.
    func testTheTurkishExamplesCoverTheSameSurfaces() {
        XCTAssertEqual(Set(CategoryHints.examplesTurkish.keys), Set(CategoryHints.examples.keys))
        for (surface, lines) in CategoryHints.examplesTurkish {
            XCTAssertGreaterThanOrEqual(lines.count, 2, surface)
        }
        XCTAssertEqual(CategoryHints.unmeasuredHintsTurkish.count, CategoryHints.unmeasuredHints.count)
    }
}
