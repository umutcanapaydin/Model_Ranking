"""Contract tests vs the real Arena datasets-server + OpenRouter APIs — env-gated.

These CANNOT run in the build sandbox (network allowlist); they run on the
owner's machine or in GitHub CI with RUN_CONTRACT_TESTS=1 (REQ-CI-001).
"""

from __future__ import annotations

import os

import pytest

from app.clients.arena_slices import SLICE_CONFIGS

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


@pytest.mark.parametrize("config", ["vision", "search", "search_factuality"])
def test_every_m15_arena_board_satisfies_the_parser_contract(config: str) -> None:
    """V3C-44 for the three M15 boards (M15-W3 review m-2): each live board parses, nothing is
    skipped wholesale, and it clears its own truncation floor."""
    from app.clients.arena import ARENA_BOARDS, ArenaClient, parse_arena

    board = ARENA_BOARDS[config]
    client = ArenaClient(config=config)
    rows, skipped = parse_arena(
        client.fetch_raw(), source=client.name, source_url=client.url, benchmark=client.benchmark
    )
    assert len(rows) >= board.minimum_rows, f"{config}: {len(rows)} rows (skipped={skipped})"
    assert {r.benchmark for r in rows} == {board.benchmark}


@pytest.mark.slice_download  # the live file: the suite's network guard steps aside (re-review 2, BLOCKING-R2-2)
@pytest.mark.parametrize("config", SLICE_CONFIGS)
def test_every_declared_slice_satisfies_the_parser_contract(config: str) -> None:
    """V3C-44 for M17-W2's canonical fake (`app.clients.fakes.slice_parquet`): the live parquet file
    parses, and every declared slice of the config clears its own floor under its own benchmark.
    Every declared config, the six Agent Arena files included (M17-W3 wave review M1)."""
    from app.clients.arena_slices import ARENA_SLICES, fetch_slices

    boards = [board for board in ARENA_SLICES if board.config == config]
    rows, refused = fetch_slices(config, boards)
    for board in boards:
        parsed = rows[board.source_name]
        problem = board.bounds_problem(len(parsed))
        assert problem is None, f"{board.source_name}: {problem} (refused={refused[board.source_name]})"
        assert {r.benchmark for r in parsed} == {board.benchmark}
