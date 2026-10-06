// #51, #58: a fixture `client_decl_gate.py --self-test` compiles. It must be REFUSED: a view that
// opens a connection, and a view that decodes a URL out of text (the security slice's S1).
import Foundation

func fixtureViewFetches(_ address: URL) async throws -> Data {
    try await URLSession.shared.data(from: address).0
}

func fixtureViewDecodesAnAddress(_ typed: String) -> [URL] {
    let json = Data("[\"https://example.invalid/?q=\(typed)\"]".utf8)
    return (try? JSONDecoder().decode([URL].self, from: json)) ?? []
}

// #85 (D-180): the screen's half of a relay through shared state, and P3, the typed question made
// into standings. The sink file's read of this global and the standings built here are REFUSED.
nonisolated(unsafe) var fixtureScreenRelay = ""

func fixtureViewRelays(_ typed: String) {
    fixtureScreenRelay = typed
}

func fixtureViewKeepsTheQuestion(_ typed: String) -> FetchedStandings? {
    try? FetchedStandings(payload: Data(typed.utf8))
}

// #60 (G-2): arithmetic on a served position through another name, the M17-W4 review's R4.
// REFUSED: the screen ranks nothing.
func fixtureViewRanksByHand(_ standing: Standing) -> Int {
    let place = standing.position
    return place + 1
}
