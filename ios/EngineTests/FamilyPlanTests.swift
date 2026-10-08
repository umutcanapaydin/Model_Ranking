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

    /// The second round's M1 and M3: the note says how the place is reached (each board's place as a
    /// share of its length, then the average), the count of models it holds, and in Turkish the
    /// coverage, the plural and an undated board.
    func testTheFamilyNoteSaysHowThePlaceIsReachedInBothLanguages() {
        let boards = [NamedBoard(name: "Aider", date: .unknown), NamedBoard(name: "SWE-bench", date: .readOn("2026-09-24"))]
        let english = UIText.familyNote(models: 58, boards: boards, coverage: 2, .english)
        XCTAssertTrue(english.contains("58 models"), english)
        XCTAssertTrue(english.contains("relative places"), english)
        XCTAssertFalse(english.contains("mean position"), english)
        XCTAssertTrue(english.contains("Aider, no date"), english)
        XCTAssertTrue(english.contains("undated, read 24 September 2026"), english)
        let turkish = UIText.familyNote(models: 58, boards: boards, coverage: 2, .turkish)
        XCTAssertTrue(turkish.contains("58 model"), turkish)
        XCTAssertTrue(turkish.contains("en az 2 panoda"), turkish)
        XCTAssertTrue(turkish.contains("göreli"), turkish)
        XCTAssertTrue(turkish.contains("Aider, tarih yok"), turkish)
        XCTAssertTrue(turkish.contains("tarihsiz, 24 Eylül 2026 okundu"), turkish)
        XCTAssertTrue(UIText.olderBoards(boards, .turkish).contains("sayılıyorlar"))
        XCTAssertTrue(UIText.olderBoards(Array(boards.prefix(1)), .turkish).hasSuffix("sayılıyor."))
    }

    /// The second round's M2: a surface is planned only once its own answers are on screen, so a
    /// "Change" never shows one coding list alone, or a new surface's list beside the old answers.
    func testASurfaceIsPlannedOnlyOnceItsAnswersAreOnScreen() {
        XCTAssertNil(plannedOutcome(routed: nil, chosen: "mathematics", answers: ["coding", "agentic-coding"]))
        XCTAssertNil(plannedOutcome(routed: nil, chosen: "coding", answers: ["mathematics"]))
        XCTAssertEqual(plannedOutcome(routed: nil, chosen: "mathematics", answers: ["mathematics"])?.tier, .manual)
        XCTAssertNil(plannedOutcome(routed: routed("vision"), chosen: nil, answers: ["coding", "agentic-coding"]))
        XCTAssertEqual(plannedOutcome(routed: routed("coding"), chosen: nil, answers: ["coding", "agentic-coding"])?.tier,
                       .similarity)
        XCTAssertNil(plannedOutcome(routed: nil, chosen: nil, answers: ["coding"]), "the launch screen plans nothing")
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

    /// Tester (M20-W4, REQ-CMB-005, D-188 clause 2): on a family whose model count, board count and
    /// coverage all differ (5, 4 and 2), the sentence the list itself shows (`combinedDisclosure`) and
    /// the boards' screen (`orderNote`) are the family note with each count in its place, in both
    /// languages, and never the every-board sentence that round 1's B1 removed.
    func testTheListsOwnNoteSaysEachCountInItsPlaceInBothLanguages() {
        let family = ["swebench", "aider", "arena_text_coding", "livecodebench"]
        let data = standings([board("swebench", [("a", 1), ("b", 2), ("c", 3)]),
                              board("aider", [("a", 1), ("d", 2), ("e", 3)]),
                              board("arena_text_coding", [("b", 1), ("c", 2), ("d", 3), ("f", 4)]),
                              board("livecodebench", [("e", 1), ("a", 2)])])
        let plan = answerPlan(outcome: routed("coding"), primaryBoard: "swebench", family: family, question: nil,
                              asOf: today, standings: data, removed: [])
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.sharedCount, 5, "f is on one board of four")
        let order = CombinedDisclosure.familyOrder(
            models: 5, boards: family.map { NamedBoard(name: "B \($0)", date: .measured("2026-09-20")) }, coverage: 2)
        XCTAssertTrue(view.disclosures.contains(order), "\(view.disclosures)")
        let english = "Our own list, built from 4 boards ("
            + family.map { "B \($0), 20 September 2026" }.joined(separator: "; ")
            + "). 5 models; a model ranked by at least 2 of them is placed by the average of its relative places "
            + "on those boards (each place as a share of that board's length). No leaderboard publishes this order."
        let turkish = "Uygulamanın kendi listesi: 4 panodan kuruldu ("
            + family.map { "B \($0), 20 Eylül 2026" }.joined(separator: "; ")
            + "). 5 model; en az 2 panoda yer alan bir model, o panolardaki göreli sıralarının ortalamasıyla "
            + "yerleşir (her sıra, o panonun uzunluğuna oranla). Bu sırayı hiçbir liste yayımlamıyor."
        XCTAssertEqual(combinedDisclosure(order, .english)?.text, english)
        XCTAssertEqual(combinedDisclosure(order, .turkish)?.text, turkish)
        XCTAssertEqual(combinedDisclosure(order, .english)?.weight, .property)
        XCTAssertEqual(orderNote(view, .english), english, "the boards' screen says the list's sentence")
        XCTAssertEqual(orderNote(view, .turkish), turkish)
    }

    /// Tester (M20-W4, REQ-CMB-004): a refinement whose board the phone's standings lack is not
    /// offered on a family list, whichever tier chose it, so no chip claims a board the list did not count.
    func testARefinementWhoseBoardTheStandingsLackIsNotOfferedOnAFamily() {
        let french = Refinements.table.filter { $0.value == "french" }
        XCTAssertFalse(french.isEmpty)
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)])])
        for outcome in [routed("everyday"), routed("everyday", tier: .model, refinements: french)] {
            let plan = answerPlan(outcome: outcome, primaryBoard: "epoch_eci", family: ["epoch_eci", "arena"],
                                  question: "best ai to write in french", asOf: today, standings: data, removed: [])
            guard case let .combined(view) = plan else { return XCTFail("\(outcome.tier): \(plan)") }
            XCTAssertEqual(view.refinements, [], "\(outcome.tier)")
            XCTAssertEqual(view.list.boards.map(\.id), ["epoch_eci", "arena"], "\(outcome.tier)")
        }
    }

    /// Tester (M20-W4, REQ-CMB-004, D-188 clause 6; the W3 Tester's R1): the W3 Tester's word probes,
    /// re-run through the answer plan W4 wires. An AI's software and a machine's health add no domain
    /// board to the family list; the writing the question names still does.
    func testTheW3WordProbesAddNoSecondReadingThroughTheAnswerPlan() {
        let software = "arena_text_industry_software_and_it_services"
        let medicine = "arena_text_industry_medicine_and_healthcare"
        let writing = "arena_text_industry_writing_and_literature_and_language"
        let data = standings([board("epoch_eci", [("a", 1), ("b", 2)]), board("arena", [("b", 1), ("a", 2)]),
                              board(software, [("a", 1), ("b", 2)]), board(medicine, [("b", 1), ("a", 2)]),
                              board(writing, [("a", 1), ("b", 2)])])
        func boards(_ question: String) -> [String] {
            let plan = answerPlan(outcome: routed("everyday"), primaryBoard: "epoch_eci", family: ["epoch_eci", "arena"],
                                  question: question, asOf: today, standings: data, removed: [])
            guard case let .combined(view) = plan else { return [] }
            return view.list.boards.map(\.id)
        }
        XCTAssertEqual(boards("best ai software for writing essays"), ["epoch_eci", "arena", writing])
        for question in ["which ai software is best for essays", "best chatbot software for poems",
                         "hangi yapay zeka yazılımı daha iyi", "sunucu sağlık durumu", "pil sağlık durumu",
                         "kubernetes sağlık kontrolü betiği"] {
            let read = boards(question)
            XCTAssertFalse(read.contains(software), question)
            XCTAssertFalse(read.contains(medicine), question)
            XCTAssertEqual(Array(read.prefix(2)), ["epoch_eci", "arena"], question)
        }
    }

    /// The M20 repo review's M1: `assistant`'s family is Arena's one board, so a language takes its place,
    /// and the list is that language's board alone (not Arena's general vote beside it), with its chip.
    func testAOneBoardFamilyWithALanguageIsThatLanguagesList() {
        let spanish = Refinements.table.filter { $0.value == "spanish" }
        let data = standings([board("arena", [("a", 1), ("b", 2), ("c", 3)]),
                              board("arena_text_spanish", [("b", 1), ("a", 2)])])
        let plan = answerPlan(outcome: routed("assistant"), primaryBoard: "arena", family: ["arena"],
                              question: "reply in spanish", asOf: today, standings: data, removed: [],
                              refinedBoard: "arena")
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["arena_text_spanish"])
        XCTAssertEqual(view.list.entries.map(\.model.id), ["b", "a"], "c has no Spanish evidence")
        XCTAssertEqual(view.refinements, spanish)
        let removed = answerPlan(outcome: routed("assistant"), primaryBoard: "arena", family: ["arena"],
                                 question: "reply in spanish", asOf: today, standings: data,
                                 removed: Set(spanish), refinedBoard: "arena")
        XCTAssertEqual(removed, .restorable(spanish))
    }

    /// The closure fixes review's M1: of a language and a domain, only the one that stands is offered,
    /// so no chip says a board was counted when it was not.
    func testOnlyTheRefinementThatStandsIsOffered() {
        let french = Refinements.table.filter { $0.value == "french" }
        let data = standings([board("epoch_gpqa", [("a", 1), ("b", 2)]), board("arena_text_expert", [("b", 1), ("a", 2)]),
                              board("arena_text_french", [("a", 1), ("b", 2)]),
                              board("arena_text_industry_legal_and_government", [("b", 1), ("a", 2)])])
        let plan = answerPlan(outcome: routed("expert"), primaryBoard: "epoch_gpqa",
                              family: ["epoch_gpqa", "arena_text_expert"], question: "legal advice in french",
                              asOf: today, standings: data, removed: [], refinedBoard: "arena_text_expert")
        guard case let .combined(view) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(view.list.boards.map(\.id), ["epoch_gpqa", "arena_text_french"])
        XCTAssertEqual(view.refinements, french)
    }

    /// The closure fixes review's M2: a family left with one board that no refinement brought (its
    /// primary missing from the standings) is today's cards, not a one-board list.
    func testAOneBoardFamilyThatNoRefinementBroughtIsTheCards() {
        let data = standings([board("arena", [("b", 1), ("a", 2)])])
        XCTAssertEqual(answerPlan(outcome: routed("everyday"), primaryBoard: "epoch_eci",
                                  family: ["epoch_eci", "arena", "epoch_mmlu"], question: "best ai", asOf: today,
                                  standings: data, removed: [], refinedBoard: "arena"), .cards)
    }

    /// The closure fixes review's M5: the memo hands the board a refinement replaces to the plan.
    func testTheMemoPassesTheBoardARefinementReplaces() {
        let memo = PlanMemo()
        let data = standings([board("arena", [("a", 1), ("b", 2), ("c", 3)]),
                              board("arena_text_spanish", [("b", 1), ("a", 2)])])
        var inputs = PlanMemo.Inputs(outcome: routed("assistant"), primaryBoard: "arena", standingsStamp: 1,
                                     removed: [], primaryHealth: nil)
        inputs.family = ["arena"]
        inputs.question = "reply in spanish"
        inputs.asOf = today
        inputs.refinedBoard = "arena"
        guard case let .combined(view) = memo.plan(inputs, standings: data) else { return XCTFail("cards") }
        XCTAssertEqual(view.list.boards.map(\.id), ["arena_text_spanish"])
    }
}
