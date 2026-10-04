"""#105 (M18-W7): every `file:line` in the PRD's status cells still lands where it says.

The PRD cites its evidence as `test_x.py:123` or `FooTests.swift:45`. A test added above a cited one
moves the pointer, and nothing noticed: M18-W3 moved 15 citations, M18-W4 eight. So:
- a citation into a test file must land on a test's declaration (`def test_`, `func test`), or on
  the file's `pytestmark`, or a class of tests;
- a citation into any other file must land on a line of it;
- the file must exist, under exactly one path of the tracked tree.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRD = ROOT / "docs" / "prd.md"
CITATION = re.compile(r"\b([\w-]+\.(?:py|swift))((?::\d+)(?:,\s*:\d+)*)")
#: A test's declaration, or a module's `pytestmark`, which governs every test in its file (REQ-CI-001
#: cites one: the live contract tests skip without `RUN_CONTRACT_TESTS`).
TEST_DECLARATION = re.compile(r"^\s*(?:async\s+)?def test_\w*\(|^\s*func test\w*\(|^pytestmark\s*="
                              r"|^(?:final )?class \w+Tests?\b|^class Test\w*")  # a class of tests, as a whole


def tracked() -> dict[str, list[str]]:
    listed = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                            check=True).stdout.split()
    by_name: dict[str, list[str]] = {}
    for path in listed:
        if "/client_decl_fixtures/" in path:  # the declaration gate's planted copies, never evidence
            continue
        by_name.setdefault(path.rsplit("/", 1)[-1], []).append(path)
    return by_name


def is_test_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("Tests.swift")


def problems(text: str, by_name: dict[str, list[str]], read: object = None) -> list[str]:
    def lines_of(path: str) -> list[str]:
        return (ROOT / path).read_text(encoding="utf-8").splitlines() if read is None else read(path)  # type: ignore[operator]

    found = []
    for row in text.splitlines():
        rid = re.match(r"\| (REQ-[A-Z]+-\d+) ", row)
        if not rid:
            continue
        for match in CITATION.finditer(row):
            name, numbers = match.group(1), [int(n) for n in re.findall(r":(\d+)", match.group(2))]
            paths = by_name.get(name, [])
            if len(paths) != 1:
                found.append(f"{rid.group(1)}: {name} is {'not tracked' if not paths else 'ambiguous: ' + str(paths)}")
                continue
            lines = lines_of(paths[0])
            for n in numbers:
                if not 1 <= n <= len(lines):
                    found.append(f"{rid.group(1)}: {name}:{n} is past the end of the file")
                elif is_test_file(paths[0]) and not TEST_DECLARATION.match(lines[n - 1]):
                    found.append(f"{rid.group(1)}: {name}:{n} is not a test's declaration: {lines[n - 1].strip()[:60]!r}")
    return found


def test_every_prd_citation_lands_on_its_test() -> None:
    text = PRD.read_text(encoding="utf-8")
    assert len(CITATION.findall(text)) > 50, "the PRD's citations were not read"
    assert not problems(text, tracked()), problems(text, tracked())


def test_the_citation_check_fails_on_a_moved_pointer() -> None:
    files = {"tests/unit/test_x.py": ["import os", "", "def test_a():", "    pass"]}
    by_name = {"test_x.py": ["tests/unit/test_x.py"]}
    read = files.__getitem__
    assert not problems("| REQ-XX-001 | c | MET. Evidence: test_x.py:3 |", by_name, read)
    assert problems("| REQ-XX-001 | c | MET. Evidence: test_x.py:4 |", by_name, read)
    assert problems("| REQ-XX-001 | c | MET. Evidence: test_x.py:9 |", by_name, read)
    assert problems("| REQ-XX-001 | c | MET. Evidence: test_gone.py:3 |", by_name, read)
