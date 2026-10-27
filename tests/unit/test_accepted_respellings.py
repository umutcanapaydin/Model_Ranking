"""#475 (D-228): a re-spelling the owner accepted, pair by pair, is neither a loss nor new.

LMArena re-spelled its `text_to_image` board on 2026-10-26, from slugs to display names, and removed none of
its 82 models. 27 names derive a new model id (`flux-2-max` -> `flux2-max`, `FLUX.2 [max]` -> `flux.2-max`),
so the board guards read 27 rows lost (D-159) and the novelty guards read the same 27 as new (D-132): the
hosted night refused, three times over. `data/accepted-cuts.yaml` could not say it: a cut excuses losses only,
on declared boards only. Its `respellings` list names each old -> new pair, under an ADR, with an expiry;
the guards judge a listed pair as the row it was, and only where it is a re-spelling: the old name and its
model left the board, the new name and its model arrived. Anything else is judged as before.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pytest

from app.workflows import refresh
from app.workflows.refresh import degradations, fingerprint_of, upward_anomalies

from .test_accepted_cuts import ACCEPTED_CUTS_FILE
from .test_refresh_board_ids import SLICE, _boards

OWN = "coding"
TODAY = dt.date(2026, 10, 27)
LOG = f"## D-228 — the probe's re-spelling\n\nAccepted for {OWN} and {SLICE.source}.\n"


def _re_derive(*indexes: int) -> object:
    """Each named probe re-spelled on both boards, its new name deriving a new id: `Probe 00` (`probe-00`)
    -> `PROBE.00` (`probe.00`), as `flux-2-max` became `FLUX.2 [max]`."""
    def change(conn: sqlite3.Connection) -> None:
        for i in indexes:
            conn.execute("INSERT INTO models (id, display, vendor) VALUES (?, ?, 'Probe')", (f"probe.{i:02d}", f"PROBE.{i:02d}"))
            conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES (?, 2.0, 6.0)", (f"probe.{i:02d}",))
            conn.execute("UPDATE scores SET raw_name = ?, model_id = ? WHERE raw_name = ?",
                         (f"PROBE.{i:02d}", f"probe.{i:02d}", f"Probe {i:02d}"))
    return change


def _pairs(*indexes: int) -> dict[str, str]:
    return {f"Probe {i:02d}": f"PROBE.{i:02d}" for i in indexes}


def _judged(tmp_path: Path, change: object, accepted: dict[str, dict[str, str]]) -> list[str]:
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", change))  # type: ignore[arg-type]
    assert live is not None and candidate is not None
    judged = refresh.respelled(candidate, live, accepted)
    assert judged.digest == candidate.digest  # what is published is the candidate, as built
    return degradations(live, judged, cuts={}) + upward_anomalies(live, judged)


def test_without_a_pair_four_re_derived_ids_are_refused_as_lost_and_new(tmp_path: Path) -> None:
    """The control, #475's shape: 4 of 12 re-derived on both boards, every guard fires."""
    reasons = _judged(tmp_path, _re_derive(0, 1, 2, 3), {})
    assert any(r.startswith(f"{OWN}'s board would lose 4 of 12") for r in reasons), reasons
    assert any(r.startswith(f"board {SLICE.source} would lose 4 of 12") for r in reasons), reasons
    assert any(r.startswith(f"{OWN} would be 4 of 12 models") for r in reasons), reasons


def test_an_accepted_re_spelling_is_neither_lost_nor_new(tmp_path: Path) -> None:
    accepted = {OWN: _pairs(0, 1, 2, 3), SLICE.source: _pairs(0, 1, 2, 3)}
    assert _judged(tmp_path, _re_derive(0, 1, 2, 3), accepted) == []


def test_a_pair_named_for_one_board_excuses_nothing_on_another(tmp_path: Path) -> None:
    reasons = _judged(tmp_path, _re_derive(0, 1, 2, 3), {OWN: _pairs(0, 1, 2, 3)})
    assert reasons and all(r.startswith(f"board {SLICE.source}") for r in reasons), reasons


