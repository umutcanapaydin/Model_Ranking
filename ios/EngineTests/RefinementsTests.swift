//  M17-W5 P1 (#64, D-168) -- the boards a question selects: the surface's primary board, then at
//  most two declared refinements the surface allows, in the declared order.

import XCTest

@testable import ModelRankingEngine

final class RefinementsTests: XCTestCase {
    private func refinement(_ kind: RefinementKind, _ value: String) throws -> Refinement {
        try XCTUnwrap(Refinements.table.first { $0.kind == kind && $0.value == value })
    }

    func testThePrimaryBoardAloneWhenNothingRefinesTheQuestion() {
        XCTAssertEqual(Refinements.boards(primary: "arena", surface: "assistant", chosen: []), ["arena"])
    }

    func testRefinementsFollowThePrimaryInTheDeclaredOrderWhateverOrderTheyCameIn() throws {
        let french = try refinement(.language, "french")
        let legal = try refinement(.domain, "legal")
        let boards = Refinements.boards(primary: "arena", surface: "assistant", chosen: [legal, french])

        XCTAssertEqual(boards, ["arena", french.board, legal.board])
    }

    func testAtMostTwoRefinementsAreAdded() throws {
        let chosen = [try refinement(.language, "french"), try refinement(.domain, "legal"),
                      try refinement(.kind, "multi_turn")]
        let boards = Refinements.boards(primary: "arena", surface: "assistant", chosen: chosen)

        XCTAssertEqual(boards.count, 3)
        XCTAssertFalse(boards.contains(try refinement(.kind, "multi_turn").board))
    }

    func testARefinementTheSurfaceDoesNotAllowIsDropped() throws {
        let ocr = try refinement(.kind, "ocr")
        XCTAssertFalse(ocr.surfaces.contains("assistant"))

        XCTAssertEqual(Refinements.boards(primary: "arena", surface: "assistant", chosen: [ocr]), ["arena"])
    }

    func testABoardAlreadyChosenIsNotChosenTwice() throws {
        let french = try refinement(.language, "french")

        XCTAssertEqual(Refinements.boards(primary: french.board, surface: "assistant", chosen: [french]),
                       [french.board])
    }

    func testWhatASurfaceAllowsIsWhatTheTableSays() {
        let vision = Refinements.allowed(for: "vision")

        XCTAssertFalse(vision.isEmpty)
        XCTAssertTrue(vision.allSatisfy { $0.surfaces.contains("vision") })
        XCTAssertTrue(Refinements.allowed(for: "no-such-surface").isEmpty)
    }
}
