//  GlowStyleTests.swift -- #351 (Golden Rule 2, D-210; REQ-APP-007): Apple Intelligence's glow around the
//  question is on whenever the model is available, and livelier while the model reads the question.

import XCTest

@testable import ModelRankingEngine

final class GlowStyleTests: XCTestCase {
    func testTheGlowIsOnWhileTheModelIsAvailableAndOffOtherwise() {
        XCTAssertNotNil(GlowStyle.of(.available, reading: false))
        XCTAssertNotNil(GlowStyle.of(.available, reading: true))
        for state in [OnDeviceState.notEligible, .turnedOff, .downloading, .unavailable] {
            XCTAssertNil(GlowStyle.of(state, reading: true), "\(state)")
        }
    }

    func testTheGlowIsLivelierWhileTheModelReads() throws {
        let idle = try XCTUnwrap(GlowStyle.of(.available, reading: false))
        let reading = try XCTUnwrap(GlowStyle.of(.available, reading: true))
        XCTAssertLessThan(reading.secondsPerTurn, idle.secondsPerTurn)
        XCTAssertGreaterThan(reading.lineWidth, idle.lineWidth)
        XCTAssertGreaterThan(reading.opacity, idle.opacity)
        XCTAssertGreaterThan(idle.lineWidth, 0, "the glow is on, not hidden, while the model waits")
    }
}
