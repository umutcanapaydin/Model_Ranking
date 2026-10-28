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
from .test_refresh_board_ids import SLICE, Change, _boards

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


# --- D-228 clause 2, shape by shape (the release Tester's delta round 2026-10-27b). A pair that is not a
# re-spelling changes NOTHING `respelled` returns; one that is reads every row as the row it was. Each shape
# below fails exactly one of `_respelled_ids`' conditions, so each condition is held on its own: the
# guard-level tests above reach "onto a kept model" only through the one-to-one rule, and never reach the old
# model kept, the old name kept, or a new name already served.

def _rows(sql: str, *values: object) -> Change:
    return lambda conn: conn.execute(sql, values)


def _then(*changes: Change) -> Change:
    def change(conn: sqlite3.Connection) -> None:
        for step in changes:
            step(conn)
    return change


def _add(model: str, raw: str, harness: str = "arena-crowd") -> Change:
    """One more row on `SLICE`, `raw` linked to `model`."""
    return _rows("INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, source_url,"
                 " observed_at) VALUES (?, ?, ?, ?, 'elo', 1300.0, ?, 'fixture://x', 't')",
                 model, raw, SLICE.source, SLICE.benchmark, harness)


def _new_model(model: str) -> Change:
    return _then(_rows("INSERT INTO models (id, display, vendor) VALUES (?, ?, 'Probe')", model, model.upper()),
                 _rows("INSERT INTO px_median (model_id, in_m, out_m) VALUES (?, 2.0, 6.0)", model))


_RE_DERIVED = _re_derive(0)  # `Probe 00` (`probe-00`) -> `PROBE.00` (`probe.00`), on both boards
_BOTH = {OWN: _pairs(0), SLICE.source: _pairs(0)}

#: shape -> (the served board's change, the candidate's change, the pairs accepted).
_NOT_A_RE_SPELLING: dict[str, tuple[Change | None, Change, dict[str, dict[str, str]]]] = {
    # The old model stayed on the board (`Probe 01` now links to it): `was[old] not in after`.
    "the-old-model-stayed": (None, _then(_RE_DERIVED, _rows(  # type: ignore[arg-type]
        "UPDATE scores SET model_id = 'probe-00' WHERE raw_name = 'Probe 01'")), _BOTH),
    # The new name arrived under a model the board already had: `now[new] not in before`.
    "onto-a-kept-model": (None, _then(_RE_DERIVED, _rows(  # type: ignore[arg-type]
        "UPDATE scores SET model_id = 'probe-11' WHERE raw_name = 'PROBE.00'")), _BOTH),
    # The old NAME is still on the board, under another new model: `old not in now`.
    "the-old-name-stayed": (None, _then(_RE_DERIVED, _new_model("probe.99"), _rows(  # type: ignore[arg-type]
        "UPDATE scores SET raw_name = 'Probe 00', model_id = 'probe.99' WHERE raw_name = 'Probe 01'")), _BOTH),
    # The new name was already on the served board (a second row of `probe-11`): `new not in was`.
    "the-new-name-was-served": (_add("probe-11", "PROBE.00"),
                                _then(_RE_DERIVED, _add("probe-11", "Probe 11b")),  # type: ignore[arg-type]
                                {SLICE.source: _pairs(0)}),
    # #478: the old model had a second name the pairs do not list, and it arrives re-spelled under the same
    # new model. One pair would move the whole model, the unlisted row with it: a pair names rows, not models.
    "a-name-the-pairs-do-not-list": (_add("probe-00", "Probe 00 alt"),
                                     _then(_add("probe-00", "Probe 00 alt"), _RE_DERIVED,  # type: ignore[arg-type]
                                           _rows("UPDATE scores SET raw_name = 'PROBE.00 ALT', model_id = 'probe.00'"
                                                 " WHERE raw_name = 'Probe 00 alt'")),
                                     {SLICE.source: _pairs(0)}),
    # The #477 security round's M4: both names of the old model are listed, but the second pair's new name was
    # already served under another model (`probe-11`). Only one pair is a re-spelling, so the model stays.
    "a-sibling-pair-that-is-not-a-re-spelling": (
        _then(_add("probe-00", "Probe 00 alt"), _add("probe-11", "PROBE.00 ALT")),  # type: ignore[arg-type]
        _then(_add("probe-00", "Probe 00 alt"), _add("probe-11", "PROBE.00 ALT"),  # type: ignore[arg-type]
              _rows("DELETE FROM scores WHERE raw_name = 'PROBE.00 ALT'"), _RE_DERIVED,
              _rows("UPDATE scores SET raw_name = 'PROBE.00 ALT', model_id = 'probe.00' WHERE raw_name = 'Probe 00 alt'")),
        {SLICE.source: {**_pairs(0), "Probe 00 alt": "PROBE.00 ALT"}}),
    # The night after the publish: the served board holds the new name, so the pair is inert (D-228,
    # "Mitigation if violated").
    "after-the-publish": (_RE_DERIVED, _RE_DERIVED, _BOTH),  # type: ignore[dict-item]
}


