//  Every screen sentence in both languages (#127, from the M18-W3 Tester's K10).
//
//  At `93040ac`, 86 of `Language.swift`'s lines ran in no test: the headline, the gap register's
//  title and buttons, "Loading", the privacy line and more. #63's finding 2, English on the Turkish
//  screen, could come back in any of them unseen. This walks every `UIText` sentence, as
//  `testEveryComposedNoticeDiffersFromItsEnglish` walks the notices. The table is held to the
//  functions `UIText` declares by `test_ios_client_contract.py`, so a sentence added later without a
//  row here fails a gate.

import XCTest

@testable import ModelRankingEngine

final class UITextLanguageTests: OfflineTestCase {
    /// One row per `UIText` function, named as it is declared. A function that takes a value is
    /// given one it knows: an unknown surface or label falls back to the engine's English on purpose.
    var sentences: [(String, (Language) -> String?)] {
        let chinese = Refinements.table[0]
        return [
            ("metric", { UIText.metric("% resolved", $0) }),
            ("title", { UIText.title($0) }),
            ("askPlaceholder", { UIText.askPlaceholder($0) }),
            ("filterPlaceholder", { UIText.filterPlaceholder($0) }),
            ("seeAll", { UIText.seeAll(12, eligible: 5, $0) }),
            ("pickLabel", { UIText.pickLabel("best_quality", $0) }),
            ("change", { UIText.change($0) }),
            ("showing", { UIText.showing($0) }),
            ("send", { UIText.send($0) }),
            ("gapsTitle", { UIText.gapsTitle($0) }),
            ("noGaps", { UIText.noGaps($0) }),
            ("clearGaps", { UIText.clearGaps($0) }),
            ("loading", { UIText.loading($0) }),
            ("heroTitle", { UIText.heroTitle($0) }),
            ("heroSubtitle", { UIText.heroSubtitle($0) }),
            ("questionEyebrow", { UIText.questionEyebrow($0) }),
            ("privateQuestion", { UIText.privateQuestion($0) }),
            ("noPicks", { UIText.noPicks($0) }),
            ("noAnswer", { UIText.noAnswer($0) }),
            ("engineAddress", { UIText.engineAddress($0, "http://127.0.0.1:8080") }),
            ("retry", { UIText.retry($0) }),
            ("noMatches", { UIText.noMatches($0) }),
            ("noMatchesHint", { UIText.noMatchesHint($0) }),
            ("openEvidence", { UIText.openEvidence($0) }),
            ("detailTitle", { UIText.detailTitle($0) }),
            ("detailCaveat", { UIText.detailCaveat($0) }),
            ("chooseSurface", { UIText.chooseSurface($0) }),
            ("alternatives", { UIText.alternatives($0) }),
            ("closestMeasured", { UIText.closestMeasured($0) }),
            ("surfacesUnavailable", { UIText.surfacesUnavailable($0) }),
            ("surfaceBlurb", { UIText.surfaceBlurb("coding", $0) }),
            ("gapsPurpose", { UIText.gapsPurpose($0) }),
            ("gapsButton", { UIText.gapsButton($0) }),
            ("surface", { UIText.surface(id: "coding", engineTitle: "Coding", $0) }),
            ("refinementName", { UIText.refinementName(chinese, $0) }),
            ("combinedTitle", { UIText.combinedTitle($0) }),
            ("combinedNote", { UIText.combinedNote(models: 4, boards: 2, $0) }),
            ("combinedEmpty", { UIText.combinedEmpty($0) }),
            ("alsoCounting", { UIText.alsoCounting($0) }),
            ("removedRefinements", { UIText.removedRefinements($0) }),
            ("combinedEffortNote", { UIText.combinedEffortNote(efforts: ["high", "max"], $0) }),
            ("boardEfforts", { UIText.boardEfforts(["high"], $0) }),
            ("boardDate", { UIText.boardDate(.measured("2026-09-24"), $0) }),
            ("chipAction", { UIText.chipAction(chinese, removed: false, $0) }),
            ("tiedPlaces", { UIText.tiedPlaces($0) }),
            ("olderBoards", { UIText.olderBoards(["SWE-bench Verified"], $0) }),
            ("onDeviceCaption", { UIText.onDeviceCaption(true, $0) }),
            ("primaryOnItsOwn", { UIText.primaryOnItsOwn($0) }),
            ("backToCombined", { UIText.backToCombined($0) }),
            ("notASearchNote", { UIText.notASearchNote($0) }),
            ("askBack", { UIText.askBack($0) }),
            ("askBackFind", { UIText.askBackFind($0) }),
            ("askBackNo", { UIText.askBackNo($0) }),
            ("accessFilter", { UIText.accessFilter($0) }),
            ("accessFilterCount", { UIText.accessFilterCount(shown: 3, of: 10, $0) }),
            ("stalePhoneCopy", { UIText.stalePhoneCopy(days: 3, $0) }),
            ("showAll", { UIText.showAll(12, $0) }),
            ("showFewer", { UIText.showFewer($0) }),
            ("seeTheBoards", { UIText.seeTheBoards($0) }),
            ("boardsBehind", { UIText.boardsBehind($0) }),
            ("placeOn", { UIText.placeOn("SWE-bench Verified", place: 2, $0) }),
        ]
    }

