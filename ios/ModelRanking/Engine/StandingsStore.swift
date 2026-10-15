//  StandingsStore.swift — the last standings the engine sent, kept on the phone for a day (D-167).
//
//  The phone fetches every board's standings whatever the question is (D-160 clause 1) and keeps
//  them, so a question asked offline is still answered. This file holds exactly what the engine
//  sent, as this app decoded it, with the time it arrived. Nothing the reader typed ever reaches it:
//  its only input is a `FetchedStandings`, which stores only the fields the app decodes.
//
//  Since #288 (D-202 clause 5) it also keeps, in a file of its own beside the standings file, the last
//  answer the engine sent for each surface, so a question asked while the engine cannot be reached shows
//  that answer, dated. The surface and the budget those answers were asked for are the only things
//  derived from the question that this file writes, and they never reach the standings file (INV-66).
//
//  It is the second file the client-declaration gate lets touch the file system, beside the gap
//  register in `FrontDoor.swift`, and each file-system call below is permitted as that exact
//  expression by the text gate (`tests/unit/test_router_hints.py`, D-167 clause 4). Both files this
//  store keeps go through the one read and the one write below.

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

    /// A copy kept without credits, by a build from before the Credits screen or from an engine older
    /// than it, is kept this long rather than a day (#260): the screen fills within the hour, and an
    /// engine that sends none is asked at most once an hour. Dated by `now` alone, so the rule holds
    /// in any order (the Tester's M2; a launch date, read lazily, did not).
    static let maxAgeWithoutCredits: TimeInterval = 3_600

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
        guard let data = contents(),
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
        guard let data = try? JSONEncoder().encode(
            StoredStandings(fetchedAt: date, payload: fetched.payload)
        ) else { return }
        replaceContents(with: data)
    }

    /// The store's file, or nil when it is absent or empty. The one read in this file.
    private func contents() -> Data? {
        // Security S1: the read below fetches an https address as happily as a file. A store is
        // only ever a file on this device, so anything else is refused before it is touched.
        guard url.isFileURL,
              let data = try? Data(contentsOf: url),
              !data.isEmpty
        else { return nil }
        return data
    }

    /// The one write in this file, to the store's own file and only when it is a file (Security S1).
    private func replaceContents(with data: Data) {
        guard url.isFileURL else { return }
        try? FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        try? data.write(to: url, options: .atomic)
    }

    /// The standings to use now: the stored ones while younger than a day, otherwise a fresh
    /// fetch, which is stored. A failed fetch serves the last good standings and keeps their time.
    /// A stored time ahead of `now` (a clock that stepped back) is fetched again.
    func current(now: Date, fetch: () async throws -> FetchedStandings) async -> Standings? {
        await currentKept(now: now, fetch: fetch)?.standings
    }

    /// #170: `currentKept` dated by the store's own clock. The app calls this one: a date the screen
    /// chose would be a 64-bit channel from the screen into the standings file (INV-66), so only this
    /// file, and the tests, reach the dated form (`PROVENANCE` in `scripts/client_decl_gate.py`).
    func currentKept(fetch: () async throws -> FetchedStandings) async -> KeptStandings? {
        await currentKept(now: Date(), fetch: fetch)
    }

    /// `current`, with the time the served standings arrived, so a copy kept past a day because a
    /// newer one could not be fetched can be said on screen (M18-W2 review M3, #72).
    func currentKept(now: Date, fetch: () async throws -> FetchedStandings) async -> KeptStandings? {
        let stored = load()
        // The #260 review's M2: a copy without credits is fetched again within the hour rather than
        // leaving the screen empty for up to a day; and only hourly (round 2's M1), so an engine that
        // sends none is not asked on every load.
        let kept = stored?.standings.credits == nil ? Self.maxAgeWithoutCredits : Self.maxAge
        if let stored, stored.fetchedAt <= now, now.timeIntervalSince(stored.fetchedAt) < kept {
            return KeptStandings(standings: stored.standings, fetchedAt: stored.fetchedAt)
        }
        do {
            let fresh = try await fetch()
            save(fresh, at: now)
            return KeptStandings(standings: fresh.standings, fetchedAt: now)
        } catch {
            return stored.map { KeptStandings(standings: $0.standings, fetchedAt: $0.fetchedAt) }
        }
    }
}

/// Standings as served, and when they arrived on this phone.
struct KeptStandings {
    let standings: Standings
    let fetchedAt: Date
}

/// Whole days the served copy has been kept past the day it is meant to last, or `nil` while it is
/// younger than a day, or when its time is unknown or ahead of `now`.
func staleCopyDays(fetchedAt: Date?, now: Date) -> Int? {
    guard let fetchedAt, fetchedAt <= now else { return nil }
    let age = now.timeIntervalSince(fetchedAt)
    guard age >= StandingsStore.maxAge else { return nil }
    return Int(age / 86_400)
}

/// #288 (D-202 clause 5): one answer the engine sent, kept so that it can be shown, dated, while the
/// engine cannot be reached. What is written for it, and nothing else.
struct KeptAnswer: Codable, Equatable {
    /// The route that sent it (`KeptAnswers.recommendationsRoute` or `KeptAnswers.categoriesRoute`).
    let route: String
    /// The surface and the budget the request carried, the two values `/v1/recommendations` is sent
    /// (REQ-RTR-004); both empty for the surfaces' list, which is asked with neither.
    let task: String
    let budget: String
    /// When it arrived, by this store's clock.
    let fetchedAt: Date
    /// The answer as the app decoded it, encoded again (`KeptAnswers.payload`), so a field the app does
    /// not decode is never kept.
    let payload: Data
}

extension StandingsStore {
    /// How many answers are kept: more than the engine has surfaces, so each surface keeps its own,
    /// and few enough that the file stays small. The oldest goes first.
    static let maxKeptAnswers = 32

    /// The kept answers' file, beside the standings file and never the same one (INV-66).
    private var answersFile: StandingsStore {
        StandingsStore(url: url.deletingLastPathComponent().appendingPathComponent("answers.json"))
    }

    /// Every kept answer, oldest first, or none when nothing usable is kept: an absent, unreadable or
    /// undecodable file is nothing kept, never a crash.
    func keptAnswers() -> [KeptAnswer] {
        guard let data = answersFile.contents(),
              let kept = try? JSONDecoder().decode([KeptAnswer].self, from: data)
        else { return [] }
        return kept
    }

    /// Keep an answer the engine just sent, dated by this store's clock (#170's rule for the
    /// standings: the screen does not choose the date written beside what it keeps).
    func keep(route: String, task: String, budget: String, payload: Data) {
        keep(route: route, task: task, budget: budget, payload: payload, at: Date())
    }

    /// `keep`, dated. A newer answer for the same route, surface and budget replaces the older one;
    /// past `maxKeptAnswers` the oldest is dropped. Best effort, like the standings.
    func keep(route: String, task: String, budget: String, payload: Data, at date: Date) {
        var kept = keptAnswers()
        kept.removeAll { $0.route == route && $0.task == task && $0.budget == budget }
        kept.append(KeptAnswer(route: route, task: task, budget: budget, fetchedAt: date, payload: payload))
        while kept.count > Self.maxKeptAnswers {
            kept.removeFirst()
        }
        guard let data = try? JSONEncoder().encode(kept) else { return }
        answersFile.replaceContents(with: data)
    }
}
