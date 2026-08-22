"""The CI coverage gate distinguishes a declared source absence from real drift.

`app.workflows.coverage` exits 1 on any empty category, which on a GitHub runner is guaranteed:
seven of nine surfaces are Epoch-backed and D-101 makes that bundle owner-placed. The build step
had already been taught to tolerate its own version of this and the coverage step had not, so the
workflow failed on every run that reached it.

The danger in fixing that is obvious and is what these tests are for: a tolerance written as
"ignore exit 1" would make the step unable to report the drift it exists to catch. The rule is
narrower — **a category may be empty only if the build said its source was unavailable** — and
every test here attacks that boundary rather than confirming it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.ci_coverage_gate import EXIT_OK, EXIT_REAL_GAP, EXIT_UNREADABLE, main

DEGRADED = (
    "epoch_eci is unavailable, so these surfaces have NO primary evidence and must disclose it "
    "rather than answer: everyday (epoch_eci: no local bundle directory supplied)"
)


def _reports(tmp_path: Path, actions: list[str], coverage: dict[str, int]) -> tuple[str, str]:
    build = tmp_path / "build-report.json"
    build.write_text(json.dumps({"required_operator_actions": actions}), encoding="utf-8")
    cov = tmp_path / "coverage-report.json"
    cov.write_text(
        json.dumps({"plan_coverage": [{"category": k, "scoreable_plans": v}
                                      for k, v in coverage.items()]}),
        encoding="utf-8",
    )
    return str(build), str(cov)


def test_a_surface_the_build_declared_absent_is_tolerated(tmp_path: Path) -> None:
    build, cov = _reports(tmp_path, [DEGRADED], {"coding": 5, "everyday": 0})

    assert main(["gate", build, cov]) == EXIT_OK


def test_a_surface_that_scores_nothing_with_NO_declared_absence_fails(tmp_path: Path) -> None:
    """The drift this workflow exists to catch. `coding` reads swebench, which a runner CAN reach;
    if it stops producing scoreable plans, that is a real finding and not an environment gap."""
    build, cov = _reports(tmp_path, [DEGRADED], {"coding": 0, "everyday": 0})

    assert main(["gate", build, cov]) == EXIT_REAL_GAP


def test_an_entirely_empty_artifact_fails_even_if_every_source_was_declared_absent(
    tmp_path: Path,
) -> None:
    """The hole a naive version of this rule leaves wide open.

    If every source is declared unavailable, every empty category is 'expected' and the job passes
    over an artifact that answers nothing at all — a green badge on a build that produced nothing.
    """
    everything = " ".join(
        f"{s} is unavailable, so these surfaces have NO primary evidence and must disclose it "
        f"rather than answer: {s}" for s in ("coding", "everyday")
    )
    build, cov = _reports(tmp_path, [everything], {"coding": 0, "everyday": 0})

    assert main(["gate", build, cov]) == EXIT_REAL_GAP


def test_a_build_report_that_declares_nothing_makes_every_gap_real(tmp_path: Path) -> None:
    """Fail CLOSED on a missing declaration. If the build's wording ever changes so nothing parses,
    the gate gets NOISIER rather than quieter — that direction is the whole point."""
    build, cov = _reports(tmp_path, [], {"coding": 5, "everyday": 0})

    assert main(["gate", build, cov]) == EXIT_REAL_GAP


def test_a_full_artifact_passes(tmp_path: Path) -> None:
    """Fixture blindness: without this, every test above could pass because the gate always fails."""
    build, cov = _reports(tmp_path, [], {"coding": 5, "everyday": 6})

    assert main(["gate", build, cov]) == EXIT_OK


def test_an_unreadable_report_is_not_a_pass(tmp_path: Path) -> None:
    assert main(["gate", str(tmp_path / "missing.json"), str(tmp_path / "gone.json")]) == (
        EXIT_UNREADABLE
    )


def test_several_surfaces_on_one_line_are_all_recognised(tmp_path: Path) -> None:
    """The build lists multiple surfaces after one marker, comma-separated. Parsing only the first
    would report the rest as real gaps and fail a correct run — a gate that fails correct work is
    a gate somebody switches off."""
    action = (
        "arena is unavailable, so these surfaces have NO primary evidence and must disclose it "
        "rather than answer: assistant, everyday, expert"
    )
    build, cov = _reports(
        tmp_path, [action], {"coding": 5, "assistant": 0, "everyday": 0, "expert": 0}
    )

    assert main(["gate", build, cov]) == EXIT_OK


@pytest.mark.parametrize("missing_key", ["plan_coverage", "required_operator_actions"])
def test_a_report_missing_its_key_does_not_crash_into_a_pass(
    tmp_path: Path, missing_key: str
) -> None:
    build = tmp_path / "b.json"
    cov = tmp_path / "c.json"
    build.write_text(
        json.dumps({} if missing_key == "required_operator_actions"
                   else {"required_operator_actions": []}), encoding="utf-8")
    cov.write_text(
        json.dumps({} if missing_key == "plan_coverage"
                   else {"plan_coverage": [{"category": "coding", "scoreable_plans": 0}]}),
        encoding="utf-8")

    assert main(["gate", str(build), str(cov)]) == EXIT_REAL_GAP
