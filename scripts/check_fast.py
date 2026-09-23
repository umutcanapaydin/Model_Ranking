#!/usr/bin/env python3
"""`make check-fast`: the legs of `make check`, run side by side.

`make check` is unchanged: serial, and what a merge is judged by (`make gate` at pre-push and
`/pre-merge`, and CI). This is the one the post-edit hook runs, after every edit, where waiting for
each leg in turn is the cost.

WHERE THE TIME GOES. `make check` runs its prerequisites one after another, so the slow ones -- the
type checker and the test suite -- wait for each other and for every record check. Here each code
leg is its own process, the record checks share one, and pytest runs on every CPU.

DERIVED, NOT ENUMERATED. The legs are read from the `check:` prerequisite line(s) of the Makefile
and of `stack.mk`, which it includes: a gate added to `check` joins a leg here without an edit, and
one removed leaves it. The only names
kept here are the three code legs (`CODE_LEGS`), which are the stack's own commands and each long
enough to be the critical path; every other prerequisite runs in the `records` leg, in the order
`check:` lists it. No prerequisite at all is a FAILURE: a check-fast with no legs would pass over
nothing.

A PROJECT'S OWN LEGS AND FORMS. Two Makefile variables, empty by default and set in `stack.mk`
(INSTALL.md), read here through `make check-fast-config`:
  * `CHECK_FAST_OWN_LEGS` -- `check:` prerequisites that each get a leg of their own, named after
    the target, beside the code legs (a Swift suite is as long as the Python one);
  * `CHECK_FAST_FORMS` -- `target=form` pairs: here, and only here, make target `form` runs in place
    of `target` (`swift-test=swift-test-parallel`). `make check` never uses a form: the serial run
    stays what a merge is judged by.
A name in either one that `check:` does not list, or a pair that is not `target=form`, FAILS: a
setting that silently matches nothing is a leg the author believes runs. `--plan` prints a replaced
target as `target=form`, so every `check:` prerequisite is still visible under its own name.

ONE INSTALL. The `check-fast` target runs `install` once, as its prerequisite, and every leg is
started as `make --no-print-directory -o install <targets...>`: concurrent `pip install -e` runs into
one virtualenv race each other.

THE TEST LEG runs pytest as `-n auto --dist loadgroup` (pytest-xdist), passed in `PYTEST_ADDOPTS`
so the `test` recipe is the very one `make check` runs. It is ONE pytest run over several workers,
so coverage and `--cov-fail-under` still apply once, to the whole suite. A test that must not run
at the same time as others -- it binds a port, writes a shared file, spends a rate-limited quota --
carries `@pytest.mark.xdist_group("serial")`: every test in that group runs on one worker, in
order. A test that is red only in parallel teaches people to ignore red; mark it, do not retry it.

Each leg writes its own log under `build/check-fast/`. Every leg is reported, a failed one with the
tail of its log.

    python3 scripts/check_fast.py [--make make] [--plan]

`--plan` prints `leg: target target...`, one leg per line, and runs nothing.
Exit: 0 every leg passed (or the plan was printed) · 1 a leg failed, or the legs cannot be derived
or the two settings are invalid · 2 cannot run (make not installed).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = ROOT / "Makefile"
#: The project's own make file, which the Makefile includes: a `check:` line there adds gates too.
STACK_MK = ROOT / "stack.mk"
LOGS = ROOT / "build" / "check-fast"

#: Each its own leg, named after itself: the stack's code legs (`stack.mk` binds them on a stack
#: other than python), and each one long enough to be the critical path on a real project.
CODE_LEGS: tuple[str, ...] = ("lint", "typecheck", "test")
#: Every other `check:` prerequisite: DevFlow's own checks, seconds each, one after another.
RECORDS = "records"
#: How the leg holding `test` runs pytest. Appended to any PYTEST_ADDOPTS already set.
PYTEST_PARALLEL = "-n auto --dist loadgroup"
TAIL = 30


def check_prerequisites(makefile: str) -> list[str]:
    """Every prerequisite of `check:`, in order, once -- from every `check:` rule line."""
    lines = makefile.splitlines()
    found: list[str] = []
    i = 0
    while i < len(lines):
        if re.match(r"check:(?![:=])", lines[i]):
            text = lines[i][len("check:"):]
            while text.endswith("\\") and i + 1 < len(lines):   # a continued line
                i += 1
                text = text[:-1] + " " + lines[i]
            for target in text.split("#", 1)[0].split():
                if target != "|" and target not in found:
                    found.append(target)
        i += 1
    if not found:
        raise ValueError("the `check:` line in the Makefile has no prerequisites -- a check-fast "
                         "with no legs would pass over nothing")
    return found


def config(make: str) -> tuple[list[str], list[str]]:
    """(own legs, form pairs) as the Makefile has them, `stack.mk` included -- asked of make itself,
    so a value set in `stack.mk`, the Makefile or on the command line is read the same way."""
    try:
        # `make` is this repository's own, or the one the caller named with --make.
        r = subprocess.run([make, "--no-print-directory", "-s", "check-fast-config"],  # noqa: S603
                           cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace",
                           timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"`make check-fast-config` could not run: {exc}") from exc
    got = {k.strip(): v.split() for k, _, v in (ln.partition(":") for ln in r.stdout.splitlines())
           if k.strip() in ("own", "forms")}
    if r.returncode != 0 or set(got) != {"own", "forms"}:
        tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or ["(no output)"]
        raise ValueError(f"`make check-fast-config` did not print its two lines `own:` and "
                         f"`forms:` (exit {r.returncode}: {tail[0][:100]})")
    return got["own"], got["forms"]


def settings(prereqs: list[str], own: list[str],
             pairs: list[str]) -> tuple[list[str], dict[str, str], list[str]]:
    """(own legs, {target: form}, problems): every name must be a `check:` prerequisite."""
    problems: list[str] = []
    for t in own:
        if t not in prereqs:
            problems.append(f"`{t}` in CHECK_FAST_OWN_LEGS is not a prerequisite of `check:`")
    forms: dict[str, str] = {}
    for pair in pairs:
        target, eq, form = pair.partition("=")
        if not (target and eq and form) or "=" in form:
            problems.append(f"`{pair}` in CHECK_FAST_FORMS is not target=form")
        elif target not in prereqs:
            problems.append(f"`{target}` in CHECK_FAST_FORMS is not a prerequisite of `check:`")
        elif target in forms:
            problems.append(f"`{target}` has two forms in CHECK_FAST_FORMS -- one would be dropped "
                            "without a word")
        else:
            forms[target] = form
    return list(dict.fromkeys(own)), forms, problems


def legs(prereqs: list[str], own: list[str] | None = None) -> dict[str, list[str]]:
    """Every prerequisite in exactly one leg: code legs and a project's own legs alone, everything
    else in `records`."""
    alone = set(CODE_LEGS) | set(own or ())
    out: dict[str, list[str]] = {t: [t] for t in prereqs if t in alone}
    rest = [t for t in prereqs if t not in alone]
    if rest:
        out.setdefault(RECORDS, []).extend(rest)
    return out


def leg_env(targets: list[str]) -> dict[str, str]:
    env = dict(os.environ)
    if "test" in targets:             # the `test` target itself; a form of it brings its own
        env["PYTEST_ADDOPTS"] = f"{env.get('PYTEST_ADDOPTS', '')} {PYTEST_PARALLEL}".strip()
    return env


def start(plan: dict[str, list[str]], make: str,
          forms: dict[str, str]) -> dict[str, subprocess.Popen[bytes] | None]:
    """Every leg at once, each writing its own log; `None` for a leg that could not start."""
    running: dict[str, subprocess.Popen[bytes] | None] = {}
    for name, prereqs in plan.items():
        targets = [forms.get(t, t) for t in prereqs]
        with (LOGS / f"{name}.log").open("wb") as log:
            try:
                # `make` and target names read from this repository's own Makefile.
                # Each leg in its own process group, so stopping it stops what it started.
                running[name] = subprocess.Popen(                          # noqa: S603
                    [make, "--no-print-directory", "-o", "install", *targets],
                    cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, env=leg_env(targets),
                    start_new_session=True)
            except OSError as exc:
                log.write(f"could not start: {exc}\n".encode())
                running[name] = None
    return running


def stop(proc: subprocess.Popen[bytes]) -> None:
    """End a leg and everything it started (make, the shell, pytest's workers)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],  # noqa: S603, S607
                       capture_output=True, check=False)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except OSError:
            proc.terminate()


