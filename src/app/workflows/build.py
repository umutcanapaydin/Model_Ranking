"""Build the evidence database end to end (REQ-ING-012, REQ-ING-013).

**What this replaces, because the replacement is the point.** Until M7 this pipeline existed only
as a ~30-line heredoc inside `.github/workflows/contract-tests.yml`. It was not in `src/`, so
`ruff`, `mypy --strict`, `pytest` and coverage had never seen it; it wrote to a throwaway
`ci_advisor.db`; and it ran on a Monday cron that had never fired. **The product's data production
path was untested, ungoverned, unrun code embedded in CI configuration** — which is why
`advisor.db` sat on the pre-M5 schema (W-023): nothing rebuilt it.

**The failure this module is built to make impossible.** `rank.py` JOINs `px_median`. An empty
`px_median` yields zero rows, `recommend()` returns None, and `/v1` answers 200 with zero picks —
a confident wrong answer. A builder that "succeeds" while leaving any stage empty produces exactly
that artifact. So every stage here is checked against a floor and the whole run fails loud, and the
final act is to read the counts back OUT of the file rather than trust what the writers reported
(the M6 lesson: *configured is not working, and neither is measured-once*).

**A build is NOT reproducible across time, and that is correct.** Four of five sources are live
feeds, so two builds a day apart legitimately differ: at M7's Stage-4.0 round a rebuild moved four
models' price medians (deepseek, kimi, glm — models whose vendors move prices) while the model set
and every other median stayed identical. Comparing two artifacts and finding drift is therefore not
evidence of a code defect. What IS reproducible, and what W2's parity proof rests on, is
same-inputs-same-output: the streamed fetch was verified to return byte-identical text to the
unbounded one, parsing to identical rows.

**Exit codes** mirror `schema.py`'s frozen D-120 contract, deliberately, so an operator learns one
convention rather than two:

    0  built and servable
    2  build failed; the target is not usable
    3  built but NOT servable, with ``required_operator_actions`` naming what is missing

Sources are injected rather than constructed inside the build so that tests drive **this** entry
point with fakes instead of a parallel implementation (V4C-50: every load-bearing path needs at
least one test through the real entry point). The defaults are the real clients.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.clients.arena_slices import ARENA_SLICES, ArenaSlice, fetch_slices
from app.clients.epoch_board import EpochBoard, parse_board
from app.clients.protocols import SourceError
from app.workflows.epoch import committed_last_verified
from app.workflows.ingest import RunContext, SourceReport, _store_scores
from app.workflows.plans import ingest_plans
from app.workflows.rank import build_price_medians
from app.workflows.registry import (
    PlanReconcileReport,
    ReconcileReport,
    reconcile,
    reconcile_plans,
)
from app.workflows.rosters import ingest_rosters
from app.workflows.schema import connect, open_readonly, reset_source
from app.workflows.sources import (
    ARENA_SLICE_CLIENT,
    EPOCH_BOARD_CLIENT,
    EPOCH_BOARDS,
    LOCAL_BUNDLES,
    REMOTE_SOURCES,
    LocalBundle,
    RemoteSource,
)

MINIMUM_MODELS_REGISTERED = 20
"""Below this the registry has drifted and the artifact is not servable.

