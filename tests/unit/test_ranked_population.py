"""REQ-EVI-002 / W-037 — the population the engine ranks has a name, and calibration calls it.

The warning this file discharges was raised three times, each time from a different wrong
population: raw CSV rows, then parsed board rows, then the full board (521 models on ECI where the
engine ranks 58). Every correction came from measuring and none from reading, because there was no
term to look up and no function to call, so the question got answered from whatever data was
nearest.

So a test that only checked "a function called `ranked_population` exists" would pass the day the
bug came back. These tests check the two things that actually stop it:

  1. the name is NARROWER than the board — it drops what cannot be recommended, and a fixture
     contains rows of both kinds so the assertion has something to fail against;
  2. the calibration script REACHES it rather than re-deriving it, and refuses to size a threshold
     when it cannot.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.workflows.categories import get_category
from app.workflows.rank import ranked_population
from app.workflows.schema import connect

SURFACE = "assistant"


def _board(path: Path) -> None:
    """Three score rows; exactly ONE of them can be recommended.

    * `priced`       — registered and priced        → in the ranked population
    * `unpriced`     — registered, no price median  → on the board, unrecommendable
    * (unreconciled) — a raw name the registry never canonicalises, `model_id IS NULL`

    The two rejects are the whole point of the fixture: with only `priced` present, a
    `ranked_population` that returned the entire board would read GREEN.
    """
    spec = get_category(SURFACE)
    conn = connect(str(path))
    try:
        for model in ("priced", "unpriced"):
            conn.execute(
                "INSERT INTO models (id, display, vendor) VALUES (?, ?, 'V')", (model, model)
            )
        rows = [("priced", "Priced", 1500.0), ("unpriced", "Unpriced", 1600.0)]
        for model_id, raw, score in rows:
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
                " harness, source_url, observed_at) VALUES (?, ?, ?, ?, ?, ?, 'none',"
                " 'fixture://x', 't')",
                (model_id, raw, spec.primary_source, spec.primary_benchmark, spec.metric, score),
            )
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
            " harness, source_url, observed_at) VALUES (NULL, 'nobody-registered', ?, ?, ?,"
            " 1700.0, 'none', 'fixture://x', 't')",
            (spec.primary_source, spec.primary_benchmark, spec.metric),
        )
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('priced', 1.0, 2.0)")
        conn.commit()
    finally:
        conn.close()


def test_the_ranked_population_is_narrower_than_the_board(tmp_path: Path) -> None:
    """Three rows on the board, one recommendable. The gap IS the warning."""
    db = tmp_path / "board.db"
    _board(db)

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        board = conn.execute("SELECT count(*) FROM scores").fetchone()[0]
        ranked = ranked_population(conn, get_category(SURFACE))
    finally:
        conn.close()

    assert board == 3, "fixture assumption: the board must carry rows the engine cannot rank"
    assert [row.model for row in ranked] == ["priced"], (
        "the ranked population included a model that is unpriced or never reconciled; sizing a "
        f"threshold against this set admits models nobody can be offered. Got: {ranked}"
    )
    assert ranked[0].blended_per_m > 0, "a ranked row without a price is not recommendable"


def test_what_the_surface_serves_comes_from_the_ranked_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The name is not a second opinion. Every pick `/v1` returns is in it, and nothing else is.

    Checked through the real entry point rather than against `category_ranking` directly — the two
    being the same function today is an implementation fact, and a test that asserted it would go
    green if the endpoint grew its own query tomorrow.
    """
    db = tmp_path / "served.db"
    _board(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")

    from fastapi.testclient import TestClient

    from app.adapter import main as adapter

    response = TestClient(adapter.app).get(
        "/v1/recommendations", params={"task": SURFACE, "budget": "unlimited"}
    )
    assert response.status_code == 200
    (answer,) = response.json()["answers"]
    served = {pick["model"] for pick in answer["picks"]}

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        population = {row.model for row in ranked_population(conn, get_category(SURFACE))}
    finally:
        conn.close()

    assert served, "fixture assumption: the surface must return at least one pick"
    assert served <= population, (
        f"the surface offered a model outside its own ranked population: {served - population}"
    )


# --- "calibration must call it" is the half a name alone does not deliver ----------------------


def test_the_calibration_script_refuses_to_size_a_threshold_without_the_ranked_population(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse, do not fall back (D-121). Falling back to the board IS W-037."""
    import scripts.arena_calibration as calibration

    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "arena_overall_0.json").write_text(
        '{"num_rows_total": 2, "rows": ['
        '{"row": {"rating": 1500.0, "rating_upper": 1510.0, "rating_lower": 1490.0}},'
        '{"row": {"rating": 1400.0, "rating_upper": 1412.0, "rating_lower": 1388.0}}]}',
        encoding="utf-8",
    )

    assert calibration.main(["arena_calibration.py", str(pages)]) == 0
    out = capsys.readouterr().out

    assert "THRESHOLD SECTIONS REFUSED" in out, (
        "the script sized a value window from the board with no artifact to check it against; "
        "that is the exact calibration W-037 records three times"
    )
    assert "within-N-of-leader" not in out, "a refused section still printed its figures"
    assert "RANKED POPULATION" not in out, "the script reported a population it never read"
    assert "--db" in out, "the refusal must name the remedy, not just decline"


def test_the_calibration_script_reaches_the_named_accessor_rather_than_re_deriving_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A private copy of the join would satisfy the sentence and reproduce the defect.

    The check is behavioural: replace `ranked_population` in the script's namespace and the
    script's numbers must follow it. A script holding its own SQL would ignore the replacement and
    report the artifact's real population — which is what this assertion catches.
    """
    import scripts.arena_calibration as calibration

    db = tmp_path / "reached.db"
    _board(db)

    sentinel = [type("Row", (), {"score": 4242.0})()]
    monkeypatch.setattr(calibration, "ranked_population", lambda _conn, _spec: sentinel)

    assert calibration.ranked_ratings(str(db), SURFACE) == [4242.0], (
        "the calibration path did not go through `ranked_population`; it is answering the "
        "question from data of its own again"
    )


def test_every_threshold_producing_script_imports_the_named_accessor() -> None:
    """V4C-49: the rule ships with its gate, or it is a sentence somebody has to remember.

    REQ-EVI-002 says calibration must call the accessor. Nothing stops the NEXT calibration script
    from being written the old way, so the rule is executable: a script that prints
    `value_window`/`min_quality` sizing must import `ranked_population`.
    """
    import ast

    offenders = []
    for path in sorted(Path("scripts").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if not any(word in source for word in ("value_window", "min_quality")):
            continue
        imported = {
            alias.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        if "ranked_population" not in imported:
            offenders.append(path.as_posix())

    assert not offenders, (
        "these scripts size a threshold without reaching the engine's ranked population "
        f"(REQ-EVI-002): {offenders}"
    )
