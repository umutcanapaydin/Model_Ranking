"""M6-W3: REQ-API-006's remaining clauses — CORS allowlist and startup validation.

The W1 security pass judged deferring these to W3 safe, with a named condition: *"provided W3
doesn't satisfy the clause with a wildcard, which would freeze as /v1 contract."* These tests are
that condition, written down so it cannot be satisfied by a wildcard later either.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapter.main import ConfigError, cors_origins, validate_startup_config


def _servable(path) -> None:
    """Create a database the startup probe accepts: schema, plus one price median.

    M7-W2 added a fourth probe check — an artifact with an EMPTY `px_median` answers every query
    with no picks, so it is refused at boot. That makes `connect(path).close()` no longer a
    servable fixture, which is the same lesson these tests already carried one line up: a fixture
    that is invalid for a DIFFERENT reason passes the test for the wrong reason.
    """
    from app.workflows.schema import connect

    conn = connect(str(path))
    try:
        conn.execute("INSERT INTO px_median (model_id, in_m, out_m) VALUES ('m', 1.0, 2.0)")
        conn.commit()
    finally:
        conn.close()


def test_a_wildcard_origin_is_refused_not_warned_about(monkeypatch: pytest.MonkeyPatch) -> None:
    """V3C-13: this surface forbids allow-all outright, not only allow-all WITH credentials.

    The baseline's rule is the narrower one. The reason for going further is contractual rather
    than defensive: the data is public, so no caller needs a wildcard to read it — and a wildcard
    frozen into `/v1` becomes something to widen from, not a default to tighten.
    """
    monkeypatch.setenv("MODEL_RANKING_CORS_ORIGINS", "*")
    with pytest.raises(ConfigError, match="wildcard"):
        cors_origins()

    monkeypatch.setenv("MODEL_RANKING_CORS_ORIGINS", "https://app.example.com, *")
    with pytest.raises(ConfigError, match="wildcard"):
        cors_origins()


def test_a_malformed_origin_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bare hostname is not an origin, and guessing the scheme is how a guard gets softer."""
    monkeypatch.setenv("MODEL_RANKING_CORS_ORIGINS", "app.example.com")
    with pytest.raises(ConfigError, match="absolute origin"):
        cors_origins()


def test_unset_means_no_cross_origin_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """The safer of the two possible defaults, asserted so nobody 'fixes' it into the other one."""
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    assert cors_origins() == ()


def test_an_explicit_allowlist_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard must permit the thing it exists to make possible."""
    monkeypatch.setenv(
        "MODEL_RANKING_CORS_ORIGINS", "https://app.example.com, https://ios.example.com"
    )
    assert cors_origins() == ("https://app.example.com", "https://ios.example.com")


def test_production_refuses_to_boot_without_its_evidence_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V3C-51: fail CLOSED at startup. A process that boots broken has already served the request."""
    monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    with pytest.raises(ConfigError, match="MODEL_RANKING_DB is unset"):
        validate_startup_config(env="production")


