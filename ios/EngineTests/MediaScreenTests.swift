import XCTest
@testable import ModelRankingEngine

/// #378 (D-218 clause 1): a surface ranked on quality only arrives with no price, and the screens say
/// the price is not measured rather than showing a dash a reader could take for "free". The rows are
/// decoded from payloads shaped as `/v1` serves them, so the tests hold the served shape.
final class MediaScreenTests: OfflineTestCase {
    private let media = ["text_to_image", "image_edit", "text_to_video", "image_to_video", "video_edit"]

    private let unpricedRow = """
    {"model": "GPT-Image-2", "vendor": "OpenAI", "score": 1383.0, "metric": "elo", "secondary_score": null,
     "blended_per_m": null, "input_per_m": null, "output_per_m": null, "evidence_date": "2026-10-07",
     "harness": "arena-crowd", "effort": "unspecified"}
    """

    func testEveryMediaSurfaceHasATurkishNameAndALineSayingWhatItIsFor() {
        for id in media {
            XCTAssertNotEqual(UIText.surface(id: id, engineTitle: "ENGINE", .turkish), "ENGINE", id)
            let english = UIText.surfaceBlurb(id, .english), turkish = UIText.surfaceBlurb(id, .turkish)
            XCTAssertNotNil(english, id)
            XCTAssertNotNil(turkish, id)
            XCTAssertNotEqual(english, turkish, id)
        }
    }

    func testThePriceNotMeasuredIsWordedInBothLanguages() {
        XCTAssertEqual(priceExclusion("not_measured", in: .english), "The price is not measured on this board")
        XCTAssertEqual(priceExclusion("not_measured", in: .turkish), "Bu listede fiyat ölçülmüyor")
    }

    /// A ranking row with null prices decodes, and its detail screen says the price is not measured: no
    /// price line, no input and output line, and no dash on the card's figures.
    func testARowWithNoPriceDecodesAndItsDetailSaysThePriceIsNotMeasured() throws {
        let row = try JSONDecoder().decode(RankedModel.self, from: Data(unpricedRow.utf8))
        for language in [Language.english, .turkish] {
            let facts = detailFacts(model: row, benchmark: "Arena text-to-image", anchor: 1165.5, closeCallMargin: 3.8,
                                    secondaryBenchmark: nil, secondaryAgeDays: nil, minQuality: 1165.5,
                                    priceExcludes: "not_measured", in: language)
            let price = facts.filter { $0.label == (language == .turkish ? "Fiyat" : "Price") }
            XCTAssertEqual(price.map(\.value), [priceExclusion("not_measured", in: language)], "\(language)")
            XCTAssertFalse(facts.contains { $0.label == "Input / output" || $0.label == "Giriş / çıkış" })
            XCTAssertFalse(facts.contains { $0.label == "Not in the price" || $0.label == "Fiyata dahil değil" })
            let figures = figuresLine(score: row.score, metric: row.metric, blendedPerM: row.blendedPerM, language,
                                      ranked: true, anchor: 1165.5)
            XCTAssertFalse(figures.contains("—"), figures)
            XCTAssertFalse(figures.contains("$"), figures)
        }
    }

    func testAPickWithNoPriceDecodes() throws {
        let pick = """
        {"label": "best_quality", "model": "GPT-Image-2", "vendor": "OpenAI", "score": 1383.0, "metric": "elo",
         "secondary_score": null, "blended_per_m": null, "input_per_m": null, "output_per_m": null,
         "evidence_date": "2026-10-07", "harness": "arena-crowd", "effort": "unspecified", "higher_effort": null,
         "higher_effort_score": null, "effort_note": null, "confidence": "Medium",
         "confidence_basis": "one independent benchmark (Arena text-to-image)", "why": "Highest score.",
         "trade_off": null, "why_fact": {"reason": "highest_score"}, "trade_off_fact": null, "model_id": "gpt-image2"}
        """
        XCTAssertNoThrow(try JSONDecoder().decode(Pick.self, from: Data(pick.utf8)))
    }

    /// `/v1/boards` lists the models only a quality-only board names under `unpriced_models`; the
    /// phone's own list for that surface keeps every one of them.
    func testTheOwnListOfAMediaBoardKeepsItsUnpricedModels() throws {
        let payload = """
        {"api_version": "v1", "attributions": [], "credits": [],
         "boards": [{"id": "arena_text_to_image", "benchmark": "Arena text-to-image", "metric": "elo",
                     "ranking_effort": null, "evidence_date": "2026-10-07", "observed_at": "2026-10-21",
                     "attribution": "LMArena",
                     "standings": [{"model": "gpt-image2", "position": 1, "effort": "unspecified"},
                                   {"model": "flux2-max", "position": 2, "effort": "unspecified"}]}],
         "models": [],
         "unpriced_models": [{"id": "gpt-image2", "display": "GPT-Image-2", "vendor": "OpenAI", "accessibility": null},
                             {"id": "flux2-max", "display": "flux-2-max", "vendor": "Other", "accessibility": null}]}
        """
        let standings = try FetchedStandings(payload: Data(payload.utf8)).standings
        let list = try combineFamily(standings, boards: ["arena_text_to_image"],
                                     asOf: Date(timeIntervalSince1970: 1_792_540_800))
        XCTAssertEqual(list.entries.map(\.model.id), ["gpt-image2", "flux2-max"])
    }
}
