"""M17-W3 P3 (#37) -- every model carries its accessibility, from Epoch's `model_metadata.csv`.

Owner ruling 2026-09-25: an attribute, not a board. W4 sends it to the phone for filters ("an open
model I can host myself", "can I use it commercially"). Measured on the 2026-09 bundle: 1,089 rows
keyed by Epoch's own model name (`model_version`), 14 with no name, 152 with no accessibility.

The attribute joins through the SAME name resolution Epoch's scores use, so it lands on the model an
Epoch score lands on. Where two names of one model disagree, the model gets no value and the
disagreement is counted, never guessed.
"""

from __future__ import annotations

import sqlite3

import pytest

from app.workflows import access
from app.workflows.refresh import serving_summary
from app.workflows.schema import connect

HEADER = "model_version,model_group,date,display_name,organization,country,accessibility,training_compute_flop\n"


def _csv(*rows: tuple[str, str]) -> str:
    return HEADER + "".join(f"{name},g,2026-01-01,,Org,US,{value},\n" for name, value in rows)


def test_the_vocabulary_is_the_one_the_file_uses() -> None:
    assert frozenset({
        "API access", "Open weights (unrestricted)", "Open weights (restricted use)",
        "Open weights (non-commercial)", "Hosted access (no API)", "Unreleased", "Limited access"}) == access.ACCESSIBILITY


def test_rows_with_no_name_or_no_value_are_skipped_and_counted() -> None:
    rows, skipped = access.parse_metadata(_csv(("a", "API access"), ("", "API access"), ("b", ""),
                                               ("c", "Open weights (unrestricted)")))
    assert [(r.raw_name, r.accessibility) for r in rows] == [
        ("a", "API access"), ("c", "Open weights (unrestricted)")]
    assert skipped == 2


def test_a_value_outside_the_vocabulary_is_refused_and_counted() -> None:
    """A changed file, not a new kind of access: refused rather than served as a filter value."""
    rows, skipped = access.parse_metadata(_csv(("a", "Free for everyone"), ("b", "API access")))
    assert [r.raw_name for r in rows] == ["b"] and skipped == 1


def test_a_file_without_the_columns_is_a_source_error() -> None:
    from app.clients.protocols import SourceError

    with pytest.raises(SourceError, match="accessibility"):
        access.parse_metadata("model_version,date\nx,2026-01-01\n")


def _models(conn: sqlite3.Connection, *ids: str) -> None:
    conn.executemany("INSERT INTO models (id, display, vendor) VALUES (?, ?, 'v')", [(i, i) for i in ids])


def test_names_link_to_the_models_their_scores_link_to_and_a_disagreement_gives_no_value() -> None:
    conn = connect(":memory:")
    try:
        # `claude-opus-4-1-20250805` resolves by a curated rule to `claude-4.1-opus`; the two gpt-5
        # spellings derive `gpt5-2025-08-07`; an unregistered name links nowhere.
        _models(conn, "claude-4.1-opus", "gpt5-2025-08-07")
        rows, _ = access.parse_metadata(_csv(
            ("claude-opus-4-1-20250805", "API access"),
            ("gpt-5-2025-08-07", "API access"),
            ("gpt-5-2025-08-07_high", "Open weights (unrestricted)"),
            ("nobody-knows-me-9", "Unreleased")))
        access.store(conn, rows, source="epoch_access", source_url="u", observed_at="z")
        report = access.link(conn)
        assert access.served(conn) == {"claude-4.1-opus": "API access"}
        assert report.conflicting == ("gpt5-2025-08-07",)
        assert report.unlinked == 1
    finally:
        conn.close()


