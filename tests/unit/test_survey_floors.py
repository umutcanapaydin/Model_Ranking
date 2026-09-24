"""D-148 -- every surface's floor under the ROWS rule, reproducibly (M15-W1 review M-2, M16-W3 P4).

`scripts/survey_boards.py --floors` reads the artifact the product serves, with no network, and prints
each surface's floor under the rule D-148 chose (the top third of the board's ROWS, one per raw name
as the parser stores them) beside the two it did not (distinct models, D-145; the ranked
population) and beside the floor `categories.py` ships today. The owner rules from that table.

It also carries the test the W4 review found missing (MINOR-5): `parse_rate_board` keeps each
model's BEST score, as the Elo path does.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path
from types import ModuleType

import pytest

from app.workflows.categories import CATEGORIES
from app.workflows.schema import connect

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "survey_boards.py"


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("survey_boards", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _board(rows: list[tuple[str, float]], date: str = "2026-09-01") -> str:
    return json.dumps({"rows": [
        {"row": {"model_name": n, "score": s, "category": "overall",
                 "leaderboard_publish_date": date}} for n, s in rows]})


@pytest.mark.parametrize("order", [[0.40, 0.55], [0.55, 0.40]])
def test_a_rate_board_keeps_each_models_best_score_whichever_comes_first(order: list[float]) -> None:
    rows, skipped = _script().parse_rate_board(
        _board([("m", order[0]), ("m", order[1]), ("n", 0.3)]), source="s", benchmark="b")
    best = {r.raw_name: r.score for r in rows}
    assert best == {"m": 55.0, "n": 30.0}
    assert skipped == 1


def _artifact(tmp_path: Path, rows: list[tuple[str, float, str]], spec_id: str = "expert") -> Path:
    """An artifact holding `rows` (raw_name, score, effort) on one surface's primary board."""
    spec = CATEGORIES[spec_id]
    path = tmp_path / "advisor.db"
    conn = connect(str(path))
    conn.executemany(
        "INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
        "source_url, observed_at) VALUES (?, ?, ?, ?, 'h', ?, ?, 'u', '2026-09-01T00:00:00+00:00')",
        [(n, spec.primary_benchmark, spec.metric, s, e, spec.primary_source) for n, s, e in rows])
    conn.commit()
    conn.close()
    return path


def test_the_rows_rule_takes_the_top_third_of_every_row_on_the_board(tmp_path: Path) -> None:
    """Six rows: the top third is the 2nd highest. Two rows of one raw name at two efforts are two
    rows under D-148, and one model under the distinct rule -- which is the difference D-148 ruled."""
    path = _artifact(tmp_path, [("a", 90.0, "high"), ("a", 88.0, "low"), ("b", 80.0, "unspecified"),
                                ("c", 70.0, "unspecified"), ("d", 60.0, "unspecified"),
                                ("e", 50.0, "unspecified")])
    table = {row["surface"]: row for row in _script().floors(sqlite3.connect(path))}
    expert = table["expert"]
    assert expert["board_rows"] == 6
    assert expert["floor_rows"] == 88.0
    assert expert["efforts"] == ["high", "low", "unspecified"]


def test_only_the_surfaces_own_source_and_metric_count(tmp_path: Path) -> None:
    """Review MINOR-4 (M24, M25): `epoch_swe_bench_verified` shares `coding`'s benchmark, so a
    count without the source predicate is 206 rows, not 173. An off-metric row must not count
    either."""
    path = _artifact(tmp_path, [("a", 90.0, "unspecified"), ("b", 80.0, "unspecified"),
                                ("c", 70.0, "unspecified")])
    spec = CATEGORIES["expert"]
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                   "source_url, observed_at) VALUES ('x', ?, ?, 99, 'h', 'unspecified', 'other_src', "
                   "'u', 'z')", (spec.primary_benchmark, spec.metric))
        db.execute("INSERT INTO scores (raw_name, benchmark, metric, score, harness, effort, source, "
                   "source_url, observed_at) VALUES ('y', ?, 'another metric', 98, 'h', "
                   "'unspecified', ?, 'u', 'z')", (spec.primary_benchmark, spec.primary_source))
    expert = {r["surface"]: r for r in _script().floors(sqlite3.connect(path))}["expert"]
    assert expert["board_rows"] == 3
    assert expert["floor_rows"] == 90.0


def test_every_surface_is_in_the_table_even_with_an_empty_board(tmp_path: Path) -> None:
    """A surface missing from the table is a surface nobody rules on; an empty board says so."""
    path = _artifact(tmp_path, [("a", 90.0, "unspecified")])
    table = {row["surface"]: row for row in _script().floors(sqlite3.connect(path))}
    assert set(table) == set(CATEGORIES)
    assert table["coding"]["board_rows"] == 0 and table["coding"]["floor_rows"] is None


def test_the_floors_mode_reads_the_artifact_and_needs_no_network(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _artifact(tmp_path, [("a", 90.0, "unspecified"), ("b", 70.0, "unspecified"),
                                ("c", 50.0, "unspecified")])
    out = tmp_path / "floors.json"
    assert _script().main(["--floors", "--db", str(path), "--out", str(out)]) == 0
    record = json.loads(out.read_text(encoding="utf-8"))
    assert {row["surface"] for row in record["floors"]} == set(CATEGORIES)
    assert "expert" in capsys.readouterr().out


# --- M17-W2 P4: how many models each category slice can rank (#22) ------------------------------


@pytest.mark.slices
def test_the_slice_survey_counts_rows_and_the_models_the_engine_can_rank(tmp_path: Path) -> None:
    """`--slices` writes every declared slice into a COPY of the artifact, reconciles, and reports per
    board: rows, the floor, and the ranked population (reconciled and priced). The served file is
    never written, and a slice adds no model its `overall` board lacks."""
    from app.clients.arena_slices import ArenaSlice
    from app.clients.fakes import fake_slice_client, slice_parquet
    from app.workflows.build import build

    from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

    artifact = tmp_path / "advisor.db"
    conn = connect(str(artifact))
    build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
          minimum_models=2)
    conn.close()
    before = artifact.read_bytes()

    boards = (ArenaSlice("text", "multi_turn", measured_rows=4),
              ArenaSlice("vision", "ocr", measured_rows=2))
    text = slice_parquet([(name, 1300.0 - i, "multi_turn", "2026-09-13")
                          for i, name in enumerate(["gpt-5", "claude-4-5-opus", "unknown-x"])])
    vision = slice_parquet([("gpt-5", 1200.0, "ocr", "2026-09-13")])
    survey = _script().measure_slices(
        artifact, tmp_path, client=fake_slice_client({"text": text, "vision": vision}), slices=boards)

    by_board = {record["board"]: record for record in survey["boards"]}
    assert by_board["arena_text_multi_turn"]["rows"] == 3
    assert by_board["arena_text_multi_turn"]["floor"] == 2
    assert by_board["arena_text_multi_turn"]["ranked_population"] == 2
    assert by_board["arena_vision_ocr"]["ranked_population"] == 1
    assert survey["models_after"] == survey["models_before"]
    assert survey["bytes_after"] >= survey["bytes_before"] > 0  # four rows may fit free pages
    assert artifact.read_bytes() == before, "the survey wrote to the served artifact"
