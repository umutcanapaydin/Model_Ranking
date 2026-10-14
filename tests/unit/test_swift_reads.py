"""#275 (D-198 clause 4): every pin file reads the app's Swift as the build compiles it.

#247 held two files to it (`test_router_hints.py` through `_code`, `test_ios_client_contract.py` through
`_swift`), each with a guard of its own. A pin anywhere else could still read a `/* */` or `#if false` copy
of a line it requires. Here every other file under `tests/unit/` is read: a `.read_text(` that reaches the
iOS folder or a `.swift` file goes through `_code(`, or through `_swift(` with `# keeps //: <why>` where a pin
cuts a line at its `//`, or says on its own line why it reads raw (`# raw: <why>`), as an absence check does,
which reads dead code too and so refuses more. Not held (round 2's N3): a read through a function's
parameter, which the guard cannot see, and whether a `# raw:` reason is true."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

UNIT = Path(__file__).resolve().parent
#: The two files #247 holds with guards of their own, and this one, whose planted lines are text.
OWN_GUARDS = {"test_router_hints.py", "test_ios_client_contract.py", Path(__file__).name}
#: What names the app's folder or a Swift file in a path.
SWIFTISH = re.compile(r'\.swift\b|"ModelRanking"|"ios"|\bios/|ModelRanking/')
BOUND = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*(?::[^=\n]*)?=\s*(.*)$")


def _swift_names(lines: list[str]) -> set[str]:
    """The module's constants bound to a path in the iOS folder, or to one built from such a constant."""
    names: set[str] = set()
    for line in lines:
        bound = BOUND.match(line)
        if bound and (SWIFTISH.search(bound.group(2))
                      or any(re.search(rf"\b{name}\b", bound.group(2)) for name in names)):
            names.add(bound.group(1))
    return names


def swift_reads(text: str) -> list[tuple[int, str]]:
    """Each `.read_text(` line that reads the iOS folder: it names it, names a constant bound to it, or
    reads a local bound within three lines to a `.swift` path, or looped within six over Swift files."""
    lines = text.splitlines()
    names = _swift_names(lines)
    found = []
    for index, line in enumerate(lines):
        if ".read_text(" not in line or line.lstrip().startswith("#"):
            continue
        local = set(re.findall(r"^\s*(\w+)\s*=.*\.swift\b", "\n".join(lines[max(0, index - 3):index]), re.M))
        local |= set(re.findall(r"\bfor (\w+) in .*\.(?:r?glob)\([^)]*\.swift", "\n".join(lines[max(0, index - 6):index + 1])))
        if SWIFTISH.search(line) or any(re.search(rf"\b{name}\b", line) for name in names | local):
            found.append((index + 1, line))
    return found


def explained(line: str) -> bool:
    """A read that goes through `_code(`; through `_swift(`, which keeps `//` comments, only with
    `# keeps //: <why>` (D-198 clause 4, round 2's N2); or one that carries `# raw: <why>`."""
    code, _, comment = line.partition("#")
    if re.search(r"\b_code\(", code) or re.match(r"\s*raw:\s*\S", comment):
        return True
    return bool(re.search(r"\b_swift\(", code)) and bool(re.match(r"\s*keeps //:\s*\S", comment))


@pytest.mark.parametrize(("line", "ok"), [
    ('    view = _swift(CLIENT / "ContentView.swift")  # keeps //: the pin cuts a line at its //', True),
    ('    view = _code((IOS / "ContentView.swift").read_text(encoding="utf-8"))', True),
    ('    text = (IOS / "app.sh").read_text(encoding="utf-8")  # raw: not Swift', True),
    ('    view = (IOS / "ContentView.swift").read_text(encoding="utf-8")', False),
    ('    view = (IOS / "ContentView.swift").read_text(encoding="utf-8")  # raw:', False),
    ('    view = (IOS / "ContentView.swift").read_text(encoding="utf-8")  # raw', False),
    ('    view = (IOS / "ContentView.swift").read_text(encoding="utf-8")  # see _code(', False),
    ('    view = (IOS / "ContentView.swift").read_text(encoding="utf-8")  # a raw read', False),
])
def test_a_read_is_explained_only_through_swift_or_code_or_a_raw_reason(line: str, ok: bool) -> None:
    """#275 (the gates Tester's M4 on #275): the line check, on planted lines. `_code` in a comment, a bare
    `raw`, and `# raw:` with no reason explain nothing."""
    assert explained(line) is ok


def test_the_detector_finds_the_reads_of_the_ios_folder() -> None:
    planted = (
        'CLIENT = ROOT / "ios" / "ModelRanking"\n'
        'VIEW = CLIENT / "ContentView.swift"\n'
        "def test_x():\n"
        '    a = VIEW.read_text(encoding="utf-8")\n'
        '    b = (ROOT / "docs" / "x.md").read_text(encoding="utf-8")\n'
        '    for path in CLIENT.rglob("*.swift"):\n'
        '        c = path.read_text(encoding="utf-8")\n'
    )
    assert [number for number, _ in swift_reads(planted)] == [4, 7]


def test_every_read_of_the_ios_folder_in_a_pin_file_goes_through_swift_or_says_why() -> None:
    unexplained = [f"{path.name}:{number}: {line.strip()}" for path in sorted(UNIT.glob("test_*.py"))
                   if path.name not in OWN_GUARDS
                   for number, line in swift_reads(path.read_text(encoding="utf-8"))  # raw: this folder's Python
                   if not explained(line)]
    assert not unexplained, ("a read of the app's Swift past `_code`, so a dead or commented copy of a line "
                             f"reads as live; go through `_code(` or say why on the line: {unexplained}")


def test_the_guard_sees_reads_it_lets_through() -> None:
    """A guard whose derived set is empty passes vacuously (AGENTS.md 3.5)."""
    seen = [line for path in sorted(UNIT.glob("test_*.py")) if path.name not in OWN_GUARDS
            for _, line in swift_reads(path.read_text(encoding="utf-8"))]  # raw: this folder's Python
    assert sum("_swift(" in line or "_code(" in line for line in seen) >= 3, "the guard sees no `_code` read"
    assert sum("# raw:" in line for line in seen) >= 10, "the guard sees no raw read it lets through"
