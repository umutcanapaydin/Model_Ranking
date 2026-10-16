//  GoldenQuestionTests.swift -- #289 (D-202 clause 2): a real question routes to the surface it asks
//  for and yields the top 3 the published boards give it.
//
//  The set is `Golden/golden-questions.json`, 30 to 50 questions as a reader types them, in English and
//  Turkish, kept apart from every held-out set (D-191). A person writes each question's surface; its
//  top 3 is derived by `scripts/golden_questions.py` from the pinned snapshot beside it (`categories.json`
//  and `boards.json` from the hosted engine, `snapshot.json` says when and from which build). This test
//  routes each question through the wording tier, as a device without the on-device model does, and
//  plans its answer from the same snapshot through `answerPlan`, as the screen plans it.
//
//  What is asserted, per question:
//  - `disputed`: nothing; the surface is not settled (D-202 clause 2). It is reported.
//  - otherwise the surface, measured (not "not measured"); and unless `top3_disputed` (a one-board
//    family, or old boards that change the top 3) the models at places 1 to 3, as a set, since tied
//    models share a place.
//  - `known_miss`: a filed miss. It is reported; a known miss that now passes FAILS, so its mark is
//    removed and the question guards the fix.
//  Every miss is written to `build/golden-report.txt` and printed.

import Foundation
import NaturalLanguage
import XCTest

@testable import ModelRankingEngine

final class GoldenQuestionTests: OfflineTestCase {
    struct Entry: Decodable {
        let question: String
        let language: String
        let expectedSurface: String
        let disputed: Bool
        let reason: String?
        let knownMiss: Int?
        let expectedTop3: [String]
        let expectedTop3Names: [String]
        let top3Disputed: Bool
        let top3Reason: String?

        enum CodingKeys: String, CodingKey {
            case question, language, disputed, reason
            case expectedSurface = "expected_surface"
            case knownMiss = "known_miss"
            case expectedTop3 = "expected_top3"
            case expectedTop3Names = "expected_top3_names"
            case top3Disputed = "top3_disputed"
            case top3Reason = "top3_reason"
        }
    }

    struct Snapshot {
        let entries: [Entry]
        let categories: [ModelRankingEngine.Category]
        let standings: Standings
        let day: Date
    }

    private struct Missing: Error, CustomStringConvertible {
        let description: String
    }

    private func snapshot() throws -> Snapshot {
        guard let folder = Bundle.module.url(forResource: "Golden", withExtension: nil) else {
            throw Missing(description: "the test bundle carries no Golden folder (ios/Package.swift resources)")
        }
        func read(_ name: String) throws -> Data { try Data(contentsOf: folder.appendingPathComponent(name)) }
        let meta = try JSONSerialization.jsonObject(with: read("snapshot.json")) as? [String: Any]
        let fetched = (meta?["fetched_at"] as? String).map { String($0.prefix(10)) } ?? ""
        let format = DateFormatter()
        format.locale = Locale(identifier: "en_US_POSIX")
        format.timeZone = TimeZone(identifier: "UTC")
        format.dateFormat = "yyyy-MM-dd"
        guard let day = format.date(from: fetched) else {
            throw Missing(description: "snapshot.json names no fetch day")
        }
        return Snapshot(entries: try JSONDecoder().decode([Entry].self, from: read("golden-questions.json")),
                        categories: try JSONDecoder().decode(CategoryList.self, from: read("categories.json")).categories,
                        standings: try JSONDecoder().decode(Standings.self, from: read("boards.json")),
                        day: day)
    }

    /// As `TurkishEmbeddingTests` does: where the assets do not load, the test fails rather than passing
    /// having measured nothing, and a skip is no way out (`make swift-test` fails a skipped test).
    private func requireTheEmbeddings() throws {
        for language in [NLLanguage.english, .turkish] where !(NLContextualEmbedding(language: language)?.hasAvailableAssets ?? false) {
            XCTFail("the \(language.rawValue) embedding's assets are not on this machine, so the golden set is not measured here")
            throw Missing(description: "no \(language.rawValue) embedding")
        }
    }

    /// The models at places 1 to 3 of what the screen plans, as a set; `nil` where it shows the cards.
    static func topThree(_ plan: AnswerPlan) -> Set<String>? {
        guard case let .combined(view) = plan else { return nil }
        return Set(view.list.entries.filter { $0.place <= 3 }.map(\.model.id))
    }

    static func plan(_ outcome: RoutingOutcome, question: String?, _ snapshot: Snapshot) -> AnswerPlan {
        let info = snapshot.categories.first { $0.id == outcome.categoryID }
        return answerPlan(outcome: outcome, primaryBoard: info?.primaryBoard, family: info?.boards, question: question,
                          asOf: snapshot.day, standings: snapshot.standings, removed: [],
                          refinedBoard: info?.refinedBoard)
    }

    /// Which reading decided a question, for the report: the words that name a surface, the general words
    /// a Turkish question about models keeps on `everyday` (#222), or the examples the embedding compares.
    static func reader(_ question: String, within known: [String]) -> String {
        if let named = CategoryHints.namedSurface(question, within: known) { return "the words that name \(named)" }
        guard SimilarityRouter.readsTurkish(question.lowercased()) else { return "the English examples" }
        return CategoryHints.generalSurface(question, within: known) == nil
            ? "the Turkish examples" : "the general words a Turkish question about models keeps on everyday"
    }

