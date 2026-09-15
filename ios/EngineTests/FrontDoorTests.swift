//  M13-W3 — the question is the front door (REQ-ASK-001..004).
//
//  There is no UI test target in this repository, and the plan (§7) records the consequence: the
//  front door's LOGIC lives in the Engine so that each criterion has a test able to fail, and
//  `ContentView` only renders it. What these tests cannot reach — whether a finger on the field
//  raises a keyboard — was partly verified on the simulator (focus, yes; the keyboard, no) and the
//  rest is the owner's to verify, as the W3 close records.

import XCTest

@testable import ModelRankingEngine

private struct DecliningModel: QuestionRouter {
    /// The on-device tier recognised the question and said nothing here measures it.
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        ModelOutputBoundary.outcome(for: ModelOutputBoundary.declineSentinel, within: known)
    }
}

private struct Silent: QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? { nil }
}

/// Answers with what it was given, immediately.
private struct Fixed: QuestionRouter {
    let outcome: RoutingOutcome?
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? { outcome }
}

/// Raised once, read from any task.
private final class Flag: @unchecked Sendable {
    private let lock = NSLock()
    private var raised = false

    func raise() {
        lock.lock()
        raised = true
        lock.unlock()
    }

    var isRaised: Bool {
        lock.lock()
        defer { lock.unlock() }
        return raised
    }
}

/// A model call that does not come back in any time a reader would wait.
private struct Hanging: QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        try? await Task.sleep(nanoseconds: 10_000_000_000)
        return RoutingOutcome(categoryID: "web-dev", tier: .model, unmeasured: false)
    }
}

private let nine = [
    "coding", "agentic-coding", "assistant", "everyday", "expert",
    "mathematics", "computer-use", "abstract", "web-dev",
]

// MARK: - REQ-ASK-004

final class RequestGateTests: XCTestCase {
    /// The citing test: two loads resolve out of order, and the newer selection survives.
    func testASlowerResponseForAnOlderSelectionCannotOverwriteTheNewerOne() {
        var gate = RequestGate()
        var shown: String?

        let mathematics = gate.begin()  // the reader chooses Mathematics…
        let coding = gate.begin()       // …then Coding, before Mathematics has answered.

        // Coding answers first; Mathematics' slower response lands afterwards.
        for (ticket, surface) in [(coding, "coding"), (mathematics, "mathematics")]
        where gate.isCurrent(ticket) {
            shown = surface
        }

        XCTAssertEqual(shown, "coding", "the stale Mathematics answer replaced the Coding selection")
    }

    func testTheCurrentResponseIsAppliedWhicheverOrderTheyArriveIn() {
        // The pairing: a gate that refused everything would pass the test above.
        var gate = RequestGate()
        let first = gate.begin()
        let second = gate.begin()

        XCTAssertFalse(gate.isCurrent(first))
        XCTAssertTrue(gate.isCurrent(second))
    }

    func testEveryLoadGetsANewTicket() {
        var gate = RequestGate()
        let tickets = (0..<5).map { _ in gate.begin() }

        XCTAssertEqual(Set(tickets).count, 5, "two loads shared a ticket, so neither can be told apart")
        XCTAssertTrue(gate.isCurrent(tickets.last!))
    }

    /// M13-W3 review BLOCKING-2: the reader asks, then picks a surface from `Change` while the
    /// question is still routing. The routing result must not replace that choice.
    func testASelectionMadeWhileAQuestionRoutesWins() {
        var routingGate = RequestGate()

        let question = routingGate.begin()  // the reader asks…
        routingGate.invalidate()            // …and chooses Mathematics before the router answers.

        XCTAssertFalse(routingGate.isCurrent(question),
                       "the late routing result would replace the surface the reader chose")
    }
}

// MARK: - REQ-ASK-001

final class SubmissionTests: XCTestCase {
    func testAQuestionCanBeSentWhenNothingIsRouting() {
        XCTAssertTrue(canSubmit("prove a theorem", inFlight: false))
    }

