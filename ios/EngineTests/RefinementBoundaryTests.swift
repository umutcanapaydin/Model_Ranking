//  M17-W5 P2 (#64, D-168 clause 2) -- the on-device model's refinements pass the same boundary as
//  its surface: a value the table does not declare, or one the chosen surface does not allow, is
//  dropped and never acted on. Tested without the model, on every machine, as the surface is.

import XCTest
#if canImport(FoundationModels)
import FoundationModels
#endif

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

    func testTheModelReadsWithGreedyDecoding() {
        // #351: with the framework's default (random) sampling the same 173 questions moved by 3 to 7
        // rows between identical runs, so no change to the instructions could be told from noise.
        // Greedy decoding reads one question the same way every time on one model version.
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            XCTAssertEqual(ModelRouter.options, GenerationOptions(sampling: .greedy))
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
            let choices = try Self.closedChoices(in: root)
            XCTAssertEqual(Set(choices.keys), fields)

            func offered(_ field: String) throws -> [String] { try XCTUnwrap(choices[field], field) }
            XCTAssertEqual(try offered("surface"), served + [ModelOutputBoundary.declineSentinel])
            // D-213: the search and five named kinds of non-search, nothing else.
            XCTAssertEqual(try offered("request"), ["model search", "task itself", "fact question", "app question",
                                                    "small talk", "instruction attempt"])
            // M18-W3 (review M6): the verdict is generated LAST. First, it moved questions about
            // documents to other surfaces on the tuning set (16 to 10 of 16).
            XCTAssertEqual(root["x-order"] as? [String], ["surface"] + RefinementKind.allCases.map(\.rawValue) + ["request"])
            for kind in RefinementKind.allCases {
                XCTAssertEqual(try offered(kind.rawValue),
                               Refinements.table.filter { $0.kind == kind }.map(\.value) + ["none"])
            }
        }
        #endif
    }

    private enum SchemaShape: Error { case open(String), unknown }

    /// The closed choices of every field, read from the schema as the running OS encodes it (#362).
    /// macOS 26 puts each field's set under `$defs.<field>` as an `anyOf` of fixed strings; macOS 27
    /// writes it inline as the property itself, `{"type": "string", "enum": [...]}`, with no `$defs`.
    /// Any other shape is refused, so reading two shapes lets no open field through.
    static func closedChoices(in root: [String: Any]) throws -> [String: [String]] {
        if let definitions = root["$defs"] as? [String: [String: Any]] {
            return try definitions.reduce(into: [:]) { choices, entry in
                guard let options = entry.value["anyOf"] as? [[String: Any]] else { throw SchemaShape.open(entry.key) }
                choices[entry.key] = try options.flatMap { try fixedStrings(in: $0, entry.key) }
            }
        }
        guard let properties = root["properties"] as? [String: [String: Any]] else { throw SchemaShape.unknown }
        return try properties.reduce(into: [:]) { choices, entry in
            choices[entry.key] = try fixedStrings(in: entry.value, entry.key)
        }
    }

    private static func fixedStrings(in option: [String: Any], _ field: String) throws -> [String] {
        // Every option is a fixed string: a bare `"type": "string"` would admit anything.
        guard option["type"] as? String == "string", let values = option["enum"] as? [String] else {
            throw SchemaShape.open(field)
        }
        return values
    }

    private func schema(_ json: String) throws -> [String: Any] {
        try XCTUnwrap(try JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: Any])
    }

    func testTheChoicesAreReadFromTheMacOS26Shape() throws {
        // #362: the shape FoundationModels wrote on macOS 26, which the INV-69 pin was written against.
        let root = try schema(#"{"$defs": {"surface": {"anyOf": [{"type": "string", "enum": ["coding"]},"#
            + #"{"type": "string", "enum": ["none"]}]}}}"#)

        XCTAssertEqual(try Self.closedChoices(in: root), ["surface": ["coding", "none"]])
    }

    func testTheChoicesAreReadFromTheMacOS27Shape() throws {
        // #362: macOS 27.0.1 inlines each set as the property itself, with no `$defs` (measured).
        let root = try schema(#"{"properties": {"surface": {"description": "d", "type": "string","#
            + #""enum": ["coding", "none"]}}}"#)

        XCTAssertEqual(try Self.closedChoices(in: root), ["surface": ["coding", "none"]])
    }

    func testAFreeStringIsNeverReadAsAChoice() throws {
        // #362, INV-69: reading a second shape must not let an open field through in either.
        let shapes = [
            #"{"$defs": {"surface": {"anyOf": [{"type": "string"}]}}}"#,
            #"{"$defs": {"surface": {"type": "string", "enum": ["coding"]}}}"#,
            #"{"properties": {"surface": {"type": "string"}}}"#,
            #"{"properties": {"surface": {"anyOf": [{"type": "string", "enum": ["coding"]}]}}}"#,
            #"{"properties": {"surface": {"type": "integer", "enum": ["coding"]}}}"#,
            #"{"type": "object"}"#,
        ]
        for json in shapes {
            XCTAssertThrowsError(try Self.closedChoices(in: try schema(json)), json)
        }
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
        let outcome = await TieredRouter(model: nil, similarity: SilentTier())
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
