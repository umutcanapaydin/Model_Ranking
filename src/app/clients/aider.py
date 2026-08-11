"""Aider polyglot source: client + parser (REQ-ING-003, D-101).

Fetches ``polyglot_leaderboard.yml`` from the Aider repository (Apache-2.0;
documented raw-data endpoint — NOT scraping). Known caveat: the leaderboard
stalled around Nov 2025 — staleness is surfaced as a source-health flag,
never silently ignored (REQ-ING-003).
"""

from __future__ import annotations

import datetime as dt

import httpx
import yaml

from app.clients.protocols import SourceError
from app.workflows.schema import ScoreRow

AIDER_URL = (
    "https://raw.githubusercontent.com/Aider-AI/aider/main/"
    "aider/website/_data/polyglot_leaderboard.yml"
)
BENCHMARK = "Aider polyglot"
METRIC = "% pass_rate_2"
HARNESS = "aider"
STALE_AFTER_DAYS = 90
_TIMEOUT_S = 30.0


class AiderClient:
    """Production RawSource for the Aider polyglot leaderboard (D-001)."""

    name = "aider"

    def __init__(self, url: str = AIDER_URL) -> None:
        self.url = url

    def fetch_raw(self) -> str:
        try:
            resp = httpx.get(self.url, timeout=_TIMEOUT_S, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            msg = f"aider fetch failed: {exc}"
            raise SourceError(msg) from exc
        return resp.text


def _as_date_str(v: object) -> str | None:
    """Normalize to a VALIDATED ISO date string, or None (never store garbage)."""
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, str) and v:
        try:
            return dt.date.fromisoformat(v[:10]).isoformat()
        except ValueError:
            return None
    return None


def parse_polyglot(
    raw: str, *, source: str = "aider", source_url: str = AIDER_URL
) -> tuple[list[ScoreRow], int]:
    """Parse the polyglot YAML into score rows; entries without a usable
    model name or pass_rate_2 are skipped (never stored as zero)."""
    try:
        entries = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        msg = f"aider payload is not valid YAML: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(entries, list):
        msg = "aider payload is not a list of runs"
        raise SourceError(msg)

    best: dict[str, ScoreRow] = {}
    skipped = 0
    for entry in entries:
        if not isinstance(entry, dict):
            skipped += 1
            continue
        name = entry.get("model")
        rate = entry.get("pass_rate_2")
        if not isinstance(name, str) or not isinstance(rate, int | float) or isinstance(rate, bool):
            skipped += 1
            continue
        cost = entry.get("total_cost")
        row = ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=float(rate),
            harness=HARNESS,
            run_date=_as_date_str(entry.get("date")),
            cost_total=(
                float(cost)
                if isinstance(cost, int | float) and not isinstance(cost, bool) and cost > 0
                else None
            ),
            source=source,
            source_url=source_url,
        )
        # The leaderboard lists the SAME model across multiple runs (dates/edit
        # formats) — found by the first LIVE run, 2026-08-10. Keep the best
        # score, count the rest (mirrors the swebench dedupe rule).
        prior = best.get(name)
        if prior is not None:
            skipped += 1
            if row.score <= prior.score:
                continue
        best[name] = row
    return list(best.values()), skipped


def staleness_flag(rows: list[ScoreRow], observed_at: str) -> str | None:
    """REQ-ING-003: report staleness relative to the run stamp, deterministically.

    Returns a human-readable flag when the newest run_date is older than
    STALE_AFTER_DAYS at ``observed_at``, else None.
    """
    dates = [r.run_date for r in rows if r.run_date]
    if not dates:
        return "stale: no run dates present"
    latest = max(dates)
    try:
        latest_d = dt.date.fromisoformat(latest)
        ref_d = dt.date.fromisoformat(observed_at[:10])
    except ValueError:
        return f"stale-check inconclusive: unparseable dates (latest={latest!r})"
    age = (ref_d - latest_d).days
    if age > STALE_AFTER_DAYS:
        return f"stale: latest run {latest} is {age} days old (> {STALE_AFTER_DAYS})"
    return None
