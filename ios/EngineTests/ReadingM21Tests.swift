//  M21-W2 (REQ-ASK-005): reading what is not a search, again. A comparison of any ranked families' names is
//  a general question (#206); the probe harnesses' rows are rebuilt by code a test runs (#193); a Turkish
//  ask with no surface word stays as it was. #194's model names in the fact doubt and #218's Turkish
//  signals before the embedding were taken out after three verdicts (D-191); their tests went with them.

import XCTest

@testable import ModelRankingEngine

/// #206 (M21-W2): the words a comparison of model names reads are the registry's. (#194's use of them in
/// the fact doubt was taken out after three verdicts, D-191.)
final class ModelNameSearchTests: OfflineTestCase {
    /// #206: the family words are the registry's, not a hand-kept list.
    func testTheFamilyWordsAreTheRegistrys() {
        XCTAssertTrue(ModelFamilies.words.isSuperset(of: ["qwen", "kimi", "mixtral", "o3", "claude", "gpt", "gemini"]))
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

/// The first M21-W2 review's K1 (#206, D-191): a comparison of model names reads every ranked family.
final class ModelNameReviewTests: OfflineTestCase {
    /// K1: a question made only of model names reads every family the registry names.
    func testAComparisonOfAnyRankedFamiliesIsAGeneralQuestion() {
        for question in ["mixtral mi qwen mi", "nemotron mu claude mu"] {
            XCTAssertTrue(CategoryHints.comparesModelsOnly(question), question)
        }
        XCTAssertFalse(CategoryHints.comparesModelsOnly("kimi mi geldi"), "\"geldi\" is no name and no particle")
    }
}

/// The M21-W2 reviews' M1 and M4 (D-191): an ask for "the best one" that names no surface is no general
/// question (#222's general ask was taken out).
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

}

/// The second review's M2 (#206, K1): a comparison of any two ranked families is a general question,
/// answered from `everyday` by the route itself.
final class ModelComparisonRouteTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    func testAComparisonOfFamiliesOutsideTheTwelveBrandsIsEveryday() async {
        // The Tester's M4: a comparison of two families with a second reading ("glm", "minimax") is still a
        // comparison of model names: every word is a name or a particle. ("o3 mü o4 mü" is not read here:
        // the words the router reads hold letters only, so "o3" is "o"; it reaches the embedding, #218.)
        for question in ["nemotron mu glm mi", "mixtral mi nemotron mu", "glm mi minimax mi"] {
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertEqual(outcome?.categoryID, "everyday", question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }
}
