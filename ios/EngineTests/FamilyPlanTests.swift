//  M20-W4 (#212, REQ-CMB-005, D-188 clause 5): the combined list is the default answer. An engine that
//  names a surface's family (M20-W1) gets the family's own list, combined by D-188 (M20-W2), with the
//  boards the question's refinement adds (M20-W3); a family of one board is today's cards; an engine
//  older than M20 keeps today's plan. An older board counts the same and is named in a small note,
//  never the stale warning over the list (D-188 clause 4).

import XCTest

@testable import ModelRankingEngine

final class FamilyPlanTests: OfflineTestCase {
    private let today = ISO8601DateFormatter().date(from: "2026-10-08T12:00:00Z") ?? Date()

    private func board(_ id: String, _ rows: [(String, Int)], date: String? = "2026-09-20") -> BoardStandings {
        BoardStandings(
            id: id, benchmark: "B \(id)", metric: "elo", rankingEffort: nil, evidenceDate: date,
            observedAt: "2026-10-07", attribution: "cite \(id)",
            standings: rows.map { Standing(model: $0.0, position: $0.1, effort: "unspecified") }
        )
    }

    private func standings(_ boards: [BoardStandings]) -> Standings {
        let ids = Set(boards.flatMap { $0.standings.map(\.model) }).sorted()
        return Standings(apiVersion: "v1", attributions: [], boards: boards,
                         models: ids.map { StandingModel(id: $0, display: $0, vendor: "V", blendedPerM: 1, accessibility: nil) })
    }

    private func routed(_ surface: String, tier: RoutingTier = .similarity, refinements: [Refinement] = []) -> RoutingOutcome {
        RoutingOutcome(categoryID: surface, tier: tier, unmeasured: false, refinements: refinements)
    }

    private var coding: Standings {
        standings([board("swebench", [("a", 1), ("b", 2)]), board("aider", [("b", 1), ("c", 2)]),
                   board("arena_text_coding", [("a", 1), ("c", 2), ("d", 3)])])
    }

