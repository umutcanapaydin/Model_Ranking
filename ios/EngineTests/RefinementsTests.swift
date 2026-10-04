//  M17-W5 P1 (#64, D-168) -- the boards a question selects: the surface's primary board, then at
//  most two declared refinements the surface allows, in the declared order.

import XCTest

@testable import ModelRankingEngine

final class RefinementsTests: OfflineTestCase {
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
        let chosen = [try refinement(.language, "french"), try refinement(.language, "german"),
                      try refinement(.domain, "legal")]
        let boards = Refinements.boards(primary: "arena", surface: "assistant", chosen: chosen)

        XCTAssertEqual(boards.count, 3)
        XCTAssertFalse(boards.contains(try refinement(.domain, "legal").board))
    }

    func testARefinementTheSurfaceDoesNotAllowIsDropped() throws {
        let french = try refinement(.language, "french")
        XCTAssertFalse(french.surfaces.contains("coding"))

        XCTAssertEqual(Refinements.boards(primary: "swebench", surface: "coding", chosen: [french]), ["swebench"])
    }

    func testABoardAlreadyChosenIsNotChosenTwice() throws {
        let french = try refinement(.language, "french")

        XCTAssertEqual(Refinements.boards(primary: french.board, surface: "assistant", chosen: [french]),
                       [french.board])
    }

    func testWhatASurfaceAllowsIsWhatTheTableSays() {
        let assistant = Refinements.allowed(for: "assistant")

        XCTAssertFalse(assistant.isEmpty)
        XCTAssertTrue(assistant.allSatisfy { $0.surfaces.contains("assistant") })
        XCTAssertTrue(Refinements.allowed(for: "no-such-surface").isEmpty)
    }

    func testARefinementIsALanguageOrADomainAndNothingElse() {
        // Owner ruling 2026-09-28 on the probe: the on-device model added a "kind" to most questions
        // it does not describe, so kinds are not refinements (D-168, note of 2026-09-28).
        XCTAssertEqual(RefinementKind.allCases, [.language, .domain])
    }
}
