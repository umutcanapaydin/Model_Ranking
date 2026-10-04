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
