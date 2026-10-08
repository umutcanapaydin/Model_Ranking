"""M19-W5 (#88): the hosted engine serves a public artifact, derived from the built one on the
owner's Mac. D-186 (the owner's ruling, 2026-10-08): while the app is on TestFlight it leaves out no
source, and the licences (D-185's table) are settled before production. The derivation's machinery
(a left-out source's rows and every byte of them gone, the medians rebuilt, the survivors refused) is
held here on sources planted in `LEFT_OUT` for each test, for that day."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.workflows import public

from .test_api_v1 import _seeded_db

#: D-185's licence table, planted in `LEFT_OUT` by the tests of the machinery (D-186 left it empty).
EXPECTED_LEFT_OUT = {"swebench", "epoch_arc_agi", "epoch_deepswe_external", "epoch_terminalbench",
                     "epoch_webdev", "epoch_mmlu", "openrouter"}


@pytest.fixture
def planted(monkeypatch: pytest.MonkeyPatch) -> None:
    """D-185's table in `LEFT_OUT`, for a test of what the derivation does to a left-out source."""
    monkeypatch.setattr(public, "LEFT_OUT", {source: "planted for the test" for source in EXPECTED_LEFT_OUT})


def _rows(db: Path, table: str) -> dict[str, int]:
    with sqlite3.connect(db) as conn:
        return dict(conn.execute(f"SELECT source, count(*) FROM {table} GROUP BY source").fetchall())


def test_the_hosted_engine_leaves_out_no_source_on_testflight() -> None:
    """D-186: every source the Mac's engine serves is served by the hosted engine until production."""
    assert public.LEFT_OUT == {}


def test_the_public_artifact_keeps_every_source_and_every_openrouter_price(tmp_path: Path) -> None:
    """D-186: nothing left out, so the public artifact's scores and prices are the built one's, LiteLLM's
    copies of OpenRouter's prices included; only the vendor plans, which `/v1` never serves, go."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT 'openrouter/' || alias, model_id, 9.0, 9.0, 'litellm', source_url,"
                     " observed_at FROM pricing WHERE source = 'litellm'")
    counts = public.derive(built, served)
    assert _rows(served, "scores") == _rows(built, "scores")
    assert _rows(served, "pricing") == _rows(built, "pricing")
    assert counts["scores_removed"] == counts["pricing_removed"] == counts["openrouter_aliases_removed"] == 0


def test_the_public_artifact_carries_no_row_of_a_left_out_source(tmp_path: Path, planted: None) -> None:
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
    # Nor writable by anyone but its owner (the M19 security review's S4).
    assert not served.stat().st_mode & 0o022, oct(served.stat().st_mode)


def test_the_price_medians_are_rebuilt_from_the_kept_prices(tmp_path: Path, planted: None) -> None:
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, planted: None
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


# --- The M19-W5 review (docs/reviews/m19-wave-5-review-round-1.md) ----------------------------------------

def test_no_openrouter_price_rides_in_under_another_source(tmp_path: Path, planted: None) -> None:
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


def test_a_public_answer_credits_only_the_prices_it_serves(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, planted: None
) -> None:
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


def test_no_byte_of_a_left_out_row_survives_in_the_file(tmp_path: Path, planted: None) -> None:
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


def test_a_left_out_price_that_survives_stops_the_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, planted: None
) -> None:
    """The release re-read's N4: the survivor check's price half had no test. With the price
    deletion gone, the derivation refuses, and leaves nothing to deploy."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT alias, model_id, 1.0, 1.0, 'openrouter', 'https://openrouter.ai',"
                     " observed_at FROM pricing WHERE source = 'litellm'")
    monkeypatch.setattr(public, "_REMOVE", {"scores": public._REMOVE["scores"]})
    with pytest.raises(ValueError, match="survived"):
        public.derive(built, served)
    assert not served.exists()


def test_a_priced_credit_must_say_which_prices_it_serves() -> None:
    """The release re-read's N4: a priced call that forgets its price sources would credit
    OpenRouter again; it is refused (the second W5 review's R4)."""
    from app.workflows.rank import attributions_for

    with pytest.raises(TypeError):
        attributions_for(["arena"], priced=True)
    assert attributions_for(["arena"], priced=False)


# --- The W5 Tester seat (docs/reviews/m19-wave-5-tester.md) ------------------------------------------------

