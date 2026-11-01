#!/usr/bin/env python3
"""Two `make check-fast` runs in one work tree take turns, so a leg that moves files never races itself (#52).

WHY (#52, Project-J). Two check-fast runs overlapped in one work tree -- a commit hook's and the post-edit
hook's -- and 12 tracked files were gone afterwards: the shape of a leg that empties files and puts them
back, racing a second run of itself. DevFlow's own record checks move nothing; every other target runs the
project's own commands, which may: the code legs, a project's own legs, and a `check:` prerequisite that
`stack.mk` adds to the records leg. So `scripts/check_fast.py` holds a per-tree lock while a run whose plan
holds such a target is in progress: a second one waits (15 minutes by default), then says NOT RUNNABLE. A
records-only run whose leg holds only DevFlow's record checks takes no lock and does not wait. The lock is the
run's own: a process a leg leaves running does not keep it.

The cases run check_fast.py in a throwaway git repository whose `test` leg empties a tracked file, waits,
and puts it back -- #52's race -- under a minimal Makefile:
  * two runs at once leave the file as it was, and both pass;
  * a run that cannot get the lock in time exits 2 and says NOT RUNNABLE;
  * `--only-records` with DevFlow's record checks alone finishes while the lock is held;
  * `--only-records` whose records leg runs a `stack.mk` command waits its turn, and that file survives too;
  * a leg that leaves a process running does not keep the lock from the next run.

No case sleeps for a fixed time (v7.3.1, gate speed). A leg holds the emptied file until the test creates `go`.
The test creates it once the second run is parked inside the same leg (the race itself), or once it printed that
it waits for the lock AND then stayed out of the leg, alive, for QUIET_S more: the message alone is no proof that
it waited (v7.3.1 review, B1). On a loaded machine a case waits longer; it never grades less.

Exit: 0 every case behaves - 1 one does not - 2 not evaluable here (no make or git).
"""
import concurrent.futures
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib_record import missing_tool, scrubbed_env  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEEP = "line one\nline two\n"
# The leg #52 measured: save a tracked file, empty it, wait, put it back. Two of these at once lose it.
# It waits for the test's `go` file (180 s of wall time at most) and says in `parked` that it is waiting.
# LEAVE_CHILD: the leg also leaves a process running when it ends, as a test's server can.
HOLD = (r"echo {leg} >> parked && end=$$(($$(date +%s) + 180)) && "
        r"while [ ! -e go ] && [ $$(date +%s) -lt $$end ]; do sleep 0.05; done")
MAKEFILE = """\
.PHONY: install check check-fast-config records-probe test
install:
\t@true
check-fast-config:
\t@echo "own: "
\t@echo "forms: "
check: records-probe test
records-probe:
\t@true
test:
\t@cp keep.txt keep.txt.save && : > keep.txt && {hold} && mv keep.txt.save keep.txt$(if $(LEAVE_CHILD), && {{ sleep 60 & echo $$! > child.pid; }})
""".format(hold=HOLD.format(leg="test"))
# A project's own `check:` prerequisite, in the records leg: the same race on another file.
STACK_MK = """\
check: mover
mover:
\t@cp keep2.txt keep2.txt.save && : > keep2.txt && {hold} && mv keep2.txt.save keep2.txt
""".format(hold=HOLD.format(leg="mover"))
WAITING = "another run holds this work tree's lock"
# How long a run that says it waits must then stay out of the held leg, alive: a run that printed the message and
# went on without the lock reaches the leg well inside it.
QUIET_S = 3.0


def tree(base: pathlib.Path, mover: bool = False) -> pathlib.Path:
    t = base / "proj"
    (t / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / "scripts" / "check_fast.py", t / "scripts" / "check_fast.py")
    (t / "Makefile").write_text(MAKEFILE + ("-include stack.mk\n" if mover else ""), encoding="utf-8")
    if mover:
        (t / "stack.mk").write_text(STACK_MK, encoding="utf-8")
        (t / "keep2.txt").write_text(KEEP, encoding="utf-8")
    (t / "keep.txt").write_text(KEEP, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=t, check=True, env=scrubbed_env())
    return t


