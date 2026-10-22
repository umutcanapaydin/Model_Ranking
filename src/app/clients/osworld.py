"""OSWorld-Verified from its own results workbook: client + parser (REQ-SRC-013, D-219).

The OSWorld team (XLANG Lab) publishes its verified board as one workbook, `osworld_verified_results.xlsx`, which its
page loads and averages in the browser. The site is "licensed under a Creative Commons Attribution-ShareAlike 4.0
International License"; it moved from `os-world.github.io`, which now redirects over plain HTTP, to
`osworld-v1.xlang.ai`, the one host this client asks.

D-219 clause 2 reads the rows the page's default "Foundation E2E GUI" tab shows that a catalogue can sell: approach type
`General model`, no extra accessibility tree and no coding action, at 100 steps, the budget most rows report (a run at
15 or 50 steps is another measurement). A model's score is the mean of its runs, as the page shows it, dated by its
latest run. Specialized GUI models and agentic frameworks are not read: a framework names a harness over a model, and
the specialized models are not catalogue models.

The workbook is read with the standard library (`zipfile` and `xml.parsers.expat`), so no dependency is added. The
parser refuses a document type and any entity declaration as it meets them, as `defusedxml` does, and a member that
unpacks past `MAX_MEMBER_BYTES` is refused before it is read. What the reader produces is bounded too: shared strings
resolved into cells may not pass `MAX_ROWS_CHARS`.
The client hands the parser the sheet's rows as one JSON list, so the build's one-string `RawSource` holds.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import math
import re
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Any
from xml.parsers import expat

from app.clients.protocols import MAX_RESPONSE_BYTES, SourceError, fetch_bounded_bytes
from app.workflows.schema import ScoreRow

SOURCE_NAME = "osworld_verified"
BENCHMARK = "OSWorld-Verified"
#: The share of tasks a run finished: the scale `% resolved` names on every task board here.
METRIC = "% resolved"
HARNESS = "OSWorld (100 steps)"
SITE_URL = "https://osworld-v1.xlang.ai/"
WORKBOOK_URL = "https://osworld-v1.xlang.ai/static/data/osworld_verified_results.xlsx"
_TIMEOUT_S = 60.0
#: The budget D-219 clause 2 reads: the one most rows report.
STEP_BUDGET = "100"
_APPROACH = "General model"
#: A member of the workbook may not unpack past this: the recorded sheet is under 2 MB.
MAX_MEMBER_BYTES = 16 * 1024 * 1024
#: What the reader may produce: every cell's resolved text, with the header name each row repeats as its key. A cell
#: `t="s"` copies a shared string, so a few KB of sheet can resolve to gigabytes, which `json.dumps` would then build
#: (the queue-1021 integration review's M1). The recorded board resolves to about 0.32 M characters; the cap is
#: `MAX_RESPONSE_BYTES`, the most any source's fetched body may hold: room for the board to grow a hundredfold, and no
#: more than a source's payload may be anywhere else.
MAX_ROWS_CHARS = MAX_RESPONSE_BYTES
#: How a workbook's members are compressed, and the flag an encrypted member carries.
_METHODS = (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
_ENCRYPTED = 0x1
#: What `zipfile` raises on broken fetched bytes: a bad CRC or header, a corrupt or cut stream, an offset that seeks
#: before the start (`ValueError`), a zip version no reader knows (`NotImplementedError`). Both calls that take these
#: touch only the fetched bytes, so the catch hides no builder bug (the queue-1021 integration review's M2, round 2).
_ZIP_ERRORS = (zipfile.BadZipFile, zlib.error, EOFError, ValueError, NotImplementedError, OSError)
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main "
_SHEET = re.compile(r"xl/worksheets/sheet\d+\.xml")
_COLUMN = re.compile(r"[A-Z]+")
#: Excel's day zero for the 1900 date system, as a workbook's serial dates count from it.
_EXCEL_EPOCH = dt.date(1899, 12, 30)


class OSWorldClient:
    """Production RawSource for the OSWorld-Verified workbook (D-001): one public file, from the site's own host."""

    name = SOURCE_NAME
    url = WORKBOOK_URL
    hosts: tuple[str, ...] = ("osworld-v1.xlang.ai",)

    def fetch_raw(self) -> str:
        data = fetch_bounded_bytes(WORKBOOK_URL, self.name, _TIMEOUT_S, hosts=self.hosts)
        # Unescaped, so the JSON is about as long as the text `MAX_ROWS_CHARS` bounds: escaping an astral character
        # makes twelve characters of one (the queue-1021 integration review's N2).
        return json.dumps(workbook_rows(data), ensure_ascii=False)


