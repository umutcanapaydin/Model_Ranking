//  Two languages composed from one truth. D-136, M12-W4.
//
//  The property that matters is not "the Turkish is present". It is that both sentences are
//  RENDERINGS of the same fact, so they cannot drift — which is precisely what a translated string
//  table cannot promise, and why the owner chose this architecture over `?lang=tr`.

import XCTest

@testable import ModelRankingEngine

final class LanguageCompositionTests: XCTestCase {

    private let highest: [String: Any] = [
        "reason": "highest_score", "benchmark": "SWE-bench Verified",
        "score": 83.5, "unit": "% resolved",
    ]
    private let window: [String: Any] = [
        "reason": "cheapest_within_window", "window": 6.0, "unit": "points",
    ]
    private let floorMet: [String: Any] = [
        "reason": "cheapest_above_floor", "floor": 84.4, "unit": "points",
    ]
    private let floorMissed: [String: Any] = [
        "reason": "nothing_clears_floor", "floor": 65.0, "unit": "points",
    ]

    // MARK: every reason speaks both languages

    func testEveryReasonTheEngineCanEmitHasBothSentences() {
        for fact in [highest, window, floorMet, floorMissed] {
            for language in Language.allCases {
                XCTAssertNotNil(whySentence(fact, in: language),
                                "\(fact["reason"] ?? "?") has no sentence in \(language.rawValue)")
            }
        }
    }

    /// **The property, and the reason this is not a string table.** Both languages print the same
    /// numbers, because both read them out of the same fact. A translated string table can drift
    /// on a number; this cannot.
    func testBothLanguagesQuoteTheSameNumbers() {
        for fact in [highest, window, floorMet, floorMissed] {
            let english = whySentence(fact, in: .english) ?? ""
            let turkish = whySentence(fact, in: .turkish) ?? ""

            XCTAssertEqual(numbers(in: english), numbers(in: turkish),
                           "the two languages quote different numbers:\n  \(english)\n  \(turkish)")
        }
    }

    /// A newer engine may name a reason this build has never heard of. Falling back to the
    /// engine's own English is correct; inventing a Turkish sentence for a reason we do not
    /// understand would be the product speaking without knowing what it is saying.
    func testAnUnknownReasonComposesNothingRatherThanGuessing() {
        XCTAssertNil(whySentence(["reason": "some_future_rule"], in: .turkish))
        XCTAssertNil(whySentence([:], in: .english))
    }

    /// The warning case must stay a warning in both languages. Translating a caution as a
    /// recommendation is the worst available failure here.
    func testTheWarningReasonStaysAWarningInTurkish() {
        let turkish = whySentence(floorMissed, in: .turkish) ?? ""

        XCTAssertTrue(turkish.contains("Dikkat"), turkish)
        XCTAssertTrue(turkish.contains("ödün"), "the quality trade-off is not stated: \(turkish)")
    }

    // MARK: trade-offs

    func testTheTradeOffSpeaksBothLanguagesAndQuotesTheSameNumbers() {
        let fact: [String: Any] = ["behind_by": 4.4, "unit": "points", "cheaper_by_times": 3]

        let english = tradeOffSentence(fact, in: .english) ?? ""
        let turkish = tradeOffSentence(fact, in: .turkish) ?? ""

        XCTAssertEqual(numbers(in: english), numbers(in: turkish))
        XCTAssertTrue(english.contains("4.4"), english)
    }

    func testALevelScoreIsNotReportedAsAGapInEitherLanguage() {
        // `lead_phrase`'s zero-guard, carried across the boundary: "0.0 points behind" and "level"
        // in the same payload was a real defect once (W4 re-review MINOR-1).
        let fact: [String: Any] = ["behind_by": 0.0, "unit": "points", "cheaper_by_percent": 30]

        // Assert on the LEAD, not on the digits: the first version of this forbade the substring
        // `"0 "` and failed on `%30 daha ucuz`, which is a saving and not a gap. A test that reads
        // the whole sentence when it means one clause finds defects that are not there.
        XCTAssertEqual(tradeOffSentence(fact, in: .english)?.hasPrefix("Just as good"), true)
        XCTAssertEqual(tradeOffSentence(fact, in: .turkish)?.hasPrefix("En iyisi kadar iyi"), true)
        for language in Language.allCases {
            let lead = (tradeOffSentence(fact, in: language) ?? "").split(separator: ",").first ?? ""
            XCTAssertFalse(lead.contains("0"), "a zero gap was reported as a gap: \(lead)")
        }
    }

