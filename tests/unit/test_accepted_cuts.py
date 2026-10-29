"""#415 (D-220 clause 3): a cut the owner accepted is not a loss.

Epoch re-ran its chess board in 2026-10 and published 154 of the 245 models the served artifact held.
The owner accepted that cut once: `data/accepted-cuts.yaml` names the board and exactly the rows it
may lose. The D-164 guard stops counting those rows as lost, and only those: any other row lost is
judged as before, and a cut named for one board excuses nothing on another. A file that cannot be read
as the schema says fails the refresh (closed), never excuses everything.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from app.workflows import boards as declared_boards
from app.workflows import refresh
from app.workflows.refresh import degradations, fingerprint_of

from .test_refresh_board_ids import SLICE, _boards
from .test_review_need_base_policy import Repo, _brief

ACCEPTED_CUTS_FILE = Path(__file__).resolve().parents[2] / "data" / "accepted-cuts.yaml"

BOARD = f"board {SLICE.source}"


def _drop(*indexes: int) -> object:
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany("DELETE FROM scores WHERE source = ? AND raw_name = ?",
                         [(SLICE.source, f"Probe {i:02d}") for i in indexes])
    return change


def _judged(tmp_path: Path, change: object, cuts: dict[str, frozenset[str]],
            base: object = None) -> list[str]:
    def both(conn: sqlite3.Connection) -> None:
        if base is not None:
            base(conn)  # type: ignore[operator]
        change(conn)  # type: ignore[operator]

    live = fingerprint_of(_boards(tmp_path / "live.db", base))  # type: ignore[arg-type]
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", both))
    assert live is not None and candidate is not None
    return degradations(live, candidate, cuts=cuts)


def _names(*indexes: int) -> frozenset[str]:
    return frozenset(f"Probe {i:02d}" for i in indexes)


def test_without_a_cut_a_quarter_lost_is_refused(tmp_path: Path) -> None:
    """The control: three of twelve rows gone refuses the night (D-164 clause 2)."""
    reasons = _judged(tmp_path, _drop(0, 1, 2), cuts={})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_the_owner_accepted_is_not_a_loss(tmp_path: Path) -> None:
    assert _judged(tmp_path, _drop(0, 1, 2), cuts={SLICE.source: _names(0, 1, 2)}) == []


def test_a_row_lost_outside_the_accepted_cut_still_counts(tmp_path: Path) -> None:
    """Five rows gone, two of them named: three of twelve is still a quarter."""
    reasons = _judged(tmp_path, _drop(0, 1, 2, 3, 4), cuts={SLICE.source: _names(0, 1)})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_named_for_one_board_excuses_nothing_on_another(tmp_path: Path) -> None:
    other = next(board.source for board in declared_boards.uncovered() if board.source != SLICE.source)
    reasons = _judged(tmp_path, _drop(0, 1, 2), cuts={other: _names(0, 1, 2)})
    assert any(reason.startswith(BOARD) for reason in reasons), reasons


def test_a_cut_excuses_an_unlinked_row_by_its_spelling(tmp_path: Path) -> None:
    def unlinked(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET model_id = NULL WHERE source = ?", (SLICE.source,))

    assert _judged(tmp_path, _drop(0, 1, 2), cuts={SLICE.source: _names(0, 1, 2)}, base=unlinked) == []


def test_the_committed_file_holds_no_cut_once_epochs_chess_cut_is_retired() -> None:
    """D-221 clause 1 (#418): the epoch_chess cut is retired once both served artifacts hold Epoch's
    published board (the Mac at `release-55cf42e`, the hosted engine at `release-2a68ca4`)."""
    assert refresh.load_accepted_cuts(ACCEPTED_CUTS_FILE) == {}
    assert ACCEPTED_CUTS_FILE.read_text(encoding="utf-8").rstrip().endswith("cuts: []")


@pytest.mark.parametrize("raw", [
    "",                                                     # an empty file is not "no cuts"
    "cuts: []\nextra: 1\n",                                 # an unknown key
    "cuts:\n  - board: epoch_chess\n    rows: [a]\n",      # no decision, no reason
    "cuts:\n  - board: not_a_board\n    decision: D-220\n    reason: r\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: []\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: [1]\n",
])
def test_a_file_that_is_not_the_schema_fails_closed(raw: str) -> None:
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw)


def test_a_file_with_no_cuts_excuses_nothing() -> None:
    assert refresh.parse_accepted_cuts("cuts: []\n") == {}


# --- The release Tester's fault injections on #416 (2026-10-23): each test below went red on a fault
# the tests above stayed green on.

@pytest.mark.parametrize("raw", [
    "cuts: {}\n",                                           # `cuts` is not a list
    "cuts: epoch_chess\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: [a]\n    expires: never\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: [a]\n"
    "  - board: epoch_chess\n    decision: D-220\n    reason: r\n    rows: [b]\n",   # one board named twice
    "cuts:\n  - board: epoch_chess\n    decision: D-22\n    reason: r\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: 220\n    reason: r\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: see D-220\n    reason: r\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: '  '\n    rows: [a]\n",
    "cuts:\n  - board: epoch_chess\n    decision: D-220\n    reason: 1\n    rows: [a]\n",
], ids=["cuts-a-map", "cuts-a-string", "an-extra-key", "a-board-twice", "a-short-adr-id", "an-adr-number",
        "an-adr-in-prose", "a-blank-reason", "a-number-for-a-reason"])
def test_a_cut_that_bends_the_schema_fails_closed(raw: str) -> None:
    """D-220 clause 3: each cut has exactly its four keys, one board once, an ADR id and a reason."""
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw)


def test_an_unreadable_file_on_disk_raises_and_a_missing_one_excuses_nothing(tmp_path: Path) -> None:
    bad = tmp_path / "accepted-cuts.yaml"
    bad.write_text("cuts: {}\n", encoding="utf-8")
    with pytest.raises(refresh.AcceptedCutError):
        refresh.load_accepted_cuts(bad)
    assert refresh.load_accepted_cuts(tmp_path / "absent.yaml") == {}


def _second_spelling(*indexes: int, linked: bool) -> object:
    """A second row for each named probe, `Probe 00` beside `probe-00` (one spelling key) unlinked, or
    `Probe 00 alt` linked to the same model: a board of sixteen rows."""
    def change(conn: sqlite3.Connection) -> None:
        if not linked:
            conn.execute("UPDATE scores SET model_id = NULL WHERE source = ?", (SLICE.source,))
        for i in indexes:
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
                " source_url, observed_at) SELECT model_id, ?, source, benchmark, metric, score, harness,"
                " effort, source_url, observed_at FROM scores WHERE source = ? AND raw_name = ?",
                (f"Probe {i:02d} alt" if linked else f"probe-{i:02d}", SLICE.source, f"Probe {i:02d}"))
    return change


@pytest.mark.parametrize("linked", [False, True], ids=["unlinked", "linked"])
def test_a_named_row_excuses_one_row_not_every_row_of_its_model_or_key(tmp_path: Path, linked: bool) -> None:
    """D-220 clause 3 names rows, not models or keys. Sixteen rows; both rows of four probes go, and the
    cut names one spelling of each: four rows excused, four lost, a quarter, refused."""
    def both_spellings_gone(conn: sqlite3.Connection) -> None:
        for i in range(4):
            conn.execute("DELETE FROM scores WHERE source = ? AND raw_name IN (?, ?)",
                         (SLICE.source, f"Probe {i:02d}", f"Probe {i:02d} alt" if linked else f"probe-{i:02d}"))

    base = _second_spelling(0, 1, 2, 3, linked=linked)
    reasons = _judged(tmp_path, both_spellings_gone, cuts={SLICE.source: _names(0, 1, 2, 3)}, base=base)
    assert any(reason.startswith(f"{BOARD} would lose 4 of 16") for reason in reasons), reasons


def _cuts_on_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str | None) -> None:
    """Point the refresh at a cuts file of the test's own (`load_accepted_cuts` binds its path as a
    default, so the default is what is patched)."""
    path = tmp_path / "cuts" / "accepted-cuts.yaml"
    if text is not None:
        path.parent.mkdir()
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(refresh.load_accepted_cuts, "__defaults__", (path,))
    # D-228: the night reads the file's re-spellings too, from the same path, against the same log.
    monkeypatch.setattr(refresh.load_accepted_respellings, "__defaults__", (path,))
    # D-223 clause 3: the ADR a cut names must name its board, so the probe's cut gets a log of its own.
    log = tmp_path / "decisions.md"
    log.write_text(f"## D-220 — a probe's cut\n\nAccepted for {SLICE.source}.\n", encoding="utf-8")
    monkeypatch.setattr(refresh, "DECISIONS_PATH", log)


def _night_dropping_three(tmp_path: Path) -> tuple[Path, tuple[refresh.RefreshOutcome, int]]:
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _drop(0, 1, 2))  # type: ignore[arg-type]
        return 0

    return live, refresh.refresh(live, builder=build)


CUT_OF_THREE = (f"cuts:\n  - board: {SLICE.source}\n    decision: D-220\n    reason: a probe\n"
                f"    until: {dt.date.today() + dt.timedelta(days=10)}\n    rows: ['Probe 00', 'Probe 01', 'Probe 02']\n")


@pytest.mark.parametrize("on_disk", [True, False], ids=["the-cut-on-disk", "no-file"])
def test_the_refresh_reads_the_cuts_file_through_its_real_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_disk: bool
) -> None:
    """Through `refresh()`: the file on disk, not a `cuts=` argument, is what the nightly guard applies."""
    _cuts_on_disk(tmp_path, monkeypatch, CUT_OF_THREE if on_disk else None)
    _, (outcome, code) = _night_dropping_three(tmp_path)
    assert code == (refresh.EXIT_PUBLISHED if on_disk else refresh.EXIT_REFUSED), outcome.reason


def test_a_malformed_cuts_file_fails_the_night_and_leaves_the_live_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fails closed through `refresh()`: the cycle stops, is recorded as failed, publishes nothing."""
    _cuts_on_disk(tmp_path, monkeypatch, CUT_OF_THREE.replace("D-220", "D-22"))
    live = _boards(tmp_path / "advisor.db")
    before = live.read_bytes()

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _drop(0, 1, 2))  # type: ignore[arg-type]
        return 0

    with pytest.raises(refresh.AcceptedCutError):
        refresh.refresh(live, builder=build)
    assert live.read_bytes() == before
    record = json.loads(refresh.status_path(live).read_text(encoding="utf-8"))
    assert record["exit_code"] == refresh.EXIT_FAILED, record
    assert "AcceptedCutError" in record["reason"], record


