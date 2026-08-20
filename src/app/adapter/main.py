"""FastAPI adapter: the L.7 /health probe plus the M6 read-only /v1 surface.

Seed C.1: day-1 green baseline. The very first commit must include a runnable
app + at least one passing test. Even if the app only serves /health.

Seed L.7: version-stamp the health probe so "which code is live?" is one curl.
  `APP_BUILD` (image tag / git SHA) is set by CI/build (e.g. `ENV APP_BUILD=<tag>`
  in the Dockerfile, or the deploy env). It defaults to "unknown" so dev/test/CI
  on defaults are unaffected. `/health` returns `{status, version, build}` from
  Day 1 (additive fields only -- the liveness `status` contract is untouched).

This module is the seed of `src/<pkg>/adapter/` -- customer-facing API surface
per K.1 boundary discipline (D-001).

M6-W1 adds `/v1`, and it adds NOTHING to the engine. Every number served here is
computed by `app.workflows.recommend`; this module chooses what to expose and how to
label it. If a route ever needs the engine to behave differently, that is a finding.

**The contract this surface freezes (owner Ruling A, 2026-08-16).** A coding request
returns BOTH coding answers -- `coding` (dated evidence, narrower) and `agentic-coding`
(broader, undated evidence) -- and NEITHER leads. The answers are ordered alphabetically
by surface id precisely because alphabetical order is meaningless, and the envelope says
so in the payload rather than in documentation the caller will not read. There is no
`primary` flag, no top-level winner, and no single-answer shortcut, because each of those
would re-introduce a ranking the owner did not make.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import logging
import os
import sqlite3
from collections.abc import AsyncIterator
from dataclasses import fields
from pathlib import Path
from typing import Any

import anyio.to_thread
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.workflows.categories import CATEGORIES, CategorySpec
from app.workflows.coverage import SOURCE_STALE_DAYS, source_health
from app.workflows.rank import RankingRow, UnbuiltEvidenceError, category_ranking
from app.workflows.recommend import (
    BUDGETS,
    Pick,
    Recommendation,
    recommend,
    round_optional_score,
    round_score,
)
from app.workflows.serialize import recommendation_json

APP_VERSION = "0.1.0"
# CI/build sets APP_BUILD to the image tag or git SHA; defaults to "unknown".
APP_BUILD = os.environ.get("APP_BUILD", "unknown")

API_VERSION = "v1"

#: Ruling A: the surfaces a bare coding request answers on, in a DELIBERATELY
#: non-semantic order. Alphabetical is the point -- any order that could be read as
#: a ranking is the defect this constant exists to avoid.
CODING_INTENT: tuple[str, ...] = ("agentic-coding", "coding")

ORDERING_NOTE = (
    "Answers are ordered alphabetically by surface id. The order carries no meaning: neither "
    "coding surface leads the other. They rank different sets of plans on different evidence, "
    "and each states its own weakness."
)

#: The ENTIRE surface this milestone declares (REQ-API-001). Asserted exactly, not merely
#: scanned for mutating verbs: the W1 security pass found that FastAPI's defaults shipped four
#: more routes than the plan declares, two of which execute unpinned third-party JavaScript from
#: a CDN. A route nobody declared is a route nobody reviewed.
DECLARED_ROUTES: frozenset[str] = frozenset(
    {"/health", f"/{API_VERSION}/categories", f"/{API_VERSION}/recommendations"}
)

# docs_url / redoc_url / openapi_url are OFF because the plan declares three routes and these
# would make seven. `/v1/categories` is the discovery surface; it needs no CDN.
#: Environments where a missing or permissive security config is a defect rather than a
#: convenience. Anything else is a developer machine, where refusing to boot helps nobody.
PRODUCTION_ENVS = frozenset({"production", "prod"})

#: The only environments allowed to RELAX the startup checks, spelled exactly. Everything else —
#: including unset — is strict. See `validate_startup_config` for the two Stage-4.0 findings that
#: inverted this default.
RELAXED_ENVS = frozenset({"development", "dev", "test", "local"})

# --- W-017 is CLOSED (M7-W3), and the budget machinery went with it -------------------------------
#
# M6 could not fix the write-while-serving defect -- its signed plan forbade engine changes -- so it
# CONTAINED it by copying the database into memory per request, and then spent a Stage-4.0 round
# deriving a memory ceiling for that copy: an RSS factor, a VM budget, a process baseline, a
# concurrency cap, and a derived `max_database_bytes()`. Every one of those constants existed to
# size a copy that no longer happens.
#
# M7-W2 removed the write; M7-W3 removed the copy. The serving path now opens the operator's file
# read-only and reads it. **A ceiling for a copy that does not happen is a control with nothing
# behind it**, so the constants are deleted rather than left at comfortable values -- keeping them
# would leave a future reader tuning a budget that governs nothing.
#
# What DOES still bound this process is the thread-pool limiter, which is a real property of the
# server regardless of snapshots: sync handlers run on AnyIO's pool, whose default of 40 is a
# number nobody in this project chose.

#: How many requests may execute a handler at once. Set on AnyIO's limiter at startup; `fly.toml`
#: ties its edge concurrency to the same number, and a test fails if the two drift.


class ConfigError(RuntimeError):
    """Security-relevant configuration is missing or unusable. Raised at STARTUP, never per-request.

    V3C-51: a process that boots with a broken security config and fails per-request has already
    served the request that mattered.
    """


def _positive_env(name: str, default: str) -> int:
    """An operator-supplied count that must be a positive integer, checked at import.

    Stage-4.0 MINOR-6: `MODEL_RANKING_MAX_CONCURRENCY=0` made the process boot, bind its port, and
    then hang EVERY request including `/health` — measured at 120 s with no response. A liveness
    probe that never answers reads as a slow start, so the deploy would have been retried rather
    than diagnosed. A negative value does the same, and a non-numeric one crashed with a ValueError
    that said nothing about which variable was wrong.
    """
    raw = os.environ.get(name, default).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        msg = f"{name} must be a positive integer; got {raw!r}"
        raise ConfigError(msg) from exc
    if value < 1:
        msg = (
            f"{name} must be at least 1; got {value}. A limiter of zero binds the port and then "
            "answers nothing, including /health"
        )
        raise ConfigError(msg)
    return value


MAX_CONCURRENT_REQUESTS = _positive_env("MODEL_RANKING_MAX_CONCURRENCY", "8")

#: The largest ranked-model count this process will serve. Measured rather than guessed: the
#: Stage-4.0 pass drove a container capped at the VM size `fly.toml` declares and found ~10,000
#: ranked models using 58% of it and ~50,000 OOM-killed, against 73 in the shipped artifact. Set an
#: order of magnitude below the measured failure and two above today's data, so a refresh that
#: doubles the registry is fine and one that multiplies it by a hundred stops at deploy.
MAX_RANKED_ROWS = int(os.environ.get("MODEL_RANKING_MAX_RANKED_ROWS", "5000"))

#: The largest ranking ONE answer may publish. This is an EGRESS bound, not a memory bound, and it
#: is checked at BOOT rather than trimmed at serve time -- deliberately.
#:
#: D-125 added the full `ranking` array beside the three picks, which took an unauthenticated GET
#: from ~1-2 KB to ~20 KB. The obvious fix, truncating in the serializer, is the one thing this
#: product refuses: a silently shortened list is a list the reader believes is complete, and
#: disclosing the truncation would need a new payload field -- a SECOND contract revision, where
#: D-124 permits one and D-125 already spent it.
#:
#: So the artifact is bounded instead of the response. An artifact that would publish a larger
#: answer cannot boot, and the operator is told which surface and what the bound is. Nothing is
#: ever truncated, because the state that would require truncating is unreachable.
#:
#: 500 is a runaway guard, not a product limit: the largest surface today is 58 rows, and 500 caps
#: one answer near ~100 KB. Raising it is a deliberate egress decision, which is why it is an
#: environment variable with a name that says what it costs.
MAX_PUBLISHED_RANKING_ROWS = int(
    os.environ.get("MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS", "500")
)


def _largest_surface_row_count(db: Path) -> tuple[str, int] | None:
    """The biggest ranking any single answer would publish, and which surface it is.

    Calls `category_ranking` rather than mirroring its join in a COUNT query. A second copy of that
    query would be a second definition of "what gets published", and this project has spent several
    milestones on what happens when two definitions of the same set drift apart.
    """
    try:
        conn = open_readonly(db)
    except sqlite3.Error:
        return None
    try:
        worst = ("", 0)
        for name, spec in CATEGORIES.items():
            size = len(category_ranking(conn, spec))
            if size > worst[1]:
                worst = (name, size)
        return worst
    except sqlite3.Error:
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def _ranked_row_count(db: Path) -> int | None:
    """How many models the artifact can actually rank, or None if it cannot be asked.

    Counts DISTINCT reconciled models carrying a score, which is what `category_ranking` joins over
    and therefore what the process pays memory for. An unreadable database returns None here rather
    than raising: `_database_unusable` above is the check that reports that, and two checks
    reporting the same fault in different words is how an operator learns to skim them.
    """
    try:
        conn = open_readonly(db)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            "SELECT count(DISTINCT model_id) FROM scores WHERE model_id IS NOT NULL"
        ).fetchone()
        return int(row[0]) if row else 0
    except sqlite3.Error:
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def _db_path() -> Path | None:
    """The evidence database, named EXPLICITLY or not at all.

    The W1 security pass: a working-directory-relative default serves the WRONG DATABASE with a
    200 instead of refusing to boot, and a server's CWD is not a thing anyone reviews. There is no
    default. Unset is a fail-closed 503, like every other unusable-evidence condition.
    """
    raw = os.environ.get("MODEL_RANKING_DB", "").strip()
    return Path(raw) if raw else None


def cors_origins() -> tuple[str, ...]:
    """The explicit origin allowlist, from `MODEL_RANKING_CORS_ORIGINS` (V3C-13).

    **A wildcard is refused, not warned about.** The baseline forbids allow-all with credentials;
    this surface goes further and forbids allow-all outright, because the answer is public data and
    no caller needs a wildcard to read it — while a wildcard frozen into `/v1` would be a contract
    to widen later rather than a default to tighten.

    Empty means NO cross-origin access, which is what a same-origin iOS client needs and is the
    safer of the two possible defaults. The W1 security pass judged deferring this safe on exactly
    that condition: that W3 would not satisfy the clause with a wildcard.
    """
    raw = os.environ.get("MODEL_RANKING_CORS_ORIGINS", "").strip()
    if not raw:
        return ()
    origins = tuple(part.strip() for part in raw.split(",") if part.strip())
    for origin in origins:
        if origin == "*":
            msg = (
                "MODEL_RANKING_CORS_ORIGINS contains '*'. This surface serves public data and needs"
                " no wildcard; a wildcard frozen into /v1 becomes a contract. List origins"
                " explicitly, or leave it unset for no cross-origin access."
            )
            raise ConfigError(msg)
        if not origin.startswith(("http://", "https://")):
            msg = f"MODEL_RANKING_CORS_ORIGINS entry {origin!r} is not an absolute origin"
            raise ConfigError(msg)
    return origins


def open_readonly(path: Path) -> sqlite3.Connection:
    """Open the pipeline database READ-ONLY.

    INV-23: the URI is derived through `Path.resolve().as_uri()`, never concatenated -- a `?` in
    the path silently dropped the mode and created a database when this was string-built elsewhere.

    Read-only is not a precaution here, it is the contract. `schema.connect()` migrates on open
    (W-009), so a serving path that used it would let an anonymous GET rewrite the operator's
    schema. The API reads; the operator migrates, explicitly, with `schema migrate`.
    """
    uri = f"{path.resolve().as_uri()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _database_unusable(db: Path) -> str | None:
    """Open the evidence database read-only and ask it whether it can answer. `None` if it can.

    Three checks, and each of them is a way the previous stat-only version said yes to a database
    that could not serve: it must open as SQLite, it must carry the tables the serving path reads,
    and those tables must carry the columns this milestone's engine selects. The third is the one
    that catches a pre-M6 artifact — the schema migrated forward and the read-only path cannot.
    """
    try:
        conn = open_readonly(db)
    except sqlite3.Error as exc:
        return f"MODEL_RANKING_DB cannot be opened read-only: {type(exc).__name__}"
    try:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        missing = {"scores", "pricing"} - tables
        if missing:
            return (
                f"MODEL_RANKING_DB is not a model_ranking database — missing table(s) "
                f"{sorted(missing)}"
            )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(scores)")}
        if "effort" not in columns:
            return (
                "MODEL_RANKING_DB predates M5's effort column, and the serving path is read-only "
                "so it cannot migrate. Run `python -m app.workflows.schema migrate --db PATH` "
                "before shipping this artifact; serving it would answer every request with zero "
                "picks while /health reported the deploy healthy"
            )
        # M7-W2: a FOURTH way to say yes to a database that cannot serve. Until this wave
        # `recommend()` built the price medians itself, so an empty `px_median` was impossible at
        # serving time. The build moved to `app.workflows.build`, and `rank.py` JOINs that table —
        # an empty one yields zero rows, `recommend()` returns None, and every query answers 200
        # with no picks while `/health` reports a healthy build. Refusing to boot is the fail-closed
        # direction (V3C-33/45), and it names the command rather than leaving an operator to guess.
        if "px_median" not in tables or not conn.execute(
            "SELECT count(*) FROM px_median"
        ).fetchone()[0]:
            return (
                "MODEL_RANKING_DB has no price medians, so every query would answer with no "
                "picks. Build it with `python -m app.workflows.build --db <path>`"
            )
    except sqlite3.Error as exc:
        return f"MODEL_RANKING_DB is unreadable: {type(exc).__name__}"
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()
    return None


def validate_startup_config(env: str | None = None) -> tuple[str, ...]:
    """Check the security-relevant configuration once, at import, and FAIL CLOSED unless told not to.

    V3C-51. Returns the warnings a deliberately relaxed environment may run with; raises otherwise.

    **Two Stage-4.0 BLOCKING findings live in the first three lines of this function.**

    *The environment used to default to `development`*, which is the permissive branch — so the
    hardening activated only when `APP_ENV` was spelled exactly `production` or `prod`, and the only
    places setting that were `Dockerfile` and `fly.toml`, two files this milestone explicitly
    declines to adopt. `APP_ENV=staging` with no database booted and served happily. An unset or
    unrecognised environment is now the STRICT branch: a process that cannot tell where it runs
    assumes the place where being wrong costs the most.

    *And the database check asked whether the VARIABLE was set*, never whether a database exists —
    while the deploy proposals set that variable unconditionally against a separately-shipped
    volume. The result was a process that booted, answered `/health` with 200, and failed every real
    request; Stage 4.3 verifies deploys with `/health`, so it would have called that deploy healthy.
    """
    raw_env = env if env is not None else os.environ.get("APP_ENV", "")
    environment = raw_env.strip().lower()
    problems: list[str] = []

    cors_origins()  # raises ConfigError on a wildcard or a malformed origin, in every environment

    strict = environment not in RELAXED_ENVS
    if environment and environment not in RELAXED_ENVS and environment not in PRODUCTION_ENVS:
        problems.append(
            f"APP_ENV={raw_env.strip()!r} is not a recognised environment, so the startup checks "
            f"are being applied strictly. Set one of {sorted(RELAXED_ENVS | PRODUCTION_ENVS)}"
        )

    db = _db_path()
    if db is None:
        problems.append("MODEL_RANKING_DB is unset — the process has no evidence database to serve")
    elif not db.is_file():
        problems.append(
            "MODEL_RANKING_DB points at no readable file — the evidence database is a shipped "
            "artifact (D-116) and this process has none, so /health would report a healthy deploy "
            "over a total evidence outage"
        )
    else:
        # **Stage 4.0 re-review RR-BLOCKING-2: stat is not open.** The previous check asked the
        # filesystem about the path and never asked SQLite about the contents, so a zero-byte file,
        # a truncated one, a non-SQLite one and one the process cannot read all booted and answered
        # `/health` with 200. It was not hypothetical: this repository's own `advisor.db` is
        # pre-M6 schema, the read-only serving path cannot migrate it, and the process would have
        # served 200s with zero picks over it. Stage 4.3 verifies deploys with `/health`.
        problem = _database_unusable(db)
        if problem:
            problems.append(problem)

        # The database-SIZE ceiling was deleted at M7-W3 with the snapshot it existed for, and the
        # Stage-4.0 pass proved that deletion right by measuring the thing it measured: a file
        # inflated to 121 MB with the same 73 models cost **zero** additional memory, so the old
        # check would have refused a harmless artifact. It also showed what the old check MISSED —
        # a 6 MB artifact with 10,000 ranked models reached 58% of a 256 MB VM, and 50,000 models
        # was OOM-killed. **The cost is linear in RANKED ROWS, not in file bytes.**
        #
        # So the ceiling is not restored, it is re-pointed at the right quantity. Not attacker
        # reachable — `task` and `budget` are closed enums and the artifact is operator-built — but
        # a data refresh that outgrows the machine should still fail at DEPLOY rather than under
        # the first burst of traffic, which is what W-017's condition (a) was always about.
        largest = _largest_surface_row_count(db)
        if largest is not None and largest[1] > MAX_PUBLISHED_RANKING_ROWS:
            problems.append(
                f"MODEL_RANKING_DB would publish {largest[1]} ranking rows in a single answer on "
                f"the {largest[0]!r} surface; this process refuses past "
                f"{MAX_PUBLISHED_RANKING_ROWS}. The response is not truncated to fit — a silently "
                "shortened ranking is one the reader believes is complete. Narrow what the build "
                "ingests, or raise MODEL_RANKING_MAX_PUBLISHED_RANKING_ROWS knowing it raises what "
                "one unauthenticated request costs to serve"
            )

        ranked = _ranked_row_count(db)
        if ranked is not None and ranked > MAX_RANKED_ROWS:
            problems.append(
                f"MODEL_RANKING_DB ranks {ranked} models; this process refuses past "
                f"{MAX_RANKED_ROWS}. Measured at Stage 4.0: ~10,000 ranked models reach 58% of a "
                "256 MiB VM and ~50,000 are OOM-killed. Raise MODEL_RANKING_MAX_RANKED_ROWS with "
                "the VM, or narrow what the build ingests"
            )

    if strict and APP_BUILD == "unknown":
        problems.append(
            "APP_BUILD is unset — /health cannot say which code is live, so a deploy cannot be"
            " verified (L.7)"
        )

    if problems and strict:
        raise ConfigError("; ".join(problems))
    return tuple(problems)


@contextlib.asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """W-017 condition (c): cap in-process concurrency EXPLICITLY, inside the running loop.

    Sync handlers run on AnyIO's thread pool, whose default limiter is **40** — a number this
    project never chose, while `fly.toml` asserted `hard_limit = 8` as "W-017's containment". Two
    different caps, one of them accidental, is not a containment; it is a coincidence that happened
    to be in the safer direction. Setting it here makes the memory arithmetic above true of the
    process that actually runs, and `test_the_concurrency_cap_is_applied_to_the_running_loop` reads
    it back rather than trusting this comment.

    It cannot be done at import: the limiter needs a loop, and asking for one outside a lifespan
    raises. That is also why the first attempt at this condition failed loudly instead of silently
    doing nothing — which is the better of the two ways to get it wrong.
    """
    anyio.to_thread.current_default_thread_limiter().total_tokens = MAX_CONCURRENT_REQUESTS
    yield


app = FastAPI(
    title="model_ranking",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=_lifespan,
)


#: **Run at import, which is the only startup this process has.** `make serve` is
#: `uvicorn app.adapter.main:app`, so importing this module IS the boot — and until M6-W3 this
#: validator was defined and called by nothing but tests. All three review seats found it
#: independently, and the security seat named why mutation testing could not: a mutant of a
#: function no production path reaches is killed by a test of a function nobody calls.
STARTUP_WARNINGS = validate_startup_config()
if STARTUP_WARNINGS:
    # **Emitted, not just returned.** The first version computed these and dropped them, which is a
    # smaller instance of the defect this same fix closed one line up — and the test asserting the
    # development path had a docstring saying "a developer machine that stays silent about it is a
    # control nobody learns from" while the process stayed silent. Found by the W3 code review.
    logging.getLogger(__name__).warning(
        "model_ranking starting with unmet configuration: %s", "; ".join(STARTUP_WARNINGS)
    )

_ALLOWED_ORIGINS = cors_origins()
if _ALLOWED_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_ALLOWED_ORIGINS),
        # Credentials are never allowed on this surface: it serves public data and authenticates
        # nobody, so allowing them could only ever be an accident with consequences.
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )


@app.middleware("http")
async def _no_sniff(request: Any, call_next: Any) -> Any:
    """Error and answer bodies are JSON; never let a browser guess otherwise."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(Exception)
