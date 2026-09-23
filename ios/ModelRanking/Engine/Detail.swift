//  Detail.swift — where the unit a reader lost on the card comes back. M15-W2.
//
//  REQ-DTL-001/002. D-143 took the metric's name off every card and row on the owner's ruling:
//  "the end user should not have to know how the ranking and the scoring are done, or what the unit
//  is." The plan's mitigation was one line — "it stays available on the detail screen" — and the
//  M14 closure seat found the screen did not exist (W-105). A reader who wants to check the number
//  had nowhere to go, which is the opposite of what this product is for.
//
//  **Every fact here is SERVED, never computed.** `Uncertainty.swift` is the one file allowed
//  arithmetic on a score (D-138) and the two conversions below go through it. Nothing on this
//  screen is derived from anything except what `/v1` already sends: no averages, no per-surface
//  comparison, no "how good is this really" verdict. The screen answers one question — where does
//  this number come from — and refuses to answer any other.
//
//  A fact this build cannot state HONESTLY is left out rather than rendered empty, the rule every
//  composer in `Language.swift` follows: a row reading "Measured: —" tells a reader the measurement
//  is missing, which is a claim, and usually a false one.

import Foundation

/// One line of the detail screen: what it is, what it says, and (sometimes) what that means.
public struct DetailFact: Equatable, Identifiable {
    public let label: String
    public let value: String
    /// The sentence under the value. `nil` where the value speaks for itself.
    public let note: String?

    public var id: String { label }

    public init(label: String, value: String, note: String? = nil) {
        self.label = label
        self.value = value
        self.note = note
    }
}