def test_an_unparseable_or_unreadable_file_is_the_cuts_error(tmp_path: Path) -> None:
    """Both fail-closed branches raise the one error the refresh records: broken YAML, and a path that
    cannot be read (here a directory where the file should be)."""
    with pytest.raises(refresh.AcceptedCutError, match="unparseable YAML"):
        refresh.parse_accepted_cuts("cuts: [unclosed\n")
    (tmp_path / "accepted-cuts.yaml").mkdir()
    with pytest.raises(refresh.AcceptedCutError, match="cannot be read"):
        refresh.load_accepted_cuts(tmp_path / "accepted-cuts.yaml")


# --- #418 (D-221): a cut excuses rows by their own name, carries an expiry, names an ADR the log holds,
# and is routed to a security review.

TODAY = dt.date(2026, 10, 24)
LOG = f"## D-220 — the cut that accepted it\n\nAccepted for {SLICE.source}.\n"


def _cut(until: str | None = "2026-11-10", decision: str = "D-220") -> str:
    line = f"    until: {until}\n" if until is not None else ""
    return (f"cuts:\n  - board: {SLICE.source}\n    decision: {decision}\n    reason: a probe\n{line}"
            "    rows: ['Probe 00']\n")


def test_a_cut_with_its_expiry_and_a_known_adr_parses() -> None:
    assert refresh.parse_accepted_cuts(_cut(), today=TODAY, decisions=LOG) == {SLICE.source: frozenset({"Probe 00"})}


