"""LiveBench 2.0 from its own release files: client + parser (REQ-SRC-013, D-219).

LiveBench publishes each release as static files on its own site: `table.csv`, one row per model and one column per
suite, and `categories.json`, each category's columns. Its page computes the overall score in the browser and stores
none ("Overall -- mean of category averages"), so the parser computes it the same way: each category's average is
the mean of its columns, the overall is the mean of the categories, rounded to two places as the page rounds. That is
the board's own rule, not a weighting of ours. A row missing a category is skipped and counted.

Each night the client reads the newest release the site serves (D-250): the page's own script lists its releases
(`["20261014","20261025","20261106"]` on 2026-11-10), the newest is taken, never one older than `RELEASE_FLOOR` (the
last read by hand), and its two files are fetched from the same host. A page that names no such release fails the
source that night, and the refresh carries the last good rows (D-156). Rows are dated by the release read. From
release 2026-10-25 `categories.json` also carries `_overall_weights`, and the page's overall is the weighted mean of
the category averages; the parser computes it the same way. LiveBench publishes no data licence; its public numbers
are used under D-215, attributed to LiveBench with its link.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import math
import re
from typing import Any

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import ScoreRow

SOURCE_NAME = "livebench"
BENCHMARK = "LiveBench"
#: The page's overall is a mean of category averages, each the share of a suite's questions a model got right.
METRIC = "% correct"
HARNESS = "LiveBench"
SITE_URL = "https://livebench.ai/"
#: D-250 clause 1: the newest release is read, never one older than the last read by hand.
RELEASE_FLOOR = "2026-10-14"
#: The key of `categories.json` that weights the overall (D-250 clause 2), never a category.
WEIGHTS_KEY = "_overall_weights"
_TIMEOUT_S = 60.0
#: The page's own script, as its HTML loads it (`./static/js/main.<hash>.js`). No `<script[^>]*` prefix: that
#: scan is quadratic in a page of many unclosed openings (the security delta's M23), and the path alone is unique.
_SCRIPT = re.compile(r'\ssrc="(?:\./|/)?(static/js/main\.[0-9a-f]+\.js)"')
#: The script's release list: an array of quoted eight-digit dates.
_RELEASES = re.compile(r'\[\s*"\d{8}"(?:\s*,\s*"\d{8}")*\s*\]')


def release_url(release: str, name: str) -> str:
    """A file of one release, on the site's own host; `release` is its date, `YYYY-MM-DD`."""
    return f"https://livebench.ai/data/{release.replace('-', '')}/{name}"


def newest_release(script: str, *, source: str = SOURCE_NAME) -> str:
    """The newest release the page's script lists, as `YYYY-MM-DD`, never older than the floor (D-250 clause 1)."""
    named: set[str] = set()
    for array in _RELEASES.findall(script):
        for stamp in re.findall(r"\d{8}", array):
            try:
                named.add(dt.datetime.strptime(stamp, "%Y%m%d").date().isoformat())
            except ValueError:
                continue
    usable = [release for release in named if release >= RELEASE_FLOOR]
    if not usable:
        msg = f"{source}: the page names no release on or after {RELEASE_FLOOR} (named: {sorted(named)})"
        raise SourceError(msg)
    return max(usable)


class LiveBenchClient:
    """Production RawSource for LiveBench's newest release (D-001, D-250): the page, its script, then two public
    files of the release it names, every one from the site's own host."""

    name = SOURCE_NAME
    url = SITE_URL
    hosts: tuple[str, ...] = ("livebench.ai",)

    def fetch_raw(self) -> str:
        page = fetch_bounded(SITE_URL, self.name, _TIMEOUT_S, hosts=self.hosts)
        found = _SCRIPT.search(page)
        if found is None:
            msg = f"{self.name}: the page loads no script that names its releases"
            raise SourceError(msg)
        script = fetch_bounded(SITE_URL + found.group(1), self.name, _TIMEOUT_S, hosts=self.hosts)
        release = newest_release(script, source=self.name)
        table = fetch_bounded(release_url(release, "table.csv"), self.name, _TIMEOUT_S, hosts=self.hosts)
        categories_text = fetch_bounded(release_url(release, "categories.json"), self.name, _TIMEOUT_S,
                                        hosts=self.hosts)
        # `RecursionError` from a file nested past the limit is bad input, not a builder bug: it fails this optional
        # source, never the night (D-121; the queue-1021 integration review's M2).
        try:
            return json.dumps({"release": release, "table": table, "categories": json.loads(categories_text)})
        except (ValueError, RecursionError) as exc:
            msg = f"{self.name}: categories.json is not valid JSON: {exc}"
            raise SourceError(msg) from exc