async def _unhandled(request: Any, exc: Exception) -> JSONResponse:
    """The 500, in the same shape as every other error and with the same header.

    Starlette's `ServerErrorMiddleware` sits OUTSIDE user middleware, so the header above never
    reached an unhandled error — the W1 security re-review measured it. This handler also keeps the
    exception's text out of the body: an exception message is the one place a secret reaches a
    response without anyone deciding it should.

    The header is set HERE rather than relying on the middleware, for the same reason this handler
    exists: `ServerErrorMiddleware` runs outside it, so nothing above would ever add it.
    """
    response = _error(500, "internal_error", "The request could not be served.")
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# `serving_snapshot` was DELETED at M7-W3, and W-017 closed with it.
#
# It copied the whole evidence database into memory for every unauthenticated GET, because
# `recommend()` wrote on every call and an HTTP surface cannot serve from a read-write handle. That
# containment was measured at roughly 47,000x amplification and named by D-116 as a condition of
# go-live. Three security passes derived three different numbers for it and the closure review
# explained why: the ratio is dominated by database SIZE, an operator variable an attacker cannot
# move, so the per-byte figure was never the quantity that decided anything.
#
# **The amplification is not bounded now, it is gone.** M7-W2 moved the median build into
# `app.workflows.build`, so the serving path performs no write at all and reads the operator's file
# directly through `open_readonly`. Nothing is copied, so there is no ceiling to compute and no
# budget to tune -- the machinery that existed only to size that copy went with it.

