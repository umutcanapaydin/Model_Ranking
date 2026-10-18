import Foundation
import XCTest
@testable import ModelRankingEngine

/// #309 (D-209 clause 8): the network observer covers the whole test, set-up and tear-down included.
final class WholeTestObserverTests: OfflineTestCase {
    func testARequestInATearDownThatSkipsSuperFailsItsOwnTest() {
        let probe = SkipsSuperInTearDown(selector: #selector(SkipsSuperInTearDown.reachesInItsTearDown))
        probe.run()
        let leftover = OfflineGuard.drain()
        XCTAssertEqual(leftover, [], "the request outlived its test and would fail the next one")
        XCTAssertGreaterThan(probe.testRun?.failureCount ?? 0, 0, "the test that reached for the network passed")
    }
}