@pytest.mark.parametrize(("raw", "why"), [
    (_cut(until=None), "no until"),
    (_cut(until="2026-10-23"), "expired"),
    (_cut(until="soon"), "not a date"),
    (_cut(decision="D-999"), "an ADR the log does not hold"),
], ids=["no-until", "expired", "until-not-a-date", "unknown-adr"])
def test_a_cut_without_a_live_expiry_or_a_known_adr_fails_closed(raw: str, why: str) -> None:
    """D-221 clauses 3 and 4: never ignored, never applied -- the refresh stops."""
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw, today=TODAY, decisions=LOG)


def test_a_cut_expiring_today_still_applies() -> None:
    assert refresh.parse_accepted_cuts(_cut(until="2026-10-24"), today=TODAY, decisions=LOG)


def _alt_spellings(conn: sqlite3.Connection) -> None:
    """A second, linked spelling for six probes: `Probe 00 alt` beside `Probe 00`, eighteen rows."""
    conn.executemany(
        "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, source_url, observed_at)"
        " VALUES (?, ?, ?, ?, 'elo', ?, 'arena-crowd', 'fixture://x', 't')",
        [(f"probe-{i:02d}", f"Probe {i:02d} alt", SLICE.source, SLICE.benchmark, 1300.0 + i) for i in range(6)])


