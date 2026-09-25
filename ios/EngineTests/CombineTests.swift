//  M17-W4 (D-160 clause 2, D-167 clause 3) -- the phone combines chosen boards by POSITION.
//
//  Only models every chosen board ranks are combined. On each board they are re-ranked among
//  themselves (tied models keep a shared rank), and the list is ordered by the sum of those ranks,
//  which orders exactly as their mean does, because every model has one rank per chosen board.
//  Ties are broken by model id, never by a display name.

import XCTest

@testable import ModelRankingEngine

final class CombineTests: XCTestCase {
    private func board(_ id: String, _ standings: [(String, Int)]) -> BoardStandings {
        BoardStandings(
            id: id, benchmark: "B \(id)", metric: "elo", evidenceDate: "2026-09-18",
            observedAt: "2026-09-25", attribution: "cite \(id)",
            standings: standings.map { Standing(model: $0.0, position: $0.1) }
        )
    }

    private func standings(_ boards: [BoardStandings]) -> Standings {
        let ids = Set(boards.flatMap { $0.standings.map(\.model) }).sorted()
        return Standings(
            apiVersion: "v1", attributions: [], boards: boards,
            models: ids.map { StandingModel(id: $0, display: $0.uppercased(), vendor: "V",
                                            blendedPerM: 1, accessibility: nil) }
        )
    }

    func testAModelMissingFromOneChosenBoardIsLeftOut() throws {
        let data = standings([board("x", [("a", 1), ("b", 2), ("c", 3)]),
                              board("y", [("a", 1), ("c", 2)])])
        let list = try combine(data, boards: ["x", "y"])

        XCTAssertEqual(list.entries.map(\.model.id), ["a", "c"])
    }

    func testTheOrderComesFromPositionsReRankedAmongTheCommonModels() throws {
        // On x the common models rank a, b, c; on y they rank c, a, b (d is on y only and does not
        // count). Sums: a 1+2=3, b 2+3=5, c 3+1=4.
        let data = standings([board("x", [("a", 1), ("b", 5), ("c", 9)]),
                              board("y", [("d", 1), ("c", 2), ("a", 3), ("b", 4)])])
        let list = try combine(data, boards: ["x", "y"])

        XCTAssertEqual(list.entries.map(\.model.id), ["a", "c", "b"])
    }

    func testTiedModelsShareARankAndAnEqualSumIsBrokenById() throws {
        // x ties b and a; y ranks a before b. Sums: a 1+1=2, b 1+2=3.
        let tie = standings([board("x", [("b", 1), ("a", 1)]), board("y", [("a", 1), ("b", 2)])])
        XCTAssertEqual(try combine(tie, boards: ["x", "y"]).entries.map(\.model.id), ["a", "b"])

        // Mirrored boards give both models the same sum; the id decides, whatever the names say.
        let even = standings([board("x", [("zeta", 1), ("alpha", 2)]),
                              board("y", [("alpha", 1), ("zeta", 2)])])
        XCTAssertEqual(try combine(even, boards: ["x", "y"]).entries.map(\.model.id), ["alpha", "zeta"])
    }

    func testATieTakesTheHigherRankAndTheNextModelSkipsPastIt() throws {
        // Competition ranking: x ties a and b at 1, so c is 3, not 2. y ranks c, a, b.
        // Sums: a 1+2=3, b 1+3=4, c 3+1=4 -> a, then b before c by id. Counting a tie as
        // "one more than every model at or above it" would give a 4, b 5, c 4 -> a, c, b.
        let data = standings([board("x", [("a", 1), ("b", 1), ("c", 3)]),
                              board("y", [("c", 1), ("a", 2), ("b", 3)])])

        XCTAssertEqual(try combine(data, boards: ["x", "y"]).entries.map(\.model.id), ["a", "b", "c"])
    }

    func testOneBoardChosenIsThatBoardsOwnOrder() throws {
        let data = standings([board("x", [("c", 1), ("a", 2), ("b", 2), ("d", 4)])])

        XCTAssertEqual(try combine(data, boards: ["x"]).entries.map(\.model.id), ["c", "a", "b", "d"])
    }

    func testTheOrderTheBoardsWereChosenInChangesNothing() throws {
        let data = standings([board("x", [("a", 1), ("b", 2), ("c", 3)]),
                              board("y", [("c", 1), ("b", 2), ("a", 3)]),
                              board("z", [("b", 1), ("a", 2), ("c", 3)])])

        XCTAssertEqual(try combine(data, boards: ["x", "y", "z"]).entries.map(\.model.id),
                       try combine(data, boards: ["z", "x", "y"]).entries.map(\.model.id))
    }

    func testEachEntryCarriesItsPositionOnEveryChosenBoardAndTheListNamesTheBoards() throws {
        let data = standings([board("x", [("a", 1), ("b", 7)]), board("y", [("b", 1), ("a", 4)])])
        let list = try combine(data, boards: ["x", "y"])

        XCTAssertEqual(list.boards.map(\.id), ["x", "y"])
        XCTAssertEqual(list.boards.map(\.attribution), ["cite x", "cite y"])
        let a = try XCTUnwrap(list.entries.first { $0.model.id == "a" })
        XCTAssertEqual(a.positions, [BoardPosition(board: "x", position: 1),
                                     BoardPosition(board: "y", position: 4)])
    }

    func testAnUnknownBoardIsRefusedNeverSkipped() {
        let data = standings([board("x", [("a", 1)])])

        XCTAssertThrowsError(try combine(data, boards: ["x", "nope"])) { error in
            XCTAssertEqual(error as? CombineError, .unknownBoard("nope"))
        }
    }

    func testChoosingNoBoardIsRefused() {
        XCTAssertThrowsError(try combine(standings([board("x", [("a", 1)])]), boards: [])) { error in
            XCTAssertEqual(error as? CombineError, .noBoards)
        }
    }

    func testABoardChosenTwiceCountsOnce() throws {
        let data = standings([board("x", [("a", 1), ("b", 2)]), board("y", [("b", 1), ("a", 2)])])

        XCTAssertEqual(try combine(data, boards: ["x", "x", "y"]).boards.map(\.id), ["x", "y"])
    }

    func testAModelTheStandingsDoNotDescribeIsRefused() {
        // Another model is described, so a lookup that fell back to "any model" would serve it.
        let data = Standings(apiVersion: "v1", attributions: [],
                             boards: [board("x", [("ghost", 1)])],
                             models: [StandingModel(id: "a", display: "A", vendor: "V",
                                                    blendedPerM: 1, accessibility: nil)])

        XCTAssertThrowsError(try combine(data, boards: ["x"])) { error in
            XCTAssertEqual(error as? CombineError, .unknownModel("ghost"))
        }
    }
}
