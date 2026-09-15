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
