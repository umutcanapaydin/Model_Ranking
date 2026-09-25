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
    """Plain http, for 127.0.0.1 only: the timing tests need a server that misbehaves on purpose."""
    monkeypatch.setattr(protocols, "ALLOWED_SCHEMES", frozenset({"https", "http"}))


#: How long a misbehaving server keeps it up. Past this it hangs up, so a fetch with no deadline
#: of its own FAILS the test's time assertion instead of hanging the suite.
_MISBEHAVE_S = 4.0


def _header_drip(conn: socket.socket, stop: threading.Event) -> None:
    conn.recv(65536)
    conn.sendall(b"HTTP/1.1 200 OK\r\n")
    until = time.monotonic() + _MISBEHAVE_S
    while not stop.is_set() and time.monotonic() < until:
        try:
            conn.sendall(b"X-Drip: 1\r\n")
        except OSError:
            return
        time.sleep(0.2)
    conn.close()


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