    func testNothingIsSentTwiceWhileTheFirstIsStillRouting() {
        XCTAssertFalse(canSubmit("prove a theorem", inFlight: true))
    }

    func testBlankQuestionsAreNotSent() {
        for blank in ["", "   ", "\n\t "] {
            XCTAssertFalse(canSubmit(blank, inFlight: false), "`\(blank)` was submittable")
        }
    }
}

// MARK: - REQ-ASK-002

final class EchoTests: XCTestCase {
    func testTheReadersOwnWordsAreShownBesideWhatTheyWereMatchedTo() {
        XCTAssertEqual(echoLine(question: "prove a theorem", surfaceTitle: "Mathematics"),
                       "“prove a theorem” → Mathematics")
    }

    func testTheEchoIsTrimmedAndKeptToOneLine() {
        XCTAssertEqual(echoLine(question: "  prove\na theorem  ", surfaceTitle: "Mathematics"),
                       "“prove a theorem” → Mathematics")
    }

    func testALongQuestionIsCutRatherThanWrappedIntoAParagraph() {
        let long = String(repeating: "word ", count: 40)
        let echo = echoLine(question: long, surfaceTitle: "Chat")

        XCTAssertTrue(echo?.contains("…”") == true, echo ?? "nil")
        XCTAssertLessThanOrEqual(echo?.count ?? .max, echoLimit + "“…” → Chat".count)
    }

    func testAnEmptyQuestionHasNoEcho() {
        XCTAssertNil(echoLine(question: "   ", surfaceTitle: "Coding"))
    }

    /// The boundary, both sides (W3 Tester EL1a, EL1c): the limit is quoted whole, and one more
    /// character is where the cut starts.
    func testAQuestionOfExactlyTheLimitIsQuotedWhole() {
        let exact = String(repeating: "a", count: echoLimit)

        XCTAssertEqual(echoLine(question: exact, surfaceTitle: "Chat"), "“\(exact)” → Chat")
    }

    func testOneCharacterOverTheLimitIsCut() {
        let over = String(repeating: "a", count: echoLimit + 1)
        let kept = String(repeating: "a", count: echoLimit)

        XCTAssertEqual(echoLine(question: over, surfaceTitle: "Chat"), "“\(kept)…” → Chat")
    }

