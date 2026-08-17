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
from app.workflows.rank import build_price_medians
from app.workflows.registry import reconcile
from app.workflows.schema import connect

# Trap 2, frozen as an ALLOWLIST. This is the third formulation and the reason for each step is
# worth keeping, because the class is the one this project keeps paying for.
#
#   v1 — nine literal key names. The fresh-eyes review killed it by adding `primary_surface`.
#   v2 — a sixteen-stem regex. The re-review killed THAT with `display_order`, `suggested`,
#        `authoritative` and `canonical_answer`. A bigger vocabulary is still a vocabulary; a
#        denylist can only forbid the words its author thought of.
#   v3 — this. The payload's key set is FROZEN. A new key is a test failure whatever it is called,
#        which is the same shape as `DECLARED_ROUTES` and `PRECEDENCE_KEY_EXEMPT`: state what is
#        allowed, not what is forbidden.
#
# D-115 says the prohibition is on the property, not on a list of words. An allowlist is how that
# sentence becomes a gate instead of an intention.
ENVELOPE_KEYS = {"api_version", "query", "surfaces_are_ranked", "ordering_note", "answers"}

ANSWER_KEYS = {
    "surface",
    "title",
    "primary_benchmark",
    "metric",
    "ranking_effort",
    "source_health",
    "evidence_dating",
    "evidence_dating_note",
    "sources",
    "eligible_count",
    "frontier_size",
    "close_call",
    "effort_mix_notice",
    "stale_notice",
    "unavailable_reason",
    "picks",
}

SOURCE_HEALTH_KEYS = {"benchmark", "sources", "stale", "notice"}
SOURCE_ENTRY_KEYS = {"source", "rows", "newest_run_date", "age_days", "stale"}

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
        FakeRawSource(
            "epoch_deepswe_external",
            DEEPSWE,
            url="https://epoch.ai/#deepswe",
            last_verified="2026-08-15",
        ),
        run,
    )
    reconcile(conn)
    # M7-W2: production builds the price medians in `app.workflows.build`, not inside
    # `recommend()`. A fixture that reconciles is standing in for that build, so it does
    # the same last step -- otherwise it seeds an artifact the engine correctly refuses.
    build_price_medians(conn)
    conn.commit()
    conn.close()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    return TestClient(adapter.app)


def _boom(*_args: object, **_kwargs: object) -> object:
    """Force the unhandled-error path, so the 500's headers and body can be asserted."""
    raise RuntimeError("synthetic failure with a secret: hunter2")


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
    response = client.get("/v1/recommendations", params={"task": "coding", "budget": "unlimited"})
    assert response.status_code == 200
    body = response.json()

    answers = body["answers"]
    assert len(answers) == 2
    assert {a["surface"] for a in answers} == {"coding", "agentic-coding"}

    # The envelope says, in the payload itself, that the order means nothing.
    assert body["surfaces_are_ranked"] is False
    assert body["ordering_note"]

    # Trap 2, frozen: the key set IS the contract. A new key — `display_order`, `suggested`,
    # `authoritative`, or anything nobody has thought of yet — fails here before it can be argued
    # about.
    assert set(body) == ENVELOPE_KEYS, f"envelope key set changed: {set(body) ^ ENVELOPE_KEYS}"
    for answer in answers:
        assert set(answer) == ANSWER_KEYS, f"answer key set changed: {set(answer) ^ ANSWER_KEYS}"
        assert set(answer["source_health"]) == SOURCE_HEALTH_KEYS
        for entry in answer["source_health"]["sources"]:
            assert set(entry) == SOURCE_ENTRY_KEYS

    # ...and no single top-level answer that would make the array decorative.
    assert "answer" not in body
    assert "pick" not in body


