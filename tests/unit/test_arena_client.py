"""ArenaClient fetch strategy — network-free via respx (W2 review + FP-M2-1).

FIXPACK FP-M2-1 red-test intake: the 2026-08-11 live run proved text/latest
carries ALL category slices (>5000 rows; page-cap abort) and that HF rate
limits bursts (429). The client now filters server-side and backs off on 429.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.clients.arena import FILTER_API, ROWS_API, WHERE_OVERALL, ArenaClient
from app.clients.protocols import SourceError


def _page(offset: int, n: int, total: int) -> httpx.Response:
    rows = [
        {
            "row_idx": offset + i,
            "row": {
                "model_name": f"m{offset + i}",
                "rating": 1300.0 + i,
                "category": "overall",
            },
        }
        for i in range(n)
    ]
    return httpx.Response(200, json={"rows": rows, "num_rows_total": total})


@respx.mock
def test_filter_endpoint_is_primary_with_overall_where() -> None:
    """FP-M2-1/2 red test: the client asks the SERVER for the 'overall' slice only."""
    route = respx.get(FILTER_API)
    route.side_effect = [_page(0, 42, 42)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 42
    sent = route.calls[0].request.url
    assert sent.params["where"] == WHERE_OVERALL
    assert "overall" in WHERE_OVERALL  # FP-M2-2: live value, not the invented 'full'
    assert route.call_count == 1


@respx.mock
def test_filter_paginates_until_total_reached() -> None:
    route = respx.get(FILTER_API)
    route.side_effect = [_page(0, 100, 150), _page(100, 50, 150)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 150
    assert route.call_count == 2


@respx.mock
def test_429_backs_off_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """FP-M2-1 red test: a rate-limit response retries with backoff, never fails fast."""
    sleeps: list[float] = []
    monkeypatch.setattr("app.clients.arena.time.sleep", sleeps.append)
    route = respx.get(FILTER_API)
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        _page(0, 5, 5),
    ]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 5
    assert sleeps == [1.0]


@respx.mock
def test_429_exhaustion_falls_back_to_rows_then_fails_loud(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.clients.arena.time.sleep", lambda _s: None)
    respx.get(FILTER_API).mock(return_value=httpx.Response(429))
    respx.get(ROWS_API).mock(return_value=httpx.Response(429))
    with pytest.raises(SourceError, match="arena fetch failed"):
        ArenaClient().fetch_raw()


@respx.mock
def test_filter_failure_falls_back_to_rows() -> None:
    """If /filter errors (endpoint drift), /rows pagination still serves — loudly capped."""
    respx.get(FILTER_API).mock(return_value=httpx.Response(500))
    rows_route = respx.get(ROWS_API)
    rows_route.side_effect = [_page(0, 30, 30)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 30
    assert rows_route.call_count == 1


@respx.mock
def test_rows_fallback_page_cap_exhaustion_fails_loudly() -> None:
    """The original live failure, preserved as a regression on the fallback path."""
    respx.get(FILTER_API).mock(return_value=httpx.Response(500))
    rows_route = respx.get(ROWS_API)
    rows_route.side_effect = [_page(i * 100, 100, 10_000) for i in range(50)]
    with pytest.raises(SourceError, match="aborted"):
        ArenaClient().fetch_raw()


def test_client_has_no_misleading_url_parameter() -> None:
    """M2 carried debt (M3-W3): provenance derives from the module constants the
    client actually uses — a caller can no longer pass a url= that fetch_raw ignores."""
    import inspect

    from app.clients.arena import ROWS_API, ArenaClient

    params = inspect.signature(ArenaClient.__init__).parameters
    assert "url" not in params
    assert ArenaClient().url.startswith(ROWS_API)
