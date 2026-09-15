"""M13 Stage 4.0 MAJOR-1 and MINOR-1 -- a memo may spare work, never change an answer.

M13-W1 memoised the `/health` probe so a 30-second poll would stop running nine rankings. The key
was `(path, mtime, size)`, which asks whether the CONTENT is the same, while the probe answers
whether this process can still SERVE it. The independent seat reproduced two states where those
differ -- a `chmod 000`, and a same-size write with the mtime set back -- and in both `/health`
read `servable` while `/v1` answered 503 or disclosed every surface unreadable. That is the W-023
shape `evidence` exists to close, reopened by an optimisation, and no test covered the memo at all.

Built from the seeded fixture rather than `advisor.db`, so these run on a fresh clone and in CI.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter

from .test_refresh import _artifact


@pytest.fixture
def serving(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    """An engine on a servable artifact, with both memos empty so no test inherits another's."""
    artifact = _artifact(tmp_path / "advisor.db")
    monkeypatch.setenv("MODEL_RANKING_DB", str(artifact))
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setattr(adapter, "_UNUSABLE_MEMO", {})
    monkeypatch.setattr(adapter, "_WARNED", set())
    return TestClient(adapter.app), artifact


def _evidence(client: TestClient) -> str:
    return str(client.get("/health").json()["evidence"])


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0, reason="root can read a mode-000 file"
)
def test_an_artifact_whose_permissions_are_revoked_reads_unavailable(
    serving: tuple[TestClient, Path],
) -> None:
    """A `chmod` during a volume migration or a hardening pass. mtime and size do not move."""
    client, artifact = serving
    assert _evidence(client) == "servable", "fixture assumption: the artifact starts servable"

    artifact.chmod(0)
    try:
        assert _evidence(client) == "unavailable", (
            "`/health` answered from the memo for a file this process can no longer open"
        )
    finally:
        artifact.chmod(0o644)


def test_a_same_size_corruption_with_its_mtime_set_back_reads_unavailable(
    serving: tuple[TestClient, Path],
) -> None:
    """The case `os.utime` makes invisible to a key built from mtime and size."""
    client, artifact = serving
    assert _evidence(client) == "servable", "fixture assumption: the artifact starts servable"
    before = artifact.stat()

    with artifact.open("r+b") as handle:
        handle.write(b"\0" * 16)
    os.utime(artifact, ns=(before.st_atime_ns, before.st_mtime_ns))
    after = artifact.stat()
    assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns), (
        "fixture assumption: the first key's two fields must not have moved"
    )

    assert _evidence(client) == "unavailable", (
        "`/health` answered from the memo for an artifact whose header was overwritten"
    )


def test_the_memo_still_spares_a_poll_against_an_unchanged_artifact(
    serving: tuple[TestClient, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half: the fix must not quietly remove the memo it corrects (W1 review MAJOR-1)."""
    client, _artifact_path = serving
    probed: list[Path] = []
    real = adapter._probe_database

    def counting(db: Path) -> str | None:
        probed.append(db)
        return real(db)

    monkeypatch.setattr(adapter, "_probe_database", counting)
    for _ in range(3):
        assert _evidence(client) == "servable"

    assert len(probed) == 1, f"three polls of one unchanged artifact ran the probe {len(probed)}x"


def test_discovery_warns_once_per_artifact_rather_than_once_per_request(
    serving: tuple[TestClient, Path], caplog: pytest.LogCaptureFixture
) -> None:
    """MINOR-1: the route is unauthenticated, so a per-request warning is a volume a caller picks."""
    client, artifact = serving
    artifact.write_bytes(b"not a database " * 300)

    with caplog.at_level(logging.WARNING, logger=adapter._LOG.name):
        for _ in range(5):
            assert client.get("/v1/categories").status_code == 200
        first = [r for r in caplog.records if "/v1/categories" in r.getMessage()]

        # A republished artifact that is still bad is a new fact, and says so once more.
        artifact.write_bytes(b"still not a database " * 300)
        for _ in range(3):
            assert client.get("/v1/categories").status_code == 200
        total = [r for r in caplog.records if "/v1/categories" in r.getMessage()]

    assert len(first) == 1, f"five requests against one bad artifact wrote {len(first)} warnings"
    assert len(total) == 2, f"a replaced, still-bad artifact was not reported again: {len(total)}"
