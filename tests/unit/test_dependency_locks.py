"""M18-W6 (#35, #26): every install reads a lock, and every lock is current with `pyproject.toml`.

A lock is the list of exact versions, with their hashes, that an install gets. Without one a fresh
venv took whatever was newest that day: a release built on 2026-09-25 differed from the tested venv
in 11 packages (#35). These tests read the three locks under `requirements/` and the three places
that install: `make install`, the engine's release (`scripts/install_engine_service.sh`) and the
serving image (`Dockerfile`). The network is never needed: a lock records the hash of the
`pyproject.toml` tables it was resolved from (`scripts/lock_dependencies.py`).
"""

from __future__ import annotations

import importlib.util
import re
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("lock_dependencies", ROOT / "scripts" / "lock_dependencies.py")
assert _spec is not None and _spec.loader is not None
locks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(locks)

PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s;\\]+)")


def _pinned(name: str) -> dict[str, list[tuple[str, int]]]:
    """Each package the lock pins -> [(version, hashes)], one entry per marker variant."""
    pins: dict[str, list[tuple[str, int]]] = {}
    current: list[tuple[str, int]] | None = None
    for line in locks.lock_path(name).read_text(encoding="utf-8").splitlines():
        match = PIN.match(line)
        if match:
            current = pins.setdefault(canonicalize_name(match.group(1)), [])
            current.append((match.group(2), 0))
        elif "--hash=sha256:" in line and current:
            version, hashes = current[-1]
            current[-1] = (version, hashes + line.count("--hash=sha256:"))
        elif line.strip() and not line.lstrip().startswith("#"):
            assert line.startswith(" "), f"{name}.lock: a line no install reads: {line!r}"
    return pins


def _wanted(extras: tuple[str, ...]) -> list[Requirement]:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    optional = project["optional-dependencies"]
    return [Requirement(text) for text in project["dependencies"] + [d for e in extras for d in optional[e]]]


def test_the_locks_are_the_declared_three() -> None:
    """A lock nobody declared is one nothing installs or checks; a missing one fails closed."""
    assert sorted(path.stem for path in (ROOT / "requirements").glob("*.lock")) == sorted(locks.LOCKS)


@pytest.mark.parametrize("name", sorted(locks.LOCKS))
def test_every_lock_is_current_with_pyproject(name: str) -> None:
    assert locks.stale(name) is None, locks.stale(name)


def test_a_changed_dependency_makes_a_lock_stale(tmp_path: Path) -> None:
    """The staleness check, watched failing: one new dependency, and every lock's hash moves."""
    edited = tmp_path / "pyproject.toml"
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    edited.write_text(text.replace('"pyyaml>=6.0",', '"pyyaml>=6.0",\n    "requests>=2",', 1), encoding="utf-8")
    for extras in locks.LOCKS.values():
        assert locks.tables_hash(extras, edited) != locks.tables_hash(extras)
    # ...and a change outside the dependency tables moves none.
    edited.write_text(text.replace('version = "0.1.0"', 'version = "0.1.1"', 1), encoding="utf-8")
    for extras in locks.LOCKS.values():
        assert locks.tables_hash(extras, edited) == locks.tables_hash(extras)


@pytest.mark.parametrize("name", sorted(locks.LOCKS))
def test_every_package_is_pinned_with_its_hashes(name: str) -> None:
    """`pip install --require-hashes` refuses a lock with an unhashed line; this says which, first."""
    pins = _pinned(name)
    assert len(pins) >= 10, f"{name}.lock pins almost nothing; was it read?"
    unhashed = [package for package, variants in pins.items() if any(h == 0 for _, h in variants)]
    assert not unhashed, f"{name}.lock pins without a hash: {unhashed}"


@pytest.mark.parametrize("name", sorted(locks.LOCKS))
def test_each_declared_dependency_is_locked_within_its_range(name: str) -> None:
    pins = _pinned(name)
    for requirement in _wanted(locks.LOCKS[name]):
        variants = pins.get(canonicalize_name(requirement.name))
        assert variants, f"{name}.lock does not pin {requirement.name}"
        for version, _ in variants:
            assert requirement.specifier.contains(version, prereleases=True), (
                f"{name}.lock pins {requirement.name}=={version}, outside {requirement.specifier}")


def test_only_the_refresh_locks_carry_pyarrow() -> None:
    """#26: the serving image runs no refresh (D-116, D-154), so it does not ship pyarrow."""
    assert "pyarrow" not in _pinned("serve")
    assert "pyarrow" in _pinned("ingest") and "pyarrow" in _pinned("dev")


def test_the_dev_extra_holds_the_ingest_extra() -> None:
    """The suite reads parquet, so a working tree has what the refresh has."""
    optional = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "optional-dependencies"]
    assert set(optional["ingest"]) <= set(optional["dev"])


@pytest.mark.parametrize(("path", "lock"), [
    ("Makefile", "requirements/dev.lock"),
    ("scripts/install_engine_service.sh", "requirements/ingest.lock"),
    ("Dockerfile", "requirements/serve.lock"),
])
def test_every_install_reads_its_lock_and_resolves_nothing_else(path: str, lock: str) -> None:
    """Each install takes its lock, hash-checked, then the project with `--no-deps`. A plain
    `pip install .` or `-e .` beside it would resolve the newest versions again."""
    text = (ROOT / path).read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    installs = re.findall(r"(?:pip|\$\(PIP\)) install[^\n]*", code)
    assert installs, f"{path} installs nothing"
    assert any("--require-hashes" in line and lock.split("/")[-1] in line for line in installs), (
        f"{path} does not install {lock} with --require-hashes")
    for line in installs:
        if "--require-hashes" not in line:
            assert "--no-deps" in line, f"{path} resolves dependencies outside its lock: {line.strip()}"
