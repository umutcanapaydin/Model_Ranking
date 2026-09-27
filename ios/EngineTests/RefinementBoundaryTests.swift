//  M17-W5 P2 (#64, D-168 clause 2) -- the on-device model's refinements pass the same boundary as
//  its surface: a value the table does not declare, or one the chosen surface does not allow, is
//  dropped and never acted on. Tested without the model, on every machine, as the surface is.

import XCTest

@testable import ModelRankingEngine

final class RefinementBoundaryTests: XCTestCase {
    private let served = ["coding", "assistant", "vision", "mathematics"]

    private func values(_ outcome: RoutingOutcome?) -> [String] {
        (outcome?.refinements ?? []).map(\.value)
    }

    func testDeclaredValuesTheSurfaceAllowsAreKept() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "french", .domain: "legal"])

        XCTAssertEqual(outcome?.categoryID, "assistant")
        XCTAssertEqual(values(outcome), ["french", "legal"])
    }

    func testAValueTheTableDoesNotDeclareIsDropped() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "klingon", .domain: "legal"])

        XCTAssertEqual(values(outcome), ["legal"], "an undeclared language was acted on")
    }

    func testAValueOfAnotherKindIsDropped() {
        // `legal` is a domain; emitted as a language it names nothing.
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "legal"])

        XCTAssertEqual(values(outcome), [])
    }

    func testAValueTheSurfaceDoesNotAllowIsDropped() {
        // A language refines the chat surfaces, not coding.
        let outcome = ModelOutputBoundary.outcome(
            for: "coding", within: served, refinements: [.language: "french"])

        XCTAssertEqual(outcome?.categoryID, "coding")
        XCTAssertEqual(values(outcome), [])
    }

    func testNoneAddsNothing() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served,
            refinements: [.language: ModelOutputBoundary.noRefinement, .domain: "legal"])

        XCTAssertEqual(values(outcome), ["legal"])
    }

    func testADeclinedQuestionCarriesNoRefinement() {
        let outcome = ModelOutputBoundary.outcome(
            for: ModelOutputBoundary.declineSentinel, within: served, refinements: [.language: "french"])

        XCTAssertEqual(outcome?.unmeasured, true)
        XCTAssertEqual(values(outcome), [])
    }

    func testARefusedSurfaceIsRefusedWhateverTheRefinements() {
        XCTAssertNil(ModelOutputBoundary.outcome(
            for: "sql-tuning", within: served, refinements: [.language: "french"]))
    }

    func testTheSchemaOffersEachKindsDeclaredValuesAndTheWayOut() {
        for kind in RefinementKind.allCases {
            let choices = ModelOutputBoundary.refinementChoices(for: kind)
            let declared = Refinements.table.filter { $0.kind == kind }.map(\.value)

            XCTAssertEqual(Set(choices), Set(declared + [ModelOutputBoundary.noRefinement]), "\(kind)")
            XCTAssertFalse(choices.contains(ModelOutputBoundary.declineSentinel))
        }
    }

    func testTheWayOutIsNotAValueAnyRefinementUses() {
        XCTAssertFalse(Refinements.table.contains { $0.value == ModelOutputBoundary.noRefinement })
    }

    func testTheWordingTierNeverRefines() async {
        let outcome = await SimilarityRouter().route(
            "I want to write a contract in French for a legal case", within: served)

        XCTAssertEqual(outcome?.refinements ?? [], [])
    }

    func testTheOutcomeNamesTheBoardsItSelects() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.domain: "legal", .language: "french"])
        let boards = outcome.map { Refinements.boards(primary: "arena", surface: $0.categoryID, chosen: $0.refinements) }

        XCTAssertEqual(boards, ["arena", "arena_text_french", "arena_text_industry_legal_and_government"])
    }
}
