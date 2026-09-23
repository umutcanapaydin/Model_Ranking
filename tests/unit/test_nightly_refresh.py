"""REQ-REF-008, D-151 / D-154 -- the engine refreshes itself once a night, and nothing a cycle does
reaches the server.

The schedule is tested as arithmetic on an injected clock. The isolation is tested with REAL child
processes -- one that hangs, one that raises, one that exits failed, one killed mid-publish --
because "a failing refresh cannot block the server" is the claim D-149 said the build wave must
SHOW rather than assume, and a fake process would only show that the fake behaves.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import random
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main, nightly
from app.workflows.refresh import EXIT_BUSY, refresh

from .test_refresh import _artifact, _builder

D = dt.datetime


class _Fixed(random.Random):
    """A random source that always answers `value`, so the window's edges can be asked for."""

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def random(self) -> float:
        return self.value


# --- D-151 clause 1: once a night, inside 23:00-01:00 ----------------------------------------------

@pytest.mark.parametrize(
    ("now", "earliest", "latest"),
    [
        (D(2026, 9, 23, 12, 0), D(2026, 9, 23, 23, 0), D(2026, 9, 24, 1, 0)),  # afternoon: tonight
        (D(2026, 9, 23, 23, 30), D(2026, 9, 23, 23, 30), D(2026, 9, 24, 1, 0)),  # inside: not before now
        (D(2026, 9, 24, 0, 30), D(2026, 9, 24, 0, 30), D(2026, 9, 24, 1, 0)),  # after midnight: same window
        (D(2026, 9, 24, 1, 0), D(2026, 9, 24, 23, 0), D(2026, 9, 25, 1, 0)),  # window just shut: tomorrow
    ],
)
def test_the_run_falls_inside_the_window_and_never_in_the_past(
    now: D, earliest: D, latest: D
) -> None:
    for value in (0.0, 0.5, 0.999999):
        at = nightly.pick_run_time(now, _Fixed(value))
        assert earliest <= at < latest, (now, value, at)


def test_the_minute_is_spread_across_the_window_rather_than_fixed() -> None:
    picks = {nightly.pick_run_time(D(2026, 9, 23, 12, 0), random.Random(seed)) for seed in range(50)}
    assert len({p.replace(second=0, microsecond=0) for p in picks}) > 30


def test_after_a_night_runs_the_next_run_is_the_following_night() -> None:
    """Once a DAY: the next pick starts from the end of the window just used, not from 'now', or a
    run at 23:05 would pick another minute before 01:00."""
    ran = nightly.pick_run_time(D(2026, 9, 23, 12, 0), _Fixed(0.04))  # ~23:05
    after = nightly.window_around(ran)[1]
    following = nightly.pick_run_time(after, _Fixed(0.0))
    assert following == D(2026, 9, 24, 23, 0)


# --- D-151 clause 2: one catch-up at startup when the last good cycle is over a day old -------------

NOW = 1_790_000_000.0


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        (None, True),
        ({"at": NOW - 3600, "exit_code": 0}, False),  # published an hour ago
        ({"at": NOW - 3600, "exit_code": 1}, False),  # unchanged an hour ago: also good
        ({"at": NOW - 25 * 3600, "exit_code": 1}, True),  # good, but more than a day old
        ({"at": NOW - 3600, "exit_code": 2}, True),  # the last cycle failed
        ({"at": NOW - 3600, "exit_code": 3}, True),  # the last cycle was refused
        ({"at": "yesterday", "exit_code": 0}, True),  # a record nobody can do arithmetic on
        ({"at": float("nan"), "exit_code": 0}, True),
    ],
)
def test_a_catch_up_runs_only_when_no_good_cycle_is_on_record_within_a_day(
    record: dict[str, object] | None, expected: bool
) -> None:
    assert nightly.needs_catch_up(record, NOW) is expected


def test_the_record_is_the_refreshs_own_file(tmp_path: Path) -> None:
    db = tmp_path / "advisor.db"
    assert nightly.read_record(db) is None
    (tmp_path / "advisor.db.refresh.json").write_text(json.dumps({"at": NOW, "exit_code": 0}))
    assert nightly.read_record(db) == {"at": NOW, "exit_code": 0}
    (tmp_path / "advisor.db.refresh.json").write_text("{torn")
    assert nightly.read_record(db) is None


