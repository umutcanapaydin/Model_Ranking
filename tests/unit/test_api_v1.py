"""M6-W1 acceptance tests for the /v1 read-only HTTP surface.

Written BEFORE the implementation (E.4: new module + locked contract → acceptance tests first).
Every test names the criterion from `docs/plans/m6-plan.md` §2 that it cites.

The one this milestone exists for is `test_coding_returns_both_surfaces_and_nothing_ranks_them`.
Ruling A — the owner's answer to M5's carried question — says the product presents BOTH coding
answers and neither leads. Trap 2 of the signed plan is that "both" silently becomes "both, but one
first": an array order read as precedence, a `primary` flag, a top-level winner. Intent does not
prevent that. This test does.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.clients.fakes import FakeRawSource
from app.workflows.ingest import RunContext, ingest_deepswe, ingest_litellm, ingest_swebench
from app.workflows.registry import reconcile
from app.workflows.schema import connect

# Fields that would re-introduce a ranking the owner did not make (Trap 2). None may appear
# anywhere in the envelope or in an answer.
PRECEDENCE_FIELDS = {
    "primary",
    "default",
    "recommended",
    "leads",
    "leading",
    "winner",
    "rank",
    "priority",
    "preferred",
}

PRICING = json.dumps(
    {
        "claude-4-5-opus": {
            "mode": "chat",
            "input_cost_per_token": 5e-06,
            "output_cost_per_token": 2.5e-05,
        },
        "gpt-5": {"mode": "chat", "input_cost_per_token": 1.25e-06, "output_cost_per_token": 1e-05},
        "deepseek-v3.2": {
            "mode": "chat",
            "input_cost_per_token": 2.8e-07,
            "output_cost_per_token": 4.1e-07,
        },
    }
)

SWEBENCH = json.dumps(
    {
        "leaderboards": [
            {
                "name": "Verified",
                "results": [
                    {"name": "Claude 4.5 Opus", "resolved": 74.5, "date": "2026-02-26"},
                    {"name": "GPT-5", "resolved": 71.0, "date": "2026-02-26"},
                    {"name": "DeepSeek V3.2", "resolved": 66.0, "date": "2026-02-26"},
                ],
            }
        ]
    }
)

# The agentic-coding board publishes RELEASE dates, never evaluation dates — that is the whole
# reason it is a separate surface (D-105) and the weakness Ruling A requires the payload to state.
DEEPSWE = """Model version,Pass@1,Harness,Reasoning effort,Release date
claude-4-5-opus_high,0.68,mini-swe-agent,high,2026-07-01
gpt-5_high,0.61,mini-swe-agent,high,2026-07-09
deepseek-v3.2_high,0.52,mini-swe-agent,high,2026-06-20
"""


def _seeded_db(path: Path) -> None:
    """Both coding surfaces in one database, from the canonical fakes (V3C-44)."""
    conn = connect(str(path))
    run = RunContext(observed_at="2026-08-16T00:00:00+00:00")
    ingest_litellm(conn, FakeRawSource("litellm", PRICING), run)
    ingest_swebench(conn, FakeRawSource("swebench", SWEBENCH), run)
    ingest_deepswe(
        conn,
        FakeRawSource("epoch_deepswe_external", DEEPSWE, url="https://epoch.ai/#deepswe", last_verified="2026-08-15"),
        run,
    )
    reconcile(conn)
    conn.commit()
    conn.close()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    return TestClient(adapter.app)


def _walk_keys(node: object) -> set[str]:
    """Every key name anywhere in the payload, at any depth."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            found.add(key)
            found |= _walk_keys(value)
    elif isinstance(node, list):
        for item in node:
            found |= _walk_keys(item)
    return found


# ---------------------------------------------------------------- REQ-API-002 (Ruling A)


def test_coding_returns_both_surfaces_and_nothing_ranks_them(client: TestClient) -> None:
    """REQ-API-002: two answers for the coding intent, and NO field puts one above the other."""
    response = client.get("/v1/recommendations", params={"task": "coding", "budget": "sinirsiz"})
    assert response.status_code == 200
    body = response.json()

    answers = body["answers"]
    assert len(answers) == 2
    assert {a["surface"] for a in answers} == {"coding", "agentic-coding"}

    # The envelope says, in the payload itself, that the order means nothing.
    assert body["surfaces_are_ranked"] is False
    assert body["ordering_note"]

    # Trap 2: no precedence field anywhere, at any depth.
    assert _walk_keys(body) & PRECEDENCE_FIELDS == set()

    # ...and no single top-level answer that would make the array decorative.
    assert "answer" not in body
    assert "pick" not in body


def test_each_coding_surface_states_its_own_weakness(client: TestClient) -> None:
    """REQ-API-002 + REQ-API-004: the answer carries the weakness, not just the coverage report."""
    body = client.get("/v1/recommendations", params={"task": "coding"}).json()
    by_surface = {a["surface"]: a for a in body["answers"]}

    # agentic-coding's evidence has no evaluation dates at all — it must say so IN THE PAYLOAD.
    assert by_surface["agentic-coding"]["evidence_dating"] == "undated"
    assert by_surface["agentic-coding"]["evidence_dating_note"]

    # coding's evidence is dated; the field is derived from the evidence actually served,
    # never from the category's policy (the M5 BLOCKING-1 lesson).
    assert by_surface["coding"]["evidence_dating"] == "dated"


