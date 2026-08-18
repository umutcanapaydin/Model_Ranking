"""M7 Stage-4.0 MINOR-3 — the slopsquat gate sees every declared dependency.

`scripts/slopsquat_check.py` returned exactly one name, `fastapi`, out of five runtime
dependencies, and printed PASS. A non-greedy bracket match stopped at the first `]` in the file —
the one inside `uvicorn[standard]` — so everything after it was invisible, including every
optional-dependency group, which is where a typo-squatted test helper would land and which CI
installs on every run.

The gate is a supply-chain control. One that inspects a fifth of the surface and reports success is
worse than none, because it is cited as coverage. These tests derive the expected set from
`pyproject.toml` rather than listing names, so a dependency added tomorrow is covered without
anyone remembering this file exists.
"""

from __future__ import annotations

import pathlib
import sys
import tomllib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import slopsquat_check  # noqa: E402


def _pyproject_names() -> set[str]:
    """Every distribution name pyproject declares, read the way packaging tools read it."""
    with (ROOT / "pyproject.toml").open("rb") as fh:
        doc = tomllib.load(fh)
    project = doc.get("project", {})
    specs = list(project.get("dependencies", []) or [])
    for group in (project.get("optional-dependencies", {}) or {}).values():
        specs.extend(group or [])
    names = set()
    for spec in specs:
        match = slopsquat_check.DEP_RE.match(spec)
        assert match, f"could not read a distribution name out of {spec!r}"
        names.add(match.group(1))
    return names


def test_the_fixture_itself_finds_more_than_one_dependency() -> None:
    """Anti-vacuity: the bug being guarded against was a set of size one."""
    assert len(_pyproject_names()) >= 5


def test_the_gate_sees_every_declared_dependency() -> None:
    """The citing test for MINOR-3: no dependency may be invisible to the supply-chain gate."""
    seen = set(slopsquat_check.declared(ROOT))
    missing = _pyproject_names() - seen
    assert not missing, (
        f"the slopsquat gate cannot see {sorted(missing)}; it would print PASS without ever "
        "checking them"
    )


def test_a_bracketed_extra_does_not_hide_what_follows_it() -> None:
    """The exact shape of the defect, driven through the real parser on a fixture file."""
    fixture = """
[project]
name = "probe"
version = "0"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
"""
    tmp = ROOT / "build" / "_slopsquat_probe"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "pyproject.toml").write_text(fixture, encoding="utf-8")
    try:
        names = set(slopsquat_check.declared(tmp))
    finally:
        (tmp / "pyproject.toml").unlink()
        tmp.rmdir()

    assert names == {"fastapi", "uvicorn", "pyyaml", "pytest"}, (
        f"a bracketed extra still truncates the dependency list; got {sorted(names)}"
    )


@pytest.mark.parametrize("name", sorted(_pyproject_names()))
def test_each_declared_dependency_is_individually_visible(name: str) -> None:
    """One case per dependency, so a failure names WHICH one went missing."""
    assert name in set(slopsquat_check.declared(ROOT))