class _Clock:
    """A wall clock that moves only when the schedule sleeps."""

    def __init__(self, start: D) -> None:
        self.at = start
        self.start = start
        self.slept: list[float] = []

    def now(self) -> D:
        return self.at

    async def sleep(self, seconds: float) -> None:
        # A schedule that never runs would otherwise loop here forever; fail it instead.
        assert self.at - self.start < dt.timedelta(days=10), "ten simulated days and no run"
        self.slept.append(seconds)
        self.at += dt.timedelta(seconds=seconds)
        await asyncio.sleep(0)


def _schedule(tmp_path: Path, clock: _Clock, runs: list[str], stop_after: int) -> nightly.NightlyRefresh:
    schedule = nightly.NightlyRefresh(
        db=tmp_path / "advisor.db", command=["unused"], now=clock.now, wall=lambda: NOW,
        sleep=clock.sleep, rng=_Fixed(0.5),
    )

    async def fake_run(trigger: str) -> int:
        runs.append(f"{trigger}@{clock.now():%d %H:%M}")
        if len(runs) >= stop_after:
            raise asyncio.CancelledError
        return 0

    schedule.run_once = fake_run  # type: ignore[method-assign]
    return schedule


def test_a_stale_engine_catches_up_once_then_keeps_the_nightly_schedule(tmp_path: Path) -> None:
    clock, runs = _Clock(D(2026, 9, 23, 12, 0)), []
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(_schedule(tmp_path, clock, runs, stop_after=3).serve())
    assert runs == ["catch-up@23 12:01", "nightly@24 00:00", "nightly@25 00:00"]
    assert max(clock.slept) <= nightly.POLL_SECONDS, "a long sleep would miss a moved clock"


def test_a_fresh_engine_does_not_catch_up(tmp_path: Path) -> None:
    (tmp_path / "advisor.db.refresh.json").write_text(json.dumps({"at": NOW - 5 * 3600, "exit_code": 1}))
    clock, runs = _Clock(D(2026, 9, 23, 12, 0)), []
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(_schedule(tmp_path, clock, runs, stop_after=1).serve())
    assert runs == ["nightly@24 00:00"]


def test_an_error_in_the_schedule_does_not_end_it(tmp_path: Path) -> None:
    (tmp_path / "advisor.db.refresh.json").write_text(json.dumps({"at": NOW - 5 * 3600, "exit_code": 1}))
    clock, runs = _Clock(D(2026, 9, 23, 12, 0)), []
    schedule = _schedule(tmp_path, clock, runs, stop_after=2)
    real_run = schedule.run_once
    calls = {"n": 0}

    async def first_one_breaks(trigger: str) -> int | None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("a bug in the schedule")
        return await real_run(trigger)

    schedule.run_once = first_one_breaks  # type: ignore[method-assign]
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(schedule.serve())
    assert len(runs) == 2, "the schedule died on the first error instead of carrying on"


# --- D-149's stated risk: a refresh cannot block or crash the server --------------------------------

def _child(tmp_path: Path, code: str, *, timeout: float = 30.0) -> nightly.NightlyRefresh:
    return nightly.NightlyRefresh(
        db=tmp_path / "advisor.db", command=[sys.executable, "-c", code], timeout=timeout
    )


def test_a_cycle_that_hangs_is_killed_at_the_timeout(tmp_path: Path) -> None:
    pid_file = tmp_path / "pid"
    schedule = _child(
        tmp_path, f"import os,time; open({str(pid_file)!r},'w').write(str(os.getpid())); "
        "time.sleep(20)", timeout=2.0,
    )
    started = time.monotonic()
    assert asyncio.run(schedule.run_once("nightly")) is None
    assert time.monotonic() - started < 15
    pid = int(pid_file.read_text())
    with pytest.raises(ProcessLookupError):
        import os

        os.kill(pid, 0)  # the child is gone, not orphaned
    assert schedule.running_since is None


