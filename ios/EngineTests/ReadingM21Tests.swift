//  M21-W2 (REQ-ASK-005): reading what is not a search, again. A search that names a ranked model is no
//  question of fact (#194); a short Turkish question is read as Turkish before the embedding (#218);
//  the probe harnesses' rows are rebuilt by code a test runs (#193).

import XCTest

@testable import ModelRankingEngine

final class ModelNameSearchTests: OfflineTestCase {
    /// #194: a search that names a model the engine ranks, beyond the eleven brands the list once
    /// held, is no question of fact, on either tier.
    func testASearchNamingARankedModelIsNoQuestionOfFact() {
        // The second review's M3: "o3" and "phi" alone are ambiguous (ozone, a letter), so their examples
        // name a version their names use; "phi-4" is read from the served names (testAServedVersion...).
        for text in ["what is cheaper, qwen or kimi", "how much does o3 mini cost per million tokens", "who makes mixtral",
                     "how much does phi-3 cost", "what is the context window of qwen3", "who trains nemotron",
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
        // The second review's M3: an ambiguous word stands as a model only beside a version its own names
        // use (Phi-3, Nova 2), written apart or onto the name (M4: "llama3", "gemma3").
        for text in ["what is phi-3 good at", "how fast is nova 2", "what is llama3 good at", "what is gemma3 good at",
                     "llama3'ü kim yaptı"] {
            XCTAssertFalse(InputSignals.asksAFact(text), text)
        }
        // A served name supplies a version the registry's names do not: Phi-4 (the second review's M4).
        let served = ServedModelNames(displayNames: ["Phi-4", "Llama 4 Maverick"])
        for text in ["what is phi-4 good at", "what is phi4 good at", "when did llama 4 come out"] {
            XCTAssertTrue(InputSignals.asksAFact(text), "\(text): no served names")
            XCTAssertFalse(InputSignals.asksAFact(text, served: served), text)
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

    // #222's general-ask rule is taken out after the second review (M1, D-191): its task words have a
    // second reading ("yaz" is summer, "öğrenci" a student, "bot" boots), so an ask for "the best one"
    // that names no surface is "not measured" again, as at 972b55e; #222 stays open with that state.

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
        for text in ["how much does kimi k2 cost", "who makes command r", "who trains aya expanse", "how fast is nova lite",
                     "who makes trinity large", "what is minimax m2", "how big is gemma 3", "what is o3 mini",
                     "who makes llama 3"] {
            XCTAssertFalse(InputSignals.asksAFact(text), text)
        }
    }

    /// The second review's M3 (D-191): no word about cost or making turns an ambiguous word, or a word only
    /// the engine serves, into a model; only a version its names use does.
    func testCostOrMakingWordsMakeNoModel() {
        let served = ServedModelNames(displayNames: ["Solar Pro 4", "Meta Llama 3.1 8B"])
        for text in ["how much does a granite countertop cost", "what is the price of granite per square foot",
                     "what is the price of mercury", "when was mercury released as a single",
                     "how much does a command strip cost", "how much does a titan watch cost",
                     "when was the titan submarine released", "how much does the usmle step 1 cost",
                     "how much does an o1 visa cost", "what is the price of nvidia stock", "who makes llama",
                     "how much do solar panels cost", "who makes meta quest", "how much does a meta quest 3 cost"] {
            XCTAssertTrue(InputSignals.asksAFact(text, served: served), text)
        }
    }

    func testAWordWithASecondMeaningIsNoModelUnlessItStandsAsOne() {
        for text in ["who founded nvidia", "what is the minimax algorithm", "what is o3 in chemistry",
                     "what is mimo in wifi", "what is a glm in statistics", "who is gemma chan",
                     "how long does an o1 visa take", "who were the mercury 7 astronauts", "when is usmle step 1",
                     "what is a llama", "who is kimi raikkonen"] {
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


/// The M21-W2 review's M4 and M5 (D-191): an ask for "the best one" is general only about a task or a
/// model; only a letter Turkish alone has, or two Turkish signals, read a question as Turkish.
final class TurkishReadingReviewTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    /// M4: an ask with no task and no model ("which is best for coffee", "where is best for a holiday")
    /// is no general question.
    func testAnAskAboutNoTaskOrModelIsNoGeneralQuestion() {
        for question in ["tatil için en iyisi neresi", "kahve için en iyisi hangisi", "araba almak için hangisi daha iyi",
                         "hangisi iyi, iphone mu samsung mu", "model uçak yapımı", "en ünlü model kim",
                         // The second review's M1: a task word with a second reading.
                         "yaz tatili için en iyisi neresi", "yazın tatil için en iyisi neresi", "yazlık için en iyisi neresi",
                         "yazıcı için hangisi iyi", "öğrenci için hangisi daha iyi, macbook mu dell mi",
                         "kışlık bot için en iyisi hangisi", "model uçak için en iyisi hangisi",
                         "kahvaltı hazırlamak için en iyisi hangisi", "kan analizi için en iyisi hangisi",
                         "saç düzeltmek için en iyisi hangisi"] {
            XCTAssertNil(CategoryHints.generalSurface(question, within: known), question)
        }
    }

    /// M5: German and Nordic letters, and an English "MI", are no Turkish signal alone.
    func testALetterOtherLanguagesShareIsNoTurkishAlone() {
        for text in ["help me draft a toast for a wedding in Zürich", "plan a weekend in Köln with kids",
                     "a tool to practise German words like Übung and Brötchen", "plan meals for a week in Göteborg",
                     "help me study for the MI board exam",
                     // The second review's M6: a capitalised name or a state code is no Turkish word.
                     "write a cover letter for Kim in Detroit, MI", "plan a road trip from Detroit MI to Omaha NE",
                     "write a short bio of Björk for Kim"] {
            XCTAssertFalse(CategoryHints.readsAsTurkish(text), text)
        }
        for text in ["kod için hangisi", "çeviri için model", "gemini mı daha iyi", "en iyi model hangisi",
                     "claude mu chatgpt mi almanca", "yaşlı bir köpek için oyuncak",
                     // The second review's M2: a particle typed twice is two signals.
                     "phi mi gemma mi", "glm mi minimax mi"] {
            XCTAssertTrue(CategoryHints.readsAsTurkish(text), text)
        }
    }
}


/// The second review's M5: the router carries the served names into the reading.
final class ServedNamesRouteTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    func testTheRouterReadsAServedModelAsASearch() async {
        var router = TieredRouter(model: nil)
        for question in ["when did yi-34b come out", "what is phi-4 good at"] {
            let without = await router.route(question, within: known)
            XCTAssertNotEqual(without.reading, .search, "\(question): no served names")
        }
        router.servedNames = ServedModelNames(displayNames: ["Yi-34B", "Phi-4"])
        for question in ["when did yi-34b come out", "what is phi-4 good at"] {
            let with = await router.route(question, within: known)
            XCTAssertEqual(with.reading, .search, question)
        }
    }
}


/// The second review's M2 (#206, K1): a comparison of any two ranked families is a general question,
/// answered from `everyday` by the route itself.
final class ModelComparisonRouteTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    func testAComparisonOfFamiliesOutsideTheTwelveBrandsIsEveryday() async {
        // The Tester's M4: a comparison of two families with a second reading ("glm", "minimax", "o3") is
        // still a comparison of model names: every word is a name or a particle.
        for question in ["nemotron mu glm mi", "mixtral mi nemotron mu", "glm mi minimax mi", "o3 mü o4 mü"] {
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertEqual(outcome?.categoryID, "everyday", question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }
}
