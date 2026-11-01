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

ONE RUN AT A TIME PER WORK TREE (#52). Two runs overlapped in one tree -- a commit hook's and the
post-edit hook's -- and 12 tracked files were gone: a leg that empties files and puts them back,
racing itself. DevFlow's record checks -- the Makefile's own `check:` line, less the code legs -- move
nothing; every other target runs the project's own commands, which may: the code legs, a project's own
legs, and a `check:` prerequisite `stack.mk` adds to the records leg. A run whose plan holds such a target
holds `build/check-fast/lock`, an flock of its own (no leg inherits it, so a process a leg leaves running
keeps nothing); a second one waits up to 15 minutes, then says NOT RUNNABLE and exits 2. A records-only
run of DevFlow's record checks alone takes no lock and never waits; it logs under
`build/check-fast/only-records/`. `make check` (serial) takes no lock.

    python3 scripts/check_fast.py [--make make] [--plan] [--without TARGET...] [--with TARGET...]

`--plan` prints `leg: target target...`, one leg per line, and runs nothing.
`--without` leaves out `check:` prerequisites, and `--with` adds make targets outside `check:`, each a leg of
its own: `make check-red` and `make check-docs` are check-fast so changed (`scripts/commit_gate.py`). A name
`--without` finds in no `check:` line, or `--with` finds no target for or finds in `check:` already, FAILS.
`--plan` prints `leg: target target...`, one leg per line, and runs nothing. `--only-records` runs the
records leg alone: the post-edit hook passes it after a document edit (`scripts/post_edit_scope.py`).
`--lock-wait S` waits S seconds for the lock, not 15 minutes.
Every leg's `make closes` grades only the close records changed since the merge-base
(`CLOSES_CHANGED=1`) unless the caller set CLOSES_CHANGED itself: empty grades them all, as `make check`
does. `/start-session` grades them all with `make closes` beside this run.
Exit: 0 every leg passed (or the plan was printed) · 1 a leg failed, or the legs cannot be derived
or the two settings are invalid · 2 cannot run (make not installed, or another run kept the lock).
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
#: Capped at four workers: on a small suite starting eight cost more than the tests (process audit F-12).
PYTEST_PARALLEL = "-n auto --maxprocesses 4 --dist loadgroup"
TAIL = 30
#: How long a run that starts a code leg waits for another one in this work tree (#52, the owner's ruling).
LOCK_WAIT_S = 15 * 60


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


def without(prereqs: list[str], names: list[str]) -> tuple[list[str], list[str]]:
    """(the prerequisites left, problems): `--without` drops these `check:` prerequisites, and a name that is
    not one fails, as CHECK_FAST_FORMS does, so a typo cannot keep a leg that was meant to go."""
    problems = [f"`{name}` in --without is not a prerequisite of `check:`" for name in names if name not in prereqs]
    return [t for t in prereqs if t not in names], problems


def added(makefile: str, names: list[str]) -> list[str]:
    """The problems with `--with`: each name must be a make target, and not a `check:` prerequisite already."""
    prereqs = check_prerequisites(makefile)
    return [f"`{name}` in --with is a prerequisite of `check:` already" if name in prereqs else
            f"`{name}` in --with is not a make target"
            for name in names if name in prereqs or not re.search(rf"^{re.escape(name)}:(?![:=])", makefile, re.M)]


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
    # check-fast grades only the close records this branch changed; `make check`, the gate and CI grade
    # every one (v7.2: 42 records took 17 s on every edit). A caller's own value stands; empty grades every
    # close record (v7.3, the review's M1).
    env.setdefault("CLOSES_CHANGED", "1")
    if "test" in targets:             # the `test` target itself; a form of it brings its own
        env["PYTEST_ADDOPTS"] = f"{env.get('PYTEST_ADDOPTS', '')} {PYTEST_PARALLEL}".strip()
    return env


def take_lock(wait_s: float):
    """This work tree's lock (#52), held by this run alone while the returned file is open: Python opens it
    non-inheritable, so no leg, and no process a leg leaves running, keeps it. None when another run kept it
    past `wait_s`."""
    LOGS.mkdir(parents=True, exist_ok=True)
    held = (LOGS / "lock").open("a+b")
    deadline, told = time.monotonic() + wait_s, False
    while True:
        try:
            if os.name == "nt":
                import msvcrt
                held.seek(0)
                msvcrt.locking(held.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return held
        except OSError:
            if time.monotonic() >= deadline:
                held.close()
                return None
            if not told:
                print(f"check-fast: another run holds this work tree's lock ({LOGS / 'lock'}) -- waiting, up to "
                      f"{wait_s / 60:g} min", flush=True)
                told = True
            time.sleep(0.25)


def start(plan: dict[str, list[str]], make: str, forms: dict[str, str],
          logs: Path) -> dict[str, subprocess.Popen[bytes] | None]:
    """Every leg at once, each writing its own log; `None` for a leg that could not start."""
    running: dict[str, subprocess.Popen[bytes] | None] = {}
    for name, prereqs in plan.items():
        targets = [forms.get(t, t) for t in prereqs]
        with (logs / f"{name}.log").open("wb") as log:
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


def run_legs(plan: dict[str, list[str]], make: str, forms: dict[str, str], logs: Path = LOGS) -> int:
    """Start every leg at once, each to its own log; 0 only if every one exits 0."""
    logs.mkdir(parents=True, exist_ok=True)
    for stale in logs.glob("*.log"):
        stale.unlink()
    print(f"check-fast: {len(plan)} leg(s) from `check:` in {MAKEFILE}, logs in {logs}", flush=True)
    started = time.monotonic()
    # Stopped from outside -- Ctrl-C, or a hook's timeout -- leaves no leg running behind it.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(128 + signal.SIGTERM))
    running = start(plan, make, forms, logs)
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
        log = logs / f"{name}.log"
        text = log.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"\n--- {name}: last {min(TAIL, len(text))} line(s) of {log} ---")
        print("\n".join(text[-TAIL:]))
    total = time.monotonic() - started
    verdict = "PASS" if not failed else f"FAIL ({', '.join(failed)})"
    print(f"\ncheck-fast {verdict} in {total:.1f}s -- `make check` remains the merge gate")
    return 1 if failed else 0


def main(argv: list[str]) -> int:  # noqa: C901
    for stream in (sys.stdout, sys.stderr):        # a cp1254 console prints `?`, never crashes
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="replace")
    parser = argparse.ArgumentParser(prog="check_fast",
                                     description="the legs of `make check`, run side by side")
    parser.add_argument("--make", default="make", help="the make to start each leg with")
    parser.add_argument("--plan", action="store_true", help="print the legs and run nothing")
    parser.add_argument("--without", nargs="+", default=[], metavar="TARGET",
                        help="`check:` prerequisites to leave out (`make check-red`, `make check-docs`)")
    parser.add_argument("--with", dest="extra", nargs="+", default=[], metavar="TARGET",
                        help="make targets outside `check:`, each run as a leg of its own (`make check-red`)")
    parser.add_argument("--only-records", action="store_true",
                        help="only the records leg: the post-edit hook after a document edit")
    parser.add_argument("--lock-wait", type=float, default=LOCK_WAIT_S, metavar="S",
                        help="seconds to wait for another run in this work tree (default: 15 minutes)")
    args = parser.parse_args(argv)
    if shutil.which(args.make) is None:
        print(f"check-fast CANNOT RUN: {args.make} not installed: cannot run the legs of "
              "`make check`")
        return 2
    try:
        # make merges every `check:` rule it reads, and it reads `stack.mk` too: a gate a project
        # adds there runs in `make check`, so it must run here.
        makefile = MAKEFILE.read_text(encoding="utf-8")
        text = makefile
        if STACK_MK.is_file():
            text += "\n" + STACK_MK.read_text(encoding="utf-8")
        prereqs, dropped = without(check_prerequisites(text), args.without)
        # DevFlow's record checks -- the Makefile's own `check:` line, less the code legs -- move nothing; any
        # other target runs the project's own commands, which may move files (#52): `stack.mk`'s in the records
        # leg too (the review's B1), and a `--with` target.
        devflow = set(check_prerequisites(makefile)) - set(CODE_LEGS)
        own, forms, problems = settings(check_prerequisites(text), *config(args.make))
        problems += dropped + added(text, args.extra)
        own = [t for t in own if t in prereqs]
    except (OSError, ValueError) as exc:
        print(f"check-fast FAIL: {exc}")
        return 1
    for problem in problems:
        print(f"check-fast FAIL: {problem}")
    if problems:
        return 1
    plan = legs(prereqs, own)
    plan.update({t: [t] for t in args.extra})
    if args.only_records:
        # A document cannot change what lint, the type checker or the tests read (v7.2).
        plan = {RECORDS: plan[RECORDS]} if RECORDS in plan else {}
        if not plan:
            print("check-fast: no records leg in `check:` -- nothing a document edit can change")
            return 0
    if args.plan:
        for name, targets in plan.items():
            print(f"{name}: {shown(targets, forms)}")
        return 0
    held = None
    if any(t not in devflow for targets in plan.values() for t in targets):
        try:
            held = take_lock(args.lock_wait)
        except OSError as exc:
            print(f"check-fast NOT RUNNABLE: cannot take this work tree's lock ({LOGS / 'lock'}): {exc}")
            return 2
        if held is None:
            print(f"check-fast NOT RUNNABLE: another check-fast run in this work tree kept its lock for "
                  f"{args.lock_wait / 60:g} min ({LOGS / 'lock'}) -- two at once can race a leg that moves files "
                  "(#52). Not a finding: run it again when that one ends")
            return 2
    try:
        return run_legs(plan, args.make, forms, LOGS / "only-records" if args.only_records else LOGS)
    finally:
        if held:
            held.close()


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
