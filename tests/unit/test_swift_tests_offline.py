"""#59 -- every Swift test class derives from `OfflineTestCase`, whose tripwire fails a test that
reaches the network (`ios/EngineTests/OfflineTestCase.swift`).

A class that derived from `XCTestCase` directly would run without the check in its own tearDown. In a
parallel run each worker process installs the tripwire from the first class it runs, so it must be
every class, not most of them.
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS = Path(__file__).resolve().parents[2] / "ios" / "EngineTests"
BASE = "OfflineTestCase.swift"


def test_every_swift_test_class_derives_from_the_offline_base() -> None:
    direct = [
        f"{path.name}: {match.group(1)}"
        for path in sorted(TESTS.glob("*.swift")) if path.name != BASE
        for match in re.finditer(r"class\s+(\w+)\s*:\s*XCTestCase\b", path.read_text(encoding="utf-8"))
    ]
    assert direct == [], "test classes that skip the network tripwire: " + ", ".join(direct)


def test_the_base_checks_every_test_and_calls_through() -> None:
    """The check is in the base's tearDown, and a subclass that overrides setUp or tearDown calls super."""
    base = (TESTS / BASE).read_text(encoding="utf-8")
    assert re.search(r"override func tearDown\(\)[^}]*OfflineGuard", base, re.S), "the base checks nothing"
    skipping = [
        f"{path.name}: {hook}"
        for path in sorted(TESTS.glob("*.swift")) if path.name != BASE
        for hook, body in re.findall(r"override func (setUp|tearDown)\(\)\s*\{(.*?)\n    \}", path.read_text(encoding="utf-8"), re.S)
        if f"super.{hook}()" not in body
    ]
    assert skipping == [], "overrides that skip the base: " + ", ".join(skipping)
