// #51, #58: a fixture that must be REFUSED: a screen file that reaches the file system, and one
// that decodes an optional URL (`decodeIfPresent`, W5 review B1).
import Foundation

func fixtureDetailWrites(_ text: String) {
    _ = FileManager.default.temporaryDirectory
}

struct FixtureBox: Decodable {
    let address: URL?
}

func fixtureDetailDecodesAnOptionalAddress(_ typed: String) -> URL? {
    (try? JSONDecoder().decode(FixtureBox.self, from: Data("{\"address\": \"\(typed)\"}".utf8)))?.address
}

// #107: a generic decode wrapper, declared here and called with `URL` elsewhere. ALLOWED here: it
// makes nothing until a caller names the type.
func fixtureDecode<T: Decodable>(_ type: T.Type, from data: Data) -> T? {
    try? JSONDecoder().decode(type, from: data)
}

// The W2 review's B2, U5: a URL hidden in a dictionary by a generic decode, then a client built on it.
// REFUSED, both: the URL is made outside its files, and the client is built with an address of its own.
func fixtureReadLike<T: Decodable>(_ example: T, from data: Data) -> [String: T]? {
    try? JSONDecoder().decode([String: T].self, from: data)
}

func fixtureDetailRelays(_ typed: String) -> URL? {
    let json = "{\"a\": \"http://127.0.0.1:8080/" + typed + "/\"}"
    guard let address = fixtureReadLike(EngineClient.localDefault, from: Data(json.utf8))?["a"] else { return nil }
    return EngineClient(baseURL: address).boards()
}

// The W2 review's M1, S2b: a function this file declares and a sink calls. Its body reads nothing
// here; the gate refuses the call, since a body another file owns can read anything.
func fixtureRelayed() -> String { "" }

// The second W2 review's B1, P3w: standings built through a protocol requirement their initialiser
// satisfies. REFUSED: a kept type is extended only in its own file, and conforms to no protocol the
// app declares.
protocol FixtureMadeFromBytes {
    init(payload: Data) throws
}

extension FetchedStandings: FixtureMadeFromBytes {}

func fixtureMake<S: FixtureMadeFromBytes>(_ kind: S.Type, _ typed: String) -> S? {
    try? S(payload: Data(typed.utf8))
}

// U10 and P3w's save: a store built on a place of the screen's choosing, and standings saved from
// here. REFUSED, both: only the store's own file builds a store or saves to one.
func fixtureStoreElsewhere(_ place: URL, _ kept: FetchedStandings) {
    StandingsStore(url: place).save(kept, at: Date())
}

// #170: a date of the screen's choosing into the standings file, a 64-bit channel. REFUSED: only the
// store's own file dates what it keeps.
func fixtureScreenDatesTheStore(_ typed: String) -> Int? {
    StandingsStore.onDevice.currentKept(now: Date(timeIntervalSince1970: Double(typed.utf8.count)), fetch: { 0 })
}

// U9: the client's address rewritten through its memory. REFUSED: no file touches memory unsafely.
func fixtureRewrites(_ client: inout EngineClient) {
    withUnsafeMutablePointer(to: &client) { _ in }
}

// #172: routes from the screen's state into the code a sink runs. A stored property's default value,
// which the implicit initialiser runs (REFUSED as the sink's call to an initialiser another file
// declares); a static `let`'s initialiser, which runs on first use (REFUSED); and a closure the screen
// builds and the sink keeps (REFUSED where the sink calls it).
struct FixtureDefaulted {
    let tag = fixtureScreenRelay
}

enum FixtureStatics {
    static let tag = fixtureScreenRelay
}

func fixtureScreenKeeps() -> FixtureKept {
    FixtureKept(make: { fixtureScreenRelay })
}