def test_a_cycle_that_raises_or_fails_reports_its_code_and_does_not_raise(tmp_path: Path) -> None:
    assert asyncio.run(_child(tmp_path, "raise SystemExit(2)").run_once("nightly")) == 2
    assert asyncio.run(_child(tmp_path, "raise RuntimeError('boom')").run_once("nightly")) == 1


def test_a_cycle_that_cannot_start_does_not_raise(tmp_path: Path) -> None:
    schedule = nightly.NightlyRefresh(db=tmp_path / "advisor.db", command=[str(tmp_path / "nope")])
    assert asyncio.run(schedule.run_once("nightly")) is None


def test_a_cycle_killed_mid_publish_leaves_the_live_artifact_and_the_lock_usable(
    tmp_path: Path,
) -> None:
    """The kill lands while the candidate is half-written. REQ-REF-001 already proves this for a
    cycle that FAILS; this is the one killed from outside, which is what the timeout does."""
    live = _artifact(tmp_path / "advisor.db")
    before = live.read_bytes()
    code = (
        "import sys, time\nfrom pathlib import Path\nfrom app.workflows.refresh import refresh\n"
        "def build(argv):\n"
        "    Path(argv[argv.index('--db') + 1]).write_bytes(b'half an artifact')\n"
        "    time.sleep(20)\n"
        "    return 0\n"
        f"refresh(Path({str(live)!r}), builder=build)\n"
    )
    assert asyncio.run(_child(tmp_path, code, timeout=4.0).run_once("nightly")) is None

    assert live.read_bytes() == before, "a killed cycle changed the live artifact"
    outcome, exit_code = refresh(live, builder=_builder(top_score=80.0))
    assert exit_code != EXIT_BUSY, "the killed cycle's lock outlived it (flock should not)"
    assert outcome.published
    # Recorded, not fixed here: the killed cycle's uniquely-named candidate stays behind (W-124).
    assert len(list(tmp_path.glob("advisor.db.*.candidate"))) <= 1


def test_the_server_answers_while_a_cycle_hangs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through the real entry point: the app's lifespan starts the schedule, a hanging child is
    running, and `/health` and `/v1/categories` still answer at once."""
    marker = tmp_path / "started"
    hanging = nightly.NightlyRefresh(
        db=tmp_path / "advisor.db",
        command=[sys.executable, "-c",
                 f"import time; open({str(marker)!r},'w').close(); time.sleep(20)"],
        grace=0.0,
    )
    monkeypatch.setattr(
        nightly.NightlyRefresh, "from_environment", classmethod(lambda cls, relaxed: hanging)
    )

    with TestClient(main.app) as client:
        deadline = time.monotonic() + 15
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists(), "the startup catch-up never started"

        started = time.monotonic()
        health = client.get("/health").json()
        assert client.get("/v1/categories").status_code == 200
        assert time.monotonic() - started < 2.0
        assert health["status"] == "ok"
        assert health["refresh"] == "running"
        closing = time.monotonic()
    # Leaving the block ran the lifespan's shutdown, which cancels the schedule and kills the child;
    # a shutdown that waited the child out would take its whole 20 seconds.
    assert time.monotonic() - closing < 10, "shutdown waited for the refresh instead of killing it"
    assert hanging.running_since is None


def test_health_says_off_when_the_switch_is_off() -> None:
    with TestClient(main.app) as client:
        assert client.get("/health").json()["refresh"] == "off"


def test_health_reports_the_last_recorded_cycle_and_the_next_run(tmp_path: Path) -> None:
    (tmp_path / "advisor.db.refresh.json").write_text(
        json.dumps({"at": NOW, "at_iso": "2026-09-22T11:41:08+00:00", "exit_code": 3})
    )
    schedule = nightly.NightlyRefresh(db=tmp_path / "advisor.db", command=["unused"])
    schedule.next_run = D(2026, 9, 23, 23, 41)
    assert schedule.report() == {
        "refresh": "scheduled",
        "refresh_next": "2026-09-23T23:41",
        "refresh_last": "refused",
        "refresh_last_at": "2026-09-22T11:41:08+00:00",
    }


# --- the switch, and where it may be on ---------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "environment", "allowed"),
    [
        (None, "production", True),
        ("", "production", True),
        ("off", "production", True),
        ("nightly", "test", True),
        ("NIGHTLY ", "development", True),
        ("nightly", "production", False),  # D-116: no ingestion on a serving host
        ("nightly", "", False),  # unset environment is the strict one
        ("nightly", "staging", False),
        ("hourly", "test", False),  # not a value this engine knows
    ],
)
def test_the_switch_is_on_only_where_ingestion_may_run(
    raw: str | None, environment: str, allowed: bool
) -> None:
    problem = nightly.switch_problem(raw, environment, main.RELAXED_ENVS)
    assert (problem is None) is allowed, problem


def test_production_refuses_to_boot_with_the_switch_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Through the real validator, in the environment that raises rather than warns."""
    monkeypatch.setenv(nightly.SWITCH, "nightly")
    with pytest.raises(main.ConfigError, match="D-116"):
        main.validate_startup_config("production")


