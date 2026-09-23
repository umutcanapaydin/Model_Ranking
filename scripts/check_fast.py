"""`make check-fast`: the same gates as `make check`, run side by side (owner, 2026-09-23).

Modelled on the owner's `check-fast` in hcs_maas_full. `make check` is unchanged and stays what a
merge is judged by; this is the one to run while working.

**Where the time goes** (measured on the owner's 8-core Mac, 2026-09-23): `make check` took 89 s, of
which the Swift suite was 61.5 s and `client-decls` 16.8 s; every Python leg together was about 27 s,
and pytest already runs on every core (`-n auto`). So the gain is not inside any one gate, it is in
not waiting for them one after another, plus `swift test --parallel` (51 s -> 28 s).

**The legs are DERIVED from `check`'s own prerequisite line** (AGENTS.md §3.5): a gate added to
`check` joins a leg here without an edit, and one removed leaves it. The only names kept are the ones
with a reason, below. `install` runs once before the legs and each leg is started with `-o install`,
because concurrent `pip install -e` runs into one virtualenv race each other.

    python3 scripts/check_fast.py [--make make]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "build" / "check-fast"

#: Run in THIS order, in one leg: `coverage-floor` reads the `coverage.json` that `test` writes.
PYTHON_CHAIN: tuple[str, ...] = ("lint", "typecheck", "test", "coverage-floor")
#: Gates with a leg of their own, because each is long enough to be the critical path.
OWN_LEG: dict[str, str] = {"swift-test": "swift", "client-decls": "client"}
#: The form a gate takes here. `swift-test-parallel` judges the same suite from its xUnit report.
PARALLEL_FORM: dict[str, str] = {"swift-test": "swift-test-parallel"}


def check_prerequisites(makefile: str) -> list[str]:
    """`check:`'s prerequisites, read from the Makefile -- the same line conformance reads."""
    found = re.search(r"^check:[ \t]*([^\n#]*)", makefile, re.M)
    prereqs = found.group(1).split() if found else []
    if not prereqs:
        msg = "`check:` has no prerequisites in the Makefile; an empty check-fast would pass"
        raise ValueError(msg)
    return prereqs


def legs(prereqs: list[str]) -> dict[str, list[str]]:
    """Every prerequisite in exactly one leg; anything not named above goes to `records`."""
    out: dict[str, list[str]] = {"python": [t for t in PYTHON_CHAIN if t in prereqs]}
    for target in prereqs:
        if target in PYTHON_CHAIN:
            continue
        leg = OWN_LEG.get(target, "records")
        out.setdefault(leg, []).append(PARALLEL_FORM.get(target, target))
    return {name: targets for name, targets in out.items() if targets}


def run_legs(commands: dict[str, list[str]], logs: Path) -> int:
    """Start every leg at once, each to its own log; 0 only if every one exits 0."""
    logs.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    running: dict[str, subprocess.Popen[bytes] | None] = {}
    for name, command in commands.items():
        with (logs / f"{name}.log").open("wb") as log:
            try:
                # The command is `make` and target names read from this repository's own Makefile.
                running[name] = subprocess.Popen(command, cwd=ROOT, stdout=log,  # noqa: S603
                                                 stderr=subprocess.STDOUT)
            except OSError as exc:
                log.write(f"could not start: {exc}\n".encode())
                running[name] = None
    finished: dict[str, tuple[int, float]] = {}
    while len(finished) < len(running):
        for name, proc in running.items():
            if name in finished:
                continue
            code = 127 if proc is None else proc.poll()
            if code is not None:
                finished[name] = (code, time.monotonic() - started)
        time.sleep(0.2)
    failed = []
    for name, (code, elapsed) in sorted(finished.items(), key=lambda item: item[1][1]):
        status = "PASS" if code == 0 else f"FAIL (exit {code})"
        print(f"  [{status:>13}] {name:<8} {elapsed:5.1f}s  {' '.join(commands[name][4:])}")
        if code != 0:
            failed.append(name)
    for name in failed:
        text = (logs / f"{name}.log").read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"\n--- {name}: last lines of {logs / (name + '.log')} ---")
        print("\n".join(text[-25:]))
    total = time.monotonic() - started
    verdict = "PASS" if not failed else f"FAIL ({', '.join(failed)})"
    print(f"\ncheck-fast {verdict} in {total:.0f}s -- `make check` remains the merge gate")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="check_fast")
    parser.add_argument("--make", default="make")
    args = parser.parse_args(argv)
    try:
        prereqs = check_prerequisites((ROOT / "Makefile").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"check-fast FAIL: {exc}")
        return 1
    commands = {name: [args.make, "--no-print-directory", "-o", "install", *targets]
                for name, targets in legs(prereqs).items()}
    return run_legs(commands, LOGS)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
