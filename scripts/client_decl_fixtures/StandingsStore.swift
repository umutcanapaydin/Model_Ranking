// #51: a file the file system is allowed to (D-167), which the gate must ALLOW.
import Foundation

func fixtureStoreFolder() -> URL {
    FileManager.default.temporaryDirectory
}

// #85 (D-180): the store builds standings from its own file, which the gate must ALLOW.
struct FetchedStandings {
    let payload: Data

    init(payload: Data) throws {
        self.payload = payload
    }
}

func fixtureStoreRestores(_ data: Data) -> FetchedStandings? {
    try? FetchedStandings(payload: data)
}

// The W2 review's B2, U3b: a store file may make a file's URL, not the engine's address from text.
// REFUSED: the address made from text, and the client built on it.
func fixtureStoreRelays(_ typed: String) -> URL {
    EngineClient(baseURL: EngineClient.engineURL(from: "http://127.0.0.1:8080/" + typed)).boards()
}
