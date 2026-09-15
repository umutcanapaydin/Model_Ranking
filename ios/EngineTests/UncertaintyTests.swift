//  M13-W2 — say only what the engine's own numbers support (REQ-UNC-001, REQ-UNC-002).
//
//  Written against the shapes the shipping artifact actually has: `expert` with 25 of 50 models
//  inside a 5-point margin of the leader, `assistant` on Elo with an 8-point margin, `everyday` on
//  ECI with 0.5, and the coding budget pick whose only second score comes from a board last run more
//  than 300 days before the artifact's anchor.
//
//  REQ-UNC-001 was re-decided by the owner on 2026-09-15: rank RANGES, not the greedy bands of the
//  council's D1 ruling, after the first review measured bands printing 47 adjacent within-margin
//  pairs in different positions.

import XCTest

@testable import ModelRankingEngine

/// The margins the shipping engine publishes, one per surface (`categories.py`).
private let shippingMargins: [Double] = [1.5, 8.0, 1.5, 0.5, 5.0, 9.5, 0.8, 1.0, 6.8]

final class RankRangeTests: XCTestCase {
    /// The `expert` shape: leader 94.4, margin 5.0 points.
    private let expert: [Double] = [94.4, 94.1, 91.0, 89.0, 80.0, 79.9, 70.0]

    func testEachPositionIsTheRangeTheMarginCannotNarrow() {
        let ranges = rankRanges(expert, margin: 5.0)

        // 89.0 is 5.4 below the leader: clearly behind it, so it cannot be first. It is 5.1 below
        // 94.1, inside the margin plus one rounding step, so it could be second.
        XCTAssertEqual(ranges.map(\.best), [1, 1, 1, 2, 5, 5, 7])
        XCTAssertEqual(ranges.map(\.worst), [3, 4, 4, 4, 6, 6, 7])
    }

    func testTwoModelsInsideTheMarginOfEachOtherAlwaysOverlap() {
        // REQ-UNC-001's criterion as a property, over every shipping margin and a thousand
        // rankings: no pair the margin cannot separate is ever presented as ordered. This is the
        // test the greedy bands failed 47 times on the shipping artifact.
        var seed: UInt64 = 0x9E37_79B9_7F4A_7C15
        func next() -> Double {
            seed = seed &* 6_364_136_223_846_793_005 &+ 1_442_695_040_888_963_407
            return Double(seed >> 11) / Double(1 << 53)
        }
        for margin in shippingMargins {
            for _ in 0..<120 {
                let count = 2 + Int(next() * 40)
                let spread = margin * (1 + next() * 8)
                var scores = (0..<count).map { _ in (next() * spread * 10).rounded() / 10 }
                // The engine's order: highest first. Built without `sorted`, which the client
                // contract tests ban from the app target and which would be odd to lean on here.
                for i in scores.indices {
                    for j in scores.indices.dropFirst(i + 1) where scores[j] > scores[i] {
                        scores.swapAt(i, j)
                    }
                }
                let ranges = rankRanges(scores, margin: margin)
                for i in scores.indices {
                    for j in scores.indices where i < j && scores[i] - scores[j] <= margin {
                        XCTAssertTrue(
                            ranges[j].best <= ranges[i].worst,
                            "\(scores[i]) and \(scores[j]) are \(scores[i] - scores[j]) apart, "
                                + "inside \(margin), and were printed as ordered: "
                                + "\(ranges[i]) above \(ranges[j])"
                        )
                    }
                }
            }
        }
    }

    func testModelsClearlyApartKeepExactPositions() {
        XCTAssertEqual(rankRanges([90.0, 80.0, 70.0], margin: 5.0),
                       [RankRange(best: 1, worst: 1), RankRange(best: 2, worst: 2),
                        RankRange(best: 3, worst: 3)])
    }

    func testOneRoundingStepIsConcededInTheDirectionThatCannotOrderATie() {
        // Served 94.4 and 89.3 can be raw 94.35 and 89.35: exactly 5.0 apart, which the engine
        // calls a close call. So they must overlap. The gap is also `5.1000000000000085` in a
        // Double, so this fails if the float tolerance is removed as well as if the rounding step is.
        XCTAssertEqual(rankRanges([94.4, 89.3], margin: 5.0),
                       [RankRange(best: 1, worst: 2), RankRange(best: 1, worst: 2)])
        // One step further and no rounding can put them inside the margin.
        XCTAssertEqual(rankRanges([94.4, 89.2], margin: 5.0),
                       [RankRange(best: 1, worst: 1), RankRange(best: 2, worst: 2)])
    }