def _echo(value: str, limit: int = 40) -> str:
    """Attacker-controlled text going back out. Bounded, and bounded visibly."""
    return value if len(value) <= limit else f"{value[:limit]}…"


def _error(status: int, code: str, message: str) -> JSONResponse:
    """The one error shape. Loud, closed, and carrying no filesystem path (REQ-API-005)."""
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def _evidence_dating(picks: tuple[Pick, ...]) -> tuple[str, str | None]:
    """Whether the evidence THIS ANSWER served carries evaluation dates (REQ-API-004).

    Derived from the rows actually published, never from the category's policy -- publishing the
    policy where the reader will assume evidence is the exact defect M5's security review caught
    as BLOCKING-1.
    """
    if not picks:
        return "unknown", None
    dated = [p.evidence_date is not None for p in picks]
    if all(dated):
        return "dated", None
    if not any(dated):
        return (
            "undated",
            "This answer's benchmark publishes no evaluation dates, only model release dates. "
            "Its scores cannot be aged, so freshness is unknown rather than recent.",
        )
    return (
        "mixed",
        "Some picks in this answer carry an evaluation date and some do not; the undated ones "
        "cannot be aged.",
    )


def _source_health_json(
    conn: sqlite3.Connection, spec: CategorySpec, today: dt.date
) -> dict[str, Any]:
    """Whether this surface's evidence source has gone quiet, on a WALL CLOCK (REQ-API-005).

    **This exists because the first version of this wave failed OPEN, and that is the one direction
    a health check may never fail in.** What shipped was `Recommendation.stale_notice`, whose own
    docstring (`recommend.py:245-252`) admits it is a RELATIVE proxy: newest `run_date` compared
    against newest `observed_at` in the same database. For a CLI run right after an ingest that is
    a fair signal. For a server process serving one static file for months it is structurally
    incapable of firing — the two dates freeze together and the answer goes quiet exactly as the
    evidence ages. The wave's own fixture proved it: `source_health` reported both sources stale
    (swebench 172 days; the DeepSWE board with no parseable date at all) while the payload served
    `stale_notice: null`.

    `coverage.source_health` is the project's wall-clock model and it was already hardened for this:
    a source with rows but NO parseable date reports `stale=True` (`coverage.py:66-69`), which is
    fail-toward-disclosure. The API reads that, rather than owning a second opinion about freshness.

    Unknown is not healthy. A benchmark the database has never heard of reports `stale: true`.

    **Keyed on the BENCHMARK, not on `spec.primary_source`.** The first version of this fix joined
    on `primary_source`, which `categories.py:23` annotates as *"informational"* — and
    `rank.py:173-235` selects rows by `benchmark` with **no source predicate**, while `rank.py:52`
    registers `epoch_swe_bench_verified` as a second first-class source for the same benchmark. The
    security re-review built the case: swebench re-dated fresh, Epoch rows 800 days old winning the
    ranking, and the payload asserted `"stale": false` beside a `sources` list naming Epoch. **One
    payload contradicting itself, and a positive false claim of freshness is worse than the silence
    it replaced.** So this asks what the ranking asks: every source contributing to this benchmark,
    stale if ANY of them is stale.
    """
    sources = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT source FROM scores WHERE benchmark = ? ORDER BY source",
            (spec.primary_benchmark,),
        )
    ]
    by_source = {h.source: h for h in source_health(conn, today=today)}
    entries: list[dict[str, Any]] = []
    for name in sources:
        health = by_source.get(name)
        if health is None:  # pragma: no cover - a source with rows always appears in the report
            entries.append(
                {
                    "source": name,
                    "rows": 0,
                    "newest_run_date": None,
                    "age_days": None,
                    "stale": True,
                }
            )
            continue
        age = health.age_days
        # A negative age is evidence dated in the FUTURE. `coverage.py:253` reads `age > window`,
        # which is False for a negative number, so an unusable date reported HEALTHY. That branch
        # was CLI-only until this wave put it on a network. Unusable is not fresh.
        stale = bool(health.stale or (age is not None and age < 0))
        entries.append(
            {
                "source": health.source,
                "rows": health.rows,
                "newest_run_date": health.newest_run_date,
                "age_days": age,
                "stale": stale,
            }
        )

    if not entries:
        return {
            "benchmark": spec.primary_benchmark,
            "sources": [],
            "stale": True,
            "notice": (
                f"No evidence source for {spec.primary_benchmark} is present in the served "
                "database, so freshness cannot be established."
            ),
        }

    stale_entries = [e for e in entries if e["stale"]]
    notice: str | None = None
    if stale_entries:
        parts = []
        for entry in stale_entries:
            age = entry["age_days"]
            if age is None:
                parts.append(f"{entry['source']} publishes no parseable evaluation date")
            elif age < 0:
                parts.append(f"{entry['source']} is dated {-age} days in the future")
            else:
                parts.append(f"{entry['source']} last published {age} days ago")
        notice = (
            f"Evidence behind {spec.primary_benchmark} may be out of date past the "
            f"{SOURCE_STALE_DAYS}-day window: {'; '.join(parts)}. The ranking may not reflect "
            "current models."
        )
    return {
        "benchmark": spec.primary_benchmark,
        "sources": entries,
        "stale": bool(stale_entries),
        "notice": notice,
    }


