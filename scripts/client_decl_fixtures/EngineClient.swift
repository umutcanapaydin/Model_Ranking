// #51: the one network door, which the gate must ALLOW: a connection, and a decoded URL.
import Foundation

func fixtureClientFetches(_ address: URL) async throws -> Int64 {
    try await URLSession(configuration: .ephemeral).bytes(from: address, delegate: nil).1.expectedContentLength
}

func fixtureClientDecodesAnAddress(_ data: Data) -> [URL] {
    (try? JSONDecoder().decode([URL].self, from: data)) ?? []
}

// #85 (D-180): the M17 relay, P2. A sink file holding mutable state anyone can set, and reading the
// screen's. REFUSED, both. The quiet client beside it holds only constants, a computed property and
// a function's local, which the gate must ALLOW.
struct FixtureRelayClient {
    nonisolated(unsafe) static var tag = ""

    func boardsQuery() -> String { Self.tag + fixtureScreenRelay }
}

struct FixtureQuietClient {
    static let limit = 4
    static var computed: Int { limit + 1 }
    let host: String

    func build() -> String {
        var parts = [host]
        parts.append("v1/boards")
        return parts.joined(separator: "/")
    }
}

// #85 (D-180, the W2 review's B2): the client and how its address is made. Only this file may build a
// client with an address of its own, or make one from text; the app builds `EngineClient()`.
struct EngineClient {
    let baseURL: URL

    init() {
        self.init(baseURL: EngineClient.localDefault)
    }

    init(baseURL: URL, session: URLSession? = nil) {
        self.baseURL = baseURL
    }

    static let localDefault = URL(string: "http://127.0.0.1:8080")!

    static func engineURL(from raw: String) -> URL {
        URL(string: raw) ?? localDefault
    }

    func boards() -> URL {
        baseURL
    }

    func recommendation(task: String, budget: String) -> URL {
        baseURL.appendingPathComponent(task + budget)
    }
}

// The W2 review's M1: a relay through an object the sink holds as a constant, which another file
// can still change (S3), and through a function another file declares (S2b). REFUSED, both.
struct FixtureHeldRelayClient {
    static let relay = NSMutableString()

    func boardsQuery() -> String { (Self.relay as String) + fixtureRelayed() }
}

// #172: the sink's half of each route. REFUSED: a default value, a static initialiser and a kept
// closure, each reading the screen's state; and Foundation's shared state, read in the sink itself.
struct FixtureKept {
    let make: () -> String
}

struct FixtureRoutesClient {
    func boardsDefaulted() -> String { FixtureDefaulted().tag }
    func boardsStatic() -> String { FixtureStatics.tag }
    func boardsKept(_ kept: FixtureKept) -> String { kept.make() }
    func boardsThreadState() -> String { (Thread.main.threadDictionary["q"] as? String) ?? "" }
    func boardsNotified() -> String {
        NotificationCenter.default.post(name: Notification.Name("q"), object: nil)
        return ""
    }
}

// The M21-W3 review's B1: Foundation's process-wide state read in a sink, and another file's mutable
// containers held in constants. REFUSED, each: a sink references only the Foundation declarations on
// its list, and reads no constant of another file's that holds an object.
struct FixtureProcessStateClient {
    func threadName() -> String { Thread.main.name ?? "" }
    func processName() -> String { ProcessInfo.processInfo.processName }
    func queueName() -> String { OperationQueue.main.name ?? "" }
    func zone() -> String { NSTimeZone.default.identifier }
    func boxed() -> String { fixtureScreenBox as String }
    func shelved() -> Int { FixtureShelf.box.count }
}