def test_production_refuses_to_boot_without_a_build_stamp(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """L.7: an unstamped production process cannot answer 'which code is live', so a deploy cannot
    be verified — and Stage 4.3's check is exactly that curl."""
    db = tmp_path / "x.db"
    db.write_bytes(b"")
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setattr("app.adapter.main.APP_BUILD", "unknown")
    with pytest.raises(ConfigError, match="APP_BUILD is unset"):
        validate_startup_config(env="production")


def test_development_reports_the_same_problems_without_refusing_to_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fail direction is environment-shaped, and the WARNINGS are still produced.

    A developer machine blocked by a missing deploy variable is a control people route around; a
    developer machine that stays silent about it is a control nobody learns from.
    """
    monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    problems = validate_startup_config(env="development")
    assert any("MODEL_RANKING_DB" in p for p in problems)


def test_a_wildcard_is_refused_in_development_too(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment softens the DATABASE check, never the CORS one.

    A wildcard is a contract decision, not a deploy variable — it would be written into a dev
    config, committed, and inherited by production, which is how allow-all ships.
    """
    monkeypatch.setenv("MODEL_RANKING_CORS_ORIGINS", "*")
    with pytest.raises(ConfigError, match="wildcard"):
        validate_startup_config(env="development")


def test_no_cors_header_is_served_when_no_allowlist_is_configured(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Built is not wired (V3C-73): the absence is asserted on a real response."""
    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    from app.adapter import main as adapter

    response = TestClient(adapter.app).get(
        "/v1/categories", headers={"Origin": "https://evil.example.com"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers}


# ---------------------------------------------- wiring, not definitions (V3C-73, all three seats)


def test_the_startup_validator_is_actually_CALLED_at_import() -> None:
    """BLOCKING from all three W3 seats: the validator was defined and invoked by nothing.

    Measured by two of them independently: `APP_ENV=production` with no database and no build stamp
    imported cleanly and served 200s. Four tests exercised the function; none exercised the
    invariant. The security seat named the reason mutation testing could not see it — *a mutant of
    a function no production path reaches is killed by a test of a function nobody calls.*

    Asserted from source, because the failure mode is the CALL going missing, and a behavioural
    test would keep passing as long as the module still imports.
    """
    import ast
    from pathlib import Path

    module = ast.parse(Path("src/app/adapter/main.py").read_text())
    module_level_calls = {
        node.value.func.id
        for node in module.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    }
    assert "validate_startup_config" in module_level_calls, (
        "the startup validator is not called at import — `uvicorn app.adapter.main:app` never "
        "runs it, so REQ-API-006's startup clause is unmet however many unit tests it has"
    )
    assert "cors_origins" in module_level_calls


def test_a_production_process_refuses_to_import_with_broken_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same invariant, proven through the real import rather than through the function.

    This is what row 7's clause (c) claimed and did not have: the process, not the helper.
    """
    import subprocess
    import sys

    env = {
        "PATH": "/usr/bin:/bin",
        "APP_ENV": "production",
        "PYTHONPATH": "src",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import app.adapter.main"],
        capture_output=True,
        text=True,
        env=env,
        cwd=".",
    )
    assert result.returncode != 0, "a production process imported with no evidence database"
    assert "MODEL_RANKING_DB is unset" in result.stderr


# ---------------------------------------------- the CORS middleware itself, not the pure function


def _client_with_origins(monkeypatch: pytest.MonkeyPatch, tmp_path, origins: str):
    """A live app whose CORS middleware was configured by the value under test.

    Loads a PRIVATE copy of the module from its spec rather than reloading the shared one. The first
    version called `importlib.reload`, and the W3 Tester found what that costs: `monkeypatch`
    restores the ENVIRONMENT at teardown but the reloaded module is already in `sys.modules` with
    the middleware installed, so every test file collected after this one got an app serving
    `Access-Control-Allow-Origin`. Nothing failed — the Tester checked reverse file order too — but
    a future test asserting the absence of that header would have passed or failed on collection
    order.

    Reloading it back is worse, and I tried it: the reload rebinds `ConfigError` and every other
    class, so tests holding a module-level reference start catching the wrong object. A private
    module leaves `sys.modules` untouched, which is the only version of this with no aftermath.
    """
    import importlib.util
    import sys

    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    monkeypatch.setenv("MODEL_RANKING_CORS_ORIGINS", origins)

    spec = importlib.util.find_spec("app.adapter.main")
    assert spec is not None and spec.loader is not None
    private = importlib.util.module_from_spec(spec)
    # Deliberately NOT registered in sys.modules: this object exists for one test and dies with it.
    spec.loader.exec_module(private)
    assert sys.modules["app.adapter.main"] is not private
    return TestClient(private.app)


def test_an_allowlisted_origin_is_echoed_and_others_are_not(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """BLOCKING from the code review: deleting the whole `add_middleware` block left 336 green.

    The previous CORS tests called `cors_origins()` — a pure function — and one asserted the
    ABSENCE of a header, which holds vacuously when the middleware is gone. So the implementation
    was correct, unproven and deletable, which the reviewer correctly called worse than wrong.
    """
    client = _client_with_origins(monkeypatch, tmp_path, "https://app.example.com")

    allowed = client.get("/v1/categories", headers={"Origin": "https://app.example.com"})
    assert allowed.headers.get("access-control-allow-origin") == "https://app.example.com"

    denied = client.get("/v1/categories", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in {k.lower() for k in denied.headers}


def test_credentials_are_never_allowed_across_origins(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """V3C-13's actual rule, asserted on a response: allow-all WITH credentials is the banned pair.

    This surface authenticates nobody, so allowing credentials could only ever be an accident.
    """
    client = _client_with_origins(monkeypatch, tmp_path, "https://app.example.com")
    response = client.get("/v1/categories", headers={"Origin": "https://app.example.com"})
    assert "access-control-allow-credentials" not in {k.lower() for k in response.headers}


def test_a_preflight_is_answered_for_get_and_refuses_a_mutating_verb(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The surface is three GET routes; a preflight must not advertise anything else."""
    client = _client_with_origins(monkeypatch, tmp_path, "https://app.example.com")
    preflight = client.options(
        "/v1/categories",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert preflight.status_code in (200, 204)
    allowed_methods = preflight.headers.get("access-control-allow-methods", "")
    assert "GET" in allowed_methods
    for verb in ("POST", "PUT", "PATCH", "DELETE"):
        assert verb not in allowed_methods


def test_the_environment_name_is_matched_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Claimed as pinned in a hand-back and it was not — the Tester checked and the mutant lived.

    `APP_ENV=PRODUCTION` from a deploy config must fail closed exactly like `production`. Dropping
    the `.lower()` would make the strictest environment the one spelled the least carefully.
    """
    # Resolved through the MODULE, not through the name imported at the top of this file: the CORS
    # tests above reload `app.adapter.main`, which rebinds `ConfigError` to a new class object, and
    # a stale reference would make this test pass alone and fail in file order. It did exactly that.
    import app.adapter.main as adapter

    monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    for spelling in ("production", "PRODUCTION", "Production", "PROD"):
        with pytest.raises(adapter.ConfigError, match="MODEL_RANKING_DB is unset"):
            adapter.validate_startup_config(env=spelling)


def test_configuring_cors_does_not_contaminate_the_shared_module() -> None:
    """The isolation itself, asserted — because the leak was invisible and order-dependent.

    The W3 Tester found the first version reloading `app.adapter.main` in place, so every test file
    collected after this one received an app with `CORSMiddleware` installed. Nothing failed, which
    is what made it worth a test rather than a comment: the cost was entirely latent, waiting for
    the first test that asserted a header's absence.
    """
    import app.adapter.main as shared

    before = len(shared.app.user_middleware)
    assert shared.cors_origins() == () or True  # touching the shared module must be harmless
    after = len(shared.app.user_middleware)
    assert before == after, "the shared app grew middleware from another test's configuration"

    # The shared app must never be serving a CORS header configured by this file.
    from .test_api_v1 import _seeded_db  # noqa: F401 - imported for parity with the other tests

    assert not any(
        "CORS" in type(mw.cls).__name__ or "CORS" in getattr(mw.cls, "__name__", "")
        for mw in shared.app.user_middleware
    ), "the shared module has CORS middleware installed by a test"


# ------------------------------------------------ Stage 4.0 closure findings (composition defects)


def test_no_engine_field_reaches_the_public_surface_undeclared() -> None:
    """Stage 4.0 BLOCKING-1: publication is a DECISION, not a default.

    W1's hand-written dictionary was a drift hazard and W2 was right to kill it — but on an
    unauthenticated surface that dictionary was also the publication allowlist, and the `asdict`
    passthrough that replaced it made "served to anonymous callers" the default for every future
    engine field. The parity tests could not see it: they enforce that engine fields REACH the
    payload, never that only declared ones do.

    This test fails when the engine gains a field, until a human puts it in one of the three lists.
    That failure is the point — it is the decision being forced.
    """
    from dataclasses import fields

    from app.adapter.main import (
        PUBLIC_ANSWER_FIELDS,
        RELOCATED_FIELDS,
        WITHHELD_ANSWER_FIELDS,
    )
    from app.workflows.recommend import Recommendation

    engine = {f.name for f in fields(Recommendation)}
    declared = PUBLIC_ANSWER_FIELDS | set(RELOCATED_FIELDS) | WITHHELD_ANSWER_FIELDS
    undeclared = sorted(engine - declared)
    assert undeclared == [], (
        f"engine field(s) {undeclared} are neither published, relocated nor withheld — decide "
        "before they reach an unauthenticated surface"
    )

    # **And the same at the nested level (RR-BLOCKING-1).** The first version of this test
    # enumerated ten of the twenty-nine engine fields: `picks` was one allowlisted key whose value
    # carried nineteen more, filtered by nothing. An allowlist that stops at the top level of a
    # nested document is a lid on one drawer.
    from app.adapter.main import PUBLIC_PICK_FIELDS, WITHHELD_PICK_FIELDS
    from app.workflows.recommend import Pick

    pick_engine = {f.name for f in fields(Pick)}
    pick_declared = PUBLIC_PICK_FIELDS | WITHHELD_PICK_FIELDS
    pick_undeclared = sorted(pick_engine - pick_declared)
    assert (
        pick_undeclared == []
    ), f"pick field(s) {pick_undeclared} are neither published nor withheld"
    assert sorted(pick_declared - pick_engine) == [], "the pick lists name fields the engine lost"
    assert undeclared == [], (
        f"engine field(s) {undeclared} are neither published, relocated nor withheld — decide "
        "before they reach an unauthenticated surface"
    )
    stale = sorted(declared - engine)
    assert stale == [], f"the lists name field(s) the engine no longer has: {stale}"


def test_the_public_payload_carries_only_declared_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The same property on a real response, because a set comparison is not a served payload."""
    from app.adapter.main import PUBLIC_ANSWER_FIELDS

    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))
    import app.adapter.main as adapter

    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()
    api_only = {
        "surface",
        "title",
        "primary_benchmark",
        "metric",
        "source_health",
        "evidence_dating",
        "evidence_dating_note",
        "unavailable_reason",
        # D-125 (M8-W2, the single revision D-124 permitted): the full ranking is published
        # beside the picks, because the client could not open a category it could not see. It is
        # listed HERE, in the guard, rather than being allowed through by widening the filter —
        # this assertion is the reason a fourth and fifth field cannot arrive unnoticed.
        "ranking",
    }
    from app.adapter.main import PUBLIC_PICK_FIELDS

    for answer in body["answers"]:
        extra = set(answer) - PUBLIC_ANSWER_FIELDS - api_only
        assert extra == set(), f"undeclared field(s) served to an anonymous caller: {sorted(extra)}"
        # ...and OPEN the picks. The first version compared top-level keys only and never looked
        # inside, which is exactly where the nineteen unfiltered fields were.
        assert answer["picks"], "no picks to inspect — this assertion would pass vacuously"
        for pick in answer["picks"]:
            extra_pick = set(pick) - PUBLIC_PICK_FIELDS
            assert extra_pick == set(), f"undeclared pick field(s) served: {sorted(extra_pick)}"


def test_an_unrecognised_environment_is_treated_as_strict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stage 4.0 BLOCKING-2: the hardening must not depend on spelling one of two exact strings.

    Measured by the closure review: `APP_ENV=staging` with no database booted and served happily,
    because anything that was not `production`/`prod` fell into the permissive branch — and the
    only places setting those two were `Dockerfile` and `fly.toml`, files this milestone explicitly
    declines to adopt. A process that cannot tell where it runs now assumes production.
    """
    import app.adapter.main as adapter

    monkeypatch.delenv("MODEL_RANKING_DB", raising=False)
    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)

    for unknown in ("staging", "uat", "prod-eu", "", "  "):
        with pytest.raises(adapter.ConfigError):
            adapter.validate_startup_config(env=unknown)

    # ...and a RELAXED environment must still be relaxed, or every developer machine is blocked.
    warnings = adapter.validate_startup_config(env="development")
    assert any("MODEL_RANKING_DB" in w for w in warnings)


def test_a_database_that_does_not_exist_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Stage 4.0 BLOCKING-3: the check asked whether the VARIABLE was set, not whether a file exists.

    The deploy proposals set `MODEL_RANKING_DB` unconditionally against a separately-shipped volume,
    so a total evidence outage produced a process that booted, answered `/health` 200, and failed
    every real request. Stage 4.3 verifies deploys with `/health` — it would have called that deploy
    healthy.
    """
    import app.adapter.main as adapter

    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("MODEL_RANKING_DB", str(tmp_path / "no-such-volume" / "advisor.db"))
    monkeypatch.setattr(adapter, "APP_BUILD", "deadbee")

    with pytest.raises(adapter.ConfigError, match="no readable file"):
        adapter.validate_startup_config(env="production")

    # A zero-byte file used to pass here, and the re-review was right to call that a blessing:
    # it is not a database, and the previous check only ever asked the filesystem about the path.
    empty = tmp_path / "empty.db"
    empty.write_bytes(b"")
    monkeypatch.setenv("MODEL_RANKING_DB", str(empty))
    with pytest.raises(adapter.ConfigError, match="not a model_ranking database"):
        adapter.validate_startup_config(env="production")

    # A REAL database passes, so the check is a probe rather than a refusal. M7-W2: "real" now
    # means SERVABLE, not merely schema-shaped — an empty `px_median` answers every query with no
    # picks, so the probe refuses it and this fixture has to be an artifact that could actually
    # serve.
    real = tmp_path / "advisor.db"
    _servable(real)
    monkeypatch.setenv("MODEL_RANKING_DB", str(real))
    assert adapter.validate_startup_config(env="production") == ()


def test_the_concurrency_cap_is_chosen_and_the_edge_agrees_with_it() -> None:
    """RESTORED at M7-W3, and the restoration is the finding.

    I deleted three tests when the memory-budget machinery went, on the grounds that they guarded a
    control that no longer exists. One of them also guarded a control that DOES still exist — the
    agreement between the process's concurrency cap and `fly.toml`'s edge `hard_limit` — and two
    mutants walked straight through the gap: setting the cap back to AnyIO's unchosen default of
    40, and drifting the edge limit to 32. Neither has anything to do with snapshots.

    The docstring of the test that replaced them says deleting a test quietly is how a control
    disappears without anyone deciding it should. That is what happened, in the same change.

    Why the agreement matters without W-017: `hard_limit` is what the EDGE will admit, and
    MAX_CONCURRENT_REQUESTS is what the process will actually run at once. If the edge admits more
    than the process runs, the surplus queues inside the app instead of being shed at the edge,
    and latency degrades in the place with the least visibility.
    """
    import re
    from pathlib import Path

    import app.adapter.main as adapter

    assert adapter.MAX_CONCURRENT_REQUESTS == 8, (
        "the concurrency cap is a CHOSEN number; AnyIO's default of 40 is what this replaced"
    )

    fly = Path("fly.toml").read_text(encoding="utf-8")
    # Comments are stripped: an M6 review found this exact assertion matching `hard_limit = 8`
    # inside a comment while the live value differed.
    live = "\n".join(line.split("#", 1)[0] for line in fly.splitlines())

    hard = re.search(r"hard_limit\s*=\s*(\d+)", live)
    assert hard, "fly.toml declares no hard_limit"
    assert int(hard.group(1)) == adapter.MAX_CONCURRENT_REQUESTS, (
        f"the edge admits {hard.group(1)} concurrent requests while the process runs "
        f"{adapter.MAX_CONCURRENT_REQUESTS}; the surplus queues inside the app"
    )

    env = re.search(r"MODEL_RANKING_MAX_CONCURRENCY\s*=\s*\"(\d+)\"", live)
    assert env and int(env.group(1)) == adapter.MAX_CONCURRENT_REQUESTS


def test_w017_is_closed_by_deletion_not_by_a_bounded_copy() -> None:
    """W-017: the serving path holds no copy of the database, so there is no ceiling to tune.

    Three of this file's tests were REMOVED at M7-W3, and they are named here because deleting a
    test quietly is how a control disappears without anyone deciding it should:

      * `test_the_servable_database_size_is_derived_from_the_declared_budget`
      * `test_a_database_larger_than_the_budget_refuses_to_boot`
      * `test_the_declared_numbers_agree_with_the_deploy_proposal`

    All three guarded `max_database_bytes()` and the constants behind it — `RSS_FACTOR`,
    `MEMORY_BUDGET_MB`, `PROCESS_BASELINE_MB` — which existed for exactly one reason: every
    in-flight request held a private in-memory COPY of the evidence database, and the process had
    to refuse to boot on a file too large to copy that many times.

    M7-W2 removed the write that forced the copy; M7-W3 removed the copy. **A ceiling for a copy
    that does not happen is a control with nothing behind it**, and keeping it would refuse to boot
    on a perfectly servable artifact. So the tests go with the code, and this one replaces them by
    asserting the property that made them unnecessary.
    """
    import ast
    from pathlib import Path

    import app.adapter.main as adapter

    source = Path("src/app/adapter/main.py").read_text(encoding="utf-8")

    assert not hasattr(adapter, "serving_snapshot"), (
        "serving_snapshot is back; W-017's amplification returns with it"
    )
    for gone in ("max_database_bytes", "RSS_FACTOR", "MEMORY_BUDGET_MB", "PROCESS_BASELINE_MB"):
        assert not hasattr(adapter, gone), (
            f"{gone} is back — it only ever sized a copy the serving path no longer makes"
        )

    # The mechanism, not the name: nothing in the adapter may copy a database into memory.
    tree = ast.parse(source)
    backups = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "backup"
    ]
    assert not backups, "the adapter calls sqlite3 backup(); that is the snapshot, renamed"
    assert ":memory:" not in source, "the adapter opens an in-memory database again"


def test_the_allowlist_actually_filters_an_undeclared_field(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Mandatory test for a stay-green fault (V3C-72): the filter's EFFECT was unobservable.

    Every engine field today is in the allowlist, so removing the filter changed nothing a test
    could see — the set-level check catches a new field being *declared*, and nothing caught the
    filter itself being *deleted*. That is the same shape as the defect this whole fix addresses:
    a control that is correct and unproven.

    So this makes the serializer emit a field the allowlist does not name, and asserts it does not
    reach an anonymous caller.
    """
    from .test_api_v1 import _seeded_db

    db = tmp_path / "pipeline.db"
    _seeded_db(db)
    monkeypatch.setenv("MODEL_RANKING_DB", str(db))

    import app.adapter.main as adapter
    from app.workflows import serialize

    real = serialize.recommendation_json

    def leaky(rec):
        data = real(rec)
        data["internal_operator_note"] = "connection string, row counts, anything"
        for pick in data.get("picks", []):
            pick["internal_pick_note"] = "the nested half, which the first fix missed"
        return data

    monkeypatch.setattr(adapter, "recommendation_json", leaky)
    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()

    for answer in body["answers"]:
        for pick in answer["picks"]:
            assert "internal_pick_note" not in pick, (
                "an undeclared field reached an anonymous caller INSIDE a pick — the nested half "
                "of the allowlist is not filtering"
            )
        assert "internal_operator_note" not in answer, (
            "an undeclared field reached an unauthenticated caller — the publication allowlist is "
            "not filtering, only documenting"
        )
    # ...and the answer is still a real answer, so the filter is not just emptying the payload.
    assert any(a["picks"] for a in body["answers"])


# --------------------------------------------------------- W-017's three conditions (Stage 4.0)


def test_the_concurrency_cap_is_applied_to_the_running_loop() -> None:
    """W-017 condition (c): the cap must be real in the process, not asserted in a config file.

    Sync handlers run on AnyIO's thread pool. Its default limiter is 40 — never chosen by this
    project — while `fly.toml` described `hard_limit = 8` as W-017's containment. Two caps, one of
    them accidental, is a coincidence rather than a containment.

    Read from INSIDE a running loop, because the limiter is per-loop: the first version of this
    test read it from the test thread and raised, which is the same shape as the defect — a check
    that looks at the wrong process.
    """
    import anyio

    import app.adapter.main as adapter

    async def probe() -> float:
        async with adapter._lifespan(adapter.app):
            return anyio.to_thread.current_default_thread_limiter().total_tokens

    assert anyio.run(probe) == adapter.MAX_CONCURRENT_REQUESTS

    # ...and the app must actually USE that lifespan, or the cap is applied to nothing.
    assert (
        adapter.app.router.lifespan_context is adapter._lifespan
    ), "the lifespan is defined but the app is not wired to it — the cap would never run"


def test_a_pre_m5_database_refuses_to_serve(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Mandatory test for a stay-green fault (V3C-72), and the case is LIVE in this repository.

    `advisor.db` and `owner_advisor.db` are pre-M5 schema — no `effort` column — and the serving
    path is read-only, so it cannot migrate them. Before this probe the process booted, answered
    `/health` with 200 and the build stamp, and returned 200 with zero picks for every real query.
    Stage 4.3 verifies deploys with `/health`, so it would have called that deploy healthy.

    Removing the column check left every test green, which is why this exists: the probe's other
    two branches were covered and its most specific one was not.
    """
    import sqlite3

    import app.adapter.main as adapter

    old = tmp_path / "pre-m5.db"
    conn = sqlite3.connect(str(old))
    try:
        # The M4-era shape: the tables exist, so the "not a model_ranking database" branch does not
        # fire; only the column check can catch this.
        conn.executescript("""
            CREATE TABLE scores (
                model_id TEXT, raw_name TEXT NOT NULL, benchmark TEXT NOT NULL,
                metric TEXT NOT NULL, score REAL NOT NULL, harness TEXT NOT NULL,
                run_date TEXT, source TEXT NOT NULL, source_url TEXT NOT NULL,
                observed_at TEXT NOT NULL
            );
            CREATE TABLE pricing (model_id TEXT, source TEXT NOT NULL);
            """)
        conn.commit()
    finally:
        conn.close()

    problem = adapter._database_unusable(old)
    assert problem is not None and "effort" in problem, (
        "a pre-M5 database passed the probe — it would boot, report /health 200, and answer every "
        "query with zero picks"
    )

    monkeypatch.delenv("MODEL_RANKING_CORS_ORIGINS", raising=False)
    monkeypatch.setattr(adapter, "APP_BUILD", "deadbee")
    monkeypatch.setenv("MODEL_RANKING_DB", str(old))
    with pytest.raises(adapter.ConfigError, match="effort"):
        adapter.validate_startup_config(env="production")


def test_the_repositorys_own_artifact_is_checked_not_assumed() -> None:
    """The probe is pointed at the real file, because that is the artifact D-116 ships.

    **Inverted at M7-W1, and the inversion is the point.** This test used to assert that
    `advisor.db` was pre-M5 and unusable — the honest state at the time, written so that whoever
    fixed it would be told to come here and update the expectation rather than meet silence. That
    is exactly what happened: `app.workflows.build` produced the artifact for the first time, this
    test went red, and W-023 closed. It now pins the opposite property.

    A test that pins a KNOWN DEFECT has to be able to notice when the defect is gone, or it
    quietly becomes a test that requires the defect.
    """
    from pathlib import Path

    import app.adapter.main as adapter

    artifact = Path("advisor.db")
    if not artifact.exists():
        pytest.skip(
            "advisor.db is not present in this checkout. It is gitignored and mounted at\n"
            "deploy time (D-116), so this guard protects the OWNER'S machine only: CI\n"
            "cannot check an artifact CI does not have. What protects a deploy is the\n"
            "startup probe in adapter.main, which refuses to boot on an unusable database.\n"
            "Recorded as W-029 so the gap is stated rather than inferred from a skip."
        )

    problem = adapter._database_unusable(artifact)
    assert problem is None, (
        f"advisor.db is not servable: {problem}. Rebuild it with "
        "`python -m app.workflows.build --db advisor.db --force --epoch-dir <bundle>` (W-023)."
    )
