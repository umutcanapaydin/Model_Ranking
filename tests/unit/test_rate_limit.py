"""M20-W5 (#187, REQ-REL-004): the hosted engine limits how often one client may ask, so a scraper cannot
run up the traffic bill Fly cannot cap. A fairness control, so it fails OPEN (AGENTS.md section 5): a limiter
that breaks lets the request through. The limit is per client and per minute, `/health` is never
limited, and with no limit set (the owner's Mac) nothing is."""

from __future__ import annotations

import contextlib
import logging
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
    # One minute held still, so no test meets the turn of a real minute halfway (a flake the M20
    # closure's full run met in `test_an_empty_header_is_the_connection`).
    monkeypatch.setattr(main, "_rate_clock", lambda: 1_000_020.0)
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


def test_the_next_minute_serves_again() -> None:
    """The review's M2: a window ends. A client refused at the end of one minute is served in the next."""
    from app.adapter import main

    main.reset_rate_windows()
    assert [main._over_limit("a", 3, 120.0 + n)[0] for n in range(4)] == [False, False, False, True]
    assert main._over_limit("a", 3, 179.9)[0] is True
    assert main._over_limit("a", 3, 180.0)[0] is False


def test_the_next_minute_serves_again_through_the_engine(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.adapter import main

    monkeypatch.setattr(main, "_rate_clock", lambda: 600.0)
    assert [_ask(client) for _ in range(4)] == [200, 200, 200, 429]
    monkeypatch.setattr(main, "_rate_clock", lambda: 660.0)
    assert _ask(client) == 200


def test_an_ipv6_host_is_counted_by_its_64(client: TestClient) -> None:
    """The review's M1: one IPv6 host holds a whole /64, so rotating its address is one client."""
    assert [_ask(client, f"2001:db8:1:2::{n}") for n in range(1, 5)] == [200, 200, 200, 429]
    assert _ask(client, "2001:db8:1:3::1") == 200


def test_a_full_table_keeps_counting_the_clients_it_holds() -> None:
    """The review's M1: new clients past the table's size never reset the counts it holds; an old
    minute's entries make room first, and a new client with no room is served uncounted."""
    from app.adapter import main

    main.reset_rate_windows()
    for _ in range(3):
        main._over_limit("held", 3, 600.0)
    for n in range(main.RATE_WINDOW_KEYS + 50):
        main._over_limit(f"new-{n}", 3, 600.0)
    assert main.rate_window_count() <= main.RATE_WINDOW_KEYS
    assert main._over_limit("held", 3, 600.0)[0] is True, "a new crowd reset a counted client"
    main._over_limit("later", 3, 660.0)
    assert main.rate_window_count() < main.RATE_WINDOW_KEYS, "an old minute's entries were not dropped"


def test_the_boot_check_refuses_an_unreadable_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """The review's M3: through `validate_startup_config` itself, not beside it."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "lots")
    with pytest.raises(main.ConfigError, match="MODEL_RANKING_RATE_LIMIT"):
        main.validate_startup_config(env="production")
    relaxed = main.validate_startup_config(env="development")
    assert any("MODEL_RANKING_RATE_LIMIT" in problem for problem in relaxed)


def test_a_relaxed_engine_with_an_unreadable_limit_serves(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "lots")
    assert all(_ask(client) == 200 for _ in range(6))


def test_a_broken_limiter_is_logged(client: TestClient, monkeypatch: pytest.MonkeyPatch,
                                    caplog: pytest.LogCaptureFixture) -> None:
    """The review's M4: failing open is not failing silently."""
    from app.adapter import main

    def broken(*_: object) -> bool:
        raise RuntimeError("the limiter broke")

    monkeypatch.setattr(main, "_over_limit", broken)
    with caplog.at_level(logging.WARNING, logger=main.__name__):
        assert _ask(client) == 200
    assert any("rate limiter failed" in record.getMessage() for record in caplog.records)


def test_a_refusal_is_logged_once_a_minute(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """The review's M4: a refused client is seen, once per window, without its address."""
    from app.adapter import main

    with caplog.at_level(logging.INFO, logger=main.__name__):
        statuses = [_ask(client) for _ in range(6)]
    assert statuses.count(429) == 3
    said = [record.getMessage() for record in caplog.records if "rate limited" in record.getMessage()]
    assert len(said) == 1 and "203.0.113.7" not in said[0]


def test_a_strict_engine_without_a_limit_says_so(monkeypatch: pytest.MonkeyPatch,
                                                 caplog: pytest.LogCaptureFixture) -> None:
    """The review's R2: a strict engine with no limit boots, and says it serves without one."""
    from app.adapter import main

    monkeypatch.delenv("MODEL_RANKING_RATE_LIMIT", raising=False)
    with caplog.at_level(logging.WARNING, logger=main.__name__), contextlib.suppress(main.ConfigError):
        main.validate_startup_config(env="production")
    assert any("no request limit" in record.getMessage() for record in caplog.records)


# --- The W5 Tester's additions (covers REQ-REL-004): the edges the Tester probed. Five of them kill a
# planted fault the earlier tests let through (docs/reviews/m20-wave-5-tester.md). ---


def test_one_64_is_one_client_whatever_its_interface_id(client: TestClient) -> None:
    """covers REQ-REL-004 (an IPv6 /64): a host rotates the whole low 64 bits, not just the last few. A
    /96 or /112 key passed the earlier test, whose addresses differ only in the last hextet."""
    rotated = ["2001:db8:1:2::1", "2001:db8:1:2:ffff::1", "2001:db8:1:2:8000:0:0:1", "2001:db8:1:2:1:2:3:4"]
    assert [_ask(client, ip) for ip in rotated] == [200, 200, 200, 429]


def test_a_long_header_is_kept_short(client: TestClient) -> None:
    """covers REQ-REL-004 (bounded memory): the table's 10,000 keys stay small whatever a header holds, so
    a header that does not parse costs at most 64 characters a client."""
    from app.adapter import main

    long_one = "x" * 4096
    assert [_ask(client, long_one + str(n)) for n in range(4)] == [200, 200, 200, 429]
    assert main.rate_window_count() == 1
    assert all(len(key) <= 64 for key in main._RATE_WINDOWS)


def test_a_header_that_does_not_parse_is_its_own_client(client: TestClient) -> None:
    """covers REQ-REL-004: an unparsable header is served and counted as itself, never an error."""
    assert [_ask(client, "not-an-address") for _ in range(4)] == [200, 200, 200, 429]
    assert _ask(client, "203.0.113.7") == 200


def test_an_empty_header_is_the_connection(client: TestClient) -> None:
    """covers REQ-REL-004: an empty or blank `Fly-Client-IP` falls back to the connection's address,
    so it shares a count with a request that has no header at all."""
    assert client.get("/v1/budgets").status_code == 200
    assert _ask(client, "") == 200
    assert _ask(client, "   ") == 200
    assert client.get("/v1/budgets").status_code == 429


def test_a_crowded_out_client_is_served(client: TestClient) -> None:
    """covers REQ-REL-004 (fails open): with every entry this minute's, a new client is served uncounted,
    past the limit too. Refusing it would turn a full table into an outage for every new reader."""
    from app.adapter import main

    for n in range(main.RATE_WINDOW_KEYS):
        main._over_limit(f"held-{n}", 3, 600.0)
    assert [main._over_limit("crowded-out", 3, 600.0)[0] for _ in range(5)] == [False] * 5
    assert main.rate_window_count() == main.RATE_WINDOW_KEYS


def test_retry_after_is_the_rest_of_the_minute(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """covers REQ-REL-004 (`Retry-After`): the client is told the seconds left in its window."""
    from app.adapter import main

    monkeypatch.setattr(main, "_rate_clock", lambda: 645.0)
    assert [_ask(client) for _ in range(3)] == [200, 200, 200]
    refused = client.get("/v1/budgets", headers={"Fly-Client-IP": "203.0.113.7"})
    assert refused.status_code == 429
    assert refused.headers["Retry-After"] == "15"


async def test_concurrent_requests_on_one_loop_never_pass_the_limit(client: TestClient) -> None:
    """covers REQ-REL-004 (hard criterion, concurrency): requests in flight together on one event loop are
    counted one by one; exactly the limit is served."""
    import asyncio

    import httpx

    from app.adapter import main

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        answers = await asyncio.gather(
            *(ac.get("/v1/budgets", headers={"Fly-Client-IP": "203.0.113.7"}) for _ in range(12))
        )
    codes = sorted(answer.status_code for answer in answers)
    assert codes == [200] * 3 + [429] * 9


def test_an_ipv4_mapped_address_is_its_ipv4_client(client: TestClient) -> None:
    """The Tester's T1: an IPv4 address written as IPv6 (`::ffff:a.b.c.d`) is that IPv4 client, not
    one /64 shared by every IPv4 reader."""
    assert [_ask(client, f"::ffff:203.0.113.{n}") for n in range(1, 5)] == [200, 200, 200, 200]
    assert [_ask(client, "::ffff:198.51.100.9") for _ in range(4)] == [200, 200, 200, 429]
    assert _ask(client, "198.51.100.9") == 429, "the mapped and the dotted spelling are one client"


def test_a_full_table_is_scanned_once_a_minute() -> None:
    """The Tester's T2: a full table of this minute's clients is not scanned again for every new one."""
    from app.adapter import main

    main.reset_rate_windows()
    for n in range(main.RATE_WINDOW_KEYS):
        main._over_limit(f"held-{n}", 3, 600.0)
    scans = main.rate_table_scans()
    for n in range(100):
        assert main._over_limit(f"new-{n}", 3, 600.0) == (False, 60)
    assert main.rate_table_scans() - scans == 1


def test_a_broken_limiter_is_logged_once_a_minute(client: TestClient, monkeypatch: pytest.MonkeyPatch,
                                                  caplog: pytest.LogCaptureFixture) -> None:
    """The Tester's R1: a limiter that stays broken warns once a minute, not on every request."""
    from app.adapter import main

    def broken(*_: object) -> bool:
        raise RuntimeError("the limiter broke")

    monkeypatch.setattr(main, "_over_limit", broken)
    monkeypatch.setattr(main, "_rate_clock", lambda: 1200.0)
    with caplog.at_level(logging.WARNING, logger=main.__name__):
        assert all(_ask(client) == 200 for _ in range(5))
    assert sum("rate limiter failed" in record.getMessage() for record in caplog.records) == 1


def test_the_boards_answer_counts_as_thirty_requests(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The M20 closure security seat's S1: one `/v1/boards` answer is about 0.5 MB, which a phone needs
    once a day, so it counts as thirty requests: four a minute under a limit of 120."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    assert main.RATE_WEIGHTS["/v1/boards"] == 30
    statuses = [client.get("/v1/boards", headers={"Fly-Client-IP": "203.0.113.50"}).status_code for _ in range(5)]
    assert statuses[:4] == [200, 200, 200, 200] and statuses[4] == 429


def test_a_wrong_host_is_refused_before_it_is_counted(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The security seat's S2 (INV-26): a request to a Host not on the list is a 400, never a 429, and
    is not counted."""
    monkeypatch.setenv("MODEL_RANKING_ALLOWED_HOSTS", "testserver")
    wrong = [client.get("/v1/budgets", headers={"Host": "evil.example", "Fly-Client-IP": "203.0.113.60"}).status_code
             for _ in range(5)]
    assert wrong == [400] * 5
    assert _ask(client, "203.0.113.60") == 200, "the refused requests were counted"


def test_a_boards_answer_after_light_requests_crosses_the_limit_and_is_said(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The closure fixes review's M3: a `/v1/boards` answer is judged by its whole weight, and the
    refusal it causes is logged, whatever the light requests before it."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    ip = {"Fly-Client-IP": "203.0.113.70"}
    # #228: the boards window is its own, so light requests never cross it; four boards answers do.
    assert all(client.get("/v1/budgets", headers=ip).status_code == 200 for _ in range(100))
    assert all(client.get("/v1/boards", headers=ip).status_code == 200 for _ in range(4))
    with caplog.at_level(logging.INFO, logger=main.__name__):
        assert client.get("/v1/boards", headers=ip).status_code == 429
    assert any("rate limited" in record.getMessage() for record in caplog.records)


def test_a_limit_below_a_boards_weight_still_serves_one_boards_answer_a_minute(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The closure fixes review's M4: under a limit below thirty, a boards answer costs the whole
    minute rather than being refused for ever."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "10")
    monkeypatch.setattr(main, "_rate_clock", lambda: 1800.0)
    ip = {"Fly-Client-IP": "203.0.113.80"}
    assert [client.get("/v1/boards", headers=ip).status_code for _ in range(2)] == [200, 429]
    monkeypatch.setattr(main, "_rate_clock", lambda: 1860.0)
    assert client.get("/v1/boards", headers=ip).status_code == 200



def test_standings_never_block_questions(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """#228: phones behind one carrier address fetch their standings in the same minute. `/v1/boards`
    counts in a window of its own, so five fetches refuse the fifth fetch and never a question."""
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    ip = {"Fly-Client-IP": "203.0.113.90"}
    boards = [client.get("/v1/boards", headers=ip).status_code for _ in range(5)]
    assert boards == [200, 200, 200, 200, 429]
    assert all(client.get("/v1/budgets", headers=ip).status_code == 200 for _ in range(100))


def test_a_refused_request_is_not_charged() -> None:
    """#228: a request the limiter refuses costs nothing, so a client that waits is served at once."""
    from app.adapter import main

    main.reset_rate_windows()
    assert [main._over_limit("k", 3, 600.0)[0] for _ in range(6)] == [False, False, False, True, True, True]
    assert main.rate_window_used("k", 600.0) == 3



def test_each_client_has_its_own_boards_window(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The W1 review's M2: the boards window is per client, not one window for every phone."""
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    for ip in ("203.0.113.91", "203.0.113.92"):
        statuses = [client.get("/v1/boards", headers={"Fly-Client-IP": ip}).status_code for _ in range(4)]
        assert statuses == [200] * 4, (ip, statuses)


def test_questions_never_block_standings(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The W1 review's M2, the other direction: a client's 120 questions leave its standings served."""
    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    ip = {"Fly-Client-IP": "203.0.113.93"}
    assert all(client.get("/v1/budgets", headers=ip).status_code == 200 for _ in range(120))
    assert client.get("/v1/budgets", headers=ip).status_code == 429
    assert client.get("/v1/boards", headers=ip).status_code == 200


def test_a_full_table_still_counts_the_standings_of_a_client_it_holds(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The W1 review's R1: a client is one entry, its questions and its standings counted in it, so a
    table full of this minute's clients never serves a client it holds uncounted standings."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_RATE_LIMIT", "120")
    ip = {"Fly-Client-IP": "203.0.113.94"}
    assert client.get("/v1/budgets", headers=ip).status_code == 200
    for n in range(main.RATE_WINDOW_KEYS):
        main._over_limit(f"crowd-{n}", 120, main._rate_clock())
    statuses = [client.get("/v1/boards", headers=ip).status_code for _ in range(6)]
    assert statuses == [200, 200, 200, 200, 429, 429], statuses
