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

from .test_deploy_hosted import _deploy, _git, _scratch

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
    repo, _served, calls, env = _scratch(tmp_path)
    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    head = _git("-C", str(repo), "rev-parse", "--short=7", "HEAD")
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith(f"-from-{head}"), stamp


@pytest.mark.parametrize("built_by", ["release-1234567", None])
def test_data_built_by_another_release_is_refused(tmp_path: Path, built_by: str | None) -> None:
    """The M21-W1 review's M4: names, ids and boards are applied when the data is built, so data an
    older release built ships an older product under HEAD's stamp (`web-dev` dark before D-190's board
    arrives). The deploy refuses it, a dry run included, and nothing is deployed."""
    _repo, served, calls, env = _scratch(tmp_path)
    record = status_path(served)
    if built_by is None:
        record.unlink()
    else:
        record.write_text(json.dumps({"served_built_by": built_by}), encoding="utf-8")
    for flags in ((), ("--dry-run",)):
        done = _deploy(env, *flags)
        assert done.returncode != 0, flags
        said = done.stdout + done.stderr
        assert "built by" in said and "refresh" in said, said
    assert not calls.exists()


def test_data_from_another_release_deploys_when_the_owner_names_it(tmp_path: Path) -> None:
    """The refusal is lifted only for the release the owner names, never for any."""
    _repo, served, calls, env = _scratch(tmp_path)
    status_path(served).unlink()
    assert _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "release-0000000"}).returncode != 0
    done = _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "unknown"})
    assert done.returncode == 0, done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith("-from-unknown"), stamp
