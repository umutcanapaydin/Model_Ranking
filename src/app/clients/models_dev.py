"""models.dev pricing source: client + parser (REQ-ING-005, D-194).

Fetches ``https://models.dev/api.json``, the catalogue the ``sst/models.dev`` repository (MIT) builds,
as the second price source in OpenRouter's place (#265). The catalogue lists one model under its maker
and again under every reseller and router that serves it, OpenRouter among them. Only the maker's own
entry is read (`MAKERS`), so the second price is the vendor's list price: a reseller's discount is not
the model's price, and models.dev's copy of OpenRouter's catalogue would bring back the prices D-194
moved away from. A maker's catalogue also resells other makers' models (Zhipu's GLM under Alibaba,
DeepSeek under NVIDIA); a model whose name is another maker's family, or that carries another
publisher's namespace, is skipped (`_made_by`).

Prices arrive as numbers in $/1M tokens already. An entry that is free (0) or unpriced is skipped, never
stored as zero (schema CHECK backs this up).
"""

from __future__ import annotations

import json
from typing import Any, TypeGuard

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.registry import named_vendors, route_vendor
from app.workflows.schema import PricingRow

MODELS_DEV_URL = "https://models.dev/api.json"
_TIMEOUT_S = 30.0

#: models.dev's provider id for each model maker that sells its own models, to the route the registry
#: reads the vendor from (`registry._VENDOR_SLUGS`). Resellers and routers are not here, on purpose.
MAKERS: dict[str, str] = {
    "openai": "openai", "anthropic": "anthropic", "google": "google", "deepseek": "deepseek", "xai": "x-ai",
    "mistral": "mistral", "alibaba": "alibaba", "moonshotai": "moonshotai", "zai": "z-ai",
    "minimax": "minimax", "cohere": "cohere", "ai21": "ai21", "xiaomi": "xiaomi", "meta": "meta",
    "nvidia": "nvidia", "upstage": "upstage", "stepfun": "stepfun", "arcee": "arcee-ai",
}


class ModelsDevClient:
    """Production RawSource for the models.dev catalogue (D-001)."""

    name = "models_dev"

    def __init__(self, url: str = MODELS_DEV_URL) -> None:
        self.url = url

    def fetch_raw(self) -> str:
        return fetch_bounded(self.url, self.name, _TIMEOUT_S)


def _is_price(v: object) -> TypeGuard[int | float]:
    """A usable price: a real number, strictly positive, and not a JSON bool."""
    return isinstance(v, int | float) and not isinstance(v, bool) and v > 0


def _made_by(model_id: str, route: str) -> bool:
    """Whether ``model_id`` in the catalogue of the maker ``route`` names is that maker's own model."""
    return "/" not in model_id and named_vendors(model_id) <= {route_vendor(route)}


def parse_models_dev(
    raw: str, *, source: str = "models_dev", source_url: str = MODELS_DEV_URL
) -> tuple[list[PricingRow], int]:
    """Parse the makers' entries into pricing rows; returns (rows, skipped)."""
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"models_dev payload is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    if not isinstance(payload, dict):
        msg = f"models_dev payload is valid JSON but not an object: got {type(payload).__name__}"
        raise SourceError(msg)

    best: dict[str, PricingRow] = {}
    skipped = 0
    for provider, route in MAKERS.items():
        entry = payload.get(provider)
        if entry is None:
            continue  # a maker models.dev no longer lists; the row floor catches a hollow catalogue
        models = entry.get("models") if isinstance(entry, dict) else None
        if not isinstance(models, dict):
            msg = f"models_dev payload malformed: {provider}.models is not an object"
            raise SourceError(msg)
        for model_id, info in models.items():
            cost = info.get("cost") if isinstance(info, dict) else None
            inp = cost.get("input") if isinstance(cost, dict) else None
            out = cost.get("output") if isinstance(cost, dict) else None
            if not _is_price(inp) or not _is_price(out) or not _made_by(model_id, route):
                skipped += 1  # free, unpriced, or another maker's model: never this maker's price
                continue
            alias = f"{route}/{model_id}"
            if alias in best:  # keep-first, as OpenRouter's parser did: UNIQUE(alias, source)
                skipped += 1
                continue
            limit = info.get("limit")
            ctx = limit.get("context") if isinstance(limit, dict) else None
            best[alias] = PricingRow(
                alias=alias,
                input_per_m=float(inp),
                output_per_m=float(out),
                context=ctx if isinstance(ctx, int) and not isinstance(ctx, bool) else None,
                source=source,
                source_url=source_url,
            )
    return list(best.values()), skipped
