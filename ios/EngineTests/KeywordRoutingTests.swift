import XCTest
@testable import ModelRankingEngine

/// D-187 (M20 hotfix): a question that names a surface outright is routed there by the wording tier,
/// in English and in Turkish, before the sentence similarity and whether or not this device has the
/// on-device model or the English embedding. On the owner's TestFlight build, with no Apple
/// Intelligence, "which model writes code best" and every Turkish question were answered "not
/// measured". Every line here is made up for this test or taken from the two hotfix reviews' probes;
/// none is from a live held-out set.
final class KeywordRoutingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality",
                         "text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit"]

    private func routed(_ question: String) async -> RoutingOutcome {
        await TieredRouter(model: nil).route(question, within: known)
    }

    /// Each line reaches its surface through the router, AND on a keyword (the second review's M6: the
    /// tier alone cannot tell a keyword match from an embedding that happens to agree).
    private func assertRoutes(_ lines: [(String, String)], file: StaticString = #filePath, line: UInt = #line) async {
        for (question, surface) in lines {
            XCTAssertEqual(CategoryHints.namedSurface(question, within: known), surface, "keyword: \(question)",
                           file: file, line: line)
            let outcome = await routed(question)
            XCTAssertEqual(outcome.categoryID, surface, question, file: file, line: line)
            XCTAssertFalse(outcome.unmeasured, question, file: file, line: line)
            XCTAssertEqual(outcome.tier, .similarity, "a keyword match is a match on wording: \(question)",
                           file: file, line: line)
        }
    }

    /// Each line names no surface, or another one, but never the one its colliding word would.
    private func assertNotNamed(_ lines: [(String, String)], file: StaticString = #filePath, line: UInt = #line) {
        for (question, wrong) in lines {
            XCTAssertNotEqual(CategoryHints.namedSurface(question, within: known), wrong, question, file: file, line: line)
        }
    }

    func testAQuestionThatNamesASurfaceInEnglishIsRoutedThere() async {
        await assertRoutes([
            ("which model writes code best", "coding"),
            ("best ai for coding", "coding"),
            ("my python script keeps crashing, which model can debug it", "coding"),
            ("which model is best for agentic coding", "agentic-coding"),
            ("best ai coding agent for my repo", "agentic-coding"),
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
        ])
    }

    /// #289, #301 (shipped by D-204 clause 2): quantum physics names `expert`, in English and in
    /// Turkish, before the embedding reads the question's other words (a field theory read as maths).
    /// Made up for this test.
    func testQuantumPhysicsNamesExpert() async {
        await assertRoutes([
            ("explain the quantum hall effect", "expert"),
            ("which model knows quantum mechanics", "expert"),
            ("kuantum tünellemesi nasıl olur", "expert"),
        ])
    }

    /// The second review's B1: the common ways to ask the app's main question about code.
    func testTheCommonWaysToAskAboutCodeAreRead() async {
        await assertRoutes([
            ("which model is best for software engineering", "coding"),
            ("best model for software development", "coding"),
            ("best ai for developers", "coding"),
            ("best ai for a junior developer", "coding"),
            ("which model is best for writing software", "coding"),
            ("which llm is best for app development", "coding"),
            ("which model is best for building an ios app", "coding"),
            ("best model for mobile development", "coding"),
            ("which model is best at swe-bench", "coding"),
            ("best model for leetcode", "coding"),
            ("best model for php", "coding"),
            ("best model for c++", "coding"),
            ("which model knows ruby on rails best", "coding"),
            ("mobil uygulama geliştirmek için en iyi model", "coding"),
            ("uygulama geliştirmek için hangi yapay zeka", "coding"),
            ("c++ için en iyi model", "coding"),
            ("which model is best for next.js", "web-dev"),
        ])
    }

    /// The words people use in a coding question without saying "code": an error's name, a framework,
    /// a query, a test, in both languages.
    func testTheWordsOfAnEverydayCodingQuestionAreRead() async {
        await assertRoutes([
            ("TypeError: undefined is not a function in my express app", "coding"),
            ("my django migration keeps failing", "coding"),
            ("write a postgres query for monthly totals", "coding"),
            ("pandas ile csv okurken UnicodeDecodeError alıyorum", "coding"),
            ("mysql sorgusu yazar mısın", "coding"),
            ("jest ile birim testi nasıl yazılır", "coding"),
            ("merge conflict çıktı ne yapmalıyım", "coding"),
            ("explain how binary search works", "coding"),
            ("does this blog post make up its numbers", "factuality"),
            ("prove that the square root of two is irrational", "mathematics"),
            ("what number comes next in 3 5 9 17", "abstract"),
            ("book a table for me on a restaurant website", "computer-use"),
            ("ekteki makaleyi özetle", "document"),
            ("küçük bir e-ticaret sitesi kurmak istiyorum", "web-dev"),
            ("en son haberleri bulan model", "search"),
        ])
    }

    /// The first review's M2: Turkish typed without its letters names its surface as well.
    func testTurkishTypedWithoutItsLettersIsRead() async {
        await assertRoutes([
            ("yazilim gelistirmek icin en iyi model", "coding"),
            ("tibbi sorular icin model", "expert"),
            ("sozlesme ozetleyen model", "document"),
            ("olasilik sorusu cozen model", "mathematics"),
            ("gorsel okuyan model", "vision"),
        ])
    }

    /// The second review's M2: an AI that operates a computer or a site for the reader is computer use,
    /// read before a site to build.
    func testOperatingASiteForTheReaderIsComputerUse() async {
        await assertRoutes([
            ("which ai can browse websites and buy things for me", "computer-use"),
            ("which model can log into a website and download my invoices", "computer-use"),
            ("which model can fill forms on a website", "computer-use"),
            ("best model for automating tasks in my browser", "computer-use"),
            ("which model can control my computer", "computer-use"),
            ("which model can operate my mac for me", "computer-use"),
        ])
    }

    /// The order tables: which of two surfaces a question names is decided by the rules' order.
    func testTheMoreSpecificSurfaceWins() async {
        await assertRoutes([
            ("search the web for the latest news", "search"),
            ("a coding agent for my codebase", "agentic-coding"),
            ("web development with react", "web-dev"),
            ("write python code to book a meeting room", "coding"),
            ("a coding agent that can use my browser", "agentic-coding"),
            ("which ai can log into my website builder for me", "computer-use"),
            ("build a website for my law firm", "web-dev"),
        ])
    }

    /// #292 (D-206 clause 1): an agent that does a coding action itself (writes or fixes code or tests,
    /// opens a pull request) is agentic coding, however far that action is from the word "agent", as
    /// long as both stand in one sentence. Made up for this test; the golden question is not here.
    func testAnAgentThatDoesTheCodingItselfIsAgenticCoding() async {
        await assertRoutes([
            ("i need an agent that reads the issue, writes the code and asks me nothing", "agentic-coding"),
            ("looking for an agent which picks up my backlog and opens a pr when it is done", "agentic-coding"),
            ("which agent can take a broken build overnight and fix the failing tests", "agentic-coding"),
            ("the agent should read our docs first and then open a pull request", "agentic-coding"),
            ("issue'yu okuyup kodu kendisi yazan bir ajan arıyorum", "agentic-coding"),
            ("hata raporunu alıp testleri düzelten ve pull request açan ajan hangisi", "agentic-coding"),
            ("bir ajan gece boyunca çalışıp testleri kendisi düzeltsin istiyorum", "agentic-coding"),
        ])
    }

    /// #292, the other direction: an agent whose action is not coding stays where it was, an agent in
    /// one sentence does not borrow a coding action from the next, and code written FOR an agent is code.
    func testAnAgentThatDoesNotCodeIsNotAgenticCoding() {
        assertNotNamed([
            ("a travel agent that books my flights and writes the itinerary", "agentic-coding"),
            ("a browser agent that opens my inbox and fills in the forms", "agentic-coding"),
            ("an agent that writes my cover letters and opens my mail", "agentic-coding"),
            ("i want an agent for my holiday plans. separately, write the code for a login page", "agentic-coding"),
            ("write python code for my customer support agent", "agentic-coding"),
            ("e-postalarımı yazan ve toplantılarımı ayarlayan bir ajan", "agentic-coding"),
            ("seyahat ajanı bana bilet açan bir site önerdi", "agentic-coding"),
            ("en iyi ajan filmi hangisi? bu kodu yazan kişiye teşekkür et", "agentic-coding"),
        ])
        XCTAssertEqual(CategoryHints.namedSurface(
            "i want an agent for my holiday plans. separately, write the code for a login page", within: known), "coding")
        XCTAssertEqual(CategoryHints.namedSurface("write python code for my customer support agent", within: known),
                       "coding")
    }

    /// #292, the release Tester's fault G06: the code an agent writes must be code. A zip, promo or
    /// postal code beside the agent's coding verb is none, in English and in Turkish, so the question is
    /// not agentic coding. Made up for this test.
    func testAnAgentWhoseCodeIsAZipOrPromoCodeIsNotAgenticCoding() {
        assertNotNamed([
            ("an agent that fills in my shipping form and writes the zip code", "agentic-coding"),
            ("i want an agent that opens the shop page and writes the promo code in the box", "agentic-coding"),
            ("kargo formunu dolduran ve posta kodunu yazan bir ajan", "agentic-coding"),
        ])
    }

    /// #292, the release Tester's fault G06b: a user agent or a travel agent is no agent that codes, though
    /// a coding verb and its object follow it in the same sentence. Made up for this test.
    func testAnAgentThatIsNoCoderIsNotAgenticCodingThoughACodingVerbFollows() {
        assertNotNamed([
            ("my user agent check keeps failing, can you fix the code", "agentic-coding"),
            ("the travel agent site we built is broken, please fix the tests", "agentic-coding"),
        ])
        XCTAssertEqual(CategoryHints.namedSurface("my user agent check keeps failing, can you fix the code",
                                                  within: known), "coding")
    }

    /// The two reviews' B1, B2 and M1 to M5: an everyday word is not a keyword.
    func testAnEverydayWordIsNotAKeyword() {
        assertNotNamed([
            ("summarise this book", "computer-use"), ("is this book a good read", "computer-use"),
            ("how does the immune system react to a virus", "web-dev"),
            ("how should i react appropriately when my boss yells", "web-dev"),
            ("how to express appreciation to my team", "coding"),
            ("write a script for my youtube video", "coding"), ("the user agent string of my phone", "agentic-coding"),
            ("user agent string parsing in python", "agentic-coding"),
            ("write a python script for my real estate agent", "agentic-coding"),
            ("which model can solve math problems by itself", "agentic-coding"),
            ("can a model learn on its own", "agentic-coding"), ("explain how autonomous cars work", "agentic-coding"),
            ("en iyi ajan filmleri hangileri", "agentic-coding"),
            ("kendi kendine ingilizce öğrenmek için hangi yapay zeka", "agentic-coding"),
            ("make updates to my essay", "factuality"), ("make up a bedtime story for my kid", "factuality"),
            ("which model is best at making up stories", "factuality"),
            ("how do i make up with my friend after a fight", "factuality"),
            ("subscribe to our newsletter", "search"), ("with the exception of mondays", "coding"),
            ("a tv program about space", "coding"), ("the prime minister's speech", "mathematics"),
            ("best coding model right now", "search"), ("is google gemini good for coding", "search"),
            ("bugün matematik için en iyi model", "search"), ("ajandamı düzenle", "agentic-coding"),
            ("bu plan mantıklı mı", "abstract"), ("haftalık çizelge hazırla", "vision"),
            ("şu ana kadar ne yaptık", "search"), ("şunu anlamadım", "search"),
            ("express your feelings in a letter", "coding"), ("how does the liver function", "coding"),
            ("what is the dress code for a wedding", "coding"), ("which ai knows the turkish tax code best", "coding"),
            ("posta kodu nedir", "coding"), ("indirim kodu nasıl kullanılır", "coding"),
            ("i caught a stomach bug", "coding"), ("how many pandas are left in the wild", "coding"),
            ("i have a query about my phone bill", "coding"),
            ("was the moon landing faked", "web-dev"), ("how do i fill in formulas in excel", "computer-use"),
            ("a birthday message for my mother-in-law", "expert"), ("a documentary about whales", "document"),
            ("how do muscles contract", "document"),
            ("yapay zeka soru çözücü öner", "abstract"), ("toplantıya geç kalacağımı haber ver", "search"),
            ("sevgilime romantik bir jest öner", "coding"), ("markete git ve alışveriş listesi yap", "coding"),
            ("site yönetimine dilekçe yaz", "web-dev"), ("arkadaşıma sitem eden bir mesaj yaz", "web-dev"),
            ("bu haftaki toplantılarımı programla", "coding"), ("büyük olasılıkla hangi model daha iyi", "mathematics"),
        ])
        XCTAssertEqual(CategoryHints.namedSurface("summarise this book", within: known), "document")
        XCTAssertEqual(CategoryHints.namedSurface("best coding model right now", within: known), "coding")
        XCTAssertEqual(CategoryHints.namedSurface("bugün matematik için en iyi model", within: known), "mathematics")
        XCTAssertEqual(CategoryHints.namedSurface("user agent string parsing in python", within: known), "coding")
    }

    /// The third review's M1 to M6: a product the reader is choosing is not a thing to build; a code of
    /// conduct, a platform's algorithm, data science, a documentary, an article to write are not what
    /// their stems name; "for me" alone is not operating a computer.
    func testTheThirdReviewsWordsAreReadAsTheyAreMeant() async {
        assertNotNamed([
            ("benim yerime ödev yapan yapay zeka", "computer-use"), ("benim yerime mail yazan yapay zeka", "computer-use"),
            ("how do i operate my new coffee machine", "computer-use"),
            ("best ai software for video editing", "coding"), ("which ai has the best ios app", "coding"),
            ("yapay zeka yazılımı öner", "coding"), ("best ai website for students", "web-dev"),
            ("our code of conduct for the office", "coding"), ("how does the instagram algorithm work", "coding"),
            ("best model for data science", "expert"), ("computer science homework help", "expert"),
            ("fiziksel terapi egzersizleri", "expert"), ("en iyi bilim kurgu filmleri", "expert"),
            ("en iyi belgesel önerisi", "document"), ("bir makale yaz", "document"),
            ("which ai works without internet", "search"),
        ])
        await assertRoutes([("best ai to chat with pdfs", "document"), ("which model can operate my computer", "computer-use")])
        for question in ["chatgpt mi gemini mi daha iyi", "claude mu chatgpt mi"] {
            XCTAssertEqual(CategoryHints.generalSurface(question, within: known), "everyday", question)
        }
    }

    /// The second review's R2: a question about AI models in general names no surface; the embedding
    /// reads it where it can, and `everyday` answers it where it cannot (a Turkish question).
    func testAGeneralQuestionIsTheEmbeddingsOrEverydaysWhereItCannotRead() async {
        for question in ["best llm", "which model is best at reasoning", "en iyi yapay zeka hangisi"] {
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
            XCTAssertEqual(CategoryHints.generalSurface(question, within: known), "everyday", question)
        }
        let turkish = await routed("en iyi yapay zeka hangisi")
        XCTAssertEqual(turkish.categoryID, "everyday")
        XCTAssertFalse(turkish.unmeasured)
    }

    /// #206: a short Turkish question made of model names is not confidently Turkish, so the embedding
    /// would read it as English; it is a general question.
    func testAShortTurkishQuestionMadeOfModelNamesIsAGeneralQuestion() async {
        for question in ["claude mu chatgpt mi", "chatgpt mi gemini mi daha iyi", "gemini mı claude mu hangisi"] {
            XCTAssertTrue(CategoryHints.comparesModelsOnly(question), question)
            let outcome = await routed(question)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
            XCTAssertFalse(outcome.unmeasured, question)
        }
        for question in ["claude vs chatgpt", "is claude good", "claude mu chatgpt mi kod yazar", "hangisi daha iyi",
                         "claude chatgpt"] {
            XCTAssertFalse(CategoryHints.comparesModelsOnly(question), question)
        }
        // The second round's M6: a model's tier name is part of its name.
        for question in ["gemini pro mu chatgpt mi", "gpt 4o mini mi claude haiku mu", "claude sonnet mı gpt mi"] {
            XCTAssertTrue(CategoryHints.comparesModelsOnly(question), question)
            let outcome = await routed(question)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
        }
    }

    /// The W3 Tester's T3 (#206): the outcome is a match on wording, which the reader is shown
    /// (`RoutingTier`). Planted, labelling it the on-device model's stayed green. Where the engine
    /// served no `everyday`, the question is not placed by the embedding: the manual fallback says so.
    func testAQuestionMadeOfModelNamesIsAMatchOnWording() async {
        for question in ["claude mu chatgpt mi", "gemini pro mu chatgpt mi"] {
            let outcome = await routed(question)
            XCTAssertEqual(outcome.categoryID, "everyday", question)
            XCTAssertEqual(outcome.tier, .similarity, question)
            let unserved = await TieredRouter(model: nil).route(question, within: ["coding", "assistant"])
            XCTAssertEqual(unserved.tier, .manual, question)
            XCTAssertTrue(unserved.unmeasured, question)
        }
    }

    /// The first review's M1, D-187 clause 4: the model's "none of these" on a question it read as a
    /// search goes to the wording tier, and a question it read as something else keeps its outcome.
    func testTheModelsDeclineOnASearchGoesToTheWordingTier() async {
        let question = "best ai for coding"
        let declined = await TieredRouter(
            model: ScriptedModelRouter(answers: [question: ["request": "model search",
                                                            "surface": ModelOutputBoundary.declineSentinel]]),
            similarity: SimilarityRouter()
        ).route(question, within: known)
        XCTAssertEqual(declined.categoryID, "coding")
        XCTAssertFalse(declined.unmeasured)
        XCTAssertEqual(declined.tier, .similarity)

        let doubted = await TieredRouter(
            model: ScriptedModelRouter(answers: [question: ["request": "task itself",
                                                            "surface": ModelOutputBoundary.declineSentinel]]),
            similarity: SimilarityRouter()
        ).route(question, within: known)
        XCTAssertEqual(doubted.tier, .model, "a question the model doubts keeps the model's outcome")
    }

    /// #378 (D-218 clause 1, reversing D-187's rule): a request to MAKE an image is answered from the
    /// image board, in both languages; a script that works on images is code, left to the embedding.
    func testARequestToMakeAnImageIsAnsweredFromTheImageBoard() async {
        await assertRoutes([("generate an image of a cat for me", "text_to_image"),
                            ("bana bir kedi resmi çiz", "text_to_image")])
        XCTAssertNotEqual(CategoryHints.namedSurface("write a script that resizes images", within: known), "vision")
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
