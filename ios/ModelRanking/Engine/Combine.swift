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
        // #74 (M17-W5 security S2): counting the models above each one was O(n²) per board, and a
        // payload at the size cap froze the screen. The shared positions are sorted once, and each
        // count is a binary search: O(n log n), the same ranks (CombinePropertyTests' oracle).
        let placed = shared.map(\.position)
        let ascending = placed.sorted()
        for standing in shared {
            // Competition ranking among the shared models: one more than those placed above it.
            let rank = 1 + countBelow(standing.position, in: ascending)
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

/// How many of `ascending` are below `position`: the index of its first element not below it.
private func countBelow(_ position: Int, in ascending: [Int]) -> Int {
    var low = 0
    var high = ascending.count
    while low < high {
        let middle = low + (high - low) / 2
        if ascending[middle] < position {
            low = middle + 1
        } else {
            high = middle
        }
    }
    return low
}

// MARK: - D-188 (M20-W2, #210): a family of boards combined into the product's own list

/// One line of a family's combined list: the model, where each board that ranks it put it (in the
/// family's order), and its place; tied models share one.
struct FamilyEntry: Equatable {
    let model: StandingModel
    let positions: [BoardPosition]
    let place: Int
}

/// A family's combined list: the boards that rank anyone (in the family's order), the ones that
/// weigh half, the number of boards a model needed, and the entries in order.
struct FamilyList: Equatable {
    let boards: [BoardStandings]
    let staleBoards: [String]
    let coverage: Int
    let entries: [FamilyEntry]
}

/// How old a board's newest evaluation may be before it weighs half (D-188 clause 4).
let freshForDays = 90

/// Combine a family of boards (D-188 clauses 2 to 4), by position and never by score (D-105):
/// - a board that ranks no model, or that the standings lack, is left out, so it can change nothing;
/// - a model enters when at least half of the remaining boards rank it, rounded up, and at least one
///   (with two boards, either is enough: D-188 clause 2 as the W1 review measured it);
/// - its place is the weighted mean of its percentile positions, (position - 1) / (size - 1), over
///   the boards that rank it; a board older than `freshForDays`, or undated, weighs half;
/// - equal means share a place, and the order breaks them by model id (#44).
func combineFamily(_ standings: Standings, boards family: [String], asOf today: Date) throws -> FamilyList {
    var seen = Set<String>()
    let ids = family.filter { seen.insert($0).inserted }
    guard !ids.isEmpty else { throw CombineError.noBoards }
    // A family board the standings lack (an outage, a source left out) is left out, as a board that
    // ranks no model is: neither can empty the list or raise the coverage (the W1 review's R1).
    let boards = ids.compactMap { id in standings.boards.first(where: { $0.id == id }) }
        .filter { !$0.standings.isEmpty }
    guard !boards.isEmpty else { throw CombineError.noBoards }
    let models = Dictionary(standings.models.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    let stale = boards.filter { isStale($0, asOf: today) }.map(\.id)
    let coverage = max(1, (boards.count + 1) / 2)

    // Per model: the weighted sum of percentile positions, the sum of weights, and the positions.
    var weighted: [String: Double] = [:]
    var weights: [String: Double] = [:]
    var positions: [String: [BoardPosition]] = [:]
    for board in boards {
        let weight = stale.contains(board.id) ? 0.5 : 1.0
        let span = Double(max(board.standings.count - 1, 1))
        var listed = Set<String>()
        for standing in board.standings where listed.insert(standing.model).inserted {
            let percentile = Double(min(max(standing.position - 1, 0), board.standings.count - 1)) / span
            weighted[standing.model, default: 0] += weight * percentile
            weights[standing.model, default: 0] += weight
            positions[standing.model, default: []].append(BoardPosition(board: board.id, position: standing.position))
        }
    }
    // A mean is compared to nine places, so two equal means computed in different orders stay equal.
    var means: [String: Int] = [:]
    for (model, list) in positions where list.count >= coverage {
        means[model] = Int(((weighted[model] ?? 0) / (weights[model] ?? 1) * 1_000_000_000).rounded())
    }
    let order = means.keys.sorted { lhs, rhs in
        let (left, right) = (means[lhs, default: 0], means[rhs, default: 0])
        return left == right ? lhs < rhs : left < right
    }
    var entries: [FamilyEntry] = []
    for (index, id) in order.enumerated() {
        guard let model = models[id] else { throw CombineError.unknownModel(id) }
        let tied = index > 0 && means[order[index - 1], default: 0] == means[id, default: 0]
        let place = tied ? entries[index - 1].place : index + 1
        entries.append(FamilyEntry(model: model, positions: positions[id, default: []], place: place))
    }
    return FamilyList(boards: boards, staleBoards: stale, coverage: coverage, entries: entries)
}

/// Whether a board's newest evaluation is older than `freshForDays` on `today`, or unknown.
private func isStale(_ board: BoardStandings, asOf today: Date) -> Bool {
    guard let date = board.evidenceDate, let evaluated = evidenceDay.date(from: String(date.prefix(10))) else {
        return true
    }
    return today.timeIntervalSince(evaluated) > Double(freshForDays) * 86_400
}

private let evidenceDay: DateFormatter = {
    let formatter = DateFormatter()
    formatter.calendar = Calendar(identifier: .gregorian)
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.timeZone = TimeZone(identifier: "UTC")
    formatter.dateFormat = "yyyy-MM-dd"
    return formatter
}()
