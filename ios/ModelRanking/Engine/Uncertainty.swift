//  Uncertainty.swift — say only what the engine's own numbers support. M13-W2.
//
//  REQ-UNC-001 and REQ-UNC-002, measured on the shipping artifact before a line of this was written:
//  on `expert`, 25 of the 50 ranked models sit inside the engine's own margin of the leader, and on
//  `mathematics` 28 of 51. The screen printed `#2 of 50` for a model the engine itself calls
//  indistinguishable from the first. And the one second benchmark behind a coding pick last ran more
//  than 300 days before the artifact was built, which nothing on screen said.
//
//  The margin is the engine's (`close_call_margin`, D-138), the order is the engine's (the client
//  never re-sorts, Trap 1), and the age is the engine's (`secondary_age_days`).
//
//  **This file subtracts served scores, which is REQ-APP-005's subject, and D-138 permits it by
//  name.** A range is the result of comparing two served scores against the engine's own threshold;
//  it never prints a new number. `test_ios_client_contract.py` names this file, with D-138, as the
//  one place allowed to do arithmetic on a served score; a second file doing it fails the gate.

import Foundation

/// The positions a model could hold, given a margin the engine cannot see inside. REQ-UNC-001.
///
/// `best` counts the models CLEARLY ahead of it, plus one; `worst` is the total less the models
/// clearly behind it. "Clearly" means further apart than the margin.
public struct RankRange: Equatable {
    public let best: Int
    public let worst: Int

    public init(best: Int, worst: Int) {
        self.best = best
        self.worst = worst
    }

    public var isExact: Bool { best == worst }
}

/// How far apart two SERVED scores can be while their raw scores are still inside the margin.
///
/// The engine rounds every score to one decimal at its output boundary (D-109), so each served
/// score is within 0.05 of the raw one and a served GAP is within 0.1 of the raw gap. The engine
/// decides a close call on raw scores (`recommend.py`: `gap <= close_pts`).
let servedResolution = 0.1

/// Binary floating point, and NOT a widening: `94.4 - 89.3` is `5.1000000000000085` in a `Double`.
let floatTolerance = 1e-9

/// Every model's position as a RANGE, in the engine's order. The owner's ruling, 2026-09-15.
///
/// **Why ranges and not bands.** The council's D1 ruling grouped the ranking into greedy bands
/// anchored at the top. The M13-W2 review measured what that costs on the shipping artifact: 47
/// adjacent pairs that sit inside the margin were printed in different bands (`=2` beside `=5`, 0.6
/// points apart), which is the ordering REQ-UNC-001 forbids. No single rank number can avoid that,
/// because "within the margin" is not transitive. A range can. Take two models inside the margin of
/// each other: the models clearly ahead of the lower one and the models clearly behind the upper one
/// are disjoint sets, and neither contains the upper one, so together they number at most n − 1 —
/// which is exactly `best(lower) ≤ worst(upper)`. `UncertaintyTests` asserts that overlap as a
/// property over every shipping margin rather than relying on this paragraph.
///
/// **The rounding direction is chosen so REQ-UNC-001 cannot be broken by rounding.** Two models are
/// treated as separable only when their served scores differ by more than `margin + 0.1`, because
/// only then can their raw scores not sit inside the margin. The cost is paid in the other direction:
/// a pair whose raw gap is between the margin and the margin plus 0.2 may be shown as overlapping
/// when the engine's raw comparison would separate it. Overstating the uncertainty by one rounding
/// step is the error this criterion allows; overstating the ORDER is the one it exists to prevent.
///
/// No margin, or one that is not a usable non-negative number, gives every model its exact position:
/// an engine older than D-138 renders exactly as it did.
public func rankRanges(_ scores: [Double], margin: Double?) -> [RankRange] {
    guard let margin, margin.isFinite, margin >= 0 else {
        return scores.indices.map { RankRange(best: $0 + 1, worst: $0 + 1) }
    }
    let separable = margin + servedResolution + floatTolerance
    return scores.indices.map { index in
        let score = scores[index]
        guard score.isFinite else { return RankRange(best: index + 1, worst: index + 1) }
        var ahead = 0
        var behind = 0
        for other in scores where other.isFinite {
            if other - score > separable {
                ahead += 1
            } else if score - other > separable {
                behind += 1
            }
        }
        return RankRange(best: ahead + 1, worst: scores.count - behind)
    }
}

