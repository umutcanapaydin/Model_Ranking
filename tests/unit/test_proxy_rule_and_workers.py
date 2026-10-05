"""Tester round 2, #143: the derived rule and the xdist hand-off, each seen through a real run.

The committed tests check the rule with the rule (`assert not conftest.proxy_names()`), so a rule
that misses a name misses it in the check too; and they call the hand-off's two halves by hand, so a
worker that never reads what it was handed passes. Here a child pytest inherits the variables and
its tests read what urllib reads (`getproxies_environment`, the function httpx asks). Every proxy
names port 9 on this machine: nothing listens there, and no probe sends anything.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROXY = "http://127.0.0.1:9"

SEES_NONE = """
import os
import urllib.request


def test_a_test_sees_no_proxy() -> None:
    seen = urllib.request.getproxies_environment()
    assert set(seen) <= {"no"}, seen
    assert os.environ.get("NO_PROXY") == "localhost", "NO_PROXY is not a proxy: it stays"
"""

GETS_THEM_BACK = f"""
import os


def test_a_live_contract_test_gets_the_proxies_back() -> None:
    assert os.environ.get("HTTPS_PROXY") == {PROXY!r}
    assert os.environ.get("all_proxy") == {PROXY!r}
"""


def _env(tmp_path: Path, pythonpath: Path, proxies: dict[str, str], *, contract: bool) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PYTEST_", "COV_"))
        and k not in ("RUN_CONTRACT_TESTS", "MODEL_RANKING_REQUIRE_ARTIFACT")
        and not k.lower().endswith("_proxy")
    }
    env.update(proxies, PYTHONPATH=str(pythonpath), NO_PROXY="localhost")
    if contract:
        env["RUN_CONTRACT_TESTS"] = "1"
    return env


def _pytest(tmp_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
         "--rootdir", str(tmp_path), *args],
        cwd=tmp_path, capture_output=True, text=True, timeout=180, check=False, env=env,
    )


def test_a_proxy_urllib_reads_in_any_case_reaches_no_test(tmp_path: Path) -> None:
    """#143 and the fix Tester's K2: urllib reads any `*_proxy` in any case, so the run hides every
    one. Only mixed-case names are planted, so the six names of the first fix hide none of them."""
    (tmp_path / "test_probe.py").write_text(SEES_NONE, encoding="utf-8")
    proxies = {name: PROXY for name in ("Https_Proxy", "Http_Proxy", "All_Proxy", "Ftp_Proxy")}
    done = _pytest(tmp_path, _env(tmp_path, ROOT, proxies, contract=False),
                   "-p", "tests.conftest", str(tmp_path / "test_probe.py"))
    assert done.returncode == 0 and "1 passed" in done.stdout, done.stdout[-2000:] + done.stderr[-2000:]


def test_under_xdist_a_unit_test_sees_no_proxy_and_a_live_contract_test_gets_them_back(tmp_path: Path) -> None:
    """#143: "removes the proxy variables for the run unless a live contract test is lifting the
    guard", under `-n` (the fix Tester's R2). The suite's own conftest is copied to a scratch root,
    so `tests/integration` there is a live contract test's place, and a child pytest runs one unit
    probe, then one contract probe, on one xdist worker. The worker started after its controller hid
    the variables: the unit probe must see none, and the contract probe must get them back."""
    (tmp_path / "tests" / "unit").mkdir(parents=True)
    (tmp_path / "tests" / "integration").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(ROOT / "tests" / "conftest.py", tmp_path / "tests" / "conftest.py")
    (tmp_path / "tests" / "unit" / "test_unit_probe.py").write_text(SEES_NONE, encoding="utf-8")
    (tmp_path / "tests" / "integration" / "test_contract_probe.py").write_text(GETS_THEM_BACK, encoding="utf-8")
    proxies = {"HTTPS_PROXY": PROXY, "all_proxy": PROXY, "Http_Proxy": PROXY}
    done = _pytest(tmp_path, _env(tmp_path, tmp_path, proxies, contract=True), "-n", "1",
                   "tests/unit/test_unit_probe.py", "tests/integration/test_contract_probe.py")
    assert done.returncode == 0 and "2 passed" in done.stdout, done.stdout[-2000:] + done.stderr[-2000:]
