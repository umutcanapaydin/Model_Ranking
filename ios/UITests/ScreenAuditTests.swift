//  #63 -- the screen audit: every flow, captured, not asserted. `make ui-test` skips this class; run
//  it with `UI_TEST_ONLY=ScreenAuditTests make ui-test`, and set the simulator's appearance and text
//  size first (`xcrun simctl ui <device> appearance dark`, `... content_size accessibility-extra-extra-extra-large`)
//  to audit those. Each capture is a screenshot and the screen's accessibility tree, kept in the
//  result bundle; `xcrun xcresulttool export attachments` writes them out.
//
//  Routing is NOT scripted here: the audit sees what the reader's question really does.

import XCTest

final class ScreenAuditTests: XCTestCase {
    private var app: XCUIApplication!
    private var language = "tr"

    override func setUp() {
        super.setUp()
        continueAfterFailure = true
    }

    private func launch(_ language: String) {
        self.language = language
        app = XCUIApplication()
        app.launchArguments = ["-language", language]
        app.launch()
        _ = evidenceButton.waitForExistence(timeout: 30)
    }

    private var evidenceButton: XCUIElement {
        app.buttons.matching(NSPredicate(format: "label CONTAINS 'Kanıta bak' OR label CONTAINS 'See the evidence'"))
            .firstMatch
    }

    private func capture(_ name: String) {
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = "\(language)-\(name)"
        shot.lifetime = .keepAlways
        add(shot)
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = "\(language)-\(name)-tree"
        tree.lifetime = .keepAlways
        add(tree)
    }

    private func captureScrolling(_ name: String, screens: Int) {
        capture("\(name)-0")
        for screen in 1...screens {
            app.swipeUp(velocity: .slow)
            capture("\(name)-\(screen)")
        }
    }

    private func ask(_ question: String) {
        let box = app.descendants(matching: .any)["question"]
        box.tap()
        box.typeText(question)
        // The highest "send" on screen is the app's; the keyboard's return key is "send" too.
        var send = app.buttons["send"].firstMatch
        for candidate in app.buttons.matching(identifier: "send").allElementsBoundByIndex
        where candidate.frame.minY < send.frame.minY {
            send = candidate
        }
        send.tap()
        sleep(3)
    }

    func test01Home() {
        for language in ["tr", "en"] {
            launch(language)
            captureScrolling("home", screens: 8)
        }
    }

    func test02Evidence() {
        for language in ["tr", "en"] {
            launch(language)
            evidenceButton.tap()
            sleep(1)
            captureScrolling("evidence", screens: 5)
        }
    }

    func test03Chooser() {
        launch("tr")
        app.buttons["change"].tap()
        sleep(1)
        captureScrolling("chooser", screens: 3)
    }

    func test04Questions() {
        for (name, question) in [("ask-web", "Python ile bir web sitesi yazmak istiyorum"),
                                 ("ask-image", "Bana bir logo resmi çiz"),
                                 ("ask-french", "Mektubumu Fransızcaya çevir")] {
            launch("tr")
            ask(question)
            captureScrolling(name, screens: 3)
        }
    }

    func test05Gaps() {
        launch("tr")
        app.buttons["gaps"].firstMatch.tap()
        sleep(1)
        capture("gaps")
    }

    func test06FullRanking() {
        launch("tr")
        for _ in 0..<12 {
            let link = app.buttons.matching(NSPredicate(format: "label CONTAINS 'modelin tamamı'")).firstMatch
            if link.exists && link.isHittable {
                link.tap()
                break
            }
            app.swipeUp(velocity: .slow)
        }
        sleep(1)
        captureScrolling("ranking", screens: 4)
    }
}