def test_a_re_derived_row_no_pair_names_still_counts(tmp_path: Path) -> None:
    """One pair of four: three rows still lost and new, 3 of 12, at the quarter."""
    reasons = _judged(tmp_path, _re_derive(0, 1, 2, 3), {OWN: _pairs(0), SLICE.source: _pairs(0)})
    assert any(r.startswith(f"{OWN}'s board would lose 3 of 12") for r in reasons), reasons


def _onto_a_kept_model(conn: sqlite3.Connection) -> None:
    """`Probe 00`..`03` leave; their names arrive linked to `probe-11`, a model the board keeps."""
    for i in range(4):
        conn.execute("UPDATE scores SET raw_name = ?, model_id = 'probe-11' WHERE raw_name = ?",
                     (f"PROBE.{i:02d}", f"Probe {i:02d}"))


def test_a_pair_onto_a_model_the_board_kept_is_not_a_re_spelling(tmp_path: Path) -> None:
    """Four rows folded into a model already there are four models lost, whatever the pairs say."""
    accepted = {OWN: _pairs(0, 1, 2, 3), SLICE.source: _pairs(0, 1, 2, 3)}
    reasons = _judged(tmp_path, _onto_a_kept_model, accepted)
    assert any(r.startswith(f"{OWN} would lose 4 of 12 models") or r.startswith(f"{OWN}'s board")
               for r in reasons), reasons


def test_two_old_names_onto_one_new_model_excuse_neither(tmp_path: Path) -> None:
    """A pair maps one model to one model; two models arriving as one is not a re-spelling."""
    def merged(conn: sqlite3.Connection) -> None:
        _re_derive(0, 1, 2, 3, 4, 5)(conn)  # type: ignore[operator]
        for odd in (1, 3, 5):
            conn.execute("UPDATE scores SET model_id = ? WHERE model_id = ?", (f"probe.{odd - 1:02d}", f"probe.{odd:02d}"))

    pairs = _pairs(0, 1, 2, 3, 4, 5)
    reasons = _judged(tmp_path, merged, {OWN: pairs, SLICE.source: pairs})
    assert any(r.startswith(f"board {SLICE.source} would lose 6 of 12") for r in reasons), reasons


# --- The file: `respellings` beside `cuts` in `data/accepted-cuts.yaml`, under a cut's rules (D-221, D-223).

def _file(board: str = OWN, until: str | None = "2026-11-10", decision: str = "D-228",
          pairs: str = "      Probe 00: PROBE.00\n", extra: str = "") -> str:
    line = f"    until: {until}\n" if until is not None else ""
    return (f"cuts: []\nrespellings:\n  - board: {board}\n    decision: {decision}\n    reason: a probe\n{line}"
            f"    pairs:\n{pairs}{extra}")


def test_a_respelling_with_its_expiry_and_a_known_adr_parses() -> None:
    assert refresh.parse_accepted_respellings(_file(), today=TODAY, decisions=LOG) == {OWN: {"Probe 00": "PROBE.00"}}
    assert refresh.parse_accepted_respellings(_file(board=SLICE.source), today=TODAY, decisions=LOG) == {
        SLICE.source: {"Probe 00": "PROBE.00"}}


def test_the_cuts_parser_reads_a_file_that_also_holds_respellings() -> None:
    assert refresh.parse_accepted_cuts(_file(), today=TODAY, decisions=LOG) == {}


