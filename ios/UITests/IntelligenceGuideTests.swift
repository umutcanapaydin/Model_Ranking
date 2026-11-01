//  #527 (D-235, amending D-175 clause 3) -- the Apple Intelligence guide and its Open Settings button (#484, D-230),
//  driven in the simulator against a local engine. Run with `make ui-test`, in its engine-up pass: the caption that
//  opens the guide is on the question card, which needs the engine's first answer.
//
//  On the simulator Apple Intelligence runs, so the guide never appears on its own. The Debug-only launch argument
//  `-UITestIntelligence unavailable` makes the app report the model as unavailable, a state a device without the model
//  is in. Assertions are on the accessibility tree; the test also attaches what it saw, as evidence (#63).

import XCTest

final class IntelligenceGuideTests: XCTestCase {
    private var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["-language", "en", "-UITestIntelligence", "unavailable"]
        app.launch()
        XCTAssertTrue(app.descendants(matching: .any)["question"].waitForExistence(timeout: 30),
                      "the screen never loaded")
    }

    func testTheGuidesOpenSettingsButtonBringsTheSettingsAppToTheFront() {
        // The caption says the model is unavailable, and it is a button: the way into the guide (#481).
        let caption = app.buttons["aiCaption"]
        XCTAssertTrue(caption.waitForExistence(timeout: 30), "the caption did not offer the guide")
        XCTAssertTrue(caption.label.hasPrefix("Apple Intelligence is unavailable now"), caption.label)
        caption.tap()

        let openSettings = app.buttons["Open Settings"]
        XCTAssertTrue(openSettings.waitForExistence(timeout: 10), "the guide did not show its Open Settings button")
        XCTAssertTrue(app.navigationBars["Apple Intelligence is unavailable now"].exists, "the guide's title is not shown")
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = "model unavailable: the Apple Intelligence guide"
        shot.lifetime = .keepAlways
        add(shot)

        openSettings.tap()
        let settings = XCUIApplication(bundleIdentifier: "com.apple.Preferences")
        XCTAssertTrue(settings.wait(for: .runningForeground, timeout: 20), "Open Settings did not bring Settings to the front")
        // The app's own state is reported a moment after Settings is in front, so it is waited for.
        let left = expectation(for: NSPredicate { _, _ in self.app.state != .runningForeground }, evaluatedWith: nil)
        wait(for: [left], timeout: 15)
        let after = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        after.name = "after Open Settings: the Settings app"
        after.lifetime = .keepAlways
        add(after)
    }
}
