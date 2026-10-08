"""REQ-API-009, D-185: `scripts/journey.py`, the Stage 5.2 journey the owner runs against the hosted
engine after a deploy (`docs/release-testflight.md` step 1.6), run here in process on a public artifact.

The script talks to a URL with urllib and imports nothing of the project, so `test_release_gates.py`
runs `make journey` with a stand-in for it. This runs its four steps for real: each request goes to the
app through `TestClient` instead of the network, on an artifact `public.derive` made from a fixture,
so a `/v1` change that breaks what the journey asserts fails here before the owner's deploy (the M19
repo review's M16).
"""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from app.workflows import public

from .test_api_v1 import _seeded_db

JOURNEY = Path(__file__).resolve().parents[2] / "scripts" / "journey.py"


def _journey() -> ModuleType:
    spec = importlib.util.spec_from_file_location("journey_under_test", JOURNEY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _public_artifact(tmp_path: Path) -> Path:
    """The fixture's built artifact with Epoch's SWE-bench Verified rows beside SWE-bench's own, as the
    owner's Mac has them, derived as the deploy script derives it: `coding` keeps Epoch's board, and
    the sources D-185 leaves out go."""
    from app.workflows.categories import CATEGORIES
    from app.workflows.schema import EFFORT_UNSPECIFIED

    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    spec = CATEGORIES["coding"]
    with sqlite3.connect(built) as conn:
        models = [row[0] for row in conn.execute("SELECT id FROM models ORDER BY id")]
        conn.executemany(
            "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, run_date,"
            " source, source_url, observed_at) VALUES (?, ?, ?, ?, ?, 'h', ?, '2026-08-10',"
            " 'epoch_swe_bench_verified', 'https://example.invalid', '2026-08-16T00:00:00+00:00')",
            [(mid, mid, spec.primary_benchmark, spec.metric, 50.0 + 10 * n,
              spec.ranking_effort or EFFORT_UNSPECIFIED) for n, mid in enumerate(models)])
    public.derive(built, served)
    return served


def _journey_on(artifact: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The journey, its requests sent to the app on `artifact` instead of over the network."""
    from app.adapter import main

    monkeypatch.setenv("MODEL_RANKING_DB", str(artifact))
    client = TestClient(main.app)
    module = _journey()

    def call(base: str, path: str, method: str = "GET", **_: object) -> tuple[int, dict | str]:
        assert base == "http://testserver", base
        response = client.request(method, path)
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, response.text

    monkeypatch.setattr(module, "call", call)
    return module


def test_every_journey_step_passes_on_the_public_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    journey = _journey_on(_public_artifact(tmp_path), monkeypatch)
    for name, step in journey.STEPS:
        assert step("http://testserver"), name


def test_the_journey_fails_when_coding_answers_with_no_pick(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Not vacuous: the round trip refuses a deploy whose coding surfaces both answer with nothing
    (W-023's shape), here a public artifact with every coding board left out (planted)."""
    planted = dict.fromkeys(("swebench", "epoch_swe_bench_verified", "epoch_deepswe_external"), "planted")
    monkeypatch.setattr(public, "LEFT_OUT", {**public.LEFT_OUT, **planted})
    journey = _journey_on(_public_artifact(tmp_path), monkeypatch)
    step = dict(journey.STEPS)["paying-customer round trip (asserts CONTENT)"]
    with pytest.raises(AssertionError, match="ZERO picks"):
        step("http://testserver")
