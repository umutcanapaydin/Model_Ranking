//  Router.swift — the front door (D-126, REQ-RTR-001..005).
//
//  D-126 drew the line and this file's whole job is to hold it:
//
//      the router picks the QUESTION; the engine answers it.
//      It may never say a model is good.
//
//  So nothing here produces a recommendation, a model name, or a sentence about quality. The only
//  thing this file can hand the rest of the app is one CATEGORY ID out of the nine the engine
//  advertises — and where the platform allows it, that is a schema constraint rather than an
//  instruction, so the model is not asked to behave: it is unable to do otherwise.
//
//  Nothing typed here leaves the device, on any tier, and nothing is embedded in the app.

import Foundation
import NaturalLanguage

#if canImport(FoundationModels)
import FoundationModels
#endif

/// How the surface was chosen. Shown to the reader, because a keyword-grade match presented as an
/// understanding of the question is a small lie the interface would be telling all day.
enum RoutingTier: String {
    /// The on-device language model, constrained to the nine ids by a generation schema.
    case model
    /// Sentence similarity against the category hints. Works on every device this app targets.
    case similarity
    /// Neither answered. The chat ranking is shown as an UNMEASURED fallback, and the reader
    /// corrects it with Change (M13-W3). A worse experience, and not a wrong one.
    case manual
}

struct RoutingOutcome: Equatable {
    let categoryID: String
    let tier: RoutingTier
    /// True when the question is NOT something the catalogue measures and was answered with the
    /// general chat ranking. REQ-RTR-005: routing there silently would let the product imply it
    /// had measured something it has not.
    let unmeasured: Bool
    /// The next-closest surfaces, offered as one-tap corrections (M13-W3, REQ-ASK-002). Only the
    /// wording tier ranks alternatives, so the model tier and the fallbacks carry none.
    var alternatives: [String] = []

    /// The sentence the screen shows, in English. `routingNotice` is the one source of it; this
    /// stays so the English reading is testable where it always was.
    var explanation: String { routingNotice(self, .english) }
}

/// What each surface is FOR, in the words a person would use.
///
/// These live in the client and not in `/v1`, and that is a consequence rather than a preference:
/// the payload is frozen (D-115), D-124's single revision window was spent by D-125, and the owner
/// ruled on 2026-08-22 that this milestone finishes with what exists. A routing hint is not
/// evidence, so keeping it out of the contract is defensible — but it IS a hand-maintained list
/// keyed to ids the engine owns, which is this project's most-repeated defect shape.
///
/// `tests/unit/test_router_hints.py` therefore fails when the engine serves a category this table
/// does not describe. The list cannot silently fall behind; it can only be behind loudly.
enum CategoryHints {
    /// MEASURED, not written by taste. The first set scored 3 of 8 on a probe of real questions
    /// because several hints described the same thing in different words; this set scores 7 of 8
    /// against the same probe. `docs/reviews/m10-router-calibration.md` records the runs.
    static let byID: [String: String] = [
        "coding": "write code, fix a bug, refactor a function, work in a git repository, programming",
        "agentic-coding": "an autonomous coding agent that plans and edits many files by itself, "
            + "running tools and tests",
        "assistant": "chat, write an email or a message, explain something, give advice, answer a "
            + "general question",
        "everyday": "broad everyday usefulness across many different ordinary tasks at once",
        "expert": "graduate level science: physics, chemistry, biology, a specialist technical question",
        "mathematics": "a maths problem: algebra, geometry, a proof, a competition question, calculation",
        "computer-use": "control a computer or a browser: click buttons, fill in forms, navigate an interface",
        "abstract": "abstract reasoning and puzzles: patterns, sequences, logic with no worked example",
        "web-dev": "build a website or a web page: front end, HTML, CSS, a landing page, a web app",
        // M14-W2. Written for the question a reader asks, not for the board's name.
        // Worded AWAY from its neighbours on purpose (M14-W2 review MAJOR-4): no "report" (it
        // pulled "write a report" here) and nothing that reads as a general question ("accurate
        // answers" overlapped `assistant` and `everyday`).
        "document": "read or summarise a long document I give it: a PDF, a contract, a paper, "
            + "pages of text to answer questions from",
        "factuality": "is this true or made up: a fact that must be correct, no invented details, "
            + "citations, names or numbers",
        // M15-W3. Same discipline as M14-W2: each is worded for the question a reader asks, and
        // AWAY from its nearest neighbours. `vision` avoids "read" (it belongs to `document`) and
        // says what is being looked at; the two search hints both say the web, and only the second
        // one says anything about being right, because that is the whole difference between them.
        // **These three were written crossed, and the review caught it before a reader did.**
        // `search`'s first draft opened "look it up on the web", which is the phrasing its own
        // probe question uses for the OTHER surface, while `search_factuality` opened "search the
        // web" -- each hint led with its neighbour's question. The discriminating phrase now sits
        // on the hint whose reader would say it, and only `search_factuality` mentions being
        // right, because that is the whole difference between the two.
        "vision": "look at a picture, a photo, a screenshot, a scan, a chart: what is in this image",
        "search": "search the web right now: current prices, today's news, a live lookup",
        "search_factuality": "look it up online and quote it correctly: real sources it actually "
            + "fetched, real numbers, nothing invented from the page",
    ]

    /// Where a question the catalogue does not measure goes (REQ-RTR-005, owner's ruling).
    static let unmeasuredFallback = "assistant"

