"""#25 -- the download helper bounds WHERE a fetch may go and HOW LONG all of it may take.

Found by the M17-W2 security look (S3) and its re-look (S-R3):
- `fetch_bounded_bytes` checked its deadline only while the body streamed, so the connection, the
  headers and every redirect hop ran unbounded (a header drip ran 12.2 s against a 3 s deadline;
  20 slow redirects ran 31.7 s);
- redirects were followed to any host and any scheme, up to httpx's 20.

The fix: every hop is `https` to a host the source declares, at most `MAX_REDIRECTS` of them, and
the deadline bounds the whole fetch. The Arena rows client, which read through its own stream,
goes through the same path.

Transport-level tests use respx; the timing tests use a loopback server on 127.0.0.1 (never the
network), with `http` allowed for that one host only.
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator

import httpx
import pytest
import respx

from app.clients import protocols
from app.clients.protocols import SourceError, fetch_bounded_bytes

URL = "https://source.example/data.json"


# --- where a fetch may go ------------------------------------------------------------------------


@respx.mock
def test_a_redirect_to_another_host_is_refused() -> None:
    respx.get(URL).mock(return_value=httpx.Response(302, headers={"Location": "https://evil.example/x"}))
    evil = respx.get("https://evil.example/x").mock(return_value=httpx.Response(200, content=b"x"))
    with pytest.raises(SourceError, match=r"refused a hop to https://evil.example"):
        fetch_bounded_bytes(URL, "probe", 5.0)
    assert not evil.called, "the refused hop must never be requested"


@respx.mock
def test_a_redirect_down_to_plain_http_is_refused() -> None:
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"Location": "http://source.example/data.json"}))
    with pytest.raises(SourceError, match=r"refused a hop to http://source.example"):
        fetch_bounded_bytes(URL, "probe", 5.0)


@respx.mock
def test_a_redirect_to_a_declared_host_is_followed() -> None:
    """Hugging Face sends a file on to its CDN (`us.aws.cdn.hf.co`, measured 2026-09-25)."""
    start = "https://huggingface.co/datasets/d/resolve/main/f.parquet"
    respx.get(start).mock(
        return_value=httpx.Response(302, headers={"Location": "https://us.aws.cdn.hf.co/f"}))
    respx.get("https://us.aws.cdn.hf.co/f").mock(return_value=httpx.Response(200, content=b"PAR1"))
    assert fetch_bounded_bytes(start, "probe", 5.0, hosts=("huggingface.co", ".hf.co")) == b"PAR1"


@respx.mock
def test_a_suffix_entry_is_a_domain_not_a_substring() -> None:
    """`.hf.co` admits `cdn.hf.co`, never `evilhf.co`."""
    respx.get(URL).mock(return_value=httpx.Response(302, headers={"Location": "https://evilhf.co/x"}))
    with pytest.raises(SourceError, match=r"refused a hop to https://evilhf.co"):
        fetch_bounded_bytes(URL, "probe", 5.0, hosts=("source.example", ".hf.co"))


@respx.mock
def test_more_redirects_than_the_bound_is_a_source_error() -> None:
    for i in range(protocols.MAX_REDIRECTS + 2):
        respx.get(f"https://source.example/{i}").mock(
            return_value=httpx.Response(302, headers={"Location": f"https://source.example/{i + 1}"}))
    with pytest.raises(SourceError, match="redirect"):
        fetch_bounded_bytes("https://source.example/0", "probe", 5.0)


@respx.mock
def test_a_first_url_that_is_not_https_is_refused() -> None:
    with pytest.raises(SourceError, match=r"refused a hop to http://source.example"):
        fetch_bounded_bytes("http://source.example/data.json", "probe", 5.0)


def test_every_remote_client_declares_where_it_may_go() -> None:
    """The hosts are the sources' own, and only the slice file may leave its host (for the CDN)."""
    from app.clients.arena import ArenaClient
    from app.clients.arena_slices import ArenaSliceClient

    assert ArenaClient().hosts == ("datasets-server.huggingface.co",)
    assert set(ArenaSliceClient("text").hosts) == {"huggingface.co", ".hf.co"}


@respx.mock
def test_the_arena_rows_client_refuses_a_redirect_off_its_host() -> None:
    from app.clients.arena import ROWS_API, ArenaClient

    respx.get(ROWS_API).mock(return_value=httpx.Response(302, headers={"Location": "https://evil.example/r"}))
    with pytest.raises(SourceError, match=r"refused a hop to https://evil.example"):
        ArenaClient().fetch_raw()


# --- how long all of it may take -----------------------------------------------------------------


def _serve(send: object) -> Iterator[int]:
    """A loopback server that answers every connection with `send(conn)`."""
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(8)
    stop = threading.Event()

    def loop() -> None:
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except OSError:
                continue
            threading.Thread(target=send, args=(conn, stop), daemon=True).start()  # type: ignore[arg-type]

    threading.Thread(target=loop, daemon=True).start()
    try:
        yield server.getsockname()[1]
    finally:
        stop.set()
        server.close()