@pytest.mark.parametrize("delete_missed", ["scores", "pricing"])
def test_a_left_out_row_the_deletes_miss_stops_the_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delete_missed: str, planted: None
) -> None:
    """#88, INV-87: the survivor check is what refuses an artifact a missed delete would leave a left-out
    source's rows in; with it made a no-op (the Tester's F2) every other test passed. Nothing is written,
    and no half-derived file is left beside the target (F6)."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO pricing (alias, model_id, input_per_m, output_per_m, source, source_url,"
                     " observed_at) SELECT alias, model_id, input_per_m, output_per_m, 'openrouter',"
                     " 'https://openrouter.ai/api/v1/models', observed_at FROM pricing WHERE source = 'litellm'")
    monkeypatch.delitem(public._REMOVE, delete_missed)
    with pytest.raises(ValueError, match="survived"):
        public.derive(built, served)
    assert not served.exists()
    assert not list(tmp_path.glob("*.deriving")), "a failed derivation leaves its workspace behind"


def test_an_artifact_left_with_no_price_is_refused_and_nothing_is_written(tmp_path: Path, planted: None) -> None:
    """#88: a public artifact with no price left would answer nothing; the derivation refuses it rather
    than ship it (the Tester's F3: `<= 0` read as `< 0` passed every test)."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("UPDATE pricing SET source = 'openrouter'")
    with pytest.raises(ValueError, match="no prices"):
        public.derive(built, served)
    assert not served.exists()
    assert not list(tmp_path.glob("*.deriving"))


def test_a_priced_payload_must_say_which_price_sources_it_serves() -> None:
    """The second W5 review's R4: a priced caller that forgot `pricing_sources` credited OpenRouter on
    the hosted engine. It is refused now; with the refusal removed (the Tester's C2) every test passed."""
    from app.workflows.rank import (
        PRICING_ATTRIBUTION,
        PRICING_ATTRIBUTION_LITELLM,
        SWEBENCH_ATTRIBUTION,
        attributions_for,
    )

    with pytest.raises(TypeError, match="price sources"):
        attributions_for(["swebench"], priced=True)
    assert attributions_for(["swebench"], priced=False) == (SWEBENCH_ATTRIBUTION,), "an unpriced payload names none"
    assert attributions_for([], priced=True, pricing_sources=None) == (PRICING_ATTRIBUTION,)
    assert attributions_for([], priced=True, pricing_sources={"litellm"}) == (PRICING_ATTRIBUTION_LITELLM,)
    assert attributions_for([], priced=True, pricing_sources={"litellm", "openrouter"}) == (PRICING_ATTRIBUTION,)


def test_d186_supersedes_d185s_list_and_says_so() -> None:
    """D-186 is the ruling `LEFT_OUT` follows now, and D-185 points at it, so neither record reads as
    the list the code holds without the other."""
    text = (Path(__file__).resolve().parents[2] / "docs" / "decisions.md").read_text(encoding="utf-8")
    assert "\n## D-186 " in text
    d185 = text.split("\n## D-185", 1)[1].split("\n## ", 1)[0]
    assert "Amended by D-186" in d185


#: The surfaces whose only source D-185's table left out; every one answers since D-186.
DARK_UNDER_D185 = ("abstract", "agentic-coding", "computer-use", "web-dev")


def test_every_surface_answers_on_the_public_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """D-186: on the hosted engine `agentic-coding`, `web-dev`, `computer-use` and `abstract` answer as
    the Mac's engine does (on TestFlight they said "Nothing to recommend here"), and `coding` keeps
    SWE-bench's own board. Each surface is given rows first, so the test is not vacuous."""
    from app.adapter import main
    from app.workflows.categories import CATEGORIES
    from app.workflows.schema import EFFORT_UNSPECIFIED

    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        models = [row[0] for row in conn.execute("SELECT id FROM models ORDER BY id")]
        for surface in DARK_UNDER_D185:
            source = CATEGORIES[surface].primary_source
            if conn.execute("SELECT count(*) FROM scores WHERE source = ?", (source,)).fetchone()[0]:
                continue
            spec = CATEGORIES[surface]
            conn.executemany(
                "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort, run_date,"
                " source, source_url, observed_at) VALUES (?, ?, ?, ?, ?, 'h', ?, '2026-08-10', ?,"
                " 'https://example.invalid', '2026-08-16T00:00:00+00:00')",
                [(mid, mid, spec.primary_benchmark, spec.metric, 50.0 + 10 * n,
                  spec.ranking_effort or EFFORT_UNSPECIFIED, source) for n, mid in enumerate(models)])
    public.derive(built, served)
    assert "swebench" in _rows(served, "scores")
    monkeypatch.setenv("MODEL_RANKING_DB", str(served))
    client = TestClient(main.app)
    for surface in (*DARK_UNDER_D185, "coding"):
        answers = {a["surface"]: a for a in client.get(f"/v1/recommendations?task={surface}").json()["answers"]}
        assert answers[surface]["unavailable_reason_code"] is None and answers[surface]["picks"], surface


def test_no_table_keeps_a_row_of_a_left_out_source(tmp_path: Path, planted: None) -> None:
    """The W5 Tester's M3: the derivation cleaned `scores` and `pricing` by name; `access` also names a
    source, and a left-out source's row there survived with no error. Every table with a `source`
    column is cleaned of the left-out sources."""
    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        conn.execute("INSERT INTO access (raw_name, accessibility, source, source_url, observed_at)"
                     " VALUES ('x', 'api', 'epoch_arc_agi', 'https://arcprize.example', '2026-10-01')")
    public.derive(built, served)
    with sqlite3.connect(served) as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        for table in tables:
            columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            if "source" in columns:
                left = conn.execute(f"SELECT count(*) FROM {table} WHERE source IN ({','.join('?' * len(EXPECTED_LEFT_OUT))})",
                                    tuple(EXPECTED_LEFT_OUT)).fetchone()[0]
                assert left == 0, table
