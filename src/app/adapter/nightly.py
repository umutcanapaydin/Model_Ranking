"""The engine's own nightly refresh (D-149 clauses 2 and 4, D-151, D-154).

Once a night, at a minute picked at random inside 23:00-01:00 local, and once at startup when the
last good cycle is more than a day old, the engine runs `python -m app.workflows.refresh` -- the
existing entry point and nothing else, so the lock, the safe publish and the refusal to publish a
worse candidate stay the one definition of "safe to serve" (D-149 clause 2).

**A child PROCESS, never a thread or a coroutine in this one.** A refresh fetches from the network
and builds a database; a thread doing that shares the interpreter with the server answering the
app, so a hang holds a pool slot, a memory blow-up takes the server down with it, and nothing can
kill a Python thread. A child process can hang, raise or be killed and the server does not notice:
this module only waits on it, asynchronously, and kills it past `TIMEOUT_SECONDS`.

**What that does and does not keep out of the server** (M16-W2 security pass, MAJOR-1). The
refresh, the build and the source fetchers are never imported here, directly or through anything
else, and a test imports the server in a fresh interpreter and checks `sys.modules` to prove it. The
serving process DOES load the source PARSERS and their HTTP client library -- it did before this
wave, through `subscribe -> plans -> ingest` and `rank -> clients.epoch` -- but nothing in it calls
them, so no fetch runs in the server. Untangling that chain is W-125.

**Off unless asked for, and never in production.** `MODEL_RANKING_REFRESH=nightly` turns it on;
`ios/app.sh up` sets it on the owner's Mac. `validate_startup_config` refuses it outside the relaxed
environments, because D-116 keeps ingestion off a serving host and a deployed engine that refreshed
itself would put it there.

What a night did is visible in two places only (D-151's stated cost): the engine log, which carries
the child's own output, and `/health`, which reports the last recorded cycle and the next run.
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import json
import logging
import math
import os
import random
import sys
import time
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

_LOG = logging.getLogger(__name__)

#: The switch, spelled exactly. Unset or `off` is off; anything else is a startup problem.
SWITCH = "MODEL_RANKING_REFRESH"
ON = "nightly"
OFF_VALUES = frozenset({"", "off"})
#: An owner-supplied bundle, passed through as `--epoch-dir`; without it the refresh fetches one
#: itself (`--fetch-epoch`, D-158).
EPOCH_DIR = "MODEL_RANKING_EPOCH_DIR"

#: D-151 clause 1. The window opens at 23:00 local and is two hours wide; the run is spread across
#: it so the upstreams do not see the same minute from every copy of this.
WINDOW_OPENS = dt.time(23, 0)
WINDOW = dt.timedelta(hours=2)
#: D-151 clause 2. A last good cycle older than this is caught up once, at startup.
CATCH_UP_AFTER = dt.timedelta(days=1)
#: A good cycle this recent makes tonight's run a repeat, so it is skipped. Four hours covers a
#: startup catch-up or a restart earlier the same night (at most two hours apart inside the window).
#: It was twelve, and the re-review measured the cost: an engine started at 13:00 on stale data
#: caught up, then skipped that night, so the data reached ~36 hours against D-151's one day.
RECENT = dt.timedelta(hours=4)
#: The catch-up waits this long after boot, so the engine is answering before any refresh starts.
STARTUP_GRACE_SECONDS = 60.0
#: A real cycle takes 6-9 seconds (the launchd log, 2026-09-20..22). Thirty minutes is not a
#: prediction of a slow night, it is the point past which a cycle is stuck rather than slow.
TIMEOUT_SECONDS = 30 * 60.0
#: The longest single sleep. The wall clock is re-read after each one, so a Mac that slept through
#: the window, or a clock that moved, is noticed within a minute rather than trusted blindly.
POLL_SECONDS = 60.0

#: `refresh.py`'s exit codes, restated rather than imported (see the module docstring).
GOOD_CYCLES = frozenset({0, 1})  # published, unchanged
CODE_NAMES = {0: "published", 1: "unchanged", 2: "failed", 3: "refused", 4: "busy"}

_SRC = Path(__file__).resolve().parents[2]
_REPO = _SRC.parent

#: What the child may inherit (security pass, MINOR-4). The refresh reads no environment variable
#: of its own; its HTTP client honours the proxy and certificate settings, and the interpreter needs
#: a locale, a home and a temp directory. Anything else in the owner's shell -- tokens included --
#: stays with the server.
CHILD_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ", "SSL_CERT_FILE",
             "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
             "no_proxy")
#: The child's output kept for the log (security pass, MINOR-1): the tail, never the whole stream.
#: 200 MB of output took the server to 974 MB when it was buffered whole.
OUTPUT_TAIL_BYTES = 64 * 1024


def switch_problem(raw: str | None, environment: str, relaxed: frozenset[str]) -> str | None:
    """Why this switch may not be set as it is, or None. Read by `validate_startup_config`."""
    value = (raw or "").strip().lower()
    if value in OFF_VALUES:
        return None
    if value != ON:
        return (f"{SWITCH}={raw!r} is not a value this engine knows; set {ON!r} to refresh nightly "
                "or leave it unset")
    if environment not in relaxed:
        return (f"{SWITCH}={ON} outside a development environment: D-116 keeps ingestion off a "
                "serving host, and this would make the serving process start it every night")
    return None


def enabled() -> bool:
    return os.environ.get(SWITCH, "").strip().lower() == ON


def window_around(moment: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
    """The window that contains `moment`, or else the next one to open. Naive local time."""
    opens = dt.datetime.combine(moment.date(), WINDOW_OPENS)
    if moment < opens + WINDOW - dt.timedelta(days=1):
        opens -= dt.timedelta(days=1)  # just after midnight: tonight's window opened yesterday
    return opens, opens + WINDOW


def pick_run_time(after: dt.datetime, rng: random.Random) -> dt.datetime:
    """A moment inside the first window that is still open at `after`, never before `after`."""
    opens, closes = window_around(after)
    start = max(opens, after)
    return start + (closes - start) * rng.random()


def read_record(db: Path) -> dict[str, object] | None:
    """The refresh's own record of its last cycle (REQ-REF-004), or None if there is none."""
    path = db.with_name(db.name + ".refresh.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def needs_catch_up(record: dict[str, object] | None, now: float) -> bool:
    """D-151 clause 2: no good cycle on record within a day. One catch-up; the caller never loops.

    Only the LAST cycle is on record, so a last cycle that failed or was refused counts as no good
    cycle at all -- the one catch-up then is the cheapest way to find out whether it still does.
    """
    if record is None:
        return True
    at, code = record.get("at"), record.get("exit_code")
    if not isinstance(at, int | float) or not math.isfinite(at) or code not in GOOD_CYCLES:
        return True
    return now - at > CATCH_UP_AFTER.total_seconds()


async def read_tail(stream: asyncio.StreamReader, tail: bytearray) -> None:
    """Read `stream` to its end, keeping only its last `OUTPUT_TAIL_BYTES` in `tail`."""
    while chunk := await stream.read(65536):
        tail.extend(chunk)
        del tail[:-OUTPUT_TAIL_BYTES]


def recently_good(record: dict[str, object] | None, now: float) -> bool:
    """A good cycle on record within `RECENT`: tonight's run would repeat it (M16-W2 review MINOR-2,
    a startup catch-up at 23:11 followed by the nightly run at 00:05)."""
    if record is None or needs_catch_up(record, now):
        return False
    at = record["at"]
    return isinstance(at, int | float) and now - at < RECENT.total_seconds()


def _drifted(lines: object) -> str:
    """The source names in the refresh record's drift lines, each `<source>: <reason>`."""
    if not isinstance(lines, list):
        return ""
    return ", ".join(sorted({str(line).split(":", 1)[0] for line in lines}))


def _aged(sources: object, now: dt.datetime | None = None) -> str:
    """`{"arena": "<stamp>"}` as `arena 3.2d`, sorted, the age computed NOW from the stamp the
    refresh recorded -- so the line is true on every night, not only the night it was written
    (review MAJOR-2). A bare number is a legacy age; anything unreadable is `?d`."""
    if not isinstance(sources, dict):
        return ""
    now = now or dt.datetime.now(tz=dt.UTC)
    parts = []
    for name, value in sorted(sources.items()):
        age: float | None = float(value) if isinstance(value, int | float) else None
        if isinstance(value, str):
            with contextlib.suppress(ValueError):
                then = dt.datetime.fromisoformat(value)
                then = then if then.tzinfo else then.replace(tzinfo=dt.UTC)
                age = (now - then).total_seconds() / 86400
        if age is not None and age < 0:
            age = None  # a clock that stepped back; not an age (re-review MINOR-1)
        parts.append(f"{name} {age:.1f}d" if age is not None else f"{name} ?d")
    return ", ".join(parts)


def refresh_command(db: Path, epoch_dir: str | None) -> list[str]:
    # `-P`: no working directory on the module path, so a stray `app/` beside the repository cannot
    # stand in for the refresh (security pass, NIT-1). `app` is found through PYTHONPATH only.
    command = [sys.executable, "-B", "-P", "-m", "app.workflows.refresh", "--db", str(db)]
    # D-158: the owner's own bundle wins; without one, the refresh fetches Epoch itself.
    command += ["--epoch-dir", epoch_dir] if epoch_dir else ["--fetch-epoch"]
    return command


@dataclass
class NightlyRefresh:
    """The schedule and the child it starts. Everything it touches from outside is injectable."""

    db: Path
    command: Sequence[str]
    now: Callable[[], dt.datetime] = dt.datetime.now
    wall: Callable[[], float] = time.time
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
    rng: random.Random = field(default_factory=random.Random)
    timeout: float = TIMEOUT_SECONDS
    grace: float = STARTUP_GRACE_SECONDS
    #: What `/health` reports. Written only by this object, on the event loop.
    next_run: dt.datetime | None = None
    running_since: float | None = None
    last_trigger: str | None = None
    #: `(when, what)` for a cycle that left NO record of its own: killed at the timeout, unable to
    #: start, or crashed before `refresh.py` could write one (M16-W2 review MAJOR-1). Without it
    #: `/health` kept reporting the previous cycle's "published" after a night that failed.
    last_failure: tuple[float, str] | None = None

    @classmethod
    def from_environment(cls, relaxed: frozenset[str]) -> NightlyRefresh | None:
        """The schedule the environment asks for, or None. The switch is checked AGAIN here, at the
        moment the schedule starts, rather than trusted from the import-time check (security pass,
        MINOR-2: the environment can change between the two)."""
        raw = os.environ.get("MODEL_RANKING_DB", "").strip()
        if not enabled() or not raw:
            return None
        environment = os.environ.get("APP_ENV", "").strip().lower()
        problem = switch_problem(os.environ.get(SWITCH), environment, relaxed)
        if problem:
            _LOG.error("nightly refresh: not started: %s", problem)
            return None
        db = Path(raw).resolve()
        return cls(db=db, command=refresh_command(db, os.environ.get(EPOCH_DIR, "").strip()))

    async def run_once(self, trigger: str) -> int | None:
        """One cycle in a child process. Returns its exit code, or None if it had to be killed or
        could not start. Never raises except on cancellation, which kills the child first."""
        started = self.wall()
        self.last_trigger, self.running_since = trigger, started
        _LOG.warning("nightly refresh: starting (%s): %s", trigger, " ".join(self.command))
        proc: asyncio.subprocess.Process | None = None
        try:
            env = {name: os.environ[name] for name in CHILD_ENV if name in os.environ}
            env["PYTHONPATH"] = str(_SRC)
            proc = await asyncio.create_subprocess_exec(
                *self.command, cwd=_REPO, env=env, stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            )
            tail = bytearray()

            async def drain() -> None:
                assert proc is not None and proc.stdout is not None
                await read_tail(proc.stdout, tail)
                await proc.wait()

            try:
                await asyncio.wait_for(drain(), timeout=self.timeout)
            except TimeoutError:
                self._log_tail(tail)
                self._failed(started, "killed")
                _LOG.error("nightly refresh: no exit after %.0fs; killing it. The live artifact "
                           "is whatever the last safe publish left (REQ-REF-001)", self.timeout)
                return None
            self._log_tail(tail)
            code = proc.returncode
            name = CODE_NAMES.get(code, "?") if code is not None else "?"
            record = read_record(self.db)
            recorded_at = record.get("at") if record else None
            wrote = isinstance(recorded_at, int | float) and recorded_at >= started
            if not wrote and code != 4:  # a busy cycle writes nothing, by design (refresh.py M1)
                # Exit 1 is "unchanged" only from a cycle that ran; an import error exits 1 too.
                name = "crashed"
                self._failed(started, "crashed")
            _LOG.warning("nightly refresh: exit %s (%s)", code, name)
            return code
        except (OSError, ValueError) as exc:
            self._failed(started, "not started")
            _LOG.error("nightly refresh: could not start the cycle: %s", exc)
            return None
        finally:
            if proc is not None and proc.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    proc.kill()
                with contextlib.suppress(Exception):
                    await asyncio.shield(proc.wait())
            self.running_since = None

    def _failed(self, started: float, what: str) -> None:
        self.last_failure = (started, what)

    @staticmethod
    def _log_tail(tail: bytearray) -> None:
        for line in tail.decode("utf-8", "replace").splitlines()[-20:]:
            _LOG.warning("nightly refresh | %s", line)

    async def _due(self) -> None:
        """Tonight's run, or the decision not to make it."""
        record = read_record(self.db)
        closes = window_around(self.next_run or self.now())[1]
        if self.now() >= closes:
            # Woken after the window (M16-W2 review MINOR-1: a Mac asleep through it ran at 08:01).
            # D-151 puts the run in the window; the one exception is data a day old, which is
            # clause 2's catch-up rule applied on waking rather than on starting.
            if needs_catch_up(record, self.wall()):
                await self.run_once("late catch-up")
            else:
                _LOG.warning("nightly refresh: the window passed while asleep; the data is under "
                             "a day old, so tonight's run is skipped")
        elif recently_good(record, self.wall()):
            _LOG.warning("nightly refresh: a good cycle ran within %s; skipping tonight's", RECENT)
        else:
            await self.run_once("nightly")

    async def _sleep_until(self, moment: dt.datetime) -> None:
        while (remaining := (moment - self.now()).total_seconds()) > 0:
            await self.sleep(min(remaining, POLL_SECONDS))

    async def serve(self) -> None:
        """The whole schedule. Runs until cancelled; nothing a cycle does can end it."""
        try:
            if needs_catch_up(read_record(self.db), self.wall()):
                await self.sleep(self.grace)
                await self.run_once("catch-up")
        except Exception:
            _LOG.exception("nightly refresh: the startup catch-up failed; the schedule continues")
        after = self.now()
        while True:
            try:
                self.next_run = pick_run_time(after, self.rng)
                await self._sleep_until(self.next_run)
                await self._due()
                after = window_around(self.next_run)[1]
            except Exception:
                # A bug in the schedule must not end it, and must not spin either.
                _LOG.exception("nightly refresh: the schedule hit an error; retrying in a minute")
                await self.sleep(POLL_SECONDS)
                after = max(after, self.now())

    def report(self) -> dict[str, str]:
        """The `/health` fields. Strings only, like the rest of that body."""
        record = read_record(self.db)
        code = record.get("exit_code") if record else None
        last = CODE_NAMES.get(code, "unknown") if isinstance(code, int) else "none"
        last_at = str(record.get("at_iso", "")) if record else ""
        recorded_at = record.get("at") if record else None
        if self.last_failure is not None and (
            not isinstance(recorded_at, int | float) or recorded_at < self.last_failure[0]
        ):
            # The newest cycle left no record, so the record's outcome is not the last one.
            at, last = self.last_failure
            last_at = dt.datetime.fromtimestamp(at, dt.UTC).isoformat()
        return {
            "refresh": "running" if self.running_since is not None else "scheduled",
            "refresh_next": self.next_run.isoformat(timespec="minutes") if self.next_run else "",
            "refresh_last": last,
            "refresh_last_at": last_at,
            # D-156 clause 4: a source serving its last good data because it failed, and one whose
            # data aged out and dropped. The app shows neither (D-151); this is where they show.
            "refresh_carried": _aged(record.get("carried") if record else None),
            "refresh_expired": _aged(record.get("expired") if record else None),
            # M16-W4: a board whose layout changed in a bundle that arrived, by source name.
            "refresh_drift": _drifted(record.get("drift") if record else None),
        }
