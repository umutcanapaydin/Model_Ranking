"""#605 (D-251): names the owner accepted as new on one board are not counted as growth there.

The hosted night of 2026-11-11 refused: Terminal-Bench 4.0, `computer-use`'s own board, took a batch of
submission files its publisher merged at once, 10 names the served artifact had never seen. D-132 refuses a
board that is more than a quarter new overnight and "a legitimate jump is published by hand", but
`data/accepted-cuts.yaml` could excuse only losses (D-220) and re-spellings (D-228). Its `additions` list names
each accepted raw name on one board, under an ADR, with an expiry. The growth guards judge a listed name's new
rows as already seen on that board alone, and on a surface's own board its model as already ranked. A name
not listed counts as before, and so does a listed name whose model also carries a name not listed.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pytest

from app.workflows import refresh
from app.workflows.refresh import degradations, fingerprint_of, upward_anomalies

from .test_refresh_board_ids import SLICE, Change, _boards

OWN = "coding"
TODAY = dt.date(2026, 11, 11)
LOG = f"## D-251 — the probe's additions\n\nAccepted for {OWN} and {SLICE.source}.\n"


def _arrive(count: int, *, second_name: int | None = None) -> Change:
    """`count` models neither board had, one row each on both boards (`Fresh 0`..). With `second_name`, that
    model also arrives under a second name, `Fresh <n> (alt)`, on both boards."""
    def change(conn: sqlite3.Connection) -> None:
        for source, benchmark, metric, harness in (("swebench", "SWE-bench Verified", "% resolved", "none"),
                                                   (SLICE.source, SLICE.benchmark, "elo", "arena-crowd")):
            names = [(f"fresh-{i}", f"Fresh {i}") for i in range(count)]
            if second_name is not None:
                names.append((f"fresh-{second_name}", f"Fresh {second_name} (alt)"))
            conn.executemany(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
                " source_url, observed_at) VALUES (?, ?, ?, ?, ?, 50, ?, 'unspecified', 'fixture://x', 't')",
                [(model, raw, source, benchmark, metric, harness) for model, raw in names],
            )
    return change


def _names(*indexes: int) -> frozenset[str]:
    return frozenset(f"Fresh {i}" for i in indexes)


def _judged(tmp_path: Path, change: Change, accepted: dict[str, frozenset[str]],
            base: Change | None = None) -> list[str]:
    def both(conn: sqlite3.Connection) -> None:
        if base is not None:
            base(conn)
        change(conn)

    live = fingerprint_of(_boards(tmp_path / "live.db", base))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", both))
    assert live is not None and candidate is not None
    judged = refresh.added(candidate, live, accepted)
    assert judged.digest == candidate.digest  # what is published is the candidate, as built
    return degradations(live, judged, cuts={}) + upward_anomalies(live, judged)


def test_without_additions_five_new_models_are_refused_on_both_boards(tmp_path: Path) -> None:
    """The control, #605's shape: 5 of 17 rows new on each board, over the quarter."""
    reasons = _judged(tmp_path, _arrive(5), {})
    assert any(r.startswith(f"{OWN}'s board would be 5 of 17 rows") for r in reasons), reasons
    assert any(r.startswith(f"board {SLICE.source} would be 5 of 17 rows") for r in reasons), reasons


def test_accepted_additions_are_not_growth(tmp_path: Path) -> None:
    accepted = {OWN: _names(0, 1, 2, 3, 4), SLICE.source: _names(0, 1, 2, 3, 4)}
    assert _judged(tmp_path, _arrive(5), accepted) == []


def test_additions_named_for_one_board_excuse_nothing_on_another(tmp_path: Path) -> None:
    reasons = _judged(tmp_path, _arrive(5), {OWN: _names(0, 1, 2, 3, 4)})
    assert reasons and all(r.startswith(f"board {SLICE.source}") for r in reasons), reasons


def test_a_new_name_no_addition_lists_still_counts(tmp_path: Path) -> None:
    """Eight arrive, two are listed: 6 of 18 is still over the quarter on both boards."""
    accepted = {OWN: _names(0, 1), SLICE.source: _names(0, 1)}
    reasons = _judged(tmp_path, _arrive(8), accepted)
    assert any(r.startswith(f"{OWN}'s board would be 6 of 18 rows") for r in reasons), reasons
    assert any(r.startswith(f"board {SLICE.source} would be 6 of 18 rows") for r in reasons), reasons