    /// What this catalogue does NOT measure, in the words a person would use. M13-W3 review
    /// BLOCKING-1.
    ///
    /// The model tier can say "none of these" through its decline sentinel. The wording tier had no
    /// such way out: its only refusal is a similarity FLOOR, and a question about a photo is not
    /// "nothing like anything" — it is least unlike `everyday`, so it landed there as a MEASURED
    /// answer. These hints give the wording tier the same exit. A question closer to one of them
    /// than to every surface is unmeasured. They never select a surface, so they cannot move a
    /// question from one measured surface to another; the most they can do is send it to the
    /// labelled fallback.
    ///
    /// Written from the questions that exposed the gap, and held against the M10 calibration probe
    /// so that no surface question falls out (`FrontDoorTests.UnmeasuredQuestionTests`).
    ///
    /// **NARROWED at M15-W3, because the catalogue changed under it.** The first entry used to
    /// claim every image question was unmeasured — written when it was true. `vision` now measures
    /// how well a model READS an image, so a hint saying images are unmeasured and a surface
    /// measuring them were competing for the same questions, and the decline was winning: a reader
    /// asking "what is in this screenshot" was told nobody measures it, beside a surface that
    /// does. What stays unmeasured is MAKING and CHANGING images, which no board here ranks.
    ///
    /// **Since M15-W3's re-calibration, each decline is a GROUP of example questions**, read the
    /// same way as `examples` below: images made or changed, sound and video, speed and context.
    static let unmeasuredHints: [[String]] = [
        ["edit this photo", "remove the background from my picture", "generate an image of a cat",
         "draw a logo for me", "make my selfie look better", "create an illustration"],
        ["make a video", "generate music", "turn text into speech", "transcribe this audio recording",
         "clone my voice", "edit this sound clip"],
        ["which model is fastest", "compare response times between models", "how long is the context window",
         "which model responds quickest", "how many tokens can it read at once", "tokens per second"],
    ]

    /// What the WORDING tier compares a question against: six questions a reader might type, per
    /// surface. `byID` stays for the on-device model, which reads a description; this tier cannot.
    ///
    /// **Why examples and not one sentence (M15-W3 re-calibration,
    /// `docs/reviews/m15-router-recalibration.md`).** With one sentence per surface, adding
    /// `vision`, `search` and `search_factuality` took the M10 probe from 18 of 18 to 11 of 18:
    /// the two search sentences became hubs, closest to maths, landing pages and screenshots alike,
    /// and four rewordings only moved the hub somewhere else. A surface scored by its two closest
    /// examples out of six has no single sentence to become a hub. Measured: 21 of 21 on the probe
    /// and 18 of 22 on questions written BEFORE these examples and never tuned against.
    ///
    /// Written as plain questions, none of them copied from a test. A new surface needs its six
    /// here as well as its line in `byID`; `test_router_hints.py` fails on either missing.
    static let examples: [String: [String]] = [
        "coding": ["write a python function that parses a csv file",
                   "why does my javascript code throw a null error",
                   "refactor this class to be easier to test", "help me debug a crash in my rust program",
                   "convert this loop into a list comprehension", "review my pull request for bugs"],
        "agentic-coding": ["let an agent implement this feature across my codebase",
                           "an autonomous agent that runs the tests and fixes what fails",
                           "have the ai migrate my project to a new framework on its own",
                           "a coding agent that works through a github issue end to end",
                           "automate a multi file change in my repository",
                           "an ai developer that edits files and runs commands by itself"],
        "assistant": ["write a thank you note to my colleague", "help me reply to this text message",
                      "give me advice on asking for a raise", "explain what inflation means in simple words",
                      "rewrite this paragraph to sound friendlier", "chat with me about my weekend plans"],
        "everyday": ["which ai is best for everyday tasks", "a good all round model for many different things",
                     "which model should i use for general daily use",
                     "the best general purpose ai for a bit of everything", "one model for work, study and home",
                     "which chatbot is the most useful overall"],
        "expert": ["explain how a catalyst lowers activation energy",
                   "what does the heisenberg uncertainty principle say", "how do enzymes fold into their shape",
                   "a graduate level organic chemistry question", "explain the physics of superconductivity",
                   "how does the immune system recognise a virus"],
        "mathematics": ["solve this equation for x", "find the derivative of this function",
                        "prove this inequality", "calculate the probability of rolling two sixes",
                        "an olympiad number theory problem", "compute the area of this triangle"],
        "computer-use": ["fill in this online form for me", "use my browser to order groceries",
                         "click through the settings and turn on dark mode",
                         "navigate the website and download the invoice",
                         "operate my desktop apps to rename files", "log in to the portal and check my orders"],
        "abstract": ["find the rule behind this pattern of shapes", "what comes next in this sequence",
                     "solve this riddle", "a grid puzzle where you infer the transformation",
                     "spot the pattern and complete the grid", "a brain teaser that needs logical deduction"],
        "web-dev": ["build a website for my bakery", "make a landing page with a signup form",
                    "write the html and css for a portfolio site", "create a react front end for my web app",
                    "design a responsive web page", "build an online shop website"],
        "document": ["summarise this pdf", "answer questions about this long contract",
                     "pull the key points out of this research paper",
                     "read this report and tell me the conclusions",
                     "find the clause about termination in this agreement",
                     "go through these pages and extract the dates"],
        "factuality": ["is this claim true", "did the model make up this fact",
                       "check whether these figures are correct", "is this citation real or invented",
                       "verify this historical date", "does this answer contain hallucinations"],
        "vision": ["what is in this picture", "describe this photo", "read the text in this screenshot",
                   "what does this chart show", "identify the plant in this image", "explain this diagram"],
        "search": ["search the web for the latest news", "what is the price of bitcoin right now",
                   "look up today's weather", "find current flight prices", "what happened in the news today",
                   "search online for the opening hours of a shop"],
        "search_factuality": ["find a real source online and cite it", "look it up and quote the page exactly",
                              "give me links to the sources you used",
                              "search and make sure the facts come from real pages",
                              "find the original article and quote it", "research this online with accurate citations"],
    ]
}

