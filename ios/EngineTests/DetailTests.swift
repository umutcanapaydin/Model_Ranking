//  M15-W2 — the detail screen's facts (REQ-DTL-001/002).
//
//  The screen renders what these tests cover and chooses no words of its own, which is the only
//  reason a view this project cannot compile in CI is allowed to exist at all.

import XCTest

@testable import ModelRankingEngine

/// A served row, as the two real ones arrive. Written here rather than decoded so a test names the
/// values it depends on; `testTheServedTypesAreDetailSubjects` holds it to the real shapes.
private struct Subject: DetailSubject {
    var model = "Claude Opus 5"
    var vendor = "Anthropic"
    var score = 1507.6
    var metric = "elo"
    var secondaryScore: Double?
    var blendedPerM = 7.5
    var inputPerM = 5.0
    var outputPerM = 25.0
    var evidenceDate: String? = "2026-09-13"
    var harness = "arena-crowd"
    var effort: String?
}

final class DetailFactTests: XCTestCase {
    private func facts(
        _ subject: Subject,
        anchor: Double? = 1400,
        margin: Double? = 8,
        second: String? = nil,
        age: Int? = nil,
        _ language: Language = .english
    ) -> [DetailFact] {
        detailFacts(
            model: subject,
            benchmark: "Arena text",
            anchor: anchor,
            closeCallMargin: margin,
            secondaryBenchmark: second,
            secondaryAgeDays: age,
            in: language
        )
    }

    private func value(_ facts: [DetailFact], _ label: String) -> String? {
        facts.first { $0.label == label }?.value
    }

    /// REQ-DTL-002, the whole reason this screen exists: D-143 took `Elo` off the card, and a
    /// reader who wants it has to be able to find it somewhere.
    func testTheUnitTheCardHidesComesBackHere() {
        let lines = facts(Subject())

        // 1507.6 against an anchor of 1400 is 65.008, and the card prints one decimal. Written as
        // "65" in the first draft and red on the owner's run: **the test was wrong, not the
        // product** — a test that rounds differently from the screen is a second account of the
        // number, which is the defect class this file exists to prevent.
        XCTAssertEqual(value(lines, "Score"), "Score 65.0 / 100")
        XCTAssertEqual(value(lines, "Measured value"), "1507.6 Elo")
        XCTAssertTrue(
            lines.contains { $0.note?.contains("Arena text") == true },
            "the native value does not say which board it is on"
        )
    }

    /// ...and it does NOT repeat itself where the card already prints the unit. A percentage card
    /// says `83.5 / 100` and the board's own number is the same number.
    func testAPercentageIsNotRestatedAsAMeasuredValue() {
        var subject = Subject()
        subject.score = 83.5
        subject.metric = "% resolved"

        XCTAssertEqual(value(facts(subject, anchor: nil), "Score"), "Score 83.5 / 100")
        XCTAssertNil(value(facts(subject, anchor: nil), "Measured value"))
    }

    /// ECI prints no score on the card at all (D-140). The detail screen is then the only place
    /// its number exists, so it must appear even though nothing was converted.
    func testARankOnlyMetricStillStatesItsNumberHere() {
        var subject = Subject()
        subject.score = 161.7
        subject.metric = "eci"

        let lines = facts(subject, anchor: nil)
        XCTAssertNil(value(lines, "Score"))
        XCTAssertEqual(value(lines, "Measured value"), "161.7 ECI")
    }

    /// REQ-UNC-003: an undated board is NAMED as undated. "Recently" would be this client
    /// inventing a date the engine refused to state.
    func testAnUndatedBoardSaysItIsUndated() {
        var subject = Subject()
        subject.evidenceDate = nil

        let measured = facts(subject).first { $0.label == "Measured on" }
        XCTAssertEqual(measured?.value, "Arena text")
        XCTAssertEqual(measured?.note, "this board does not date its results")
        XCTAssertFalse(measured?.note?.contains("2026") == true)
    }

    /// Review M-1: the date is the date the board was RUN, which is what `/v1` sends and what the
    /// card says. "Published" is a stronger claim than the engine makes, and two words for one
    /// served field is two accounts of it.
    func testTheDateIsTheRunDateAndNothingStronger() {
        let measured = facts(Subject()).first { $0.label == "Measured on" }

        XCTAssertEqual(measured?.note, "run on 2026-09-13")
        XCTAssertFalse(measured?.note?.contains("publish") == true)
    }

    /// ...and a date string this build cannot read falls through to the undated notice instead of
    /// being printed. `evidence_date: "unknown"` rendered "result published unknown" before.
    func testAnUnreadableDateIsNotPrintedAsADate() {
        for broken in ["unknown", "2026-13-45", "soon", "20260913"] {
            var subject = Subject()
            subject.evidenceDate = broken

            let measured = facts(subject).first { $0.label == "Measured on" }
            XCTAssertEqual(
                measured?.note, "this board does not date its results", "date: \(broken)"
            )
        }
    }

    /// Review M-6: a board name the card never passed is not a fact. No name, no line.
    func testAnEmptyBoardNameProducesNoMeasuredLine() {
        let lines = detailFacts(
            model: Subject(),
            benchmark: "",
            anchor: 1400,
            closeCallMargin: 8,
            secondaryBenchmark: nil,
            secondaryAgeDays: nil,
            in: .english
        )
        XCTAssertNil(lines.first { $0.label == "Measured on" })
        XCTAssertFalse(lines.contains { $0.value.trimmingCharacters(in: .whitespaces).isEmpty })
    }