def test_a_model_with_a_name_not_listed_is_not_excused(tmp_path: Path) -> None:
    """#478's lesson: a name is accepted, a model is not. `fresh-0` arrives as `Fresh 0` and `Fresh 0 (alt)`;
    listing only `Fresh 0` leaves both of its rows counted (with three unlisted: 5 of 18, over the quarter)."""
    accepted = {OWN: _names(0), SLICE.source: _names(0)}
    reasons = _judged(tmp_path, _arrive(4, second_name=0), accepted)
    assert any(r.startswith(f"{OWN}'s board would be 5 of 17 rows") for r in reasons), reasons


def test_listing_every_name_of_a_two_named_model_excuses_both_rows(tmp_path: Path) -> None:
    names = _names(0, 1, 2, 3) | {"Fresh 0 (alt)"}
    assert _judged(tmp_path, _arrive(4, second_name=0), {OWN: names, SLICE.source: names}) == []


def _a_quarter_lost(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM scores WHERE source = ? AND raw_name IN ('Probe 00', 'Probe 01', 'Probe 02')",
                 (SLICE.source,))


def test_an_addition_never_excuses_a_loss(tmp_path: Path) -> None:
    """Listing names the board already serves, or lost, changes nothing: additions only ever remove NEW rows."""
    served = frozenset({"Probe 00", "Probe 01", "Probe 02", "Probe 03"})
    reasons = _judged(tmp_path, _a_quarter_lost, {SLICE.source: served})
    assert any(r.startswith(f"board {SLICE.source} would lose 3 of 12") for r in reasons), reasons


def test_a_board_returning_is_untouched(tmp_path: Path) -> None:
    """A board the served artifact does not hold passes as returning (D-132); an addition does not make
    its other rows count as new."""
    def no_slice(conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM scores WHERE source = ?", (SLICE.source,))

    live = fingerprint_of(_boards(tmp_path / "live.db", no_slice))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _arrive(5)))
    assert live is not None and candidate is not None
    judged = refresh.added(candidate, live, {SLICE.source: _names(0)})
    assert judged.boards[SLICE.source] == candidate.boards[SLICE.source]
    assert not [r for r in upward_anomalies(live, judged) if r.startswith(f"board {SLICE.source}")]


def test_a_first_artifact_has_nothing_to_add_to(tmp_path: Path) -> None:
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _arrive(5)))
    assert candidate is not None
    assert refresh.added(candidate, None, {OWN: _names(0)}) is candidate


# --- The file: `additions` beside `cuts` in `data/accepted-cuts.yaml`, under a cut's rules (D-221, D-223).

def _file(board: str = OWN, until: str | None = "2026-11-25", decision: str = "D-251",
          names: str = "      - Fresh 0\n", extra: str = "") -> str:
    line = f"    until: {until}\n" if until is not None else ""
    return (f"cuts: []\nadditions:\n  - board: {board}\n    decision: {decision}\n    reason: a probe\n{line}"
            f"    names:\n{names}{extra}")


def test_an_addition_with_its_expiry_and_a_known_adr_parses() -> None:
    assert refresh.parse_accepted_additions(_file(), today=TODAY, decisions=LOG) == {OWN: frozenset({"Fresh 0"})}
    assert refresh.parse_accepted_additions(_file(board=SLICE.source), today=TODAY, decisions=LOG) == {
        SLICE.source: frozenset({"Fresh 0"})}


def test_a_file_without_additions_accepts_none() -> None:
    assert refresh.parse_accepted_additions("cuts: []\n", today=TODAY, decisions=LOG) == {}


def test_additions_sit_beside_respellings() -> None:
    raw = _file() + "respellings: []\n"
    assert refresh.parse_accepted_additions(raw, today=TODAY, decisions=LOG) == {OWN: frozenset({"Fresh 0"})}
    assert refresh.parse_accepted_respellings(raw, today=TODAY, decisions=LOG) == {}
    assert refresh.parse_accepted_cuts(raw, today=TODAY, decisions=LOG) == {}


