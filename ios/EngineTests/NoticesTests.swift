//  The answer's notices in the reader's language (M18-W2, D-176, #63 finding 2).
//
//  D-136 composed the sentences under a pick from the engine's facts and left the notices in the
//  engine's English. A Turkish reader met five English sentences on the coding screen, and the
//  stale one named internal source ids. These tests hold the remainder: each notice is composed
//  from served facts in both languages, quotes the same numbers in both, names no source id, and
//  falls back to the engine's own English when a fact is missing or one this build does not know.
//  REQ-LOC-001 (the client composes every sentence from facts) is cited here.

import XCTest

@testable import ModelRankingEngine

final class NoticesTests: OfflineTestCase {

    private func health(_ ages: [Int?], stale: [Bool]? = nil, benchmark: String = "SWE-bench Verified")
        -> SourceHealth
    {
        let flags = stale ?? ages.map { _ in true }
        let rows = zip(ages, flags).enumerated().map { index, pair in
            SourceRow(source: "source_\(index)", rows: 10, newestRunDate: nil, ageDays: pair.0, stale: pair.1)
        }
        return SourceHealth(benchmark: benchmark, stale: flags.contains(true), notice: "engine text",
                            sources: rows, reason: nil)
    }

    // MARK: staleness

    func testAStaleBoardIsSaidInBothLanguagesWithoutItsSourceIds() {
        let served = health([101, 220])
        let english = staleSentence(served, .english)
        let turkish = staleSentence(served, .turkish)

        XCTAssertEqual(english, "The evidence behind SWE-bench Verified may be out of date: its newest "
            + "results are 101 days old. The ranking may not reflect current models.")
        XCTAssertEqual(turkish, "SWE-bench Verified için kanıt güncel olmayabilir: en yeni sonuçları "
            + "101 günlük. Sıralama güncel modelleri yansıtmayabilir.")
        for sentence in [english, turkish] {
            XCTAssertFalse(sentence?.contains("source_") ?? true, "an internal source id reached the reader")
        }
    }

    func testOneStaleSourceOfTwoIsCountedNotGeneralised() {
        let served = health([12, 200], stale: [false, true])

        XCTAssertEqual(staleSentence(served, .english), "The evidence behind SWE-bench Verified may be out "
            + "of date: 1 of its 2 sources last published 200 days ago. The ranking may not reflect current models.")
        XCTAssertEqual(staleSentence(served, .turkish), "SWE-bench Verified için kanıt güncel olmayabilir: "
            + "2 kaynağından 1 tanesi en son 200 gün önce yayımladı. Sıralama güncel modelleri yansıtmayabilir.")
    }

    func testUndatedAndFutureDatedSourcesAreNamedAsSuch() {
        let served = health([nil, -3])

        XCTAssertEqual(staleSentence(served, .english), "The evidence behind SWE-bench Verified may be out "
            + "of date: 1 of its 2 sources publishes no evaluation date; 1 of its 2 sources is dated in the "
            + "future. The ranking may not reflect current models.")
        XCTAssertEqual(staleSentence(served, .turkish), "SWE-bench Verified için kanıt güncel olmayabilir: "
            + "2 kaynağından 1 tanesi ölçüm tarihi yayımlamıyor; 2 kaynağından 1 tanesi ileri bir tarih taşıyor. "
            + "Sıralama güncel modelleri yansıtmayabilir.")
    }

    func testAFreshBoardSaysNothing() {
        XCTAssertNil(staleSentence(health([10, 20], stale: [false, false]), .turkish))
    }

    func testABoardWithNoSourceAtAllIsSaid() {
        let empty = SourceHealth(benchmark: "DeepSWE", stale: true, notice: "engine text", sources: [],
                                 reason: "no_source")

        XCTAssertEqual(staleSentence(empty, .english),
                       "No evidence source for DeepSWE is in the served data, so how fresh it is cannot be told.")
        XCTAssertEqual(staleSentence(empty, .turkish),
                       "DeepSWE için sunulan veride hiçbir kanıt kaynağı yok; ne kadar güncel olduğu bilinemiyor.")
    }

    // MARK: dating, effort, ordering, the ranked-on line, an empty answer