def test_the_environment_builds_the_refreshs_own_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "advisor.db"))
    monkeypatch.setenv(nightly.EPOCH_DIR, "/bundles/epoch")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv(nightly.SWITCH, raising=False)
    assert nightly.NightlyRefresh.from_environment(main.RELAXED_ENVS) is None

    monkeypatch.setenv(nightly.SWITCH, "nightly")
    schedule = nightly.NightlyRefresh.from_environment(main.RELAXED_ENVS)
    assert schedule is not None
    assert list(schedule.command) == [
        sys.executable, "-B", "-P", "-m", "app.workflows.refresh",
        "--db", str((tmp_path / "advisor.db").resolve()), "--epoch-dir", "/bundles/epoch",
    ]


def test_the_serving_process_never_loads_the_refresh_the_build_or_the_fetchers() -> None:
    """REQ-REF-007's structural half, from the other side (D-116), measured TRANSITIVELY.

    The first version of this test read `main.py`'s and `nightly.py`'s own import lines, and the
    security pass showed what that missed: importing the server loads `app.workflows.ingest`, every
    `app.clients` parser and `httpx`, through `subscribe -> plans -> ingest` (MAJOR-1, W-125). So
    this imports the server in a FRESH interpreter and reads `sys.modules`: whatever else is there,
    the modules that run a cycle or fetch a source are not.
    """
    import subprocess

    probe = (
        "import sys, app.adapter.main\n"
        "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('app.'))))"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True,
        env={**__import__("os").environ, "APP_ENV": "test", "PYTHONPATH": "src"},
    ).stdout.split()
    assert "app.adapter.main" in loaded, "the probe did not import the server"
    cycle = {"app.workflows.refresh", "app.workflows.build", "app.workflows.sources",
             "app.workflows.epoch", "app.workflows.rosters"}
    assert not cycle & set(loaded), sorted(cycle & set(loaded))


def test_the_child_inherits_no_secret_from_the_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Security pass, MINOR-4: the child gets an allowlist, not the owner's whole shell."""
    seen = tmp_path / "env.json"
    monkeypatch.setenv("SOME_API_TOKEN", "do-not-pass-me")
    code = f"import json, os; json.dump(sorted(os.environ), open({str(seen)!r}, 'w'))"
    assert asyncio.run(_child(tmp_path, code).run_once("nightly")) == 0
    names = json.loads(seen.read_text())
    assert "SOME_API_TOKEN" not in names
    assert "PYTHONPATH" in names and "PATH" in names


