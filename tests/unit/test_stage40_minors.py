"""M7 Stage-4.0 MINOR findings, each with the citing test it was reported for missing.

The Stage-4.0 pass returned PASS with zero blocking findings, so none of this gates the deploy.
They are fixed anyway because D-122 relaxes review DEPTH, not the rule that a root-cause defect is
fixed wherever it is found — and because two of them are controls that were reporting success while
inspecting almost nothing, which is the defect this project has spent five milestones on.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapter import main as adapter
from app.workflows.schema import connect


def _servable(path: Path, ranked: int = 1) -> None:
    """An artifact the startup probe accepts, with a chosen number of ranked models."""
    conn = connect(str(path))
    try:
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('m', 1.0, 2.0)")
        for i in range(ranked):
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
                " harness, source_url, observed_at) VALUES (?, ?, 's', 'b', 'm', 1.0, 'none',"
                " 'fixture://x', 't')",
                (f"m{i}", f"M{i}"),
            )
        conn.commit()
    finally:
        conn.close()


# --- MINOR-1: the ceiling now measures ranked ROWS, which is what costs memory -----------------


def test_an_artifact_with_too_many_ranked_models_refuses_to_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The replacement for the deleted file-size ceiling, pointed at the right quantity.

    Stage 4.0 measured both: a file inflated to 121 MB carrying the same 73 models cost ZERO extra
    memory, while a 6 MB artifact with 10,000 ranked models reached 58% of a 256 MiB VM and 50,000
    was OOM-killed. The old ceiling would have refused the harmless artifact and admitted the
    dangerous one, which is why W3 was right to delete it and wrong to leave nothing behind.
    """
    db = tmp_path / "big.db"
    _servable(db, ranked=12)
    monkeypatch.setattr(adapter, "MAX_RANKED_ROWS", 5)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setattr(adapter, "APP_BUILD", "deadbee")
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)

    with pytest.raises(adapter.ConfigError, match="ranks 12 models"):
        adapter.validate_startup_config(env="production")

    # ...and an artifact inside the bound boots, so this is a ceiling and not a refusal.
    monkeypatch.setattr(adapter, "MAX_RANKED_ROWS", 5000)
    assert adapter.validate_startup_config(env="production") == ()


def test_the_ranked_count_is_distinct_reconciled_models_not_score_rows(tmp_path: Path) -> None:
    """What is counted decides whether the bound means anything.

    `category_ranking` joins over reconciled models; unreconciled rows never enter it and cost
    nothing. Counting raw score rows would refuse an artifact for evidence it cannot even use.
    """
    db = tmp_path / "mixed.db"
    _servable(db, ranked=3)
    conn = connect(str(db))
    try:
        for i in range(20):
            conn.execute(
                "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
                " harness, source_url, observed_at) VALUES (NULL, ?, 's', 'b', 'm', 1.0, 'none',"
                " 'fixture://x', 't')",
                (f"unreconciled-{i}",),
            )
        # ...and a second row for a model already counted, which must not count twice.
        conn.execute(
            "INSERT INTO scores (model_id, raw_name, source, benchmark, metric, score,"
            " harness, source_url, observed_at) VALUES ('m0', 'M0', 's2', 'b', 'm', 2.0, 'none',"
            " 'fixture://x', 't')"
        )
        conn.commit()
    finally:
        conn.close()

    assert adapter._ranked_row_count(db) == 3


# --- MINOR-2: the 500 body must not carry the exception's text --------------------------------


def test_an_unhandled_error_does_not_leak_its_exception_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The one mutant of eight that survived Stage 4.0: replacing the generic body with `str(exc)`.

    An exception message is the one place a secret or a filesystem path reaches a response without
    anyone deciding it should, and the control was correct — it simply had no test that would
    notice if it stopped being.
    """
    db = tmp_path / "ok.db"
    _servable(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("APP_ENV", "test")

    secret = "sk-live-DO-NOT-LEAK-8f3c1e/var/secrets/token"

    def _boom(*_a: object, **_k: object) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(adapter, "_answer_for", _boom)

    client = TestClient(adapter.app, raise_server_exceptions=False)
    response = client.get("/v1/recommendations", params={"task": "coding"})

    assert response.status_code == 500
    body = response.text
    assert secret not in body, "the exception's text reached the response body"
    assert "sk-live" not in body
    assert "/var/secrets" not in body
    assert response.headers.get("x-content-type-options") == "nosniff"


# --- MINOR-6: an unusable concurrency value must refuse at import, not hang at request ---------


@pytest.mark.parametrize("value", ["0", "-1", "abc", ""])
def test_an_unusable_concurrency_value_is_refused(value: str) -> None:
    """`=0` bound the port and then answered nothing, including /health, for 120 s.

    A liveness probe that never answers reads as a slow start, so a deploy would be retried rather
    than diagnosed. Checked at import because that is the only place it can fail loudly.
    """
    with pytest.raises(adapter.ConfigError, match="MODEL_RANKING_MAX_CONCURRENCY"):
        adapter._positive_env("MODEL_RANKING_MAX_CONCURRENCY", value)


def test_a_usable_concurrency_value_is_accepted() -> None:
    """The guard must permit what it exists to make possible."""
    assert adapter._positive_env("MODEL_RANKING_MAX_CONCURRENCY", "8") == 8


# --- MINOR-7: third-party text reaching an unauthenticated caller is bounded -------------------


def test_a_hostile_harness_string_is_bounded_before_it_reaches_a_caller() -> None:
    """`harness` is copied verbatim from a leaderboard row; nothing upstream bounds it.

    `model` and `vendor` come from the canonical registry, so a source can only influence WHICH
    registered name is chosen. This one is different, and the iOS client is the next piece of work.
    """
    hostile = "A" * 50_000
    bounded = adapter._bounded_pick({"harness": hostile, "model": "gpt-5", "score": 1.0})

    assert len(bounded["harness"]) <= adapter.MAX_UNTRUSTED_TEXT + 1
    assert bounded["harness"].endswith("…")
    assert bounded["model"] == "gpt-5", "a registry-derived field must not be truncated"
    assert bounded["score"] == 1.0, "a non-string field must pass through untouched"


def test_a_normal_harness_name_is_not_truncated() -> None:
    """The bound must be far above every real value, or it becomes a data-loss bug."""
    real = "live-SWE-agent + Claude 4.5 Opus"
    assert adapter._bounded_pick({"harness": real})["harness"] == real
