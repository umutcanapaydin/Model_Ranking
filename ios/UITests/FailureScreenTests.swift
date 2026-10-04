//  D-175 -- the screen when the engine does not answer. `make ui-test` runs this class in its second
//  pass, after it has stopped the engine, so nothing in the app is told to fail: the address it was
//  built for simply has no one listening.

import XCTest

final class FailureScreenTests: XCTestCase {
    private var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
    }

    private func launch(_ language: String) {
        app.launchArguments = ["-language", language]
        app.launch()
    }

    func testNoEngineShowsTheFailureWithTheAddressAndARetry() {
        launch("en")
        XCTAssertTrue(app.staticTexts["No answer right now"].waitForExistence(timeout: 30),
                      "the failure screen never appeared")
        // M18-W1 review B2: the address the app asked, so a wrong one is visible.
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label CONTAINS '127.0.0.1:8090'")).firstMatch
            .exists, "the failure does not say which address was asked")
        let retry = app.buttons["Try again"]
        XCTAssertTrue(retry.exists)
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = "no engine: the failure screen"
        shot.lifetime = .keepAlways
        add(shot)
        retry.tap()
        XCTAssertTrue(app.staticTexts["No answer right now"].waitForExistence(timeout: 30),
                      "a retry with no engine should fail the same way, not hang")
    }

    /// #96: a Turkish title over English sentences. Every line of the failure is the reader's language.
    func testInTurkishEveryLineOfTheFailureIsTurkish() {
        launch("tr")
        XCTAssertTrue(app.staticTexts["Şu anda cevap yok"].waitForExistence(timeout: 30))
        XCTAssertTrue(app.staticTexts["Motor yanıt vermiyor."].exists, "the failure's sentence is not Turkish")
        XCTAssertTrue(app.staticTexts.matching(NSPredicate(format: "label BEGINSWITH 'Bu soruları cevaplayan'"))
            .firstMatch.exists, "the remedy is not Turkish")
        XCTAssertTrue(app.buttons["Tekrar dene"].exists)
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = "no engine: the failure screen in Turkish"
        shot.lifetime = .keepAlways
        add(shot)
    }
}
