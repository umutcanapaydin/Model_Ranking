#!/usr/bin/env python3
"""Decide whether zero plan coverage on a CI runner is expected or a real failure.

`app.workflows.coverage` exits 1 when any category has zero scoreable plans, and that is the right
behaviour: a category that can answer nothing is louder as an exit code than as a number in a
report nobody reads. On a GitHub runner it is also GUARANTEED — seven of the nine surfaces are
Epoch-backed, D-101 makes the Epoch bundle an owner-placed artifact, and no runner has one.

So the coverage step failed on every run where it got far enough to execute. **The build step one
line above it had already been taught this exact tolerance** — it accepts exit 3 and prints
`built with degraded evidence (expected on a runner: no Epoch bundle)` — and the lesson was not
carried to the next step. That is the same shape as a repair landing on one of two scans.

The tolerance implemented here is NOT "ignore exit 1". It is: **a category may be empty only if
the build reported its source unavailable.** A surface whose sources were reachable and which still
scores nothing is a real failure and still fails the job — which is the whole reason the step
exists.

This lives in a file rather than in a `run:` heredoc because of W-023, which this project paid a
milestone for: the evidence pipeline once existed only inside a CI heredoc, invisible to ruff,
mypy, pytest and coverage, and it had never run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_REAL_GAP = 1
EXIT_UNREADABLE = 2


def degraded_surfaces(build_report: dict) -> set[str]:
    """Surfaces the BUILD said have no primary evidence, taken from its own words.

    The build reports these as sentences rather than as a list, so they are parsed rather than
    read. That is a weakness and it is stated here instead of hidden: a wording change upstream
    turns a tolerated gap into a reported failure, which is the safe direction — this gate becomes
    noisier, never quieter.
    """
    surfaces: set[str] = set()
    for note in build_report.get("required_operator_actions", []) or []:
        text = str(note)
        marker = "must disclose it rather than answer:"
        if marker not in text:
            continue
        # `... must disclose it rather than answer: agentic-coding (epoch_deepswe_external: ...)`
        # More than one surface can follow, comma-separated, each optionally parenthesised.
        tail = text.split(marker, 1)[1]
        for chunk in tail.split(","):
            name = chunk.strip().split(" ", 1)[0].strip().strip(":()")
            if name:
                surfaces.add(name)
    return surfaces


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return EXIT_UNREADABLE
    try:
        build = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        coverage = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ci-coverage-gate: cannot read a report: {exc}", file=sys.stderr)
        return EXIT_UNREADABLE

    expected = degraded_surfaces(build)
    empty = {c["category"] for c in coverage.get("plan_coverage", []) if c["scoreable_plans"] == 0}
    unexpected = sorted(empty - expected)
    tolerated = sorted(empty & expected)

    if tolerated:
        print(f"ci-coverage-gate: {len(tolerated)} surface(s) empty as the build predicted: "
              f"{', '.join(tolerated)}")
    if unexpected:
        print("ci-coverage-gate FAIL: these surfaces score nothing and the build did NOT say "
              f"their sources were unavailable: {', '.join(unexpected)}", file=sys.stderr)
        print("  A reachable source that produces no scoreable plan is the drift this workflow "
              "exists to catch.", file=sys.stderr)
        return EXIT_REAL_GAP

    covered = [c["category"] for c in coverage.get("plan_coverage", [])
               if c["scoreable_plans"] > 0]
    if not covered:
        print("ci-coverage-gate FAIL: NO surface scored anything at all. Even with every "
              "owner-placed source absent, the runner-reachable ones must produce something — "
              "otherwise this job would pass on a completely empty artifact.", file=sys.stderr)
        return EXIT_REAL_GAP

    print(f"ci-coverage-gate PASS: {len(covered)} surface(s) scored ({', '.join(covered)}); "
          f"{len(tolerated)} empty by declared source absence")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