@pytest.mark.parametrize("shape", sorted(_NOT_A_RE_SPELLING))
def test_a_pair_that_is_not_a_re_spelling_changes_nothing(tmp_path: Path, shape: str) -> None:
    served, change, accepted = _NOT_A_RE_SPELLING[shape]
    live = fingerprint_of(_boards(tmp_path / "live.db", served))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", change))
    assert live is not None and candidate is not None
    assert refresh.respelled(candidate, live, accepted) == candidate, f"{shape} moved the candidate"


def test_a_re_spelling_reads_every_row_as_the_row_it_was(tmp_path: Path) -> None:
    """The shapes' control: a re-spelled model with two rows on a board, beside a row linked to no model,
    reads as the board it was, row for row, while the digest stays the candidate's."""
    both_nights = _then(_add("probe-00", "Probe 00", harness="a-second-harness"),
                        _rows("UPDATE scores SET model_id = NULL WHERE raw_name = 'Probe 05' AND source = ?",
                              SLICE.source))
    live = fingerprint_of(_boards(tmp_path / "live.db", both_nights))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _then(both_nights, _RE_DERIVED)))  # type: ignore[arg-type]
    assert live is not None and candidate is not None
    judged = refresh.respelled(candidate, live, _BOTH)
    assert candidate.boards != live.boards, "the control re-derives no id"
    assert judged.board == live.board and judged.boards == live.boards and judged.models == live.models
    assert judged.digest == candidate.digest


def test_a_model_with_two_names_moves_when_the_pairs_list_both(tmp_path: Path) -> None:
    """#478's control: the same model, both of its names listed, reads as the board it was."""
    served = _add("probe-00", "Probe 00 alt")
    live = fingerprint_of(_boards(tmp_path / "live.db", served))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _then(served, _RE_DERIVED, _rows(  # type: ignore[arg-type]
        "UPDATE scores SET raw_name = 'PROBE.00 ALT', model_id = 'probe.00' WHERE raw_name = 'Probe 00 alt'"))))
    assert live is not None and candidate is not None
    both = {SLICE.source: {**_pairs(0), "Probe 00 alt": "PROBE.00 ALT"}}
    judged = refresh.respelled(candidate, live, both)
    assert candidate.boards[SLICE.source] != live.boards[SLICE.source], "the control re-derives no id"
    assert judged.boards[SLICE.source] == live.boards[SLICE.source]


