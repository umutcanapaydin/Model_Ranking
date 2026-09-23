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
    assert expert["floor_today"] == CATEGORIES["expert"].min_quality
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
    record = json.loads(out.read_text())
    assert {row["surface"] for row in record["floors"]} == set(CATEGORIES)
    assert "expert" in capsys.readouterr().out
