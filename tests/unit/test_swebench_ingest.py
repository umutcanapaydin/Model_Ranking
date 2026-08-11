"""SWE-bench Verified ingestion tests — cite REQ-ING-002 and REQ-ING-004."""

from __future__ import annotations

import json

import pytest

from app.clients.fakes import FakeRawSource
from app.clients.protocols import SourceError
from app.clients.swebench import parse_verified, split_harness
from app.workflows.ingest import RunContext, ingest_swebench
from app.workflows.schema import connect

FIXTURE = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Lite",
                "results": [{"name": "SomeAgent + SomeModel", "resolved": 99.0}],
            },
            {
                "name": "Verified",
                "results": [
                    {
                        "name": "live-SWE-agent + Claude 4.5 Opus medium",
                        "resolved": 79.2,
                        "date": "2025-12-15",
                        "cost": 376.9,
                    },
                    {"name": "TRAE + Doubao-Seed-Code", "resolved": 78.8, "date": "2025-09-28"},
                    {"name": "SoloEntryNoPlus", "resolved": 50.0},
                    {"name": "broken-entry", "resolved": None},
                    {"name": "bool-entry", "resolved": True},
                ],
            },
        ]
    }
)


def _fake() -> FakeRawSource:
    return FakeRawSource("swebench", FIXTURE)


def test_only_verified_board_is_parsed() -> None:
    """REQ-ING-002: Lite/Multimodal rows never mix into Verified results."""
    rows, skipped = parse_verified(FIXTURE)
    assert {r.raw_name for r in rows} == {
        "live-SWE-agent + Claude 4.5 Opus medium",
        "TRAE + Doubao-Seed-Code",
        "SoloEntryNoPlus",
    }
    assert all(r.benchmark == "SWE-bench Verified" for r in rows)
    assert skipped == 2  # broken-entry (None) + bool-entry (True)


def test_harness_is_retained_with_every_score() -> None:
    """REQ-ING-002: a score is a model+harness pair; no '+' → unknown-agent."""
    rows, _ = parse_verified(FIXTURE)
    by_name = {r.raw_name: r for r in rows}
    assert by_name["live-SWE-agent + Claude 4.5 Opus medium"].harness == "live-SWE-agent"
    assert by_name["TRAE + Doubao-Seed-Code"].harness == "TRAE"
    assert by_name["SoloEntryNoPlus"].harness == "unknown-agent"


def test_run_date_and_cost_are_stored() -> None:
    """REQ-ING-002: % resolved + run date (+cost when present) survive parsing."""
    rows, _ = parse_verified(FIXTURE)
    by_name = {r.raw_name: r for r in rows}
    top = by_name["live-SWE-agent + Claude 4.5 Opus medium"]
    assert top.run_date == "2025-12-15"
    assert top.cost_total == 376.9
    assert by_name["TRAE + Doubao-Seed-Code"].cost_total is None


def test_duplicate_entry_names_keep_best_score() -> None:
    """Reviewer regression: resubmitted duplicate names must not abort the source."""
    payload = json.dumps(
        {
            "leaderboards": [
                {
                    "name": "Verified",
                    "results": [
                        {"name": "Agent + Model", "resolved": 70.0},
                        {"name": "Agent + Model", "resolved": 75.0},
                        {"name": "Agent + Model", "resolved": 60.0},
                    ],
                }
            ]
        }
    )
    rows, skipped = parse_verified(payload)
    assert len(rows) == 1
    assert rows[0].score == 75.0
    assert skipped == 2
    conn = connect()
    report = ingest_swebench(conn, FakeRawSource("swebench", payload), RunContext(observed_at="t"))
    assert report.stored == 1


def test_nonlist_results_fails_loudly() -> None:
    payload = json.dumps({"leaderboards": [{"name": "Verified", "results": "oops"}]})
    with pytest.raises(SourceError, match="not a list"):
        parse_verified(payload)


def test_split_harness_edges() -> None:
    assert split_harness("A + B") == ("A", "B")
    assert split_harness("NoPlus") == ("unknown-agent", "NoPlus")


def test_ingest_stores_with_provenance_and_replaces() -> None:
    """REQ-ING-004: provenance stamped; re-run replaces the working set."""
    conn = connect()
    ingest_swebench(conn, _fake(), RunContext(observed_at="t1"))
    report = ingest_swebench(conn, _fake(), RunContext(observed_at="t2"))
    assert report.stored == 3
    stamps = {
        r[0]
        for r in conn.execute("SELECT DISTINCT observed_at FROM scores WHERE source='swebench'")
    }
    assert stamps == {"t2"}


def test_missing_verified_board_fails_loudly() -> None:
    payload = json.dumps({"leaderboards": [{"name": "Lite", "results": []}]})
    with pytest.raises(SourceError, match="no Verified leaderboard"):
        parse_verified(payload)


def test_malformed_payload_fails_loudly() -> None:
    with pytest.raises(SourceError, match="malformed"):
        parse_verified('{"nope": 1}')
