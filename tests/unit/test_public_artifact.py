"""M19-W5 (#88): the hosted engine serves a public artifact, derived from the built one on the
owner's Mac with every source whose terms do not clearly permit a public app left out. The owner's
Mac keeps every source (W-129). The licence table is in the ADR this wave adds."""

from __future__ import annotations

import re
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
    # Nor writable by anyone but its owner (the M19 security review's S4).
    assert not served.stat().st_mode & 0o022, oct(served.stat().st_mode)


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


# --- The M19-W5 review (docs/reviews/m19-wave-5-review-round-1.md) ----------------------------------------

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


def test_a_left_out_price_that_survives_stops_the_derivation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delete_missed: str
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


def test_an_artifact_left_with_no_price_is_refused_and_nothing_is_written(tmp_path: Path) -> None:
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


def test_the_adr_names_every_source_the_public_artifact_leaves_out() -> None:
    """#88's ruling is an ADR (wave plan P3): D-185's table and `LEFT_OUT` name the same sources, so
    neither can drop or add one alone (the Tester's R1: a row deleted from D-185 passed every test)."""
    text = (Path(__file__).resolve().parents[2] / "docs" / "decisions.md").read_text(encoding="utf-8")
    adr = text.split("\n## D-185", 1)[1].split("\n## ", 1)[0]
    tabled = set(re.findall(r"^\s*\| `([a-z_]+)` \|", adr, re.MULTILINE))
    assert tabled == set(public.LEFT_OUT), (tabled, sorted(public.LEFT_OUT))


#: D-185 clause 3: the surfaces whose only source the public artifact leaves out.
DARK_ON_THE_HOSTED_ENGINE = ("abstract", "agentic-coding", "computer-use", "web-dev")


def test_each_surface_whose_only_source_is_left_out_goes_dark_and_coding_keeps_epochs_board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Wave plan P3: "each affected surface saying it has no evidence", and D-185: `coding` ranks on
    Epoch's SWE-bench Verified. The wave's test drives one of the four, on a fixture where it is the only
    one with rows. Here each surface is given rows first, so each answers on the built artifact (the test
    is not vacuous), and `coding` gets Epoch's rows beside SWE-bench's own. Deleting by benchmark rather
    than by source (the Tester's F11) darkened `coding` and passed every test."""
    from app.adapter import main
    from app.workflows.categories import CATEGORIES
    from app.workflows.schema import EFFORT_UNSPECIFIED

    built, served = tmp_path / "built.db", tmp_path / "public.db"
    _seeded_db(built)
    with sqlite3.connect(built) as conn:
        models = [row[0] for row in conn.execute("SELECT id FROM models ORDER BY id")]
        feeds = [(surface, CATEGORIES[surface].primary_source) for surface in DARK_ON_THE_HOSTED_ENGINE]
        for surface, source in [*feeds, ("coding", "epoch_swe_bench_verified")]:
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
    for path in (built, served):
        monkeypatch.setenv("MODEL_RANKING_DB", str(path))
        client = TestClient(main.app)
        for surface in (*DARK_ON_THE_HOSTED_ENGINE, "coding"):
            answers = {a["surface"]: a for a in client.get(f"/v1/recommendations?task={surface}").json()["answers"]}
            answer = answers[surface]
            if path == served and surface != "coding":
                assert answer["unavailable_reason_code"] == "no_evidence", (path.name, surface, answer)
                assert answer["source_health"]["reason"] == "no_source", (path.name, surface)
            else:
                assert answer["unavailable_reason_code"] is None and answer["picks"], (path.name, surface, answer)


def test_the_adr_and_the_runbook_name_the_surfaces_that_go_dark() -> None:
    """D-185 clause 3 and the owner's runbook say which surfaces answer "no evidence" on the hosted
    engine; the test above holds the engine to that list, and this holds the two records to it (the
    Tester's R4: one surface dropped from the runbook's sentence passed every test)."""
    root = Path(__file__).resolve().parents[2]
    adr = (root / "docs" / "decisions.md").read_text(encoding="utf-8").split("\n## D-185", 1)[1].split("\n## ", 1)[0]
    runbook = (root / "docs" / "release-testflight.md").read_text(encoding="utf-8")
    for name, text in (("D-185", adr), ("docs/release-testflight.md", runbook)):
        flat = " ".join(text.split())
        named = re.search(r"((?:`[a-z-]+`(?:, | and ))+`[a-z-]+`) (?:say|answer)[^.]*no evidence on the hosted engine", flat)
        assert named, name
        assert set(re.findall(r"`([a-z-]+)`", named.group(1))) == set(DARK_ON_THE_HOSTED_ENGINE), (name, named.group(1))