    func testUndatedEvidenceIsSaidInBothLanguages() {
        XCTAssertEqual(datingSentence("undated", benchmark: "DeepSWE", .english),
                       "The DeepSWE evidence in this answer carries no evaluation dates, only model release "
                       + "dates. Its scores cannot be aged, so how fresh they are is unknown.")
        XCTAssertEqual(datingSentence("undated", benchmark: "DeepSWE", .turkish),
                       "Bu cevaptaki DeepSWE kanıtı ölçüm tarihi taşımıyor, yalnızca modellerin çıkış "
                       + "tarihlerini taşıyor. Puanların yaşı bilinemiyor; ne kadar güncel oldukları da bilinmiyor.")
        XCTAssertNotNil(datingSentence("mixed", benchmark: "DeepSWE", .turkish))
        XCTAssertNil(datingSentence("dated", benchmark: "DeepSWE", .turkish), "dated evidence needs no note")
        XCTAssertNil(datingSentence("some_future_kind", benchmark: "DeepSWE", .turkish),
                     "an unknown kind composes nothing; the engine's English is shown instead")
    }

    func testTheEffortMixNamesTheLevelsInBothLanguages() {
        XCTAssertEqual(effortMixSentence(efforts: ["max", "high", "max"], .turkish),
                       "Not: Bu alan modelleri tek bir çaba düzeyinde karşılaştırmıyor ve buradaki puanlar "
                       + "farklı düzeylerden geliyor (yüksek, en yüksek). Daha yüksek çabayla çalıştırılan bir model, "
                       + "daha düşük çabayla çalıştırılandan iyi görünebilir.")
        XCTAssertNil(effortMixSentence(efforts: ["max"], .english), "one level is not a mix")
    }

    func testTheOrderingNoteAndTheRankedOnLineSpeakTurkish() {
        XCTAssertTrue(orderingSentence(.turkish).hasPrefix("Buradaki sıranın bir anlamı yok"))
        XCTAssertEqual(orderingSentence(.english), orderingNoteEnglish)
        XCTAssertEqual(rankedOnSentence(count: 54, benchmark: "SWE-bench Verified", effort: nil, .turkish),
                       "SWE-bench Verified üzerinde sıralanan 54 model")
        XCTAssertEqual(rankedOnSentence(count: 18, benchmark: "DeepSWE", effort: "high", .turkish),
                       "DeepSWE üzerinde, yüksek çaba düzeyinde sıralanan 18 model")
        XCTAssertEqual(rankedOnSentence(count: 18, benchmark: "DeepSWE", effort: "high", .english),
                       "18 models ranked on DeepSWE, at high effort")
    }

    /// Review M2: the engine has three reasons, and the third ("could not be read") was said as the
    /// first. Each is composed from its code (D-176 clause 7); no code, or one this build does not
    /// know, composes nothing, and the engine's English is shown.
    func testAnEmptyAnswerSaysWhichOfItsThreeReasons() {
        let codes = ["no_evidence", "over_budget", "unreadable"]
        for language in Language.allCases {
            let said = codes.compactMap { unavailableSentence(code: $0, benchmark: "DeepSWE", language) }
            XCTAssertEqual(Set(said).count, 3, "two reasons collapsed into one, which M7 spent a security round preventing")
        }
        XCTAssertTrue(unavailableSentence(code: "no_evidence", benchmark: "DeepSWE", .turkish)?.contains("DeepSWE") == true)
        XCTAssertNil(unavailableSentence(code: nil, benchmark: "B", .turkish))
        XCTAssertNil(unavailableSentence(code: "some_future_reason", benchmark: "B", .turkish))
    }

    func testABoardWhoseEvidenceCouldNotBeReadIsNotSaidToHaveNoSource() {
        let unreadable = SourceHealth(benchmark: "B", stale: true, notice: "engine text", sources: [], reason: "unreadable")
        let english = staleSentence(unreadable, .english)
        XCTAssertEqual(english, "This surface's evidence could not be read, so how fresh it is is unknown.")
        XCTAssertNotNil(staleSentence(unreadable, .turkish))
        let unknown = SourceHealth(benchmark: "B", stale: true, notice: "engine text", sources: [], reason: nil)
        XCTAssertNil(staleSentence(unknown, .turkish), "an empty health with no reason is the engine's English")
    }

