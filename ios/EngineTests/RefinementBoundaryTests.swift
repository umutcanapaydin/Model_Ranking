//  M17-W5 P2 (#64, D-168 clause 2) -- the on-device model's refinements pass the same boundary as
//  its surface: a value the table does not declare, or one the chosen surface does not allow, is
//  dropped and never acted on. Tested without the model, on every machine, as the surface is.

import XCTest

@testable import ModelRankingEngine

final class RefinementBoundaryTests: OfflineTestCase {
    private let served = ["coding", "assistant", "vision", "mathematics"]

    private func values(_ outcome: RoutingOutcome?) -> [String] {
        (outcome?.refinements ?? []).map(\.value)
    }

    func testDeclaredValuesTheSurfaceAllowsAreKept() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "french", .domain: "legal"])

        XCTAssertEqual(outcome?.categoryID, "assistant")
        XCTAssertEqual(values(outcome), ["french", "legal"])
    }

    func testAValueTheTableDoesNotDeclareIsDropped() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "klingon", .domain: "legal"])

        XCTAssertEqual(values(outcome), ["legal"], "an undeclared language was acted on")
    }

    func testAValueOfAnotherKindIsDropped() {
        // `legal` is a domain; emitted as a language it names nothing.
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "legal"])

        XCTAssertEqual(values(outcome), [])
    }

    func testAValueTheSurfaceDoesNotAllowIsDropped() {
        // A language refines the chat surfaces, not coding.
        let outcome = ModelOutputBoundary.outcome(
            for: "coding", within: served, refinements: [.language: "french"])

        XCTAssertEqual(outcome?.categoryID, "coding")
        XCTAssertEqual(values(outcome), [])
    }

    func testNoneAddsNothing() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served,
            refinements: [.language: ModelOutputBoundary.noRefinement, .domain: "legal"])

        XCTAssertEqual(values(outcome), ["legal"])
    }

    func testADeclinedQuestionCarriesNoRefinement() {
        let outcome = ModelOutputBoundary.outcome(
            for: ModelOutputBoundary.declineSentinel, within: served, refinements: [.language: "french"])

        XCTAssertEqual(outcome?.unmeasured, true)
        XCTAssertEqual(values(outcome), [])
    }

    func testARefusedSurfaceIsRefusedWhateverTheRefinements() {
        XCTAssertNil(ModelOutputBoundary.outcome(
            for: "sql-tuning", within: served, refinements: [.language: "french"]))
    }

    func testTheSchemaOffersEachKindsDeclaredValuesAndTheWayOut() {
        for kind in RefinementKind.allCases {
            let choices = ModelOutputBoundary.refinementChoices(for: kind)
            let declared = Refinements.table.filter { $0.kind == kind }.map(\.value)

            XCTAssertEqual(Set(choices), Set(declared + [ModelOutputBoundary.noRefinement]), "\(kind)")
            XCTAssertFalse(choices.contains(ModelOutputBoundary.declineSentinel))
        }
    }

    func testTheWayOutIsNotAValueAnyRefinementUses() {
        XCTAssertFalse(Refinements.table.contains { $0.value == ModelOutputBoundary.noRefinement })
    }

    func testTheWordingTierNeverRefines() async {
        // Asserts only where the embedding assets load; elsewhere the tier answers nothing (review
        // M5). `test_only_the_model_output_boundary_builds_an_outcome_with_refinements` holds the
        // rule on every machine, from the source.
        let outcome = await SimilarityRouter().route(
            "I want to write a contract in French for a legal case", within: served)

        XCTAssertEqual(outcome?.refinements ?? [], [])
    }

    func testTheModelsSchemaBuildsForTheServedSurfaces() throws {
        // Tester R1: `route` falls back to the next tier when the schema cannot be built, with no
        // other sign. The schema needs the framework, not an enabled model, so this runs wherever
        // FoundationModels exists.
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            XCTAssertNoThrow(try ModelRouter.schema(for: served))
            XCTAssertNoThrow(try ModelRouter.schema(for: ["assistant"]))
        }
        #endif
    }

    func testTheModelsSchemaOffersExactlyTheDeclaredChoicesAndNothingElse() throws {
        // Security pass S1: the text pins held that the closed sets were PRESENT, not that the
        // schema holds nothing else. Read from the schema itself, as the model receives it, so an
        // added free-text field, an appended filter or a lost way out each fail here.
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            let data = try JSONEncoder().encode(try ModelRouter.schema(for: served))
            let root = try XCTUnwrap(try JSONSerialization.jsonObject(with: data) as? [String: Any])
            // D-169 (M18-W3): the request verdict, a closed yes/no, beside the surface and refinements.
            let fields = Set(["request", "surface"] + RefinementKind.allCases.map(\.rawValue))

            XCTAssertEqual(root["additionalProperties"] as? Bool, false)
            XCTAssertEqual(Set(root["required"] as? [String] ?? []), fields)
            XCTAssertEqual(Set((root["properties"] as? [String: Any] ?? [:]).keys), fields)
            let definitions = try XCTUnwrap(root["$defs"] as? [String: [String: Any]])
            XCTAssertEqual(Set(definitions.keys), fields)

            func offered(_ field: String) throws -> [String] {
                let options = try XCTUnwrap(definitions[field]?["anyOf"] as? [[String: Any]], field)
                return try options.flatMap { option -> [String] in
                    // Every option is a fixed string: a bare `"type": "string"` would admit anything.
                    XCTAssertEqual(option["type"] as? String, "string", field)
                    return try XCTUnwrap(option["enum"] as? [String], "\(field) offers a free value")
                }
            }
            XCTAssertEqual(try offered("surface"), served + [ModelOutputBoundary.declineSentinel])
            XCTAssertEqual(try offered("request"), ["a model search", "something else"])
            for kind in RefinementKind.allCases {
                XCTAssertEqual(try offered(kind.rawValue),
                               Refinements.table.filter { $0.kind == kind }.map(\.value) + ["none"])
            }
        }
        #endif
    }

    func testTheModelTierOffersNoAlternatives() {
        // Security pass S1: an alternative is a surface the reader can tap, and a tap sends it to
        // the engine as `task`. Only the wording tier ranks them, from the ids the engine serves.
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.language: "french", .domain: "legal"])

        XCTAssertEqual(outcome?.alternatives, [])
    }

    func testTheManualTierNeverRefines() async {
        // Review M5: the last tier, when neither the model nor the wording answers.
        struct Silent: QuestionRouter {
            func route(_ question: String, within known: [String]) async -> RoutingOutcome? { nil }
        }
        let outcome = await TieredRouter(model: nil, similarity: Silent())
            .route("I want to write a contract in French for a legal case", within: served)

        XCTAssertEqual(outcome.tier, .manual)
        XCTAssertEqual(outcome.refinements, [])
    }

    func testTheOutcomeNamesTheBoardsItSelects() {
        let outcome = ModelOutputBoundary.outcome(
            for: "assistant", within: served, refinements: [.domain: "legal", .language: "french"])
        let boards = outcome.map { Refinements.boards(primary: "arena", surface: $0.categoryID, chosen: $0.refinements) }

        XCTAssertEqual(boards, ["arena", "arena_text_french", "arena_text_industry_legal_and_government"])
    }
}