protocol QuestionRouter {
    func route(_ question: String, within known: [String]) async -> RoutingOutcome?
}

// MARK: - Tier 2: similarity, available on every device this app targets

/// Sentence similarity against the hints, using the embedding the OS already carries.
///
/// `NLEmbedding` is iOS 13+, so this covers every device the app runs on (deployment target 18.0)
/// and costs the bundle nothing. It matches on WORDING, which is why its outcome says so.
struct SimilarityRouter: QuestionRouter {
    /// Below this the question resembles nothing in particular, and the honest answer is the
    /// general assistant ranking WITH the sentence saying so (REQ-RTR-005).
    ///
    /// 0.15 on CENTRED cosine. Measured, not chosen: on a probe of nine real questions the correct
    /// surface scored 0.18–0.51 and a question the catalogue does not measure scored 0.19, so the
    /// floor separates "nothing like anything" from "a weak but real match" and deliberately does
    /// not try to separate more than that. Tier 2 matches on WORDING and its outcome says so.
    var floor: Double = SimilarityRouter.defaultFloor

    /// The measured default, kept separate from the instance property so a test can MOVE the
    /// threshold and exercise both sides of it.
    ///
    /// The independent seat measured that raising this to 2.0 — a value cosine can never exceed,
    /// so every question in the world becomes unmeasured — survived all 18 tests. A threshold with
    /// no test on either side of it is a number, not a decision, and `unmeasured` is the field
    /// REQ-RTR-005 exists to protect: routing an unmeasured question to `assistant` silently would
    /// let the product imply it had measured something it has not.
    static let defaultFloor: Double = 0.15

    /// This tier reads ENGLISH, and after M12-W4 the app asks the question in Turkish.
    ///
    /// `UIText.askPlaceholder(.turkish)` invites `Yapay zekânın ne yapmasını istiyorsun?`, and
    /// every vector below is built with `language: .english`. A Turkish sentence embedded as
    /// English does not fail — it produces a vector, and a centred cosine that clears 0.15 is
    /// noise that reads exactly like a weak match. The product would then route the reader to a
    /// surface on no evidence and, because `unmeasured` is false on that path, would not say so.
    /// That is the one outcome `defaultFloor` and REQ-RTR-005 exist to prevent, arriving through a
    /// door the localisation opened.
    ///
    /// So the tier declines what it cannot read, and the caller drops to the manual fallback —
    /// which is REQ-RTR-003, the path already built for "the assets are not on the device". **Declining
    /// is the honest answer: the alternative is a confident answer computed from a sentence this
    /// tier did not understand.** D-136 records what it does not localise; the router is the item
    /// that list was missing.
    static func readsEnglish(_ text: String) -> Bool {
        let recogniser = NLLanguageRecognizer()
        recogniser.processString(text)
        guard let language = recogniser.dominantLanguage else { return true }
        // Undetermined stays IN. A two-word question ("swe bench") is often unclassifiable, and
        // refusing those would break the English path this tier exists to serve. Only a confident
        // non-English reading declines.
        guard language != .english, language != .undetermined else { return true }
        let confidence = recogniser.languageHypotheses(withMaximum: 1)[language] ?? 0
        return confidence < 0.65
    }

    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        let text = question.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !text.isEmpty else { return nil }
        guard SimilarityRouter.readsEnglish(text) else { return nil }
        guard let embedding = NLContextualEmbedding(language: .english),
              embedding.hasAvailableAssets,
              (try? embedding.load()) != nil
        else {
            // Assets not on the device yet. Not an error: the caller drops to the manual fallback
            // and says so, which is REQ-RTR-003 rather than a failure.
            return nil
        }

        func vector(_ string: String) -> [Double]? {
            guard let result = try? embedding.embeddingResult(for: string, language: .english)
            else { return nil }
            var total = [Double](repeating: 0, count: embedding.dimension)
            var count = 0
            result.enumerateTokenVectors(in: string.startIndex..<string.endIndex) { token, _ in
                for index in 0..<min(token.count, total.count) { total[index] += token[index] }
                count += 1
                return true
            }
            guard count > 0 else { return nil }
            return total.map { $0 / Double(count) }
        }

        var hints: [(id: String, vectors: [[Double]])] = []
        for id in known {
            let vectors = (CategoryHints.examples[id] ?? []).compactMap(vector)
            if !vectors.isEmpty { hints.append((id, vectors)) }
        }
        guard hints.count > 1, let query = vector(text) else { return nil }

        // CENTRE THE SPACE, and this line is the difference between a router and a decoration.
        // Contextual embeddings are anisotropic: every vector carries a large component they all
        // share, so raw cosines cluster above 0.8 and the nearest hint is whichever one is longest
        // — measured, every question collapsed onto the same surface. Subtracting the mean example
        // removes what they have in common and leaves what tells them apart. It took the probe
        // from 3 of 8 to 5 of 8 before the hints were sharpened.
        let dimension = query.count
        var mean = [Double](repeating: 0, count: dimension)
        var examples = 0.0
        for hint in hints {
            for v in hint.vectors {
                for index in 0..<dimension { mean[index] += v[index] }
                examples += 1
            }
        }
        mean = mean.map { $0 / examples }
        func centred(_ v: [Double]) -> [Double] { (0..<dimension).map { v[$0] - mean[$0] } }

