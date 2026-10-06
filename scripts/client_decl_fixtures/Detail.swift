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
