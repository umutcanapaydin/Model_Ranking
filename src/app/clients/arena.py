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
import math
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.clients.protocols import SourceError, bounded_get
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
PREFERRED_CATEGORY = OVERALL_CATEGORY  # the overall board; the other slices: arena_slices.py


@dataclass(frozen=True)
class ArenaBoard:
    """One config of the dataset, read as its own source.

    **The dataset carries 22 boards and this project read one of them for twelve milestones.**
    They are configs of the SAME dataset under the SAME CC-BY-4.0 grant through the SAME
    documented endpoint, with byte-identical columns — verified against `document` and
    `text_factuality` on 2026-09-18, both carrying `category: overall` exactly as `text` does.
    Adding one is a row in this table, not a client.

    `id` is the `scores.source` value and is load-bearing: `CategorySpec.primary_source` names it,
    and `build.py` maps a failed source to the surfaces that go silent. **`text` keeps the id
    `arena`** because rows carrying that source are already in every built artifact and renaming it
    would orphan them.
    """

    id: str
    config: str
    benchmark: str
    minimum_rows: int
    """Floor below which a technically-successful fetch is a FAILED dependency.

    Sized per board and NOT copied from `text`'s 250: `document`'s whole `latest` split is 44 rows.
    A floor borrowed from a bigger board fails every day; a floor of 1 catches nothing (W-024).
    """


ARENA_BOARDS: dict[str, ArenaBoard] = {
    "text": ArenaBoard("arena", "text", BENCHMARK, 250),
    # Which model is best with documents. 44 rows in the whole `latest` split, ~40 in the overall
    # board; 25 is below any real day and far above a truncation.
    "document": ArenaBoard("arena_document", "document", "Arena document", 25),
    # Which model makes things up least. The split is large (3,582 rows across slices) but the
    # overall board is the same order of size as the others.
    "text_factuality": ArenaBoard("arena_factuality", "text_factuality", "Arena factuality", 25),
    # ── M15-W3: the three boards the W1 survey said the engine can actually rank ───────────────
    #
    # Measured, not chosen: `docs/research/m15-board-survey-2026-09-21.md` counted the models on
    # every one of the dataset's 22 boards that reconcile to the registry AND carry a price, which
    # is the only population this engine can recommend from. Everything else it found was refused
    # here — every image and video board ranks ZERO (priced per image), and the `*_style_control`
    # boards are the same boards with style effects controlled for, which is a second answer to one
    # question rather than a new one.
    "vision": ArenaBoard("arena_vision", "vision", "Arena vision", 60),
    # 152 rows, 41 rankable. 60 is well below any real day for a board this size.
    "search": ArenaBoard("arena_search", "search", "Arena search", 20),
    # 34 rows, 25 rankable; the whole board is small, so the floor is too (W-024's lesson both ways).
    "search_factuality": ArenaBoard(
        "arena_search_factuality", "search_factuality", "Arena search factuality", 20
    ),
}
_PAGE = 100
#: The ratings an Arena Elo board can plausibly carry; anything outside is refused and counted.
ELO_BAND = (0.0, 5000.0)
_MAX_PAGES = 50  # safety valve: latest split is a few hundred rows
_TIMEOUT_S = 30.0
#: REQ-GRD-002 / W-050. Each PAGE is capped at `MAX_RESPONSE_BYTES`, and until now nothing capped
#: the total: fifty full pages accumulate into one list and are then copied by `json.dumps`, which
#: a hostile upstream can turn into gigabytes of live objects on the owner's laptop, unattended,
#: every twelve hours. A page count is not a size bound.
#:
#: 5,000 rows against a board that carries ~394 is a twelve-fold margin, and the split it reads is
#: 10,359 rows — so this also stops a reordered split from paging the whole thing in.
#: 2,000 and NOT 5,000: `_MAX_PAGES * _PAGE` is exactly 5,000, so a limit set there fires at the
#: same instant as the page cap and never actually runs — measured, the page cap's message won and
#: this one was unreachable. A bound that coincides with another bound is not a bound.
_MAX_MERGED_ROWS = 2_000
_RETRIES_429 = 3


