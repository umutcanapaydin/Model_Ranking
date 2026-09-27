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
    /// How many models every chosen board ranks (#54): the length of the list, stated on screen.
    var sharedCount: Int { list.entries.count }
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
        list: list, refinements: offered, removed: removed.intersection(offered)
    ))
}
