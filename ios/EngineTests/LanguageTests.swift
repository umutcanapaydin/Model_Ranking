//  Two languages composed from one truth. D-136, M12-W4.
//
//  The property that matters is not "the Turkish is present". It is that both sentences are
//  RENDERINGS of the same fact, so they cannot drift — which is precisely what a translated string
//  table cannot promise, and why the owner chose this architecture over `?lang=tr`.

import XCTest

@testable import ModelRankingEngine

final class LanguageCompositionTests: OfflineTestCase {

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
    /// M17-W1 (D-159): a surface whose own board is empty has no floor to clear.
    private let floorUnmeasured: [String: Any] = [
        "reason": "no_floor_measured", "unit": "points",
    ]

    // MARK: every reason speaks both languages

    func testEveryReasonTheEngineCanEmitHasBothSentences() {
        for fact in [highest, window, floorMet, floorMissed, floorUnmeasured] {
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
        for fact in [highest, window, floorMet, floorMissed, floorUnmeasured] {
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

final class LocalisedUnitTests: OfflineTestCase {

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
            // The page count is grouped as each language reads it (#63 finding 6), so it is compared
            // as the one number it is, and the amounts are compared digit for digit.
            let english = priceInPages(price, in: .english).replacingOccurrences(of: groupedPages(.english), with: "1500")
            let turkish = priceInPages(price, in: .turkish).replacingOccurrences(of: groupedPages(.turkish), with: "1500")
            let digits = { (text: String) in
                text.split(whereSeparator: { !$0.isNumber && $0 != "." }).map(String.init)
            }
            XCTAssertEqual(digits(english).sorted(), digits(turkish).sorted(),
                           "\(english)  vs  \(turkish)")
        }
    }
}

final class ScreenChromeTests: OfflineTestCase {

    /// The chrome is a string TABLE — a title, a placeholder, a button — and that is deliberate:
    /// a table is the right shape for text carrying no values, and the wrong shape for a sentence
    /// that quotes numbers. D-136 turns on exactly that distinction.
    func testEveryPieceOfChromeSpeaksBothLanguagesAndTheyDiffer() {
        let pairs: [(String, String)] = [
            (UIText.title(.english), UIText.title(.turkish)),
            (UIText.askPlaceholder(.english), UIText.askPlaceholder(.turkish)),
            (UIText.filterPlaceholder(.english), UIText.filterPlaceholder(.turkish)),
            (UIText.change(.english), UIText.change(.turkish)),
            (UIText.showing(.english), UIText.showing(.turkish)),
            (UIText.send(.english), UIText.send(.turkish)),
            (UIText.chooseSurface(.english), UIText.chooseSurface(.turkish)),
            (UIText.alternatives(.english), UIText.alternatives(.turkish)),
            (UIText.surfacesUnavailable(.english), UIText.surfacesUnavailable(.turkish)),
            (UIText.closestMeasured(.english), UIText.closestMeasured(.turkish)),
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

    func testEverySurfaceHasATurkishName() {
        let ids = ["coding", "agentic-coding", "assistant", "everyday", "expert",
                   "mathematics", "computer-use", "abstract", "web-dev", "document", "factuality",
                   "vision", "search", "search_factuality"]

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

final class HostileFactValueTests: OfflineTestCase {

    /// **BLOCKING-1 of the M12 Stage 4.0 review.** `Int(Double)` is not a conversion, it is an
    /// assertion that the value fits — and every number here arrives from `/v1`. A well-formed
    /// answer carrying `1e19`, or a negative price, killed the process with `SIGTRAP`.
    ///
    /// The client's own contract promises the opposite: an unreadable payload becomes
    /// `undecodable` and the screen says so. **A trap bypasses every failure path this app has.**
    ///
    /// These cases are the values a wire format permits, not the values a correct engine sends.
    /// That distinction is the reason they were untested: nobody had asked what the app does when
    /// the thing it trusts is wrong.
    private let hostile: [Double] = [
        1e19, -1e19, .infinity, -.infinity, .nan,
        .greatestFiniteMagnitude, -.greatestFiniteMagnitude, 0, -0.0, -1.0,
    ]

    func testNoPriceValueCanKillTheApp() {
        for value in hostile {
            for language in Language.allCases {
                let text = priceInPages(value, in: language)
                XCTAssertFalse(text.isEmpty, "\(value) produced nothing")
            }
        }
    }

    /// **This test asserted `XCTAssertNotNil` until M12-W5, and that was the wrong contract.**
    /// It was written at BLOCKING-1 to prove the app does not TRAP on a hostile number, and in
    /// proving it, it pinned the behaviour Stage 4.0 then filed as MAJOR-4: a sentence that
    /// survives a value it could not read is a sentence that has dropped the number and kept the
    /// claim. `nil` is the correct answer — the caller falls back to the engine's English, which
    /// D-136 guarantees is always present.
    ///
    /// The real contract has two halves, and only both together mean anything: **never trap, and
    /// never emit a sentence with the quantity missing.** Asserting the first alone is how the
    /// second was lost.
    private func assertSound(_ sentence: String?, _ label: String) {
        guard let sentence else { return }          // refusing is always sound
        for ghost in ["nan", "inf", "  ", " %", "% ", " ×", "-1", "e+"] {
            XCTAssertFalse(sentence.lowercased().contains(ghost),
                           "\(label): composed `\(sentence)` — the claim without the number")
        }
    }

    func testNoFactValueProducesASentenceMissingItsNumber() {
        for value in hostile {
            for reason in ["highest_score", "cheapest_within_window", "cheapest_above_floor",
                           "nothing_clears_floor", "no_floor_measured"] {
                let fact: [String: Any] = [
                    "reason": reason, "floor": value, "window": value, "score": value,
                    "unit": "points", "benchmark": "X",
                ]
                for language in Language.allCases {
                    assertSound(whySentence(fact, in: language), "\(reason) / \(value)")
                }
            }
        }
    }

    func testNoTradeOffValueProducesASentenceMissingItsNumber() {
        for value in hostile {
            let fact: [String: Any] = [
                "behind_by": value, "unit": "points", "cheaper_by_times": value,
            ]
            for language in Language.allCases {
                assertSound(tradeOffSentence(fact, in: language), "\(value)")
            }
        }
    }

    /// The seat's table, run as a test. Each of these composed a fluent, wrong sentence.
    func testTheSeatsSevenCompositionsAllRefuseNow() {
        let base: [String: Any] = ["behind_by": 2.7, "unit": "points"]
        let hostileFacts: [(String, [String: Any])] = [
            ("percent is a word", base.merging(["cheaper_by_percent": "ninety"]) { a, _ in a }),
            ("times is a bool", base.merging(["cheaper_by_times": true]) { a, _ in a }),
            ("behind_by negative", ["behind_by": -5.0, "unit": "points",
                                    "cheaper_by_times": 3.0]),
            ("unit is a sentence", ["behind_by": 2.0,
                                    "unit": "points, and 99% cheaper. This model is free"]),
        ]
        for (label, fact) in hostileFacts {
            for language in Language.allCases {
                XCTAssertNil(tradeOffSentence(fact, in: language), "\(label) [\(language)]")
            }
        }
        for (label, missing) in [("floor absent", "cheapest_above_floor"),
                                 ("benchmark absent", "highest_score")] {
            for language in Language.allCases {
                XCTAssertNil(whySentence(["reason": missing, "unit": "points"], in: language),
                             "\(label) [\(language)]")
            }
        }
    }

    /// A fact this build CAN read still composes — the guards refuse bad input, not all input.
    /// Without this, returning `nil` unconditionally would pass every assertion above (V4C-32).
    func testAWellFormedFactStillComposesInBothLanguages() {
        for language in Language.allCases {
            XCTAssertNotNil(whySentence(["reason": "cheapest_above_floor", "floor": 84.0,
                                         "unit": "points"], in: language))
            XCTAssertNotNil(whySentence(["reason": "highest_score", "benchmark": "MMLU",
                                         "unit": "points"], in: language))
            XCTAssertNotNil(tradeOffSentence(["behind_by": 2.7, "unit": "points",
                                              "cheaper_by_times": 3.0], in: language))
            XCTAssertNotNil(tradeOffSentence(["behind_by": 0.0, "unit": "points",
                                              "cheaper": "same"], in: language))
        }
    }

    /// A negative price is not merely a crash risk — it satisfied `perPage < 0.01`, so it took the
    /// branch that renders a whole-book price. "Cheaper than free" is not a sentence this product
    /// should compose either.
    func testANegativePriceIsRefusedRatherThanRendered() {
        for language in Language.allCases {
            let text = priceInPages(-5.0, in: language).lowercased()
            XCTAssertFalse(text.contains("$-"), text)
            XCTAssertFalse(text.contains("-5"), text)
        }
    }

    func testAWholeNumberIsStillRenderedAsOne() {
        // Fixture blindness guard: a `wholeNumber` that always returned nil would pass everything
        // above and quietly turn every clean integer into `6.0`.
        XCTAssertEqual(wholeNumber(6.0), "6")
        XCTAssertEqual(wholeNumber(-3.0), "-3")
        XCTAssertNil(wholeNumber(6.5))
        XCTAssertNil(wholeNumber(.nan))
    }

    func testAnOrdinaryPriceIsUnaffected() {
        XCTAssertTrue(priceInPages(10.0, in: .english).contains("$10"))
        XCTAssertTrue(priceInPages(36.09, in: .english).contains("per page"))
    }
}

/// The router reads English. After M12-W4 the app asks in Turkish. Stage 4.0 MAJOR-7.
final class RouterLanguageTests: OfflineTestCase {
    /// The exact sentence the Turkish placeholder invites, plus questions a Turkish reader would
    /// actually type on this product.
    func testTurkishQuestionsAreDeclinedRatherThanScoredAsEnglish() {
        let turkish = [
            "Yapay zekânın ne yapmasını istiyorsun?",
            "Bana kod yazmasında yardım edecek en iyi model hangisi?",
            "Matematik problemlerini çözmek için hangi modeli seçmeliyim?",
            "En ucuz ama yeterince iyi olan model hangisi acaba?",
        ]
        for question in turkish {
            XCTAssertFalse(SimilarityRouter.readsEnglish(question.lowercased()), question)
        }
    }

    /// Without this, `readsEnglish` returning `false` unconditionally would satisfy the test above
    /// and silently disable tier 2 for everyone (V4C-32).
    func testEnglishQuestionsStillReachTheSimilarityTier() {
        let english = [
            "which model is best at writing code for me",
            "what should i use to solve hard maths problems",
            "i want the cheapest model that is still good enough",
            "who is the best at using a computer on my behalf",
        ]
        for question in english {
            XCTAssertTrue(SimilarityRouter.readsEnglish(question), question)
        }
    }

    /// A short question is often unclassifiable, and refusing those would break the path this tier
    /// exists to serve. Undetermined stays in — stated as a test so the choice is not a side
    /// effect of a confidence constant.
    func testShortAndUnclassifiableQuestionsAreNotRefused() {
        for question in ["swe bench", "elo", "coding", "gpt", ""] {
            XCTAssertTrue(SimilarityRouter.readsEnglish(question), question)
        }
    }
}

/// M18-W1 second review B2 (REQ-DEV-001): the address under a failure to reach the engine, in both
/// languages.
final class EngineAddressLanguageTests: OfflineTestCase {
    func testTheEngineAddressLineSpeaksBothLanguages() {
        let address = "http://my-mac.local:8080"
        XCTAssertEqual(UIText.engineAddress(.english, address), "Engine address: http://my-mac.local:8080")
        XCTAssertEqual(UIText.engineAddress(.turkish, address), "Motor adresi: http://my-mac.local:8080")
    }
}

/// M17-W5 review M4: a board added by a refinement is named as its chip is, and a chip says what a
/// tap on it does, in both languages.
final class CombinedListLanguageTests: OfflineTestCase {

    private func board(_ id: String, benchmark: String) -> BoardStandings {
        BoardStandings(id: id, benchmark: benchmark, metric: "elo", rankingEffort: nil, evidenceDate: nil,
                       observedAt: nil, attribution: "cite", standings: [])
    }

    func testARefinementBoardIsNamedAsItsChipIs() {
        let french = Refinements.table.first { $0.value == "french" }!
        let slice = board(french.board, benchmark: "Arena text (french)")
        XCTAssertEqual(boardTitle(slice, refinements: [french], .turkish), "Arena text · Fransızca")
        XCTAssertEqual(boardTitle(slice, refinements: [french], .english), "Arena text · French")
        let primary = board("arena_document", benchmark: "Arena document")
        XCTAssertEqual(boardTitle(primary, refinements: [french], .turkish), "Arena document")
    }

    func testAChipSaysWhatATapDoes() {
        let french = Refinements.table.first { $0.value == "french" }!
        XCTAssertEqual(UIText.chipAction(french, removed: false, .english), "Remove the French board")
        XCTAssertEqual(UIText.chipAction(french, removed: true, .english), "Add the French board back")
        XCTAssertEqual(UIText.chipAction(french, removed: false, .turkish), "Fransızca panosunu çıkar")
        XCTAssertEqual(UIText.chipAction(french, removed: true, .turkish), "Fransızca panosunu geri ekle")
    }

    func testTheCombinedListSaysItIsTheProductsOwnInBothLanguages() {
        // D-160 clause 3 (plan P3, second review M8): the list is the product's combination, not a
        // published leaderboard, and says how many models and boards it holds.
        XCTAssertEqual(UIText.combinedNote(models: 34, boards: 2, .english),
                       "The app's own list: 34 models ranked on all 2 boards, ordered by their places on each. "
                           + "No leaderboard publishes this order.")
        XCTAssertEqual(UIText.combinedNote(models: 34, boards: 2, .turkish),
                       "Uygulamanın kendi listesi: 2 panonun hepsinde yer alan 34 model, her panodaki sıralarına "
                           + "göre dizildi. Bu sırayı hiçbir liste yayımlamıyor.")
    }

    func testTheDetailsSentencesSayTheirFactsInBothLanguages() {
        // Tester M2: the per-board efforts, a model's place on a board, and the empty list.
        XCTAssertEqual(UIText.boardEfforts(["high", "unspecified"], .english),
                       "Effort levels of the models in this list: high, unspecified")
        XCTAssertEqual(UIText.boardEfforts(["high", "unspecified"], .turkish),
                       "Bu listedeki modellerin çaba düzeyleri: yüksek, belirtilmemiş")
        XCTAssertEqual(UIText.placeOn("Arena text · French", place: 3, .english), "#3 on Arena text · French")
        XCTAssertEqual(UIText.placeOn("Arena text · Fransızca", place: 3, .turkish),
                       "Arena text · Fransızca listesinde #3")
        XCTAssertEqual(UIText.combinedEmpty(.english),
                       "No model is ranked on every one of these boards. Remove a board above to see a list.")
        XCTAssertEqual(UIText.combinedEmpty(.turkish),
                       "Bu panoların hepsinde yer alan bir model yok. Liste için yukarıdan bir panoyu çıkar.")
    }
}

/// #96 (M18-W1 review K4): the failure screen's title and address line spoke the reader's language and
/// the sentences under them did not.
final class FailureLanguageTests: OfflineTestCase {
    private let every: [EngineError] = [
        .unreachable("refused"), .timedOut(seconds: 15), .insecureTransport, .offline,
        .refused(status: 503, code: "unavailable", message: "The evidence database is unavailable."),
        .undecodable("x"),
    ]

    func testEveryFailureSaysWhatHappenedInBothLanguages() {
        XCTAssertEqual(EngineError.unreachable("x").errorDescription(.turkish), "Motor yanıt vermiyor.")
        XCTAssertEqual(EngineError.timedOut(seconds: 15).errorDescription(.turkish),
                       "Motor 15 saniye içinde yanıt vermedi.")
        for error in every {
            XCTAssertEqual(error.errorDescription(.english), error.errorDescription,
                           "the English sentence moved: \(error)")
            XCTAssertNotNil(error.errorDescription(.turkish))
        }
    }

    func testEveryRemedyIsInBothLanguagesAndTheEnginesRefusalIsNotRepeated() {
        XCTAssertEqual(EngineError.offline.recovery(.turkish),
                       "Bu cihazın internet bağlantısı yok. Yeniden bağlan ve tekrar dene.")
        for error in every {
            XCTAssertEqual(error.recovery(.english), error.recovery, "the English remedy moved: \(error)")
            XCTAssertEqual(error.recovery(.turkish) == nil, error.recovery == nil,
                           "a remedy exists in one language only: \(error)")
        }
    }

    /// The engine's own refusal is shown as the engine sent it (#96): it is the engine's sentence,
    /// and this app has no fact to compose it from.
    func testTheEnginesRefusalIsShownAsSent() {
        let refusal = EngineError.refused(status: 503, code: "unavailable", message: "Down for a rebuild.")
        XCTAssertEqual(refusal.errorDescription(.turkish), "Down for a rebuild.")
    }
}

/// #63 findings 5, 6 and 7 (M18-W2).
final class TurkishWordingTests: OfflineTestCase {
    /// "SORUN" reads as "problem"; the label means "your question".
    func testTheQuestionLabelSaysQuestion() {
        XCTAssertEqual(UIText.questionEyebrow(.turkish), "SORU")
    }

    /// "1,500 sayfa" reads as one and a half pages in Turkish, where the comma is the decimal mark.
    func testThePageCountIsGroupedTheWayEachLanguageReadsIt() {
        XCTAssertEqual(groupedPages(.turkish), "1.500")
        XCTAssertEqual(groupedPages(.english), "1,500")
    }

    func testADateIsSaidInWordsInBothLanguages() {
        XCTAssertEqual(readableDate("2026-04-20", .turkish), "20 Nisan 2026")
        XCTAssertEqual(readableDate("2026-04-20", .english), "20 April 2026")
        XCTAssertEqual(readableDate("2026-01-05T00:00:00Z", .turkish), "5 Ocak 2026")
        XCTAssertNil(readableDate("2026-02-30", .english), "a day February cannot have")
        XCTAssertNil(readableDate("unknown", .turkish))
    }

    /// The app says "sen" everywhere; the formal "siz" crept into five sentences.
    func testTheRegisterIsSenInEverySentenceThatHadSiz() {
        let manual = RoutingOutcome(categoryID: "assistant", tier: .manual, unmeasured: true, alternatives: [])
        let sentences = [
            routingNotice(manual, .turkish),
            routingNotice(RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: false,
                                         alternatives: []), .turkish),
            UIText.seeAll(44, eligible: 40, .turkish),
            UIText.surfacesUnavailable(.turkish),
            whySentence(["reason": "nothing_clears_floor", "floor": 65.0, "unit": "points"], in: .turkish) ?? "",
        ]
        for sentence in sentences {
            XCTAssertNil(sentence.range(of: #"(nuz|nüz|nız|niz|unun|edin|dokunun|çekin)\b"#, options: .regularExpression),
                         "formal register: \(sentence)")
        }
    }
}

/// #63 findings 9, 13, 14 and new finding A (M18-W2): what the screen says about itself.
final class ScreenExplanationTests: OfflineTestCase {
    /// Finding 9: "#4–13" with nothing saying why a position is a range.
    func testARangeIsExplainedOnceWhereOneIsShown() {
        let ranges = [RankRange(best: 1, worst: 1), RankRange(best: 2, worst: 4), RankRange(best: 2, worst: 4)]
        XCTAssertEqual(rangeNote(ranges: ranges, shown: [0, 1], .english),
                       "A range such as #2–4 means the benchmark cannot tell this model apart from the "
                       + "others in those places.")
        XCTAssertEqual(rangeNote(ranges: ranges, shown: [0, 1], .turkish),
                       "#2–4 gibi bir aralık, ölçümün bu modeli o sıralardaki diğerlerinden ayırt "
                       + "edemediği anlamına gelir.")
        XCTAssertNil(rangeNote(ranges: ranges, shown: [0], .english), "no range on screen, nothing to explain")
    }

    /// M20-W4 (#208, D-188): the caption under the question, the primary board's toggle and the
    /// half-weight note, each in both languages.
    func testTheM20SentencesAreSaidInBothLanguages() {
        // The W4 review's M5: one caption per state, so a phone that cannot run the model is not told
        // it is turned off.
        let states: [OnDeviceState] = [.available, .notEligible, .turnedOff, .downloading, .unavailable]
        for state in states {
            XCTAssertNotEqual(UIText.onDeviceCaption(state, .english), UIText.onDeviceCaption(state, .turkish))
        }
        XCTAssertEqual(Set(states.map { UIText.onDeviceCaption($0, .english) }).count, states.count)
        XCTAssertEqual(Set(states.map { UIText.onDeviceCaption($0, .turkish) }).count, states.count)
        XCTAssertEqual(UIText.onDeviceCaption(.available, .english), "Apple Intelligence enhanced")
        XCTAssertNotEqual(UIText.primaryOnItsOwn(.english), UIText.primaryOnItsOwn(.turkish))
        XCTAssertNotEqual(UIText.backToCombined(.english), UIText.backToCombined(.turkish))
        let aider = [NamedBoard(name: "Aider", date: .unknown)]
        XCTAssertNotEqual(UIText.olderBoards(aider, .english), UIText.olderBoards(aider, .turkish))
    }

    /// The combined list's tied places ("1, 1, 3") say why, once.
    func testTiedPlacesOnTheCombinedListAreExplained() {
        XCTAssertNotNil(UIText.tiedPlaces(.turkish))
        XCTAssertNotEqual(UIText.tiedPlaces(.turkish), UIText.tiedPlaces(.english))
    }

    /// Finding 13: three surfaces whose names blur. Each surface the engine serves has one line saying
    /// what it is for, in both languages.
    func testEverySurfaceHasALineSayingWhatItIsFor() {
        for id in ["coding", "agentic-coding", "assistant", "everyday", "expert", "mathematics", "computer-use",
                   "abstract", "web-dev", "document", "factuality", "vision", "search", "search_factuality"] {
            let english = UIText.surfaceBlurb(id, .english)
            let turkish = UIText.surfaceBlurb(id, .turkish)
            XCTAssertNotNil(english, id)
            XCTAssertNotNil(turkish, id)
            XCTAssertNotEqual(english, turkish, id)
        }
        let blurred = ["factuality", "search", "search_factuality"].compactMap { UIText.surfaceBlurb($0, .turkish) }
        XCTAssertEqual(Set(blurred).count, 3)
        XCTAssertNil(UIText.surfaceBlurb("a-surface-this-build-does-not-know", .english))
    }

    /// Finding 14: the register's sheet says what it is for.
    func testTheGapRegisterSaysWhatItIsFor() {
        XCTAssertNotEqual(UIText.gapsPurpose(.turkish), UIText.gapsPurpose(.english))
        XCTAssertTrue(UIText.gapsPurpose(.english).contains("this device"))
    }
}

/// #78 (M18-W2 P6): the combined list's access filter says what it does.
final class AccessFilterLanguageTests: OfflineTestCase {
    func testTheFilterSaysWhatItDoesInBothLanguages() {
        XCTAssertEqual(UIText.accessFilter(.english), "Only models with an API or open weights")
        XCTAssertEqual(UIText.accessFilter(.turkish), "Yalnızca API'si ya da açık ağırlıkları olan modeller")
        XCTAssertEqual(UIText.accessFilterCount(shown: 2, of: 3, .english), "2 of 3 shown; places are among all 3")
        XCTAssertEqual(UIText.accessFilterCount(shown: 2, of: 3, .turkish),
                       "3 modelin 2 tanesi gösteriliyor; sıralar 3 modelin tamamı içinde")
    }
}

/// Review K2 (M18-W2): effort names (high, max, xhigh, unspecified) sat untranslated in Turkish sentences.
final class EffortNameTests: OfflineTestCase {
    func testEveryEffortTheEngineServesHasATurkishName() {
        let turkish = ["minimal": "en düşük", "low": "düşük", "medium": "orta", "high": "yüksek",
                       "xhigh": "çok yüksek", "max": "en yüksek", "unspecified": "belirtilmemiş"]
        for (effort, name) in turkish {
            XCTAssertEqual(effortName(effort, .turkish), name)
            XCTAssertEqual(effortName(effort, .english), effort, "English keeps the engine's word")
        }
        XCTAssertEqual(effortName("ultra", .turkish), "ultra", "a level this build does not know keeps its name")
    }
}
