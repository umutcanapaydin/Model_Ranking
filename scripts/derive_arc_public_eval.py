#!/usr/bin/env python3
"""Derive each model setting's ARC-AGI-2 public-evaluation score from ARC Prize's MIT dataset (D-194, #265).

    PYTHONPATH=src .venv/bin/python scripts/derive_arc_public_eval.py --out data/arc-agi-2-public-eval.json

`arcprize/arc_agi_v2_public_eval` on Hugging Face (MIT) holds ARC Prize's own runs on the 120 public
evaluation tasks: one folder a model setting, one JSON file a task, and each test pair's two attempts with
their answer grid. 32 folders also carry a `results.json` whose `score` is the sum of the task scores. The
dataset has not changed since 2026-06-04, and scoring every folder reads about 4,300 files, so the scores
are derived here once, at a pinned revision, and committed (`data/arc-agi-2-public-eval.json`); the
build reads that file, and the contract test fails when the dataset moves on from the revision.

**The score**, as ARC Prize's `results.json` computes it: a test pair is solved when either attempt is
correct, a task scores the share of its pairs solved, and a setting scores the sum over the 120 tasks,
as a percentage. A task a setting did not run scores 0. A setting that ran fewer than `MIN_TASKS` is
left out: its score would mostly measure what it skipped.

**An attempt ARC Prize marked** `correct: true` or `false` keeps its mark. **One it left unmarked**
(`null`, whole settings such as GPT-5 Pro and Claude Sonnet 4.5; the #265 review's B1) is scored by
comparing its answer with the solution of its own `metadata.pair_index`, from the `arcprize/ARC-AGI-2`
repository (Apache-2.0) at `SOLUTIONS_COMMIT`; read as wrong, those settings were served at 0. ARC Prize last
changed those solutions on 2025-05-15, removing the first test pair of five tasks, so a setting with an
unmarked attempt run before then would be compared with solutions it never answered: it is left out
(`left_out_as_predating_solutions`; round 2's N1). The same comparison is run on every marked attempt,
and the record names each attempt where it disagrees with ARC Prize's mark. Each setting is dated by its
latest attempt's `start_timestamp`.
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
SOLUTIONS = "arcprize/ARC-AGI-2"
#: The solutions' commit, pinned: a later change to the task set must not re-score the unmarked settings.
SOLUTIONS_COMMIT = "f3283f727488ad98fe575ea6a5ac981e4a188e49"
#: When `data/evaluation` last changed at that commit (`2c42f4d6`, "Update faa9f03d with edits").
SOLUTIONS_CHANGED = "2025-05-15T23:12:29+00:00"
SOLUTION_HOSTS = ("api.github.com", "raw.githubusercontent.com")
TASKS = 120
#: 95 % of the tasks: a setting missing more is a partial run.
MIN_TASKS = 114
_TASK_FILE = re.compile(r"(?P<setting>[^/]+)/(?P<task>[0-9a-f]{8})\.json")

#: Hugging Face answers 429 past its anonymous rate; each wait is what it asks, at most this many times.
RETRIES = 30


def _get(url: str, hosts: tuple[str, ...] = HOSTS) -> bytes:
    for _ in range(RETRIES):
        answer = bounded_get(url, "arc_agi_2", 60.0, hosts=hosts)
        if answer.status != 429:
            return answer.body
        wait = answer.headers.get("retry-after", "")
        time.sleep(min(float(wait), 300.0) if wait.replace(".", "", 1).isdigit() else 60.0)
    msg = f"arc_agi_2: still 429 after {RETRIES} waits: {url}"
    raise SourceError(msg)


def _attempts(pair: object) -> list[dict[str, Any]]:
    if not isinstance(pair, dict):
        return []
    return [pair[key] for key in ("attempt_1", "attempt_2") if isinstance(pair.get(key), dict)]


def _solves(attempt: dict[str, Any], expected: object) -> bool:
    """ARC Prize's mark where it made one; else the answer compared with the published solution."""
    mark = attempt.get("correct")
    if isinstance(mark, bool):
        return mark
    return mark is None and expected is not None and attempt.get("answer") == expected


def _pair_index(pair: object, position: int) -> int:
    """The test pair an attempt answered: its `metadata.pair_index`, else its position in the file."""
    for attempt in _attempts(pair):
        meta = attempt.get("metadata")
        index = meta.get("pair_index") if isinstance(meta, dict) else None
        if isinstance(index, int) and not isinstance(index, bool) and index >= 0:
            return index
    return position


def _solution(expected: list[Any], index: int) -> object:
    return expected[index] if index < len(expected) else None


def task_score(attempts: Any, expected: list[Any]) -> float:
    """The share of a task's test pairs solved by either attempt; ``expected`` is each pair's solution."""
    if not isinstance(attempts, list) or not attempts:
        return 0.0
    solved = 0
    for position, pair in enumerate(attempts):
        solution = _solution(expected, _pair_index(pair, position))
        if any(_solves(attempt, solution) for attempt in _attempts(pair)):
            solved += 1
    return solved / len(attempts)


def _disagreements(attempts: Any, expected: list[Any]) -> tuple[int, list[tuple[int, str, bool]]]:
    """How many of ARC Prize's marks were compared, and each (pair, attempt, mark) the comparison disagrees with."""
    checked, found = 0, []
    for position, pair in enumerate(attempts if isinstance(attempts, list) else []):
        index = _pair_index(pair, position)
        solution = _solution(expected, index)
        for key in ("attempt_1", "attempt_2"):
            attempt = pair.get(key) if isinstance(pair, dict) else None
            if isinstance(attempt, dict) and isinstance(attempt.get("correct"), bool) and solution is not None:
                checked += 1
                if (attempt.get("answer") == solution) != attempt["correct"]:
                    found.append((index, key, attempt["correct"]))
    return checked, found


