"""#403: a media surface never shows a per-token price.

A media board's model ranks with no price by construction (D-218 clause 1), but `/v1/standings` prices a model, not
a surface: a media board name that resolved to a priced text model's id would show that model's per-token price on
an image or video board. On 2026-10-23's candidate no such collision exists; the build now names one in its drift,
which the night records and `/health` lists, so a latent risk cannot become a live one unseen.
"""

from __future__ import annotations

from app.workflows import build as build_module
from app.workflows.categories import CATEGORIES
from app.workflows.schema import connect

MEDIA = next(spec for spec in CATEGORIES.values() if not spec.priced)


def _artifact(*, priced: bool) -> object:
    conn = connect(":memory:")
    conn.execute("INSERT INTO models (id, display, vendor) VALUES ('gpt-4o', 'GPT-4o', 'openai')")
    conn.execute("INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score, harness, source_url,"
                 " observed_at) VALUES ('gpt-4o', 'GPT-4o (image)', ?, ?, ?, 1200, 'arena-crowd', 'u', 't')",
                 (MEDIA.primary_source, MEDIA.primary_benchmark, MEDIA.metric))
    if priced:
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('gpt-4o', 2.5, 10.0)")
    return conn


def test_a_media_board_model_with_a_text_price_is_named() -> None:
    lines = build_module.media_price_collisions(_artifact(priced=True))
    assert len(lines) == 1 and "gpt-4o" in lines[0] and MEDIA.primary_source in lines[0], lines


def test_a_media_board_model_with_no_price_is_not_a_collision() -> None:
    assert build_module.media_price_collisions(_artifact(priced=False)) == []


def test_the_build_reports_a_collision_in_its_drift(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """The wiring: whatever the check finds reaches the build's drift, which the night records."""
    from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

    monkeypatch.setattr(build_module, "media_price_collisions", lambda conn: ["probe: a collision"])
    report = build_module.build(connect(":memory:"), plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML,
                                sources=_sources(), minimum_models=2)
    assert "probe: a collision" in report.drift