#: Pick fields whose value is VERBATIM third-party text rather than a number or an allowlisted
#: identifier. `model` and `vendor` are safe: they come from the canonical registry, so a source can
#: only influence WHICH registered name is chosen, never what the string is. `harness` is different
#: — it is copied out of a leaderboard row, and nothing upstream bounds it.
UNTRUSTED_PICK_TEXT = frozenset({"harness"})

#: Where a third-party string is cut. Far longer than every real harness name in the current
#: artifact; short enough that a hostile leaderboard row cannot push a megabyte through an
#: unauthenticated GET into whatever renders it. Stage 4.0 MINOR-7 — hygiene today, and worth doing
#: now because an iOS client is the next piece of work rather than a distant one.
MAX_UNTRUSTED_TEXT = 120


def _bounded_pick(pick: dict[str, Any]) -> dict[str, Any]:
    """Bound the pick fields that carry third-party text through to the caller."""
    for field in UNTRUSTED_PICK_TEXT:
        value = pick.get(field)
        if isinstance(value, str) and len(value) > MAX_UNTRUSTED_TEXT:
            pick[field] = value[:MAX_UNTRUSTED_TEXT] + "…"
    return pick


#: `Recommendation` fields the envelope RELOCATES rather than repeats. `task` is the answer's
#: `surface`; `budget` belongs to the query, which is one query for all the answers — repeating it
#: per answer would give two copies of one value a chance to disagree.
RELOCATED_FIELDS = ("task", "budget")

