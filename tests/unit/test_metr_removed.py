"""D-249: METR's time horizons leave the app, and `long-tasks` with them.

METR's page reserves all rights and its permission email drew no answer, so no METR number may be
served: the source is not declared, the surface and its family are gone, its credit is deleted (an
artifact that still holds its rows is refused, never credited), the public copy drops its rows, and
the refresh record stops naming it as a silent source.

covers D-249
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.workflows import board_tables, public
from app.workflows.board_tables import CREDITS
from app.workflows.categories import CATEGORIES
from app.workflows.families import FAMILIES
from app.workflows.rank import ATTRIBUTIONS, SOURCE_ATTRIBUTION, attributions_for
from app.workflows.refresh import EXIT_PUBLISHED, RefreshOutcome, status_path, write_status
from app.workflows.sources import REMOTE_SOURCES

from .test_api_v1 import _seeded_db

ROOT = Path(__file__).resolve().parents[2]
METR = "metr_time_horizons"


def test_metr_is_no_declared_source_and_is_named_as_removed_with_its_reason() -> None:
    assert METR not in {source.name for source in REMOTE_SOURCES}
    assert "D-249" in getattr(board_tables, "REMOVED_SOURCES", {}).get(METR, "")


def test_long_tasks_is_no_surface_and_no_family() -> None:
    assert "long-tasks" not in CATEGORIES
    assert "long-tasks" not in FAMILIES
    assert all(METR not in boards for boards in FAMILIES.values())
    assert all(spec.primary_source != METR for spec in CATEGORIES.values())


def test_metr_is_neither_credited_nor_attributed() -> None:
    """Deleted, not retired (D-249 clause 2): no credit, no citation."""
    assert "metr" not in CREDITS
    assert METR not in SOURCE_ATTRIBUTION
    assert not [citation for citation in ATTRIBUTIONS if "METR" in citation]


def test_an_artifact_still_holding_metr_rows_is_refused_not_credited() -> None:
    with pytest.raises(ValueError, match="unattributed evidence source"):
        attributions_for([METR], priced=False)


def test_the_recommendation_route_refuses_long_tasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    client = TestClient(adapter.app)
    assert client.get("/v1/recommendations", params={"task": "long-tasks"}).status_code == 400
    assert "long-tasks" not in {c["id"] for c in client.get("/v1/categories").json()["categories"]}


def test_the_public_copy_drops_every_row_of_a_removed_source(tmp_path: Path) -> None:
    """D-249 clause 3: the first nights' live artifact, built by an older release, still holds METR's rows."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(scores)")]
        picked = ", ".join("?" if c == "source" else c for c in columns)
        planted = conn.execute(f"INSERT INTO scores ({', '.join(columns)}) SELECT {picked} FROM scores",
                               (METR,)).rowcount
    assert planted > 0, "the fixture plants METR rows"
    counts = public.derive(built, served)
    assert counts["scores_removed"] == planted
    with sqlite3.connect(served) as conn:
        assert conn.execute("SELECT count(*) FROM scores WHERE source = ?", (METR,)).fetchone()[0] == 0
    assert public.LEFT_OUT == {}, "the kept state is public: LEFT_OUT stays empty (test_nightly_hosted.py)"


def test_the_refresh_record_forgets_a_removed_sources_last_arrival(tmp_path: Path) -> None:
    """D-249 clause 4: otherwise D-243's notice names METR as silent every night from the eighth."""
    at = dt.datetime(2026, 11, 20, 21, 30, tzinfo=dt.UTC).timestamp()
    old = dt.datetime(2026, 11, 9, 21, 30, tzinfo=dt.UTC).isoformat(timespec="seconds")
    target = tmp_path / "advisor.db"
    status_path(target).write_text(json.dumps({"sources_last_ok": {METR: old, "arena": old}}), encoding="utf-8")
    outcome = RefreshOutcome(published=True, reason="r", live_fingerprint=None, candidate_fingerprint="",
                             surfaces=1, arrived=())
    write_status(target, outcome, EXIT_PUBLISHED, at=at)
    record = json.loads(status_path(target).read_text(encoding="utf-8"))
    assert METR not in record["sources_last_ok"]
    assert METR not in record["silent"]
    assert "arena" in record["silent"], "a declared source's silence is still named"


def test_the_app_neither_routes_to_nor_names_long_tasks() -> None:
    for path in ("ios/ModelRanking/Engine/Router.swift", "ios/ModelRanking/Engine/Language.swift"):
        assert "long-tasks" not in (ROOT / path).read_text(encoding="utf-8"), path
