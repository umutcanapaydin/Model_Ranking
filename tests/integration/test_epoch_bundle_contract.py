"""Contract tests vs the real Epoch AI benchmarks bundle (V3C-44) — env-gated (#79).

M17-W3 added Epoch's own boards and `model_metadata.csv`, tested only against fixtures; a change to
their upstream layout was caught only by the nightly refresh's drift record. These read the live
bundle the refresh reads, through the same download (`fetch_bundle`) and the same parsers. They
CANNOT run in the build sandbox; they run with RUN_CONTRACT_TESTS=1 (REQ-CI-001).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CONTRACT_TESTS") != "1",
    reason="contract test needs network; set RUN_CONTRACT_TESTS=1",
)


@pytest.fixture(scope="module")
def bundle(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The live bundle, downloaded and unpacked once for the module, inside every download bound."""
    from app.clients.epoch_bundle import fetch_bundle

    return fetch_bundle(tmp_path_factory.mktemp("epoch-bundle"))


def test_every_declared_epoch_board_satisfies_the_parser_contract(bundle: Path) -> None:
    """Each declared board's file is in the bundle, parses under its declared columns, and yields
    rows on its own benchmark. One test over all of them, so one layout change lists every board it
    broke."""
    from app.clients.epoch_board import parse_board, read_bundle_file
    from app.clients.protocols import SourceError
    from app.workflows.sources import EPOCH_BOARDS

    problems: list[str] = []
    for board in EPOCH_BOARDS:
        try:
            rows, skipped = parse_board(read_bundle_file(bundle, board.file, board.source_name), board)
        except SourceError as exc:  # every board's failure is reported, not only the first
            problems.append(f"{board.source_name}: {exc}")
            continue
        if len(rows) < 5 or skipped > len(rows):
            problems.append(f"{board.source_name}: {len(rows)} rows, {skipped} skipped")
        elif {r.benchmark for r in rows} != {board.benchmark}:
            problems.append(f"{board.source_name}: benchmarks {sorted({r.benchmark for r in rows})}")
    assert problems == []


def test_the_live_model_metadata_satisfies_the_parser_contract(bundle: Path) -> None:
    """`model_metadata.csv` carries the columns the accessibility parser reads, and enough rows that
    the phone's filter is not empty (219 models linked on the 2026-09-25 candidate)."""
    from app.clients.epoch_board import read_bundle_file
    from app.workflows.access import FILE, SOURCE, parse_metadata

    rows, skipped = parse_metadata(read_bundle_file(bundle, FILE, SOURCE))
    assert len(rows) >= 200, f"only {len(rows)} rows (skipped={skipped})"