#: **The publication allowlist for an UNAUTHENTICATED surface (Stage 4.0 BLOCKING-1).**
#:
#: W1's hand-written dictionary was a drift hazard and W2 was right to kill it — but on a public
#: surface that dictionary was also doing a second job nobody had named: it decided what gets
#: PUBLISHED. Replacing it with an `asdict` passthrough made the default for every future engine
#: field "served to anonymous callers, because nobody excluded it". The parity tests could not see
#: it: they enforce that engine fields REACH the payload, never that only declared ones do.
#:
#: So the two jobs are now separate and both explicit. `recommendation_json` still enumerates
#: nothing — a field added to the engine cannot silently fail to arrive. This set decides whether
#: it is allowed OUT, and `test_no_engine_field_reaches_the_public_surface_undeclared` fails until
#: a human puts a new field in one of the three lists. **Publication is a decision, not a default.**
PUBLIC_ANSWER_FIELDS = frozenset(
    {
        "ranking_effort",
        "sources",
        "eligible_count",
        "frontier_size",
        "close_call",
        "effort_mix_notice",
        "stale_notice",
        "picks",
    }
)

#: Engine fields deliberately WITHHELD from `/v1`. Empty today, and it exists so that withholding
#: one is a recorded decision rather than an omission.
WITHHELD_ANSWER_FIELDS: frozenset[str] = frozenset()

