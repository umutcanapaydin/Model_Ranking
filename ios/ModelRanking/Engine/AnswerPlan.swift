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
    /// #72 (M18-W2): the surface's own board's health, from its answer's `source_health`.
    var staleness: SourceHealth? = nil
    /// #72's other half (review M3): whole days the phone's copy of the standings is past its day.
    var phoneCopyDays: Int? = nil

    /// Everything this list must say, as data (#67, M18-W2 P4): the view renders exactly these, and
    /// a test on the plan holds them, so a branch of the view cannot quietly skip one. Loudest first.
    var disclosures: [CombinedDisclosure] {
        var out: [CombinedDisclosure] = []
        if let staleness, staleness.stale { out.append(.staleBoard(staleness)) }
        if let phoneCopyDays { out.append(.stalePhoneCopy(days: phoneCopyDays)) }
        out.append(.productsOwnOrder(models: sharedCount, boards: list.boards.count))
        if Set(list.entries.map(\.place)).count < list.entries.count { out.append(.tiedPlaces) }
        if !efforts.isEmpty { out.append(.mixedEfforts(efforts)) }
        return out
    }
}

/// One fact the combined list owes its reader (REQ-APP-003 on the combined path).
enum CombinedDisclosure: Equatable {
    /// #72: the surface's own board is stale, as its cards would have said.
    case staleBoard(SourceHealth)
    /// #72, review M3: the standings this list combines were kept on the phone past their day,
    /// because a newer copy could not be fetched.
    case stalePhoneCopy(days: Int)
    /// D-160 clause 3: the order is the product's own; how many models, on how many boards (#54).
    case productsOwnOrder(models: Int, boards: Int)
    /// Some places are shared (1, 1, 3).
    case tiedPlaces
    /// D-112: the listed models were measured at different efforts (review B1).
    case mixedEfforts([String])
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
    outcome: RoutingOutcome?, primaryBoard: String?, standings: Standings?, removed: Set<Refinement>,
    primaryHealth: SourceHealth? = nil, phoneCopyDays: Int? = nil
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
        mixedEfforts: mixedEfforts(list), staleness: primaryHealth, phoneCopyDays: phoneCopyDays
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
/// One model is one card, by the id the engine sends with each pick (D-182, #138): names are not
/// unique (#102), and two models can share a name, a vendor, a score and a price. An engine older
/// than D-182 sends no id, and then a model is the same row only if all four agree (`sameRow`).
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

/// D-182 (#138): one model is one card, by the id the engine sends; an engine older than D-182 sends
/// none, and then the four shown values decide, as they did.
private func sameRow(_ left: Pick, _ right: Pick) -> Bool {
    if let leftID = left.modelId, let rightID = right.modelId {
        return leftID == rightID
    }
    return left.model == right.model && left.vendor == right.vendor && left.score == right.score
        && left.blendedPerM == right.blendedPerM
}

// MARK: - The combined list's length (M18-W2, #63 new finding A)

/// How many rows of the combined list show before the reader asks for the rest. Ten: the answer is
/// at the top, and 160 rows put everything below the list, "See the boards" included, out of reach.
let combinedVisibleRows = 10

func visibleCount(total: Int, expanded: Bool) -> Int {
    expanded ? total : min(total, combinedVisibleRows)
}

// MARK: - The plan, computed when its inputs change (#70, M18-W2)

/// `answerPlan`, and with it `combine`, ran in the screen's `body`, so every render paid for it,
/// every keystroke in the question field included. The memo plans once per change of what the plan
/// reads; a render with the same inputs gets the plan it already has.
final class PlanMemo {
    /// What a plan reads. The standings are named by a stamp the screen bumps when it replaces them,
    /// so comparing inputs never compares a 4 MiB payload.
    struct Inputs: Equatable {
        let outcome: RoutingOutcome?
        let primaryBoard: String?
        let standingsStamp: Int
        let removed: Set<Refinement>
        let primaryHealth: SourceHealth?
        var phoneCopyDays: Int? = nil
    }

    private var last: (inputs: Inputs, plan: AnswerPlan)?
    /// How many plans were computed: what the tests count.
    private(set) var computed = 0

    func plan(_ inputs: Inputs, standings: Standings?) -> AnswerPlan {
        if let last, last.inputs == inputs { return last.plan }
        computed += 1
        let plan = answerPlan(outcome: inputs.outcome, primaryBoard: inputs.primaryBoard, standings: standings,
                              removed: inputs.removed, primaryHealth: inputs.primaryHealth,
                              phoneCopyDays: inputs.phoneCopyDays)
        last = (inputs, plan)
        return plan
    }
}

// MARK: - The reader's access filter (#78, M18-W2)

/// Whether a model's served accessibility (Epoch's `model_metadata.csv`, M17-W3) says it has an API
/// or open weights. An unpublished value, or one this build does not know, is not claimed.
func hasAPIOrOpenWeights(_ accessibility: String?) -> Bool {
    guard let accessibility else { return false }
    return accessibility == "API access" || accessibility.hasPrefix("Open weights")
}

/// The combined list's rows with the filter applied. Each keeps its place among all the shared
/// models: the filter hides rows, it does not re-rank them (D-167).
func filteredEntries(_ entries: [CombinedEntry], onlyAPIOrOpenWeights: Bool) -> [CombinedEntry] {
    onlyAPIOrOpenWeights ? entries.filter { hasAPIOrOpenWeights($0.model.accessibility) } : entries
}

/// The routed surface's own health, from the answers on screen: what the plan's stale-board
/// disclosure reads (#72). A function, so a test drives the lookup the view makes (review M4).
func routedSurfaceHealth(_ answers: [Answer], _ outcome: RoutingOutcome?) -> SourceHealth? {
    guard let outcome else { return nil }
    return answers.first { $0.surface == outcome.categoryID }?.sourceHealth
}
