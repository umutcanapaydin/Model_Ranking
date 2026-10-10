//  #227 -- which way `bringIntoView` moves the home screen next, from where the element is.
//
//  The coding test failed four times in full runs, its second family list "never came on screen
//  within 60 swipes": each fast swipe flings the lazy stack on, and once a fling has carried the list
//  past the top, swiping on up never brings it back. Now each step is a drag of under half the screen
//  that stops before it is let go, so nothing is flung past, and its direction is decided here, from
//  the element's frame, so it is tested without a simulator.

import CoreGraphics
import XCTest

enum ScrollStep: Equatable {
    case done, dragUp, dragDown
}

/// The next step toward `element` (nil while the lazy stack has not built it yet, which happens below
/// the screen as the list is read top down).
func scrollStep(toward element: CGRect?, hittable: Bool, on screen: CGRect) -> ScrollStep {
    guard let frame = element else { return .dragUp }
    if hittable, screen.contains(frame) { return .done }
    return frame.minY < screen.minY ? .dragDown : .dragUp
}

final class ScrollStepTests: XCTestCase {
    private let screen = CGRect(x: 0, y: 0, width: 400, height: 800)

    func testAnElementOnScreenNeedsNoStep() {
        XCTAssertEqual(scrollStep(toward: CGRect(x: 0, y: 300, width: 400, height: 40), hittable: true, on: screen), .done)
    }

    func testAnElementNotBuiltYetIsBelowSoTheScreenMovesUp() {
        XCTAssertEqual(scrollStep(toward: nil, hittable: false, on: screen), .dragUp)
    }

    func testAnElementBelowTheScreenMovesItUp() {
        XCTAssertEqual(scrollStep(toward: CGRect(x: 0, y: 900, width: 400, height: 40), hittable: false, on: screen), .dragUp)
    }

    /// #227's overshoot: the element was carried past the top. The next step comes back down to it.
    func testAnElementCarriedPastTheTopBringsTheScreenBackDown() {
        XCTAssertEqual(scrollStep(toward: CGRect(x: 0, y: -300, width: 400, height: 40), hittable: false, on: screen),
                       .dragDown)
        XCTAssertEqual(scrollStep(toward: CGRect(x: 0, y: -20, width: 400, height: 40), hittable: true, on: screen),
                       .dragDown, "half above the top")
    }
}
