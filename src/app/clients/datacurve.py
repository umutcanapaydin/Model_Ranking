"""DeepSWE from Datacurve's own leaderboard: client + parser (REQ-SRC-012, D-216).

It replaces Epoch's copy of the board (`epoch_deepswe_external`), which publishes no licence (#265). Datacurve's site
loads its leaderboard as one JSON file (`LEADERBOARD_URL`, DeepSWE v1.1): one row a configuration, with its model,
harness, stated `reasoning_effort` and Pass@1. It is public, so no token is read or sent, and it publishes no licence:
its numbers are used under D-215, attributed to Datacurve with its link.

A row keeps the effort Datacurve states; a row that states none ran at its model's default and stands at `high`, the
surface's level (D-194 clause 1), as the leaderboard itself labels Gemini 3.1 Pro's default run. Rows are undated: the
list gathers jobs of several dates and names none per row.

There is no fallback. On a night the site fails, answers with something that is not the board, or redirects off its
host, the source fails, and the refresh carries the previous night's rows (D-156), as for every source (the owner's
ruling of 2026-10-21).
"""

from __future__ import annotations

import json
import math
from typing import Any

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import EFFORT_LEVELS, ScoreRow

SOURCE_NAME = "datacurve_deepswe"
BENCHMARK = "DeepSWE"
METRIC = "% resolved"
SITE_URL = "https://deepswe.datacurve.ai/"
LEADERBOARD_URL = "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json"
_TIMEOUT_S = 60.0
#: The benchmark a leaderboard row must name.
_LEADERBOARD_SOURCE = "deep-swe"
#: D-216 clause 3: a row that states no effort ran at its model's default and stands at `agentic-coding`'s level.
DEFAULT_EFFORT = "high"


class DatacurveClient:
    """Production RawSource for Datacurve's DeepSWE leaderboard (D-001): one public file, from its own host."""

    name = SOURCE_NAME
    url = LEADERBOARD_URL
    hosts: tuple[str, ...] = ("deepswe.datacurve.ai",)

    def fetch_raw(self) -> str:
        return fetch_bounded(LEADERBOARD_URL, self.name, _TIMEOUT_S, hosts=self.hosts)


def parse_datacurve(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the leaderboard into one row a configuration; returns (rows, skipped).

    A row that is not a usable DeepSWE score is skipped and counted; a file that is not the board fails the source.
    """
    try:
        board: Any = json.loads(raw)
    except (ValueError, RecursionError) as exc:  # #411: a 4,300-digit integer, deep nesting
        msg = f"{source}: the leaderboard is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    entries = board.get("rows") if isinstance(board, dict) else None
    if not isinstance(entries, list) or not entries:
        msg = f"{source}: the leaderboard holds no rows"
        raise SourceError(msg)
    best: dict[tuple[str, str, str], ScoreRow] = {}
    skipped = 0
    for entry in entries:
        row = _row(entry, source)
        if row is None:
            skipped += 1
            continue
        key = (row.raw_name, row.harness, row.effort or "")
        if key in best:
            skipped += 1
            if row.score <= best[key].score:
                continue
        best[key] = row
    return list(best.values()), skipped


def _row(entry: object, source: str) -> ScoreRow | None:
    if not isinstance(entry, dict) or entry.get("source") != _LEADERBOARD_SOURCE:
        return None
    model, harness, mean = entry.get("model"), entry.get("harness"), entry.get("pass_at_1")
    if not isinstance(model, str) or not model.strip() or not isinstance(harness, str) or not harness.strip():
        return None
    if not isinstance(mean, int | float) or isinstance(mean, bool) or not math.isfinite(mean) or not 0 <= mean <= 1:
        return None
    stated = entry.get("reasoning_effort")
    effort = DEFAULT_EFFORT if stated is None else stated if stated in EFFORT_LEVELS else None
    if effort is None:
        return None
    return ScoreRow(
        raw_name=model.strip(),
        benchmark=BENCHMARK,
        metric=METRIC,
        score=float(mean) * 100.0,
        harness=harness.strip(),
        run_date=None,
        cost_total=None,
        source=source,
        source_url=SITE_URL,
        effort=effort,
    )