#: **The same decision, one level down (Stage 4.0 re-review RR-BLOCKING-1).** `picks` is a single
#: allowlisted key whose value is the recursive serialization of every `Pick` — nineteen more
#: fields, and the first version of this fix filtered none of them. The finding it was closing had
#: named both halves in its own narration ("all nineteen `Pick` fields and all ten `Recommendation`
#: fields") and the fix restored the allowlist for the ten. An allowlist that stops at the top level
#: of a nested document is not an allowlist; it is a lid on one drawer.
PUBLIC_PICK_FIELDS = frozenset(
    {
        "label",
        "model",
        "vendor",
        "score",
        "metric",
        "secondary_score",
        "blended_per_m",
        "input_per_m",
        "output_per_m",
        "evidence_date",
        "harness",
        "effort",
        "higher_effort",
        "higher_effort_score",
        "effort_note",
        "confidence",
        "confidence_basis",
        "why",
        "trade_off",
    }
)

#: Pick fields deliberately WITHHELD. Empty today, same reason as above.
WITHHELD_PICK_FIELDS: frozenset[str] = frozenset()


#: Fields a RANKING row publishes. Deliberately smaller than `PUBLIC_PICK_FIELDS`: a ranking row is
#: a model's position in one ordering, while a pick additionally carries WHY the engine chose it
#: (`label`, `why`, `trade_off`), which is meaningless for a row nobody chose. Keeping the sets
#: separate also keeps the payload honest about its own size — up to 44 rows per answer.
PUBLIC_RANKING_FIELDS = frozenset(
    {
        "model",
        "vendor",
        "score",
        "metric",
        "secondary_score",
        "blended_per_m",
        "input_per_m",
        "output_per_m",
        "evidence_date",
        "harness",
        "effort",
    }
)


def _ranking_json(rows: list[RankingRow], spec: CategorySpec) -> list[dict[str, Any]]:
    """The full ranking for one surface, in the ENGINE's order (D-125).

    **The client never re-sorts this** (M8 plan, Trap 1). The order is the engine's answer to one
    question — highest primary-benchmark score first — and a client that re-orders it is answering
    a different question with the engine's numbers.

    Derived from the dataclass rather than enumerated, for the same reason `_answer_json` stopped
    listing nineteen `Pick` fields by hand: a field added to `RankingRow` arrives here whether or
    not anyone remembers this function exists, and the allowlist above decides what is published.
    """
    published = []
    for row in rows:
        raw = {f.name: getattr(row, f.name) for f in fields(row)}
        entry = {k: v for k, v in raw.items() if k in PUBLIC_RANKING_FIELDS}
        # D-109: rounding happens at the OUTPUT BOUNDARY, and this is one. Every other boundary
        # already did it -- recommend.py, rank.py's export, subscribe.py, coverage.py -- and this
        # function, added with D-125, did not. The result was one model appearing TWICE in a single
        # payload with two different scores: 83.5 in `picks` and 83.47107438016529 in `ranking`,
        # rendered on the phone as "83.5 % resolved" directly above "83.471 % resolved". D-109's
        # own rationale names this exact shape. Found by the M8 fresh-eyes review.
        entry["score"] = round_score(entry["score"])
        entry["secondary_score"] = round_optional_score(entry["secondary_score"])
        # The metric is a property of the SURFACE, not of the row, and the client needs it beside
        # every score it renders rather than having to reach back up the payload.
        entry["metric"] = spec.metric
        published.append(_bounded_pick(entry))
    return published