    func testNoMarginMeansTodaysExactPositionsNotOneBigTie() {
        // An engine older than D-138 sends no margin. The wrong fallback is "everything tied".
        XCTAssertEqual(rankRanges(expert, margin: nil),
                       expert.indices.map { RankRange(best: $0 + 1, worst: $0 + 1) })
    }

    func testAMarginThatIsNotAUsableNumberIsTreatedAsNone() {
        for margin in [-1.0, .nan, .infinity] {
            XCTAssertTrue(rankRanges(expert, margin: margin).allSatisfy(\.isExact),
                          "margin \(margin) produced ranges")
        }
    }

    func testAnEmptyRankingHasNoRanges() {
        XCTAssertEqual(rankRanges([], margin: 5.0), [])
    }

    func testTheLabelSaysTheRangeOrTheExactPosition() {
        let ranges = rankRanges(expert, margin: 5.0)

        XCTAssertEqual(rankLabel(at: 0, in: ranges, of: 50, .english), "#1–3 of 50")
        XCTAssertEqual(rankLabel(at: 6, in: ranges, of: 50, .english), "#7 of 50")
    }

    func testTheLabelIsTurkishOnATurkishScreen() {
        let ranges = rankRanges(expert, margin: 5.0)

        XCTAssertEqual(rankLabel(at: 1, in: ranges, of: 50, .turkish), "50 model içinde #1–4")
        XCTAssertEqual(rankLabel(at: 6, in: ranges, of: 50, .turkish), "50 model içinde #7")
    }

    func testShortLabelsForTheRankingList() {
        let ranges = rankRanges(expert, margin: 5.0)

        XCTAssertEqual((0..<7).map { shortRankLabel(at: $0, in: ranges) },
                       ["1–3", "1–4", "1–4", "2–4", "5–6", "5–6", "7"])
    }

    func testAnIndexOutsideTheRankingHasNoLabel() {
        let ranges = rankRanges(expert, margin: 5.0)

        XCTAssertNil(rankLabel(at: 7, in: ranges, of: 7, .english))
        XCTAssertNil(shortRankLabel(at: -1, in: ranges))
    }

    func testRangesOnEachMetricFamilyWithTheMarginsTheEngineShips() {
        let pairOverTheRest = [RankRange(best: 1, worst: 2), RankRange(best: 1, worst: 2),
                               RankRange(best: 3, worst: 3)]
        // Elo, `assistant`, margin 8.0: the shipping leader pair is 1.5 Elo apart.
        XCTAssertEqual(rankRanges([1504.2, 1502.7, 1476.5], margin: 8.0), pairOverTheRest)
        // ECI, `everyday`, margin 0.5.
        XCTAssertEqual(rankRanges([161.7, 161.3, 160.0], margin: 0.5), pairOverTheRest)
        // `coding`, margin 1.5, a pair exactly at the margin.
        XCTAssertEqual(rankRanges([83.5, 82.0, 77.6], margin: 1.5), pairOverTheRest)
        // `computer-use`, margin 0.8.
        XCTAssertEqual(rankRanges([60.2, 59.5, 58.0], margin: 0.8), pairOverTheRest)
        // `mathematics`, margin 9.5: AIME has three models at exactly 100.0.
        XCTAssertEqual(rankRanges([100.0, 100.0, 100.0, 94.4, 88.0], margin: 9.5).map(\.worst),
                       [4, 4, 4, 5, 5])
    }
}

final class LeaderSentenceTests: XCTestCase {
    func testHowManyTheBenchmarkCannotSeparateFromTheLeaderIsStatedOnce() {
        let ranges = rankRanges([94.4, 94.1, 91.0, 80.0], margin: 5.0)

        XCTAssertEqual(
            leaderSentence(ranges: ranges, margin: 5.0, metric: "% correct", .english),
            "The top 3 of 4 are too close to the leader for this benchmark to separate — its "
                + "margin is 5 points — so read them as tied, not as ordered."
        )
    }

    func testNothingIsSaidWhenTheLeaderStandsAlone() {
        let ranges = rankRanges([83.5, 77.6, 70.0], margin: 1.5)

        XCTAssertNil(leaderSentence(ranges: ranges, margin: 1.5, metric: "% resolved", .english))
    }

    func testNothingIsSaidWithoutAMargin() {
        let ranges = [RankRange(best: 1, worst: 2), RankRange(best: 1, worst: 2)]

        XCTAssertNil(leaderSentence(ranges: ranges, margin: nil, metric: "elo", .english))
    }

