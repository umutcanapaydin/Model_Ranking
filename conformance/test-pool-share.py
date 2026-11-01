#!/usr/bin/env python3
"""A test inside run-all's pool gets its share of the CPUs, and run-all starts the longest tests first.

WHY (v7.3.1, #114). #106 let test-deploy-classes and test-git-hooks run their cases side by side, eight at a
time. Inside run-all's own pool of eight that made 64, and the warm gate got slower, not faster: 18.3 s to
19.4 s. And the pool started the tests in name order, so test-pr-check, test-sandbox and test-statusline,
which wait more than they compute, started last and held the leg. So run-all hands each test DEVFLOW_SHARE,
its share (twice the CPUs over the pool's size; 1 when DEVFLOW_JOBS is set or unreadable), and starts the
tests the longest first by their last run here, a new test first. The order only schedules: every test still
runs once, and the report keeps the name order.

The share is its own variable, read only by a test's own pool. Passed as DEVFLOW_JOBS, it also narrowed every
runner a test starts: test-delivered-tree's nested run-all ran two tests at a time, and inside falsify two
whole-suite recipes ran past their 180 s. falsify.py hands its recipes no share.

Through the real entry point, in a throwaway tree: run-all.py with probe tests that log what they were handed
and when they started; and lib_record.pool_jobs as a test's own pool and as a runner read it.

Exit: 0 every case behaves - 1 one does not.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CPUS = os.cpu_count() or 1
PROBE = ('"""A probe."""\nimport os, pathlib, time\n'
         'with open(os.environ["POOL_LOG"], "a") as f:\n'
         '    e = os.environ.get\n'
         '    f.write(f"{pathlib.Path(__file__).name} {e(\'DEVFLOW_SHARE\', \'-\')}/{e(\'DEVFLOW_JOBS\', \'-\')} {time.monotonic()}\\n")\n')
NAMES = ("test-a.py", "test-b.py", "test-c.py")


def env(**extra: str) -> dict:
    e = {k: v for k, v in os.environ.items()
         if k not in ("DEVFLOW_JOBS", "DEVFLOW_SHARE", "CI", "GITHUB_ACTIONS", "DEVFLOW_FRESH")}
    return {**e, **extra}


def run_all(pkg: pathlib.Path, **extra: str) -> tuple[list[tuple[str, str]], str]:
    """Run the copied run-all.py; (each probe's name and its `DEVFLOW_SHARE/DEVFLOW_JOBS` in start order, the report)."""
    log = pkg / "pool.log"
    log.unlink(missing_ok=True)
    r = subprocess.run([sys.executable, str(pkg / "conformance" / "run-all.py")], cwd=pkg, capture_output=True,
                       text=True, env=env(POOL_LOG=str(log), DEVFLOW_VERBOSE="1", **extra), timeout=120)
    rows = [ln.split() for ln in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
    return [(n, j) for n, j, _ in sorted(rows, key=lambda x: float(x[2]))], r.stdout


def main() -> int:
    bad: list[str] = []
    count = 0

    def case(name: str, ok: bool, detail: str = "") -> None:
        nonlocal count
        count += 1
        if not ok:
            bad.append(f"  {name}" + (f": {detail}" if detail else ""))

    with tempfile.TemporaryDirectory() as tmp:
        pkg = pathlib.Path(tmp)
        (pkg / "conformance").mkdir()
        for f in ("run-all.py", "lib_record.py"):
            shutil.copy(HERE / f, pkg / "conformance" / f)
        for n in NAMES:
            (pkg / "conformance" / n).write_text(PROBE, encoding="utf-8")
        durations = pkg / "build" / "conformance-cache" / "durations.json"

        share = str(max(1, 2 * CPUS // min(8, CPUS)))
        got, _ = run_all(pkg)
        case(f"run-all hands each test its share of {CPUS} CPU(s), DEVFLOW_SHARE={share}, and leaves DEVFLOW_JOBS "
             "alone, so a runner the test starts keeps its own width", sorted(got) == [(n, f"{share}/-") for n in NAMES],
             str(got))
        case("run-all's share times its pool's size never passes twice the CPUs",
             bool(got) and all(j.split("/")[0].isdigit() and int(j.split("/")[0]) * min(8, CPUS)
                               <= 2 * max(CPUS, min(8, CPUS)) for _, j in got), str(got))
        case("after a run, each test's time is remembered for the next one's order",
             durations.is_file() and sorted(json.loads(durations.read_text(encoding="utf-8"))) == list(NAMES))
        got, _ = run_all(pkg, DEVFLOW_JOBS="1")
        case("a set DEVFLOW_JOBS gives each test 1: DEVFLOW_JOBS=1 runs each test's own pool one at a time",
             sorted(got) == [(n, "1/1") for n in NAMES], str(got))
        got, _ = run_all(pkg, DEVFLOW_JOBS="lots")
        case("an unreadable DEVFLOW_JOBS gives each test 1", sorted(got) == [(n, "1/lots") for n in NAMES], str(got))

        durations.parent.mkdir(parents=True, exist_ok=True)
        durations.write_text(json.dumps({"test-a.py": 1.0, "test-c.py": 9.0, "test-gone.py": 99.0}), encoding="utf-8")
        got, out = run_all(pkg, DEVFLOW_JOBS="1")
        case("the longest last time starts first, a test with no time before every timed one",
             [n for n, _ in got] == ["test-b.py", "test-c.py", "test-a.py"], str(got))
        lines = [ln for ln in out.splitlines() if "[PASS" in ln]
        case("the report keeps the name order, whatever the start order",
             [ln.split()[2] for ln in lines] == list(NAMES), "\n" + out)
        for broken in ("{not json", '["a list"]', '{"test-a.py": "slow", "test-c.py": null}',
                       '{"test-a.py": 1' + "0" * 400 + "}", "[" * 100000):
            durations.write_text(broken, encoding="utf-8")
            got, _ = run_all(pkg, DEVFLOW_JOBS="1")
            case(f"a remembered order that does not read ({broken[:12]}) is the name order, every test once",
                 [n for n, _ in got] == list(NAMES), str(got))

    # lib_record.pool_jobs as a test's own pool reads it (inside=True) and as a runner reads it.
    def jobs(inside: bool, **extra: str) -> str:
        code = f"import sys; sys.path.insert(0, {str(HERE)!r}); import lib_record; print(lib_record.pool_jobs(8, {inside})[0])"
        return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env(**extra),
                              timeout=60).stdout.strip()
    alone = str(min(8, CPUS))
    case("a test's own pool takes the share run-all handed it", jobs(True, DEVFLOW_SHARE="3", DEVFLOW_JOBS="1") == "3")
    case("a test's own pool with an unreadable share runs one at a time", jobs(True, DEVFLOW_SHARE="x") == "1")
    case(f"a test run on its own keeps min(8, CPUs) = {alone}", jobs(True) == alone)
    # 11 is above the cap of 8, so no CPU count can make a runner's width look like the share.
    case("a runner ignores DEVFLOW_SHARE: a run-all inside a test keeps its width", jobs(False, DEVFLOW_SHARE="11") == alone)
    # The tests that run a pool of their own take the share, asked of their own jobs() with the module loaded.
    for name in ("test-deploy-classes.py", "test-git-hooks.py"):
        code = (f"import importlib.util as u; s = u.spec_from_file_location('t', {str(HERE / name)!r}); "
                "m = u.module_from_spec(s); s.loader.exec_module(m); print(m.jobs())")
        got = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                             env=env(DEVFLOW_SHARE="11")).stdout.strip()
        case(f"{name} sizes its pool by the share run-all hands it", got == "11", got or "no answer")
        src = (HERE / name).read_text(encoding="utf-8")
        case(f"{name} runs its pool at jobs() and reads no CPU count of its own",
             "max_workers=jobs()" in src and "cpu_count" not in src)

    if bad:
        print("test-pool-share FAIL (conformance/run-all.py and lib_record.pool_jobs):")
        print("\n".join(bad))
        return 1
    print(f"test-pool-share PASS: {count} cases -- each test in run-all's pool gets its share of the {CPUS} "
          "CPU(s), and run-all starts the longest first while it reports in name order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
