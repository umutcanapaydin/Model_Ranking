//  REQ-IOS-001 — the client's failure vocabulary and its one security control, executed.
//
//  `EngineClient` decides what the reader is TOLD when something goes wrong, and every branch of
//  that decision shipped unexecuted. Two of them matter more than the rest:
//
//  * `SameHostOnly` is the app's only network security control. It refuses a redirect that leaves
//    the engine's host — a `302 Location:` is otherwise followed up to twenty times by
//    `URLSession`, which would send the app's next request wherever a response told it to.
//  * the error vocabulary distinguishes "not running" from "did not answer in time" from "refused
//    because it is not encrypted". Collapsing them sends a developer to restart a healthy server,
//    and the shortest path out of that wrong diagnosis is `NSAllowsArbitraryLoads`.
//
//  The redirect delegate is tested DIRECTLY rather than through a live server. That is deliberate:
//  a test that needs a listening socket to prove a security control is a test that gets disabled
//  the first time CI has no network.

import XCTest

@testable import ModelRankingEngine

final class SameHostOnlyTests: OfflineTestCase {
    private func redirect(from host: String, to target: String) async -> URLRequest? {
        let delegate = SameHostOnly(host: host)
        let response = HTTPURLResponse(
            url: URL(string: "http://\(host)/v1/categories")!,
            statusCode: 302, httpVersion: nil, headerFields: ["Location": target]
        )!
        return await withCheckedContinuation { continuation in
            delegate.urlSession(
                URLSession.shared,
                task: URLSession.shared.dataTask(with: URL(string: "http://\(host)/")!),
                willPerformHTTPRedirection: response,
                newRequest: URLRequest(url: URL(string: target)!),
                completionHandler: { continuation.resume(returning: $0) }
            )
        }
    }

    func testARedirectToAnotherHostIsRefused() async {
        let followed = await redirect(from: "127.0.0.1", to: "https://evil.example.com/v1/categories")

        XCTAssertNil(followed, "the app followed a redirect off the engine's host")
    }

    func testARedirectOnTheSameHostIsFollowed() async {
        // The pairing, so the control cannot be "refuse everything" — that would break an engine
        // that answers a trailing slash or a version prefix with a 302, for no security gain.
        let followed = await redirect(from: "127.0.0.1", to: "http://127.0.0.1/v1/categories/")

        XCTAssertNotNil(followed, "a same-host redirect was refused; a deploy would break for nothing")
    }

    func testTheHostIsComparedWithoutCase() async {
        // W1 second review K3 (REQ-DEV-001): DNS names are not case-sensitive, the owner's address is written
        // mixed-case, and URLSession sends the host lower-cased.
        let followed = await redirect(from: "My-Mac.local", to: "http://my-mac.local/v1/categories/")

        XCTAssertNotNil(followed, "a same-host redirect was refused for the case of its letters")
    }

    func testALookalikeHostIsNotTreatedAsTheSameHost() async {
        let followed = await redirect(from: "127.0.0.1", to: "http://127.0.0.1.evil.example.com/v1")

        XCTAssertNil(followed, "a suffix match let `127.0.0.1.evil.example.com` pass as the engine")
    }

    func testAHostThatMERELYENDSWithTheEngineHostIsRefused() async {
        // The case the test above does NOT cover, and the reason it matters: the seat measured
        // that rewriting the equality check as `hasSuffix` survived every test in this file. The
        // attack `hasSuffix` opens is a host with a PREFIX glued on, not a suffix — which is the
        // shape a real deployment meets first, since D-116 puts the engine on a named host.
        let followed = await redirect(from: "engine.example.com",
                                      to: "https://evil-engine.example.com/v1/categories")

        XCTAssertNil(followed, "`evil-engine.example.com` was accepted as `engine.example.com`")
    }

    func testARedirectWithNoHostAtAllIsRefused() async {
        // `request.url?.host` is optional on both sides. Two nils comparing equal would make a
        // hostless URL match a hostless baseURL, and the guard would pass on nothing at all.
        let followed = await redirect(from: "127.0.0.1", to: "file:///etc/passwd")

        XCTAssertNil(followed, "a redirect with no host was followed")
    }
}

final class EngineErrorVocabularyTests: OfflineTestCase {

    /// Every case must say something DIFFERENT, because the whole reason they are separate cases
    /// is that they need different advice. A blanket sentence is the M8 plan's Trap 2.
    func testEveryFailureModeSaysSomethingDifferent() {
        let cases: [EngineError] = [
            .unreachable("connection refused"),
            .timedOut(seconds: 10),
            .insecureTransport,
            .offline,
            .refused(status: 503, code: "artifact_unbuilt", message: "The evidence database is not built."),
            .undecodable("missing key `answers`"),
        ]

        let sentences = cases.compactMap(\.errorDescription)

        XCTAssertEqual(sentences.count, cases.count, "a failure mode has no sentence at all")
        XCTAssertEqual(Set(sentences).count, cases.count,
                       "two failure modes tell the reader the same thing: \(sentences)")
    }

