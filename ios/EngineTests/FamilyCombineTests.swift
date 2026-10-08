//  M20-W2 (#210, REQ-CMB-002, REQ-CMB-003, D-188 clauses 2 to 4) -- a family of boards combined into
//  the product's own list, by position and never by score (D-105).
//
//  A model enters when at least half of the family's boards rank it, and at least two (one, for a
//  family of one board). Its place is the weighted mean of its percentile positions, (position - 1)
//  over (the board's size - 1), across the boards that rank it. A board whose newest evaluation is
//  more than 90 days old, or that publishes no date, weighs half. Equal means share a place, and the
//  order breaks them by model id.

import XCTest

@testable import ModelRankingEngine

final class FamilyCombineTests: OfflineTestCase {
    /// 2026-10-08: the day the rule was written. "fresh" is inside 90 days of it, "old" outside.
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
        return Standings(
            apiVersion: "v1", attributions: [], boards: boards,
            models: ids.map { StandingModel(id: $0, display: $0.uppercased(), vendor: "V",
                                            blendedPerM: 1, accessibility: nil) }
        )
    }

    private func order(_ list: FamilyList) -> [String] { list.entries.map(\.model.id) }
    private func places(_ list: FamilyList) -> [String: Int] {
        Dictionary(uniqueKeysWithValues: list.entries.map { ($0.model.id, $0.place) })
    }

    /// D-188 clause 2: half of the family's boards, and at least two.
    func testAModelNeedsHalfTheFamilyAndAtLeastTwoBoards() throws {
        let four = standings([board("p", [("a", 1), ("b", 2), ("c", 3)]), board("q", [("a", 1), ("b", 2)]),
                              board("r", [("a", 1)]), board("s", [("a", 1), ("d", 2)])])
        let list = try combineFamily(four, boards: ["p", "q", "r", "s"], asOf: today)
        XCTAssertEqual(list.coverage, 2)
        XCTAssertEqual(Set(order(list)), ["a", "b"], "c and d stand on one board of four")

        let five = standings((1...5).map { board("b\($0)", [("a", 1), ("b", 2)] + ($0 <= 2 ? [("c", 3)] : [])) })
        let fiveList = try combineFamily(five, boards: (1...5).map { "b\($0)" }, asOf: today)
        XCTAssertEqual(fiveList.coverage, 3)
        XCTAssertEqual(Set(order(fiveList)), ["a", "b"], "c stands on two boards of five")

        let one = standings([board("only", [("a", 1), ("b", 2), ("c", 3)])])
        XCTAssertEqual(order(try combineFamily(one, boards: ["only"], asOf: today)), ["a", "b", "c"],
                       "a family of one board is that board")
    }

    /// D-188 clause 3: the mean of percentile positions, so a board of 3 and a board of 101 count alike.
    func testThePlaceIsTheMeanPercentilePosition() throws {
        // a: 0/2 and 50/100 -> 0.25; b: 1/2 and 0/100 -> 0.25; c: 2/2 and 100/100 -> 1.
        let small = board("small", [("a", 1), ("b", 2), ("c", 3)])
        var rows = [("b", 1)] + (2...100).map { ("x\($0)", $0) }
        rows[50] = ("a", 51)
        rows.append(("c", 101))
        let large = board("large", rows)
        let list = try combineFamily(standings([small, large]), boards: ["small", "large"], asOf: today)
        XCTAssertEqual(Array(order(list).prefix(2)), ["a", "b"], "equal means are ordered by model id")
        XCTAssertEqual(places(list)["a"], places(list)["b"], "equal means share a place")
        XCTAssertEqual(order(list).last, "c")
    }

    /// D-188 clause 4: a board past 90 days weighs half, so a split between a fresh and an old board is
    /// decided by the fresh one; with both fresh it is a tie.
    func testAnOldBoardWeighsHalf() throws {
        let fresh = board("fresh", [("a", 1), ("b", 2)])
        let old = board("old", [("b", 1), ("a", 2)], date: "2026-06-25")
        let split = try combineFamily(standings([fresh, old]), boards: ["fresh", "old"], asOf: today)
        XCTAssertEqual(order(split), ["a", "b"])
        XCTAssertLessThan(places(split)["a"] ?? 0, places(split)["b"] ?? 0)
        XCTAssertEqual(split.staleBoards, ["old"])

        let bothFresh = board("also", [("b", 1), ("a", 2)])
        let tie = try combineFamily(standings([fresh, bothFresh]), boards: ["fresh", "also"], asOf: today)
        XCTAssertEqual(places(tie)["a"], places(tie)["b"])
        XCTAssertEqual(tie.staleBoards, [])
    }

    /// D-188 clause 4: a board that publishes no date cannot be aged, so it weighs half too.
    func testAnUndatedBoardWeighsHalf() throws {
        let fresh = board("fresh", [("a", 1), ("b", 2)])
        let undated = board("undated", [("b", 1), ("a", 2)], date: nil)
        let list = try combineFamily(standings([fresh, undated]), boards: ["fresh", "undated"], asOf: today)
        XCTAssertEqual(order(list), ["a", "b"])
        XCTAssertEqual(list.staleBoards, ["undated"])
    }

    /// Each entry carries where every board that ranks it put it, in the family's order.
    func testAnEntryCarriesEachBoardsPosition() throws {
        let list = try combineFamily(standings([board("p", [("a", 1), ("b", 2)]), board("q", [("b", 1), ("a", 2)])]),
                                     boards: ["p", "q"], asOf: today)
        let a = list.entries.first { $0.model.id == "a" }
        XCTAssertEqual(a?.positions, [BoardPosition(board: "p", position: 1), BoardPosition(board: "q", position: 2)])
    }

    func testAnUnknownBoardOrModelIsRefused() {
        let data = standings([board("p", [("a", 1)])])
        XCTAssertThrowsError(try combineFamily(data, boards: ["p", "nope"], asOf: today)) {
            XCTAssertEqual($0 as? CombineError, .unknownBoard("nope"))
        }
        XCTAssertThrowsError(try combineFamily(data, boards: [], asOf: today)) {
            XCTAssertEqual($0 as? CombineError, .noBoards)
        }
        let orphan = Standings(apiVersion: "v1", attributions: [], boards: [board("p", [("ghost", 1)])], models: [])
        XCTAssertThrowsError(try combineFamily(orphan, boards: ["p"], asOf: today)) {
            XCTAssertEqual($0 as? CombineError, .unknownModel("ghost"))
        }
    }

    // MARK: - Properties, on boards built from a fixed generator

    /// A small deterministic generator, so a failure names its seed and replays.
    private struct Generator {
        var state: UInt64
        mutating func next(_ bound: Int) -> Int {
            state = state &* 6364136223846793005 &+ 1442695040888963407
            return Int((state >> 33) % UInt64(bound))
        }
    }

    private func randomFamily(_ seed: UInt64) -> (Standings, [String]) {
        var generator = Generator(state: seed)
        let models = (0..<12).map { "m\($0)" }
        var boards: [BoardStandings] = []
        for index in 0..<(2 + generator.next(5)) {
            var pool = models
            var rows: [(String, Int)] = []
            for position in 1...(3 + generator.next(9)) where !pool.isEmpty {
                rows.append((pool.remove(at: generator.next(pool.count)), position))
            }
            let date = generator.next(3) == 0 ? "2026-05-01" : "2026-09-20"
            boards.append(board("b\(index)", rows, date: date))
        }
        return (standings(boards), boards.map(\.id))
    }

    func testTheBoardsOrderChangesNothing() throws {
        for seed in UInt64(1)...60 {
            let (data, ids) = randomFamily(seed)
            let forward = try combineFamily(data, boards: ids, asOf: today)
            let backward = try combineFamily(data, boards: ids.reversed(), asOf: today)
            XCTAssertEqual(order(forward), order(backward), "seed \(seed)")
            XCTAssertEqual(places(forward), places(backward), "seed \(seed)")
        }
    }

    func testABoardWithNoModelsChangesNothing() throws {
        for seed in UInt64(1)...60 {
            let (data, ids) = randomFamily(seed)
            let empty = board("empty", [])
            let more = Standings(apiVersion: "v1", attributions: [], boards: data.boards + [empty], models: data.models)
            XCTAssertEqual(order(try combineFamily(data, boards: ids, asOf: today)),
                           order(try combineFamily(more, boards: ids + ["empty"], asOf: today)), "seed \(seed)")
        }
    }

    /// Two models ranked by the same boards: the one better on every one of them is placed before.
    func testAModelBetterOnEveryBoardIsPlacedBefore() throws {
        for seed in UInt64(1)...80 {
            let (data, ids) = randomFamily(seed)
            let list = try combineFamily(data, boards: ids, asOf: today)
            let boards = data.boards
            for first in list.entries {
                for second in list.entries where first.model.id != second.model.id {
                    let sameBoards = Set(first.positions.map(\.board)) == Set(second.positions.map(\.board))
                    let better = first.positions.allSatisfy { mine in
                        second.positions.contains { $0.board == mine.board && mine.position < $0.position }
                    }
                    if sameBoards && better {
                        XCTAssertLessThan(first.place, second.place,
                                          "seed \(seed): \(first.model.id) before \(second.model.id) on \(boards.count) boards")
                    }
                }
            }
        }
    }
}
