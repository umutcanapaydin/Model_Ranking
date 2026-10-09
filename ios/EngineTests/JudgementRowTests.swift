//  #226 (M21-W2): the judgement sheet's rows are what the screen shows, beside the primary board's own
//  order, so the owner's judgement reads D-188's list as the reader sees it.

import Foundation
import XCTest

@testable import ModelRankingEngine

final class JudgementRowTests: OfflineTestCase {
    private func board(_ id: String, _ rows: [(String, Int)]) -> BoardStandings {
        BoardStandings(id: id, benchmark: "B \(id)", metric: "elo", rankingEffort: nil, evidenceDate: "2026-10-01",
                       observedAt: "2026-10-07", attribution: "x",
                       standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "unspecified") })
    }

    private func standings(_ boards: [BoardStandings]) -> Standings {
        let ids = Set(boards.flatMap { $0.standings.map(\.model) }).sorted()
        return Standings(apiVersion: "v1", attributions: [], boards: boards,
                         models: ids.map { StandingModel(id: $0, display: $0.uppercased(), vendor: "V", blendedPerM: 1,
                                                         accessibility: nil) })
    }

    private func categories() throws -> [ModelRankingEngine.Category] {
        let payload = Data(#"""
        {"categories": [{"id": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified",
          "metric": "% resolved", "ranking_effort": null, "primary_board": "swebench",
          "boards": ["swebench", "aider"], "refined_board": null}]}
        """#.utf8)
        return try JSONDecoder().decode(CategoryList.self, from: payload).categories
    }

    func testARowIsTheFamilyListBesideThePrimaryBoardsOwnOrder() throws {
        let data = standings([board("swebench", [("a", 1), ("b", 2), ("c", 3)]), board("aider", [("c", 1), ("b", 2), ("a", 3)])])
        let row = JudgementRows.row(question: "best model for coding",
                                    outcome: RoutingOutcome(categoryID: "coding", tier: .similarity, unmeasured: false),
                                    categories: try categories(), standings: data, asOf: Date())
        XCTAssertEqual(row["q"] as? String, "best model for coding")
        XCTAssertEqual(row["surface"] as? String, "coding")
        XCTAssertEqual(row["primary"] as? [String], ["A", "B", "C"])
        XCTAssertEqual(Set(row["family"] as? [String] ?? []), ["A", "B", "C"])
        XCTAssertEqual(row["boards"] as? [String], ["swebench", "aider"])
    }

    func testAQuestionWithNoFamilyListSaysSo() throws {
        let data = standings([board("swebench", [("a", 1)])])
        let row = JudgementRows.row(question: "asdf", outcome: RoutingOutcome(categoryID: "coding", tier: .manual,
                                                                              unmeasured: true),
                                    categories: try categories(), standings: data, asOf: Date())
        XCTAssertEqual(row["family"] as? [String], [])
        XCTAssertEqual(row["primary"] as? [String], ["A"])
    }

    /// The M21-W2 review's M7: the primary board is read in its position order and both lists are cut at
    /// five, whatever order the payload sends.
    func testBothListsAreInPlaceOrderAndCutAtFive() throws {
        let order = [("f", 6), ("a", 1), ("e", 5), ("b", 2), ("d", 4), ("c", 3)]
        let data = standings([board("swebench", order), board("aider", order)])
        let row = JudgementRows.row(question: "best model for coding",
                                    outcome: RoutingOutcome(categoryID: "coding", tier: .similarity, unmeasured: false),
                                    categories: try categories(), standings: data, asOf: Date())
        XCTAssertEqual(row["primary"] as? [String], ["A", "B", "C", "D", "E"])
        XCTAssertEqual(row["family"] as? [String], ["A", "B", "C", "D", "E"])
    }
}
