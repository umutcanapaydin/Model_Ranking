"""How well Apple Intelligence reads a question, beside the wording tier (#351, Golden Rule 2, D-210).

Every reading rule before #351 was tuned and measured on the wording tier alone; the on-device model the
app asks first was never scored. This runs `scripts/router_probe/ReadingProbe.swift` -- the model tier as
the app runs it, or `PROBE_TIER=wording` -- over each set, scores it, and writes the report:

    make model-tier                                      # the golden set and m24, both tiers
    .venv/bin/python scripts/model_tier.py --sets m24 --runs 2 --tiers model --label greedy
    .venv/bin/python scripts/model_tier.py --compare greedy kinds    # run 1 of each, question by question
    .venv/bin/python scripts/model_tier.py --compare greedy:1 greedy:2   # one label's two runs

The probe is not part of the package (it needs Apple Intelligence), so the working tree's `ios/` is
copied to a temporary directory with the probe beside the tests; the checkout is never touched. Where
the model is not available the probe fails, and this exits 2 NOT RUNNABLE: an empty run is never a
score. Every run keeps its rows, one per question, under `build/model-tier/<label>/`. A change is judged
on those rows: the questions it fixed against the ones it broke, by an exact McNemar test. Since #351 the
model reads with greedy decoding, so one run per variant is enough; `--runs 2` checks that two agree.

A set row is `[question, expected]`: a surface, `a|b` when either answers it, or `NOT_A_SEARCH`.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "scripts" / "router_probe" / "ReadingProbe.swift"
GOLDEN = ROOT / "ios" / "EngineTests" / "Golden" / "golden-questions.json"
SETS = {"m24": ROOT / "scripts" / "router_probe" / "reading_heldout_m24_questions.json"}
REPORT = ROOT / "build" / "model-tier-report.txt"
RUNS = ROOT / "build" / "model-tier"
NOT_A_SEARCH = "NOT_A_SEARCH"


class EmptyRun(Exception):
    """The run read no question of the set: there is nothing to score."""


class Score:
    """The counts of one run of one set. A plain class: the tests load this file by path."""

    def __init__(self) -> None:
        self.right = self.total = self.searches_right = self.searches = self.searches_unmeasured = 0
        self.not_searches_caught = self.not_searches = self.no_answer = 0
        self.misses: list[tuple[str, str, str, str]] = []

    def line(self) -> str:
        def pct(a: int, b: int) -> str:
            return f"{a}/{b} ({100 * a / b:.0f}%)" if b else f"{a}/0"
        return (f"right {pct(self.right, self.total)} | searches {pct(self.searches_right, self.searches)}"
                f" | not a search caught {pct(self.not_searches_caught, self.not_searches)}"
                f" | searches not measured {self.searches_unmeasured} | no answer {self.no_answer}")


def right(expected: str, row: dict[str, str] | None) -> bool:
    """Whether one question was read right: the m23 and m24 write-ups' rule (module docstring of
    tests/unit/test_model_tier_score.py)."""
    reading = row.get("reading", "nil") if row else "nil"
    if expected == NOT_A_SEARCH:
        return reading not in ("search", "nil")
    return (row is not None and row["surface"] in expected.split("|") and row["unmeasured"] != "true"
            and reading == "search")


def score(rows_expected: list[list[str]], probe_rows: list[dict[str, str]]) -> Score:
    """One run's counts, by `right`."""
    if not probe_rows:
        raise EmptyRun("the probe wrote no row")
    by_question = {row["q"]: row for row in probe_rows}
    result = Score()
    for question, expected in rows_expected:
        row = by_question.get(question)
        result.total += 1
        if row is None or row["surface"] == "nil":
            result.no_answer += 1
        ok = right(expected, row)
        if expected == NOT_A_SEARCH:
            result.not_searches += 1
            result.not_searches_caught += ok
        else:
            result.searches += 1
            result.searches_unmeasured += row is not None and row["unmeasured"] == "true"
            result.searches_right += ok
        result.right += ok
        if not ok:
            result.misses.append((expected, row["surface"] if row else "-", row.get("reading", "nil") if row else "nil",
                                  question))
    return result


def mcnemar(fixed: int, broken: int) -> float:
    """The exact two-sided McNemar test: how likely so lopsided a split of the changed questions is by chance."""
    changed = fixed + broken
    if changed == 0:
        return 1.0
    tail = sum(math.comb(changed, k) for k in range(min(fixed, broken) + 1)) / (1 << changed)
    return min(1.0, 2 * tail)


class Comparison:
    """Two runs of one set, question by question. A plain class: the tests load this file by path."""

    def __init__(self) -> None:
        self.fixed: list[str] = []  # wrong in the base run, right in the candidate
        self.broken: list[str] = []  # right in the base run, wrong in the candidate
        self.searches_net = self.not_searches_net = 0

    def line(self) -> str:
        net = len(self.fixed) - len(self.broken)
        return (f"fixed {len(self.fixed)}, broke {len(self.broken)}, net {net:+d}"
                f" (exact McNemar p={mcnemar(len(self.fixed), len(self.broken)):.3f})"
                f" | searches net {self.searches_net:+d} | not a search net {self.not_searches_net:+d}")


