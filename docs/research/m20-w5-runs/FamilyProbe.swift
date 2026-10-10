//  FamilyProbe.swift -- scratch (M20-W5, #195): for each question, the wording tier's surface and
//  reading, the refinements the words name, the family list the app would build, and the primary
//  board's own order beside it. Not committed; run from a scratch copy of ios/.
import XCTest
@testable import ModelRankingEngine

final class FamilyProbe: XCTestCase {
    let served = ["coding", "agentic-coding", "assistant", "everyday", "expert", "mathematics", "computer-use",
                  "abstract", "web-dev", "document", "factuality", "vision", "search", "search_factuality"]

    func testFamilies() async throws {
        let env = ProcessInfo.processInfo.environment
        guard let input = env["PROBE_QUESTIONS"], let output = env["PROBE_OUT"], let boardsPath = env["PROBE_BOARDS"],
              let familiesPath = env["PROBE_FAMILIES"] else { return XCTFail("set the PROBE_ variables") }
        let standings = try JSONDecoder().decode(Standings.self, from: Data(contentsOf: URL(fileURLWithPath: boardsPath)))
        let families = try JSONDecoder().decode([String: [String]].self,
                                                from: Data(contentsOf: URL(fileURLWithPath: familiesPath)))
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        let questions = (json as? [[String: String]])?.compactMap { $0["q"] } ?? []
        guard !questions.isEmpty else { return XCTFail("no questions") }
        let asOf = ISO8601DateFormatter().date(from: "2026-10-08T00:00:00Z") ?? Date()
        var rows: [[String: String]] = []
        for question in questions {
            let read = await TieredRouter(model: nil).route(question, within: served)
            let surface = read.categoryID
            let words = Refinements.read(question)
            let allowed = words.filter { $0.surfaces.contains(surface) }
            var row: [String: String] = [
                "q": question, "surface": surface, "unmeasured": "\(read.unmeasured)", "reading": "\(read.reading)",
                "tier": "\(read.tier)",
                "language": words.filter { $0.kind == .language }.map(\.value).joined(separator: ","),
                "domain": words.filter { $0.kind == .domain }.map(\.value).joined(separator: ","),
                "allowed": allowed.map(\.value).joined(separator: ","),
            ]
            let family = families[surface] ?? []
            if let primary = family.first {
                let boards = Refinements.familyBoards(primary: primary, family: family, surface: surface, chosen: allowed)
                if let list = try? combineFamily(standings, boards: boards, asOf: asOf) {
                    row["boards"] = list.boards.map(\.id).joined(separator: ",")
                    row["stale"] = list.staleBoards.joined(separator: ",")
                    row["entries"] = "\(list.entries.count)"
                    row["top10"] = list.entries.prefix(10).map(\.model.id).joined(separator: ",")
                }
                if let board = standings.boards.first(where: { $0.id == primary }) {
                    var seen = Set<String>()
                    let order = board.standings.sorted { $0.position < $1.position }.map(\.model)
                        .filter { seen.insert($0).inserted }
                    row["primarySize"] = "\(order.count)"
                    row["primaryTop10"] = order.prefix(10).joined(separator: ",")
                }
            }
            rows.append(row)
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