@pytest.mark.parametrize("raw", [
    _file(until=None),
    _file(until="2026-10-26"),
    _file(until="2026-11-27"),                                       # past D-223's 30 days
    _file(decision="D-999"),                                         # an ADR the log does not hold
    _file(board="no_such_board"),
    _file(pairs="      Probe 00: ''\n"),                             # a name with no letter or digit
    _file(pairs="      '!!': PROBE.00\n"),
    _file(pairs="      Probe 00: Probe 00\n"),                       # not a re-spelling
    _file(pairs="      Probe 00: PROBE.00\n      Probe 01: PROBE.00\n"),   # two old names, one new
    _file(pairs="      Probe 00: PROBE.00\n      PROBE.00: PROBE.01\n"),   # a chain
    _file(pairs="      - Probe 00\n"),                               # not a map
    _file(pairs="      {}\n"),
    _file(extra="    rows: [a]\n"),                                  # a cut's key on a re-spelling
    _file() + "  - board: coding\n    decision: D-228\n    reason: r\n    until: 2026-11-10\n"
              "    pairs:\n      Probe 01: PROBE.01\n",                # one board named twice
    "cuts: []\nrespellings: {}\n",
    "cuts: []\nrespellings: []\nextra: 1\n",
    "respellings: []\n",                                             # `cuts` stays required
], ids=["no-until", "expired", "past-the-cap", "unknown-adr", "unknown-board", "blank-new", "blank-old",
        "same-name", "two-onto-one", "a-chain", "pairs-a-list", "pairs-empty", "an-extra-key",
        "a-board-twice", "respellings-a-map", "an-unknown-top-key", "no-cuts"])
def test_a_respelling_that_bends_the_schema_fails_closed(raw: str) -> None:
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_respellings(raw, today=TODAY, decisions=LOG)


def test_the_adr_must_name_the_board_it_accepts() -> None:
    with pytest.raises(refresh.AcceptedCutError, match="does not name"):
        refresh.parse_accepted_respellings(_file(), today=TODAY, decisions="## D-228 — a probe\n\nNo board.\n")


# --- Through `refresh()`: the file on disk is what the night applies.

def _on_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str | None) -> None:
    path = tmp_path / "cuts" / "accepted-cuts.yaml"
    if text is not None:
        path.parent.mkdir()
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(refresh.load_accepted_cuts, "__defaults__", (path,))
    monkeypatch.setattr(refresh.load_accepted_respellings, "__defaults__", (path,))
    log = tmp_path / "decisions.md"
    log.write_text(LOG, encoding="utf-8")
    monkeypatch.setattr(refresh, "DECISIONS_PATH", log)


def _both_boards() -> str:
    until = dt.date.today() + dt.timedelta(days=10)
    pairs = "".join(f"      Probe {i:02d}: PROBE.{i:02d}\n" for i in range(4))
    return "cuts: []\nrespellings:\n" + "".join(
        f"  - board: {board}\n    decision: D-228\n    reason: a probe\n    until: {until}\n    pairs:\n{pairs}"
        for board in (OWN, SLICE.source))


def _night(tmp_path: Path) -> tuple[refresh.RefreshOutcome, int]:
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _re_derive(0, 1, 2, 3))  # type: ignore[arg-type]
        return 0

    return refresh.refresh(live, builder=build)


@pytest.mark.parametrize("on_disk", [True, False], ids=["the-pairs-on-disk", "no-file"])
def test_the_night_reads_the_respellings_through_its_real_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_disk: bool
) -> None:
    _on_disk(tmp_path, monkeypatch, _both_boards() if on_disk else None)
    outcome, code = _night(tmp_path)
    assert code == (refresh.EXIT_PUBLISHED if on_disk else refresh.EXIT_REFUSED), outcome.reason
    if on_disk:
        assert f"Probe 00 -> PROBE.00 on board {SLICE.source} and 1 more" in outcome.renamed, outcome.renamed
        assert outcome.largest_board_change is None, outcome.largest_board_change


def test_a_malformed_respellings_list_fails_the_night(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _on_disk(tmp_path, monkeypatch, _both_boards().replace("D-228", "D-22"))
    with pytest.raises(refresh.AcceptedCutError):
        _night(tmp_path)


def test_the_committed_file_parses() -> None:
    """The file the night reads is the schema, whatever it holds today."""
    refresh.load_accepted_cuts(ACCEPTED_CUTS_FILE)
    refresh.load_accepted_respellings(ACCEPTED_CUTS_FILE)