    func testTheCorrectionReachesEverySurfaceTheEngineServes() throws {
        let categories = try nine.map { id in
            try JSONDecoder().decode(
                ModelRankingEngine.Category.self,
                from: Data(#"{"id": "\#(id)", "title": "T-\#(id)", "primary_benchmark": "B", "metric": "elo", "ranking_effort": null}"#.utf8)
            )
        }

        let choices = surfaceChoices(categories, selected: "mathematics", .english)

        XCTAssertEqual(choices.map(\.id), nine, "a surface is unreachable, or the engine's order moved")
        XCTAssertEqual(choices.filter(\.isSelected).map(\.id), ["mathematics"])
        XCTAssertEqual(choices.first?.title, "T-coding", "English uses the engine's own title")
    }

    func testTheCorrectionIsInTheReadersLanguage() throws {
        let coding = try JSONDecoder().decode(
            ModelRankingEngine.Category.self,
            from: Data(#"{"id": "coding", "title": "Coding", "primary_benchmark": "B", "metric": "elo", "ranking_effort": null}"#.utf8)
        )

        XCTAssertEqual(surfaceChoices([coding], selected: "x", .turkish).first?.title, "Kod yazma")
    }
}

// MARK: - REQ-ASK-003

final class UnmeasuredQuestionTests: XCTestCase {
    /// The tier that IS the product for most of the device base (plan §0): no model, the real
    /// wording tier. M13-W3 review BLOCKING-1 — the first version of these tests stubbed a model
    /// tier that declined whatever it was asked, so the question strings were never read, and on
    /// this tier both questions went to `everyday` as MEASURED answers.
    private let shipping = TieredRouter(model: nil, similarity: SimilarityRouter())

    /// Wrong MODALITY: an image job, which no surface measures.
    func testAnImageQuestionIsAnsweredWithARankingAndTheSentenceSayingWhatItCannotTell() async {
        let outcome = await shipping.route("make my profile photo look better", within: nine)

        XCTAssertEqual(outcome.categoryID, "assistant", "no ranking was loaded for the question")
        XCTAssertTrue(outcome.unmeasured, "an image question was answered as a measured one")
        XCTAssertTrue(routingNotice(outcome, .english).contains("cannot tell you which model is best"))
    }

    /// Wrong AXIS: a measured domain, asked about a property nothing measures.
    func testASpeedQuestionIsAnsweredWithARankingAndTheSentenceSayingWhatItCannotTell() async {
        let outcome = await shipping.route("which model answers fastest", within: nine)

        XCTAssertEqual(outcome.categoryID, "assistant")
        XCTAssertTrue(outcome.unmeasured, "a speed question was answered as a measured one")
        XCTAssertTrue(routingNotice(outcome, .turkish).contains("söyleyemez"))
    }

    /// The reviewer's third probe, and the same axis gap.
    func testAContextWindowQuestionIsNotAnsweredAsMeasured() async {
        let outcome = await shipping.route("which model has the longest context window", within: nine)

        XCTAssertTrue(outcome.unmeasured, "a context-window question was answered as a measured one")
    }

    /// W3 re-review NEW-1: measured tasks that MENTION a photo, a video or a frame. The wording tier
    /// cannot always tell them from questions ABOUT those things (the probe table is in the W3
    /// close), so the property held here is the one a reader needs: the right surface is either
    /// the answer, or the FIRST one-tap alternative. It holds whichever way a future hint change
    /// moves these questions.
    func testAMeasuredTaskIsNeverMoreThanOneTapFromItsSurface() async {
        let cases: [(String, String)] = [
            ("click through a website and upload a photo", "computer-use"),
            ("a web app for streaming video", "web-dev"),
            ("solve this geometry problem about a picture frame", "mathematics"),
            ("build a photo gallery website", "web-dev"),
        ]
        for (question, surface) in cases {
            let outcome = await shipping.route(question, within: nine)

            if outcome.unmeasured {
                XCTAssertEqual(outcome.alternatives.first, surface,
                               "\(question): declined, and its surface is not one tap away")
            } else {
                XCTAssertEqual(outcome.categoryID, surface, question)
            }
        }
    }

    /// The W3 Tester re-run's over-declines. Which single surface is "right" is arguable for
    /// these, so each names the surfaces a reader could reasonably want, and the property is that
    /// one of them is the answer or one tap away.
    func testTheTestersOverDeclinesStayWithinOneTapOfAReasonableSurface() async {
        let cases: [(String, Set<String>)] = [
            ("write a script that resizes images", ["coding", "agentic-coding"]),
            ("optimise the latency of my web API", ["coding", "web-dev"]),
        ]
        for (question, reasonable) in cases {
            let outcome = await shipping.route(question, within: nine)

            if outcome.unmeasured {
                XCTAssertFalse(reasonable.isDisjoint(with: outcome.alternatives),
                               "\(question): declined with \(outcome.alternatives), none of them \(reasonable)")
            } else {
                XCTAssertTrue(reasonable.contains(outcome.categoryID), question)
            }
        }
    }

    /// W3 Tester RN2t, RN3t: a MEASURED match must not carry the unmeasured sentence in Turkish.
    func testAMeasuredMatchDoesNotSayItCannotTellInTurkish() {
        for tier in [RoutingTier.model, .similarity] {
            let outcome = RoutingOutcome(categoryID: "coding", tier: tier, unmeasured: false)

            XCTAssertFalse(routingNotice(outcome, .turkish).contains("söyleyemez"), "\(tier)")
        }
    }

    func testADeclineNeverOffersTheChatRankingItIsAlreadyShowing() async {
        let outcome = await shipping.route("make my profile photo look better", within: nine)

        XCTAssertTrue(outcome.unmeasured)
        XCTAssertFalse(outcome.alternatives.contains(CategoryHints.unmeasuredFallback))
        XCTAssertLessThanOrEqual(outcome.alternatives.count, 2)
        XCTAssertTrue(outcome.alternatives.allSatisfy(nine.contains))
    }

    /// The other side, so the decline hints cannot pass the tests above by declining everything:
    /// the M10 calibration probe's seven correct routes (`docs/reviews/m10-router-calibration.md`,
    /// run 4) still land where they did, and none of them is flagged unmeasured.
    func testTheCalibrationProbeStillRoutesWhereItDidBefore() async {
        let probe: [(String, String)] = [
            ("fix a bug in my python repo", "coding"),
            ("build me a landing page", "web-dev"),
            ("solve this competition math problem", "mathematics"),
            ("an agent that refactors my codebase", "agentic-coding"),
            ("click through this website and fill form", "computer-use"),
            ("a logic puzzle with no examples", "abstract"),
            ("help me write an email to my landlord", "assistant"),
        ]
        for (question, surface) in probe {
            let outcome = await SimilarityRouter().route(question, within: nine)

            XCTAssertEqual(outcome?.categoryID, surface, question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }

    /// The model tier's decline PATH, labelled as what it is: the sentinel reaches the notice. It
    /// does not read the question, and it is not cited as the wrong-modality or wrong-axis test.
    func testTheModelTiersDeclineIsCarriedThroughToTheNotice() async {
        let outcome = await TieredRouter(model: DecliningModel(), similarity: Silent())
            .route("anything at all", within: nine)

        XCTAssertEqual(outcome.tier, .model)
        XCTAssertTrue(outcome.unmeasured)
        XCTAssertTrue(routingNotice(outcome, .english).contains("cannot tell you which model is best"))
    }

    /// MINOR-5: the wording tier says what it can know — that the WORDS point nowhere measured —
    /// and not a fact about the catalogue.
    func testTheWordingTiersDeclineSaysItIsGoingByTheWording() {
        let outcome = RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: true)

        XCTAssertTrue(routingNotice(outcome, .english).hasPrefix("Going by its wording"))
        XCTAssertFalse(routingNotice(outcome, .english).contains("best at conversation"))
    }

    /// Each Turkish branch says its own thing (W3 Tester RN1t, RN2t): the manual fallback names the
    /// control that corrects it, the wording tier says it went by the wording, and the model tier
    /// does not.
    func testEveryUnmeasuredBranchSaysItsOwnThingInTurkish() {
        let manual = RoutingOutcome(categoryID: "assistant", tier: .manual, unmeasured: true)
        let wording = RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: true)
        let model = RoutingOutcome(categoryID: "assistant", tier: .model, unmeasured: true)

        XCTAssertTrue(routingNotice(manual, .turkish).contains("Değiştir"))
        XCTAssertTrue(routingNotice(wording, .turkish).hasPrefix("Kelimelerine bakılırsa"))
        XCTAssertTrue(routingNotice(model, .turkish).contains("söyleyemez"))
        XCTAssertFalse(routingNotice(model, .turkish).hasPrefix("Kelimelerine"))
    }

    /// The contradiction second-opinion P1 found: `manual` loaded a ranking while claiming to be
    /// measured and telling the reader to pick a surface that was already picked for them.
    func testWhenBothTiersDeclineTheFallbackIsLabelledUnmeasured() async {
        let router = TieredRouter(model: nil, similarity: Silent())

        let outcome = await router.route("¿cuál es el mejor modelo?", within: nine)

        XCTAssertEqual(outcome.tier, .manual)
        XCTAssertTrue(outcome.unmeasured, "`tier = manual` may not carry `unmeasured = false`")
        XCTAssertFalse(routingNotice(outcome, .english).contains("below."),
                       "the old 'Pick a surface below' sentence survived with no strip below it")
        XCTAssertTrue(routingNotice(outcome, .english).contains("Change"))
    }

    func testAMeasuredMatchDoesNotCarryTheUnmeasuredSentence() {
        for tier in [RoutingTier.model, .similarity] {
            let outcome = RoutingOutcome(categoryID: "coding", tier: tier, unmeasured: false)

            XCTAssertFalse(routingNotice(outcome, .english).contains("cannot tell you"), "\(tier)")
        }
    }

    func testTheEnglishExplanationIsTheSameSentenceTheScreenShows() {
        let outcome = RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: true)

        XCTAssertEqual(outcome.explanation, routingNotice(outcome, .english))
    }

    func testEveryNoticeSpeaksBothLanguagesAndTheyDiffer() {
        let outcomes = [
            RoutingOutcome(categoryID: "coding", tier: .model, unmeasured: false),
            RoutingOutcome(categoryID: "coding", tier: .similarity, unmeasured: false),
            RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: true),
            RoutingOutcome(categoryID: "assistant", tier: .manual, unmeasured: true),
        ]
        for outcome in outcomes {
            XCTAssertNotEqual(routingNotice(outcome, .english), routingNotice(outcome, .turkish))
        }
    }
}

