//  KeptAnswers.swift -- #288 phase 2, red: nothing is kept or shown yet.

import Foundation

enum KeptAnswers {
    static let recommendationsRoute = "v1/recommendations"
    static let categoriesRoute = "v1/categories"
    static let maxAge: TimeInterval = 7 * 86_400

    static func standsIn(for error: EngineError) -> Bool { false }

    static func payload(_ recommendation: Recommendation) -> Data? { nil }

    static func payload(_ categories: [Category]) -> Data? { nil }

    static func recommendation(_ kept: [KeptAnswer], task: String, budget: String,
                               now: Date) -> (recommendation: Recommendation, fetchedAt: Date)? { nil }

    static func categories(_ kept: [KeptAnswer], now: Date) -> (categories: [Category], fetchedAt: Date)? { nil }
}
