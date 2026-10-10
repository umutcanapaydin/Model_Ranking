"""`make check-fast` -- DevFlow v6.6's `scripts/check_fast.py`, with this project's own legs.

The script is DevFlow's, unchanged. What this project adds lives in `stack.mk`: the iOS client check
and the Swift suite each get a leg of their own, and the Swift suite runs in its parallel form. These
tests hold that configuration against the real Makefile, so a setting that silently matches nothing,
or a gate that falls out of every leg, is red here and not only in the conformance run.
"""

from __future__ import annotations

import importlib.util
import shlex
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_fast.py"


def _mod() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_fast", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plan(*args: str) -> dict[str, list[str]]:
    result = subprocess.run([sys.executable, str(SCRIPT), "--plan", *args], cwd=ROOT, capture_output=True,
                            encoding="utf-8", check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    plan = {}
    for line in result.stdout.splitlines():
        name, sep, targets = line.partition(":")
        if sep and not name.startswith("check-fast"):
            plan[name.strip()] = targets.split()
    assert plan, "fails closed: the plan printed no leg"
    return plan


def test_the_project_legs_are_seen_and_every_gate_runs_once() -> None:
    plan = _plan()
    assert plan["client-decls"] == ["client-decls"]
    assert plan["swift-test"] == ["swift-test=swift-test-parallel"]
    shown = [t.split("=")[0] for targets in plan.values() for t in targets]
    prereqs = _mod().check_prerequisites((ROOT / "Makefile").read_text(encoding="utf-8"))
    assert sorted(shown) == sorted(prereqs)


def test_the_coverage_floor_runs_after_the_tests_it_reads() -> None:
    """W-041's floor reads the coverage.json pytest writes. Under v6.6 a separate `check:`
    prerequisite would land in the records leg, beside the tests, and read the previous run's file;
    so it runs inside the `test` recipe, after pytest, and is no leg of its own."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\ntest: ", 1)[1].split("\n\n", 1)[0]
    assert recipe.index("pytest") < recipe.index("module_coverage_floor.py")
    assert "coverage-floor" not in _mod().check_prerequisites(makefile)


def test_a_setting_that_names_no_check_prerequisite_fails() -> None:
    _, _, problems = _mod().settings(["lint", "test"], ["client-decls"], ["swift-test=swift-test-parallel"])
    assert len(problems) == 2


def test_an_empty_check_line_fails_closed() -> None:
    with pytest.raises(ValueError):
        _mod().check_prerequisites("gate: check\n")


def test_without_drops_the_named_legs_and_refuses_a_name_that_is_not_one() -> None:
    """The M21 closure fixes review's B1 and M2: `check-red` and `check-docs` are check-fast without some legs.
    A name that is not a `check:` prerequisite fails, as CHECK_FAST_FORMS does, so a typo cannot keep a leg."""
    kept, problems = _mod().without(["lint", "test", "swift-test", "check-records"], ["test", "swift-test"])
    assert kept == ["lint", "check-records"] and problems == []
    _, problems = _mod().without(["lint", "test"], ["tests"])
    assert problems and "tests" in problems[0]


RECORDS = ["check-records", "check-records-selftest", "install-check", "harvest-context-check", "shell-dialect",
           "wave-check-all"]


@pytest.mark.parametrize(("target", "legs"), [
    ("check-fast", {"lint": ["lint"], "typecheck": ["typecheck"], "test": ["test"],
                    "records": [*RECORDS, "conformance"], "client-decls": ["client-decls"],
                    "swift-test": ["swift-test=swift-test-parallel"]}),
    # A declared red commit: no leg that runs tests, and the code and tests still build (round 2, M1).
    ("check-red", {"lint": ["lint"], "typecheck": ["typecheck"], "records": RECORDS,
                   "swift-build-tests": ["swift-build-tests"], "pytest-collect": ["pytest-collect"]}),
    # A docs-only commit: every leg that reads Markdown.
    ("check-docs", {"lint": ["lint"], "typecheck": ["typecheck"], "test": ["test"],
                    "records": [*RECORDS, "conformance"]}),
])
def test_each_commit_gate_runs_exactly_its_legs(target: str, legs: dict[str, list[str]]) -> None:
    """The fixes review's round 2, M7: the lists were pinned by a substring, so `check-docs` could drop
    `conformance` (mutant X16) and stay green. Each gate's legs, as `make` runs it, are pinned exactly."""
    printed = subprocess.run(["make", "-n", target], cwd=ROOT, capture_output=True, text=True, check=False,
                             timeout=60).stdout
    line = next(ln for ln in printed.splitlines() if "scripts/check_fast.py" in ln)
    args = shlex.split(line)
    given = args[args.index("scripts/check_fast.py") + 1:]
    given = [a for i, a in enumerate(given) if a != "--make" and (i == 0 or given[i - 1] != "--make")]
    assert _plan(*given) == legs


def test_the_red_gates_compile_legs_build_and_collect_and_run_nothing() -> None:
    """Round 2, M1: `check-red` left out every leg that compiles Swift, so a red commit's Swift was not built.
    It builds the package and its tests (offline, under the watchdog, skipped without a toolchain as
    swift-test is), and collects the Python tests, so a red commit has no build or collection error."""
    swift = subprocess.run(["make", "-n", "swift-build-tests"], cwd=ROOT, capture_output=True, text=True,
                           check=False, timeout=60).stdout
    assert "swift build --build-tests" in swift and "swift test" not in swift, swift
    assert "watchdog.py" in swift and "SKIPPED NO-ENVIRONMENT: no swift toolchain on PATH" in swift, swift
    collect = subprocess.run(["make", "-n", "pytest-collect"], cwd=ROOT, capture_output=True, text=True,
                             check=False, timeout=60).stdout
    assert "pytest --collect-only" in collect and "--cov" not in collect, collect


def test_with_adds_a_leg_and_refuses_a_name_that_is_no_target() -> None:
    """`--with` runs make targets outside `check:` as legs of their own; a name that is no target, or that
    `check:` already runs, fails, as `--without` does."""
    assert _plan("--with", "pytest-collect")["pytest-collect"] == ["pytest-collect"]
    for name in ("no-such-target", "lint"):
        done = subprocess.run([sys.executable, str(SCRIPT), "--plan", "--with", name], cwd=ROOT, capture_output=True,
                              encoding="utf-8", check=False)
        assert done.returncode == 1 and name in done.stdout, done.stdout
