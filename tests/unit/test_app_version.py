"""#459: `/health`'s version is the release's.

v0.2.0 shipped answering `"version": "0.1.0"`: the version is kept by hand in `pyproject.toml` and in
`APP_VERSION`, and nothing compared either with the release being cut. One fact in three places, so
one gate (AGENTS.md §3.5): the served version is the package's, and the package is never older than
the newest release record under `docs/releases/`. No record, or none that names a version, is a
failure, never a vacuous pass.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

from app.adapter import main

REPO = Path(__file__).resolve().parents[2]
RECORD = re.compile(r"^v(\d+)\.(\d+)\.(\d+)\.md$")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _package() -> str:
    return str(tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"])


def _newest_release() -> tuple[int, ...]:
    found = [tuple(int(g) for g in m.groups()) for p in (REPO / "docs" / "releases").iterdir()
             if (m := RECORD.match(p.name))]
    assert found, "no release record under docs/releases/ names a version"
    return max(found)


def test_health_serves_the_packages_version() -> None:
    body = TestClient(main.app).get("/health").json()
    assert body["version"] == main.APP_VERSION == _package()


def test_the_package_is_not_older_than_the_newest_release_record() -> None:
    assert _version(_package()) >= _newest_release(), (
        f"pyproject.toml says {_package()}, but docs/releases/ records v{'.'.join(map(str, _newest_release()))}: "
        "bump `version` in pyproject.toml and `APP_VERSION` in src/app/adapter/main.py with the release"
    )
