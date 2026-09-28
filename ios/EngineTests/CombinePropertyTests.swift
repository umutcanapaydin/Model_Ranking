// Ref #61, D-167 clause 3: independent grouped-rank oracle, generated inputs and invariants.
import XCTest
@testable import ModelRankingEngine

final class CombinePropertyTests: XCTestCase {
    private struct Generator {
        var state: UInt64
        mutating func next(_ bound: Int) -> Int {
            state = state &* 6364136223846793005 &+ 1442695040888963407
            return Int((state >> 32) % UInt64(bound))
        }
    }

    private func board(_ id: String, _ rows: [(String, Int)]) -> BoardStandings {
        BoardStandings(id: id, benchmark: "Benchmark \(id)", metric: "ips", rankingEffort: "high",
                       evidenceDate: "2026-09-25", observedAt: "2026-09-26", attribution: "Source \(id)",
                       standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "max") })
    }

    private func payload(_ boards: [BoardStandings]) -> Standings {
        let ids = Set(boards.flatMap { $0.standings.map(\.model) }).sorted()
        return Standings(apiVersion: "v1", attributions: ["fixture"], boards: boards,
                         models: ids.enumerated().map { index, id in
            StandingModel(id: id, display: "Reverse \(ids.count - index)", vendor: "Vendor \(id)",
                          blendedPerM: Double(index) / 10, accessibility: "API access")
        })
    }

    // Written from D-167, deliberately not the production filter/count or summed-rank comparator.
    // Each ordered position GROUP consumes its member count before the next group's rank.
    private func reference(_ data: Standings, chosen: [String]) throws -> CombinedList {
        var boards: [BoardStandings] = []
        for id in chosen where !boards.contains(where: { $0.id == id }) {
            boards.append(try XCTUnwrap(data.boards.first { $0.id == id }))
        }
        var tables: [[String: Int]] = []
        for b in boards {
            var first: [String: Int] = [:]
            for row in b.standings where first[row.model] == nil { first[row.model] = row.position }
            tables.append(first)
        }
        let candidates = data.models.filter { m in tables.allSatisfy { $0[m.id] != nil } }
        let ids = Set(candidates.map(\.id))
        var vectors: [String: [Int]] = Dictionary(uniqueKeysWithValues: ids.map { ($0, []) })
        for table in tables {
            let groups = Dictionary(grouping: table.filter { ids.contains($0.key) }, by: { $0.value })
            var nextRank = 1
            for position in groups.keys.sorted() {
                let group = groups[position]!
                for entry in group { vectors[entry.key]!.append(nextRank) }
                nextRank += group.count
            }
        }
        // Compare arithmetic averages as fractions; no production comparator is called.
        let ordered = candidates.sorted { a, b in
            let av = vectors[a.id]!, bv = vectors[b.id]!
            let left = av.reduce(0, +) * bv.count, right = bv.reduce(0, +) * av.count
            return left == right ? a.id < b.id : left < right
        }
        // A place is one more than the models whose average is strictly lower (review M1).
        func below(_ a: StandingModel, _ b: StandingModel) -> Bool {
            let av = vectors[a.id]!, bv = vectors[b.id]!
            return av.reduce(0, +) * bv.count < bv.reduce(0, +) * av.count
        }
        return CombinedList(boards: boards, entries: ordered.map { m in
            CombinedEntry(model: m, positions: boards.enumerated().map { i, b in
                BoardPosition(board: b.id, position: tables[i][m.id]!)
            }, place: 1 + ordered.filter { below($0, m) }.count)
        })
    }

    func testWholeBoardRankingIsNotSharedPopulationRanking() throws {
        // Ref #61 fourth Tester: correct shared sums tie; a wins by id. Whole-board sums pick b.
        let data = payload([board("x", [("a", 1), ("b", 2)]),
                            board("y", [("b", 1), ("u", 2), ("v", 3), ("a", 4)])])
        XCTAssertEqual(try combine(data, boards: ["x", "y"]).entries.map(\.model.id), ["a", "b"])
    }

    func testGeneratedCombinationsMatchIndependentGroupedReference() throws {
        var rng = Generator(state: 0x61D167)
        var empty = 0, ties = 0, duplicates = 0, unshared = 0
        for trial in 0..<1200 {
            let size = 2 + rng.next(7), count = 1 + rng.next(4)
            var boards: [BoardStandings] = []
            for b in 0..<count {
                var rows: [(String, Int)] = []
                for m in 0..<size where rng.next(4) != 0 {
                    rows.append(("m\(m)", 1 + rng.next(5) * 3))
                }
                if rows.count > Set(rows.map { $0.1 }).count { ties += 1 }
                if let row = rows.first, rng.next(2) == 0 {
                    rows.append((row.0, row.1 + 100)); duplicates += 1
                }
                if rng.next(2) == 0 { rows.reverse() }
                boards.append(board("b\(b)", rows))
            }
            boards.append(board("unchosen", [("outside", 1)]))
            let data = payload(boards)
            var chosen = (0..<count).map { "b\($0)" }
            if rng.next(2) == 0 { chosen.reverse() }
            chosen.append(chosen[0])
            let expected = try reference(data, chosen: chosen)
            if expected.entries.isEmpty { empty += 1 }
            if expected.entries.count < Set(boards[0].standings.map(\.model)).count { unshared += 1 }
            XCTAssertEqual(try combine(data, boards: chosen), expected, "seed=0x61D167 trial=\(trial) data=\(data) chosen=\(chosen)")
        }
        XCTAssertGreaterThan(empty, 20)
        XCTAssertGreaterThan(ties, 100)
        XCTAssertGreaterThan(duplicates, 100)
        XCTAssertGreaterThan(unshared, 100)
    }

    func testNonCommonRowsCannotChangeTheCombinedOrder() throws {
        var rng = Generator(state: 0x61ADD)
        for trial in 0..<300 {
            var base: [BoardStandings] = []
            var expanded: [BoardStandings] = []
            for b in 0..<3 {
                var rows: [(String, Int)] = []
                for m in 0..<5 { rows.append(("m\(m)", 1 + rng.next(4))) }
                base.append(board("b\(b)", rows))
                var added = rows.map { ($0.0, $0.1 * 3 + 10) }
                added.append(("private\(b)", 1))
                added.append(("other\(b)", 2))
                expanded.append(board("b\(b)", added))
            }
            let chosen = base.map(\.id)
            let original = try combine(payload(base), boards: chosen)
            let changed = try combine(payload(expanded), boards: chosen.reversed())
            XCTAssertEqual(original.entries.map(\.model.id), changed.entries.map(\.model.id), "trial=\(trial)")
            XCTAssertEqual(changed.boards.map(\.id), Array(chosen.reversed()))
        }
    }
}
