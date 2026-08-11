"""Contract test vs the real LiteLLM endpoint (V3C-44) — env-gated.

Runs ONLY when RUN_CONTRACT_TESTS=1 (CI job or owner machine); the default
test suite stays network-free (permission-matrix §3).
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CONTRACT_TESTS") != "1",
    reason="contract test needs network; set RUN_CONTRACT_TESTS=1",
)


def test_real_litellm_payload_satisfies_parser_contract() -> None:
    """REQ-ING-001 acceptance: the live payload yields ≥500 priced chat aliases."""
    from app.clients.litellm import LiteLLMClient, parse_pricing

    rows, skipped = parse_pricing(LiteLLMClient().fetch_raw())
    assert len(rows) >= 500, f"only {len(rows)} priced aliases (skipped={skipped})"
    sample = rows[0]
    assert sample.input_per_m > 0
    assert sample.output_per_m > 0
