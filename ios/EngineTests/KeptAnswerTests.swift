//  #288 (D-202 clause 5) -- when the engine cannot be reached, the last answer it sent for the same
//  surface and budget is shown, dated, instead of the failure sentence.
//
//  The answers are kept in a file of their own beside the standings, never in the standings file
//  (INV-66), as the app decoded them, with the time they arrived. Nothing is bundled (REQ-APP-001):
//  the only answers the phone ever holds are ones the engine sent it.

import XCTest

@testable import ModelRankingEngine

/// Trimmed from what `/v1/recommendations?task=assistant&budget=unlimited` returned on 2026-10-16 (one
/// answer, one pick, one ranked row; the names and the long sentences shortened), not written from the
/// Swift structs.
private func recommendationPayload(task: String = "assistant", budget: String = "unlimited",
                                   model: String = "Model A") -> Data {
    Data(#"""
    {"api_version": "v1", "query": {"task": "\#(task)", "budget": "\#(budget)"}, "surfaces_are_ranked": false,
     "ordering_note": "No position here means anything.",
     "answers": [{"ranking_effort": null, "sources": ["Arena leaderboard data (CC-BY-4.0)"], "eligible_count": 205,
      "frontier_size": 9, "close_call": null, "close_call_fact": null, "effort_mix_notice": "Mixed efforts.",
      "stale_notice": null,
      "picks": [{"label": "best_quality", "model": "\#(model)", "vendor": "Vendor", "score": 1514.8, "metric": "elo",
       "secondary_score": null, "blended_per_m": 7.4, "input_per_m": 3.7, "output_per_m": 18.5,
       "evidence_date": "2026-10-08", "harness": "arena-crowd", "effort": "high", "higher_effort": null,
       "higher_effort_score": null, "effort_note": "A run at high effort.", "confidence": "Medium",
       "confidence_basis": "one independent benchmark (Arena text)", "why": "Highest Arena text score.",
       "trade_off": null, "why_fact": {"reason": "highest_score", "benchmark": "Arena text", "score": 1514.8,
       "unit": "Elo", "measured": true}, "trade_off_fact": null, "model_id": "model-a"}],
      "surface": "\#(task)", "title": "Chat",
      "ranking": [{"model": "\#(model)", "vendor": "Vendor", "score": 1514.8, "harness": "arena-crowd",
       "effort": "high", "evidence_date": "2026-10-08", "secondary_score": null, "input_per_m": 3.7,
       "output_per_m": 18.5, "blended_per_m": 7.4, "metric": "elo"}],
      "primary_benchmark": "Arena text", "metric": "elo",
      "source_health": {"benchmark": "Arena text", "sources": [{"source": "arena", "rows": 414,
       "newest_run_date": "2026-10-08", "age_days": 7, "stale": false}], "stale": false, "notice": null,
       "reason": null},
      "evidence_dating": "dated", "evidence_dating_note": null, "unavailable_reason": null,
      "unavailable_reason_code": null}]}
    """#.utf8)
}

private let categoriesPayload = Data(#"""
    {"categories": [{"id": "assistant", "title": "Chat", "primary_benchmark": "Arena text", "metric": "elo",
      "ranking_effort": null, "primary_board": "arena", "boards": ["arena", "epoch_eci"]},
     {"id": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified", "metric": "% resolved",
      "ranking_effort": null, "close_call_margin": 1.5}]}
    """#.utf8)

final class KeptAnswerTests: OfflineTestCase {
    private var folder: URL!
    private let arrived = Date(timeIntervalSince1970: 1_790_000_000)

    override func setUp() {
        super.setUp()
        folder = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
    }

    override func tearDown() {
        try? FileManager.default.removeItem(at: folder)
        super.tearDown()
    }

    private func store() -> StandingsStore {
        StandingsStore(url: folder.appendingPathComponent("standings.json"))
    }

    private func decoded(_ payload: Data = recommendationPayload()) throws -> Recommendation {
        try JSONDecoder().decode(Recommendation.self, from: payload)
    }

    private func keep(_ recommendation: Recommendation, task: String = "assistant", budget: String = "unlimited",
                      at date: Date) throws {
        let payload = try XCTUnwrap(KeptAnswers.payload(recommendation), "the answer could not be encoded to keep")
        store().keep(route: KeptAnswers.recommendationsRoute, task: task, budget: budget, payload: payload, at: date)
    }

    func testNothingKeptMeansNothingToShow() {
        XCTAssertEqual(store().keptAnswers(), [])
        XCTAssertNil(KeptAnswers.recommendation(store().keptAnswers(), task: "assistant", budget: "unlimited",
                                                now: arrived))
        XCTAssertNil(KeptAnswers.categories(store().keptAnswers(), now: arrived))
    }

    func testAnAnswerIsKeptWithTheTimeItArrivedAndShownForItsOwnSurface() throws {
        try keep(try decoded(), at: arrived)
        let kept = try XCTUnwrap(KeptAnswers.recommendation(store().keptAnswers(), task: "assistant",
                                                            budget: "unlimited", now: arrived.addingTimeInterval(3_600)))
        XCTAssertEqual(kept.fetchedAt, arrived)
        XCTAssertEqual(kept.recommendation.answers.map(\.surface), ["assistant"])
        XCTAssertEqual(kept.recommendation.orderingNote, "No position here means anything.")
    }

    func testAKeptAnswerIsWhatTheAppDecoded() throws {
        // The answer is kept as the app decoded it and read back the same: the pick's numbers, its
        // open-ended fact, the ranking row and the source health all survive the round trip.
        let original = try decoded()
        try keep(original, at: arrived)
        let back = try XCTUnwrap(KeptAnswers.recommendation(store().keptAnswers(), task: "assistant",
                                                            budget: "unlimited", now: arrived)).recommendation
        let pick = try XCTUnwrap(back.answers.first?.picks.first)
        let was = try XCTUnwrap(original.answers.first?.picks.first)
        XCTAssertEqual(pick.model, was.model)
        XCTAssertEqual(pick.score, was.score)
        XCTAssertEqual(pick.blendedPerM, was.blendedPerM)
        XCTAssertEqual(pick.whyFactDictionary["score"] as? Double, 1514.8)
        XCTAssertEqual(pick.whyFactDictionary["measured"] as? Bool, true)
        XCTAssertEqual(pick.whyFactDictionary["reason"] as? String, "highest_score")
        XCTAssertNil(pick.tradeOffFact)
        XCTAssertEqual(back.answers.first?.ranking, original.answers.first?.ranking)
        XCTAssertEqual(back.answers.first?.sourceHealth, original.answers.first?.sourceHealth)
        XCTAssertEqual(back.query.task, "assistant")
    }

    func testAKeptAnswerIsNeverShownForAnotherSurfaceOrBudget() throws {
        try keep(try decoded(), at: arrived)
        let kept = store().keptAnswers()
        XCTAssertNil(KeptAnswers.recommendation(kept, task: "coding", budget: "unlimited", now: arrived),
                     "an answer for another surface was shown")
        XCTAssertNil(KeptAnswers.recommendation(kept, task: "assistant", budget: "cheap", now: arrived),
                     "an answer for another budget was shown")
        XCTAssertNil(KeptAnswers.categories(kept, now: arrived), "an answer was shown as the surfaces")
    }

    func testAnAnswerKeptUnderOneSurfaceButSentForAnotherIsNotShown() throws {
        // The kept entry's own key and the answer it holds must agree; a mismatch shows nothing.
        try keep(try decoded(recommendationPayload(task: "coding")), task: "assistant", at: arrived)
        XCTAssertNil(KeptAnswers.recommendation(store().keptAnswers(), task: "assistant", budget: "unlimited",
                                                now: arrived))
    }

    func testAKeptAnswerOlderThanItsLimitIsNotShown() throws {
        try keep(try decoded(), at: arrived)
        let kept = store().keptAnswers()
        let limit = KeptAnswers.maxAge
        XCTAssertNotNil(KeptAnswers.recommendation(kept, task: "assistant", budget: "unlimited",
                                                   now: arrived.addingTimeInterval(limit - 60)))
        XCTAssertNil(KeptAnswers.recommendation(kept, task: "assistant", budget: "unlimited",
                                                now: arrived.addingTimeInterval(limit)),
                     "an expired answer was shown")
        XCTAssertNil(KeptAnswers.recommendation(kept, task: "assistant", budget: "unlimited",
                                                now: arrived.addingTimeInterval(-3_600)),
                     "an answer dated after now (a clock that stepped back) was shown")
        XCTAssertEqual(limit, 7 * 86_400, "a week, the limit #288 took")
    }

    func testANewerAnswerForTheSameSurfaceReplacesTheOlderOne() throws {
        try keep(try decoded(recommendationPayload(model: "Old")), at: arrived)
        try keep(try decoded(recommendationPayload(model: "New")), at: arrived.addingTimeInterval(60))
        XCTAssertEqual(store().keptAnswers().count, 1)
        let kept = try XCTUnwrap(KeptAnswers.recommendation(store().keptAnswers(), task: "assistant",
                                                            budget: "unlimited", now: arrived.addingTimeInterval(120)))
        XCTAssertEqual(kept.recommendation.answers.first?.picks.first?.model, "New")
        XCTAssertEqual(kept.fetchedAt, arrived.addingTimeInterval(60))
    }

    func testEachSurfaceKeepsItsOwnAnswerAndTheOldestGoesFirst() throws {
        let limit = StandingsStore.maxKeptAnswers
        for index in 0...limit {
            try keep(try decoded(recommendationPayload(task: "surface-\(index)")), task: "surface-\(index)",
                     at: arrived.addingTimeInterval(Double(index)))
        }
        let kept = store().keptAnswers()
        XCTAssertEqual(kept.count, limit, "the kept answers grew past their limit")
        XCTAssertFalse(kept.contains { $0.task == "surface-0" }, "the oldest answer was not the one dropped")
        XCTAssertNotNil(KeptAnswers.recommendation(kept, task: "surface-\(limit)", budget: "unlimited",
                                                   now: arrived.addingTimeInterval(Double(limit))))
        XCTAssertNotNil(KeptAnswers.recommendation(kept, task: "surface-1", budget: "unlimited",
                                                   now: arrived.addingTimeInterval(Double(limit))))
    }

    func testTheSurfacesAreKeptAndShownToo() throws {
        let categories = try JSONDecoder().decode(CategoryList.self, from: categoriesPayload).categories
        let payload = try XCTUnwrap(KeptAnswers.payload(categories))
        store().keep(route: KeptAnswers.categoriesRoute, task: "", budget: "", payload: payload, at: arrived)
        let kept = try XCTUnwrap(KeptAnswers.categories(store().keptAnswers(), now: arrived.addingTimeInterval(60)))
        XCTAssertEqual(kept.categories, categories)
        XCTAssertEqual(kept.fetchedAt, arrived)
        XCTAssertNil(KeptAnswers.recommendation(store().keptAnswers(), task: "", budget: "", now: arrived),
                     "the surfaces were shown as an answer")
        XCTAssertNil(KeptAnswers.categories(store().keptAnswers(), now: arrived.addingTimeInterval(KeptAnswers.maxAge)))
    }

    func testKeepingAnAnswerNeverTouchesTheStandingsFile() throws {
        // INV-66: nothing derived from the question reaches the standings file. The answers live in a
        // file of their own beside it.
        let standings = Data(#"""
            {"api_version":"v1","attributions":["a"],"boards":[],"models":[],"credits":[]}
            """#.utf8)
        store().save(try FetchedStandings(payload: standings), at: arrived)
        let file = folder.appendingPathComponent("standings.json")
        let before = try Data(contentsOf: file)
        try keep(try decoded(), at: arrived.addingTimeInterval(60))

        XCTAssertEqual(try Data(contentsOf: file), before, "keeping an answer changed the standings file")
        XCTAssertEqual(store().load()?.fetchedAt, arrived)
        XCTAssertFalse(String(decoding: before, as: UTF8.self).contains("assistant"))
        XCTAssertEqual(store().keptAnswers().count, 1)
        XCTAssertEqual(try FileManager.default.contentsOfDirectory(atPath: folder.path).sorted(),
                       ["answers.json", "standings.json"])
    }

    func testAStorePointedAnywhereButAFileKeepsNothing() throws {
        // Security S1, for the kept answers: the store only ever reads and writes a file on this device.
        try keep(try decoded(), at: arrived)
        let stored = try Data(contentsOf: folder.appendingPathComponent("answers.json"))
        let elsewhere = try XCTUnwrap(URL(string: "data:application/json;base64,\(stored.base64EncodedString())"))
        XCTAssertEqual(StandingsStore(url: elsewhere).keptAnswers(), [], "a store read answers from something not a file")
        XCTAssertEqual(OfflineGuard.drain(), [])
    }

    func testAnUnreadableFileIsNothingKept() throws {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        try Data("not json".utf8).write(to: folder.appendingPathComponent("answers.json"))
        XCTAssertEqual(store().keptAnswers(), [])
        try keep(try decoded(), at: arrived)
        XCTAssertEqual(store().keptAnswers().count, 1, "an unreadable file stopped a new answer being kept")
    }

    func testOnlyAnEngineThatCouldNotBeReachedIsStoodInFor() {
        // D-202 clause 5 says "cannot be reached": an engine that answered and refused, or sent what this
        // app cannot read, says so itself, and a cleartext refusal is a setting to fix, not an outage.
        for error: EngineError in [.unreachable("x"), .timedOut(seconds: 10), .offline] {
            XCTAssertTrue(KeptAnswers.standsIn(for: error), "\(error)")
        }
        for error: EngineError in [.refused(status: 503, code: "c", message: "m"), .undecodable("x"), .insecureTransport] {
            XCTAssertFalse(KeptAnswers.standsIn(for: error), "\(error)")
        }
    }

    func testTheOnDeviceAnswersAreReadWithoutReachingOut() {
        _ = StandingsStore.onDevice.keptAnswers()
        XCTAssertEqual(OfflineGuard.drain(), [], "the on-device answers reached for a remote address")
    }
}
