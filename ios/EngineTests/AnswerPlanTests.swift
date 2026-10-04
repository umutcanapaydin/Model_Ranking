//  M17-W5 P3 (#64, D-168 clause 7) -- what the screen shows for a routed question: today's cards
//  when one board is chosen, the product's combined list when more than one is.

import XCTest

@testable import ModelRankingEngine

final class AnswerPlanTests: OfflineTestCase {
    private func board(_ id: String, _ rows: [(String, Int)]) -> BoardStandings {
        BoardStandings(
            id: id, benchmark: "B \(id)", metric: "elo", rankingEffort: nil, evidenceDate: "2026-09-18",
            observedAt: "2026-09-25", attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "unspecified") }
        )
    }

    private func refinement(_ kind: RefinementKind, _ value: String) -> Refinement {
        Refinements.table.first { $0.kind == kind && $0.value == value }!
    }

    private var french: Refinement { refinement(.language, "french") }
    private var legal: Refinement { refinement(.domain, "legal") }

    private var data: Standings {
        let boards = [board("arena", [("a", 1), ("b", 2), ("c", 3)]),
                      board(french.board, [("b", 1), ("a", 2)]),
                      board(legal.board, [("a", 1), ("b", 2), ("c", 3)])]
        return Standings(apiVersion: "v1", attributions: [], boards: boards,
                         models: ["a", "b", "c"].map { StandingModel(id: $0, display: $0, vendor: "V",
                                                                    blendedPerM: 1, accessibility: nil) })
    }

    private func routed(_ refinements: [Refinement], unmeasured: Bool = false) -> RoutingOutcome {
        RoutingOutcome(categoryID: "assistant", tier: .model, unmeasured: unmeasured, refinements: refinements)
    }

    func testNoQuestionShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: nil, primaryBoard: "arena", standings: data, removed: []), .cards)
    }

    func testOneBoardShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([]), primaryBoard: "arena", standings: data, removed: []), .cards)
    }

    func testSeveralBoardsShowTheCombinedList() throws {
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", french.board])
        XCTAssertEqual(view.list.entries.map(\.model.id), ["a", "b"])
        XCTAssertEqual(view.sharedCount, 2, "the shared count is what the detail screen states (#54)")
        XCTAssertEqual(view.refinements, [french])
    }

    func testAnUnmeasuredQuestionShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french], unmeasured: true), primaryBoard: "arena",
                                  standings: data, removed: []), .cards)
    }

    func testAnEngineThatNamesNoPrimaryBoardShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: nil, standings: data, removed: []), .cards)
    }

    func testStandingsNotYetKeptShowTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: nil, removed: []), .cards)
    }

    func testARefinementTheReaderRemovedIsNotCombined() {
        let plan = answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: data,
                              removed: [french])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", legal.board])
        XCTAssertEqual(view.refinements, [french, legal], "a removed refinement stays on screen to restore")
        XCTAssertEqual(view.removed, [french])
    }

    func testRemovingEveryRefinementReturnsToTheCardsAndKeepsThemToRestore() {
        // Found on the simulator: removing the only refinement took its chip away with the list,
        // so it could not be put back without asking again.
        XCTAssertEqual(answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: data,
                                  removed: [french, legal]), .restorable([french, legal]))
    }

    func testARefinementWhoseBoardTheStandingsLackIsNotOfferedToRestore() {
        let missing = Standings(apiVersion: "v1", attributions: [], boards: [data.boards[0], data.boards[2]],
                                models: data.models)
        XCTAssertEqual(answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: missing,
                                  removed: [legal]), .restorable([legal]))
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: missing,
                                  removed: [french]), .cards)
    }

    func testNothingIsOfferedToRestoreWhenRestoringCouldNotCombine() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "nowhere", standings: data,
                                  removed: [french]), .cards)
        XCTAssertEqual(answerPlan(outcome: routed([french], unmeasured: true), primaryBoard: "arena",
                                  standings: data, removed: [french]), .cards)
    }

    func testABoardTheStandingsLackIsLeftOutNotFailed() {
        let missing = Standings(apiVersion: "v1", attributions: [], boards: [data.boards[0], data.boards[2]],
                                models: data.models)
        let plan = answerPlan(outcome: routed([french, legal]), primaryBoard: "arena", standings: missing, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.list.boards.map(\.id), ["arena", legal.board])
        XCTAssertEqual(view.refinements, [legal], "a chip for a board not counted would say it was")
    }

    func testAPrimaryBoardTheStandingsLackShowsTheCards() {
        XCTAssertEqual(answerPlan(outcome: routed([french]), primaryBoard: "nowhere", standings: data,
                                  removed: []), .cards)
    }

    func testBoardsThatShareNoModelStillShowTheCombinedListEmpty() {
        // D-167 clause 3 exactly (#54): nothing is guessed, so an empty list is said, not filled.
        let apart = Standings(apiVersion: "v1", attributions: [],
                              boards: [board("arena", [("a", 1)]), board(french.board, [("b", 1)])],
                              models: data.models)
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: apart, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.sharedCount, 0)
    }

    // MARK: - What the combined list discloses (review B1, M4; D-112)

    private func boardAt(_ id: String, _ rows: [(String, Int, String)], rankingEffort: String? = nil,
                         evidenceDate: String? = "2026-09-18", observedAt: String? = "2026-09-25",
                         benchmark: String? = nil) -> BoardStandings {
        BoardStandings(
            id: id, benchmark: benchmark ?? "B \(id)", metric: "elo", rankingEffort: rankingEffort,
            evidenceDate: evidenceDate, observedAt: observedAt, attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: $0.2) }
        )
    }

    private func held(_ boards: [BoardStandings]) -> Standings {
        Standings(apiVersion: "v1", attributions: [], boards: boards, models: data.models)
    }

    func testTheCombinedListSaysWhichEffortsItsModelsStandAt() {
        // The cards disclose an unequal comparison (D-112); the list that replaces them must too.
        let mixed = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "unspecified"), ("c", 3, "max")]),
                          boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: mixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.mixedEfforts, [BoardEfforts(board: "arena", efforts: ["high", "unspecified"])],
                       "only the listed models' efforts count: c, at max, is not in the list")
        XCTAssertEqual(view.efforts, ["high", "unspecified"])
    }

    // MARK: the combined list's disclosures, as data (#67, #72, M18-W2 P4)

    private func stale(_ days: Int) -> SourceHealth {
        SourceHealth(benchmark: "B arena", stale: true, notice: "old",
                     sources: [SourceRow(source: "s", rows: 3, newestRunDate: nil, ageDays: days, stale: true)])
    }

    /// #67: the gate could not see a view branch, so the combined list's disclosures are fields of
    /// its plan, and this test holds every one of them on the plan rather than on the view's text.
    func testTheCombinedListCarriesEveryDisclosureItOwes() {
        let mixed = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "unspecified")]),
                          boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: mixed, removed: [],
                              primaryHealth: stale(120))
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.disclosures, [
            .staleBoard(stale(120)),
            .productsOwnOrder(models: 2, boards: 2),
            .tiedPlaces,
            .mixedEfforts(["high", "unspecified"]),
        ])
    }

    /// #72: the cards warned that the surface's board was stale and the combined list that replaced
    /// them did not. A fresh board says nothing; a stale one is said first and loudly.
    func testAStaleBoardIsSaidOnTheCombinedListAsLoudlyAsOnTheCards() {
        let fresh = SourceHealth(benchmark: "B arena", stale: false, notice: nil, sources: [])
        let quiet = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: data, removed: [],
                               primaryHealth: fresh)
        guard case let .combined(calm) = quiet else { return XCTFail("\(quiet)") }
        XCTAssertFalse(calm.disclosures.contains { if case .staleBoard = $0 { return true }; return false })

        let loud = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: data, removed: [],
                              primaryHealth: stale(200))
        guard case let .combined(warned) = loud else { return XCTFail("\(loud)") }
        let said = warned.disclosures.compactMap { combinedDisclosure($0, .turkish) }
        XCTAssertEqual(said.first?.weight, .state, "the stale board is not the loud warning the cards give")
        XCTAssertTrue(said.first?.text.contains("200") == true, said.first?.text ?? "nil")
    }

    /// Every disclosure says itself in both languages, and none is dropped on the way.
    func testEveryCombinedDisclosureIsSaidInBothLanguages() {
        let all: [CombinedDisclosure] = [.staleBoard(stale(120)), .productsOwnOrder(models: 2, boards: 2),
                                         .tiedPlaces, .mixedEfforts(["high", "max"])]
        for disclosure in all {
            let english = combinedDisclosure(disclosure, .english)
            let turkish = combinedDisclosure(disclosure, .turkish)
            XCTAssertNotNil(english, "\(disclosure)")
            XCTAssertNotEqual(english?.text, turkish?.text, "\(disclosure)")
        }
    }

    // MARK: the plan is computed when its inputs change (#70, M18-W2 P5)

    private func inputs(_ removed: Set<Refinement> = [], stamp: Int = 1) -> PlanMemo.Inputs {
        PlanMemo.Inputs(outcome: routed([french]), primaryBoard: "arena", standingsStamp: stamp,
                        removed: removed, primaryHealth: nil)
    }

    /// `answerPlan`, and with it `combine`, ran in `body` on every render, every keystroke included.
    func testTheSameInputsAreNotPlannedTwice() {
        let memo = PlanMemo()
        let first = memo.plan(inputs(), standings: data)
        for _ in 0..<50 { XCTAssertEqual(memo.plan(inputs(), standings: data), first) }
        XCTAssertEqual(memo.computed, 1, "typing in the field re-planned an unchanged question")
    }

    func testAChangedInputIsPlannedAgain() {
        let memo = PlanMemo()
        let combined = memo.plan(inputs(), standings: data)
        XCTAssertEqual(memo.plan(inputs([french]), standings: data),
                       answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: data, removed: [french]))
        XCTAssertEqual(memo.plan(inputs([french], stamp: 2), standings: data),
                       memo.plan(inputs([french]), standings: data), "new standings, same plan, planned again")
        XCTAssertEqual(memo.computed, 4)
        XCTAssertNotEqual(combined, memo.plan(inputs([french]), standings: data))
    }

    func testEveryEffortIsNamedOnceInTheBoardsOwnOrder() {
        let mixed = held([boardAt("arena", [("a", 1, "unspecified"), ("b", 2, "high")]),
                          boardAt(french.board, [("b", 1, "max"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: mixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.efforts, ["unspecified", "high", "max"])
    }

    func testAModelListedTwiceOnABoardCountsItsFirstRowAsTheCombinationDoes() {
        // Security pass S4: only a malformed payload lists a model twice on one board. `combine`
        // counts its first row; the effort notice must not name an effort no counted row has.
        let doubled = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "high"), ("a", 3, "max")]),
                            boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: doubled, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.mixedEfforts, [])
    }

    func testABoardRankedAtOneEffortIsNeverAMix() {
        let fixed = held([boardAt("arena", [("a", 1, "high"), ("b", 2, "medium")], rankingEffort: "high"),
                          boardAt(french.board, [("b", 1, "high"), ("a", 2, "high")])])
        let plan = answerPlan(outcome: routed([french]), primaryBoard: "arena", standings: fixed, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }

        XCTAssertEqual(view.mixedEfforts, [], "a surface that ranks at one named effort compares at it")
    }

    func testTheEffortNoteNamesEveryEffortInBothLanguages() {
        for language in Language.allCases {
            let note = UIText.combinedEffortNote(efforts: ["high", "unspecified"], language)
            XCTAssertTrue(note.contains("high") && note.contains("unspecified"), "\(language): \(note)")
        }
    }

    func testABoardThatPublishesNoEvaluationDateIsDatedByTheDayItWasRead() {
        // `observed_at` is when the engine read the board, not when anything was measured.
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: "2026-09-18")), .measured("2026-09-18"))
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: nil)), .readOn("2026-09-25"))
        XCTAssertEqual(boardDate(boardAt("x", [], evidenceDate: nil, observedAt: nil)), .unknown)
        XCTAssertNotEqual(UIText.boardDate(.readOn("2026-09-25"), .english),
                          UIText.boardDate(.measured("2026-09-25"), .english))
        XCTAssertTrue(UIText.boardDate(.readOn("2026-09-25"), .turkish).contains(readableDate("2026-09-25", .turkish) ?? "?"))
    }

    func testEveryRefinementHasANameInBothLanguages() {
        for refinement in Refinements.table {
            for language in Language.allCases {
                XCTAssertFalse(UIText.refinementName(refinement, language).isEmpty, "\(refinement.value) \(language)")
            }
            XCTAssertNotEqual(UIText.refinementName(refinement, .turkish), refinement.value,
                              "\(refinement.value) has no Turkish name")
        }
    }
}

