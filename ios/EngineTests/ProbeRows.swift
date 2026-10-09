//  ProbeRows.swift — the rows `scripts/router_probe/ReadingProbe.swift` writes and
//  `ReplayProbe.swift` reads back (#193, M21-W2). (A stub in the red commit.)

@testable import ModelRankingEngine

enum ProbeRows {
    /// The model's outcome a recorded row stands for, or `nil` where the model answered nothing.
    static func rebuild(_ row: [String: String]) -> RoutingOutcome? { nil }

    /// A recorded row read again by this copy's code, as `ReplayProbe` writes it.
    static func replay(_ row: [String: String]) -> [String: String] { row }

    /// The row the wording mode writes: the wording tier's own outcome, then the app's reading.
    static func wordingRow(_ question: String, tier: RoutingOutcome?, read: RoutingOutcome) -> [String: String] { [:] }
}
