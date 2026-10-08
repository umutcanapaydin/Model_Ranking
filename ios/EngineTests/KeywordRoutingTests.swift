import XCTest
@testable import ModelRankingEngine

/// D-187 (M20 hotfix): a question that names a surface outright is routed there by the wording tier,
/// in English and in Turkish, before the sentence similarity and whether or not this device has the
/// on-device model or the English embedding. On the owner's TestFlight build, with no Apple
/// Intelligence, "which model writes code best" and every Turkish question were answered "not
/// measured". Every line here is made up for this test; none is from a held-out set.
final class KeywordRoutingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    private func routed(_ question: String) async -> RoutingOutcome {
        await TieredRouter(model: nil).route(question, within: known)
    }

    private func assertRoutes(_ lines: [(String, String)], file: StaticString = #filePath, line: UInt = #line) async {
        for (question, surface) in lines {
            let outcome = await routed(question)
            XCTAssertEqual(outcome.categoryID, surface, question, file: file, line: line)
            XCTAssertFalse(outcome.unmeasured, question, file: file, line: line)
            XCTAssertEqual(outcome.tier, .similarity, "a keyword match is a match on wording: \(question)",
                           file: file, line: line)
        }
    }

    func testAQuestionThatNamesASurfaceInEnglishIsRoutedThere() async {
        await assertRoutes([
            ("which model writes code best", "coding"),
            ("best ai for coding", "coding"),
            ("my python script keeps crashing, which model can debug it", "coding"),
            ("which model is best for agentic coding", "agentic-coding"),
            ("best ai agent to fix issues in my repo on its own", "agentic-coding"),
            ("best model for math", "mathematics"),
            ("which model is best at reading images", "vision"),
            ("best model for web search", "search"),
            ("find sources online and cite them", "search_factuality"),
            ("build me a website, which ai should i use", "web-dev"),
            ("summarise a long pdf", "document"),
            ("which model is best for medical questions", "expert"),
            ("a model that can drive my browser", "computer-use"),
            ("which model solves logic puzzles", "abstract"),
            ("which model hallucinates the least", "factuality"),
            ("best llm", "everyday"),
        ])
    }

    func testAQuestionThatNamesASurfaceInTurkishIsRoutedThere() async {
        await assertRoutes([
            ("en iyi kodlama modeli hangisi", "coding"),
            ("kod yazmak için en iyi yapay zeka", "coding"),
            ("yazılım geliştirmek için hangi model", "coding"),
            ("kendi başına kod yazan ajan hangisi", "agentic-coding"),
            ("matematik için en iyi model", "mathematics"),
            ("fotoğraftaki yazıyı okuyan model", "vision"),
            ("internette arama yapan en iyi yapay zeka", "search"),
            ("web sitesi yapmak için hangi model", "web-dev"),
            ("uzun bir pdf belgesini özetleyecek model", "document"),
            ("tıbbi sorular için en iyi model", "expert"),
            ("bulmaca çözen model", "abstract"),
            ("en iyi yapay zeka hangisi", "everyday"),
        ])
    }

    /// The words people use in a coding question without saying "code": an error's name, a framework,
    /// a query, a test, in both languages (made up; measured on the tuning and retired sets, D-187).
    func testTheWordsOfAnEverydayCodingQuestionAreRead() async {
        await assertRoutes([
            ("TypeError: undefined is not a function in my express app", "coding"),
            ("my django migration keeps failing", "coding"),
            ("write a postgres query for monthly totals", "coding"),
            ("pandas ile csv okurken UnicodeDecodeError alıyorum", "coding"),
            ("mysql sorgusu yazar mısın", "coding"),
            ("jest ile birim testi nasıl yazılır", "coding"),
            ("merge conflict çıktı ne yapmalıyım", "coding"),
            ("does this blog post make up its numbers", "factuality"),
            ("prove that the square root of two is irrational", "mathematics"),
            ("what number comes next in 3 5 9 17", "abstract"),
            ("book a table for me on a restaurant website", "computer-use"),
            ("ekteki makaleyi özetle", "document"),
            ("küçük bir e-ticaret sitesi kurmak istiyorum", "web-dev"),
            ("en son haberleri bulan model", "search"),
        ])
    }

    /// The hotfix review's M2: Turkish typed without its letters names its surface as well.
    func testTurkishTypedWithoutItsLettersIsRead() async {
        await assertRoutes([
            ("yazilim gelistirmek icin en iyi model", "coding"),
            ("tibbi sorular icin model", "expert"),
            ("sozlesme ozetleyen model", "document"),
            ("olasilik sorusu cozen model", "mathematics"),
            ("gorsel okuyan model", "vision"),
        ])
    }

    /// The hotfix review's B1 and B2: an everyday word is not a keyword. Each line names no surface by
    /// it, or names another; none goes where the colliding word would send it.
    func testAnEverydayWordIsNotAKeyword() {
        let lines: [(String, String)] = [
            ("summarise this book", "computer-use"), ("how does the immune system react to a virus", "web-dev"),
            ("write a script for my youtube video", "coding"), ("the user agent string of my phone", "agentic-coding"),
            ("make updates to my essay", "factuality"), ("subscribe to our newsletter", "search"),
            ("with the exception of mondays", "coding"), ("a tv program about space", "coding"),
            ("the prime minister's speech", "mathematics"), ("best coding model right now", "search"),
            ("implement binary search in python", "search"), ("is google gemini good for coding", "search"),
            ("bugün matematik için en iyi model", "search"), ("ajandamı düzenle", "agentic-coding"),
            ("bu plan mantıklı mı", "abstract"), ("haftalık çizelge hazırla", "vision"),
            ("şu ana kadar ne yaptık", "search"), ("şunu anlamadım", "search"),
            ("express your feelings in a letter", "coding"), ("how does the liver function", "coding"),
        ]
        for (question, wrong) in lines {
            XCTAssertNotEqual(CategoryHints.namedSurface(question, within: known), wrong, question)
        }
        XCTAssertEqual(CategoryHints.namedSurface("summarise this book", within: known), "document")
        XCTAssertEqual(CategoryHints.namedSurface("best coding model right now", within: known), "coding")
        XCTAssertEqual(CategoryHints.namedSurface("bugün matematik için en iyi model", within: known), "mathematics")
    }

    /// The hotfix review's M1, D-187 clause 4: the model's "none of these" on a question it read as a
    /// search goes to the wording tier, and a question it read as something else keeps its outcome.
    func testTheModelsDeclineOnASearchGoesToTheWordingTier() async {
        let question = "best ai for coding"
        let declined = await TieredRouter(
            model: ScriptedModelRouter(answers: [question: ["request": "a model search",
                                                            "surface": ModelOutputBoundary.declineSentinel]]),
            similarity: SimilarityRouter()
        ).route(question, within: known)
        XCTAssertEqual(declined.categoryID, "coding")
        XCTAssertFalse(declined.unmeasured)
        XCTAssertEqual(declined.tier, .similarity)

        let doubted = await TieredRouter(
            model: ScriptedModelRouter(answers: [question: ["request": "something else",
                                                            "surface": ModelOutputBoundary.declineSentinel]]),
            similarity: SimilarityRouter()
        ).route(question, within: known)
        XCTAssertEqual(doubted.tier, .model, "a question the model doubts keeps the model's outcome")
    }

    /// The order the rules are read in is the decision between two surfaces a question names: web
    /// search is `search`, not `web-dev`; an agent that codes is `agentic-coding`, not `coding`.
    func testTheMoreSpecificSurfaceWins() async {
        await assertRoutes([
            ("search the web for the latest news", "search"),
            ("a coding agent for my codebase", "agentic-coding"),
            ("web development with react", "web-dev"),
        ])
    }

    /// D-187: a request to MAKE an image is answered from `vision`, in both languages.
    func testARequestToMakeAnImageIsAnsweredFromVision() async {
        await assertRoutes([("generate an image of a cat for me", "vision"), ("bana bir kedi resmi çiz", "vision")])
    }

    /// A question that names no surface is left to the sentence similarity, as before: no keyword is
    /// a guess.
    func testAQuestionThatNamesNoSurfaceIsLeftToTheSimilarity() {
        for question in ["hi can you help me with something", "what is the tallest mountain in the world",
                         "nasılsın"] {
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
        }
    }

    /// A keyword never routes to a surface the engine did not serve.
    func testAKeywordNeverRoutesToASurfaceTheEngineDidNotServe() {
        XCTAssertNotEqual(CategoryHints.namedSurface("best ai for coding", within: ["assistant", "everyday"]), "coding")
        XCTAssertEqual(CategoryHints.namedSurface("best model for math", within: ["mathematics"]), "mathematics")
    }
}
