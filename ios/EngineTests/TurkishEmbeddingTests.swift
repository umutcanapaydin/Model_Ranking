import XCTest
import NaturalLanguage
@testable import ModelRankingEngine

/// #222 (the reading wave of 2026-10-14): a confidently Turkish question that names no surface is read
/// by the wording tier against Turkish examples, through the same multilingual embedding, instead of
/// falling to "not measured". Every line is from the wave's own tuning sentences
/// (`scripts/router_probe/turkish_tuning_questions.json`) or the review's own
/// (`docs/reviews/backlog-reading-review*.md`, three rounds), never from a held-out set. Turkish letters
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
        for question in ["gemini mi gpt mi \u{00F6}dev", "\u{00E7}eviri i\u{00E7}in claude mu", "en iyi model hangisi bence", "hangi model daha iyi sence",
                         "en iyi model for writing cover letters"] {
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
            XCTAssertFalse(outcome.unmeasured, question)
            let unserved = await SimilarityRouter().route(question, within: known.filter { $0 != "everyday" })
            XCTAssertNotNil(unserved, question)
            XCTAssertEqual(unserved?.unmeasured, false, question)
        }
    }

    /// The review's M2: the recogniser knows no Azerbaijani or Turkmen and reads them as Turkish. A letter
    /// Turkish never writes keeps them out, so they decline as before. The round-2 review's N2: the Turkmen
    /// line is one the recogniser itself reads as Turkish, so only the letter rule keeps it out.
    func testALetterTurkishNeverWritesIsNotTurkish() async {
        let turkmen = "men\u{00E4} bir hat \u{00FD}azy\u{0148}"
        let recogniser = NLLanguageRecognizer()
        recogniser.processString(turkmen)
        XCTAssertEqual(recogniser.dominantLanguage, .turkish)
        XCTAssertGreaterThanOrEqual(recogniser.languageHypotheses(withMaximum: 1)[.turkish] ?? 0,
                                    SimilarityRouter.confidentLanguage)
        // The round-3 review's N2: decomposed, the Turkmen line is still kept out.
        for question in ["m\u{0259}n\u{0259} bir \u{015F}eir yaz", turkmen, turkmen.decomposedStringWithCanonicalMapping] {
            XCTAssertFalse(SimilarityRouter.readsTurkish(question), question)
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertNil(outcome, question)
        }
        XCTAssertTrue(SimilarityRouter.readsTurkish("y\u{00FC}kledi\u{011F}im foto\u{011F}rafta ne var"))
    }

    /// The round-2 review's M2: an emoji's variation selector or a decomposed accent is a mark, not a letter,
    /// so a Turkish question that carries one is still Turkish.
    func testAMarkIsNotALetterTurkishNeverWrites() {
        let question = "h\u{00FC}cre zar\u{0131}ndan iyonlar nas\u{0131}l ge\u{00E7}er"
        XCTAssertTrue(SimilarityRouter.readsTurkish(question + " \u{2764}\u{FE0F}"))
        XCTAssertTrue(SimilarityRouter.readsTurkish(question.decomposedStringWithCanonicalMapping))
        // The round-3 review's N1: a Greek letter or an accented Latin one is no Turkic letter.
        XCTAssertTrue(SimilarityRouter.readsTurkish(question + " \u{03C0}"))
        XCTAssertTrue(SimilarityRouter.readsTurkish(question + " caf\u{00E9}"))
    }

    /// The round-2 review's N1: a Turkish question typed without its letters is read against the examples
    /// in plain letters too. Against the lettered ones alone this line read as `factuality` in the tuning run.
    func testATurkishQuestionTypedWithoutItsLettersReachesItsSurface() async throws {
        try requireTheEmbedding()
        let question = "annemin dogum gunu icin guzel bir mesaj yazar misin"
        XCTAssertTrue(SimilarityRouter.readsTurkish(question))
        let outcome = await SimilarityRouter().route(question, within: known)
        XCTAssertEqual(outcome?.categoryID, "assistant")
    }

    /// The round-2 review's N3: the kept vectors are the router's examples, never the typed question; and the
    /// round-2 review's N4: a Turkish question that names its surface keeps it, and now also offers the two
    /// closest others, as an English one does.
    func testTheKeptVectorsAreExamplesOnlyAndANamedTurkishQuestionOffersAlternatives() async throws {
        try requireTheEmbedding()
        let question = "python kodumu h\u{0131}zland\u{0131}r"
        let outcome = await SimilarityRouter().route(question, within: known)
        XCTAssertEqual(outcome?.categoryID, "coding")
        XCTAssertEqual(outcome?.alternatives.count, 2)
        let typed = "bu c\u{00FC}mle hi\u{00E7}bir \u{00F6}rnekte ge\u{00E7}meyen tuhaf bir soru"
        _ = await SimilarityRouter().route(typed, within: known)
        let examples = Set((CategoryHints.examples.values.flatMap { $0 })
                           + CategoryHints.examplesTurkishBothSpellings.values.flatMap { $0 }
                           + CategoryHints.unmeasuredHints.flatMap { $0 }
                           + CategoryHints.unmeasuredHintsTurkishBothSpellings.flatMap { $0 })
        let kept = ExampleVectors.shared.keys
        XCTAssertFalse(kept.isEmpty)
        for key in kept {
            XCTAssertTrue(examples.contains(String(key.split(separator: "\n", omittingEmptySubsequences: false).last ?? "")), key)
        }
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

/// #293 (run golden-night, D-206 clause 1): a plain question that names no surface, and that is close to
/// nothing in particular, is read by the example sentences. Before #293 such a question could settle on
/// `mathematics` or another surface it had nothing to do with; the search-with-sources, factuality and
/// assistant examples now give it somewhere better to land. Every question here is made up for this test,
/// none is from the golden set or a held-out set. Turkish letters are escapes, so this file stays ASCII.
final class PlainRequestReadingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    /// Where the assets do not load, these tests fail rather than pass asserting nothing.
    private func requireTheEmbedding() throws {
        struct NoEmbedding: Error {}
        guard NLContextualEmbedding(language: .english)?.hasAvailableAssets ?? false,
              NLContextualEmbedding(language: .turkish)?.hasAvailableAssets ?? false else {
            XCTFail("the embedding's assets are not on this machine, so #293's routing is not measured here")
            throw NoEmbedding()
        }
    }

    private func assertRoutes(_ question: String, to surface: String, file: StaticString = #filePath,
                              line: UInt = #line) async {
        XCTAssertNil(CategoryHints.namedSurface(question, within: known), "no keyword: \(question)", file: file, line: line)
        let outcome = await TieredRouter(model: nil).route(question, within: known)
        XCTAssertEqual(outcome.categoryID, surface, question, file: file, line: line)
        XCTAssertFalse(outcome.unmeasured, question, file: file, line: line)
        XCTAssertEqual(outcome.tier, .similarity, question, file: file, line: line)
    }

    /// An English request for studies with their sources is a search that must cite real pages.
    func testAnEnglishRequestForStudiesWithTheirSourcesIsASearchWithSources() async throws {
        try requireTheEmbedding()
        await assertRoutes("show me published papers on how screen time affects kids, with the sources",
                           to: "search_factuality")
    }

    /// A Turkish request for a few polite sentences to someone is a short message to write: `assistant`.
    func testATurkishRequestForAFewPoliteSentencesIsAMessageToWrite() async throws {
        try requireTheEmbedding()
        for question in [
            "ev arkada\u{015F}\u{0131}ma bu ak\u{015F}am ge\u{00E7} gelece\u{011F}imi nazik\u{00E7}e s\u{00F6}yleyen iki c\u{00FC}mle",
            "\u{00F6}\u{011F}retmenime \u{00F6}devi yar\u{0131}n teslim edece\u{011F}imi kibarca anlatan \u{00FC}\u{00E7} c\u{00FC}mle",
        ] {
            XCTAssertTrue(SimilarityRouter.readsTurkish(question.lowercased()), question)
            await assertRoutes(question, to: "assistant")
        }
    }

    /// What stays: a question that really is maths, with number words in it, is still read as maths.
    func testAMathsQuestionWithNumberWordsIsStillMaths() async throws {
        try requireTheEmbedding()
        await assertRoutes("solve for x in two x plus three equals eleven", to: "mathematics")
        await assertRoutes("iki say\u{0131}n\u{0131}n toplam\u{0131} on ise ve fark\u{0131} iki ise say\u{0131}lar ka\u{00E7}",
                           to: "mathematics")
    }
}
