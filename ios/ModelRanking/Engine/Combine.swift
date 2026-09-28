//  Combine.swift — the product's own list: chosen boards combined by position (D-160, D-167).
//
//  The one file D-160 clause 2 lets do arithmetic on positions, beside `Uncertainty.swift` for
//  scores (D-138). The standings it reads carry no score at all (D-167 clause 2), so nothing here
//  can average two scales (D-105).
//
//  The rule, as the owner ruled it (D-167 clause 3):
//  - only models EVERY chosen board ranks are combined; nothing is guessed for a missing one;
//  - on each board those models are re-ranked among themselves, tied models sharing a rank;
//  - the list is ordered by the sum of a model's ranks, which orders exactly as their mean does,
//    because every model has one rank per chosen board -- and stays in whole numbers;
//  - an equal sum is broken by model id, never by a display name (#44);
//  - a model's PLACE is one more than the models with a lower sum, so tied models share one: the
//    order breaks a tie, the place on screen does not (code review M1, owner ruling 2026-09-28).

import Foundation

/// A model's position on one chosen board, as that board published it.
struct BoardPosition: Equatable {
    let board: String
    let position: Int
}

/// One line of a combined list: the model, and where each chosen board put it.
struct CombinedEntry: Equatable {
    let model: StandingModel
    /// In the order the boards were chosen, one per board.
    let positions: [BoardPosition]
    /// Its place in the combined list; tied models share one (1, 1, 3).
    let place: Int
}

/// A combined list and the boards it came from, with their dates and attributions for the detail
/// screen (D-160 clause 3).
struct CombinedList: Equatable {
    let boards: [BoardStandings]
    let entries: [CombinedEntry]
}

enum CombineError: Error, Equatable {
    case noBoards
    case unknownBoard(String)
    case unknownModel(String)
}

/// Combine `chosen` boards of `standings`. A board chosen twice counts once.
func combine(_ standings: Standings, boards chosen: [String]) throws -> CombinedList {
    var seen = Set<String>()
    let ids = chosen.filter { seen.insert($0).inserted }
    guard !ids.isEmpty else { throw CombineError.noBoards }
    let boards = try ids.map { id -> BoardStandings in
        guard let board = standings.boards.first(where: { $0.id == id }) else {
            throw CombineError.unknownBoard(id)
        }
        return board
    }
    let models = Dictionary(standings.models.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })

    var common = Set(boards[0].standings.map(\.model))
    for board in boards.dropFirst() {
        common.formIntersection(board.standings.map(\.model))
    }

    var sums: [String: Int] = [:]
    var positions: [String: [BoardPosition]] = [:]
    for board in boards {
        // A model listed twice on one board (only a bad payload could) counts once (security S7).
        var listed = Set<String>()
        let shared = board.standings.filter { common.contains($0.model) && listed.insert($0.model).inserted }
        for standing in shared {
            // Competition ranking among the shared models: one more than those placed above it.
            let rank = 1 + shared.filter { $0.position < standing.position }.count
            sums[standing.model, default: 0] = sums[standing.model, default: 0] + rank
            positions[standing.model, default: []].append(
                BoardPosition(board: board.id, position: standing.position)
            )
        }
    }

    let order = common.sorted { lhs, rhs in
        let (left, right) = (sums[lhs, default: 0], sums[rhs, default: 0])
        return left == right ? lhs < rhs : left < right
    }
    var entries: [CombinedEntry] = []
    for (index, id) in order.enumerated() {
        guard let model = models[id] else { throw CombineError.unknownModel(id) }
        let tied = index > 0 && sums[order[index - 1], default: 0] == sums[id, default: 0]
        let place = tied ? entries[index - 1].place : index + 1
        entries.append(CombinedEntry(model: model, positions: positions[id, default: []], place: place))
    }
    return CombinedList(boards: boards, entries: entries)
}
