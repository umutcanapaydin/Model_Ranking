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