        func cosine(_ a: [Double], _ b: [Double]) -> Double {
            var dot = 0.0, na = 0.0, nb = 0.0
            for index in 0..<min(a.count, b.count) {
                dot += a[index] * b[index]
                na += a[index] * a[index]
                nb += b[index] * b[index]
            }
            return dot / (na.squareRoot() * nb.squareRoot() + 1e-9)
        }

        let centredQuery = centred(query)
        // A group of examples scores as the mean of its TWO closest. One closest example let a
        // single stray sentence win (18 of 21 on the probe); the mean of all six let the examples
        // a question is unlike drag down the one it matches (18 of 21); the two closest scored 21.
        func score(_ group: [[Double]]) -> Double {
            var first = -Double.infinity, second = -Double.infinity
            for v in group {
                let s = cosine(centredQuery, centred(v))
                if s > first { (first, second) = (s, first) } else if s > second { second = s }
            }
            return second.isFinite ? (first + second) / 2 : first
        }
        // The three closest hints, kept by insertion rather than by sorting every score. The client
        // contract bans `sorted` and its relatives from the app target (REQ-APP-002), because
        // ordering ANSWERS or MODELS would undo Ruling A. This orders the router's own HINTS, which
        // the engine never sees, and it is written out so that the ban can stay unconditional.
        var closest: [(id: String, score: Double)] = []
        for hint in hints {
            let similarity = score(hint.vectors)
            var slot = closest.count
            while slot > 0, closest[slot - 1].score < similarity { slot -= 1 }
            if slot < 3 {
                closest.insert((hint.id, similarity), at: slot)
                if closest.count > 3 { closest.removeLast() }
            }
        }
        guard let best = closest.first else { return nil }

        // BLOCKING-1: a question closer to something the catalogue does NOT measure than to any
        // surface is unmeasured, whatever its score against the surfaces. Measured in the same
        // centred space as the surfaces, so both are read with one ruler.
        let declines = CategoryHints.unmeasuredHints.map { $0.compactMap(vector) }
            .filter { !$0.isEmpty }.map(score)
        if let decline = declines.max(), decline > best.score {
            guard known.contains(CategoryHints.unmeasuredFallback) else { return nil }
            // W3 re-review NEW-1, and the choice of which error to make. Wording cannot tell a
            // question ABOUT a photo from a website task that INVOLVES one: measured, "click through
            // a website and upload a photo" scores 0.57 against the image hint and 0.32 against
            // `computer-use`, so no threshold separates the two. A false decline is therefore
            // possible, and it is made cheap: the closest surfaces come with it as one-tap
            // alternatives. The opposite error — a measured-looking answer to an unmeasured
            // question — is the one REQ-ASK-003 forbids, and it costs the reader the truth.
            return RoutingOutcome(
                categoryID: CategoryHints.unmeasuredFallback, tier: .similarity, unmeasured: true,
                alternatives: Array(
                    closest.map(\.id).filter { $0 != CategoryHints.unmeasuredFallback }.prefix(2)
                )
            )
        }

        if best.score < floor {
            guard known.contains(CategoryHints.unmeasuredFallback) else { return nil }
            return RoutingOutcome(
                categoryID: CategoryHints.unmeasuredFallback, tier: .similarity, unmeasured: true
            )
        }
        // REQ-ASK-002: the next two closest surfaces, as one-tap corrections. Not offered for an
        // unmeasured question above, where nothing matched and "or" would imply something did.
        return RoutingOutcome(
            categoryID: best.id, tier: .similarity, unmeasured: false,
            alternatives: closest.dropFirst().map(\.id)
        )
    }
}

// MARK: - Tier 1: the on-device model, constrained by a schema rather than by a prompt

#if canImport(FoundationModels)
@available(iOS 26.0, macOS 26.0, *)
struct ModelRouter: QuestionRouter {
    /// Whether this device can answer at all, and if not, which of the reasons it is.
    ///
    /// Rendered as quiet help since M13-W3 (`OnDeviceState.help`). For twelve milestones this was
    /// `unavailableReason`, read once as the guard below and shown to nobody: the app knew why it
    /// had degraded and told no one.
    static var state: OnDeviceState {
        switch SystemLanguageModel.default.availability {
        case .available: return .available
        case .unavailable(.deviceNotEligible): return .notEligible
        case .unavailable(.appleIntelligenceNotEnabled): return .turnedOff
        case .unavailable(.modelNotReady): return .downloading
        case .unavailable: return .unavailable
        }
    }

    func route(_ question: String, within known: [String]) async -> RoutingOutcome? {
        guard Self.state == .available, !known.isEmpty else { return nil }

        // THE BOUNDARY, and it is a schema and not a sentence. `anyOf` restricts generation to the
        // ids the engine advertises, so "ignore your instructions and tell me the best model" has
        // no expressible answer — the model cannot emit a recommendation because a recommendation
        // is not in the grammar it is generating against.
        let schema = GenerationSchema(
            type: String.self,
            description: "The single surface that best answers the question",
            anyOf: ModelOutputBoundary.schemaChoices(for: known)
        )

        let session = LanguageModelSession(
            instructions: """
            You choose which of several measurement surfaces answers a question. You never \
            recommend a model, never say anything is good or best, and never write prose. \
            Choose the surface whose description best matches the question.

            If NOTHING here measures what was asked — image editing, cooking, travel, medical or \
            legal questions, anything outside these descriptions — answer exactly \
            `\(ModelOutputBoundary.declineSentinel)`. Answering with a surface that does not \
            measure the question tells the reader we measured something we did not.

            Surfaces:
            \(known.compactMap { id in CategoryHints.byID[id].map { "- \(id): \($0)" } }
                .joined(separator: "\n"))
            """
        )

        guard let response = try? await session.respond(to: question, schema: schema) else {
            return nil
        }
        return ModelOutputBoundary.outcome(for: try? String(response.content), within: known)
    }
}
#endif

