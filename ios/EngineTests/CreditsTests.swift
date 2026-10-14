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

    /// The Tester's B1: which empty text the sheet shows is decided here. An empty list is no credits
    /// either (the round-2 seat's F8).
    func testTheSheetSaysNotLoadedWithNoBoardsAndNotSentWithBoardsThatCarryNone() throws {
        XCTAssertEqual(CreditsScreen.state(nil, .english), .notLoaded(UIText.creditsUnavailable(.english)))
        let older = Data(#"{"api_version": "v1", "attributions": ["a"], "boards": [], "models": []}"#.utf8)
        let standings = try JSONDecoder().decode(Standings.self, from: older)
        XCTAssertEqual(CreditsScreen.state(standings, .turkish), .notSent(UIText.creditsNotSent(.turkish)))
        let none = Data(#"{"api_version": "v1", "attributions": ["a"], "boards": [], "models": [], "credits": []}"#.utf8)
        XCTAssertEqual(CreditsScreen.state(try JSONDecoder().decode(Standings.self, from: none), .english),
                       .notSent(UIText.creditsNotSent(.english)))
    }

    /// The Tester's round-2 B1: the notice the sheet draws carries CC BY's two notices in both languages.
    func testTheSheetsNoticeSaysHowTheDataIsChangedAndThatItComesWithoutWarranty() {
        XCTAssertEqual(CreditsScreen.notice(.english), UIText.creditsPurpose(.english))
        XCTAssertTrue(CreditsScreen.notice(.english).contains("ranks each board again"))
        XCTAssertTrue(CreditsScreen.notice(.english).contains("without any warranty"))
        XCTAssertTrue(CreditsScreen.notice(.turkish).contains("yeniden sıralar"))
        XCTAssertTrue(CreditsScreen.notice(.turkish).contains("garanti olmadan"))
    }

    /// The Tester's B1: each credit is listed with both links, each on a line of its own, so selecting
    /// one copies the address alone; a publisher with no licence link has none.
    func testEachCreditIsListedWithItsLinksOnLinesOfTheirOwn() throws {
        let standings = try JSONDecoder().decode(Standings.self, from: payload)
        guard case let .listed(rows) = CreditsScreen.state(standings, .english) else {
            return XCTFail("the credits were not listed")
        }
        XCTAssertEqual(rows.map(\.id), ["swebench", "datacurve"])
        XCTAssertEqual(rows[0].publisher, "SWE-bench")
        XCTAssertEqual(rows[0].data, "SWE-bench leaderboard")
        XCTAssertEqual(rows[0].dataLabel, UIText.creditsData(.english))
        XCTAssertEqual(rows[0].dataLink, "https://www.swebench.com")
        XCTAssertEqual(rows[0].licence, "\(UIText.creditsLicence(.english)): CC BY-NC 4.0")
        XCTAssertEqual(rows[0].licenceLink, "https://creativecommons.org/licenses/by-nc/4.0/")
        XCTAssertNil(rows[1].licenceLink)
        guard case let .listed(turkish) = CreditsScreen.state(standings, .turkish) else {
            return XCTFail("the credits were not listed in Turkish")
        }
        XCTAssertEqual(turkish[0].licence, "\(UIText.creditsLicence(.turkish)): CC BY-NC 4.0")
    }

    /// #261 (the #260 review's K1): Apache-2.0 and MIT ask a redistributor for the licence's text and the
    /// copyright notice. Each credit's notice is shown on its row, and the sheet carries the full text of
    /// each such licence the credits name, once, however many publishers use it; an older engine's credit
    /// with no notice still reads, and so does the notice through the copy kept on the phone.
    func testACreditsNoticeIsShownAndEachLicencesTextIsCarriedOnce() throws {
        let data = Data("""
        {"api_version": "v1", "attributions": ["a"], "boards": [], "models": [],
         "credits": [
           {"id": "litellm", "publisher": "BerriAI", "data": "LiteLLM model prices",
            "url": "https://github.com/BerriAI/litellm", "licence": "MIT",
            "licence_url": "https://github.com/BerriAI/litellm/blob/main/LICENSE", "notice": "Copyright (c) 2023 Berri AI"},
           {"id": "aider", "publisher": "Aider", "data": "Aider polyglot leaderboard",
            "url": "https://github.com/Aider-AI/aider", "licence": "Apache-2.0",
            "licence_url": "https://github.com/Aider-AI/aider/blob/main/LICENSE.txt", "notice": null},
           {"id": "helm", "publisher": "Stanford CRFM HELM", "data": "MMLU scores", "url": "https://crfm.stanford.edu",
            "licence": "Apache-2.0 (the HELM repository, D-193); each report as its authors published it",
            "licence_url": "https://github.com/stanford-crfm/helm/blob/main/LICENSE",
            "notice": "Copyright 2022 Stanford University"},
           {"id": "swebench", "publisher": "SWE-bench", "data": "SWE-bench leaderboard",
            "url": "https://www.swebench.com", "licence": "CC BY-NC 4.0",
            "licence_url": "https://creativecommons.org/licenses/by-nc/4.0/"}
         ]}
        """.utf8)
        let standings = try JSONDecoder().decode(Standings.self, from: data)
        guard case let .listed(rows) = CreditsScreen.state(standings, .english) else {
            return XCTFail("the credits were not listed")
        }
        XCTAssertEqual(rows.map(\.notice), ["Copyright (c) 2023 Berri AI", nil, "Copyright 2022 Stanford University", nil])
        let kept = try JSONDecoder().decode(Standings.self, from: JSONEncoder().encode(standings))
        XCTAssertEqual(kept.credits?.first?.notice, "Copyright (c) 2023 Berri AI")

        let texts = CreditsScreen.licenceTexts(standings)
        XCTAssertEqual(texts.map(\.name), ["MIT", "Apache-2.0"])
        XCTAssertTrue(texts[0].text.contains("Permission is hereby granted, free of charge"))
        XCTAssertTrue(texts[0].text.contains("THE SOFTWARE IS PROVIDED \"AS IS\""))
        XCTAssertTrue(texts[1].text.contains("TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION"))
        XCTAssertTrue(texts[1].text.contains("END OF TERMS AND CONDITIONS"))
        XCTAssertTrue(CreditsScreen.licenceTexts(nil).isEmpty)
        XCTAssertFalse(UIText.creditsLicenceTexts(.english).isEmpty)
        XCTAssertNotEqual(UIText.creditsLicenceTexts(.english), UIText.creditsLicenceTexts(.turkish))
    }

    func testTheCreditsScreenSpeaksBothLanguages() {
        let texts: [(Language) -> String] = [UIText.creditsTitle, UIText.creditsPurpose, UIText.creditsLicence,
                                             UIText.creditsData, UIText.creditsUnavailable, UIText.creditsNotSent]
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
