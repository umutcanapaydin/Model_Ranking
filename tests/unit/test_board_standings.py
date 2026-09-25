"""M17-W4 P1 (#50) -- every board's standings on one route, as positions (D-160, D-167).

The phone combines boards on the device (D-160). It downloads every board every day, whatever the
question, so the request says nothing about the question (D-167 clause 1). It receives POSITIONS,
never scores, so no later change on the phone can average two scales (D-105, D-167 clause 2).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.workflows import access
from app.workflows.schema import connect

from .test_api_v1 import _seeded_db

ENVELOPE_KEYS = {"api_version", "attributions", "boards", "models"}
PAYLOAD_KEYS = ENVELOPE_KEYS - {"api_version"}  # the route adds the version (review M5)
BOARD_KEYS = {"id", "benchmark", "metric", "ranking_effort", "evidence_date", "observed_at",
              "attribution", "standings"}
STANDING_KEYS = {"model", "position", "effort"}
MODEL_KEYS = {"id", "display", "vendor", "blended_per_m", "accessibility"}


def _conn() -> sqlite3.Connection:
    conn = connect(":memory:")
    for mid, name, in_m, out_m in (("a", "A", 1.0, 2.0), ("b", "B", 3.0, 4.0), ("c", "C", 5.0, 6.0),
                                   ("d", "D", 7.0, 8.0), ("unpriced", "U", None, None)):
        conn.execute("INSERT INTO models (id, display, vendor) VALUES (?, ?, 'V')", (mid, name))
        if in_m is not None:
            conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES (?, ?, ?)", (mid, in_m, out_m))
    return conn


def _score(conn: sqlite3.Connection, source: str, benchmark: str, metric: str, raw: str,
           model: str | None, score: float, *, effort: str = "unspecified", run_date: str | None = None) -> None:
    conn.execute(
        "INSERT INTO scores (raw_name, model_id, benchmark, metric, score, harness, effort, run_date, source, "
        "source_url, observed_at) VALUES (?, ?, ?, ?, ?, 'h', ?, ?, ?, 'u', '2026-09-25T00:00:00+00:00')",
        (raw, model, benchmark, metric, score, effort, run_date, source))


def _chess(conn: sqlite3.Connection) -> None:
    """a 70 (at max; 40 unspecified), b 55, c 55, d 10, an unpriced model 90, an unlinked name 99."""
    for raw, model, score, effort in (("a_max", "a", 70.0, "max"), ("a", "a", 40.0, "unspecified"),
                                      ("b", "b", 55.0, "unspecified"), ("c", "c", 55.0, "unspecified"),
                                      ("d", "d", 10.0, "unspecified"), ("u", "unpriced", 90.0, "unspecified"),
                                      ("nobody", None, 99.0, "unspecified")):
        _score(conn, "epoch_chess", "Chess puzzles", "% correct", raw, model, score, effort=effort,
               run_date="2026-09-18")


def _payload(conn: sqlite3.Connection) -> dict:  # type: ignore[type-arg]
    from app.workflows.standings import board_standings

    return board_standings(conn)


def _board(payload: dict, board_id: str) -> dict:  # type: ignore[type-arg]
    return next(b for b in payload["boards"] if b["id"] == board_id)


def test_positions_follow_each_models_best_row_and_ties_share_one() -> None:
    conn = _conn()
    _chess(conn)
    board = _board(_payload(conn), "epoch_chess")
    assert [(s["model"], s["position"]) for s in board["standings"]] == [("a", 1), ("b", 2), ("c", 2), ("d", 4)]


def test_each_standing_carries_the_effort_of_its_own_evidence() -> None:
    """D-112: a board with no effort policy ranks on the best evidence each model has, and says which
    effort that evidence was run at, so the phone can disclose an unequal comparison."""
    conn = _conn()
    _chess(conn)
    board = _board(_payload(conn), "epoch_chess")
    assert board["ranking_effort"] is None
    assert {s["model"]: s["effort"] for s in board["standings"]} == {
        "a": "max", "b": "unspecified", "c": "unspecified", "d": "unspecified"}


def test_a_board_a_surface_ranks_at_one_effort_stands_at_that_effort() -> None:
    """Code review B1, D-112: `agentic-coding` ranks DeepSWE at `high`, so the board the phone gets
    is the board that surface ranks -- not each model's best row at any effort."""
    conn = _conn()
    for raw, model, score, effort in (("a_max", "a", 70.0, "max"), ("a_high", "a", 50.0, "high"),
                                      ("b_high", "b", 60.0, "high"), ("c_low", "c", 90.0, "low")):
        _score(conn, "epoch_deepswe_external", "DeepSWE", "% resolved", raw, model, score, effort=effort)
    board = _board(_payload(conn), "epoch_deepswe_external")
    assert board["ranking_effort"] == "high"
    assert [(s["model"], s["position"], s["effort"]) for s in board["standings"]] == [
        ("b", 1, "high"), ("a", 2, "high")]


