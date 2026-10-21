"""`agentic-coding` moves from Epoch's copy of DeepSWE to Datacurve's own leaderboard (#265, D-216) — cite REQ-SRC-012.

The surface, its family and the registry name the new source; Epoch's copy is no longer built, and stays attributed
and credited as a retired source, so an artifact an older release built still boots (D-194 clause 6). Datacurve is
credited for its leaderboard. Through the build's own ingest and the served API, `agentic-coding` answers from the
recorded leaderboard at `high` effort, and a night the site fails is carried by the refresh (D-156).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_litellm
from app.workflows.rank import build_price_medians
from app.workflows.registry import reconcile
from app.workflows.schema import connect

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "datacurve"
SITE = "https://deepswe.datacurve.ai/"


def _leaderboard() -> str:
    """D-216: Datacurve's own leaderboard, the list the source reads."""
    return (FIXTURES / "leaderboard-live.json").read_text(encoding="utf-8")


def test_agentic_coding_ranks_on_datacurve_and_epochs_copy_is_not_built() -> None:
    """covers REQ-SRC-012 (D-216 clause 1): the surface, its family and the registry; nothing builds Epoch's copy."""
    from app.workflows import categories, families, sources

    spec = categories.CATEGORIES["agentic-coding"]
    assert (spec.primary_source, spec.primary_benchmark, spec.metric, spec.ranking_effort) == (
        "datacurve_deepswe", "DeepSWE", "% resolved", "high")
    assert families.FAMILIES["agentic-coding"] == ("datacurve_deepswe", "terminalbench_4", "arena_agent")
    assert "datacurve_deepswe" in {s.name for s in sources.REMOTE_SOURCES}
    assert "epoch_deepswe_external" not in {b.name for b in sources.LOCAL_BUNDLES}
    assert all("epoch_deepswe_external" not in family for family in families.FAMILIES.values())


def test_datacurve_is_credited_for_its_leaderboard_with_its_link() -> None:
    """covers REQ-SRC-012 (D-216 clauses 2 and 8): the citation names the publisher and the leaderboard's link, and the
    Credits screen names Datacurve's leaderboard, which publishes no licence, used under D-215. Nothing is built from
    the CC BY 4.0 dataset, so it is not credited."""
    from app.workflows import board_tables, rank

    citation = rank.SOURCE_ATTRIBUTION["datacurve_deepswe"]
    assert "Datacurve" in citation and SITE in citation and "huggingface.co" not in citation
    assert citation in rank.ATTRIBUTIONS
    assert [c["id"] for c in rank.credits_for([citation])] == ["datacurve_site"]
    site = board_tables.CREDITS["datacurve_site"]
    assert (site.publisher, site.url, site.licence_url) == ("Datacurve", SITE, None) and "D-215" in site.licence
    assert "datacurve" not in board_tables.CREDITS


def test_epochs_copy_stays_attributed_and_credited_as_a_retired_source() -> None:
    """covers REQ-SRC-012 (D-216 clause 6, D-194 clause 6): an older artifact's rows keep D-193's citation and its
    credit, so the engine boots on it until the refresh replaces it; no build names the source again."""
    from app.workflows import board_tables, rank

    retired = board_tables.RETIRED_EXTERNAL_ATTRIBUTION["epoch_deepswe_external"]
    assert "https://deepswe.datacurve.ai/" in retired and "epoch_deepswe_external" not in rank.SOURCE_ATTRIBUTION
    assert "epoch_deepswe_external" not in board_tables.EPOCH_EXTERNAL_ATTRIBUTION
    assert rank.attributions_for(["epoch_deepswe_external"], priced=False) == (retired,)
    assert [c["id"] for c in rank.credits_for([retired])] == ["datacurve_leaderboard", "epoch_compilation"]
    assert board_tables.CREDITS["datacurve_leaderboard"].licence == "© Datacurve; no licence published"


def _built(path: Path) -> None:
    """The leaderboard through the build's own ingest, with a LiteLLM price for every model it names."""
    from app.workflows import sources

    models = {row["model"] for row in json.loads(_leaderboard())["rows"]}
    prices = json.dumps({name: {"mode": "chat", "input_cost_per_token": 3e-06, "output_cost_per_token": 1.5e-05}
                         for name in sorted(models)})
    conn = connect(str(path))
    run = RunContext(observed_at="2026-10-21T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", prices), run)
    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")
    assert declared.ingest(conn, FakeRawSource("datacurve_deepswe", _leaderboard()), run).stored == 70
    reconcile(conn)
    build_price_medians(conn)
    conn.commit()
    conn.close()