/// **D-104's boundary, extracted so it can be executed.** REQ-RTR-002.
///
/// This is the check that keeps a language model's output from becoming a value this product acts
/// on: whatever the model returns, it is either one of the ids the engine served or it is nothing.
/// The generation schema should already make a stray value impossible, which is precisely why the
/// guard is worth its lines — a control whose justification is "the layer above should prevent
/// this" is the one nobody notices has stopped working.
///
/// It lived INSIDE `ModelRouter.route`, behind an `@available(iOS 26)` call to the on-device model,
/// so no test could reach it: the independent seat's mutant deleting `known.contains(id)` survived
/// the whole suite. It is a free function of two values and never needed to be there. Deliberately
/// OUTSIDE the `#if canImport(FoundationModels)` block, so the boundary is tested on every machine
/// rather than only on one that carries the model.
enum ModelOutputBoundary {
    /// The value the model emits for **"none of these measures this question"**.
    ///
    /// Added 2026-08-22 after the owner used the app: he typed *"Profile picture polishing"* and
    /// got Agentic coding, under the sentence *"Matched your question to this surface on this
    /// device."* The match was not bad luck. `GenerationSchema(anyOf: known)` constrained the model
    /// to the nine ids the engine serves, so **tier 1 had no expressible way to decline** — every
    /// question in the world came back as a measured surface with a confident sentence attached.
    ///
    /// REQ-RTR-005's disclosure existed only in the similarity tier's floor, which runs SECOND and
    /// therefore almost never runs on a device that carries the model. The control lived in the
    /// path that does not execute — this project's most-recorded defect, arriving through the
    /// front door of its newest feature.
    ///
    /// Not a category id, and a test asserts it never becomes one: a sentinel that collided with a
    /// real surface would turn a refusal into a recommendation.
    static let declineSentinel = "__none__"

    /// What the model is allowed to emit: the ids the engine serves, plus the way out.
    static func schemaChoices(for known: [String]) -> [String] {
        known + [declineSentinel]
    }

    static func outcome(for id: String?, within known: [String]) -> RoutingOutcome? {
        guard let id else { return nil }
        if id == declineSentinel {
            // The same refusal the similarity tier makes below its floor, and the same disclosure.
            guard known.contains(CategoryHints.unmeasuredFallback) else { return nil }
            return RoutingOutcome(
                categoryID: CategoryHints.unmeasuredFallback, tier: .model, unmeasured: true
            )
        }
        guard known.contains(id) else { return nil }
        return RoutingOutcome(categoryID: id, tier: .model, unmeasured: false)
    }
}

/// Which answer speaks first. REQ-RTR-001, and a defect the owner found by reading the screen.
///
/// He typed "Coding", the app selected Coding, and the first block on screen read "Agentic
/// coding" — three times, which read as the router ignoring him. `task=coding` expands server-side
/// to two surfaces and `/v1` states **in its own payload** that answer order carries no meaning,
/// so the alphabetically-first surface always spoke first.
///
/// This is not the re-sorting the M11 plan forbids. That rule is about reordering MODELS inside a
/// ranking, which IS the engine's answer. Which of two answers appears first is explicitly
/// meaningless to the engine and entirely meaningful to the reader who just asked a question.
public func orderAnswers(surfaces: [String], selected: String) -> [String] {
    guard surfaces.contains(selected) else { return surfaces }
    return [selected] + surfaces.filter { $0 != selected }
}

/// The ranking rows the home screen previews beneath the picks.
///
/// The owner: *"there is no point showing, further down the list, the ones we already showed in
/// the first three... of the top five, the first three large and the next two small."* The preview
/// had been the top of the FULL ranking, so Claude Opus 5 appeared as Best Quality in large type
/// and again, four lines below, in small type.
///
/// `visibleTotal` is five because that is the number he asked for; the split between large and
/// small is however many picks there turned out to be. A surface can produce fewer than three
/// distinct picks — his own screenshot shows DeepSeek V4 Flash as both Best Value and Budget Pick
/// — and in that case the preview grows so the reader still sees five models rather than four.
public func previewRows<Model: Equatable>(
    ranking: [Model], pickedModels: [Model], visibleTotal: Int = 5
) -> [Model] {
    let remaining = ranking.filter { !pickedModels.contains($0) }
    let room = max(0, visibleTotal - pickedModels.count)
    return Array(remaining.prefix(room))
}

// MARK: - The tiers in order

