"""`app.clients.epoch_board` — the module that had no test at all (M8 fresh-eyes review).

**Why this file exists, stated plainly.** `epoch_board.py` is the single reader behind all seven
Epoch boards and therefore behind six of the nine categories this product ships. It reached HEAD at
**32% coverage with zero tests referencing it**: `parse_board` and `fetch_raw` were entirely
unexecuted. Three independent reviewers found it in the same pass, and an independent tester placed
fourteen mutants in it — every one survived, including the two below that re-open findings this
project already paid for once:

* **the bundle-escape guard.** M5 reproduced a symlink in a downloaded ZIP pointing at
  `/etc/shadow`. This module's docstring cites that incident as the reason its check exists. The
  check was carried forward as PROSE; the test was not carried with it, and deleting the guard kept
  the suite green.
* **the URL guard (D-101 "never fetches").** Deleting it let `EpochBoardClient("https://…")` be
  accepted and treated as a filesystem path.

The rest cover the controls the module advertises in its own comments. Each test names the mutation
it dies to, because the point of this file is that these lines are now EXECUTED, not merely present.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.clients.epoch import SourceError
from app.clients.epoch_board import EpochBoard, EpochBoardClient, parse_board

VERIFIED = "2026-08-01"

FRACTION = EpochBoard(
    file="board.csv",
    source_name="epoch_test",
    benchmark="Test bench",
    metric="accuracy",
    score_column="Score",
    scale="fraction",
    date_column="Started at",
    maximum=1.0,
)
RAW = EpochBoard(
    file="board.csv",
    source_name="epoch_raw",
    benchmark="Raw bench",
    metric="elo",
    score_column="Elo",
    scale="raw",
    maximum=None,
)


def _csv(*rows: str) -> str:
    return "\n".join(rows) + "\n"


# --- fetch_raw: the two guards that were carried forward as prose ------------------------------


def test_a_symlink_escaping_the_bundle_is_refused(tmp_path: Path) -> None:
    """M5's `/etc/shadow` finding, re-proved for this copy of the guard.

    Dies to: deleting `is_relative_to(root)` at `epoch_board.py:83`. That mutation read the symlink
    target and the whole suite stayed green, because nothing executed this path.
    """
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    secret = tmp_path / "outside" / "secret.csv"
    secret.parent.mkdir()
    secret.write_text("Model version,Score\nleaked,0.9\n", encoding="utf-8")
    (bundle / "board.csv").symlink_to(secret)

    client = EpochBoardClient(bundle, FRACTION, last_verified=VERIFIED)

    with pytest.raises(SourceError, match="outside the bundle"):
        client.fetch_raw()


def test_a_declared_file_that_climbs_out_of_the_bundle_is_refused(tmp_path: Path) -> None:
    """The same guard reached by path traversal rather than by symlink."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (tmp_path / "escaped.csv").write_text("Model version,Score\nx,0.5\n", encoding="utf-8")
    board = EpochBoard(
        file="../escaped.csv",
        source_name="epoch_test",
        benchmark="b",
        metric="m",
        score_column="Score",
    )

    with pytest.raises(SourceError, match="outside the bundle"):
        EpochBoardClient(bundle, board, last_verified=VERIFIED).fetch_raw()


def test_a_url_is_not_a_bundle_directory(tmp_path: Path) -> None:
    """D-101: this project reads an owner-placed bundle and NEVER fetches.

    Dies to: deleting the `"://" in bundle_dir` check at `epoch_board.py:62`, after which a URL is
    accepted and quietly treated as a `Path`.
    """
    with pytest.raises(SourceError, match="not a URL"):
        EpochBoardClient("https://epoch.ai/bundle", FRACTION, last_verified=VERIFIED)


