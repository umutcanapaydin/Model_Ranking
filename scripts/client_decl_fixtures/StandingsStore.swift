// #51: a file the file system is allowed to (D-167), which the gate must ALLOW.
import Foundation

func fixtureStoreFolder() -> URL {
    FileManager.default.temporaryDirectory
}
