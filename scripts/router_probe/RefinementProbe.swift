//  RefinementProbe.swift — the on-device model's surface and refinement choices, measured (M17-W5,
//  D-168, docs/research/m17-w5-refinement-probe-2026-09-28.md).
//
//  It calls `ModelRouter().route` itself, so it runs only where Apple Intelligence is enabled; the
//  package never builds it. To run, copy `ios/` to a scratch directory (never this checkout), put
//  this file in the copy's `EngineTests/`, and from the copy:
//
//      PROBE_QUESTIONS=/abs/path/refinement_heldout_questions.json PROBE_OUT=/abs/path/out.json \
//          swift test --filter RefinementProbe
//
//  A question set is either `[[question, expected surface]]` (probe_questions.json,
//  heldout_questions.json) or `[{q, surface, language, domain, kind}]` (refinement_questions.json,
//  refinement_heldout_questions.json). The output is one row per question: the surface, whether it
//  was declined, and each refinement kind's value or `none`. The model is not deterministic: run
//  every set at least twice. Scoring is described in the research record.
import XCTest
@testable import ModelRankingEngine

final class RefinementProbe: XCTestCase {
    /// The ids `/v1/categories` served when the probe was written; pass the live list if it changed.
    let served = ["coding", "agentic-coding", "assistant", "everyday", "expert", "mathematics", "computer-use",
                  "abstract", "web-dev", "document", "factuality", "vision", "search", "search_factuality"]

    func testProbe() async throws {
        guard #available(macOS 26.0, iOS 26.0, *) else { throw XCTSkip("no FoundationModels here") }
        let env = ProcessInfo.processInfo.environment
        guard let input = env["PROBE_QUESTIONS"], let output = env["PROBE_OUT"] else {
            throw XCTSkip("set PROBE_QUESTIONS and PROBE_OUT")
        }
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        let questions = (json as? [[String]])?.map { $0[0] }
            ?? (json as? [[String: String]])?.compactMap { $0["q"] } ?? []
        var rows: [[String: String]] = []
        for question in questions {
            let outcome = await ModelRouter().route(question, within: served)
            var row = ["q": question, "surface": outcome?.categoryID ?? "nil",
                       "unmeasured": "\(outcome?.unmeasured ?? false)"]
            for kind in RefinementKind.allCases {
                row[kind.rawValue] = outcome?.refinements.first { $0.kind == kind }?.value ?? "none"
            }
            rows.append(row)
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