    func testTheEnginesOwnWordsSurviveARefusal() {
        // D-121 / the 503 branch: the engine distinguishes an unbuilt artifact from an unknown
        // task, and the client flattening that would discard the distinction it was built to make.
        let error = EngineError.refused(
            status: 503, code: "artifact_unbuilt",
            message: "The evidence database has no price medians."
        )

        XCTAssertEqual(error.errorDescription, "The evidence database has no price medians.")
    }

    func testTimedOutNamesTheNumberOfSecondsRatherThanBeingVague() {
        guard let sentence = EngineError.timedOut(seconds: 10).errorDescription else {
            return XCTFail("no sentence")
        }
        XCTAssertTrue(sentence.contains("10"), "the timeout does not say how long it waited: \(sentence)")
    }

    func testUnreachableNamesTheRemedy_toTheAUDIENCEThatCanActOnIt() {
        // Written at M11 asserting `recovery` contained "make run". At M12-W2 that became wrong
        // for the right reason: an end user does not own a repository, so the developer remedy
        // moved to `diagnostic`. The INTENT is unchanged and is asserted on both halves — the
        // remedy is still named, and the reader is no longer the one being told to run it.
        let error = EngineError.unreachable("connection refused")

        XCTAssertTrue((error.diagnostic ?? "").contains("make run"),
                      "the developer remedy is not named anywhere: \(error.diagnostic ?? "nil")")
        XCTAssertFalse((error.recovery ?? "").contains("make run"),
                       "the person holding the phone is still being told to run a build command")
    }
}

final class PayloadDecodingTests: OfflineTestCase {

