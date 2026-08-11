"""ArenaClient pagination — network-free via respx (W2 review finding)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.clients.arena import ROWS_API, ArenaClient
from app.clients.protocols import SourceError


def _page(offset: int, n: int, total: int) -> httpx.Response:
    rows = [
        {
            "row_idx": offset + i,
            "row": {"model_name": f"m{offset + i}", "rating": 1300.0 + i, "category": "full"},
        }
        for i in range(n)
    ]
    return httpx.Response(200, json={"rows": rows, "num_rows_total": total})


@respx.mock
def test_paginates_until_total_reached() -> None:
    """150 rows → two pages (100 + 50), merged into one payload."""
    route = respx.get(ROWS_API)
    route.side_effect = [_page(0, 100, 150), _page(100, 50, 150)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 150
    assert payload["num_rows_total"] == 150
    assert route.call_count == 2


@respx.mock
def test_short_page_without_total_terminates() -> None:
    """num_rows_total missing → the short final page ends the loop."""
    route = respx.get(ROWS_API)
    route.side_effect = [
        httpx.Response(200, json={"rows": [{"row": {"model_name": "m", "rating": 1300.0}}]})
    ]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 1
    assert route.call_count == 1


@respx.mock
def test_page_cap_exhaustion_fails_loudly() -> None:
    """W2 review: exhausting _MAX_PAGES must raise, never truncate silently."""
    route = respx.get(ROWS_API)
    route.side_effect = [_page(i * 100, 100, 10_000) for i in range(50)]
    with pytest.raises(SourceError, match="aborted"):
        ArenaClient().fetch_raw()


@respx.mock
def test_http_error_maps_to_source_error() -> None:
    respx.get(ROWS_API).mock(return_value=httpx.Response(500))
    with pytest.raises(SourceError, match="arena fetch failed"):
        ArenaClient().fetch_raw()