Inherited from the CI heredoc's own assertion rather than invented here; it is the one floor this
pipeline has ever had, and it caught nothing because the step never ran.
"""


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
"""What a table name may look like before this module will interpolate it into SQL."""


class BuildError(RuntimeError):
    """A stage produced an unusable result. Carries the operator-facing sentence."""


@dataclass
class BuildReport:
    """What the build actually produced, read back from the artifact where possible."""

    sources: list[SourceReport] = field(default_factory=list)
    plans_stored: int = 0
    rosters_stored: int = 0
    reconciled: ReconcileReport | None = None
    plans_reconciled: PlanReconcileReport | None = None
    price_models: int = 0
    verified: dict[str, int] = field(default_factory=dict)
    required_operator_actions: list[str] = field(default_factory=list)
    #: D-156. Sources that failed this cycle and serve their last good data instead, with its age in
    #: days, and sources whose last good data was too old to carry (their lists drop).
    carried: dict[str, float] = field(default_factory=dict)
    #: `None` when the age could not be read at all -- still expired, never carried.
    expired: dict[str, float | None] = field(default_factory=dict)
    since: dict[str, str | None] = field(default_factory=dict)
    #: M16-W4: declared boards missing or reshaped in a bundle that DID arrive, carried or not. A
    #: changed layout otherwise looks exactly like a quiet night.
    drift: list[str] = field(default_factory=list)
    #: D-157 clause 4: the models the registry derived from the data, and the names with the most
    #: rows that nothing matched -- the curation that remains, made visible.
    derived: list[str] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)

    def sources_json(self) -> dict[str, object]:
        """What the refresh needs from this build, and nothing it would have to re-derive (review
        MINOR-1: the refresh used to infer these from row stamps, with different arithmetic)."""
        return {
            "arrived": sorted({r.source for r in self.sources}),
            "carried": self.carried,
            "expired": self.expired,
            "since": self.since,
            "drift": self.drift,
            "derived": self.derived,
            "unmatched": self.unmatched,
        }

    def as_json(self) -> dict[str, object]:
        return {
            "sources": [
                {
                    "source": r.source,
                    "stored": r.stored,
                    "skipped": r.skipped,
                    "health": r.health,
                    "effort_unknown": r.effort_unknown,
                }
                for r in self.sources
            ],
            "plans_stored": self.plans_stored,
            "rosters_stored": self.rosters_stored,
            "models_registered": self.reconciled.models_registered if self.reconciled else 0,
            "plans_matched": self.plans_reconciled.matched if self.plans_reconciled else 0,
            "price_models": self.price_models,
            "verified_from_artifact": self.verified,
            "required_operator_actions": self.required_operator_actions,
            "carried": self.carried,
            "expired": self.expired,
            "drift": self.drift,
            "derived": self.derived,
            "unmatched": self.unmatched,
        }


def _read_back(conn: sqlite3.Connection) -> dict[str, int]:
    """Count what is IN the file, not what the writers said they wrote (Trap 3).

    The table list is derived from the artifact rather than typed here, so a table added to the
    schema starts being verified without this function being edited.
    """
    names = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            " ORDER BY name"
        )
    ]
    counts: dict[str, int] = {}
    for name in names:
        # The identifier comes from sqlite_master rather than from a caller, but a comment saying
        # so is not a control. SQLite cannot bind an identifier, so the name is CHECKED before it
        # is interpolated and an unexpected shape stops the build instead of being quoted and run.
        if not _IDENTIFIER.fullmatch(name):
            msg = f"refusing to count a table with an unexpected name: {name!r}"
            raise BuildError(msg)
        counts[name] = int(conn.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0])  # noqa: S608
    return counts


def _ingest_curated(
    label: str, ingest: Callable[[], SourceReport]
) -> int:
    """Run one curated-YAML stage, giving every failure the same operator-facing shape.

    `ingest_plans` and `ingest_rosters` raise SourceError on a malformed or empty document, while
    a well-formed document holding nothing returns a report with `stored == 0`. Both are the same
    thing to an operator — the artifact will not serve — so both leave here as a BuildError rather
    than as two error types a caller has to know about.
    """
    try:
        result = ingest()
    except SourceError as exc:
        msg = f"{label} ingest failed: {exc}"
        raise BuildError(msg) from exc
    if result.stored <= 0:
        msg = f"{label} ingest stored nothing; a printed zero is not a pass"
        raise BuildError(msg)
    return result.stored



#: D-144 as ruled by the owner, D-156. "If the data is about a month old, the list drops."
CARRY_MAX_AGE = dt.timedelta(days=30)


@dataclass
class Carry:
    """What a failed source may fall back to: the live artifact's rows, if they are young enough.

    `last_ok` is the refresh's per-source record of when each source last ARRIVED in a cycle whose
    content is what the live artifact serves. It is the age that matters: an unchanged cycle
    publishes nothing, so a row's `observed_at` can be far older than the fetch that confirmed it.
    Without a record for a source, the live rows' newest `observed_at` stands in. It can overstate
    the age; it understates it only for rows stamped ahead of now by less than the carry limit,
    read as age 0 (a clock that stepped back; M16-W3 re-reviews).
    """

    live: Path
    last_ok: Mapping[str, str]
    now: dt.datetime
    carried: dict[str, float] = field(default_factory=dict)
    expired: dict[str, float | None] = field(default_factory=dict)
    #: The stamp each carried or expired source's age was measured from -- what the refresh records,
    #: so `/health` can say how old the SERVED data is on any later night (M16-W3 review MAJOR-2).
    since: dict[str, str | None] = field(default_factory=dict)

    def _age(self, stamp: str | None, *, clamp: bool = False) -> float | None:
        try:
            then = dt.datetime.fromisoformat(stamp or "")
        except ValueError:
            return None
        if then.tzinfo is None:
            then = then.replace(tzinfo=dt.UTC)
        age = (self.now - then).total_seconds() / 86400
        # A stamp from the future (a clock that stepped back) is not an age at all; carrying on it
        # would carry forever (M16-W3 review MINOR-2). Unless `clamp`: see `age_days`.
        if age < 0:
            # Only a bounded step back reads as young. Further ahead is not an error the ruling
            # can absorb: it would carry until real time reached the stamp, and 30 days more
            # (third review MINOR-2).
            return 0.0 if clamp and -age < CARRY_MAX_AGE.total_seconds() / 86400 else None
        return age

    def age_days(self, live: sqlite3.Connection, source: str) -> tuple[float | None, str | None]:
        """(age in days, the stamp it was measured from). The refresh's arrival record first; the
        live rows' own newest `observed_at` when there is none, or when it is unusable."""
        stamp = self.last_ok.get(source)
        age = self._age(stamp)
        if age is None:
            newest = [live.execute(f"SELECT MAX(observed_at) FROM {t} WHERE source = ?",  # noqa: S608
                                   (source,)).fetchone()[0] for t in ("scores", "pricing")]
            stamp = max((x for x in newest if x), default=None)
            # The rows are the last word. If they are ahead of now too, the clock stepped back and
            # the data is as young as it gets: carry at age 0 rather than expire (re-review
            # MINOR-1) -- within the carry limit; further ahead expires.
            age = self._age(stamp, clamp=True)
        return age, stamp

    def restore(self, conn: sqlite3.Connection, source: str) -> str:
        """Copy `source`'s rows from the live artifact. Returns "carried", "expired" or "absent"."""
        try:
            # INV-23: never a hand-built `file:...?mode=ro`, which a path carrying `?` or `#` turns
            # into a WRITABLE connection -- against the artifact the reader is serving.
            live = open_readonly(self.live)
        except sqlite3.Error:
            return "absent"
        try:
            copied = 0
            rows_by_table = {}
            for table in ("scores", "pricing"):
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
                live_cols = {r[1] for r in live.execute(f"PRAGMA table_info({table})")}
                shared = [c for c in cols if c in live_cols]
                select = ", ".join("NULL" if c == "model_id" else c for c in shared)
                rows_by_table[table] = (shared, live.execute(
                    f"SELECT {select} FROM {table} WHERE source = ?", (source,)).fetchall())  # noqa: S608
                copied += len(rows_by_table[table][1])
            if not copied:
                return "absent"
            age, stamp = self.age_days(live, source)
        except sqlite3.Error:
            return "absent"
        finally:
            live.close()
        self.since[source] = stamp
        if age is None or age > CARRY_MAX_AGE.total_seconds() / 86400:
            # `None`, not infinity: the report is printed with `json.dumps`, which would write the
            # non-JSON token `Infinity` and break the refresh that reads it.
            self.expired[source] = round(age, 1) if age is not None else None
            return "expired"
        try:
            with conn:
                for table, (shared, rows) in rows_by_table.items():
                    if rows:
                        conn.executemany(
                            f"INSERT INTO {table} ({', '.join(shared)}) "  # noqa: S608
                            f"VALUES ({', '.join('?' * len(shared))})", rows)
        except sqlite3.Error:
            # A schema the carried rows no longer fit (review NIT-3) degrades to "nothing carried",
            # never to a failed build. The re-reset is not redundant: the rollback also undoes a
            # reset still pending in the same transaction.
            for table in ("pricing", "scores"):
                reset_source(conn, table, source)
            self.since.pop(source, None)
            return "absent"
        # The carry is REPORTED rather than silent: a surface serving month-old data looks exactly
        # like a healthy one from outside, which is what the refresh record and /health are for.
        self.carried[source] = round(age, 1)
        return "carried"


