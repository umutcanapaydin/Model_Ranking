"""Arena (LMArena) leaderboard source: client + parser (REQ-ING-007/-008, D-101).

Reads the OFFICIAL ``lmarena-ai/leaderboard-dataset`` (CC-BY-4.0) through the
documented Hugging Face datasets-server filter API — never the arena.ai site
(its ToS bans scraping; the dataset is the sanctioned path). Attribution is
REQUIRED and carried into every export (REQ-ING-008).

Shape (verified against the dataset card, 2026-08-11): subsets per arena
(``text``, ``vision``, …), splits ``latest``/``full``; text columns:
``model_name, organization, license, rating, rating_lower, rating_upper,
variance, vote_count, rank, category, leaderboard_publish_date``.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.clients.protocols import MAX_RESPONSE_BYTES, SourceError
from app.workflows.schema import ScoreRow

DATASET = "lmarena-ai/leaderboard-dataset"
ROWS_API = "https://datasets-server.huggingface.co/rows"
FILTER_API = "https://datasets-server.huggingface.co/filter"
# FIXPACK FP-M2-1/2 (live catches 2026-08-11): text/latest carries ALL category
# slices AND multiple leaderboard snapshots (21 259 rows) — the page-cap guard
# fired exactly as designed. FP-M2-2 corrections, verified against live rows:
#   * the overall board's category value is 'overall' (NOT 'full' — that fixture
#     value was invented in M2-W2 and never met live data: it filtered 0 rows);
#   * the filtered slice (386 rows) spans SEVERAL publish dates, so "best score
#     per model" could surface an OLD-but-higher rating as current. We therefore
#     keep only the NEWEST snapshot present (see parse_arena).
OVERALL_CATEGORY = "overall"
WHERE_OVERALL = "\"category\"='overall'"
BENCHMARK = "Arena text"
METRIC = "elo"
HARNESS = "arena-crowd"
ATTRIBUTION = "Arena leaderboard data © LMArena — lmarena-ai/leaderboard-dataset (CC-BY-4.0)"
PREFERRED_CATEGORY = OVERALL_CATEGORY  # the overall board; 20+ other slices exist
_PAGE = 100
_MAX_PAGES = 50  # safety valve: latest split is a few hundred rows
_TIMEOUT_S = 30.0
_RETRIES_429 = 3


def arena_source_url(config: str = "text", split: str = "latest") -> str:
    """Provenance for the surface we actually read.

    W-024: this named the FILTER endpoint long after that endpoint stopped serving this dataset.
    A citation pointing at a URL the code does not call is one nobody can follow.
    """
    return str(
        httpx.URL(ROWS_API, params={"dataset": DATASET, "config": config, "split": split})
    )


class ArenaClient:
    """Production RawSource for the Arena text leaderboard (D-001).

    fetch_raw paginates the documented filter API and returns ONE merged JSON
    document ``{"rows": [...], "num_rows_total": N}`` so the parser stays a
    pure function over a single payload.
    """

    name = "arena"

    def __init__(self, config: str = "text", split: str = "latest") -> None:
        # M2-closure carried debt, cleaned in M3-W3: the old `url=` parameter was
        # provenance-only while fetch_raw always used the module constants — a
        # misleading API. Provenance now derives from the same constants it uses.
        self.config = config
        self.split = split
        self.url = arena_source_url(config, split)

    def _get_page(self, endpoint: str, page: int, extra: dict[str, str]) -> dict[str, Any]:
        """One page with 429 backoff (FP-M2-1: HF rate-limited the live run)."""
        params: dict[str, str | int] = {
            "dataset": DATASET,
            "config": self.config,
            "split": self.split,
            "offset": page * _PAGE,
            "length": _PAGE,
            **extra,
        }
        last_exc: Exception | None = None
        for attempt in range(_RETRIES_429 + 1):
            try:
                # Streamed rather than fetched whole (M7 Stage-4.0 MINOR-4). Two reasons, and the
                # second is why this reads better than the version it replaces: the body is capped
                # WHILE it is read, so a hostile or broken upstream cannot make this process buffer
                # gigabytes; and the status and headers arrive BEFORE the body, so the 429 retry
                # below decides without paying for a response it is about to discard.
                with httpx.stream(
                    "GET",
                    endpoint,
                    params=params,
                    timeout=_TIMEOUT_S,
                    follow_redirects=True,
                ) as resp:
                    if resp.status_code == 429 and attempt < _RETRIES_429:
                        retry_after = resp.headers.get("Retry-After")
                        delay = (
                            float(retry_after)
                            if retry_after and retry_after.replace(".", "", 1).isdigit()
                            else float(2 ** (attempt + 1))
                        )
                        time.sleep(min(delay, 30.0))
                        continue
                    resp.raise_for_status()
                    body = bytearray()
                    for chunk in resp.iter_bytes():
                        body += chunk
                        if len(body) > MAX_RESPONSE_BYTES:
                            msg = (
                                f"arena: page {page} exceeded {MAX_RESPONSE_BYTES} bytes "
                                "and was cut off; the filter endpoint has changed shape"
                            )
                            raise SourceError(msg)
                payload = json.loads(bytes(body).decode("utf-8", "replace"))
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                break
            if not isinstance(payload, dict):
                last_exc = ValueError("payload is not an object")
                break
            return payload
        msg = f"arena fetch failed (page {page}): {last_exc}"
        raise SourceError(msg) from last_exc

    @staticmethod
    def _overall_prefix(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
        """The leading run of `overall` rows in one page, and whether the board ended inside it.

        The split is ordered by category — MEASURED on 2026-08-21, not assumed: `overall` occupies
        roughly the first 400 of 10,359 rows and `chinese` begins at ~400. So the board we want is
        a PREFIX, and reading past its end is downloading unrelated slices, which is the
        self-rate-limiting chain W-007 removed.
        """
        for index, entry in enumerate(rows):
            # The record is NESTED: this API wraps each one as {"row_idx": N, "row": {...}}, and
            # the category lives inside. Reading it off the outer object matched nothing, so the
            # prefix ended at row zero and every board came back empty — caught by the existing
            # client tests on the first run, which is what they are for.
            nested = entry.get("row")
            record: dict[str, Any] = nested if isinstance(nested, dict) else entry
            if record.get("category") != OVERALL_CATEGORY:
                return rows[:index], True
        return rows, False

    def _paginate(self, endpoint: str, extra: dict[str, str]) -> str:
        merged: list[dict[str, Any]] = []
        total: int | None = None
        for page in range(_MAX_PAGES):
            payload = self._get_page(endpoint, page, extra)
            rows = payload.get("rows")
            if not isinstance(rows, list):
                msg = f"arena API returned no rows list (page {page})"
                raise SourceError(msg)
            rows, board_ended = self._overall_prefix(rows)
            merged.extend(rows)
            if board_ended:
                break
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

    def fetch_raw(self) -> str:
        """Fetch the overall board as the ordered PREFIX of the split.

        **W-024, and it was never an outage.** For an entire milestone this source was recorded as
        "upstream down" on the strength of a 500 from the `filter` endpoint, and a user-facing
        surface shipped blind because of it. The dataset was healthy the whole time: `/is-valid`
        reports filter support, `/splits` lists `text/latest`, `/first-rows` returns rows carrying
        `category='overall'`, and `/rows` serves them. Only `filter` fails — and it fails **with no
        `where` clause at all**, so it was never our query.

        Reproducing a failure proves the failure is real. It proves nothing about its SCOPE.

        **This is not W-007's fallback returning.** W-007 removed an AUTOMATIC one: a filter failure
        silently began paginating everything, category after category, until the client
        rate-limited itself. This is a deliberate read of a different endpoint, under the same page
        valve, that STOPS at the first row outside the board — four or five requests, not a
        hundred. There is no fallback and no chain: if this fails, the source fails loudly and the
        artifact keeps its previous working set.

        Two guards stand behind the ordering assumption, because "the rows happen to be sorted" is
        not something upstream owes us: `parse_arena` filters by category again, and the source's
        `minimum_rows` floor turns a short read into a FAILED dependency instead of a quiet one.
        """
        return self._paginate(ROWS_API, {})


def parse_arena(
    raw: str,
    *,
    source: str = "arena",
    source_url: str = arena_source_url(),
) -> tuple[list[ScoreRow], int]:
    """Parse merged rows into Elo score records; returns (rows, skipped).

    Prefers the overall leaderboard slice (``category == "overall"``); when the
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

    # FP-M2-2: the split holds several leaderboard snapshots. Keep ONLY the newest
    # publish date present, so a stale-but-higher rating can never read as current.
    dates = [
        str(r.get("leaderboard_publish_date"))[:10]
        for r in working
        if isinstance(r.get("leaderboard_publish_date"), str)
    ]
    newest = max(dates) if dates else None
    if newest is not None:
        current = [r for r in working if str(r.get("leaderboard_publish_date", ""))[:10] == newest]
        working, dropped_snapshots = current, len(working) - len(current)
    else:
        dropped_snapshots = 0

    best: dict[str, ScoreRow] = {}
    skipped = dropped_wrappers + dropped_snapshots + len(rows_raw) - len(preferred or rows_raw)
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