// MARK: - Alternatives: correcting in one tap

final class AlternativeSurfaceTests: XCTestCase {
    func testTheWordingTierOffersTheNextClosestSurfacesAsAlternatives() async {
        let outcome = await SimilarityRouter(floor: -2.0)
            .route("fix the failing unit test in my python project", within: nine)

        let alternatives = outcome?.alternatives ?? []
        XCTAssertEqual(alternatives.count, 2)
        XCTAssertFalse(alternatives.contains(outcome?.categoryID ?? ""),
                       "the chosen surface was offered as its own alternative")
        XCTAssertTrue(alternatives.allSatisfy(nine.contains), "an alternative is not a served surface")
        XCTAssertEqual(Set(alternatives).count, alternatives.count)
    }

    func testAnUnmeasuredQuestionOffersNoAlternativesBecauseNothingMatched() async {
        let outcome = await SimilarityRouter(floor: 2.0)
            .route("fix the failing unit test in my python project", within: nine)

        XCTAssertEqual(outcome?.alternatives, [])
    }

    /// W3 Tester SA6: the engine's list can arrive in any order; the choice and its alternatives
    /// must not move with it.
    func testTheAlternativesDoNotDependOnTheOrderTheSurfacesArrivedIn() async {
        let question = "fix the failing unit test in my python project"
        let rotated = Array(nine[4...] + nine[..<4])

        let first = await SimilarityRouter(floor: -2.0).route(question, within: nine)
        let second = await SimilarityRouter(floor: -2.0).route(question, within: rotated)

        XCTAssertEqual(first?.categoryID, second?.categoryID)
        XCTAssertEqual(first?.alternatives, second?.alternatives)
    }
}

