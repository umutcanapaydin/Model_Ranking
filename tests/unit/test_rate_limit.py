"""M20-W5 (#187): the hosted engine limits how often one client may ask, so a scraper cannot run up the
traffic bill Fly cannot cap. A fairness control, so it fails OPEN (AGENTS.md section 5): a limiter
that breaks lets the request through. The limit is per client and per minute, `/health` is never
limited, and with no limit set (the owner's Mac) nothing is."""

from __future__ import annotations

import pathlib
import tomllib

import pytest
from fastapi.testclient import TestClient

from .test_api_v1 import _seeded_db

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def client(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.adapter import main

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "3")
    main.reset_rate_windows()
    return TestClient(main.app)


def _ask(client: TestClient, ip: str = "203.0.113.7") -> int:
    return client.get("/v1/budgets", headers={"Fly-Client-IP": ip}).status_code


def test_a_client_past_the_limit_is_told_to_wait(client: TestClient) -> None:
    assert [_ask(client) for _ in range(3)] == [200, 200, 200]
    refused = client.get("/v1/budgets", headers={"Fly-Client-IP": "203.0.113.7"})
    assert refused.status_code == 429
    assert refused.json()["error"]["code"] == "rate_limited"
    assert 1 <= int(refused.headers["Retry-After"]) <= 60
    assert refused.headers["X-Content-Type-Options"] == "nosniff"


def test_the_limit_is_per_client(client: TestClient) -> None:
    for _ in range(3):
        _ask(client, "203.0.113.7")
    assert _ask(client, "203.0.113.7") == 429
    assert _ask(client, "198.51.100.9") == 200


def test_health_is_never_limited(client: TestClient) -> None:
    for _ in range(3):
        _ask(client)
    assert client.get("/health", headers={"Fly-Client-IP": "203.0.113.7"}).status_code == 200


def test_no_limit_is_set_on_the_owners_mac(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MODEL_RANKING_RATE_LIMIT")
    assert all(_ask(client) == 200 for _ in range(10))


def test_the_limiter_fails_open(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """A fairness control: when it breaks, the reader is served, never refused."""
    from app.adapter import main

    def broken(*_: object) -> bool:
        raise RuntimeError("the limiter broke")

    monkeypatch.setattr(main, "_over_limit", broken)
    assert all(_ask(client) == 200 for _ in range(6))


def test_the_window_memory_is_bounded(client: TestClient) -> None:
    from app.adapter import main

    for n in range(main.RATE_WINDOW_KEYS + 50):
        _ask(client, f"10.0.{n // 256}.{n % 256}")
    assert main.rate_window_count() <= main.RATE_WINDOW_KEYS


def test_an_unreadable_limit_refuses_to_boot_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "lots")
    problems = main.rate_limit_problems()
    assert problems and "MODEL_RANKING_RATE_LIMIT" in problems[0]
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "-1")
    assert main.rate_limit_problems()
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    assert main.rate_limit_problems() == []


def test_the_hosted_engine_sets_its_limit() -> None:
    """#187: the deployment names its limit, so a hosted engine never runs without one."""
    fly = tomllib.loads((ROOT / "fly.toml").read_text(encoding="utf-8"))
    assert int(fly["env"]["MODEL_RANKING_RATE_LIMIT"]) > 0
