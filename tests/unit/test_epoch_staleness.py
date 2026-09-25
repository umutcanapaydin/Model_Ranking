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


def test_ci_no_longer_ages_the_epoch_bundle() -> None:
    """D-158 clause 4 (#16): the Epoch acquisition clock is the refresh record now.

    Since M16-W4 the nightly refresh fetches the bundle itself, and each board's arrival is in
    `sources_last_ok`. The CI step that aged `data/epoch-source.yaml` measured a manual acquisition
    that no longer happens, so it would turn CI red for no reason. The owner had it removed on
    2026-09-25 (a one-time workflow change by the agent). This test replaces the one that pinned
    the step, so the step cannot quietly return. Parsed as YAML, as before: a guard that reads
    prose reports on documentation, not behaviour.
    """
    import yaml as _yaml

    doc = _yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    runs = [str(step.get("run", "")) for job in doc["jobs"].values() for step in job["steps"]]
    assert runs, "no steps read: the workflow did not parse as expected"
    assert not [r for r in runs if "app.workflows.epoch --check-staleness" in r], (
        "a CI step ages data/epoch-source.yaml again; D-158 clause 4 moved that clock into the "
        "refresh record"
    )


def test_ingest_stamp_and_committed_clock_are_one_value() -> None:
    """W4 review BLOCKING-3 citing test: the acquisition clock exists ONCE.

    The first cut kept the clock in two places — `data/epoch-source.yaml` (which CI
    checks) and a hardcoded `--last-verified` default on the only production path that
    constructs an `EpochClient`. Re-acquire the bundle, update the file, and CI goes
    green while the data keeps carrying the old stamp. A committed record that the
    ingest path does not read is not a record; it is a decoration.
    """
    import argparse
    import inspect

    from app.workflows import board_measurement
    from app.workflows.epoch import EPOCH_SOURCE_PATH, committed_last_verified

    committed = committed_last_verified()
    assert (
        committed
        == parse_epoch_source_doc(EPOCH_SOURCE_PATH.read_text(encoding="utf-8")).last_verified
    )

    # The CLI's default must BE the committed value, not a literal that matches it today.
    source = inspect.getsource(board_measurement.main)
    assert "committed_last_verified()" in source
    assert '"--last-verified", default="' not in source

    parser_defaults = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--last-verified", default=committed_last_verified())
    parser_defaults["last_verified"] = parser.parse_args([]).last_verified
    assert parser_defaults["last_verified"] == committed
