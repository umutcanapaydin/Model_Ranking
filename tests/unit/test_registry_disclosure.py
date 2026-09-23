"""M16-W4 P5, D-157 clause 4 -- the engine says which models it derived and which names it could not.

Ruled 2026-09-23 (W4 plan decision 2): disclosure is the engine's. `/v1` and the app do not change;
the build report, the refresh record and `/health` name the derived models and the names nothing
matched -- the curation that remains, made visible instead of discovered.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from app.adapter import nightly
from app.workflows.refresh import EXIT_PUBLISHED, RefreshOutcome, refresh, status_path, write_status

from .test_build import AIDER, PRICING
from .test_refresh_carry import _sources, _use

WITH_GPT6 = json.dumps({**json.loads(PRICING), "openrouter/openai/gpt-6-astra": {
    "mode": "chat", "input_cost_per_token": 2e-06, "output_cost_per_token": 1.6e-05}})
AIDER_GPT6 = json.dumps([*json.loads(AIDER),
                         {"model": "gpt-6-astra", "pass_rate_2": 80.0, "edit_format": "diff"},
                         {"model": "mystery-model-9", "pass_rate_2": 50.0, "edit_format": "diff"},
                         {"model": "gpt-5-image", "pass_rate_2": 40.0, "edit_format": "diff"}])


def test_a_cycle_records_the_models_it_derived_and_the_names_it_could_not_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = tmp_path / "advisor.db"
    _use(monkeypatch, _sources(pricing=WITH_GPT6, aider=AIDER_GPT6))
    outcome, code = refresh(live)
    assert code == EXIT_PUBLISHED, outcome.reason
    record = json.loads(status_path(live).read_text(encoding="utf-8"))
    assert record["derived"] == ["gpt6-astra"]
    assert "mystery-model-9" in record["unmatched"]
    assert "gpt-6-astra" not in record["unmatched"]
    # the modality guard refusing an image model is the guard working, not a model we are missing
    assert "gpt-5-image" not in record["unmatched"]


def test_health_counts_the_derived_models_and_names_the_top_unmatched(tmp_path: Path) -> None:
    target = tmp_path / "advisor.db"
    outcome = RefreshOutcome(published=True, reason="r", live_fingerprint=None,
                             candidate_fingerprint="", surfaces=1,
                             derived=("gpt6-astra", "kimi-k3"),
                             unmatched=("mystery-model-9", "another-1", "a2", "a3", "a4", "a5"))
    write_status(target, outcome, 0, at=dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp())
    report = nightly.NightlyRefresh(db=target, command=["unused"]).report()
    assert report["refresh_derived"] == "2"
    assert report["refresh_unmatched"] == "mystery-model-9, another-1, a2, a3, a4"


def test_a_cycle_that_is_not_served_keeps_the_served_lists(tmp_path: Path) -> None:
    """The lists describe the SERVED artifact: a refused candidate's registry is not what readers see."""
    target = tmp_path / "advisor.db"
    at = dt.datetime(2026, 9, 23, tzinfo=dt.UTC).timestamp()

    def cycle(code: int, derived: tuple[str, ...]) -> dict:
        write_status(target, RefreshOutcome(published=code == 0, reason="r", live_fingerprint=None,
                                            candidate_fingerprint="", surfaces=1, derived=derived),
                     code, at=at)
        return json.loads(status_path(target).read_text(encoding="utf-8"))

    assert cycle(0, ("gpt6-astra",))["derived"] == ["gpt6-astra"]
    assert cycle(3, ("gpt6-astra", "kimi-k3"))["derived"] == ["gpt6-astra"]
