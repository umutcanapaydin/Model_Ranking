//  The three defects the owner found by USING the app, 2026-08-22 (M11-W3, REQ-RUN-001).
//
//  Every milestone before this one closed green while these were shipping. They were not missed by
//  a weak test; they were missed because nothing had opened the app. That is the whole content of
//  M10's carried question, answered from the other side: the residue the gates do not catch is
//  caught by execution, and a person is a kind of execution.
//
//  Written RED first, before any fix, per the M11 plan's Trap 2.

import XCTest

@testable import ModelRankingEngine

private let nine = [
    "coding", "agentic-coding", "assistant", "everyday", "expert",
    "mathematics", "computer-use", "abstract", "web-dev",
]

// MARK: - Defect 1 — the on-device tier cannot say "I do not measure this"

final class UnmeasurableThroughTheModelTierTests: XCTestCase {

    /// **The owner typed "Profile picture polishing" and got Agentic coding, with the sentence
    /// "Matched your question to this surface on this device."**
    ///
    /// The cause is structural, not a bad match. `GenerationSchema(anyOf: known)` constrains the
    /// model to the nine ids the engine serves, so tier 1 has no expressible way to decline —
    /// every question in the world, including image editing and calorie counting, comes back as
    /// one of nine measured surfaces with a confident sentence attached.
    ///
    /// REQ-RTR-005 says an unmeasured question routes to `assistant` AND says so. That disclosure
    /// lived only in the SIMILARITY tier's floor, which runs second and therefore almost never
    /// runs at all on a device that has the model. **The control existed in the path that does not
    /// execute.**
    func testTheModelTierCanExpressThatNothingMeasuresTheQuestion() {
        let outcome = ModelOutputBoundary.outcome(
            for: ModelOutputBoundary.declineSentinel, within: nine)

        XCTAssertEqual(outcome?.unmeasured, true,
                       "the model declined and the app reported a measured match")
        XCTAssertEqual(outcome?.categoryID, CategoryHints.unmeasuredFallback)
    }

    func testTheDeclineSentinelIsOfferedToTheModelAlongsideTheRealIds() {
        // A sentinel the schema does not contain is a sentinel the model can never emit.
        let choices = ModelOutputBoundary.schemaChoices(for: nine)

        XCTAssertTrue(choices.contains(ModelOutputBoundary.declineSentinel),
                      "the model is still forced to choose a measured surface")
        XCTAssertEqual(Set(choices).subtracting([ModelOutputBoundary.declineSentinel]), Set(nine),
                       "the choice list drifted from the ids the engine actually serves")
    }

    func testTheSentinelIsNotAValidSurfaceId() {
        // If it collided with a real id the decline would silently become a recommendation.
        XCTAssertFalse(nine.contains(ModelOutputBoundary.declineSentinel))
    }

    func testDecliningStillRefusesWhenTheFallbackSurfaceIsNotServed() {
        XCTAssertNil(
            ModelOutputBoundary.outcome(
                for: ModelOutputBoundary.declineSentinel, within: ["coding", "web-dev"]),
            "the router named `assistant` on a surface list that does not have it")
    }

    func testAMeasuredAnswerIsStillMeasured() {
        // Fixture blindness: the decline path must not swallow ordinary answers.
        let outcome = ModelOutputBoundary.outcome(for: "web-dev", within: nine)

        XCTAssertEqual(outcome?.unmeasured, false)
        XCTAssertEqual(outcome?.categoryID, "web-dev")
    }
}

// MARK: - Defect 2 — the surface the router chose is not the one shown first

final class AnswerOrderingTests: XCTestCase {

    /// **The owner typed "Coding", the app selected Coding, and the first block on screen read
    /// "Agentic coding".** He read that as the router ignoring him, and repeated it three times.
    ///
    /// `task=coding` expands server-side to `CODING_INTENT = ("agentic-coding", "coding")`, and
    /// `/v1` states in its own payload that answer order carries no meaning. So the client is free
    /// to order them — and had not, so the alphabetically-first surface always spoke first.
    ///
    /// This is NOT the re-sorting the plan's Trap 1 forbids: that is about reordering MODELS inside
    /// a ranking, which is the engine's answer. Which of two ANSWERS appears first is explicitly
    /// meaningless to the engine and explicitly meaningful to the reader who just asked.
    func testTheSelectedSurfaceIsShownFirst() {
        let ordered = orderAnswers(surfaces: ["agentic-coding", "coding"], selected: "coding")

        XCTAssertEqual(ordered.first, "coding",
                       "the reader asked for `coding` and another surface answered first")
    }

    func testTheOtherSurfacesKeepTheirRelativeOrder() {
        let ordered = orderAnswers(
            surfaces: ["abstract", "agentic-coding", "coding"], selected: "coding")

        XCTAssertEqual(ordered, ["coding", "abstract", "agentic-coding"],
                       "reordering the selected surface must not shuffle the rest")
    }