def test_a_source_holding_two_boards_is_refused() -> None:
    """Code review M1: the refusal existed and nothing pinned it."""
    conn = _conn()
    _chess(conn)
    _score(conn, "epoch_chess", "Chess endgames", "% correct", "a", "a", 1.0)
    with pytest.raises(ValueError, match="more than one board"):
        _payload(conn)


def test_only_rankable_models_stand_and_a_board_with_none_is_absent() -> None:
    """Reconciled AND priced, as on every surface (REQ-EVI-002): an unpriced model and an unlinked
    name never stand, and a board none of whose models can be ranked is not published."""
    conn = _conn()
    _chess(conn)
    _score(conn, "epoch_mystery", "Mystery game puzzles", "% correct", "u", "unpriced", 50.0)
    payload = _payload(conn)
    assert {b["id"] for b in payload["boards"]} == {"epoch_chess"}
    assert "unpriced" not in {s["model"] for s in _board(payload, "epoch_chess")["standings"]}
    assert "unpriced" not in {m["id"] for m in payload["models"]}


def test_the_payload_carries_no_score_at_all() -> None:
    """D-167 clause 2: the phone gets positions, so it cannot mix scales whatever it later does."""
    conn = _conn()
    _chess(conn)
    payload = _payload(conn)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                assert "score" not in key.lower(), key
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    served = {s["position"] for b in payload["boards"] for s in b["standings"]}
    assert all(isinstance(p, int) for p in served)
    assert not {70.0, 55.0, 10.0} & {v for m in payload["models"] for v in m.values()}


def test_the_key_sets_are_frozen() -> None:
    """The same allowlist discipline as `test_api_v1.py`: a new key is decided, never allowed."""
    conn = _conn()
    _chess(conn)
    payload = _payload(conn)
    assert set(payload) == PAYLOAD_KEYS
    for board in payload["boards"]:
        assert set(board) == BOARD_KEYS
        for standing in board["standings"]:
            assert set(standing) == STANDING_KEYS
    for model in payload["models"]:
        assert set(model) == MODEL_KEYS


def test_each_board_is_dated_and_attributed() -> None:
    from app.clients.epoch import EPOCH_ATTRIBUTION
    from app.workflows.rank import PRICING_ATTRIBUTION

    conn = _conn()
    _chess(conn)
    payload = _payload(conn)
    board = _board(payload, "epoch_chess")
    assert (board["benchmark"], board["metric"]) == ("Chess puzzles", "% correct")
    assert board["evidence_date"] == "2026-09-18"
    assert board["observed_at"] == "2026-09-25"
    assert board["attribution"] == EPOCH_ATTRIBUTION
    assert set(payload["attributions"]) == {EPOCH_ATTRIBUTION, PRICING_ATTRIBUTION}


def test_an_unattributed_source_fails_rather_than_publishing() -> None:
    conn = _conn()
    _score(conn, "nobody_reviewed_this", "Mystery", "% correct", "a", "a", 1.0)
    with pytest.raises(ValueError, match="unattributed"):
        _payload(conn)


def test_a_metric_whose_direction_is_not_declared_fails() -> None:
    """Positions need to know which way is better. Every metric served today is higher-is-better;
    a new one is refused until somebody says which way it runs."""
    conn = _conn()
    _score(conn, "epoch_chess", "Chess puzzles", "seconds to solve", "a", "a", 1.0)
    with pytest.raises(ValueError, match="direction"):
        _payload(conn)


def test_models_carry_the_served_blend_and_their_accessibility() -> None:
    conn = _conn()
    _chess(conn)
    conn.execute("INSERT INTO access (raw_name, model_id, accessibility, source, source_url, observed_at) "
                 "VALUES ('a', 'a', 'API access', ?, 'u', 'z')", (access.SOURCE,))
    models = {m["id"]: m for m in _payload(conn)["models"]}
    assert models["a"] == {"id": "a", "display": "A", "vendor": "V", "blended_per_m": 1.25,
                           "accessibility": "API access"}
    assert models["b"]["accessibility"] is None
    assert set(models) == {"a", "b", "c", "d"}


def test_an_artifact_from_before_the_access_table_still_publishes() -> None:
    conn = _conn()
    _chess(conn)
    conn.execute("DROP TABLE access")
    assert {m["accessibility"] for m in _payload(conn)["models"]} == {None}


# --- the route -----------------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    return TestClient(adapter.app)


def test_the_route_publishes_the_standings(client: TestClient) -> None:
    response = client.get("/v1/boards")
    assert response.status_code == 200
    body = response.json()
    from app.adapter.main import API_VERSION

    assert set(body) == ENVELOPE_KEYS and body["api_version"] == API_VERSION
    assert {b["id"] for b in body["boards"]} >= {"swebench"}


