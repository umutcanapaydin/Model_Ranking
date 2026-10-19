//  #354 (#351 phase 3): the on-device model is prewarmed when the question field gains focus. Apple asks for a
//  window of at least a second before the question, which typing gives; it saves latency, never accuracy.

import XCTest

@testable import ModelRankingEngine

final class PrewarmTests: OfflineTestCase {
    func testTheTiersHandAPrewarmToTheModelTier() {
        let model = PrewarmRecordingModelTier()
        TieredRouter(model: model, similarity: SilentTier()).prewarm(within: ["coding", "vision"])
        XCTAssertEqual(model.prewarmed, [["coding", "vision"]])
    }

    func testAQuestionSentWithNoPrewarmIsStillReadByTheModel() async {
        let model = PrewarmRecordingModelTier()
        let outcome = await TieredRouter(model: model, similarity: SilentTier())
            .route("which ai is best for my python bugs", within: ["coding"])
        XCTAssertEqual(outcome.tier, .model)
        XCTAssertEqual(outcome.categoryID, "coding")
        XCTAssertEqual(model.prewarmed, [])
    }

    func testOnlyTheFieldGainingFocusWithTheModelReadyPrewarms() {
        XCTAssertTrue(Prewarm.onFocus(from: false, to: true, .available))
        XCTAssertFalse(Prewarm.onFocus(from: true, to: true, .available), "focus kept is not focus gained")
        XCTAssertFalse(Prewarm.onFocus(from: true, to: false, .available))
        for state in [OnDeviceState.downloading, .turnedOff, .notEligible, .unavailable] {
            XCTAssertFalse(Prewarm.onFocus(from: false, to: true, state), "\(state)")
        }
    }
}
