//  M20-W3 (#211, REQ-CMB-004, D-188): the question picks its family. The surface it routes to brings
//  every board of its family (`/v1/categories`' `boards`, M20-W1), and a refinement adds its slice,
//  at most two (D-168). With no on-device model, the words of a language or a domain choose the
//  refinement the model would have. The question never leaves the phone: these are local reads.

import XCTest

@testable import ModelRankingEngine

final class QuestionFamilyTests: OfflineTestCase {
    private func values(_ refinements: [Refinement]) -> [String] { refinements.map(\.value) }

    func testTheFamilyComesFirstThenTheRefinements() {
        let family = ["epoch_eci", "arena", "arena_text_hard_prompts"]
        let french = Refinements.table.filter { $0.value == "french" }
        XCTAssertEqual(Refinements.familyBoards(family: family, surface: "everyday", chosen: french),
                       family + ["arena_text_french"])
        XCTAssertEqual(Refinements.familyBoards(family: family, surface: "everyday", chosen: []), family)
    }

    func testARefinementTheSurfaceDoesNotAllowAddsNothing() {
        let family = ["swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"]
        let software = Refinements.table.filter { $0.value == "software" }
        XCTAssertEqual(Refinements.familyBoards(family: family, surface: "coding", chosen: software), family,
                       "Ruling A: coding takes no refinement")
    }

    func testAtMostTwoRefinementsAndNoneTwice() {
        let family = ["arena"]
        let chosen = Refinements.table.filter { ["french", "legal", "medicine"].contains($0.value) }
        let boards = Refinements.familyBoards(family: family, surface: "assistant", chosen: chosen)
        XCTAssertEqual(boards.count, 3)
        XCTAssertEqual(Refinements.familyBoards(family: ["arena", "arena_text_french"], surface: "assistant",
                                                chosen: Refinements.table.filter { $0.value == "french" }),
                       ["arena", "arena_text_french"])
    }

    /// With no on-device model, a language the TASK concerns, or a domain, is read from the words.
    func testTheWordsOfALanguageOrADomainChooseTheRefinement() {
        XCTAssertEqual(values(Refinements.read("best ai to answer in french")), ["french"])
        XCTAssertEqual(values(Refinements.read("almanca yazışma için en iyi yapay zeka")), ["german"])
        XCTAssertEqual(values(Refinements.read("ispanyolca ceviri icin model")), ["spanish"])
        XCTAssertEqual(values(Refinements.read("which ai is best for legal questions")), ["legal"])
        XCTAssertEqual(values(Refinements.read("tıbbi sorular için en iyi yapay zeka")), ["medicine"])
        XCTAssertEqual(values(Refinements.read("best ai for french legal contracts")), ["french", "legal"])
    }

    /// A word with a second reading is not a refinement: polishing a photo is not Polish.
    func testAWordWithASecondReadingIsNoRefinement() {
        XCTAssertEqual(values(Refinements.read("best ai for polishing my photos")), [])
        XCTAssertEqual(values(Refinements.read("polish my essay")), [])
        XCTAssertEqual(values(Refinements.read("translate this into polish")), ["polish"])
        XCTAssertEqual(values(Refinements.read("what is the best ai")), [])
        XCTAssertEqual(values(Refinements.read("is it good for coding")), [], "\"is\" is not the Turkish \"iş\"")
    }
}
