"""Replayable M5-W1 comparison of the five owner-mounted coding boards.

This is a decision-evidence producer, not a new production source policy. It
maps each candidate independently into a disposable database, then runs the
same registry, plan coverage, ranking, and selected-evidence health functions
used by the product. Release dates are never promoted to evaluation dates.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from app.clients.epoch import EpochClient
from app.clients.protocols import SourceError
from app.workflows.categories import CATEGORIES
from app.workflows.coverage import plan_coverage, plan_evidence_health
from app.workflows.ingest import RunContext, _store_scores, ingest_epoch, ingest_swebench
from app.workflows.plans import ingest_plans
from app.workflows.recommend import round_score
from app.workflows.registry import reconcile, reconcile_plans
from app.workflows.rosters import ingest_rosters
from app.workflows.schema import ScoreRow, connect
from app.workflows.subscribe import plan_ranking

BASELINE_SOURCE_URL = (
    "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/"
    "master/data/leaderboards.json"
)
OBSERVED_AT = "2026-08-16T00:00:00+00:00"


@dataclass(frozen=True)
class _CandidateSpec:
    id: str
    label: str
    filename: str
    score_column: str
    harness_column: str | None
    run_date_column: str | None
    multiplier: float
    date_meaning: str
    default_source_url: str
    effort_column: str | None = None
    effort_value: str | None = None


_CANDIDATES: tuple[_CandidateSpec, ...] = (
    _CandidateSpec(
        id="deepswe",
        label="DeepSWE",
        filename="deepswe_external.csv",
        score_column="Pass@1",
        harness_column="Harness",
        run_date_column=None,
        multiplier=100.0,
        date_meaning="model release date only; evidence is undated",
        default_source_url="https://deepswe.datacurve.ai/",
        effort_column="Reasoning effort",
        effort_value="high",
    ),
    _CandidateSpec(
        id="frontiercode",
        label="FrontierCode",
        filename="frontiercode_external.csv",
        score_column="Main score",
        harness_column="Harness",
        run_date_column=None,
        multiplier=100.0,
        date_meaning="model release date only; evidence is undated",
        default_source_url="https://cognition.com/frontiercode",
    ),
    _CandidateSpec(
        id="terminalbench",
        label="TerminalBench",
        filename="terminalbench_external.csv",
        score_column="Accuracy mean",
        harness_column="Agent",
        run_date_column="Run date",
        multiplier=100.0,
        date_meaning="Run date is the evaluation date",
        default_source_url="https://www.tbench.ai/leaderboard/terminal-bench/2.0",
    ),
    _CandidateSpec(
        id="aider",
        label="Aider polyglot",
        filename="aider_polyglot_external.csv",
        score_column="Percent correct",
        harness_column=None,
        run_date_column="Date of evaluation",
        multiplier=1.0,
        date_meaning="Date of evaluation is the evaluation date",
        default_source_url="https://aider.chat/docs/leaderboards/",
    ),
)


@dataclass(frozen=True)
class SelectedEvidence:
    """One selected score row, including its plan-level freshness state."""

    plan: str
    model: str
    score: float
    harness: str
    evidence_date: str | None
    status: str


@dataclass(frozen=True)
class BoardMeasurement:
    """Engine result for one independently measured board."""

    candidate: str
    filename: str
    csv_rows: int
    stored_rows: int
    skipped_rows: int
    filtered_rows: int
    scoreable_plans: int
    total_plans: int
    fresh: int
    stale: int
    undated: int
    unscored: int
    date_meaning: str
    selected: tuple[SelectedEvidence, ...]


@dataclass(frozen=True)
class GeminiContradiction:
    """The two real rows REQ-REC-012 requires the decision record to carry."""

    epoch_model: str
    epoch_score: float
    epoch_harness: str
    epoch_evaluation_date: str
    epoch_log_id: str
    epoch_log_url: str
    deepswe_model: str
    deepswe_score: float
    deepswe_harness: str
    deepswe_effort: str
    ratio: float
    verdict: str


@dataclass(frozen=True)
class W1Measurement:
    """Complete replayable W1 decision record input."""

    baseline: BoardMeasurement
    candidates: tuple[BoardMeasurement, ...]
    gemini_contradiction: GeminiContradiction


@dataclass
class _PayloadSource:
    """In-memory RawSource used to replay the committed SWE-bench snapshot."""

    name: str
    url: str
    raw: str

    def fetch_raw(self) -> str:
        return self.raw


@dataclass(frozen=True)
class _ParsedCandidate:
    csv_rows: int
    rows: tuple[ScoreRow, ...]
    skipped: int
    filtered: int


def _csv_rows(path: Path) -> list[dict[str, str | None]]:
    """Read one strict CSV shape and fail loudly on envelope defects."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise SourceError(f"W1 measurement input unreadable: {path}: {exc}") from exc
    try:
        reader = csv.DictReader(io.StringIO(raw), strict=True)
        if reader.fieldnames is None:
            raise SourceError(f"W1 measurement CSV has no header: {path}")
        rows = list(reader)
    except csv.Error as exc:
        raise SourceError(f"W1 measurement CSV malformed: {path}: {exc}") from exc
    if not rows:
        raise SourceError(f"W1 measurement CSV has no rows: {path}")
    return rows


