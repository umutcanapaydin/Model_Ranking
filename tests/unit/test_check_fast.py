"""`make check-fast` -- the same gates as `make check`, run side by side.

Modelled on the owner's `check-fast` in hcs_maas_full. `check` stays what a merge is judged by. The
legs are DERIVED from `check`'s own prerequisite line (AGENTS.md §3.5): a gate added to `check`
joins `check-fast` without anyone editing this, and one removed leaves it. The only names kept
here are the ones with a reason: the Python chain runs in order (`coverage-floor` reads the
`coverage.json` that `test` writes), and the Swift leg runs its parallel form.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_fast.py"


def _mod() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_fast", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flat(legs: dict[str, list[str]]) -> list[str]:
    return [t for targets in legs.values() for t in targets]


def test_the_legs_run_every_gate_check_runs_exactly_once() -> None:
    """Read from the real Makefile: nothing dropped, nothing doubled."""
    mod = _mod()
    prereqs = mod.check_prerequisites((ROOT / "Makefile").read_text(encoding="utf-8"))
    assert prereqs, "fails closed: an empty `check` would make an empty check-fast"
    flat = _flat(mod.legs(prereqs))
    swapped = [mod.PARALLEL_FORM.get(t, t) for t in prereqs]
    assert sorted(flat) == sorted(swapped)
    assert len(flat) == len(set(flat))


def test_the_python_chain_keeps_its_order() -> None:
    legs = _mod().legs(["coverage-floor", "lint", "test", "typecheck", "conformance"])
    assert legs["python"] == ["lint", "typecheck", "test", "coverage-floor"]


def test_a_new_gate_in_check_joins_a_leg_without_an_edit() -> None:
    legs = _mod().legs(["lint", "test", "a-gate-added-tomorrow", "swift-test"])
    assert "a-gate-added-tomorrow" in _flat(legs)
    assert "swift-test-parallel" in _flat(legs) and "swift-test" not in _flat(legs)


def test_an_empty_check_line_fails_closed() -> None:
    with pytest.raises(ValueError):
        _mod().check_prerequisites("gate: check\n")


def test_any_failing_leg_fails_the_run(tmp_path: Path) -> None:
    mod = _mod()
    ok = {"a": ["true"], "b": ["sh", "-c", "exit 0"]}
    assert mod.run_legs(ok, tmp_path) == 0
    bad = {"a": ["true"], "b": ["sh", "-c", "echo broken; exit 3"]}
    assert mod.run_legs(bad, tmp_path) != 0
    assert "broken" in (tmp_path / "b.log").read_text(encoding="utf-8")


def test_a_leg_that_cannot_start_fails_the_run(tmp_path: Path) -> None:
    assert _mod().run_legs({"a": ["/nonexistent/binary"]}, tmp_path) != 0