def test_the_ordering_note_does_not_rank_the_surfaces(client: TestClient) -> None:
    """Trap 2's quietest vector: no key changes, the PROSE does the ranking.

    The re-review rewrote `ORDERING_NOTE` to "Use the coding answer; agentic-coding is
    supplementary evidence only" and every test stayed green, because the only assertion on it was
    that it is truthy. A note that a client renders verbatim is part of the contract.
    """
    body = client.get("/v1/recommendations", params={"task": "coding"}).json()
    note = body["ordering_note"].lower()

    assert "carries no meaning" in note or "no meaning" in note
    assert "neither" in note
    for ranking_word in (
        "use the",
        "supplementary",
        "prefer",
        "instead of",
        "more reliable",
        "authoritative",
        "we recommend",
        "should use",
    ):
        assert ranking_word not in note, f"the ordering note ranks the surfaces: {ranking_word!r}"


def test_the_two_coding_answers_are_structurally_symmetric(client: TestClient) -> None:
    """REQ-API-002 / D-115 clause 5: asymmetry is precedence by another route.

    If one answer carries a field the other does not, a client renders one of them as the richer,
    more authoritative one — without any field ever being called `primary`.
    """
    answers = client.get("/v1/recommendations", params={"task": "coding"}).json()["answers"]
    a, b = answers
    assert set(a) == set(b), f"answer key sets differ: {set(a) ^ set(b)}"
    assert set(a["source_health"]) == set(b["source_health"])
    # Deliberately NOT asserting equal pick labels. The re-review showed that goes False on a
    # one-board database where the contract is perfectly satisfied and `unavailable_reason` is
    # set — it would report a violation that has not occurred, which is its own kind of dishonest
    # test. Symmetry of SHAPE is the contract property; symmetry of CONTENT is not.


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


def test_an_unhealthy_source_is_disclosed_on_a_wall_clock(client: TestClient) -> None:
    """REQ-API-005 (the unhealthy-source case) + V3C-33/45: this control fails toward DISCLOSURE.

    The fixture's evidence is old (SWE-bench dated 2026-02-26) and the agentic board publishes no
    evaluation dates at all. Both are unhealthy and the payload must say so.

    The first version of this wave served `stale_notice: null` for both, because the engine's
    notice is a RELATIVE proxy — newest run date against newest observation in the same file — so
    it cannot fire for a server serving one static database. The wall clock is the anchor.
    """
    body = client.get("/v1/recommendations", params={"task": "coding"}).json()
    by_surface = {a["surface"]: a for a in body["answers"]}

    for surface, health in ((s, by_surface[s]["source_health"]) for s in by_surface):
        assert health["stale"] is True, f"{surface} reports healthy on months-old evidence"
        assert health["notice"], f"{surface} is stale and says nothing"

    # The undated board must be reported stale BECAUSE it is undated, never assumed current.
    agentic = by_surface["agentic-coding"]["source_health"]["sources"]
    assert [e["newest_run_date"] for e in agentic] == [None]
    assert [e["age_days"] for e in agentic] == [None]
    assert all(e["stale"] for e in agentic)


def test_fresh_evidence_reports_healthy_and_says_nothing(tmp_path: Path) -> None:
    """The arithmetic's OTHER direction. A control asserted only in one direction is half a control.

    The re-review's MINOR-R2: `stale` was asserted True three times and False nowhere, so a
    function hard-wired to "always stale" would have passed every test. Fail-closed is right; a
    freshness check that can only ever say "stale" is not a freshness check.
    """
    import datetime as dt

    from app.adapter import main as adapter
    from app.workflows.categories import CATEGORIES

    db = tmp_path / "fresh.db"
    _seeded_db(db)
    conn = adapter.open_readonly(db)
    try:
        # 2026-03-01 is three days after the fixture's SWE-bench evaluation date.
        health = adapter._source_health_json(conn, CATEGORIES["coding"], today=dt.date(2026, 3, 1))
    finally:
        conn.close()

    assert health["stale"] is False
    assert health["notice"] is None
    assert [e["age_days"] for e in health["sources"]] == [3]