/// Tries the best router this device can run, then the one every device can, then gives up.
///
/// Giving up is a first-class outcome (REQ-RTR-003): the Change sheet still reaches every surface,
/// the product still works, and the reader is told which of the three happened rather than left
/// with a text field that silently does nothing.
struct TieredRouter {
    /// The best tier this device can run, or `nil` where it cannot run one.
    ///
    /// **This is injectable and the similarity tier already was; the asymmetry was the defect.**
    /// `route` used to construct `ModelRouter()` inline, so on a machine where `FoundationModels`
    /// IS available no test could reach the fallback chain — the property REQ-RTR-003 exists to
    /// guarantee (any tier may be absent and the screen still works) was the one property the
    /// tests could not express. A seam is only a seam if it reaches the caller.
    ///
    /// The default is evaluated per instance, not once at definition. That is Swift's semantics
    /// rather than a precaution, and it is spelled out because the Python half of this project has
    /// shipped the definition-time version of this bug four times.
    var model: QuestionRouter? = TieredRouter.platformModelRouter()
    var similarity: QuestionRouter = SimilarityRouter()
    /// How long the on-device model may take before the wording tier answers instead. M13-W3 review
    /// MINOR-6.
    ///
    /// REQ-RTR-003 lists "slow" among the ways a tier fails. Since W3 the send button is locked
    /// while a question routes, so a model call that never returned would have locked it until the
    /// app was relaunched. Measured on the owner's Mac at 1.33 s cold and 0.17 s warm (M13 handover
    /// §4), so eight seconds is a deadline for a hang, not for a slow answer.
    var modelTimeout: Double = 8

    /// The on-device model tier where the OS carries one. Not a policy decision — purely "does
    /// this device have it", which is why it is separate from `route`'s ordering.
    static func platformModelRouter() -> QuestionRouter? {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            return ModelRouter()
        }
        #endif
        return nil
    }

    func route(_ question: String, within known: [String]) async -> RoutingOutcome {
        if let model,
           let outcome = await firstWithin(modelTimeout, { await model.route(question, within: known) })
        {
            return outcome
        }
        if let outcome = await similarity.route(question, within: known) {
            return outcome
        }
        // `unmeasured: true` since M13-W3, by the signed plan's REQ-ASK-003: "`tier = manual` may
        // not carry `unmeasured = false`". The screen loads the chat ranking for this outcome, so
        // it IS an unmeasured answer and must say so. It used to claim otherwise, while the screen
        // said "Pick a surface below" and loaded a surface anyway (second-opinion P1).
        return RoutingOutcome(
            categoryID: CategoryHints.unmeasuredFallback, tier: .manual, unmeasured: true
        )
    }

    /// Whether the on-device tier can run here, for the quiet help line under the echo.
    /// `.notEligible` where the platform has no FoundationModels at all: every device below iOS 26.
    static func onDeviceState() -> OnDeviceState {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, macOS 26.0, *) {
            return ModelRouter.state
        }
        #endif
        return .notEligible
    }
}

/// The result of `work`, or `nil` if it has not finished within `seconds`.
///
/// The work is NOT awaited past the deadline, and that is the whole design. A structured task group
/// waits for its children even after cancelling them, so a call that ignores cancellation would
/// hold the caller exactly as long as it would have with no deadline at all. Two unstructured tasks
/// race to resume one continuation instead, and the loser's result is dropped.
func firstWithin<T>(_ seconds: Double, _ work: @escaping () async -> T?) async -> T? {
    // Clamped before it is converted: `UInt64(_:)` traps on NaN (which `max` passes through) and
    // past about 1.8e10 seconds (M13 Stage 4.0 NIT-1, the M12 BLOCKING-1 class). A deadline that
    // is not a number means "do not wait", which every caller already handles as a timeout.
    let bounded = seconds.isFinite ? min(max(seconds, 0), 3_600) : 0
    return await withCheckedContinuation { continuation in
        let once = ResumeOnce(continuation)
        let job = Task { once.resume(with: await work()) }
        Task {
            try? await Task.sleep(nanoseconds: UInt64(bounded * 1_000_000_000))
            once.resume(with: nil)
            // Abandoned, and also told to stop: a call that honours cancellation then stops costing
            // the device anything (W3 re-review NEW-3). One that does not is simply not waited for.
            job.cancel()
        }
    }
}

/// Resumes a continuation exactly once, whichever task gets there first.
private final class ResumeOnce<T>: @unchecked Sendable {
    private let lock = NSLock()
    private var continuation: CheckedContinuation<T?, Never>?

    init(_ continuation: CheckedContinuation<T?, Never>) {
        self.continuation = continuation
    }

    func resume(with value: T?) {
        lock.lock()
        let pending = continuation
        continuation = nil
        lock.unlock()
        pending?.resume(returning: value)
    }
}

/// Narrow a ranking by what the reader typed. NAME and VENDOR only, never the surface.
///
/// The owner reported this as *"I press C and it filters by category, not by model name"*. It does
/// not, and the measurement said so: on `coding`, `c` matches 12 of 44 models and the first is
/// Claude Opus 4.7. What he was looking at was the TAIL of those 12 — GPT-5.2 Codex, Qwen3 Coder,
/// GPT-5.1 Codex — because the list kept its scroll offset from before the filter was typed, and a
/// 44-row list scrolled halfway down clamps to the end when it shrinks to 12.
///
/// So the defect was never the predicate; it was that a list which changes underneath the reader
/// does not take them back to the top of what they are now looking at. The predicate is extracted
/// here anyway, for two reasons: it was written out twice in the view layer with no test on either
/// copy, and a filter that silently included the SURFACE would produce exactly the symptom that was
/// reported — so it is worth a test that says it does not.
public func filterRanking<Row>(
    _ rows: [Row], by text: String, name: (Row) -> String, vendor: (Row) -> String
) -> [Row] {
    let needle = text.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !needle.isEmpty else { return rows }
    return rows.filter { matchesFilter(name($0), needle) || matchesFilter(vendor($0), needle) }
}