/// #63 finding 1 (M18-W2): one model as three full cards, the Best value one describing the best as
/// "the cheapest model within 6 points of the best".
final class PickCardTests: OfflineTestCase {
    private func pick(_ label: String, _ model: String, reason: String, score: Double = 73.8,
                      price: Double = 1.31) throws -> Pick
    {
        let json = """
        {"label": "\(label)", "model": "\(model)", "vendor": "Google", "score": \(score), "metric": "% resolved",
         "blended_per_m": \(price), "input_per_m": 1, "output_per_m": 2, "harness": "h",
         "confidence": "Medium", "confidence_basis": "b", "why": "why \(label)",
         "why_fact": {"reason": "\(reason)", "unit": "points", "window": 6.0, "floor": 67.0,
                      "benchmark": "DeepSWE"}}
        """
        return try JSONDecoder().decode(Pick.self, from: Data(json.utf8))
    }

    func testOneModelHoldingThreeLabelsIsOneCardWithThreeLabels() throws {
        let picks = [try pick("best_quality", "Gemini 3.8 Flash", reason: "highest_score"),
                     try pick("best_value", "Gemini 3.8 Flash", reason: "cheapest_within_window"),
                     try pick("budget_pick", "Gemini 3.8 Flash", reason: "cheapest_above_floor")]
        let cards = pickCards(picks)

        XCTAssertEqual(cards.count, 1)
        XCTAssertEqual(cards.first?.labels, ["best_quality", "best_value", "budget_pick"])
        // The value-window sentence describes a model BEHIND the best; said of the best it contradicts
        // itself. The floor sentence is a fact about this model, and stays.
        XCTAssertEqual(cards.first?.reasons.map(\.label), ["best_quality", "budget_pick"])
    }

