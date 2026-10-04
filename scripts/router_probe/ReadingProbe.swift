//  ReadingProbe.swift — the on-device model's reading of a question, as the app decides it: the
//  model tier, then the signals in code (D-169 as amended at M18-W3). Measured in
//  docs/research/m18-w3-question-reading-probe-2026-10-04.md.
//
//  It calls `ModelRouter().route` itself, so it runs only where Apple Intelligence is enabled; the
//  package never builds it. To run, copy `ios/` to a scratch directory (never this checkout), put
//  this file in the copy's `EngineTests/`, and from the copy:
//
//      PROBE_QUESTIONS=/abs/path/set.json PROBE_OUT=/abs/path/out.json swift test --filter ReadingProbe
//
//  A set is `[[question, expected]]` or `[{q, expected, ...}]`. The output is one row per question:
//  the surface, whether it was declined, the model's own verdict and the app's reading. The model is
//  not deterministic: run every set at least twice. Where the model is not available the test
//  fails, so no file of empty rows is ever scored.
import XCTest
@testable import ModelRankingEngine

final class ReadingProbe: XCTestCase {
    let served = ["coding", "agentic-coding", "assistant", "everyday", "expert", "mathematics", "computer-use",
                  "abstract", "web-dev", "document", "factuality", "vision", "search", "search_factuality"]

    func testProbe() async throws {
        guard #available(macOS 26.0, iOS 26.0, *) else { return XCTFail("no FoundationModels here") }
        guard ModelRouter.state == .available else {
            return XCTFail("the on-device model is not available here: \(ModelRouter.state)")
        }
        let env = ProcessInfo.processInfo.environment
        guard let input = env["PROBE_QUESTIONS"], let output = env["PROBE_OUT"] else {
            return XCTFail("set PROBE_QUESTIONS and PROBE_OUT")
        }
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        let questions = (json as? [[String]])?.compactMap(\.first)
            ?? (json as? [[String: String]])?.compactMap { $0["q"] } ?? []
        guard !questions.isEmpty else { return XCTFail("\(input) holds no questions this harness can read") }
        var rows: [[String: String]] = []
        for question in questions {
            let model = await ModelRouter().route(question, within: served)
            // The tiers as the app runs them: the wording tier and the manual fallback are not this
            // probe's subject, so a model that answers nothing is recorded as such.
            let read = model.map { TieredRouter.read(question, $0) }
            rows.append(["q": question, "surface": read?.categoryID ?? "nil",
                         "unmeasured": "\(read?.unmeasured ?? false)",
                         "model": model.map { $0.reading == .search ? "search" : "not" } ?? "nil",
                         "reading": read.map { "\($0.reading)" } ?? "nil"])
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
