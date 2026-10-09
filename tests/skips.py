"""#137: every reason a test may skip, in one place, with whether CI's test job has it.

A test that needs something a machine may lack says so with `@pytest.mark.needs("<what>")` (the
`artifact` marker is the same as `needs("artifact")`). `tests/conftest.py` hands collection to
`apply`, which skips a test where something it needs is absent here and, asked to, writes the count
of tests CI's test job will skip: those needing anything `NEEDS` marks as absent there.
`scripts/coverage_floor.py --derive` compares that count with `docs/skip-budget.txt` in
`make test`, so a wave sees a raise before it pushes, not after CI says so (it missed three times in
M18 and once in M19-W2).

No test skips any other way: `test_skip_budget_local.py` refuses a skip call or a `skipif` outside
this file, so the count is the tests' own and never a second list.
"""

from __future__ import annotations

import functools
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = Path("advisor.db")


@functools.cache
def offline() -> bool:
    """#122: whether a child process of this run is refused an outside peer by the operating system.
    A child names TEST-NET-1 over UDP, which sends no packet: outside a sandbox it simply succeeds;
    inside macOS's profile the system refuses it (EPERM), and in a Linux network namespace with only
    loopback there is no route to it (ENETUNREACH). A child, because this process carries a Python
    guard of its own that would answer first."""
    probe = ("import errno, socket\ns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
             "try:\n    s.connect(('192.0.2.1', 9))\nexcept OSError as e:\n"
             "    print('refused' if e.errno in (errno.EPERM, errno.EACCES, errno.ENETUNREACH) else e)\n")
    child = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=30, check=False)
    return child.stdout.strip() == "refused"


class Need(NamedTuple):
    what: str
    here: Callable[[], bool]
    in_ci: bool
    why: str


#: Each need: what it is, whether this machine has it, and whether CI's test job (`.github/workflows/
#: ci.yml`, ubuntu, `pytest`) has it, with the reason. A need CI lacks is a skip the budget counts.
#: `in_ci` is held equal to what `ci_job_facts` reads from the workflow (`test_ci_needs.py`, #182).
NEEDS: dict[str, Need] = {
    "artifact": Need("the built advisor.db", lambda: ARTIFACT.is_file(), False,
                     "gitignored, so never in a checkout (W-108)"),
    "contract": Need("RUN_CONTRACT_TESTS=1 and a live upstream", lambda: os.environ.get("RUN_CONTRACT_TESTS") == "1",
                     False, "the test job sets no RUN_CONTRACT_TESTS; the contract job does (REQ-CI-001)"),
    "epoch": Need("EPOCH_DATA_DIR, the owner-fetched Epoch bundle", lambda: bool(os.environ.get("EPOCH_DATA_DIR")),
                  False, "the bundle is the owner's download, never in CI"),
    "xcode": Need("Xcode's compiler (xcrun)", lambda: shutil.which("xcrun") is not None, False,
                  "the test job runs on ubuntu"),
    "macos": Need("macOS's System Configuration proxy fallback",
                  lambda: hasattr(urllib.request, "getproxies_macosx_sysconf"), False,
                  "the test job runs on ubuntu, which has no such fallback (#150)"),
    "offline": Need("a run offline at the operating system's level, children included", offline, False,
                    "CI's half is a patch for the owner's workflow file (#122)"),
    "bash_curl": Need("bash and curl", lambda: shutil.which("bash") is not None and shutil.which("curl") is not None,
                      True, "both are on the ubuntu image"),
    "git": Need("a git checkout", lambda: shutil.which("git") is not None and (ROOT / ".git").exists(), True,
                "the job checks the repository out"),
    "not_root": Need("a user that is not root", lambda: not (hasattr(os, "geteuid") and os.geteuid() == 0), True,
                     "the job runs as the runner user; root reads a mode-000 file"),
}


def ci_job_facts(workflow_text: str) -> dict[str, bool]:
    """#182: whether CI's test job has each need, read from its workflow file. The job's runner, the
    steps before the one that runs `pytest`, the variables that step sees and its command decide it;
    `test_ci_needs.py` holds `NEEDS[...].in_ci` equal to this. A runner it cannot read is an error,
    not a guess."""
    workflow = yaml.safe_load(workflow_text)
    job = workflow["jobs"]["test"]
    runner = str(job.get("runs-on", ""))
    if not runner.startswith(("ubuntu-", "macos-")):
        msg = f"#182: the test job's runner {runner!r} is not one this reads (ubuntu-*, macos-*)"
        raise ValueError(msg)
    steps = job.get("steps", [])
    at = next(i for i, step in enumerate(steps) if re.search(r"(?<![\w-])pytest(?![\w-])", str(step.get("run", ""))))
    command = str(steps[at]["run"])
    before = steps[:at]
    env = {**(workflow.get("env") or {}), **(job.get("env") or {}), **(steps[at].get("env") or {})}
    sudo = re.findall(r"\bsudo\b([^&|;]*)", command)
    return {
        "artifact": any("advisor.db" in str(step.get("run", "")) for step in before),
        "contract": str(env.get("RUN_CONTRACT_TESTS", "")) == "1",
        "epoch": bool(env.get("EPOCH_DATA_DIR")),
        "xcode": runner.startswith("macos-"),
        "macos": runner.startswith("macos-"),
        # #122's patch: a network namespace (`unshare --net` or `-n`) around the run.
        "offline": bool(re.search(r"\bunshare\b[^&|;]*\s(?:--net\b|-[a-zA-Z]*n[a-zA-Z]*\b)", command)),
        "bash_curl": True,  # both are on the ubuntu and macOS images
        "git": any(str(step.get("uses", "")).startswith("actions/checkout@") for step in before),
        # Root unless the last `sudo` before pytest drops to a user (`-u`), as #122's patch does.
        "not_root": "container" not in job and not (sudo and not re.search(r"\s-u\s", sudo[-1])),
    }


def configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", f"needs(*what): the test needs each named thing ({', '.join(sorted(NEEDS))}; "
        "tests/skips.py); skipped where one is absent, and counted for CI's skip budget (#137).",
    )


def needs_of(item: pytest.Item) -> set[str]:
    named = {str(name) for mark in item.iter_markers("needs") for name in mark.args}
    if item.get_closest_marker("artifact") is not None:
        named.add("artifact")
    if unknown := named - NEEDS.keys():
        msg = f"{item.nodeid} needs {sorted(unknown)}, which tests/skips.py does not name"
        raise pytest.UsageError(msg)
    return named


def apply(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip what this machine cannot run, and write CI's count where `--ci-skips-report` asks."""
    available = {name: need.here() for name, need in NEEDS.items()}
    ci_skips: dict[str, int] = {}
    skipped_in_ci = 0
    for item in items:
        named = needs_of(item)
        if missing := sorted(name for name in named if not available[name]):
            reason = "needs " + "; ".join(f"{NEEDS[name].what} ({NEEDS[name].why})" for name in missing)
            item.add_marker(pytest.mark.skip(reason=reason))
        if lacking := [name for name in named if not NEEDS[name].in_ci]:
            skipped_in_ci += 1
            for name in lacking:
                ci_skips[name] = ci_skips.get(name, 0) + 1
    report = config.getoption("ci_skips_report", default=None)
    if report:
        Path(report).write_text(json.dumps({"tests": len(items), "skipped": skipped_in_ci, "by_need": ci_skips}),
                                encoding="utf-8")
