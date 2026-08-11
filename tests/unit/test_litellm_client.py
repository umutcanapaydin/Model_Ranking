"""LiteLLM client HTTP error mapping — network-free via respx (reviewer finding)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.clients.litellm import LiteLLMClient
from app.clients.protocols import SourceError

URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"


@respx.mock
def test_http_error_maps_to_source_error() -> None:
    respx.get(URL).mock(return_value=httpx.Response(500))
    with pytest.raises(SourceError, match="litellm fetch failed"):
        LiteLLMClient().fetch_raw()


@respx.mock
def test_network_failure_maps_to_source_error() -> None:
    respx.get(URL).mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(SourceError, match="litellm fetch failed"):
        LiteLLMClient().fetch_raw()


@respx.mock
def test_success_returns_body() -> None:
    respx.get(URL).mock(return_value=httpx.Response(200, text='{"ok": {}}'))
    assert LiteLLMClient().fetch_raw() == '{"ok": {}}'
