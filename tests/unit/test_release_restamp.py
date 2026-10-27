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

from app.adapter.nightly import built_by_another
from app.workflows.refresh import EXIT_PUBLISHED, EXIT_REFUSED, EXIT_UNCHANGED, refresh, status_path

from .test_deploy_hosted import _deploy, _git, _scratch
from .test_refresh import _artifact, _builder


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


# --- The hotfix-1026 Tester (docs/reviews/release-tester.md, delta round 2026-10-26 hotfix) ----------------


def test_the_republish_reason_names_d225_and_the_record_says_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-225: the night's record says what the cycle did. A republish of unchanged data reads apart from a
    night whose content moved, and it clears the refusal count like any served cycle."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    record = _record(target)
    status_path(target).write_text(json.dumps({**record, "consecutive_refusals": 2}), encoding="utf-8")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_PUBLISHED
    assert outcome.reason == "unchanged content, republished as this release's own build (D-225)"
    after = _record(target)
    assert after["outcome"] == "published" and after["consecutive_refusals"] == 0
    assert after["built_by"] == after["served_built_by"] == "release-bbbbbbb"


@pytest.mark.parametrize("record", ["not json", ""])
def test_an_unreadable_record_is_taken_over_by_the_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, record: str
) -> None:
    """D-225 clause 1, `or none`: the deploy refuses a record it cannot read (`unreadable`), so a release's
    quiet night over one publishes its own build and writes a record the deploy reads."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    status_path(target).write_text(record, encoding="utf-8")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    _outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_PUBLISHED
    assert _record(target)["served_built_by"] == "release-bbbbbbb"


def test_a_releases_quiet_night_makes_its_own_deploy_and_startup_accept_the_data(tmp_path: Path) -> None:
    """#460 end to end: the record a republish writes is the one `scripts/deploy_hosted_engine.sh` reads.
    Before the night the deploy refuses data an older release built; after a quiet night run by HEAD's
    release (`scripts/nightly_hosted.sh` stamps `release-<short sha>`) the same deploy goes through, and the
    engine's startup catch-up (#258) no longer sees another release's data."""
    repo, served, calls, env = _scratch(tmp_path)
    _artifact(served, top_score=74.5, stamp="t0")
    status_path(served).write_text(json.dumps({"served_built_by": "release-1234567"}), encoding="utf-8")
    assert _deploy(env, "--dry-run").returncode != 0, "the older release's data must be refused first"

    head = _git("-C", str(repo), "rev-parse", "--short=7", "HEAD")
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("APP_BUILD", f"release-{head}")
        outcome, code = refresh(served, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_PUBLISHED, outcome.reason
    assert outcome.live_fingerprint == outcome.candidate_fingerprint

    done = _deploy(env)
    assert done.returncode == 0, done.stdout + done.stderr
    stamp = [arg for arg in calls.read_text(encoding="utf-8").split() if arg.startswith("APP_BUILD=")][-1]
    assert stamp.endswith(f"-from-{head}"), stamp
    assert not built_by_another(_record(served), f"release-{head}")


def test_a_republish_never_overwrites_an_artifact_replaced_mid_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W-047's guard on the D-225 path. The lock stops two refreshes, not a hand-run `build.py`: an unchanged
    cycle that publishes must still re-read the live artifact before it replaces it, as every other publish
    does (`tests/unit/test_refresh.py::test_a_baseline_replaced_mid_cycle_is_not_published_over`). Before
    D-225 an unchanged cycle never published, so it never needed the re-read."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")

    def builds_while_someone_else_publishes(argv: list[str]) -> int:
        _artifact(Path(argv[argv.index("--db") + 1]), top_score=74.5, stamp="LATER")
        _artifact(target, top_score=95.0)  # another writer, mid-cycle
        return 0

    outcome, code = refresh(target, builder=builds_while_someone_else_publishes)
    assert code != EXIT_PUBLISHED, f"a concurrent publish was overwritten: {outcome.reason}"
    with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as conn:
        kept = conn.execute("SELECT max(score) FROM scores").fetchone()[0]
    assert kept == pytest.approx(95.0), "the other writer's artifact was lost"


def test_a_republish_past_a_serving_bound_stays_unchanged_and_names_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#467 (D-227): a republish runs the serving-bound check first, because the engine runs the same check when
    it starts. A release that lowered a bound keeps the older artifact serving on a quiet night, names the bound,
    and does not count a refusal; a night whose content moved is still refused at the bound."""
    target = tmp_path / "advisor.db"
    _served(target, monkeypatch, "release-aaaaaaa")
    served = target.read_bytes()
    monkeypatch.setenv("MODEL_RANKING_MAX_RANKED_ROWS", "1")
    monkeypatch.setenv("APP_BUILD", "release-bbbbbbb")
    outcome, code = refresh(target, builder=_builder(top_score=74.5, stamp="LATER"))
    assert code == EXIT_UNCHANGED, outcome.reason
    assert not outcome.published and "past a bound" in outcome.reason, outcome.reason
    assert target.read_bytes() == served, "a file past the engine's own bound replaced the served one"
    record = _record(target)
    assert record["served_built_by"] == "release-aaaaaaa" and record["consecutive_refusals"] == 0
    moved, code = refresh(target, builder=_builder(top_score=75.5, stamp="LATER"))
    assert code == EXIT_REFUSED and "past a bound" in moved.reason, "the bound must bite on a moved night"
