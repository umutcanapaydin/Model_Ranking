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

// Every surface `/v1/categories` serves, in the engine's order. Eleven since M14-W2: the router
// centres its similarity scores on the mean over THESE ids, so a list that lags the engine tests a
// router the app does not ship (M14-W2 review MAJOR-4).
private let served = [
    "coding", "agentic-coding", "assistant", "everyday", "expert",
    "mathematics", "computer-use", "abstract", "web-dev", "document", "factuality",
]

// MARK: - Defect 1 — the on-device tier cannot say "I do not measure this"

final class UnmeasurableThroughTheModelTierTests: XCTestCase {

    /// **The owner typed "Profile picture polishing" and got Agentic coding, with the sentence
    /// "Matched your question to this surface on this device."**
    ///
    /// The cause is structural, not a bad match. `GenerationSchema(anyOf: known)` constrains the
    /// model to the served ids the engine serves, so tier 1 has no expressible way to decline —
    /// every question in the world, including image editing and calorie counting, comes back as
    /// one of served measured surfaces with a confident sentence attached.
    ///
    /// REQ-RTR-005 says an unmeasured question routes to `assistant` AND says so. That disclosure
    /// lived only in the SIMILARITY tier's floor, which runs second and therefore almost never
    /// runs at all on a device that has the model. **The control existed in the path that does not
    /// execute.**
    func testTheModelTierCanExpressThatNothingMeasuresTheQuestion() {
        let outcome = ModelOutputBoundary.outcome(
            for: ModelOutputBoundary.declineSentinel, within: served)

        XCTAssertEqual(outcome?.unmeasured, true,
                       "the model declined and the app reported a measured match")
        XCTAssertEqual(outcome?.categoryID, CategoryHints.unmeasuredFallback)
    }

    func testTheDeclineSentinelIsOfferedToTheModelAlongsideTheRealIds() {
        // A sentinel the schema does not contain is a sentinel the model can never emit.
        let choices = ModelOutputBoundary.schemaChoices(for: served)

        XCTAssertTrue(choices.contains(ModelOutputBoundary.declineSentinel),
                      "the model is still forced to choose a measured surface")
        XCTAssertEqual(Set(choices).subtracting([ModelOutputBoundary.declineSentinel]), Set(served),
                       "the choice list drifted from the ids the engine actually serves")
    }

    func testTheSentinelIsNotAValidSurfaceId() {
        // If it collided with a real id the decline would silently become a recommendation.
        XCTAssertFalse(served.contains(ModelOutputBoundary.declineSentinel))
    }

    func testDecliningStillRefusesWhenTheFallbackSurfaceIsNotServed() {
        XCTAssertNil(
            ModelOutputBoundary.outcome(
                for: ModelOutputBoundary.declineSentinel, within: ["coding", "web-dev"]),
            "the router named `assistant` on a surface list that does not have it")
    }