/// `#5–13 of 44`, or `#1 of 44` where the position is exact.
public func rankLabel(at index: Int, in ranges: [RankRange], of total: Int, _ language: Language)
    -> String?
{
    guard let span = shortRankLabel(at: index, in: ranges) else { return nil }
    switch language {
    case .english: return "#\(span) of \(total)"
    case .turkish: return "\(total) model içinde #\(span)"
    }
}

/// The same position for a row in a list: `5–13`, `1`.
public func shortRankLabel(at index: Int, in ranges: [RankRange]) -> String? {
    guard ranges.indices.contains(index) else { return nil }
    let range = ranges[index]
    return range.isExact ? "\(range.best)" : "\(range.best)–\(range.worst)"
}

/// How many models the benchmark cannot separate from the leader, stated ONCE per ranking.
///
/// `nil` when the leader stands alone. It is shown on the full ranking, where the ranges appear in
/// bulk, and not on the home screen: there the engine's own `close_call` sentence already says the
/// runner-up is inside the margin, and D-135 says a fact is stated once.
///
/// It names the benchmark's MARGIN rather than claiming a gap, because the count includes the one
/// rounding step `rankRanges` concedes. And it says "cannot separate" rather than "margin of error":
/// on boards that publish no standard error the margin is the median gap between neighbours, which
/// is a resolution, not an error bar.
public func leaderSentence(
    ranges: [RankRange], margin: Double?, metric: String, _ language: Language
) -> String? {
    let tied = ranges.filter { $0.best == 1 }.count
    guard tied > 1, let margin, let amount = number(margin) else { return nil }
    let unit = marginUnit(for: metric, singular: amount == "1", language)
    switch language {
    case .english:
        return "The top \(tied) of \(ranges.count) are too close to the leader for this benchmark "
            + "to separate — its margin is \(amount) \(unit) — so read them as tied, not as ordered."
    case .turkish:
        return "\(ranges.count) modelin ilk \(tied) tanesi lidere bu benchmark'ın ayırt "
            + "edemeyeceği kadar yakın — payı \(amount) \(unit) — yani sıralı değil berabere okuyun."
    }
}

/// The unit a MARGIN is counted in, which is not always the unit a score is printed in.
///
/// A percentage board's margin is a distance in points: `5 % correct` reads as a score, not as a
/// gap. Keyed on the metric, like `scaleExplanation`, so a tenth surface on an existing scale needs
/// no edit here. `singular` exists because `abstract`'s margin is 1.0 and "1 points" shipped in the
/// first draft of this file.
func marginUnit(for metric: String, singular: Bool, _ language: Language) -> String {
    switch metric.lowercased() {
    case "% resolved", "% correct":
        if language == .turkish { return "puan" }
        return singular ? "point" : "points"
    case "elo": return "Elo"
    case "eci": return "ECI"
    default: return localisedUnit(metric, in: language)
    }
}

// MARK: - How many benchmarks measured a pick (REQ-UNC-002)

/// The evidence line under a pick: the composed count where the engine's verdict is one this build
/// knows, the engine's own `confidence_basis` where it is not, and NOTHING where the payload
/// contradicts itself.
///
/// The last case is the M13-W2 review's MINOR-3. The first version fell back to the basis whenever
/// the composer returned `nil`, so a "High" with no second score printed "two independent
/// benchmarks": the contradiction, repeated as a fact.
public func evidenceLine(
    verdict: String,
    basis: String,
    secondaryScore: Double?,
    secondaryBenchmark: String?,
    secondaryAgeDays: Int?,
    evidenceDate: String?,
    _ language: Language
) -> String? {
    switch verdict {
    case "High", "Medium":
        return evidenceBreadth(
            verdict: verdict, secondaryScore: secondaryScore,
            secondaryBenchmark: secondaryBenchmark, secondaryAgeDays: secondaryAgeDays,
            evidenceDate: evidenceDate, language
        )
    default:
        return basis.isEmpty ? nil : basis
    }
}

