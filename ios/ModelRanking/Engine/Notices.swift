//  Notices.swift — an answer's notices in the reader's language, from the facts `/v1` serves.
//  M18-W2, D-176, #63 finding 2.
//
//  D-136 composed the two sentences under a pick and left the notices -- staleness, undated
//  evidence, the effort mix, the close call, the ordering note, an empty answer -- in the engine's
//  English, "recorded as an explicit remainder rather than left to be discovered by a Turkish
//  reader". A Turkish reader then met five English sentences on the coding screen, one of them
//  naming internal source ids. This file is that remainder.
//
//  Every notice is composed from a served FACT, never from the engine's sentence: `source_health`'s
//  rows, `evidence_dating`'s kind, the picks' efforts, `close_call_fact` (D-176). The engine still
//  decides WHETHER a notice is said; this file decides only how. Where a fact is missing or one this
//  build does not know, the engine's own English is shown instead, D-136's fallback: an English
//  sentence is a lesser answer, a dropped one is a cut D-135 forbids.

import Foundation

/// The values the engine's `close_call` sentence quotes (D-176).
struct CloseCallFact: Decodable, Equatable {
    let model: String
    let behindBy: Double
    let unit: String

    enum CodingKeys: String, CodingKey {
        case model, unit
        case behindBy = "behind_by"
    }
}

// MARK: - Staleness, from `source_health`

/// The staleness notice, or `nil` when the board is not stale. Names no source id: the reader needs
/// how old the evidence is, not what the engine calls its feeds (#63 finding 2).
func staleSentence(_ health: SourceHealth, _ language: Language) -> String? {
    guard health.stale else { return nil }
    let benchmark = health.benchmark
    guard !health.sources.isEmpty else {
        // Review M2: no sources has two causes, and the engine names which (D-176 clause 7). A
        // health that names neither is the engine's English.
        switch (health.reason, language) {
        case ("no_source", .turkish):
            return "\(benchmark) için sunulan veride hiçbir kanıt kaynağı yok; ne kadar güncel olduğu bilinemiyor."
        case ("no_source", .english):
            return "No evidence source for \(benchmark) is in the served data, so how fresh it is cannot be told."
        case ("unreadable", .turkish):
            return "Bu alanın kanıtı okunamadı; ne kadar güncel olduğu bilinmiyor."
        case ("unreadable", .english):
            return "This surface's evidence could not be read, so how fresh it is is unknown."
        default:
            return nil
        }
    }
    let total = health.sources.count
    let stale = health.sources.filter(\.stale)
    let ages = stale.compactMap(\.ageDays).filter { $0 >= 0 }
    let aged = ages.sorted()
    let undated = stale.filter { $0.ageDays == nil }.count
    let future = stale.filter { ($0.ageDays ?? 0) < 0 }.count

    var clauses: [String] = []
    if !aged.isEmpty {
        if aged.count == total {
            // Every source is old, so the freshest of them is how old the evidence is.
            clauses.append(language == .turkish
                ? "en yeni sonuçları \(aged[0]) günlük"
                : "its newest results are \(aged[0]) days old")
        } else {
            let days = aged.map(String.init).joined(separator: language == .turkish ? " ve " : " and ")
            clauses.append(language == .turkish
                ? "\(total) kaynağından \(aged.count) tanesi en son \(days) gün önce yayımladı"
                : "\(aged.count) of its \(total) sources last published \(days) days ago")
        }
    }
    if undated > 0 {
        clauses.append(language == .turkish
            ? "\(total) kaynağından \(undated) tanesi ölçüm tarihi yayımlamıyor"
            : "\(undated) of its \(total) sources \(undated == 1 ? "publishes" : "publish") no evaluation date")
    }
    if future > 0 {
        clauses.append(language == .turkish
            ? "\(total) kaynağından \(future) tanesi ileri bir tarih taşıyor"
            : "\(future) of its \(total) sources \(future == 1 ? "is" : "are") dated in the future")
    }
    guard !clauses.isEmpty else { return nil }
    let said = clauses.joined(separator: "; ")
    return language == .turkish
        ? "\(benchmark) için kanıt güncel olmayabilir: \(said). Sıralama güncel modelleri yansıtmayabilir."
        : "The evidence behind \(benchmark) may be out of date: \(said). The ranking may not reflect current models."
}

// MARK: - Undated evidence, the effort mix, the ordering, the ranked-on line, an empty answer