    /// The set is what D-202 asks: 30 to 50 questions, in both languages, each on a surface the snapshot
    /// serves, each with a derived top 3.
    func testTheGoldenSetIsWellFormed() throws {
        let snapshot = try snapshot()
        XCTAssertTrue((30...50).contains(snapshot.entries.count), "\(snapshot.entries.count) questions")
        XCTAssertEqual(Set(snapshot.entries.map(\.language)), ["en", "tr"])
        let served = Set(snapshot.categories.map(\.id))
        for entry in snapshot.entries {
            XCTAssertTrue(served.contains(entry.expectedSurface), entry.question)
            XCTAssertFalse(entry.expectedTop3.isEmpty, entry.question)
            XCTAssertEqual(entry.expectedTop3.count, entry.expectedTop3Names.count, entry.question)
            XCTAssertTrue(!entry.disputed || entry.reason != nil, "a disputed question says why: \(entry.question)")
            XCTAssertTrue(!entry.top3Disputed || entry.top3Reason != nil, entry.question)
        }
    }

    /// The two derivations agree: for each surface whose top 3 is settled, the family list the app builds
    /// from the snapshot (a surface chosen by hand, so no question's words refine it) has the top 3 the
    /// script wrote. A miss in the routed test below is then the router's or a refinement's, never a
    /// disagreement between the script and `combineFamily`.
    func testEachSurfacesFamilyListGivesTheDerivedTopThree() throws {
        let snapshot = try snapshot()
        var checked = Set<String>()
        for entry in snapshot.entries where !entry.top3Disputed && checked.insert(entry.expectedSurface).inserted {
            let plan = Self.plan(chosenOutcome(entry.expectedSurface), question: nil, snapshot)
            XCTAssertEqual(Self.topThree(plan), Set(entry.expectedTop3), entry.expectedSurface)
        }
        XCTAssertFalse(checked.isEmpty, "no surface's top 3 is settled, so nothing was compared")
    }

    func testEachGoldenQuestionRoutesToItsSurfaceAndItsTopThree() async throws {
        try requireTheEmbeddings()
        let snapshot = try snapshot()
        let known = snapshot.categories.map(\.id)
        let names = Dictionary(snapshot.standings.models.map { ($0.id, $0.display) }, uniquingKeysWith: { first, _ in first })
        func shown(_ ids: Set<String>?) -> String {
            guard let ids else { return "the engine's cards (no list from the boards)" }
            return ids.map { names[$0] ?? $0 }.sorted().joined(separator: ", ")
        }
        var report: [String] = []
        var passing = 0, asserted = 0, disputed = 0, knownMisses = 0
        for entry in snapshot.entries {
            let outcome = await TieredRouter(model: nil).route(entry.question, within: known)
            let got = Self.topThree(Self.plan(outcome, question: entry.question, snapshot))
            let surfaceRight = outcome.categoryID == entry.expectedSurface && !outcome.unmeasured
            let topRight = entry.top3Disputed || got == Set(entry.expectedTop3)
            let lines = [
                "  question: \(entry.question) [\(entry.language)]",
                "  expected: \(entry.expectedSurface) / \(entry.expectedTop3Names.joined(separator: ", "))"
                    + (entry.top3Disputed ? " (top 3 not asserted: \(entry.top3Reason ?? ""))" : ""),
                "  got:      \(outcome.categoryID)\(outcome.unmeasured ? " (not measured)" : "") via \(outcome.tier)"
                    + " / \(shown(got))",
                "  read by:  " + Self.reader(entry.question, within: known),
            ]
            if entry.disputed {
                disputed += 1
                report.append("DISPUTED (\(entry.reason ?? "")):\n" + lines.joined(separator: "\n"))
                continue
            }
            asserted += 1
            let pass = surfaceRight && topRight
            if pass { passing += 1 }
            if let issue = entry.knownMiss {
                knownMisses += 1
                if pass {
                    XCTFail("known miss #\(issue) now passes; remove its known_miss mark: \(entry.question)")
                    report.append("KNOWN MISS NOW PASSES (#\(issue)):\n" + lines.joined(separator: "\n"))
                } else {
                    report.append("KNOWN MISS (#\(issue)):\n" + lines.joined(separator: "\n"))
                }
            } else if !pass {
                XCTFail("golden miss: \(entry.question) expected \(entry.expectedSurface), got \(outcome.categoryID)"
                        + (surfaceRight ? " with another top 3" : ""))
                report.append("MISS:\n" + lines.joined(separator: "\n"))
            }
        }
        let summary = "golden set: \(passing) of \(asserted) asserted questions pass (\(knownMisses) known misses), "
            + "\(disputed) disputed, \(snapshot.entries.count) in all"
        let text = ([summary] + report).joined(separator: "\n\n") + "\n"
        print(text)
        let build = URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().appendingPathComponent("build")
        try? FileManager.default.createDirectory(at: build, withIntermediateDirectories: true)
        try? text.write(to: build.appendingPathComponent("golden-report.txt"), atomically: true, encoding: .utf8)
        XCTAssertGreaterThan(asserted, 0, "no golden question is asserted")
    }
}
