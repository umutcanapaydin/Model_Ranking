"""OpenRouter pricing source: client + parser (REQ-ING-005, D-101).

Fetches the public, no-auth ``/api/v1/models`` catalog (documented data API,
attribution required per OpenRouter terms — carried in export metadata).
Prices arrive as STRING $/token values; converted to $/1M. Entries that are
free (0) or unpriced are skipped, never stored as zero (schema CHECK backs
this up).
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.clients.protocols import SourceError
from app.workflows.schema import PricingRow

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"
_TIMEOUT_S = 30.0


class OpenRouterClient:
    """Production RawSource for the OpenRouter model catalog (D-001)."""

    name = "openrouter"

    def __init__(self, url: str = OPENROUTER_URL) -> None:
        self.url = url

    def fetch_raw(self) -> str:
        try:
            resp = httpx.get(self.url, timeout=_TIMEOUT_S, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            msg = f"openrouter fetch failed: {exc}"
            raise SourceError(msg) from exc
        return resp.text


def _price_per_m(v: object) -> float | None:
    """OpenRouter prices are strings like '0.00000125' ($/token); bad/zero → None."""
    if isinstance(v, str) and v:
        try:
            f = float(v)
        except ValueError:
            return None
    elif isinstance(v, int | float) and not isinstance(v, bool):
        f = float(v)
    else:
        return None
    return f * 1_000_000 if f > 0 else None


def parse_models(
    raw: str, *, source: str = "openrouter", source_url: str = OPENROUTER_URL
) -> tuple[list[PricingRow], int]:
    """Parse the catalog into pricing rows; returns (rows, skipped)."""
    try:
        payload: dict[str, Any] = json.loads(raw)
        data = payload["data"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        msg = f"openrouter payload malformed: {exc!r}"
        raise SourceError(msg) from exc
    if not isinstance(data, list):
        msg = "openrouter payload malformed: data is not a list"
        raise SourceError(msg)

    best: dict[str, PricingRow] = {}
    skipped = 0
    for entry in data:
        if not isinstance(entry, dict):
            skipped += 1
            continue
        alias = entry.get("id")
        pricing = entry.get("pricing")
        if not isinstance(alias, str) or not isinstance(pricing, dict):
            skipped += 1
            continue
        in_m = _price_per_m(pricing.get("prompt"))
        out_m = _price_per_m(pricing.get("completion"))
        if in_m is None or out_m is None:
            skipped += 1  # free or unpriced entries never become 0-price rows
            continue
        ctx = entry.get("context_length")
        row = PricingRow(
            alias=alias,
            input_per_m=in_m,
            output_per_m=out_m,
            context=int(ctx) if isinstance(ctx, int) and not isinstance(ctx, bool) else None,
            source=source,
            source_url=source_url,
        )
        if alias in best:  # duplicate ids would break UNIQUE(alias, source)
            # keep-FIRST (unlike scores' keep-best): catalog order is OpenRouter's
            # canonical listing and prices are equal-authority — deliberate policy.
            skipped += 1
            continue
        best[alias] = row
    return list(best.values()), skipped