def _fall_back(conn: sqlite3.Connection, carry: Carry | None, source: str) -> str:
    """After a failed source's rows are reset: carry its last good data if the ruling allows."""
    return carry.restore(conn, source) if carry is not None else "absent"


#: How many unmatched names the report carries: the top of the curation queue, not all of it.
UNMATCHED_LISTED = 20
#: And how long each may be. They are upstream text on their way to `/health`; one was measured at
#: 100 kB, which made a 5 MB response (M16 Stage 4.0 security review, MINOR-1).
UNMATCHED_NAME_CHARS = 80


def _most_unmatched(conn: sqlite3.Connection, refused: set[str]) -> list[str]:
    """The score names nothing matched, most rows first. A modality refusal is the guard working,
    not a model we are missing, so it is left out (M14-W1 review MAJOR-2's distinction)."""
    # A category slice repeats its `overall` board's names, up to 26 times, and adds none it lacks
    # (measured 2026-09-24); counted, they would rank Arena names above every other source's (wave
    # review K2). So the queue counts every source except the declared slices.
    slices = [board.source_name for board in ARENA_SLICES]
    rows = conn.execute(
        "SELECT raw_name, COUNT(*) AS n FROM scores WHERE model_id IS NULL "  # noqa: S608
        f"AND source NOT IN ({','.join('?' * len(slices))}) "
        "GROUP BY raw_name ORDER BY n DESC, raw_name", slices).fetchall()
    return [name[:UNMATCHED_NAME_CHARS] for name, _ in rows if name not in refused][:UNMATCHED_LISTED]