    /// A payload the app cannot read must become `undecodable` — NOT an empty screen. Rendering a
    /// contract mismatch as "no results" is how a broken `/v1` looks exactly like a correct answer
    /// of zero picks.
    func testAMalformedPayloadDoesNotDecodeIntoAnEmptyAnswer() {
        let truncated = Data(#"{"categories": [{"id": "coding"}]}"#.utf8)

        XCTAssertThrowsError(try JSONDecoder().decode(CategoryList.self, from: truncated),
                             "a category list missing required fields decoded into something")
    }

    func testAWellFormedCategoryListDecodes() throws {
        // Fixture blindness: without this, the test above would pass if `CategoryList` were
        // undecodable from anything at all.
        //
        // This payload is COPIED from what `/v1/categories` actually returns, not written from
        // the Swift struct (V3C-44). The first draft of it was written from the struct, invented
        // two fields the engine has never sent, and omitted one it always does — which is the
        // "typed out from an imagined payload" defect `Models.swift` opens by warning about.
        let payload = Data(#"""
        {"categories": [{"id": "coding", "title": "Coding",
          "primary_benchmark": "SWE-bench Verified", "metric": "% resolved",
          "ranking_effort": null}]}
        """#.utf8)

        let list = try JSONDecoder().decode(CategoryList.self, from: payload)

        XCTAssertEqual(list.categories.first?.id, "coding")
        XCTAssertNil(list.categories.first?.rankingEffort, "an absent effort must stay absent")
    }

    /// M20-W1 (D-188 clause 1; the W1 review's M5): a surface's family decodes, primary first, and an
    /// engine older than M20 that sends none leaves it absent.
    func testTheFamilyDecodesAndIsAbsentFromAnOlderEngine() throws {
        let payload = Data(#"""
        {"categories": [{"id": "coding", "title": "Coding", "primary_benchmark": "SWE-bench Verified",
          "metric": "% resolved", "ranking_effort": null, "primary_board": "swebench",
          "boards": ["swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"]},
         {"id": "vision", "title": "Vision", "primary_benchmark": "Arena vision", "metric": "elo",
          "ranking_effort": null, "primary_board": "arena_vision"}]}
        """#.utf8)
        let list = try JSONDecoder().decode(CategoryList.self, from: payload)
        XCTAssertEqual(list.categories.first?.boards, ["swebench", "epoch_swe_bench_verified", "aider", "arena_text_coding"])
        XCTAssertNil(list.categories.last?.boards)
    }

    /// M16-W2 (D-152, D-153): the two W1 fields reach the client. COPIED from `/v1/categories` on
    /// 2026-09-23 (V3C-44), one surface that carries a price exclusion and one that does not.
    func testTheFloorAndThePriceExclusionDecode() throws {
        let payload = Data(#"""
        {"categories": [{"id": "expert", "title": "Hard science questions",
          "primary_benchmark": "GPQA Diamond", "metric": "% correct", "ranking_effort": null,
          "close_call_margin": 5.0, "score_anchor": null, "min_quality": 83.6,
          "price_excludes": null, "secondary_benchmark": null, "secondary_age_days": null},
         {"id": "search", "title": "Answering with a web search",
          "primary_benchmark": "Arena search", "metric": "elo", "ranking_effort": null,
          "close_call_margin": 6.5, "score_anchor": 1206.9, "min_quality": 1206.9,
          "price_excludes": "search_call", "secondary_benchmark": null,
          "secondary_age_days": null}]}
        """#.utf8)

        let list = try JSONDecoder().decode(CategoryList.self, from: payload)

        XCTAssertEqual(list.categories.map(\.minQuality), [83.6, 1206.9])
        XCTAssertEqual(list.categories.map(\.priceExcludes), [nil, "search_call"])
    }
}

// MARK: - Remediation of the M11-W2 independent review
//
// The seat's measurement: `EngineClient` line coverage 27.05%, `Models` 0.00%. The tests above
// exercise the SENTENCES the client can say and never the DECISION that picks one — so collapsing
// the whole `URLError` switch into a single `unreachable`, and discarding the engine's own 503
// body, both survived. A test on an error's `errorDescription` is a test of a string table.

/// Drives `EngineClient.get` against a URLProtocol stub, so the mapping from a real transport
/// condition to an `EngineError` is executed rather than assumed.
private final class StubProtocol: URLProtocol, @unchecked Sendable {
    /// What the next request should do. A URLProtocol is instantiated by the loading system, so
    /// there is nowhere but a static to put this.
    nonisolated(unsafe) static var outcome: Result<(Int, Data), URLError> = .success((200, Data()))

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func stopLoading() {}

    /// The URL the last request actually asked for. The point of the budget picker is that the
    /// CHOICE reaches the engine, and a picker that changes a `@State` and sends the old value
    /// would look identical on screen until somebody compared two answers.
    nonisolated(unsafe) static var lastRequestedURL: URL?
    /// The whole last request, for the headers (M17-W4 review M4).
    nonisolated(unsafe) static var lastRequest: URLRequest?

    override func startLoading() {
        Self.lastRequestedURL = request.url
        Self.lastRequest = request
        switch Self.outcome {
        case let .failure(error):
            client?.urlProtocol(self, didFailWithError: error)
        case let .success((status, body)):
            let response = HTTPURLResponse(
                url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: body)
            client?.urlProtocolDidFinishLoading(self)
        }
    }
}

final class EngineClientDecisionTests: OfflineTestCase {
    private func client() -> EngineClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubProtocol.self]
        return EngineClient(
            baseURL: URL(string: "http://127.0.0.1:8080")!,
            session: URLSession(configuration: configuration)
        )
    }

    private func categoriesError() async -> EngineError? {
        do {
            _ = try await client().categories()
            return nil
        } catch let error as EngineError {
            return error
        } catch {
            return nil
        }
    }

    func testATimeoutIsNotReportedAsAnUnreachableEngine() async {
        // "Start the engine" is wrong advice for an engine that accepted the connection.
        StubProtocol.outcome = .failure(URLError(.timedOut))

        guard case .timedOut = await categoriesError() else {
            return XCTFail("a timeout was mapped to something else; the URLError switch is collapsing")
        }
    }

    func testACleartextRefusalIsNotReportedAsAnUnreachableEngine() async {
        // The one moment App Transport Security fires. Misreporting it sends a developer to
        // NSAllowsArbitraryLoads, which would ship this product's first network call in the clear.
        StubProtocol.outcome = .failure(URLError(.appTransportSecurityRequiresSecureConnection))

        let error = await categoriesError()
        XCTAssertEqual(error, .insecureTransport)
    }

    func testNoNetworkIsNotReportedAsAnUnreachableEngine() async {
        StubProtocol.outcome = .failure(URLError(.notConnectedToInternet))

        let error = await categoriesError()
        XCTAssertEqual(error, .offline)
    }

    func testAnUnmappedTransportFailureFallsBackToUnreachable() async {
        // The default arm, so the switch cannot become "everything is a special case".
        StubProtocol.outcome = .failure(URLError(.cannotConnectToHost))

        guard case .unreachable = await categoriesError() else {
            return XCTFail("an ordinary connection failure stopped being `unreachable`")
        }
    }

    func testAnUnreachableEngineNamesTheAddressItTried() async {
        // W1 review M4 (REQ-DEV-001): a mistyped override falls back to loopback, and on a phone the only sign of it
        // would be this detail.
        StubProtocol.outcome = .failure(URLError(.cannotConnectToHost))

        guard case let .unreachable(detail) = await categoriesError() else {
            return XCTFail("an ordinary connection failure stopped being `unreachable`")
        }
        XCTAssertTrue(detail.contains("http://127.0.0.1:8080"), detail)
    }

    func testTheEnginesOwnRefusalBodyIsCarriedThroughRatherThanReplaced() async {
        // D-121: the engine distinguishes an unbuilt artifact from an unknown task. Flattening
        // that here discards the distinction it was built to make.
        let body = Data(
            #"{"error": {"code": "evidence_unavailable", "message": "The evidence database is not available."}}"#.utf8
        )
        StubProtocol.outcome = .success((503, body))

        guard case let .refused(status, code, message) = await categoriesError() else {
            return XCTFail("a 503 with an engine error body did not become `refused`")
        }
        XCTAssertEqual(status, 503)
        XCTAssertEqual(code, "evidence_unavailable")
        XCTAssertEqual(message, "The evidence database is not available.")
    }

    func testAnUnreadableBodyBecomesUndecodableRatherThanAnEmptyScreen() async {
        // A contract mismatch rendered as "no results" is how a broken /v1 looks exactly like a
        // correct answer of zero. Under D-124 this is a finding against /v1 first.
        StubProtocol.outcome = .success((200, Data(#"{"not_categories": []}"#.utf8)))

        guard case .undecodable = await categoriesError() else {
            return XCTFail("a payload this app cannot read did not become `undecodable`")
        }
    }

    func testAWellFormedAnswerIsReturnedRatherThanThrown() async throws {
        // Fixture blindness: without this, every test above could pass because the stub breaks
        // everything.
        let body = Data(#"""
        {"categories": [{"id": "coding", "title": "Coding",
          "primary_benchmark": "SWE-bench Verified", "metric": "% resolved",
          "ranking_effort": null}]}
        """#.utf8)
        StubProtocol.outcome = .success((200, body))

        let categories = try await self.client().categories()

        XCTAssertEqual(categories.map { $0.id }, ["coding"])
    }
}

// MARK: - M12-W2 — what the person holding the phone is told

final class UserFacingMessageTests: OfflineTestCase {

    private let all: [EngineError] = [
        .unreachable("Could not connect to the server."),
        .timedOut(seconds: 10),
        .insecureTransport,
        .offline,
        .refused(status: 503, code: "evidence_unavailable", message: "The evidence is not available."),
        .undecodable("missing key `answers`"),
    ]

    /// **The strings a reader sees must not contain a developer's world.**
    ///
    /// For eleven milestones this app told an end user to *"start it with `make run` in the engine
    /// repository"* and explained `NSAllowsArbitraryLoads` to them. That was correct while the only
    /// reader was the person who built it, and stopped being correct the week a 60-year-old CFO
    /// opened the app.
    func testNoUserFacingSentenceAssumesTheReaderOwnsTheSystem() {
        let developerWorld = [
            "make run", "repository", "nsallowsarbitraryloads", "/v1", "contract", "artifact",
            "http", "localhost", "127.0.0.1", "endpoint", "payload", "json",
        ]

        for error in all {
            let text = ((error.errorDescription ?? "") + " " + (error.recovery ?? "")).lowercased()
            for term in developerWorld {
                XCTAssertFalse(text.contains(term),
                               "a reader is shown `\(term)` in: \(text)")
            }
        }
    }

    func testEveryFailureStillTellsThemSomethingTheyCanDoOrThatNothingCanBeDone() {
        for error in all {
            let recovery = error.recovery
            if case .refused = error {
                XCTAssertNil(recovery, "the engine's own message is the recovery; do not say it twice")
                continue
            }
            XCTAssertNotNil(recovery, "\(error) leaves the reader with nothing")
            XCTAssertFalse(recovery!.isEmpty)
        }
    }

    /// **The detail is moved, not deleted**, and this is the test that stops the next person
    /// deleting it. The `unreachable` detail is what tells whoever is debugging that this was a
    /// refused connection rather than a DNS failure.
    func testTheDeveloperDetailSurvivesWhereItIsNeeded() {
        guard let diagnostic = EngineError.unreachable("Could not connect to the server.").diagnostic
        else {
            return XCTFail("the transport detail was dropped rather than moved")
        }

        XCTAssertTrue(diagnostic.contains("Could not connect to the server."))
        XCTAssertTrue(diagnostic.contains("make run"), "the developer remedy went missing entirely")
    }

    func testTheCleartextWarningSurvivesForWhoeverWouldOtherwiseDisableIt() {
        // This one exists to head off a one-line "fix" that would ship the product's first network
        // call in the clear. It must not be lost just because a reader should not see it.
        let diagnostic = EngineError.insecureTransport.diagnostic ?? ""

        XCTAssertTrue(diagnostic.contains("NSAllowsArbitraryLoads"))
    }

    func testAFailureWithNothingExtraToSayDoesNotInventADiagnostic() {
        XCTAssertNil(EngineError.offline.diagnostic)
        XCTAssertNil(EngineError.timedOut(seconds: 10).diagnostic)
    }
}

// MARK: - M12-W3 — the chosen budget reaches the engine

final class BudgetIsSentTests: OfflineTestCase {
    private func client() -> EngineClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubProtocol.self]
        return EngineClient(
            baseURL: URL(string: "http://127.0.0.1:8080")!,
            session: URLSession(configuration: configuration)
        )
    }

    private func query(task: String, budget: String) async -> [String: String] {
        StubProtocol.lastRequestedURL = nil
        StubProtocol.outcome = .success((200, Data(#"{"not_a_recommendation": true}"#.utf8)))
        _ = try? await client().recommendation(task: task, budget: budget)
        guard let url = StubProtocol.lastRequestedURL,
              let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems
        else { return [:] }
        return Dictionary(uniqueKeysWithValues: items.map { ($0.name, $0.value ?? "") })
    }

    /// The budget the caller passes is the one the engine is asked for. Written for REQ-BGT-001's
    /// picker (M12-W3), which the signed m13-plan §2 W3 retired: the app now asks at `unlimited`,
    /// but `EngineClient` still takes a budget, and must never send a different one.
    func testTheBudgetTheReaderChoseIsWhatTheEngineIsAsked() async {
        for budget in ["low", "medium", "unlimited"] {
            let sent = await query(task: "coding", budget: budget)

            XCTAssertEqual(sent["budget"], budget,
                           "the engine was asked for `\(sent["budget"] ?? "nothing")`")
        }
    }

    func testTheSurfaceAndTheBudgetAreBothSentAndNothingElseIs() async {
        let sent = await query(task: "everyday", budget: "low")

        XCTAssertEqual(sent, ["task": "everyday", "budget": "low"],
                       "the request carries something other than the two things it should")
    }

    func testNothingTheReaderTypedIsEverSent() async {
        // REQ-RTR-004, re-asserted here because the budget picker is the first new control to
        // touch this request since the router was built. D-104's boundary is that the typed
        // question never crosses the network.
        let sent = await query(task: "coding", budget: "low")

        XCTAssertNil(sent["question"])
        XCTAssertNil(sent["q"])
    }
}


/// M17-W4 (D-167): the standings are fetched whatever the question is, so the request carries
/// nothing -- no query, no path beyond the route -- and the bytes the engine sent are kept whole.
final class BoardsRequestTests: OfflineTestCase {
    private func client() -> EngineClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubProtocol.self]
        return EngineClient(
            baseURL: URL(string: "http://127.0.0.1:8080")!,
            session: URLSession(configuration: configuration)
        )
    }

    private let payload = Data(#"""
        {"api_version":"v1","attributions":["a"],"boards":[{"id":"epoch_chess","benchmark":"Chess puzzles",\#
        "metric":"% correct","ranking_effort":null,"evidence_date":"2026-09-18","observed_at":"2026-09-25","attribution":"a",\#
        "standings":[{"model":"a","position":1,"effort":"max"},{"model":"b","position":1,"effort":"unspecified"}]}],"models":[{"id":"a",\#
        "display":"A","vendor":"V","blended_per_m":1.25,"accessibility":null},{"id":"b","display":"B",\#
        "vendor":"V","blended_per_m":3.25,"accessibility":"API access"}]}
        """#.utf8)

    func testTheBoardsRequestCarriesNothing() async throws {
        StubProtocol.lastRequestedURL = nil
        StubProtocol.outcome = .success((200, payload))
        _ = try await client().boards()
        let url = try XCTUnwrap(StubProtocol.lastRequestedURL)

        XCTAssertEqual(url.path, "/v1/boards")
        XCTAssertNil(url.query, "the standings request carried a query; D-167 says it carries nothing")
    }

    func testAWellFormedPayloadDecodesAndKeepsWhatItDecoded() async throws {
        // Since security S2 the phone keeps the standings encoded again from what it decoded, not
        // the engine's bytes verbatim: the kept payload decodes to exactly the same standings.
        StubProtocol.outcome = .success((200, payload))
        let fetched = try await client().boards()

        XCTAssertEqual(try FetchedStandings(payload: fetched.payload).standings, fetched.standings)
        XCTAssertEqual(fetched.standings.boards.first?.standings.map(\.position), [1, 1])
        XCTAssertEqual(fetched.standings.models.map(\.accessibility), [nil, "API access"])
    }

    func testTheBoardsRequestSetsNoHeaderOfItsOwn() async throws {
        // Review M4: nothing about the reader can ride in a header either. The app sets none; what
        // URLSession adds by itself is the same on every request.
        StubProtocol.lastRequest = nil
        StubProtocol.outcome = .success((200, payload))
        _ = try await client().boards()
        let request = try XCTUnwrap(StubProtocol.lastRequest)
        let own = (request.allHTTPHeaderFields ?? [:]).keys.filter { !["Accept", "Accept-Encoding", "Accept-Language", "User-Agent"].contains($0) }

        XCTAssertEqual(own, [], "the standings request carried headers of its own")
        XCTAssertEqual(request.httpMethod ?? "GET", "GET")
        XCTAssertNil(request.httpBody)
    }

    func testAnUnreadableResponseIsRefusedRatherThanStored() async {
        // Review M4.
        StubProtocol.outcome = .success((200, Data(#"{"boards": "not a list"}"#.utf8)))
        do {
            _ = try await client().boards()
            XCTFail("an unreadable standings payload was accepted")
        } catch let EngineError.undecodable(detail) {
            XCTAssertFalse(detail.isEmpty)
        } catch {
            XCTFail("an unreadable payload failed as \(error), not as a refused payload")
        }
    }

    func testAnOversizedPayloadIsRefusedBeforeItIsDecoded() async {
        StubProtocol.outcome = .success((200, Data(count: EngineClient.maxStandingsBytes + 1)))
        do {
            _ = try await client().boards()
            XCTFail("an oversized standings payload was accepted")
        } catch let EngineError.undecodable(detail) {
            XCTAssertTrue(detail.contains("larger than"), detail)
        } catch {
            XCTFail("an oversized payload failed as \(error), not as a refused payload")
        }
    }
}

/// A stub that sends its body in chunks, from a queue of its own, and records whether the loading
/// system stopped it before the last one: the observable difference between a read that stops at
/// its ceiling and one that takes everything and checks the size after (review M1).
private final class ChunkedStub: URLProtocol, @unchecked Sendable {
    nonisolated(unsafe) static var chunkSize = 64 * 1024
    nonisolated(unsafe) static var chunks = 64
    /// The `Content-Length` the response declares, or none.
    nonisolated(unsafe) static var declared: Int?
    private static let lock = NSLock()
    nonisolated(unsafe) private static var sent = 0
    nonisolated(unsafe) private static var stoppedEarly = false
    private var cancelled = false

    static func reset() {
        lock.lock(); defer { lock.unlock() }
        sent = 0
        stoppedEarly = false
    }

    static var observed: (sent: Int, stopped: Bool) {
        lock.lock(); defer { lock.unlock() }
        return (sent, stoppedEarly)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let headers = Self.declared.map { ["Content-Length": String($0)] } ?? [:]
        let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: headers)!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        let (size, count) = (Self.chunkSize, Self.chunks)
        DispatchQueue(label: "chunked-stub").async { [self] in
            for _ in 0..<count {
                if isCancelled { return }
                client?.urlProtocol(self, didLoad: Data(repeating: 0x20, count: size))
                Self.lock.lock(); Self.sent += 1; Self.lock.unlock()
                Thread.sleep(forTimeInterval: 0.005)
            }
            if !isCancelled { client?.urlProtocolDidFinishLoading(self) }
        }
    }

    private var isCancelled: Bool {
        Self.lock.lock(); defer { Self.lock.unlock() }
        return cancelled
    }

    override func stopLoading() {
        Self.lock.lock(); defer { Self.lock.unlock() }
        cancelled = true
        if Self.sent < Self.chunks { Self.stoppedEarly = true }
    }
}

/// #56 (M17-W4 security S3): the phone read a whole response into memory before any size check, and
/// only `/v1/boards` had a ceiling. Every route has one now, and the read stops at it.
final class ResponseCeilingTests: OfflineTestCase {
    private func chunkedClient() -> EngineClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [ChunkedStub.self]
        return EngineClient(baseURL: URL(string: "http://127.0.0.1:8080")!, session: URLSession(configuration: configuration))
    }

    private func settle() async {
        for _ in 0..<200 where !ChunkedStub.observed.stopped {
            try? await Task.sleep(nanoseconds: 10_000_000)
        }
    }

    /// Review M1, the property itself: 4 MiB offered in 64 KiB chunks against the categories' 256 KiB
    /// ceiling. The transfer is stopped long before its last chunk; a read that took everything and
    /// checked the size afterwards would have let all 64 arrive.
    func testTheReadStopsAtTheCeilingWhileTheResponseStreams() async {
        ChunkedStub.reset()
        ChunkedStub.declared = nil
        ChunkedStub.chunks = 64
        do {
            _ = try await chunkedClient().categories()
            XCTFail("a 4 MiB answer was accepted under a 256 KiB ceiling")
        } catch let EngineError.undecodable(detail) {
            XCTAssertTrue(detail.contains("larger than"), detail)
        } catch {
            XCTFail("refused as \(error)")
        }
        await settle()
        let observed = ChunkedStub.observed
        XCTAssertTrue(observed.stopped, "the transfer was not stopped: the whole response was read")
        XCTAssertLessThan(observed.sent, 32, "\(observed.sent) of 64 chunks were sent before the read stopped")
    }

    /// A declared length over the ceiling is refused before a byte is read: here the body that follows
    /// is small, and only the declaration can refuse it.
    func testADeclaredLengthOverTheCeilingIsRefusedBeforeTheBody() async {
        ChunkedStub.reset()
        ChunkedStub.declared = 10 * 1024 * 1024
        ChunkedStub.chunks = 1
        ChunkedStub.chunkSize = 16
        defer {
            ChunkedStub.declared = nil
            ChunkedStub.chunkSize = 64 * 1024
            ChunkedStub.chunks = 64
        }
        do {
            _ = try await chunkedClient().categories()
            XCTFail("a response declaring 10 MiB was read")
        } catch let EngineError.undecodable(detail) {
            XCTAssertTrue(detail.contains("larger than"), "refused for its body, not its declaration: \(detail)")
        } catch {
            XCTFail("refused as \(error)")
        }
    }

    private func client() -> EngineClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubProtocol.self]
        return EngineClient(
            baseURL: URL(string: "http://127.0.0.1:8080")!,
            session: URLSession(configuration: configuration)
        )
    }

    private func refusal(_ call: (EngineClient) async throws -> Void) async -> String? {
        do {
            try await call(client())
            return nil
        } catch let EngineError.undecodable(detail) {
            return detail
        } catch {
            return "\(error)"
        }
    }

    func testEveryRouteHasACeilingAboveWhatTheEngineSendsToday() {
        // Measured on the 2026-10-04 artifact: categories 4,300 bytes, the largest recommendation
        // 47,920, the boards 513,532. Each ceiling leaves room to grow and none is unbounded.
        XCTAssertEqual(EngineClient.byteCeiling(for: "v1/categories"), 256 * 1024)
        XCTAssertEqual(EngineClient.byteCeiling(for: "v1/recommendations"), 1024 * 1024)
        XCTAssertEqual(EngineClient.byteCeiling(for: "v1/boards"), EngineClient.maxStandingsBytes)
        XCTAssertEqual(EngineClient.byteCeiling(for: "v1/anything-new"), 256 * 1024,
                       "a route nobody sized gets the smallest ceiling, not none")
    }

    func testAnOversizedAnswerIsRefusedOnTheRoutesThatHadNoCeiling() async {
        StubProtocol.outcome = .success((200, Data(repeating: 0x20, count: 1024 * 1024 + 1)))
        let recommendation = await refusal { _ = try await $0.recommendation(task: "coding", budget: "unlimited") }
        XCTAssertTrue(recommendation?.contains("larger than") == true, recommendation ?? "accepted")

        StubProtocol.outcome = .success((200, Data(repeating: 0x20, count: 256 * 1024 + 1)))
        let categories = await refusal { _ = try await $0.categories() }
        XCTAssertTrue(categories?.contains("larger than") == true, categories ?? "accepted")
    }

    func testAnAnswerAtTheCeilingIsReadWhole() async {
        // At the ceiling exactly, the read completes and the payload reaches the decoder.
        StubProtocol.outcome = .success((200, Data(repeating: 0x20, count: 256 * 1024)))
        let categories = await refusal { _ = try await $0.categories() }
        XCTAssertFalse(categories?.contains("larger than") == true, categories ?? "")
    }

    func testAnOversizedRefusalIsCappedToo() async {
        StubProtocol.outcome = .success((503, Data(repeating: 0x20, count: 256 * 1024 + 1)))
        let categories = await refusal { _ = try await $0.categories() }
        XCTAssertTrue(categories?.contains("larger than") == true, categories ?? "accepted")
    }
}

/// M18-W1 (#87, D-171, REQ-DEV-001): the engine the app talks to is set per build, and loopback when it is not.
final class EngineAddressTests: OfflineTestCase {
    func testABuildsEngineAddressIsUsedWhenItIsAnHttpUrlWithAHost() {
        XCTAssertEqual(EngineClient.engineURL(from: "http://My-Mac.local:8080"),
                       URL(string: "http://My-Mac.local:8080"))
        XCTAssertEqual(EngineClient.engineURL(from: "https://engine.example"), URL(string: "https://engine.example"))
        XCTAssertEqual(EngineClient.engineURL(from: "http://192.0.2.26:8080"), URL(string: "http://192.0.2.26:8080"))
    }

    func testAFailureToReachTheEngineShowsTheAddressItAsked() {
        // W1 second review B2: on a phone, a mistyped ENGINE_URL falls back to loopback, which the
        // phone can never reach; the address under the error is how the owner sees it.
        let address = URL(string: "http://my-mac.local:8080")!
        for error: EngineError in [.unreachable("x"), .timedOut(seconds: 5), .offline] {
            let note = error.addressNote(address, .english)
            XCTAssertEqual(note, "Engine address: http://my-mac.local:8080", "\(error)")
        }
    }

    func testAFailureWhoseCauseIsTheAddressShowsIt() {
        // W1 third review M10: the engine's own refusal of a Host not on its list (D-171), and ATS
        // refusing a cleartext name, are the two failures where the address is the cause.
        let address = URL(string: "http://my-mac.local:8080")!
        for error: EngineError in [.refused(status: 400, code: "unknown_host", message: "m"), .insecureTransport] {
            XCTAssertEqual(error.addressNote(address, .english), "Engine address: http://my-mac.local:8080", "\(error)")
        }
    }

    func testTheAddressLineIsInTheReadersLanguage() {
        // W1 Tester T5 (REQ-DEV-001): the failure view passes the reader's language; the line follows it.
        let address = URL(string: "http://my-mac.local:8080")!
        for error: EngineError in [.unreachable("x"), .timedOut(seconds: 5), .offline, .insecureTransport,
                                   .refused(status: 400, code: "unknown_host", message: "m")] {
            XCTAssertEqual(error.addressNote(address, .turkish), "Motor adresi: http://my-mac.local:8080", "\(error)")
        }
    }

    func testAnAnswerTheEngineGaveCarriesNoAddress() {
        let address = URL(string: "http://127.0.0.1:8080")!
        for error: EngineError in [.refused(status: 503, code: "c", message: "m"), .undecodable("x")] {
            XCTAssertNil(error.addressNote(address, .english), "\(error)")
        }
    }

    func testAnythingElseFallsBackToLoopback() {
        let loopback = URL(string: "http://127.0.0.1:8080")
        // W1 second Tester T11: `http://:8080` parses with an EMPTY host (not nil), as an override that
        // lost its name does; only the `!host.isEmpty` guard sends it to loopback.
        for raw: String? in [nil, "", "not a url", "ftp://engine.example", "file:///etc/passwd", "http://",
                             "http://:8080", "$(ENGINE_URL)", "javascript:alert(1)"] {
            XCTAssertEqual(EngineClient.engineURL(from: raw), loopback, raw ?? "nil")
        }
    }
}

/// A stub that answers 200, hands over the first bytes of a body, and then the transfer fails.
private final class MidStreamFailureStub: URLProtocol, @unchecked Sendable {
    nonisolated(unsafe) static var failure = URLError(.timedOut)

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func stopLoading() {}

    override func startLoading() {
        guard let url = request.url,
              let response = HTTPURLResponse(url: url, statusCode: 200, httpVersion: nil,
                                             headerFields: ["Content-Type": "application/json"])
        else {
            client?.urlProtocol(self, didFailWithError: URLError(.badURL))
            return
        }
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        // A typed response and more than the 512 bytes URLSession sniffs, so the response is handed
        // over now; the failure comes later, from a queue of its own. Sent at once, it is thrown by the
        // request itself, before any body is read, which is the case the other stubs hold.
        client?.urlProtocol(self, didLoad: Data((#"{"categories": ["# + String(repeating: " ", count: 2048)).utf8))
        let failure = Self.failure
        DispatchQueue(label: "mid-stream-failure").asyncAfter(deadline: .now() + 0.2) { [self] in
            client?.urlProtocol(self, didFailWithError: failure)
        }
    }
}

/// W2 Tester (#56): the body is read inside the same `do` as the request, so a transfer that dies
/// after its first bytes is mapped like one that never started. With the read moved below the
/// `catch`, a timeout mid-body escaped as a raw URLError, the screen said the app needs an update,
/// and every test passed: every other stub here fails before it answers.
final class MidStreamFailureTests: OfflineTestCase {
    func testATransferThatDiesMidBodyIsMappedLikeOneThatNeverStarted() async throws {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MidStreamFailureStub.self]
        let base = try XCTUnwrap(URL(string: "http://127.0.0.1:8080"))
        let client = EngineClient(baseURL: base, session: URLSession(configuration: configuration))
        let cases: [(URLError.Code, EngineError)] = [
            (.timedOut, .timedOut(seconds: EngineClient.requestTimeout)),
            (.networkConnectionLost, .offline),
        ]
        for (code, expected) in cases {
            MidStreamFailureStub.failure = URLError(code)
            do {
                _ = try await client.categories()
                XCTFail("a transfer that died mid-body was read")
            } catch let error as EngineError {
                XCTAssertEqual(error, expected, "\(code)")
            } catch {
                XCTFail("a \(code) thrown mid-body escaped unmapped: \(error)")
            }
        }
    }
}

/// #144 (the M18 closure security seat's S10): the phone's engine session kept cookies for its life,
/// so a cookie set by the engine's host, or by anyone on the home network's cleartext path, rode on
/// every later request, the parameterless `/v1/boards` included. The session the app builds is read
/// here as it ships, through its own configuration. Its configuration is what can be observed: a
/// URLProtocol stub bypasses the session's cookie handling (measured: a stub answering `Set-Cookie`
/// saw no `Cookie` sent back even from the session that kept cookies), so a stub cannot show it.
/// INV-85; REQ-GAP-001 (nothing the phone records leaves it, and a cookie is a record it sends back).
final class EngineCookieTests: OfflineTestCase {
    private func shippedConfiguration() throws -> URLSessionConfiguration {
        let session = Mirror(reflecting: EngineClient()).children.first { $0.label == "session" }?.value
        return try XCTUnwrap(session as? URLSession, "the client keeps no session where this test looks").configuration
    }

    func testTheShippedSessionNeitherStoresNorSendsACookie() throws {
        let configuration = try shippedConfiguration()
        XCTAssertFalse(configuration.httpShouldSetCookies, "the session attaches stored cookies to requests")
        XCTAssertEqual(configuration.httpCookieAcceptPolicy, .never, "the session accepts cookies")
        XCTAssertNil(configuration.httpCookieStorage, "the session has somewhere to keep a cookie")
    }
}
