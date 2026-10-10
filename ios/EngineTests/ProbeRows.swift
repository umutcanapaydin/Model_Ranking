//  ProbeRows.swift -- the rows `scripts/router_probe/ReadingProbe.swift` writes and
//  `ReplayProbe.swift` reads back (#193, M21-W2). Both harnesses call these, and `ProbeRowTests` runs
//  them, so a fault in the rebuild fails a committed test.

import Foundation

@testable import ModelRankingEngine

enum ProbeRows {
    /// The model's outcome a recorded row stands for: its own surface (`routed`), whether it declined,
    /// and its verdict ("not" is its doubt). `nil` where the model answered nothing.
    static func rebuild(_ row: [String: String]) -> RoutingOutcome? {
        guard let routed = row["routed"], routed != "nil" else { return nil }
        var model = RoutingOutcome(categoryID: routed, tier: .model, unmeasured: row["declined"] == "true")
        model.reading = row["model"] == "not" ? .unsure : .search
        return model
    }

    /// A recorded row read again by this copy's code, as `ReplayProbe` writes it. A row the model
    /// answered nothing stays as it was.
    static func replay(_ row: [String: String]) -> [String: String] {
        guard let model = rebuild(row) else { return row }
        let question = row["q"] ?? ""
        let read = TieredRouter.read(question, model)
        return ["q": question, "surface": read.categoryID, "routed": model.categoryID,
                "declined": row["declined"] ?? "", "unmeasured": "\(read.unmeasured)", "model": row["model"] ?? "",
                "reading": "\(read.reading)"]
    }

    /// The row the wording mode writes: the wording tier's own outcome (`tier`, `nil` where it declined),
    /// then the app's reading of the question as a device without the model reads it.
    static func wordingRow(_ question: String, tier: RoutingOutcome?, read: RoutingOutcome) -> [String: String] {
        ["q": question, "surface": read.categoryID, "routed": tier?.categoryID ?? "nil",
         "unmeasured": "\(read.unmeasured)", "model": "nil", "reading": "\(read.reading)",
         "tier": "\(read.tier)", "declined": "\(tier?.unmeasured ?? true)"]
    }
}

/// #226 (M21-W2): one row of the owner's judgement sheet: what the screen shows for a question (our
/// family list's first five, planned by `answerPlan` as the screen plans it) beside the primary board's
/// own first five. `scripts/router_probe/JudgementProbe.swift` writes these; `scripts/judgement_sheet.py`
/// blinds them into the sheet the owner fills in. A question the screen answers with cards has no
/// family list, and the sheet leaves it out.
enum JudgementRows {
    static func row(question: String, outcome: RoutingOutcome, categories: [ModelRankingEngine.Category],
                    standings: Standings, asOf: Date) -> [String: Any] {
        let info = categories.first { $0.id == outcome.categoryID }
        let display = Dictionary(standings.models.map { ($0.id, $0.display) }, uniquingKeysWith: { first, _ in first })
        var row: [String: Any] = ["q": question, "surface": outcome.categoryID, "family": [String](),
                                  "primary": [String](), "boards": [String]()]
        if let primary = info?.primaryBoard, let board = standings.boards.first(where: { $0.id == primary }) {
            var seen = Set<String>()
            let order = board.standings.sorted { $0.position < $1.position }.map(\.model).filter { seen.insert($0).inserted }
            row["primary"] = order.prefix(5).map { display[$0] ?? $0 }
        }
        let plan = answerPlan(outcome: outcome, primaryBoard: info?.primaryBoard, family: info?.boards, question: question,
                              asOf: asOf, standings: standings, removed: [], refinedBoard: info?.refinedBoard)
        if case let .combined(view) = plan {
            row["family"] = view.list.entries.prefix(5).map(\.model.display)
            row["boards"] = view.list.boards.map(\.id)
        }
        return row
    }
}
