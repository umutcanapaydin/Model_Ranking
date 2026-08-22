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

final class SameHostOnlyTests: XCTestCase {
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

final class EngineErrorVocabularyTests: XCTestCase {

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

    func testUnreachableTellsThemHowToStartTheEngine() {
        let recovery = EngineError.unreachable("connection refused").recovery ?? ""

        XCTAssertTrue(recovery.contains("make run"),
                      "the one recoverable failure does not name the remedy: \(recovery)")
    }
}

final class PayloadDecodingTests: XCTestCase {

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

    override func startLoading() {
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

final class EngineClientDecisionTests: XCTestCase {
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
