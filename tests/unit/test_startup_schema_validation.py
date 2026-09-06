"""Startup refuses a database the serving path cannot read — cites REQ-FIX-002.

**The hole this closes, reproduced before it was diagnosed.** `_database_unusable` checked a
hand-written list: the tables `scores` and `pricing`, a `scores.effort` column, and a non-empty
`px_median`. `models` was not on that list, and `rank.py` joins it on every ranking. A database
carrying everything the probe asked for and no `models` table returned `None` — "usable" — so the
process would boot green, `/health` would report a healthy build, and every surface would answer
with nothing.

That is the shape this project has already paid for twice (W-023, W-058): healthy to every
existence check, answering nothing. The probe's own docstring said it existed because a stat-only
version had said yes to a database that could not serve; it had simply been extended one table at a
time, each time by whoever met the next failure.

**So the fix is not a longer list.** A list is a thing somebody must remember to update, and the
next table added to a query will not be on it either. The probe now RUNS what the serving path
runs — one ranking per advertised surface, read-only — so the check cannot drift from the code it
is checking. These tests pin both halves: it must refuse a schema the ranking cannot read, and it
must still accept the real artifact.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app import adapter as _adapter_pkg  # noqa: F401  (ensures the module below imports cleanly)
from app.adapter import main as main_module
from app.adapter.main import _database_unusable
from app.workflows.categories import CATEGORIES

from .test_refresh import _artifact

REPO = Path(__file__).resolve().parents[2]

#: The objects the OLD probe asked for. A database with exactly these and nothing else was
#: accepted; it is the fixture that proves the regression.
#: `score`, not `value` — M13-W1 review MINOR. The first version named the column `value`, so
#: `assert "models" in problem` passed only because SQLite reports a missing TABLE before a missing
#: COLUMN. Add a `models` table and the message became `no such column: score`, and the fixture that
#: claimed to isolate `models` was isolating a typo.
LEGACY_PROBE_SCHEMA = """
CREATE TABLE scores (
    model_id TEXT, benchmark TEXT, metric TEXT, score REAL, effort TEXT,
    source TEXT, harness TEXT, run_date TEXT, observed_at TEXT, raw_name TEXT
);
CREATE TABLE pricing (model_id TEXT, input_per_m REAL, output_per_m REAL, source TEXT);
CREATE TABLE px_median (task TEXT, median REAL);
INSERT INTO px_median VALUES ('coding', 3.0);
"""


def _write(path: Path, script: str) -> Path:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(script)
        conn.commit()
    finally:
        conn.close()
    return path


def test_a_database_without_models_is_refused(tmp_path: Path) -> None:
    """The exact artifact the old probe called usable.

    `models` carries the display name and vendor of every ranked row. Without it a ranking raises,
    and the process converts that into a per-surface unavailable answer — after boot, per request,
    with nothing at startup having said the artifact was wrong.
    """
    db = _write(tmp_path / "no_models.db", LEGACY_PROBE_SCHEMA)
    problem = _database_unusable(db)
    assert problem is not None, "a database the ranking cannot read was accepted at startup"
    assert "models" in problem, f"the refusal must name what is missing, got: {problem!r}"


def test_a_servable_artifact_is_accepted(tmp_path: Path) -> None:
    """The other half, and the one that makes the first half safe to trust.

    A refusal check is only as good as its false-positive rate: one that rejects a good artifact
    fails closed on every boot, which is a worse outage than the defect it prevents. This wave made
    startup refuse on any sqlite error from a real ranking, so this is the branch most worth
    guarding — and it must be guarded somewhere a gate can SEE.

    **It was not. M13-W1 review MAJOR-4.** The first version read `Path("advisor.db")` and skipped
    when absent, with the comment *"the repo ships it; CI may not"*. `.gitignore` is `*.db`: the
    repo does NOT ship it, so the only test of the accept half skipped on every fresh clone and in
    CI. It is built here instead, from the same seeded fixture the refresh tests use.
    """
    assert _database_unusable(_artifact(tmp_path / "good.db")) is None


def test_the_shipping_artifact_is_accepted() -> None:
    """The same claim against the real thing, when the real thing is present.

    Kept in ADDITION to the built fixture rather than instead of it: a fixture proves the check
    accepts what this test suite can construct, and only the shipping artifact proves it accepts
    what the product actually serves. This one may skip; the one above may not.
    """
    artifact = REPO / "advisor.db"
    if not artifact.exists():  # pragma: no cover - gitignored; absent on a fresh clone
        pytest.skip("advisor.db is not in this working tree (it is gitignored)")
    assert _database_unusable(artifact) is None


def test_an_artifact_that_ranks_nothing_is_refused(tmp_path: Path) -> None:
    """M13-W1 review BLOCKING-1: readable schema, zero rankable surfaces.

    The probe used to run every surface's ranking and throw the rows away, so it caught a MISSING
    table (which raises) and missed an EMPTY one (which returns no rows). A reviewer reproduced
    three artifacts that booted green and answered nothing; this is the cheapest of them.
    """
    db = _artifact(tmp_path / "emptied.db")
    conn = sqlite3.connect(db)
    try:
        conn.execute("DELETE FROM models")
        conn.commit()
    finally:
        conn.close()
    problem = _database_unusable(db)
    assert problem is not None, "an artifact that ranks nothing on any surface was accepted"
    assert "ranks nothing" in problem


def test_every_advertised_surface_is_probed(tmp_path: Path) -> None:
    """M13-W1 tester MAJOR-2: "all nine surfaces" is the stated mechanism and nothing pinned it.

    Truncating the loop to the first surface survived the entire suite. `category_ranking` is one
    parameterised query today, so nine equals one for schema purposes and the impact is currently
    nil — but the comment sells nine-per-boot as the safety property, and the moment one spec
    acquires its own query shape the loop can shrink to one with no test noticing.
    """
    probed: list[str] = []
    real = main_module.category_ranking

    def spy(conn: object, spec: object) -> list[object]:
        probed.append(getattr(spec, "id", "?"))
        return real(conn, spec)  # type: ignore[arg-type]

    main_module.category_ranking = spy  # type: ignore[assignment]
    try:
        _database_unusable(_artifact(tmp_path / "probed.db"))
    finally:
        main_module.category_ranking = real  # type: ignore[assignment]
    assert set(probed) == set(
        CATEGORIES
    ), f"the probe visited {len(set(probed))} of {len(CATEGORIES)} advertised surfaces"


def test_a_non_database_is_still_refused(tmp_path: Path) -> None:
    """Regression guard on the branch that already worked, so the fix cannot eat it."""
    path = tmp_path / "not.db"
    path.write_bytes(b"this is not a sqlite file")
    problem = _database_unusable(path)
    assert problem is not None


def test_an_empty_price_median_table_is_still_refused(tmp_path: Path) -> None:
    """M7-W2's finding must survive M13's rewrite.

    An empty `px_median` yields zero rows from the ranking JOIN, so every query answers 200 with no
    picks while `/health` reports healthy. That check predates this one and is easy to lose when
    the surrounding function is replaced.
    """
    db = _write(
        tmp_path / "no_medians.db",
        LEGACY_PROBE_SCHEMA.replace("INSERT INTO px_median VALUES ('coding', 3.0);", ""),
    )
    problem = _database_unusable(db)
    assert problem is not None
