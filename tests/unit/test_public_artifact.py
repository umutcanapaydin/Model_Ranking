"""M19-W5 (#88): the hosted engine serves a public artifact, derived from the built one on the
owner's Mac with every source whose terms do not clearly permit a public app left out. The owner's
Mac keeps every source (W-129). The licence table is in the ADR this wave adds."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.workflows import public

from .test_api_v1 import _seeded_db

#: The sources the licence review of 2026-10-07 found no clear permission for (#88).
EXPECTED_LEFT_OUT = {"swebench", "epoch_arc_agi", "epoch_deepswe_external", "epoch_terminalbench",
                     "epoch_webdev", "epoch_mmlu", "openrouter"}


def _rows(db: Path, table: str) -> dict[str, int]:
    with sqlite3.connect(db) as conn:
        return dict(conn.execute(f"SELECT source, count(*) FROM {table} GROUP BY source").fetchall())


def test_the_left_out_sources_are_the_ones_the_licence_review_named() -> None:
    assert set(public.LEFT_OUT) == EXPECTED_LEFT_OUT
    assert all(reason.strip() for reason in public.LEFT_OUT.values()), "each source says why it is left out"


def test_the_public_artifact_carries_no_row_of_a_left_out_source(tmp_path: Path) -> None:
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    assert {"swebench", "epoch_deepswe_external"} <= set(_rows(built, "scores")), "the fixture seeds them"
    counts = public.derive(built, served)
    assert not set(_rows(served, "scores")) & EXPECTED_LEFT_OUT
    assert not set(_rows(served, "pricing")) & EXPECTED_LEFT_OUT
    assert counts["scores_removed"] == sum(n for s, n in _rows(built, "scores").items() if s in EXPECTED_LEFT_OUT)
    assert _rows(built, "scores")["swebench"] > 0, "the built artifact is left as it was"
    # The image's engine is not root and the copy is root's: the file must be readable by all.
    assert served.stat().st_mode & 0o004, oct(served.stat().st_mode)


def test_the_price_medians_are_rebuilt_from_the_kept_prices(tmp_path: Path) -> None:
    """A median kept from the built artifact would still carry a left-out source's prices."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        kept = sorted(conn.execute("SELECT model_id, in_m, out_m FROM px_median").fetchall())
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT alias, model_id, 999.0, 999.0, 'openrouter', 'https://openrouter.ai',"
                     " observed_at FROM pricing WHERE source = 'litellm'")
        from app.workflows.rank import build_price_medians
        build_price_medians(conn)
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        assert sorted(conn.execute("SELECT model_id, in_m, out_m FROM px_median").fetchall()) == kept


def test_a_surface_whose_only_source_is_left_out_says_it_has_no_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-121's path, not a new one: the surface answers that it has no evidence, and never a 500."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    public.derive(built, served)
    monkeypatch.setenv("MODEL_RANKING_DB", str(served))
    from app.adapter import main

    answer = TestClient(main.app).get("/v1/recommendations?task=agentic-coding").json()["answers"][0]
    assert answer["surface"] == "agentic-coding"
    assert answer["unavailable_reason_code"] == "no_evidence"
    assert answer["source_health"]["reason"] == "no_source"


def test_derive_refuses_to_overwrite_the_built_artifact(tmp_path: Path) -> None:
    built = tmp_path / "built.db"
    _seeded_db(built)
    with pytest.raises(ValueError):
        public.derive(built, built)


# --- The M19-W5 review (docs/reviews/m19-wave-5-review.md) -----------------------------------------

def test_no_openrouter_price_rides_in_under_another_source(tmp_path: Path) -> None:
    """MJ1: LiteLLM carries copies of OpenRouter's prices under `openrouter/...` aliases; leaving the
    `openrouter` source out left them in, 456 rows linked to 179 models."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT 'openrouter/' || alias, model_id, 9.0, 9.0, 'litellm', source_url,"
                     " observed_at FROM pricing WHERE source = 'litellm'")
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        assert conn.execute("SELECT count(*) FROM pricing WHERE alias LIKE 'openrouter/%'").fetchone()[0] == 0


def test_a_public_answer_credits_only_the_prices_it_serves(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MJ1: every priced answer credited "OpenRouter's public model catalog", whose prices the public
    artifact does not carry. The credit follows the price sources present; the full artifact keeps it."""
    from app.adapter import main

    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT alias, model_id, input_per_m, output_per_m, 'openrouter',"
                     " 'https://openrouter.ai/api/v1/models', observed_at FROM pricing WHERE source = 'litellm'")
    public.derive(built, served)
    for path, credits_openrouter in ((built, True), (served, False)):
        monkeypatch.setenv("MODEL_RANKING_DB", str(path))
        credits = " ".join(TestClient(main.app).get("/v1/boards").json()["attributions"])
        assert ("OpenRouter" in credits) is credits_openrouter, (path.name, credits)
        assert "litellm" in credits, credits


def test_no_byte_of_a_left_out_row_survives_in_the_file(tmp_path: Path) -> None:
    """M2: without VACUUM the deleted rows stay in the file's free pages ("ARC-AGI" 573 times in the
    shipped file), and every test passed."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    marker = "left-out-marker-7f3a9c"
    with sqlite3.connect(built) as conn:
        conn.executemany(
            "INSERT INTO scores (raw_name, benchmark, metric, score, harness, source, source_url, observed_at)"
            " VALUES (?, 'ARC-AGI', '% correct', 1.0, 'h', 'epoch_arc_agi', ?, '2026-10-01')",
            [(f"{marker}-{n}", f"https://arcprize.example/{marker}") for n in range(200)])
    assert marker.encode() in built.read_bytes()
    public.derive(built, served)
    assert marker.encode() not in served.read_bytes()


def test_the_public_artifact_carries_no_vendor_plan(tmp_path: Path) -> None:
    """M2: the subscription plans (Perplexity's among them, which its terms keep from public display)
    rode in the image, unserved by /v1. The hosted engine needs none."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO plans (id, provider, name, monthly_usd, currency, region, limits, source_url,"
                     " last_verified, observed_at) VALUES ('p', 'perplexity', 'Pro', 20, 'USD', 'US', 'x',"
                     " 'https://example.invalid', '2026-10-01', '2026-10-01')")
        conn.execute("INSERT INTO plan_models (plan_id, raw_name) VALUES ('p', 'sonar')")
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        assert conn.execute("SELECT count(*) FROM plans").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM plan_models").fetchone()[0] == 0


def test_the_public_artifact_opens_read_only_whatever_the_built_one_journals(tmp_path: Path) -> None:
    """R3: a copy of a WAL-mode artifact stays WAL, and cannot be opened read-only in a folder the
    engine cannot write (`/srv`, root's)."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