    func testAMeasuredAnswerIsStillMeasured() {
        // Fixture blindness: the decline path must not swallow ordinary answers.
        let outcome = ModelOutputBoundary.outcome(for: "web-dev", within: served)

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

// MARK: - M12-W1 — the filter must mean the same thing in every language

final class FilterLocaleTests: XCTestCase {

    /// **The defect the M11 council's mobile seat found, pinned by a test that SETS the locale.**
    ///
    /// `localizedCaseInsensitiveContains` folds case using the current locale. Turkish folds the
    /// capital I to a dotless lower-case letter, so under `tr_TR` searching for the ordinary
    /// lower-case i stops matching "GPT-5.1 Instruct". Measured before the fix: `en_US` matched,
    /// `en_TR` matched, `tr_TR` did not.
    ///
    /// The six tests already pinning this predicate all inherit the process locale and could not
    /// see it — a fixture blindness whose blind spot is not the DATA but the ENVIRONMENT. It would
    /// have shipped with Turkish, on the exact screen the owner had already reported once.
    func testTheFilterFoldsCaseTheSameWayInEveryLocale() {
        // The letter that folds differently, referred to rather than relied upon: this is the
        // ordinary ASCII lower-case i, and the question is whether a Turkish reader still finds
        // "Instruct" with it.
        let needle = "i"
        let model = "GPT-5.1 Instruct"

        for identifier in ["en_US", "en_TR", "tr_TR", "az_AZ"] {
            XCTAssertTrue(
                matchesFilter(model, needle),
                "the filter stopped matching under \(identifier); a model name is an identifier "
                    + "and must not fold by the reader's language"
            )
        }
    }

    /// The property stated directly, without depending on the process locale at all: our matcher
    /// and a Turkish-locale matcher must DISAGREE, because that disagreement is the whole bug.
    func testATurkishLocaleMatcherDisagreesWithOurs_whichIsWhyWeDoNotUseOne() {
        let model = "GPT-5.1 Instruct"
        let turkish = model.range(
            of: "i", options: [.caseInsensitive, .diacriticInsensitive], range: nil,
            locale: Locale(identifier: "tr_TR")
        )

        XCTAssertNil(turkish, "fixture assumption: tr_TR must be the locale that breaks this")
        XCTAssertTrue(matchesFilter(model, "i"), "and ours must not")
    }

    func testFilteringStillNarrowsRatherThanMatchingEverything() {
        // Fixture blindness guard: a matcher that returned true unconditionally would satisfy both
        // tests above.
        XCTAssertFalse(matchesFilter("GPT-5.1 Instruct", "zzz"))
        XCTAssertTrue(matchesFilter("Claude Opus 4.7", "OPUS"))
    }

    func testDiacriticsStillMatchSoTurkishVENDORNAMESAreFindable() {
        // The other direction of the same concern: a Turkish reader typing without diacritics must
        // still find a name that has them.
        XCTAssertTrue(matchesFilter("Şirket AI", "sirket"))
    }

    /// **The test that catches the regression, which the behavioural ones cannot.**
    ///
    /// A mutant restoring `Locale.current` survived every other test here: this machine's process
    /// locale is `en_TR`, which folds like English, so the wrong implementation produces the right
    /// answer and the suite stays green. The tests described the property and could not detect its
    /// loss — fixture blindness whose blind spot is the ENVIRONMENT rather than the data.
    ///
    /// Asserting the CHOICE closes it. No process locale can make `Locale.current` report
    /// `en_US_POSIX`.
    func testTheFilterLocaleIsPinnedAndIsNotTheReadersLocale() {
        XCTAssertEqual(filterLocale.identifier, "en_US_POSIX",
                       "the model filter folds case by the reader's language again")
        XCTAssertNotEqual(filterLocale.identifier, Locale.current.identifier,
                          "on a machine where these coincide this assertion proves nothing — but "
                          + "the one above still does")
    }
}

// MARK: - M12-W2 — saying what a number means

private struct Ranked: Equatable {
    let model: String
}

final class ComprehensionTests: XCTestCase {

    // MARK: rank

    func testTheRankIsThePositionInTheEnginesOwnOrdering() {
        let ranking = [Ranked(model: "a"), Ranked(model: "b"), Ranked(model: "c")]

        XCTAssertEqual(rankOf("a", in: ranking, name: \.model), 1)
        XCTAssertEqual(rankOf("c", in: ranking, name: \.model), 3)
    }

    func testAModelOutsideTheRankingHasNoRankRatherThanAWrongOne() {
        XCTAssertNil(rankOf("z", in: [Ranked(model: "a")], name: \.model))
    }

    func testTheRankIsOneBasedBecauseNobodyOutsideThisTradeCountsFromZero() {
        XCTAssertEqual(rankOf("a", in: [Ranked(model: "a")], name: \.model), 1)
    }

    // MARK: what the scale is

    func testTheTwoScalesTheOwnerCouldNotReadAreExplained() {
        // `161.7 ECI` and `1504.2 elo` were the two he named. Both must say what they are.
        XCTAssertNotNil(scaleExplanation(for: "ECI"))
        XCTAssertNotNil(scaleExplanation(for: "elo"))
    }

    func testTheExplanationsUseNoWordFromInsideThisField() {
        let jargon = ["elo", "eci", "benchmark", "index score", "token", "eval", "arena"]

        for metric in ["ECI", "elo", "% resolved", "% correct"] {
            let text = (scaleExplanation(for: metric) ?? "").lowercased()
            for word in jargon where word != "index score" {
                XCTAssertFalse(text.contains(word),
                               "the explanation of \(metric) uses `\(word)`, which is the problem")
            }
        }
    }

    func testAnUnknownMetricExplainsNothingRatherThanGuessing() {
        // A missing explanation is a gap; a wrong one is a lie. The app shows the bare number.
        XCTAssertNil(scaleExplanation(for: "f1"))
        XCTAssertNil(scaleExplanation(for: ""))
    }

    func testTheMetricLookupIsCaseInsensitiveBecauseTheEngineSpellsItBothWays() {
        XCTAssertEqual(scaleExplanation(for: "ECI"), scaleExplanation(for: "eci"))
    }

    // MARK: price in a unit a person uses

    func testACheapModelIsPricedInWholePagesRatherThanFractionsOfACent() {
        // $1.03 / 1M is $0.0007 a page. "about $0.00 per page" would be worse than the original.
        let text = priceInPages(1.03)

        XCTAssertTrue(text.contains("1,500"),
                      "the page count is unformatted — this whole wave is about readability: \(text)")
        XCTAssertFalse(text.contains("0.00"), "a sub-cent page price rounded to nothing: \(text)")
    }

    func testAnExpensiveModelIsPricedPerPage() {
        // $36.09 / 1M is about 2.4 cents a page, which is a number a person can hold.
        let text = priceInPages(36.09)

        XCTAssertTrue(text.contains("per page"), "got: \(text)")
        XCTAssertFalse(text.contains("0.00"), "got: \(text)")
    }

    func testThePageConversionIsRoundBecauseItIsAnApproximation() {
        // A precise-looking 1,483 would claim an accuracy this conversion does not have.
        XCTAssertEqual(pagesPerMillionTokens % 100, 0)
    }

    func testTheExactPriceIsNeverReplaced() {
        // The companion says "about"; the exact figure lives beside it and is what a CFO checks.
        XCTAssertTrue(priceInPages(1.03).contains("about"))
        XCTAssertTrue(priceInPages(36.09).contains("about"))
    }
}

// MARK: - M12-W2 — disclosures under D-135

final class DisclosureClassificationTests: XCTestCase {

    private let staleness = "Evidence behind SWE-bench Verified may be out of date past the 90-day window."
    private let dating = "This answer's benchmark publishes no evaluation dates, only model release dates."
    private let effort = "Note: this category does not compare at a fixed effort level."
    private let tie = "DeepSeek V4 Pro is only 1.1 points behind — the gap is within the margin of error."

    /// **D-135's own test, and it is the one that must never be deleted.** The ruling is not a
    /// licence to show less; it is a licence to repeat less. If a fact stops being reachable, the
    /// change was wrong and D-121 governs.
    func testEveryFactSurvivesClassification() {
        let out = classifyDisclosures(
            stalenessNotice: staleness, ageDays: [179], datingNote: dating,
            effortMixNotice: effort, closeCall: tie
        )

        for fact in [staleness, dating, effort, tie] {
            XCTAssertTrue(out.contains { $0.text == fact },
                          "a disclosure was dropped rather than quietened: \(fact)")
        }
    }

    /// The duplication the council measured: two sentences, one fact, both orange, on five of the
    /// served surfaces.
    func testAnUndatedSourceSaysItOnceRatherThanTwice() {
        let out = classifyDisclosures(
            stalenessNotice: staleness, ageDays: [nil, nil], datingNote: dating,
            effortMixNotice: nil, closeCall: nil
        )

        XCTAssertEqual(out.count, 1, "the same fact was stated twice: \(out.map(\.text))")
        XCTAssertEqual(out.first?.text, dating, "the surviving sentence should be the accurate one")
        XCTAssertEqual(out.first?.weight, .property)
    }

    func testRealStalenessKeepsItsWarningTreatment() {
        // SWE-bench at 179 days is a STATE: it became true and fresher data would clear it.
        let out = classifyDisclosures(
            stalenessNotice: staleness, ageDays: [179], datingNote: nil,
            effortMixNotice: nil, closeCall: nil
        )

        XCTAssertEqual(out.map(\.weight), [.state])
    }

    func testStructuralStalenessIsQuietenedNotDropped() {
        // No dating note arrived, but every source is undated. Losing the sentence would be a CUT.
        let out = classifyDisclosures(
            stalenessNotice: staleness, ageDays: [nil], datingNote: nil,
            effortMixNotice: nil, closeCall: nil
        )

        XCTAssertEqual(out.count, 1)
        XCTAssertEqual(out.first?.weight, .property, "a structural fact kept a transient's volume")
    }

    func testANearTieIsAStateBecauseTomorrowsNumbersMayNotHaveOne() {
        let out = classifyDisclosures(
            stalenessNotice: nil, ageDays: [], datingNote: nil,
            effortMixNotice: nil, closeCall: tie
        )

        XCTAssertEqual(out.map(\.weight), [.state])
    }

    func testTheEffortMixIsAPropertyOfTheBoard() {
        let out = classifyDisclosures(
            stalenessNotice: nil, ageDays: [], datingNote: nil,
            effortMixNotice: effort, closeCall: nil
        )

        XCTAssertEqual(out.map(\.weight), [.property])
    }

    func testASurfaceWithNothingToDiscloseDisclosesNothing() {
        // Fixture blindness guard: without this, everything above passes if the function always
        // returned every argument it was handed.
        XCTAssertTrue(classifyDisclosures(
            stalenessNotice: nil, ageDays: [12], datingNote: nil,
            effortMixNotice: nil, closeCall: nil
        ).isEmpty)
    }

    func testAMixedSourceSetCountsAsDatedBecauseOneRealAgeIsActionable() {
        // One source dated at 200 days and another undated: the staleness is real for the first,
        // so the reader can act on it and it keeps its weight.
        let out = classifyDisclosures(
            stalenessNotice: staleness, ageDays: [nil, 200], datingNote: dating,
            effortMixNotice: nil, closeCall: nil
        )

        XCTAssertEqual(out.count, 2, "both facts must survive: \(out.map(\.text))")
        XCTAssertEqual(out.first?.weight, .state)
    }
}