def test_a_missing_csv_names_the_path_it_looked_for(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(SourceError, match="missing CSV"):
        EpochBoardClient(bundle, FRACTION, last_verified=VERIFIED).fetch_raw()


# --- parse_board: the shape guards, loud rather than empty --------------------------------------


def test_a_renamed_score_column_raises_and_names_the_columns_that_are_there() -> None:
    """Dies to: deleting the `score_column not in fieldnames` check.

    The module's own comment says "Loud rather than empty: a renamed upstream column would
    otherwise ingest zero rows and look like a quiet outage instead of the shape change it is."
    Nothing enforced that. A silent zero-row board is the exact shape W-023 shipped for a whole
    milestone.
    """
    raw = _csv("Model version,Accuracy", "m,0.5")
    with pytest.raises(SourceError, match="declared score column 'Score' is not in the CSV"):
        parse_board(raw, FRACTION)


def test_the_diagnostic_lists_what_the_csv_actually_had() -> None:
    """Without this the operator is told what is missing and not what arrived instead."""
    raw = _csv("Model version,Accuracy mean", "m,0.5")
    with pytest.raises(SourceError) as exc:
        parse_board(raw, FRACTION)
    assert "Accuracy mean" in str(exc.value)


def test_a_csv_without_a_model_column_raises() -> None:
    raw = _csv("Name,Score", "m,0.5")
    with pytest.raises(SourceError, match="no 'Model version' column"):
        parse_board(raw, FRACTION)


def test_an_empty_payload_raises_rather_than_returning_nothing() -> None:
    with pytest.raises(SourceError, match="empty"):
        parse_board("   \n", FRACTION)


# --- _number: the ceiling that six categories' thresholds depend on -----------------------------


def test_a_fraction_board_refuses_a_value_above_its_declared_ceiling() -> None:
    """The control `test_sources.py` asserts the DECLARATION of and never exercised.

    That test's own failure message works the example: "a value of 84.7 would be multiplied to
    8470". Deleting the ceiling produced exactly 8470.0 and stayed green across the whole suite.
    8470 clears `computer-use`'s floor of 53.4 by two orders of magnitude, so the product would
    recommend on a scale 100x wrong with every gate passing.
    """
    raw = _csv("Model version,Score,Started at", "already-percent,84.7,2026-01-01", "ok,0.9,2026-01-01")
    rows, skipped = parse_board(raw, FRACTION)

    assert [r.raw_name for r in rows] == ["ok"]
    assert skipped == 1
    assert rows[0].score == pytest.approx(90.0)


def test_a_raw_board_has_no_ceiling_because_elo_has_none() -> None:
    """The other direction, so the fix cannot be "reject everything large"."""
    rows, skipped = parse_board(_csv("Model version,Elo", "m,1711.9"), RAW)
    assert skipped == 0
    assert rows[0].score == pytest.approx(1711.9)


def test_a_non_finite_score_is_skipped_and_counted() -> None:
    """`nan` passes BOTH remaining guards once `isfinite` is gone: `nan < 0` and `nan > max` are
    each False. It would be stored, and every comparison against it is false forever after."""
    rows, skipped = parse_board(_csv("Model version,Score", "m,nan", "ok,0.5"), FRACTION)
    assert [r.raw_name for r in rows] == ["ok"]
    assert skipped == 1
    assert all(math.isfinite(r.score) for r in rows)


def test_a_negative_score_is_skipped_and_counted() -> None:
    rows, skipped = parse_board(_csv("Model version,Score", "m,-0.5", "ok,0.5"), FRACTION)
    assert [r.raw_name for r in rows] == ["ok"]
    assert skipped == 1


def test_a_row_with_no_model_name_is_skipped_and_counted() -> None:
    rows, skipped = parse_board(_csv("Model version,Score", ",0.5", "ok,0.5"), FRACTION)
    assert [r.raw_name for r in rows] == ["ok"]
    assert skipped == 1


def test_the_skipped_count_is_the_number_actually_dropped() -> None:
    """Dies to: never incrementing `skipped`. The build report would claim a clean ingest."""
    raw = _csv("Model version,Score", "a,0.5", "b,notanumber", ",0.3", "d,9.9")
    rows, skipped = parse_board(raw, FRACTION)
    assert len(rows) == 1
    assert skipped == 3, "three rows were dropped and the report must say three"


# --- the unit conversion and the one-row-per-model rule ------------------------------------------


def test_a_fraction_board_is_converted_onto_the_projects_scale() -> None:
    """Dies to: `multiplier = 1.0` always. Every fraction board would ingest 0.847 instead of 84.7
    and ALL SIX new category floors would then reject everything — a total, silent outage."""
    rows, _ = parse_board(_csv("Model version,Score", "m,0.847"), FRACTION)
    assert rows[0].score == pytest.approx(84.7)


def test_a_model_listed_more_than_once_keeps_its_best_score() -> None:
    """Dies to both `>` -> `<` (worst wins) and unconditional overwrite (last wins).

    Boards list a model repeatedly for different scaffolds and reruns; terminalbench is 204 rows
    for 59 models. Which row survives decides what the product recommends.
    """
    raw = _csv("Model version,Score", "m,0.30", "m,0.90", "m,0.60")
    rows, _ = parse_board(raw, FRACTION)
    assert len(rows) == 1
    assert rows[0].score == pytest.approx(90.0)


def test_every_row_declares_the_boards_benchmark_metric_and_harness() -> None:
    """`harness="none"` is an attribution claim: these boards run no agent scaffold."""
    rows, _ = parse_board(_csv("Model version,Score", "m,0.5"), FRACTION)
    (row,) = rows
    assert (row.benchmark, row.metric, row.harness) == ("Test bench", "accuracy", "none")
    assert row.source == "epoch_test"
    assert row.source_url == "epoch-bundle#board.csv"


# --- run_date: validated, never invented --------------------------------------------------------


def test_a_valid_timestamp_becomes_an_iso_date() -> None:
    rows, _ = parse_board(
        _csv("Model version,Score,Started at", "m,0.5,2026-08-19T10:04:00Z"), FRACTION
    )
    assert rows[0].run_date == "2026-08-19"


@pytest.mark.parametrize(
    "stamp", ["<script>alert(1)</script>", "not-a-date", "2026-13-45", "0000000000", ""]
)
def test_a_run_date_that_is_not_a_date_is_dropped_rather_than_truncated(stamp: str) -> None:
    """The M8 security finding. `stamp[:10]` accepted ANY ten characters.

    `<script>alert(1)</script>` became the evidence date `'<script>al'`, and `_evidence_dating`
    only asks whether the date is not-None — so the surface reported its evidence as DATED, which
    is the one thing this module's docstring says it must never do. It also placed ten characters
    of third-party text into an unauthenticated payload.
    """
    rows, _ = parse_board(_csv("Model version,Score,Started at", f"m,0.5,{stamp}"), FRACTION)
    assert rows[0].run_date is None, (
        f"{stamp!r} was accepted as an evaluation date; the surface would call this evidence dated"
    )


def test_a_board_with_no_date_column_leaves_evidence_undated() -> None:
    """Aggregated boards have no evaluation date, and the engine's undated disclosure depends on
    that staying None rather than being filled with something plausible."""
    rows, _ = parse_board(_csv("Model version,Elo", "m,1500"), RAW)
    assert rows[0].run_date is None