def _answer_json(
    spec: CategorySpec,
    ranking: list[dict[str, Any]],
    rec: Recommendation | None,
    unavailable_reason: str | None,
    source_health_json: dict[str, Any],
) -> dict[str, Any]:
    """One answer: the engine's own serialization, plus the fields only the API knows.

    **Nothing here enumerates an engine field.** The previous version listed all nineteen `Pick`
    fields and all ten `Recommendation` fields by hand; it was correct the day it was written and
    the W1 review killed it by deleting one line, with every test still green. `recommendation_json`
    walks the dataclass, so a field added to the engine arrives here whether anyone remembers it or
    not — and `tests/unit/test_serializer_parity.py` fails if one does not.

    The API's own additions are the ones the engine cannot know: which surface this is, how fresh
    its source is on a wall clock, whether its evidence carries dates, and why it has no picks.
    """
    picks = rec.picks if rec else ()
    dating, dating_note = _evidence_dating(picks)

    if rec is not None:
        # The engine's own serialization, and NOTHING to fall back on. The first version merged
        # the engine over a scaffold of Nones built from the dataclass, which meant a field the
        # serializer dropped was silently replaced by `null` — the W2 fault injection caught it:
        # deleting `close_call` and `effort_mix_notice` left every test green because the scaffold
        # supplied them. A default that hides a missing field is the mirror problem wearing a
        # different hat.
        engine = recommendation_json(rec)
        # Filtered to what this surface DECLARES it publishes, not to what the engine happens to
        # carry. An undeclared field is dropped rather than served, and the citing test fails on it
        # so the drop is loud in CI rather than silent in production.
        engine = {k: v for k, v in engine.items() if k in PUBLIC_ANSWER_FIELDS}
        # ...and the same filter one level down, because `picks` is a door rather than a value.
        engine["picks"] = [
            _bounded_pick({k: v for k, v in pick.items() if k in PUBLIC_PICK_FIELDS})
            for pick in engine.get("picks", [])
        ]
    else:
        # No run happened, so there is nothing to serialize and every engine field is genuinely
        # absent. This scaffold is a statement about an ANSWER THAT DOES NOT EXIST, not a fallback
        # for one that does.
        engine = {
            field.name: [] if field.name == "picks" else None
            for field in fields(Recommendation)
            if field.name in PUBLIC_ANSWER_FIELDS
        }
        engine.update(
            eligible_count=0,
            frontier_size=0,
            sources=[],
            # The caller asked about a surface and the surface has a policy, even with no run.
            # Where a run EXISTS its own value wins — M5's BLOCKING-1, never the policy in place
            # of the evidence.
            ranking_effort=spec.ranking_effort,
        )

    return {
        **engine,
        "surface": spec.id,
        "title": spec.title,
        # D-125: every model the engine ranked for this surface, in its order. Per-answer by
        # construction, so it cannot become a cross-surface leaderboard — Ruling A is untouched.
        "ranking": ranking,
        "primary_benchmark": spec.primary_benchmark,
        "metric": spec.metric,
        "source_health": source_health_json,
        "evidence_dating": dating,
        "evidence_dating_note": dating_note,
        "unavailable_reason": unavailable_reason,
    }


def _utc_today() -> dt.date:
    """The wall clock, in UTC, behind a seam a test can replace.

    The engine's four existing date call sites all take an injectable `today`; this one did not,
    which is why the freshness arithmetic had no way to be tested for its `False` case.
    """
    return dt.datetime.now(tz=dt.UTC).date()


