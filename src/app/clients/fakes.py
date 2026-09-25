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


# --- Arena's category slices (M17-W2, #22) ------------------------------------------------------

#: The live file's eleven columns (`text/latest`, read 2026-09-24; the publish date is a string).
SLICE_COLUMNS = (
    "model_name", "organization", "license", "rating", "rating_lower", "rating_upper", "variance",
    "vote_count", "rank", "category", "leaderboard_publish_date",
)


def slice_parquet(rows: list[tuple[str, float, str, str]], *, drop: str | None = None) -> bytes:
    """A parquet file shaped like the dataset's, from `(model, rating, category, date)` rows.

    `pyarrow` is imported here, not at module level: this module is imported by tests that run the
    server, and the server must never load it (D-154).
    """
    import io

    import pyarrow as pa
    import pyarrow.parquet as pq

    values: dict[str, list[object]] = {
        "model_name": [r[0] for r in rows],
        "organization": ["org" for _ in rows],
        "license": ["proprietary" for _ in rows],
        "rating": [r[1] for r in rows],
        "rating_lower": [r[1] - 5 for r in rows],
        "rating_upper": [r[1] + 5 for r in rows],
        "variance": [1.0 for _ in rows],
        "vote_count": [1000 for _ in rows],
        "rank": [1 for _ in rows],
        "category": [r[2] for r in rows],
        "leaderboard_publish_date": [r[3] for r in rows],
    }
    if drop is not None:
        del values[drop]
    sink = io.BytesIO()
    pq.write_table(pa.table(values), sink)
    return sink.getvalue()


class FakeSliceDownload:
    """`ArenaSliceClient` fake: one config's file, or a failed download when `payload` is None."""

    def __init__(self, config: str, payload: bytes | None) -> None:
        self.config = config
        self.name = f"arena_slices_{config}"
        self.url = f"fixture://arena/{config}.parquet"
        self._payload = payload

    def fetch_bytes(self) -> bytes:
        if self._payload is None:
            msg = f"{self.name}: fixture configured to fail"
            raise SourceError(msg)
        return self._payload


def fake_slice_client(payloads: dict[str, bytes | None]) -> type[FakeSliceDownload]:
    """A client TYPE the build constructs per config, as it constructs `ArenaSliceClient`."""

    class _Configured(FakeSliceDownload):
        def __init__(self, config: str) -> None:
            super().__init__(config, payloads.get(config))

    return _Configured
