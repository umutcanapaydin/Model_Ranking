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

// #107: three more ways to make a URL from text. REFUSED: the parse strategy, the wrapper called
// with `URL`, and a link detector.
func fixtureViewParses(_ typed: String) -> URL? {
    try? URL(typed, strategy: .url)
}

func fixtureViewDecodesThroughAWrapper(_ data: Data) -> URL? {
    fixtureDecode(URL.self, from: data)
}

func fixtureViewFindsLinks(_ typed: String) -> [URL] {
    let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue)
    return detector?.matches(in: typed, range: NSRange(typed.startIndex..., in: typed)).compactMap(\.url) ?? []
}

// The W2 review's B1: arithmetic on a served number through the names it can pass under. REFUSED, each.
func fixtureA1Reassigned(_ standing: Standing) -> Int {
    var place = 0
    place = standing.position
    return place + 1
}

func fixtureServedPlace(_ standing: Standing) -> Int {
    standing.position
}

func fixtureA2Returned(_ standing: Standing) -> Int {
    fixtureServedPlace(standing) + 1
}

extension Standing {
    var fixtureA3Next: Int {
        position + 1
    }
}

func fixtureA5Wrapping(_ standing: Standing) -> Int {
    standing.position &+ 1
}

func fixtureA6Advanced(_ standing: Standing) -> Int {
    standing.position.advanced(by: 1)
}

func fixtureA7Converted(_ standing: Standing) -> Int32 {
    Int32(standing.position) + 1
}

func fixtureA8Unlisted(_ standing: Standing) -> Double {
    (standing.ageDays ?? 0) - 100
}

func fixtureA10Literal(_ standing: Standing) -> Int {
    var total = 0
    for place in [standing.position] {
        total = place + 1
    }
    return total
}

func fixtureA11Tuple(_ standings: [Standing]) -> Int {
    var total = 0
    for (index, place) in standings.map(\.position).enumerated() {
        total = place * index
    }
    return total
}

struct FixtureRanker {
    func rank(_ place: Int) -> Int {
        place + 1
    }
}

func fixtureA12Method(_ standing: Standing) -> Int {
    FixtureRanker().rank(standing.position)
}

func fixtureClosure(_ standings: [Standing]) -> [Int] {
    standings.map(\.position).map { $0 - 1 }
}

// The W2 review's M4: Foundation's sort, keyed on a served number. REFUSED.
func fixtureO1SortsByFoundation(_ standings: [Standing]) -> [Standing] {
    standings.sorted(using: KeyPathComparator(\Standing.position))
}

// The W2 fix's own probes, past the review's list: a condition's binding, a case's binding, a
// memberwise initialiser, a function as a value, a mutating method, a protocol requirement and a
// compound operator. Each REFUSED.
func fixtureIfLet(_ standing: Standing) -> Double {
    if let age = standing.ageDays {
        return age * 2
    }
    return 0
}

func fixtureGuardLet(_ standing: Standing) -> Double {
    guard let age = standing.ageDays else { return 0 }
    return age * 2
}

func fixtureCase(_ standing: Standing) -> Double {
    switch standing.ageDays {
    case let .some(age): return age * 2
    case .none: return 0
    }
}

struct FixturePlaceBox {
    let value: Int
}

func fixtureThroughABox(_ standing: Standing) -> Int {
    let box = FixturePlaceBox(value: standing.position)
    return box.value + 1
}

func fixtureAsAValue(_ standing: Standing) -> Int {
    let served = fixtureServedPlace
    return served(standing) + 1
}

func fixtureAppended(_ standing: Standing) -> Int {
    var places: [Int] = []
    places.append(standing.position)
    return places[0] + 1
}

protocol FixturePlaced {
    var placed: Int { get }
}

extension Standing: FixturePlaced {
    var placed: Int { position }
}

func fixtureByProtocol(_ item: any FixturePlaced) -> Int {
    item.placed + 1
}

func fixtureCompound(_ standing: Standing) -> Int {
    var place = standing.position
    place -= 1
    return place
}
