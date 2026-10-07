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
//  the surface, the model's own surface before the image rule, whether it was declined, the model's
//  own verdict and the app's reading. The model is not deterministic: run every set at least twice.
//  Where the model is not available the test fails, so no file of empty rows is ever scored.
//
//  `PROBE_TIER=wording` reads every question as a device without the model does (M19-W4, #113): the
//  wording tier, then the same signals in code. `routed` is then the wording tier's own surface, and
//  `model` is "nil" on every row. It needs no Apple Intelligence. In both modes `declined` says the
//  tier itself answered "not measured", so a run can tell a decline from the image rule's override.
import XCTest
@testable import ModelRankingEngine

final class ReadingProbe: XCTestCase {
    let served = ["coding", "agentic-coding", "assistant", "everyday", "expert", "mathematics", "computer-use",
                  "abstract", "web-dev", "document", "factuality", "vision", "search", "search_factuality"]

    func testProbe() async throws {
        let env = ProcessInfo.processInfo.environment
        let wording = env["PROBE_TIER"] == "wording"
        if !wording {
            guard #available(macOS 26.0, iOS 26.0, *) else { return XCTFail("no FoundationModels here") }
            guard ModelRouter.state == .available else {
                return XCTFail("the on-device model is not available here: \(ModelRouter.state)")
            }
        }
        guard let input = env["PROBE_QUESTIONS"], let output = env["PROBE_OUT"] else {
            return XCTFail("set PROBE_QUESTIONS and PROBE_OUT")
        }
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        let questions = (json as? [[String]])?.compactMap(\.first)
            ?? (json as? [[String: String]])?.compactMap { $0["q"] } ?? []
        guard !questions.isEmpty else { return XCTFail("\(input) holds no questions this harness can read") }
        var rows: [[String: String]] = []
        for question in questions {
            if wording {
                // As the app runs it with no model: the wording tier, its manual fallback, then the reading.
                let tier = await SimilarityRouter().route(question, within: served)
                let read = await TieredRouter(model: nil).route(question, within: served)
                rows.append(["q": question, "surface": read.categoryID, "routed": tier?.categoryID ?? "nil",
                             "unmeasured": "\(read.unmeasured)", "model": "nil", "reading": "\(read.reading)",
                             "tier": "\(read.tier)", "declined": "\(tier?.unmeasured ?? true)"])
                continue
            }
            guard #available(macOS 26.0, iOS 26.0, *) else { return XCTFail("no FoundationModels here") }
            let model = await ModelRouter().route(question, within: served)
            // The tiers as the app runs them: the wording tier and the manual fallback are not this
            // probe's subject, so a model that answers nothing is recorded as such.
            let read = model.map { TieredRouter.read(question, $0) }
            // `routed` is the model's own surface, before the image rule (the reviews' B4): a run can
            // count each override.
            rows.append(["q": question, "surface": read?.categoryID ?? "nil", "routed": model?.categoryID ?? "nil",
                         "unmeasured": "\(read?.unmeasured ?? false)", "declined": "\(model?.unmeasured ?? false)",
                         "model": model.map { $0.reading == .search ? "search" : "not" } ?? "nil",
                         "reading": read.map { "\($0.reading)" } ?? "nil"])
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
