//  The router tiers the Swift tests build `TieredRouter` from (#126, the M18-W3 Tester's K9).
//
//  Eight stubs lived privately in four test files, and there was no shared answering wording tier:
//  the gap the W3 Tester's T6 found, no reading test driving an answering wording tier through
//  `TieredRouter`, grew in that space. They live here, and `test_ios_client_contract.py` refuses a
//  `QuestionRouter` stub declared in any other test file. The canonical model tier with a script is
//  the app's own `ScriptedModelRouter` (D-175 clause 3).

import Foundation

@testable import ModelRankingEngine

/// A tier that never answers, so the question reaches the tier after it.
struct SilentTier: QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? { nil }
}

/// A tier that answers with what it was given, at once, or refuses with `nil`.
struct FixedTier: QuestionRouter {
    let outcome: RoutingOutcome?
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? { outcome }
}

/// A tier that records each question it was asked. A class, so the record survives the copy `route`
/// is called on: a value type cannot record being called.
final class SpyTier: QuestionRouter, @unchecked Sendable {
    private(set) var questions: [String] = []
    let outcome: RoutingOutcome?

    init(outcome: RoutingOutcome?) { self.outcome = outcome }

    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        questions.append(question)
        return outcome
    }
}

/// The on-device model tier that recognised the question and said nothing here measures it.
struct DecliningModelTier: QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        ModelOutputBoundary.outcome(for: ModelOutputBoundary.declineSentinel, within: known)
    }
}

/// A model call that does not come back in any time a reader would wait.
struct HangingTier: QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        try? await Task.sleep(nanoseconds: 10_000_000_000)
        return RoutingOutcome(categoryID: "web-dev", tier: .model, unmeasured: false)
    }
}

/// A wording tier that always names one surface, as `SimilarityRouter` does above its floor.
struct AnsweringWordingTier: QuestionRouter {
    let surface: String
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        RoutingOutcome(categoryID: surface, tier: .similarity, unmeasured: false)
    }
}
