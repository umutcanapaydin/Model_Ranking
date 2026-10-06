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


def _hooks_skipping_super(text: str) -> list[str]:
    """Each `setUp`/`tearDown` override, instance or class, whose body never calls its super."""
    return [
        f"{kind or ''}{hook}"
        for kind, hook, body in re.findall(
            r"override\s+(class\s+)?func\s+(setUp|tearDown)\(\)\s*(?:throws\s*)?\{(.*?)\n\s{4}\}", text, re.S)
        if f"super.{hook}()" not in body
    ]


def test_the_check_sees_a_class_setup_that_skips_super() -> None:
    """W5 review M1: a subclass's `class func setUp()` without super skipped the install, and the
    instance-only pattern above did not see it."""
    sample = "final class X: OfflineTestCase {\n    override class func setUp() {\n        prepare()\n    }\n}\n"
    assert _hooks_skipping_super(sample) == ["class setUp"]


def test_the_base_checks_every_test_and_calls_through() -> None:
    """The check is in the base's tearDown, and a subclass that overrides setUp or tearDown calls super."""
    base = (TESTS / BASE).read_text(encoding="utf-8")
    assert re.search(r"override func tearDown\(\)[^}]*OfflineGuard", base, re.S), "the base checks nothing"
    skipping = [f"{path.name}: {hook}" for path in sorted(TESTS.glob("*.swift")) if path.name != BASE
                for hook in _hooks_skipping_super(path.read_text(encoding="utf-8"))]
    assert skipping == [], "overrides that skip the base: " + ", ".join(skipping)


def test_no_swift_test_runs_outside_the_tripwire() -> None:
    """W5 review M1: Swift Testing's `@Test` functions are not `XCTestCase` methods and get no tearDown."""
    users = [p.name for p in sorted(TESTS.glob("*.swift")) if re.search(r"^\s*import\s+Testing\b",
                                                                           p.read_text(encoding="utf-8"), re.M)]
    assert users == [], users


def test_no_test_class_reaches_xctestcase_through_an_alias() -> None:
    """W5 second review M11: `typealias PlainCase = XCTestCase` let a class derive from XCTestCase under
    another name, past the check that every class derives from the offline base."""
    aliases = [p.name for p in sorted(TESTS.glob("*.swift"))
               if re.search(r"typealias\s+\w+\s*=\s*(?:XCTest\.)?XCTestCase\b", p.read_text(encoding="utf-8"))]
    assert aliases == [], aliases


def test_no_swift_source_builds_a_background_session() -> None:
    """W5 Tester (round 2's M11): a background session never asks custom protocol classes. The SDK's
    own header says so (`NSURLSession.h`, on `protocolClasses`: "Custom NSURLProtocol subclasses are
    not available to background sessions"). So the tripwire listed in a background configuration
    catches nothing, and only the source can refuse one. The base's own check of the list is exempt."""
    engine = TESTS.parent / "ModelRanking"
    users = [p.name for p in sorted([*TESTS.glob("*.swift"), *engine.rglob("*.swift")]) if p.name != BASE
             and re.search(r"\bbackground\s*\(\s*withIdentifier|backgroundSessionConfiguration",
                           p.read_text(encoding="utf-8"))]
    assert users == [], users


def test_the_base_fails_a_test_whose_requests_it_recorded() -> None:
    """W5 Tester (#59): with its assertion on the drained requests removed, the base's tearDown failed
    nothing and every test passed (the check above matches `OfflineGuard` in the body, which the drain
    alone satisfies). Swift cannot hold this here: the way to expect a failure is `XCTExpectFailure`,
    which `scripts/swift_xunit_gate.py` refuses because the parallel run reports it as a pass."""
    base = (TESTS / BASE).read_text(encoding="utf-8")
    tear_down = re.search(r"override func tearDown\(\) \{(.*?)\n    \}", base, re.S)
    assert tear_down, "the base has no tearDown"
    body = tear_down.group(1)
    drained = re.search(r"let (\w+) = OfflineGuard\.drain\(\)", body)
    assert drained, "the base no longer reads what the tripwire saw"
    assert re.search(rf"XCTAssertEqual\(\s*{drained.group(1)}\s*,\s*\[\]", body), (
        "the base no longer fails a test that reached for the network")


def test_a_bare_session_configuration_is_refused_in_any_spelling() -> None:
    """#108: `URLSessionConfiguration()` trapped an xctest process under the tripwire (signal 5). Read
    without trapping a process on the owner's Mac: its `init` is `[super init]`, an uninitialised base
    configuration the factories never return, and a session copies a configuration through every
    setter, the exchanged Swift `setProtocolClasses:` among them, which takes `[AnyClass]?`. Which
    value traps is unmeasured; what holds either way is that no source builds one."""
    planted = {
        "A.swift": "let c = URLSessionConfiguration()",
        "B.swift": "let c = URLSessionConfiguration.init( )",
        "C.swift": "let c = URLSessionConfiguration.ephemeral  // not URLSessionConfiguration()",
    }
    assert _bare_configurations(planted) == ["A.swift", "B.swift"]


def test_no_swift_source_builds_a_bare_session_configuration() -> None:
    """#108: in the app and its tests, every configuration comes from a factory the tripwire guards."""
    engine = TESTS.parent / "ModelRanking"
    sources = {p.name: p.read_text(encoding="utf-8") for p in sorted([*TESTS.glob("*.swift"), *engine.rglob("*.swift")])}
    assert len(sources) > 20, "the Swift sources were not read"
    assert _bare_configurations(sources) == []


def _bare_configurations(sources: dict[str, str]) -> list[str]:
    """#108: not yet written."""
    return []
