"""M18-W1 (#87, D-171, REQ-DEV-001) -- the engine checks the Host, and serves beyond loopback only with a list.

The owner's phone reaches the engine on his home network, by opt-in. Two things keep that narrow:
a request whose Host is not on the service's list is refused (a browser page cannot rebind a name to
the engine, the M17 closure security seat's INFO I-4), and a bind beyond loopback with no list does
not start. Without a list, as in tests and by-hand development, every Host is served, but only on
loopback: a request that arrived on a network address is refused, whatever the bind (review B1).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter

from .test_api_v1 import _seeded_db

HOSTS = "MODEL_RANKING_ALLOWED_HOSTS"
BIND = "MODEL_RANKING_BIND"
LIST = "127.0.0.1,localhost,umut-macbook-pro-2.local,192.168.0.26"


@pytest.fixture()
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "pipeline.db"
    _seeded_db(path)
    monkeypatch.setenv("MODEL_RANKING_DB", str(path))
    monkeypatch.delenv(HOSTS, raising=False)
    monkeypatch.delenv(BIND, raising=False)
    return path


@pytest.mark.parametrize("base", ["http://127.0.0.1:8080", "http://localhost:8080",
                                  "http://Umut-MacBook-Pro-2.local:8080", "http://192.168.0.26:8080"])
def test_a_host_on_the_list_is_served(db: Path, monkeypatch: pytest.MonkeyPatch, base: str) -> None:
    monkeypatch.setenv(HOSTS, LIST)
    assert TestClient(adapter.app, base_url=base).get("/v1/categories").status_code == 200


@pytest.mark.parametrize("base", ["http://evil.example", "http://127.0.0.1.evil.example:8080",
                                  "http://192.168.0.27:8080", "http://umut-macbook-pro-2.local.evil.example"])
def test_a_host_not_on_the_list_is_refused(db: Path, monkeypatch: pytest.MonkeyPatch, base: str) -> None:
    monkeypatch.setenv(HOSTS, LIST)
    response = TestClient(adapter.app, base_url=base).get("/v1/categories")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_host"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_without_a_list_every_host_is_served(db: Path) -> None:
    """Tests and by-hand development set no list; nothing changes for them."""
    assert TestClient(adapter.app, base_url="http://evil.example").get("/v1/categories").status_code == 200


def test_a_bind_beyond_loopback_needs_a_list_of_hosts(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def complains() -> bool:
        return any(HOSTS in problem for problem in adapter.validate_startup_config("test"))

    monkeypatch.setenv(BIND, "0.0.0.0")
    assert complains(), "a bind beyond loopback with no list must refuse to start (the service's preflight)"
    monkeypatch.setenv(HOSTS, LIST)
    assert not complains()
    monkeypatch.delenv(HOSTS)
    for loopback in ("127.0.0.1", "localhost", "::1"):
        monkeypatch.setenv(BIND, loopback)
        assert not complains(), loopback


def test_without_a_list_a_request_arriving_on_a_network_address_is_refused(db: Path) -> None:
    """W1 review B1: `make run` and a hand-typed uvicorn bound 0.0.0.0 with no list, and a foreign
    Host was served. With no list, only what arrives on loopback is served, whatever the bind."""
    response = TestClient(adapter.app, base_url="http://192.168.0.26:8080").get("/v1/categories")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_host"
    assert TestClient(adapter.app, base_url="http://127.0.0.1:8080").get("/v1/categories").status_code == 200


def test_the_host_is_compared_without_case_on_both_sides(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W1 review M5: httpx and URLSession lower-case the host, so only a raw header tests the header
    side, and only a mixed-case entry tests the list side."""
    monkeypatch.setenv(HOSTS, "127.0.0.1,Umut-MacBook-Pro-2.local")
    client = TestClient(adapter.app, base_url="http://127.0.0.1:8080")
    assert client.get("/v1/categories", headers={"host": "UMUT-MACBOOK-PRO-2.LOCAL:8080"}).status_code == 200
    assert client.get("/v1/categories", headers={"host": "umut-macbook-pro-2.local"}).status_code == 200


def test_an_empty_host_is_refused_when_a_list_is_set(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(HOSTS, LIST)
    response = TestClient(adapter.app, base_url="http://127.0.0.1:8080").get("/v1/categories", headers={"host": ""})
    assert response.status_code == 400


def test_an_ipv6_host_is_compared_without_its_brackets_or_port(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """W1 Tester T2: `_host_name`'s bracket branch never ran; `[::1]:8080` is `::1` on the list."""
    monkeypatch.setenv(HOSTS, "127.0.0.1,::1")
    client = TestClient(adapter.app, base_url="http://127.0.0.1:8080")
    assert client.get("/v1/categories", headers={"host": "[::1]:8080"}).status_code == 200
    assert client.get("/v1/categories", headers={"host": "[::1]"}).status_code == 200
    assert client.get("/v1/categories", headers={"host": "[::2]:8080"}).status_code == 400
    assert client.get("/v1/categories", headers={"host": "[::1"}).status_code == 400


def test_without_a_list_a_connection_with_no_local_address_is_not_called_a_network_one() -> None:
    """W1 Tester T2: `_arrived_off_loopback`'s first branch never ran. uvicorn reports no address, or a
    path, for a Unix socket; neither is a network address."""
    assert adapter._arrived_off_loopback(None) is False
    assert adapter._arrived_off_loopback(("/tmp/engine.sock", None)) is False
    assert adapter._arrived_off_loopback(("192.168.0.26", 8080)) is True
    assert adapter._arrived_off_loopback(("::1", 8080)) is False
