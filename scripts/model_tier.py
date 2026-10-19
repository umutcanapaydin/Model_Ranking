"""How well Apple Intelligence reads a question, beside the wording tier (#351, Golden Rule 2, D-210).

Every reading rule before #351 was tuned and measured on the wording tier alone; the on-device model the
app asks first was never scored. This runs `scripts/router_probe/ReadingProbe.swift` -- the model tier as
the app runs it, or `PROBE_TIER=wording` -- over each set, scores it, and writes the report:

    make model-tier                                      # the golden set and m24, both tiers
    .venv/bin/python scripts/model_tier.py --sets m24 --runs 2 --tiers model

The probe is not part of the package (it needs Apple Intelligence), so the working tree's `ios/` is
copied to a temporary directory with the probe beside the tests; the checkout is never touched. Where
the model is not available the probe fails, and this exits 2 NOT RUNNABLE: an empty run is never a
score. The model is not deterministic: `--runs 2` reads every set twice.

A set row is `[question, expected]`: a surface, `a|b` when either answers it, or `NOT_A_SEARCH`.
"""

from __future__ import annotations

import argparse
import json
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


def score(rows_expected: list[list[str]], probe_rows: list[dict[str, str]]) -> Score:
    """The m23 and m24 write-ups' rule (module docstring of tests/unit/test_model_tier_score.py)."""
    if not probe_rows:
        raise EmptyRun("the probe wrote no row")
    by_question = {row["q"]: row for row in probe_rows}
    result = Score()
    for question, expected in rows_expected:
        row = by_question.get(question)
        result.total += 1
        if row is None or row["surface"] == "nil":
            result.no_answer += 1
        reading = row.get("reading", "nil") if row else "nil"
        if expected == NOT_A_SEARCH:
            result.not_searches += 1
            ok = reading not in ("search", "nil")
            result.not_searches_caught += ok
        else:
            result.searches += 1
            unmeasured = row is not None and row["unmeasured"] == "true"
            result.searches_unmeasured += unmeasured
            ok = row is not None and row["surface"] in expected.split("|") and not unmeasured and reading == "search"
            result.searches_right += ok
        result.right += ok
        if not ok:
            result.misses.append((expected, row["surface"] if row else "-", reading, question))
    return result


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
    args = parser.parse_args()
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
                    try:
                        result = score(expected, run_probe(copy, questions, copy / f"out-{name}-{tier}-{run}.json", tier))
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


if __name__ == "__main__":
    sys.exit(main())
