"""Source-client Protocol boundaries (D-001 / K.1) — shared contract, K.8.

Every external data source is reached ONLY through one of these Protocols.
Production clients live beside a fake for tests; tests never make network
calls (permission-matrix §3).
"""

from __future__ import annotations

import contextlib
import threading
import time
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import httpx


class RawSource(Protocol):
    """Fetches one source's raw payload (JSON/YAML text) from its documented endpoint."""

    name: str
    url: str

    def fetch_raw(self) -> str:
        """Return the raw payload text. Raises SourceError on failure."""
        ...


class SourceError(RuntimeError):
    """A source could not be fetched or its payload failed validation.

    Ingestion of THIS source aborts loudly; other sources proceed
    (architecture §3 — fairness-class fail OPEN).
    """


#: The largest response body any source client will read into memory, in bytes.
#:
#: **M7 Stage-4.0 MINOR-4.** Four of the five clients had no bound at all, and the fifth checked
#: `len(resp.content)` — which is measured AFTER httpx has already buffered and decompressed the
#: whole body, so it bounded what the PARSER received and not what the process paid. The pass
#: measured the difference: a 4.6 MB gzip body expanded to 434 MB of text in a 1.94 GB process.
#:
#: 32 MiB is roughly 15x the largest real payload these sources return (litellm's price feed at
#: ~2 MB) and small enough that five of them in one build cannot exhaust an operator's machine.
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


#: The schemes a fetch may use, on its first URL and on every redirect hop (#25).
ALLOWED_SCHEMES = frozenset({"https"})
#: Redirect hops a fetch follows at most (#25; httpx's own default is 20). Hugging Face uses one.
MAX_REDIRECTS = 5
#: With no deadline of its own, a fetch may take this many of its per-operation timeouts in all:
#: connection, headers, every redirect hop and the body (#25).
DEADLINE_FACTOR = 4.0


@dataclass(frozen=True)
class Fetched:
    """One bounded fetch's answer: its final status, its headers and its body."""

    status: int
    headers: dict[str, str]
    body: bytes


def host_allowed(url: httpx.URL, hosts: Collection[str]) -> bool:
    """Whether `url` may be requested: an allowed scheme, and a host named exactly in `hosts` or
    under one of its `.domain` entries (`.hf.co` admits `cdn.hf.co`, never `evilhf.co`)."""
    host = url.host.lower()
    return url.scheme in ALLOWED_SCHEMES and any(
        host == entry or (entry.startswith(".") and host.endswith(entry)) for entry in hosts
    )