def _required_columns(rows: list[dict[str, str | None]], spec: _CandidateSpec) -> None:
    required = {"Model version", spec.score_column}
    if spec.harness_column is not None:
        required.add(spec.harness_column)
    if spec.run_date_column is not None:
        required.add(spec.run_date_column)
    if spec.effort_column is not None:
        required.add(spec.effort_column)
    missing = sorted(column for column in required if column not in rows[0])
    if missing:
        raise SourceError(f"W1 measurement {spec.filename} missing columns: {', '.join(missing)}")


def _finite_score(value: object, multiplier: float) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    score = parsed * multiplier
    return score if math.isfinite(score) and 0.0 <= score <= 100.0 else None


def _evaluation_date(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()[:10]
    try:
        parsed = dt.date.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed.isoformat() if parsed.isoformat() == candidate else None


def _source_url(entry: dict[str, str | None], default: str) -> str:
    for column in ("Source link", "Source Link", "Source"):
        value = entry.get(column)
        if isinstance(value, str) and value.strip().startswith("https://"):
            return value.strip()
    return default


def _parse_candidate(path: Path, spec: _CandidateSpec) -> _ParsedCandidate:
    entries = _csv_rows(path)
    _required_columns(entries, spec)
    best: dict[tuple[str, str], ScoreRow] = {}
    skipped = filtered = 0
    benchmark = CATEGORIES["coding"].primary_benchmark
    metric = CATEGORIES["coding"].metric

    for entry in entries:
        if None in entry:  # an over-wide row is a malformed real shape, not a silent skip
            raise SourceError(f"W1 measurement {spec.filename} contains an over-wide CSV row")
        if spec.effort_column is not None and entry.get(spec.effort_column) != spec.effort_value:
            filtered += 1
            continue
        raw_name = entry.get("Model version")
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        score = _finite_score(entry.get(spec.score_column), spec.multiplier)
        if spec.harness_column is None:
            harness = "aider"
        else:
            raw_harness = entry.get(spec.harness_column)
            harness = raw_harness.strip() if isinstance(raw_harness, str) else ""
        run_date = (
            _evaluation_date(entry.get(spec.run_date_column))
            if spec.run_date_column is not None
            else None
        )
        if not name or score is None or not harness:
            skipped += 1
            continue
        if (
            spec.run_date_column is not None
            and entry.get(spec.run_date_column)
            and run_date is None
        ):
            skipped += 1
            continue
        row = ScoreRow(
            raw_name=name,
            benchmark=benchmark,
            metric=metric,
            score=score,
            harness=harness,
            run_date=run_date,
            cost_total=None,
            source=f"m5_w1_measure_{spec.id}",
            source_url=_source_url(entry, spec.default_source_url),
        )
        key = (name, harness)
        prior = best.get(key)
        if prior is not None:
            skipped += 1
            if (row.score, row.run_date or "") <= (prior.score, prior.run_date or ""):
                continue
        best[key] = row
    return _ParsedCandidate(len(entries), tuple(best.values()), skipped, filtered)


def _prepared_connection(plans_raw: str, rosters_raw: str) -> sqlite3.Connection:
    conn = connect()
    run = RunContext(observed_at=OBSERVED_AT)
    ingest_plans(conn, plans_raw, run)
    ingest_rosters(conn, rosters_raw, run)
    reconcile_plans(conn)
    return conn


def _engine_measurement(
    conn: sqlite3.Connection,
    *,
    candidate: str,
    filename: str,
    csv_rows: int,
    stored_rows: int,
    skipped_rows: int,
    filtered_rows: int,
    date_meaning: str,
    today: dt.date,
) -> BoardMeasurement:
    reconcile(conn)
    coverage = next(row for row in plan_coverage(conn) if row.category == "coding")
    ranking = plan_ranking(conn, CATEGORIES["coding"])
    health = plan_evidence_health(conn, CATEGORIES["coding"], today)
    if coverage.scoreable_plans != len(ranking):
        raise AssertionError("coverage and ranking disagree on scoreable plan count")
    health_by_id = {row.plan_id: row for row in health.plans}
    selected = tuple(
        SelectedEvidence(
            plan=row.plan,
            model=row.scored_by_model,
            score=round_score(row.score),
            harness=row.harness,
            evidence_date=row.evidence_date,
            status=health_by_id[row.plan_id].status,
        )
        for row in ranking
    )
    return BoardMeasurement(
        candidate=candidate,
        filename=filename,
        csv_rows=csv_rows,
        stored_rows=stored_rows,
        skipped_rows=skipped_rows,
        filtered_rows=filtered_rows,
        scoreable_plans=coverage.scoreable_plans,
        total_plans=coverage.total_plans,
        fresh=health.fresh,
        stale=health.stale,
        undated=health.undated,
        unscored=health.unscored,
        date_meaning=date_meaning,
        selected=selected,
    )


def _baseline(
    plans_raw: str, rosters_raw: str, baseline_raw: str, today: dt.date
) -> BoardMeasurement:
    conn = _prepared_connection(plans_raw, rosters_raw)
    try:
        report = ingest_swebench(
            conn,
            _PayloadSource("swebench", BASELINE_SOURCE_URL, baseline_raw),
            RunContext(observed_at=OBSERVED_AT),
        )
        return _engine_measurement(
            conn,
            candidate="Existing SWE-bench baseline",
            filename="m5-swebench-baseline.json",
            csv_rows=report.stored + report.skipped,
            stored_rows=report.stored,
            skipped_rows=report.skipped,
            filtered_rows=0,
            date_meaning="leaderboard date is the evaluation date",
            today=today,
        )
    finally:
        conn.close()


def _epoch(
    bundle_dir: Path, plans_raw: str, rosters_raw: str, today: dt.date, last_verified: str
) -> BoardMeasurement:
    conn = _prepared_connection(plans_raw, rosters_raw)
    try:
        client = EpochClient(bundle_dir, last_verified=last_verified)
        report = ingest_epoch(conn, client, RunContext(observed_at=OBSERVED_AT))
        csv_rows = len(_csv_rows(bundle_dir / "swe_bench_verified.csv"))
        return _engine_measurement(
            conn,
            candidate="Epoch SWE-bench Verified",
            filename="swe_bench_verified.csv",
            csv_rows=csv_rows,
            stored_rows=report.stored,
            skipped_rows=report.skipped,
            filtered_rows=0,
            date_meaning="Started at is the evaluation timestamp",
            today=today,
        )
    finally:
        conn.close()


def _candidate(
    bundle_dir: Path,
    plans_raw: str,
    rosters_raw: str,
    today: dt.date,
    spec: _CandidateSpec,
) -> BoardMeasurement:
    parsed = _parse_candidate(bundle_dir / spec.filename, spec)
    conn = _prepared_connection(plans_raw, rosters_raw)
    try:
        _store_scores(
            conn,
            f"m5_w1_measure_{spec.id}",
            list(parsed.rows),
            RunContext(observed_at=OBSERVED_AT),
        )
        return _engine_measurement(
            conn,
            candidate=spec.label,
            filename=spec.filename,
            csv_rows=parsed.csv_rows,
            stored_rows=len(parsed.rows),
            skipped_rows=parsed.skipped,
            filtered_rows=parsed.filtered,
            date_meaning=spec.date_meaning,
            today=today,
        )
    finally:
        conn.close()


def _find_model(rows: list[dict[str, str | None]], model: str) -> dict[str, str | None]:
    matches = [row for row in rows if row.get("Model version") == model]
    if len(matches) != 1:
        raise SourceError(f"W1 measurement expected exactly one {model!r} row, got {len(matches)}")
    return matches[0]


def _gemini_contradiction(bundle_dir: Path) -> GeminiContradiction:
    epoch = _find_model(
        _csv_rows(bundle_dir / "swe_bench_verified.csv"),
        "gemini-3.1-pro-preview-customtools",
    )
    deep = _find_model(_csv_rows(bundle_dir / "deepswe_external.csv"), "gemini-3.1-pro-preview")
    try:
        epoch_score = float(epoch["mean_score"] or "")
        deep_score = float(deep["Pass@1"] or "")
    except (KeyError, ValueError) as exc:
        raise SourceError("REQ-REC-012 Gemini evidence has an unusable score") from exc
    required = {
        "epoch_evaluation_date": _evaluation_date(epoch.get("Started at")),
        "epoch_log_id": epoch.get("id"),
        "epoch_log_url": epoch.get("Logs"),
        "deepswe_harness": deep.get("Harness"),
        "deepswe_effort": deep.get("Reasoning effort"),
    }
    if not all(isinstance(value, str) and value for value in required.values()):
        raise SourceError("REQ-REC-012 Gemini evidence is missing provenance/configuration fields")
    return GeminiContradiction(
        epoch_model="gemini-3.1-pro-preview-customtools",
        epoch_score=epoch_score,
        epoch_harness="inspect_ai",
        epoch_evaluation_date=required["epoch_evaluation_date"] or "",
        epoch_log_id=required["epoch_log_id"] or "",
        epoch_log_url=required["epoch_log_url"] or "",
        deepswe_model="gemini-3.1-pro-preview",
        deepswe_score=deep_score,
        deepswe_harness=required["deepswe_harness"] or "",
        deepswe_effort=required["deepswe_effort"] or "",
        ratio=epoch_score / deep_score,
        verdict="unresolved; disclose both scores and the harness/effort difference",
    )


def measure_w1_boards(
    bundle_dir: str | Path,
    *,
    plans_raw: str,
    rosters_raw: str,
    baseline_raw: str,
    today: dt.date,
    last_verified: str,
) -> W1Measurement:
    """Run the signed W1 comparison from local artifacts without network access."""
    bundle = Path(bundle_dir)
    baseline = _baseline(plans_raw, rosters_raw, baseline_raw, today)
    candidates: tuple[BoardMeasurement, ...] = (
        _epoch(bundle, plans_raw, rosters_raw, today, last_verified),
    )
    candidates += tuple(
        _candidate(bundle, plans_raw, rosters_raw, today, spec) for spec in _CANDIDATES
    )
    return W1Measurement(
        baseline=baseline,
        candidates=candidates,
        gemini_contradiction=_gemini_contradiction(bundle),
    )


def main(argv: list[str] | None = None) -> int:
    """Print the deterministic W1 measurement JSON. No files or databases are mutated."""
    parser = argparse.ArgumentParser(prog="m5-w1-measure-boards", description=__doc__)
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--plans", default="data/plans.yaml")
    parser.add_argument("--rosters", default="data/rosters.yaml")
    parser.add_argument("--baseline", default="data/m5-swebench-baseline.json")
    parser.add_argument("--today", default="2026-08-16")
    parser.add_argument("--last-verified", default="2026-08-15")
    args = parser.parse_args(argv)
    try:
        today = dt.date.fromisoformat(args.today)
        report = measure_w1_boards(
            args.bundle_dir,
            plans_raw=Path(args.plans).read_text(encoding="utf-8"),
            rosters_raw=Path(args.rosters).read_text(encoding="utf-8"),
            baseline_raw=Path(args.baseline).read_text(encoding="utf-8"),
            today=today,
            last_verified=args.last_verified,
        )
    except (OSError, SourceError, ValueError) as exc:
        print(f"error: W1 measurement failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
