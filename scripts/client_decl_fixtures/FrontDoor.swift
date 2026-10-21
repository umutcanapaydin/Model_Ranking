// #246 (G-13): a store makes a URL from text and loads it, which the gate must REFUSE: the stores make
// a URL only from the file system's folders (`STORE_FOUNDATION_ALLOWED`, `URL_MADE_BY_NAME`).
import Foundation

func fixtureStoreLoad(_ typed: String) -> Data? {
    let target: URL? = try? .init("ht" + "tps://example.invalid/?q=" + typed, strategy: .url)
    guard let target else { return nil }
    return try? Data(contentsOf: target)
}

// The backlog-gates review round 1's M2: the same, through a parse strategy. REFUSED: it is off the store's list.
func fixtureStoreParse(_ typed: String) -> Data? {
    guard let target = try? URL.ParseStrategy().parse("ht" + "tps://example.invalid/?q=" + typed) else { return nil }
    return try? Data(contentsOf: target)
}

// #242 (G-13; the backlog-gates review rounds 2 and 3, M1; #276): a store's URL made by a generic helper of its
// own, its type given and inferred, through a `typealias` of `URL`, and by a cast; and a read of anything but the
// store's own `url`. REFUSED, each: a store makes a URL only from the file manager's folders, and reads only its
// own file.
typealias FixtureAddress = URL

func fixtureStoreHelper<T: Decodable>(_ type: T.Type, _ data: Data) -> T? {
    try? JSONDecoder().decode(type, from: data)
}

func fixtureStoreInferred<T: Decodable>(_ data: Data) -> T? {
    try? JSONDecoder().decode(T.self, from: data)
}

func fixtureStoreGeneric(_ data: Data, _ value: Any) -> [Data?] {
    let given = fixtureStoreHelper([URL].self, data)?.first
    let inferred: URL? = fixtureStoreInferred(data)
    let cast = value as? URL
    return [given, inferred, cast].map { $0.flatMap { try? Data(contentsOf: $0) } }
}

// The register's store, as the app declares it: it reads only its own `url`, built only here. ALLOWED: `load()`.
// REFUSED: the #276 shape, a URL decoded through an alias and bound to `url` between the guard and the read.
struct GapRegisterStore {
    let url: URL

    func load() -> Data? {
        guard url.isFileURL else { return nil }
        return try? Data(contentsOf: url)
    }

    func loadShadowed(_ data: Data) -> Data? {
        guard url.isFileURL, let url = try? JSONDecoder().decode(FixtureAddress.self, from: data) else { return nil }
        return try? Data(contentsOf: url)
    }
}

// #242 (G-13): a function of the store's own file that takes a URL from its caller and builds the store on it, so
// another file chooses the address though the initialiser is called here. REFUSED at the parameter.
extension GapRegisterStore {
    static func fixtureAt(_ place: URL) -> GapRegisterStore {
        GapRegisterStore(url: place)
    }
}

// #242, the security review's M2: the register's store built on a URL read through a key path off another file's
// type. REFUSED: a URL-typed declaration of another file, read by any form, is received, not made.
func fixtureStoreKeyPath(_ held: FixtureAddressHolder) -> GapRegisterStore {
    GapRegisterStore(url: held[keyPath: \FixtureAddressHolder.address])
}

// #242, the security review's round 2, M2: the same read with the key path bound to a name first. REFUSED: a store
// reads a URL through a key path only when the key path is written in place, where the gate can read its members.
func fixtureStoreKeyPathHeld(_ held: FixtureAddressHolderAgain) -> GapRegisterStore {
    let path = \FixtureAddressHolderAgain.address
    return GapRegisterStore(url: held[keyPath: path])
}