// MARK: - A slow tier is a failing tier (REQ-RTR-003, M13-W3 review MINOR-6)

final class SlowTierTests: XCTestCase {
    private let wording = RoutingOutcome(categoryID: "coding", tier: .similarity, unmeasured: false)

    func testAModelTierThatNeverAnswersHandsTheQuestionToTheWordingTier() async {
        let router = TieredRouter(model: Hanging(), similarity: Fixed(outcome: wording),
                                  modelTimeout: 0.2)
        let started = Date()

        let outcome = await router.route("fix my code", within: nine)

        XCTAssertEqual(outcome.tier, .similarity, "the question waited for a model that never came")
        XCTAssertLessThan(Date().timeIntervalSince(started), 5,
                          "the deadline was waited out by the call it exists to abandon")
    }

    func testAModelTierThatAnswersInTimeIsStillUsed() async {
        let model = RoutingOutcome(categoryID: "web-dev", tier: .model, unmeasured: false)
        let router = TieredRouter(model: Fixed(outcome: model), similarity: Fixed(outcome: wording),
                                  modelTimeout: 5)

        let outcome = await router.route("build me a landing page", within: nine)

        XCTAssertEqual(outcome.tier, .model, "the deadline cut off a model that answered")
    }

    /// W3 re-review-2 R3-4: the abandoned call is not only left behind, it is told to stop.
    func testTheCallThatMissesTheDeadlineIsCancelled() async {
        let cancelled = Flag()

        let result: Int? = await firstWithin(0.1) {
            await withTaskCancellationHandler {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                return 1
            } onCancel: {
                cancelled.raise()
            }
        }

        XCTAssertNil(result, "the deadline did not win against a call that sleeps five seconds")
        for _ in 0..<100 where !cancelled.isRaised {
            try? await Task.sleep(nanoseconds: 20_000_000)
        }
        XCTAssertTrue(cancelled.isRaised, "the abandoned call was never cancelled")
    }

