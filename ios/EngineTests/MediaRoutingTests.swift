import NaturalLanguage
import XCTest
@testable import ModelRankingEngine

/// #378 (D-218 clause 1): a request to make or change a picture or a video is answered from its own
/// board, ranked on quality only, which reverses the decline hint of #113 and #192 and D-187's rule that
/// sent such a request to `vision`. Reading a picture the person has stays `vision`'s. Every line is made
/// up for this test; none is from a live held-out set.
final class MediaRoutingTests: OfflineTestCase {
    private let known = ["coding", "assistant", "agentic-coding", "everyday", "expert", "mathematics",
                         "computer-use", "abstract", "web-dev", "document", "factuality", "vision",
                         "search", "search_factuality",
                         "text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit"]
    private let media = ["text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit"]

    private func requireTheEmbedding(_ language: NLLanguage) throws {
        struct NoEmbedding: Error {}
        guard NLContextualEmbedding(language: language)?.hasAvailableAssets ?? false else {
            XCTFail("the embedding's assets are not on this machine, so the wording tier is not measured here")
            throw NoEmbedding()
        }
    }

    /// Every media surface has a routing hint for the model tier and six examples in each language for
    /// the wording tier, so no surface the engine serves is one the front door cannot reach.
    func testEveryMediaSurfaceIsDescribedForBothTiers() {
        for surface in media {
            XCTAssertNotNil(CategoryHints.byID[surface], surface)
            XCTAssertEqual(CategoryHints.examples[surface]?.count, 6, surface)
            XCTAssertEqual(CategoryHints.examplesTurkish[surface]?.count, 6, surface)
        }
    }

    /// The probe of each surface: a request that names what it wants made or changed reaches that surface
    /// on its words alone, in English and in Turkish, before any embedding runs.
    func testARequestThatNamesItsJobReachesItsSurfaceOnItsWords() {
        let lines: [(String, String)] = [
            ("generate a picture of a red bicycle", "text_to_image"),
            ("bir bisiklet resmi oluştur", "text_to_image"),
            ("edit my photo so the colours pop", "image_edit"),
            ("bu fotoğrafı düzenle", "image_edit"),
            ("create a video of waves crashing at night", "text_to_video"),
            ("dalgaların videosunu yap", "text_to_video"),
            ("animate this photo of my cat", "image_to_video"),
            ("bu fotoğrafı canlandır", "image_to_video"),
            ("edit this video of my wedding", "video_edit"),
            ("düğün videomu düzenle", "video_edit"),
        ]
        for (question, surface) in lines {
            XCTAssertEqual(CategoryHints.namedSurface(question, within: known), surface, question)
        }
    }

    /// A question about a picture the person has, or one that only mentions a video, is not a request to
    /// make or change one: `vision` keeps reading pictures, and a video to summarise is left to the
    /// embedding rather than sent to a making board on one word.
    func testReadingAPictureOrMentioningAVideoNamesNoMediaSurface() {
        XCTAssertEqual(CategoryHints.namedSurface("describe the picture i took at the zoo", within: known), "vision")
        XCTAssertEqual(CategoryHints.namedSurface("bu fotoğrafta ne yazıyor", within: known), "vision")
        for question in ["summarise this video lecture for me", "help me draw conclusions from this survey",
                         "write a script that resizes images"] {
            let named = CategoryHints.namedSurface(question, within: known)
            XCTAssertFalse(named.map(media.contains) ?? false, "\(question) -> \(named ?? "nil")")
        }
    }

    /// The wording tier, on a device with no on-device model: a request in a reader's own words, with no
    /// keyword, reaches a media surface, measured, never "not measured".
    func testTheWordingTierAnswersAMediaRequestFromItsBoard() async throws {
        try requireTheEmbedding(.english)
        let lines: [(String, String)] = [
            ("paint a watercolour of a lighthouse at dawn", "text_to_image"),
            ("make my profile photo look better", "image_edit"),
            ("cut the silent parts out of my video", "video_edit"),
        ]
        for (question, surface) in lines {
            let outcome = await TieredRouter(model: nil).route(question, within: known)
            XCTAssertEqual(outcome.categoryID, surface, question)
            XCTAssertFalse(outcome.unmeasured, question)
        }
    }

    /// An engine that serves no media surface (an older one) is never sent a question to one: the media
    /// rules only name a surface the engine served, and the question is still answered, measured.
    func testAnEngineWithoutTheMediaSurfacesIsNeverSentToOne() async {
        let older = known.filter { !media.contains($0) }
        for question in ["bana bir kedi resmi çiz", "generate a picture of a red bicycle", "animate this photo of my cat"] {
            let named = CategoryHints.namedSurface(question, within: older)
            XCTAssertFalse(named.map(media.contains) ?? false, question)
            let outcome = await TieredRouter(model: nil).route(question, within: older)
            XCTAssertTrue(older.contains(outcome.categoryID), question)
        }
    }
}