def _surfaces_left_without_evidence(missing: Sequence[str]) -> list[str]:
    """Translate failed optional sources into the SURFACES a user would notice.

    "arena is unreachable" is an operations sentence. "the assistant surface has no evidence" is
    the one that decides whether this artifact may be deployed, and it is derived from CATEGORIES
    rather than typed here, so a category that changes its primary source starts reporting
    correctly without this function being edited.
    """
    from app.workflows.categories import CATEGORIES

    actions: list[str] = []
    for entry in missing:
        source = entry.split(":", 1)[0]
        blinded = sorted(
            task for task, spec in CATEGORIES.items() if spec.primary_source == source
        )
        if blinded:
            actions.append(
                f"{source} is unavailable, so these surfaces have NO primary evidence and must "
                f"disclose it rather than answer: {', '.join(blinded)} ({entry})"
            )
        else:
            actions.append(f"{source} is unavailable (no surface names it as primary): {entry}")
    return actions


def _board_failed(
    conn: sqlite3.Connection, carry: Carry | None, source: str, why: str,
    drift: list[str] | None, missing: list[str],
) -> None:
    """One board rejected (an Epoch board or a slice): its rows go, the drift is recorded, and its
    last good data comes back if young enough (D-156); otherwise it is missing."""
    for table in ("pricing", "scores"):
        reset_source(conn, table, source)
    if drift is not None:
        drift.append(f"{source}: {why}")
    if _fall_back(conn, carry, source) != "carried":
        missing.append(f"{source}: {why}")