def test_explicit_single_surface_request_returns_that_surface_alone(client: TestClient) -> None:
    """REQ-API-002: Ruling A binds the coding INTENT; a caller naming one surface has chosen."""
    body = client.get("/v1/recommendations", params={"task": "agentic-coding"}).json()
    assert [a["surface"] for a in body["answers"]] == ["agentic-coding"]
    assert body["surfaces_are_ranked"] is False


def test_ordering_is_documented_and_stable(client: TestClient) -> None:
    """REQ-API-002: the order is deliberate, non-semantic, and identical run to run."""
    first = client.get("/v1/recommendations", params={"task": "coding"}).json()
    second = client.get("/v1/recommendations", params={"task": "coding"}).json()
    assert first == second
    assert [a["surface"] for a in first["answers"]] == ["agentic-coding", "coding"]


# ---------------------------------------------------------------- REQ-API-001 (surface shape)


def test_no_mutating_route_exists(client: TestClient) -> None:
    """REQ-API-001: V3C-12 is satisfied by ABSENCE, and the absence is asserted, not claimed."""
    from app.adapter import main as adapter

    mutating = {"POST", "PUT", "PATCH", "DELETE"}
    for route in adapter.app.routes:
        methods = getattr(route, "methods", set()) or set()
        assert not (methods & mutating), f"{getattr(route, 'path', route)} exposes {methods & mutating}"


def test_categories_endpoint_lists_the_registry(client: TestClient) -> None:
    """REQ-API-001: a client can discover the surfaces without hardcoding them."""
    body = client.get("/v1/categories").json()
    ids = {c["id"] for c in body["categories"]}
    assert {"coding", "agentic-coding", "assistant"} <= ids


def test_health_contract_is_untouched(client: TestClient) -> None:
    """REQ-API-001: L.7 build stamp survives the API milestone unchanged."""
    body = client.get("/health").json()
    assert {"status", "version", "build"} <= set(body)
    assert body["status"] == "ok"


# ---------------------------------------------------------------- REQ-API-005 (error contract)


def test_unknown_task_fails_closed_with_the_stable_shape(client: TestClient) -> None:
    """REQ-API-005: a bad input is refused, loudly, in the documented shape."""
    response = client.get("/v1/recommendations", params={"task": "nope"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "unknown_task"
    assert "nope" in body["error"]["message"]
    assert set(body["error"]) == {"code", "message"}


def test_unknown_budget_fails_closed_with_the_stable_shape(client: TestClient) -> None:
    """REQ-API-005: same shape for the other input dimension — one contract, not two."""
    response = client.get("/v1/recommendations", params={"task": "coding", "budget": "nope"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_budget"


def test_missing_database_fails_closed_and_leaks_no_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-API-005: fail closed, and never hand a caller a filesystem path."""
    secret = tmp_path / "not-a-real-place" / "pipeline.db"
    monkeypatch.setenv("MODEL_RANKING_DB", str(secret))
    from app.adapter import main as adapter

    response = TestClient(adapter.app, raise_server_exceptions=False).get(
        "/v1/recommendations", params={"task": "coding"}
    )
    assert response.status_code == 503
    body = response.text
    assert body.count("error")  # the stable shape, not a stack trace
    assert str(secret) not in body
    assert "not-a-real-place" not in body
    assert "Traceback" not in body


def test_a_surface_that_cannot_answer_is_disclosed_not_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-API-005 + the honesty doctrine: silence is the one answer this product may not give.

    An empty database can rank nothing. The wrong behaviours are (a) omitting the surface, which
    reads as "there is only one coding answer", and (b) 500. The right one is to serve the answer
    with no picks and say why.
    """
    db = tmp_path / "empty.db"
    connect(str(db)).close()
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    response = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"})
    assert response.status_code == 200
    answers = response.json()["answers"]
    assert len(answers) == 2  # BOTH still present — Ruling A does not bend on empty data
    for answer in answers:
        assert answer["picks"] == []
        assert answer["unavailable_reason"]


# ---------------------------------------------------------------- read-only handle


def test_the_api_never_writes_to_the_database(client: TestClient, tmp_path: Path) -> None:
    """The serving path opens the database read-only: a request may not migrate or mutate it.

    W-009 records that `connect()` migrates on open. An HTTP surface that calls it would let any
    anonymous GET rewrite the operator's schema.
    """
    db = Path(client.app.state.db_path) if hasattr(client.app.state, "db_path") else None
    before = (tmp_path / "pipeline.db").read_bytes()
    client.get("/v1/recommendations", params={"task": "coding"})
    after = (tmp_path / "pipeline.db").read_bytes()
    assert before == after, "a GET changed the database file"
    assert db is None or db.exists()


def test_read_only_handle_refuses_a_write() -> None:
    """The seam itself is proven, not assumed: the handle rejects SQL that writes."""
    import tempfile

    from app.adapter.main import open_readonly

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ro.db"
        connect(str(path)).close()
        conn = open_readonly(path)
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE probe (x INTEGER)")
