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

import datetime as dt
import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.workflows.categories import CATEGORIES, CategorySpec
from app.workflows.coverage import SOURCE_STALE_DAYS, source_health
from app.workflows.recommend import BUDGETS, Pick, Recommendation, recommend

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
app = FastAPI(
    title="model_ranking",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
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


def serving_snapshot(path: Path) -> sqlite3.Connection:
    """A private in-memory copy of the operator's database, for one request to compute against.

    **Why this exists, stated plainly because it is a workaround and workarounds rot when the
    reason is lost.** `recommend()` is a read API that WRITES: `build_price_medians` does
    `DELETE FROM px_median` + `INSERT` on every call (`rank.py:143-170`). M5's closure security
    review already recorded this as NOTE-7 / MINOR-3 — `recommend.main` opens a read-write handle
    *correctly*, because the engine genuinely writes.

    An HTTP surface cannot. Serving from a read-write handle would let an anonymous GET rewrite
    the operator's table, and `schema.connect()` would migrate the file on top of that (W-009).

    So the file is opened READ-ONLY and copied into memory; the engine writes into the copy, which
    is discarded when the request ends. The operator's bytes are never touched — asserted by
    `test_the_api_never_writes_to_the_database`.

    **This does not fix the defect, it contains it.** The real fix is to let the median computation
    run without writing, which is an engine change M6-W1 is not allowed to make (the signed plan:
    "if a route needs the engine to behave differently, that is a finding"). Filed as such.
    """
    source = open_readonly(path)
    try:
        memory = sqlite3.connect(":memory:")
        source.backup(memory)
    finally:
        source.close()
    return memory


def _db_path() -> Path | None:
    """The evidence database, named EXPLICITLY or not at all.

    The W1 security pass: a working-directory-relative default serves the WRONG DATABASE with a
    200 instead of refusing to boot, and a server's CWD is not a thing anyone reviews. There is no
    default. Unset is a fail-closed 503, like every other unusable-evidence condition.
    """
    raw = os.environ.get("MODEL_RANKING_DB", "").strip()
    return Path(raw) if raw else None


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


def _pick_json(pick: Pick) -> dict[str, Any]:
    return {
        "label": pick.label,
        "model": pick.model,
        "vendor": pick.vendor,
        "score": pick.score,
        "metric": pick.metric,
        "secondary_score": pick.secondary_score,
        "blended_per_m": pick.blended_per_m,
        "input_per_m": pick.input_per_m,
        "output_per_m": pick.output_per_m,
        "evidence_date": pick.evidence_date,
        "harness": pick.harness,
        "effort": pick.effort,
        "higher_effort": pick.higher_effort,
        "higher_effort_score": pick.higher_effort_score,
        "effort_note": pick.effort_note,
        "confidence": pick.confidence,
        "confidence_basis": pick.confidence_basis,
        "why": pick.why,
        "trade_off": pick.trade_off,
    }


def _answer_json(
    spec: CategorySpec,
    rec: Recommendation | None,
    unavailable_reason: str | None,
    source_health_json: dict[str, Any],
) -> dict[str, Any]:
    picks = rec.picks if rec else ()
    dating, dating_note = _evidence_dating(picks)
    return {
        "surface": spec.id,
        "title": spec.title_tr,
        "primary_benchmark": spec.primary_benchmark,
        "metric": spec.metric,
        # Read from the RUN, not from the category, even though the two are equal today. This
        # module's own rule two functions up is that a payload publishes what a run produced;
        # reading `spec` here would be the same coupling M5's BLOCKING-1 was.
        "ranking_effort": rec.ranking_effort if rec else spec.ranking_effort,
        "source_health": source_health_json,
        "evidence_dating": dating,
        "evidence_dating_note": dating_note,
        "sources": list(rec.sources) if rec else [],
        "eligible_count": rec.eligible_count if rec else 0,
        "frontier_size": rec.frontier_size if rec else 0,
        "close_call": rec.close_call if rec else None,
        "effort_mix_notice": rec.effort_mix_notice if rec else None,
        "stale_notice": rec.stale_notice if rec else None,
        "unavailable_reason": unavailable_reason,
        "picks": [_pick_json(p) for p in picks],
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
    except sqlite3.DatabaseError:
        return _answer_json(spec, None, "This surface's evidence could not be read.", health)
    if rec is None:
        return _answer_json(
            spec,
            None,
            "No model on this surface's benchmark fits the requested budget, so this answer "
            "ranks nothing. It is shown rather than hidden.",
            health,
        )
    return _answer_json(spec, rec, None, health)


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
                "title": spec.title_tr,
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
    budget: str = Query(default="sinirsiz"),
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
        conn = serving_snapshot(path)
    except sqlite3.Error:
        return _error(503, "evidence_unavailable", "The evidence database is not available.")
    try:
        answers = [_answer_for(conn, surface, budget) for surface in surfaces]
    finally:
        conn.close()

    return {
        "api_version": API_VERSION,
        "query": {"task": task, "budget": budget},
        "surfaces_are_ranked": False,
        "ordering_note": ORDERING_NOTE,
        "answers": answers,
    }
