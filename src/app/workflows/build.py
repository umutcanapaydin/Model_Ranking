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
import json
import os
import re
import sqlite3
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

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
from app.workflows.schema import connect, reset_source
from app.workflows.sources import (
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


def _ingest_boards(
    conn: sqlite3.Connection,
    bundle_dir: Path | None,
    run: RunContext,
    boards: Sequence[EpochBoard] | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Read the declared Epoch boards (D-127). Same bundle, same read-only rules as `_ingest_bundles`.

    Separate from `_ingest_bundles` because these are DATA-declared boards sharing one reader, while
    the two bundles above are distinct clients with their own parsers. Merging them would mean the
    board table pretending to be a client list, which is what the registry exists to stop.
    """
    boards = EPOCH_BOARDS if boards is None else boards
    if bundle_dir is None:
        return [], [f"{b.source_name}: no local bundle directory supplied" for b in boards]

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
            for table in ("pricing", "scores"):
                reset_source(conn, table, board.source_name)
            missing.append(f"{board.source_name}: {exc}")
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


def _ingest_bundles(
    conn: sqlite3.Connection,
    bundle_dir: Path | None,
    run: RunContext,
    bundles: Sequence[LocalBundle] | None = None,
) -> tuple[list[SourceReport], list[str]]:
    """Read the owner-placed bundle, never fetch it (D-101).

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
        return [], [f"{b.name}: no local bundle directory supplied" for b in bundles]

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
            missing.append(f"{bundle.name}: {exc}")
            continue
        results.append(result)
    return results, missing


def _ingest_sources(
    conn: sqlite3.Connection, sources: Sequence[RemoteSource], run: RunContext
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
            if source.required:
                msg = f"{source.name}: dependency unusable: {exc}"
                raise BuildError(msg) from exc
            # An OPTIONAL source that fails does not stop the build, and it does not disappear
            # either. It is named here, surfaces as exit 3, and the categories it was the sole
            # evidence for will disclose that they have none.
            missing.append(f"{source.name}: {exc}")
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
    run: RunContext | None = None,
    minimum_models: int | None = None,
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
    minimum_models = MINIMUM_MODELS_REGISTERED if minimum_models is None else minimum_models
    run = run or RunContext()
    report = BuildReport()

    report.plans_stored = _ingest_curated(
        "plan", lambda: ingest_plans(conn, plans_yaml, run)
    )
    report.rosters_stored = _ingest_curated(
        "roster", lambda: ingest_rosters(conn, rosters_yaml, run)
    )
    report.sources, degraded = _ingest_sources(conn, sources, run)
    bundle_reports, bundle_missing = _ingest_bundles(conn, bundle_dir, run, bundles)
    board_reports, board_missing = _ingest_boards(conn, bundle_dir, run, boards)
    report.sources.extend(board_reports)
    report.sources.extend(bundle_reports)
    report.required_operator_actions = _surfaces_left_without_evidence(
        [*degraded, *bundle_missing, *board_missing]
    )

    reconciled = reconcile(conn)
    if reconciled.models_registered < minimum_models:
        msg = (
            f"reconciliation registered {reconciled.models_registered} models, below "
            f"{minimum_models} — registry drift, not a slow day"
        )
        raise BuildError(msg)
    report.reconciled = reconciled
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
            "unpacked Epoch bundle directory (D-101: acquired out of band, never fetched here). "
            "Omitting it builds an artifact in which agentic-coding has no primary evidence, "
            "which is reported as a required operator action rather than passed over."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing --db (destructive defaults stay OFF, V3C-06/53)",
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

    payload = report.as_json()
    payload["built"] = True
    payload["path"] = str(target)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 3 if report.required_operator_actions else 0


if __name__ == "__main__":
    sys.exit(main())
