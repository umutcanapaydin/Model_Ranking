"""Contract tests vs the real Arena datasets-server + OpenRouter APIs — env-gated.

These CANNOT run in the build sandbox (network allowlist); they run on the
owner's machine or in GitHub CI with RUN_CONTRACT_TESTS=1 (REQ-CI-001).
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CONTRACT_TESTS") != "1",
    reason="contract test needs network; set RUN_CONTRACT_TESTS=1",
)


def test_real_openrouter_catalog_satisfies_parser_contract() -> None:
    """REQ-ING-005 acceptance: live catalog yields ≥100 priced models."""
    from app.clients.openrouter import OpenRouterClient, parse_models

    rows, skipped = parse_models(OpenRouterClient().fetch_raw())
    assert len(rows) >= 100, f"only {len(rows)} priced models (skipped={skipped})"
    assert all(r.input_per_m > 0 for r in rows)


def test_real_arena_latest_satisfies_parser_contract() -> None:
    """REQ-ING-007/REQ-CAT-002 acceptance: live text/latest yields ≥20 Elo rows."""
    from app.clients.arena import ArenaClient, parse_arena

    rows, skipped = parse_arena(ArenaClient().fetch_raw())
    assert len(rows) >= 20, f"only {len(rows)} arena rows (skipped={skipped})"
    assert all(r.metric == "elo" and r.harness == "arena-crowd" for r in rows)
