"""#613 (D-253): a board that grows by merged submissions publishes its arrivals without a ruling per batch.

Three hosted nights refused, 2026-11-13 to 2026-11-15. Terminal-Bench 4.0, `computer-use`'s own board, took 13
submissions its publisher merged in batches. All 33 served rows were still there. The roster and the board read
the arrivals as over D-132's quarter, and their prices moved the surface's median by 30% while no price
changed. The arrivals are now computed for a board `SUBMISSION_BOARDS` names, as D-251's listed additions were
named. That holds only while:
- every served row of that board is kept;
- each new name excuses one row (M26);
- the arrivals are at most half of the board (`MAX_SUBMISSION_GAIN`).

The median-price guard leaves out every arrival an addition sets aside, so it judges the prices of the models
served on both nights.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.workflows import refresh
from app.workflows.refresh import degradations, fingerprint_of, upward_anomalies

from .test_accepted_additions import OWN, _arrive, _both, _names
from .test_refresh_board_ids import SLICE, Change, _boards

#: The probe's submission board: `coding`'s own board (SWE-bench Verified in the fixture).
SUBMITTED = (OWN,)


def _arrive_priced(count: int, *, in_m: float = 2.0, out_m: float = 6.0, rows: int = 1) -> Change:
    """`count` models `coding`'s board never held, priced, each with `rows` rows under its one name (one harness
    each)."""
    def change(conn: sqlite3.Connection) -> None:
        for i in range(count):
            model = f"fresh-{i}"
            conn.execute("INSERT OR IGNORE INTO models (id, display, vendor) VALUES (?, ?, 'Probe')",
                         (model, f"Fresh {i}"))
            conn.execute("INSERT OR IGNORE INTO px_median (model_id, in_m, out_m) VALUES (?, ?, ?)",
                         (model, in_m, out_m))
            conn.executemany(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
                " source_url, observed_at) VALUES (?, ?, 'swebench', 'SWE-bench Verified', '% resolved', 50,"
                " ?, 'unspecified', 'fixture://x', 't')",
                [(model, f"Fresh {i}", f"harness-{r}") for r in range(rows)])
    return change


def _lose_served(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM scores WHERE source = 'swebench' AND model_id = 'probe-00'")


def _reprice_served(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE px_median SET in_m = in_m / 2, out_m = out_m / 2 WHERE model_id LIKE 'probe-%'")


def _judged(tmp_path: Path, change: Change, *, submitted: tuple[str, ...] = SUBMITTED,
            accepted: dict[str, frozenset[str]] | None = None) -> list[str]:
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", change))
    assert live is not None and candidate is not None
    computed = refresh.arrivals(candidate, live, submitted)
    judged = refresh.added(candidate, live, refresh.merged_additions(accepted or {}, computed))
    assert judged.digest == candidate.digest  # what is published is the candidate, as built
    return degradations(live, judged, cuts={}) + upward_anomalies(live, judged)


def _own(reasons: list[str]) -> list[str]:
    return [r for r in reasons if r.startswith(OWN)]


# --- The arrivals are computed, and the guards judge the board as before when a condition fails.

def test_without_a_submission_board_five_arrivals_are_refused(tmp_path: Path) -> None:
    """The control, #613's shape: 5 of 17 rows and models new on `coding`, over the quarter."""
    reasons = _judged(tmp_path, _arrive_priced(5), submitted=())
    assert any(r.startswith(f"{OWN}'s board would be 5 of 17 rows") for r in reasons), reasons
    assert any(r.startswith(f"{OWN} would be 5 of 17 models") for r in reasons), reasons


def test_a_submission_board_s_arrivals_publish(tmp_path: Path) -> None:
    assert _judged(tmp_path, _arrive_priced(5)) == []


def test_arrivals_up_to_half_the_board_publish(tmp_path: Path) -> None:
    """12 new of 24 rows: exactly half, at the cap."""
    assert _own(_judged(tmp_path, _arrive_priced(12))) == []


def test_arrivals_over_half_the_board_are_judged_as_before(tmp_path: Path) -> None:
    """13 new of 25 rows (52%): a board that more than doubles between two publishes is published by hand."""
    reasons = _judged(tmp_path, _arrive_priced(13))
    assert any(r.startswith(f"{OWN}'s board would be 13 of 25 rows") for r in reasons), reasons


def test_a_lost_served_row_turns_the_computed_arrivals_off(tmp_path: Path) -> None:
    """An append-only board keeps its rows. One served row lost (1 of 12, which the loss guard passes) and 5
    arrivals: the arrivals count as before, 5 of 16."""
    reasons = _judged(tmp_path, _both(_lose_served, _arrive_priced(5)))
    assert any(r.startswith(f"{OWN}'s board would be 5 of 16 rows") for r in reasons), reasons