def _cell(value: object) -> float | None:
    try:
        score = float(str(value).strip())
    except ValueError:
        return None
    return score if math.isfinite(score) and 0 <= score <= 100 else None


def _release_date(release: dict[str, Any], source: str) -> str:
    """The release's date, `YYYY-MM-DD`: every row is dated by it (D-250 clause 1)."""
    stamp = release.get("release")
    try:
        if not isinstance(stamp, str) or dt.date.fromisoformat(stamp).isoformat() != stamp:
            raise ValueError(stamp)
    except ValueError:
        msg = f"{source}: the release names no date (`release`: {stamp!r})"
        raise SourceError(msg) from None
    return stamp


def _weights(categories: dict[str, Any], source: str) -> dict[str, float]:
    """Each category's weight in the overall: the release's own where it names one, else 1 (D-250 clause 2).

    The page accepts a weight only for a named category, finite and above zero; any other entry is a format this
    parser does not know, so it fails the source rather than guess.
    """
    stated = categories.get(WEIGHTS_KEY, {})
    if not isinstance(stated, dict):
        msg = f"{source}: {WEIGHTS_KEY} is not a map of category to weight"
        raise SourceError(msg)
    weights = {category: 1.0 for category in categories if category != WEIGHTS_KEY}
    for category, weight in stated.items():
        if (category not in weights or isinstance(weight, bool) or not isinstance(weight, int | float)
                or not math.isfinite(weight) or weight <= 0):
            msg = f"{source}: {WEIGHTS_KEY} weights {category!r} at {weight!r}, which the page would not use"
            raise SourceError(msg)
        weights[category] = float(weight)
    return weights


def _categories(release: dict[str, Any], source: str, columns: list[str]) -> dict[str, list[str]]:
    categories = release.get("categories")
    if not isinstance(categories, dict) or not [c for c in categories if c != WEIGHTS_KEY]:
        msg = f"{source}: the release names no categories"
        raise SourceError(msg)
    named: dict[str, list[str]] = {}
    for category, members in categories.items():
        if category == WEIGHTS_KEY:
            continue
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
    """Parse one release into a row a model at the weighted mean of its category averages; returns (rows, skipped)."""
    try:
        release: Any = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        msg = f"{source}: the release is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    table = release.get("table") if isinstance(release, dict) else None
    if not isinstance(table, str):
        msg = f"{source}: the release holds no table"
        raise SourceError(msg)
    # `csv.Error` (a field past csv's limit, a NUL) is bad input, not a builder bug, as `epoch_board` rules: it
    # fails this optional source, never the night (D-121; the queue-1021 integration review's M2).
    try:
        reader = csv.DictReader(io.StringIO(table))
        columns = list(reader.fieldnames or [])
        entries = list(reader)
    except csv.Error as exc:
        msg = f"{source}: the table is malformed CSV: {exc}"
        raise SourceError(msg) from exc
    if "model" not in columns:
        msg = f"{source}: the table has no `model` column"
        raise SourceError(msg)
    run_date = _release_date(release, source)
    categories = _categories(release, source, columns)
    weights = _weights(release["categories"], source)
    rows: list[ScoreRow] = []
    skipped = 0
    for entry in entries:
        model = (entry.get("model") or "").strip()
        weighted: list[tuple[float, float]] = []
        for category, members in categories.items():
            cells = [_cell(entry.get(member)) for member in members]
            if any(cell is None for cell in cells):
                break
            weighted.append((sum(cell for cell in cells if cell is not None) / len(cells), weights[category]))
        if not model or len(weighted) != len(categories):
            skipped += 1
            continue
        rows.append(ScoreRow(
            raw_name=model,
            benchmark=BENCHMARK,
            metric=METRIC,
            score=round(sum(average * weight for average, weight in weighted) / sum(w for _, w in weighted), 2),
            harness=HARNESS,
            run_date=run_date,
            cost_total=None,
            source=source,
            source_url=SITE_URL,
        ))
    if not rows:
        msg = f"{source}: the release ranks no model"
        raise SourceError(msg)
    return rows, skipped
