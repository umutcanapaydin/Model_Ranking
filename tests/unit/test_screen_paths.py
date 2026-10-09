"""#199 (M21-W2; the review's M8): the reading each screen test waits for is the fixture's, not a second
copy in the test's body. `ios/UITests/ScreenPaths.json` holds each question, the model's scripted
answer and its reading; `ScreenPathFixtureTests` holds the reading under `swift test`, and here every
screen test that asks a question waits through `waitForReading(of:)`, which reads the same fixture."""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
UI = ROOT / "ios/UITests/ScreenPathTests.swift"
FIXTURE = ROOT / "ios/UITests/ScreenPaths.json"
ASK = re.compile(r'\b(?:ask|askAgain)\("((?:[^"\\]|\\.)*)"\)\n((?:[^\n]*\n){1,2})')


def test_every_question_a_screen_test_asks_is_in_the_fixture() -> None:
    fixture = {row["q"] for row in json.loads(FIXTURE.read_text(encoding="utf-8"))}
    asked = {match.group(1) for match in ASK.finditer(UI.read_text(encoding="utf-8"))}
    assert asked, "no question was read from the screen tests"
    assert asked <= fixture, sorted(asked - fixture)


def test_a_question_that_is_no_search_is_waited_for_by_its_fixture_reading() -> None:
    """A note or a question back is waited for by `waitForReading(of:)`, never by naming the element
    again in the test, so a reading change in the fixture moves both suites at once."""
    fixture = {row["q"]: row["reading"] for row in json.loads(FIXTURE.read_text(encoding="utf-8"))}
    checked = 0
    for match in ASK.finditer(UI.read_text(encoding="utf-8")):
        question, following = match.group(1), match.group(2)
        if fixture.get(question, "search") == "search":
            continue
        checked += 1
        assert f'waitForReading(of: "{question}")' in following, question
        assert not re.search(r'field\("(askBack|notASearch)"\)\.waitForExistence', following), question
    assert checked >= 8, "fewer questions than the fixture's non-searches were read"


def test_what_a_screen_test_checks_after_its_wait_is_its_fixture_reading_too() -> None:
    """The second review's M5: after the wait, the test does not name the other reading's element again:
    `assertReadingAlone(of:)` derives it from the same fixture, so a reading changed there cannot leave a
    stale `XCTAssertFalse(field("askBack").exists)` behind."""
    swift = UI.read_text(encoding="utf-8")
    for match in re.finditer(r'waitForReading\(of: "((?:[^"\\]|\\.)*)"\)[^\n]*\n((?:[^\n]*\n){1,2})', swift):
        question, following = match.group(1), match.group(2)
        assert not re.search(r'XCTAssert(?:False|True)\(field\("(askBack|notASearch)"\)\.exists', following), question


def test_a_search_is_waited_for_by_what_only_an_answer_shows() -> None:
    """The second review's M5: the note shows Change too, so a search's wait reads the answer itself (the
    combined list or a card's evidence), never Change."""
    swift = UI.read_text(encoding="utf-8")
    arm = re.search(r'case "search":([^\n]*)', swift)
    assert arm, "waitForReading has no search arm"
    assert '"change"' not in arm.group(1) and "waitForAnswer" in arm.group(1), arm.group(1)
