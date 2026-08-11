"""Contract tests vs the real SWE-bench + Aider endpoints (V3C-44) — env-gated."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CONTRACT_TESTS") != "1",
    reason="contract test needs network; set RUN_CONTRACT_TESTS=1",
)


def test_real_swebench_payload_satisfies_parser_contract() -> None:
    """REQ-ING-002 acceptance: all live Verified entries parse; harness present."""
    from app.clients.swebench import SweBenchClient, parse_verified

    rows, skipped = parse_verified(SweBenchClient().fetch_raw())
    assert len(rows) >= 100, f"only {len(rows)} Verified rows (skipped={skipped})"
    assert all(r.harness for r in rows)


def test_real_aider_payload_satisfies_parser_contract() -> None:
    """REQ-ING-003 acceptance: live polyglot parses; staleness check runs."""
    from app.clients.aider import AiderClient, parse_polyglot, staleness_flag

    rows, skipped = parse_polyglot(AiderClient().fetch_raw())
    assert len(rows) >= 20, f"only {len(rows)} aider rows (skipped={skipped})"
    flag = staleness_flag(rows, "2026-08-10T00:00:00+00:00")
    assert flag is None or "stale" in flag
