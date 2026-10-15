//  KeptAnswers.swift -- #288 (D-202 clause 5): the last answer the engine sent, shown while it cannot
//  be reached.
//
//  A phone away from its engine showed only the failure sentence. Now the last answer the engine sent
//  for the same surface and budget is shown instead, with the day it arrived, for up to a week. The
//  answers are kept by `StandingsStore` (in a file beside the standings, never in it) as this app
//  decoded them; this file only encodes them to keep, and decides which kept answer, if any, may stand
//  in. Nothing is bundled (REQ-APP-001): an answer the phone shows is one the engine sent it.

import Foundation

enum KeptAnswers {
    /// The two routes whose answers are kept: the answer for a surface, and the surfaces' list.
    static let recommendationsRoute = "v1/recommendations"
    static let categoriesRoute = "v1/categories"

    /// How long a kept answer may stand in for one the engine could not send: a week. The engine
    /// refreshes nightly (D-151), so an older answer is more likely wrong than late.
    static let maxAge: TimeInterval = 7 * 86_400

    /// Whether a failure is one a kept answer stands in for: the engine could not be reached (D-202
    /// clause 5). An engine that answered and refused, or sent what this app cannot read, says so
    /// itself; a cleartext refusal is a setting to fix, which an old answer would hide.
    static func standsIn(for error: EngineError) -> Bool {
        switch error {
        case .unreachable, .timedOut, .offline:
            return true
        case .insecureTransport, .refused, .undecodable:
            return false
        }
    }

    /// An answer as the app decoded it, encoded to keep.
    static func payload(_ recommendation: Recommendation) -> Data? {
        try? JSONEncoder().encode(recommendation)
    }

    /// The surfaces' list as the app decoded it, encoded to keep.
    static func payload(_ categories: [Category]) -> Data? {
        try? JSONEncoder().encode(CategoryList(categories: categories))
    }

    /// The kept answer for this very surface and budget, with the time it arrived, or nil: never one
    /// kept for another surface or budget, nor one whose own query names another, nor one past
    /// `maxAge` or dated after `now`.
    static func recommendation(_ kept: [KeptAnswer], task: String, budget: String,
                               now: Date) -> (recommendation: Recommendation, fetchedAt: Date)? {
        guard let entry = kept.last(where: {
            $0.route == recommendationsRoute && $0.task == task && $0.budget == budget
        }), usable(entry, now: now),
              let answer = try? JSONDecoder().decode(Recommendation.self, from: entry.payload),
              answer.query.task == task, answer.query.budget == budget
        else { return nil }
        return (answer, entry.fetchedAt)
    }

    /// The kept surfaces' list, with the time it arrived, or nil when none is kept, it is past `maxAge`,
    /// or it is empty.
    static func categories(_ kept: [KeptAnswer], now: Date) -> (categories: [Category], fetchedAt: Date)? {
        guard let entry = kept.last(where: { $0.route == categoriesRoute }), usable(entry, now: now),
              let list = try? JSONDecoder().decode(CategoryList.self, from: entry.payload),
              !list.categories.isEmpty
        else { return nil }
        return (list.categories, entry.fetchedAt)
    }

    /// #288 phase 3, red: nothing is shown yet.
    static func shown(after error: EngineError, _ kept: [KeptAnswer], task: String, budget: String,
                      now: Date) -> (recommendation: Recommendation, fetchedAt: Date)? { nil }

    /// Younger than `maxAge`, and not dated after `now` (a clock that stepped back).
    private static func usable(_ entry: KeptAnswer, now: Date) -> Bool {
        entry.fetchedAt <= now && now.timeIntervalSince(entry.fetchedAt) < maxAge
    }
}
