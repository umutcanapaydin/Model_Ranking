//  #59 -- no Swift test reaches the network.
//
//  A test once built a store on an https address and read it; the read reached the network and the
//  test passed whatever the code did. The Python suite has a network tripwire (`tests/conftest.py`);
//  this is the Swift suite's. Every test class derives from `OfflineTestCase`
//  (`tests/unit/test_swift_tests_offline.py` holds that).
//
//  The ways a test can make a request that it catches (measured on macOS 26 before it was written).
//  Not caught: a session built from a bare `URLSessionConfiguration()` (#108), and a test class that
//  is not an `OfflineTestCase` (held by `tests/unit/test_swift_tests_offline.py`, aliases included):
//  - `URLProtocol.registerClass` reaches `URLSession.shared` and `Data(contentsOf:)`, but not a
//    session built on its own configuration, which is what `EngineClient` builds without a stub.
//  - So `URLSessionConfiguration.default` and `.ephemeral` are exchanged for versions that put the
//    tripwire first.
//  - And the `protocolClasses` setter is exchanged for one that appends the tripwire LAST, so a stub
//    session still answers through its stub, and a request the stub declines is caught instead of
//    falling through to the real stack (W5 review M1).
//  The tripwire answers every request it sees with "not connected" and records it; the base's
//  tearDown fails the test that made it. Nothing leaves the machine, and nothing crashes.

import Foundation
import XCTest

enum OfflineGuard {
    /// Every request no stub answered, in the order they were made.
    nonisolated(unsafe) static var attempts: [String] = []
    /// Set when the exchange could not be made; every test then fails saying so, rather than the run
    /// crashing (a crash dialog on the owner's Mac) or passing unguarded.
    nonisolated(unsafe) static var notInstalled: String?
    private static let lock = NSLock()

    static func record(_ request: URLRequest) {
        lock.lock()
        defer { lock.unlock() }
        attempts.append(request.url?.absoluteString ?? "(no URL)")
    }

    /// What was attempted since the last call, and a clean slate.
    static func drain() -> [String] {
        lock.lock()
        defer { lock.unlock() }
        let seen = attempts
        attempts = []
        return seen
    }

    final class Tripwire: URLProtocol {
        override class func canInit(with request: URLRequest) -> Bool { true }
        override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
        override func startLoading() {
            OfflineGuard.record(request)
            client?.urlProtocol(self, didFailWithError: URLError(.notConnectedToInternet))
        }
        override func stopLoading() {}
    }

    /// Once per process: a parallel run starts several, and each installs it from its first class.
    static let installed: Void = {
        URLProtocol.registerClass(Tripwire.self)
        exchange("defaultSessionConfiguration", "offlineDefault", classMethod: true)
        exchange("ephemeralSessionConfiguration", "offlineEphemeral", classMethod: true)
        exchange("backgroundSessionConfigurationWithIdentifier:", "offlineBackground:", classMethod: true)
        exchange("setProtocolClasses:", "offlineSetProtocolClasses:", classMethod: false)
    }()

    private static func exchange(_ original: String, _ replacement: String, classMethod: Bool) {
        let type: AnyClass = URLSessionConfiguration.self
        let lookup = classMethod ? class_getClassMethod : class_getInstanceMethod
        guard let from = lookup(type, NSSelectorFromString(original)),
              let to = lookup(type, NSSelectorFromString(replacement)) else {
            notInstalled = "URLSessionConfiguration.\(original) is gone; #59's tripwire cannot see sessions"
            return
        }
        method_exchangeImplementations(from, to)
    }
}

extension URLSessionConfiguration {
    // After the exchange each name calls the other, so these call the ORIGINAL getter.
    @objc class func offlineDefault() -> URLSessionConfiguration {
        let configuration = offlineDefault()
        configuration.protocolClasses = [OfflineGuard.Tripwire.self] + (configuration.protocolClasses ?? [])
        return configuration
    }

    @objc class func offlineEphemeral() -> URLSessionConfiguration {
        let configuration = offlineEphemeral()
        configuration.protocolClasses = [OfflineGuard.Tripwire.self] + (configuration.protocolClasses ?? [])
        return configuration
    }

    // W5 second review M11: a background configuration, too.
    @objc class func offlineBackground(_ identifier: String) -> URLSessionConfiguration {
        let configuration = offlineBackground(identifier)
        configuration.protocolClasses = [OfflineGuard.Tripwire.self] + (configuration.protocolClasses ?? [])
        return configuration
    }

    // After the exchange this calls the ORIGINAL setter, with the tripwire after whatever was set.
    @objc func offlineSetProtocolClasses(_ classes: [AnyClass]?) {
        var list = classes ?? []
        if !list.contains(where: { $0 == OfflineGuard.Tripwire.self }) {
            list.append(OfflineGuard.Tripwire.self)
        }
        offlineSetProtocolClasses(list)
    }
}

/// The base of every test class in this target.
class OfflineTestCase: XCTestCase {
    override class func setUp() {
        super.setUp()
        OfflineGuard.installed
    }

    // Per test too: a subclass whose `class func setUp()` skipped super would otherwise run unguarded
    // (W5 review M1). Once per process either way.
    override func setUp() {
        super.setUp()
        OfflineGuard.installed
    }

    override func tearDown() {
        let attempts = OfflineGuard.drain()
        XCTAssertNil(OfflineGuard.notInstalled)
        XCTAssertTrue(URLSessionConfiguration.ephemeral.protocolClasses?.first == OfflineGuard.Tripwire.self,
                      "the tripwire was never installed in this process (#59)")
        XCTAssertEqual(attempts, [], "this test reached for the network; route it to a stub (#59)")
        super.tearDown()
    }
}

final class OfflineGuardTests: OfflineTestCase {
    func testEverySessionConfigurationAsksTheTripwireFirst() {
        // A session a test builds for itself, as `EngineClient` does without a stub, is caught too.
        for configuration in [URLSessionConfiguration.default, URLSessionConfiguration.ephemeral,
                              URLSessionConfiguration.background(withIdentifier: "offline-guard-test")] {
            XCTAssertTrue(configuration.protocolClasses?.first == OfflineGuard.Tripwire.self,
                          "\(configuration.protocolClasses ?? [])")
        }
    }

    func testARequestAStubDeclinesIsCaughtToo() async {
        // W5 review M1: a stub session sets its own protocols, and a request its stub declines fell
        // through to the real stack. Loopback's discard port, so nothing leaves the machine either way.
        let address = URL(string: "http://127.0.0.1:9/declined")!
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [DecliningStub.self]
        _ = try? await URLSession(configuration: configuration).data(from: address)
        XCTAssertEqual(OfflineGuard.drain(), [address.absoluteString])
    }

    func testARequestNoStubAnswersIsCaughtWithoutLeavingTheMachine() async {
        // The shape of the test #59 was raised for: a read of an https address inside a test.
        let address = URL(string: "https://example.invalid/standings.json")!
        let session = URLSession(configuration: .ephemeral)
        do {
            _ = try await session.data(from: address)
            XCTFail("the request was answered")
        } catch {
            XCTAssertEqual((error as? URLError)?.code, .notConnectedToInternet, "\(error)")
        }
        _ = try? Data(contentsOf: address)
        XCTAssertEqual(OfflineGuard.drain(), [address.absoluteString, address.absoluteString])
    }
}

/// A stub that answers nothing: every request falls past it.
final class DecliningStub: URLProtocol {
    override class func canInit(with request: URLRequest) -> Bool { false }
}