@pytest.mark.parametrize(("raw", "why"), [
    (_file(until=None), "until"),
    (_file(until="2026-11-10"), "past"),
    (_file(until="2026-12-31"), "more than"),
    (_file(decision="D-999"), "not in docs/decisions.md"),
    (_file(decision="soon"), "not an ADR id"),
    (_file(board="no-such-board"), "neither a surface nor a declared board"),
    (_file(names="      []\n"), "names"),
    (_file(names="      - '---'\n"), "names"),
    (_file(names="      - Fresh 0\n      - Fresh 0\n"), "names"),
    (_file(extra="    rows: []\n"), "exactly"),
    (_file() + _file().split("additions:\n", 1)[1], "named twice"),
    ("cuts: []\nadditions: {}\n", "the file is"),
    ("cuts: []\nextra: []\n", "the file is"),
], ids=["no until", "past", "too far", "unknown ADR", "not an ADR id", "unknown board", "no names",
        "a name with no letter", "a name twice", "an extra key", "a board twice", "not a list", "unknown key"])
def test_an_addition_off_its_schema_fails_the_refresh(raw: str, why: str) -> None:
    with pytest.raises(refresh.AcceptedCutError, match=why):
        refresh.parse_accepted_additions(raw, today=TODAY, decisions=LOG)


def test_the_adr_must_name_the_board() -> None:
    log = "## D-251 — the probe's additions\n\nNames no board.\n"
    with pytest.raises(refresh.AcceptedCutError, match="does not name"):
        refresh.parse_accepted_additions(_file(), today=TODAY, decisions=log)


def test_the_committed_terminal_bench_addition_parses_until_its_expiry() -> None:
    """D-251 clause 2: `computer-use`'s board, Terminal-Bench 4.0's ten names of 2026-11-11, until 2026-11-25."""
    raw = refresh.ACCEPTED_CUTS_PATH.read_text(encoding="utf-8")
    decisions = refresh.DECISIONS_PATH.read_text(encoding="utf-8")
    accepted = refresh.parse_accepted_additions(raw, today=TODAY, decisions=decisions)
    assert set(accepted) == {"computer-use"}
    assert accepted["computer-use"] == frozenset({
        "anthropic/claude-haiku-5-5", "meta/muse-wonder-1.0", "moonshotai/kimi-k3.1-pro", "openai/gpt-5.4-mini",
        "openai/gpt-6.1-terra", "openrouter/mistralai/mistral-large-4-0", "openrouter/nvidia/nemotron-3.5-super-vl",
        "openrouter/reflection/beam-1.0-501b-a23b", "openrouter/thinkingmachines/inkling",
        "openrouter/thinkingmachines/inkling-small",
    })
    with pytest.raises(refresh.AcceptedCutError, match="past"):
        refresh.parse_accepted_additions(raw, today=dt.date(2026, 11, 26), decisions=decisions)


def test_the_night_reads_the_committed_file_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the conftest fixture, the loader defaults to the file the hosted night reads (#477 (2))."""
    monkeypatch.undo()
    assert refresh.load_accepted_additions.__defaults__ == (refresh.ACCEPTED_CUTS_PATH,)


def test_the_suite_reads_no_committed_additions_by_default() -> None:
    assert refresh.load_accepted_additions.__defaults__ != (refresh.ACCEPTED_CUTS_PATH,)
    assert refresh.load_accepted_additions() == {}


# --- Through `refresh()`: the file on disk is what the night applies.

def _on_disk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str | None) -> None:
    path = tmp_path / "cuts" / "accepted-cuts.yaml"
    if text is not None:
        path.parent.mkdir()
        path.write_text(text, encoding="utf-8")
    for loader in (refresh.load_accepted_cuts, refresh.load_accepted_respellings, refresh.load_accepted_additions):
        monkeypatch.setattr(loader, "__defaults__", (path,))
    log = tmp_path / "decisions.md"
    log.write_text(LOG, encoding="utf-8")
    monkeypatch.setattr(refresh, "DECISIONS_PATH", log)


def _both_boards(names: str = "".join(f"      - Fresh {i}\n" for i in range(5))) -> str:
    until = dt.date.today() + dt.timedelta(days=10)
    return "cuts: []\nadditions:\n" + "".join(
        f"  - board: {board}\n    decision: D-251\n    reason: a probe\n    until: {until}\n    names:\n{names}"
        for board in (OWN, SLICE.source))


