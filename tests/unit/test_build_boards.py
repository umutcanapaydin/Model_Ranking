"""`_ingest_boards` — seven of the tester's eight mutants here survived (M8 fresh-eyes review).

`test_build.py` proves the `boards=` SEAM works: the argument is honoured and the module registry
is not read. Nothing proved what happens INSIDE the loop. Each test below names the mutation it
dies to, because the finding was not "this code is wrong" — it is that this code was unexecuted in
every direction that matters when a board goes bad.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.clients.epoch_board import EpochBoard
from app.workflows import build as build_mod
from app.workflows.schema import connect

BOARD = EpochBoard(
    file="board.csv",
    source_name="epoch_probe",
    benchmark="Probe bench",
    metric="% correct",
    score_column="Score",
    scale="fraction",
    maximum=1.0,
)


def _bundle(tmp_path: Path, body: str) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir(exist_ok=True)
    (bundle / "board.csv").write_text(body, encoding="utf-8")
    return bundle


def _run(conn: sqlite3.Connection, bundle: Path | None, boards=(BOARD,)):
    run = build_mod.RunContext()
    return build_mod._ingest_boards(conn, bundle, run, boards), run


def test_a_board_that_parses_nothing_is_a_failure_and_not_a_quiet_success(tmp_path: Path) -> None:
    """BLD-03. A board that reads zero rows is the exact shape W-023 shipped for a milestone:
    everything reports fine and every query answers nothing."""
    conn = connect(":memory:")
    try:
        bundle = _bundle(tmp_path, "Model version,Score\n")  # header only
        (reports, missing), _ = _run(conn, bundle)
    finally:
        conn.close()

    assert reports == []
    assert missing and "epoch_probe" in missing[0]
    assert "0 rows" in missing[0], f"the operator is not told the board was empty: {missing}"


def test_a_rejected_board_leaves_no_rows_behind(tmp_path: Path) -> None:
    """BLD-02: the `reset_source` rollback. Without it a board that fails AFTER storing some rows
    leaves them in `scores`, so the artifact carries evidence from a source the report calls
    missing — the L.2 shape, and the reason the other registries have a rollback test."""
    conn = connect(":memory:")
    try:
        # Real rows land, then the board is rejected: a second file whose score column is gone.
        good = _bundle(tmp_path, "Model version,Score\nalpha,0.9\n")
        (reports, missing), _ = _run(conn, good)
        assert reports and not missing
        stored = conn.execute(
            "SELECT count(*) FROM scores WHERE source = 'epoch_probe'"
        ).fetchone()[0]
        assert stored > 0, "fixture assumption: the good pass must store rows"

        broken = _bundle(tmp_path, "Model version,Accuracy\nalpha,0.9\n")
        (reports, missing), _ = _run(conn, broken)
        assert missing, "the renamed column must be reported"

        left = conn.execute("SELECT count(*) FROM scores WHERE source = 'epoch_probe'").fetchone()[0]
        assert left == 0, (
            f"{left} rows from a REJECTED board are still in the artifact; the build report calls "
            "this source missing while the database serves its evidence"
        )
    finally:
        conn.close()


def test_a_missing_bundle_directory_names_every_surface_it_blinded(tmp_path: Path) -> None:
    """BLD-04: returning `[], []` here reported seven blinded surfaces as fine.

    D-121: a source may be optional, but a blind surface may never be silent.
    """
    conn = connect(":memory:")
    try:
        (reports, missing), _ = _run(conn, None)
    finally:
        conn.close()

    assert reports == []
    assert len(missing) == 1
    assert "epoch_probe" in missing[0]


def test_a_board_failure_is_reported_per_board_and_not_swallowed_whole(tmp_path: Path) -> None:
    """BLD-07: widening the except to `Exception` launders a TypeError or KeyError inside the
    reader into 'this source is missing', which sends an operator to look for a file that is
    there. A real bad input still arrives as SourceError."""
    conn = connect(":memory:")
    try:
        bundle = _bundle(tmp_path, "Model version,Accuracy\nalpha,0.9\n")
        (reports, missing), _ = _run(conn, bundle)
    finally:
        conn.close()

    assert reports == []
    assert "declared score column" in missing[0], (
        f"the operator is told the source is missing rather than renamed: {missing}"
    )


def test_the_report_counts_what_landed_and_what_was_dropped(tmp_path: Path) -> None:
    """BLD-08: `stored=skipped` made the build report lie about how much evidence arrived."""
    conn = connect(":memory:")
    try:
        # stored MUST differ from skipped. The first version of this test had three of each and
        # the `stored=skipped` mutant was invisible: two numbers that happen to be equal cannot
        # tell you which one you are reading. Three parsed, one dropped.
        bundle = _bundle(
            tmp_path,
            "Model version,Score\nalpha,0.9\nbeta,0.8\ndelta,0.7\ngamma,notanumber\n",
        )
        (reports, missing), _ = _run(conn, bundle)
    finally:
        conn.close()

    assert not missing
    (report,) = reports
    assert report.source == "epoch_probe"
    assert report.stored == 3, f"three models parsed; the report says {report.stored}"
    assert report.skipped == 1, f"one row was dropped; the report says {report.skipped}"
    assert report.stored != report.skipped, (
        "fixture assumption: the two counts must differ or swapping them is invisible"
    )


def test_a_board_that_escapes_the_bundle_is_refused_through_the_build(tmp_path: Path) -> None:
    """The guard from `test_epoch_board.py`, driven through the REAL entry point (V4C-50: every
    load-bearing path needs at least one test through the real entry point)."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("Model version,Score\nleaked,0.9\n", encoding="utf-8")
    (bundle / "board.csv").symlink_to(outside)

    conn = connect(":memory:")
    try:
        (reports, missing), _ = _run(conn, bundle)
        left = conn.execute("SELECT count(*) FROM scores WHERE source = 'epoch_probe'").fetchone()[0]
    finally:
        conn.close()

    assert reports == []
    assert "outside the bundle" in missing[0]
    assert left == 0, "a refused board still put rows in the artifact"