    func testAnEngineThatNamesAFamilyShowsTheFamilysListByDefault() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                              family: ["swebench", "aider", "arena_text_coding"], question: "best model for coding",
                              asOf: today, standings: coding, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["swebench", "aider", "arena_text_coding"])
        XCTAssertEqual(Set(view.list.entries.map(\.model.id)), ["a", "b", "c"], "two of three boards, d on one")
    }

    func testAFamilyOfOneBoardShowsTheCards() {
        let plan = answerPlan(outcome: routed("assistant"), primaryBoard: "arena", family: ["arena"],
                              question: "best chatbot", asOf: today,
                              standings: standings([board("arena", [("a", 1)])]), removed: [])
        XCTAssertEqual(plan, .cards)
    }

    func testAnEngineOlderThanM20KeepsTodaysPlan() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench", standings: coding, removed: [])
        XCTAssertEqual(plan, .cards, "no family named: one board, today's cards")
    }

    /// M20-W3 on screen: with no on-device model, a language word adds its board and offers its chip.
    func testALanguageWordAddsItsBoardWithNoModel() {
        let french = Refinements.table.first { $0.value == "french" }
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("everyday"), primaryBoard: "epoch_eci", family: ["epoch_eci", "arena"],
                              question: "best ai to write in french", asOf: today, standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["epoch_eci", "arena", "arena_text_french"])
        XCTAssertEqual(view.refinements, [french].compactMap { $0 })
    }

    /// D-188 clause 6: where the on-device model read the question, its choice stands, none included;
    /// the words are read only where another tier answered.
    func testTheOnDeviceModelsChoiceOfNoRefinementStands() {
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("everyday", tier: .model), primaryBoard: "epoch_eci",
                              family: ["epoch_eci", "arena"], question: "best ai to write in french", asOf: today,
                              standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["epoch_eci", "arena"])
        XCTAssertEqual(view.refinements, [])
    }

    /// D-188 clause 4: an old board counts the same and is a small note; the loud stale warning is not said.
    func testAnOldFamilyBoardIsASmallNoteNotTheLoudWarning() {
        let data = standings([board("swebench", [("a", 1), ("b", 2)], date: "2026-02-26"),
                              board("aider", [("b", 1), ("a", 2)])])
        let stale = SourceHealth(benchmark: "B swebench", stale: true, notice: "old",
                                 sources: [SourceRow(source: "swebench", rows: 2, newestRunDate: "2026-02-26",
                                                     ageDays: 224, stale: true)], reason: nil)
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench", family: ["swebench", "aider"],
                              question: "best model for coding", asOf: today, standings: data, removed: [],
                              primaryHealth: stale)
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertFalse(view.disclosures.contains { if case .staleBoard = $0 { return true }; return false })
        XCTAssertTrue(view.disclosures.contains(.olderBoards([NamedBoard(name: "B swebench", date: .measured("2026-02-26"))])))
        let said = view.disclosures.compactMap { combinedDisclosure($0, .english) }
        XCTAssertTrue(said.allSatisfy { $0.weight != .state }, "nothing here is the loud warning")
    }

    /// The W4 review's B1: the older-boards note dates each board, in the plural where there are two.
    func testTheOlderBoardsNoteIsSaidInBothLanguagesWithEachDate() {
        let one = [NamedBoard(name: "SWE-bench Verified", date: .measured("2026-06-25"))]
        let english = combinedDisclosure(.olderBoards(one), .english)
        let turkish = combinedDisclosure(.olderBoards(one), .turkish)
        XCTAssertNotNil(english)
        XCTAssertNotEqual(english?.text, turkish?.text)
        XCTAssertTrue(english?.text.contains("SWE-bench Verified") == true)
        XCTAssertTrue(english?.text.contains("25 Jun") == true, english?.text ?? "")
        let two = one + [NamedBoard(name: "Aider", date: .unknown)]
        let both = UIText.olderBoards(two, .english)
        XCTAssertTrue(both.contains("they count"), both)
        XCTAssertTrue(UIText.olderBoards(one, .english).contains("it counts"))
    }

    /// The W4 review's B1: a family list says how many boards built it, each with its date, and how
    /// many of them a model needs; never that every model is on every board.
    func testAFamilyListSaysItsBoardsTheirDatesAndTheCoverage() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                              family: ["swebench", "aider", "arena_text_coding"], question: "best model for coding",
                              asOf: today, standings: coding, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        let boards = ["swebench", "aider", "arena_text_coding"].map { NamedBoard(name: "B \($0)", date: .measured("2026-09-20")) }
        XCTAssertTrue(view.disclosures.contains(.familyOrder(models: 3, boards: boards, coverage: 2)), "\(view.disclosures)")
        XCTAssertFalse(view.disclosures.contains { if case .productsOwnOrder = $0 { return true }; return false })
        let note = UIText.familyNote(models: 3, boards: boards, coverage: 2, .english)
        XCTAssertTrue(note.contains("3 boards"), note)
        XCTAssertTrue(note.contains("at least 2"), note)
        XCTAssertTrue(note.contains("B aider"), note)
        XCTAssertTrue(note.contains("20 Sep"), note)
        XCTAssertFalse(note.contains("on all"), note)
        XCTAssertNotEqual(note, UIText.familyNote(models: 3, boards: boards, coverage: 2, .turkish))
        XCTAssertEqual(orderNote(view, .english), note, "the boards' screen says the same sentence")
    }

    /// The W4 review's M2: a removed refinement is not counted on a family, and comes back.
    func testARemovedRefinementIsNotCountedOnAFamilyAndComesBack() {
        let french = Refinements.table.filter { $0.value == "french" }
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("everyday"), primaryBoard: "epoch_eci", family: ["epoch_eci", "arena"],
                              question: "reply in french", asOf: today, standings: data, removed: Set(french))
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["epoch_eci", "arena"])
        XCTAssertEqual(view.removed, Set(french))
        XCTAssertEqual(view.refinements, french, "the removed chip stays, to restore")
    }

    /// The W4 review's M2: a one-board family whose every refinement is removed keeps the chips.
    func testAOneBoardFamilyWithEveryRefinementRemovedIsRestorable() {
        let french = Refinements.table.filter { $0.value == "french" }
        let data = standings([board("arena", [("b", 1), ("a", 2)]), board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("assistant"), primaryBoard: "arena", family: ["arena"],
                              question: "reply in french", asOf: today, standings: data, removed: Set(french))
        XCTAssertEqual(plan, .restorable(french))
    }

    /// The W4 review's M2: a refinement the surface does not allow is never offered.
    func testARefinementTheSurfaceDoesNotAllowIsNotOffered() {
        let french = Refinements.table.filter { $0.value == "french" }
        let data = standings([board("swebench", [("a", 1), ("b", 2)]), board("aider", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)])])
        let plan = answerPlan(outcome: routed("coding", tier: .model, refinements: french), primaryBoard: "swebench",
                              family: ["swebench", "aider"], question: "code in french", asOf: today,
                              standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.refinements, [])
        XCTAssertEqual(view.list.boards.map(\.id), ["swebench", "aider"])
    }

    /// The W4 review's M2: the paired surface is planned at the routed tier, as itself.
    func testThePairedOutcomeIsTheOtherSurfaceAtTheRoutedTier() {
        let paired = pairedOutcome(routed("coding", tier: .model), surface: "agentic-coding")
        XCTAssertEqual(paired?.categoryID, "agentic-coding")
        XCTAssertEqual(paired?.tier, .model)
        XCTAssertNil(pairedOutcome(nil, surface: "agentic-coding"))
        XCTAssertEqual(pairedSurface(routed: "agentic-coding", answers: ["coding", "agentic-coding"]), "coding")
        XCTAssertEqual(pairedSurface(routed: "coding", answers: ["coding", "agentic-coding"]), "agentic-coding")
        XCTAssertNil(pairedSurface(routed: "vision", answers: ["vision"]))
    }

    /// Ruling A (the W4 review's M2): both coding lists or neither.
    func testCodingShowsBothFamilyListsOrNeither() {
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                              family: ["swebench", "aider", "arena_text_coding"], question: "best model for coding",
                              asOf: today, standings: coding, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(familyLists(plan, paired: false, pairedPlan: nil)?.first, view)
        XCTAssertNil(familyLists(plan, paired: false, pairedPlan: nil)?.second)
        XCTAssertEqual(familyLists(plan, paired: true, pairedPlan: plan)?.second, view)
        XCTAssertNil(familyLists(plan, paired: true, pairedPlan: .cards), "one coding list alone would lead")
        XCTAssertNil(familyLists(plan, paired: true, pairedPlan: nil))
        XCTAssertNil(familyLists(.cards, paired: false, pairedPlan: nil))
    }

    /// The W4 review's M2 and M4: the memo keeps the family, and a surface the reader chose gets its
    /// family list, read from no words.
    func testTheMemoKeepsTheFamilyAndAChosenSurfaceGetsItsList() {
        let memo = PlanMemo()
        var inputs = PlanMemo.Inputs(outcome: chosenOutcome("coding"), primaryBoard: "swebench", standingsStamp: 1,
                                     removed: [], primaryHealth: nil)
        inputs.family = ["swebench", "aider", "arena_text_coding"]
        inputs.asOf = today
        guard case let .combined(view) = memo.plan(inputs, standings: coding) else { return XCTFail("cards") }
        XCTAssertEqual(view.refinements, [])
        XCTAssertEqual(chosenOutcome("coding").tier, .manual)
    }

    /// The W4 review's M2: a family whose models all miss the coverage is today's cards, and the
    /// phone copy's age is said on a family list.
    func testAnEmptyFamilyListIsTheCardsAndTheCopysAgeIsSaid() {
        let thin = standings([board("swebench", [("a", 1)]), board("aider", [("b", 1)]),
                              board("arena_text_coding", [("c", 1)])])
        XCTAssertEqual(answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                                  family: ["swebench", "aider", "arena_text_coding"], question: nil, asOf: today,
                                  standings: thin, removed: []), .cards)
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench",
                              family: ["swebench", "aider", "arena_text_coding"], question: nil, asOf: today,
                              standings: coding, removed: [], phoneCopyDays: 3)
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertTrue(view.disclosures.contains(.stalePhoneCopy(days: 3)))
    }

    func testTheMemoPlansAgainWhenTheFamilyOrTheQuestionChanges() {
        let memo = PlanMemo()
        var inputs = PlanMemo.Inputs(outcome: routed("coding"), primaryBoard: "swebench", standingsStamp: 1,
                                     removed: [], primaryHealth: nil)
        inputs.family = ["swebench", "aider"]
        inputs.question = "best model for coding"
        inputs.asOf = today
        _ = memo.plan(inputs, standings: coding)
        _ = memo.plan(inputs, standings: coding)
        XCTAssertEqual(memo.computed, 1)
        inputs.question = "best model for coding in french"
        _ = memo.plan(inputs, standings: coding)
        XCTAssertEqual(memo.computed, 2)
    }
}
