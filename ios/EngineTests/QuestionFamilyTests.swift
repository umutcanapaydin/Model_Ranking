//  M20-W3 (#211, REQ-CMB-004, D-188): the question picks its family. The surface it routes to brings
//  every board of its family (`/v1/categories`' `boards`, M20-W1), and a refinement adds its slice,
//  at most two (D-168). With no on-device model, the words of a language or a domain choose the
//  refinement the model would have. The question never leaves the phone: these are local reads.

import XCTest

@testable import ModelRankingEngine

final class QuestionFamilyTests: OfflineTestCase {
    private func values(_ refinements: [Refinement]) -> [String] { refinements.map(\.value) }

    private func refinements(_ values: [String]) -> [Refinement] {
        values.compactMap { value in Refinements.table.first { $0.value == value } }
    }

    func testTheFamilyComesFirstThenTheRefinements() {
        let family = ["epoch_eci", "arena", "arena_text_hard_prompts"]
        XCTAssertEqual(Refinements.familyBoards(primary: "epoch_eci", family: family, surface: "everyday",
                                                chosen: refinements(["french"])),
                       family + ["arena_text_french"])
        XCTAssertEqual(Refinements.familyBoards(primary: "epoch_eci", family: family, surface: "everyday", chosen: []),
                       family)
    }

    func testARefinementTheSurfaceDoesNotAllowAddsNothing() {
        let family = ["swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"]
        XCTAssertEqual(Refinements.familyBoards(primary: "swebench", family: family, surface: "coding",
                                                chosen: refinements(["software"])),
                       family, "Ruling A: coding takes no refinement")
    }

    func testAtMostTwoRefinementsAndNoneTwice() {
        let boards = Refinements.familyBoards(primary: "arena", family: ["arena"], surface: "assistant",
                                              chosen: refinements(["french", "legal", "medicine"]))
        XCTAssertEqual(boards, ["arena", "arena_text_french", "arena_text_industry_legal_and_government"])
        XCTAssertEqual(Refinements.familyBoards(primary: "arena", family: ["arena", "arena_text_french"],
                                                surface: "assistant", chosen: refinements(["french"])),
                       ["arena", "arena_text_french"])
    }

    /// The W3 review's M4: languages come before domains whatever order they were chosen in.
    func testLanguagesComeBeforeDomainsWhateverOrderTheyAreChosenIn() {
        XCTAssertEqual(Refinements.familyBoards(primary: "arena", family: ["arena"], surface: "assistant",
                                                chosen: refinements(["legal", "medicine", "french", "german"])),
                       ["arena", "arena_text_french", "arena_text_german"])
    }

    /// The W3 review's M4: a refinement the family already holds takes none of the two places.
    func testARefinementAlreadyInTheFamilyLeavesRoomForTwoMore() {
        XCTAssertEqual(Refinements.familyBoards(primary: "arena", family: ["arena", "arena_text_french"],
                                                surface: "assistant",
                                                chosen: refinements(["french", "german", "legal"])),
                       ["arena", "arena_text_french", "arena_text_german",
                        "arena_text_industry_legal_and_government"])
    }

    /// The W3 review's M4: a board the family names twice counts once.
    func testABoardTheFamilyNamesTwiceCountsOnce() {
        XCTAssertEqual(Refinements.familyBoards(primary: "epoch_eci", family: ["epoch_eci", "arena", "arena"],
                                                surface: "everyday", chosen: []),
                       ["epoch_eci", "arena"])
    }

    /// The W3 review's M5: an engine older than M20 sends no family, and the primary board still leads.
    func testAnEngineWithNoFamilyLeavesThePrimaryBoardFirst() {
        XCTAssertEqual(Refinements.familyBoards(primary: "arena", family: [], surface: "assistant",
                                                chosen: refinements(["german", "french"])),
                       ["arena", "arena_text_german", "arena_text_french"], "within a kind, the order chosen")
        XCTAssertEqual(Refinements.boards(primary: "arena", surface: "assistant", chosen: refinements(["legal"])),
                       ["arena", "arena_text_industry_legal_and_government"])
    }

