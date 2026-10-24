"""#426 (D-223 clause 1): a night that never finishes says where it stopped.

On 2026-10-23 the engine killed the night at 30 minutes, past the cycle's own 27-minute alarm, and the record kept
nothing of it. Now the build runs in a child of the cycle, in the cycle's process group, and the cycle kills it at
`BUILD_LIMIT_SECONDS` with its own clock; the build writes each source's start and finish to a progress file, and a
killed night's record names the source it was reading. Every night's record carries each source's seconds.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from app.workflows import build as build_module
from app.workflows import refresh as refresh_module
from app.workflows.refresh import EXIT_FAILED, refresh, status_path

from .test_refresh import _wide


def _progress_file(argv: list[str]) -> Path:
    return Path(argv[argv.index("--progress-out") + 1])


def test_the_build_child_is_killed_at_its_limit() -> None:
    started = time.monotonic()
    code = refresh_module.build_in_child(
        [], limit=0.5, command=[sys.executable, "-c", "import time; time.sleep(30)"])
    assert code == refresh_module.EXIT_BUILD_KILLED
    assert time.monotonic() - started < 10


def test_a_build_child_that_finishes_returns_its_own_exit_code() -> None:
    assert refresh_module.build_in_child([], limit=30, command=[sys.executable, "-c", "raise SystemExit(3)"]) == 3


def test_a_killed_build_fails_the_night_and_its_record_names_the_source(tmp_path: Path) -> None:
    live = tmp_path / "advisor.db"
    _wide(live)

    def hangs_on_aider(argv: list[str]) -> int:
        _progress_file(argv).write_text("start\tlitellm\t1.0\ndone\tlitellm\t4.0\nstart\taider\t4.0\n",
                                        encoding="utf-8")
        return refresh_module.EXIT_BUILD_KILLED

    outcome, code = refresh(live, builder=hangs_on_aider)
    assert code == EXIT_FAILED
    assert "aider" in outcome.reason and "killed" in outcome.reason, outcome.reason
    record = json.loads(status_path(live).read_text(encoding="utf-8"))
    assert "aider" in record["reason"], record
    assert record["source_seconds"] == {"litellm": 3.0, "aider": None}, record


def test_every_nights_record_carries_each_sources_seconds(tmp_path: Path) -> None:
    live = tmp_path / "advisor.db"
    _wide(live)

    def builds(argv: list[str]) -> int:
        _progress_file(argv).write_text("start\taider\t10.0\ndone\taider\t12.5\n", encoding="utf-8")
        _wide(Path(argv[argv.index("--db") + 1]))
        return 0

    refresh(live, builder=builds)
    record = json.loads(status_path(live).read_text(encoding="utf-8"))
    assert record["source_seconds"] == {"aider": 2.5}, record


def test_the_build_writes_each_sources_start_and_finish(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Through `_ingest_sources`: a source that fails still writes its finish, so only a hang leaves a start open."""
    import dataclasses

    from app.clients.fakes import FakeRawSource
    from app.workflows import sources
    from app.workflows.ingest import RunContext
    from app.workflows.schema import connect

    progress = tmp_path / "progress"
    monkeypatch.setattr(build_module, "PROGRESS_FILE", progress)
    simplebench_file = Path(__file__).resolve().parents[1] / "fixtures" / "simplebench" / "leaderboard-data.js"
    declared = {s.name: s for s in sources.REMOTE_SOURCES}
    chain = (
        dataclasses.replace(declared["datacurve_deepswe"], client=lambda: FakeRawSource("datacurve_deepswe", "{")),
        dataclasses.replace(declared["simplebench"], client=lambda: FakeRawSource(
            "simplebench", simplebench_file.read_text(encoding="utf-8"))),
    )
    build_module._ingest_sources(connect(":memory:"), chain, RunContext(observed_at="2026-10-24T00:00:00Z"))
    events = [line.split("\t")[:2] for line in progress.read_text(encoding="utf-8").splitlines()]
    assert events == [["start", "datacurve_deepswe"], ["done", "datacurve_deepswe"],
                      ["start", "simplebench"], ["done", "simplebench"]]


def test_the_nightly_entry_builds_in_a_child(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The production path, `python -m app.workflows.refresh` (`main`), hands `refresh` the child builder; a
    caller of `refresh()` itself keeps the in-process build its tests patch."""
    seen: dict[str, object] = {}

    def fake_refresh(target: Path, **kwargs):  # type: ignore[no-untyped-def]
        seen.update(kwargs)
        return refresh_module.RefreshOutcome(published=False, reason="t", live_fingerprint=None,
                                             candidate_fingerprint="", surfaces=0), refresh_module.EXIT_UNCHANGED

    monkeypatch.setattr(refresh_module, "refresh", fake_refresh)
    monkeypatch.setattr(refresh_module, "_Limits", lambda *a: type("L", (), {"close": lambda self: None})())
    refresh_module.main(["--db", str(tmp_path / "advisor.db")])
    assert seen["builder"] is refresh_module.build_in_child
