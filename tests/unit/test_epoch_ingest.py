"""Epoch CSV bundle client/parser acceptance tests (REQ-ING-010)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.clients.epoch import (
    EPOCH_BUNDLE_URL,
    EPOCH_SWE_BENCH_FILE,
    EpochClient,
    parse_swe_bench_verified,
)
from app.clients.protocols import SourceError

FIXTURE = """Model version,mean_score,Best score (across scorers),Started at,id
gemini-3.1-pro-preview-customtools,0.756198347107438,0.756198347107438,2026-02-24T13:34:48.126Z,new-run
claude-opus-4-6,0.80,0.80,2026-02-10T22:23:09.876Z,old-run
claude-opus-4-6,0.75,0.75,2026-02-18T20:07:57.705Z,newer-run
bad-score,not-a-number,0.50,2026-02-20T00:00:00Z,bad-score
bad-date,0.50,0.50,not-a-date,bad-date
"""


def _parse(raw: str = FIXTURE):
    return parse_swe_bench_verified(
        raw,
        source="epoch_swe_bench_verified",
        source_url=f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}",
    )


def test_parser_uses_project_scale_harness_date_and_provenance() -> None:
    """REQ-ING-010: the real Epoch fields map honestly to the existing ScoreRow contract."""
    rows, skipped = _parse()
    by_name = {row.raw_name: row for row in rows}

    gemini = by_name["gemini-3.1-pro-preview-customtools"]
    assert gemini.score == pytest.approx(75.6198347107438)
    assert gemini.benchmark == "SWE-bench Verified"
    assert gemini.metric == "% resolved"
    assert gemini.harness == "inspect_ai"
    assert gemini.run_date == "2026-02-24"
    assert gemini.cost_total is None
    assert gemini.source == "epoch_swe_bench_verified"
    assert gemini.source_url == f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}"
    assert skipped == 3


def test_duplicate_model_versions_keep_the_newest_evaluation() -> None:
    """REQ-ING-010: duplicate runs resolve deterministically by evidence time, not best score."""
    rows, skipped = _parse()
    claude = next(row for row in rows if row.raw_name == "claude-opus-4-6")

    assert claude.score == 75.0
    assert claude.run_date == "2026-02-18"
    assert len(rows) == 2
    assert skipped == 3  # duplicate + malformed score + malformed evaluation date

    reversed_runs = """Model version,mean_score,Started at
claude-opus-4-6,0.75,2026-02-18T20:07:57.705Z
claude-opus-4-6,0.80,2026-02-10T22:23:09.876Z
"""
    reversed_rows, reversed_skipped = _parse(reversed_runs)
    assert [(row.score, row.run_date) for row in reversed_rows] == [(75.0, "2026-02-18")]
    assert reversed_skipped == 1


@pytest.mark.parametrize(
    ("source", "source_url"),
    [
        ("", f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}"),
        ("epoch_swe_bench_verified", ""),
        ("epoch_swe_bench_verified", "fixture://not-documentation"),
    ],
)
def test_parser_rejects_missing_or_undocumented_provenance(source: str, source_url: str) -> None:
    """REQ-ING-010: source provenance is mandatory, never inferred or omitted."""
    with pytest.raises(SourceError, match="provenance"):
        parse_swe_bench_verified(FIXTURE, source=source, source_url=source_url)


@pytest.mark.parametrize(
    "raw",
    [
        "Model version,mean_score\nmodel,0.5\n",
        'Model version,mean_score,Best score (across scorers),Started at,id\n"unterminated',
        "",
    ],
)
def test_malformed_or_empty_board_fails_loudly(raw: str) -> None:
    """REQ-ING-010: a malformed board aborts this source instead of looking empty."""
    with pytest.raises(SourceError, match="epoch_swe_bench_verified"):
        _parse(raw)


def test_client_reads_only_the_allowlisted_local_csv(tmp_path: Path) -> None:
    """REQ-ING-010: the client reads the unpacked CSV bundle without HTML/network fetching."""
    (tmp_path / EPOCH_SWE_BENCH_FILE).write_text(FIXTURE, encoding="utf-8")
    client = EpochClient(tmp_path, last_verified="2026-08-15")

    assert client.fetch_raw() == FIXTURE
    assert client.name == "epoch_swe_bench_verified"
    assert client.url == f"{EPOCH_BUNDLE_URL}#{EPOCH_SWE_BENCH_FILE}"
    assert client.last_verified == "2026-08-15"

    with pytest.raises(SourceError, match="local unpacked bundle"):
        EpochClient("https://epoch.ai/data/benchmark_data.zip", last_verified="2026-08-15")


def test_client_last_verified_is_its_own_mandatory_clock(tmp_path: Path) -> None:
    """REQ-ING-010: Epoch verification time is explicit and validated independently."""
    (tmp_path / EPOCH_SWE_BENCH_FILE).write_text(FIXTURE, encoding="utf-8")
    with pytest.raises(SourceError, match="last_verified"):
        EpochClient(tmp_path, last_verified="15/08/2026")


def test_missing_epoch_board_fails_loudly_per_source(tmp_path: Path) -> None:
    """REQ-ING-010: a missing CSV aborts Epoch only with a source-identifying error."""
    client = EpochClient(tmp_path, last_verified="2026-08-15")
    with pytest.raises(SourceError, match=r"epoch_swe_bench_verified.*missing"):
        client.fetch_raw()


def test_real_epoch_swe_bench_csv_satisfies_the_parser_contract() -> None:
    """REQ-ING-010: the parser is checked against the owner-fetched real CSV shape."""
    raw_dir = os.environ.get("EPOCH_DATA_DIR")
    if raw_dir is None:
        pytest.skip("set EPOCH_DATA_DIR to the unpacked owner-fetched Epoch bundle")

    client = EpochClient(Path(raw_dir), last_verified="2026-08-15")
    rows, skipped = parse_swe_bench_verified(
        client.fetch_raw(), source=client.name, source_url=client.url
    )

    # Retrieved 2026-08-15: 35 source rows, 33 unique model versions. The two
    # duplicate rows are older evaluations and must be counted, not hidden.
    assert len(rows) == 33
    assert skipped == 2
    by_name = {row.raw_name: row for row in rows}
    assert by_name["claude-opus-4-6"].run_date == "2026-02-18"
    assert by_name["claude-opus-4-6"].score == pytest.approx(78.71900826446281)
    assert by_name["gpt-5.1-2025-11-13_high"].run_date == "2026-02-18"
    assert "gemini-3.1-pro-preview-customtools" in by_name
    assert all(row.harness == "inspect_ai" and row.source_url == client.url for row in rows)
