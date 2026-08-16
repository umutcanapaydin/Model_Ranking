"""Replay contract for the signed M5-W1 board decision evidence."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import pytest

from app.clients.protocols import SourceError
from app.workflows.board_measurement import (
    BASELINE_EXTRACT_SHA256,
    BASELINE_RAW_ROWS,
    BASELINE_RAW_SHA256,
    BASELINE_RETRIEVED_AT,
    BASELINE_SOURCE_COMMIT,
    BASELINE_STORED_ROWS,
    W1Measurement,
    main,
    measure_w1_boards,
    validate_baseline_snapshot,
)


def _real_measurement() -> tuple[W1Measurement, Path]:
    raw_dir = os.environ.get("EPOCH_DATA_DIR")
    if raw_dir is None:
        pytest.skip("set EPOCH_DATA_DIR to the unpacked owner-fetched Epoch bundle")
    root = Path(__file__).resolve().parents[2]
    report = measure_w1_boards(
        raw_dir,
        plans_raw=(root / "data/plans.yaml").read_text(encoding="utf-8"),
        rosters_raw=(root / "data/rosters.yaml").read_text(encoding="utf-8"),
        baseline_raw=(root / "data/m5-swebench-baseline.json").read_text(encoding="utf-8"),
        today=dt.date(2026, 8, 16),
        last_verified="2026-08-15",
    )
    return report, root


def test_real_five_board_measurement_replays_the_signed_engine_results() -> None:
    """REQ-SUB-007: real registry/coverage/ranking reproduces before + five candidates."""
    report, _ = _real_measurement()

    baseline = report.baseline
    assert (baseline.csv_rows, baseline.stored_rows, baseline.skipped_rows) == (180, 173, 7)
    assert (baseline.scoreable_plans, baseline.total_plans) == (1, 10)
    assert (baseline.fresh, baseline.stale, baseline.undated, baseline.unscored) == (0, 1, 0, 9)
    assert [
        (row.plan, row.model, row.score, row.harness, row.evidence_date, row.status)
        for row in baseline.selected
    ] == [
        (
            "Google AI Pro",
            "Gemini 3 Pro",
            77.4,
            "live-SWE-agent",
            "2025-11-20",
            "stale",
        )
    ]

    measured = {row.candidate: row for row in report.candidates}
    expected = {
        "Epoch SWE-bench Verified": (35, 33, 2, 0, 5, 2, 3, 0, 5),
        "DeepSWE": (50, 13, 0, 37, 6, 0, 0, 6, 4),
        "FrontierCode": (25, 20, 5, 0, 3, 0, 0, 3, 7),
        "TerminalBench": (204, 181, 23, 0, 5, 0, 5, 0, 5),
        "Aider polyglot": (77, 71, 6, 0, 0, 0, 0, 0, 10),
    }
    assert {
        name: (
            row.csv_rows,
            row.stored_rows,
            row.skipped_rows,
            row.filtered_rows,
            row.scoreable_plans,
            row.fresh,
            row.stale,
            row.undated,
            row.unscored,
        )
        for name, row in measured.items()
    } == expected

    assert all(row.evidence_date is None for row in measured["DeepSWE"].selected)
    assert all(row.evidence_date is None for row in measured["FrontierCode"].selected)
    assert {row.evidence_date for row in measured["TerminalBench"].selected} == {"2026-03-13"}
    assert {row.status for row in measured["TerminalBench"].selected} == {"stale"}


def test_gemini_contradiction_is_preserved_in_the_decision_record() -> None:
    """REQ-REC-012: both real rows and their configuration disagreement stay disclosed."""
    report, root = _real_measurement()
    conflict = report.gemini_contradiction

    assert conflict.epoch_model == "gemini-3.1-pro-preview-customtools"
    assert conflict.epoch_score == pytest.approx(0.756198347107438)
    assert conflict.epoch_harness == "inspect_ai"
    assert conflict.epoch_evaluation_date == "2026-02-24"
    assert conflict.epoch_log_id == "8QQQWDgmmEsmQVUJWcxx4P"
    assert conflict.epoch_log_url.endswith("/8QQQWDgmmEsmQVUJWcxx4P.eval")
    assert conflict.deepswe_model == "gemini-3.1-pro-preview"
    assert conflict.deepswe_score == pytest.approx(0.11751662971175167)
    assert (conflict.deepswe_harness, conflict.deepswe_effort) == ("mini-swe-agent", "high")
    assert conflict.ratio == pytest.approx(6.434819897084048)
    assert conflict.verdict.startswith("unresolved")

    decision = (root / "docs/reviews/m5-w1-board-measurement.md").read_text(encoding="utf-8")
    for artifact in (
        conflict.epoch_model,
        "75.6",
        conflict.epoch_harness,
        conflict.epoch_log_id,
        conflict.epoch_log_url,
        conflict.deepswe_model,
        "11.8",
        conflict.deepswe_harness,
        f"`{conflict.deepswe_effort}` effort",
        "unresolved causally",
    ):
        assert artifact in decision


def test_complete_baseline_snapshot_rejects_truncation_and_provenance_drift() -> None:
    """REQ-SUB-007: before evidence is complete and pinned, not a self-proving mini fixture."""
    root = Path(__file__).resolve().parents[2]
    path = root / "data/m5-swebench-baseline.json"
    raw = path.read_text(encoding="utf-8")
    validate_baseline_snapshot(raw)
    payload = json.loads(raw)
    assert payload["snapshot"] == {
        "source_commit": BASELINE_SOURCE_COMMIT,
        "source_url": (
            "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/"
            f"{BASELINE_SOURCE_COMMIT}/data/leaderboards.json"
        ),
        "raw_sha256": BASELINE_RAW_SHA256,
        "extract_sha256": BASELINE_EXTRACT_SHA256,
        "retrieved_at": BASELINE_RETRIEVED_AT,
        "board": "Verified",
        "raw_rows": BASELINE_RAW_ROWS,
        "parser_expected_rows": BASELINE_STORED_ROWS,
        "fields": ["name", "resolved", "date", "cost"],
    }
    assert len(payload["leaderboards"][0]["results"]) == BASELINE_RAW_ROWS

    payload["leaderboards"][0]["results"].pop()
    with pytest.raises(SourceError, match="truncated"):
        validate_baseline_snapshot(json.dumps(payload))
    payload["snapshot"]["source_commit"] = "mutable-master"
    with pytest.raises(SourceError, match="provenance"):
        validate_baseline_snapshot(json.dumps(payload))

    payload = json.loads(raw)
    payload["leaderboards"][0]["results"][0]["name"] = "silently replaced row"
    with pytest.raises(SourceError, match="content drifted"):
        validate_baseline_snapshot(json.dumps(payload))


def test_real_measurement_cli_applies_d109_once_at_json_boundary(
    capsys, tmp_path: Path, monkeypatch
) -> None:
    """REQ-REC-010/REQ-REC-012: real entry keeps raw math but emits one-decimal scores."""
    raw_dir = os.environ.get("EPOCH_DATA_DIR")
    if raw_dir is None:
        pytest.skip("set EPOCH_DATA_DIR to the unpacked owner-fetched Epoch bundle")

    monkeypatch.chdir(tmp_path)  # defaults resolve from the repository, not the caller's cwd
    assert main(["--bundle-dir", raw_dir]) == 0
    output_text = capsys.readouterr().out
    output = json.loads(output_text)
    conflict = output["gemini_contradiction"]
    assert conflict["epoch_score"] == 75.6
    assert conflict["deepswe_score"] == 11.8
    assert conflict["ratio"] == 6.4
    assert conflict["score_unit"] == "percentage points"
    assert "0.756198347107438" not in output_text
    assert "0.11751662971175167" not in output_text

    emitted_scores: list[float] = []

    def collect(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if (key == "score" or key.endswith("_score")) and isinstance(child, float):
                    emitted_scores.append(child)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(output)
    assert emitted_scores
    assert all(score == round(score, 1) for score in emitted_scores)