/// How many benchmarks measured a pick, and how old each of them is.
///
/// **This replaces nothing on screen, and that is the finding.** The payload has carried
/// `confidence` since M2 and the client never rendered it, so neither the word nor what it stood for
/// ever reached a reader. What it stands for is a COUNT: the engine answers "High" exactly when a
/// second, current benchmark scored the model (`recommend.confidence_of`), which is coverage wearing
/// a statistics word. This says the count in words a reader can check, and never says "confidence".
///
/// **It reads the engine's verdict rather than re-deriving it.** The engine counts a second board
/// only if it is at most 90 days old (`STALE_NOTICE_DAYS`). Repeating that threshold here would be a
/// second definition of "current" on the other side of a network.
///
/// The ages it states: the primary's run date in parentheses, and the second board's age in days.
/// Those are the two boards' ages, and the older of them is whichever is older; this does not pick
/// one, because the reader can compare a date and a day count and the code would only be guessing
/// at which they care about.
///
/// `nil` for a verdict this build does not know or a payload that contradicts itself ("High" with no
/// second score). `evidenceLine` decides what the screen shows instead.
public func evidenceBreadth(
    verdict: String,
    secondaryScore: Double?,
    secondaryBenchmark: String?,
    secondaryAgeDays: Int?,
    evidenceDate: String?,
    _ language: Language
) -> String? {
    let counted: Int
    switch verdict {
    case "High": counted = 2
    case "Medium": counted = 1
    default: return nil
    }
    if counted == 2, secondaryScore == nil { return nil }

    var sentence: String
    switch (counted, language) {
    case (1, .english): sentence = "Measured on 1 benchmark"
    case (1, .turkish): sentence = "1 benchmark ile ölçüldü"
    case (_, .english): sentence = "Measured on 2 independent benchmarks"
    case (_, .turkish): sentence = "2 bağımsız benchmark ile ölçüldü"
    }
    if let date = isoDate(evidenceDate) {
        sentence += language == .english ? " (run \(date))" : " (\(date) tarihli)"
    }
    sentence += "."

    // The second board is named only for a pick it actually SCORED. The board is a property of the
    // surface and arrives for every pick; a pick it never measured must not be told it did.
    // A name enters the sentence only through `label`, which refuses anything that could itself be
    // a sentence.
    guard secondaryScore != nil, let board = label(secondaryBenchmark) else { return sentence }
    // A negative age is a run dated in the future, and an astronomical one did not come from a
    // working engine; both are "no usable age".
    let age = secondaryAgeDays.flatMap { (0...100_000).contains($0) ? $0 : nil }

    if counted == 2 {
        guard let days = age else { return sentence }
        return sentence + (language == .english
            ? " \(board) last ran \(days) days ago."
            : " \(board) en son \(days) gün önce çalıştırıldı.")
    }
    // A `nil` age means the board is undated OR the artifact could not be read when the surfaces
    // were fetched (D-138). The sentence claims only what both share: the age is not available. The
    // first version said "publishes no run dates", which is false about Aider in the second case.
    switch (age, language) {
    case let (days?, .english):
        return sentence + " \(board) also scored it, but last ran \(days) days ago, so it is not counted."
    case let (days?, .turkish):
        return sentence + " Ayrıca \(board) sonucu var, ama en son \(days) gün önce çalıştırılmış; "
            + "bu yüzden sayılmıyor."
    case (nil, .english):
        return sentence + " \(board) also scored it, but its run dates are not available, so it is "
            + "not counted."
    case (nil, .turkish):
        return sentence + " Ayrıca \(board) sonucu var, ama çalıştırma tarihleri elimizde değil; "
            + "bu yüzden sayılmıyor."
    }
}

/// `2026-04-20`, or `nil`. A string is printed as a date only if it is one: ISO shape, a real month,
/// a day that month can have.
func isoDate(_ value: String?) -> String? {
    guard let value, value.count >= 10 else { return nil }
    let day = String(value.prefix(10))
    let parts = day.split(separator: "-", omittingEmptySubsequences: false)
    guard parts.count == 3, parts[0].count == 4, parts[1].count == 2, parts[2].count == 2,
          parts.allSatisfy({ $0.allSatisfy { $0.isASCII && $0.isNumber } }),
          let year = Int(parts[0]), let month = Int(parts[1]), let date = Int(parts[2])
    else { return nil }
    var components = DateComponents()
    components.year = year
    components.month = month
    components.day = date
    let calendar = Calendar(identifier: .gregorian)
    guard (1...12).contains(month), date >= 1,
          let first = calendar.date(from: DateComponents(year: year, month: month, day: 1)),
          let days = calendar.range(of: .day, in: .month, for: first),
          days.contains(date)
    else { return nil }
    return day
}