def bounded_get(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None,
    *, limit: int = MAX_RESPONSE_BYTES, deadline: float | None = None,
    follow_redirects: bool = True, hosts: Collection[str] | None = None,
) -> Fetched:
    """GET a source payload inside every bound this project keeps on a download.

    - **Bytes:** at most `limit`, counted while the body is read, so a hostile or broken upstream is
      stopped at the socket rather than after the process has paid for the body (M7 Stage 4.0).
    - **Where:** the first URL and every redirect hop must be `https` to a host in `hosts` (by
      default the first URL's own), at most `MAX_REDIRECTS` hops. A refused hop is never requested
      (#25: redirects used to go to any host and scheme, twenty deep).
    - **How long:** `deadline` (by default `DEADLINE_FACTOR` x `timeout`) bounds the WHOLE fetch:
      the connection, the headers, every redirect hop and the body. httpx's `timeout` is per
      operation, so a header drip or a chain of slow redirects never trips it (#25), and the
      deadline used to start only at the body (M16-W4 security pass, F4). The fetch runs in a
      worker thread; past the deadline the caller gets a `SourceError` at once, and the client is
      closed under the worker, which then ends at its next read.

    Build-time only (D-116): the realistic cost of an unbounded fetch is a night lost, not an outage.
    Every failure is a `SourceError`, whatever its class: an `IDNAError` from a malformed redirect
    once escaped and ended the whole build (M17-W2 security re-look, S-R3).
    """
    import httpx

    allowed = tuple(hosts) if hosts else (httpx.URL(url).host,)
    total = deadline if deadline is not None else timeout * DEADLINE_FACTOR
    started = time.monotonic()

    def hop(request: httpx.Request) -> None:
        if not host_allowed(request.url, allowed):
            msg = f"{name}: refused a hop to {request.url.scheme}://{request.url.host}"
            raise SourceError(msg)

    if not host_allowed(httpx.URL(url), allowed):
        hop(httpx.Request("GET", url))
    client = httpx.Client(timeout=timeout, follow_redirects=follow_redirects,
                          max_redirects=MAX_REDIRECTS, event_hooks={"request": [hop]})
    outcome: dict[str, Fetched | BaseException] = {}

    def fetch() -> None:
        try:
            answer = _read(client, url, params, name, limit, lambda: time.monotonic() - started > total)
            if answer is not None:
                outcome["answer"] = answer
        except BaseException as exc:  # handed to the caller, which turns it into a SourceError
            outcome["error"] = exc

    worker = threading.Thread(target=fetch, name=f"fetch-{name}", daemon=True)
    worker.start()
    worker.join(total)
    with contextlib.suppress(Exception):
        client.close()  # past the deadline this ends the worker at its next read
    late = f"{name}: the download passed its {total:.0f} s deadline and was cut off"
    if worker.is_alive():
        raise SourceError(late)
    error = outcome.get("error")
    if isinstance(error, BaseException):
        raise _source_error(error, name) from error
    answer = outcome.get("answer")
    if not isinstance(answer, Fetched):  # the worker saw the deadline pass mid-body
        raise SourceError(late)
    return answer


def _read(
    client: httpx.Client, url: str, params: dict[str, str] | None, name: str, limit: int,
    expired: Callable[[], bool],
) -> Fetched | None:
    """One streamed GET, its body capped while it is read; None once the deadline has passed."""
    with client.stream("GET", url, params=params) as response:
        if response.status_code != 429:  # a 429 is an answer: its caller decides on the retry
            response.raise_for_status()
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_bytes():
            if expired():
                return None
            size += len(chunk)
            if size > limit:
                msg = (f"{name}: response exceeded {limit} bytes and was cut off; "
                       "a source that returns more than this has changed shape")
                raise SourceError(msg)
            chunks.append(chunk)
        return Fetched(response.status_code, dict(response.headers), b"".join(chunks))


def _source_error(error: BaseException, name: str) -> SourceError:
    """Any failure of a fetch, as the `SourceError` that ends this source and no other."""
    import httpx

    if isinstance(error, SourceError):
        return error
    if isinstance(error, httpx.TooManyRedirects):
        return SourceError(f"{name}: more than {MAX_REDIRECTS} redirects")
    if isinstance(error, httpx.HTTPError):
        return SourceError(f"{name} fetch failed: {error}")
    return SourceError(f"{name} fetch failed: {type(error).__name__}: {error}")


def fetch_bounded_bytes(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None,
    *, limit: int = MAX_RESPONSE_BYTES, deadline: float | None = None,
    follow_redirects: bool = True, hosts: Collection[str] | None = None,
) -> bytes:
    """`bounded_get`'s body, for a source that treats every non-2xx answer as a failure."""
    answer = bounded_get(url, name, timeout, params, limit=limit, deadline=deadline,
                         follow_redirects=follow_redirects, hosts=hosts)
    if answer.status == 429:
        msg = f"{name} fetch failed: 429 Too Many Requests"
        raise SourceError(msg)
    return answer.body


def fetch_bounded(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None,
    *, hosts: Collection[str] | None = None,
) -> str:
    """`fetch_bounded_bytes`, decoded: every text source reads through this."""
    return fetch_bounded_bytes(url, name, timeout, params, hosts=hosts).decode("utf-8", "replace")
