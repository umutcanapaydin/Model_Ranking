"""#100 (D-179): the board guards compare a board's rows by the model each links to, as the roster
guards do.

D-173 clause 2 moved the roster guards to model ids (#39); the board guards (D-159 on a surface's own
board, D-164 on every declared board) still compared raw names. The M18-W4 reviewer's probe: an
upstream that re-spelled 77 of the 173 names on `coding`'s board, keeping every model, was refused as
names lost and new. Here a re-spelling moves no board guard, and what the guards are for still
refuses: new models, more rows for models already there, rows moved to other models, and a quarter
lost. An unlinked row has no model, so it is still compared by its name.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from app.workflows import boards as declared_boards
from app.workflows.refresh import (
    EXIT_PUBLISHED,
    degradations,
    fingerprint_of,
    refresh,
    upward_anomalies,
)

from .test_refresh import _wide

#: A declared board no surface ranks on (D-164), beside `coding`'s own board (D-159).
SLICE = declared_boards.uncovered()[0]
BOTH = ("coding's board", f"board {SLICE.source}")

Change = Callable[[sqlite3.Connection], None]


def _boards(path: Path, change: Change | None = None) -> Path:
    """`_wide`'s twelve probe models on `coding`'s board, and the same twelve on `SLICE`."""
    _wide(path, models=12)
    conn = sqlite3.connect(path)
    try:
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness,"
            " source_url, observed_at) VALUES (?, ?, ?, ?, 'elo', ?, 'arena-crowd', 'fixture://x', 't')",
            [(f"probe-{i:02d}", f"Probe {i:02d}", SLICE.source, SLICE.benchmark, 1200.0 + i) for i in range(12)],
        )
        if change is not None:
            change(conn)
        conn.commit()
    finally:
        conn.close()
    return path


def _reasons(tmp_path: Path, change: Change, base: Change | None = None) -> list[str]:
    def both(conn: sqlite3.Connection) -> None:
        if base is not None:
            base(conn)
        change(conn)

    live = fingerprint_of(_boards(tmp_path / "live.db", base))
    candidate = fingerprint_of(_boards(tmp_path / "candidate.db", both))
    assert live is not None and candidate is not None
    return degradations(live, candidate) + upward_anomalies(live, candidate)


def _re_spell(conn: sqlite3.Connection) -> None:
    """Every probe row re-spelled, each still linked to its model: `Probe 00` -> `PROBE 00`."""
    conn.execute("UPDATE scores SET raw_name = upper(raw_name) WHERE raw_name LIKE 'Probe %'")


def test_a_board_whose_rows_are_only_re_spelled_moves_no_guard(tmp_path: Path) -> None:
    """The reviewer's probe, on both kinds of board: every name re-spelled, every model kept."""
    assert _reasons(tmp_path, _re_spell) == []


def test_a_re_spelled_board_publishes_and_records_the_re_spellings(tmp_path: Path) -> None:
    """Through the cycle: the night publishes, and its record says what was re-spelled, where."""
    live = _boards(tmp_path / "advisor.db")

    def re_spelling(argv: list[str]) -> int:
        _boards(Path(argv[argv.index("--db") + 1]), _re_spell)
        return 0

    outcome, code = refresh(live, builder=re_spelling)
    assert code == EXIT_PUBLISHED, outcome.reason
    assert "Probe 00 -> PROBE 00 on board " + SLICE.source + " and 1 more" in outcome.renamed, outcome.renamed


def _new_models(conn: sqlite3.Connection) -> None:
    """Five rows for models neither board had: 5 of 17 is over the quarter (D-132)."""
    for source, benchmark, metric in (("swebench", "SWE-bench Verified", "% resolved"),
                                      (SLICE.source, SLICE.benchmark, "elo")):
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
            " source_url, observed_at) VALUES (?, ?, ?, ?, ?, 50, ?, 'unspecified', 'fixture://x', 't')",
            [(f"fresh-{i}", f"Fresh {i}", source, benchmark, metric,
              "none" if source == "swebench" else "arena-crowd") for i in range(5)],
        )


def _more_rows_for_the_same_models(conn: sqlite3.Connection) -> None:
    """Five more rows on each board, each a new spelling of a model already there. The floor counts
    every row (D-159), so these move it as surely as new models would."""
    conn.execute(
        "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, effort,"
        " source_url, observed_at) SELECT model_id, raw_name || ' (copy)', source, benchmark, metric,"
        " score, harness, effort, source_url, observed_at FROM scores"
        " WHERE raw_name IN ('Probe 00', 'Probe 01', 'Probe 02', 'Probe 03', 'Probe 04')")


def _moved_to_other_models(conn: sqlite3.Connection) -> None:
    """Every row on `SLICE` keeps its name and links to another model, as a registry change can do."""
    conn.execute("UPDATE scores SET model_id = 'other-' || model_id WHERE source = ?", (SLICE.source,))


def _a_quarter_lost(conn: sqlite3.Connection) -> None:
    """Three of twelve rows gone from `SLICE` (D-128: at a quarter refuses)."""
    conn.execute("DELETE FROM scores WHERE source = ? AND raw_name IN ('Probe 00', 'Probe 01', 'Probe 02')",
                 (SLICE.source,))


