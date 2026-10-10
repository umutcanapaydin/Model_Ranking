//  JudgementProbe.swift -- the rows of the owner's judgement sheet (#226, M21-W2): per question, what the
//  screen shows (our family list's first five) beside the primary board's own first five, from the
//  served `/v1/categories` and `/v1/boards`. The row is `JudgementRows.row`, in `EngineTests/`, which a
//  test runs. Install it beside `ReadingProbe.swift` in a scratch copy's `EngineTests/`, and from the copy:
//
//      JUDGE_QUESTIONS=/abs/q.json JUDGE_CATEGORIES=/abs/categories.json JUDGE_BOARDS=/abs/boards.json \
//      JUDGE_OUT=/abs/rows.json swift test --filter JudgementProbe
//
//  The questions are routed by the wording tier, as a device without the model does, so a run can be
//  made again; `JUDGE_TIER=model` uses the on-device model where it runs.
import Foundation
import XCTest
@testable import ModelRankingEngine

final class JudgementProbe: XCTestCase {
    func testRows() async throws {
        let env = ProcessInfo.processInfo.environment
        guard let input = env["JUDGE_QUESTIONS"], let categoriesPath = env["JUDGE_CATEGORIES"],
              let boardsPath = env["JUDGE_BOARDS"], let output = env["JUDGE_OUT"] else {
            return XCTFail("set JUDGE_QUESTIONS, JUDGE_CATEGORIES, JUDGE_BOARDS and JUDGE_OUT")
        }
        let categories = try JSONDecoder().decode(CategoryList.self,
                                                  from: Data(contentsOf: URL(fileURLWithPath: categoriesPath))).categories
        let standings = try JSONDecoder().decode(Standings.self, from: Data(contentsOf: URL(fileURLWithPath: boardsPath)))
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        let questions = (json as? [String]) ?? (json as? [[String: String]])?.compactMap { $0["q"] } ?? []
        guard !questions.isEmpty else { return XCTFail("\(input) holds no questions") }
        let known = categories.map(\.id)
        let router = env["JUDGE_TIER"] == "model" ? TieredRouter() : TieredRouter(model: nil)
        var rows: [[String: Any]] = []
        for question in questions {
            let outcome = await router.route(question, within: known)
            rows.append(JudgementRows.row(question: question, outcome: outcome, categories: categories,
                                          standings: standings, asOf: Date()))
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
