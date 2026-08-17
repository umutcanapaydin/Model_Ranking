"""M7-W2 — the four guards my own mutants walked straight through (REQ-API-008).

Each test here exists because a mutant stayed GREEN across 475 passing tests. They are grouped in
one file because they share a single question: **when the engine cannot answer, does it say the
RIGHT thing about why?** Getting that wrong does not crash anything — it sends an operator to fix
the wrong problem, or tells a user their budget was too tight when the database was never built.

The one worth reading twice is `test_the_no_evidence_branch_asks_whether_evidence_reached_the_ranking`:
it pins the security seat's BLOCKING-5, a fix I shipped and never tested.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.adapter import main as adapter
from app.workflows.categories import get_category
from app.workflows.rank import UnbuiltEvidenceError, require_price_medians
from app.workflows.recommend import recommend
from app.workflows.schema import connect


def _built(path: Path) -> None:
    """A minimal artifact the startup probe accepts."""
    conn = connect(str(path))
    try:
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('m', 1.0, 2.0)")
        conn.commit()
    finally:
        conn.close()


# --- M3: a corrupt database must not be reported as merely unbuilt -----------------------------


def test_a_corrupt_database_is_not_reported_as_unbuilt(tmp_path: Path) -> None:
    """A file that is not a database raises DatabaseError and must reach the caller as one."""
    junk = tmp_path / "junk.db"
    junk.write_bytes(b"this is definitely not a sqlite database" * 64)
    conn = sqlite3.connect(junk)
    try:
        with pytest.raises(sqlite3.DatabaseError) as exc:
            require_price_medians(conn)
        assert not isinstance(exc.value, UnbuiltEvidenceError), (
            "a corrupt file was reported as an unbuilt artifact; the operator would be told to "
            "rebuild when the real fault is that this is not a database"
        )
    finally:
        conn.close()


def test_an_operational_error_that_is_not_a_missing_table_is_re_raised(tmp_path: Path) -> None:
    """The NARROWING itself, which the test above cannot reach.

    A junk file raises `DatabaseError`, which never enters the `except sqlite3.OperationalError`
    clause at all — so widening that clause back to every OperationalError stayed GREEN across the
    whole suite. A LOCKED database is the case that actually goes through it: it is operational,
    it is not a missing table, and reporting it as "rebuild the artifact" would send an operator
    to rebuild a database whose only problem is that another process is holding it.
    """
    db = tmp_path / "locked.db"
    _built(db)

    holder = sqlite3.connect(db, isolation_level=None)
    reader = sqlite3.connect(f"file:{db}", uri=True, timeout=0.1)
    try:
        holder.execute("BEGIN EXCLUSIVE")
        with pytest.raises(sqlite3.OperationalError) as exc:
            require_price_medians(reader)
        assert "locked" in str(exc.value).lower()
        assert not isinstance(exc.value, UnbuiltEvidenceError), (
            "a locked database was reported as unbuilt; the remedy named would be the wrong one"
        )
    finally:
        holder.rollback()
        holder.close()
        reader.close()


# --- M4: the error type is part of the contract ------------------------------------------------


def test_unbuilt_evidence_is_not_a_value_error() -> None:
    """`recommend()` raises ValueError for an unknown budget — a CALLER mistake.

    If UnbuiltEvidenceError subclassed ValueError, every caller catching a usage error would
    silently absorb an unfinished artifact, and the CLI's two branches would collapse into one.
    The separation is deliberate and was previously undefended: the mutant that merged them stayed
    green across the whole suite.
    """
    assert issubclass(UnbuiltEvidenceError, RuntimeError)
    assert not issubclass(UnbuiltEvidenceError, ValueError)


# --- M9: the startup probe's fourth check ------------------------------------------------------


def test_the_startup_probe_refuses_an_artifact_with_no_price_medians(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail-closed at BOOT, which is the check that actually protects a deploy.

    A schema-valid database with an empty `px_median` passes every existence check, answers
    `/health` 200 with a correct build stamp, and returns no picks for every real query — the exact
    shape W-023 shipped. Stage 4.3 verifies deploys with `/health`, so this must stop the process
    from starting rather than surface per-request.
    """
    unbuilt = tmp_path / "unbuilt.db"
    connect(str(unbuilt)).close()  # schema present, px_median empty

    problem = adapter._database_unusable(unbuilt)

    assert problem is not None, "a database that answers nothing passed the startup probe"
    assert "price medians" in problem
    assert "app.workflows.build" in problem, "the probe must name the remedy, not just refuse"

    built = tmp_path / "built.db"
    _built(built)
    assert adapter._database_unusable(built) is None, "the probe rejects a servable artifact"


