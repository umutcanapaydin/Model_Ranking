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