def _ingest_boards(
    conn: sqlite3.Connection,
    bundle_dir: Path | None,
    run: RunContext,
    boards: Sequence[EpochBoard] | None = None,
    carry: Carry | None = None,
    drift: list[str] | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Read the declared Epoch boards (D-127). Same bundle, same read-only rules as `_ingest_bundles`.

    Separate from `_ingest_bundles` because these are DATA-declared boards sharing one reader, while
    the two bundles above are distinct clients with their own parsers. Merging them would mean the
    board table pretending to be a client list, which is what the registry exists to stop.
    """
    boards = EPOCH_BOARDS if boards is None else boards
    if bundle_dir is None:
        return [], [f"{b.source_name}: no local bundle directory supplied" for b in boards
                    if _fall_back(conn, carry, b.source_name) != "carried"]

    results: list[SourceReport] = []
    missing: list[str] = []
    last_verified = committed_last_verified()
    for board in boards:
        try:
            client = EPOCH_BOARD_CLIENT(bundle_dir, board, last_verified=last_verified)
            rows, skipped = parse_board(client.fetch_raw(), board)
            if not rows:
                msg = f"parsed 0 rows from {board.file}"
                raise SourceError(msg)
            stored = _store_scores(conn, board.source_name, rows, run)
        except (SourceError, OSError) as exc:
            _board_failed(conn, carry, board.source_name, str(exc), drift, missing)
            continue
        report = SourceReport(
            source=board.source_name,
            stored=len(rows),
            skipped=skipped,
            effort_unknown=stored,
        )
        # Boards were the ONE source kind that never reached `run.reports`; every `ingest_*` in
        # `ingest.py` appends. Harmless while nothing in production reads that field, and exactly
        # the kind of inconsistency that becomes a bug the day something does.
        run.reports.append(report)
        results.append(report)
    return results, missing


def _ingest_slices(
    conn: sqlite3.Connection,
    run: RunContext,
    slices: Sequence[ArenaSlice],
    carry: Carry | None = None,
    drift: list[str] | None = None,
    *,
    client: Callable[[str], Any] | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Arena's category slices (M17-W2, #22): one download per config, one board per slice.

    The Epoch boards' shape, with one difference that decides the failure rules. A config's slices
    all come out of ONE file, so a failed download fails every slice of that config, and each then
    carries on its own clock (D-156). A file that downloads but holds too few rows for one slice
    fails that slice alone. A slice is optional, like every board of this dataset (D-121, D-144):
    it never fails the build, and no surface names it, so a failure is an operator line only.
    """
    client_type = ARENA_SLICE_CLIENT if client is None else client
    results: list[SourceReport] = []
    missing: list[str] = []
    for config in dict.fromkeys(board.config for board in slices):
        boards = [board for board in slices if board.config == config]
        try:
            rows, refused = fetch_slices(config, boards, client=client_type)
        except SourceError as exc:
            for board in boards:
                _board_failed(conn, carry, board.source_name, str(exc), drift, missing)
            continue
        for board in boards:
            parsed = rows[board.source_name]
            try:
                if len(parsed) < board.minimum_rows:
                    msg = (f"parsed {len(parsed)} rows, below its floor of {board.minimum_rows}; "
                           "the file answered but this slice's shape has changed")
                    raise SourceError(msg)
                stored = _store_scores(conn, board.source_name, parsed, run)
            except SourceError as exc:
                _board_failed(conn, carry, board.source_name, str(exc), drift, missing)
                continue
            report = SourceReport(
                source=board.source_name,
                stored=len(parsed),
                skipped=refused[board.source_name],
                effort_unknown=stored,
            )
            run.reports.append(report)
            results.append(report)
    return results, missing


def _ingest_bundles(
    conn: sqlite3.Connection,
    bundle_dir: Path | None,
    run: RunContext,
    bundles: Sequence[LocalBundle] | None = None,
    carry: Carry | None = None,
    drift: list[str] | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Read the bundle, never fetch it: the refresh fetches (D-158), or the owner supplies one.

    Absence is a REPORTED degradation rather than a skipped step. That distinction is the whole
    reason this function exists: the pipeline this module replaced ingested five remote sources and
    no bundle at all, so `agentic-coding` answered every query with an empty list while the
    contract said both coding surfaces were presented equally.
    """
    # Read at CALL time. Binding LOCAL_BUNDLES as a default here would repeat, inside the very
    # wave that fixed it in build(), the defect this milestone is about: a default argument is
    # bound at definition time, so the injection point silently ignores the module attribute.
    bundles = LOCAL_BUNDLES if bundles is None else bundles
    if bundle_dir is None:
        return [], [f"{b.name}: no local bundle directory supplied" for b in bundles
                    if _fall_back(conn, carry, b.name) != "carried"]

    results: list[SourceReport] = []
    missing: list[str] = []
    last_verified = committed_last_verified()
    for bundle in bundles:
        try:
            client = bundle.client_type(bundle_dir, last_verified=last_verified)
            result = bundle.ingest(conn, client, run)
            if result.stored <= 0:
                msg = f"stored 0 rows from {bundle_dir}"
                raise SourceError(msg)
        except (SourceError, OSError) as exc:
            # Same rollback as a rejected remote source (MINOR-1), and the reason applies harder
            # here: `epoch_deepswe_external` is the sole primary evidence for `agentic-coding`, so
            # a partial bundle left in place would make that surface answer from fragments while
            # the build reports it as having none.
            for table in ("pricing", "scores"):
                reset_source(conn, table, bundle.name)
            if drift is not None:
                drift.append(f"{bundle.name}: {exc}")
            if _fall_back(conn, carry, bundle.name) != "carried":
                missing.append(f"{bundle.name}: {exc}")
            continue
        results.append(result)
    return results, missing


def _ingest_sources(
    conn: sqlite3.Connection, sources: Sequence[RemoteSource], run: RunContext,
    carry: Carry | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Ingest every declared source, failing loud on an unusable or hollow one.

    A source that fetches, parses and stores nothing is the failure this checks for. It passes a
    status check and a parser, and it produces an artifact that answers questions with silence.
    """
    if not sources:
        msg = "no evidence sources configured; the build would produce an empty artifact"
        raise BuildError(msg)

    results: list[SourceReport] = []
    missing: list[str] = []
    for source in sources:
        try:
            result = source.ingest(conn, source.client(), run)
            if result.stored < source.minimum_rows:
                msg = (
                    f"{source.name}: stored {result.stored} rows, below its floor of "
                    f"{source.minimum_rows} — the feed answered but its shape has changed"
                )
                raise BuildError(msg)
        except (SourceError, BuildError) as exc:
            # A source we REJECT must leave nothing behind. `ingest` has already written by the
            # time the floor is evaluated, and for an optional source the error is swallowed — so
            # without this the partial rows were committed anyway. The artifact would hold, say,
            # three arena rows while the build reported arena as unavailable, and at serving time
            # the "no evidence source is present" branch would NOT fire, because the source IS
            # present: the surface would answer confidently from truncated evidence, defeating the
            # exact disclosure D-121 stakes itself on. (Security review MINOR-1.)
            #
            # A SAVEPOINT cannot do this job: every `ingest_*` commits internally via `with conn:`,
            # which ends the transaction and discards outstanding savepoints. `reset_source` is
            # the mechanism this project already uses to replace a source's working set, so the
            # rollback is expressed in the same terms as the write.
            for table in ("pricing", "scores"):
                reset_source(conn, table, source.name)
            # D-156: every source carries forward its last good data for up to CARRY_MAX_AGE, the
            # required ones included (ruled 2026-09-23). Only when there is nothing young enough to
            # carry does the old rule apply: a required source fails the build.
            fallback = _fall_back(conn, carry, source.name)
            if fallback == "carried":
                continue
            if source.required:
                why = (f"its last good data is older than {CARRY_MAX_AGE.days} days (expired)"
                       if fallback == "expired" else "")
                msg = f"{source.name}: dependency unusable: {exc}" + (f"; {why}" if why else "")
                raise BuildError(msg) from exc
            # An OPTIONAL source that fails does not stop the build, and it does not disappear
            # either. It is named here, surfaces as exit 3, and the categories it was the sole
            # evidence for will disclose that they have none.
            missing.append(f"{source.name}: {exc}" + (
                f" (last good data expired: older than {CARRY_MAX_AGE.days} days)"
                if fallback == "expired" else ""))
            continue
        results.append(result)
    return results, missing


def build(
    conn: sqlite3.Connection,
    *,
    plans_yaml: str,
    rosters_yaml: str,
    sources: Sequence[RemoteSource] | None = None,
    bundle_dir: Path | None = None,
    bundles: Sequence[LocalBundle] | None = None,
    boards: Sequence[EpochBoard] | None = None,
    slices: Sequence[ArenaSlice] | None = None,
    run: RunContext | None = None,
    minimum_models: int | None = None,
    carry_from: Path | None = None,
    last_ok: Mapping[str, str] | None = None,
    now: dt.datetime | None = None,
) -> BuildReport:
    """Run every stage, failing loud on any empty result (REQ-ING-013).

    Raises BuildError with an operator-facing sentence. Never returns a report describing a
    partially-built database as a success.
    """
    # Read at CALL time, never bound as a default argument. A default binds at definition time, so
    # `sources=REMOTE_SOURCES` in the signature would make the module attribute unpatchable — and
    # the first version of this function did exactly that: a test that believed it was injecting
    # fakes reached the real network instead, and only a live upstream outage revealed it. An
    # injection point that cannot actually be injected is this project's most-repeated defect.
    # Third instance, M8: `_ingest_boards` took a `boards` parameter and read it at call time --
    # correctly -- while `build()` exposed no way to pass one, so eight tests that believed they
    # controlled the source set silently ran the real board list against a bundle directory that
    # did not exist. A seam is only a seam if it reaches the caller.
    sources = REMOTE_SOURCES if sources is None else sources
    slices = ARENA_SLICES if slices is None else slices
    minimum_models = MINIMUM_MODELS_REGISTERED if minimum_models is None else minimum_models
    run = run or RunContext()
    report = BuildReport()

    report.plans_stored = _ingest_curated(
        "plan", lambda: ingest_plans(conn, plans_yaml, run)
    )
    report.rosters_stored = _ingest_curated(
        "roster", lambda: ingest_rosters(conn, rosters_yaml, run)
    )
    # D-156: with a live artifact to fall back on, a failed source serves its last good data.
    carry = (Carry(live=carry_from, last_ok=last_ok or {}, now=now or dt.datetime.now(tz=dt.UTC))
             if carry_from is not None and Path(carry_from).is_file() else None)
    if carry is not None:
        report.carried, report.expired = carry.carried, carry.expired
        report.since = carry.since
    try:
        report.sources, degraded = _ingest_sources(conn, sources, run, carry)
    except BuildError as exc:
        # The refresh records what expired even when a REQUIRED source's expiry fails the build
        # (review MAJOR-2): the build is the one place that knows, so it says so on the way out.
        exc.report = report  # type: ignore[attr-defined]
        raise
    bundle_reports, bundle_missing = _ingest_bundles(conn, bundle_dir, run, bundles, carry,
                                                    drift=report.drift)
    board_reports, board_missing = _ingest_boards(conn, bundle_dir, run, boards, carry,
                                                  drift=report.drift)
    slice_reports, slice_missing = _ingest_slices(conn, run, slices, carry, drift=report.drift)
    report.sources.extend(board_reports)
    report.sources.extend(bundle_reports)
    report.sources.extend(slice_reports)
    report.required_operator_actions = _surfaces_left_without_evidence(
        [*degraded, *bundle_missing, *board_missing, *slice_missing]
    )

    reconciled = reconcile(conn)
    if reconciled.models_registered < minimum_models:
        msg = (
            f"reconciliation registered {reconciled.models_registered} models, below "
            f"{minimum_models} — registry drift, not a slow day"
        )
        raise BuildError(msg)
    report.reconciled = reconciled
    report.derived = list(reconciled.derived)
    report.unmatched = _most_unmatched(conn, {name for name, _ in reconciled.modality_drops})
    report.plans_reconciled = reconcile_plans(conn)

    # The stage whose absence M6 could not see: without it px_median is empty and every query
    # answers 200 with zero picks.
    report.price_models = build_price_medians(conn)
    if report.price_models <= 0:
        msg = "price medians built 0 models; the artifact would answer every query with no picks"
        raise BuildError(msg)

    conn.commit()

    report.verified = _read_back(conn)
    for table in ("models", "pricing", "scores", "px_median"):
        if report.verified.get(table, 0) <= 0:
            msg = f"{table} is empty in the built artifact; it cannot serve"
            raise BuildError(msg)

    return report


#: How long a `.building` file must be untouched before this build treats it as abandoned.
#:
#: W-028: a SIGKILLed build leaves its workspace behind, and the unique-per-run naming that closed
#: a much worse corruption bug means a run cannot tell another run's litter from a LIVE sibling's
#: workspace — so it deleted neither, and the litter accumulated. Age tells them apart: a running
#: build writes continuously, so a workspace untouched for hours belongs to a process that is gone.
#: Six hours is far beyond any observed build (~60 s) and far below any plausible pause.
ABANDONED_WORKSPACE_AGE_S = 6 * 60 * 60


def _sweep_abandoned_workspaces(target: Path, *, now: float | None = None) -> list[Path]:
    """Delete `.building` files old enough to be certainly dead. Returns what it removed.

    Deliberately conservative in the one direction that matters: an in-flight sibling's workspace
    is seconds old and is never touched, so the worst case of a wrong guess here is litter that
    stays one more cycle — never a live build losing its file underneath it, which is the failure
    the unique naming exists to prevent.
    """
    swept: list[Path] = []
    clock = time.time() if now is None else now
    for candidate in target.parent.glob(f"{target.name}.*.building"):
        try:
            if clock - candidate.stat().st_mtime < ABANDONED_WORKSPACE_AGE_S:
                continue
            candidate.unlink()
        except OSError:
            continue  # a sibling won the race, or the file is not ours to remove
        swept.append(candidate)
    return swept


def _write_sources(path: str | None, sources: dict[str, object] | None) -> None:
    if path:
        Path(path).write_text(json.dumps(sources or {"arrived": [], "carried": {}, "expired": {},
                                                    "since": {}}), encoding="utf-8")


def _read_last_ok(path: str | None) -> dict[str, str]:
    """The refresh's per-source arrival record. Unreadable is EMPTY, which makes every carry judged
    by its rows' own `observed_at` (see `Carry` for the one case that reads younger)."""
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def main(argv: list[str] | None = None) -> int:
    """Operator entry point (REQ-ING-012). See the module docstring for the exit codes."""
    parser = argparse.ArgumentParser(prog="build", description="Build the evidence database.")
    parser.add_argument("--db", required=True, help="path to write; must not already exist")
    parser.add_argument("--plans", default="data/plans.yaml")
    parser.add_argument("--rosters", default="data/rosters.yaml")
    parser.add_argument(
        "--epoch-dir",
        default=None,
        help=(
            "unpacked Epoch bundle directory. The build never fetches it: the refresh does, with "
            "--fetch-epoch (D-158), or the owner supplies one. "
            "Omitting it builds an artifact in which agentic-coding has no primary evidence, "
            "which is reported as a required operator action rather than passed over."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing --db (destructive defaults stay OFF, V3C-06/53)",
    )
    parser.add_argument(
        "--carry-from",
        help="the live artifact: a source that fails serves its last good rows from it (D-156)",
    )
    parser.add_argument(
        "--last-ok",
        help="JSON file mapping each source to when it last arrived; the age a carry is judged by",
    )
    parser.add_argument(
        "--report-out",
        help="write which sources arrived, were carried or expired here, on success and on failure",
    )
    args = parser.parse_args(argv)

    target = Path(args.db)
    # MINOR-3: a directory target used to raise PermissionError and exit 1, a code the D-120
    # contract above does not define. Refuse it by name, before any work, with the declared code.
    if target.is_dir():
        print(json.dumps({"error": f"{target} is a directory, not a database path"}))
        return 2
    if target.exists() and not args.force:
        print(json.dumps({"error": f"{target} exists; pass --force to overwrite"}))
        return 2
    for name, path in (("plans", Path(args.plans)), ("rosters", Path(args.rosters))):
        if not path.is_file():
            print(json.dumps({"error": f"{name} file not found: {path}"}))
            return 2

    # BUILD TO A TEMPORARY FILE AND RENAME ONLY ON SUCCESS.
    #
    # The first version of this function deleted the target BEFORE doing any work, then deleted it
    # again on the failure path. The M7-W1 security review measured what that costs: a 970 KB
    # working artifact, `--force`, one mistyped `--plans`, and the operator is left with nothing —
    # having had a good database thirty seconds earlier. Any of the four required sources going
    # down mid-build does the same, and this wave's own ledger (W-024) is proof that upstreams do.
    #
    # The same review found a second escape: an AttributeError from an upstream payload walked past
    # the except clause entirely and left a schema-valid, px_median-empty database at the target —
    # Trap 1's artifact, produced by the builder written to prevent it.
    #
    # Both are the same defect: the target was the workspace. Now the workspace is a temp file and
    # the target is only ever replaced by a database that finished. `except BaseException` is
    # deliberate and not over-broad — whatever kills this process, including KeyboardInterrupt and
    # MemoryError, must not leave a partial artifact behind.
    # The workspace name is UNIQUE PER RUN, and the first version's was not. With a deterministic
    # `<target>.building`, two overlapping builds shared one path: the security seat drove build A
    # to completion — `"built": true`, 73 models read back — while build B truncated the same file
    # underneath it, and A then published B's empty database. **Trap 1's artifact, from a
    # successful build**, because `_read_back` validates the CONNECTION and `replace()` acts on the
    # PATH. SQLite's unlink detection kills the loser of a natural race, which protects the loser
    # and not the target, and a ~60 s build makes overlap ordinary rather than exotic.
    _sweep_abandoned_workspaces(target)
    handle, raw = tempfile.mkstemp(prefix=f"{target.name}.", suffix=".building", dir=target.parent)
    os.close(handle)
    workspace = Path(raw)
    workspace.unlink()  # sqlite wants to create it; mkstemp only reserved the name

    conn: sqlite3.Connection | None = None
    try:
        conn = connect(str(workspace))
        report = build(
            conn,
            plans_yaml=Path(args.plans).read_text(encoding="utf-8"),
            rosters_yaml=Path(args.rosters).read_text(encoding="utf-8"),
            bundle_dir=Path(args.epoch_dir) if args.epoch_dir else None,
            carry_from=Path(args.carry_from) if args.carry_from else None,
            last_ok=_read_last_ok(args.last_ok),
        )
    except BaseException as exc:
        if conn is not None:
            conn.close()
        workspace.unlink(missing_ok=True)
        # `ValueError` was in this tuple with no reachable trigger, and the comment beside
        # it said the opposite of what it did. The Tester seat's R62 makes the direction
        # explicit: WIDENING this catch is the dangerous move, because every class added
        # here turns a builder bug into a tidy exit 2 that reads like a bad input.
        if isinstance(exc, (BuildError, SourceError, sqlite3.Error, OSError)):
            failed = getattr(exc, "report", None)
            _write_sources(args.report_out, failed.sources_json() if failed else None)
            print(json.dumps({"error": str(exc), "built": False}))
            return 2
        # Anything else is a bug in this builder rather than a bad input. The artifact is already
        # safe; let the traceback out rather than dressing an unknown failure as a clean exit 2.
        raise
    finally:
        if conn is not None:
            conn.close()

    # The publish itself can fail (EPERM, a read-only directory), and when it did it left a
    # complete database at the workspace path plus an uncaught traceback — the one added line that
    # sat outside the guard. It is inside now: the target is still never corrupted, and a failed
    # publish cleans up after itself instead of leaving a 929 KB file nobody will recognise.
    try:
        workspace.replace(target)
    except OSError as exc:
        workspace.unlink(missing_ok=True)
        print(json.dumps({"error": f"could not publish to {target}: {exc}", "built": False}))
        return 2

    _write_sources(args.report_out, report.sources_json())
    payload = report.as_json()
    payload["built"] = True
    payload["path"] = str(target)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 3 if report.required_operator_actions else 0


if __name__ == "__main__":
    sys.exit(main())
