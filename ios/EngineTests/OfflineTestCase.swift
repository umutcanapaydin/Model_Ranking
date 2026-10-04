//  #59 -- no Swift test reaches the network.
//
//  A test once built a store on an https address and read it; the read reached the network and the
//  test passed whatever the code did. The Python suite has a network tripwire (`tests/conftest.py`);
//  this is the Swift suite's. Every test class derives from `OfflineTestCase`
//  (`tests/unit/test_swift_tests_offline.py` holds that).

import Foundation
import XCTest

/// The tripwire. Stub until #59's fix installs it.
enum OfflineGuard {
    final class Tripwire: URLProtocol {}
}

/// The base of every test class in this target.
class OfflineTestCase: XCTestCase {}

final class OfflineGuardTests: OfflineTestCase {
    func testEverySessionConfigurationAsksTheTripwireFirst() {
        // A session a test builds for itself, as `EngineClient` does without a stub, is caught too.
        for configuration in [URLSessionConfiguration.default, URLSessionConfiguration.ephemeral] {
            XCTAssertTrue(configuration.protocolClasses?.first == OfflineGuard.Tripwire.self,
                          "\(configuration.protocolClasses ?? [])")
        }
    }
}
