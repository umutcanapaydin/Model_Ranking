"""ARC-AGI-2 from ARC Prize's own public-evaluation runs: client + parser (REQ-SRC-012, D-194).

ARC Prize publishes its runs on the 120 public evaluation tasks of ARC-AGI-2 under MIT
(`arcprize/arc_agi_v2_public_eval` on Hugging Face). They replace Epoch's copy of the ARC Prize
leaderboard, whose terms bar commercial use (#265). They are the PUBLIC set, not the leaderboard's
semi-private one, so the scores run higher than arcprize.org's; the benchmark says so in its name.

Scoring every model setting reads about 4,300 files, past Hugging Face's anonymous rate, and the dataset
has not changed since 2026-06-04. So `scripts/derive_arc_public_eval.py` derives the scores once at a
pinned revision into `data/arc-agi-2-public-eval.json`, committed with its licence and revision, and
this client reads that file; the contract test fails when the dataset moves past the revision.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from app.clients.protocols import SourceError
from app.workflows.schema import ScoreRow

SOURCE_NAME = "arc_agi_2"
BENCHMARK = "ARC-AGI-2 (public eval)"
METRIC = "% correct"
HARNESS = "arc-prize"
DATASET_URL = "https://huggingface.co/datasets/arcprize/arc_agi_v2_public_eval"
RECORD_PATH = Path(__file__).resolve().parents[3] / "data" / "arc-agi-2-public-eval.json"


class ArcAgi2Client:
    """RawSource over the committed derivation (D-001); it reads a file in the repository, not the network."""

    name = SOURCE_NAME
    url = DATASET_URL

    def __init__(self, path: Path = RECORD_PATH) -> None:
        self.path = path

    def fetch_raw(self) -> str:
        try:
            return self.path.read_text(encoding="utf-8")
        except OSError as exc:
            msg = f"{self.name}: the committed derivation is unreadable: {self.path}: {exc}"
            raise SourceError(msg) from exc


def _number(value: object) -> float | None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    return float(value) if math.isfinite(value) else None


def parse_arc_agi_2(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the derivation into one row a model setting; returns (rows, skipped)."""
    try:
        record: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"{source}: the derivation is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(record, dict):
        msg = f"{source}: the derivation is not an object"
        raise SourceError(msg)
    revision, settings, tasks = record.get("revision"), record.get("settings"), record.get("tasks")
    if record.get("licence") != "MIT" or not isinstance(revision, str) or not revision:
        msg = f"{source}: the derivation does not name the MIT dataset at a revision"
        raise SourceError(msg)
    if not isinstance(settings, dict) or not settings or not isinstance(tasks, int) or tasks <= 0:
        msg = f"{source}: the derivation holds no settings or no task count"
        raise SourceError(msg)
    min_tasks = record.get("min_tasks")
    floor: int = min_tasks if isinstance(min_tasks, int) and not isinstance(min_tasks, bool) else tasks
    source_url = f"{DATASET_URL}/tree/{revision}"
    rows: list[ScoreRow] = []
    skipped = 0
    for setting, entry in settings.items():
        score = _number(entry.get("score")) if isinstance(entry, dict) else None
        ran = entry.get("tasks_run") if isinstance(entry, dict) else None
        run_date = entry.get("run_date") if isinstance(entry, dict) else None
        if score is None or not 0.0 <= score <= 100.0 or not isinstance(ran, int) or ran < floor:
            skipped += 1
            continue
        rows.append(ScoreRow(
            raw_name=setting,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score,
            harness=HARNESS,
            # The #265 review's M6: the date of the setting's latest attempt, as the derivation records it.
            run_date=run_date if isinstance(run_date, str) else None,
            cost_total=_number(entry.get("cost_usd")),
            source=source,
            source_url=source_url,
        ))
    return rows, skipped
