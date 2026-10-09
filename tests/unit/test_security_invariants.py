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
    for title, pattern in (("The list", ROW), ("Gaps", GAP), ("Retired ids", RETIRED)):
        for line in section(text, title).splitlines():
            # Any table line but a header (`| INV |`, `| Gap |`) or a rule (`|---`): the W6
            # Tester's T2 wrote `|INV-n |`, which a test for `| INV-` never looked at.
            first = line.strip("|").split("|", 1)[0].strip() if line.startswith("|") else ""
            row = line.startswith("|") and not line.startswith("|-") and first not in {"INV", "Gap"}
            if row and not pattern.match(line.rstrip()):
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
            # A citation outside backticks is one the gate would never read (the W6 Tester's T2).
            unread += tuple(re.findall(r"(?:tests|ios)/\S+::\w+", re.sub(r"`[^`]*`", "", cell)))
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
            if not name.startswith("test"):  # a helper pytest or XCTest never runs (the Tester's T2)
                found.append(f"INV-{row.number} cites {path}::{name}, which is not a test")
            elif name not in declared_names(file):
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


def test_a_retired_row_a_wrong_count_a_short_list_and_a_broken_gap_are_refused() -> None:
    """The M18-W6 Tester's survivors: four of the gate's refusals were never watched failing, and
    each could be removed with every test green: a number that is both a row and retired, a count
    that disagrees with the rows, a list read as almost empty, and a gap or retired row the gate
    cannot read (a broken gap row was reported only as the gap being missing)."""
    text = LIST.read_text(encoding="utf-8")
    rows, _, retired = parse(text)
    both = problems(_planted(f"| INV-{min(retired)} | x | y | `make lint` |"))
    assert any("is a row and retired" in p for p in both), both
    miscounted = re.sub(r"\*\*Count\.\*\* \d+ rows", f"**Count.** {len(rows) + 1} rows", text, count=1)
    assert any("the list states" in p for p in problems(miscounted))
    emptied = "\n".join(line for line in text.splitlines() if not ROW.match(line.rstrip()))
    assert any("rows were read from the list" in p for p in problems(emptied))
    gap = next(line for line in section(text, "Gaps").splitlines() if GAP.match(line))
    assert any(p.startswith("Gaps: a row the gate cannot read") for p in problems(text.replace(gap, gap[:-2], 1)))
    old = next(line for line in section(text, "Retired ids").splitlines() if RETIRED.match(line))
    broken = old.replace(" |", "|", 1)
    assert any(p.startswith("Retired ids: a row the gate cannot read")
               for p in problems(text.replace(old, broken, 1)))


def test_the_testers_three_spellings_are_refused() -> None:
    """The W6 Tester's T2: a row without a space after its first `|`, a citation of a helper pytest
    never runs, and a bare citation outside backticks, each passed the gate."""
    text = LIST.read_text(encoding="utf-8")
    rows, _, retired = parse(text)
    last = next(line for line in reversed(section(text, "The list").splitlines()) if ROW.match(line))
    new = max({row.number for row in rows} | retired) + 1
    tight = text.replace(last, last + f"\n|INV-{new} | x | y | `tests/unit/test_no_such_file.py::test_nothing` |", 1)
    assert any("cannot read" in p for p in problems(tight)), "a row without a space was not read"
    helper = text.replace(last, last[:-2] + "<br>`tests/unit/test_refresh.py::_builder` |", 1)
    assert any("not a test" in p for p in problems(helper)), "a helper was accepted as a test"
    bare = text.replace(last, last[:-2] + "<br>tests/unit/test_nope.py::test_gone |", 1)
    assert any("cannot read as a test" in p for p in problems(bare)), "a bare citation was skipped"


