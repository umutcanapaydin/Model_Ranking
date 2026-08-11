"""Day-1 green baseline test (seed C.1) + L.7 version-stamp contract.

Smoke test for the minimal /health endpoint. Its job is to ensure that
`make check` passes on a fresh clone (C.1), AND that the health body carries the
L.7 version stamp `{status, version, build}` from Day 1 -- so a deploy is
verifiable with one `curl /health | jq .build` (Stage 4.3). Any future failure
is a real regression, not an "I never had it working."
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.adapter.main import app


def test_health_returns_l7_contract() -> None:
    # covers seed C.1 (day-1 green baseline) + L.7 (version-stamped probe)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"  # liveness contract unchanged
    # L.7: build identity is present (CI sets APP_BUILD; defaults to "unknown")
    assert {"status", "version", "build"} <= set(body)
    assert body["build"]  # non-empty
    assert body["version"]  # non-empty
