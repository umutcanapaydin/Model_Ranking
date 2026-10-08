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
                       ["arena", "arena_text_french", "arena_text_german"])
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
}
