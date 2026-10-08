//  M20-W4 (#212, REQ-CMB-005, D-188 clause 5): the combined list is the default answer. An engine that
//  names a surface's family (M20-W1) gets the family's own list, combined by D-188 (M20-W2), with the
//  boards the question's refinement adds (M20-W3); a family of one board is today's cards; an engine
//  older than M20 keeps today's plan. A board that weighs half is a small note, never the stale
//  warning over the list (D-188 clause 4).

import XCTest

@testable import ModelRankingEngine

final class FamilyPlanTests: OfflineTestCase {
    private let today = ISO8601DateFormatter().date(from: "2026-10-08T12:00:00Z") ?? Date()

    private func board(_ id: String, _ rows: [(String, Int)], date: String? = "2026-09-20") -> BoardStandings {
        BoardStandings(
            id: id, benchmark: "B \(id)", metric: "elo", rankingEffort: nil, evidenceDate: date,
            observedAt: "2026-10-07", attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "unspecified") }
        )
    }

    private func standings(_ boards: [BoardStandings]) -> Standings {
        let ids = Set(boards.flatMap { $0.standings.map(\.model) }).sorted()
        return Standings(apiVersion: "v1", attributions: [], boards: boards,
                         models: ids.map { StandingModel(id: $0, display: $0, vendor: "V", blendedPerM: 1, accessibility: nil) })
    }

    private func routed(_ surface: String, tier: RoutingTier = .similarity, refinements: [Refinement] = []) -> RoutingOutcome {
        RoutingOutcome(categoryID: surface, tier: tier, unmeasured: false, refinements: refinements)
    }

    private var coding: Standings {
        standings([board("swebench", [("a", 1), ("b", 2)]), board("aider", [("b", 1), ("c", 2)]),
                   board("arena_text_coding", [("a", 1), ("c", 2), ("d", 3)])])
    }

    func testAnEngineThatNamesAFamilyShowsTheFamilysListByDefault() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                              family: ["swebench", "aider", "arena_text_coding"], question: "best model for coding",
                              asOf: today, standings: coding, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["swebench", "aider", "arena_text_coding"])
        XCTAssertEqual(Set(view.list.entries.map(\.model.id)), ["a", "b", "c"], "two of three boards, d on one")
    }

    func testAFamilyOfOneBoardShowsTheCards() {
        let plan = answerPlan(outcome: routed("assistant"), primaryBoard: "arena", family: ["arena"],
                              question: "best chatbot", asOf: today,
                              standings: standings([board("arena", [("a", 1)])]), removed: [])
        XCTAssertEqual(plan, .cards)
    }

    func testAnEngineOlderThanM20KeepsTodaysPlan() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench", standings: coding, removed: [])
        XCTAssertEqual(plan, .cards, "no family named: one board, today's cards")
    }

    /// M20-W3 on screen: with no on-device model, a language word adds its board and offers its chip.
    func testALanguageWordAddsItsBoardWithNoModel() {
        let french = Refinements.table.first { $0.value == "french" }
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("everyday"), primaryBoard: "epoch_eci", family: ["epoch_eci", "arena"],
                              question: "best ai to write in french", asOf: today, standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["epoch_eci", "arena", "arena_text_french"])
        XCTAssertEqual(view.refinements, [french].compactMap { $0 })
    }

    /// D-188 clause 4: an old board weighs half and is a small note; the loud stale warning is not said.
    func testAnOldFamilyBoardIsASmallNoteNotTheLoudWarning() {
        let data = standings([board("swebench", [("a", 1), ("b", 2)], date: "2026-02-26"),
                              board("aider", [("b", 1), ("a", 2)])])
        let stale = SourceHealth(benchmark: "B swebench", stale: true, notice: "old",
                                 sources: [SourceRow(source: "swebench", rows: 2, newestRunDate: "2026-02-26",
                                                     ageDays: 224, stale: true)], reason: nil)
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench", family: ["swebench", "aider"],
                              question: "best model for coding", asOf: today, standings: data, removed: [],
                              primaryHealth: stale)
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertFalse(view.disclosures.contains { if case .staleBoard = $0 { return true }; return false })
        XCTAssertTrue(view.disclosures.contains(.boardsWeighHalf(["B swebench"])))
        let said = view.disclosures.compactMap { combinedDisclosure($0, .english) }
        XCTAssertTrue(said.allSatisfy { $0.weight != .state }, "nothing here is the loud warning")
    }

    func testTheWeighedHalfNoteIsSaidInBothLanguages() {
        let english = combinedDisclosure(.boardsWeighHalf(["SWE-bench Verified"]), .english)
        let turkish = combinedDisclosure(.boardsWeighHalf(["SWE-bench Verified"]), .turkish)
        XCTAssertNotNil(english)
        XCTAssertNotEqual(english?.text, turkish?.text)
        XCTAssertTrue(english?.text.contains("SWE-bench Verified") == true)
    }

    func testTheMemoPlansAgainWhenTheFamilyOrTheQuestionChanges() {
        let memo = PlanMemo()
        var inputs = PlanMemo.Inputs(outcome: routed("coding"), primaryBoard: "swebench", standingsStamp: 1,
                                     removed: [], primaryHealth: nil)
        inputs.family = ["swebench", "aider"]
        inputs.question = "best model for coding"
        inputs.asOf = today
        _ = memo.plan(inputs, standings: coding)
        _ = memo.plan(inputs, standings: coding)
        XCTAssertEqual(memo.computed, 1)
        inputs.question = "best model for coding in french"
        _ = memo.plan(inputs, standings: coding)
        XCTAssertEqual(memo.computed, 2)
    }
}
