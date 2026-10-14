// #246 (G-13): a store makes a URL from text and loads it, which the gate must REFUSE: the stores make
// a URL only from the file system's folders (`STORE_FOUNDATION_ALLOWED`, `URL_MADE_BY_NAME`).
import Foundation

func fixtureStoreLoad(_ typed: String) -> Data? {
    let target: URL? = try? .init("ht" + "tps://example.invalid/?q=" + typed, strategy: .url)
    guard let target else { return nil }
    return try? Data(contentsOf: target)
}

// The backlog-gates review's M2: the same, through a parse strategy. REFUSED: it is off the store's list.
func fixtureStoreParse(_ typed: String) -> Data? {
    guard let target = try? URL.ParseStrategy().parse("ht" + "tps://example.invalid/?q=" + typed) else { return nil }
    return try? Data(contentsOf: target)
}