def test_a_child_that_floods_its_output_is_kept_to_a_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Security pass, MINOR-1: 200 MB of output was buffered whole into the server. Only the tail
    is kept now, and the last line still reaches the log."""
    monkeypatch.setattr(nightly, "OUTPUT_TAIL_BYTES", 4096)
    code = "import sys\nfor i in range(200000): sys.stdout.write('x' * 99 + '\\n')\nprint('LAST LINE')"
    with caplog.at_level("WARNING", logger="app.adapter.nightly"):
        assert asyncio.run(_child(tmp_path, code).run_once("nightly")) == 0
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("nightly refresh |")]
    assert lines and lines[-1] == "nightly refresh | LAST LINE"
    assert len(lines) <= 20


def test_the_tail_never_holds_more_than_its_limit() -> None:
    """The bound itself, measured on the buffer rather than inferred from the log."""
    async def run() -> int:
        reader = asyncio.StreamReader()
        peak = 0
        for _ in range(100):
            reader.feed_data(b"y" * 100_000)
        reader.feed_data(b"END")
        reader.feed_eof()

        class Watched(bytearray):
            def extend(self, data: object) -> None:  # type: ignore[override]
                nonlocal peak
                super().extend(data)  # type: ignore[arg-type]
                peak = max(peak, len(self))

        watched = Watched()
        await nightly.read_tail(reader, watched)
        assert bytes(watched).endswith(b"END")
        assert len(watched) == nightly.OUTPUT_TAIL_BYTES
        return peak

    assert asyncio.run(run()) <= nightly.OUTPUT_TAIL_BYTES + 65536


def test_the_schedule_rechecks_the_switch_when_it_starts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Security pass, MINOR-2: the import-time check is not trusted at start-up time."""
    monkeypatch.setenv("MODEL_RANKING_DB", "advisor.db")
    monkeypatch.setenv(nightly.SWITCH, "nightly")
    monkeypatch.setenv("APP_ENV", "production")
    assert nightly.NightlyRefresh.from_environment(main.RELAXED_ENVS) is None
    monkeypatch.setenv("APP_ENV", "test")
    assert nightly.NightlyRefresh.from_environment(main.RELAXED_ENVS) is not None


def test_the_retirement_script_removes_what_the_installer_installed() -> None:
    """The owner retires launchd with `scripts/retire_refresh.sh` (D-154). Two paths in two scripts
    are two accounts of one fact, pinned together the way the installer's are (W-096)."""
    import plistlib

    retire = Path("scripts/retire_refresh.sh").read_text(encoding="utf-8")
    with Path("deploy/com.hcs.modelranking.refresh.plist").open("rb") as handle:
        job = plistlib.load(handle)
    wrapper_tail = job["ProgramArguments"][1].split("/Library/", 1)[1]
    assert f'LABEL="{job["Label"]}"' in retire
    assert f'WRAPPER="$HOME/Library/{wrapper_tail}"' in retire
    # It refuses to leave a night with no refresher: the engine must say it refreshes first.
    assert retire.index('"refresh"') < retire.index("launchctl bootout")


# --- the M16-W2 review ---------------------------------------------------------------------------------

def test_a_killed_cycle_shows_on_health_instead_of_the_last_good_one(tmp_path: Path) -> None:
    """MAJOR-1: a killed child writes no record, so `/health` kept saying the previous "published"."""
    (tmp_path / "advisor.db.refresh.json").write_text(
        json.dumps({"at": time.time() - 3600, "at_iso": "an hour ago", "exit_code": 0})
    )
    schedule = _child(tmp_path, "import time; time.sleep(20)", timeout=1.0)
    assert asyncio.run(schedule.run_once("nightly")) is None
    assert schedule.report()["refresh_last"] == "killed"
    assert schedule.report()["refresh_last_at"] != "an hour ago"


def test_a_crash_before_the_record_is_not_reported_as_unchanged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """MINOR-4: an import error exits 1, which is `unchanged` only from a cycle that ran."""
    with caplog.at_level("WARNING", logger="app.adapter.nightly"):
        assert asyncio.run(_child(tmp_path, "import no_such_module").run_once("nightly")) == 1
    assert any(r.getMessage() == "nightly refresh: exit 1 (crashed)" for r in caplog.records)
    schedule = _child(tmp_path, "import no_such_module")
    asyncio.run(schedule.run_once("nightly"))
    assert schedule.report()["refresh_last"] == "crashed"


def test_a_cycle_that_writes_its_own_record_is_reported_from_it(tmp_path: Path) -> None:
    record = tmp_path / "advisor.db.refresh.json"
    code = (f"import json, time; json.dump({{'at': time.time(), 'at_iso': 'now', 'exit_code': 1}}, "
            f"open({str(record)!r}, 'w')); raise SystemExit(1)")
    schedule = _child(tmp_path, code)
    assert asyncio.run(schedule.run_once("nightly")) == 1
    assert schedule.last_failure is None
    assert schedule.report()["refresh_last"] == "unchanged"