    func testEveryScreenSentenceIsSaidInBothLanguages() {
        for (name, compose) in sentences {
            let english = compose(.english)
            let turkish = compose(.turkish)
            XCTAssertFalse((english ?? "").trimmingCharacters(in: .whitespaces).isEmpty, "\(name): no English")
            XCTAssertFalse((turkish ?? "").trimmingCharacters(in: .whitespaces).isEmpty, "\(name): no Turkish")
            XCTAssertNotEqual(turkish, english, "\(name): the Turkish reader is given the English")
        }
    }

    func testTheTableNamesEachSentenceOnce() {
        let names = sentences.map(\.0)
        XCTAssertEqual(Set(names).count, names.count, "a sentence is listed twice")
    }

    /// The fix Tester's T1 (#127). The table gives each function one input, so a sentence's other
    /// branches went unwalked, and a sentence that carries a value the language changes (a date, an
    /// effort, a refinement's name) differed from its English even with an English frame around the
    /// Turkish value. Here every other branch is walked, each with a value both languages print
    /// alike: a date this build cannot read, an effort and a refinement it does not know.
    func testEveryBranchAndFrameIsSaidInBothLanguages() {
        let unnamed = Refinement(value: "zz-unnamed", kind: .language, board: "zz", surfaces: [], reason: "")
        let frames: [(String, (Language) -> String?)] = [
            ("boardDate", { UIText.boardDate(.measured("zz-day"), $0) }),
            ("boardDate", { UIText.boardDate(.readOn("zz-day"), $0) }),
            ("boardDate", { UIText.boardDate(.unknown, $0) }),
            ("combinedEffortNote", { UIText.combinedEffortNote(efforts: ["zz-effort"], $0) }),
            ("boardEfforts", { UIText.boardEfforts(["zz-effort"], $0) }),
            ("chipAction", { UIText.chipAction(unnamed, removed: false, $0) }),
            ("chipAction", { UIText.chipAction(unnamed, removed: true, $0) }),
            ("seeAll", { UIText.seeAll(12, eligible: nil, $0) }),
            ("seeAll", { UIText.seeAll(12, eligible: 12, $0) }),
            ("pickLabel", { UIText.pickLabel("best_value", $0) }),
            ("pickLabel", { UIText.pickLabel("budget_pick", $0) }),
        ]
        for (index, (name, compose)) in frames.enumerated() {
            let english = compose(.english)
            let turkish = compose(.turkish)
            XCTAssertFalse((turkish ?? "").trimmingCharacters(in: .whitespaces).isEmpty, "\(name) #\(index): no Turkish")
            XCTAssertNotEqual(turkish, english, "\(name) #\(index): the Turkish reader is given the English")
        }
    }
}