def test_every_model_on_the_leaderboard_links_a_catalogue_model(tmp_path: Path) -> None:
    """covers REQ-SRC-012 (D-216): the leaderboard's 70 rows name 28 models, and the alias rules link each."""
    db = tmp_path / "built.db"
    _built(db)
    with sqlite3.connect(db) as conn:
        linked = dict(conn.execute("SELECT raw_name, model_id FROM scores WHERE source = 'datacurve_deepswe'"))
    assert len(linked) == 28 and all(linked.values()), linked
    assert linked["gpt-6-astra"] == "gpt6-astra" and linked["claude-opus-5"] == "claude-5-opus"


def test_agentic_coding_answers_from_the_leaderboard_at_high_effort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-012 (D-216 clauses 1 and 3): from the leaderboard, the surface's best `high` run is
    Gemini 3.8 Flash's 73.8; GPT-6 Astra's `xhigh` 74.1, the board's top score, is not ranked as a `high` one."""
    from app.adapter import main

    db = tmp_path / "built.db"
    _built(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    answer = TestClient(main.app).get("/v1/recommendations?task=agentic-coding").json()["answers"][0]
    assert answer["unavailable_reason_code"] is None, answer
    top = answer["picks"][0]
    assert top["label"] == "best_quality" and top["score"] == 73.8, top


def test_the_surface_was_calibrated_on_the_leaderboard_it_reads() -> None:
    """covers REQ-SRC-012 (D-216 clause 7): the record measured Datacurve's leaderboard, not the June dataset job."""
    written = json.loads(Path("docs/research/d216-agentic-coding-calibration.json").read_text(encoding="utf-8"))
    assert "leaderboard" in written["stderr_from"] and written["ranked_population"] >= 19, written


def test_a_night_the_site_fails_is_carried_and_the_surface_still_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """covers REQ-SRC-012 (D-216 clause 6, the owner's ruling of 2026-10-21; D-156): a pin on the path that already
    holds. Through `build()`, the real entry point: the live artifact holds last night's leaderboard; tonight the
    site fails, the source is carried with its rows unchanged, no operator action names it, and `agentic-coding`
    answers from the carried board, never an empty one."""
    import dataclasses

    from app.adapter import main
    from app.workflows import sources
    from app.workflows.build import build

    from .test_build import PLANS_YAML, ROSTERS_YAML, _sources
    from .test_carry_forward import NOW, _iso, _rows

    models = {row["model"] for row in json.loads(_leaderboard())["rows"]}
    prices = json.dumps({name: {"mode": "chat", "input_cost_per_token": 3e-06, "output_cost_per_token": 1.5e-05}
                         for name in sorted(models)})
    declared = next(s for s in sources.REMOTE_SOURCES if s.name == "datacurve_deepswe")

    def with_site(payload: str | None) -> tuple[sources.RemoteSource, ...]:
        site = dataclasses.replace(declared, client=lambda: FakeRawSource("datacurve_deepswe", payload))
        return (*_sources(pricing=prices), site)

    live = tmp_path / "advisor.db"
    conn = connect(str(live))
    build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=with_site(_leaderboard()), minimum_models=2)
    conn.close()
    assert len(_rows(live, "datacurve_deepswe")) == 70

    tonight = tmp_path / "candidate.db"
    conn = connect(str(tonight))
    report = build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=with_site(None), minimum_models=2,
                   carry_from=live, last_ok={"datacurve_deepswe": _iso(1)}, now=NOW)
    assert report.carried == {"datacurve_deepswe": pytest.approx(1.0)}
    assert _rows(conn, "datacurve_deepswe") == _rows(live, "datacurve_deepswe")
    assert not any("datacurve" in a or "agentic-coding" in a for a in report.required_operator_actions)
    conn.close()

    monkeypatch.setenv("MODEL_RANKING_DB", str(tonight))
    answer = TestClient(main.app).get("/v1/recommendations?task=agentic-coding").json()["answers"][0]
    assert answer["unavailable_reason_code"] is None and answer["picks"], answer
    assert answer["picks"][0]["score"] == 73.8
