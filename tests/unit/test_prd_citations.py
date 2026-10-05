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
MAKEFILE = re.compile(r"\bMakefile:(\d+)")
TEST_DECLARATION = re.compile(r"^\s*(?:async\s+)?def test_\w*\(|^\s*func test\w*\(|^pytestmark\s*="
                              r"|^(?:final )?class \w+Tests?\b|^class Test\w*")  # a class of tests, as a whole
#: A pointer with no file in front of it (`, :106`), and `at :693` where the line places it in a test.
BARE_POINTER = re.compile(r"(?<![\w.:])(\bat\s+)?:(\d+)\b")
#: Any `file.ext:N` on a line: the file a bare pointer after it belongs to.
NAMED_FILE = re.compile(r"\b([\w-]+\.\w+):\d+")


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
    for number, row in enumerate(text.splitlines(), start=1):
        # Every line, not only the requirement rows (the W7 review's M2: the `**Status:**` lines held
        # a third of the pointers); each is named by its requirement where the line has one.
        rid = re.search(r"\b(REQ-[A-Z]+-\d+)\b", row)
        where = rid.group(1) if rid else f"line {number}"
        for match in MAKEFILE.finditer(row):
            makefile = lines_of("Makefile")
            n = int(match.group(1))
            if not (1 <= n <= len(makefile) and re.match(r"^[\w.-]+:", makefile[n - 1])):
                found.append(f"{where}: Makefile:{n} is not a target's line")
            elif (target := re.match(r"^([\w.-]+):", makefile[n - 1])) and (
                    target.group(1) not in re.findall(r"`(?:make )?([\w.-]+)`", row)):
                # Tester (M18-W7): the stale `Makefile:108` is a target's line too (`format:`), so the
                # line must define a target the sentence names (`make check`).
                found.append(f"{where}: Makefile:{n} defines `{target.group(1)}`, which the line does not name")
        for match in CITATION.finditer(row):
            name, numbers = match.group(1), [int(n) for n in re.findall(r":(\d+)", match.group(2))]
            paths = by_name.get(name, [])
            if len(paths) != 1:
                found.append(f"{where}: {name} is {'not tracked' if not paths else 'ambiguous: ' + str(paths)}")
                continue
            lines = lines_of(paths[0])
            for n in numbers:
                if not 1 <= n <= len(lines):
                    found.append(f"{where}: {name}:{n} is past the end of the file")
                elif is_test_file(paths[0]) and not TEST_DECLARATION.match(lines[n - 1]):
                    found.append(f"{where}: {name}:{n} is not a test's declaration: {lines[n - 1].strip()[:60]!r}")
        # Tester (M18-W7): a pointer that goes on past a parenthetical (`test_rank.py:92 (which
        # asserts the blend), :106`) is outside the citation matched above. It belongs to the file
        # named last before it on the line. One the line places inside a test (`exercised at :693`)
        # need only exist. A workflow's or a record's pointers stay outside this gate.
        matched = [m.span() for m in (*CITATION.finditer(row), *MAKEFILE.finditer(row))]
        for bare in BARE_POINTER.finditer(row):
            if any(start <= bare.start(2) < end for start, end in matched):
                continue
            named = list(NAMED_FILE.finditer(row[:bare.start()]))
            if not named or not named[-1].group(1).endswith((".py", ".swift")):
                continue
            name, n = named[-1].group(1), int(bare.group(2))
            paths = by_name.get(name, [])
            if len(paths) != 1:
                continue  # reported above, with the citation that names it
            lines = lines_of(paths[0])
            if not 1 <= n <= len(lines):
                found.append(f"{where}: {name}:{n} is past the end of the file")
            elif is_test_file(paths[0]) and not bare.group(1) and not TEST_DECLARATION.match(lines[n - 1]):
                found.append(f"{where}: {name}:{n} is not a test's declaration: {lines[n - 1].strip()[:60]!r}")
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
    # The W7 review's M2: a pointer on a `**Status:**` line, outside the table, is read too.
    assert problems("**Status:** **MET.** Evidence: test_x.py:4", by_name, read)
    files["Makefile"] = ["# a comment", "check: lint test", "\t$(PY) -m pytest"]
    assert not problems("is a leg of `make check` (Makefile:2)", by_name, read)
    assert problems("is a leg of `make check` (Makefile:3)", by_name, read)


