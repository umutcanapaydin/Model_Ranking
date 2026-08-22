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
