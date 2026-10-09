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
    EXIT_FAILED,
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
    status_path(served).write_text("{}", encoding="utf-8")  # a record from before #198: no builder named
    assert _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "release-0000000"}).returncode != 0
    done = _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "unknown"})
    assert done.returncode == 0, done.stdout + done.stderr
    assert "builder the record does not name" in done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith("-from-unknown"), stamp


@pytest.mark.parametrize("record", [None, "not json"])
def test_unknown_accepts_no_missing_or_unreadable_record(tmp_path: Path, record: str | None) -> None:
    """The second W1 review's R1: `unknown` names a record that does not name its builder, never a copy
    with no record or a record nobody can read."""
    _repo, served, calls, env = _scratch(tmp_path)
    if record is None:
        status_path(served).unlink()
    else:
        status_path(served).write_text(record, encoding="utf-8")
    done = _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "unknown"})
    assert done.returncode != 0, done.stdout + done.stderr
    assert not calls.exists()


def test_the_refusal_runs_before_anything_is_derived(tmp_path: Path) -> None:
    """The second W1 review's R1: a refused deploy leaves no public artifact behind."""
    repo, served, _calls, env = _scratch(tmp_path)
    status_path(served).write_text(json.dumps({"served_built_by": "release-1234567"}), encoding="utf-8")
    assert _deploy(env).returncode != 0
    assert not (repo / "build" / "hosted" / "advisor.db").exists()


# --- The M21-W1 Tester (docs/reviews/m21-wave-1-tester.md) -------------------------------------------------


def test_the_owner_accepts_the_release_the_refusal_names_and_unknown_never_stands_for_it(tmp_path: Path) -> None:
    """The Tester's T1 (#198, the first review's M4): the refusal tells the owner to deploy anyway with
    `DEPLOY_ACCEPT_DATA_FROM=<the record's release>`, and that value is what is accepted. `unknown` names a
    record that names no builder; it never accepts data a named older release built."""
    _repo, served, calls, env = _scratch(tmp_path)
    status_path(served).write_text(json.dumps({"served_built_by": "release-1234567"}), encoding="utf-8")
    refused = _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "unknown"})
    assert refused.returncode != 0 and not calls.exists(), refused.stdout + refused.stderr
    assert "DEPLOY_ACCEPT_DATA_FROM=release-1234567" in refused.stderr, refused.stderr
    done = _deploy({**env, "DEPLOY_ACCEPT_DATA_FROM": "release-1234567"})
    assert done.returncode == 0, done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith("-from-1234567"), stamp


@pytest.mark.parametrize("length", [9, 40])
def test_a_longer_spelling_of_heads_release_is_heads_data(tmp_path: Path, length: int) -> None:
    """The Tester's T2 (#198): the Mac's engine is stamped `release-<RELEASE>` (`scripts/engine_service.sh`),
    and RELEASE holds what `git rev-parse --short` printed at install (`scripts/install_engine_service.sh`),
    which git lengthens past seven characters as a repository grows. Every record `_scratch` writes is seven
    characters long, so the deploy's cut to seven was held by no test: without it, a longer spelling of HEAD
    is refused as another release's data."""
    repo, served, calls, env = _scratch(tmp_path)
    full = _git("-C", str(repo), "rev-parse", "HEAD")
    status_path(served).write_text(json.dumps({"served_built_by": f"release-{full[:length]}"}), encoding="utf-8")
    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith(f"-from-{full[:7]}"), stamp


def test_nights_not_published_in_a_row_keep_naming_the_served_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Tester's T3 (#198): after the Mac moves to a new release, its nights may fail or be refused for a
    while (a source down, a board guard). Each record carries the served artifact's builder forward, never
    the cycle before it, so the second such night still names the release that built what is served, and
    the deploy keeps refusing that data as another release's."""
    target = tmp_path / "advisor.db"
    monkeypatch.setenv("APP_BUILD", "release-aaaaaaa")
    _cycle(target, EXIT_PUBLISHED)
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    for night, code in enumerate((EXIT_FAILED, EXIT_REFUSED, EXIT_FAILED)):
        record = _cycle(target, code)
        assert (record["built_by"], record["served_built_by"]) == ("release-bbbbbbb", "release-aaaaaaa"), night
