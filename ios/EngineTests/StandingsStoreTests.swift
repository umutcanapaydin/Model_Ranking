//  M17-W4 (D-167) -- the phone keeps the last standings the engine sent, and asks again once a day.
//
//  The store holds only what the engine sent, byte for byte, with the time it arrived. A question
//  asked while the phone is offline is answered from it; a failed fetch never replaces it.

import XCTest

@testable import ModelRankingEngine

private let standingsPayload = Data(#"""
    {"api_version":"v1","attributions":["a"],"boards":[{"id":"epoch_chess","benchmark":"Chess puzzles",\#
    "metric":"% correct","ranking_effort":null,"evidence_date":null,"observed_at":"2026-09-25","attribution":"a",\#
    "standings":[{"model":"a","position":1,"effort":"unspecified"}]}],"models":[{"id":"a","display":"A","vendor":"V",\#
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

    func testAPayloadIsKeptWithTheTimeItArrived() throws {
        store().save(try fetched(), at: arrived)
        let loaded = try XCTUnwrap(store().load())

        XCTAssertEqual(loaded.fetchedAt, arrived)
        XCTAssertEqual(loaded.standings, try fetched().standings)
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
        XCTAssertEqual(store().load()?.standings, try fetched().standings)
    }

    func testAStorePointedAnywhereButAFileReadsNothing() throws {
        // Security S1: the store's read fetches any address it is given, an https one included, so
        // a store built on one would be a way off the device. Proven without the network: a `data:`
        // address holding a perfectly good stored file, which that read would happily return.
        store().save(try fetched(), at: arrived)
        let stored = try Data(contentsOf: folder.appendingPathComponent("standings.json"))
        let elsewhere = try XCTUnwrap(URL(string: "data:application/json;base64,\(stored.base64EncodedString())"))

        XCTAssertNotNil(store().load(), "the file store itself must still load")
        XCTAssertNil(StandingsStore(url: elsewhere).load(), "a store read something that is not a file")
    }

    func testOnlyTheFieldsTheAppDecodesAreStored() throws {
        // Security S2: the store keeps the standings, re-encoded from what was decoded, so a payload
        // carrying anything else -- a field the engine never serves -- is not written as it came.
        var smuggled = try XCTUnwrap(String(data: standingsPayload, encoding: .utf8))
        smuggled.removeLast()
        smuggled += #","typed":"help me write a poem"}"#
        let fetched = try FetchedStandings(payload: Data(smuggled.utf8))
        store().save(fetched, at: arrived)
        let stored = try XCTUnwrap(store().load())

        XCTAssertFalse(String(decoding: stored.payload, as: UTF8.self).contains("typed"))
        XCTAssertEqual(stored.standings, fetched.standings)
    }

    func testAPayloadOverTheCeilingIsNeverAccepted() {
        // Security S2: the ceiling holds wherever standings are made, not only on the network path.
        XCTAssertThrowsError(try FetchedStandings(payload: Data(count: EngineClient.maxStandingsBytes + 1)))
    }

    func testAnUnreadableFileIsNothingStoredNotACrash() throws {
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
        try Data("not json".utf8).write(to: folder.appendingPathComponent("standings.json"))

        XCTAssertNil(store().load())
    }
}
