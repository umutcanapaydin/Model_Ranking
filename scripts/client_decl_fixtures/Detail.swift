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