    /// W3 Tester FW2: when the work wins, the deadline task still fires later and tries to resume
    /// the same continuation. Resuming twice is fatal, so surviving past the deadline IS the test.
    func testAFastAnswerSurvivesTheDeadlineFiringAfterIt() async {
        let result: Int? = await firstWithin(0.1) { 1 }

        XCTAssertEqual(result, 1)
        try? await Task.sleep(nanoseconds: 400_000_000)  // the deadline task fires in here
    }

    /// M13 Stage 4.0 NIT-1: `UInt64(_:)` traps on NaN and past about 1.8e10 seconds. No wire value
    /// reaches the deadline today, so surviving these calls IS the test.
    func testADeadlineThatIsNotASensibleNumberDoesNotTrap() async {
        for hostile in [Double.nan, -.infinity, .infinity] {
            let result: Int? = await firstWithin(hostile) { 1 }
            XCTAssertTrue(result == nil || result == 1, "\(hostile)")
        }
        let astronomical: Int? = await firstWithin(1e30) { 1 }
        XCTAssertEqual(astronomical, 1, "a huge deadline is clamped, and the work still wins")
    }

    func testTheShippedDeadlineIsLongerThanTheMeasuredColdStart() {
        // 1.33 s cold on the owner's Mac (M13 handover §4). A deadline under that would send every
        // first question of the day to the wording tier.
        XCTAssertGreaterThan(TieredRouter().modelTimeout, 1.33)
    }
}

// MARK: - The on-device tier, as help

final class OnDeviceHelpTests: XCTestCase {
    func testNothingIsSaidWhenTheModelIsAvailable() {
        XCTAssertNil(OnDeviceState.available.help(.english))
    }

    func testEveryDegradedStateExplainsItselfInBothLanguagesWithoutSoundingLikeAnError() throws {
        for state in [OnDeviceState.notEligible, .turnedOff, .downloading, .unavailable] {
            // `XCTUnwrap`, not `!`: a force unwrap that fails takes the whole run down with it
            // (W3 Tester nit).
            let english = try XCTUnwrap(state.help(.english), "\(state)")
            let turkish = try XCTUnwrap(state.help(.turkish), "\(state)")

            XCTAssertNotEqual(english, turkish)
            XCTAssertFalse(english.lowercased().contains("error"), english)
            XCTAssertTrue(english.contains("wording"), "the reader is not told what still works")
        }
    }

    /// W3 Tester B3: nothing called this, and it is what the help line reads. On a host without
    /// FoundationModels the other branch runs; this one cannot reach it, and the W3 close says so.
    func testTheHelpLineReadsThePlatformsOwnAnswer() {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            XCTAssertEqual(TieredRouter.onDeviceState(), ModelRouter.state)
            return
        }
        #endif
        XCTAssertEqual(TieredRouter.onDeviceState(), .notEligible)
    }
}