class Run:
    """One check_fast.py run in the tree, its output in a log beside the tree, read while it runs."""

    def __init__(self, t: pathlib.Path, *args: str, **extra: str):
        self.log = t.parent / f"run-{len(list(t.parent.glob('run-*.log')))}.log"
        env = scrubbed_env(extra)
        with self.log.open("w", encoding="utf-8") as out:
            self.proc = subprocess.Popen([sys.executable, str(t / "scripts" / "check_fast.py"), "--make", "make",
                                          *args], cwd=t, env=env, stdout=out, stderr=subprocess.STDOUT)

    def output(self) -> str:
        return self.log.read_text(encoding="utf-8", errors="replace")

    def finish(self, timeout: float = 300) -> tuple[int, str]:
        try:
            return self.proc.wait(timeout=timeout), self.output()
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            return -9, self.output() + f"\n(killed after {timeout:g} s)"


def until(condition, limit: float = 120) -> bool:
    """Poll `condition` until it holds; False when it never did within `limit` seconds (a generous bound)."""
    end = time.monotonic() + limit
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.05)
    return False


def parked(t: pathlib.Path, leg: str) -> int:
    """How many runs are inside `leg`, holding its file emptied."""
    try:
        return (t / "parked").read_text(encoding="utf-8").split().count(leg)
    except OSError:
        return 0


def go(t: pathlib.Path) -> None:
    """Let every held leg put its file back."""
    (t / "go").touch()


def contend(t: pathlib.Path, other: "Run", leg: str) -> list[str]:
    """While the first run holds `leg`: does `other` wait for the lock? It is graded as waiting only when it says
    so and then, for QUIET_S more, stays alive and out of the leg. A run that enters the leg is the race (#52)."""
    until(lambda: WAITING in other.output() or parked(t, leg) >= 2 or other.proc.poll() is not None)
    if WAITING in other.output() and parked(t, leg) < 2:
        until(lambda: parked(t, leg) >= 2 or other.proc.poll() is not None, QUIET_S)
    if parked(t, leg) >= 2:
        return [f"a second run entered the {leg} leg while the first held it -- it did not wait for the lock (#52)"]
    if WAITING not in other.output():
        return ["the second run neither waited for the lock nor reached its leg -- nothing was graded"]
    if other.proc.poll() is not None:
        return ["the second run said it waits for the lock, then ended while the first still held it"]
    return []


def verdict(out: str) -> str:
    """A run's verdict line only: a racing leg's own errors are the defect, not this test crashing."""
    return ([ln for ln in out.splitlines() if ln.startswith("check-fast ")][-1:] or ["(no verdict)"])[0]


def overlap(base: pathlib.Path) -> list[str]:
    """Two full runs at once: the second waits, the file survives, both pass."""
    bad: list[str] = []
    t = tree(base)
    first, second = Run(t), None
    try:
        if until(lambda: parked(t, "test") >= 1):
            second = Run(t)
            bad += contend(t, second, "test")
    finally:
        go(t)
    rc1, out1 = first.finish()
    if second is None:
        return ["the first run's test leg never started -- nothing was graded"]
    rc2, out2 = second.finish()
    kept = (t / "keep.txt").read_text(encoding="utf-8")
    if kept != KEEP:
        bad.append(f"two runs at once left keep.txt as {kept!r}, not as it was: the leg raced itself (#52)")
    for name, rc, out in (("first", rc1, out1), ("second", rc2, out2)):
        if rc != 0:
            bad.append(f"the {name} of two overlapping runs exited {rc}, not 0: {verdict(out)}")
    return bad


