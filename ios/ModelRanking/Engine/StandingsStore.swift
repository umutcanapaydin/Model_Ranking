//  StandingsStore.swift — the last standings the engine sent, kept on the phone for a day (D-167).
//
//  The phone fetches every board's standings whatever the question is (D-160 clause 1) and keeps
//  them, so a question asked offline is still answered. This file holds exactly what the engine
//  sent, as this app decoded it, with the time it arrived. Nothing the reader typed ever reaches it:
//  its only input is a `FetchedStandings`, which stores only the fields the app decodes.
//
//  It is the second file the client-declaration gate lets touch the file system, beside the gap
//  register in `FrontDoor.swift`, and each file-system call below is permitted as that exact
//  expression by the text gate (`tests/unit/test_router_hints.py`, D-167 clause 4).

import Foundation

/// What is written: the engine's bytes and when they arrived. Nothing else.
private struct StoredStandings: Codable {
    let fetchedAt: Date
    let payload: Data
}

/// The standings as read back, with the time they arrived.
struct LoadedStandings {
    let standings: Standings
    let fetchedAt: Date
    let payload: Data
}

public struct StandingsStore {
    public let url: URL

    /// A day, the refresh cadence the owner ruled (D-167 clause 1). The engine itself refreshes
    /// nightly (D-151), so asking more often would fetch the same bytes.
    static let maxAge: TimeInterval = 86_400

    public init(url: URL) {
        self.url = url
    }

    /// The caches directory: public data the phone can always fetch again, so the system may purge
    /// it and it is never backed up.
    public static var onDevice: StandingsStore {
        let base = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        return StandingsStore(
            url: base.appendingPathComponent("Standings", isDirectory: true)
                .appendingPathComponent("standings.json")
        )
    }

    /// The stored standings, or nil when nothing usable is stored: an absent, unreadable or
    /// undecodable file is nothing stored, never a crash.
    func load() -> LoadedStandings? {
        // Security S1: the read below fetches an https address as happily as a file. A store is
        // only ever a file on this device, so anything else is refused before it is touched.
        guard url.isFileURL,
              let data = try? Data(contentsOf: url),
              let stored = try? JSONDecoder().decode(StoredStandings.self, from: data),
              let fetched = try? FetchedStandings(payload: stored.payload)
        else { return nil }
        return LoadedStandings(
            standings: fetched.standings, fetchedAt: stored.fetchedAt, payload: fetched.payload
        )
    }

    /// Best effort, like the gap register: a store that cannot be written costs a download, never
    /// the reader's answer.
    func save(_ fetched: FetchedStandings, at date: Date) {
        guard url.isFileURL, let data = try? JSONEncoder().encode(
            StoredStandings(fetchedAt: date, payload: fetched.payload)
        ) else { return }
        try? FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        try? data.write(to: url, options: .atomic)
    }

    /// The standings to combine now: the stored ones while younger than a day, otherwise a fresh
    /// fetch, which is stored. A failed fetch serves the last good standings and keeps their time.
    /// A stored time ahead of `now` (a clock that stepped back) is fetched again.
    func current(now: Date, fetch: () async throws -> FetchedStandings) async -> Standings? {
        let stored = load()
        if let stored, stored.fetchedAt <= now, now.timeIntervalSince(stored.fetchedAt) < Self.maxAge {
            return stored.standings
        }
        do {
            let fresh = try await fetch()
            save(fresh, at: now)
            return fresh.standings
        } catch {
            return stored?.standings
        }
    }
}
