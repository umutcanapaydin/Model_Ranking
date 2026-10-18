"""Terminal-Bench 4.0 from its leaderboard repository: client + parser (REQ-SRC-012, D-194).

TB 4.0's official leaderboard is defined and kept in `harbor-framework/terminal-bench` (Apache-2.0):
`leaderboard/leaderboard.yaml` names the board, and each submission is one JSON file under
`leaderboard/submissions/`, with its model, agent, reasoning effort, run date and accuracy over 330
trials. It replaces Epoch's copy of the TB 2.0 leaderboard, which states no licence (#265).

TB 2.0's raw submissions on Hugging Face are Apache-2.0 too, and are not read: they keep submissions the
official board took down for cheating, and trials it rescored to zero (tbench.ai's "leaderboard integrity
update"), so rebuilding the board from them would serve scores its maintainers withdrew.

The client lists the directory through GitHub's contents API and reads each file from the repository's
own raw path; a listing that points anywhere else is refused (#25's rule for every hop). It hands the
parser one JSON list of `{"file", "body"}`, so the build's one-string `RawSource` holds.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any, TypeGuard

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import EFFORT_LEVELS, ScoreRow

SOURCE_NAME = "terminalbench_4"
BENCHMARK = "Terminal-Bench 4.0"
METRIC = "% resolved"
REPOSITORY = "https://github.com/harbor-framework/terminal-bench"
LISTING_URL = "https://api.github.com/repos/harbor-framework/terminal-bench/contents/leaderboard/submissions"
#: A submission file's path, as the request will send it: httpx removes dot segments first, so a prefix test
#: on the listed string let `..` out of the repository (the #265 review's M2).
_SUBMISSION_PATH = re.compile(r"/harbor-framework/terminal-bench/[A-Za-z0-9._-]+/leaderboard/submissions/[A-Za-z0-9._-]+\.json")
_TIMEOUT_S = 30.0
#: The board had 21 submissions on 2026-10-13. Ten times that is a shape change, not a busy month.
MAX_SUBMISSIONS = 250
#: Run efforts the schema holds; `none` (no reasoning) and no effort are both stored as unspecified.
_NO_EFFORT = frozenset({"", "none"})


class TerminalBench4Client:
    """Production RawSource for TB 4.0's leaderboard submissions (D-001)."""

    name = SOURCE_NAME
    url = LISTING_URL
    hosts: tuple[str, ...] = ("api.github.com", "raw.githubusercontent.com")

    def fetch_raw(self) -> str:
        try:
            listing: Any = json.loads(fetch_bounded(LISTING_URL, self.name, _TIMEOUT_S, hosts=self.hosts))
        except json.JSONDecodeError as exc:
            msg = f"{self.name}: the submissions listing is not JSON: {exc}"
            raise SourceError(msg) from exc
        if not isinstance(listing, list):
            msg = f"{self.name}: the submissions listing is not a list"
            raise SourceError(msg)
        files = [entry for entry in listing if isinstance(entry, dict) and entry.get("type") == "file"
                 and str(entry.get("name", "")).endswith(".json")]
        if len(files) > MAX_SUBMISSIONS:
            msg = f"{self.name}: {len(files)} submissions, more than {MAX_SUBMISSIONS}; the board changed shape"
            raise SourceError(msg)
        bodies = []
        for entry in files:
            link = entry.get("download_url")
            if not _in_submissions(link):
                msg = f"{self.name}: a listed file points outside the repository: {link!r}"
                raise SourceError(msg)
            bodies.append({"file": entry["name"], "body": fetch_bounded(link, self.name, _TIMEOUT_S,
                                                                         hosts=self.hosts)})
        return json.dumps(bodies)


def _in_submissions(link: object) -> TypeGuard[str]:
    """Whether ``link`` reads a file in the repository's submissions directory, once normalised."""
    import httpx

    if not isinstance(link, str):
        return False
    try:
        url = httpx.URL(link)
    except (httpx.InvalidURL, ValueError):
        return False
    # The request sends the raw path, so the raw path is what is judged: no percent-encoding at all (#326).
    return (url.scheme == "https" and url.host == "raw.githubusercontent.com"
            and b"%" not in url.raw_path and _SUBMISSION_PATH.fullmatch(url.path) is not None)


def _accuracy(value: object) -> float | None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        return None
    score = float(value)
    return score if math.isfinite(score) and 0.0 <= score <= 100.0 else None


def _row(submission: object, *, source: str, source_url: str) -> ScoreRow | None:
    """One submission as a score row, or None when it is not one."""
    if not isinstance(submission, dict):
        return None
    run, about, metrics = (submission.get(key) for key in ("source_filter", "metadata", "metrics"))
    if not isinstance(run, dict) or not isinstance(about, dict) or not isinstance(metrics, dict):
        return None
    model, agent = run.get("model_name"), run.get("agent")
    score = _accuracy(metrics.get("accuracy"))
    if not isinstance(model, str) or not model.strip() or not isinstance(agent, str) or not agent.strip():
        return None
    if score is None:
        return None
    effort = run.get("reasoning_effort") or about.get("reasoning_effort") or ""
    effort = effort.strip().lower() if isinstance(effort, str) else ""
    if effort not in _NO_EFFORT and effort not in EFFORT_LEVELS:
        return None  # an effort the schema does not hold would fail the whole source at the store
    cost = metrics.get("total_cost_usd")
    date = about.get("date")
    return ScoreRow(
        raw_name=model.strip(),
        benchmark=BENCHMARK,
        metric=METRIC,
        score=score,
        harness=agent.strip(),
        run_date=date if isinstance(date, str) else None,
        cost_total=float(cost) if isinstance(cost, int | float) and not isinstance(cost, bool) else None,
        source=source,
        source_url=source_url,
        effort=None if effort in _NO_EFFORT else effort,
    )


def parse_terminalbench_4(raw: str, *, source: str = SOURCE_NAME, source_url: str = LISTING_URL,
                          ) -> tuple[list[ScoreRow], int]:
    """Parse the client's list of submission files; returns (rows, skipped).

    One row per model, agent and effort, the better accuracy kept; a file that is not a submission is
    skipped and counted, as is one whose effort the schema does not hold.
    """
    try:
        entries: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"{source}: payload is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(entries, list):
        msg = f"{source}: payload is not a list of submission files"
        raise SourceError(msg)
    best: dict[tuple[str, str, str | None], ScoreRow] = {}
    skipped = 0
    for entry in entries:
        body = entry.get("body") if isinstance(entry, dict) else None
        try:
            submission = json.loads(body) if isinstance(body, str) else None
        except json.JSONDecodeError:
            submission = None
        row = _row(submission, source=source, source_url=source_url)
        if row is None:
            skipped += 1
            continue
        key = (row.raw_name, row.harness, row.effort)
        if key in best:
            skipped += 1
            if row.score <= best[key].score:
                continue
        best[key] = row
    return list(best.values()), skipped