    func testDifferentModelsKeepTheirOwnCardsInTheEnginesOrder() throws {
        let picks = [try pick("best_quality", "A", reason: "highest_score", score: 80),
                     try pick("best_value", "B", reason: "cheapest_within_window", score: 76, price: 0.5),
                     try pick("budget_pick", "B", reason: "cheapest_above_floor", score: 76, price: 0.5)]
        let cards = pickCards(picks)

        XCTAssertEqual(cards.map(\.lead.model), ["A", "B"])
        XCTAssertEqual(cards.map(\.labels), [["best_quality"], ["best_value", "budget_pick"]])
        XCTAssertEqual(cards[1].reasons.map(\.label), ["best_value", "budget_pick"],
                       "without the best on the card, the value sentence is true and stays")
    }

    /// A warning is never merged away: "nothing at this price clears the bar" stays on the card.
    func testAFloorWarningSurvivesTheMerge() throws {
        let picks = [try pick("best_quality", "A", reason: "highest_score"),
                     try pick("budget_pick", "A", reason: "nothing_clears_floor")]
        XCTAssertEqual(pickCards(picks).first?.reasons.map(\.label), ["best_quality", "budget_pick"])
    }

    /// Display names are not unique (#102). Two rows that differ in vendor, score or price are two
    /// models, even under one name.
    func testOneNameOnTwoDifferentRowsIsTwoCards() throws {
        let picks = [try pick("best_quality", "Same", reason: "highest_score", score: 80),
                     try pick("budget_pick", "Same", reason: "cheapest_above_floor", score: 70, price: 0.2)]
        XCTAssertEqual(pickCards(picks).count, 2)
    }
}

/// New finding A (M18-W2): the combined list was every shared model, about 160 rows and 10,900
/// points tall, with "See the boards" at its end.
final class CombinedLengthTests: OfflineTestCase {
    func testTheListShowsItsTopTenUntilAskedForTheRest() {
        XCTAssertEqual(visibleCount(total: 160, expanded: false), 10)
        XCTAssertEqual(visibleCount(total: 160, expanded: true), 160)
        XCTAssertEqual(visibleCount(total: 7, expanded: false), 7)
        XCTAssertEqual(visibleCount(total: 0, expanded: false), 0)
    }
}
