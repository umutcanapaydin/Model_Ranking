"""Arena (LMArena) leaderboard source: client + parser (REQ-ING-007/-008, D-101).

Reads the OFFICIAL ``lmarena-ai/leaderboard-dataset`` (CC-BY-4.0) through the
documented Hugging Face datasets-server rows API — never the arena.ai site
(its ToS bans scraping; the dataset is the sanctioned path). Attribution is
REQUIRED and carried into every export (REQ-ING-008).

Shape (verified against the dataset card, 2026-08-11): subsets per arena
(``text``, ``vision``, …), splits ``latest``/``full``; text columns:
``model_name, organization, license, rating, rating_lower, rating_upper,
variance, vote_count, rank, category, leaderboard_publish_date``.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.clients.protocols import SourceError
from app.workflows.schema import ScoreRow

DATASET = "lmarena-ai/leaderboard-dataset"
ROWS_API = "https://datasets-server.huggingface.co/rows"
BENCHMARK = "Arena text"
METRIC = "elo"
HARNESS = "arena-crowd"
ATTRIBUTION = "Arena leaderboard data © LMArena — lmarena-ai/leaderboard-dataset (CC-BY-4.0)"
PREFERRED_CATEGORY = "full"  # overall leaderboard; other category slices exist
_PAGE = 100
_MAX_PAGES = 50  # safety valve: latest split is a few hundred rows
_TIMEOUT_S = 30.0


class ArenaClient:
    """Production RawSource for the Arena text leaderboard (D-001).

    fetch_raw paginates the documented rows API and returns ONE merged JSON
    document ``{"rows": [...], "num_rows_total": N}`` so the parser stays a
    pure function over a single payload.
    """

    name = "arena"

    def __init__(self, config: str = "text", split: str = "latest", url: str = ROWS_API) -> None:
        self.config = config
        self.split = split
        self.url = f"{url}?dataset={DATASET}&config={config}&split={split}"

    def fetch_raw(self) -> str:
        merged: list[dict[str, Any]] = []
        total: int | None = None
        for page in range(_MAX_PAGES):
            params: dict[str, str | int] = {
                "dataset": DATASET,
                "config": self.config,
                "split": self.split,
                "offset": page * _PAGE,
                "length": _PAGE,
            }
            try:
                resp = httpx.get(ROWS_API, params=params, timeout=_TIMEOUT_S, follow_redirects=True)
                resp.raise_for_status()
                payload = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                msg = f"arena fetch failed (page {page}): {exc}"
                raise SourceError(msg) from exc
            rows = payload.get("rows")
            if not isinstance(rows, list):
                msg = f"arena rows API returned no rows list (page {page})"
                raise SourceError(msg)
            merged.extend(rows)
            total = (
                payload.get("num_rows_total")
                if isinstance(payload.get("num_rows_total"), int)
                else total
            )
            if len(rows) < _PAGE or (total is not None and len(merged) >= total):
                break
        else:  # loop exhausted _MAX_PAGES without a break — never truncate silently
            msg = (
                f"arena fetch aborted: > {_MAX_PAGES * _PAGE} rows in {self.config}/{self.split}"
                " — raise _MAX_PAGES deliberately instead of truncating"
            )
            raise SourceError(msg)
        return json.dumps({"rows": merged, "num_rows_total": total})


def parse_arena(
    raw: str,
    *,
    source: str = "arena",
    source_url: str = f"{ROWS_API}?dataset={DATASET}&config=text&split=latest",
) -> tuple[list[ScoreRow], int]:
    """Parse merged rows into Elo score records; returns (rows, skipped).

    Prefers the overall leaderboard slice (``category == "full"``); when the
    dataset carries no such slice, all rows are used (tolerant, tested).
    Duplicate model names keep the best rating (M1 live-run doctrine).
    """
    try:
        payload: dict[str, Any] = json.loads(raw)
        wrapped = payload["rows"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        msg = f"arena payload malformed: {exc!r}"
        raise SourceError(msg) from exc
    if not isinstance(wrapped, list):
        msg = "arena payload malformed: rows is not a list"
        raise SourceError(msg)

    rows_raw: list[dict[str, Any]] = []
    dropped_wrappers = 0
    for w in wrapped:
        row = w.get("row") if isinstance(w, dict) else None
        if isinstance(row, dict):
            rows_raw.append(row)
        else:
            dropped_wrappers += 1  # counted, never silent (M2-W2 review)

    preferred = [r for r in rows_raw if r.get("category") == PREFERRED_CATEGORY]
    working = preferred or rows_raw

    best: dict[str, ScoreRow] = {}
    skipped = dropped_wrappers + len(rows_raw) - len(working)
    for entry in working:
        name = entry.get("model_name")
        rating = entry.get("rating")
        if (
            not isinstance(name, str)
            or not isinstance(rating, int | float)
            or isinstance(rating, bool)
        ):
            skipped += 1
            continue
        pub = entry.get("leaderboard_publish_date")
        row = ScoreRow(
            raw_name=name,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=float(rating),
            harness=HARNESS,
            run_date=str(pub)[:10] if isinstance(pub, str) and pub else None,
            cost_total=None,
            source=source,
            source_url=source_url,
        )
        prior = best.get(name)
        if prior is not None:
            skipped += 1
            if row.score <= prior.score:
                continue
        best[name] = row
    return list(best.values()), skipped
