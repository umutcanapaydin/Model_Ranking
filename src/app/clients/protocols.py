"""Source-client Protocol boundaries (D-001 / K.1) — shared contract, K.8.

Every external data source is reached ONLY through one of these Protocols.
Production clients live beside a fake for tests; tests never make network
calls (permission-matrix §3).
"""

from __future__ import annotations

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


def fetch_bounded(
    url: str, name: str, timeout: float, params: dict[str, str] | None = None
) -> str:
    """GET a source payload, refusing to buffer more than `MAX_RESPONSE_BYTES`.

    Streams and counts as it reads, so a hostile or broken upstream is stopped at the socket
    rather than after the process has already paid for the body. Build-time only — D-116 keeps
    ingestion off the serving host — so the realistic consequence of the unbounded version was a
    hung or OOM-killed BUILD, not a serving outage. It still chained into a worse failure: an
    out-of-memory kill mid-build used to leave a half-written artifact behind.
    """
    import httpx

    try:
        with httpx.stream(
            "GET", url, timeout=timeout, follow_redirects=True, params=params
        ) as response:
            response.raise_for_status()
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    msg = (
                        f"{name}: response exceeded {MAX_RESPONSE_BYTES} bytes and was cut off; "
                        "a source that returns more than this has changed shape"
                    )
                    raise SourceError(msg)
                chunks.append(chunk)
    except httpx.HTTPError as exc:
        msg = f"{name} fetch failed: {exc}"
        raise SourceError(msg) from exc
    return b"".join(chunks).decode("utf-8", "replace")