def test_health_covers_every_source_behind_the_benchmark_not_just_the_declared_one(
    tmp_path: Path,
) -> None:
    """The join key is the BENCHMARK, because that is what the ranking selects on.

    Mandatory test for a stay-green fault (V3C-72), reproducing the security re-review's
    constructed case. `categories.py:23` calls `primary_source` *informational*, and
    `rank.py:173-235` selects `WHERE benchmark = :primary` with no source predicate, while
    `rank.py:52` registers a second first-class source for the SAME benchmark. Keyed on
    `primary_source`, the payload asserted `"stale": false` while serving evidence from a source it
    had not looked at — a positive false claim of freshness, which is worse than the silence it
    replaced.
    """
    import datetime as dt

    from app.adapter import main as adapter
    from app.workflows.categories import CATEGORIES

    db = tmp_path / "twosource.db"
    _seeded_db(db)
    writable = connect(str(db))
    # A second source on the same benchmark, ancient. This is the shape M5 shipped: Epoch is a
    # first-class source for SWE-bench Verified alongside swebench.com.
    writable.execute(
        "INSERT INTO scores (model_id, raw_name, benchmark, metric, score, harness, effort,"
        " run_date, source, source_url, observed_at)"
        " VALUES ('gpt-5', 'GPT-5', 'SWE-bench Verified', '% resolved', 79.0, 'inspect_ai',"
        " 'high', '2024-06-08', 'epoch_swe_bench_verified', 'https://epoch.ai/benchmarks',"
        " '2026-08-16T00:00:00+00:00')"
    )
    writable.commit()
    writable.close()

    conn = adapter.open_readonly(db)
    try:
        # Three days after the swebench rows: that source alone would read FRESH.
        health = adapter._source_health_json(conn, CATEGORIES["coding"], today=dt.date(2026, 3, 1))
    finally:
        conn.close()

    named = {entry["source"] for entry in health["sources"]}
    assert named == {"swebench", "epoch_swe_bench_verified"}, named
    assert health["stale"] is True, "a fresh declared source hid an ancient contributing one"
    assert "epoch_swe_bench_verified" in health["notice"]