    /// The engine's three empty answers, as it serves them, each said for what it is.
    func testTheEnginesThreeEmptyAnswersAreEachSaidTruly() throws {
        func empty(_ code: String, _ health: String) throws -> Answer {
            try JSONDecoder().decode(Answer.self, from: Data("""
            {"surface": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified",
             "metric": "% resolved", "eligible_count": 0, "frontier_size": 0, "sources": [], "picks": [],
             "ranking": [], "unavailable_reason": "engine sentence", "unavailable_reason_code": "\(code)",
             "source_health": {"benchmark": "SWE-bench Verified", "stale": true, "notice": "engine notice",
                               "sources": [], "reason": "\(health)"}}
            """.utf8))
        }
        let unreadable = try empty("unreadable", "unreadable")
        let said = answerDisclosures(unreadable, anchor: nil, .english).map(\.text)
        XCTAssertEqual(said, ["This surface's evidence could not be read, so how fresh it is is unknown."])
        XCTAssertEqual(unavailableSentence(code: unreadable.unavailableReasonCode, benchmark: "SWE-bench Verified", .english),
                       "This surface's evidence could not be read. This is a gap in the evidence, not a result.")
        let gap = try empty("no_evidence", "no_source")
        XCTAssertTrue(answerDisclosures(gap, anchor: nil, .english).first?.text.hasPrefix("No evidence source") == true)
    }

    // MARK: the close call

    private let ranked = ["Claude Opus 4.7", "GPT-5.5", "Gemini 3.5 Flash"]

    func testACloseCallIsSaidFromItsFact() {
        let fact = CloseCallFact(model: "GPT-5.5", behindBy: 1.2, unit: "points")

        XCTAssertEqual(closeCallSentence(fact, ranked: ranked, leader: 83.5, metric: "% resolved",
                                         anchor: nil, .english),
                       "GPT-5.5 is only 1.2 points behind — the gap is within the margin of error and either "
                       + "choice is defensible.")
        XCTAssertEqual(closeCallSentence(fact, ranked: ranked, leader: 83.5, metric: "% resolved",
                                         anchor: nil, .turkish),
                       "GPT-5.5 yalnızca 1.2 puan geride — fark hata payı içinde, ikisi de savunulabilir bir seçim.")
        XCTAssertEqual(closeCallSentence(CloseCallFact(model: "GPT-5.5", behindBy: 0, unit: "points"),
                                         ranked: ranked, leader: 83.5, metric: "% resolved", anchor: nil, .turkish),
                       "GPT-5.5 berabere — fark hata payı içinde, ikisi de savunulabilir bir seçim.")
    }

    /// D-143's rule (review M-2), applied here: on a surface whose cards read out of 100, the gap is
    /// said out of 100 too, never as Elo above rows that say `59.6 / 100`.
    func testOnAnAnchoredEloSurfaceTheGapIsOutOf100() throws {
        let fact = CloseCallFact(model: "GPT-5.5", behindBy: 5.2, unit: "Elo")
        let sentence = try XCTUnwrap(closeCallSentence(fact, ranked: ranked, leader: 1500, metric: "elo",
                                                       anchor: 1400, .english))

        XCTAssertFalse(sentence.contains("Elo"), sentence)
        XCTAssertTrue(sentence.contains("points behind"), sentence)
    }

    /// The fact names a model; the app names it only if the answer's own ranking lists it. A name the
    /// ranking does not carry is the engine's English or nothing, never a sentence this app made up.
    func testAModelTheRankingDoesNotListIsNotNamed() {
        let stranger = CloseCallFact(model: "Unlisted 9", behindBy: 1, unit: "points")
        XCTAssertNil(closeCallSentence(stranger, ranked: ranked, leader: 83.5, metric: "% resolved",
                                       anchor: nil, .turkish))
        let negative = CloseCallFact(model: "GPT-5.5", behindBy: -1, unit: "points")
        XCTAssertNil(closeCallSentence(negative, ranked: ranked, leader: 83.5, metric: "% resolved",
                                       anchor: nil, .turkish), "a negative gap reads as ahead")
    }

    func testBothLanguagesQuoteTheSameNumbers() {
        let fact = CloseCallFact(model: "GPT-5.5", behindBy: 1.2, unit: "points")
        let pairs: [(String?, String?)] = [
            (staleSentence(health([101, 220]), .english), staleSentence(health([101, 220]), .turkish)),
            (staleSentence(health([12, 200], stale: [false, true]), .english),
             staleSentence(health([12, 200], stale: [false, true]), .turkish)),
            (closeCallSentence(fact, ranked: ranked, leader: 83.5, metric: "% resolved", anchor: nil, .english),
             closeCallSentence(fact, ranked: ranked, leader: 83.5, metric: "% resolved", anchor: nil, .turkish)),
            (rankedOnSentence(count: 54, benchmark: "B", effort: nil, .english),
             rankedOnSentence(count: 54, benchmark: "B", effort: nil, .turkish)),
        ]
        for (english, turkish) in pairs {
            XCTAssertEqual(digits(english), digits(turkish), "\(english ?? "nil")\n\(turkish ?? "nil")")
        }
    }