@pytest.mark.parametrize(("change", "boards"), [
    (_new_models, BOTH),
    (_more_rows_for_the_same_models, BOTH),
    (_moved_to_other_models, BOTH[1:]),
    (_a_quarter_lost, BOTH[1:]),
], ids=["new models", "more rows for the same models", "moved to other models", "a quarter lost"])
def test_what_the_board_guards_are_for_still_refuses(
    tmp_path: Path, change: Change, boards: tuple[str, ...]
) -> None:
    reasons = _reasons(tmp_path, change)
    for board in boards:
        assert any(reason.startswith(board) for reason in reasons), (board, reasons)


def test_a_relabelled_harness_or_effort_moves_no_board_guard(tmp_path: Path) -> None:
    """A row's harness and effort are its provenance, not its model: a relabel on rows the board
    already had is published (`test_refresh.py::test_a_freshness_or_provenance_update_is_published`),
    never read as rows lost and new."""

    def relabel(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET harness = 'other', effort = 'high' WHERE source = ?", (SLICE.source,))

    assert _reasons(tmp_path, relabel) == []


def test_an_unlinked_row_is_still_compared_by_its_name(tmp_path: Path) -> None:
    """A row the reconcile linked to no model has nothing but its name, so re-spelling it is a name
    lost and a name gained, as before."""

    def unlinked(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET model_id = NULL WHERE source = ?", (SLICE.source,))

    reasons = _reasons(tmp_path, _re_spell, base=unlinked)
    assert any(reason.startswith(f"board {SLICE.source}") for reason in reasons), reasons
    assert not any(reason.startswith("coding's board") for reason in reasons), reasons


@pytest.mark.parametrize("direction", ["gains", "loses"])
def test_a_row_that_keeps_its_name_and_changes_its_link_counts(tmp_path: Path, direction: str) -> None:
    """D-179, as the M19-W1 review's M1 asked it to say: a row whose link is gained or lost changes
    what the board serves (a standing appears or leaves), so twelve such rows on one board refuse
    the night, the way twelve new names did before."""

    def unlinked(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET model_id = NULL WHERE source = ?", (SLICE.source,))

    def relinked(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE scores SET model_id = 'probe-' || substr(raw_name, 7) WHERE source = ?",
                     (SLICE.source,))

    reasons = (_reasons(tmp_path, relinked, base=unlinked) if direction == "gains"
               else _reasons(tmp_path, unlinked))
    assert any(reason.startswith(f"board {SLICE.source}") for reason in reasons), reasons


def _priced_by_two_feeds(path: Path) -> Path:
    """Twelve derived models on `SLICE`, each with a price and an accessibility value. Four are priced
    by `litellm` alone, eight by `openrouter`: a `litellm` expiry unlinks a third of the board."""
    from app.workflows import access
    from app.workflows.rank import build_price_medians
    from app.workflows.registry import reconcile
    from app.workflows.schema import connect

    conn = connect(str(path))
    try:
        for i in range(12):
            name = f"zorblax-{i}"
            conn.execute(
                "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, source_url,"
                " observed_at) VALUES (?, ?, 'elo', ?, 'arena-crowd', 'unspecified', ?, 'u', 't')",
                (name, SLICE.benchmark, 1200.0 + i, SLICE.source))
            conn.execute(
                "INSERT INTO pricing (alias, input_per_m, output_per_m, source, source_url, observed_at)"
                " VALUES (?, 1, 2, ?, 'u', 't')", (name, "litellm" if i < 4 else "openrouter"))
            conn.execute(
                "INSERT INTO access (raw_name, accessibility, source, source_url, observed_at)"
                " VALUES (?, 'API access', 'epoch_access', 'u', 't')", (name,))
        reconcile(conn)
        build_price_medians(conn)
        access.link(conn)
        conn.commit()
    finally:
        conn.close()
    return path


def _built_without(live: Path, path: Path, source: str) -> Path:
    """What a build makes without `source`: its rows gone, every link made again (D-157)."""
    import shutil

    from app.workflows import access
    from app.workflows.rank import build_price_medians
    from app.workflows.registry import reconcile

    shutil.copyfile(live, path)
    conn = sqlite3.connect(path)
    try:
        for table in ("scores", "pricing", "access"):
            conn.execute(f"DELETE FROM {table} WHERE source = ?", (source,))
        conn.execute("UPDATE scores SET model_id = NULL")
        conn.execute("UPDATE pricing SET model_id = NULL")
        conn.execute("DELETE FROM models")
        reconcile(conn)
        build_price_medians(conn)
        access.link(conn)
        conn.commit()
    finally:
        conn.close()
    return path


def test_a_price_feeds_expiry_is_judged_against_the_links_a_build_would_make(tmp_path: Path) -> None:
    """The M19-W1 Tester's M5 and K1 (D-156 clause 3, D-179). On the night a price feed's data expires,
    the baseline is the live artifact without that feed's rows, but it kept every link, while a build
    without the feed unlinks each derived model the feed alone priced (D-157). So the board guards
    read those rows as lost and new, and the accessibility guard read their values as lost: an expiry
    the refresh exists to publish was refused. The baseline is linked again, as a build links it."""
    from app.workflows.refresh import _served_without

    live_path = _priced_by_two_feeds(tmp_path / "live.db")
    live = fingerprint_of(live_path)
    candidate = fingerprint_of(_built_without(live_path, tmp_path / "candidate.db", "litellm"))
    assert live is not None and candidate is not None
    assert len(live.boards[SLICE.source]) == 12 and candidate.accessible == 8, "the fixture proves nothing"
    baseline = _served_without(live_path, {"litellm"})
    reasons = degradations(baseline, candidate) + upward_anomalies(live, candidate, baseline)
    assert not [r for r in reasons if SLICE.source in r or r.startswith("accessibility")], reasons
