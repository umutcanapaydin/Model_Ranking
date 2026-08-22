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

from app.clients.arena import DATASET, FILTER_API, ROWS_API, ArenaClient
from app.clients.protocols import SourceError
from app.workflows.ingest import RunContext, ingest_arena
from app.workflows.schema import connect


def _page(offset: int, n: int, total: int, *, then_other: int = 0) -> httpx.Response:
    """One page of the split, wrapped exactly as the API wraps it.

    `then_other` appends rows from a DIFFERENT category, which is how the real split ends the
    overall board: it is ordered by category, so `chinese` simply begins. The client stops there,
    and a page containing the boundary is the only way to exercise that.
    """
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
    rows += [
        {
            "row_idx": offset + n + i,
            "row": {"model_name": f"zh{i}", "rating": 1200.0, "category": "chinese"},
        }
        for i in range(then_other)
    ]
    return httpx.Response(200, json={"rows": rows, "num_rows_total": total})


@respx.mock
def test_the_rows_endpoint_is_primary_and_the_board_stops_at_its_own_end() -> None:
    """W-024: the primary read moved, and WHY it moved is the part worth keeping.

    This used to assert that the client asked the SERVER to filter, via `where`. That endpoint no
    longer serves this dataset — it fails with no `where` clause at all — while `/rows` serves it
    fine. The client now reads the board as the ordered PREFIX of the split and stops at the first
    row outside it.

    What is preserved is the property the old test was really about: **the client takes the overall
    board and nothing else.** It just proves it on the client side now, because the server stopped
    offering to do it.
    """
    route = respx.get(ROWS_API)
    route.side_effect = [_page(0, 42, 10_000, then_other=8)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 42, "rows outside the overall board were kept"
    assert route.call_count == 1, "the client kept reading after the board ended"
    assert all(r["row"]["category"] == "overall" for r in payload["rows"])


@respx.mock
def test_it_paginates_across_the_board_and_stops_where_the_board_does() -> None:
    """The board spans pages — ~400 rows at 100 a page — so stopping early truncates it silently."""
    route = respx.get(ROWS_API)
    route.side_effect = [_page(0, 100, 10_000), _page(100, 50, 10_000, then_other=50)]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 150
    assert route.call_count == 2


@respx.mock
def test_429_backs_off_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """FP-M2-1 red test: a rate-limit response retries with backoff, never fails fast."""
    sleeps: list[float] = []
    monkeypatch.setattr("app.clients.arena.time.sleep", sleeps.append)
    route = respx.get(ROWS_API)
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        _page(0, 5, 5, then_other=1),
    ]
    payload = json.loads(ArenaClient().fetch_raw())
    assert len(payload["rows"]) == 5
    assert sleeps == [1.0]


@respx.mock
def test_429_exhaustion_fails_loud_without_full_rows_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """W-007, mirrored onto the endpoint that is primary now.

    The invariant is unchanged and is the whole point: **a failure of the primary read must abort
    this source loudly and must never begin reading a DIFFERENT surface.** W-007 was raised when a
    filter failure silently started paginating everything until the client rate-limited itself.
    W-024 swapped which endpoint is primary; it did not weaken this. The forbidden endpoint is
    simply the other one now.
    """
    monkeypatch.setattr("app.clients.arena.time.sleep", lambda _s: None)
    respx.get(ROWS_API).mock(return_value=httpx.Response(429))
    filter_route = respx.get(FILTER_API).mock(return_value=_page(0, 1, 1))
    with pytest.raises(SourceError, match="arena fetch failed"):
        ArenaClient().fetch_raw()
    assert filter_route.call_count == 0, "a failed read fell back to another endpoint (W-007)"


@respx.mock
def test_primary_failure_fails_loud_without_falling_back_to_another_endpoint() -> None:
    """W-007: endpoint drift aborts this source rather than trying somewhere else.

    This is the exact failure that produced W-024's misdiagnosis — a 500 from one endpoint — and
    the correct response to it is still to fail loudly. Reading a different surface automatically
    is what turns one bad endpoint into a self-inflicted rate limit.
    """
    respx.get(ROWS_API).mock(return_value=httpx.Response(500))
    filter_route = respx.get(FILTER_API)
    filter_route.side_effect = [_page(0, 30, 30)]
    with pytest.raises(SourceError, match="arena fetch failed"):
        ArenaClient().fetch_raw()
    assert filter_route.call_count == 0


@respx.mock
def test_page_cap_exhaustion_fails_loudly_without_falling_back(monkeypatch) -> None:
    """The anti-truncation cap still fires, and still opens no fallback path.

    It matters MORE now than it did: the split is 10,359 rows and the client stops at a category
    boundary, so a split that stopped being ordered would page forever. The cap is what turns that
    into a loud failure instead of a hundred requests — and `minimum_rows` catches the opposite
    error, a board that ends too early.
    """
    monkeypatch.setattr("app.clients.arena.time.sleep", lambda _s: None)
    rows_route = respx.get(ROWS_API)
    rows_route.side_effect = [_page(i * 100, 100, 10_000) for i in range(50)]
    filter_route = respx.get(FILTER_API)
    with pytest.raises(SourceError, match="aborted"):
        ArenaClient().fetch_raw()
    assert rows_route.call_count == 50
    assert filter_route.call_count == 0


def test_client_has_no_misleading_url_parameter() -> None:
    """M2 carried debt (M3-W3): provenance derives from the module constants the
    client actually uses — a caller can no longer pass a url= that fetch_raw ignores."""
    import inspect

    params = inspect.signature(ArenaClient.__init__).parameters
    assert "url" not in params
    provenance = httpx.URL(ArenaClient().url)
    # W-024: provenance must name the endpoint the code CALLS. It named the filter endpoint for a
    # milestone after that endpoint stopped answering — a citation nobody could follow.
    assert str(provenance).split("?", maxsplit=1)[0] == ROWS_API
    assert provenance.params["dataset"] == DATASET
    assert provenance.params["config"] == "text"
    assert provenance.params["split"] == "latest"


@respx.mock
def test_ingest_persists_the_exact_filtered_surface_as_provenance() -> None:
    """REQ-ING-004/D-101: stored provenance identifies the surface actually fetched."""
    route = respx.get(ROWS_API).mock(return_value=_page(0, 1, 1, then_other=1))
    source = ArenaClient()
    conn = connect()

    report = ingest_arena(conn, source, RunContext(observed_at="2026-08-16T00:00:00Z"))

    assert report.stored == 1
    sent = route.calls[0].request.url
    stored = conn.execute("SELECT DISTINCT source_url FROM scores WHERE source='arena'").fetchone()[
        0
    ]
    provenance = httpx.URL(stored)
    assert str(provenance).split("?", maxsplit=1)[0] == ROWS_API
    # `where` is gone: the filter endpoint no longer serves this dataset (W-024), so the
    # provenance and the request agree on the three parameters that remain.
    for key in ("dataset", "config", "split"):
        assert provenance.params[key] == sent.params[key]
        conn.close()
