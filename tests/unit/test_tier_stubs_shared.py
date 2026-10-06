"""#126: the Swift tests build `TieredRouter` from one shared set of tier stubs, `TierStubs.swift`.

These gates refuse a `QuestionRouter` stub declared in any other test file. They were in
`test_ios_client_contract.py`; they have a file of their own so that tests added to that file by
other changes do not collide with them.
"""

from __future__ import annotations

import pathlib
import re

CLIENT = pathlib.Path(__file__).resolve().parents[2] / "ios/ModelRanking"


def test_the_swift_tests_share_one_set_of_tier_stubs() -> None:
    """#126 (the M18-W3 Tester's K9): eight `QuestionRouter` stubs lived privately in four test files,
    with no shared answering wording tier, and the gap the Tester's T6 found (no reading test drove
    an answering wording tier through `TieredRouter`) grew in that space. The stubs live in one file,
    `TierStubs.swift`, and no other test file declares one."""
    tests = CLIENT.parent / "EngineTests"
    home = tests / "TierStubs.swift"
    declares = re.compile(r"\b(?:struct|class|enum|actor)\s+(\w+)\s*:[^{\n]*\bQuestionRouter\b")
    elsewhere = [f"{path.name}: {match.group(1)}" for path in sorted(tests.glob("*.swift")) if path != home
                 for match in declares.finditer(path.read_text(encoding="utf-8"))]
    shared = declares.findall(home.read_text(encoding="utf-8")) if home.exists() else []
    assert len(shared) >= 4, f"TierStubs.swift declares {shared}; the shared tiers are missing"
    assert not elsewhere, f"tier stubs declared outside TierStubs.swift: {elsewhere}"


def test_no_test_file_declares_a_tier_stub_in_any_shape() -> None:
    """#126 (the fix Tester's T1): the stub gate above reads a declaration only as `struct Name:
    ... QuestionRouter` on one line, so a generic stub (`struct Name<T>: QuestionRouter`), one that
    conforms in an extension, or one whose conformance runs onto the next line passed it. Here every
    test source, in any folder, is read with its line comments removed, and a conformance to
    `QuestionRouter` outside `TierStubs.swift` fails."""
    tests = CLIENT.parent / "EngineTests"
    home = tests / "TierStubs.swift"
    conforms = re.compile(r"\b(?:struct|class|enum|actor|extension)\s+[\w.]+\s*(?:<[^>{]*>)?"
                          r"\s*:[^{]*\bQuestionRouter\b")
    assert conforms.search(home.read_text(encoding="utf-8")), "the pattern finds no shared stub"
    sources = sorted(path for path in tests.rglob("*.swift") if path != home)
    assert len(sources) >= 10, f"read {len(sources)} test sources; was EngineTests read?"
    found = []
    for path in sources:
        code = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
        found += [f"{path.name}: {' '.join(m.group(0).split())[:60]}" for m in conforms.finditer(code)]
    assert not found, f"tier stubs declared outside TierStubs.swift: {found}"