def _unscorable(attempts: Any, expected: list[Any]) -> int:
    """Unmarked attempts with no solution at their pair index; none is expected in a comparable setting."""
    return sum(1 for position, pair in enumerate(attempts if isinstance(attempts, list) else [])
               for attempt in _attempts(pair)
               if attempt.get("correct") is None and _solution(expected, _pair_index(pair, position)) is None)


def comparable(bodies: list[Any]) -> bool:
    """Whether every unmarked attempt ran after the solutions it is compared with last changed (N1)."""
    return not any(attempt.get("correct") is None
                   and str((attempt.get("metadata") or {}).get("start_timestamp", "")) < SOLUTIONS_CHANGED
                   for body in bodies if isinstance(body, list) for pair in body for attempt in _attempts(pair))


def _latest_run(bodies: list[Any]) -> str | None:
    """The date of the setting's latest attempt."""
    starts = [attempt["metadata"]["start_timestamp"][:10] for body in bodies if isinstance(body, list)
              for pair in body for attempt in _attempts(pair)
              if isinstance(attempt.get("metadata"), dict)
              and isinstance(attempt["metadata"].get("start_timestamp"), str)]
    return max(starts) if starts else None


def _attempt_cost(attempt: object) -> float:
    """What one attempt cost, in USD, as its metadata records it; 0 when it records none."""
    meta = attempt.get("metadata") if isinstance(attempt, dict) else None
    cost = meta.get("cost") if isinstance(meta, dict) else None
    total = cost.get("total_cost") if isinstance(cost, dict) else None
    return float(total) if isinstance(total, int | float) and not isinstance(total, bool) else 0.0


def _solutions() -> tuple[str, dict[str, list[Any]]]:
    """Each public evaluation task's test outputs, from ARC-AGI-2's repository at `SOLUTIONS_COMMIT`."""
    commit = SOLUTIONS_COMMIT
    listing = json.loads(_get(f"https://api.github.com/repos/{SOLUTIONS}/contents/data/evaluation?ref={commit}",
                              SOLUTION_HOSTS))
    raw = f"https://raw.githubusercontent.com/{SOLUTIONS}/{commit}/data/evaluation/"
    solutions: dict[str, list[Any]] = {}
    for entry in listing:
        name = entry["name"]
        if re.fullmatch(r"[0-9a-f]{8}\.json", name):
            task = json.loads(_get(raw + name, SOLUTION_HOSTS))
            solutions[name[:-5]] = [pair.get("output") for pair in task["test"]]
    return commit, solutions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="derive_arc_public_eval")
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    solutions_commit, solutions = _solutions()
    info = json.loads(_get(API))
    revision = info["sha"]
    files = [s["rfilename"] for s in info["siblings"]]
    tasks: dict[str, list[tuple[str, str]]] = {}
    for name in files:
        match = _TASK_FILE.fullmatch(name)
        if match:
            tasks.setdefault(match["setting"], []).append((name, match["task"]))
    resolve = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"

    def score(setting: str) -> tuple[str, dict[str, Any]]:
        read = [(json.loads(_get(resolve + path)), solutions.get(task, [])) for path, task in tasks[setting]]
        solved = sum(task_score(body, expected) for body, expected in read)
        marks = [_disagreements(body, expected) for body, expected in read]
        tasks_read = [task for _, task in tasks[setting]]
        cost = sum(_attempt_cost(attempt) for body, _ in read if isinstance(body, list)
                   for pair in body for attempt in _attempts(pair))
        return setting, {
            "tasks_run": len(read), "solved": round(solved, 6), "score": round(100 * solved / TASKS, 4),
            "cost_usd": round(cost, 4) if cost else None, "run_date": _latest_run([body for body, _ in read]),
            "marks_checked": sum(m[0] for m in marks),
            "disagreements": [[setting, task, *found] for task, (_, items) in zip(tasks_read, marks, strict=True)
                              for found in items],
            "unscorable": sum(_unscorable(body, expected) for body, expected in read),
            "comparable": comparable([body for body, _ in read]),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        scored = dict(pool.map(score, sorted(tasks)))
    partial = sorted(k for k, v in scored.items() if v["tasks_run"] < MIN_TASKS)
    predating = sorted(k for k, v in scored.items() if not v["comparable"] and k not in partial)
    disagreements = [d for v in scored.values() for d in v.pop("disagreements")]
    kept = {k: {f: x for f, x in v.items() if f != "comparable"} for k, v in scored.items()
            if k not in partial and k not in predating}
    record = {
        "dataset": DATASET,
        "url": f"https://huggingface.co/datasets/{DATASET}",
        "revision": revision,
        "licence": "MIT",
        "publisher": "ARC Prize Foundation",
        "tasks": TASKS,
        "min_tasks": MIN_TASKS,
        "derived_by": "scripts/derive_arc_public_eval.py",
        "solutions": {"repository": SOLUTIONS, "url": f"https://github.com/{SOLUTIONS}", "revision": solutions_commit,
                      "licence": "Apache-2.0"},
        "marks_checked": sum(v["marks_checked"] for v in scored.values()),
        "marks_disagreeing": len(disagreements),
        "disagreements": disagreements,
        "unscorable": sum(v["unscorable"] for v in kept.values()),
        "left_out_as_partial": partial,
        "left_out_as_predating_solutions": predating,
        "settings": kept,
    }
    Path(args.out).write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"{len(kept)} settings kept of {len(scored)} at {revision[:12]}; marks checked "
          f"{record['marks_checked']}, disagreeing {record['marks_disagreeing']}, unscorable {record['unscorable']}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