def test_a_flood_under_one_new_name_excuses_one_row(tmp_path: Path) -> None:
    """M26 holds for computed arrivals: 10 rows under the one new name `Fresh 0`: one excused, 9 of
    the 21 judged rows still new."""
    reasons = _judged(tmp_path, _arrive_priced(1, rows=10))
    assert any(r.startswith(f"{OWN}'s board would be 9 of 21 rows") for r in reasons), reasons


def test_a_board_not_named_a_submission_board_is_judged_as_before(tmp_path: Path) -> None:
    """`coding`'s arrivals are computed; the declared board beside it, with the same 5 arrivals, is not."""
    reasons = _judged(tmp_path, _arrive(5))
    assert reasons and all(r.startswith(f"board {SLICE.source}") for r in reasons), reasons


def test_a_first_artifact_has_no_arrivals(tmp_path: Path) -> None:
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _arrive_priced(5)))
    assert candidate is not None
    assert refresh.arrivals(candidate, None, SUBMITTED) == {}


def test_the_arrivals_are_the_new_names_only(tmp_path: Path) -> None:
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _arrive_priced(3)))
    assert live is not None and candidate is not None
    assert refresh.arrivals(candidate, live, SUBMITTED) == {OWN: _names(0, 1, 2)}


def test_listed_and_computed_additions_merge_board_by_board() -> None:
    merged = refresh.merged_additions({OWN: _names(0), "other": _names(5)}, {OWN: _names(1)})
    assert merged == {OWN: _names(0, 1), "other": _names(5)}


# --- The median-price guard leaves out what an addition set aside (#613, the nights of 2026-11-13 and 11-14).

def test_cheap_arrivals_move_the_median_without_an_addition(tmp_path: Path) -> None:
    """The control: 12 arrivals at $0.30 beside 12 served models at $3.00 move the median 45%."""
    reasons = _judged(tmp_path, _arrive_priced(12, in_m=0.2, out_m=0.6), submitted=())
    assert any(r.startswith(f"{OWN}'s median price would move down") for r in reasons), reasons


def test_computed_arrivals_leave_the_median_alone(tmp_path: Path) -> None:
    assert _judged(tmp_path, _arrive_priced(12, in_m=0.2, out_m=0.6)) == []


def test_listed_arrivals_leave_the_median_alone(tmp_path: Path) -> None:
    """D-251's listed additions had the same gap: the roster guard set them aside, the median counted them."""
    reasons = _judged(tmp_path, _arrive_priced(12, in_m=0.2, out_m=0.6), submitted=(),
                      accepted={OWN: frozenset(f"Fresh {i}" for i in range(12))})
    assert not [r for r in reasons if "median price" in r], reasons


def test_a_price_change_on_the_served_models_still_trips_beside_arrivals(tmp_path: Path) -> None:
    reasons = _judged(tmp_path, _both(_reprice_served, _arrive_priced(5)))
    assert any(r.startswith(f"{OWN}'s median price would move down 50%") for r in reasons), reasons


# --- The named set, and the night's record.

def test_terminal_bench_4_is_the_one_submission_board() -> None:
    assert refresh.submission_surfaces() == ("computer-use",)
    assert set(refresh.SUBMISSION_BOARDS) == {"terminalbench_4"}
    assert all(reason.strip() for reason in refresh.SUBMISSION_BOARDS.values())


def test_a_submission_board_no_surface_ranks_on_fails_closed() -> None:
    with pytest.raises(ValueError, match="nowhere"):
        refresh.submission_surfaces({"terminalbench_4": "a reason", "no_such_source": "a reason"})
    with pytest.raises(ValueError, match="nowhere"):
        refresh.submission_surfaces({})