@pytest.mark.parametrize("raw", [
    "cuts: []\ncuts: []\n",
    "cuts: []\nrespellings:\n  - board: coding\n    decision: D-228\n    reason: r\n    until: 2026-10-30\n"
    "    pairs:\n      \"Probe 00\": \"PROBE.00\"\n      \"Probe 00\": \"PROBE.01\"\n",
])
def test_a_key_written_twice_fails_closed(raw: str) -> None:
    """#479: YAML keeps the last of two equal keys, so a second `pairs` entry or a second `cuts` list would
    silently replace the first. The file is refused instead."""
    with pytest.raises(refresh.AcceptedCutError, match="twice"):
        refresh.parse_accepted_respellings(raw, today=TODAY, decisions=LOG)
    with pytest.raises(refresh.AcceptedCutError, match="twice"):
        refresh.parse_accepted_cuts(raw, today=TODAY, decisions=LOG)


def test_the_committed_file_holds_no_re_spelling_once_a_night_published_the_new_names() -> None:
    """#477 (1): the hosted nights of 2026-10-27 and 2026-10-28 published text_to_image's new names, so the
    D-228 entry is inert, and past 2026-11-10 it would fail every night. It is removed."""
    assert refresh.load_accepted_respellings(ACCEPTED_CUTS_FILE) == {}


def test_the_suite_reads_no_committed_policy_by_default() -> None:
    """#477 (2): a test that runs the refresh reads a fixture's empty policy, never the committed file, whose
    `until:` dates would turn the whole suite red on the day they pass. Only the tests that name
    ACCEPTED_CUTS_FILE read it."""
    assert refresh.load_accepted_cuts.__defaults__ != (refresh.ACCEPTED_CUTS_PATH,)
    assert refresh.load_accepted_respellings.__defaults__ != (refresh.ACCEPTED_CUTS_PATH,)
    assert refresh.load_accepted_cuts() == {} and refresh.load_accepted_respellings() == {}


def test_a_merge_key_fails_closed() -> None:
    """The #477 security round's M1: `<<: *pairs` copies one mapping into another, and the mapping's own key then
    silently replaces the copied one, which is #479's override by another road."""
    raw = ("cuts: []\nrespellings:\n  - board: coding\n    decision: D-228\n    reason: r\n    until: 2026-10-30\n"
           "    pairs: &p\n      \"Probe 00\": \"PROBE.00\"\n  - board: SLICE\n    decision: D-228\n    reason: r\n"
           "    until: 2026-10-30\n    pairs:\n      <<: *p\n      \"Probe 00\": \"PROBE.09\"\n").replace("SLICE", SLICE.source)
    with pytest.raises(refresh.AcceptedCutError, match="merge key"):
        refresh.parse_accepted_respellings(raw, today=TODAY, decisions=LOG)


def test_a_wide_mapping_is_walked_in_linear_time() -> None:
    """The #477 security round's M2: `list.count` per key made the repeated-key walk quadratic (40,000 keys took
    115 s). The walk alone, on a composed mapping of 40,000 keys, counted once, is well under two seconds."""
    import time

    import yaml

    from app.workflows import yaml_guard

    node = yaml.compose("".join(f"k{i}: 1\n" for i in range(40_000)), Loader=yaml.SafeLoader)
    started = time.perf_counter()
    yaml_guard._refuse_repeated_keys(node, "a wide mapping")
    assert time.perf_counter() - started < 2.0


@pytest.mark.parametrize("board", ["[coding]", "{coding: 1}"])
def test_a_board_that_is_not_a_name_fails_closed(board: str) -> None:
    """#479's second clause (the #477 security round's M3): a list or a mapping as `board:` raised `TypeError`."""
    respelling = (f"cuts: []\nrespellings:\n  - board: {board}\n    decision: D-228\n    reason: r\n"
                  "    until: 2026-10-30\n    pairs:\n      \"Probe 00\": \"PROBE.00\"\n")
    cut = f"cuts:\n  - board: {board}\n    decision: D-228\n    reason: r\n    until: 2026-10-30\n    rows: [a]\n"
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_respellings(respelling, today=TODAY, decisions=LOG)
    with pytest.raises(refresh.AcceptedCutError):
        refresh.parse_accepted_cuts(cut, today=TODAY, decisions=LOG)
