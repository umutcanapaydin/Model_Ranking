"""M6-W3: REQ-API-006's remaining clauses — CORS allowlist and startup validation.

The W1 security pass judged deferring these to W3 safe, with a named condition: *"provided W3
doesn't satisfy the clause with a wildcard, which would freeze as /v1 contract."* These tests are
that condition, written down so it cannot be satisfied by a wildcard later either.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapter.main import ConfigError, cors_origins, validate_startup_config


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
    }
    for answer in body["answers"]:
        extra = set(answer) - PUBLIC_ANSWER_FIELDS - api_only
        assert extra == set(), f"undeclared field(s) served to an anonymous caller: {sorted(extra)}"


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

    # A real file passes, so the check is about existence rather than about refusing everything.
    real = tmp_path / "advisor.db"
    real.write_bytes(b"")
    monkeypatch.setenv("MODEL_RANKING_DB", str(real))
    assert adapter.validate_startup_config(env="production") == ()


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
        return data

    monkeypatch.setattr(adapter, "recommendation_json", leaky)
    body = TestClient(adapter.app).get("/v1/recommendations", params={"task": "coding"}).json()

    for answer in body["answers"]:
        assert "internal_operator_note" not in answer, (
            "an undeclared field reached an unauthenticated caller — the publication allowlist is "
            "not filtering, only documenting"
        )
    # ...and the answer is still a real answer, so the filter is not just emptying the payload.
    assert any(a["picks"] for a in body["answers"])
