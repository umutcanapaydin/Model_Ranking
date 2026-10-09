"""#105 (M18-W7) and #131: every piece of evidence the PRD cites still exists, by name.

The PRD cited its evidence as `test_x.py:123`. A test added above a cited one moved the pointer:
M18-W3 moved 15 citations, M18-W4 eight. #105 made each pointer land on a test's declaration, and
that still let a pointer shift onto ANOTHER test's declaration (two at M18-W7, four at #126). So
evidence is cited by name (#131):
- `test_x.py::test_name`, and `::test_other` for another in the same file (also after a
  parenthetical, and as "in `::test_name`" for a place inside a test);
- each name is declared in its file: a test, a class of tests, or the file's `pytestmark`; in a
  source file, the function, type or constant;
- the file exists under exactly one path of the tracked tree;
- a line pointer into a Python or Swift file is refused, and so is `Makefile:N`; a make target is
  named as `make <target>`, and the Makefile must define it.
Workflow and record pointers (`ci.yml:7`, `m7-plan.md:166`) stay outside this gate.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PRD = ROOT / "docs" / "prd.md"
#: A citation by name: `test_x.py::test_a`.
NAMED = re.compile(r"\b([\w-]+\.(?:py|swift))::(\w+)")
#: Another name of the file named last before it on the line: `, ::test_b`, "in `::test_b`".
BARE_NAME = re.compile(r"(?<![\w.:])::(\w+)")
#: A line pointer into Python or Swift, and a bare `:N` or `at :N` after one.
LINE_POINTER = re.compile(r"\b([\w-]+\.(?:py|swift)):(\d+)")
BARE_LINE = re.compile(r"(?<![\w.:])(?:\bat\s+)?:(\d+)\b")
#: Any `file.ext:N` or `file.ext::name`: the file a bare pointer after it belongs to.
ANY_FILE = re.compile(r"\b([\w-]+\.\w+)(?=::?\w)")
MAKEFILE_LINE = re.compile(r"\bMakefile:\d+")
MAKE_TARGET = re.compile(r"`make ([\w.-]+)")
#: What a test file declares: a test, a class of tests, or its `pytestmark`.
TEST_DECLARATION = re.compile(r"^\s*(?:async\s+)?def (test_\w*)\(|^\s*func (test\w*)\(|^(pytestmark)\s*="
                              r"|^(?:final )?class (\w+Tests?)\b|^class (Test\w*)")
#: What a source file declares: a function, a type, a constant or a property.
SOURCE_DECLARATION = re.compile(
    r"^\s*(?:async\s+)?def (\w+)\(|^\s*class (\w+)|^(\w+)\s*(?::[^=]+)?=(?!=)"
    r"|^\s*(?:(?:public|private|fileprivate|internal|static|final|@\w+)\s+)*"
    r"(?:func|struct|enum|class|actor|protocol|let|var|typealias)\s+(\w+)")


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


def declared(path: str, lines: list[str]) -> set[str]:
    pattern = TEST_DECLARATION if is_test_file(path) else SOURCE_DECLARATION
    return {name for line in lines if (hit := pattern.match(line)) for name in hit.groups() if name}


def problems(text: str, by_name: dict[str, list[str]], read: object = None) -> list[str]:
    def lines_of(path: str) -> list[str]:
        return (ROOT / path).read_text(encoding="utf-8").splitlines() if read is None else read(path)  # type: ignore[operator]

    names_of: dict[str, set[str]] = {}

    def check(where: str, name: str, test: str) -> str | None:
        paths = by_name.get(name, [])
        if len(paths) != 1:
            return f"{where}: {name} is {'not tracked' if not paths else 'ambiguous: ' + str(paths)}"
        if paths[0] not in names_of:
            names_of[paths[0]] = declared(paths[0], lines_of(paths[0]))
        if test not in names_of[paths[0]]:
            return f"{where}: {name}::{test} is not declared in {paths[0]}"
        return None

    targets: set[str] | None = None
    found = []
    for number, row in enumerate(text.splitlines(), start=1):
        # Every line, not only the requirement rows (the W7 review's M2: the `**Status:**` lines held
        # a third of the pointers); each is named by its requirement where the line has one.
        rid = re.search(r"\b(REQ-[A-Z]+-\d+)\b", row)
        where = rid.group(1) if rid else f"line {number}"
        for match in LINE_POINTER.finditer(row):
            found.append(f"{where}: {match.group(0)} is a line pointer; cite the test by name (#131)")
        for match in MAKEFILE_LINE.finditer(row):
            found.append(f"{where}: {match.group(0)} is a line pointer; name the target as `make <target>`")
        for match in MAKE_TARGET.finditer(row):
            if targets is None:
                targets = {hit.group(1) for line in lines_of("Makefile") if (hit := re.match(r"^([\w.-]+):", line))}
            if match.group(1) not in targets:
                found.append(f"{where}: `make {match.group(1)}` names no target in the Makefile")
        named_spans = [m.span() for m in NAMED.finditer(row)]
        for match in NAMED.finditer(row):
            if problem := check(where, match.group(1), match.group(2)):
                found.append(problem)
        for bare in BARE_NAME.finditer(row):
            if any(start <= bare.start() < end for start, end in named_spans):
                continue
            files = list(ANY_FILE.finditer(row[:bare.start()]))
            if not files or not files[-1].group(1).endswith((".py", ".swift")):
                found.append(f"{where}: ::{bare.group(1)} follows no Python or Swift file")
            elif problem := check(where, files[-1].group(1), bare.group(1)):
                found.append(problem)
        # A bare line pointer after a Python or Swift file is a line pointer too (`, :106`, `at :693`).
        line_spans = [m.span() for m in LINE_POINTER.finditer(row)]
        for bare in BARE_LINE.finditer(row):
            if any(start <= bare.start(1) < end for start, end in line_spans):
                continue
            files = list(ANY_FILE.finditer(row[:bare.start()]))
            if files and files[-1].group(1).endswith((".py", ".swift")):
                found.append(f"{where}: {bare.group(0).strip()} after {files[-1].group(1)} is a line pointer; "
                             "cite the test by name (#131)")
    return found


@pytest.mark.needs("git")
def test_every_prd_citation_names_its_test() -> None:
    text = PRD.read_text(encoding="utf-8")
    assert len(NAMED.findall(text)) > 50, "the PRD's citations were not read"
    assert not problems(text, tracked()), problems(text, tracked())


FILES = {"tests/unit/test_x.py": ["import os", "", "def test_a():", "    pass", "", "def test_b():", "    pass"],
         "src/app/x.py": ["LIMIT = 3", "", "def fetch():", "    pass"],
         "Makefile": ["format: install", "check: lint test", "\t$(PY) -m pytest"]}
BY_NAME = {"test_x.py": ["tests/unit/test_x.py"], "x.py": ["src/app/x.py"]}


def test_a_name_must_be_declared_in_its_file() -> None:
    read = FILES.__getitem__
    assert not problems("| REQ-XX-001 | c | MET. Evidence: test_x.py::test_a |", BY_NAME, read)
    assert problems("| REQ-XX-001 | c | MET. Evidence: test_x.py::test_gone |", BY_NAME, read)
    assert problems("| REQ-XX-001 | c | MET. Evidence: test_gone.py::test_a |", BY_NAME, read)
    assert problems("Evidence: test_x.py::os", BY_NAME, read), "an import is not a test"
    # The W7 review's M2: a pointer on a `**Status:**` line, outside the table, is read too.
    assert problems("**Status:** **MET.** Evidence: test_x.py::test_gone", BY_NAME, read)
    # A source file is cited by its function or constant.
    assert not problems("Evidence: x.py::fetch and x.py::LIMIT", BY_NAME, read)
    assert problems("Evidence: x.py::gone", BY_NAME, read)


def test_every_name_of_a_list_and_after_a_parenthetical_is_read() -> None:
    """Tester (M18-W7): with only the first of a list read, or a pointer past a parenthetical left
    outside the citation, a moved one passed. Each `::name` belongs to the file named last before it,
    and an ambiguous file name is a problem, not its first path."""
    read = FILES.__getitem__
    assert not problems("Evidence: test_x.py::test_a (which asserts it), ::test_b.", BY_NAME, read)
    assert problems("Evidence: test_x.py::test_a (which asserts it), ::test_gone.", BY_NAME, read)
    assert not problems("Evidence: test_x.py::test_a (`f()` exercised in ::test_b)", BY_NAME, read)
    assert problems("Evidence: ::test_a with no file before it", BY_NAME, read)
    assert problems("Evidence: test_x.py::test_a",
                    {"test_x.py": ["tests/unit/test_x.py", "tests/b/test_x.py"]}, read)
    # Workflow and record pointers stay outside this gate.
    assert not problems("Evidence: `.github/workflows/ci.yml:7`, `:54`; test_x.py::test_a", BY_NAME, read)


def test_line_pointers_are_refused_and_make_targets_must_exist() -> None:
    read = FILES.__getitem__
    for text in ("Evidence: test_x.py:3", "Evidence: test_x.py::test_a, :6", "Evidence: x.py:1",
                 "Evidence: test_x.py::test_a (`f()` exercised at :4)", "a leg of `make check` (Makefile:2)"):
        assert problems(text, BY_NAME, read), text
    assert not problems("`make check` runs it", BY_NAME, read)
    assert problems("`make gone` runs it", BY_NAME, read)


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


def _body_of(lines: list[str], name: str) -> str:
    """The lines of test `name`, from its declaration to the next test's (or the file's end)."""
    starts = [k for k, line in enumerate(lines) if (hit := TEST_DECLARATION.match(line)) and name in hit.groups()]
    assert len(starts) == 1, f"{name} is declared {len(starts)} times"
    end = next((k for k in range(starts[0] + 1, len(lines)) if TEST_DECLARATION.match(lines[k])), len(lines))
    return "\n".join(lines[starts[0]:end])


@pytest.mark.needs("git")
def test_a_place_the_prd_points_into_holds_the_code_it_names() -> None:
    """#126 (its fix Tester's R1), in #131's terms. A place inside a test is cited as
    "`clear()` exercised in `::testName`", and the code it names must stand in that test's body.
    As a line it only had to exist: after #126 removed lines above it, it sat on a doc comment, every
    gate passed, and #131's conversion then named the test the stale line led to."""
    by_name = tracked()
    places = 0
    for row in PRD.read_text(encoding="utf-8").splitlines():
        for match in re.finditer(r"`([^`]+)`[^`(]{0,40}?\bin\s+`?::(\w+)", row):  # with or without backticks
            files = list(ANY_FILE.finditer(row[: match.start()]))
            assert files, f"no file named before {match.group(0)!r}"
            (path,) = by_name[files[-1].group(1)]
            body = _body_of((ROOT / path).read_text(encoding="utf-8").splitlines(), match.group(2))
            places += 1
            assert match.group(1) in body, f"{files[-1].group(1)}::{match.group(2)} does not hold `{match.group(1)}`"
    assert places, "no place inside a test was read; the pattern matches nothing"
