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
