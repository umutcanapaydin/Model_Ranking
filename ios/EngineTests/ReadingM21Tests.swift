//  M21-W2 (REQ-ASK-005): reading what is not a search, again. A search that names a ranked model is no
//  question of fact (#194); a short Turkish question is read as Turkish before the embedding (#218);
//  the probe harnesses' rows are rebuilt by code a test runs (#193).

import XCTest

@testable import ModelRankingEngine

final class ModelNameSearchTests: OfflineTestCase {
    /// #194: a search that names a model the engine ranks, beyond the eleven brands the list once
    /// held, is no question of fact, on either tier.
    func testASearchNamingARankedModelIsNoQuestionOfFact() {
        for text in ["what is cheaper, qwen or kimi", "how much does o3 cost per million tokens", "who makes mixtral",
                     "how much does phi-4 cost", "what is the context window of qwen3", "who trains nemotron",
                     "when did glm 4.5 come out", "kimi mi qwen mi daha ucuz", "how many tokens can magistral read"] {
            XCTAssertFalse(InputSignals.asksAFact(text), text)
        }
        for tier in [RoutingTier.model, .similarity] {
            let read = TieredRouter.read("what is cheaper, qwen or kimi",
                                         RoutingOutcome(categoryID: "assistant", tier: tier, unmeasured: false))
            XCTAssertEqual(read.reading, .search, "\(tier)")
        }
    }

    /// #194: a family word that is also plain English names a model only beside a version.
    func testAFamilyWordThatIsAlsoEnglishNeedsAVersion() {
        for text in ["what is phi in mathematics", "who was the titan atlas", "where is palmyra",
                     "what is the command for undo"] {
            XCTAssertTrue(InputSignals.asksAFact(text), text)
        }
        for text in ["how much does phi 4 cost", "what is phi-4 good at", "how fast is nova 2"] {
            XCTAssertFalse(InputSignals.asksAFact(text), text)
        }
    }

    /// #194: the family words are the registry's, not a hand-kept list.
    func testTheFamilyWordsAreTheRegistrys() {
        XCTAssertTrue(ModelFamilies.words.isSuperset(of: ["qwen", "kimi", "mixtral", "o3", "claude", "gpt", "gemini"]))
        XCTAssertTrue(ModelFamilies.ambiguous.isSubset(of: ModelFamilies.words))
    }
}

final class TurkishBeforeTheEmbeddingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    /// #218: a Turkish particle or a Turkish letter makes a question Turkish before the embedding.
    func testAParticleOrATurkishLetterReadsAsTurkish() {
        for text in ["claude mu chatgpt mi almanca", "kod için hangisi", "en iyi model hangisi",
                     "çeviri için model", "gemini mı daha iyi"] {
            XCTAssertTrue(CategoryHints.readsAsTurkish(text), text)
        }
        for text in ["best model for coding", "is it mid or good", "which ai writes music", "mixtral vs qwen"] {
            XCTAssertFalse(CategoryHints.readsAsTurkish(text), text)
        }
    }

    /// #218: such a question is answered by the Turkish path, never by the English embedding's guess.
    func testAShortTurkishQuestionWithAnExtraWordIsAGeneralQuestion() async {
        let outcome = await SimilarityRouter().route("claude mu chatgpt mi almanca", within: known)
        XCTAssertEqual(outcome?.categoryID, "everyday")
    }
}

final class ProbeRowTests: OfflineTestCase {
    /// #193: a recorded model row read back gives the reading this copy's code gives it.
    func testARecordedRowReadBackGivesItsReading() {
        let row = ["q": "what is the capital of australia", "routed": "assistant", "declined": "false",
                   "model": "not", "surface": "assistant", "unmeasured": "false", "reading": "notASearch"]
        let rebuilt = ProbeRows.rebuild(row)
        XCTAssertEqual(rebuilt?.categoryID, "assistant")
        XCTAssertEqual(rebuilt?.tier, .model)
        XCTAssertEqual(rebuilt?.reading, .unsure, "the model's \"not\" is its doubt")
        let replayed = ProbeRows.replay(row)
        XCTAssertEqual(replayed["reading"], "notASearch", "the model's doubt and a question of fact")
        XCTAssertEqual(replayed["surface"], "assistant")
        XCTAssertEqual(replayed["routed"], "assistant")
        let search = ProbeRows.replay(["q": "best model for coding", "routed": "coding", "declined": "false",
                                       "model": "search"])
        XCTAssertEqual(search["reading"], "search")
        XCTAssertEqual(search["unmeasured"], "false")
        XCTAssertNil(ProbeRows.rebuild(["q": "x", "routed": "nil", "declined": "false", "model": "nil"]))
        XCTAssertEqual(ProbeRows.replay(["q": "x", "routed": "nil"]), ["q": "x", "routed": "nil"],
                       "a row the model answered nothing stays so")
    }

    /// #193: the wording mode's row on a question the wording tier declines.
    func testTheWordingRowOnADeclinedQuestion() {
        let read = RoutingOutcome(categoryID: "assistant", tier: .manual, unmeasured: true)
        let row = ProbeRows.wordingRow("asdf qwer zxcv", tier: nil, read: read)
        XCTAssertEqual(row["routed"], "nil")
        XCTAssertEqual(row["declined"], "true")
        XCTAssertEqual(row["tier"], "manual")
        XCTAssertEqual(row["model"], "nil")
        XCTAssertEqual(row["unmeasured"], "true")
        XCTAssertEqual(row["surface"], "assistant")
    }
}