def test_the_freshness_clock_is_utc(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Mandatory test for a stay-green fault (V3C-72): local time drifted from every other clock.

    `coverage.main` and the three other date call sites use `datetime.now(tz=UTC).date()`. This
    module used `date.today()`. Measured on the review host: local 2026-08-17 while UTC was still
    2026-08-16 — so at the 90-day boundary the API and the CLI disagree about one database at one
    instant, which is Trap 1's shape and the thing this milestone exists to close.
    """
    import datetime as dt

    from app.adapter import main as adapter

    assert adapter._utc_today() == dt.datetime.now(tz=dt.UTC).date()

    # The serving path must go through that seam, not around it.
    db = tmp_path / "clock.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setattr(adapter, "_utc_today", lambda: dt.date(2026, 3, 1))
    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()
    ages = [
        entry["age_days"]
        for answer in body["answers"]
        for entry in answer["source_health"]["sources"]
        if entry["age_days"] is not None
    ]
    assert ages == [3], f"the serving path did not use the UTC seam: {ages}"


def test_evidence_dated_in_the_future_is_not_healthy(tmp_path: Path) -> None:
    """V3C-33/45: an unusable date must fail toward disclosure, in BOTH impossible directions.

    `coverage.py:253` reads `age > window`, which is False for a negative age — so evidence dated
    in the future reported healthy. That branch was CLI-only until this wave put it on a network;
    the fix is what made a latent engine fail-open reachable, so the clamp lives here.
    """
    import datetime as dt

    from app.adapter import main as adapter
    from app.workflows.categories import CATEGORIES

    db = tmp_path / "future.db"
    _seeded_db(db)
    conn = adapter.open_readonly(db)
    try:
        health = adapter._source_health_json(conn, CATEGORIES["coding"], today=dt.date(2025, 1, 1))
    finally:
        conn.close()

    assert all(e["age_days"] is not None and e["age_days"] < 0 for e in health["sources"])
    assert health["stale"] is True
    assert "future" in health["notice"]


def test_an_absent_evidence_source_is_never_reported_healthy(client: TestClient) -> None:
    """V3C-33/45: unknown is not healthy. A source the database never heard of fails CLOSED."""
    body = client.get("/v1/recommendations", params={"task": "assistant"}).json()
    health = body["answers"][0]["source_health"]
    assert health["sources"] == []
    assert health["stale"] is True
    assert health["notice"]


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


def _all_routes(app_obj: object, prefix: str = "") -> list[tuple[str, set[str]]]:
    """Every route, INCLUDING inside mounts.

    The first version of this walk read `app.routes` one level deep and asked only "is anything
    mutating?". A `Mount` has no `.methods`, so mounting a sub-application with a POST route left
    every test green while `POST /sub/wipe` returned 200. A guarantee is only as strong as its walk.
    """
    found: list[tuple[str, set[str]]] = []
    for route in getattr(app_obj, "routes", []):
        path = prefix + str(getattr(route, "path", ""))
        methods = set(getattr(route, "methods", set()) or set())
        if methods:
            found.append((path, methods))
        inner = getattr(route, "app", None)
        if inner is not None and hasattr(inner, "routes"):
            found.extend(_all_routes(inner, path))
        elif hasattr(route, "routes"):
            found.extend(_all_routes(route, path))
    return found


def test_no_mutating_route_exists(client: TestClient) -> None:
    """REQ-API-001: V3C-12 is satisfied by ABSENCE, and the absence is asserted, not claimed."""
    from app.adapter import main as adapter

    mutating = {"POST", "PUT", "PATCH", "DELETE"}
    for path, methods in _all_routes(adapter.app):
        assert not (methods & mutating), f"{path} exposes {methods & mutating}"


def test_the_shipped_surface_is_exactly_the_declared_surface(client: TestClient) -> None:
    """REQ-API-001: the plan declares three routes. Anything else shipped was never reviewed.

    The security pass found FastAPI's defaults adding `/docs`, `/redoc`, `/openapi.json` and
    `/docs/oauth2-redirect` — seven routes where the plan declares three, two of them executing
    unpinned third-party JavaScript from a CDN. Scanning for mutating verbs would never have said
    so, because none of them mutates: the previous test had this list in hand and asked the
    narrower question.
    """
    from app.adapter import main as adapter

    # Written out HERE, not read from the module. `DECLARED_ROUTES` was self-declaring: adding a
    # real `@app.get("/v1/purge")` and the constant in one change left every test green, because
    # the test asked the module to confirm itself. The re-review found it — the same lesson the
    # author had already applied to the exemption set and not to this one.
    expected = {"/health", "/v1/categories", "/v1/recommendations"}
    shipped = {path for path, _ in _all_routes(adapter.app)}
    assert (
        shipped == expected
    ), f"undeclared: {sorted(shipped - expected)}; missing: {sorted(expected - shipped)}"
    assert set(adapter.DECLARED_ROUTES) == expected, "the module's own declaration drifted"


def test_responses_forbid_content_type_sniffing(client: TestClient) -> None:
    """Every response this app produces, INCLUDING the 500 — the header claim is checked, not made.

    The re-review found the first version claiming "every response" while checking two: Starlette's
    `ServerErrorMiddleware` sits outside user middleware, so the 500 carried no header at all. The
    remedy is an explicit handler rather than a narrowed claim, because a test whose docstring is
    broader than its assertions is the overstatement class this wave has already been caught in.
    """
    for response in (
        client.get("/v1/recommendations", params={"task": "coding"}),
        client.get("/v1/recommendations", params={"task": "<svg onload=alert(1)>"}),
        client.get("/health"),
        client.get("/v1/categories"),
        client.get("/does-not-exist"),
    ):
        assert response.headers["x-content-type-options"] == "nosniff", response.url

    from app.adapter import main as adapter

    crashing = TestClient(adapter.app, raise_server_exceptions=False)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(adapter, "open_readonly", _boom)
        response = crashing.get("/v1/recommendations", params={"task": "coding"})
    assert response.status_code == 500
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "Traceback" not in response.text
    assert "_boom" not in response.text


def test_echoed_input_is_bounded(client: TestClient) -> None:
    """REQ-API-005: an error body reflects attacker text, so the reflection is capped."""
    response = client.get("/v1/recommendations", params={"task": "A" * 5000})
    assert response.status_code == 400
    assert len(response.json()["error"]["message"]) < 300


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


def test_an_unset_database_env_fails_closed_rather_than_guessing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """REQ-API-005: no CWD-relative default. Serving the wrong data with a 200 is the worst outcome.

    Mandatory test for a stay-green fault (V3C-72): the fix-delta injection restored
    `os.environ.get("MODEL_RANKING_DB", "pipeline.db")` and nothing went red. A relative default
    means the answer depends on the process's working directory, which nobody reviews and no
    deploy artifact records — and it fails by serving a plausible answer from the wrong file.
    """
    monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    from app.adapter import main as adapter

    assert adapter._db_path() is None
    response = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "evidence_unavailable"


def test_an_unbuilt_artifact_is_refused_rather_than_answered_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M7-W2 splits this test in two, and the split IS REQ-API-008.

    It used to point an EMPTY database at `/v1` and assert a 200 carrying two empty-but-explained
    answers. That was right while `recommend()` built the price medians itself, because an empty
    database genuinely was "nothing ranks here". The build moved to `app.workflows.build`, so an
    empty database is now an UNFINISHED ARTIFACT — a server-side fault, not a result — and
    answering it 200 is the 200-with-no-picks failure W-023 shipped.

    Refusal is the `evidence_unavailable` class M6 already defined for a database that cannot be
    read, because both mean "this server cannot answer". The remedy is deliberately NOT in the
    body: it is in the startup log and the CLI, and a public error body is not the place to
    publish what command fixes this host.
    """
    db = tmp_path / "empty.db"
    connect(str(db)).close()
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    response = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"})

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "evidence_unavailable"
    assert "build" not in body["error"]["message"], "the remedy must not be published to callers"


def test_a_surface_that_cannot_answer_is_disclosed_not_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """REQ-API-005 + the honesty doctrine: silence is the one answer this product may not give.

    The other half of the split above. On a BUILT artifact where one surface's evidence source is
    absent, the wrong behaviours are still (a) omitting the surface, which reads as "there is only
    one coding answer", and (b) a 500. The right one is a 200 that carries the answer with no picks
    and says why — and D-121 stakes a degraded build's whole legitimacy on this.

    The seeded fixture gives BOTH coding surfaces evidence, so Ruling A is checked there; the
    surface with none is `assistant`, whose Arena source this fixture never ingests. Both halves
    matter and they are different claims, so the test makes both rather than picking whichever
    happened to be empty.
    """
    db = tmp_path / "partial.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    response = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"})
    assert response.status_code == 200
    answers = response.json()["answers"]
    assert len(answers) == 2, "BOTH surfaces stay present — Ruling A does not bend on thin data"

    assistant = TestClient(adapter.app).get(
        "/v1/recommendations", params={"task": "assistant"}
    )
    assert assistant.status_code == 200, "a surface with no evidence is DISCLOSED, never refused"
    (blind,) = assistant.json()["answers"]
    assert blind["picks"] == []
    assert blind["unavailable_reason"], "an empty answer must say why it is empty"
    assert "no evidence" in blind["unavailable_reason"].lower(), (
        "the reason must name the evidence gap, not blame the budget"
    )
    assert blind["source_health"]["stale"] is True


# ---------------------------------------------------------------- read-only handle


def test_the_api_never_writes_to_the_database(client: TestClient, tmp_path: Path) -> None:
    """The serving path opens the database read-only: a request may not migrate or mutate it.

    W-009 records that `connect()` migrates on open. An HTTP surface that calls it would let any
    anonymous GET rewrite the operator's schema.
    """
    before = (tmp_path / "pipeline.db").read_bytes()
    response = client.get("/v1/recommendations", params={"task": "coding"})
    after = (tmp_path / "pipeline.db").read_bytes()
    assert (
        response.status_code == 200
    ), "the request must have actually served, or this proves nothing"
    assert before == after, "a GET changed the database file"
    assert not list(tmp_path.glob("pipeline.db-*")), "a GET left a journal/WAL sidecar behind"


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
