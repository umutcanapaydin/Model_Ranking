"""M18-W6 (#89, W-131): `docs/security-invariants.md` is held together by this gate.

The list says, for each security invariant, which tests fail when it is removed. This gate cannot
prove that they do (the mutation samples did), but it refuses everything that would let the list
rot without anyone seeing it:
- a cited test file or test function that does not exist, or a `make` target the Makefile lacks;
- a row with no test that names no gap, a gap that names no issue, a row citing a gap not listed;
- an `INV-n` written in `src/`, `scripts/`, `tests/` or `ios/` that is neither a row nor retired;
- a number used twice, or skipped;
- a row count that disagrees with the count the list states.

Each check is a function over text, and each is watched failing on a planted list.
"""

from __future__ import annotations

import functools
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIST = ROOT / "docs" / "security-invariants.md"


def tracked(*suffixes: str) -> list[Path]:
    """The tracked files under `src`, `scripts`, `tests` and `ios` with these suffixes: the tree git
    holds, not a build directory beside it (`ios/.build` holds thousands of third-party files)."""
    listed = subprocess.run(["git", "ls-files", "src", "scripts", "tests", "ios"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / name for name in listed if name.endswith(suffixes)]

ROW = re.compile(r"^\| INV-(\d+) \| (.+?) \| (.+?) \| (.+) \|$")
GAP = re.compile(r"^\| (G-\d+) \| (.+?) \| (.+?) \| (.+) \|$")
TEST = re.compile(r"`((?:tests|ios)/[\w./-]+\.(?:py|swift))::(\w+)`")
MAKE = re.compile(r"`make ([\w-]+)`")
#: Anything in a cell that looks like a citation. Each must be read as a test or a target, or the
#: gate fails: a citation it cannot read is one it would never check (the W6 review's M5).
CITED = re.compile(r"`((?:tests|ios)/[^`]*|make\b[^`]*)`")
GAP_REF = re.compile(r"\bG-\d+\b")
MENTION = re.compile(r"\bINV-(\d+)\b")
RETIRED = re.compile(r"^\| INV-(\d+) \|")


@dataclass(frozen=True)
class Row:
    number: int
    tests: tuple[tuple[str, str], ...]
    targets: tuple[str, ...]
    gaps: tuple[str, ...]
    none: bool
    unread: tuple[str, ...]  # citations in the cell that are neither a test nor a target


def section(text: str, title: str) -> str:
    start = text.index(f"## {title}")
    following = text.find("\n## ", start + 1)
    return text[start:following if following >= 0 else len(text)]


def unreadable(text: str) -> list[str]:
    """Lines that look like a row of the list, a gap or a retired id, and that the parser cannot
    read. Each is a finding: a row the gate cannot read is one it never checks (the W6 review's M5)."""
    found = []
    for title, pattern, prefix in (("The list", ROW, "| INV-"), ("Gaps", GAP, "| G-"),
                                   ("Retired ids", RETIRED, "| INV-")):
        for line in section(text, title).splitlines():
            if line.startswith(prefix) and not pattern.match(line.rstrip()):
                found.append(f"{title}: a row the gate cannot read: {line[:80]!r}")
    return found


def parse(text: str) -> tuple[list[Row], dict[str, str], set[int]]:
    """The rows, the gaps (id -> issue cell) and the retired numbers."""
    rows = []
    for line in section(text, "The list").splitlines():
        match = ROW.match(line.rstrip())
        if match:
            cell = match.group(4)
            unread = tuple(c for c in CITED.findall(cell) if not TEST.fullmatch(f"`{c}`") and not MAKE.fullmatch(f"`{c}`"))
            rows.append(Row(int(match.group(1)), tuple(TEST.findall(cell)), tuple(MAKE.findall(cell)),
                            tuple(GAP_REF.findall(cell)), "**none**" in cell, unread))
    gaps = {m.group(1): m.group(4) for line in section(text, "Gaps").splitlines() if (m := GAP.match(line.rstrip()))}
    retired = {int(m.group(1)) for line in section(text, "Retired ids").splitlines()
               if (m := RETIRED.match(line.rstrip()))}
    return rows, gaps, retired


@functools.cache
def declared_names(path: Path) -> frozenset[str]:
    """The functions a test file declares: `def` in Python, `func` in Swift."""
    pattern = r"^\s*(?:async\s+)?def (\w+)\(" if path.suffix == ".py" else r"\bfunc (\w+)\("
    return frozenset(re.findall(pattern, path.read_text(encoding="utf-8"), re.M))


def problems(text: str, root: Path = ROOT) -> list[str]:
    rows, gaps, retired = parse(text)
    found: list[str] = unreadable(text)
    if len(rows) < 50:
        found.append(f"only {len(rows)} rows were read from the list")
    numbers = [row.number for row in rows]
    for number in sorted({n for n in numbers if numbers.count(n) > 1}):
        found.append(f"INV-{number} is two rows")
    for number in sorted(set(numbers) & retired):
        found.append(f"INV-{number} is a row and retired")
    every = set(numbers) | retired
    if every:
        for number in sorted(set(range(1, max(every) + 1)) - every):
            found.append(f"INV-{number} is skipped: neither a row nor retired")
    count = re.search(r"\*\*Count\.\*\* (\d+) rows", text)
    if not count or int(count.group(1)) != len(rows):
        found.append(f"the list states {count.group(1) if count else 'no'} rows and has {len(rows)}")
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    for row in rows:
        for citation in row.unread:
            found.append(f"INV-{row.number} cites `{citation}`, which the gate cannot read as a test")
        if not (row.tests or row.targets) and not (row.none and row.gaps):
            found.append(f"INV-{row.number} cites no test and names no gap")
        for gap in row.gaps:
            if gap not in gaps:
                found.append(f"INV-{row.number} names {gap}, which the gaps table does not list")
        for path, name in row.tests:
            file = root / path
            if not file.is_file():
                found.append(f"INV-{row.number} cites {path}, which does not exist")
                continue
            if name not in declared_names(file):
                found.append(f"INV-{row.number} cites {path}::{name}, which is not declared there")
        for target in row.targets:
            if not re.search(rf"^{re.escape(target)}:", makefile, re.M):
                found.append(f"INV-{row.number} cites `make {target}`, which the Makefile does not have")
    for gap, issue in gaps.items():
        if not re.search(r"#\d+", issue):
            found.append(f"{gap} names no issue")
    return found


def dangling(texts: dict[str, str], text: str) -> list[str]:
    """`INV-n` written in a source file that the list neither holds nor retires."""
    rows, _, retired = parse(text)
    known = {row.number for row in rows} | retired
    return sorted(f"{name}: INV-{n}" for name, body in texts.items()
                  for n in {int(m) for m in MENTION.findall(body)} if n not in known)


def test_the_list_holds_together() -> None:
    assert not problems(LIST.read_text(encoding="utf-8")), problems(LIST.read_text(encoding="utf-8"))


def test_every_invariant_the_code_names_is_on_the_list() -> None:
    files = tracked(".py", ".sh", ".swift")
    assert len(files) > 100, "the scan read almost nothing"
    texts = {str(path.relative_to(ROOT)): path.read_text(encoding="utf-8", errors="replace") for path in files}
    assert not dangling(texts, LIST.read_text(encoding="utf-8")), dangling(texts, LIST.read_text(encoding="utf-8"))


# --- the gate, watched failing ---------------------------------------------------------------------

def _planted(row: str, gap: str = "| G-1 | INV-2 | something | #1 |") -> str:
    """The real list with its first row replaced, and its gaps table holding one gap."""
    text = LIST.read_text(encoding="utf-8")
    first = next(line for line in section(text, "The list").splitlines() if ROW.match(line))
    gaps = section(text, "Gaps")
    kept = [line for line in gaps.splitlines() if not GAP.match(line)]
    at = kept.index("|---|---|---|---|") + 1
    return text.replace(first, row, 1).replace(gaps, "\n".join([*kept[:at], gap, *kept[at:]]), 1)


def _first_number() -> int:
    text = LIST.read_text(encoding="utf-8")
    return next(int(m.group(1)) for line in section(text, "The list").splitlines() if (m := ROW.match(line)))


def test_a_test_that_does_not_exist_is_refused() -> None:
    n = _first_number()
    row = f"| INV-{n} | x | y | `tests/unit/test_security_invariants.py::test_that_was_never_written` |"
    assert any("not declared there" in p for p in problems(_planted(row)))
    row = f"| INV-{n} | x | y | `tests/unit/test_no_such_file.py::test_x` |"
    assert any("does not exist" in p for p in problems(_planted(row)))
    row = f"| INV-{n} | x | y | `make no-such-target` |"
    assert any("Makefile does not have" in p for p in problems(_planted(row)))


def test_a_row_with_no_test_needs_a_gap_with_an_issue() -> None:
    n = _first_number()
    assert any("cites no test" in p for p in problems(_planted(f"| INV-{n} | x | y | nothing |")))
    gapless = problems(_planted(f"| INV-{n} | x | y | **none**: gap G-9 |"))
    assert any("does not list" in p for p in gapless)
    issueless = problems(_planted(f"| INV-{n} | x | y | **none**: gap G-1 |", gap="| G-1 | x | y | soon |"))
    assert any("names no issue" in p for p in issueless)


def test_a_number_used_twice_or_skipped_is_refused() -> None:
    text = LIST.read_text(encoding="utf-8")
    rows, _, _ = parse(text)
    twice = problems(_planted(f"| INV-{rows[1].number} | x | y | `make lint` |"))
    assert any("is two rows" in p for p in twice) and any("is skipped" in p for p in twice)


def test_an_invariant_named_in_code_but_not_on_the_list_is_refused() -> None:
    text = LIST.read_text(encoding="utf-8")
    rows, _, retired = parse(text)
    unknown = max({row.number for row in rows} | retired) + 1
    assert dangling({"src/x.py": "# holds INV-" + str(unknown)}, text)
    assert not dangling({"src/x.py": f"# holds INV-{rows[0].number}"}, text)


def test_a_row_or_a_citation_the_gate_cannot_read_is_refused() -> None:
    """The W6 review's M5: a new last row with a trailing space, and a class path in a cell, were
    both skipped without a word, and the gate passed."""
    text = LIST.read_text(encoding="utf-8")
    rows, _, retired = parse(text)
    last = next(line for line in reversed(section(text, "The list").splitlines()) if ROW.match(line))
    new = max({row.number for row in rows} | retired) + 1
    spaced = text.replace(last, last + f"\n| INV-{new} | x | y | `tests/unit/test_no_such_file.py::test_nothing` | ", 1)
    assert any("does not exist" in p for p in problems(spaced)), "a row with a trailing space was not read"
    broken = text.replace(last, last + f"\n| INV-{new} | a row with a cell missing |", 1)
    assert any("cannot read" in p for p in problems(broken))
    classy = text.replace(last, last[:-2] + "<br>`tests/unit/test_nope.py::TestX::test_gone` |", 1)
    assert any("cannot read as a test" in p for p in problems(classy))