def _due(tmp_path: Path, now: D, record_age_hours: float | None) -> list[str]:
    if record_age_hours is not None:
        (tmp_path / "advisor.db.refresh.json").write_text(
            json.dumps({"at": NOW - record_age_hours * 3600, "exit_code": 0})
        )
    ran: list[str] = []
    schedule = nightly.NightlyRefresh(
        db=tmp_path / "advisor.db", command=["unused"], now=lambda: now, wall=lambda: NOW
    )
    schedule.next_run = D(2026, 9, 23, 23, 30)

    async def record_run(trigger: str) -> int:
        ran.append(trigger)
        return 0

    schedule.run_once = record_run  # type: ignore[method-assign]
    asyncio.run(schedule._due())
    return ran


def test_a_night_runs_when_the_last_good_cycle_was_last_night(tmp_path: Path) -> None:
    assert _due(tmp_path, D(2026, 9, 23, 23, 30), record_age_hours=23) == ["nightly"]


def test_a_second_run_in_one_night_is_skipped(tmp_path: Path) -> None:
    """MINOR-2: a catch-up at 23:11 then the nightly run at 00:05 was two cycles in one night."""
    assert _due(tmp_path, D(2026, 9, 23, 23, 30), record_age_hours=0.3) == []


def test_a_daytime_catch_up_does_not_cancel_the_night(tmp_path: Path) -> None:
    """Re-review MINOR-1: a catch-up at 13:00 is ten hours old by 23:30, and the night still runs."""
    assert _due(tmp_path, D(2026, 9, 23, 23, 30), record_age_hours=10) == ["nightly"]


def test_waking_after_the_window_runs_only_on_day_old_data(tmp_path: Path) -> None:
    """MINOR-1: a Mac asleep through the window ran at 08:01 regardless of how fresh the data was."""
    morning = D(2026, 9, 24, 8, 1)
    assert _due(tmp_path, morning, record_age_hours=20) == []
    assert _due(tmp_path, morning, record_age_hours=30) == ["late catch-up"]


def test_a_relative_database_path_is_resolved_before_the_child_gets_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MINOR-5 (mutant M12): `app.sh` passes `advisor.db`, and the child runs in another directory."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("MODEL_RANKING_DB", "advisor.db")
    monkeypatch.setenv(nightly.SWITCH, "nightly")
    schedule = nightly.NightlyRefresh.from_environment(main.RELAXED_ENVS)
    assert schedule is not None
    db_argument = list(schedule.command)[list(schedule.command).index("--db") + 1]
    assert db_argument == str((tmp_path / "advisor.db").resolve())



def test_a_busy_cycle_is_not_a_crash(tmp_path: Path) -> None:
    """Exit 4 writes no record BY DESIGN (another cycle holds the lock, `refresh.py` M1), so the
    missing record must not be read as a crash -- the launchd job overlaps until it is retired."""
    schedule = _child(tmp_path, "raise SystemExit(4)")
    assert asyncio.run(schedule.run_once("nightly")) == 4
    assert schedule.last_failure is None


def test_health_names_each_carried_and_expired_source_with_its_age(tmp_path: Path) -> None:
    """D-156 clause 4: with no screen in the app, `/health` is where a carry shows."""
    (tmp_path / "advisor.db.refresh.json").write_text(json.dumps({
        "at": NOW, "at_iso": "x", "exit_code": 0,
        "carried": {"arena_search": 3.2, "swebench": 0.5},
        "expired": {"arena_vision": 31.0},
    }))
    schedule = nightly.NightlyRefresh(db=tmp_path / "advisor.db", command=["unused"])
    report = schedule.report()
    assert report["refresh_carried"] == "arena_search 3.2d, swebench 0.5d"
    assert report["refresh_expired"] == "arena_vision 31.0d"


def test_health_says_nothing_is_carried_when_nothing_is(tmp_path: Path) -> None:
    (tmp_path / "advisor.db.refresh.json").write_text(json.dumps({"at": NOW, "exit_code": 1}))
    report = nightly.NightlyRefresh(db=tmp_path / "advisor.db", command=["unused"]).report()
    assert report["refresh_carried"] == "" and report["refresh_expired"] == ""