/// `evidence_dating`'s note, by its kind (REQ-UNC-003). `nil` for dated evidence and for a kind this
/// build does not know.
func datingSentence(_ kind: String?, benchmark: String, _ language: Language) -> String? {
    switch (kind, language) {
    case ("undated", .english):
        return "The \(benchmark) evidence in this answer carries no evaluation dates, only model release "
            + "dates. Its scores cannot be aged, so how fresh they are is unknown."
    case ("undated", .turkish):
        return "Bu cevaptaki \(benchmark) kanıtı ölçüm tarihi taşımıyor, yalnızca modellerin çıkış "
            + "tarihlerini taşıyor. Puanların yaşı bilinemiyor; ne kadar güncel oldukları da bilinmiyor."
    case ("mixed", .english):
        return "Some picks in this answer carry an evaluation date from \(benchmark) and some do not; "
            + "the undated ones cannot be aged."
    case ("mixed", .turkish):
        return "Bu cevaptaki seçimlerin bir kısmı \(benchmark) ölçüm tarihi taşıyor, bir kısmı taşımıyor; "
            + "tarihsiz olanların yaşı bilinemiyor."
    default:
        return nil
    }
}

/// The effort-mix notice (D-112), naming the levels the picks were measured at. `nil` below two.
func effortMixSentence(efforts: [String], _ language: Language) -> String? {
    let distinct = Set(efforts.filter { !$0.isEmpty })
    let levels = distinct.sorted()  // the engine's order: `sorted(distinct)`
    guard levels.count > 1 else { return nil }
    let named = levels.map { effortName($0, language) }.joined(separator: ", ")
    return language == .turkish
        ? "Not: Bu alan modelleri tek bir çaba düzeyinde karşılaştırmıyor ve buradaki puanlar farklı "
            + "düzeylerden geliyor (\(named)). Daha yüksek çabayla çalıştırılan bir model, daha düşük "
            + "çabayla çalıştırılandan iyi görünebilir."
        : "Note: this category does not compare at one effort level, and the scores here come from "
            + "different levels (\(named)). A model run at a higher effort can look better than one "
            + "run at a lower effort."
}

/// The engine's `ORDERING_NOTE`, word for word. `test_ios_client_contract.py` holds the two equal,
/// so the Turkish below translates the sentence the engine actually sends.
let orderingNoteEnglish = "No position here means anything: neither coding surface leads the other, and "
    + "the one you chose is shown first only because you chose it. They rank different sets of models on "
    + "different evidence, and each states its own weakness."

/// Ruling A's disclosure: the order of two answers carries no meaning.
func orderingSentence(_ language: Language) -> String {
    language == .turkish
        ? "Buradaki sıranın bir anlamı yok: iki kod yazma alanından biri diğerinin önünde değil; seçtiğin "
            + "önce gösteriliyor, çünkü onu sen seçtin. Farklı modelleri farklı kanıtlarla sıralıyorlar ve her "
            + "biri kendi zayıflığını söylüyor."
        : orderingNoteEnglish
}

/// The line under a surface: how many models, on which board, at which effort.
func rankedOnSentence(count: Int, benchmark: String, effort: String?, _ language: Language) -> String {
    switch (effort.map { effortName($0, language) }, language) {
    case let (level?, .turkish): return "\(benchmark) üzerinde, \(level) çaba düzeyinde sıralanan \(count) model"
    case (nil, .turkish): return "\(benchmark) üzerinde sıralanan \(count) model"
    case let (level?, .english): return "\(count) models ranked on \(benchmark), at \(level) effort"
    case (nil, .english): return "\(count) models ranked on \(benchmark)"
    }
}

/// Why an answer has no picks, by the engine's code (D-176 clause 7). Its three reasons stay three
/// (M7, review M2): nothing reached the ranking, nothing fit a budget, the evidence could not be read.
/// `nil` for no code or one this build does not know: the engine's English is shown.
func unavailableSentence(code: String?, benchmark: String, _ language: Language) -> String? {
    switch (code, language) {
    case ("no_evidence", .turkish):
        return "Bu alanın sıralayacak kanıtı yok: sunulan veride \(benchmark) üzerinden sıralamaya giren "
            + "bir sonuç yok. Bu bir sonuç değil, kanıttaki bir boşluk."
    case ("no_evidence", .english):
        return "This surface has no evidence to rank: nothing on \(benchmark) reached the ranking in the "
            + "served data. This is a gap in the evidence, not a result."
    case ("over_budget", .turkish):
        return "Bu alanın listesindeki hiçbir model istenen bütçeye uymuyor, bu yüzden bu cevap hiçbir şey "
            + "sıralamıyor. Gizlenmek yerine gösteriliyor."
    case ("over_budget", .english):
        return "No model on this surface's benchmark fits the requested budget, so this answer ranks "
            + "nothing. It is shown rather than hidden."
    case ("unreadable", .turkish):
        return "Bu alanın kanıtı okunamadı. Bu bir sonuç değil, kanıttaki bir boşluk."
    case ("unreadable", .english):
        return "This surface's evidence could not be read. This is a gap in the evidence, not a result."
    default:
        return nil
    }
}

