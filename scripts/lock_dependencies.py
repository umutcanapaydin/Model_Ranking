"""Write the dependency lock files from `pyproject.toml` (M18-W6, #35).

Each lock pins every package an install needs, for every platform and every Python the project
supports, with the hashes `pip install --require-hashes` checks. An install from a lock gets the
versions the suite ran on, not whatever was newest that day (#35: a release venv built on
2026-09-25 differed from the tested one in 11 packages).

    python scripts/lock_dependencies.py           # resolve and write every lock (needs the network)
    python scripts/lock_dependencies.py --check   # offline: is each lock current with pyproject?

Each lock records the hash of the `pyproject.toml` tables it was resolved from, so `--check`, and
`tests/unit/test_dependency_locks.py`, can tell a stale lock without the network.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
LOCK_DIR = ROOT / "requirements"

#: Which extras each lock holds, and who installs it.
#: - `serve`: the serving image (`Dockerfile`), which runs no refresh, so it has no pyarrow (#26);
#: - `ingest`: the engine's release on the owner's Mac (`scripts/install_engine_service.sh`), which
#:   serves and refreshes;
#: - `dev`: a working tree (`make install`) and the suite.
LOCKS: dict[str, tuple[str, ...]] = {"serve": (), "ingest": ("ingest",), "dev": ("dev", "ingest")}

#: The oldest Python the project supports (`requires-python`); the lock resolves from it upwards.
PYTHON = "3.11"

HASH_LINE = "# pyproject-sha256: "


def lock_path(name: str) -> Path:
    return LOCK_DIR / f"{name}.lock"


def tables_hash(extras: tuple[str, ...], pyproject: Path = PYPROJECT) -> str:
    """The hash of what a lock is resolved from: the dependencies, the extras it holds, and the
    supported Pythons. A change to anything else in `pyproject.toml` leaves the locks current."""
    project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]
    optional = project.get("optional-dependencies", {})
    tables = {
        "requires-python": project.get("requires-python"),
        "dependencies": sorted(project.get("dependencies", [])),
        "extras": {extra: sorted(optional[extra]) for extra in extras},
    }
    return hashlib.sha256(json.dumps(tables, sort_keys=True).encode()).hexdigest()


def recorded_hash(lock: Path) -> str | None:
    for line in lock.read_text(encoding="utf-8").splitlines():
        if line.startswith(HASH_LINE):
            return line.removeprefix(HASH_LINE).strip()
    return None


def stale(name: str) -> str | None:
    """Why the lock `name` is not current with `pyproject.toml`, or None."""
    lock = lock_path(name)
    if not lock.is_file():
        return f"{lock.relative_to(ROOT)} is missing"
    if recorded_hash(lock) != tables_hash(LOCKS[name]):
        return f"{lock.relative_to(ROOT)} was resolved from another pyproject.toml; run `make lock`"
    return None


def write(name: str) -> None:
    extras = LOCKS[name]
    command = [sys.executable, "-m", "uv", "pip", "compile", str(PYPROJECT.relative_to(ROOT)),
               "--universal", "--python-version", PYTHON, "--generate-hashes", "--no-header",
               "--quiet", *(arg for extra in extras for arg in ("--extra", extra))]
    resolved = subprocess.run(  # noqa: S603 -- our own interpreter and arguments, no shell
        command, cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    header = [
        f"# requirements/{name}.lock: written by `make lock` (scripts/lock_dependencies.py) from",
        f"# pyproject.toml, extras: {', '.join(extras) or 'none'}. Do not edit it by hand.",
        f"# Install with: pip install --require-hashes -r requirements/{name}.lock",
        f"{HASH_LINE}{tables_hash(extras)}",
    ]
    LOCK_DIR.mkdir(exist_ok=True)
    lock_path(name).write_text("\n".join(header) + "\n" + resolved, encoding="utf-8")


def main(argv: list[str]) -> int:
    if argv == ["--check"]:
        problems = [problem for name in LOCKS if (problem := stale(name))]
        for problem in problems:
            print(f"FAIL [lock]: {problem}")
        if not problems:
            print(f"lock: {len(LOCKS)} lock(s) current with {PYPROJECT.name}")
        return 1 if problems else 0
    if argv:
        print(__doc__)
        return 2
    for name in LOCKS:
        write(name)
        print(f"lock: wrote {lock_path(name).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
