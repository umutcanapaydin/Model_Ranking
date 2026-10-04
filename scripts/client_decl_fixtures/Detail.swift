// #51: a fixture that must be REFUSED: a screen file that reaches the file system.
import Foundation

func fixtureDetailWrites(_ text: String) {
    _ = FileManager.default.temporaryDirectory
}
