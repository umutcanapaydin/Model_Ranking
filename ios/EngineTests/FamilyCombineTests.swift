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

    // MARK: - The M20-W2 Tester's tests: faults that passed every test above

    /// covers REQ-CMB-002 (D-188 clause 3) -- the M20-W2 Tester's M1: the place is the MEAN over the
    /// boards that rank a model. y: (0.25 + 0.5) / 2 = 0.375 on two boards; x: 0.5 on one. A sum (y 0.75)
    /// or a mean over every board (x 0.25) puts x first.
    func testTheMeanIsOverTheBoardsThatRankTheModel() throws {
        let p = board("p", [("m1", 1), ("y", 2), ("x", 3), ("m4", 4), ("m5", 5)])
        let q = board("q", [("z", 1), ("y", 2), ("w", 3)])
        let list = try combineFamily(standings([p, q]), boards: ["p", "q"], asOf: today)
        XCTAssertEqual(order(list), ["m1", "z", "y", "x", "m4", "m5", "w"])
        XCTAssertEqual(list.entries.map(\.place), [1, 1, 3, 4, 5, 6, 6])
    }

    /// covers REQ-CMB-002 (D-188 clause 3) -- the M20-W2 Tester's M2: three models sharing a position share
    /// one place, and the next model is placed after all three (1, 1, 1, 4), not after the second.
    func testThreeModelsSharingAPositionShareOnePlace() throws {
        let list = try combineFamily(standings([board("p", [("c", 1), ("a", 1), ("b", 1), ("d", 4)])]),
                                     boards: ["p"], asOf: today)
        XCTAssertEqual(order(list), ["a", "b", "c", "d"])
        XCTAssertEqual(list.entries.map(\.place), [1, 1, 1, 4])
    }

    /// covers REQ-CMB-002 (D-188 clause 2) -- the M20-W2 Tester's M3: a board named twice in a family
    /// counts once, so it neither raises the coverage nor counts a model's position twice.
    func testABoardNamedTwiceCountsOnce() throws {
        let data = standings([board("p", [("a", 1), ("b", 2)]), board("q", [("c", 1), ("a", 2)])])
        let once = try combineFamily(data, boards: ["p", "q"], asOf: today)
        XCTAssertEqual(try combineFamily(data, boards: ["p", "q", "p"], asOf: today), once)
    }

    /// covers REQ-CMB-002 (D-188 clause 2) -- the M20-W2 Tester's M3: a model one board lists twice (only
    /// a bad payload could) stands on that board once, so it does not reach the coverage on it alone.
    func testAModelListedTwiceOnABoardCountsOnce() throws {
        let data = standings([board("p", [("a", 1), ("a", 2), ("b", 3)]), board("q", [("b", 1)]),
                              board("r", [("c", 1)])])
        let list = try combineFamily(data, boards: ["p", "q", "r"], asOf: today)
        XCTAssertEqual(list.coverage, 2)
        XCTAssertEqual(order(list), ["b"], "a stands on one board of three, however often that board lists it")
    }

    /// covers REQ-CMB-002 (D-188 clause 3) -- the M20-W2 Tester's M3: a position past the board's size
    /// counts as its last place, so one bad row cannot outweigh every other board.
    func testAPositionPastTheBoardsSizeCountsAsItsLast() throws {
        let data = standings([board("p", [("a", 1), ("b", 9)]), board("q", [("b", 1), ("a", 2)])])
        let list = try combineFamily(data, boards: ["p", "q"], asOf: today)
        XCTAssertEqual(places(list)["a"], places(list)["b"], "b is last on p and first on q, a the other way")
    }

    /// covers REQ-CMB-002 -- the M20-W2 Tester's M3, the W2 review's R2 from the other side: a model the
    /// model list lacks takes no place, so the models after it keep theirs.
    func testAModelTheModelListLacksTakesNoPlace() throws {
        let data = Standings(apiVersion: "v1", attributions: [],
                             boards: [board("p", [("ghost", 1), ("a", 2), ("b", 3)])],
                             models: ["a", "b"].map { StandingModel(id: $0, display: $0, vendor: "V",
                                                                    blendedPerM: 1, accessibility: nil) })
        let list = try combineFamily(data, boards: ["p"], asOf: today)
        XCTAssertEqual(order(list), ["a", "b"])
        XCTAssertEqual(list.entries.map(\.place), [1, 2])
    }

    /// covers REQ-CMB-002 -- the M20-W2 Tester's M3: a board that ranks no model is not among the list's
    /// boards, the ones the detail screen names as the list's sources.
    func testABoardThatRanksNoModelIsNotAmongTheListsBoards() throws {
        let data = standings([board("p", [("a", 1)]), board("empty", [])])
        XCTAssertEqual(try combineFamily(data, boards: ["p", "empty"], asOf: today).boards.map(\.id), ["p"])
    }

    /// covers REQ-CMB-002 (D-188 clause 3) -- the M20-W2 Tester's M3: equal means summed in a different
    /// order are still equal, so they share a place. a is 0.1, 0.2, 0.3 on p, q, r, and b 0.3, 0.2, 0.1;
    /// in floating point 0.1 + 0.2 + 0.3 is not 0.3 + 0.2 + 0.1.
    func testEqualMeansSummedInADifferentOrderShareAPlace() throws {
        // A board of eleven: a and b where given (sharing one position on q), the rest filled in.
        func eleven(_ id: String, a: Int, b: Int) -> BoardStandings {
            let taken: Set<Int> = a == b ? [a, a + 1] : [a, b]
            let others = (1...11).filter { !taken.contains($0) }.map { ("o\($0)", $0) }
            return board(id, ([("a", a), ("b", b)] + others).sorted { $0.1 < $1.1 })
        }
        let data = standings([eleven("p", a: 2, b: 4), eleven("q", a: 3, b: 3), eleven("r", a: 4, b: 2)])
        XCTAssertEqual(data.boards.map(\.standings.count), [11, 11, 11])
        let list = try combineFamily(data, boards: ["p", "q", "r"], asOf: today)
        XCTAssertNotNil(places(list)["a"])
        XCTAssertEqual(places(list)["a"], places(list)["b"], "a and b both average 0.2")
    }

    /// covers REQ-CMB-002 (D-188 clause 3) -- the M20-W2 Tester's M3: two means a thousandth apart stay
    /// apart (a board of 1001 models; the served boards' steps are about that fine).
    func testMeansAThousandthApartStayApart() throws {
        let rows = (1...1001).map { ("m\(String(format: "%04d", $0))", $0) }
        let list = try combineFamily(standings([board("big", rows)]), boards: ["big"], asOf: today)
        XCTAssertEqual(Array(list.entries.prefix(3).map(\.place)), [1, 2, 3])
    }

    /// covers REQ-CMB-002 -- the M20-W2 Tester's M3: a payload carrying one board id twice is read at its
    /// first copy, as `combine` reads it and as the scan the W2 review's M5 replaced did.
    func testABoardIdSentTwiceIsReadAtItsFirstCopy() throws {
        let data = standings([board("p", [("a", 1), ("b", 2)]), board("p", [("b", 1), ("a", 2)])])
        XCTAssertEqual(order(try combineFamily(data, boards: ["p"], asOf: today)), ["a", "b"])
    }

    /// covers REQ-CMB-003 (D-188 clause 4) -- the M20-W2 Tester's M3: a date the phone cannot read cannot
    /// be aged, so the board is named as an undated one is; a date with a time is read by its day.
    func testAnUnreadableDateIsNamed() throws {
        let data = standings([board("p", [("a", 1)], date: "Sept 2026"),
                              board("q", [("a", 1)], date: "2026-07-10T23:59:59Z")])
        XCTAssertEqual(try combineFamily(data, boards: ["p", "q"], asOf: today).staleBoards, ["p"])
    }

    /// covers REQ-CMB-002 -- the W2 review's M5, whose fix shipped without a test: a family's boards are
    /// looked up once by id, so a family list near `/v1/categories`' size cap cannot freeze the screen
    /// (#74's failure by a new path). The scan it replaced took 33.7 s for 25,000 boards. Undated boards,
    /// so the time measured is the lookup's.
    func testAFamilyOfManyBoardsCombinesWithoutFreezing() throws {
        let count = 25_000
        let boards = (0..<count).map { board(String(format: "b%05d", $0), [("a", 1)], date: nil) }
        let data = standings(boards)
        let started = Date()
        let list = try combineFamily(data, boards: boards.map(\.id), asOf: today)
        let seconds = Date().timeIntervalSince(started)
        XCTAssertEqual(list.boards.count, count)
        XCTAssertEqual(order(list), ["a"])
        XCTAssertLessThan(seconds, 5, "combineFamily took \(seconds) s for a family of \(count) boards")
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

    /// The M20 closure security seat's S3: a position at the integer's limit, which decodes, places
    /// the model last rather than trapping. Written with its fix: the red would trap the test process
    /// and open a crash dialog on the owner's Mac; the seat showed the overflow with `xcrun swift`.
    func testAPositionAtTheIntegersLimitDoesNotTrap() throws {
        let boards = [
            BoardStandings(id: "one", benchmark: "One", metric: "elo", rankingEffort: nil, evidenceDate: "2026-10-01",
                           observedAt: "2026-10-07", attribution: "x",
                           standings: [Standing(model: "a", position: Int.min, effort: "unspecified"),
                                       Standing(model: "b", position: 1, effort: "unspecified")]),
        ]
        let standings = Standings(apiVersion: "v1", attributions: [], boards: boards,
                                  models: ["a", "b"].map { StandingModel(id: $0, display: $0, vendor: "V", blendedPerM: 1,
                                                                         accessibility: nil) })
        let list = try combineFamily(standings, boards: ["one"], asOf: Date())
        XCTAssertEqual(Set(list.entries.map(\.model.id)), ["a", "b"])
    }
}