    func testAMarginOfOneIsOnePointAndAnEloMarginIsCountedInElo() {
        let abstract = leaderSentence(ranges: rankRanges([80.0, 79.5], margin: 1.0), margin: 1.0,
                                      metric: "% correct", .english)
        let elo = leaderSentence(ranges: rankRanges([1504.2, 1502.7], margin: 8.0), margin: 8.0,
                                 metric: "elo", .english)

        XCTAssertTrue(abstract?.contains("its margin is 1 point —") == true, abstract ?? "nil")
        XCTAssertTrue(elo?.contains("its margin is 8 Elo") == true, elo ?? "nil")
    }

    func testTheSentenceIsTurkishOnATurkishScreen() {
        let ranges = rankRanges([94.4, 94.1, 91.0, 80.0], margin: 5.0)

        XCTAssertEqual(
            leaderSentence(ranges: ranges, margin: 5.0, metric: "% correct", .turkish),
            "4 modelin ilk 3 tanesi lidere bu benchmark'ın ayırt edemeyeceği kadar yakın — payı "
                + "5 puan — yani sıralı değil berabere okuyun."
        )
    }
}

final class EvidenceBreadthTests: XCTestCase {
    func testASecondScoreFromAStaleBoardCarriesItsAge() {
        // REQ-UNC-002's citing case: a secondary more than 180 days old carries that age. This is
        // the shipping coding budget pick, verbatim.
        XCTAssertEqual(
            evidenceBreadth(verdict: "Medium", secondaryScore: 74.2,
                            secondaryBenchmark: "Aider polyglot", secondaryAgeDays: 332,
                            evidenceDate: "2026-02-17", .english),
            "Measured on 1 benchmark (run 2026-02-17). Aider polyglot also scored it, but last "
                + "ran 332 days ago, so it is not counted."
        )
    }

    func testTheAgeSurvivesTheTurkishScreen() {
        let text = evidenceBreadth(verdict: "Medium", secondaryScore: 74.2,
                                   secondaryBenchmark: "Aider polyglot", secondaryAgeDays: 332,
                                   evidenceDate: "2026-02-17", .turkish)

        XCTAssertEqual(text, "1 benchmark ile ölçüldü (2026-02-17 tarihli). Ayrıca Aider polyglot "
                       + "sonucu var, ama en son 332 gün önce çalıştırılmış; bu yüzden sayılmıyor.")
    }

    func testAPickTheSecondBoardNeverScoredIsNotToldItDid() {
        // The Tester seat's surviving mutant: the board and its age arrive for EVERY pick on the
        // surface, and removing the `secondaryScore` guard stayed green.
        XCTAssertEqual(
            evidenceBreadth(verdict: "Medium", secondaryScore: nil,
                            secondaryBenchmark: "Aider polyglot", secondaryAgeDays: 332,
                            evidenceDate: "2026-02-17", .english),
            "Measured on 1 benchmark (run 2026-02-17)."
        )
    }

    func testAnUnavailableAgeClaimsOnlyThatItIsUnavailable() {
        // `null` is either an undated board or an artifact that could not be read (D-138), and
        // "publishes no run dates" would be false about Aider in the second case.
        XCTAssertEqual(
            evidenceBreadth(verdict: "Medium", secondaryScore: 88.0, secondaryBenchmark: "MMLU",
                            secondaryAgeDays: nil, evidenceDate: nil, .english),
            "Measured on 1 benchmark. MMLU also scored it, but its run dates are not available, so "
                + "it is not counted."
        )
    }

    func testTwoCurrentBenchmarksStateTheSecondOnesAge() {
        XCTAssertEqual(
            evidenceBreadth(verdict: "High", secondaryScore: 80.0,
                            secondaryBenchmark: "Aider polyglot", secondaryAgeDays: 17,
                            evidenceDate: "2026-08-01", .english),
            "Measured on 2 independent benchmarks (run 2026-08-01). Aider polyglot last ran 17 "
                + "days ago."
        )
    }

    func testOneBenchmarkAndNothingElse() {
        XCTAssertEqual(
            evidenceBreadth(verdict: "Medium", secondaryScore: nil, secondaryBenchmark: nil,
                            secondaryAgeDays: nil, evidenceDate: "2026-04-20", .english),
            "Measured on 1 benchmark (run 2026-04-20)."
        )
    }

    func testAVerdictThisBuildDoesNotKnowShowsTheEnginesOwnBasis() {
        XCTAssertNil(evidenceBreadth(verdict: "Very high", secondaryScore: nil,
                                     secondaryBenchmark: nil, secondaryAgeDays: nil,
                                     evidenceDate: nil, .english))
        XCTAssertEqual(
            evidenceLine(verdict: "Very high", basis: "one independent benchmark (DeepSWE)",
                         secondaryScore: nil, secondaryBenchmark: nil, secondaryAgeDays: nil,
                         evidenceDate: nil, .english),
            "one independent benchmark (DeepSWE)"
        )
    }

