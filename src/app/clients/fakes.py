"""Canonical fakes for source clients (one per integration — V3C-44).

Tests use these instead of the network (permission-matrix §3: no outbound
HTTP from tests).
"""

from __future__ import annotations

from app.clients.protocols import SourceError


class FakeRawSource:
    """RawSource fake returning a fixed payload (or raising, to test fail paths)."""

    def __init__(
        self,
        name: str,
        payload: str | None,
        url: str = "fixture://payload",
        *,
        last_verified: str | None = None,
    ) -> None:
        self.name = name
        self.url = url
        self.last_verified = last_verified
        self._payload = payload

    def fetch_raw(self) -> str:
        if self._payload is None:
            msg = f"{self.name}: fixture configured to fail"
            raise SourceError(msg)
        return self._payload
