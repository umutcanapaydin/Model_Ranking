//  M13-W4 — the card says what a number is out of (REQ-CMP-004), a cheap price is not printed as
//  free, and a pick no reader budgeted for is not called a budget pick.

import XCTest

@testable import ModelRankingEngine

final class ScoreFormTests: XCTestCase {
    /// REQ-CMP-004's citing tests, one per metric family, each in both languages.
    func testABoundedPercentageIsShownAgainstItsCeiling() {
        XCTAssertEqual(scoreText(83.5, metric: "% resolved", .english), "Score 83.5 / 100")
        XCTAssertEqual(scoreText(94.4, metric: "% correct", .turkish), "Puan 94.4 / 100")
        XCTAssertEqual(scoreText(100.0, metric: "% correct", .english), "Score 100 / 100")
    }

    func testAnEloRatingCarriesTheNameOfItsScaleAndNoInventedCeiling() {
        let text = scoreText(1504.2, metric: "elo", .english)

        XCTAssertEqual(text, "Score 1504.2 Elo")
        XCTAssertEqual(scoreText(1504.2, metric: "elo", .turkish), "Puan 1504.2 Elo")
        XCTAssertFalse(text?.contains("/") == true, "an unbounded scale was given a ceiling")
    }

    func testAnECIScoreIsNotPrintedBecauseItsScaleHasNeitherACeilingNorAName() {
        XCTAssertNil(scoreText(161.7, metric: "ECI", .english))
        XCTAssertNil(scoreText(161.7, metric: "eci", .turkish))
    }

    func testNoTwoMetricFamiliesAreRenderedInTheSameForm() {
        // Per FAMILY, not per surface (W4 review MINOR-5): a bounded score and an Elo rating must
        // not share a shape a reader could line up. Two surfaces of one family share the form, and
        // their section titles tell them apart; the prd row says so.
        let bounded = scoreText(83.5, metric: "% resolved", .english) ?? ""
        let elo = scoreText(1504.2, metric: "elo", .english) ?? ""

        XCTAssertTrue(bounded.hasSuffix("/ 100"))
        XCTAssertTrue(elo.hasSuffix("Elo"))
    }

    func testAPercentageAboveItsCeilingIsNotPrintedAgainstIt() {
        XCTAssertNil(scoreText(150.0, metric: "% correct", .english))
    }

    func testAScoreTheAppCannotReadIsNotPrinted() {
        for hostile in [Double.nan, .infinity, -3.0, 1e19] {
            XCTAssertNil(scoreText(hostile, metric: "% resolved", .english), "\(hostile)")
        }
    }

    func testAnUnknownMetricKeepsTheEnginesOwnLabel() {
        XCTAssertEqual(scoreText(0.8, metric: "f1", .english), "0.8 f1")
        XCTAssertEqual(scoreText(0.8, metric: "f1", .turkish), "0.8 f1")
    }

    func testTheFiguresLineAlwaysCarriesThePrice() {
        XCTAssertEqual(
            figuresLine(score: 83.5, metric: "% resolved", blendedPerM: 10.0, .english, ranked: true),
            "Score 83.5 / 100  ·  $10/1M"
        )
        XCTAssertEqual(
            figuresLine(score: 161.7, metric: "ECI", blendedPerM: 2.06, .english, ranked: true),
            "$2.06/1M", "an ECI card still states its price"
        )
    }

    /// W4 review MINOR-8: C1 replaced ECI's number WITH its rank. A card with no rank to show must
    /// not end up placing the model nowhere.
    func testARankOnlyScoreWithNoRankBesideItKeepsTheEnginesNumber() {
        for language in Language.allCases {
            XCTAssertEqual(
                figuresLine(score: 161.7, metric: "ECI", blendedPerM: 2.06, language, ranked: false),
                "161.7 ECI  ·  $2.06/1M"
            )
        }
        XCTAssertEqual(
            figuresLine(score: 83.5, metric: "% resolved", blendedPerM: 10.0, .english, ranked: false),
            "Score 83.5 / 100  ·  $10/1M", "a score that can be shown is shown the same way either way"
        )
        // W4 re-review NEW-2: the engine's number comes back only for a rank-only metric, never for
        // a score `scoreText` refused, such as a "percentage" above its ceiling.
        XCTAssertEqual(
            figuresLine(score: 150, metric: "% correct", blendedPerM: 2.06, .english, ranked: false),
            "$2.06/1M"
        )
    }