def test_a_board_failure_does_not_raise_out_of_the_ingest(tmp_path: Path) -> None:
    """Containment is the contract: `_ingest_boards` reports, it does not abort the build.

    A `csv.Error` used to escape it entirely and reach the operator as a traceback, which
    `build.py` reserves for a bug in the builder rather than a bad input.
    """
    conn = connect(":memory:")
    try:
        huge = "x" * 200_000
        bundle = _bundle(tmp_path, f'Model version,Score\n"{huge}",0.5\n')
        (reports, missing), _ = _run(conn, bundle)  # must not raise
    finally:
        conn.close()

    assert reports == []
    assert missing and "epoch_probe" in missing[0]


@pytest.mark.parametrize("column", ["Model version", "Score"])
def test_a_renamed_column_is_loud_rather_than_empty(tmp_path: Path, column: str) -> None:
    """BLD-06's neighbour: either missing column must reach `required_operator_actions`."""
    header = "Model version,Score".replace(column, f"Renamed{column}")
    conn = connect(":memory:")
    try:
        (reports, missing), _ = _run(conn, _bundle(tmp_path, f"{header}\nalpha,0.9\n"))
    finally:
        conn.close()
    assert reports == []
    assert missing


def test_the_board_ingest_catches_bad_input_and_not_every_exception() -> None:
    """BLD-07, asserted structurally because a behavioural test cannot reach it honestly.

    Widening `except (SourceError, OSError)` to `except Exception` launders a `TypeError` or
    `KeyError` inside the reader into "this source is missing" — sending an operator to look for a
    file that is present while a real bug goes unreported. Forcing such a bug from a test would
    mean planting one, so this reads the clause instead: the narrowness IS the control, and it is
    the kind that decays silently during a debugging session.
    """
    import ast

    tree = ast.parse(Path("src/app/workflows/build.py").read_text(encoding="utf-8"))
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_ingest_boards"
    )
    handlers = [h for n in ast.walk(fn) if isinstance(n, ast.Try) for h in n.handlers]
    assert handlers, "_ingest_boards no longer contains its per-board containment"

    for handler in handlers:
        caught = handler.type
        names = (
            [e.id for e in caught.elts if isinstance(e, ast.Name)]
            if isinstance(caught, ast.Tuple)
            else [caught.id] if isinstance(caught, ast.Name) else []
        )
        assert names, f"_ingest_boards catches a bare or non-name exception: {ast.dump(handler)}"
        assert "Exception" not in names and "BaseException" not in names, (
            f"_ingest_boards catches {names}; a programming error inside the reader would be "
            "reported to the operator as a missing source"
        )


def test_a_board_report_reaches_the_run_context_like_every_other_source(tmp_path: Path) -> None:
    """MINOR-7: boards were the one source kind that never appended to `run.reports`.

    Every `ingest_*` in `ingest.py` appends; `_ingest_boards` built the report and returned it
    without recording it. Harmless while nothing in production reads that field — and precisely the
    inconsistency that becomes a defect the day something does, in the source kind that carries six
    of the nine surfaces.
    """
    conn = connect(":memory:")
    try:
        bundle = _bundle(tmp_path, "Model version,Score\nalpha,0.9\n")
        (reports, missing), run = _run(conn, bundle)
    finally:
        conn.close()

    assert not missing
    assert reports, "fixture assumption: the board must ingest"
    assert [r.source for r in run.reports] == ["epoch_probe"], (
        "the board's SourceReport never reached the run context; every other ingest records one"
    )