    func testTheSamePriceCaseSaysSoRatherThanClaimingASaving() {
        let fact: [String: Any] = ["behind_by": 2.0, "unit": "points", "cheaper": "same"]

        XCTAssertTrue((tradeOffSentence(fact, in: .english) ?? "").contains("same price"))
        XCTAssertTrue((tradeOffSentence(fact, in: .turkish) ?? "").contains("aynı fiyata"))
    }

    func testATradeOffWithoutItsGapComposesNothing() {
        XCTAssertNil(tradeOffSentence(["unit": "points"], in: .english))
    }

    // MARK: numbers do not change shape between languages

    func testANumberIsSpelledTheSameWayInBothLanguages() {
        // Turkish writes decimals with a comma, and that convention is deliberately NOT applied:
        // these are the ENGINE's numbers, and two readers comparing notes must see the same digits.
        let fact: [String: Any] = ["behind_by": 4.4, "unit": "puan", "cheaper_by_times": 3]

        XCTAssertTrue((tradeOffSentence(fact, in: .turkish) ?? "").contains("4.4"))
        XCTAssertFalse((tradeOffSentence(fact, in: .turkish) ?? "").contains("4,4"))
    }

    func testAWholeNumberLosesItsTrailingZero() {
        XCTAssertTrue((whySentence(window, in: .english) ?? "").contains("6 points"), "6.0 leaked")
    }

    func testTheLanguageSwitchCarriesAFlagForEach() {
        XCTAssertEqual(Set(Language.allCases.map(\.flag)).count, Language.allCases.count)
    }

    private func numbers(in text: String) -> [String] {
        text.split(whereSeparator: { !$0.isNumber && $0 != "." }).map(String.init)
    }
}

final class LocalisedUnitTests: XCTestCase {

    /// **Seen on the first Turkish screenshot: "En iyisinin 6 points yakınında".** The unit came
    /// from the engine as an English display label and went into a Turkish sentence unchanged. A
    /// half-translated sentence reads worse than an untranslated one, because the reader cannot
    /// tell which half to trust.
    func testAScoreUnitIsTranslatedInsideATurkishSentence() {
        let fact: [String: Any] = [
            "reason": "cheapest_within_window", "window": 6.0, "unit": "points",
        ]

        let turkish = whySentence(fact, in: .turkish) ?? ""

        XCTAssertTrue(turkish.contains("puan"), turkish)
        XCTAssertFalse(turkish.contains("points"), "an English unit is inside a Turkish sentence")
    }

    func testTheEnglishSentenceIsUnaffected() {
        XCTAssertEqual(localisedUnit("points", in: .english), "points")
    }

    /// `elo` and `ECI` are the NAMES of scales, not words. Translating a proper noun would make
    /// two readers unable to compare notes — the same reasoning that leaves the digits alone.
    func testTheNameOfAScaleIsNotTranslated() {
        for scale in ["elo", "ECI"] {
            XCTAssertEqual(localisedUnit(scale, in: .turkish), scale)
        }
    }

    func testAnUnknownUnitPassesThroughRatherThanVanishing() {
        XCTAssertEqual(localisedUnit("f1", in: .turkish), "f1")
    }

    func testTheScaleExplanationAndThePriceSpeakTurkishToo() {
        // These are composed by the client, so leaving them English would be the half-done
        // localisation the M12 plan names as its second trap.
        XCTAssertNotEqual(scaleExplanation(for: "ECI", in: .turkish),
                          scaleExplanation(for: "ECI", in: .english))
        XCTAssertTrue((priceInPages(10.0, in: .turkish)).contains("yaklaşık"))
        XCTAssertTrue((priceInPages(36.09, in: .turkish)).contains("sayfa başına"))
    }