/// The detail lines for one model on one surface, in the reader's language.
///
/// - Parameters:
///   - model: the served row — a pick and a ranking row carry the same fields, so both open this.
///   - benchmark: the surface's primary board, from the answer (never guessed from the metric).
///   - anchor: the surface's `score_anchor` (its floor, D-162), so the out-of-100 line here agrees with the card.
///   - closeCallMargin: the engine's own tie margin, stated on the board's own scale.
///   - secondaryBenchmark / secondaryAgeDays: the evidence-only second board (REQ-UNC-002, D-139).
///   - minQuality: the surface's floor, `/v1/categories` `min_quality` (D-152, REQ-FLR-002).
///   - priceExcludes: what the surface's price leaves out, `price_excludes` (D-153, REQ-PRC-002).
public func detailFacts(
    model: DetailSubject,
    benchmark: String,
    anchor: Double?,
    closeCallMargin: Double?,
    secondaryBenchmark: String?,
    secondaryAgeDays: Int?,
    minQuality: Double? = nil,
    priceExcludes: String? = nil,
    in language: Language
) -> [DetailFact] {
    var facts: [DetailFact] = []

    // 1. The number the card showed, with what it means underneath. Same call as the card's, so
    //    the two screens cannot disagree about a score (the M13 defect class: two accounts of one
    //    number, computed in two places).
    if let shown = scoreText(model.score, metric: model.metric, language, anchor: anchor) {
        facts.append(
            DetailFact(
                label: language == .turkish ? "Puan" : "Score",
                value: shown,
                note: anchoredScaleExplanation(
                    for: model.metric, anchored: anchor != nil, in: language
                ) ?? scaleExplanation(for: model.metric, in: language)
            )
        )
    }

    // 2. **The unit, returned.** This is the line REQ-DTL-002 exists for: the engine's own number
    //    on the board's own scale, named. It appears ONLY when the card converted or hid it --
    //    printing `1507.6 Elo` under a card that already says `1507.6 Elo` is noise.
    let cardConverted = scoreText(model.score, metric: model.metric, language)
        != scoreText(model.score, metric: model.metric, language, anchor: anchor)
    let cardShowsNoScore = scoreForm(for: model.metric) == .rankOnly
    if let native = number(model.score), cardConverted || cardShowsNoScore {
        facts.append(
            DetailFact(
                label: language == .turkish ? "Ölçülen değer" : "Measured value",
                value: "\(native) \(scoreUnit(for: model.metric, in: language))",
                note: language == .turkish
                    ? "\(benchmark) üzerinde, o listenin kendi ölçeğinde"
                    : "on \(benchmark), on that board's own scale"
            )
        )
    }

    // 3. Where it was measured, and when. An undated board is NAMED as undated (REQ-UNC-003):
    //    "recently" would be this client inventing a date the engine refused to state.
    // Review M-6: guarded, because `Measured on:` with nothing after it tells a reader the
    // measurement is missing -- a claim, and a false one. The file's own rule, now enforced.
    if !benchmark.trimmingCharacters(in: .whitespaces).isEmpty {
    facts.append(
        DetailFact(
            label: language == .turkish ? "Ölçüm" : "Measured on",
            value: benchmark,
            // **`run`, not `published`** (review M-1): `/v1` sends the date the board was RUN, and
            // the card says exactly that (`Uncertainty.swift`'s evidence line). Two words for one
            // served field is two accounts of it, and the stronger word is the wrong one.
            //
            // Through `isoDate`, like the card, because a date string this build cannot read must
            // fall through to the undated notice rather than be printed. `evidence_date: "unknown"`
            // rendered "result published unknown" and took the dated branch: the `number(_:)`
            // lesson (`Language.swift`), applied to dates.
            note: isoDate(model.evidenceDate).map {
                language == .turkish ? "\($0) tarihinde çalıştı" : "run on \($0)"
            } ?? (language == .turkish
                ? "bu liste sonuçlarını tarihlendirmiyor"
                : "this board does not date its results")
        )
    )
    }

    // 4. How this board was run, when the engine says so. `effort` is the comparability axis M5
    //    was spent on: two scores from different effort levels are not the same measurement.
    if !model.harness.isEmpty {
        // Review N-2: the harness alone is still a fact. Dropping it because the engine sent no
        // effort showed the reader neither, and the harness is half of what M5 was spent on.
        facts.append(
            DetailFact(
                label: language == .turkish ? "Çalıştırma" : "Run at",
                value: model.effort.map { "\(model.harness) · \($0)" } ?? model.harness,
                note: model.effort == nil
                    ? (language == .turkish
                        ? "bu liste tek bir seviyede çalışır"
                        : "this board runs at one level")
                    : (language == .turkish
                        ? "aynı listede farklı seviyeler karşılaştırılabilir değildir"
                        : "levels on one board are not comparable with each other")
            )
        )
    }

    // 5. The second board, as EVIDENCE and never as a ranking input (REQ-CAT-003). Its age is the
    //    engine's own count against the artifact's anchor (D-139).
    if let second = secondaryBenchmark, let score = model.secondaryScore, let shown = number(score) {
        let age = secondaryAgeDays.map {
            language == .turkish ? "\($0) gün önce çalıştı" : "last run \($0) days ago"
        }
        facts.append(
            DetailFact(
                label: language == .turkish ? "İkinci kanıt" : "Second measurement",
                value: "\(shown) · \(second)",
                note: age
            )
        )
    }

    // 6. **The price, in both forms.** The owner's note asked for price to come back as an
    //    attribute rather than a control, and this is where it lands: the exact per-million figures
    //    a buyer checks, and the pages-of-text form for everyone else.
    // Review M-7: `priceTag` returns "—" for a price the engine could not resolve, and this file
    // forbids exactly that. A model with no price gets no price line; the card's own figures line
    // already says what it can, and a dash here would read as "free" to somebody.
    if model.blendedPerM.isFinite, model.blendedPerM > 0 {
        facts.append(
            DetailFact(
                label: language == .turkish ? "Fiyat" : "Price",
                value: priceTag(model.blendedPerM),
                note: priceInPages(model.blendedPerM, in: language)
            )
        )
    }
    // 6b. **What that price leaves out** (D-153, REQ-PRC-002). The engine sends a CODE and this
    //     build words it; a code this build does not know is left out rather than printed raw.
    if let excluded = priceExclusion(priceExcludes, in: language) {
        facts.append(
            DetailFact(
                label: language == .turkish ? "Fiyata dahil değil" : "Not in the price",
                value: excluded,
                note: language == .turkish
                    ? "her arama, sağlayıcısı tarafından ayrıca ücretlendirilir"
                    : "each search the model makes is billed separately by its provider"
            )
        )
    }
    if let input = number(model.inputPerM), let output = number(model.outputPerM) {
        facts.append(
            DetailFact(
                label: language == .turkish ? "Giriş / çıkış" : "Input / output",
                value: language == .turkish
                    ? "$\(input) / $\(output) · 1M jeton"
                    : "$\(input) / $\(output) per 1M",
                note: language == .turkish
                    ? "kartın fiyatı bu ikisinin karışımı"
                    : "the card's price is a blend of these two"
            )
        )
    }

    // 7. What this surface cannot tell apart, on its own scale. The card says "too close to call"
    //    in words; here the reader sees the number behind that sentence (D-138).
    if let margin = closeCallMargin, let shown = number(margin) {
        let unit = marginUnit(for: model.metric, singular: shown == "1", language)
        facts.append(
            DetailFact(
                label: language == .turkish ? "Ayırt edilemeyen fark" : "Too close to call",
                value: "\(shown) \(unit)",
                note: language == .turkish
                    ? "bu kadar yakın iki model berabere okunmalı"
                    : "two models this close are read as tied, not as ordered"
            )
        )
    }

    // 8. **The floor** (D-152, REQ-FLR-002, W-112): the score below which this surface recommends
    //    nothing. Printed through `scoreText` with the card's anchor, so it is on the same scale as
    //    the score above it; a rank-only board has no such scale, and gets its own unit instead.
    if let floor = minQuality {
        let shown = scoreText(floor, metric: model.metric, language, anchor: anchor)
            ?? number(floor).map { "\($0) \(scoreUnit(for: model.metric, in: language))" }
        if let shown {
            facts.append(
                DetailFact(
                    label: language == .turkish ? "Öneri eşiği" : "Recommendation floor",
                    value: shown,
                    note: language == .turkish
                        ? "bu puanın altındaki hiçbir modeli bu alanda önermiyoruz"
                        : "below this, the product recommends no model for this kind of question"
                )
            )
        }
    }

    return facts
}

