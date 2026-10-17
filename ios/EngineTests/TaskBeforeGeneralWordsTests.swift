import XCTest
@testable import ModelRankingEngine

/// #295 (D-208): a Turkish verb clause right before "yapay zeka" names the task; a description does not.
/// Turkish letters are written as escapes, so this file stays ASCII (rule L1).
final class TaskBeforeGeneralWordsTests: OfflineTestCase {
    func testAnActiveParticipleWithItsObjectNamesATask() {
        for question in ["taray\u{131}c\u{131}mda benim yerime al\u{131}\u{15f}veri\u{15f} yapacak bir yapay zeka var m\u{131}",
                         "kod yazan yapay zeka hangisi", "resim \u{e7}izebilen bir yapay zeka \u{f6}nerir misin",
                         "matematik sorusu \u{e7}\u{f6}zecek yapay zek\u{e2}"] {
            XCTAssertTrue(CategoryHints.namesTaskBeforeGeneralWords(question), question)
        }
    }

    func testADescriptionOrNoClauseNamesNoTask() {
        for question in ["en iyi yapay zeka hangisi", "hangi yapay zeka daha iyi", "\u{fc}cretsiz yapay zeka var m\u{131}",
                         "en son \u{e7}\u{131}kan yapay zeka hangisi", "en \u{e7}ok kullan\u{131}lan yapay zeka",
                         "\u{fc}cretsiz olan bir yapay zeka var m\u{131}", "yeni \u{e7}\u{131}kan yapay zeka", "yapay zeka nedir"] {
            XCTAssertFalse(CategoryHints.namesTaskBeforeGeneralWords(question), question)
        }
    }

    func testTheGeneralWordsAreTakenOutAndNothingElse() {
        XCTAssertEqual(CategoryHints.withoutGeneralWords("al\u{131}\u{15f}veri\u{15f} yapacak bir yapay zeka var m\u{131}"),
                       "al\u{131}\u{15f}veri\u{15f} yapacak bir var m\u{131}")
        XCTAssertEqual(CategoryHints.withoutGeneralWords("kod yazan yapay zek\u{e2}?"), "kod yazan")
        XCTAssertEqual(CategoryHints.withoutGeneralWords("yapay olarak"), "yapay olarak")
    }
}
