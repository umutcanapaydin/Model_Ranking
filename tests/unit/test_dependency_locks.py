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


def _wanted(name: str) -> list[Requirement]:
    if name == locks.BUILD:
        return [Requirement(text) for text in locks.build_requires()]
    extras = locks.LOCKS[name]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    optional = project["optional-dependencies"]
    return [Requirement(text) for text in project["dependencies"] + [d for e in extras for d in optional[e]]]


def test_the_locks_are_the_declared_ones() -> None:
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
    for name in locks.LOCKS:
        if name != locks.BUILD:
            assert locks.tables_hash(locks.resolved_from(name), edited) != locks.tables_hash(locks.resolved_from(name))
    # ...a new build backend moves the build lock's...
    edited.write_text(text.replace('requires = ["setuptools>=75"]', 'requires = ["setuptools>=76"]', 1),
                      encoding="utf-8")
    build = locks.resolved_from(locks.BUILD)
    assert locks.tables_hash(build, edited) != locks.tables_hash(build)
    # ...and a change outside those tables moves none.
    edited.write_text(text.replace('version = "0.1.0"', 'version = "0.1.1"', 1), encoding="utf-8")
    for name in locks.LOCKS:
        assert locks.tables_hash(locks.resolved_from(name), edited) == locks.tables_hash(locks.resolved_from(name))


@pytest.mark.parametrize("name", sorted(locks.LOCKS))
def test_every_package_is_pinned_with_its_hashes(name: str) -> None:
    """`pip install --require-hashes` refuses a lock with an unhashed line; this says which, first."""
    pins = _pinned(name)
    assert len(pins) >= (1 if name == locks.BUILD else 10), f"{name}.lock pins almost nothing; was it read?"
    unhashed = [package for package, variants in pins.items() if any(h == 0 for _, h in variants)]
    assert not unhashed, f"{name}.lock pins without a hash: {unhashed}"


@pytest.mark.parametrize("name", sorted(locks.LOCKS))
def test_each_declared_dependency_is_locked_within_its_range(name: str) -> None:
    pins = _pinned(name)
    for requirement in _wanted(name):
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


#: A pip command, however it is spelled: `pip`, `pip3`, `$(PIP)`, `python -m pip`, `uv pip`, with
#: options before or after `install` (the W6 review's M7).
PIP_INSTALL = re.compile(r"(?:\bpip3?\b|\$\(PIP\)|\$\{?PIP\}?)[^&;|\n]*?\binstall\b[^&;|\n]*", re.IGNORECASE)
#: What a project install may name: the project, and nothing beside it (the W6 Tester's T3).
PROJECT = {".", '"$rel"', "$rel"}


def install_targets(command: str) -> list[str]:
    """What a pip install names besides its options and the files its `-r` reads."""
    words, targets, skip = command.split("install", 1)[1].split(), [], False
    for word in words:
        if skip:
            skip = False
        elif word in {"-r", "--requirement", "-c", "--constraint"}:
            skip = True
        elif not word.startswith("-") and word != "\\":
            targets.append(word)
    return targets


def install_commands(text: str) -> list[str]:
    """Every pip install in a file, with shell continuations joined and comments dropped."""
    code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    return [match.group(0) for match in PIP_INSTALL.finditer(code.replace("\\\n", " "))]


def install_problems(path: str, text: str, lock: str) -> list[str]:
    """Each install takes its lock and the build lock, hash-checked, then the project with
    `--no-deps --no-build-isolation`. Anything else resolves or fetches versions no test ran."""
    installs = install_commands(text)
    if not installs:
        return [f"{path} installs nothing"]
    problems = []
    for wanted in (lock, "requirements/build.lock"):
        if not any("--require-hashes" in c and wanted.split("/")[-1] in c for c in installs):
            problems.append(f"{path} does not install {wanted} with --require-hashes")
    for command in installs:
        if "--require-hashes" in command:
            if install_targets(command):
                problems.append(f"{path} names a package beside its locks: {command.strip()}")
            continue
        if ("--no-deps" not in command or "--no-build-isolation" not in command
                or len(targets := install_targets(command)) != 1 or targets[0] not in PROJECT):
            problems.append(f"{path} resolves or fetches outside its locks: {command.strip()}")
    return problems


@pytest.mark.parametrize(("path", "lock"), [
    ("Makefile", "requirements/dev.lock"),
    ("scripts/install_engine_service.sh", "requirements/ingest.lock"),
    ("Dockerfile", "requirements/serve.lock"),
])
def test_every_install_reads_its_lock_and_resolves_nothing_else(path: str, lock: str) -> None:
    assert not install_problems(path, (ROOT / path).read_text(encoding="utf-8"), lock)


@pytest.mark.parametrize("planted", [
    "RUN pip3 install requests",  # the review's probes, beside the locked install
    "RUN python -m pip --no-cache-dir install requests",
    "RUN uv pip install requests",
    "RUN pip install --no-deps .",  # no isolation flag: fetches the newest setuptools
])
def test_the_install_check_reads_every_spelling(planted: str) -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8") + f"\n{planted}\n"
    assert install_problems("Dockerfile", text, "requirements/serve.lock")


def test_a_lock_resolved_from_another_pyproject_is_reported_and_fails_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """The M18-W6 Tester's survivor: `stale` could answer None for every lock and every test stayed
    green, since the planted test reads `tables_hash` and the real one sees current locks. Here a
    copied lock records another hash, and then goes missing: `stale` says so, and `--check` fails."""
    import shutil

    (tmp_path / "requirements").mkdir()
    for name in locks.LOCKS:
        shutil.copy(locks.lock_path(name), tmp_path / "requirements" / f"{name}.lock")
    monkeypatch.setattr(locks, "ROOT", tmp_path)
    monkeypatch.setattr(locks, "LOCK_DIR", tmp_path / "requirements")
    assert [locks.stale(name) for name in locks.LOCKS] == [None] * len(locks.LOCKS)
    serve = locks.lock_path("serve")
    recorded = locks.recorded_hash(serve)
    assert recorded
    serve.write_text(serve.read_text(encoding="utf-8").replace(recorded, "0" * 64, 1), encoding="utf-8")
    assert "make lock" in (locks.stale("serve") or ""), "a lock with another hash was called current"
    assert locks.main(["--check"]) == 1
    assert "FAIL [lock]: requirements/serve.lock" in capsys.readouterr().out
    serve.unlink()
    assert "missing" in (locks.stale("serve") or ""), "a missing lock was called current"


@pytest.mark.parametrize(("path", "planted"), [
    # The W6 Tester's T3: a project install that also names a package, and pip spelled in capitals.
    ("Dockerfile", "RUN pip install --no-cache-dir --prefix=/install --no-deps --no-build-isolation . requests"),
    ("scripts/install_engine_service.sh", '"${PIP}" install requests'),
    ("scripts/install_engine_service.sh", "$PIP install requests"),
])
def test_an_install_beside_the_project_or_a_capital_pip_is_read(path: str, planted: str) -> None:
    lock = {"Dockerfile": "requirements/serve.lock",
            "scripts/install_engine_service.sh": "requirements/ingest.lock"}[path]
    text = (ROOT / path).read_text(encoding="utf-8") + f"\n{planted}\n"
    assert install_problems(path, text, lock), planted