/// The sentence for a `price_excludes` code (D-153), or `nil` for no code or one this build does not
/// know. Shared by the card and the detail screen, so the two cannot word one fact differently.
public func priceExclusion(_ code: String?, in language: Language) -> String? {
    switch code {
    case "search_call":
        return language == .turkish
            ? "Arama çağrıları bu fiyata dahil değil"
            : "Search calls are not included in this price"
    default:
        return nil
    }
}

/// What the detail screen needs from a served row. A `Pick` and a `RankedModel` both satisfy it,
/// so one screen serves both and there is one place where these lines are written.
public protocol DetailSubject {
    var model: String { get }
    var vendor: String { get }
    var score: Double { get }
    var metric: String { get }
    var secondaryScore: Double? { get }
    var blendedPerM: Double { get }
    var inputPerM: Double { get }
    var outputPerM: Double { get }
    var evidenceDate: String? { get }
    var harness: String { get }
    var effort: String? { get }
}

/// The unit a SCORE is printed in, which is not the unit a MARGIN is counted in.
///
/// Review N-1: the first draft reached for `marginUnit`, whose own documentation says the two
/// differ — a percentage board's margin is "points", and `83.5 points` reads as a different
/// measurement from `83.5 % resolved`. Keyed on the metric, like every other unit decision here.
func scoreUnit(for metric: String, in language: Language) -> String {
    switch scoreForm(for: metric) {
    case let .namedScale(name): return name
    case .rankOnly: return metric.uppercased()
    case .bounded, .unknown: return localisedUnit(metric, in: language)
    }
}