def wait(running: dict[str, subprocess.Popen[bytes] | None],
         started: float) -> dict[str, tuple[int, float]]:
    """{leg: (exit code, seconds since the start)} once every leg has finished."""
    finished: dict[str, tuple[int, float]] = {}
    while len(finished) < len(running):
        for name, proc in running.items():
            code = 127 if proc is None else proc.poll()
            if name not in finished and code is not None:
                finished[name] = (code, time.monotonic() - started)
        time.sleep(0.1)
    return finished


def shown(targets: list[str], forms: dict[str, str]) -> str:
    """A leg's targets as `--plan` prints them: a replaced one as `target=form`."""
    return " ".join(f"{t}={forms[t]}" if t in forms else t for t in targets)


def run_legs(plan: dict[str, list[str]], make: str, forms: dict[str, str]) -> int:
    """Start every leg at once, each to its own log; 0 only if every one exits 0."""
    LOGS.mkdir(parents=True, exist_ok=True)
    for stale in LOGS.glob("*.log"):
        stale.unlink()
    print(f"check-fast: {len(plan)} leg(s) from `check:` in {MAKEFILE}, logs in {LOGS}", flush=True)
    started = time.monotonic()
    # Stopped from outside -- Ctrl-C, or a hook's timeout -- leaves no leg running behind it.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(128 + signal.SIGTERM))
    running = start(plan, make, forms)
    try:
        finished = wait(running, started)
    finally:
        for proc in running.values():
            if proc is not None and proc.poll() is None:
                stop(proc)

    failed = []
    for name, (code, elapsed) in sorted(finished.items(), key=lambda item: item[1][1]):
        status = "PASS" if code == 0 else f"FAIL (exit {code})"
        print(f"  [{status:>13}] {name:<9} {elapsed:6.1f}s  {shown(plan[name], forms)}")
        if code != 0:
            failed.append(name)
    for name in failed:
        log = LOGS / f"{name}.log"
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"\n--- {name}: last {min(TAIL, len(text))} line(s) of {log} ---")
        print("\n".join(text[-TAIL:]))
    total = time.monotonic() - started
    verdict = "PASS" if not failed else f"FAIL ({', '.join(failed)})"
    print(f"\ncheck-fast {verdict} in {total:.1f}s -- `make check` remains the merge gate")
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    for stream in (sys.stdout, sys.stderr):        # a cp1254 console prints `?`, never crashes
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="check_fast",
                                     description="the legs of `make check`, run side by side")
    parser.add_argument("--make", default="make", help="the make to start each leg with")
    parser.add_argument("--plan", action="store_true", help="print the legs and run nothing")
    args = parser.parse_args(argv)
    if shutil.which(args.make) is None:
        print(f"check-fast CANNOT RUN: {args.make} not installed: cannot run the legs of "
              "`make check`")
        return 2
    try:
        # make merges every `check:` rule it reads, and it reads `stack.mk` too: a gate a project
        # adds there runs in `make check`, so it must run here.
        text = MAKEFILE.read_text(encoding="utf-8")
        if STACK_MK.is_file():
            text += "\n" + STACK_MK.read_text(encoding="utf-8")
        prereqs = check_prerequisites(text)
        own, forms, problems = settings(prereqs, *config(args.make))
    except (OSError, ValueError) as exc:
        print(f"check-fast FAIL: {exc}")
        return 1
    for problem in problems:
        print(f"check-fast FAIL: {problem}")
    if problems:
        return 1
    plan = legs(prereqs, own)
    if args.plan:
        for name, targets in plan.items():
            print(f"{name}: {shown(targets, forms)}")
        return 0
    return run_legs(plan, args.make, forms)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
