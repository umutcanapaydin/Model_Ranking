"""Tester, #143: a proxy in the environment a run inherits reaches no test, the first one included."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROBE = """
import urllib.request


def test_the_first_test_of_a_run_sees_no_proxy() -> None:
    seen = urllib.request.getproxies_environment()
    assert not {k: v for k, v in seen.items() if k in ("http", "https", "all")}, seen
"""


def test_a_proxy_planted_in_the_runs_environment_reaches_no_test(tmp_path: Path) -> None:
    """#143: "`pytest_configure` removes the proxy variables for the run ... a test plants one and
    sees no proxy in a test's environment". The fix's own test plants after the run has started and
    calls `_hide_proxies()` itself, and every teardown hides them again, so with the call in
    `pytest_configure` removed the suite stayed green, a proxy in the shell or not. Here a child
    pytest inherits the variables, and its first and only test reads what httpx reads
    (`urllib.request.getproxies_environment()`, the `http`, `https` and `all` keys). Port 9 on this
    machine: nothing listens, and nothing is sent."""
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_probe.py").write_text(PROBE, encoding="utf-8")
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PYTEST_", "COV_"))
        and k not in ("RUN_CONTRACT_TESTS", "MODEL_RANKING_REQUIRE_ARTIFACT")
    }
    env["PYTHONPATH"] = str(root)
    for scheme in ("http", "https", "all"):
        env[f"{scheme}_proxy"] = env[f"{scheme.upper()}_PROXY"] = "http://127.0.0.1:9"
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
         "-p", "tests.conftest", "--rootdir", str(tmp_path), str(tmp_path / "test_probe.py")],
        cwd=tmp_path, capture_output=True, text=True, timeout=120, check=False, env=env,
    )
    assert done.returncode == 0, done.stdout[-2000:] + done.stderr[-2000:]
    assert "1 passed" in done.stdout, done.stdout[-2000:]
