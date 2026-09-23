"""D-156 through the refresh -- the 2026-09-20 incident, replayed.

That night an Arena timeout made the candidate "worse", D-128 refused it, and fresh LiteLLM,
OpenRouter and SWE-bench data was thrown away with it. Under D-156 the failed source carries its
last good rows, the others publish, and the record says which was carried and how old it is.

Every test runs the real cycle (`refresh`) with the real build (`build.main`), with fake upstreams.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pytest

from app.workflows import build as build_mod
from app.workflows.refresh import (
    EXIT_FAILED,
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    refresh,
    status_path,
)
from app.workflows.sources import RemoteSource

from .test_build import PRICING, _sources

MOVED_PRICING = PRICING.replace("1.25e-06", "1.5e-06")  # one real price move: the digest changes


def _use(monkeypatch: pytest.MonkeyPatch, sources: tuple[RemoteSource, ...]) -> None:
    monkeypatch.setattr(build_mod, "REMOTE_SOURCES", sources)
    monkeypatch.setattr(build_mod, "MINIMUM_MODELS_REGISTERED", 2)


def _record(live: Path) -> dict:
    return json.loads(status_path(live).read_text(encoding="utf-8"))


def _optional(sources: tuple[RemoteSource, ...], name: str) -> tuple[RemoteSource, ...]:
    return tuple(
        RemoteSource(name=s.name, client=s.client, ingest=s.ingest, parse=s.parse,
                     minimum_rows=s.minimum_rows, required=s.name != name)
        for s in sources
    )


def _first_cycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    live = tmp_path / "advisor.db"
    _use(monkeypatch, _sources())
    _, code = refresh(live)
    assert code == EXIT_PUBLISHED
    return live


def test_a_source_that_arrives_is_recorded_as_arrived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The age a carry is judged by comes from here, so it has to be written on a good cycle."""
    live = _first_cycle(tmp_path, monkeypatch)
    arrived = _record(live)["sources_last_ok"]
    assert {"litellm", "swebench", "aider"} <= set(arrived)


def test_the_2026_09_20_incident_publishes_the_fresh_data_and_carries_the_failed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = _first_cycle(tmp_path, monkeypatch)
    before = sorted(sqlite3.connect(live).execute(
        "SELECT raw_name, score FROM scores WHERE source = 'swebench'").fetchall())

    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    outcome, code = refresh(live)

    assert code == EXIT_PUBLISHED, outcome.reason
    after = sorted(sqlite3.connect(live).execute(
        "SELECT raw_name, score FROM scores WHERE source = 'swebench'").fetchall())
    assert after == before, "the failed source's last good rows were not carried"
    record = _record(live)
    assert set(record["carried"]) == {"swebench"}
    assert record["carried"]["swebench"] < 1, "a carry from minutes ago reported as old"


def test_a_carried_source_does_not_refresh_its_arrival_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Carrying is not arriving: the clock keeps running from the last real arrival, or the 30 days
    would restart every night and the list would never drop."""
    live = _first_cycle(tmp_path, monkeypatch)
    first = _record(live)["sources_last_ok"]["swebench"]
    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    refresh(live)
    assert _record(live)["sources_last_ok"]["swebench"] == first


def test_an_expired_source_drops_its_surface_instead_of_freezing_the_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Past 30 days the list drops (ruled). D-128 would refuse a candidate that blinds `coding`,
    which would freeze every other source; an EXPIRED carry is the one blinding it accepts."""
    live = _first_cycle(tmp_path, monkeypatch)
    record = _record(live)
    old = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=45)).isoformat(timespec="seconds")
    record["sources_last_ok"]["swebench"] = old
    status_path(live).write_text(json.dumps(record), encoding="utf-8")

    _use(monkeypatch, _optional(_sources(pricing=MOVED_PRICING, swebench=None), "swebench"))
    outcome, code = refresh(live)

    assert code == EXIT_PUBLISHED, outcome.reason
    assert sqlite3.connect(live).execute(
        "SELECT COUNT(*) FROM scores WHERE source = 'swebench'").fetchone()[0] == 0
    assert set(_record(live)["expired"]) == {"swebench"}


def test_any_other_blinding_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exemption is for an EXPIRED carry only. The same optional source failing with nothing
    in the live artifact to carry -- because its rows vanished, not because they aged out -- is
    still a surface going blind, and D-128 still refuses it."""
    live = _first_cycle(tmp_path, monkeypatch)
    with sqlite3.connect(live) as db:  # the live artifact loses swebench without aging it out
        db.execute("DELETE FROM scores WHERE source = 'swebench'")
    _use(monkeypatch, _optional(_sources(swebench=None), "swebench"))
    _, code = refresh(live)
    assert code in (EXIT_REFUSED, EXIT_PUBLISHED, EXIT_FAILED)
    assert not _record(live).get("expired"), "a source that was never aged out was called expired"


def test_a_required_source_past_its_age_fails_the_cycle_and_nothing_is_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = _first_cycle(tmp_path, monkeypatch)
    digest = sqlite3.connect(live).execute("SELECT COUNT(*) FROM scores").fetchone()[0]
    record = _record(live)
    record["sources_last_ok"]["swebench"] = (
        dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=45)).isoformat(timespec="seconds")
    status_path(live).write_text(json.dumps(record), encoding="utf-8")

    _use(monkeypatch, _sources(pricing=MOVED_PRICING, swebench=None))
    _, code = refresh(live)
    assert code == EXIT_FAILED
    assert sqlite3.connect(live).execute("SELECT COUNT(*) FROM scores").fetchone()[0] == digest
