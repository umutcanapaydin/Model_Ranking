"""Source-client Protocol boundaries (D-001 / K.1) — shared contract, K.8.

Every external data source is reached ONLY through one of these Protocols.
Production clients live beside a fake for tests; tests never make network
calls (permission-matrix §3).
"""

from __future__ import annotations

import time
from typing import Protocol


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


def fetch_bounded_bytes(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None,
    *, limit: int = MAX_RESPONSE_BYTES, deadline: float | None = None,
    follow_redirects: bool = True,
) -> bytes:
    """GET a source payload, refusing to buffer more than `limit` (`MAX_RESPONSE_BYTES` by default).

    Streams and counts as it reads, so a hostile or broken upstream is stopped at the socket
    rather than after the process has already paid for the body. Build-time only — D-116 keeps
    ingestion off the serving host — so the realistic consequence of the unbounded version was a
    hung or OOM-killed BUILD, not a serving outage. It still chained into a worse failure: an
    out-of-memory kill mid-build used to leave a half-written artifact behind.

    `timeout` is httpx's, PER operation: a body drip-fed one byte a minute never trips it.
    `deadline` bounds the whole download in seconds (M16-W4 security pass, F4).
    """
    import httpx

    started = time.monotonic()

    try:
        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=follow_redirects, params=params
        ) as response:
            response.raise_for_status()
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if deadline is not None and time.monotonic() - started > deadline:
                    msg = f"{name}: the download passed its {deadline:.0f} s deadline and was cut off"
                    raise SourceError(msg)
                if total > limit:
                    msg = (
                        f"{name}: response exceeded {limit} bytes and was cut off; "
                        "a source that returns more than this has changed shape"
                    )
                    raise SourceError(msg)
                chunks.append(chunk)
    except SourceError:
        raise
    except httpx.HTTPError as exc:
        msg = f"{name} fetch failed: {exc}"
        raise SourceError(msg) from exc
    except Exception as exc:
        # M17-W2 security re-look S-R3: a redirect to a malformed host (`Location: http://xn--/x`)
        # raised `IDNAError` from inside httpx, which is not an `httpx.HTTPError`. It escaped, the
        # build re-raised it, and one upstream's bad redirect ended the cycle for every source.
        msg = f"{name} fetch failed: {type(exc).__name__}: {exc}"
        raise SourceError(msg) from exc
    return b"".join(chunks)


def fetch_bounded(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None
) -> str:
    """`fetch_bounded_bytes`, decoded: every text source reads through this."""
    return fetch_bounded_bytes(url, name, timeout, params).decode("utf-8", "replace")
