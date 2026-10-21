"""Contract tests vs the real SWE-bench + Aider endpoints (V3C-44) — env-gated."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs("contract")  # #137: RUN_CONTRACT_TESTS=1 and the network


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


def test_real_terminalbench_4_submissions_satisfy_parser_contract() -> None:
    """REQ-SRC-012 acceptance (#265): the live TB 4.0 repository's submissions parse, none skipped."""
    from app.clients.terminalbench import TerminalBench4Client, parse_terminalbench_4

    client = TerminalBench4Client()
    rows, skipped = parse_terminalbench_4(client.fetch_raw(), source=client.name, source_url=client.url)
    assert len(rows) >= 10, f"only {len(rows)} TB 4.0 rows (skipped={skipped})"
    assert skipped == 0 and all(0 <= r.score <= 100 for r in rows)


def test_real_datacurve_leaderboard_satisfies_parser_contract() -> None:
    """REQ-SRC-012 acceptance (#265, D-216): Datacurve's own leaderboard parses whole with no token: every
    configuration a row at its stated effort, above the floor."""
    from app.clients.datacurve import DatacurveClient, parse_datacurve
    from app.workflows.sources import REMOTE_SOURCES

    rows, skipped = parse_datacurve(DatacurveClient().fetch_raw())
    floor = next(s for s in REMOTE_SOURCES if s.name == "datacurve_deepswe").minimum_rows
    assert len(rows) >= floor and skipped == 0, f"{len(rows)} rows, {skipped} skipped"
    assert all(0 <= r.score <= 100 and r.harness for r in rows)


def test_real_osworld_verified_workbook_satisfies_parser_contract() -> None:
    """REQ-SRC-013 acceptance (#379, D-219): the live OSWorld-Verified workbook, from the site's own host with no token,
    reads into general models at 100 steps, above the floor."""
    from app.clients.osworld import OSWorldClient, parse_osworld
    from app.workflows.sources import REMOTE_SOURCES

    rows, skipped = parse_osworld(OSWorldClient().fetch_raw())
    floor = next(s for s in REMOTE_SOURCES if s.name == "osworld_verified").minimum_rows
    assert len(rows) >= floor, f"{len(rows)} rows, {skipped} skipped"
    assert all(0 <= r.score <= 100 and r.harness == "OSWorld (100 steps)" for r in rows)


def test_the_committed_arc_agi_2_derivation_is_the_datasets_current_revision() -> None:
    """REQ-SRC-012 acceptance (#265): ARC Prize has not moved its public-evaluation dataset past the revision
    `data/arc-agi-2-public-eval.json` was derived at. When it has, re-run `scripts/derive_arc_public_eval.py`."""
    import json

    from app.clients.arc_prize import ArcAgi2Client
    from app.clients.protocols import fetch_bounded

    committed = json.loads(ArcAgi2Client().fetch_raw())["revision"]
    live = json.loads(fetch_bounded("https://huggingface.co/api/datasets/arcprize/arc_agi_v2_public_eval",
                                    "arc_agi_2", 30.0))["sha"]
    assert live == committed, f"the dataset moved from {committed[:12]} to {live[:12]}: re-derive it"