def test_a_query_string_changes_nothing(client: TestClient) -> None:
    """D-167 clause 1: nothing the phone could send shapes the answer, so nothing it sends means
    anything. The same bytes come back whatever is appended."""
    plain = client.get("/v1/boards")
    assert plain.status_code == 200
    asked = client.get("/v1/boards?task=coding&boards=epoch_chess&q=help+me+write")
    assert (asked.status_code, asked.content) == (200, plain.content)


def test_a_missing_artifact_is_unavailable_not_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "absent.db"))
    from app.adapter import main as adapter

    response = TestClient(adapter.app).get("/v1/boards")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "evidence_unavailable"


def test_an_artifact_that_would_publish_too_many_standings_refuses_to_boot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An EGRESS bound checked at boot, like `MAX_PUBLISHED_RANKING_ROWS`: nothing is truncated."""
    from app.adapter import main as adapter

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setattr(adapter, "APP_BUILD", "deadbee")
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    monkeypatch.setattr(adapter, "MAX_PUBLISHED_STANDINGS_ROWS", 1)
    with pytest.raises(adapter.ConfigError, match="standings"):
        adapter.validate_startup_config(env="production")
    monkeypatch.setattr(adapter, "MAX_PUBLISHED_STANDINGS_ROWS", 25000)
    assert adapter.validate_startup_config(env="production") == ()


@pytest.mark.parametrize(("source", "metric", "match"), [
    ("nobody_reviewed_this", "% correct", "unattributed"),
    ("epoch_chess", "seconds to solve", "direction"),
])
def test_a_payload_the_route_would_refuse_refuses_the_boot_instead(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str, metric: str, match: str
) -> None:
    """Code review M1: an artifact every `/v1/boards` request would answer with a 500 must not boot
    healthy. The refusal happens where the other artifact problems are found."""
    from app.adapter import main as adapter

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO scores (raw_name, model_id, benchmark, metric, score, harness, effort, source, "
            "source_url, observed_at) SELECT 'x', id, 'B', ?, 1, 'h', 'unspecified', ?, 'u', 'z' "
            "FROM models LIMIT 1", (metric, source))
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setattr(adapter, "APP_BUILD", "deadbee")
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    with pytest.raises(adapter.ConfigError, match=match):
        adapter.validate_startup_config(env="production")


def test_equal_best_scores_disclose_the_newest_runs_effort() -> None:
    """Second review M8: the tie-break decides which effort a standing discloses. Among equal best
    scores the newest run wins, as `rank.category_ranking` breaks the same tie."""
    conn = _conn()
    _score(conn, "epoch_chess", "Chess puzzles", "% correct", "a_low", "a", 60.0, effort="low",
           run_date="2026-08-01")
    _score(conn, "epoch_chess", "Chess puzzles", "% correct", "a_max", "a", 60.0, effort="max",
           run_date="2026-09-01")
    board = _board(_payload(conn), "epoch_chess")
    assert [(s["model"], s["effort"]) for s in board["standings"]] == [("a", "max")]


def test_every_board_of_a_benchmark_a_surface_ranks_at_one_effort_stands_at_it() -> None:
    """Second review R5: a surface ranks its BENCHMARK across every source (D-112), so the policy
    follows the benchmark, not only the surface's primary source."""
    conn = _conn()
    for source in ("epoch_deepswe_external", "swebench"):
        _score(conn, source, "DeepSWE", "% resolved", f"{source}_a_max", "a", 70.0, effort="max")
        _score(conn, source, "DeepSWE", "% resolved", f"{source}_a_high", "a", 50.0, effort="high")
    payload = _payload(conn)
    for source in ("epoch_deepswe_external", "swebench"):
        board = _board(payload, source)
        assert board["ranking_effort"] == "high"
        assert [s["effort"] for s in board["standings"]] == ["high"]


def test_two_surfaces_ranking_one_benchmark_at_different_efforts_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Second review R5: two policies for one benchmark cannot both hold; the later must not
    silently overwrite the earlier."""
    import dataclasses

    from app.workflows.categories import CATEGORIES

    spec = next(s for s in CATEGORIES.values() if s.ranking_effort)
    monkeypatch.setitem(CATEGORIES, "probe", dataclasses.replace(spec, id="probe", ranking_effort="max"))
    conn = _conn()
    _chess(conn)
    with pytest.raises(ValueError, match="two efforts"):
        _payload(conn)


def test_a_payload_refused_after_boot_is_unavailable_and_logged_with_its_reason(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Second review M7: a nightly refresh can publish, under a running process, an artifact the
    boot check would refuse. The reader gets the closed 503; the operator gets the reason."""
    from app.adapter import main as adapter

    def refuse(_conn: object) -> dict:  # type: ignore[type-arg]
        raise ValueError("epoch_chess: metric '% faster' has no declared direction")

    monkeypatch.setattr(adapter, "board_standings", refuse)
    with caplog.at_level("WARNING"):
        response = client.get("/v1/boards")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "evidence_unavailable"
    assert "% faster" not in response.text
    assert "'% faster' has no declared direction" in caplog.text