    func testASingleAnswerIsUnchanged() {
        XCTAssertEqual(orderAnswers(surfaces: ["mathematics"], selected: "mathematics"),
                       ["mathematics"])
    }

    func testASelectionThatIsNotAmongTheAnswersLeavesTheOrderAlone() {
        // The engine answered something else entirely; inventing an order would hide that.
        XCTAssertEqual(orderAnswers(surfaces: ["abstract", "coding"], selected: "web-dev"),
                       ["abstract", "coding"])
    }
}

// MARK: - Defect 3 — the list repeats what the picks already showed

final class RankingPreviewTests: XCTestCase {

    /// **"Claude Opus 5" appeared as Best Quality in large type and again, immediately below, in
    /// the small list.** The owner's words: there is no point showing, further down the list, the
    /// ones we already showed in the first three.
    ///
    /// His shape: of the top five, the first three large and the next two small. So the preview is
    /// the top of the ranking with the pick models REMOVED, and short enough that the two together
    /// are five.
    func testThePreviewDoesNotRepeatAModelAlreadyShownAsAPick() {
        let preview = previewRows(
            ranking: ["opus", "gpt", "grok", "gemini", "llama", "mistral"],
            pickedModels: ["opus", "gpt", "grok"])

        XCTAssertFalse(preview.contains("opus"), "the preview repeated a pick")
        XCTAssertEqual(preview, ["gemini", "llama"])
    }

    func testThePicksAndThePreviewTogetherShowFive() {
        let preview = previewRows(
            ranking: ["a", "b", "c", "d", "e", "f", "g"], pickedModels: ["a", "b", "c"])

        XCTAssertEqual(preview.count, 2)
    }

    func testFewerPicksStillYieldsFiveVisibleModels() {
        // A surface can produce fewer than three picks — one model can be two picks at once, which
        // the owner's own screenshot shows (DeepSeek V4 Flash is both Best Value and Budget Pick).
        let preview = previewRows(ranking: ["a", "b", "c", "d", "e", "f"], pickedModels: ["a"])

        XCTAssertEqual(preview.count, 4, "one pick should leave room for four more, not two")
        XCTAssertEqual(preview, ["b", "c", "d", "e"])
    }

    func testAShortRankingIsNotPadded() {
        let preview = previewRows(ranking: ["a", "b"], pickedModels: ["a", "b"])

        XCTAssertEqual(preview, [], "nothing is left to preview and nothing was invented")
    }

    func testNoPicksAtAllPreviewsTheTopFive() {
        let preview = previewRows(ranking: ["a", "b", "c", "d", "e", "f"], pickedModels: [])

        XCTAssertEqual(preview, ["a", "b", "c", "d", "e"])
    }
}

// MARK: - Second owner session, 2026-08-23

private struct Row: Equatable {
    let model: String
    let vendor: String
}

final class RankingFilterTests: XCTestCase {

    private let rows = [
        Row(model: "Claude Opus 4.7", vendor: "Anthropic"),
        Row(model: "GPT-5.5", vendor: "OpenAI"),
        Row(model: "Gemini 3.5 Flash", vendor: "Google"),
        Row(model: "GPT-5.2 Codex", vendor: "OpenAI"),
        Row(model: "Qwen3 Coder", vendor: "Alibaba"),
    ]

    private func matches(_ text: String) -> [String] {
        filterRanking(rows, by: text, name: { $0.model }, vendor: { $0.vendor }).map(\.model)
    }

    /// The owner's report was *"it filters by category, not by model name"*. It does not — and this
    /// is the test that says so. `c` matches every model whose NAME or VENDOR contains it,
    /// including Claude, which is the row he was not looking at because the list had kept its
    /// scroll offset and clamped to the end.
    func testASingleLetterMatchesEveryNameThatContainsIt() {
        XCTAssertEqual(matches("c"), ["Claude Opus 4.7", "GPT-5.2 Codex", "Qwen3 Coder"])
    }

    func testTheVendorMatchesToo() {
        XCTAssertEqual(matches("anthropic"), ["Claude Opus 4.7"])
        XCTAssertEqual(matches("google"), ["Gemini 3.5 Flash"])
    }

    func testCaseDoesNotMatter() {
        XCTAssertEqual(matches("CLAUDE"), matches("claude"))
    }

    func testAnEmptyOrBlankFilterShowsEverything() {
        XCTAssertEqual(matches("").count, rows.count)
        XCTAssertEqual(matches("   ").count, rows.count)
    }

    func testSurroundingSpaceDoesNotBreakAMatch() {
        XCTAssertEqual(matches("  codex  "), ["GPT-5.2 Codex"])
    }

    func testNothingMatchesWhenNothingMatches() {
        XCTAssertEqual(matches("zzzz"), [])
    }
}
