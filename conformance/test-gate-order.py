#!/usr/bin/env python3
"""`make gate` runs its cheapest legs first: DevFlow's record checks and the conformance suite before any code leg.

WHY (#51, Project-K, a swift stack). The pre-push gate refused three pushes on `test-documented-paths` -- a
path in a docs row -- only after 10 to 20 minutes of the stack's tests, two of them the owner's own pushes.
So `make gate` runs `check`'s record checks, then `conformance`, then the legs that run the project's own
commands: a records or docs refusal costs seconds.

What it compares: the order make itself runs `gate` in (`make -n --debug=b gate` names each target as make
decides to run it, and runs nothing) against `scripts/check_fast.py --plan`, whose legs other than `records`
are the code legs (lint, typecheck, test, a project's own). The record checks are the prerequisites of the
Makefile's own `check:` line that are not code legs; a project's `stack.mk` may add more, which run after them.

FAILS CLOSED: an order make did not print, a plan with no code leg, a code leg or record check the order never
reaches -- each is a FAILURE. Without make: NOT-EVALUABLE.

Exit: 0 cheapest first - 1 a code leg runs before a record check or the conformance suite - 2 no make.
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
#: GNU make 3.81 quotes `like this', 4.x 'like this'.
REMAKE = re.compile(r"Must remake target [`'](.+?)'")
LEG = re.compile(r"^\s*([A-Za-z0-9_.-]+):[ \t]*(.*?)\s*$")


def gate_order() -> list[str]:
    r = subprocess.run(["make", "-n", "--debug=b", "gate"], cwd=ROOT, capture_output=True, encoding="utf-8",
                       errors="replace", timeout=120, env=scrubbed_env())
    return [m.group(1) for m in REMAKE.finditer(r.stdout)]


def code_legs() -> list[str] | None:
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_fast.py"), "--plan"], cwd=ROOT,
                       capture_output=True, encoding="utf-8", errors="replace", timeout=120, env=scrubbed_env())
    if r.returncode != 0:
        return None
    legs = [(m.group(1), m.group(2).split()) for m in map(LEG.match, r.stdout.splitlines()) if m]
    return [t.partition("=")[0] for name, targets in legs if name != "records" for t in targets]


def record_checks(code: list[str]) -> list[str]:
    """The prerequisites of the Makefile's own `check:` line(s), less the code legs (stack.mk's are the project's)."""
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    found: list[str] = []
    for m in re.finditer(r"^check:(?![:=])([^\n#]*)", text, re.M):
        found += [t for t in m.group(1).split("|")[0].split() if t not in code and t not in found]
    return found


def main() -> int:
    if (no_make := missing_tool("make", "ask make for the order it runs `gate` in")):
        print(f"test-gate-order NOT-EVALUABLE: {no_make}")
        return 2
    order, code = gate_order(), code_legs()
    bad: list[str] = []
    if not order or "gate" not in order:
        bad.append("`make -n --debug=b gate` named no target -- there is no order to grade")
    if not code:
        bad.append("`scripts/check_fast.py --plan` printed no code leg -- nothing to order the record checks before")
    if bad:
        print("test-gate-order FAIL: " + "; ".join(bad))
        return 1
    records = record_checks(code)
    missing = [t for t in [*code, *records, "conformance"] if t not in order]
    if missing:
        print(f"test-gate-order FAIL: `make gate` never reaches {', '.join(missing)} -- a leg it does not run "
              "cannot be ordered")
        return 1
    first = min(order.index(t) for t in code)
    late = [t for t in [*records, "conformance"] if order.index(t) > first]
    if not records:
        bad.append("the Makefile's `check:` line names no record check -- nothing is shown to run first")
    for t in late:
        bad.append(f"`{t}` runs after the code leg `{order[first]}` -- a records or docs refusal waits for the "
                   "project's tests (#51)")
    if bad:
        print("test-gate-order FAIL (`make gate`, as make orders it):")
        print("\n".join(f"  {b}" for b in bad))
        print(f"  order: {' '.join(order)}")
        return 1
    print(f"test-gate-order PASS: `make gate` runs {len(records)} record check(s) and the conformance suite before "
          f"its first code leg (`{order[first]}`, of {len(code)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