def test_the_probe_reports_a_schema_fault_before_a_content_fault(tmp_path: Path) -> None:
    """Ordering is a decision: a pre-M5 database is a MIGRATION problem, not a build problem.

    Both faults are present in a pre-M5 artifact — no `effort` column AND no medians — and telling
    the operator to rebuild would send them past the migration they actually need.
    """
    pre_m5 = tmp_path / "prem5.db"
    conn = sqlite3.connect(pre_m5)
    try:
        conn.executescript(
            "CREATE TABLE scores (model_id TEXT, source TEXT);"
            "CREATE TABLE pricing (model_id TEXT, source TEXT);"
            "CREATE TABLE px_median (model_id TEXT, in_m REAL, out_m REAL);"
        )
        conn.commit()
    finally:
        conn.close()

    problem = adapter._database_unusable(pre_m5)

    assert problem is not None
    assert "effort" in problem, f"the schema fault must be reported first; got: {problem}"


# --- M11: the security seat's BLOCKING-5, which I fixed and never tested ------------------------


def test_the_no_evidence_branch_asks_whether_evidence_reached_the_ranking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BLOCKING-5: `health["sources"]` is non-empty as soon as ONE row exists under a benchmark.

    The security seat reached this state deliberately: a single score row whose model never
    reconciles to the registry never enters `category_ranking`, but it does make the source look
    present — so the surface fell back to *"No model fits the requested budget"* with nothing
    ranked at all. `minimum_rows` counts rows STORED, not rows usable, and the build's
    reconciliation floor is global rather than per-benchmark, so nothing upstream rules it out.

    This test is the reason the predicate calls `category_ranking` instead.
    """
    db = tmp_path / "unreconciled.db"
    conn = connect(str(db))
    try:
        spec = get_category("assistant")
        # One row under the assistant benchmark, from a model the registry never canonicalises.
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
            " harness, source_url, observed_at) VALUES (NULL, 'a-model-nobody-registered',"
            " ?, ?, ?, 1500.0, 'none', 'fixture://x', 't')",
            (spec.primary_source, spec.primary_benchmark, spec.metric),
        )
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('m', 1.0, 2.0)")
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")
    from fastapi.testclient import TestClient

    response = TestClient(adapter.app).get(
        "/v1/recommendations", params={"task": "assistant", "budget": "unlimited"}
    )

    assert response.status_code == 200
    (answer,) = response.json()["answers"]
    assert answer["picks"] == []
    reason = str(answer["unavailable_reason"]).lower()
    assert "no evidence" in reason, (
        "a surface where nothing reached the ranking blamed the BUDGET; the predicate is asking "
        f"whether rows landed in a table again. Got: {reason}"
    )


def test_a_surface_with_real_evidence_and_an_impossible_budget_still_blames_the_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other direction, so the fix cannot collapse into one blanket sentence again.

    This is the pairing the D-121 amendment once CLAIMED existed and did not — a record asserting a
    control that was not there. It exists now.

    The fixture is one model that DOES reconcile and DOES rank, priced far above the `low` cap, so
    the surface has real evidence and genuinely nothing affordable. That is the only shape that can
    tell the two sentences apart.
    """
    db = tmp_path / "pricey.db"
    conn = connect(str(db))
    try:
        spec = get_category("assistant")
        conn.execute("INSERT INTO models (id, display, vendor) VALUES ('pricey', 'Pricey', 'V')")
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
            " harness, source_url, observed_at) VALUES ('pricey', 'Pricey', ?, ?, ?,"
            " 1600.0, 'none', 'fixture://x', 't')",
            (spec.primary_source, spec.primary_benchmark, spec.metric),
        )
        # Far above the `low` cap of $2/1M blended, so the budget is what excludes it.
        conn.execute(
            "INSERT INTO px_median (model_id, in_m, out_m) VALUES ('pricey', 500.0, 900.0)"
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")
    from fastapi.testclient import TestClient

    response = TestClient(adapter.app).get(
        "/v1/recommendations", params={"task": "assistant", "budget": "low"}
    )

    assert response.status_code == 200
    (answer,) = response.json()["answers"]
    assert answer["picks"] == [], "fixture assumption: the low budget must exclude this model"
    reason = str(answer["unavailable_reason"]).lower()
    assert "budget" in reason
    assert "no evidence" not in reason, (
        "a surface WITH evidence was told it has none; the two causes have collapsed again"
    )


def test_the_cli_and_the_api_agree_that_an_unbuilt_artifact_is_not_a_budget_result(
    tmp_path: Path,
) -> None:
    """One artifact, two boundaries, one cause. Divergence here is how a wrong diagnosis spreads."""
    from app.workflows.recommend import main as cli_main

    unbuilt = tmp_path / "unbuilt.db"
    connect(str(unbuilt)).close()

    conn = sqlite3.connect(f"file:{unbuilt}?mode=ro", uri=True)
    try:
        with pytest.raises(UnbuiltEvidenceError):
            recommend(conn, budget="unlimited", task="coding")
    finally:
        conn.close()

    assert cli_main(["--db", str(unbuilt), "--budget", "unlimited", "--task", "coding"]) == 2
