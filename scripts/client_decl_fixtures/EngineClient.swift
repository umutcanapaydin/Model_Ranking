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