# --- the client gates' wording (the M21-W3 review's rounds 3 and 4) --------------------------------
#
# What the compiled gate refuses is defined by its fixture (`scripts/client_decl_fixtures/`, held by its
# self-test), and what a text pin refuses by the spellings its test reads. A record that describes the
# refused forms in prose is always wider or narrower than that, so the register's rows name the fixture's
# rules and the pins' tests instead, and other records point at the rows. These checks hold the wording
# they can read exactly. Their limits: a restatement that names no gate, or that sits beside its pointer,
# is not read; they hold that the sentence and the pointer are there, not that nothing else is said.

#: A row cites the compiled gate when its tests name one of these.
COMPILED_CITATIONS = ("`make client-decls`", "`tests/unit/test_client_decl_gate.py::")
#: The text-pin files: a row cites a pin when it cites a test in one of them.
PIN_FILES = ("tests/unit/test_router_hints.py", "tests/unit/test_ios_client_contract.py")
_NAMES = r"`[^`]+`(?:(?:, | and )`[^`]+`)*"
_GAPS = r"\((G-\d+(?:, G-\d+)*)\)"
#: The sentence a row that cites the compiled gate carries, naming the fixture's rules (`FIXTURE_RULES`).
COMPILED = re.compile(r"The compiled gate refuses the shapes its fixture holds \(`scripts/client_decl_fixtures/`, "
                      rf"rules? ({_NAMES})\), each as written there; the same form written another way \(bound to a "
                      r"name first, split over lines, behind a widened type\) is not held, and any other form is not "
                      rf"held {_GAPS}\.")
#: The sentence a row that cites a text pin carries, naming each pin test it cites.
PINS = re.compile(rf"[Tt]he text pins? ({_NAMES}) refuses? the spellings (?:it|they) reads?; any other spelling is not "
                  r"held \(G-14\)\.")
#: The sentence a row carries for pins that read the Swift without `_code` (the M21-W3 review's round 5,
#: B1; gap G-15), naming each such pin, a test the pin files declare.
RAW = re.compile(rf"[Tt]he text pins? ({_NAMES}) reads? the Swift without `_code`, so a `#if false` or `/\* \*/` "
                 r"copy of a line (?:it|they) requires? satisfies (?:it|them) \(G-15\)\.")
#: How a record outside the register refers to what these gates hold, instead of restating it.
POINTER = re.compile(r"[Hh]eld in part by the compiled gate and the text pins: see "
                     r"(INV-\d+(?:(?:, | and )INV-\d+)*) in `docs/security-invariants\.md`")
#: What names one of the client gates in a record outside the register.
GATE_NAMES = ("client_decl_gate.py", "client-decls", "test_router_hints.py", "test_ios_client_contract.py")
LIST_ITEM = re.compile(r"^\s*(?:[-*]|\d+\.) ")
PRD_ROW = re.compile(r"^\| (REQ-[A-Z]+-\d+) \|")
#: What a PRD row cites when it rests on a client gate: a test in one of the three gate files, or the
#: compiled gate itself (the M21-W3 review's round 5, B2: the architecture branch read both pin files,
#: the PRD branch only the rows a register row draws on).
PRD_GATE_CITATIONS = ("test_router_hints.py", "test_ios_client_contract.py", "test_client_decl_gate.py", "client-decls")
#: PRD rows that cite a gate test for a property the register does not hold, each with why. A row that
#: cites a gate test, draws on no gated row and is not here fails closed: it points at its row, or it
#: is added here with a reason.
NOT_ON_REGISTER = {
    "REQ-APP-001": "no canned payload is compiled into the shipping target: what the build carries, not a "
                   "privacy or arithmetic property",
    "REQ-APP-003": "every disclosure the engine sends is shown: what the screen says, not what it computes "
                   "or sends",
    "REQ-APP-004": "the app degrades with a stated condition: availability, not privacy or arithmetic",
    "REQ-RTR-005": "the unmeasured fallback is a surface the engine serves: which surface, not what leaves "
                   "the phone",
    "REQ-PRC-002": "a search price says the search call is not in it: what the screen says beside a served "
                   "price, not a change to it",
}
COUNTED = re.compile(r"\*\*Count\.\*\* (\d+) rows, .*? (\d+) hold only in part, .*? (\d+) gaps are open", re.S)


