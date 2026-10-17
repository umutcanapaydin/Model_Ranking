#!/usr/bin/env python3
"""The two local memories of v7.2 forget exactly when they must.

WHY (the owner's ruling of 2026-10-17, process audit F-8/F-11/D-27). `make gate` stopped re-proving the
pinned Bash guard on every push (`conformance/run-all.py` remembers a pass by the content of the test and
its inputs) and stopped asking the network about an unchanged manifest (`scripts/net_cache.py`, twelve
hours). A memory that outlives what it remembers is a gate that did not run, so both polarities: each is
used when nothing changed, and dropped when an input changes, in CI, with DEVFLOW_FRESH, in the
distribution (the conformance memory), past twelve hours or on another stack (the network memory).

Exit: 0 every case behaves - 1 one does not.
"""
import importlib.util
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    bad: list[str] = []
    count = 0

    def case(name: str, ok: bool) -> None:
        nonlocal count
        count += 1
        if not ok:
            bad.append(f"  {name}")

    saved = {k: os.environ.pop(k) for k in ("CI", "GITHUB_ACTIONS", "DEVFLOW_FRESH") if k in os.environ}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            pkg = pathlib.Path(tmp)
            (pkg / "conformance").mkdir()
            (pkg / ".claude" / "hooks").mkdir(parents=True)
            shutil.copy(ROOT / "conformance" / "run-all.py", pkg / "conformance" / "run-all.py")
            (pkg / "conformance" / "test-bash-guard.py").write_text("print('ok')\n", encoding="utf-8")
            (pkg / ".claude" / "hooks" / "bash_guard.py").write_text("x = 1\n", encoding="utf-8")
            spec = importlib.util.spec_from_file_location("ra", pkg / "conformance" / "run-all.py")
            ra = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ra)
            t = "test-bash-guard.py"
            case("conformance memory: nothing remembered yet, the test runs", ra.cached(t) == "")
            ra.remember(t)
            case("conformance memory: after a pass on the same inputs, it is not run again", ra.cached(t) != "")
            (pkg / ".claude" / "hooks" / "bash_guard.py").write_text("x = 2\n", encoding="utf-8")
            case("conformance memory: the guard changed, the test runs", ra.cached(t) == "")
            ra.remember(t)
            (pkg / "conformance" / t).write_text("print('changed')\n", encoding="utf-8")
            case("conformance memory: the test itself changed, it runs", ra.cached(t) == "")
            ra.remember(t)
            (pkg / "scripts").mkdir()
            (pkg / "scripts" / "deploy_gate.py").write_text("y = 1\n", encoding="utf-8")
            case("conformance memory: a script the guard reaches appeared, it runs", ra.cached(t) == "")
            ra.remember(t)
            (pkg / "scripts" / "deploy_gate.py").unlink()
            case("conformance memory: that script was deleted, it runs", ra.cached(t) == "")
            ra.remember(t)
            (pkg / "scripts" / "__pycache__").mkdir()
            (pkg / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"\0")
            case("conformance memory: bytecode is not an input", ra.cached(t) != "")
            os.environ["CI"] = "true"
            case("conformance memory: in CI it always runs", ra.cached(t) == "")
            del os.environ["CI"]
            os.environ["DEVFLOW_FRESH"] = "1"
            case("conformance memory: DEVFLOW_FRESH runs it", ra.cached(t) == "")
            del os.environ["DEVFLOW_FRESH"]
            (pkg / ".gp-distribution").write_text("x\n", encoding="utf-8")
            case("conformance memory: in the distribution it always runs", ra.cached(t) == "")
            (pkg / ".gp-distribution").unlink()
            case("conformance memory: a test with no declared inputs is never remembered",
                 ra.cache_key("test-something-else.py") is None)

        with tempfile.TemporaryDirectory() as tmp:
            pkg = pathlib.Path(tmp)
            (pkg / "scripts").mkdir()
            shutil.copy(ROOT / "scripts" / "net_cache.py", pkg / "scripts" / "net_cache.py")
            (pkg / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

            def net(*args: str, **env: str) -> int:
                e = {k: v for k, v in os.environ.items() if k not in ("CI", "GITHUB_ACTIONS", "DEVFLOW_FRESH")}
                return subprocess.run([sys.executable, str(pkg / "scripts" / "net_cache.py"), *args],
                                      capture_output=True, text=True, env={**e, **env}).returncode

            case("network memory: nothing remembered, the leg runs", net("fresh", "deps") == 1)
            net("record", "deps")
            case("network memory: the same manifest within 12 h, not asked again", net("fresh", "deps") == 0)
            case("network memory: the other leg is remembered apart", net("fresh", "slopsquat") == 1)
            case("network memory: in CI it always runs", net("fresh", "deps", CI="true") == 1)
            case("network memory: DEVFLOW_FRESH runs it", net("fresh", "deps", DEVFLOW_FRESH="1") == 1)
            old = time.time() - 13 * 3600
            os.utime(pkg / "build" / "net-cache" / "deps", (old, old))
            case("network memory: past 12 hours it runs", net("fresh", "deps") == 1)
            net("record", "deps")
            (pkg / "pyproject.toml").write_text("[project]\nname='x'\ndependencies=['y']\n", encoding="utf-8")
            case("network memory: the manifest changed, it runs", net("fresh", "deps") == 1)
            net("record", "deps")
            (pkg / ".devflow-stack").write_text("go\n", encoding="utf-8")
            case("network memory: another stack is never remembered", net("fresh", "deps") == 1)
    finally:
        os.environ.update(saved)

    if bad:
        print("test-local-caches FAIL (conformance/run-all.py's memory, scripts/net_cache.py):")
        print("\n".join(bad))
        return 1
    print(f"test-local-caches PASS: {count} cases -- the conformance and network memories are used only while "
          "nothing they remember changed, and never in CI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
