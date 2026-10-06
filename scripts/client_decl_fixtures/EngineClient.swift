// #51: the one network door, which the gate must ALLOW: a connection, and a decoded URL.
import Foundation

func fixtureClientFetches(_ address: URL) async throws -> Data {
    try await URLSession.shared.data(from: address).0
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
}

// The W2 review's M1: a relay through an object the sink holds as a constant, which another file
// can still change (S3), and through a function another file declares (S2b). REFUSED, both.
struct FixtureHeldRelayClient {
    static let relay = NSMutableString()

    func boardsQuery() -> String { (Self.relay as String) + fixtureRelayed() }
}
