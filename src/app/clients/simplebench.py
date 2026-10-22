"""SimpleBench from the leaderboard file its page loads: client + parser (REQ-SRC-013, D-219).

SimpleBench publishes its board as one script its page loads, `static/js/leaderboard-data.js`. Its `leaderboardData`
array holds one object per row: rank, model, AVG@5 score (as `"88.4%"`), organisation and the date the row was added.
The same file holds an open-ended board of three models (`openEndedData`) and the prices the page shows; neither is
this board, and neither is read. The human baselines carry no rank (`"-"`) and are not models: skipped and counted.

The file is read as text, never run: only the `leaderboardData` array, one flat object at a time, each matched field
by field, so a row of another shape is skipped and counted rather than guessed at. SimpleBench publishes no licence on
its site (its repository is MIT, for its code and public questions); its public numbers are used under D-215,
attributed to the SimpleBench team with its link. A row is dated by the day it was added.
"""

from __future__ import annotations

import math
import re

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import ScoreRow

SOURCE_NAME = "simplebench"
BENCHMARK = "SimpleBench"
METRIC = "% correct"
HARNESS = "SimpleBench (AVG@5)"
SITE_URL = "https://simple-bench.com/"
DATA_URL = "https://simple-bench.com/static/js/leaderboard-data.js"
_TIMEOUT_S = 60.0
_BOARD = re.compile(r"\bconst\s+leaderboardData\s*=\s*\[(?P<body>.*?)\n\s*\];", re.DOTALL)
_OBJECT = re.compile(r"\{[^{}]*\}")
_ROW = re.compile(
    r'\{\s*rank:\s*"(?P<rank>[^"]*)",\s*model:\s*"(?P<model>[^"]*)",\s*score:\s*"(?P<score>[^"]*)",'
    r'\s*organization:\s*"[^"]*",\s*dateAdded:\s*(?:"(?P<date>\d{4}-\d{2}-\d{2})"|null)\s*\}')
_PERCENT = re.compile(r"(?P<value>\d+(?:\.\d+)?)%")
#: The rank a row that is not a model (a human baseline) carries.
_UNRANKED = "-"


class SimpleBenchClient:
    """Production RawSource for SimpleBench's leaderboard file (D-001): one public file, from the site's own host."""

    name = SOURCE_NAME
    url = DATA_URL
    hosts: tuple[str, ...] = ("simple-bench.com",)

    def fetch_raw(self) -> str:
        return fetch_bounded(DATA_URL, self.name, _TIMEOUT_S, hosts=self.hosts)


def _score(text: str) -> float | None:
    found = _PERCENT.fullmatch(text.strip())
    if found is None:
        return None
    value = float(found.group("value"))
    return value if math.isfinite(value) and 0 <= value <= 100 else None


def parse_simplebench(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse the `leaderboardData` array into one row a ranked model; returns (rows, skipped).

    A row that is not a usable ranked score is skipped and counted; a file without the board fails the source.
    """
    board = _BOARD.search(raw)
    if board is None:
        msg = f"{source}: the file holds no `leaderboardData` array"
        raise SourceError(msg)
    rows: list[ScoreRow] = []
    seen: set[str] = set()
    skipped = 0
    for found in _OBJECT.finditer(board.group("body")):
        row = _ROW.fullmatch(found.group())
        model = row.group("model").strip() if row else ""
        score = _score(row.group("score")) if row else None
        if row is None or row.group("rank").strip() == _UNRANKED or not model or score is None or model in seen:
            skipped += 1
            continue
        seen.add(model)
        rows.append(ScoreRow(
            raw_name=model,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=score,
            harness=HARNESS,
            run_date=row.group("date"),
            cost_total=None,
            source=source,
            source_url=SITE_URL,
        ))
    if not rows:
        msg = f"{source}: the board ranks no model"
        raise SourceError(msg)
    return rows, skipped