def test_a_pointer_past_a_parenthetical_is_read_too() -> None:
    """Tester (M18-W7): `test_rank.py:92 (which asserts the blend), :106` -- the W7 fix round's own
    rewording put `:106` outside the citation the gate matches, so moving it passed the gate. A bare
    pointer belongs to the file named last before it on the line; one the PRD calls a place inside a
    test (`exercised at :693`) need only exist. Workflow and record pointers stay outside this gate."""
    files = {"tests/unit/test_x.py": ["import os", "", "def test_a():", "    pass"]}
    by_name = {"test_x.py": ["tests/unit/test_x.py"]}
    read = files.__getitem__
    assert not problems("Evidence: test_x.py:3 (which asserts it), :3.", by_name, read)
    assert problems("Evidence: test_x.py:3 (which asserts it), :4.", by_name, read)
    assert not problems("Evidence: test_x.py:3 (`a()` exercised at :4)", by_name, read)
    assert problems("Evidence: test_x.py:3 (`a()` exercised at :9)", by_name, read)
    assert not problems("Evidence: `.github/workflows/ci.yml:7`, `:54`; test_x.py:3", by_name, read)


def test_every_pointer_of_a_list_is_read_and_a_name_must_be_one_file() -> None:
    """Tester (M18-W7): with only the first of `test_x.py:3, :4` read, or an ambiguous name taken as
    its first path, the gate passed on the real PRD and on its own self-test."""
    files = {"tests/unit/test_x.py": ["import os", "", "def test_a():", "    pass"]}
    read = files.__getitem__
    assert problems("Evidence: test_x.py:3, :4", {"test_x.py": ["tests/unit/test_x.py"]}, read)
    assert problems("Evidence: test_x.py:3", {"test_x.py": ["tests/unit/test_x.py", "tests/b/test_x.py"]}, read)


def test_a_makefile_pointer_lands_on_the_target_its_sentence_names() -> None:
    """Tester (M18-W7): the M2 fix asked for a target's line, and `Makefile:108`, the stale pointer
    M2 named, is one (`format:`). Put back in the PRD, it passed. The line must define a target the
    sentence names."""
    files = {"Makefile": ["format: install", "check: lint test", "\t$(PY) -m pytest"]}
    read = files.__getitem__
    assert not problems("`make install-check`, a leg of `make check` (Makefile:2)", {}, read)
    assert problems("`make install-check`, a leg of `make check` (Makefile:1)", {}, read)


def test_a_test_is_cited_by_name_and_a_line_pointer_is_refused() -> None:
    """#131: a pointer by line that shifted onto ANOTHER test's declaration passed this gate. It
    happened at M18-W7 (two pointers) and again at #126 (four). A test is cited by name,
    `test_x.py::test_a`, and the gate checks that the name is declared in that file; a line pointer
    into a test file is refused, whatever it lands on."""
    files = {"tests/unit/test_x.py": ["import os", "", "def test_a():", "    pass", "", "def test_b():", "    pass"]}
    by_name = {"test_x.py": ["tests/unit/test_x.py"]}
    read = files.__getitem__
    assert not problems("Evidence: test_x.py::test_a, ::test_b", by_name, read)
    assert problems("Evidence: test_x.py:3", by_name, read), "a line pointer was accepted"
    assert problems("Evidence: test_x.py::test_gone", by_name, read)
    assert problems("Evidence: test_x.py::test_a, ::test_gone", by_name, read)