def _fixture_rules() -> set[str]:
    """The compiled gate's rule names, as its self-test holds them (`FIXTURE_RULES`)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("client_decl_gate", ROOT / "scripts" / "client_decl_gate.py")
    assert spec and spec.loader
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    return set(gate.FIXTURE_RULES)


@functools.cache
def _pin_tests() -> frozenset[str]:
    """The tests the two pin files declare."""
    return frozenset().union(*(declared_names(ROOT / path) for path in PIN_FILES))


def _gated(claim: str, cell: str) -> tuple[bool, set[str]]:
    """Whether a row cites the compiled gate, and the pin tests it cites."""
    return (any(c in cell for c in COMPILED_CITATIONS),
            {name for path, name in TEST.findall(cell) if path in PIN_FILES})


def gate_row_problems(text: str, rules: set[str]) -> list[str]:
    """Each register row that cites a client gate says it is held in part; one that cites the compiled gate
    carries COMPILED, naming rules the fixture has; one that cites a text pin carries PINS, naming exactly
    the pin tests it cites; RAW, where a row carries it, names pins the files declare; and the gaps the
    sentences name are exactly the row's own "Partial:"."""
    found: list[str] = []
    for line in section(text, "The list").splitlines():
        match = ROW.match(line.rstrip())
        if not match:
            continue
        number, claim, cell = match.group(1), match.group(2), match.group(4)
        compiled, pins = _gated(claim, cell)
        if not (compiled or pins or "Held in part" in claim):
            continue
        if "Held in part" not in claim:
            found.append(f"INV-{number} cites a client gate and does not say it is held in part")
        named: set[str] = set()
        if compiled:
            said = COMPILED.search(claim)
            if not said:
                found.append(f"INV-{number} cites the compiled gate and does not name its fixture's rules ({COMPILED.pattern})")
            else:
                unknown = set(re.findall(r"`([^`]+)`", said.group(1))) - rules
                if unknown:
                    found.append(f"INV-{number} names rules the fixture does not have: {sorted(unknown)}")
                named |= set(said.group(2).split(", "))
        if pins:
            said = PINS.search(claim)
            if not said:
                found.append(f"INV-{number} cites a text pin and does not name it ({PINS.pattern})")
            else:
                if set(re.findall(r"`([^`]+)`", said.group(1))) != pins:
                    found.append(f"INV-{number} names other pin tests than the {sorted(pins)} it cites")
                named.add("G-14")
        if said_raw := RAW.search(claim):
            unknown = set(re.findall(r"`([^`]+)`", said_raw.group(1))) - _pin_tests()
            if unknown:
                found.append(f"INV-{number} names raw-reading pins the pin files do not declare: {sorted(unknown)}")
            named.add("G-15")
        partial = set(GAP_REF.findall(" ".join(re.findall(r"Partial: [^<]*", cell))))
        if (compiled or pins) and named != partial:
            found.append(f"INV-{number}'s sentences name {sorted(named)}, its Partial: names {sorted(partial)}")
    return found


def table_problems(text: str) -> list[str]:
    """Each gap's Rows column is exactly the rows that name it, and the count line's three numbers are the
    rows, the rows that name a gap, and the gaps."""
    rows, gaps, _ = parse(text)
    found: list[str] = []
    for line in section(text, "Gaps").splitlines():
        if match := GAP.match(line.rstrip()):
            listed = {int(n) for n in re.findall(r"INV-(\d+)", match.group(2))}
            naming = {row.number for row in rows if match.group(1) in row.gaps}
            if listed != naming:
                found.append(f"{match.group(1)} lists INV-{sorted(listed)}; the rows that name it are INV-{sorted(naming)}")
    counted = COUNTED.search(text)
    actual = (len(rows), sum(1 for row in rows if row.gaps), len(gaps))
    if not counted or tuple(int(n) for n in counted.groups()) != actual:
        found.append(f"the count line says {counted.groups() if counted else 'nothing'}; the tables hold {actual}")
    return found