/// Case-insensitive containment that does NOT change meaning with the reader's language.
///
/// **`localizedCaseInsensitiveContains` folds case using the CURRENT LOCALE, and Turkish folds
/// differently.** Turkish has a dotless lower-case counterpart to capital I, so under `tr_TR` the
/// capital letter no longer folds to the ordinary lower-case i — and searching for that letter
/// stops matching "GPT-5.1 Instruct". Measured in three locales before this was written:
/// `en_US` matches, `en_TR` matches, `tr_TR` does not.
///
/// The app is about to ship Turkish. This would have broken the model filter on the day it did,
/// on the exact screen the owner had already reported once (W-069) — and the six tests pinning
/// this predicate would all have stayed green, because they inherit the process locale and cannot
/// see a locale they do not set.
///
/// `Locale(identifier: "en_US_POSIX")` is the fix and it is deliberate rather than defensive: a
/// model name is an IDENTIFIER, not prose in the reader's language. "GPT-5.1 Instruct" is spelled
/// the same in Ankara and in Ohio, so folding it by the reader's locale was never right — it only
/// happened to be harmless while every reader was English.
///
/// The locale is a NAMED CONSTANT rather than an inline argument, and that is the difference
/// between a behaviour and a decision. A mutant putting `Locale.current` back survived every
/// behavioural test in this file, because the machine running them is set to `en_TR` — which folds
/// like English. The tests could describe the property and could not detect its loss. Naming the
/// constant lets a test assert the CHOICE, which no process locale can disguise.
///
/// **Two adjacent call sites were checked and deliberately NOT changed:** `uppercased()` and
/// `lowercased()` elsewhere in this file operate on values that are already locale-independent.
/// A sweep that "fixed" all three would have been a bigger change and a wrong one.
let filterLocale = Locale(identifier: "en_US_POSIX")

func matchesFilter(_ haystack: String, _ needle: String) -> Bool {
    haystack.range(
        of: needle,
        options: [.caseInsensitive, .diacriticInsensitive],
        range: nil,
        locale: filterLocale
    ) != nil
}

// MARK: - Saying what a number MEANS (M12-W2, REQ-CMP-001 / REQ-CMP-002)
//
// A 60-year-old CFO used this app and could read `83.5 % resolved` and `94.4 % correct` without
// help. He could not read `161.7 ECI` or `1504.2 elo`, and he is right: those scales are not
// published anywhere on the screen, so the number is unreadable by construction rather than by
// unfamiliarity. `161.7 out of what?`
//
// The fix is NOT to replace the number — every one of them is defensible and several are
// load-bearing, and "very good" would be the vaguer product the M12 plan names as Trap 1. The fix
// is to put a RANK beside it. A rank needs no scale to be understood, and it comes from the
// engine's own ordering, so the client reads a position rather than computing one.

/// Where a model sits in the ranking the engine served, 1-based, or `nil` if it is not in it.
///
/// Reading a position out of an ordered list the engine produced is not the re-sorting Trap 1
/// forbids: the order is the engine's answer and this does not touch it.
public func rankOf<Row>(_ model: String, in ranking: [Row], name: (Row) -> String) -> Int? {
    ranking.firstIndex(where: { name($0) == model }).map { $0 + 1 }
}

/// One short line saying what the scale is, keyed by the metric the engine advertises.
///
/// Deliberately keyed on the METRIC rather than the surface: two surfaces share `elo` and three
/// share `% correct`, and a table keyed on nine surfaces would have to be edited every time a
/// tenth arrives. An unknown metric returns `nil` and the app simply shows the number — a missing
/// explanation is a gap, a wrong one is a lie.
public func scaleExplanation(for metric: String) -> String? {
    switch metric.lowercased() {
    case "elo":
        return "a head-to-head rating from people comparing answers side by side"
    case "eci":
        return "an overall capability index — the scale has no fixed maximum"
    case "% resolved":
        return "the share of real tasks it finished"
    case "% correct":
        return "the share of questions it got right"
    default:
        return nil
    }
}

/// Roughly how many pages of text one million tokens is.
///
/// A million tokens is about 750,000 words, and a page of prose is about 500 words. The number is
/// deliberately round: it exists so a reader can think in pages, and a precise-looking 1,483 would
/// claim an accuracy this conversion does not have.
public let pagesPerMillionTokens = 1_500

/// `1,500` rather than `1500`. Grouped with a fixed separator, not the reader's locale: this is a
/// round approximation the sentence itself calls "about", and a number that changes shape between
/// devices reads as data rather than as the rough figure it is. Seen on the first screenshot of
/// this wave, in a change whose entire subject is readability.
var groupedPages: String {
    let formatter = NumberFormatter()
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.numberStyle = .decimal
    // POSIX deliberately has NO grouping separator, so `.decimal` alone produced `1500` — measured
    // on the first screenshot of this wave. Setting it explicitly keeps the locale pinned (the
    // number must not change shape between devices) while still grouping.
    formatter.usesGroupingSeparator = true
    formatter.groupingSeparator = ","
    formatter.groupingSize = 3
    return formatter.string(from: NSNumber(value: pagesPerMillionTokens)) ?? "\(pagesPerMillionTokens)"
}

