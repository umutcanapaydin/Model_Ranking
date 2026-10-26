"""#460: a release's first quiet night serves data that release built.

The deploy refuses data another release built (#198, the M21-W1 review's M4), and a cycle whose candidate
matches the served fingerprint used to keep the older release's artifact and its name. So after any code
change, every night whose data did not move refused its own deploy, until a source happened to change.
An unchanged cycle run by a release over an artifact another release built now publishes its own
candidate: the same in everything a user sees, and truly built by the release the record names.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.workflows.refresh import EXIT_PUBLISHED, EXIT_UNCHANGED, refresh, status_path

from .test_refresh import _builder


def _served(target: Path, monkeypatch: pytest.MonkeyPatch, build: str) -> None:
    monkeypatch.setenv("APP_BUILD", build)
    _outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="t0"))
    assert code == EXIT_PUBLISHED


def _record(target: Path) -> dict[str, object]:
    return dict(json.loads(status_path(target).read_text(encoding="utf-8")))


def test_a_new_release_publishes_its_own_build_of_unchanged_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_PUBLISHED, outcome.reason
    assert outcome.live_fingerprint == outcome.candidate_fingerprint, "nothing a user sees moved"
    assert _record(target)["served_built_by"] == "release-bbbbbbb"
    with sqlite3.connect(target) as conn:
        assert {row[0] for row in conn.execute("SELECT observed_at FROM scores")} == {"LATER"}, (
            "the served artifact is the one this release built, not the older one renamed"
        )


def test_the_same_release_stays_unchanged_so_nothing_churns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_UNCHANGED, outcome.reason
    assert _record(target)["served_built_by"] == "release-aaaaaaa"


@pytest.mark.parametrize("build", [None, "dev-abc1234", "unknown"])
def test_a_cycle_that_is_not_a_release_never_republishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, build: str | None
) -> None:
    """A cycle run by hand (`unstamped`) or by dev code names no release the deploy accepts, so taking
    the served artifact over would only turn a deployable record into one nothing deploys."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    if build is None:
        monkeypatch.delenv("APP_BUILD")
    else:
        monkeypatch.setenv("APP_BUILD", build)
    outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_UNCHANGED, outcome.reason
    assert _record(target)["served_built_by"] == "release-aaaaaaa"


def test_a_record_from_before_198_is_taken_over_by_the_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`unknown` (a record naming no builder) deploys only by the owner's override; this release's own
    build of the same data needs none."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    status_path(target).write_text("{}", encoding="utf-8")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    _outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_PUBLISHED
    assert _record(target)["served_built_by"] == "release-bbbbbbb"
