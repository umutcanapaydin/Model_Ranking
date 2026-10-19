"""#328: a Bash-hook call that outlives its timeout is a named finding, not a dead test.

CI once showed `[FAIL] test-bash-guard.py (no output) (exit 1)`: the per-case `subprocess.run(..., timeout=120)`
raised `TimeoutExpired` inside the thread pool, and the whole test died with nothing on stdout. Here every hook
call times out: the test must still finish, print a FAIL line naming the cases, and exit 1.
"""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("test_bash_guard_328", ROOT / "conformance" / "test-bash-guard.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_hook_call_that_times_out_is_reported_by_its_case(monkeypatch: pytest.MonkeyPatch,
                                                             capsys: pytest.CaptureFixture[str]) -> None:
    module = _module()
    real = subprocess.run

    def slow_hook(args, *rest, **kwargs):  # type: ignore[no-untyped-def]
        if isinstance(args, list) and len(args) == 3 and args[1] == "-c" and "bash_guard" in str(args[2]):
            raise subprocess.TimeoutExpired(args, kwargs.get("timeout") or 0)
        return real(args, *rest, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", slow_hook)
    assert module.main() == 1
    out = capsys.readouterr().out
    assert "timed out" in out and "test-bash-guard FAIL" in out, out[-2000:]