def test_no_existing_table_changes_shape() -> None:
    """Additive only: the new table is new; the columns every served table had stay as they were."""
    conn = connect(":memory:")
    try:
        cols = {t: [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
                for t in ("models", "scores", "pricing")}
        assert cols["models"] == ["id", "display", "vendor"]
        assert "accessibility" not in cols["scores"] + cols["pricing"]
        assert [r[1] for r in conn.execute("PRAGMA table_info(access)")] == [
            "raw_name", "model_id", "accessibility", "source", "source_url", "observed_at"]
    finally:
        conn.close()


def test_a_change_in_accessibility_moves_the_fingerprint() -> None:
    """Served content (D-164's reason): W4 sends it, so a change publishes."""
    conn = connect(":memory:")
    try:
        _models(conn, "claude-4.1-opus")
        rows, _ = access.parse_metadata(_csv(("claude-opus-4-1-20250805", "API access")))
        access.store(conn, rows, source="epoch_access", source_url="u", observed_at="z")
        access.link(conn)
        before = serving_summary(conn).digest
        conn.execute("UPDATE access SET accessibility = 'Open weights (unrestricted)'")
        assert serving_summary(conn).digest != before
    finally:
        conn.close()


def test_the_build_reads_the_bundles_metadata_and_a_missing_file_is_a_missing_line(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The file comes from the Epoch bundle the refresh fetches (D-158), through the bundle's own
    path guard; with no file the attribute is missing and said so, and the build goes on."""
    from app.workflows import build as build_mod

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "model_metadata.csv").write_text(_csv(("claude-opus-4-1-20250805", "API access")),
                                               encoding="utf-8")
    conn = connect(":memory:")
    try:
        _models(conn, "claude-4.1-opus")
        reports, missing = build_mod._ingest_access(conn, bundle, build_mod.RunContext())
        assert [r.stored for r in reports] == [1] and missing == []
        access.link(conn)
        assert access.served(conn) == {"claude-4.1-opus": "API access"}
        (bundle / "model_metadata.csv").unlink()
        reports, missing = build_mod._ingest_access(conn, bundle, build_mod.RunContext())
        assert reports == [] and missing and missing[0].startswith("epoch_access")
    finally:
        conn.close()


def test_an_artifact_from_before_the_table_still_fingerprints() -> None:
    """Found by P5's measurement on the served artifact: it predates `access`, and the fingerprint
    raised `no such table`. The refresh reads a live artifact that raises as UNREADABLE, so every
    night after the merge would have failed. An artifact without the table serves no values."""
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript("CREATE TABLE models (id TEXT PRIMARY KEY, display TEXT, vendor TEXT);")
        assert access.served(conn) == {}
    finally:
        conn.close()


@pytest.mark.parametrize("order", [("API access", "Open weights (unrestricted)"),
                                   ("Open weights (unrestricted)", "API access")])
def test_one_name_listed_twice_with_two_values_is_a_disagreement_not_the_last_row(order) -> None:  # type: ignore[no-untyped-def]
    """Wave review M3: a second row under the same name replaced the first, so file order chose the
    value. It is counted as a disagreement instead, and the model gets none."""
    conn = connect(":memory:")
    try:
        _models(conn, "claude-4.1-opus")
        rows, _ = access.parse_metadata(_csv(*(("claude-opus-4-1-20250805", v) for v in order)))
        access.store(conn, rows, source="epoch_access", source_url="u", observed_at="z")
        report = access.link(conn)
        assert access.served(conn) == {}
        assert report.conflicting == ("claude-4.1-opus",)
    finally:
        conn.close()


def test_the_build_reports_the_attribute_as_arrived(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Wave review M4: the refresh learns what arrived from the build's sources, so an attribute
    missing from them never gets a last-arrived record and `/health` cannot say when it came."""
    from app.workflows.build import build

    from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

    (tmp_path / access.FILE).write_text(_csv(("claude-opus-4-1-20250805", "API access")), encoding="utf-8")
    conn = connect(":memory:")
    try:
        report = build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
                       minimum_models=2, bundle_dir=tmp_path, bundles=(), boards=(),
                       access_files=(access.FILE,))
        assert access.SOURCE in report.sources_json()["arrived"]  # type: ignore[operator]
    finally:
        conn.close()


def _build_with(conn: sqlite3.Connection, bundle, **kw):  # type: ignore[no-untyped-def]
    from app.workflows.build import build

    from .test_build import PLANS_YAML, ROSTERS_YAML, _sources

    return build(conn, plans_yaml=PLANS_YAML, rosters_yaml=ROSTERS_YAML, sources=_sources(),
                 minimum_models=2, bundle_dir=bundle, bundles=(), boards=(), slices=(),
                 access_files=(access.FILE,), **kw)


def test_the_build_links_what_it_stores(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester T1: the build's own `access.link` after reconcile is what serves a value; without it
    every row stays unlinked and the phone gets none."""
    (tmp_path / access.FILE).write_text(_csv(("claude-opus-4-5-20251101", "API access")), encoding="utf-8")
    conn = connect(":memory:")
    try:
        report = _build_with(conn, tmp_path)
        assert access.served(conn) == {"claude-4.5-opus": "API access"}
        assert report.access["linked"] == 1
    finally:
        conn.close()


def test_a_night_the_file_is_missing_serves_the_last_good_values_through_the_build(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester T2: D-156 through `build()`, not only through `Carry.restore`."""
    import datetime as dt

    now = dt.datetime(2026, 9, 23, 22, 0, tzinfo=dt.UTC)
    live = tmp_path / "live.db"
    old = connect(str(live))
    _build_with(old, tmp_path / "none")
    access.store(old, [access.AccessRow("claude-opus-4-5-20251101", "API access")], source=access.SOURCE,
                 source_url="u", observed_at=(now - dt.timedelta(days=2)).isoformat())
    old.close()
    empty = tmp_path / "bundle"
    empty.mkdir()
    conn = connect(str(tmp_path / "cand.db"))
    try:
        report = _build_with(conn, empty, carry_from=live, last_ok={}, now=now)
        assert access.SOURCE in report.carried
        assert access.served(conn) == {"claude-4.5-opus": "API access"}
    finally:
        conn.close()


def test_a_metadata_file_that_resolves_outside_the_bundle_is_refused(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester T3: the file is read through the bundle's path guard, which a planted symlink meets."""
    from app.workflows import build as build_mod

    outside = tmp_path / "outside.csv"
    outside.write_text(_csv(("claude-opus-4-5-20251101", "API access")), encoding="utf-8")
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / access.FILE).symlink_to(outside)
    conn = connect(":memory:")
    try:
        reports, missing = build_mod._ingest_access(conn, bundle, build_mod.RunContext())
        assert reports == [] and missing and "outside the bundle" in missing[0]
        assert conn.execute("SELECT COUNT(*) FROM access").fetchone()[0] == 0
    finally:
        conn.close()


def test_a_metadata_file_with_no_valid_row_is_a_missing_line(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester B2: a file that parses to nothing is a failed source, never an empty attribute."""
    from app.workflows import build as build_mod

    (tmp_path / access.FILE).write_text(_csv(("x", "Free for all"), ("", "API access")), encoding="utf-8")
    conn = connect(":memory:")
    try:
        reports, missing = build_mod._ingest_access(conn, tmp_path, build_mod.RunContext())
        assert reports == [] and missing == [f"{access.SOURCE}: parsed 0 rows from {access.FILE}"]
    finally:
        conn.close()


def test_a_bundle_without_the_metadata_file_says_so_in_the_build_report(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester T5: a bundle that arrived without `model_metadata.csv` is an operator line and a drift
    line (`/health`'s `refresh_drift`), not only a value `_ingest_access` returned."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    conn = connect(":memory:")
    try:
        report = _build_with(conn, bundle)
        assert any(line.startswith(f"{access.SOURCE} is unavailable") for line in report.required_operator_actions)
        assert any(entry.startswith(f"{access.SOURCE}:") for entry in report.drift)
    finally:
        conn.close()


def test_the_build_report_names_the_models_whose_names_disagree(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Tester T5: the research record reads the models left without a value from the build report."""
    (tmp_path / access.FILE).write_text(_csv(("claude-opus-4-5-20251101", "API access"),
                                             ("claude-opus-4-5-20251101", "Open weights (unrestricted)")),
                                        encoding="utf-8")
    conn = connect(":memory:")
    try:
        report = _build_with(conn, tmp_path)
        assert report.access["conflicting"] == ["claude-4.5-opus"]
        assert access.served(conn) == {}
    finally:
        conn.close()