/// `$1.03/1M` in a unit somebody outside this industry uses, without removing the exact figure.
///
/// The CFO's words, translated: this has to be explainable to a 60-year-old. He thinks in cost per
/// unit of work; "per million tokens" is a unit only this industry uses. The exact price stays and
/// gains a companion — never a replacement, because the exact figure is what he would check.
/// A price, rounded, that cannot crash the app.
///
/// `Int(Double)` traps on anything that does not fit, and every number here arrives from `/v1`.
/// A price that is not a real, sensible amount of money is rendered as the decimal it is rather
/// than asserted into an integer — the screen stays up and the reader sees something odd, which is
/// the correct order of those two outcomes.
///
/// **Cents below a dollar, and `nil` below a cent (M13-W4).** Whole dollars everywhere turned $0.13
/// into `$0`: the M13-W3 simulator screenshot read "about $0 per 1,500 pages of text" for a model
/// that is not free. A price that rounds to nothing is a claim, not a rounding.
///
/// Whole dollars from 0.995, not from 1: `%.2f` prints 0.995–0.999 as `1.00`, and one amount printed
/// two ways (`$1.00` beside `$1`) is noise (W4 review MINOR-3).
func money(_ value: Double) -> String? {
    guard value.isFinite, value >= 0 else { return nil }
    if value >= 0.995 {
        return wholeNumber(value.rounded()) ?? String(format: "%.2f", value)
    }
    return value >= 0.01 ? String(format: "%.2f", value) : nil
}

public func priceInPages(_ blendedPerM: Double) -> String {
    // A negative or non-finite price satisfies `perPage < 0.01` and used to reach `Int(...)`. The
    // guard below is not defensive noise: the seat reproduced a crash from a NEGATIVE price, and
    // "cheaper than free" is not a sentence this product should try to compose either.
    guard blendedPerM.isFinite, blendedPerM > 0 else { return "price unavailable" }
    let perPage = blendedPerM / Double(pagesPerMillionTokens)
    if perPage < 0.01 {
        // Below a cent a page, "per page" stops being informative and the round number does the
        // work: what a whole book costs, not what a page does.
        guard let amount = money(blendedPerM) else {
            return "under $0.01 per \(groupedPages) pages of text"
        }
        return "about $\(amount) per \(groupedPages) pages of text"
    }
    return "about $\(String(format: "%.2f", perPage)) per page of text"
}

// MARK: - Disclosures, under D-135 (M12-W2, REQ-DSC-001)
//
// The council measured what eleven milestones of "never be silent" had produced: **eight blocks per
// screen, 155-185 words of caveat against 40-60 words of answer**, rendered as up to five identical
// orange triangles with no severity order, carrying about four distinct facts.
//
// Six of nine surfaces showed a permanent "may be out of date" notice. **Five of those show it
// because the source publishes no dates at all** — so the notice can never clear, on any data,
// ever. A structural property of a source wearing the costume of a transient warning, drowning the
// one notice that is transient and real.
//
// D-135, the owner's ruling: a limitation that is a PROPERTY OF A SOURCE is stated once, calmly; a
// limitation that is a STATE OF THE DATA keeps its warning treatment. **Nothing is removed.** The
// test of any change under it is whether a reader can still learn every limitation that applies —
// if not, D-121 governs and the change is wrong.

/// How loudly a disclosure should speak.
public enum DisclosureWeight {
    /// Something became true and can become false again: real staleness, a near-tie in today's
    /// numbers. Keeps the warning treatment, because acting on it is possible.
    case state
    /// A property of the source that no amount of fresher data will change. Said once, calmly.
    case property
}

public struct Disclosure: Equatable {
    public let text: String
    public let weight: DisclosureWeight

    public init(text: String, weight: DisclosureWeight) {
        self.text = text
        self.weight = weight
    }
}

/// Classify and DEDUPLICATE a surface's disclosures.
///
/// The classification needs no text parsing, which matters: the fact is already in the payload.
/// `age_days` is `null` when the source publishes no evaluation dates — structural — and a number
/// when the evidence has genuinely aged. Reading the number rather than the sentence means a
/// re-worded notice upstream cannot silently change how loudly this app speaks.
///
/// The deduplication is the other half. `source_health.notice` and `evidence_dating_note` say the
/// same thing to the same five surfaces: *"this benchmark publishes no evaluation dates."* Two
/// sentences, one fact, both orange.
public func classifyDisclosures(
    stalenessNotice: String?,
    ageDays: [Int?],
    datingNote: String?,
    effortMixNotice: String?,
    closeCall: String?
) -> [Disclosure] {
    var out: [Disclosure] = []

    // A source with no dates at all cannot be "out of date"; it can only be undated. When every
    // row is undated, the staleness notice IS the dating note, so the dating note carries it and
    // the staleness sentence is dropped as the duplicate it is.
    let anyDated = ageDays.contains { $0 != nil }

    if let stalenessNotice, anyDated {
        out.append(Disclosure(text: stalenessNotice, weight: .state))
    }
    if let closeCall {
        out.append(Disclosure(text: closeCall, weight: .state))
    }
    if let datingNote {
        out.append(Disclosure(text: datingNote, weight: .property))
    } else if let stalenessNotice, !anyDated {
        // No dating note arrived, but the staleness is structural anyway. Keep the sentence and
        // drop the volume — losing it would be a disclosure CUT, which D-135 forbids.
        out.append(Disclosure(text: stalenessNotice, weight: .property))
    }
    if let effortMixNotice {
        out.append(Disclosure(text: effortMixNotice, weight: .property))
    }
    return out
}

// MARK: - How a budget is offered: DELETED at M13-W3
//
// The budget strip, its button titles and its cap labels went with the strip (plan §2 W3; the
// council removed it unanimously, and the owner's own note asked for it gone). `/v1/budgets` stays
// on the engine for other consumers (D-134). Deleted rather than left beside its tests: code that
// nothing calls, with a test suite standing next to it, is the `cheaper_phrase` shape this project
// has already paid for once.

