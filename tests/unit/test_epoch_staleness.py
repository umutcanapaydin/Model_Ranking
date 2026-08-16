"""Epoch acquisition-clock cadence tests (REQ-ING-010, V4C-50)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from app.clients.epoch import EPOCH_BUNDLE_URL
from app.clients.protocols import SourceError
from app.workflows.epoch import check_staleness, main, parse_epoch_source_doc

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DOC = REPO_ROOT / "data" / "epoch-source.yaml"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "contract-tests.yml"


def test_shipped_epoch_clock_is_source_specific_and_fresh_on_entry_day() -> None:
    """REQ-ING-010: acquisition age is explicit and remains separate from evaluation dates."""
    raw = SOURCE_DOC.read_text(encoding="utf-8")
    doc = parse_epoch_source_doc(raw)
    assert doc.source_url == EPOCH_BUNDLE_URL
    assert doc.last_verified == "2026-08-15"
    assert check_staleness(raw, dt.date(2026, 11, 13)) == []  # age 90: boundary is fresh
    stale = check_staleness(raw, dt.date(2026, 11, 14))
    assert len(stale) == 1 and "91 days old" in stale[0]


def test_epoch_clock_cli_exit_codes_through_real_entrypoint(tmp_path, capsys) -> None:
    """REQ-ING-010: the exact CI command returns 0 fresh, 1 stale, and 2 invalid input."""
    assert main(["--check-staleness", str(SOURCE_DOC), "--today", "2026-11-13"]) == 0
    assert main(["--check-staleness", str(SOURCE_DOC), "--today", "2026-11-14"]) == 1
    assert "STALE: epoch-benchmark-data" in capsys.readouterr().out
    assert main(["--check-staleness", str(tmp_path / "missing.yaml")]) == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "schema: 2",
        "staleness_days: 0",
        "id: wrong-source",
        "source_url: https://example.invalid/bundle.zip",
        "last_verified: 15/08/2026",
    ],
)
def test_epoch_clock_rejects_wrong_schema_threshold_or_provenance(mutation: str) -> None:
    """REQ-ING-010: every authored metadata field is load-bearing and fails loudly."""
    raw = SOURCE_DOC.read_text(encoding="utf-8")
    originals = {
        "schema: 2": "schema: 1",
        "staleness_days: 0": "staleness_days: 90",
        "id: wrong-source": "id: epoch-benchmark-data",
        "source_url: https://example.invalid/bundle.zip": f"source_url: {EPOCH_BUNDLE_URL}",
        "last_verified: 15/08/2026": "last_verified: 2026-08-15",
    }
    with pytest.raises(SourceError):
        parse_epoch_source_doc(raw.replace(originals[mutation], mutation))


def test_weekly_workflow_wires_the_epoch_clock_without_a_conditional() -> None:
    """V4C-49: the signed cadence rule ships with one unconditional CI consumer."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    command = "python -m app.workflows.epoch --check-staleness data/epoch-source.yaml"
    assert workflow.count(command) == 1
    plan_job = workflow.split("\n  plan-staleness:", 1)[1].split("\n  live-contracts:", 1)[0]
    assert command in plan_job
    step = plan_job[plan_job.index(command) - 180 : plan_job.index(command) + len(command)]
    assert "if:" not in step
