// #60 (G-2): the fixture's served numbers, decoded from the engine as the app's `Models.swift` does.
// Every numeric field a decoded type stores is a served number, listed or not (the W2 review's B1).
import Foundation

struct Standing: Decodable {
    let model: String
    let position: Int
    let score: Double
    let ageDays: Double?
}

struct Pick: Decodable {
    let blendedPerM: Double
}

// #85 (D-180): the standings the app keeps, declared here as the app declares them, outside both
// sinks. The sinks may build them; the code that runs when they do is held as the sinks are.
struct FetchedStandings {
    let payload: Data

    init(payload: Data) throws {
        self.payload = fixtureStamped(payload)
    }
}

// The second W2 review's S5: a function the standings' initialiser runs, reading a global the screen
// sets. REFUSED, the read: a privacy sink runs this code.
nonisolated(unsafe) var fixtureKeptNote = ""

func fixtureStamped(_ payload: Data) -> Data {
    payload + Data(fixtureKeptNote.utf8)
}

// S5b: a decoding witness reading the same global. REFUSED: a decoder runs it without naming it.
struct FixtureNoted: Decodable {
    let note: String

    init(from decoder: Decoder) throws {
        note = fixtureKeptNote
    }
}

// #297 (D-206 clause 4): the types a kept answer is, declared as the app declares them. Only a decode builds
// one, in the engine client or in the kept answers' read-back; the synthesised decoders here run only inside
// such a decode, which the gate must ALLOW.
struct Query: Codable {
    let task: String
}

struct Recommendation: Codable {
    let query: Query
}

struct Category: Codable {
    let id: String
}

struct CategoryList: Codable {
    let categories: [Category]
}