def _blocks(text: str) -> list[str]:
    """A markdown file's paragraphs and list items, each one block."""
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if not line.strip() or LIST_ITEM.match(line):
            if current:
                blocks.append("\n".join(current))
            current = [line] if line.strip() else []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def pointer_problems(records: dict[str, str], prd: str, register: str) -> list[str]:
    """Outside the register, a block that names a client gate points at the register's rows; so does a PRD
    row that cites the compiled gate, one a gated row takes as its source, one that cites any test a gated
    row cites, one that cites a test in a gate file (`PRD_GATE_CITATIONS`), and one that names a test the
    three gate files declare, with or without its file (the M21-W3 review's round 6, M4). A PRD row in
    NOT_ON_REGISTER is exempt, with its reason. The pointer names rows that exist, and every gated row
    the PRD row draws on."""
    rows, _, _ = parse(register)
    known = {row.number for row in rows}
    sources: dict[str, set[int]] = {}
    tests: dict[str, set[int]] = {}
    for line in section(register, "The list").splitlines():
        match = ROW.match(line.rstrip())
        if not match or not any(_gated(match.group(2), match.group(4))):
            continue
        for req in re.findall(r"REQ-[A-Z]+-\d+", match.group(3)):
            sources.setdefault(req, set()).add(int(match.group(1)))
        for _, name in TEST.findall(match.group(4)):
            tests.setdefault(name, set()).add(int(match.group(1)))
    found: list[str] = []

    def check(where: str, block: str, needed: set[int]) -> None:
        pointer = POINTER.search(" ".join(block.split()))  # a wrapped paragraph is one sentence
        if not pointer:
            found.append(f"{where} names a client gate or draws on a gated row, and does not point at its row")
            return
        named = {int(n) for n in re.findall(r"INV-(\d+)", pointer.group(1))}
        if named - known:
            found.append(f"{where} points at rows the register does not hold: {sorted(named - known)}")
        if needed - named:
            found.append(f"{where} does not point at INV-{sorted(needed - named)}, which it draws on")

    for name, text in records.items():
        for block in _blocks(text):
            if any(gate in block for gate in GATE_NAMES):
                check(f"{name}: {block.strip()[:60]!r}", block, set())
    gated = 0
    exempt: set[str] = set()
    for line in prd.splitlines():
        if not (match := PRD_ROW.match(line)):
            continue
        req = match.group(1)
        needed = set(sources.get(req, set()))
        for name, numbers in tests.items():
            if re.search(rf"\b{name}\b", line):
                needed |= numbers
        cites = any(c in line for c in PRD_GATE_CITATIONS)
        if req in NOT_ON_REGISTER:
            exempt.add(req)
            if needed:
                found.append(f"docs/prd.md {req} is listed as off the register but draws on INV-{sorted(needed)}")
            elif not cites:
                found.append(f"docs/prd.md {req} is listed as off the register and cites no gate test: a stale entry")
            continue
        if needed or cites:
            gated += 1
            check(f"docs/prd.md {req}", line, needed)
    for req in sorted(set(NOT_ON_REGISTER) - exempt):
        found.append(f"NOT_ON_REGISTER names {req}, which the PRD does not hold")
    if gated < 3:
        found.append(f"only {gated} PRD rows were read as gated")
    return found


def _records() -> dict[str, str]:
    return {name: (ROOT / name).read_text(encoding="utf-8") for name in ("docs/architecture.md", "AGENTS.md")}


