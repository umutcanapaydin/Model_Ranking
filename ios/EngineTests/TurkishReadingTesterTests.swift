import XCTest
import NaturalLanguage
@testable import ModelRankingEngine

/// The reading wave's Tester (`docs/reviews/backlog-reading-tester.md`): faults planted in #222's Turkish path
/// that the wave's own tests left green. Every line here is the Tester's own, never from a held-out set;
/// Turkish letters are written as escapes, so this file stays ASCII (rule L1). # covers D-196 clause 1
final class TurkishReadingTesterTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality"]

    private func requireTheEmbedding() throws {
        struct NoEmbedding: Error {}
        guard NLContextualEmbedding(language: .turkish)?.hasAvailableAssets ?? false else {
            XCTFail("the embedding's assets are not on this machine, so #222's routing is not measured here")
            throw NoEmbedding()
        }
    }

    /// T5: D-196 says the English path is unchanged. The general-question rule the wave added runs on a
    /// Turkish question only; run on an English one too, these went to `everyday` and the suite stayed green.
    func testAnEnglishQuestionWithAGeneralWordIsStillReadByTheEmbedding() async throws {
        try requireTheEmbedding()
        for question in ["which ai explains how volcanoes erupt", "claude for writing a thank you note to my boss",
                         "which model can fill in this web form for me"] {
            XCTAssertTrue(SimilarityRouter.readsEnglish(question), question)
            XCTAssertNotNil(CategoryHints.generalSurface(question, within: known), question)
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertNotEqual(outcome?.categoryID, "everyday", question)
            XCTAssertEqual(outcome?.unmeasured, false, question)
        }
    }

    /// T6: D-196 clause 1 reads the decline groups in plain letters too. With the lettered groups only,
    /// these plain-typed requests to change an image read as `abstract`.
    func testATurkishRequestToChangeAnImageTypedPlainReachesVision() async throws {
        try requireTheEmbedding()
        for question in ["bu fotodaki arka plani bulaniklastir", "portremi cizgi film gibi yap"] {
            XCTAssertTrue(SimilarityRouter.readsTurkish(question), question)
            XCTAssertNil(CategoryHints.namedSurface(question, within: known), question)
            let outcome = await SimilarityRouter().route(question, within: known)
            XCTAssertEqual(outcome?.categoryID, "vision", question)
        }
    }

    /// T7: each of the ten letters keeps a line out on its own, in both cases. The wave's test line holds
    /// three of them and the schwa line one, so dropping any of the other four, or the capitals, stayed green.
    func testEachLetterAzerbaijaniAndTurkmenWriteKeepsALineOutOfTurkishOnItsOwn() {
        let line = "bu ak\u{015F}am yemekte ne pi\u{015F}irsem diye d\u{00FC}\u{015F}\u{00FC}n\u{00FC}yorum"
        XCTAssertTrue(SimilarityRouter.readsTurkish(line))
        for letter in ["\u{0259}", "\u{00E4}", "\u{0148}", "\u{00FD}", "\u{017E}",
                       "\u{018F}", "\u{00C4}", "\u{0147}", "\u{00DD}", "\u{017D}"] {
            XCTAssertFalse(SimilarityRouter.readsTurkish(line + " " + letter), "U+\(String(letter.unicodeScalars.first!.value, radix: 16))")
        }
    }

    /// T9: the round-2 review's N3 keys a kept vector by the embedding's model and revision and by the
    /// language, so a model loaded later never reads another's vectors. The wave's test reads only a key's
    /// last line, so a key without the model, the revision or the language passed it.
    func testAKeptVectorIsKeyedByTheEmbeddingsModelRevisionAndLanguage() async throws {
        try requireTheEmbedding()
        _ = await SimilarityRouter().route("bu ak\u{015F}am ne pi\u{015F}irsem", within: known)
        _ = await SimilarityRouter().route("what should i cook tonight", within: known)
        var languages = Set<String>()
        for key in ExampleVectors.shared.keys {
            let parts = key.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
            XCTAssertEqual(parts.count, 4, key)
            guard parts.count == 4, let embedding = NLContextualEmbedding(language: NLLanguage(rawValue: parts[2]))
            else { continue }
            XCTAssertEqual(parts[0], embedding.modelIdentifier, key)
            XCTAssertEqual(parts[1], String(embedding.revision), key)
            languages.insert(parts[2])
        }
        XCTAssertEqual(languages, [NLLanguage.english.rawValue, NLLanguage.turkish.rawValue])
    }

    /// T10: the tables the Turkish path reads (`...BothSpellings`) hold each line once, its plain twin beside
    /// it, and all three decline groups. A twin kept twice counts one sentence as a surface's two closest
    /// examples, and a group dropped from the read table moved the image rule's comparison; both stayed green,
    /// since the wave's count test reads the lettered table.
    func testTheTablesTheTurkishPathReadsHoldEachLineOnceAndTheThreeGroups() {
        XCTAssertEqual(CategoryHints.unmeasuredHintsTurkishBothSpellings.count, CategoryHints.unmeasuredHints.count)
        XCTAssertEqual(Set(CategoryHints.examplesTurkishBothSpellings.keys), Set(CategoryHints.examples.keys))
        var pairs = CategoryHints.examplesTurkish.keys.map { surface in
            (CategoryHints.examplesTurkishBothSpellings[surface] ?? [], CategoryHints.examplesTurkish[surface] ?? [])
        }
        pairs += zip(CategoryHints.unmeasuredHintsTurkishBothSpellings, CategoryHints.unmeasuredHintsTurkish).map { ($0, $1) }
        for (read, written) in pairs {
            XCTAssertEqual(Set(read).count, read.count, "\(written.first ?? "")")
            XCTAssertEqual(Set(read), Set(written + written.map(CategoryHints.plain)), "\(written.first ?? "")")
        }
    }

    /// T8: a line the recogniser reads as Turkish below `confidentLanguage` stays off the Turkish path, and one
    /// above it is on it. No test held the threshold, so 0.3, 0.9 and 0.99 all passed.
    func testTheTurkishPathNeedsTheRecognisersConfidence() {
        for unsure in ["html sayfasi", "iphone mu android mi"] {
            let recogniser = NLLanguageRecognizer()
            recogniser.processString(unsure)
            XCTAssertEqual(recogniser.dominantLanguage, .turkish, unsure)
            XCTAssertLessThan(recogniser.languageHypotheses(withMaximum: 1)[.turkish] ?? 1, SimilarityRouter.confidentLanguage, unsure)
            XCTAssertFalse(SimilarityRouter.readsTurkish(unsure), unsure)
        }
        for sure in ["pizza tarifi", "api anahtari"] {
            XCTAssertTrue(SimilarityRouter.readsTurkish(sure), sure)
        }
    }
}