    /// With no on-device model, a language the TASK concerns, or a domain, is read from the words.
    func testTheWordsOfALanguageOrADomainChooseTheRefinement() {
        XCTAssertEqual(values(Refinements.read("best ai to answer in french")), ["french"])
        XCTAssertEqual(values(Refinements.read("almanca yazışma için en iyi yapay zeka")), ["german"])
        XCTAssertEqual(values(Refinements.read("ispanyolca ceviri icin model")), ["spanish"])
        XCTAssertEqual(values(Refinements.read("which ai is best for legal questions")), ["legal"])
        XCTAssertEqual(values(Refinements.read("tıbbi sorular için en iyi yapay zeka")), ["medicine"])
        XCTAssertEqual(values(Refinements.read("best ai for legal contracts in french")), ["french", "legal"])
        XCTAssertEqual(values(Refinements.read("translate this into german")), ["german"])
        XCTAssertEqual(values(Refinements.read("japanese language practice")), ["japanese"])
        XCTAssertEqual(values(Refinements.read("translate from korean to english")), ["korean"])
        XCTAssertEqual(values(Refinements.read("learn spanish with ai")), ["spanish"])
        XCTAssertEqual(values(Refinements.read("doktor randevusu için yapay zeka")), ["medicine"])
    }

    /// A word with a second reading is not a refinement: polishing a photo is not Polish.
    func testAWordWithASecondReadingIsNoRefinement() {
        XCTAssertEqual(values(Refinements.read("best ai for polishing my photos")), [])
        XCTAssertEqual(values(Refinements.read("polish my essay")), ["writing"], "an essay is writing; polishing is no language")
        XCTAssertEqual(values(Refinements.read("translate this into polish")), ["polish"])
        XCTAssertEqual(values(Refinements.read("what is the best ai")), [])
        XCTAssertEqual(values(Refinements.read("is it good for coding")), [], "\"is\" is not the Turkish \"iş\"")
    }