// MARK: - The close call, from `close_call_fact`

/// The close call (REQ-REC-004), or `nil` when the fact cannot be said honestly: a model the answer's
/// ranking does not list, or a gap that is not a distance.
///
/// On a surface whose cards read out of 100 (D-143), the gap is said out of 100 too, the rule
/// `leaderSentence` follows (review M-2): never `5.2 Elo` above rows that say `59.6 / 100`.
func closeCallSentence(
    _ fact: CloseCallFact, ranked: [String], leader: Double?, metric: String, anchor: Double?,
    _ language: Language
) -> String? {
    guard ranked.contains(fact.model), fact.behindBy.isFinite, fact.behindBy >= 0 else { return nil }
    let tail = language == .turkish
        ? "fark hata payı içinde, ikisi de savunulabilir bir seçim."
        : "the gap is within the margin of error and either choice is defensible."
    if fact.behindBy == 0 {
        return language == .turkish ? "\(fact.model) berabere — \(tail)" : "\(fact.model) is level — \(tail)"
    }
    let converted = leader.flatMap {
        distanceOutOf100(below: $0, by: fact.behindBy, metric: metric, anchor: anchor)
    }
    guard let named = label(fact.unit), let amount = number(converted ?? fact.behindBy) else { return nil }
    // Points are words and are translated; a scale's name (`Elo`) is not (`localisedUnit`).
    let unit = converted != nil || named == "points"
        ? marginUnit(for: "% correct", singular: amount == "1", language)
        : named
    return language == .turkish
        ? "\(fact.model) yalnızca \(amount) \(unit) geride — \(tail)"
        : "\(fact.model) is only \(amount) \(unit) behind — \(tail)"
}

// MARK: - One answer's notices

/// Every notice of one answer, in the reader's language, classified and deduplicated by D-135's
/// `classifyDisclosures`. Each is the composed sentence where its facts allow, and the engine's own
/// English where they do not.
func answerDisclosures(_ answer: Answer, anchor: Double?, _ language: Language) -> [Disclosure] {
    // `source_health` when it speaks, else the engine's older relative notice, as before (D-135).
    let staleness = answer.sourceHealth.flatMap { health in
        health.notice.map { staleSentence(health, language) ?? $0 }
    } ?? answer.staleNotice
    let dating = answer.evidenceDatingNote.map {
        datingSentence(answer.evidenceDating, benchmark: answer.primaryBenchmark, language) ?? $0
    }
    let effort = answer.effortMixNotice.map {
        effortMixSentence(efforts: answer.picks.compactMap(\.effort), language) ?? $0
    }
    let tie = answer.closeCall.map { served in
        answer.closeCallFact.flatMap {
            closeCallSentence($0, ranked: answer.ranking.map(\.model), leader: answer.ranking.first?.score,
                              metric: answer.metric, anchor: anchor, language)
        } ?? served
    }
    return classifyDisclosures(
        stalenessNotice: staleness,
        ageDays: (answer.sourceHealth?.sources ?? []).map(\.ageDays),
        datingNote: dating,
        effortMixNotice: effort,
        closeCall: tie
    )
}

// MARK: - The combined list's disclosures (#67, #72, M18-W2 P4)

/// A combined-list disclosure as the screen says it, with D-135's weight: a stale board is a state,
/// loud, unless none of its sources carries a date at all (then it is a property of the board).
func combinedDisclosure(_ disclosure: CombinedDisclosure, _ language: Language) -> Disclosure? {
    switch disclosure {
    case let .staleBoard(health):
        guard let text = staleSentence(health, language) ?? health.notice else { return nil }
        let dated = health.sources.contains { $0.ageDays != nil }
        return Disclosure(text: text, weight: dated ? .state : .property)
    case let .stalePhoneCopy(days):
        return Disclosure(text: UIText.stalePhoneCopy(days: days, language), weight: .state)
    case let .productsOwnOrder(models, boards):
        return Disclosure(text: UIText.combinedNote(models: models, boards: boards, language), weight: .property)
    case .tiedPlaces:
        return Disclosure(text: UIText.tiedPlaces(language), weight: .property)
    case let .mixedEfforts(efforts):
        return Disclosure(text: UIText.combinedEffortNote(efforts: efforts, language), weight: .property)
    case let .boardsWeighHalf(benchmarks):
        return Disclosure(text: UIText.boardsWeighHalf(benchmarks, language), weight: .property)
    }
}
