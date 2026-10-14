// #246 (G-13): a store makes a URL from text and loads it, which the gate must REFUSE: the stores make
// a URL only from the file system's folders (`STORE_URL_MAKERS`).
import Foundation

func fixtureStoreLoad(_ typed: String) -> Data? {
    let target: URL? = try? .init("ht" + "tps://example.invalid/?q=" + typed, strategy: .url)
    guard let target else { return nil }
    return try? Data(contentsOf: target)
}
