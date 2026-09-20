//  Scores.swift — a score says what it is out of, or it is not printed as a score. M13-W4.
//
//  REQ-CMP-004, the council's C1 ruling (M13 plan §7): `Score 83.5 / 100` where the metric has a real
//  ceiling, `Score 1504.2 Elo` where the scale is unbounded but carries a name a reader can look up,
//  and a RANK alone for ECI, whose scale publishes neither a ceiling nor a unit anyone can hold.
//
//  The owner asked for one "Score" (owner, translated from Turkish). Taken literally that prints
//  `Score 161.7` beside `Score 83.5`, and invites a comparison between two numbers on unrelated
//  scales — which D-105 forbids the engine from making and which the screen would then make for it.
//  The five-seat council refused the literal form 4–1 and every one of its seats endorsed the
//  intent; this is the intent.

import Foundation

/// How a metric's number may be shown.
public enum ScoreForm: Equatable {
    /// A share of a fixed whole: the number has a real ceiling of 100.
    case bounded
    /// An unbounded rating with a name a reader can look up.
    case namedScale(String)
    /// Neither a ceiling nor a readable unit: only the rank is honest.
    case rankOnly
    /// A metric this build does not know. The number keeps the engine's own label, as before.
    case unknown
}

/// Keyed on the METRIC the engine advertises, like `scaleExplanation`: two surfaces share `elo` and
/// three share `% correct`, and a tenth surface on an existing scale needs no edit here.
public func scoreForm(for metric: String) -> ScoreForm {
    switch metric.lowercased() {
    case "% resolved", "% correct": return .bounded
    case "elo": return .namedScale("Elo")
    case "eci": return .rankOnly
    default: return .unknown
    }
}

/// The score as a card or a row prints it, or `nil` where only the rank may be shown.
///
/// `nil` also for a number the form cannot hold: a "percentage" above 100 has no honest rendering
/// against a ceiling of 100, and a number that does not fit the scale did not come from a working
/// engine. The rank beside it still says where the model sits.
public func scoreText(
    _ score: Double, metric: String, _ language: Language, anchor: Double? = nil
) -> String? {
    guard let value = number(score) else { return nil }
    let word = language == .turkish ? "Puan" : "Score"
    switch scoreForm(for: metric) {
    case .bounded:
        guard score <= 100 else { return nil }
        return "\(word) \(value) / 100"
    case let .namedScale(name):
        // D-143 (M14-W4): one scale for the reader, out of 100, when the engine publishes the
        // surface's anchor. An engine older than W4 sends none, and the named scale stays.
        if let converted = scoreOutOf100(score, metric: metric, anchor: anchor),
           let shown = number(converted)
        {
            return "\(word) \(shown) / 100"
        }
        return "\(word) \(value) \(name)"
    case .rankOnly:
        return nil
    case .unknown:
        return "\(value) \(localisedUnit(metric, in: language))"
    }
}

/// `$10/1M`: the exact price, beside whatever the score line says. Never localised, for the reason
/// `Format` in `ContentView` gave: `$2,06` reads as two thousand and six outside a comma-decimal
/// locale, beside a `$` that is unambiguously not local currency.
///
/// **Never `$0/1M` for a price that is not zero (M13-W4 review MINOR-4).** Three decimals round
/// anything under $0.0005/1M to `$0`, which is the defect this wave fixed on the page line, moved to
/// the tag. Below the last digit the tag says so. Zero and `-0.0` read `—`, as `priceInPages` reads
/// them "price unavailable": two lines on one card must not disagree about whether a price exists.
public func priceTag(_ blendedPerM: Double) -> String {
    guard blendedPerM.isFinite, blendedPerM > 0 else { return "—" }
    guard blendedPerM >= 0.001 else { return "<$0.001/1M" }
    let formatter = NumberFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.numberStyle = .decimal
    formatter.usesGroupingSeparator = false
    formatter.maximumFractionDigits = 3
    return "$\(formatter.string(from: NSNumber(value: blendedPerM)) ?? "\(blendedPerM)")/1M"
}

/// The figures line of a card or a row: the score where one may be shown, and always the price.
///
/// `ranked` says whether the caller shows a rank beside it, and it has no default on purpose. C1
/// replaced ECI's number WITH its rank; a card that has no rank to show would then place the model
/// nowhere at all (M13-W4 review MINOR-8). Without a rank, a rank-only metric keeps the engine's own
/// number and label, the form it had before D-140.
public func figuresLine(
    score: Double, metric: String, blendedPerM: Double, _ language: Language, ranked: Bool,
    anchor: Double? = nil
) -> String {
    var shown = scoreText(score, metric: metric, language, anchor: anchor)
    if shown == nil, !ranked, scoreForm(for: metric) == .rankOnly, let value = number(score) {
        shown = "\(value) \(localisedUnit(metric, in: language))"
    }
    return [shown, priceTag(blendedPerM)].compactMap { $0 }.joined(separator: "  ·  ")
}