def _drop_alts(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM scores WHERE source = ? AND raw_name LIKE '% alt'", (SLICE.source,))


def test_a_cut_naming_a_models_kept_spelling_excuses_none_of_its_lost_rows(tmp_path: Path) -> None:
    """D-221 clause 2 (the #416 security delta's M2): six `alt` rows go, a third of eighteen; the cut names
    the six spellings that STAY. By model it excused all six; by name it excuses none."""
    reasons = _judged(tmp_path, _drop_alts, cuts={SLICE.source: _names(0, 1, 2, 3, 4, 5)}, base=_alt_spellings)
    assert any(reason.startswith(f"{BOARD} would lose 6 of 18") for reason in reasons), reasons


def test_a_cut_naming_the_lost_spellings_excuses_them(tmp_path: Path) -> None:
    lost = frozenset(f"Probe {i:02d} alt" for i in range(6))
    assert _judged(tmp_path, _drop_alts, cuts={SLICE.source: lost}, base=_alt_spellings) == []


def test_review_need_reads_the_file_the_refresh_reads() -> None:
    """D-221 clause 4, derived, not typed twice: the path review-need routes is the refresh's own."""
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location("review_need_418", root / "scripts" / "review_need.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert str(refresh.ACCEPTED_CUTS_PATH.relative_to(root)) in module.EXCEPTION_FILES


@pytest.mark.parametrize(("mode", "want"), [("light", "review-need: security"),
                                            ("heavy", "review-need: code-reviewer+security")])
def test_a_change_to_the_cuts_file_goes_to_a_security_review(tmp_path: Path, mode: str, want: str) -> None:
    """D-221 clause 4: in either mode, whatever else the range holds."""
    repo = Repo(tmp_path / mode, _brief(mode))
    repo.write("data/accepted-cuts.yaml", "cuts: []\n")
    repo.commit("data: a cut")
    _, last, out = repo.need()
    assert last == want, out
    assert "policy edit: data/accepted-cuts.yaml" in out, out


@pytest.mark.parametrize("name", ["!!!", "\u4e2d\u6587"], ids=["punctuation", "no-latin-letter"])
def test_a_cut_name_with_an_empty_spelling_key_fails_closed(name: str) -> None:
    """The #418 security review's M3: such a name keys to "", and would excuse any lost unlinked row that does."""
    raw = _cut().replace("['Probe 00']", f"['{name}']")
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw, today=TODAY, decisions=LOG)


# --- #429 (D-223 clauses 2 and 3): an expiry no more than 30 days out, and a strict ADR check.

@pytest.mark.parametrize(("raw", "log"), [
    (_cut(until="2026-11-24"), LOG),                                            # 31 days out
    (_cut(until="9999-12-31"), LOG),                                            # the review's M1
    (_cut(), "```\n" + LOG + "```\n"),                                          # only in a code block
    (_cut(), LOG + "\n**Superseded by D-221 (2026-10-24)**: replaced.\n"),       # superseded
    (_cut(), "## D-220 — the cut that accepted it\n\nAccepted for another board.\n"),  # not this board
], ids=["31-days-out", "year-9999", "in-a-code-block", "superseded", "names-another-board"])
def test_a_cut_past_the_cap_or_under_a_weak_adr_fails_closed(raw: str, log: str) -> None:
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(raw, today=TODAY, decisions=log)


def test_an_expiry_thirty_days_out_and_a_four_digit_adr_parse() -> None:
    """The cap's edge applies, and an ADR id past D-999 (the review's R2) is read."""
    log = f"## D-1000 — a later cut\n\nAccepted for {SLICE.source}.\n"
    raw = _cut(until="2026-11-23", decision="D-1000")
    assert refresh.parse_accepted_cuts(raw, today=TODAY, decisions=log) == {SLICE.source: frozenset({"Probe 00"})}


def test_an_unreadable_decision_log_is_the_cuts_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The review's R2: the branch that reads the log fails closed when the log cannot be read."""
    monkeypatch.setattr(refresh, "DECISIONS_PATH", tmp_path / "absent.md")
    with pytest.raises(refresh.AcceptedCutError, match="cannot be read"):
        refresh.parse_accepted_cuts(_cut(), today=TODAY)


# --- The release v0.2.0 Tester: each schema check refuses on its own branch.
#
# D-221 made `until:` a required key, so every older malformed case above, written without it, is now refused by the
# key-set check before it reaches the check it was written for. With the declared-board, named-twice, ADR-shape,
# reason or rows check removed, the suite stayed green. Each case below is a valid cut but for one field, and the
# message pins the check that refuses it.

def _one_cut(board: str = SLICE.source, decision: object = "D-220", reason: object = "a probe",
             rows: str = "['Probe 00']") -> str:
    return (f"  - board: {board}\n    decision: {decision}\n    reason: {reason}\n    until: 2026-11-10\n"
            f"    rows: {rows}\n")


@pytest.mark.parametrize(("raw", "refusal"), [
    ("cuts:\n" + _one_cut(board="not_a_board"), "is not a declared board"),
    ("cuts:\n" + _one_cut() + _one_cut(rows="['Probe 01']"), "is named twice"),
    ("cuts:\n" + _one_cut(decision="D-22"), "is not an ADR id"),
    ("cuts:\n" + _one_cut(decision="220"), "is not an ADR id"),
    ("cuts:\n" + _one_cut(decision="see D-220"), "is not an ADR id"),
    ("cuts:\n" + _one_cut(reason="'  '"), "gives no reason"),
    ("cuts:\n" + _one_cut(reason="1"), "gives no reason"),
    ("cuts:\n" + _one_cut(rows="[]"), "rows are not a list of names"),
    ("cuts:\n" + _one_cut(rows="[1]"), "rows are not a list of names"),
], ids=["undeclared-board", "a-board-twice", "a-short-adr-id", "an-adr-number", "an-adr-in-prose", "a-blank-reason",
        "a-number-for-a-reason", "no-rows", "a-number-for-a-row"])
def test_each_schema_check_refuses_a_cut_that_is_valid_but_for_its_field(raw: str, refusal: str) -> None:
    """# covers D-220 clause 3, D-221, INV-54: the cut fails closed, and by the check its field names."""
    with pytest.raises(refresh.AcceptedCutError, match=refusal):
        refresh.parse_accepted_cuts(raw, today=TODAY, decisions=LOG)
