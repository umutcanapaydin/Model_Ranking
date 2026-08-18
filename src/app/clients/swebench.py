"""SWE-bench Verified source: client + parser (REQ-ING-002, D-101).

Fetches the swebench.com leaderboard JSON from its GitHub repository
(documented raw-data endpoint — NOT scraping). Only the **Verified**
leaderboard is ingested; a score record is always a model+harness pair.
"""

from __future__ import annotations

import json
from typing import Any

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import ScoreRow

SWEBENCH_URL = (
    "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/"
    "master/data/leaderboards.json"
)
BENCHMARK = "SWE-bench Verified"
METRIC = "% resolved"
UNKNOWN_HARNESS = "unknown-agent"
_TIMEOUT_S = 30.0


class SweBenchClient:
    """Production RawSource for the SWE-bench leaderboards (D-001)."""

    name = "swebench"

    def __init__(self, url: str = SWEBENCH_URL) -> None:
        self.url = url

    def fetch_raw(self) -> str:
        return fetch_bounded(self.url, self.name, _TIMEOUT_S)


def split_harness(entry_name: str) -> tuple[str, str]:
    """Split a leaderboard entry into (harness, model-ish remainder).

    Entries look like ``"live-SWE-agent + Claude 4.5 Opus medium"``; an entry
    without a ``+`` keeps the full name and gets UNKNOWN_HARNESS
    (REQ-ING-002: harness is never silently dropped).
    """
    if "+" in entry_name:
        harness, _, rest = entry_name.partition("+")
        return harness.strip(), rest.strip()
    return UNKNOWN_HARNESS, entry_name.strip()


def parse_verified(
    raw: str, *, source: str = "swebench", source_url: str = SWEBENCH_URL
) -> tuple[list[ScoreRow], int]:
    """Parse the Verified leaderboard into score rows.

    Returns ``(rows, skipped)``; entries without a usable ``resolved`` score
    are skipped. Other leaderboards (Lite, Multimodal, …) are never mixed in
    (REQ-ING-002).
    """
    try:
        data: dict[str, Any] = json.loads(raw)
        boards = data["leaderboards"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        msg = f"swebench payload malformed: {exc!r}"
        raise SourceError(msg) from exc
    if not isinstance(boards, list):
        msg = "swebench payload malformed: leaderboards is not a list"
        raise SourceError(msg)

    verified = next(
        (b for b in boards if isinstance(b, dict) and b.get("name") == "Verified"), None
    )
    if verified is None:
        msg = "swebench payload has no Verified leaderboard"
        raise SourceError(msg)
    results = verified.get("results", [])
    if not isinstance(results, list):
        msg = "swebench payload malformed: Verified results is not a list"
        raise SourceError(msg)

    best: dict[str, ScoreRow] = {}
    skipped = 0
    for entry in results:
        if not isinstance(entry, dict):
            skipped += 1
            continue
        name = entry.get("name")
        resolved = entry.get("resolved")
        if (
            not isinstance(name, str)
            or not isinstance(resolved, int | float)
            or isinstance(resolved, bool)
        ):
            skipped += 1
            continue
        harness, _ = split_harness(name)
        cost = entry.get("cost")
        row = ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=float(resolved),
            harness=harness,
            run_date=entry.get("date") if isinstance(entry.get("date"), str) else None,
            cost_total=(
                float(cost)
                if isinstance(cost, int | float) and not isinstance(cost, bool)
                else None
            ),
            source=source,
            source_url=source_url,
        )
        # Duplicate display names (resubmissions) would violate the scores UNIQUE
        # constraint and abort the whole source — keep the best score, count the rest.
        prior = best.get(name)
        if prior is not None:
            skipped += 1
            if row.score <= prior.score:
                continue
        best[name] = row
    return list(best.values()), skipped
