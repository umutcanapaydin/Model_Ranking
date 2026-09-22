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

// Every surface `/v1/categories` serves, in the engine's order. Fourteen since M15-W3: the router
// centres its similarity scores on the mean over THESE ids, so a list that lags the engine tests a
// router the app does not ship (M14-W2 review MAJOR-4).
private let served = [
    "coding", "agentic-coding", "assistant", "everyday", "expert",
    "mathematics", "computer-use", "abstract", "web-dev", "document", "factuality",
    "vision", "search", "search_factuality",
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
        let categories = try served.map { id in
            try JSONDecoder().decode(
                ModelRankingEngine.Category.self,
                from: Data(#"{"id": "\#(id)", "title": "T-\#(id)", "primary_benchmark": "B", "metric": "elo", "ranking_effort": null}"#.utf8)
            )
        }

        let choices = surfaceChoices(categories, selected: "mathematics", .english)

        XCTAssertEqual(choices.map(\.id), served, "a surface is unreachable, or the engine's order moved")
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
        let outcome = await shipping.route("make my profile photo look better", within: served)

        XCTAssertEqual(outcome.categoryID, "assistant", "no ranking was loaded for the question")
        XCTAssertTrue(outcome.unmeasured, "an image question was answered as a measured one")
        XCTAssertTrue(routingNotice(outcome, .english).contains("cannot tell you which model is best"))
    }

    /// Wrong AXIS: a measured domain, asked about a property nothing measures.
    func testASpeedQuestionIsAnsweredWithARankingAndTheSentenceSayingWhatItCannotTell() async {
        let outcome = await shipping.route("which model answers fastest", within: served)

        XCTAssertEqual(outcome.categoryID, "assistant")
        XCTAssertTrue(outcome.unmeasured, "a speed question was answered as a measured one")
        XCTAssertTrue(routingNotice(outcome, .turkish).contains("söyleyemez"))
    }

    /// The reviewer's third probe, and the same axis gap.
    func testAContextWindowQuestionIsNotAnsweredAsMeasured() async {
        let outcome = await shipping.route("which model has the longest context window", within: served)

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
            let outcome = await shipping.route(question, within: served)

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
            let outcome = await shipping.route(question, within: served)

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
        let outcome = await shipping.route("make my profile photo look better", within: served)

        XCTAssertTrue(outcome.unmeasured)
        XCTAssertFalse(outcome.alternatives.contains(CategoryHints.unmeasuredFallback))
        XCTAssertLessThanOrEqual(outcome.alternatives.count, 2)
        XCTAssertTrue(outcome.alternatives.allSatisfy(served.contains))
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
            let outcome = await SimilarityRouter().route(question, within: served)

            XCTAssertEqual(outcome?.categoryID, surface, question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }

    /// The POSITIVE half, added by the M14 closure seat's MAJOR-4: a reader can actually REACH the
    /// two surfaces M14 added.
    ///
    /// Every other test of these ids checks that the nine older questions do not fall out of an
    /// eleven-id list -- all negatives. The milestone's premise is that people reach a surface by
    /// asking for it in their own words, and nothing asserted that. This runs the real embedding
    /// router, like the calibration probe above, so a hint reworded into a neighbour's territory
    /// fails here rather than on a reader's phone.
    ///
    /// If this fails after a hint edit, the hint is the defect, not the test: both questions are
    /// plain readings of what each surface measures.
    func testTheTwoNewSurfacesAreReachableByAsking() async {
        let probe: [(String, String)] = [
            ("summarise this 40 page contract pdf for me", "document"),
            ("is this quote real or did it invent the citation", "factuality"),
            // M15-W3, the same rule as the two above: a surface nobody can reach is not a surface.
            ("what is in this screenshot i am sending", "vision"),
            ("search the web for today's gold price", "search"),
            ("look it up online and give me the real source", "search_factuality"),
        ]
        for (question, surface) in probe {
            let outcome = await SimilarityRouter().route(question, within: served)

            XCTAssertEqual(outcome?.categoryID, surface, question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }

    /// M15-W3 review m-3: W-115 narrowed the image decline group to MAKING and CHANGING images,
    /// because `vision` now ranks READING one -- and nothing tested it. The seat put the reading
    /// questions back into the decline group and all 257 Swift tests stayed green.
    func testAQuestionAboutReadingAnImageReachesVisionRatherThanTheImageDecline() async {
        for question in ["describe this photo", "what is in this picture"] {
            let outcome = await SimilarityRouter().route(question, within: served)

            XCTAssertEqual(outcome?.categoryID, "vision", question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
        // and the other half of W-115's narrowing: MAKING one is still declined
        let made = await SimilarityRouter().route("generate an image of a cat", within: served)
        XCTAssertEqual(made?.unmeasured, true)
    }

    /// M15-W3 review m-4: the positive routing tests above paraphrase the router's own examples, so
    /// they prove the examples reach a surface, not that a reader's own words do. These five were
    /// written for the D-147 held-out set (`scripts/router_probe/heldout_questions.json`), before
    /// the examples they are routed against existed, and were never tuned on.
    func testQuestionsNobodyTunedOnStillReachTheSurfaceTheyName() async {
        let heldOut: [(String, String)] = [
            ("my unit tests fail after upgrading pandas", "coding"),
            ("answer questions from this 200 page annual report", "document"),
            ("read the numbers off this bar chart image", "vision"),
            ("what is the weather in berlin today", "search"),
            ("how do i politely decline a meeting", "assistant"),
        ]
        for (question, surface) in heldOut {
            let outcome = await SimilarityRouter().route(question, within: served)

            XCTAssertEqual(outcome?.categoryID, surface, question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }

    /// W-118 / M16-W1 review M-1: the examples that fixed ordinary questions have a regression
    /// test, so reverting them fails here rather than on a reader's phone.
    ///
    /// Before M16-W1 these three reached `vision`, `search` and `coding` with `unmeasured` false --
    /// the app answering a household question with a ranking of models for reading screenshots.
    /// `assistant` had no general example among its six and `vision`'s were question-shaped
    /// sentences any short question resembled (`docs/reviews/m16-router-floor-measurement.md`).
    /// Measured: all three route to `assistant` with the shipped examples and none of them does
    /// with the previous set.
    func testAnOrdinaryQuestionLandsOnGeneralHelpRatherThanAMeasuredSurface() async {
        for question in ["how do i cook rice",
                         "my back hurts what should i do",
                         "how do i change a flat tyre"] {
            let outcome = await SimilarityRouter().route(question, within: served)

            XCTAssertEqual(outcome?.categoryID, "assistant", question)
        }
    }

    /// W-118: the floor still decides, and nonsense is declined -- but NOT by the floor, and the
    /// difference is the finding.
    ///
    /// `docs/reviews/m16-router-floor-measurement.md` re-measured 86 questions under D-147's
    /// scoring: nonsense scores 0.16-0.40 and the lowest CORRECT route scores 0.232, so the ranges
    /// overlap and nothing below 0.15 was observed at all. What declines `zzz` is the decline
    /// groups outscoring every surface. So this test asserts both facts separately, rather than
    /// crediting the floor with work it does not do: the floor is exercised on a question that
    /// routes confidently (both sides of the threshold, the M13 seat's requirement), and nonsense
    /// is asserted to be declined however that happens.
    func testTheFloorDecidesAndNonsenseIsDeclinedByTheGroupsInstead() async {
        let real = "fix a bug in my python repo"

        let routed = await SimilarityRouter().route(real, within: served)
        XCTAssertEqual(routed?.unmeasured, false, real)

        let unreachable = await SimilarityRouter(floor: 0.9).route(real, within: served)
        XCTAssertEqual(unreachable?.unmeasured, true, "the floor no longer decides anything")

        let noise = await SimilarityRouter().route("zzz", within: served)
        XCTAssertEqual(noise?.unmeasured, true, "nonsense routed as a measured question")
        let noiseWithoutFloor = await SimilarityRouter(floor: 0.0).route("zzz", within: served)
        XCTAssertEqual(noiseWithoutFloor?.unmeasured, true, "it is the decline groups, not the floor")
    }

    /// The model tier's decline PATH, labelled as what it is: the sentinel reaches the notice. It
    /// does not read the question, and it is not cited as the wrong-modality or wrong-axis test.
    func testTheModelTiersDeclineIsCarriedThroughToTheNotice() async {
        let outcome = await TieredRouter(model: DecliningModel(), similarity: Silent())
            .route("anything at all", within: served)

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

        let outcome = await router.route("¿cuál es el mejor modelo?", within: served)

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
            .route("fix the failing unit test in my python project", within: served)

        let alternatives = outcome?.alternatives ?? []
        XCTAssertEqual(alternatives.count, 2)
        XCTAssertFalse(alternatives.contains(outcome?.categoryID ?? ""),
                       "the chosen surface was offered as its own alternative")
        XCTAssertTrue(alternatives.allSatisfy(served.contains), "an alternative is not a served surface")
        XCTAssertEqual(Set(alternatives).count, alternatives.count)
    }

    func testAnUnmeasuredQuestionOffersNoAlternativesBecauseNothingMatched() async {
        let outcome = await SimilarityRouter(floor: 2.0)
            .route("fix the failing unit test in my python project", within: served)

        XCTAssertEqual(outcome?.alternatives, [])
    }

    /// W3 Tester SA6: the engine's list can arrive in any order; the choice and its alternatives
    /// must not move with it.
    func testTheAlternativesDoNotDependOnTheOrderTheSurfacesArrivedIn() async {
        let question = "fix the failing unit test in my python project"
        let rotated = Array(served[4...] + served[..<4])

        let first = await SimilarityRouter(floor: -2.0).route(question, within: served)
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

        let outcome = await router.route("fix my code", within: served)

        XCTAssertEqual(outcome.tier, .similarity, "the question waited for a model that never came")
        XCTAssertLessThan(Date().timeIntervalSince(started), 5,
                          "the deadline was waited out by the call it exists to abandon")
    }

    func testAModelTierThatAnswersInTimeIsStillUsed() async {
        let model = RoutingOutcome(categoryID: "web-dev", tier: .model, unmeasured: false)
        let router = TieredRouter(model: Fixed(outcome: model), similarity: Fixed(outcome: wording),
                                  modelTimeout: 5)

        let outcome = await router.route("build me a landing page", within: served)

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

// MARK: - REQ-GAP-001/002 (M14-W3): the gap register

final class GapRegisterTests: XCTestCase {
    private let t0 = Date(timeIntervalSince1970: 1_800_000_000)

    /// REQ-GAP-001: an unmeasured question is recorded with a count.
    func testAQuestionIsRecordedAndCounted() {
        var register = GapRegister()
        register.record("make my profile photo look better", at: t0)
        register.record("make my profile photo look better", at: t0.addingTimeInterval(60))

        XCTAssertEqual(register.entries.count, 1)
        XCTAssertEqual(register.entries.first?.count, 2)
        XCTAssertEqual(register.entries.first?.lastAsked, t0.addingTimeInterval(60))
    }

    /// Case and runs of whitespace do not make a second gap -- and the fold ignores the reader's
    /// locale, so a Turkish phone does not split `I` from `i` (W-079).
    func testTwoSpellingsOfOneQuestionAreOneGap() {
        var register = GapRegister()
        register.record("Image  Enchantment", at: t0)
        register.record("  image enchantment ", at: t0)

        XCTAssertEqual(register.entries.count, 1)
        XCTAssertEqual(register.entries.first?.count, 2)
        XCTAssertEqual(register.entries.first?.question, "Image  Enchantment", "shown as first typed")
    }

    /// Blank text is not a question.
    func testBlankTextRecordsNothing() {
        var register = GapRegister()
        register.record("   \n ", at: t0)
        XCTAssertTrue(register.entries.isEmpty)
    }

    /// REQ-GAP-002: most-asked first; among equals, the most recent first.
    func testTheOwnerReadsTheMostAskedFirst() {
        var register = GapRegister()
        register.record("a", at: t0)
        register.record("b", at: t0.addingTimeInterval(10))
        register.record("b", at: t0.addingTimeInterval(20))
        register.record("c", at: t0.addingTimeInterval(30))

        XCTAssertEqual(register.ordered.map(\.question), ["b", "c", "a"])
    }

    /// Bounded: a pasted document is not stored whole, and the list cannot grow without end.
    func testTheRegisterIsBounded() {
        var register = GapRegister()
        register.record(String(repeating: "x", count: 5_000), at: t0)
        XCTAssertEqual(register.entries.first?.question.count, GapRegister.maxLength)

        register.clear()
        for index in 0..<(GapRegister.maxEntries + 5) {
            register.record("question \(index)", at: t0.addingTimeInterval(Double(index)))
        }
        XCTAssertEqual(register.entries.count, GapRegister.maxEntries)
        XCTAssertFalse(register.entries.contains { $0.question == "question 0" },
                       "the least-asked, oldest entry is the one that makes room")
    }

    /// It survives a relaunch, and an unreadable file is an empty register rather than a crash.
    func testTheRegisterRoundTripsThroughItsFile() throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString).appendingPathComponent("gap-register.json")
        let store = GapRegisterStore(url: url)
        var register = GapRegister()
        register.record("which model is best at tax tables", at: t0)
        store.save(register)

        XCTAssertEqual(store.load(), register)

        try Data("not json".utf8).write(to: url)
        XCTAssertEqual(store.load(), GapRegister())
    }
}

/// The M14-W3/W4 review's fixes to the gap register (m-1, S-2, S-3).
final class GapRegisterHardeningTests: XCTestCase {
    /// m-1: a router failure is not a gap in the catalogue.
    func testOnlyARoutedUnmeasuredQuestionIsAGap() {
        XCTAssertTrue(recordsGap(RoutingOutcome(categoryID: "assistant", tier: .similarity, unmeasured: true)))
        XCTAssertTrue(recordsGap(RoutingOutcome(categoryID: "assistant", tier: .model, unmeasured: true)))
        XCTAssertFalse(recordsGap(RoutingOutcome(categoryID: "assistant", tier: .manual, unmeasured: true)))
        XCTAssertFalse(recordsGap(RoutingOutcome(categoryID: "coding", tier: .similarity, unmeasured: false)))
    }

    /// S-3: one character loaded with combining marks is still held to the byte bound.
    func testAnEntryIsBoundedInBytesNotOnlyCharacters() {
        var register = GapRegister()
        let heavy = "a" + String(repeating: "\u{0301}", count: 5_000) + " photo"
        register.record(heavy)
        let stored = register.entries.first?.question ?? ""
        XCTAssertLessThanOrEqual(stored.utf8.count, GapRegister.maxBytes)
    }

    /// S-2: the register lives in a folder of its own, which is what carries the backup exclusion.
    func testTheRegisterLivesInItsOwnFolder() {
        XCTAssertEqual(
            GapRegisterStore.onDevice.url.deletingLastPathComponent().lastPathComponent, "GapRegister"
        )
    }

    /// S-1: the phone's store writes with complete file protection.
    func testThePhonesStoreIsProtectedWhileLocked() {
        XCTAssertTrue(GapRegisterStore.onDevice.writeOptions.contains(.completeFileProtection))
    }

    /// And a save into a fresh folder round-trips, folder created on the way.
    func testASaveCreatesItsFolderAndRoundTrips() throws {
        let folder = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let store = GapRegisterStore(url: folder.appendingPathComponent("gap-register.json"))
        var register = GapRegister()
        register.record("remove the background from my photo")
        store.save(register)
        XCTAssertEqual(store.load(), register)
    }

    /// M15 closure security seat, MAJOR-1: the exclusion was guarded only by a STRING in the source,
    /// so `isExcludedFromBackup = false` written after it passed every gate. This reads what the
    /// file system actually recorded, for the folder (which an atomic write never replaces) and the
    /// file, after a real save.
    func testASavedRegisterIsExcludedFromBackupOnDisk() throws {
        let folder = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString, isDirectory: true)
        defer { try? FileManager.default.removeItem(at: folder) }
        let file = folder.appendingPathComponent("gap-register.json")
        var register = GapRegister()
        register.record("make this photo sharper")
        GapRegisterStore(url: file).save(register)

        for url in [folder, file] {
            let values = try url.resourceValues(forKeys: [.isExcludedFromBackupKey])
            XCTAssertEqual(values.isExcludedFromBackup, true, "\(url.lastPathComponent) would be backed up")
        }
    }
}
