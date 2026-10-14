import Foundation
import XCTest

@testable import ModelRankingEngine

/// #261 (D-197 clause 3), the gates Tester: the sheet carries a licence's text for each licence the served
/// credits name, and only those. A credit's licence names one when it begins with its name
/// (`LicenceText.carried`), wherever that credit sits in the list.
final class CreditsTesterTests: OfflineTestCase {
    private func standings(_ credits: String) throws -> Standings {
        let data = Data("""
        {"api_version": "v1", "attributions": ["a"], "boards": [], "models": [], "credits": [\(credits)]}
        """.utf8)
        return try JSONDecoder().decode(Standings.self, from: data)
    }

    private let swebench = """
    {"id": "swebench", "publisher": "SWE-bench", "data": "SWE-bench leaderboard", "url": "https://www.swebench.com",
     "licence": "CC BY-NC 4.0", "licence_url": "https://creativecommons.org/licenses/by-nc/4.0/"}
    """
    private let datacurve = """
    {"id": "datacurve", "publisher": "Datacurve", "data": "DeepSWE leaderboard", "url": "https://deepswe.datacurve.ai/",
     "licence": "No licence published", "licence_url": null}
    """

    /// HELM's licence is "Apache-2.0 (the HELM repository, D-193); ...": it begins with the name, so the
    /// Apache text is carried even when no credit's licence is "Apache-2.0" alone, and when the credit is
    /// third in the list.
    func testALicenceIsCarriedForACreditWhoseLicenceBeginsWithItsNameWhereverItIsListed() throws {
        let helm = """
        {"id": "helm", "publisher": "Stanford CRFM HELM", "data": "MMLU scores", "url": "https://crfm.stanford.edu",
         "licence": "Apache-2.0 (the HELM repository, D-193); each report as its authors published it",
         "licence_url": "https://github.com/stanford-crfm/helm/blob/main/LICENSE", "notice": "Copyright 2022 Stanford University"}
        """
        let texts = CreditsScreen.licenceTexts(try standings([swebench, datacurve, helm].joined(separator: ",")))
        XCTAssertEqual(texts.map(\.name), ["Apache-2.0"])
        XCTAssertEqual(texts.first?.text, LicenceText.apache20)
    }

    /// Credits that name neither Apache-2.0 nor MIT carry no licence text: the section is for the
    /// licences the credits name, not every licence the app holds.
    func testCreditsThatNameNoCarriedLicenceCarryNoText() throws {
        XCTAssertEqual(CreditsScreen.licenceTexts(try standings([swebench, datacurve].joined(separator: ","))), [])
        XCTAssertEqual(CreditsScreen.licenceTexts(try standings("")), [])
    }
}
