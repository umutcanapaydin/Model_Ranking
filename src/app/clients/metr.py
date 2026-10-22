"""METR's time horizons from METR's own file: client + parser (REQ-SRC-013, D-218 clause 2, D-219).

METR publishes each model's time horizon as one YAML file its page offers for download (Time Horizon 1.1,
`assets/benchmark_results_1_1.yaml`): the length of task, in a skilled person's minutes, that the model finishes half
the time (`p50_horizon_length`). METR publishes no licence and no terms, and its robots allow the file; its public
numbers are used under D-215, attributed to METR with its link. They rank `long-tasks`, the surface D-218 clause 2
opens for them.

A row's name is METR's key with its `_inspect` mark removed (it names the harness, Inspect) and its underscores read as
hyphens, the spelling the registry reconciles. Its harness is the scaffold METR names last for the model, or `METR`
where it names none. Rows are undated: `release_date` is the model's release, never an evaluation date (D-139).
The file is read through the project's bounded YAML loader (W-005), so an alias bomb is refused before it expands.
"""

from __future__ import annotations

import math
from typing import Any

import yaml

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import ScoreRow
from app.workflows.yaml_guard import safe_load_bounded

SOURCE_NAME = "metr_time_horizons"
BENCHMARK = "METR time horizon"
METRIC = "minutes"
SITE_URL = "https://metr.org/time-horizons/"
DATA_URL = "https://metr.org/assets/benchmark_results_1_1.yaml"
_TIMEOUT_S = 60.0
#: The harness a row names where METR names no scaffold for the model.
DEFAULT_HARNESS = "METR"
_INSPECT_MARK = "_inspect"


class MetrClient:
    """Production RawSource for METR's time-horizon file (D-001): one public file, from METR's own host."""

    name = SOURCE_NAME
    url = DATA_URL
    hosts: tuple[str, ...] = ("metr.org",)

    def fetch_raw(self) -> str:
        return fetch_bounded(DATA_URL, self.name, _TIMEOUT_S, hosts=self.hosts)


def _name(key: str) -> str:
    return key.removesuffix(_INSPECT_MARK).replace("_", "-")


def _harness(entry: dict[str, Any]) -> str:
    scaffolds = entry.get("scaffolds")
    named = [s.strip() for s in scaffolds if isinstance(s, str) and s.strip()] if isinstance(scaffolds, list) else []
    return named[-1] if named else DEFAULT_HARNESS


def _horizon(entry: dict[str, Any]) -> float | None:
    metrics = entry.get("metrics")
    horizon = metrics.get("p50_horizon_length") if isinstance(metrics, dict) else None
    estimate = horizon.get("estimate") if isinstance(horizon, dict) else None
    if not isinstance(estimate, int | float) or isinstance(estimate, bool) or not math.isfinite(estimate):
        return None
    return float(estimate) if estimate >= 0 else None


def parse_metr(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the file into one row a model at its 50% time horizon in minutes; returns (rows, skipped).

    A model without a usable horizon is skipped and counted; a file that is not the board fails the source.
    """
    try:
        board: Any = safe_load_bounded(raw, what="METR's time horizons (remote)")
    except yaml.YAMLError as exc:
        msg = f"{source}: the file is not valid YAML: {exc}"
        raise SourceError(msg) from exc
    results = board.get("results") if isinstance(board, dict) else None
    if not isinstance(results, dict) or not results:
        msg = f"{source}: the file holds no results"
        raise SourceError(msg)
    rows: list[ScoreRow] = []
    skipped = 0
    for key, entry in results.items():
        score = _horizon(entry) if isinstance(entry, dict) else None
        if not isinstance(key, str) or not key.strip() or score is None or not isinstance(entry, dict):
            skipped += 1
            continue
        rows.append(ScoreRow(
            raw_name=_name(key.strip()),
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score,
            harness=_harness(entry),
            run_date=None,
            cost_total=None,
            source=source,
            source_url=SITE_URL,
        ))
    if not rows:
        msg = f"{source}: no model in the file has a usable time horizon"
        raise SourceError(msg)
    return rows, skipped
