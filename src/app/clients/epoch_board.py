"""One parameterised reader for every board in the Epoch bundle (D-127).

**Why this exists rather than a client per board.** The bundle carries 77 CSVs and this project
reads two of them, through two near-identical clients that each hardcode a filename, a source name
and a benchmark. Opening D-127's nine categories that way would mean six more copies — and "a list
of files typed out by hand" is the shape this project has been caught by five times, most recently
in M7's four separate instances. The boards are declared as DATA in `app.workflows.sources`; this
module is the one reader that walks them.

**What varies between boards, and it is more than the filename.** Epoch publishes two kinds of
file. Boards it evaluated itself carry `mean_score` on a [0, 1] scale and a `Started at` timestamp.
Boards it AGGREGATES from elsewhere carry whatever column the upstream leaderboard used —
`Score`, `Accuracy`, `EM`, `Arena Score`, `ECI Score` — and **no evaluation date at all**.

That second group is undated evidence, which this project already has a contract for: the engine
discloses it per answer (REQ-API-004) exactly as it does for DeepSWE. Nothing new is needed to be
honest about it — but a reader that silently invented a date would defeat the disclosure, so this
one leaves `run_date` as `None` and lets the surface say so.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import math
from dataclasses import dataclass
from pathlib import Path

from app.clients.epoch import validate_last_verified
from app.clients.protocols import SourceError
from app.workflows.schema import ScoreRow


@dataclass(frozen=True)
class EpochBoard:
    """One board in the bundle, declared rather than coded."""

    file: str
    source_name: str
    benchmark: str
    metric: str
    score_column: str
    #: ``fraction`` multiplies by 100 so a [0, 1] board lands on the same 0-100 scale the rest of
    #: this project reports. That is a UNIT CHANGE of one quantity, not the cross-scale mixing
    #: D-105 forbids -- 0.65 and 65% are the same number. It is declared per board because an
    #: unconverted fraction silently fails every threshold: a floor of 83.6 rejects a board whose
    #: leader reads 0.948.
    scale: str = "fraction"
    #: ``Started at`` where Epoch ran the evaluation itself; ``None`` for an aggregated board,
    #: which makes its rows undated evidence the engine discloses.
    date_column: str | None = None
    #: The upper bound a parsed score may not exceed, on the board's OWN scale before conversion.
    #: Elo boards have no natural ceiling, so ``None`` disables the check rather than inventing one.
    maximum: float | None = 1.0


class EpochBoardClient:
    """Reads ONE declared board out of the owner-placed bundle. Never fetches (D-101)."""

    def __init__(self, bundle_dir: str | Path, board: EpochBoard, *, last_verified: str) -> None:
        if isinstance(bundle_dir, str) and "://" in bundle_dir:
            msg = f"{board.source_name}: expected a local unpacked bundle directory, not a URL"
            raise SourceError(msg)
        self.board = board
        self.name = board.source_name
        self.url = f"epoch-bundle#{board.file}"
        self.bundle_dir = Path(bundle_dir)
        self.last_verified = validate_last_verified(last_verified, source_name=board.source_name)

    def fetch_raw(self) -> str:
        """Read the allowlisted CSV, refusing anything that resolves outside the bundle.

        M5's finding: a bundle is an unpacked ZIP from the internet, a ZIP can carry a symlink, and
        that was reproduced against /etc/shadow. The control is `is_relative_to(root)` on the
        RESOLVED path, which catches a symlink and a `../` traversal alike.

        An earlier version also tested `resolved.is_symlink()` and the docstring presented that as
        the M5 check. It is dead by construction -- `resolve(strict=True)` on the line above has
        already followed every link, so the predicate is always False. Removed rather than left
        reading as a second control: a tautology cited as a guard is how the next reader concludes
        a check exists where there is none. `tests/unit/test_epoch_board.py` now executes the real
        one against a planted symlink.
        """
        path = self.bundle_dir / self.board.file
        try:
            resolved = path.resolve(strict=True)
            root = self.bundle_dir.resolve(strict=True)
        except OSError as exc:
            msg = f"{self.name}: missing CSV in local unpacked bundle: {path}"
            raise SourceError(msg) from exc
        if not resolved.is_relative_to(root):
            msg = f"{self.name}: refused a CSV that resolves outside the bundle: {path}"
            raise SourceError(msg)
        try:
            return resolved.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            msg = f"{self.name}: CSV is unreadable: {path}: {exc}"
            raise SourceError(msg) from exc


def _number(value: object, *, maximum: float | None) -> float | None:
    """Parse one score, rejecting bool-like, non-finite and out-of-range values."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        score = float(str(value).strip().replace("%", ""))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score) or score < 0.0:
        return None
    if maximum is not None and score > maximum:
        return None
    return score