    func testTheTurkishPriceStillCarriesTheSameNumberAsTheEnglish() {
        // Both are renderings of one value; a language must not change what something costs.
        for price in [1.03, 10.0, 36.09] {
            let english = priceInPages(price, in: .english)
            let turkish = priceInPages(price, in: .turkish)
            let digits = { (text: String) in
                text.split(whereSeparator: { !$0.isNumber && $0 != "." }).map(String.init)
            }
            XCTAssertEqual(digits(english).sorted(), digits(turkish).sorted(),
                           "\(english)  vs  \(turkish)")
        }
    }
}

final class ScreenChromeTests: XCTestCase {

    /// The chrome is a string TABLE — a title, a placeholder, a button — and that is deliberate:
    /// a table is the right shape for text carrying no values, and the wrong shape for a sentence
    /// that quotes numbers. D-136 turns on exactly that distinction.
    func testEveryPieceOfChromeSpeaksBothLanguagesAndTheyDiffer() {
        let pairs: [(String, String)] = [
            (UIText.title(.english), UIText.title(.turkish)),
            (UIText.askPlaceholder(.english), UIText.askPlaceholder(.turkish)),
            (UIText.filterPlaceholder(.english), UIText.filterPlaceholder(.turkish)),
            (UIText.budget("low", .english), UIText.budget("low", .turkish)),
            (UIText.pickLabel("best_quality", .english), UIText.pickLabel("best_quality", .turkish)),
        ]

        for (english, turkish) in pairs {
            XCTAssertFalse(english.isEmpty)
            XCTAssertFalse(turkish.isEmpty)
            XCTAssertNotEqual(english, turkish, "`\(english)` was never translated")
        }
    }

    /// **Keyed on the engine's ID, never on its English title.** The id is the contract (D-127);
    /// the title is the product, and six titles changed at M12-W2 alone. Keying on the title would
    /// break the Turkish screen every time somebody improved an English name.
    func testASurfaceIsTranslatedByItsIdNotItsEnglishName() {
        XCTAssertEqual(
            UIText.surface(id: "abstract", engineTitle: "Puzzles & pattern finding", .turkish),
            UIText.surface(id: "abstract", engineTitle: "Something else entirely", .turkish),
            "the Turkish name follows the English one, so renaming a title breaks the translation"
        )
    }

    func testAllNineSurfacesHaveATurkishName() {
        let ids = ["coding", "agentic-coding", "assistant", "everyday", "expert",
                   "mathematics", "computer-use", "abstract", "web-dev"]

        for id in ids {
            let turkish = UIText.surface(id: id, engineTitle: "ENGINE", .turkish)
            XCTAssertNotEqual(turkish, "ENGINE", "`\(id)` falls back to the engine's English")
        }
    }

    /// A surface this build has not heard of still appears, in English. Hiding a surface the
    /// engine serves would be a worse answer than showing it in the wrong language.
    func testAnUnknownSurfaceShowsTheEnginesNameRatherThanVanishing() {
        XCTAssertEqual(UIText.surface(id: "quantum", engineTitle: "Quantum", .turkish), "Quantum")
    }

    func testTheBudgetCapKeepsItsFigureInBothLanguages() {
        let low = BudgetOption(id: "low", blendedCapPerM: 2.0)

        XCTAssertEqual(low.capLabel(in: .english), "under $2/1M")
        XCTAssertEqual(low.capLabel(in: .turkish), "$2/1M altı")
    }

    func testTheSeeAllLineCountsTheSameInBothLanguages() {
        let english = UIText.seeAll(58, eligible: 25, .english)
        let turkish = UIText.seeAll(58, eligible: 25, .turkish)

        for number in ["58", "25"] {
            XCTAssertTrue(english.contains(number), english)
            XCTAssertTrue(turkish.contains(number), turkish)
        }
    }

    func testTheSeeAllLineDropsTheBudgetClauseWhenEverythingFits() {
        // The disclosure exists because the ranking is NOT budget-filtered; when the two agree
        // there is nothing to disclose and saying it anyway is noise (D-135's spirit).
        XCTAssertFalse(UIText.seeAll(44, eligible: 44, .turkish).contains("bütçenize"))
        XCTAssertFalse(UIText.seeAll(44, eligible: nil, .english).contains("fit your budget"))
    }
}