    /// The W3 review's M1: an English language name is also a nationality or a country's, so it names
    /// the task's language only beside a word that says so.
    func testALanguageNameIsReadOnlyAsTheTasksLanguage() {
        for question in ["french fries recipe", "german shepherd training tips", "history of the korean war",
                         "chinese economy news", "spanish flu pandemic", "russian roulette rules",
                         "mandarin orange cake", "write in Turkish about German cars"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
    }

    /// The W3 review's second round, M1: "in" before a nationality, or a speaker, is no language.
    func testANationalityAfterInIsNoLanguage() {
        for question in ["best ai for investing in chinese stocks", "what is trending in korean dramas",
                         "recipes in french cuisine", "trends in german politics", "news in japanese markets",
                         "invest in japanese yen", "in russian history class", "best chinese speaker brand",
                         "japanese speaker for my car", "learn chinese cooking"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
        XCTAssertEqual(values(Refinements.read("reply in german please")), ["german"])
        XCTAssertEqual(values(Refinements.read("answer in french and spanish")), ["french"], "one language, the first named")
    }

    /// The second round's M2: the words choose at most one language and one domain, as the model's
    /// schema does, each the first the question names.
    func testTheWordsChooseOneOfEachKindTheFirstNamed() {
        XCTAssertEqual(values(Refinements.read("translate legal contracts from german to french")), ["german", "legal"])
        XCTAssertEqual(values(Refinements.read("translate from korean to japanese")), ["korean"])
        XCTAssertEqual(values(Refinements.read("medical and legal questions")), ["medicine"])
    }

    /// The second round's M5: each context word is held.
    func testEachContextWordThatMakesALanguageIsHeld() {
        XCTAssertEqual(values(Refinements.read("i want to speak japanese")), ["japanese"])
        XCTAssertEqual(values(Refinements.read("speaking russian with ai")), ["russian"])
        XCTAssertEqual(values(Refinements.read("korean translation app")), ["korean"])
        XCTAssertEqual(values(Refinements.read("a spanish translator")), ["spanish"])
        XCTAssertEqual(values(Refinements.read("translate from korean")), ["korean"])
        XCTAssertEqual(values(Refinements.read("switching from german cars to japanese ones")), [],
                       "to and from count only in a question that asks to translate")
        XCTAssertEqual(values(Refinements.read("writing tests for my api")), [])
        XCTAssertEqual(values(Refinements.read("writing sql queries")), [])
        XCTAssertEqual(values(Refinements.read("data scientific notebooks")), [])
    }

    /// The second round's M4: Turkish and English words with a second meaning.
    func testMoreWordsWithASecondMeaningAreNoDomain() {
        for question in ["kullanıcı hikayesi yaz", "sunucu işletmek", "doctor who episodes"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
        XCTAssertEqual(values(Refinements.read("işletme ödevim için yapay zeka")), ["business"])
    }

    /// The W3 Tester's M1 and M2: an AI's software is no software domain, and the Turkish word for
    /// health before "check" or "status" is a machine's, not medicine.
    func testAnAIsSoftwareAndAMachinesHealthAreNoDomain() {
        XCTAssertEqual(values(Refinements.read("best ai software for writing essays")), ["writing"])
        XCTAssertEqual(values(Refinements.read("hangi yapay zeka yazılımı daha iyi")), [])
        XCTAssertEqual(values(Refinements.read("chatbot software for my shop")), [])
        for question in ["kubernetes sağlık kontrolü betiği", "sunucu sağlık durumu", "pil sağlık durumu"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
        XCTAssertEqual(values(Refinements.read("sağlık sorularım için yapay zeka")), ["medicine"])
        XCTAssertEqual(values(Refinements.read("software architecture questions")), ["software"])
    }

    /// The W3 review's M2: the Turkish word for Polish is also the word for a dialect.
    func testTheTurkishWordForADialectIsNoPolish() {
        for question in ["karadeniz lehçesi ile yaz", "bu lehçeyi anlayan yapay zeka"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
    }

    /// The W3 review's M3: a domain word with a second meaning, or beside a word that makes it
    /// something else, adds nothing.
    func testADomainWordWithASecondMeaningIsNoDomain() {
        for question in ["write a science fiction story", "doktora tezi yazımı", "which ai explains moore's law",
                         "law of large numbers explained", "my sister in law wants a recipe",
                         "my mother-in-law wants a recipe", "kubernetes health check script",
                         "battery health of my phone", "write user stories for my sprint",
                         "a novel approach to sorting", "best ai for writing code", "thin film solar cells",
                         "fizik tedavi egzersizleri", "fiziksel terapi egzersizleri", "best model for data science",
                         "computer science homework help", "veri bilimi için yapay zeka", "sağlıklı yemek tarifi"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
        XCTAssertEqual(values(Refinements.read("bilimkurgu hikayesi yaz")), ["writing"], "a story is writing; science fiction is no science")
        XCTAssertEqual(values(Refinements.read("en iyi bilim kurgu romanları")), [])
        XCTAssertEqual(values(Refinements.read("physics homework help")), ["science"])
        XCTAssertEqual(values(Refinements.read("fizik ödevime yardım et")), ["science"])
    }

    /// The W3 Tester's T1 (REQ-CMB-004, D-188 clause 6): "to" makes a language in a question that asks
    /// to translate, and neither "to" nor "from" does in one that does not. Planted, "to" dropped and
    /// the translation condition dropped each stayed green: since the second round's `languageEnds`,
    /// "switching from german cars to japanese ones" reads nothing either way, as "cars" and "ones"
    /// end no language.
    func testToOrFromMakesALanguageOnlyInAQuestionThatAsksToTranslate() {
        XCTAssertEqual(values(Refinements.read("translate this paragraph to french")), ["french"])
        XCTAssertEqual(values(Refinements.read("translate to japanese please")), ["japanese"])
        for question in ["upgrading from german to japanese cars", "moving from korean to chinese food"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
    }

    /// The W3 Tester's T1 (REQ-CMB-004, D-188 clause 6): the context words and guards no test held.
    /// Planted, each of these stayed green: "learning" dropped, the "bilgisayar" ("computer") guard on
    /// "bilim" ("science") dropped, and the writing guards on "codes", "scripts", "queries" and
    /// "functions" dropped.
    func testTheRemainingContextWordsAndGuardsAreHeld() {
        XCTAssertEqual(values(Refinements.read("learning japanese with ai")), ["japanese"])
        XCTAssertEqual(values(Refinements.read("chinese translations of poems")), ["chinese", "writing"])
        for question in ["bilgisayar bilimi ödevi", "writing codes", "writing scripts for my app",
                         "writing queries for postgres", "writing functions in python"] {
            XCTAssertEqual(values(Refinements.read(question)), [], question)
        }
    }
}