def arena_source_url(config: str = "text", split: str = "latest") -> str:
    """Provenance for the surface we actually read.

    W-024: this named the FILTER endpoint long after that endpoint stopped serving this dataset.
    A citation pointing at a URL the code does not call is one nobody can follow.
    """
    return str(httpx.URL(ROWS_API, params={"dataset": DATASET, "config": config, "split": split}))


class ArenaClient:
    """Production RawSource for the Arena text leaderboard (D-001).

    fetch_raw paginates the documented filter API and returns ONE merged JSON
    document ``{"rows": [...], "num_rows_total": N}`` so the parser stays a
    pure function over a single payload.
    """

    name = "arena"
    #: Where a page fetch may go (#25): the datasets-server's own host, no other.
    hosts: tuple[str, ...] = ("datasets-server.huggingface.co",)

    def __init__(self, config: str = "text", split: str = "latest") -> None:
        # M2-closure carried debt, cleaned in M3-W3: the old `url=` parameter was
        # provenance-only while fetch_raw always used the module constants — a
        # misleading API. Provenance now derives from the same constants it uses.
        #
        # M14-W2: the board decides `name` and `benchmark`, and `name` becomes an INSTANCE
        # attribute shadowing the class one. The class attribute stays so that anything reading
        # `ArenaClient.name` without an instance still sees the original source id.
        #
        # An unknown config is refused rather than defaulted. Defaulting it would ingest the
        # `document` board under the `arena` source id and silently merge two boards' Elo into one
        # surface — different scales, one ranking, which is the comparison D-105 forbids.
        if config not in ARENA_BOARDS:
            msg = (
                f"arena: no board registered for config {config!r}; "
                f"known boards: {sorted(ARENA_BOARDS)}"
            )
            raise SourceError(msg)
        self.board = ARENA_BOARDS[config]
        self.name = self.board.id
        self.benchmark = self.board.benchmark
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
            # Through the one bounded fetch (#25): the body capped while it is read (M7 Stage-4.0
            # MINOR-4), every hop `https` to the datasets-server only, and a deadline over the
            # whole page. A 429 comes back as an answer rather than an error, so the retry below
            # decides on its status and headers.
            try:
                answer = bounded_get(endpoint, self.name, _TIMEOUT_S,
                                     {k: str(v) for k, v in params.items()}, hosts=self.hosts)
            except SourceError as exc:
                last_exc = exc
                break
            if answer.status == 429 and attempt < _RETRIES_429:
                retry_after = answer.headers.get("retry-after")
                delay = (
                    float(retry_after)
                    if retry_after and retry_after.replace(".", "", 1).isdigit()
                    else float(2 ** (attempt + 1))
                )
                time.sleep(min(delay, 30.0))
                continue
            if answer.status == 429:
                last_exc = SourceError("429 Too Many Requests, after every retry")
                break
            try:
                payload = json.loads(answer.body.decode("utf-8", "replace"))
            except ValueError as exc:
                last_exc = exc
                break
            if not isinstance(payload, dict):
                last_exc = ValueError("payload is not an object")
                break
            return payload
        msg = f"arena fetch failed (page {page}): {last_exc}"
        raise SourceError(msg) from last_exc

    @staticmethod
    def _overall_prefix(rows: list[Any]) -> tuple[list[Any], bool]:
        """The leading run of `overall` rows in one page, and whether the board ended inside it.

        Typed `list[Any]`, deliberately. These rows are parsed JSON from an endpoint on the
        internet, so `list[dict[str, Any]]` is an assertion about the upstream rather than a fact
        about the value — and annotating it that way made mypy call the isinstance guard below
        UNREACHABLE, which is how a type hint talks a guard out of existing.

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
            if not isinstance(entry, dict):
                # `parse_arena` guards this and the prefix scan did not, so a payload of
                # `{"rows": ["x"]}` raised AttributeError — not a SourceError, so `build.py`
                # deliberately re-raises it and the whole unattended cycle died on a traceback.
                # A hostile or broken upstream is a BAD INPUT, and a bad input ends this source.
                msg = f"{OVERALL_CATEGORY}: a row in the payload is not an object"
                raise SourceError(msg)
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
            if len(merged) > _MAX_MERGED_ROWS:
                msg = (
                    f"arena fetch aborted: more than {_MAX_MERGED_ROWS} rows in the overall board "
                    f"of {self.config}/{self.split} — a board this size is a shape change, and "
                    "accumulating it unattended is how one upstream fills this machine"
                )
                raise SourceError(msg)
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
    benchmark: str = BENCHMARK,
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

    rows, refused = score_rows(working, source=source, source_url=source_url, benchmark=benchmark)
    skipped = dropped_wrappers + dropped_snapshots + len(rows_raw) - len(preferred or rows_raw)
    return rows, skipped + refused


def score_rows(
    entries: list[dict[str, Any]], *, source: str, source_url: str, benchmark: str
) -> tuple[list[ScoreRow], int]:
    """One board's records as Elo score rows; returns (rows, refused).

    Shared by `parse_arena` and the category slices (`arena_slices.py`, M17-W2), so a slice is held
    to exactly the rules the `overall` board is: a malformed or out-of-band rating is refused and
    counted, and a duplicate name keeps its best rating and counts the other.
    """
    best: dict[str, ScoreRow] = {}
    skipped = 0
    for entry in entries:
        name = entry.get("model_name")
        rating = entry.get("rating")
        # M15 closure security seat, MINOR-1: `json.loads` accepts `Infinity`, and one such rating
        # made its surface answer 500 while /health still said servable. Refused like any other
        # malformed row, and COUNTED as one (M2's rule), never silently stored.
        if (
            not isinstance(name, str)
            or not isinstance(rating, int | float)
            or isinstance(rating, bool)
            or not math.isfinite(rating)
            # W4 review MINOR-4: a finite 1e308 would be served as the leader. Every Arena board
            # is an Elo board, and a real rating sits in the low thousands.
            or not ELO_BAND[0] < rating < ELO_BAND[1]
        ):
            skipped += 1
            continue
        pub = entry.get("leaderboard_publish_date")
        row = ScoreRow(
            raw_name=name,
            benchmark=benchmark,
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


class ArenaVisionClient(ArenaClient):
    """The `vision` board: which model reads a screenshot, a photo or a scanned page best."""

    name = "arena_vision"

    def __init__(self, split: str = "latest") -> None:
        super().__init__(config="vision", split=split)


class ArenaSearchClient(ArenaClient):
    """The `search` board: which model answers best when it looks things up."""

    name = "arena_search"

    def __init__(self, split: str = "latest") -> None:
        super().__init__(config="search", split=split)


class ArenaSearchFactualityClient(ArenaClient):
    """The `search_factuality` board: which model gets its facts right when it looks them up."""

    name = "arena_search_factuality"

    def __init__(self, split: str = "latest") -> None:
        super().__init__(config="search_factuality", split=split)


class ArenaDocumentClient(ArenaClient):
    """The `document` board: which model is best with documents.

    A named subclass and not a lambda, because `test_the_registry_names_nothing_that_does_not_exist`
    checks that every registered source names a class that exists in the tree — a guard against a
    client being deleted while its registry row lingers. A lambda has no name to check, so
    registering one would quietly retire that guard for these sources.
    """

    name = "arena_document"  # class level too: a class-level read must not see "arena" (m3)

    def __init__(self, split: str = "latest") -> None:
        super().__init__(config="document", split=split)


class ArenaFactualityClient(ArenaClient):
    """The `text_factuality` board: which model makes things up least."""

    name = "arena_factuality"

    def __init__(self, split: str = "latest") -> None:
        super().__init__(config="text_factuality", split=split)