def test_every_row_about_the_client_gates_names_its_fixture_rules_and_its_pins() -> None:
    """The M21-W3 review's rounds 3 and 4 (B1, R1): a row listed the forms its gate refuses in prose, and
    the prose was wider than the gate. A row that cites the compiled gate names the fixture's rules and
    says any form written another way is not held; one that cites a text pin names the pin tests; and the
    gaps they name are its "Partial:". Each refusal is watched on a planted row."""
    text = LIST.read_text(encoding="utf-8")
    rules = _fixture_rules()
    assert not gate_row_problems(text, rules), gate_row_problems(text, rules)
    gated = next(line for line in section(text, "The list").splitlines()
                 if ROW.match(line) and "`make client-decls`" in line and "`tests/unit/test_router_hints.py::" in line)
    unsaid = text.replace(gated, COMPILED.sub("", gated, count=1), 1)
    assert any("fixture's rules" in p for p in gate_row_problems(unsaid, rules))
    unknown = text.replace(gated, re.sub(r"rules? `[^`]+`", "rule `no such rule`", gated, count=1), 1)
    assert any("rules the fixture does not have" in p for p in gate_row_problems(unknown, rules))
    other = text.replace(gated, re.sub(r"is not held \(G-\d+", "is not held (G-99", gated, count=1), 1)
    assert any("its Partial: names" in p for p in gate_row_problems(other, rules))
    pinless = text.replace(gated, PINS.sub("", gated, count=1), 1)
    assert any("does not name it" in p for p in gate_row_problems(pinless, rules))


def test_the_gap_table_and_the_count_line_match_the_rows() -> None:
    """The M21-W3 review's round 4 (M1): a gap's Rows column could drop a row that names it, and the count
    line's words were not read."""
    text = LIST.read_text(encoding="utf-8")
    assert not table_problems(text), table_problems(text)
    gap = next(line for line in section(text, "Gaps").splitlines() if GAP.match(line) and ", INV-" in line.split(" | ")[1])
    dropped = text.replace(gap, gap.replace(", INV-", ", XNV-", 1), 1)
    assert any("the rows that name it" in p for p in table_problems(dropped))
    miscounted = re.sub(r"(\d+) gaps are open", lambda m: f"{int(m.group(1)) + 1} gaps are open", text, count=1)
    assert any("the count line says" in p for p in table_problems(miscounted))


def test_no_record_restates_a_client_gates_property_without_its_row() -> None:
    """The M21-W3 review's rounds 3 and 4 (B2, R1): `docs/architecture.md`, REQ-RTR-004 and REQ-CMB-004
    stated what a gate holds flatly, and round 5's REQ-DTL-001 cited a pin no register row cites. A record
    outside the register that names a client gate, a PRD row that draws on a gated row (its source, or a
    test it cites), and a PRD row that cites any gate test points at the row instead, unless the PRD row
    is listed in NOT_ON_REGISTER with its reason. Round 6's M4: a row naming a gate test without its file
    was not read."""
    register = LIST.read_text(encoding="utf-8")
    prd = (ROOT / "docs" / "prd.md").read_text(encoding="utf-8")
    problems_now = pointer_problems(_records(), prd, register)
    assert not problems_now, problems_now
    stated = {"docs/architecture.md": "- `scripts/client_decl_gate.py`: the network belongs only to the client.\n"}
    assert pointer_problems(stated, prd, register)
    for req in ("REQ-RTR-004", "REQ-CMB-004", "REQ-DTL-001"):
        row = next(line for line in prd.splitlines() if line.startswith(f"| {req} |"))
        unpointed = prd.replace(row, POINTER.sub("held in part", row), 1)
        assert any(req in p for p in pointer_problems(_records(), unpointed, register)), req
    row = next(line for line in prd.splitlines() if line.startswith("| REQ-CMP-002 |"))
    bare = prd.replace(row, row[:-2] + " The detail pin (test_the_detail_screen_is_reachable_and_composes_nothing_itself) "
                       "holds that nothing on the screen is computed. |", 1)
    assert any("REQ-CMP-002" in p for p in pointer_problems(_records(), bare, register)), "a bare gate test name was not read"
