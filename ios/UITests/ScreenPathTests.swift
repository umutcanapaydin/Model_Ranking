//  D-175 -- the screen's paths, driven in the simulator against a local engine. Run with
//  `make ui-test`, which starts the engine on 127.0.0.1:8090 and builds the app for it.
//
//  Routing is scripted (D-175 clause 3): the model tier answers from the table below, through the
//  model's own boundary, so a path never depends on the on-device model's reading. Assertions are on
//  the accessibility tree; each test also attaches what it saw, as evidence (#63).

import XCTest

final class ScreenPathTests: XCTestCase {
    private var app: XCUIApplication!

    /// What the model tier answers, per question (the generation schema's field names).
    private let routing: [String: [String: String]] = [
        "Which model writes code best?": ["surface": "coding", "language": "none", "domain": "none"],
        "Translate my letter into French": ["surface": "assistant", "language": "french", "domain": "none"],
    ]

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        let table = (try? JSONSerialization.data(withJSONObject: routing)).flatMap { String(data: $0, encoding: .utf8) }
        app.launchArguments = ["-language", "en", "-UITestRouting", table ?? "{}"]
        app.launch()
        XCTAssertTrue(field("question").waitForExistence(timeout: 30), "the screen never loaded")
        // The engine's first answer: a card's way into its evidence.
        XCTAssertTrue(app.buttons.matching(NSPredicate(format: "label CONTAINS 'See the evidence'")).firstMatch
            .waitForExistence(timeout: 30), "no answer from the engine on 127.0.0.1:8090")
    }

    private func field(_ identifier: String) -> XCUIElement {
        app.descendants(matching: .any)[identifier]
    }

    private func ask(_ question: String) {
        let box = field("question")
        box.tap()
        box.typeText(question)
        app.buttons["send"].tap()
    }

    /// Swipe until the element is wholly on screen. A coordinate tap does not scroll, and the
    /// combined list is long.
    private func bringIntoView(_ element: XCUIElement) {
        let screen = app.windows.firstMatch.frame
        for _ in 0..<60 where !(element.isHittable && screen.contains(element.frame)) {
            app.swipeUp(velocity: .fast)
        }
        XCTAssertTrue(screen.contains(element.frame), "\(element) never came on screen")
    }

    private func keep(_ name: String) {
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = name
        shot.lifetime = .keepAlways
        add(shot)
    }

    func testAQuestionThatSelectsOneBoardShowsTheCards() {
        ask("Which model writes code best?")
        XCTAssertTrue(app.buttons["change"].waitForExistence(timeout: 20))
        XCTAssertFalse(field("combinedList").waitForExistence(timeout: 3), "one board needs no combination")
        keep("one board: the cards")
    }

    /// M17-W5's first simulator-found defect: a removed chip vanished and could not be restored.
    func testARemovedRefinementCanBeRestored() {
        ask("Translate my letter into French")
        XCTAssertTrue(field("combinedList").waitForExistence(timeout: 30), "a refinement should combine boards")
        keep("two boards: the combined list")
        let chip = app.buttons["chip.french"]
        XCTAssertEqual(chip.label, "Remove the French board")
        chip.tap()
        XCTAssertTrue(app.buttons["chip.french"].waitForExistence(timeout: 10), "the removed chip vanished")
        XCTAssertEqual(app.buttons["chip.french"].label, "Add the French board back")
        XCTAssertFalse(field("combinedList").exists, "with its board removed, one board is left: the cards")
        keep("chip removed")
        app.buttons["chip.french"].tap()
        XCTAssertTrue(field("combinedList").waitForExistence(timeout: 10), "restoring the chip did not combine")
    }

    /// M17-W5's second simulator-found defect: "See the boards" took no tap across most of its row.
    func testTheBoardsRowAnswersATapAwayFromItsText() {
        ask("Translate my letter into French")
        let row = app.buttons["seeTheBoards"]
        XCTAssertTrue(row.waitForExistence(timeout: 30))
        bringIntoView(row)
        row.coordinate(withNormalizedOffset: CGVector(dx: 0.7, dy: 0.5)).tap()
        XCTAssertTrue(app.staticTexts["The boards behind this list"].waitForExistence(timeout: 10),
                      "a tap in the row's empty middle did not open the boards")
        keep("the boards behind a combined list")
    }

    func testChangeOpensTheChooserAndAChoiceIsShown() {
        app.buttons["change"].tap()
        XCTAssertTrue(app.navigationBars["What should we rank?"].waitForExistence(timeout: 10))
        keep("the surface chooser")
        app.buttons.element(boundBy: 1).tap()
        XCTAssertTrue(app.buttons["change"].waitForExistence(timeout: 10), "the chooser did not close")
    }

    func testACardOpensItsEvidence() {
        app.buttons.matching(NSPredicate(format: "label CONTAINS 'See the evidence'")).firstMatch.tap()
        XCTAssertTrue(app.navigationBars.firstMatch.waitForExistence(timeout: 10))
        XCTAssertFalse(field("question").isHittable, "the evidence screen did not open")
        keep("a card's evidence")
    }
}
