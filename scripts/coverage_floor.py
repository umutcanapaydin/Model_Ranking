#!/usr/bin/env python3
"""A test run that verified nothing must not report success — skips and coverage, together.

Conditions 15-6 (open since 2026-09-03) and 17-3. Two halves of one failure, adopted together at
Increment 17 because the field instance shows them as one:

  **214 contract tests skipped on every pull request and the job was green** — the CI job had no
  `services:` block, so the suite that exercises tenancy and authorization against a real dependency
  never ran. In the same commit, `practices.md` said *"A skip is not a pass. A control that could
  not run reports NOT RUNNABLE and fails; it never reports success."* The rule was present, the
  third exit state that implemented it had been deleted, and nothing replaced it. What those tests
  certified: a P0 authorization capability marked DONE for months that had never functioned.

WHY A BUDGET RATHER THAN A `services:` CHECK. The council considered asserting that a workflow
running a services-requiring suite declares those services, and refused it: GP would have to infer
*"this suite needs Postgres"* from a repository it does not author, which is either a heuristic
shaped like one project or a hand-kept suite-to-service map — V5C-110 again. A skip budget needs no
knowledge of the suite's dependencies. It is portable across pytest, jest and go test, and it fires
on the 214 case regardless of WHY they skipped. Those 214 skipped via a conftest fixture check, not
an import error; a `services:` grep would not have caught them.

**This does NOT close condition 15-8.** 15-8 is open on *"nothing in GP inspects a real CI run"*,
and this reads a report a run produced — closer, and not the same thing. Six of the seven seats that
adopted the check made leaving 15-8 open a condition of their vote.

Usage:
    python3 scripts/coverage_floor.py --junit <report.xml> [--budget-file docs/skip-budget.txt]
    python3 scripts/coverage_floor.py --self-test

Exit: 0 within budget · 1 over budget or under the coverage floor · 2 cannot evaluate.
"""
import argparse
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_BUDGET = ROOT / "docs" / "skip-budget.txt"


def read_budget(path: pathlib.Path) -> int | None:
    """The committed number. Absent means unset, which is a FAILURE, not a licence."""
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            try:
                return int(line)
            except ValueError:
                return None
    return None


def counts(junit: pathlib.Path) -> tuple[int, int, int]:
    """(tests, skipped, failures+errors) summed across suites — pytest nests, jest does not."""
    root = ET.parse(junit).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    tests = sum(int(s.get("tests", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    bad = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    return tests, skipped, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--junit")
    ap.add_argument("--budget-file", default=str(DEFAULT_BUDGET))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            j = pathlib.Path(d) / "j.xml"
            b = pathlib.Path(d) / "b.txt"
            b.write_text("5\n")
            j.write_text('<testsuite tests="220" skipped="214" failures="0" errors="0"/>')
            over = counts(j)[1] > read_budget(b)
            j.write_text('<testsuite tests="220" skipped="2" failures="0" errors="0"/>')
            under = counts(j)[1] > read_budget(b)
            ok = over and not under
            print(f"coverage_floor --self-test {'PASS' if ok else 'FAIL'}: "
                  f"214 skips over a budget of 5 -> {over} (want True); 2 skips -> {under} (want False)")
            return 0 if ok else 1

    if not a.junit:
        print("coverage_floor CANNOT RUN: --junit <report.xml> is required. A run that produced no "
              "machine-readable report cannot be judged, and 'no report' is not 'no skips'.")
        return 2
    junit = pathlib.Path(a.junit)
    if not junit.is_file():
        print(f"coverage_floor CANNOT RUN: {junit} does not exist. The test step did not emit a "
              f"report -- which is itself the 'did-not-run vs ran-and-failed' confusion this "
              f"control exists to separate.")
        return 2

    budget = read_budget(pathlib.Path(a.budget_file))
    if budget is None:
        print(f"coverage_floor FAIL: no skip budget in {a.budget_file}. **An unset budget is a "
              f"failure, not an unlimited one** -- the absent third exit state is exactly how 214 "
              f"tests skipped green for weeks. Commit a number, and lower it over time.")
        return 1

    tests, skipped, bad = counts(junit)
    if skipped > budget:
        print(f"coverage_floor FAIL: {skipped} test(s) skipped of {tests}, budget is {budget}. "
              f"A skip is not a pass. Either wire what they need (services, fixtures, credentials) "
              f"or raise the budget deliberately, in the tree, where a reviewer sees it.")
        return 1
    print(f"coverage_floor PASS: {skipped} skipped of {tests} (budget {budget}), {bad} failed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"coverage_floor internal error: {exc}", file=sys.stderr)
        sys.exit(2)