def _night(tmp_path: Path) -> tuple[refresh.RefreshOutcome, int]:
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _arrive(5))
        return 0

    return refresh.refresh(live, builder=build)


@pytest.mark.parametrize("on_disk", [True, False], ids=["the-additions-on-disk", "no-file"])
def test_the_night_reads_the_additions_through_its_real_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_disk: bool
) -> None:
    _on_disk(tmp_path, monkeypatch, _both_boards() if on_disk else None)
    outcome, code = _night(tmp_path)
    assert code == (refresh.EXIT_PUBLISHED if on_disk else refresh.EXIT_REFUSED), outcome.reason
    if not on_disk:
        assert "would be 5 of 17 rows" in outcome.reason, outcome.reason


def test_a_malformed_additions_list_fails_the_night(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _on_disk(tmp_path, monkeypatch, _both_boards().replace("D-251", "D-25"))
    with pytest.raises(refresh.AcceptedCutError):
        _night(tmp_path)



# --- Release Tester, run golive-1111: the two shapes the first tests did not reach.

def _arrive_ranked(count: int) -> Change:
    """`count` models neither board had, PRICED so the surface ranks them (as the real night's Terminal-Bench
    batch was: "10 of 31 models"), one row each on `coding`'s own board."""
    def change(conn: sqlite3.Connection) -> None:
        for i in range(count):
            model = f"fresh-{i}"
            conn.execute("INSERT OR IGNORE INTO models (id, display, vendor) VALUES (?, ?, 'Probe')",
                         (model, f"Fresh {i}"))
            conn.execute("INSERT OR IGNORE INTO px_median (model_id, in_m, out_m) VALUES (?, 2.0, 6.0)", (model,))
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
                " source_url, observed_at) VALUES (?, ?, 'swebench', 'SWE-bench Verified', '% resolved', 50,"
                " 'none', 'unspecified', 'fixture://x', 't')", (model, f"Fresh {i}"))
    return change


def test_an_accepted_addition_leaves_the_surfaces_ranked_models_too(tmp_path: Path) -> None:
    """The night of 2026-11-11 refused on "10 of 31 models" as well as on rows (#605). Naming the rows
    alone must clear the models guard on the surface's own board, and without it that guard must fire."""
    (tmp_path / "a").mkdir()
    control = _judged(tmp_path / "a", _arrive_ranked(5), {})
    assert any(r.startswith(f"{OWN} would be 5 of 17 models") for r in control), control
    (tmp_path / "b").mkdir()
    assert _judged(tmp_path / "b", _arrive_ranked(5), {OWN: _names(0, 1, 2, 3, 4)}) == []


def _arrive_unlinked(count: int) -> Change:
    """`count` rows on `SLICE`'s board that the reconcile linked to no model (`model_id` NULL)."""
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
            " source_url, observed_at) VALUES (NULL, ?, ?, ?, 'elo', 50, 'arena-crowd', 'unspecified',"
            " 'fixture://x', 't')", [(f"Fresh {i}", SLICE.source, SLICE.benchmark) for i in range(count)])
    return change


def test_unlinked_rows_are_excused_by_their_listed_names_only(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "c").mkdir()
    assert _judged(tmp_path / "a", _arrive_unlinked(5), {}) != []
    assert _judged(tmp_path / "b", _arrive_unlinked(5), {SLICE.source: _names(0, 1, 2, 3, 4)}) == []
    assert _judged(tmp_path / "c", _arrive_unlinked(8), {SLICE.source: _names(0, 1)}) != []


def test_an_unlinked_row_the_served_board_holds_is_not_excused(tmp_path: Path) -> None:
    """Served holds `Fresh 0..1` unlinked; the candidate adds 3 more, and `Fresh 0..1` are listed: listing a
    key the served board holds excuses nothing, so the 3 genuinely new rows of 20 stay counted."""
    (tmp_path / "a").mkdir()
    base = _arrive_unlinked(2)

    def more(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
            " source_url, observed_at) VALUES (NULL, ?, ?, ?, 'elo', 50, 'arena-crowd', 'unspecified',"
            " 'fixture://x', 't')", [(f"New {i}", SLICE.source, SLICE.benchmark) for i in range(5)])

    reasons = _judged(tmp_path / "a", more, {SLICE.source: _names(0, 1)}, base=base)
    assert any("5 of 19" in r for r in reasons), reasons