def waiting(base: pathlib.Path) -> list[str]:
    """While a full run holds the lock: a records-only run of DevFlow's checks finishes; a run past its wait stops."""
    bad: list[str] = []
    t = tree(base)
    first = Run(t)
    try:
        if not until(lambda: parked(t, "test") >= 1):
            bad.append("the long run's test leg never started -- the waiting cases were not graded")
            return bad
        rc_q, out_q = Run(t, "--only-records").finish(120)
        if rc_q != 0 or first.proc.poll() is not None:
            bad.append(f"`--only-records` did not finish while the lock was held (exit {rc_q}; "
                       f"the first run {'had already ended' if first.proc.poll() is not None else 'still ran'}): "
                       f"{verdict(out_q)}")
        rc_l, out_l = Run(t, "--lock-wait", "0.5").finish(120)
        if rc_l != 2 or "NOT RUNNABLE" not in out_l:
            bad.append(f"a run that waited past its limit exited {rc_l} without NOT RUNNABLE: {verdict(out_l)}")
    finally:
        go(t)
        first.finish()
    return bad


def project_records(base: pathlib.Path) -> list[str]:
    """B1 (the review): the records leg runs a project command from stack.mk, so a records-only run takes the lock."""
    bad: list[str] = []
    t = tree(base, mover=True)
    first, quick = Run(t), None
    try:
        if until(lambda: parked(t, "mover") >= 1):
            quick = Run(t, "--only-records")
            bad += contend(t, quick, "mover")
    finally:
        go(t)
    rc1, out1 = first.finish()
    if quick is None:
        return ["the full run's stack.mk leg never started -- the records-only case was not graded"]
    rc_q, out_q = quick.finish()
    kept = (t / "keep2.txt").read_text(encoding="utf-8")
    if kept != KEEP:
        bad.append(f"a records-only run beside a full one left keep2.txt as {kept!r}: its records leg runs "
                   "stack.mk's command and raced it (#52)")
    for name, rc, out in (("full run", rc1, out1), ("records-only run", rc_q, out_q)):
        if rc != 0:
            bad.append(f"the {name} beside the other exited {rc}, not 0: {verdict(out)}")
    return bad


def leftover(base: pathlib.Path) -> list[str]:
    """B2 (the review): a process a leg leaves running holds no lock; the next run does not wait for it."""
    bad: list[str] = []
    t = tree(base)
    go(t)  # no leg here is held
    child = None
    try:
        rc_r, out_r = Run(t, LEAVE_CHILD="1").finish(120)
        if (t / "child.pid").is_file():
            child = int((t / "child.pid").read_text(encoding="utf-8").strip() or 0) or None
        rc_n, out_n = Run(t, "--lock-wait", "3").finish(120)
        if rc_r != 0 or child is None:
            bad.append(f"the run that leaves a process running did not run as planted (exit {rc_r}): "
                       f"{verdict(out_r)}")
        elif rc_n != 0:
            bad.append(f"a process a leg left running kept the lock: the next run exited {rc_n}: "
                       f"{verdict(out_n)}")
    finally:
        if child:
            try:
                os.kill(child, signal.SIGTERM)
            except OSError:
                pass
    return bad


def main() -> int:
    for tool in ("make", "git"):
        if (why := missing_tool(tool, "run check_fast.py in a throwaway repository")):
            print(f"test-check-fast-lock NOT-EVALUABLE: {why}")
            return 2
    # Each case has its own tree, so they run side by side.
    with tempfile.TemporaryDirectory() as tmp, concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        cases = [overlap, waiting, project_records, leftover]
        found = list(pool.map(lambda c: c(pathlib.Path(tmp) / c.__name__), cases))
    bad = [b for case in found for b in case]
    if bad:
        print("test-check-fast-lock FAIL (scripts/check_fast.py, two runs in one work tree):")
        print("\n".join(f"  {b}" for b in bad))
        return 1
    print("test-check-fast-lock PASS: two check-fast runs in one tree took turns and left it as it was; a run past "
          "its wait says NOT RUNNABLE; the records-only run waits only when its leg runs a project command; a "
          "process a leg leaves running keeps no lock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