    private func digits(_ text: String?) -> [String] {
        let pattern = try? NSRegularExpression(pattern: #"\d+(?:\.\d+)?"#)
        let text = text ?? ""
        return (pattern?.matches(in: text, range: NSRange(text.startIndex..., in: text)) ?? [])
            .compactMap { Range($0.range, in: text).map { String(text[$0]) } }.sorted()
    }

    // MARK: one answer, end to end

    private func answer(_ extra: String) throws -> Answer {
        let json = """
        {"surface": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified",
         "metric": "% resolved", "eligible_count": 3, "frontier_size": 3, "sources": [],
         "picks": [
           {"label": "best_quality", "model": "Claude Opus 4.7", "vendor": "Anthropic", "score": 83.5,
            "metric": "% resolved", "blended_per_m": 8.75, "input_per_m": 4.4, "output_per_m": 21.9,
            "harness": "h", "effort": "max", "confidence": "High", "confidence_basis": "b", "why": "w"},
           {"label": "best_value", "model": "GPT-5.5", "vendor": "OpenAI", "score": 82.3,
            "metric": "% resolved", "blended_per_m": 9.84, "input_per_m": 5, "output_per_m": 20,
            "harness": "h", "effort": "high", "confidence": "High", "confidence_basis": "b", "why": "w"}
         ],
         "ranking": [
           {"model": "Claude Opus 4.7", "vendor": "Anthropic", "score": 83.5, "metric": "% resolved",
            "blended_per_m": 8.75, "input_per_m": 4.4, "output_per_m": 21.9, "harness": "h"},
           {"model": "GPT-5.5", "vendor": "OpenAI", "score": 82.3, "metric": "% resolved",
            "blended_per_m": 9.84, "input_per_m": 5, "output_per_m": 20, "harness": "h"}
         ],
         \(extra)}
        """
        return try JSONDecoder().decode(Answer.self, from: Data(json.utf8))
    }

    func testEveryNoticeOfTheCodingScreenReachesTheReaderInTurkish() throws {
        let served = try answer("""
        "close_call": "GPT-5.5 is only 1.2 points behind — the gap is within the margin of error and either choice is defensible.",
        "close_call_fact": {"model": "GPT-5.5", "behind_by": 1.2, "unit": "points"},
        "effort_mix_notice": "Note: this category does not compare at a fixed effort level (high, max).",
        "source_health": {"benchmark": "SWE-bench Verified", "stale": true,
          "notice": "Evidence behind SWE-bench Verified may be out of date: epoch_swe_bench_verified last published 101 days ago.",
          "sources": [{"source": "epoch_swe_bench_verified", "rows": 3, "newest_run_date": "2026-06-25", "age_days": 101, "stale": true}]},
        "evidence_dating": "dated"
        """)
        let notices = answerDisclosures(served, anchor: nil, .turkish)

        XCTAssertEqual(notices.count, 3, notices.map(\.text).joined(separator: "\n"))
        for notice in notices {
            XCTAssertFalse(notice.text.contains("Note:") || notice.text.contains(" behind")
                           || notice.text.contains("Evidence"), "English in Turkish mode: \(notice.text)")
            XCTAssertFalse(notice.text.contains("epoch_"), "a source id reached the reader: \(notice.text)")
        }
        XCTAssertEqual(notices.map(\.weight), [.state, .state, .property], "D-135's weights moved")
    }

    /// D-136's fallback, kept: a payload without the facts (an older engine) still shows every notice,
    /// in the engine's own English, rather than dropping one (D-135 forbids a cut).
    func testWithoutTheFactsTheEnginesOwnSentenceIsShown() throws {
        let served = try answer("""
        "close_call": "GPT-5.5 is only 1.2 points behind.",
        "evidence_dating": "dated"
        """)

        XCTAssertEqual(answerDisclosures(served, anchor: nil, .turkish).map(\.text),
                       ["GPT-5.5 is only 1.2 points behind."])
    }
}
