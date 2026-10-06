//  ReplayProbe.swift — a recorded `ReadingProbe` run, read again by this copy's code (M19-W4).
//
//  A variant that changes only the code after the model (the signals in code, the image rule) does
//  not change what the model answers. Each row of a run records the model's own surface (`routed`),
//  whether it declined (`declined`) and its verdict (`model`); this harness rebuilds that outcome
//  and gives it to `TieredRouter.read`, as the app does. So a code-only variant is scored on the
//  very answers the reference runs drew, exactly. A variant that changes the model's instructions
//  needs fresh runs through `ReadingProbe.swift`. Rows where the model answered nothing stay so.
//
//  Install it beside `ReadingProbe.swift` in a scratch copy's `EngineTests/`, and from the copy:
//
//      PROBE_RUN=/abs/path/run.json PROBE_OUT=/abs/path/out.json swift test --filter ReplayProbe
import XCTest
@testable import ModelRankingEngine

final class ReplayProbe: XCTestCase {
    func testReplay() throws {
        let env = ProcessInfo.processInfo.environment
        guard let input = env["PROBE_RUN"], let output = env["PROBE_OUT"] else {
            return XCTFail("set PROBE_RUN and PROBE_OUT")
        }
        let json = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: input)))
        guard let recorded = json as? [[String: String]], !recorded.isEmpty,
              recorded.allSatisfy({ $0["routed"] != nil && $0["declined"] != nil && $0["model"] != nil })
        else { return XCTFail("\(input) is not a ReadingProbe run with `routed`, `declined` and `model`") }
        // A wording-tier run is not replayed: its manual-tier rows carry no tier answer to rebuild, so a
        // replay would copy the old reading (the M19-W4 review's M3). Run that tier fresh instead.
        guard !recorded.contains(where: { $0["tier"] != nil }) else {
            return XCTFail("\(input) is a wording-tier run; run it fresh with PROBE_TIER=wording, not replayed")
        }
        let rows: [[String: String]] = recorded.map { row in
            let question = row["q"] ?? ""
            guard let routed = row["routed"], routed != "nil" else { return row }
            var model = RoutingOutcome(categoryID: routed, tier: .model, unmeasured: row["declined"] == "true")
            model.reading = row["model"] == "not" ? .unsure : .search
            let read = TieredRouter.read(question, model)
            return ["q": question, "surface": read.categoryID, "routed": routed, "declined": row["declined"] ?? "",
                    "unmeasured": "\(read.unmeasured)", "model": row["model"] ?? "", "reading": "\(read.reading)"]
        }
        try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
            .write(to: URL(fileURLWithPath: output))
    }
}