def test_the_night_publishes_the_arrivals_and_records_them(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Through `refresh()`: the night reads `SUBMISSION_BOARDS`, publishes, and lists each admitted name."""
    monkeypatch.setattr(refresh, "SUBMISSION_BOARDS", {"swebench": "the probe's submission board"})
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _arrive_priced(5))
        return 0

    outcome, code = refresh.refresh(live, builder=build)
    assert code == refresh.EXIT_PUBLISHED, outcome.reason
    expected = [f"Fresh {i} on {OWN}'s board" for i in range(5)]
    assert list(outcome.admitted) == expected
    record = json.loads(Path(str(live) + ".refresh.json").read_text(encoding="utf-8"))
    assert record["admitted"] == expected
    assert json.loads(outcome.as_json())["admitted_count"] == 5


def test_the_night_without_the_submission_board_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(refresh, "SUBMISSION_BOARDS", {"terminalbench_4": "not this fixture's board"})
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _arrive_priced(5))
        return 0

    outcome, code = refresh.refresh(live, builder=build)
    assert code == refresh.EXIT_REFUSED
    assert "would be 5 of 17" in outcome.reason
    assert outcome.admitted == ()


# --- The security review, round 1 (`docs/reviews/enhancement-issue-613-submission-boards-security.md`): B1 and M2.

def _unlinked(*names: str, effort: str = "low") -> Change:
    """Rows on `coding`'s board the reconcile linked to no model, one per raw name given (a name given twice is two
    rows of one key). The reconcile links per (raw name, effort), so a new model's name can arrive linked at one
    effort and unlinked at another."""
    def change(conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
            " source_url, observed_at) VALUES (NULL, ?, 'swebench', 'SWE-bench Verified', '% resolved', 50, ?, ?,"
            " 'fixture://x', 't')", [(raw, f"harness-u{i}", effort) for i, raw in enumerate(names)])
    return change


def test_b1_a_linked_name_does_not_excuse_an_unlinked_twin(tmp_path: Path) -> None:
    """P2: one new linked model `Fresh 0` and 4 unlinked `fresh 0` rows. The two names excuse a row each: the linked
    row and one unlinked copy. 3 of the 15 judged rows stay new, under the quarter, and no third row is excused."""
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db",
                                       _both(_arrive_priced(1), _unlinked(*["fresh 0"] * 4))))
    assert live is not None and candidate is not None
    judged = refresh.added(candidate, live, refresh.arrivals(candidate, live, SUBMITTED))
    assert len(candidate.board[OWN]) - len(judged.board[OWN]) == 2


def test_b1_twin_keys_cannot_carry_a_board_past_half(tmp_path: Path) -> None:
    """P2c: 6 new linked models, each with 2 unlinked twin rows under its spelling key. The board grows 12 to 30, and
    the 18 new rows are 60% of it, over the cap: the arrivals are not computed, and the night is refused."""
    twins = [f"fresh {i}" for i in range(6) for _ in range(2)]
    reasons = _judged(tmp_path, _both(_arrive_priced(6), _unlinked(*twins)))
    assert any(r.startswith(f"{OWN}'s board would be 18 of 30 rows") for r in reasons), reasons


def test_listed_linked_names_excuse_no_unlinked_twin(tmp_path: Path) -> None:
    """The same rule on D-251's listed path: a listed name that is a linked spelling excuses linked rows only."""
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _both(_arrive_priced(1), _unlinked("Fresh 0"))))
    assert live is not None and candidate is not None
    judged = refresh.added(candidate, live, {OWN: _names(0)})
    assert len(candidate.board[OWN]) - len(judged.board[OWN]) == 1


def test_m2_unlinked_arrivals_are_computed_by_key_and_publish(tmp_path: Path) -> None:
    live = fingerprint_of(_boards(tmp_path / "live.db"))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", _unlinked("New A", "New B", "New C", "New D")))
    assert live is not None and candidate is not None
    assert refresh.arrivals(candidate, live, SUBMITTED) == {OWN: frozenset({"newa", "newb", "newc", "newd"})}
    (tmp_path / "j").mkdir()
    assert _judged(tmp_path / "j", _unlinked("New A", "New B", "New C", "New D")) == []


def test_m2_unlinked_arrivals_alone_are_refused_without_the_submission_board(tmp_path: Path) -> None:
    reasons = _judged(tmp_path, _unlinked("New A", "New B", "New C", "New D", "New E"), submitted=())
    assert any(r.startswith(f"{OWN}'s board would be 5 of 17 rows") for r in reasons), reasons


def test_m2_an_unlinked_flood_under_one_key_excuses_one_row(tmp_path: Path) -> None:
    """10 unlinked rows under one new key: one excused, 9 of the 21 judged rows new, refused."""
    reasons = _judged(tmp_path, _unlinked(*["New A"] * 10))
    assert any(r.startswith(f"{OWN}'s board would be 9 of 21 rows") for r in reasons), reasons


def test_m2_unlinked_arrivals_over_half_the_board_are_judged_as_before(tmp_path: Path) -> None:
    """13 unlinked new keys of 25 rows (52%)."""
    reasons = _judged(tmp_path, _unlinked(*[f"New {i}" for i in range(13)]))
    assert any(r.startswith(f"{OWN}'s board would be 13 of 25 rows") for r in reasons), reasons


def test_m1_a_refused_night_records_what_the_guards_set_aside(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`admitted` is what the growth guards set aside, published or not: here a price change on the served models
    refuses the night, and the record still names the five arrivals the guards did not count."""
    monkeypatch.setattr(refresh, "SUBMISSION_BOARDS", {"swebench": "the probe's submission board"})
    live = _boards(tmp_path / "advisor.db")

    def build(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _both(_reprice_served, _arrive_priced(5)))
        return 0

    outcome, code = refresh.refresh(live, builder=build)
    assert code == refresh.EXIT_REFUSED
    assert "median price" in outcome.reason
    assert list(outcome.admitted) == [f"Fresh {i} on {OWN}'s board" for i in range(5)]
