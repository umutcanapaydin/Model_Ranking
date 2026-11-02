"""#557: `@pytest.mark.xdist_group("serial")` keeps a test off the other workers only under `--dist loadgroup`.

AGENTS.md section 3.3 promises it for `make check-fast`, and that check passes the flag; `make test` (the merge
gate) and CI run `pytest -n auto` with the project's own options alone. These tests run a small suite under
the project's `[tool.pytest.ini_options]` with `-n 4` and nothing else, as `make test` and CI do, and measure
the worker each marked test ran on (the release delta Tester's M1, 2026-11-01).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

MARKED = 8
SUITE = '''
import os
import time

import pytest


def _record(name):
    with open(os.environ["WORKERS_LOG"], "a", encoding="utf-8") as fh:
        fh.write(f"{name} {os.environ.get('PYTEST_XDIST_WORKER', 'none')}\\n")


@pytest.mark.xdist_group("serial")
@pytest.mark.parametrize("i", range(MARKED_COUNT))
def test_marked(i):
    time.sleep(0.05)
    _record(f"marked{i}")


@pytest.mark.parametrize("i", range(16))
def test_free(i):
    time.sleep(0.05)
    _record(f"free{i}")
'''.replace("MARKED_COUNT", str(MARKED))


def _workers(tmp_path: Path, *extra: str) -> dict[str, str]:
    (tmp_path / "test_suite.py").write_text(SUITE, encoding="utf-8")
    log = tmp_path / "workers.log"
    # The project's options as `make test` and CI read them: its pyproject, `-n 4`, nothing from check-fast.
    # `--no-cov` and a junit path in the temp folder keep the inner run off the outer run's report files.
    cmd = [sys.executable, "-m", "pytest", "-c", str(ROOT / "pyproject.toml"), "--rootdir", str(tmp_path),
           "-p", "no:cacheprovider", "--no-cov", f"--junitxml={tmp_path / 'report.xml'}", "-q", "-n", "4",
           *extra, str(tmp_path / "test_suite.py")]
    env = {"PATH": "/usr/bin:/bin", "WORKERS_LOG": str(log), "PYTEST_ADDOPTS": ""}
    r = subprocess.run(cmd, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120, check=False)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return dict(line.split() for line in log.read_text(encoding="utf-8").splitlines())


@pytest.mark.xdist_group("serial")
def test_the_projects_own_options_keep_a_marked_group_on_one_worker(tmp_path: Path) -> None:
    """covers #557: `pytest -n 4` under the project's options runs every `serial` test on one worker."""
    seen = _workers(tmp_path)
    marked = {seen[f"marked{i}"] for i in range(MARKED)}
    assert len(marked) == 1, f"the `serial` group ran on {sorted(marked)}: `--dist loadgroup` is not in effect"
    assert "none" not in marked, "the inner run did not start workers, so the check measured nothing"


@pytest.mark.xdist_group("serial")
def test_the_measure_can_fail(tmp_path: Path) -> None:
    """covers #557: with `--dist load` on the command line the same group spreads, so the check above can go red."""
    seen = _workers(tmp_path, "--dist", "load")
    assert len({seen[f"marked{i}"] for i in range(MARKED)}) > 1