# --- The release security delta 2026-11-11: M25 (an addition held up the loss counts) and M26 (one name, many rows).

def _unpriced(*indexes: int) -> Change:
    """The named served probes lose their price, so the surface stops ranking them while its board keeps their
    rows: a loss of ranked models that only the count guards (`surfaces`, `eligible`) can see."""
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany("DELETE FROM px_median WHERE model_id = ?", [(f"probe-{i:02d}",) for i in indexes])
    return change


def _both(*changes: Change) -> Change:
    def change(conn: sqlite3.Connection) -> None:
        for each in changes:
            each(conn)
    return change


def test_m25_seven_served_models_leaving_the_ranking_are_refused_alone(tmp_path: Path) -> None:
    """The control: 7 of 12 ranked models gone, nothing arriving."""
    reasons = _judged(tmp_path, _unpriced(*range(7)), {})
    assert any(r.startswith(f"{OWN} would lose 7 of 12 models") for r in reasons), reasons


def test_m25_an_accepted_addition_does_not_hide_a_loss_of_ranked_models(tmp_path: Path) -> None:
    """M25: the same loss with 5 listed arrivals. The arrivals are taken out of the growth count, so they are
    taken out of the loss counts too: 12 - 7 + 5 ranked, judged as 5 of 12, still refused."""
    reasons = _judged(tmp_path, _both(_unpriced(*range(7)), _arrive_ranked(5)), {OWN: _names(0, 1, 2, 3, 4)})
    assert any(r.startswith(f"{OWN} would lose 7 of 12 models") for r in reasons), reasons


def test_m25_an_accepted_addition_does_not_hide_a_budget_emptying(tmp_path: Path) -> None:
    """M25's budget half: every served model leaves the ranking and 5 listed arrivals are offered at every budget.
    Judged without the arrivals, the surface offers nothing where it offered 12."""
    reasons = _judged(tmp_path, _both(_unpriced(*range(12)), _arrive_ranked(5)), {OWN: _names(0, 1, 2, 3, 4)})
    assert any(r.startswith(f"{OWN} offered 12 models at the") for r in reasons), reasons


def test_m25_an_addition_with_no_loss_still_publishes(tmp_path: Path) -> None:
    assert _judged(tmp_path, _arrive_ranked(5), {OWN: _names(0, 1, 2, 3, 4)}) == []


def _flood(count: int, *, linked: bool) -> Change:
    """`count` rows under the one name `Fresh 0` on `SLICE`'s board, one per harness: copies of one new model, or
    unlinked."""
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
            " source_url, observed_at) VALUES (?, 'Fresh 0', ?, ?, 'elo', 50, ?, 'unspecified', 'fixture://x', 't')",
            [("fresh-0" if linked else None, SLICE.source, SLICE.benchmark, f"harness-{i}") for i in range(count)])
    return change


@pytest.mark.parametrize("linked", [True, False], ids=["copies-of-one-model", "unlinked"])
def test_m26_one_listed_name_excuses_one_row_not_a_flood(tmp_path: Path, linked: bool) -> None:
    """M26: 40 rows under the one listed name `Fresh 0`. A name excuses the row the owner looked at, so 39 of
    51 judged rows are still new and the board is refused (D-159's flood rule)."""
    reasons = _judged(tmp_path, _flood(40, linked=linked), {SLICE.source: _names(0)})
    assert any(r.startswith(f"board {SLICE.source} would be 39 of 51 rows") for r in reasons), reasons


@pytest.mark.parametrize("linked", [True, False], ids=["copies-of-one-model", "unlinked"])
def test_m26_a_listed_name_still_excuses_its_one_row(tmp_path: Path, linked: bool) -> None:
    """Four rows under `Fresh 0`, one listed: three of 15 judged rows are new, under the quarter."""
    assert not [r for r in _judged(tmp_path, _flood(4, linked=linked), {SLICE.source: _names(0)})
                if r.startswith(f"board {SLICE.source}")]
