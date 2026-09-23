"""M16-W4 P2 -- Epoch's 2026-09 layout, and a changed layout that fails loud.

Epoch moved the capabilities index from `epoch_capabilities_index.csv` into a directory, one row
per model under its display name, with the score column renamed to `eci`. The build read the old
path, found nothing, and the `everyday` surface's primary board CARRIED (D-156) with nothing saying
why -- a layout change that looks exactly like a quiet night. So a declared board that is missing
or reshaped in a bundle that DID arrive is recorded as drift, by name, carried or not, and reaches
the refresh record and `/health`.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from app.adapter import nightly
from app.clients.epoch_board import parse_board
from app.workflows.build import build
from app.workflows.refresh import RefreshOutcome, status_path, write_status
from app.workflows.schema import connect
from app.workflows.sources import EPOCH_BOARDS

from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

ECI = next(b for b in EPOCH_BOARDS if b.source_name == "epoch_eci")
NEW_ECI = (
    "Model,Display name,eci,eci_ci_low,eci_ci_high,date,Organization\n"
    "GPT-6 Astra,GPT-6 Astra,166.6,163.0,172.03,2026-09-03,OpenAI\n"
    "Claude Opus 5,Claude Opus 5,162.67,160.1,165.2,2026-08-01,Anthropic\n"
)
GPQA = "Model version,mean_score,Started at\ngpt-5,0.85,2026-09-01T00:00:00Z\n"


def test_the_capabilities_index_is_declared_where_the_2026_09_bundle_puts_it() -> None:
    assert ECI.file == "epoch_capabilities_index/eci_scores.csv"


def test_the_capabilities_index_reads_the_2026_09_layout() -> None:
    rows, skipped = parse_board(NEW_ECI, ECI)
    assert {r.raw_name: r.score for r in rows} == {"GPT-6 Astra": 166.6, "Claude Opus 5": 162.67}
    assert skipped == 0
    # `date` is a model's release date, and a release date never becomes evidence (epoch-source.yaml)
    assert {r.run_date for r in rows} == {None}


def _build_with_bundle(tmp_path: Path, bundle: Path | None) -> object:
    conn = connect(str(tmp_path / "candidate.db"))
    return build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
                 minimum_models=2, bundle_dir=bundle)


def test_a_board_missing_from_a_bundle_that_arrived_is_drift(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "gpqa_diamond.csv").write_text(GPQA, encoding="utf-8")
    report = _build_with_bundle(tmp_path, bundle)
    drifted = {line.split(":")[0] for line in report.drift}  # type: ignore[attr-defined]
    assert "epoch_eci" in drifted
    assert "epoch_deepswe_external" in drifted, "the two bundle clients report drift like the boards"
    assert "epoch_gpqa" not in drifted
    assert report.sources_json()["drift"] == report.drift  # type: ignore[attr-defined]


def test_no_bundle_at_all_is_not_drift(tmp_path: Path) -> None:
    """Nothing arrived, so nothing changed shape: that is a missing source, reported as one."""
    assert _build_with_bundle(tmp_path, None).drift == []  # type: ignore[attr-defined]


def test_drift_reaches_the_refresh_record_and_health(tmp_path: Path) -> None:
    target = tmp_path / "advisor.db"
    outcome = RefreshOutcome(published=False, reason="r", live_fingerprint=None,
                             candidate_fingerprint="", surfaces=1,
                             drift=("epoch_eci: missing CSV in local unpacked bundle",))
    write_status(target, outcome, 1, at=dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp())
    record = json.loads(status_path(target).read_text(encoding="utf-8"))
    assert record["drift"] == ["epoch_eci: missing CSV in local unpacked bundle"]
    report = nightly.NightlyRefresh(db=target, command=["unused"]).report()
    assert report["refresh_drift"] == "epoch_eci"


def test_a_cycle_records_the_drift_its_build_found(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Through the real `refresh()` and `build.main`: a fetched bundle without the index."""
    from app.workflows.refresh import refresh

    from .test_refresh_carry import _first_cycle

    live = _first_cycle(tmp_path, monkeypatch)

    def fetch(dest: Path) -> None:
        (dest / "gpqa_diamond.csv").write_text(GPQA, encoding="utf-8")

    refresh(live, fetch_epoch=fetch)
    record = json.loads(status_path(live).read_text(encoding="utf-8"))
    assert any(line.startswith("epoch_eci:") for line in record["drift"])
