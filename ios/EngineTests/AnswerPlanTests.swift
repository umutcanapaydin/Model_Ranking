//  M17-W5 P3 (#64, D-168 clause 7) -- what the screen shows for a routed question: today's cards
//  when one board is chosen, the product's combined list when more than one is.

import XCTest

@testable import ModelRankingEngine

final class AnswerPlanTests: XCTestCase {
    private func board(_ id: String, _ rows: [(String, Int)]) -> BoardStandings {
        BoardStandings(
            id: id, benchmark: "B \(id)", metric: "elo", rankingEffort: nil, evidenceDate: "2026-09-18",
            observedAt: "2026-09-25", attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "unspecified") }
        )
    }

    private func refinement(_ kind: RefinementKind, _ value: String) -> Refinement {
        Refinements.table.first { $0.kind == kind && $0.value == value }!
    }

    private var french: Refinement { refinement(.language, "french") }
    private var legal: Refinement { refinement(.domain, "legal") }

    private var data: Standings {
        let boards = [board("arena", [("a", 1), ("b", 2), ("c", 3)]),
                      board(french.board, [("b", 1), ("a", 2)]),
                      board(legal.board, [("a", 1), ("b", 2), ("c", 3)])]
        return Standings(apiVersion: "v1", attributions: [], boards: boards,
                         models: ["a", "b", "c"].map { StandingModel(id: $0, display: $0, vendor: "V",
                                                                    blendedPerM: 1, accessibility: nil) })
    }

    private func routed(_ refinements: [Refinement], unmeasured: Bool = false) -> RoutingOutcome {
        RoutingOutcome(categoryID: "assistant", tier: .model, unmeasured: unmeasured, refinements: refinements)
    }

    func testNoQuestionShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: nil, primaryBoard: "arena", standings: data, removed: []), .cards)
    }

    func testOneBoardShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([]), primaryBoard: "arena", standings: data, removed: []), .cards)
    }

    func testSeveralBoardsShowTheCombinedList() throws {
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", french.board])
        XCTAssertEqual(view.list.entries.map(\.model.id), ["a", "b"])
        XCTAssertEqual(view.sharedCount, 2, "the shared count is what the detail screen states (#54)")
        XCTAssertEqual(view.refinements, [french])
    }

    func testAnUnmeasuredQuestionShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french], unmeasured: true), primaryBoard: "arena",
                                  standings: data, removed: []), .cards)
    }

    func testAnEngineThatNamesNoPrimaryBoardShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: nil, standings: data, removed: []), .cards)
    }

    func testStandingsNotYetKeptShowTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: nil, removed: []), .cards)
    }

    func testARefinementTheReaderRemovedIsNotCombined() {
        let plan = answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: data,
                              removed: [french])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", legal.board])
        XCTAssertEqual(view.refinements, [french, legal], "a removed refinement stays on screen to restore")
        XCTAssertEqual(view.removed, [french])
    }

    func testRemovingEveryRefinementReturnsToTheCardsAndKeepsThemToRestore() {
        // Found on the simulator: removing the only refinement took its chip away with the list,
        // so it could not be put back without asking again.
        XCTAssertEqual(answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: data,
                                  removed: [french, legal]), .restorable([french, legal]))
    }

    func testARefinementWhoseBoardTheStandingsLackIsNotOfferedToRestore() {
        let missing = Standings(apiVersion: "v1", attributions: [], boards: [data.boards[0], data.boards[2]],
                                models: data.models)
        XCTAssertEqual(answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: missing,
                                  removed: [legal]), .restorable([legal]))
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: missing,
                                  removed: [french]), .cards)
    }

    func testNothingIsOfferedToRestoreWhenRestoringCouldNotCombine() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "nowhere", standings: data,
                                  removed: [french]), .cards)
        XCTAssertEqual(answerPlan(outcome: routed([french], unmeasured: true), primaryBoard: "arena",
                                  standings: data, removed: [french]), .cards)
    }

    func testABoardTheStandingsLackIsLeftOutNotFailed() {
        let missing = Standings(apiVersion: "v1", attributions: [], boards: [data.boards[0], data.boards[2]],
                                models: data.models)
        let plan = answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: missing, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", legal.board])
        XCTAssertEqual(view.refinements, [legal], "a chip for a board not counted would say it was")
    }

    func testAPrimaryBoardTheStandingsLackShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "nowhere", standings: data,
                                  removed: []), .cards)
    }

    func testBoardsThatShareNoModelStillShowTheCombinedListEmpty() {
        // D-167 clause 3 exactly (#54): nothing is guessed, so an empty list is said, not filled.
        let apart = Standings(apiVersion: "v1", attributions: [],
                              boards: [board("arena", [("a", 1)]), board(french.board, [("b", 1)])],
                              models: data.models)
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: apart, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.sharedCount, 0)
    }

    // MARK: - What the combined list discloses (review B1, M4; D-112)

    private func boardAt(_ id: String, _ rows: [(String, Int, String)], rankingEffort: String? = nil,
                         evidenceDate: String? = "2026-09-18", observedAt: String? = "2026-09-25",
                         benchmark: String? = nil) -> BoardStandings {
        BoardStandings(
            id: id, benchmark: benchmark ?? "B \(id)", metric: "elo", rankingEffort: rankingEffort,
            evidenceDate: evidenceDate, observedAt: observedAt, attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: $0.2) }
        )
    }

    private func held(_ boards: [BoardStandings]) -> Standings {
        Standings(apiVersion: "v1", attributions: [], boards: boards, models: data.models)
    }

    func testTheCombinedListSaysWhichEffortsItsModelsStandAt() {
        // The cards disclose an unequal comparison (D-112); the list that replaces them must too.
        let mixed = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "unspecified"), ("c", 3, "max")]),
                          boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: mixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.mixedEfforts, [BoardEfforts(board: "arena", efforts: ["high", "unspecified"])],
                       "only the listed models' efforts count: c, at max, is not in the list")
        XCTAssertEqual(view.efforts, ["high", "unspecified"])
    }

    func testEveryEffortIsNamedOnceInTheBoardsOwnOrder() {
        let mixed = held([boardAt("arena", [("a", 1, "unspecified"), ("b", 2, "high")]),
                          boardAt(french.board, [("b", 1, "max"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: mixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.efforts, ["unspecified", "high", "max"])
    }

    func testABoardRankedAtOneEffortIsNeverAMix() {
        let fixed = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "medium")], rankingEffort: "high"),
                          boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: fixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.mixedEfforts, [], "a surface that ranks at one named effort compares at it")
    }

    func testTheEffortNoteNamesEveryEffortInBothLanguages() {
        for language in Language.allCases {
            let note = UIText.combinedEffortNote(efforts: ["high", "unspecified"], language)
            XCTAssertTrue(note.contains("high") && note.contains("unspecified"), "\(language): \(note)")
        }
    }

    func testABoardThatPublishesNoEvaluationDateIsDatedByTheDayItWasRead() {
        // `observed_at` is when the engine read the board, not when anything was measured.
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: "2026-09-18")), .measured("2026-09-18"))
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: nil)), .readOn("2026-09-25"))
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: nil, observedAt: nil)), .unknown)
        XCTAssertNotEqual(UIText.boardDate(.readOn("2026-09-25"), .english),
                          UIText.boardDate(.measured("2026-09-25"), .english))
        XCTAssertTrue(UIText.boardDate(.readOn("2026-09-25"), .turkish).contains("2026-09-25"))
    }

    func testEveryRefinementHasANameInBothLanguages() {
        for refinement in Refinements.table {
            for language in Language.allCases {
                XCTAssertFalse(UIText.refinementName(refinement, language).isEmpty, "\(refinement.value) \(language)")
            }
            XCTAssertNotEqual(UIText.refinementName(refinement, .turkish), refinement.value,
                              "\(refinement.value) has no Turkish name")
        }
    }
}