def _check_header(reader: csv.DictReader[str], board: EpochBoard) -> None:
    """Refuse a board whose SHAPE changed, loudly and before any row is read.

    Extracted from `parse_board` when containing `csv.Error` pushed that function past the
    complexity gate. Keeping it inline would have meant either a `# noqa` or a quieter check, and
    the shape guards are the reason this reader fails loud rather than empty.
    """
    try:
        fieldnames = reader.fieldnames
    except csv.Error as exc:
        msg = f"{board.source_name}: CSV header is unreadable: {exc}"
        raise SourceError(msg) from exc
    if not fieldnames:
        msg = f"{board.source_name}: CSV has no header"
        raise SourceError(msg)
    if "Model version" not in fieldnames:
        msg = f"{board.source_name}: CSV has no 'Model version' column"
        raise SourceError(msg)
    if board.score_column not in fieldnames:
        # Loud rather than empty: a renamed upstream column would otherwise ingest zero rows and
        # look like a quiet outage instead of the shape change it is.
        msg = (
            f"{board.source_name}: declared score column {board.score_column!r} is not in the CSV. "
            f"Columns present: {fieldnames}"
        )
        raise SourceError(msg)


def parse_board(
    raw: str, board: EpochBoard, *, source: str | None = None, source_url: str | None = None
) -> tuple[list[ScoreRow], int]:
    """Parse one declared board into the project's score contract.

    Returns ``(rows, skipped)``. A row is skipped when it has no model name or no readable score —
    counted, never guessed at (REQ-CAN-005's rule applied to a different field).
    """
    if not raw.strip():
        msg = f"{board.source_name}: CSV payload is empty"
        raise SourceError(msg)

    reader = csv.DictReader(io.StringIO(raw))
    _check_header(reader, board)

    # `csv.Error` is a BAD INPUT, not a builder bug, and it escaped as an uncaught traceback:
    # `_ingest_boards` catches `(SourceError, OSError)`, and a single cell over csv's 131_072-byte
    # field limit -- or a NUL byte -- propagated all the way out and broke D-120's exit contract.
    # `build.py` reserves the traceback path for "a bug in this builder rather than a bad input"
    # in as many words. One oversized cell in an operator-supplied file is exactly a bad input.
    try:
        entries = list(reader)
    except csv.Error as exc:
        msg = f"{board.source_name}: CSV is malformed: {exc}"
        raise SourceError(msg) from exc

    multiplier = 100.0 if board.scale == "fraction" else 1.0
    best: dict[str, ScoreRow] = {}
    skipped = 0

    for entry in entries:
        name = (entry.get("Model version") or "").strip()
        score = _number(entry.get(board.score_column), maximum=board.maximum)
        if not name or score is None:
            skipped += 1
            continue
        run_date = None
        if board.date_column:
            # VALIDATED, not truncated. `stamp[:10]` accepted any ten characters as a date, so
            # `<script>alert(1)</script>` became the evidence date `'<script>al'` -- and because
            # `_evidence_dating` only asks whether the date is not-None, the surface then reported
            # its evidence as DATED. This module's own docstring says a reader that invented a date
            # would defeat that disclosure; inventing one by truncation is still inventing one.
            # It also put ten characters of third-party text into an unauthenticated payload.
            # The sibling client has always validated (clients/epoch.py uses date.fromisoformat).
            stamp = (entry.get(board.date_column) or "").strip()[:10]
            try:
                run_date = dt.date.fromisoformat(stamp).isoformat() if stamp else None
            except ValueError:
                run_date = None
        row = ScoreRow(
            raw_name=name,
            benchmark=board.benchmark,
            metric=board.metric,
            score=score * multiplier,
            harness="none",
            run_date=run_date,
            cost_total=None,
            source=source or board.source_name,
            source_url=source_url or f"epoch-bundle#{board.file}",
        )
        # One row per model: a board may list a model more than once (different scaffolds, reruns).
        # The BEST score wins, which is the same rule `parse_swe_bench_verified` already applies.
        prior = best.get(name)
        if prior is None or row.score > prior.score:
            best[name] = row

    return list(best.values()), skipped
