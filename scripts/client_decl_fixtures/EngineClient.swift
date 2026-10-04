// #51: the one network door, which the gate must ALLOW: a connection, and a decoded URL.
import Foundation

func fixtureClientFetches(_ address: URL) async throws -> Data {
    try await URLSession.shared.data(from: address).0
}

func fixtureClientDecodesAnAddress(_ data: Data) -> [URL] {
    (try? JSONDecoder().decode([URL].self, from: data)) ?? []
}
