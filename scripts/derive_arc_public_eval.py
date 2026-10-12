#!/usr/bin/env python3
"""Derive each model setting's ARC-AGI-2 public-evaluation score from ARC Prize's MIT dataset (D-194, #265).

    PYTHONPATH=src .venv/bin/python scripts/derive_arc_public_eval.py --out data/arc-agi-2-public-eval.json

`arcprize/arc_agi_v2_public_eval` on Hugging Face (MIT) holds ARC Prize's own runs on the 120 public
evaluation tasks: one folder a model setting, one JSON file a task, and each test pair's two attempts
marked `correct`. 32 folders also carry a `results.json` whose `score` is the sum of the task scores. The
dataset has not changed since 2026-06-04, and scoring every folder reads about 4,300 files, so the scores
are derived here once, at a pinned revision, and committed (`data/arc-agi-2-public-eval.json`); the
build reads that file, and the contract test fails when the dataset moves on from the revision.

**The score**, as ARC Prize's `results.json` computes it: a test pair is solved when either attempt is
correct, a task scores the share of its pairs solved, and a setting scores the sum over the 120 tasks,
as a percentage. A task a setting did not run scores 0. A setting that ran fewer than `MIN_TASKS` is
left out: its score would mostly measure what it skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.clients.protocols import SourceError, bounded_get

DATASET = "arcprize/arc_agi_v2_public_eval"
API = f"https://huggingface.co/api/datasets/{DATASET}"
HOSTS = ("huggingface.co", ".hf.co")
TASKS = 120
#: 95 % of the tasks: a setting missing more is a partial run.
MIN_TASKS = 114
_TASK_FILE = re.compile(r"(?P<setting>[^/]+)/(?P<task>[0-9a-f]{8})\.json")


#: Hugging Face answers 429 past its anonymous rate; each wait is what it asks, at most this many times.
RETRIES = 30


def _get(url: str) -> bytes:
    for _ in range(RETRIES):
        answer = bounded_get(url, "arc_agi_2", 60.0, hosts=HOSTS)
        if answer.status != 429:
            return answer.body
        wait = answer.headers.get("retry-after", "")
        time.sleep(min(float(wait), 300.0) if wait.replace(".", "", 1).isdigit() else 60.0)
    msg = f"arc_agi_2: still 429 after {RETRIES} waits: {url}"
    raise SourceError(msg)


def task_score(attempts: Any) -> float:
    """The share of a task's test pairs solved by either attempt."""
    if not isinstance(attempts, list) or not attempts:
        return 0.0
    solved = 0
    for pair in attempts:
        if isinstance(pair, dict) and any(
            isinstance(pair.get(key), dict) and pair[key].get("correct") is True for key in ("attempt_1", "attempt_2")
        ):
            solved += 1
    return solved / len(attempts)


def _attempt_cost(attempt: object) -> float:
    """What one attempt cost, in USD, as its metadata records it; 0 when it records none."""
    meta = attempt.get("metadata") if isinstance(attempt, dict) else None
    cost = meta.get("cost") if isinstance(meta, dict) else None
    total = cost.get("total_cost") if isinstance(cost, dict) else None
    return float(total) if isinstance(total, int | float) and not isinstance(total, bool) else 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="derive_arc_public_eval")
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    info = json.loads(_get(API))
    revision = info["sha"]
    files = [s["rfilename"] for s in info["siblings"]]
    tasks: dict[str, list[str]] = {}
    for name in files:
        match = _TASK_FILE.fullmatch(name)
        if match:
            tasks.setdefault(match["setting"], []).append(name)
    resolve = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"

    def score(setting: str) -> tuple[str, dict[str, Any]]:
        paths = tasks[setting]
        bodies = [json.loads(_get(resolve + path)) for path in paths]
        solved = sum(task_score(body) for body in bodies)
        cost = sum(_attempt_cost(pair.get(key)) for body in bodies if isinstance(body, list)
                   for pair in body if isinstance(pair, dict) for key in ("attempt_1", "attempt_2"))
        return setting, {"tasks_run": len(paths), "solved": round(solved, 6), "score": round(100 * solved / TASKS, 4),
                         "cost_usd": round(cost, 4) if cost else None}

    settings = sorted(tasks)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        scored = dict(pool.map(score, settings))
    kept = {k: v for k, v in scored.items() if v["tasks_run"] >= MIN_TASKS}
    record = {
        "dataset": DATASET,
        "url": f"https://huggingface.co/datasets/{DATASET}",
        "revision": revision,
        "licence": "MIT",
        "publisher": "ARC Prize Foundation",
        "tasks": TASKS,
        "min_tasks": MIN_TASKS,
        "derived_by": "scripts/derive_arc_public_eval.py",
        "left_out_as_partial": sorted(k for k in scored if k not in kept),
        "settings": kept,
    }
    Path(args.out).write_text(json.dumps(record, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(f"{len(kept)} settings kept of {len(scored)} at {revision[:12]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
