"""#198 (REQ-REL-003, seed L.7 for the data): the hosted deploy names the release that built its data.

The deploy derives the public artifact from the one the owner's Mac serves and stamps the code it
deploys (`release-<sha>-data-<digest>`). W1-style fixes (names, ids) are applied when the data is
built, so a Mac running an older release would ship that release's data under HEAD's stamp. The
refresh now records which build made the served artifact, and the deploy's stamp names it.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from app.workflows.refresh import (
    EXIT_PUBLISHED,
    EXIT_REFUSED,
    RefreshOutcome,
    status_path,
    write_status,
)

from .test_deploy_hosted import _deploy, _scratch

AT = dt.datetime(2026, 10, 9, tzinfo=dt.UTC).timestamp()


def _cycle(target: Path, code: int) -> dict[str, object]:
    write_status(target, RefreshOutcome(published=code == EXIT_PUBLISHED, reason="r", live_fingerprint=None,
                                        candidate_fingerprint="", surfaces=1), code, at=AT)
    return dict(json.loads(status_path(target).read_text(encoding="utf-8")))


def test_the_record_names_the_build_that_made_the_served_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "advisor.db"
    monkeypatch.setenv("APP_BUILD", "release-aaaaaaa")
    first = _cycle(target, EXIT_PUBLISHED)
    assert first["built_by"] == "release-aaaaaaa" and first["served_built_by"] == "release-aaaaaaa"
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    refused = _cycle(target, EXIT_REFUSED)
    assert refused["built_by"] == "release-bbbbbbb"
    assert refused["served_built_by"] == "release-aaaaaaa", "a refused cycle's build is not what is served"
    published = _cycle(target, EXIT_PUBLISHED)
    assert published["served_built_by"] == "release-bbbbbbb"


def test_a_record_without_a_build_says_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_BUILD", raising=False)
    assert _cycle(tmp_path / "advisor.db", EXIT_PUBLISHED)["served_built_by"] == "unknown"


def test_the_deploy_stamp_names_the_release_that_built_the_data(tmp_path: Path) -> None:
    _repo, served, calls, env = _scratch(tmp_path)
    status_path(served).write_text(json.dumps({"served_built_by": "release-1234567890abcdef"}), encoding="utf-8")
    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith("-from-1234567"), stamp


def test_a_dry_run_says_when_the_data_is_another_releases(tmp_path: Path) -> None:
    _repo, served, _calls, env = _scratch(tmp_path)
    status_path(served).write_text(json.dumps({"served_built_by": "release-1234567"}), encoding="utf-8")
    done = _deploy(env, "--dry-run")
    assert done.returncode == 0, done.stdout + done.stderr
    assert "built by release-1234567" in done.stdout + done.stderr


def test_a_served_artifact_with_no_record_is_stamped_unknown(tmp_path: Path) -> None:
    _repo, _served, calls, env = _scratch(tmp_path)
    assert _deploy(env).returncode == 0
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith("-from-unknown"), stamp
