"""LiveBench 2.0 from its own release files: client + parser (REQ-SRC-013, D-219).

LiveBench publishes each release as static files on its own site: `table.csv`, one row per model and one column per
suite, and `categories.json`, each category's columns. Its page computes the overall score in the browser and stores
none ("Overall -- mean of category averages"), so the parser computes it the same way: each category's average is
the mean of its columns, the overall is the mean of the categories, rounded to two places as the page rounds. That is
the board's own rule, not a weighting of ours. A row missing a category is skipped and counted.

Release 2026-10-14 (LiveBench 2.0) is pinned, as Datacurve's `v1.1` is: a new release is a code edit, and the night's
staleness line says when the pinned one grows old (D-188 clause 4). Rows are dated by the release. LiveBench publishes
no data licence; its public numbers are used under D-215, attributed to LiveBench with its link.
"""

from __future__ import annotations

import csv
import io
import json
import math
from typing import Any

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.board_tables import LIVEBENCH_RELEASE_DATE
from app.workflows.schema import ScoreRow

SOURCE_NAME = "livebench"
BENCHMARK = "LiveBench"
#: The page's overall is a mean of category averages, each the share of a suite's questions a model got right.
METRIC = "% correct"
HARNESS = "LiveBench"
SITE_URL = "https://livebench.ai/"
#: The pinned release, named once in `board_tables` (its credit and citation name it too).
RELEASE_DATE = LIVEBENCH_RELEASE_DATE
RELEASE = RELEASE_DATE.replace("-", "")
TABLE_URL = f"https://livebench.ai/data/{RELEASE}/table.csv"
CATEGORIES_URL = f"https://livebench.ai/data/{RELEASE}/categories.json"
_TIMEOUT_S = 60.0


class LiveBenchClient:
    """Production RawSource for one pinned LiveBench release (D-001): two public files, from the site's own host."""

    name = SOURCE_NAME
    url = TABLE_URL
    hosts: tuple[str, ...] = ("livebench.ai",)

    def fetch_raw(self) -> str:
        table = fetch_bounded(TABLE_URL, self.name, _TIMEOUT_S, hosts=self.hosts)
        categories_text = fetch_bounded(CATEGORIES_URL, self.name, _TIMEOUT_S, hosts=self.hosts)
        try:
            categories = json.loads(categories_text)
        except json.JSONDecodeError as exc:
            msg = f"{self.name}: categories.json is not valid JSON: {exc}"
            raise SourceError(msg) from exc
        return json.dumps({"table": table, "categories": categories})


def _cell(value: object) -> float | None:
    try:
        score = float(str(value).strip())
    except ValueError:
        return None
    return score if math.isfinite(score) and 0 <= score <= 100 else None


def _categories(release: dict[str, Any], source: str, columns: list[str]) -> dict[str, list[str]]:
    categories = release.get("categories")
    if not isinstance(categories, dict) or not categories:
        msg = f"{source}: the release names no categories"
        raise SourceError(msg)
    named: dict[str, list[str]] = {}
    for category, members in categories.items():
        if not isinstance(members, list) or not members or not all(isinstance(m, str) for m in members):
            msg = f"{source}: category {category!r} names no columns"
            raise SourceError(msg)
        missing = [m for m in members if m not in columns]
        if missing:
            msg = f"{source}: category {category!r} names columns the table lacks: {missing}"
            raise SourceError(msg)
        named[str(category)] = list(members)
    return named


def parse_livebench(raw: str, *, source: str = SOURCE_NAME) -> tuple[list[ScoreRow], int]:
    """Parse one release into a row a model at the mean of its category averages; returns (rows, skipped)."""
    try:
        release: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"{source}: the release is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    table = release.get("table") if isinstance(release, dict) else None
    if not isinstance(table, str):
        msg = f"{source}: the release holds no table"
        raise SourceError(msg)
    reader = csv.DictReader(io.StringIO(table))
    columns = list(reader.fieldnames or [])
    if "model" not in columns:
        msg = f"{source}: the table has no `model` column"
        raise SourceError(msg)
    categories = _categories(release, source, columns)
    rows: list[ScoreRow] = []
    skipped = 0
    for entry in reader:
        model = (entry.get("model") or "").strip()
        averages: list[float] = []
        for members in categories.values():
            cells = [_cell(entry.get(member)) for member in members]
            if any(cell is None for cell in cells):
                break
            averages.append(sum(cell for cell in cells if cell is not None) / len(cells))
        if not model or len(averages) != len(categories):
            skipped += 1
            continue
        rows.append(ScoreRow(
            raw_name=model,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=round(sum(averages) / len(averages), 2),
            harness=HARNESS,
            run_date=RELEASE_DATE,
            cost_total=None,
            source=source,
            source_url=SITE_URL,
        ))
    if not rows:
        msg = f"{source}: the release ranks no model"
        raise SourceError(msg)
    return rows, skipped