@dataclass
class _Node:
    """One element of a workbook part: what the reader below needs of a tree, and nothing else."""

    tag: str
    attrs: dict[str, str]
    children: list[_Node] = field(default_factory=list)
    text: str = ""

    def iter(self, tag: str) -> list[_Node]:
        """Every element with this tag, this one included, in document order. The walk keeps its own stack: a part
        nested past the recursion limit raised `RecursionError`, which no caller catches, so one file aborted the night
        (D-121; the queue-1021 integration review's M2)."""
        found: list[_Node] = []
        pending = [self]
        while pending:
            node = pending.pop()
            if node.tag == tag:
                found.append(node)
            pending.extend(reversed(node.children))
        return found

    def find(self, tag: str) -> _Node | None:
        return next((child for child in self.children if child.tag == tag), None)


def _refuse(*_: object) -> None:
    msg = f"{SOURCE_NAME}: a workbook part declares a document type or an entity, which a workbook never needs"
    raise SourceError(msg)


def _parse_xml(body: bytes, name: str) -> _Node:
    """A part's elements, read with expat and every document type and entity refused (no expansion bomb)."""
    parser = expat.ParserCreate(namespace_separator=" ")
    root = _Node("", {})
    stack = [root]
    # Each open element's text, collected in pieces and joined once at its end: expat may deliver text in many
    # pieces (one a character reference), and `+=` on each made the read quadratic (the queue-1021 integration
    # review's N1).
    pieces: list[list[str]] = [[]]

    def start(tag: str, attrs: dict[str, str]) -> None:
        node = _Node(tag, attrs)
        stack[-1].children.append(node)
        stack.append(node)
        pieces.append([])

    def end(_: str) -> None:
        stack.pop().text = "".join(pieces.pop())

    def text(data: str) -> None:
        pieces[-1].append(data)

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = text
    parser.StartDoctypeDeclHandler = _refuse
    parser.EntityDeclHandler = _refuse
    parser.UnparsedEntityDeclHandler = _refuse
    parser.ExternalEntityRefHandler = _refuse  # type: ignore[assignment]
    try:
        parser.Parse(body, True)
    except expat.ExpatError as exc:
        msg = f"{SOURCE_NAME}: {name} is not well-formed XML: {exc}"
        raise SourceError(msg) from exc
    if not root.children:
        msg = f"{SOURCE_NAME}: {name} holds no element"
        raise SourceError(msg)
    return root.children[0]


def _member(archive: zipfile.ZipFile, name: str) -> _Node:
    info = archive.getinfo(name)
    if info.file_size > MAX_MEMBER_BYTES:
        msg = f"{SOURCE_NAME}: {name} unpacks to {info.file_size} bytes, past the cap of {MAX_MEMBER_BYTES}"
        raise SourceError(msg)
    # A workbook's members are stored or deflated, never encrypted: every other method's decoder raises a class of
    # its own, so it is refused before it is read. What reading a stored or deflated member can raise (a CRC that a
    # lying size fails, a corrupt stream, a cut one) is bad input, not a builder bug: it fails this optional source,
    # never the night (D-121; the queue-1021 integration review's M2).
    if info.compress_type not in _METHODS or info.flag_bits & _ENCRYPTED:
        msg = f"{SOURCE_NAME}: {name} is encrypted or compressed as a workbook never is"
        raise SourceError(msg)
    try:
        body = archive.read(name)
    except _ZIP_ERRORS as exc:
        msg = f"{SOURCE_NAME}: {name} does not unpack: {exc}"
        raise SourceError(msg) from exc
    return _parse_xml(body, name)


def _text(element: _Node) -> str:
    return "".join(node.text for node in element.iter(f"{_NS}t"))