@pytest.fixture
def loopback_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plain http allowed as a scheme: the timing tests need a server that misbehaves on purpose.
    Each test still passes `hosts=("127.0.0.1",)`, which is what keeps it on the loopback."""
    monkeypatch.setattr(protocols, "ALLOWED_SCHEMES", frozenset({"https", "http"}))


#: How long a misbehaving server keeps it up. Past this it hangs up, so a fetch with no deadline
#: of its own FAILS the test's time assertion instead of hanging the suite.
_MISBEHAVE_S = 4.0
#: #178: the per-read timeout of the default-deadline test, the drip's interval, and one stall of the
#: drip as long as a read took under a loaded `make check-fast` (more than 0.3 s, 2026-10-06). The
#: per-read timeout must outlast the stall by a wide margin, or it, not the deadline, ends the fetch:
#: the read has 0.7 s of slack where it had 0.1 s, and the deadline (3 s) stays under `_MISBEHAVE_S`.
_PER_READ_S = 0.75
_DRIP_S = 0.05
_LOAD_STALL_S = 0.4


def _header_drip(conn: socket.socket, stop: threading.Event, stall: float = 0.0) -> None:
    conn.recv(65536)
    conn.sendall(b"HTTP/1.1 200 OK\r\n")
    until = time.monotonic() + _MISBEHAVE_S
    while not stop.is_set() and time.monotonic() < until:
        try:
            conn.sendall(b"X-Drip: 1\r\n")
        except OSError:
            return
        time.sleep(_DRIP_S + stall)
        stall = 0.0
    conn.close()


def _header_drip_stalling_once(conn: socket.socket, stop: threading.Event) -> None:
    """The drip, with one pause as long as a loaded machine's: a stand-in for #178's run."""
    _header_drip(conn, stop, stall=_LOAD_STALL_S)


def _slow_redirect(conn: socket.socket, stop: threading.Event) -> None:
    conn.recv(65536)
    time.sleep(0.4)
    port = conn.getsockname()[1]
    try:
        conn.sendall(f"HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:{port}/next\r\n"
                     "Content-Length: 0\r\nConnection: close\r\n\r\n".encode())
    finally:
        conn.close()


def _body_drip(conn: socket.socket, stop: threading.Event) -> None:
    conn.recv(65536)
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\n")
    until = time.monotonic() + _MISBEHAVE_S
    while not stop.is_set() and time.monotonic() < until:
        try:
            conn.sendall(b"x")
        except OSError:
            return
        time.sleep(0.05)
    conn.close()


@pytest.mark.parametrize("behaviour", [_header_drip, _slow_redirect, _body_drip])
@pytest.mark.usefixtures("loopback_http")
def test_the_deadline_bounds_the_whole_fetch(behaviour: object) -> None:
    """The headers, every redirect hop and the body all count: the fetch ends at its deadline,
    whatever the server does, with a per-operation timeout that alone would never fire."""
    for port in _serve(behaviour):
        started = time.monotonic()
        with pytest.raises(SourceError, match="deadline"):
            fetch_bounded_bytes(f"http://127.0.0.1:{port}/", "probe", 5.0,
                                deadline=1.0, hosts=("127.0.0.1",))
        assert time.monotonic() - started < 2.5


# --- W-126 (M18-W6, #90): the cycle's fetches share one time budget ------------------------------


@respx.mock
def test_no_fetch_starts_once_the_cycle_budget_is_spent() -> None:
    """Past the budget the source fails at once, and carries its last good data (D-156), instead of
    one more 120 s download running the night into the engine's kill."""
    route = respx.get(URL).mock(return_value=httpx.Response(200, content=b"{}"))
    with protocols.cycle_budget(0.0), pytest.raises(SourceError, match="time budget is spent"):
        fetch_bounded_bytes(URL, "probe", 5.0)
    assert not route.called, "a fetch started after the budget was spent"
    assert fetch_bounded_bytes(URL, "probe", 5.0) == b"{}", "the budget outlived its cycle"


@pytest.mark.parametrize("behaviour", [_body_drip])
@pytest.mark.usefixtures("loopback_http")
def test_an_open_fetch_is_cut_at_the_end_of_the_cycle_budget(behaviour: object) -> None:
    """A download whose own deadline is far off still ends with the cycle's budget."""
    for port in _serve(behaviour):
        started = time.monotonic()
        with protocols.cycle_budget(1.0), pytest.raises(SourceError, match="deadline"):
            fetch_bounded_bytes(f"http://127.0.0.1:{port}/", "probe", 5.0, deadline=60.0,
                                hosts=("127.0.0.1",))
        assert time.monotonic() - started < 2.5


# --- the Tester's pins (T1-T7) -------------------------------------------------------------------


@respx.mock
def test_a_look_alike_of_the_sources_own_host_is_refused() -> None:
    """T1: an exact entry is exact. The default `source.example` must not admit `evilsource.example`."""
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"Location": "https://evilsource.example/x"}))
    with pytest.raises(SourceError, match=r"refused a hop to https://evilsource\.example"):
        fetch_bounded_bytes(URL, "probe", 5.0)