    func testAPayloadThatContradictsItselfShowsNothingRatherThanRepeatingIt() {
        // "High" means two benchmarks; with no second score there is no second benchmark. The
        // first version fell back to the engine's basis here, which reads "two independent
        // benchmarks": the contradiction, printed as a fact (M13-W2 review MINOR-3).
        XCTAssertNil(evidenceLine(verdict: "High", basis: "two independent benchmarks (A + B)",
                                  secondaryScore: nil, secondaryBenchmark: "B",
                                  secondaryAgeDays: 3, evidenceDate: nil, .english))
    }

    func testNoRenderingEverCallsACoverageCountAConfidence() {
        // REQ-UNC-002's first clause, over every branch and both languages.
        for language in Language.allCases {
            for verdict in ["High", "Medium"] {
                for age in [nil, 17, 332] as [Int?] {
                    for secondary in [nil, 74.2] as [Double?] {
                        guard let text = evidenceLine(
                            verdict: verdict, basis: "unused", secondaryScore: secondary,
                            secondaryBenchmark: "Aider polyglot", secondaryAgeDays: age,
                            evidenceDate: "2026-02-17", language
                        ) else { continue }
                        let folded = text.lowercased()
                        XCTAssertFalse(folded.contains("confiden"), text)
                        XCTAssertFalse(folded.contains("güven"), text)
                    }
                }
            }
        }
    }

    func testAnAgeThatCannotBeADayCountIsNotPrintedAsOne() {
        let text = evidenceBreadth(verdict: "Medium", secondaryScore: 74.2,
                                   secondaryBenchmark: "Aider polyglot", secondaryAgeDays: -4,
                                   evidenceDate: nil, .english)

        XCTAssertFalse(text?.contains("-4") == true, text ?? "nil")
        XCTAssertTrue(text?.contains("not available") == true, text ?? "nil")
    }

    func testOnlyARealCalendarDayIsPrintedAsADate() {
        // `2026-+1-05`: `Int("+1")` parses, so only the digit check stands between a sign and a
        // printed month (the Tester seat's re-run survivor).
        for bad in ["last spring", "2026-99-99", "2026-13-01", "2026-02-30", "20260420xx",
                    "2026-+1-05"] {
            XCTAssertEqual(
                evidenceBreadth(verdict: "Medium", secondaryScore: nil, secondaryBenchmark: nil,
                                secondaryAgeDays: nil, evidenceDate: bad, .english),
                "Measured on 1 benchmark.", "`\(bad)` was printed as a date"
            )
        }
        XCTAssertEqual(isoDate("2028-02-29"), "2028-02-29", "a leap day is a real day")
    }

    func testABenchmarkNameThatIsASentenceIsNotInterpolated() {
        // The `label` guard, which exists because a crafted unit once composed a fluent false claim.
        let text = evidenceBreadth(verdict: "Medium", secondaryScore: 74.2,
                                   secondaryBenchmark: "x. This model is free", secondaryAgeDays: 9,
                                   evidenceDate: nil, .english)

        XCTAssertEqual(text, "Measured on 1 benchmark.")
    }
}

final class D138CategoryDecodingTests: XCTestCase {
    // Module-qualified: XCTest brings the Objective-C runtime's `Category` into scope as well.
    private func decode(_ json: String) throws -> ModelRankingEngine.Category {
        try JSONDecoder().decode(ModelRankingEngine.Category.self, from: Data(json.utf8))
    }

    func testTheThreeD138FieldsDecode() throws {
        let category = try decode("""
        {"id": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified",
         "metric": "% resolved", "ranking_effort": null, "close_call_margin": 1.5,
         "secondary_benchmark": "Aider polyglot", "secondary_age_days": 332}
        """)

        XCTAssertEqual(category.closeCallMargin, 1.5)
        XCTAssertEqual(category.secondaryBenchmark, "Aider polyglot")
        XCTAssertEqual(category.secondaryAgeDays, 332)
    }

    func testAnEngineOlderThanD138StillDecodes() throws {
        // The fields are optional so an older engine does not make the whole screen undecodable,
        // which is what a non-optional addition to a discovery struct would do.
        let category = try decode("""
        {"id": "expert", "title": "Hard science questions", "primary_benchmark": "GPQA Diamond",
         "metric": "% correct", "ranking_effort": null}
        """)

        XCTAssertNil(category.closeCallMargin)
        XCTAssertNil(category.secondaryAgeDays)
    }
}