def compare(rows_expected: list[list[str]], base_rows: list[dict[str, str]],
            candidate_rows: list[dict[str, str]]) -> Comparison:
    if not base_rows or not candidate_rows:
        raise EmptyRun("a run to compare holds no row")
    base = {row["q"]: row for row in base_rows}
    candidate = {row["q"]: row for row in candidate_rows}
    result = Comparison()
    for question, expected in rows_expected:
        was, now = right(expected, base.get(question)), right(expected, candidate.get(question))
        if was == now:
            continue
        (result.fixed if now else result.broken).append(question)
        if expected == NOT_A_SEARCH:
            result.not_searches_net += 1 if now else -1
        else:
            result.searches_net += 1 if now else -1
    return result


def run_name(text: str) -> tuple[str, int]:
    """`label` is run 1 of that label; `label:2` is its run 2."""
    label, _, run = text.partition(":")
    return label, int(run) if run else 1


def rows_path(label: str, name: str, tier: str, run: int) -> Path:
    return RUNS / label / f"{name}-{tier}-{run}.json"


def load_set(name: str) -> list[list[str]]:
    if name == "golden":
        # D-211 clause 2: a row of the owner's two classes is scored as not a search.
        return [[r["question"], NOT_A_SEARCH if "not_a_search" in r else r["expected_surface"]]
                for r in json.loads(GOLDEN.read_text(encoding="utf-8"))]
    rows: list[list[str]] = json.loads(SETS[name].read_text(encoding="utf-8"))
    return rows


def run_probe(copy: Path, questions: Path, out: Path, tier: str) -> list[dict[str, str]]:
    swift = shutil.which("swift")
    if swift is None:
        raise EmptyRun("no `swift` on PATH")
    env = {**os.environ, "PROBE_QUESTIONS": str(questions), "PROBE_OUT": str(out),
           "PROBE_TIER": "wording" if tier == "wording" else ""}
    done = subprocess.run([swift, "test", "--filter", "ReadingProbe"], cwd=copy / "ios", env=env,  # noqa: S603
                          capture_output=True, encoding="utf-8", errors="replace", timeout=3600)
    if done.returncode != 0 or not out.is_file():
        tail = "\n".join((done.stdout + done.stderr).strip().splitlines()[-5:])
        raise EmptyRun(f"the {tier} probe did not run:\n{tail}")
    probe_rows: list[dict[str, str]] = json.loads(out.read_text(encoding="utf-8"))
    return probe_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sets", nargs="+", default=["golden", "m24"], choices=["golden", *SETS])
    parser.add_argument("--tiers", nargs="+", default=["model", "wording"], choices=["model", "wording"])
    parser.add_argument("--runs", type=int, default=1, help="model-tier runs per set (the wording tier is exact)")
    parser.add_argument("--misses", action="store_true", help="list every miss in the report")
    parser.add_argument("--label", default="latest", help="where the runs' rows are kept, under build/model-tier/")
    parser.add_argument("--compare", nargs=2, metavar=("BASE", "CANDIDATE"),
                        help="compare two kept runs (`label` or `label:run`) question by question; runs no model")
    args = parser.parse_args()
    if args.compare:
        return compare_runs(args)
    lines: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp)
        shutil.copytree(ROOT / "ios", copy / "ios", ignore=shutil.ignore_patterns(".build", "*.xcodeproj"))
        shutil.copy(PROBE, copy / "ios" / "EngineTests")
        for name in args.sets:
            expected = load_set(name)
            questions = copy / f"{name}.json"
            questions.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
            for tier in args.tiers:
                for run in range(1, (args.runs if tier == "model" else 1) + 1):
                    kept = rows_path(args.label, name, tier, run)
                    kept.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        result = score(expected, run_probe(copy, questions, kept, tier))
                    except EmptyRun as error:
                        print(f"model-tier NOT RUNNABLE: {name}, {tier} tier: {error}")
                        return 2
                    lines.append(f"{name} {tier} run {run}: {result.line()}")
                    print(lines[-1], flush=True)
                    if args.misses:
                        lines += [f"  MISS expected={e} got={g} reading={r} :: {q}" for e, g, r, q in sorted(result.misses)]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"model-tier: report written to {REPORT.relative_to(ROOT)}")
    return 0


def compare_runs(args: argparse.Namespace) -> int:
    (base_label, base_run), (candidate_label, candidate_run) = map(run_name, args.compare)
    lines: list[str] = []
    for name in args.sets:
        expected = load_set(name)
        for tier in args.tiers:
            paths = rows_path(base_label, name, tier, base_run), rows_path(candidate_label, name, tier, candidate_run)
            if not all(path.is_file() for path in paths):
                continue
            base, candidate = (json.loads(path.read_text(encoding="utf-8")) for path in paths)
            result = compare(expected, base, candidate)
            lines.append(f"{name} {tier} {args.compare[0]} -> {args.compare[1]}: {result.line()}")
            if args.misses:
                lines += [f"  FIXED  {q}" for q in result.fixed] + [f"  BROKEN {q}" for q in result.broken]
    if not lines:
        print(f"model-tier NOT RUNNABLE: no set has kept rows for both {args.compare[0]} and {args.compare[1]}")
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
