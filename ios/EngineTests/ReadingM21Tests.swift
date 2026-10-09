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
        // The review's M3: an ambiguous word stands as a model beside a version its own names use (Phi-3,
        // Nova 2), or in a question about a model's cost or making.
        for text in ["how much does phi 4 cost", "what is phi-3 good at", "how fast is nova 2"] {
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

final class WordingTierReachTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    /// #222 (M21-W2): a Turkish search that asks for "the best one", "which one", a model or a
    /// recommendation, naming no surface, is a general question, not "not measured". Written for this
    /// test, never from a held-out set.
    func testATurkishAskForTheBestOneIsAGeneralQuestion() async {
        for question in ["ingilizce e-posta yazmak için en iyisi hangisi", "fransızca mektup yazmama yardım edecek model",
                         "muhasebe soruları için hangisi daha iyi", "şiir yazmak için en iyisi",
                         "bir hikaye yazdırmak istiyorum hangisi iyi", "yazı: blog yazısı için öneri",
                         "sunum hazırlamak için en iyisi", "ödev yaparken hangisini kullanayım",
                         "yemek tarifi önerecek model", "dil öğrenmek için en iyisi"] {
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
            XCTAssertEqual(CategoryHints.generalSurface(question, within: known), "everyday", question)
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertFalse(outcome.unmeasured, question)
        }
    }

    /// #222: a question that is no ask for the best one stays as it was.
    func testATurkishQuestionThatAsksForNoneIsNoGeneralQuestion() {
        for question in ["hangisi daha uzun, nil mi amazon mu", "bugün hava nasıl", "kitabın yazarı kim"] {
            XCTAssertNil(CategoryHints.generalSurface(question, within: known), question)
        }
    }
}

/// The M21-W2 review's M1 to M3 and K1 (#194, D-191): a served model's name is a search whatever its
/// version's spelling; a word with a second meaning is no model unless it stands as one.
final class ModelNameReviewTests: OfflineTestCase {
    func testAServedModelIsASearchWhateverItsVersionsSpelling() {
        for text in ["who makes llama", "how much does llama cost per token", "how much does kimi k2 cost",
                     "who makes command r", "who trains aya expanse", "how fast is nova lite", "who makes trinity large",
                     "what is minimax m2", "how big is gemma 3", "what is o3 mini"] {
            XCTAssertFalse(InputSignals.asksAFact(text), text)
        }
    }

    func testAWordWithASecondMeaningIsNoModelUnlessItStandsAsOne() {
        for text in ["who founded nvidia", "what is the minimax algorithm", "what is o3 in chemistry",
                     "what is mimo in wifi", "what is a glm in statistics", "who is gemma chan",
                     "how long does an o1 visa take", "who were the mercury 7 astronauts", "when is usmle step 1",
                     "what do llamas eat", "who is kimi raikkonen"] {
            XCTAssertTrue(InputSignals.asksAFact(text), text)
        }
    }

    func testAModelOnlyTheEngineServesIsASearch() {
        let served = ServedModelNames(displayNames: ["StarCoder 2 15B", "Yi-34B", "Solar Pro 4", "Muse Spark"])
        for text in ["who makes starcoder 2", "when did yi-34b come out", "who makes solar pro 4", "what is muse spark"] {
            XCTAssertTrue(InputSignals.asksAFact(text), "\(text): no model with no served names")
            XCTAssertFalse(InputSignals.asksAFact(text, served: served), text)
            let read = TieredRouter.read(text, RoutingOutcome(categoryID: "assistant", tier: .similarity,
                                                              unmeasured: false), served: served)
            XCTAssertEqual(read.reading, .search, text)
        }
        for text in ["what is solar energy", "who is the greek muse of history"] {
            XCTAssertTrue(InputSignals.asksAFact(text, served: served), text)
        }
        let fromStandings = ServedModelNames(Standings(apiVersion: "v1", attributions: [], boards: [],
                                                       models: [StandingModel(id: "yi-34b", display: "Yi-34B", vendor: "01",
                                                                              blendedPerM: 1, accessibility: nil)]))
        XCTAssertFalse(InputSignals.asksAFact("when did yi-34b come out", served: fromStandings))
    }

    /// K1: a question made only of model names reads every family the registry names.
    func testAComparisonOfAnyRankedFamiliesIsAGeneralQuestion() {
        for question in ["mixtral mi qwen mi", "nemotron mu claude mu"] {
            XCTAssertTrue(CategoryHints.comparesModelsOnly(question), question)
        }
        XCTAssertFalse(CategoryHints.comparesModelsOnly("kimi mi geldi"), "kimi alone is a Turkish word")
    }
}
