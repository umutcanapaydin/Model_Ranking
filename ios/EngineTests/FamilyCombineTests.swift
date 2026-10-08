//  M20-W2 (#210, REQ-CMB-002, REQ-CMB-003, D-188 clauses 2 to 4) -- a family of boards combined into
//  the product's own list, by position and never by score (D-105).
//
//  A model enters when at least half of the family's boards rank it, rounded up, and at least one (with
//  two boards, either is enough: the W1 review measured "and at least two" as an intersection). Its place is the weighted mean of its percentile positions, (position - 1)
//  over (the board's size - 1), across the boards that rank it; every board counts the same, and one
//  whose newest evaluation is more than 90 days old, or undated, is named under the list (the W2
//  review measured a half weight letting Arena decide five families alone). Equal means share a place,
//  and the order breaks them by model id.

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

    /// D-188 clause 2: half of the family's boards, rounded up, and at least one.
    func testAModelNeedsHalfTheFamilysBoards() throws {
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

        // Two boards: either is enough, so the list is their union, not their intersection.
        let two = standings([board("p", [("a", 1), ("b", 2)]), board("q", [("c", 1), ("a", 2)])])
        let twoList = try combineFamily(two, boards: ["p", "q"], asOf: today)
        XCTAssertEqual(twoList.coverage, 1)
        XCTAssertEqual(Set(order(twoList)), ["a", "b", "c"])
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
        // With two boards either is enough, so the large board's other models enter too (each by its
        // one percentile); a, b and c are read among themselves.
        let three = order(list).filter { ["a", "b", "c"].contains($0) }
        XCTAssertEqual(three, ["a", "b", "c"], "equal means are ordered by model id, and c is last")
        XCTAssertEqual(places(list)["a"], places(list)["b"], "equal means share a place")
        XCTAssertLessThan(places(list)["b"] ?? 0, places(list)["c"] ?? 0)
    }

    /// D-188 clause 4 as the W2 review measured it: an old board counts the same, and is named.
    func testAnOldBoardCountsTheSameAndIsNamed() throws {
        let fresh = board("fresh", [("a", 1), ("b", 2)])
        let old = board("old", [("b", 1), ("a", 2)], date: "2026-06-25")
        let split = try combineFamily(standings([fresh, old]), boards: ["fresh", "old"], asOf: today)
        XCTAssertEqual(places(split)["a"], places(split)["b"], "a split between two boards is a tie")
        XCTAssertEqual(split.staleBoards, ["old"])
    }

    /// D-188 clause 4: a board that publishes no date cannot be aged; it counts the same, and is named.
    func testAnUndatedBoardCountsTheSameAndIsNamed() throws {
        let fresh = board("fresh", [("a", 1), ("b", 2)])
        let undated = board("undated", [("b", 1), ("a", 2)], date: nil)
        let list = try combineFamily(standings([fresh, undated]), boards: ["fresh", "undated"], asOf: today)
        XCTAssertEqual(places(list)["a"], places(list)["b"])
        XCTAssertEqual(list.staleBoards, ["undated"])
    }

    /// The W2 review's M6: a board is named past 90 whole days, as the engine's own line draws it.
    func testTheNinetyDayLine() throws {
        let ninety = board("ninety", [("a", 1), ("b", 2)], date: "2026-07-10")
        let ninetyOne = board("ninetyOne", [("a", 1), ("b", 2)], date: "2026-07-09")
        let list = try combineFamily(standings([ninety, ninetyOne]), boards: ["ninety", "ninetyOne"], asOf: today)
        XCTAssertEqual(list.staleBoards, ["ninetyOne"])
    }

    /// The W2 review's M4: a shared position counts as that position, the competition ranking a board
    /// publishes (two models at 1, the next at 3).
    func testASharedPositionCountsAsThatPosition() throws {
        let tied = board("tied", [("a", 1), ("b", 1), ("c", 3)])
        let list = try combineFamily(standings([tied]), boards: ["tied"], asOf: today)
        XCTAssertEqual(places(list)["a"], 1)
        XCTAssertEqual(places(list)["b"], 1)
        XCTAssertEqual(places(list)["c"], 3)
    }

    /// The W2 review's R2: one standing naming a model the payload's model list lacks leaves that model
    /// out; it does not blank the family.
    func testAModelTheModelListLacksIsLeftOut() throws {
        let data = Standings(apiVersion: "v1", attributions: [], boards: [board("p", [("a", 1), ("ghost", 2)])],
                             models: [StandingModel(id: "a", display: "A", vendor: "V", blendedPerM: 1, accessibility: nil)])
        XCTAssertEqual(order(try combineFamily(data, boards: ["p"], asOf: today)), ["a"])
    }

    /// Each entry carries where every board that ranks it put it, in the family's order.
    func testAnEntryCarriesEachBoardsPosition() throws {
        let list = try combineFamily(standings([board("p", [("a", 1), ("b", 2)]), board("q", [("b", 1), ("a", 2)])]),
                                     boards: ["p", "q"], asOf: today)
        let a = list.entries.first { $0.model.id == "a" }
        XCTAssertEqual(a?.positions, [BoardPosition(board: "p", position: 1), BoardPosition(board: "q", position: 2)])
    }

    /// The W1 review's R1: a family board the standings lack (an Arena outage, a source left out) is left
    /// out of the family, so it can neither empty the list nor raise the coverage.
    func testAFamilyBoardTheStandingsLackIsLeftOut() throws {
        let data = standings([board("p", [("a", 1), ("b", 2)]), board("q", [("b", 1), ("a", 2)])])
        let full = try combineFamily(data, boards: ["p", "q"], asOf: today)
        let withGone = try combineFamily(data, boards: ["p", "gone", "q"], asOf: today)
        XCTAssertEqual(order(full), order(withGone))
        XCTAssertEqual(withGone.coverage, full.coverage)
        XCTAssertEqual(withGone.boards.map(\.id), ["p", "q"])
    }

    func testAFamilyWithNoKnownBoardIsRefused() {
        let data = standings([board("p", [("a", 1)])])
        XCTAssertThrowsError(try combineFamily(data, boards: ["nope"], asOf: today)) {
            XCTAssertEqual($0 as? CombineError, .noBoards, "a family none of whose boards is kept has no list")
        }
        XCTAssertThrowsError(try combineFamily(data, boards: [], asOf: today)) {
            XCTAssertEqual($0 as? CombineError, .noBoards)
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
            var position = 1
            for _ in 1...(3 + generator.next(9)) where !pool.isEmpty {
                rows.append((pool.remove(at: generator.next(pool.count)), position))
                // Now and then two models share a place, as a board publishes a tie (the W2 review's M3).
                if generator.next(4) != 0 { position = rows.count + 1 }
            }
            let date: String? = [nil, "2026-05-01", "2026-09-20", "2026-09-20"][generator.next(4)]
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
