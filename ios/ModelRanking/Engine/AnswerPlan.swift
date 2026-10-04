//  AnswerPlan.swift — what the screen shows for a routed question (D-168 clause 7, M17-W5).
//
//  One board: today's cards, unchanged. More than one: the product's own combined list, built by
//  `combine` (D-167) from the standings the phone keeps (`StandingsStore`). Decided here, in the
//  Engine layer, so every branch is a function of its inputs and tested without a screen.

import Foundation

/// A combined list ready for the screen.
struct CombinedView: Equatable {
    let list: CombinedList
    /// Every refinement the question chose whose board the standings hold, the removed ones
    /// included, so each can be restored.
    let refinements: [Refinement]
    /// The refinements the reader removed on this device. Removing one sends nothing.
    let removed: Set<Refinement>
    /// Per chosen board that ranks at no one effort, the efforts the listed models stand at on it,
    /// when they differ (D-112): the notice the cards carry, which this list replaces (review B1).
    let mixedEfforts: [BoardEfforts]
    /// Every effort named in `mixedEfforts`, once each, in the order the boards name them.
    var efforts: [String] { firstSeen(mixedEfforts.flatMap(\.efforts)) }
    /// How many models every chosen board ranks (#54): the length of the list, stated on screen.
    var sharedCount: Int { list.entries.count }
}

/// The efforts a board's listed models stand at, when there are two or more (D-112).
struct BoardEfforts: Equatable {
    let board: String
    let efforts: [String]
}

/// What a board's date means. `observed_at` is the day the engine read the board, not a day
/// anything was measured, and the screen says which it shows (review B1).
enum BoardDate: Equatable {
    case measured(String)
    case readOn(String)
    case unknown
}

func boardDate(_ board: BoardStandings) -> BoardDate {
    if let date = board.evidenceDate { return .measured(date) }
    if let read = board.observedAt { return .readOn(String(read.prefix(10))) }
    return .unknown
}

/// A board as the reader knows it: a board a refinement added is named as its chip is, so the two
/// can be matched (review M4); the surface's own board keeps its benchmark's name.
func boardTitle(_ board: BoardStandings, refinements: [Refinement], _ language: Language) -> String {
    guard let refinement = refinements.first(where: { $0.board == board.id }) else { return board.benchmark }
    let family = board.benchmark.split(separator: "(").first
        .map { $0.trimmingCharacters(in: .whitespaces) } ?? board.benchmark
    return "\(family) · \(UIText.refinementName(refinement, language))"
}

/// D-112 as the engine applies it to the cards (`effort_mix_notice`): a board a surface ranks at
/// one named effort compares at it; any other says so when its listed models' efforts differ.
private func mixedEfforts(_ list: CombinedList) -> [BoardEfforts] {
    let listed = Set(list.entries.map(\.model.id))
    return list.boards.compactMap { board in
        guard board.rankingEffort == nil else { return nil }
        // In the board's own order, so the client orders nothing of its own (Ruling A's tripwire),
        // and a model's first row only, as `combine` counts it (security pass S4).
        var counted = Set<String>()
        let rows = board.standings.filter { listed.contains($0.model) && counted.insert($0.model).inserted }
        let efforts = firstSeen(rows.map(\.effort)).filter { !$0.isEmpty }
        return efforts.count > 1 ? BoardEfforts(board: board.id, efforts: efforts) : nil
    }
}

private func firstSeen(_ values: [String]) -> [String] {
    var seen = Set<String>()
    return values.filter { seen.insert($0).inserted }
}

enum AnswerPlan: Equatable {
    case cards
    /// One board because the reader removed every refinement: today's cards, with the removed
    /// refinements still on screen so each can be restored.
    case restorable([Refinement])
    case combined(CombinedView)
}

/// The plan for a question. Anything missing -- no question, an unmeasured one, an engine that
/// names no primary board, standings not yet kept, a primary board they lack -- is today's cards.
/// A refinement whose board the standings lack is left out rather than failing the list.
func answerPlan(
    outcome: RoutingOutcome?, primaryBoard: String?, standings: Standings?, removed: Set<Refinement>
) -> AnswerPlan {
    // A primary board the standings lack needs no check of its own: `combine` refuses an unknown
    // board, and a refusal is today's cards below.
    guard let outcome, !outcome.unmeasured, let primaryBoard, let standings else { return .cards }
    // Only a refinement whose board the standings hold is offered: a chip for a board that is not
    // counted would say it was.
    let offered = outcome.refinements.filter { refinement in
        standings.boards.contains { $0.id == refinement.board }
    }
    let kept = offered.filter { !removed.contains($0) }
    let boards = Refinements.boards(primary: primaryBoard, surface: outcome.categoryID, chosen: kept)
    guard boards.count > 1 else {
        // Every refinement removed: the cards, and the chips that restore them, provided restoring
        // them would combine at all.
        let all = Refinements.boards(primary: primaryBoard, surface: outcome.categoryID, chosen: offered)
        guard kept.isEmpty, all.count > 1, (try? combine(standings, boards: all)) != nil else { return .cards }
        return .restorable(offered)
    }
    guard let list = try? combine(standings, boards: boards) else { return .cards }
    return .combined(CombinedView(
        list: list, refinements: offered, removed: removed.intersection(offered),
        mixedEfforts: mixedEfforts(list)
    ))
}

// MARK: - One card per model (#63 finding 1, M18-W2)

/// The picks one model holds, shown as one card.
struct PickCard: Identifiable {
    /// In the engine's order; the first decides the card's look and opens its detail.
    let picks: [Pick]

    var lead: Pick { picks[0] }
    var id: String { lead.label }
    /// Every label the model earned: `best_quality`, `best_value`, `budget_pick`.
    var labels: [String] { picks.map(\.label) }

    /// The picks whose reason the card says. All of them, but one: the value-window sentence ("the
    /// cheapest model within 6 points of the best") on a card that IS the best, where it contradicts
    /// itself. A warning (`nothing_clears_floor`) is never dropped.
    var reasons: [Pick] {
        let isBest = labels.contains("best_quality")
        return picks.filter { pick in
            !(isBest && pick.label != "best_quality"
              && (pick.whyFactDictionary["reason"] as? String) == PickReason.cheapestWithinWindow.rawValue)
        }
    }
}

/// The engine's picks as cards: one per model, in the engine's order.
///
/// A model is the same row only if name, vendor, score and price all agree. Names alone are not
/// unique (#102), and two rows that agree on all four are one model to any reader.
func pickCards(_ picks: [Pick]) -> [PickCard] {
    var groups: [[Pick]] = []
    for pick in picks {
        if let index = groups.firstIndex(where: { sameRow($0[0], pick) }) {
            groups[index].append(pick)
        } else {
            groups.append([pick])
        }
    }
    return groups.map(PickCard.init)
}

private func sameRow(_ left: Pick, _ right: Pick) -> Bool {
    left.model == right.model && left.vendor == right.vendor && left.score == right.score
        && left.blendedPerM == right.blendedPerM
}
