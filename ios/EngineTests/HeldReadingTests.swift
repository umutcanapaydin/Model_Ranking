//  #132 (M21-W3): D-169's held reading, driven by Swift tests now that it lives in the Engine. The
//  screen's wiring of it (the card's two taps, the field held while "Find a model" answers) stays
//  pinned in `tests/unit/test_ios_client_contract.py` and seen by the UI target.

import XCTest

@testable import ModelRankingEngine

final class HeldReadingTests: OfflineTestCase {
    private func outcome(_ reading: InputReading) -> RoutingOutcome {
        var outcome = RoutingOutcome(categoryID: "assistant", tier: .model, unmeasured: false)
        outcome.reading = reading
        return outcome
    }

    func testASearchIsAnsweredAndAnythingElseIsHeld() {
        XCTAssertNil(HeldReading.holding(outcome(.search), typed: "best model for code"))
        XCTAssertEqual(HeldReading.holding(outcome(.notASearch), typed: "hello"),
                       HeldReading(typed: "hello", outcome: outcome(.notASearch)))
        XCTAssertEqual(HeldReading.holding(outcome(.unsure), typed: "a playlist"),
                       HeldReading(typed: "a playlist", outcome: outcome(.unsure)))
    }

    func testTheCardAsksBackExactlyWhileUnsure() {
        XCTAssertTrue(HeldReading(typed: "x", outcome: outcome(.unsure)).asksBack)
        XCTAssertFalse(HeldReading(typed: "x", outcome: outcome(.notASearch)).asksBack)
    }

    /// "Find a model" answers the held question as a search, on the surface it was routed to.
    func testFindAModelAnswersAsRouted() {
        let held = HeldReading(typed: "x", outcome: outcome(.unsure))
        XCTAssertEqual(held.confirmed.reading, .search)
        XCTAssertEqual(held.confirmed.categoryID, "assistant")
        XCTAssertEqual(held.confirmed.tier, .model)
    }

    /// "No" is exactly the note: the same question, read as not a search.
    func testNoIsTheNote() {
        let held = HeldReading(typed: "x", outcome: outcome(.unsure))
        XCTAssertEqual(held.declined, HeldReading(typed: "x", outcome: outcome(.notASearch)))
        XCTAssertFalse(held.declined.asksBack)
    }
}