    /// Review M-7: `priceTag` renders "—" for a price the engine could not resolve, and this file
    /// forbids a line that states a measurement it does not have. A dash reads as free to someone.
    func testAModelWithNoResolvedPriceGetsNoPriceLine() {
        for missing in [0.0, -1.0, Double.nan] {
            var subject = Subject()
            subject.blendedPerM = missing

            let lines = facts(subject)
            XCTAssertNil(lines.first { $0.label == "Price" }, "price: \(missing)")
            XCTAssertFalse(lines.contains { $0.value == "—" }, "price: \(missing)")
        }
    }

    /// REQ-DTL-001: price returns as an ATTRIBUTE here, in both the form a buyer checks and the
    /// form everyone else can hold.
    func testPriceIsStatedTwiceOnPurpose() {
        let lines = facts(Subject())

        XCTAssertEqual(value(lines, "Price"), "$7.5/1M")
        XCTAssertEqual(value(lines, "Input / output"), "$5 / $25 per 1M")
        XCTAssertTrue(lines.first { $0.label == "Price" }?.note?.contains("pages") == true)
    }

    /// D-138's margin, as a number rather than as the card's sentence.
    func testTheTieMarginIsShownOnTheBoardsOwnScale() {
        XCTAssertEqual(value(facts(Subject()), "Too close to call"), "8 Elo")
        XCTAssertNil(value(facts(Subject(), margin: nil), "Too close to call"))
    }

    /// The second board is evidence, and it carries its age (D-139). Absent without a score.
    func testTheSecondBoardAppearsOnlyWithItsOwnScore() {
        var subject = Subject()
        XCTAssertNil(value(facts(subject, second: "Aider Polyglot", age: 40), "Second measurement"))

        subject.secondaryScore = 71.2
        let lines = facts(subject, second: "Aider Polyglot", age: 40)
        XCTAssertEqual(value(lines, "Second measurement"), "71.2 · Aider Polyglot")
        XCTAssertEqual(lines.first { $0.label == "Second measurement" }?.note, "last run 40 days ago")
    }

    /// Nothing here is invented when the engine sent nothing — and nothing served is dropped
    /// either. Review N-2: the harness alone is still a fact, so an absent effort hides neither.
    func testTheHarnessIsShownWithOrWithoutAnEffort() {
        XCTAssertEqual(value(facts(Subject()), "Run at"), "arena-crowd")
        XCTAssertEqual(
            facts(Subject()).first { $0.label == "Run at" }?.note, "this board runs at one level"
        )

        var subject = Subject()
        subject.effort = "high"
        XCTAssertEqual(value(facts(subject), "Run at"), "arena-crowd · high")
        XCTAssertFalse(facts(subject).contains { $0.value.isEmpty || $0.value == "—" })
    }

    /// Review N-1: a SCORE's unit is not a MARGIN's unit. `marginUnit` renders a percentage
    /// board's margin as "points", and `83.5 points` is a different measurement from `83.5 %`.
    func testTheNativeValueUsesTheScoresUnitNotTheMargins() {
        var subject = Subject()
        subject.score = 161.7
        subject.metric = "eci"
        XCTAssertEqual(value(facts(subject, anchor: nil), "Measured value"), "161.7 ECI")

        XCTAssertEqual(value(facts(Subject()), "Measured value"), "1507.6 Elo")
        XCTAssertFalse(
            facts(Subject()).contains { $0.value.contains("points") },
            "a score is labelled with the margin's unit"
        )
    }

    /// Every line is Turkish in Turkish — the half-translated screen W-085 caught, one screen
    /// later. **Rewritten after the W2 review**, whose measurement was blunt: the first version
    /// checked that labels were non-empty and named four English ones, so all seven NOTES could be
    /// hard-coded to English and it stayed green. A denylist of four strings is a denylist wearing
    /// better clothes, which is what this file says about its own predecessors.
    ///
    /// The honest form compares the two languages line by line: same subject, same order, and no
    /// label or note may be the English one. Add a line in one language only and this fails too.
    func testNoLineSurvivesInEnglishOnTheTurkishScreen() {
        var subject = Subject()
        subject.secondaryScore = 71.2
        subject.effort = "high"
        let english = facts(subject, second: "Aider Polyglot", age: 40, .english)
        let turkish = facts(subject, second: "Aider Polyglot", age: 40, .turkish)

        XCTAssertEqual(english.count, turkish.count, "the two languages show different lines")
        XCTAssertFalse(english.isEmpty)
        for (left, right) in zip(english, turkish) {
            XCTAssertNotEqual(left.label, right.label, "label `\(left.label)` is not translated")
            if let note = left.note {
                XCTAssertNotEqual(note, right.note, "the note under `\(left.label)` is not translated")
                XCTAssertNotNil(right.note)
            }
        }
        XCTAssertEqual(value(turkish, "Puan"), "Puan 65.0 / 100")
        XCTAssertEqual(value(turkish, "Ölçülen değer"), "1507.6 Elo")
        XCTAssertTrue(UIText.detailCaveat(.turkish).contains("kıyaslanamaz"))

        // Review M-3: `per 1M` was English prose on the Turkish screen, and it is the only free
        // "per" in the client -- `priceTag`'s `$7.5/1M` is a currency format and stays as it is.
        XCTAssertFalse(
            value(turkish, "Giriş / çıkış")?.contains("per") == true, "`per 1M` was not translated"
        )
    }

    /// The two served types really do satisfy the protocol this screen takes — the conformance,
    /// not a copy of their fields, is what makes one screen serve a pick and a ranking row.
    func testTheServedTypesAreDetailSubjects() {
        XCTAssertTrue((Pick.self as Any.Type) is DetailSubject.Type)
        XCTAssertTrue((RankedModel.self as Any.Type) is DetailSubject.Type)
    }
}
