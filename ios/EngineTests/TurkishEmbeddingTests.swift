import XCTest
import NaturalLanguage
@testable import ModelRankingEngine

/// #222 (the reading wave of 2026-10-14): a confidently Turkish question that names no surface is read
/// by the wording tier against Turkish examples, through the same multilingual embedding, instead of
/// falling to "not measured". Every line is from the wave's own tuning sentences
/// (`scripts/router_probe/turkish_tuning_questions.json`), never from a held-out set. Turkish letters
/// are written as escapes, so this file stays ASCII (rule L1).
final class TurkishEmbeddingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    private var embeddingLoads: Bool {
        NLContextualEmbedding(language: .turkish)?.hasAvailableAssets ?? false
    }

    func testATurkishSearchThatNamesNoSurfaceReachesItsSurface() async {
        // Asserts only where the embedding assets load, as `testTheWordingTierNeverRefines` does.
        guard embeddingLoads else { return }
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

    /// A Turkish question naming an AI brand keeps `everyday`, as before #222: the names pull the
    /// embedding off the one word that is the task ("\u{00F6}dev" read as `abstract` in the tuning run).
    func testATurkishQuestionNamingABrandKeepsEveryday() async {
        for question in ["gemini mi gpt mi \u{00F6}dev", "\u{00E7}eviri i\u{00E7}in claude mu"] {
            XCTAssertTrue(CategoryHints.namesABrand(question), question)
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
            XCTAssertFalse(outcome.unmeasured, question)
        }
        XCTAssertFalse(CategoryHints.namesABrand("en iyi yapay zeka hangisi"))
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
