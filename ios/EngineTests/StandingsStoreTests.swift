//  M17-W4 (D-167) -- the phone keeps the last standings the engine sent, and asks again once a day.
//
//  The store holds only what the engine sent, byte for byte, with the time it arrived. A question
//  asked while the phone is offline is answered from it; a failed fetch never replaces it.

import XCTest

@testable import ModelRankingEngine

private let standingsPayload = Data(#"""
    {"api_version":"v1","attributions":["a"],"boards":[{"id":"epoch_chess","benchmark":"Chess puzzles",\#
    "metric":"% correct","evidence_date":null,"observed_at":"2026-09-25","attribution":"a",\#
    "standings":[{"model":"a","position":1}]}],"models":[{"id":"a","display":"A","vendor":"V",\#
    "blended_per_m":1.25,"accessibility":null}]}
    """#.utf8)

final class StandingsStoreTests: XCTestCase {
    private var folder: URL!
    private let arrived = Date(timeIntervalSince1970: 1_790_000_000)

    override func setUp() {
        folder = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
    }

    override func tearDown() {
        try? FileManager.default.removeItem(at: folder)
    }

    private func store() -> StandingsStore {
        StandingsStore(url: folder.appendingPathComponent("standings.json"))
    }

    private func fetched() throws -> FetchedStandings {
        try FetchedStandings(payload: standingsPayload)
    }

    func testNothingStoredMeansNothingToServe() {
        XCTAssertNil(store().load())
    }

    func testAPayloadIsKeptWithTheTimeItArrivedAndTheBytesTheEngineSent() throws {
        store().save(try fetched(), at: arrived)
        let loaded = try XCTUnwrap(store().load())

        XCTAssertEqual(loaded.fetchedAt, arrived)
        XCTAssertEqual(loaded.payload, standingsPayload)
        XCTAssertEqual(loaded.standings.boards.map(\.id), ["epoch_chess"])
    }

    func testItIsFetchedAgainOnlyOnceADayHasPassed() async throws {
        store().save(try fetched(), at: arrived)
        var fetches = 0
        let fetch: () async throws -> FetchedStandings = {
            fetches += 1
            return try FetchedStandings(payload: standingsPayload)
        }

        _ = await store().current(now: arrived.addingTimeInterval(23 * 3600), fetch: fetch)
        XCTAssertEqual(fetches, 0, "a payload younger than a day was fetched again")
        _ = await store().current(now: arrived.addingTimeInterval(24 * 3600), fetch: fetch)
        XCTAssertEqual(fetches, 1, "a payload a day old was not fetched again")
    }

    func testAPayloadStampedInTheFutureIsFetchedAgain() async throws {
        // A clock that stepped back would otherwise keep yesterday's standings until it caught up.
        store().save(try fetched(), at: arrived)
        var fetches = 0
        _ = await store().current(now: arrived.addingTimeInterval(-3600)) {
            fetches += 1
            return try FetchedStandings(payload: standingsPayload)
        }
        XCTAssertEqual(fetches, 1)
    }

    func testAFailedFetchKeepsTheLastGoodPayload() async throws {
        store().save(try fetched(), at: arrived)
        let served = await store().current(now: arrived.addingTimeInterval(2 * 86_400)) {
            throw EngineError.offline
        }

        XCTAssertEqual(served?.boards.map(\.id), ["epoch_chess"])
        XCTAssertEqual(store().load()?.fetchedAt, arrived, "a failed fetch replaced the stored time")
    }

    func testAFetchedPayloadIsStoredAndServed() async throws {
        let served = await store().current(now: arrived) { try FetchedStandings(payload: standingsPayload) }

        XCTAssertEqual(served?.models.map(\.id), ["a"])
        XCTAssertEqual(store().load()?.payload, standingsPayload)
    }

    func testAnUnreadableFileIsNothingStoredNotACrash() throws {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        try Data("not json".utf8).write(to: folder.appendingPathComponent("standings.json"))

        XCTAssertNil(store().load())
    }
}