def _answer_for(
    conn: sqlite3.Connection, task: str, budget: str, today: dt.date | None = None
) -> dict[str, Any]:
    """One surface's answer. A surface that cannot answer is DISCLOSED, never dropped.

    Dropping it would tell the caller there is only one coding answer, which is precisely the
    thing Ruling A forbids -- and it would do so most often when the data is thinnest.
    """
    spec = CATEGORIES[task]
    try:
        # UTC, matching every existing call site (`coverage.main`). Local time made the API and
        # the CLI disagree about one database at one instant near the 90-day boundary — measured:
        # local 2026-08-17 while UTC was still 2026-08-16. Two artifacts of one run disagreeing
        # is Trap 1, which this milestone exists to close, not to add to.
        health = _source_health_json(conn, spec, today=today or _utc_today())
    except sqlite3.DatabaseError:
        health = {
            "benchmark": spec.primary_benchmark,
            "sources": [],
            "stale": True,
            "notice": "This surface's evidence could not be read; freshness is unknown.",
        }
    try:
        rec = recommend(conn, budget=budget, task=task)
    except UnbuiltEvidenceError:
        # Defence in depth behind the startup probe, which normally stops the process from booting
        # on an unbuilt artifact. This catches the case where the file is replaced UNDER a running
        # process — the mounted-artifact deploy shape (D-116) makes that a real sequence, not a
        # hypothetical. Re-raised as the same 503 class M6 already uses for an unreadable database,
        # because both are "the server cannot answer", not "the answer is empty".
        raise
    except sqlite3.DatabaseError:
        return _answer_json(spec, [], None, "This surface's evidence could not be read.", health)

    # Computed HERE, and `recommend()` computes it again at `recommend.py:298`. An earlier version
    # of this comment claimed it was "computed ONCE and reused" and that asking twice "is how the
    # two drift" -- both false, and an independent review caught it. They cannot drift: it is the
    # same function against the same connection inside one request, so the two results are the
    # same rows by construction. The real cost is a duplicate query per answer, twice per coding
    # request. Ledgered rather than threaded through `recommend()`, because that is a signature
    # change on the scoring path and this is a comment that was wrong, not a defect that was.
    try:
        ranked = category_ranking(conn, spec)
    except sqlite3.DatabaseError:
        ranked = []
    ranking = _ranking_json(ranked, spec)

    if rec is None:
        # WHY the answer is empty decides whether it is honest, and there are two different
        # reasons. M7-W1's security and code-review seats both found this line attaching the
        # BUDGET explanation unconditionally, including on a surface whose evidence source is
        # absent entirely — where nothing was excluded by budget and the sentence is simply false.
        #
        # One payload then carried two contradictory accounts of itself: `source_health` correctly
        # said "no evidence source is present", and this field said "nothing fits your budget".
        # D-121 permits a degraded build ONLY because the surface discloses a missing source, so a
        # false cause served beside the true one invalidates the ADR rather than inconveniencing
        # it. An evidence engine with no evidence fails CLOSED on the question (V3C-33/45): it says
        # it cannot answer, rather than implying it looked and found nothing.
        # **The predicate asks whether evidence reached the RANKING, not whether rows landed in a
        # table**, and the difference is a finding rather than a refinement. The first version
        # tested `health["sources"]`, which is non-empty as soon as a single row exists under this
        # benchmark — including a row whose model name never reconciled to the registry and so
        # never entered `category_ranking`. The security seat reached that state deliberately: one
        # unreconciled arena row put the surface back on the budget sentence with nothing ranked.
        # `minimum_rows` counts rows STORED, not rows usable, and the build's reconciliation floor
        # is global rather than per-benchmark, so nothing upstream rules the state out.
        if not ranked:
            return _answer_json(
                spec,
                ranking,
                None,
                f"This surface has no evidence to rank: nothing on {spec.primary_benchmark} "
                "reached the ranking in the served database, so no budget was applied. "
                "This is a gap in the evidence, not a result.",
                health,
            )
        return _answer_json(
            spec,
            ranking,
            None,
            "No model on this surface's benchmark fits the requested budget, so this answer "
            "ranks nothing. It is shown rather than hidden.",
            health,
        )
    return _answer_json(spec, ranking, rec, None, health)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness + build identity (L.7).

    A green probe proves the process is *up*, never *which code* it is; the
    `build` stamp closes that gap (one `curl /health | jq .build` vs three
    exec-and-grep checks). Additive fields only; `status` is unchanged.
    """
    return {"status": "ok", "version": APP_VERSION, "build": APP_BUILD}


@app.get(f"/{API_VERSION}/categories")
def categories() -> dict[str, Any]:
    """The rankable surfaces, so a client discovers them instead of hardcoding them."""
    return {
        "categories": [
            {
                "id": spec.id,
                "title": spec.title,
                "primary_benchmark": spec.primary_benchmark,
                "metric": spec.metric,
                "ranking_effort": spec.ranking_effort,
            }
            for spec in CATEGORIES.values()
        ],
        "coding_intent_surfaces": list(CODING_INTENT),
        "surfaces_are_ranked": False,
    }


@app.get(f"/{API_VERSION}/recommendations")
def recommendations(
    task: str = Query(default="coding"),
    budget: str = Query(default="unlimited"),
) -> Any:
    """Ruling A's endpoint: `task=coding` answers on BOTH coding surfaces, neither leading.

    A caller that names one surface explicitly has already chosen, and gets that one alone --
    Ruling A binds the coding INTENT, not every possible request.
    """
    if task not in CATEGORIES:
        return _error(
            400,
            "unknown_task",
            f"unknown task {_echo(task)!r}; expected one of {sorted(CATEGORIES)}",
        )
    if budget not in BUDGETS:
        return _error(
            400,
            "unknown_budget",
            f"unknown budget {_echo(budget)!r}; expected one of {sorted(BUDGETS)}",
        )

    path = _db_path()
    if path is None or not path.is_file():
        # Fail closed, and say nothing about where the file was looked for: a path in an error
        # body is a free map of the host for anyone probing the surface.
        return _error(503, "evidence_unavailable", "The evidence database is not available.")

    surfaces = CODING_INTENT if task == "coding" else (task,)
    try:
        # Direct read-only handle: nothing is copied, because nothing writes.
        conn = open_readonly(path)
    except sqlite3.Error:
        return _error(503, "evidence_unavailable", "The evidence database is not available.")
    try:
        answers = [_answer_for(conn, surface, budget) for surface in surfaces]
    except UnbuiltEvidenceError:
        # REQ-API-008. NOT a 200 with empty picks: an unbuilt artifact means the server cannot
        # answer, which is the `evidence_unavailable` class M6 already defined, not an answer whose
        # result happens to be empty. The remedy stays OUT of the body — the operator finds it in
        # the startup log and in the CLI, and a public error body is not the place to publish what
        # command fixes this host.
        return _error(503, "evidence_unavailable", "The evidence database is not available.")
    finally:
        conn.close()

    return {
        "api_version": API_VERSION,
        "query": {"task": task, "budget": budget},
        "surfaces_are_ranked": False,
        "ordering_note": ORDERING_NOTE,
        "answers": answers,
    }
