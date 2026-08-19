//  Models.swift — the /v1 contract, in Swift.
//
//  These types are a MIRROR of the payload the engine serves, not a design of their own. Every
//  field here exists because `PUBLIC_ANSWER_FIELDS` or `PUBLIC_PICK_FIELDS` in
//  `src/app/adapter/main.py` publishes it, and the shape was read off a live response rather than
//  remembered — a Swift struct written from an imagined payload is exactly the "typed-out
//  enumeration" this project has been caught by five times.
//
//  **Nothing in this file computes.** No sorting, no arithmetic on prices or scores, no derived
//  "best" flag. The engine decides all of that (D-104, D-105, D-109) and the client renders it.
//  If a screen needs a value that is not here, that is a finding against /v1 (D-124), not a
//  licence to compute it on the phone.

import Foundation

/// The whole response to one question.
struct Recommendation: Decodable {
    let apiVersion: String
    let query: Query
    /// Both coding answers arrive here when the task is `coding` — Ruling A, frozen by D-115.
    let answers: [Answer]
    /// The engine's own words about why the order carries no meaning. Rendered, never paraphrased.
    let orderingNote: String
    /// The engine states this explicitly so a client cannot infer ranking from position.
    let surfacesAreRanked: Bool

    enum CodingKeys: String, CodingKey {
        case apiVersion = "api_version"
        case query
        case answers
        case orderingNote = "ordering_note"
        case surfacesAreRanked = "surfaces_are_ranked"
    }
}

/// One rankable surface, as the engine advertises it on `/v1/categories`.
///
/// Fetched rather than hardcoded, deliberately. The engine derives this list from CATEGORIES; a
/// copy of it in Swift would be a second roster to keep in step, and this project has already
/// spent two milestones on the cost of a list typed out by hand.
struct Category: Decodable, Identifiable, Equatable {
    let id: String
    let title: String
    let primaryBenchmark: String
    let metric: String
    let rankingEffort: String?

    enum CodingKeys: String, CodingKey {
        case id
        case title
        case primaryBenchmark = "primary_benchmark"
        case metric
        case rankingEffort = "ranking_effort"
    }
}

struct CategoryList: Decodable {
    let categories: [Category]
}

struct Query: Decodable {
    let task: String
    let budget: String
}

/// One surface's answer. A surface with nothing to say still arrives, carrying the reason.
struct Answer: Decodable, Identifiable {
    let surface: String
    let title: String
    let primaryBenchmark: String
    let metric: String
    let eligibleCount: Int
    let frontierSize: Int
    let picks: [Pick]

    /// Present when `picks` is empty. The engine distinguishes "nothing fits your budget" from
    /// "this surface has no evidence to rank" — two different sentences, and M7 spent a security
    /// round making sure they are not collapsed into one. The client must not collapse them either.
    let unavailableReason: String?

    let closeCall: String?
    let staleNotice: String?
    let effortMixNotice: String?
    let rankingEffort: String?
    let evidenceDating: String?
    let evidenceDatingNote: String?
    let sources: [String]
    let sourceHealth: SourceHealth?

    /// Every model the engine ranked for this surface, in ITS order (D-125).
    ///
    /// This is not "more picks". The three picks answer three different questions; this answers
    /// one, in score order. **The client never re-sorts it** (M8 plan, Trap 1) — re-ordering the
    /// engine's answer is answering a different question with its numbers.
    let ranking: [RankedModel]

    var id: String { surface }

    enum CodingKeys: String, CodingKey {
        case surface, title, metric, picks, sources
        case primaryBenchmark = "primary_benchmark"
        case eligibleCount = "eligible_count"
        case frontierSize = "frontier_size"
        case unavailableReason = "unavailable_reason"
        case closeCall = "close_call"
        case staleNotice = "stale_notice"
        case effortMixNotice = "effort_mix_notice"
        case rankingEffort = "ranking_effort"
        case evidenceDating = "evidence_dating"
        case evidenceDatingNote = "evidence_dating_note"
        case sourceHealth = "source_health"
        case ranking
    }
}

/// One model's position in a surface's ranking. Carries no `label`, `why` or `trade_off`, because
/// nothing chose it — those belong to a `Pick`.
struct RankedModel: Decodable, Identifiable {
    let model: String
    let vendor: String
    let score: Double
    let metric: String
    let secondaryScore: Double?
    let blendedPerM: Double
    let inputPerM: Double
    let outputPerM: Double
    let evidenceDate: String?
    let harness: String
    let effort: String?

    var id: String { model }

    enum CodingKeys: String, CodingKey {
        case model, vendor, score, metric, harness, effort
        case secondaryScore = "secondary_score"
        case blendedPerM = "blended_per_m"
        case inputPerM = "input_per_m"
        case outputPerM = "output_per_m"
        case evidenceDate = "evidence_date"
    }
}

/// How fresh this surface's evidence is, on a wall clock. `notice` is the sentence a user reads.
struct SourceHealth: Decodable {
    let benchmark: String
    let stale: Bool
    let notice: String?
    let sources: [SourceRow]
}

struct SourceRow: Decodable, Identifiable {
    let source: String
    let rows: Int
    let newestRunDate: String?
    let ageDays: Int?
    let stale: Bool

    var id: String { source }

    enum CodingKeys: String, CodingKey {
        case source, rows, stale
        case newestRunDate = "newest_run_date"
        case ageDays = "age_days"
    }
}

/// One labelled answer. `label` is the engine's, not the client's: `best_quality`, `best_value`,
/// `budget_pick`.
struct Pick: Decodable, Identifiable {
    let label: String
    let model: String
    let vendor: String
    let score: Double
    let metric: String
    let secondaryScore: Double?
    let blendedPerM: Double
    let inputPerM: Double
    let outputPerM: Double
    let evidenceDate: String?
    let harness: String
    let effort: String?
    let higherEffort: String?
    let higherEffortScore: Double?
    let effortNote: String?
    let confidence: String
    let confidenceBasis: String
    /// The engine's explanation of why this model was chosen. Displayed verbatim.
    let why: String
    /// What this choice costs relative to the leader. Absent when there is nothing to trade off.
    let tradeOff: String?

    var id: String { "\(label)-\(model)" }

    enum CodingKeys: String, CodingKey {
        case label, model, vendor, score, metric, harness, effort, confidence, why
        case secondaryScore = "secondary_score"
        case blendedPerM = "blended_per_m"
        case inputPerM = "input_per_m"
        case outputPerM = "output_per_m"
        case evidenceDate = "evidence_date"
        case higherEffort = "higher_effort"
        case higherEffortScore = "higher_effort_score"
        case effortNote = "effort_note"
        case confidenceBasis = "confidence_basis"
        case tradeOff = "trade_off"
    }
}

/// The engine's error envelope. `/v1` returns this shape for every refusal.
struct EngineErrorBody: Decodable {
    struct Detail: Decodable {
        let code: String
        let message: String
    }
    let error: Detail
}
