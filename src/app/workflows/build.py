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
import re
import sqlite3
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, SourceReport
from app.workflows.plans import ingest_plans
from app.workflows.rank import build_price_medians
from app.workflows.registry import (
    PlanReconcileReport,
    ReconcileReport,
    reconcile,
    reconcile_plans,
)
from app.workflows.rosters import ingest_rosters
from app.workflows.schema import connect
from app.workflows.sources import REMOTE_SOURCES, RemoteSource

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
    report.required_operator_actions = _surfaces_left_without_evidence(degraded)

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


def main(argv: list[str] | None = None) -> int:
    """Operator entry point (REQ-ING-012). See the module docstring for the exit codes."""
    parser = argparse.ArgumentParser(prog="build", description="Build the evidence database.")
    parser.add_argument("--db", required=True, help="path to write; must not already exist")
    parser.add_argument("--plans", default="data/plans.yaml")
    parser.add_argument("--rosters", default="data/rosters.yaml")
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing --db (destructive defaults stay OFF, V3C-06/53)",
    )
    args = parser.parse_args(argv)

    target = Path(args.db)
    if target.exists() and not args.force:
        print(json.dumps({"error": f"{target} exists; pass --force to overwrite"}))
        return 2
    for name, path in (("plans", Path(args.plans)), ("rosters", Path(args.rosters))):
        if not path.is_file():
            print(json.dumps({"error": f"{name} file not found: {path}"}))
            return 2

    if target.exists():
        target.unlink()

    conn: sqlite3.Connection | None = None
    try:
        conn = connect(str(target))
        report = build(
            conn,
            plans_yaml=Path(args.plans).read_text(encoding="utf-8"),
            rosters_yaml=Path(args.rosters).read_text(encoding="utf-8"),
        )
    except (BuildError, SourceError, sqlite3.Error, OSError) as exc:
        if conn is not None:
            conn.close()
        # A half-built artifact that looks servable is the failure mode this milestone exists to
        # end. Nothing partial survives a failed build.
        target.unlink(missing_ok=True)
        print(json.dumps({"error": str(exc), "built": False}))
        return 2
    finally:
        if conn is not None:
            conn.close()

    payload = report.as_json()
    payload["built"] = True
    payload["path"] = str(target)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 3 if report.required_operator_actions else 0


if __name__ == "__main__":
    sys.exit(main())