def workbook_rows(data: bytes) -> list[dict[str, str | None]]:
    """The first sheet's rows, each keyed by the header row's names; every value as the cell's text."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except _ZIP_ERRORS as exc:
        msg = f"{SOURCE_NAME}: the file is not a workbook: {exc}"
        raise SourceError(msg) from exc
    with archive:
        names = archive.namelist()
        sheets = sorted(name for name in names if _SHEET.fullmatch(name))
        if not sheets:
            msg = f"{SOURCE_NAME}: the workbook holds no sheet"
            raise SourceError(msg)
        shared = ([_text(item) for item in _member(archive, "xl/sharedStrings.xml").iter(f"{_NS}si")]
                  if "xl/sharedStrings.xml" in names else [])
        grid: list[dict[str, str | None]] = []
        for row in _member(archive, sheets[0]).iter(f"{_NS}row"):
            cells: dict[str, str | None] = {}
            for cell in row.iter(f"{_NS}c"):
                column = _COLUMN.match(cell.attrs.get("r", ""))
                if column is None:
                    continue
                value = cell.find(f"{_NS}v")
                kind = cell.attrs.get("t")
                if kind == "s" and value is not None and (value.text or "").isdigit() and int(value.text or 0) < len(shared):
                    cells[column.group()] = shared[int(value.text or 0)]
                elif kind == "inlineStr":
                    cells[column.group()] = _text(cell)
                else:
                    cells[column.group()] = value.text if value is not None else None
            grid.append(cells)
    if not grid:
        msg = f"{SOURCE_NAME}: the sheet holds no rows"
        raise SourceError(msg)
    return _keyed(grid)


def _keyed(grid: list[dict[str, str | None]]) -> list[dict[str, str | None]]:
    """Each row after the header keyed by the header's names, refused once their text passes `MAX_ROWS_CHARS`."""
    header = grid[0]
    rows: list[dict[str, str | None]] = []
    resolved = 0
    for cells in grid[1:]:
        named = {str(header.get(column) or column): value for column, value in cells.items()}
        resolved += sum(len(key) + len(value or "") for key, value in named.items())
        if resolved > MAX_ROWS_CHARS:
            msg = (f"{SOURCE_NAME}: the sheet's cells resolve to more than {MAX_ROWS_CHARS} characters, past the cap of "
                   f"{MAX_ROWS_CHARS}: a workbook that repeats its strings this often is not the board")
            raise SourceError(msg)
        rows.append(named)
    return rows


def _yes(value: object) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "y"}


def _score(value: object) -> float | None:
    try:
        score = float(str(value).strip())
    except ValueError:
        return None
    return score if math.isfinite(score) and 0 <= score <= 100 else None


def _date(value: object) -> str | None:
    try:
        serial = int(float(str(value)))
    except ValueError:
        return None
    return (_EXCEL_EPOCH + dt.timedelta(days=serial)).isoformat() if 0 < serial < 100_000 else None


def parse_osworld(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the workbook's rows into one row a general model at 100 steps; returns (rows, skipped).

    A run of a general model at 100 steps that is not a usable end-to-end score (no number, out of range, an extra
    accessibility tree or coding action) is skipped and counted, and so is the model it belongs to; a payload that is
    not the board fails the source.
    """
    try:
        workbook: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"{source}: the workbook's rows are not valid JSON: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(workbook, list):
        msg = f"{source}: the workbook's rows are not a list"
        raise SourceError(msg)
    runs: dict[str, list[float]] = {}
    dates: dict[str, list[str]] = {}
    refused: set[str] = set()
    skipped = 0
    for entry in workbook:
        if not isinstance(entry, dict) or entry.get("Approach type") != _APPROACH:
            continue
        if str(entry.get("Max steps")).strip() != STEP_BUDGET:
            continue
        model = entry.get("Model")
        if not isinstance(model, str) or not model.strip():
            continue
        name = model.strip()
        score = _score(entry.get("Success rate"))
        if score is None or _yes(entry.get("Additional a11y tree used")) or _yes(
                entry.get("Additional coding-based action")):
            skipped += 1
            refused.add(name)
            continue
        runs.setdefault(name, []).append(score)
        if (date := _date(entry.get("Date"))) is not None:
            dates.setdefault(name, []).append(date)
    rows = [
        ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=sum(scores) / len(scores),
            harness=HARNESS,
            run_date=max(dates[name]) if name in dates else None,
            cost_total=None,
            source=source,
            source_url=SITE_URL,
        )
        for name, scores in runs.items() if name not in refused
    ]
    if not rows:
        msg = f"{source}: the workbook holds no general model's run at {STEP_BUDGET} steps"
        raise SourceError(msg)
    return rows, skipped