@respx.mock
def test_a_429_is_never_returned_as_data() -> None:
    """T2: `bounded_get` hands a 429 back as an answer for the Arena client's retry; every other
    source must see it as a failure, not as a body."""
    respx.get(URL).mock(return_value=httpx.Response(429, content=b'{"error": "slow down"}'))
    with pytest.raises(SourceError, match="429"):
        fetch_bounded_bytes(URL, "probe", 5.0)


@respx.mock
def test_the_arena_client_gives_up_after_its_retries_even_with_a_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """T2: the exhaustion branch, with a 429 that carries JSON a parser would happily read."""
    from app.clients import arena
    from app.clients.arena import ROWS_API, ArenaClient

    monkeypatch.setattr(arena.time, "sleep", lambda _s: None)
    route = respx.get(ROWS_API).mock(
        return_value=httpx.Response(429, content=b'{"rows": [], "num_rows_total": 0}'))
    with pytest.raises(SourceError, match="429"):
        ArenaClient().fetch_raw()
    assert route.call_count == arena._RETRIES_429 + 1


@pytest.mark.usefixtures("loopback_http")
def test_without_a_deadline_of_its_own_a_fetch_takes_four_timeouts_at_most() -> None:
    """T3: litellm, openrouter, swebench, aider and the Arena rows client pass no deadline and rely
    on the default: `DEADLINE_FACTOR` x `timeout`."""
    assert protocols.DEADLINE_FACTOR == 4.0
    for port in _serve(_header_drip_stalling_once):
        started = time.monotonic()
        with pytest.raises(SourceError, match="deadline"):
            fetch_bounded_bytes(f"http://127.0.0.1:{port}/", "probe", _PER_READ_S, hosts=("127.0.0.1",))
        assert time.monotonic() - started < protocols.DEADLINE_FACTOR * _PER_READ_S + 1.3


@respx.mock
def test_five_redirects_are_followed_and_a_sixth_is_refused() -> None:
    """T4: the bound is five, as the owner approved (2026-09-25), not merely `MAX_REDIRECTS`."""
    assert protocols.MAX_REDIRECTS == 5
    for i in range(5):
        respx.get(f"https://source.example/ok{i}").mock(
            return_value=httpx.Response(302, headers={"Location": f"https://source.example/ok{i + 1}"}))
    respx.get("https://source.example/ok5").mock(return_value=httpx.Response(200, content=b"done"))
    assert fetch_bounded_bytes("https://source.example/ok0", "probe", 5.0) == b"done"


@pytest.mark.slice_download
@respx.mock
def test_the_slice_client_follows_its_file_to_the_hugging_face_cdn() -> None:
    """T5: the slice client passes its hosts; without them the CDN hop would be refused."""
    from app.clients.arena_slices import ArenaSliceClient, parquet_url

    respx.get(parquet_url("text")).mock(
        return_value=httpx.Response(302, headers={"Location": "https://us.aws.cdn.hf.co/xet/f"}))
    respx.get("https://us.aws.cdn.hf.co/xet/f").mock(return_value=httpx.Response(200, content=b"PAR1"))
    assert ArenaSliceClient("text").fetch_bytes() == b"PAR1"


@respx.mock
def test_follow_redirects_false_is_honoured() -> None:
    """T7: the Epoch bundle passes `follow_redirects=False`; a redirect is then a failure and its
    target is never requested."""
    respx.get(URL).mock(
        return_value=httpx.Response(302, headers={"Location": "https://source.example/elsewhere"}))
    target = respx.get("https://source.example/elsewhere").mock(
        return_value=httpx.Response(200, content=b"x"))
    with pytest.raises(SourceError):
        fetch_bounded_bytes(URL, "probe", 5.0, follow_redirects=False)
    assert not target.called



# --- #71: the deadline is decided before the client is closed under the worker -------------------


class _ClosingRaces:
    """An `httpx.Client` stand-in that forces #71's interleaving every time: the worker blocks in its
    read until `close()`, then fails with EBADF, and `close()` returns only after the worker has
    recorded that error and ended. Under load that window opened by chance (the EBADF flake)."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.closed = threading.Event()

    def stream(self, *args: object, **kwargs: object) -> _ClosingRaces:
        return self

    def __enter__(self) -> None:
        self.closed.wait(5)
        raise OSError(9, "Bad file descriptor")

    def __exit__(self, *exc: object) -> None:
        return None

    def close(self) -> None:
        self.closed.set()
        # The worker records its error and ENDS before `close` returns (W4 review R2: a sleep here
        # made the old code fail only when the timing allowed it).
        for worker in [t for t in threading.enumerate() if t.name == "fetch-probe"]:
            worker.join(5)


def test_a_read_failing_after_the_deadline_is_reported_as_the_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    """#71: `bounded_get` closed the client and only then asked whether the worker was still alive.
    A worker that woke on the closed socket and exited in between turned a late fetch into
    `probe fetch failed: [Errno 9] Bad file descriptor`. Late is decided at the deadline."""
    monkeypatch.setattr(httpx, "Client", _ClosingRaces)
    with pytest.raises(SourceError, match="deadline"):
        fetch_bounded_bytes("https://source.example/", "probe", 5.0, deadline=0.2)
