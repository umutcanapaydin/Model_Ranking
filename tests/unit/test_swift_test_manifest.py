"""Every Swift test is named in the committed manifest (D-150 clause 1 as amended, W-111).

`make swift-test` compares the manifest with what the toolchain DISCOVERS, which is the real check
-- but it only runs where Swift is installed, and this project's Swift half has been unrunnable in
every lane but the owner's for three milestones. This is the half that runs everywhere: the
manifest is compared with the test declarations in the source, so an agent with no toolchain still
cannot delete a test without the deletion showing up in a diff of this file.

The floor that used to guard this was an integer somebody raised by hand. It was wrong three times
(W-091, W-111, and the M14 closure), and it could never have caught a deletion: the count and the
declaration drop together. The M15-W4 seat is what established that, after the first description of
this fix was put to the owner and accepted on a false claim.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "ios" / "EngineTests"
MANIFEST = TESTS / "test-manifest.txt"

#: `ModelRankingEngineTests.ClassName/testName`, as `swift test --list-tests` prints it.
ENTRY = re.compile(r"^(?P<module>[A-Za-z_]\w*)\.(?P<cls>[A-Za-z_]\w*)/(?P<test>test\w*)$")
CLASS = re.compile(r"^\s*(?:public\s+|final\s+|private\s+)*class\s+(\w+)\s*:\s*XCTestCase", re.M)
FUNC = re.compile(r"^\s*(?:public\s+|private\s+|final\s+)*func\s+(test\w*)\s*\(\s*\)", re.M)


#: `//` to end of line and `/* ... */`, removed before the declarations are read (review M-4: a
#: test commented out still matched, so the manifest agreed with a suite that no longer ran it).
#: Over-stripping this way can only ever HIDE a declaration, which fails the comparison below --
#: the safe direction, and the opposite of the client gate's problem, where a stripper that ate
#: real code hid a defect.
COMMENT = re.compile(r"//[^\n]*|/\*[\s\S]*?\*/")


def _declared() -> set[tuple[str, str]]:
    """`(class, test)` for every test function declared under `ios/EngineTests`."""
    found: set[tuple[str, str]] = set()
    for path in sorted(TESTS.rglob("*.swift")):
        source = COMMENT.sub("", path.read_text(encoding="utf-8"))
        # Split the file at each XCTestCase class so a function is attributed to the class it is in.
        marks = [(m.start(), m.group(1)) for m in CLASS.finditer(source)]
        for index, (start, name) in enumerate(marks):
            end = marks[index + 1][0] if index + 1 < len(marks) else len(source)
            found |= {(name, func) for func in FUNC.findall(source[start:end])}
    return found


def test_the_manifest_lists_exactly_the_tests_the_sources_declare() -> None:
    lines = [line for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]
    entries = [ENTRY.match(line) for line in lines]
    assert all(entries), [line for line, m in zip(lines, entries, strict=True) if not m]

    listed = {(m["cls"], m["test"]) for m in entries if m}
    declared = _declared()

    assert len(listed) == len(lines), "the manifest repeats a test"
    missing = sorted(listed - declared)
    added = sorted(declared - listed)
    assert not missing, (
        f"{missing} is in {MANIFEST.name} and declared nowhere: a deleted test, or a rename that "
        "did not reach the manifest. Deleting a test means deleting its line here, deliberately"
    )
    assert not added, (
        f"{added} is declared and not in {MANIFEST.name}: add it, so the manifest keeps being the "
        "list of what must run (`cd ios && swift test --list-tests | sort > "
        "EngineTests/test-manifest.txt`)"
    )


def test_no_test_DECLARATION_compiles_conditionally() -> None:
    """`#if false` around a test leaves it declared and never run (review M-4).

    A `#if` INSIDE a test body is fine and the suite has two (`#if canImport(FoundationModels)`,
    which is what a test of an optional framework looks like). What cannot be allowed is a
    condition around the declaration itself, where the test stays in the manifest, stays in this
    file's regex, and never runs. Indentation is the difference, and it is the one signal available
    without parsing Swift: a directive at file or class level sits in the first four columns.
    """
    guarded = [
        f"{path.name}:{source[:m.start()].count(chr(10)) + 1}"
        for path in sorted(TESTS.rglob("*.swift"))
        for source in [path.read_text(encoding="utf-8")]
        for m in re.finditer(r"^ {0,3}#(?:if|elseif|else)\b", source, re.M)
    ]

    assert not guarded, (
        f"{guarded} put a compilation condition around a declaration; a test inside `#if false` "
        "stays in the manifest and never runs. Delete the test, or the condition"
    )


def test_the_manifest_is_sorted_and_one_module(
) -> None:
    """A sorted single-module file makes a deletion one readable line in a diff, which is the point."""
    lines = [line for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert lines == sorted(lines), "the manifest is not sorted; regenerate it with `| sort`"
    assert {ENTRY.match(line)["module"] for line in lines if ENTRY.match(line)} == {  # type: ignore[index]
        "ModelRankingEngineTests"
    }