    func testThePriceIsNotLocalised() {
        XCTAssertEqual(priceTag(2.06), "$2.06/1M")
        XCTAssertEqual(priceTag(0.125), "$0.125/1M")
    }

    /// W4 review MINOR-4: the page line's `$0` defect, moved to the tag, and a price that exists on
    /// one line and not on the other.
    func testThePriceTagNeverPrintsZeroForAPriceThatIsNot() {
        XCTAssertEqual(priceTag(0.0004), "<$0.001/1M")
        XCTAssertEqual(priceTag(0.001), "$0.001/1M")
        XCTAssertEqual(priceTag(0), "—", "the page line says 'price unavailable' for the same value")
        XCTAssertEqual(priceTag(-0.0), "—")
    }
}

final class CheapPriceTests: XCTestCase {
    /// Seen on the M13-W3 simulator screenshot: DeepSeek V4 Flash at $0.13/1M read "about $0 per
    /// 1,500 pages of text". Rounding to whole dollars made a model that is not free look free.
    func testAPriceBelowADollarKeepsItsCents() {
        XCTAssertEqual(priceInPages(0.13), "about $0.13 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(0.13, in: .turkish), "1,500 sayfa metin için yaklaşık $0.13")
        XCTAssertEqual(priceInPages(0.75), "about $0.75 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(0.75, in: .turkish), "1,500 sayfa metin için yaklaşık $0.75")
    }

    /// Exact in both languages (W4 review MINOR-2): "about $0.01" would tell a reader that a
    /// $0.004 model costs a cent, and a substring check let that through in Turkish.
    func testAPriceBelowACentSaysSoInsteadOfPrintingZero() {
        XCTAssertEqual(priceInPages(0.004), "under $0.01 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(0.004, in: .turkish), "1,500 sayfa metin için $0.01'den az")
    }

    /// W4 review MINOR-3: the dollar boundary. $0.99 keeps its cents, and an amount that rounds to
    /// a dollar reads `$1` as a dollar does, never `$1.00` beside it.
    func testTheDollarBoundaryPrintsOneAmountOneWay() {
        XCTAssertEqual(priceInPages(0.99), "about $0.99 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(0.999), "about $1 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(1.0), "about $1 per 1,500 pages of text")
    }

    func testAWholeDollarPriceIsUnchanged() {
        XCTAssertEqual(priceInPages(10.0), "about $10 per 1,500 pages of text")
        XCTAssertEqual(priceInPages(1.03), "about $1 per 1,500 pages of text")
    }
}

final class PickLabelTests: XCTestCase {
    /// Plan §2 W4: with no budget control, a label implying the reader set a budget is false.
    func testTheCheapestAcceptablePickIsNotCalledABudgetPick() {
        XCTAssertEqual(UIText.pickLabel("budget_pick", .english), "AFFORDABLE PICK")
        XCTAssertEqual(UIText.pickLabel("budget_pick", .turkish), "UYGUN FİYATLI SEÇİM")
        for language in Language.allCases {
            let label = UIText.pickLabel("budget_pick", language)
            XCTAssertFalse(label.contains("BUDGET") || label.contains("BÜTÇE"), label)
        }
    }

    func testTheOtherLabelsAreUnchanged() {
        XCTAssertEqual(UIText.pickLabel("best_quality", .english), "BEST QUALITY")
        XCTAssertEqual(UIText.pickLabel("best_value", .turkish), "EN İYİ DEĞER")
    }
}

// MARK: - M14-W4: one score out of 100, per surface (D-143)

final class OutOf100Tests: XCTestCase {
    /// REQ-SCR-001: an anchored Elo reads out of 100, and a model exactly at the anchor reads 50.
    func testAnEloRatingAtItsAnchorReadsFiftyOutOfAHundred() {
        XCTAssertEqual(scoreText(1467.5, metric: "elo", .english, anchor: 1467.5), "Score 50 / 100")
        XCTAssertEqual(scoreText(1467.5, metric: "elo", .turkish, anchor: 1467.5), "Puan 50 / 100")
    }

    /// The Elo expectation, checked against numbers worked by hand: 400 points above the anchor is
    /// ten-to-one, 100/(1 + 10^-1) = 90.9.
    func testTheConversionIsTheEloExpectationAgainstTheAnchor() {
        XCTAssertEqual(scoreOutOf100(1800, metric: "elo", anchor: 1400)!, 90.909, accuracy: 0.001)
        XCTAssertEqual(scoreOutOf100(1000, metric: "elo", anchor: 1400)!, 9.091, accuracy: 0.001)
    }

    /// REQ-SCR-002: strictly monotonic, so the conversion can never reorder a ranking. Over a whole
    /// served-looking Elo board, descending in, strictly descending out.
    func testTheConversionNeverReordersARanking() {
        let board = stride(from: 1516.3, through: 1361.4, by: -0.7).map { $0 }
        let converted = board.compactMap { scoreOutOf100($0, metric: "elo", anchor: 1450.6) }

        XCTAssertEqual(converted.count, board.count)
        for (higher, lower) in zip(converted, converted.dropFirst()) {
            XCTAssertGreaterThan(higher, lower, "a lower rating read as a higher score")
        }
        XCTAssertTrue(converted.allSatisfy { (0...100).contains($0) })
    }

    /// A percentage is already out of 100: identity, with or without an anchor.
    func testAPercentageIsUnchangedByTheConversion() {
        XCTAssertEqual(scoreOutOf100(83.5, metric: "% resolved", anchor: nil), 83.5)
        XCTAssertEqual(scoreText(83.5, metric: "% resolved", .english, anchor: 1400), "Score 83.5 / 100")
    }

    /// No anchor, no conversion: an engine older than W4 renders exactly as before.
    func testWithoutAnAnchorTheNamedScaleStays() {
        XCTAssertEqual(scoreText(1504.2, metric: "elo", .english, anchor: nil), "Score 1504.2 Elo")
        XCTAssertNil(scoreOutOf100(1504.2, metric: "elo", anchor: nil))
        XCTAssertNil(scoreOutOf100(1504.2, metric: "elo", anchor: .nan))
    }

    /// D-143 leaves ECI undecided, so it stays rank-only even if an anchor were ever sent.
    func testECIStaysRankOnly() {
        XCTAssertNil(scoreOutOf100(161.7, metric: "eci", anchor: 150))
        XCTAssertNil(scoreText(161.7, metric: "ECI", .english, anchor: 150))
    }

    /// Cards and rows go through `figuresLine`, which must pass the anchor on.
    func testTheFiguresLineCarriesTheConvertedScore() {
        let line = figuresLine(
            score: 1467.5, metric: "elo", blendedPerM: 5.0, .english, ranked: true, anchor: 1467.5
        )
        XCTAssertTrue(line.hasPrefix("Score 50 / 100"), line)
    }

    /// Review m-2 (REQ-SCR-002): monotone for any anchor the engine can serve, over the whole span a
    /// served Elo board occupies (±400 Elo, at the served 0.1 resolution). Since D-162 the anchor is
    /// each surface's floor, derived from its board, so the anchors are a range, not a pinned list:
    /// every Elo floor served so far lies between 1150 and 1550.
    func testTheConversionNeverReordersOnAnyAnchor() {
        for anchor in stride(from: 1100.0, through: 1600.0, by: 12.5) {
            let board = stride(from: anchor + 400, through: anchor - 400, by: -0.1).map { $0 }
            let converted = board.compactMap { scoreOutOf100($0, metric: "elo", anchor: anchor) }
            XCTAssertEqual(converted.count, board.count, "anchor \(anchor)")
            XCTAssertTrue(
                zip(converted, converted.dropFirst()).allSatisfy { $0 > $1 }, "anchor \(anchor)"
            )
        }
    }

    /// Review S-4: an anchor nowhere near the score is broken data, not a reference. The card keeps
    /// the engine's own scale rather than reading every model as 0 / 100.
    func testAnUnreasonableAnchorIsRefused() {
        XCTAssertNil(scoreOutOf100(1450, metric: "elo", anchor: 1e300))
        XCTAssertNil(scoreOutOf100(1450, metric: "elo", anchor: -1e6))
        XCTAssertEqual(scoreText(1504.2, metric: "elo", .english, anchor: 1e300), "Score 1504.2 Elo")
        XCTAssertNotNil(scoreOutOf100(1450, metric: "elo", anchor: 1450 + 2000))
    }

    /// And the line under the card says what that 100 means, in both languages, only when anchored.
    func testTheScaleLineExplainsTheHundredOnlyWhenAnchored() {
        XCTAssertNotNil(anchoredScaleExplanation(for: "elo", anchored: true, in: .english))
        XCTAssertNotNil(anchoredScaleExplanation(for: "elo", anchored: true, in: .turkish))
        XCTAssertNil(anchoredScaleExplanation(for: "elo", anchored: false, in: .english))
        XCTAssertNil(anchoredScaleExplanation(for: "% correct", anchored: true, in: .english))
    }
}

/// Review M-1/M-2: the sentences on an anchored card speak the card's unit, never `Elo`.
final class OutOf100SentenceTests: XCTestCase {
    /// The assistant best-value card the seat measured: anchor 1400, a leader reading 65.0 / 100
    /// (1507.5) and a pick 25.5 Elo behind it reading 61.6. The sentence must say 3.4 points.
    func testTheTradeOffSaysPointsOutOf100NotElo() {
        let fact: [String: Any] = ["behind_by": 25.5, "unit": "Elo", "cheaper_by_percent": 90.0]
        let restated = anchoredFact(fact, leader: 1507.5, metric: "elo", anchor: 1400)
        let sentence = tradeOffSentence(restated, in: .english)!

        XCTAssertFalse(sentence.contains("Elo"), sentence)
        XCTAssertTrue(sentence.hasPrefix("3.4 points behind the best one"), sentence)
        XCTAssertTrue(tradeOffSentence(restated, in: .turkish)!.contains("puan"))
    }

    /// The floor is a POSITION: at the anchor it is exactly 50.
    func testTheFloorIsRestatedAsAPosition() {
        let fact: [String: Any] = ["reason": "cheapest_above_floor", "floor": 1400.0, "unit": "Elo"]
        let restated = anchoredFact(fact, leader: 1455.4, metric: "elo", anchor: 1400)
        XCTAssertEqual(restated["floor"] as? Double, 50)
        XCTAssertEqual(restated["unit"] as? String, "points")
    }

    /// All or nothing: one number that cannot be converted leaves the whole fact native, so a
    /// sentence never mixes Elo and points.
    func testAnUnconvertibleFactStaysWhole() {
        let fact: [String: Any] = ["behind_by": 25.5, "window": "thirty", "unit": "Elo"]
        let restated = anchoredFact(fact, leader: 1455.4, metric: "elo", anchor: 1400)
        XCTAssertEqual(restated["unit"] as? String, "Elo")
        XCTAssertEqual(restated["behind_by"] as? Double, 25.5)
    }

    /// Off an anchored Elo surface the fact is untouched.
    func testOtherScalesAreUntouched() {
        let fact: [String: Any] = ["behind_by": 4.0, "unit": "% correct"]
        XCTAssertEqual(
            anchoredFact(fact, leader: 90, metric: "% correct", anchor: nil)["behind_by"] as? Double, 4
        )
        XCTAssertEqual(
            anchoredFact(fact, leader: 1455.4, metric: "elo", anchor: nil)["unit"] as? String,
            "% correct"
        )
    }

    /// The tie note: the margin in points below the leader, never `Elo` above /100 rows. Which
    /// models are tied does not change (REQ-SCR-004): only the sentence's unit does.
    func testTheLeaderNoteSpeaksPointsWhenAnchored() {
        let ranges = rankRanges([1455.4, 1453.0, 1450.1, 1400.0], margin: 8)
        let native = leaderSentence(ranges: ranges, margin: 8, metric: "elo", .english)!
        let anchored = leaderSentence(
            ranges: ranges, margin: 8, metric: "elo", .english, leader: 1455.4, anchor: 1400
        )!

        XCTAssertTrue(native.contains("8 Elo"), native)
        XCTAssertFalse(anchored.contains("Elo"), anchored)
        XCTAssertTrue(anchored.contains("points"), anchored)
        XCTAssertEqual(ranges, rankRanges([1455.4, 1453.0, 1450.1, 1400.0], margin: 8))
    }
}
