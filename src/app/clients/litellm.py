"""LiteLLM pricing source: client + parser (REQ-ING-001, D-101).

Fetches ``model_prices_and_context_window.json`` from LiteLLM's canonical
GitHub raw URL (documented data endpoint — NOT scraping) and parses it into
:class:`~app.workflows.schema.PricingRow` records.

Parsing rules (REQ-ING-001):
- only chat-capable entries (``mode`` in {None, "chat", "responses"});
- an entry missing EITHER input or output cost is SKIPPED, never stored as zero;
- prices are converted from $/token to $/1M tokens.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypeGuard

from app.clients.protocols import SourceError, fetch_bounded
from app.workflows.schema import PricingRow

if TYPE_CHECKING:
    from app.clients.protocols import RawSource

LITELLM_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/" "model_prices_and_context_window.json"
)
_CHAT_MODES = (None, "chat", "responses")
_TIMEOUT_S = 30.0


class LiteLLMClient:
    """Production RawSource for LiteLLM pricing (D-001)."""

    name = "litellm"

    def __init__(self, url: str = LITELLM_URL) -> None:
        self.url = url

    def fetch_raw(self) -> str:
        return fetch_bounded(self.url, self.name, _TIMEOUT_S)


def _is_price(v: object) -> TypeGuard[int | float]:
    """A usable price: real number, strictly positive, and NOT a JSON bool."""
    return isinstance(v, int | float) and not isinstance(v, bool) and v > 0


def parse_pricing(
    raw: str, *, source: str = "litellm", source_url: str = LITELLM_URL
) -> tuple[list[PricingRow], int]:
    """Parse the LiteLLM JSON into pricing rows.

    Returns ``(rows, skipped)`` where ``skipped`` counts entries dropped for
    missing prices or non-chat mode (REQ-ING-001: never stored as zero).
    """
    try:
        # Annotated `Any`, not `dict[str, Any]`, and the distinction is the bug's whole history:
        # the previous annotation ASSERTED the envelope instead of checking it, so mypy believed
        # the payload was a dict and reported the guard below as unreachable code. A type
        # annotation over `json.loads` is a wish, not a validation.
        data: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"litellm payload is not valid JSON: {exc}"
        raise SourceError(msg) from exc
    # M7-W1 security review, BLOCKING-2: this parser was the only one of the five without an
    # envelope guard. Valid JSON that is a list, a string or null reached `.items()` and raised
    # AttributeError, which is not SourceError — so it escaped every caller's except clause, killed
    # the build with an undeclared exit code, and left a half-populated database at the target. The
    # trigger is a third party's response body, not anything an operator does.
    if not isinstance(data, dict):
        msg = f"litellm payload is valid JSON but not an object: got {type(data).__name__}"
        raise SourceError(msg)

    rows: list[PricingRow] = []
    skipped = 0
    for alias, info in data.items():
        if not isinstance(info, dict) or info.get("mode") not in _CHAT_MODES:
            skipped += 1
            continue
        inp = info.get("input_cost_per_token")
        out = info.get("output_cost_per_token")
        if not _is_price(inp) or not _is_price(out):
            skipped += 1
            continue
        ctx = info.get("max_input_tokens")
        rows.append(
            PricingRow(
                alias=alias,
                input_per_m=float(inp) * 1_000_000,
                output_per_m=float(out) * 1_000_000,
                context=int(ctx) if isinstance(ctx, int) and not isinstance(ctx, bool) else None,
                source=source,
                source_url=source_url,
            )
        )
    return rows, skipped


def _static_conformance_check(client: RawSource) -> RawSource:
    """Compile-time proof that LiteLLMClient satisfies RawSource (reviewer finding)."""
    return client


if TYPE_CHECKING:
    _static_conformance_check(LiteLLMClient())
