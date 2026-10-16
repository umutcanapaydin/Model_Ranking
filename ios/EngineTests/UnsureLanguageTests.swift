import XCTest
import NaturalLanguage
@testable import ModelRankingEngine

/// #273: a question the recogniser reads as another language than English, below `confidentLanguage`,
/// took the English path and got a confident board, with nothing on the screen saying it was unsure.
/// The lines are the triage's two Kurmanji lines and the implementer's own (Kurmanji, Basque, Albanian,
/// Uzbek), never a held-out row. Letters beyond ASCII are written as escapes, so this file stays ASCII
/// (rule L1).
final class UnsureLanguageTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    /// Each is read as some language other than English at less than `confidentLanguage`, and none names
    /// a surface or a model, so only the reading decides its path.
    private let unsure = [
        "k\u{00EE}jan model ji bo wergerandin\u{00EA} ba\u{015F}tir e",  // Kurmanji, the triage's
        "ez dixwazim w\u{00EA}neyek\u{00EA} \u{00E7}\u{00EA}kim",          // Kurmanji, the triage's
        "al\u{00EE}kariya min bike",                                        // Kurmanji
        "zein da eredurik onena",                                           // Basque
        "cili model \u{00EB}sht\u{00EB} m\u{00EB} i miri",                  // Albanian
        "qaysi model eng yaxshi",                                           // Uzbek
    ]

    /// The premise, held so a recogniser that grows sure of one of these lines fails here, not silently
    /// elsewhere: it is unsure, and English is not its reading.
    private func assertUnsureAndNotEnglish(_ question: String, file: StaticString = #filePath, line: UInt = #line) {
        let recogniser = NLLanguageRecognizer()
        recogniser.processString(question)
        let language = recogniser.dominantLanguage ?? .undetermined
        XCTAssertNotEqual(language, .english, question, file: file, line: line)
        XCTAssertNotEqual(language, .undetermined, question, file: file, line: line)
        XCTAssertLessThan(recogniser.languageHypotheses(withMaximum: 1)[language] ?? 1,
                          SimilarityRouter.confidentLanguage, question, file: file, line: line)
    }

    func testAQuestionTheRecogniserIsUnsureOfIsNotReadAsEnglish() {
        for question in unsure {
            assertUnsureAndNotEnglish(question)
            XCTAssertFalse(SimilarityRouter.readsTurkish(question), question)
            XCTAssertFalse(SimilarityRouter.readsEnglish(question), question)
        }
    }

    /// The sign the issue names: on a device without the model, such a question is answered "not measured"
    /// (the manual fallback, REQ-RTR-003), not with a surface the embedding guessed from a sentence it did not read.
    func testAQuestionTheRecogniserIsUnsureOfIsAnsweredNotMeasured() async throws {
        struct NoEmbedding: Error {}
        guard NLContextualEmbedding(language: .english)?.hasAvailableAssets ?? false else {
            XCTFail("the embedding's assets are not on this machine, so #273's routing is not measured here")
            throw NoEmbedding()
        }
        for question in unsure {
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
            XCTAssertNil(CategoryHints.generalSurface(question, within: known), question)
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertTrue(outcome.unmeasured, question)
            XCTAssertEqual(outcome.tier, .manual, question)
        }
    }

    /// The fix's main risk, a short English question declined (the triage's note). Each is read as another
    /// language below `confidentLanguage`, but holds fewer than three words of language: a model's name
    /// or tier and a version are no language's words. Counted word by word, five of the seven would decline.
    func testAShortEnglishQuestionOfNamesAndVersionsStaysOnTheEnglishPath() {
        for question in ["claude vs gemini vs gpt", "grok 4 vs gpt 5", "kimi k2 vs glm 4.5", "qwen 3 coder vs claude",
                         "claude vs gpt", "arena elo", "gemini pro vs flash"] {
            assertUnsureAndNotEnglish(question)
            XCTAssertLessThan(SimilarityRouter.languageWords(question).count, SimilarityRouter.wordsToReadALanguage, question)
            XCTAssertTrue(SimilarityRouter.readsEnglish(question), question)
        }
        XCTAssertEqual(SimilarityRouter.languageWords("gpt-4o mu Claude Opus mu, kod"), ["mu", "mu", "kod"])
    }

    /// The other side of the floor: an unsure question with words enough, whose readings hold English at
    /// `englishAmongReadings` or more, stays on the English path.
    func testAnUnsureQuestionWhoseReadingsHoldEnglishStaysOnTheEnglishPath() {
        for question in ["rewrite my bio pls", "make me a logo pls", "bot 2 write cv", "os world leaders"] {
            assertUnsureAndNotEnglish(question)
            XCTAssertGreaterThanOrEqual(SimilarityRouter.languageWords(question).count, SimilarityRouter.wordsToReadALanguage)
            XCTAssertTrue(SimilarityRouter.readsEnglish(question), question)
        }
    }
}
