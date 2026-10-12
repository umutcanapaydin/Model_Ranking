import Foundation
import XCTest

@testable import ModelRankingEngine

/// #260 (the owner's D-185 ruling, 2026-10-12): the Credits screen shows every served source with its
/// publisher, licence and links, from the `credits` the engine sends on `/v1/boards`.
final class CreditsTests: OfflineTestCase {
    private let payload = Data("""
    {"api_version": "v1", "attributions": ["a"], "boards": [], "models": [],
     "credits": [
       {"id": "swebench", "publisher": "SWE-bench", "data": "SWE-bench leaderboard",
        "url": "https://www.swebench.com", "licence": "CC BY-NC 4.0",
        "licence_url": "https://creativecommons.org/licenses/by-nc/4.0/"},
       {"id": "datacurve", "publisher": "Datacurve", "data": "DeepSWE leaderboard",
        "url": "https://deepswe.datacurve.ai/", "licence": "No licence published", "licence_url": null}
     ]}
    """.utf8)

    /// Since security S2 the phone keeps the standings encoded from what it decoded: a credit the
    /// model drops is gone from the kept copy, and from the screen.
    func testTheCreditsSurviveTheStandingsKeptOnThePhone() throws {
        let kept = try JSONEncoder().encode(JSONDecoder().decode(Standings.self, from: payload))
        let object = try XCTUnwrap(JSONSerialization.jsonObject(with: kept) as? [String: Any])
        let credits = try XCTUnwrap(object["credits"] as? [[String: Any]], "the kept standings lost the credits")
        XCTAssertEqual(credits.map { $0["id"] as? String }, ["swebench", "datacurve"])
        XCTAssertEqual(credits[0]["licence_url"] as? String, "https://creativecommons.org/licenses/by-nc/4.0/")
    }

    func testACreditDecodesWithItsLinksAndAPublisherWithNoLicenceHasNoLicenceLink() throws {
        let credits = try XCTUnwrap(JSONDecoder().decode(Standings.self, from: payload).credits)
        XCTAssertEqual(credits.map(\.id), ["swebench", "datacurve"])
        XCTAssertEqual(credits[0], Credit(id: "swebench", publisher: "SWE-bench", data: "SWE-bench leaderboard",
                                          url: "https://www.swebench.com", licence: "CC BY-NC 4.0",
                                          licenceUrl: "https://creativecommons.org/licenses/by-nc/4.0/"))
        XCTAssertNil(credits[1].licenceUrl)
    }

    /// A phone ahead of its engine: an engine from before #260 sends no credits, and the boards still read.
    func testAnEngineThatSendsNoCreditsStillGivesTheBoards() throws {
        let older = Data(#"{"api_version": "v1", "attributions": ["a"], "boards": [], "models": []}"#.utf8)
        let standings = try JSONDecoder().decode(Standings.self, from: older)
        XCTAssertNil(standings.credits)
        XCTAssertEqual(standings.attributions, ["a"])
    }

    func testTheCreditsScreenSpeaksBothLanguages() {
        let texts: [(Language) -> String] = [UIText.creditsTitle, UIText.creditsPurpose, UIText.creditsLicence,
                                             UIText.creditsData, UIText.creditsUnavailable]
        for text in texts {
            XCTAssertFalse(text(.english).isEmpty)
            XCTAssertNotEqual(text(.english), text(.turkish))
        }
        // CC BY 4.0 section 3(a)(1): the notice of modification and the warranty disclaimer, in both
        // languages (the round-2 review's M2).
        XCTAssertTrue(UIText.creditsPurpose(.english).contains("ranks each board again"))
        XCTAssertTrue(UIText.creditsPurpose(.english).contains("combines boards"))
        XCTAssertTrue(UIText.creditsPurpose(.english).contains("without any warranty"))
        XCTAssertTrue(UIText.creditsPurpose(.turkish).contains("yeniden sıralar"))
        XCTAssertTrue(UIText.creditsPurpose(.turkish).contains("birleştirir"))
        XCTAssertTrue(UIText.creditsPurpose(.turkish).contains("garanti olmadan"))
    }
}
