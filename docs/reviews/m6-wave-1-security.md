# Wave 1 Security Review (m6)

**Reviewer:** Security-Reviewer subagent (fresh eyes — did not author this wave)
**Date:** 2026-08-17
**Risk tier:** MED, with a **pulled-forward** security pass (`docs/plans/m6-plan.md` §3 W1.5, §4 "Effective wave review tiers")
**Source:** A — protected-base `subagent-profiles/Security-Reviewer.md`; no Stage-1 override declared
**Commit range:** `1faaf77..4dc6f53`
**Scope note:** the profile describes this pass at Stage 4.0 closure. This is the per-wave variant the
permission matrix allows for a HIGH-risk slice, scoped to this wave's diff. It does **not** replace the
M6 closure review; it closes `docs/warnings.ledger.md` **W-016 row 4** (F15 — the plan-tagged pass that
disappears quietly).

## Verdict

**BLOCKING**

One BLOCKING finding, six MINOR, seven NOTE.

The read-only serving seam — the thing this wave was most likely to get wrong — is **correct, and I
verified it independently rather than accepting the claim** (NOTE-1, NOTE-2). The error contract leaks
no filesystem path, no stack trace, no SQL fragment, and no host shape; I attacked it and could not make
it. What blocks is the opposite of a leak: the surface **withholds** a disclosure it owes. The project's
own wall-clock source-health model exists, deliberately fails *toward* disclosure, and is **not attached
to the live request path**. On the exact answer where that model says "stale, because this source has no
parseable date at all", `/v1` serves a recommendation with no staleness disclosure of any kind. That is a
safety/disclosure control failing **OPEN** (V3C-33/45), a built-not-wired control (V3C-73), and an
acceptance criterion with no citing test (V3C-02) — three independent BLOCKING triggers on one defect.
A fail-open finding may not be ledgered.

---

## Findings

### BLOCKING

**BLOCKING-1 — `src/app/adapter/main.py:180` (and the absence of any `source_health` call in the
module) — REQ-API-005's "unhealthy source" case is neither wired nor tested, and the disclosure that
*is* wired fails OPEN.** — OWASP A04 Insecure Design / A09 Security Logging and Monitoring Failures —
V3C-73 (built is not wired) + V3C-02 (criterion without a citing test) + V3C-33/45 (safety control
failing open).

REQ-API-005 names **four** cases: unknown task, unknown budget, **an unhealthy source**, and a missing
database. The wave-close checklist (`docs/plans/m6-wave-1-close.md` row 6) maps the third case to
`tests/unit/test_api_v1.py:240` `test_a_surface_that_cannot_answer_is_disclosed_not_dropped`. That test
uses an **empty but schema-valid** database, which exercises `main.py:198-203` (`rec is None`, no model
fits). "No data" is not "unhealthy source". The two conditions are distinct in this codebase and the
project has a dedicated model for the second one.

This project already owns a wall-clock health check: `src/app/workflows/coverage.py:235`
`source_health()`, with `SOURCE_STALE_DAYS = 90` at `coverage.py:43`, and a comment at `coverage.py:66-69`
recording that a prior review hardened it so a source with rows but no parseable date reports
`stale=True` — *"exactly the direction a health check must never fail in."* **`main.py` never imports or
calls it.** Verified: `grep -c coverage src/app/adapter/main.py` is 0, and the module's import block is
`main.py:30-39`.

What *is* wired is `Recommendation.stale_notice`, serialized at `main.py:180`. Its own docstring at
`src/app/workflows/recommend.py:245-252` states the limitation: it is a **relative** proxy — newest
`run_date` on the primary benchmark versus newest `observed_at` anywhere in the same database — and
*"a database that was never re-ingested cannot report itself stale (no wall-clock anchor, by determinism
design)."* That limitation was acceptable for a CLI an operator runs after an ingest. **An HTTP surface
is a process that serves one static file indefinitely**, which is the precise deployment shape in which a
relative-only staleness measure is structurally unable to fire.

Evidence — measured against this wave's own canonical fixture (`tests/unit/test_api_v1.py:81`
`_seeded_db`), today 2026-08-17:

```
today: 2026-08-17   SOURCE_STALE_DAYS = 90
  source_health: SourceHealth(source='epoch_deepswe_external', rows=3,
                              newest_run_date=None, age_days=None, stale=True)
  source_health: SourceHealth(source='swebench', rows=3,
                              newest_run_date='2026-02-26', age_days=172, stale=True)

  GET /v1/recommendations?task=coding
    surface=agentic-coding   stale_notice=None      <-- source_health says stale=True
    surface=coding           stale_notice=<fires>
  fields naming source health or age anywhere in the payload: []
  main.py imports coverage: False
```

**Both** sources are unhealthy by the project's own model. The `coding` answer discloses it only by
accident of the relative proxy. The `agentic-coding` answer — the one whose source is flagged stale
*specifically because it has no parseable date*, the case `coverage.py:66-69` was hardened for — is
served with `stale_notice: null` and no age field anywhere in the envelope.

`evidence_dating: "undated"` (`main.py:113-135`) does not close this. It says *the benchmark publishes no
evaluation dates*. It does not say *this source has gone quiet*. A client receives an answer it cannot
distinguish from one drawn from a board updated yesterday, and it is exactly the answer Ruling A forbids
the product from ranking below the other — so the caller is invited to weigh two answers equally when one
of them rests on evidence the project's own health model would refuse.

**Why BLOCKING and not ledgerable.** The control class is disclosure/safety, not fairness, so it must
fail **CLOSED** (V3C-33/45) and a fail-open finding may never be ledgered. `source_health` is an
implemented, unit-green control not attached to the live request path — an unshipped control under
V3C-73, and the wave-checklist row 6 asserts "built is not wired" was checked. The criterion has no
citing test, which is a standalone GATE under `permission-matrix.md` §11 (V3C-02). And the plan puts this
in W1's slice, not W3's: `docs/plans/m6-plan.md` §3 W1.3 reads *"The error contract and its four cases."*

**Remedy shape (not prescriptive on the wire format).** Call `source_health()` on the serving snapshot,
and either (a) refuse the answer for a stale source under the existing `unavailable_reason` /
`_error` contract, or (b) carry an explicit per-answer source-health disclosure that fires on
`stale=True` including the `age_days is None` case. Add the citing test REQ-API-005's third case has
never had, and make it enter through `TestClient` per V3C-73. Whichever is chosen, freeze it: it is a
`/v1` envelope field and therefore a K.8 shared-contract addition under `m6-plan.md` §4.

---

### MINOR

**MINOR-1 — `src/app/adapter/main.py:58` — the shipped surface has four anonymous GET routes the plan
never declared, and two of them execute unpinned third-party JavaScript.**
`FastAPI(title=..., version=...)` enables the documentation routes by default. Enumerated from the live
app:

```
/openapi.json         {GET, HEAD}
/docs                 {GET, HEAD}
/docs/oauth2-redirect {GET, HEAD}
/redoc                {GET, HEAD}
/health               {GET}
/v1/categories        {GET}
/v1/recommendations   {GET}
```

REQ-API-001 freezes the surface as three routes. Seven ship. `/docs` and `/redoc` return `text/html`
that loads, with **no Subresource Integrity and at floating major-version tags**:
`cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js`,
`cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css`,
`cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js`, plus `fonts.googleapis.com` and
`fastapi.tiangolo.com`. The served bytes can change without any change to this repository — a
supply-chain dependency that no manifest records and `pip-audit` cannot see.

MINOR rather than BLOCKING because the origin holds nothing worth stealing today: no cookies, no auth,
no session, no secrets, and `/v1` data is public. It is nonetheless a default-deny miss —
`permission-matrix.md` §3 makes a production external call ASK-gated and routes it through `clients/`
(D-001 / K.1), and this ships one in an HTML page. The sharp part: `tests/unit/test_api_v1.py:177`
`test_no_mutating_route_exists` **iterates `app.routes`** and therefore had this exact list in hand.
It asked only "is anything mutating?" and never "is this the surface we declared?"
Fix: `FastAPI(..., docs_url=None, redoc_url=None, openapi_url=None)` in the served profile, or an
explicit ADR that the docs routes are part of the frozen surface; and extend the route test to assert the
route **set**, not just the method set.

**MINOR-2 — `src/app/adapter/main.py:249` and `:253` — unbounded raw attacker input is reflected into
the error body, and a citing test now freezes that behaviour.**
`f"unknown task {task!r}; ..."` and `f"unknown budget {budget!r}; ..."` echo the raw query value.
Measured, all `400` with `content-type: application/json`:

```
task=<script>alert(1)</script>   -> "unknown task '<script>alert(1)</script>'; expected one of [...]"
budget=' OR 1=1--                -> "unknown budget \"' OR 1=1--\"; expected one of [...]"
task=A*4000                      -> all 4000 characters echoed
task=a\x00b                      -> "unknown task 'a\\x00b'; ..."
```

No path, no stack, no SQL fragment — REQ-API-005's stated prohibition holds. But no response carries
`X-Content-Type-Options: nosniff` (measured headers are `content-length` and `content-type` only), the
same origin also serves `text/html` at `/docs` (MINOR-1), and the amplitude is capped only by the HTTP
server's request-line limit, never by the application. The consumer this milestone exists for is an iOS
client that will render `error.message` verbatim, so this is an injection hazard handed downstream, not
just a reflected-content note.
It is also **contract-frozen**: `tests/unit/test_api_v1.py:211` asserts `"nope" in body["error"]["message"]`,
so the echo cannot be removed without editing an acceptance test. Fix: return the closed vocabulary
without the input, or truncate and escape, and relax that assertion to the error `code`.

**MINOR-3 — `src/app/adapter/main.py:75-101` `serving_snapshot` — an anonymous GET allocates a full
copy of the operator's database in memory, with no cap, no cache and no rate limit.**
`docs/warnings.ledger.md` **W-017** ledgers this as a *cost* — *"Its cost grows with the database size"* —
ACCEPTED, owning milestone M6-W3. That framing is incomplete for a network surface: it names neither
concurrency nor the trigger. Measured, on an operator database inflated to a realistic 51 MB:

```
single request                       0.055 s      -> 200
20 concurrent requests               1.53 s, all 200, delta maxrss = 1115 MB
10 snapshots held open (1.0 MB db)   delta maxrss = 11.8 MB
```

Memory is `concurrency x db_size x ~1.1`, driven by a ~120-byte unauthenticated request — roughly a
450,000x amplification. Under uvicorn's default 40-slot sync threadpool a 51 MB database peaks near
2 GB. The current operator databases are ~1.0 MB (`advisor.db`, `owner_advisor.db`), so this is **not
exploitable at meaningful scale today**, which is why it is MINOR and not BLOCKING, and why it may be
ledgered: rate-limiting is the fairness class and correctly fails OPEN, so no fail-direction rule is
violated.
Two conditions, both concrete. (a) **W-017's row must be amended** to state the vector, not only the
cost — as written, W3 could remove the engine write, close W-017, and leave an unbounded per-request
copy in place. (b) This must be bounded **before Stage 4.3 deploy** — a concurrency cap, a shared
read-only snapshot with an explicit refresh, or a reverse-proxy rate limit. It becomes BLOCKING at the
deploy gate, not at this wave's close.

**MINOR-4 — `src/app/adapter/main.py:195-196`, `:260`, `:266` — every fail-closed path is silent
server-side. No log line, no correlation ID (V3C-103).**
Measured with `logging.basicConfig(level=DEBUG)`: a `503` produced **no** application log record, only
the test client's own HTTP line. `except sqlite3.DatabaseError` at `:195-196` swallows the exception
entirely and returns `200` with a fixed sentence. The baseline's v3.5 clause requires the
operator-actionable reason server-side and an opaque correlation ID in the unauthenticated response,
with the acceptance bar *"an operator distinguishes not-ready from dead in one command."* Today three
very different states — file absent, file unreadable, schema wrong — are indistinguishable to both the
caller (correctly) **and** the operator (incorrectly). Confirmed: a foreign-but-valid SQLite file returns
`200` with a prose `unavailable_reason` and no record anywhere that the operator's database has the
wrong schema.
Compounding: coverage shows `main.py:195-196` and `:265-266` are **not exercised by any test in the
wave** (`93%`, missing `131, 195-196, 265-266`). Both are error branches.

**MINOR-5 — `src/app/adapter/main.py:108-110` versus the framework defaults — three error shapes ship
on one surface, and the third one echoes raw input.**
Measured: the handler emits `{"error":{"code","message"}}`; Starlette emits `{"detail":"Not Found"}` on
`404` and `{"detail":"Method Not Allowed"}` on `405`; an unhandled exception emits `text/plain`
`Internal Server Error` (correct — `app.debug` is `False`, verified, and no stack reaches the body). No
`exception_handler` is registered for `HTTPException` or `RequestValidationError`.
`RequestValidationError` is currently **unreachable** because both parameters are bare `str`
(`main.py:239-240`) — I could not trigger a `422`. It becomes reachable the moment W2 or W3 adds one
typed or constrained query parameter, and FastAPI's default handler then emits a body the frozen error
contract never approved, echoing the raw value:

```
{"detail":[{"type":"int_parsing","loc":["query","limit"],
            "msg":"Input should be a valid integer, unable to parse string as an integer",
            "input":"../../etc/passwd"}]}
```

(Proved on a throwaway probe app in scratchpad; no project file was modified.) `m6-plan.md` §4 freezes
"the error body shape" as a public contract, so register the handlers now, while it costs three lines.

**MINOR-6 — `src/app/adapter/main.py:105` — the default database path is *relative*, and nothing
validates it at startup.**
`Path(os.environ.get("MODEL_RANKING_DB", "pipeline.db"))` resolves against the **process working
directory**. No file named `pipeline.db` exists in this repository (the real ones are `advisor.db`,
`live.db`, `owner_advisor.db`), so on defaults the surface serves `503` forever — fail-closed, which is
right. The residual risk is the other direction: a deployment started from an unexpected directory
serves whatever `./pipeline.db` happens to be, silently and with a `200`. This is the concrete cost of
deferring V3C-51 (see the deferral judgement below), and the cheapest fix is to require the variable
rather than default it.

---

### PASS — observations of good security hygiene

- **`open_readonly` (`main.py:61-72`) is right, and INV-23 holds under attack.** I tried the `?`-in-path
  case the docstring claims to have fixed: `Path("/tmp/.../weird?name.db").resolve().as_uri()` yields
  `file:///.../weird%3Fname.db`, so appending `?mode=ro` cannot be swallowed. Request served `200`; no
  stray database was created next to it. `test_read_only_handle_refuses_a_write`
  (`tests/unit/test_api_v1.py:280`) proves the seam itself, not just its effect.
- **The read-only claim is true, verified independently.** Across five requests on a 1.0 MB copy of the
  real `advisor.db`: SHA-256 identical, `st_mtime_ns` identical, and **no `-wal`, `-shm` or `-journal`
  sidecar created**. Repeated against a WAL-mode database with a hot uncommitted `-wal`: served `200`,
  directory contents unchanged. This is the one thing the wave most needed to be right about.
- **V3C-12 satisfied by proven absence, and I verified the absence rather than the claim.** A grep for
  `@app.post|put|patch|delete`, `APIRouter`, `add_api_route`, `include_router` and `mount(` across all of
  `src/` returns **zero** hits, and `main.py` is the only file in `src/` mentioning `FastAPI` at all.
  Live enumeration of `app.routes` confirms every route is `GET`/`HEAD`, including the four undeclared
  ones in MINOR-1. `POST /v1/recommendations` returns `405`.
- **The error contract leaks nothing it was told not to leak.** Missing database, unreadable database
  (mode `0o000`), a directory, a FIFO, and 1.4 KB of non-SQLite bytes all return the identical
  `503 {"error":{"code":"evidence_unavailable","message":"The evidence database is not available."}}`.
  No path, no `errno`, no SQLite message, no `Traceback`. The `500` path returns `text/plain`
  `Internal Server Error` with `app.debug` false.
- **No SQL injection reachable from `task` or `budget`.** Both are checked against closed vocabularies
  before use (`main.py:247`, `:251`); `task` then reaches only `CATEGORIES[...]` and `get_category()`
  (`categories.py:78-84`, a dict lookup). Every query on the serving path is parameterised —
  `rank.py:133-137`, `rank.py:163-168`, `recommend.py:253-257`. Neither value reaches the filesystem: the
  only path input is the operator's environment variable.
- **The disclosure discipline this project is built on survives contact with the API.** A surface that
  cannot answer is served with `picks: []` and a reason rather than dropped (`main.py:190-203`), which is
  the correct direction — and it is exactly why BLOCKING-1 stands out as the one place the surface goes
  quiet instead.
- **Concurrency is clean.** 20 simultaneous requests: all `200`, zero exceptions, no cross-thread SQLite
  errors, database bytes unchanged. Each connection is created, used and closed inside one threadpool
  thread (`main.py:264-270`, `finally: conn.close()`).
- **Secrets and dependencies.** `gitleaks git --log-opts=1faaf77..4dc6f53` — **no leaks found**.
  `gitleaks dir` on both wave files — clean. No `.env` in the diff. The diff adds **no third-party
  import**: every new import is stdlib, `fastapi` (already `fastapi>=0.115` in `pyproject.toml:11`), or
  first-party `app.*`. No slopsquat surface.
- `make lint` / `mypy` clean on both wave files; `pytest tests/unit/test_api_v1.py` — **13 passed**.

---

## The deferral judgement the plan asked for

`docs/plans/m6-plan.md` §2 REQ-API-006 carries four clauses. Two shipped early in this wave, two are
planned for W3. Asked whether deferring them is safe for a surface that exists **now**:

**CORS (V3C-13) — SAFE to defer, and deferring is currently *safer* than implementing.** There is no
CORS middleware anywhere in `src/` (grep for `cors`, `allow_origins`, `middleware`: zero hits), so the
browser same-origin policy denies every cross-origin read by default. That is the default-deny posture
the baseline wants. Two conditions on W3, both cheap to get wrong: (a) W3 must not satisfy "the CORS
clause" by adding `allow_origins=["*"]` and calling it configured — a permissive allowlist would be
strictly worse than today's absence, and it would then be frozen as `/v1` contract; (b) whatever W3 adds
must never pair a wildcard with `allow_credentials=True`, which is the BLOCKING combination in
`permission-matrix.md` §11.

**Startup validation (V3C-51) — SAFE to defer, with one named cost.** There is nothing
security-critical to validate yet: the process reads exactly two environment variables, `APP_BUILD`
(`main.py:43`, a build stamp, intentionally public via `/health` per L.7) and `MODEL_RANKING_DB`
(`main.py:105`). No auth secret, no key, no TLS material, no enforcement flag — so there is no insecure
value to silently default to, and every configuration failure I could construct resolves to a `503`,
which is fail-closed. The cost is MINOR-6: without a boot check, a wrong working directory is discovered
by serving wrong data with a `200`, not by refusing to start. Deferring the *validator* is fine;
making the database path **required rather than defaulted** should not wait for W3, because it is a
one-line change that converts a silent-wrong-data mode into a loud one.

**Already shipped ahead of plan, and correct:** "the API's database handle is opened read-only"
(`main.py:61-72`, verified above) and "no plaintext credential exists in source" — there is no credential
of any kind in this diff, and none in the module.

---

## Gates passed

- [x] Secret scan green — `gitleaks git --log-opts="1faaf77..4dc6f53"`: **1 commit scanned, no leaks found**.
      `gitleaks dir` on `src/app/adapter` and `tests/unit/test_api_v1.py`: clean. **Not suppressed and
      recorded, per the no-agent-suppression rule:** a repo-wide `gitleaks dir .` still reports 2
      pre-existing `generic-api-key` findings in `docs/reviews/m2-security-review.md:8` and
      `docs/reviews/m4-security-review.md:310`. These are the known **W-001** false positive (an ADR
      label following the word "APIs"), they are outside this wave's diff, and they remain the owner's
      open decision.
- [ ] pip-audit green — **NOT RUN, NO-ENVIRONMENT.** `pip-audit` is declared at `pyproject.toml:32` but
      is not installed in `.venv`. Recorded rather than assumed: the wave adds **zero** new
      dependencies, so this wave changes nothing pip-audit would see, but I did not confirm the Stage-2
      result and there is no `.claude/last-check.log` in the tree to confirm it from.
- [x] Slopsquat check green — no new third-party import in the diff (full `+import` list reviewed).
- [ ] Default-deny preserved for new external surfaces — **NO.** MINOR-1: four undeclared anonymous GET
      routes ship, two of them loading unpinned third-party JavaScript.
- [x] Permission-matrix not violated — no destructive operation, no `git reset`/`push --force`/`rm -rf`,
      no `DROP TABLE`, no migration, no auth/PII/payment/crypto path in the diff. No `⛔`-glob touch.
      MINOR-1 is an ASK-gated §3 external call, flagged rather than treated as a violation.
- [x] Prompt-injection hygiene — N/A and verified so: no `eval`/`exec`, no LLM call, no prompt
      construction, no fetched or user-supplied document consumed. `task` and `budget` are matched
      against closed vocabularies, never interpreted.
- [x] Auth/PII human-review trigger — did not fire. There is no authentication, no session, no
      credential, no PII field, and no mutating route on this surface; nothing in the diff touches an
      auth/PII/payment/migration path.
- [ ] SAST — **NOT RUN, NO-ENVIRONMENT.** Neither `bandit` nor `semgrep` is installed and neither is a
      declared dependency of this project. Substituted with the manual attack pass recorded above
      (input reflection, error-path enumeration, filesystem and URI handling, concurrency, memory,
      route enumeration). Recorded as a gap, not as a pass.
- [x] **Control-class fail direction (V3C-33/45)** — walked; **one violation, BLOCKING-1.**

### Fail-direction table (every failure path on this surface)

| Path | file:line | Class | Direction | Correct? |
|---|---|---|---|---|
| Unknown `task` | `main.py:247-250` | validation / safety | `400`, CLOSED | yes |
| Unknown `budget` | `main.py:251-254` | validation / safety | `400`, CLOSED | yes |
| Database file absent | `main.py:257-260` | availability | `503`, CLOSED | yes |
| Database unopenable or corrupt | `main.py:264-266` | availability | `503`, CLOSED | yes |
| Per-surface `sqlite3.DatabaseError` | `main.py:195-196` | disclosure | `200` + reason, asserts nothing | yes (content-closed) |
| No model fits the budget | `main.py:198-203` | disclosure | `200` + reason | yes |
| Unhandled exception | framework | availability | `500`, generic, CLOSED | yes |
| **Source unhealthy per `source_health`** | **not implemented** | **disclosure / safety** | **`200`, served as current — OPEN** | **NO — BLOCKING-1** |
| Rate limiting | not implemented | fairness | absent (would fail OPEN) | acceptable class; see MINOR-3 |

**Disable switches:** none exist on this surface, and none is required — there is no control here with an
off position. The read-only serving seam is unconditional (`main.py:95`), which is the correct shape: it
has no bypass to test.

---

## Acceptance criteria evidence

| REQ | Status | Evidence (file:line) |
|---|---|---|
| REQ-API-001 (read-only surface, no mutating route) | **PASS with MINOR-1** | Routes `main.py:207`, `:218`, `:237`. Absence proven by `tests/unit/test_api_v1.py:177` `test_no_mutating_route_exists` + my independent grep across all of `src/` (zero mutating decorators, zero routers). MINOR-1: the shipped route **set** is larger than the declared one. |
| REQ-API-002 (two coding answers, nothing ranks them) | PASS (security-relevant part only) | `main.py:50` `CODING_INTENT`, `:262`, `:272-278`; `tests/unit/test_api_v1.py:123` walks every key at every depth against `PRECEDENCE_FIELDS`. No security defect; plan-compliance is the Code-Reviewer's call. |
| REQ-API-004 (undated evidence disclosed in the answer) | PASS | `main.py:113-135` derives dating from the picks actually served, never from category policy; `tests/unit/test_api_v1.py:145`. Correctly resists the M5 BLOCKING-1 shape. |
| **REQ-API-005 (error contract, four cases)** | **BLOCKING** | unknown task -> `main.py:247-250` / test `:204`. unknown budget -> `main.py:251-254` / test `:214`. missing database -> `main.py:257-260` / test `:221`. **unhealthy source -> no implementation, no citing test.** The mapped test (`:240`) covers an empty database, a different condition. See BLOCKING-1. |
| REQ-API-005 (no path in the response body) | PASS | `main.py:108-110` `_error` carries only `code` + `message`; test `tests/unit/test_api_v1.py:221` asserts the path and `Traceback` are absent; independently re-attacked with five bad-database shapes, all identical `503`. |
| REQ-API-006 (database handle read-only) — early | PASS | `main.py:61-72` + `:75-101`; tests `:266`, `:280`; independently verified byte-, mtime- and sidecar-identical, including under WAL. |
| REQ-API-006 (no plaintext credential) | PASS | No credential of any kind in `main.py`; gitleaks clean on the range. |
| REQ-API-006 (CORS, startup validation) | Deferred to W3 as planned | Judged safe to defer, with the two named conditions above. |

---

## Risks queued

1. **BLOCKING-1 must be fixed in a W1 mini-fix-wave**, not carried. It is a fail-open, and a fail-open
   may not be ledgered. Its citing test must enter through `TestClient` (V3C-73).
2. **`docs/warnings.ledger.md` W-017 needs an amendment** naming the vector — unauthenticated,
   unbounded, `concurrency x db_size` — not only the cost. As written, W3 can close it by fixing the
   engine write while leaving the per-request copy unbounded.
3. **MINOR-3 becomes BLOCKING at Stage 4.3.** No deploy of this surface without a concurrency cap, a
   shared snapshot, or a proxy rate limit.
4. **MINOR-5 before W2/W3 adds any typed query parameter** — the `422` shape is one parameter away from
   shipping, and `m6-plan.md` §4 freezes the error body as public contract.
5. **MINOR-1 needs a decision, not a default**: disable the docs routes in the served profile, or ADR
   them into the frozen surface. Either way, extend `test_no_mutating_route_exists` to assert the route
   **set**.
6. **W3 must not satisfy the CORS clause with a wildcard.** Flagged now because a permissive allowlist
   would be worse than today's absence and would freeze as contract.
7. **`pip-audit` and a SAST tool are not installed.** Two gates in this profile's checklist have no
   runner in this environment. Under `V4C-13` this is a control with no runner, recorded not hidden.
8. **`main.py:247`** carries a latent fragility, not a defect: `task != "coding" and task not in
   CATEGORIES` special-cases the literal `"coding"` as always valid. If `CATEGORIES` ever loses or
   renames that key, `main.py:192` `CATEGORIES[task]` raises `KeyError` and the route turns `500`.
   Cheap fix: validate against `CATEGORIES` alone.

---
---

# RE-REVIEW — fix delta (m6 W1)

> **This is a new section appended on 2026-08-17. Everything above is the original record and has
> not been edited.** All `file:line` citations *below this line* refer to the **working tree**
> (uncommitted); citations *above* this line refer to `4dc6f53`. Line numbers moved — the same
> defect may carry two different numbers in the two halves of this document.

**Reviewer:** Security-Reviewer subagent (same reviewer; did not author the fix)
**Date:** 2026-08-17
**Delta reviewed:** `git diff 4dc6f53 -- src tests` — `src/app/adapter/main.py` +140/-13,
`tests/unit/test_api_v1.py` +203/-32; working tree, nothing committed
**Risk class:** inherited from the bug it fixes (V4C-50) — the delta touches the disclosure path
that was failing open, so this pass is mandatory before W1 closes

## Re-review verdict

**BLOCKING**

**BLOCKING-1 is NOT closed.** It is materially *narrowed* — the wall clock is genuinely wired, the
undated case and the absent-source case now fail closed, and four of the five things I asked for
landed correctly. But the block stands, for two reasons, and the first is the one the coordinator
himself suspected:

- **BLOCKING-1a (carried, not closed)** — the health block is keyed on `spec.primary_source`, which
  is not the source the answer was served from. I built the case and it fails **open**, now with an
  affirmative false number rather than a silence.
- **BLOCKING-2 (new — introduced by the fix)** — a database whose newest evaluation date is in the
  **future** reports `stale: false` with a negative `age_days`. The fix wired a control that had a
  pre-existing fail-open branch, and that branch is now reachable from an anonymous GET.

Answering the coordinator's framing directly: **this cannot ship as a stated limitation.** A stated
limitation is the right instrument for a *missing* number. What ships here is a **wrong** number —
machine-readable `"stale": false` over evidence 800 days old — and a limitation recorded in a
docstring does not travel with the JSON to the client that renders it.

New tally for this delta: **2 BLOCKING · 3 MINOR · 4 prior findings confirmed CLOSED · 1 claimed
remediation that is not in the tree.**

---

## Status of every finding from the original pass

| Original | Status | Evidence |
|---|---|---|
| **BLOCKING-1** fail-open staleness | **NOT CLOSED** — narrowed, still fails open | BLOCKING-1a below |
| **MINOR-1** 7 routes vs 3 | **CLOSED** | `main.py:64-75`; shipped route set is exactly `{/health, /v1/categories, /v1/recommendations}`; `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` all return `404`. CDN JavaScript is gone with them. |
| **MINOR-2** unbounded reflection + no nosniff | **CLOSED (with a caveat)** | `main.py:141-143` `_echo`; a 5000-character `task` yields a 115-character message with a visible ellipsis, and quote/backslash flooding yields 135. `nosniff` present on `200`/`400`/`404`/`405`/`/health`. Caveat: MINOR-9. |
| **MINOR-3** DoS amplification | **OPEN as agreed** — but see the tree discrepancy below | Not fixed (correct; W3 owns the engine write). |
| **MINOR-4** silent fail-closed, no logging | **OPEN, and slightly worse** | Still no log line, no correlation ID on any fail-closed path. The delta adds a *new* untested error branch — MINOR-10. |
| **MINOR-5** three error shapes / latent 422 | **OPEN as agreed, and I confirm the assessment** | Both params are still bare `str` (`main.py:365-366`); I could not reach a `422` — every malformed attempt returns `400`. It remains one typed parameter away. |
| **MINOR-6** CWD-relative default DB path | **CLOSED** | `main.py:130-138` returns `None` when unset; `main.py:381` fails closed to `503`. The stay-green mutant and its mandatory new test are the right shape. |
| **NOTE-8** `task != "coding"` special case | **CLOSED** (unasked, and correct) | `main.py:361` is now `if task not in CATEGORIES`. |

### One claimed remediation is not in the working tree

The message states: *"I rewrote the W-017 ledger row to name it as a vector rather than as cost,
per your finding, and to record that it becomes BLOCKING at Stage 4.3."* **That edit is not
present.** `git status --porcelain -- docs` shows `docs/warnings.ledger.md` **unmodified**, and
`docs/warnings.ledger.md:14` still reads *"Its cost grows with the database size."* with no mention
of concurrency, no mention of the trigger, and no Stage-4.3 escalation (`grep "Stage 4.3"
docs/warnings.ledger.md` returns nothing). `docs/decisions.md` **is** modified — D-115 landed, and
it is a good ADR — so the edit most likely went astray rather than being skipped.

I flag it because this is the F15 shape at one remove: a remediation reported as done, believed
done, and therefore never re-checked. Not a finding against the code; a finding against the record.
MINOR-3 stays open with its original escalation clause intact and unrecorded.

---

## New findings

### BLOCKING

**BLOCKING-1a — `src/app/adapter/main.py:197` — the health block is keyed on
`spec.primary_source`, which is not the source the answer was served from. The control still fails
OPEN, and now does so with an affirmative false claim.** — OWASP A04 Insecure Design — V3C-33/45.

The coordinator named this as the case he was least sure of. It is real, it is reachable, and it is
the same defect as BLOCKING-1 displaced by one level.

`main.py:197` does
`{h.source: h for h in source_health(conn, today=today)}.get(spec.primary_source)`.
Three facts make that the wrong key:

1. **`primary_source` is documented as not being a health key.** `src/app/workflows/categories.py:23`
   annotates the field: *"informational; health flags live on ingest reports (not persisted yet)."*
   The fix promoted an explicitly informational field into the join key of a safety control.
2. **The ranking does not filter by source.** `src/app/workflows/rank.py:173-235` `category_ranking`
   selects `WHERE benchmark = :primary AND metric = :metric`, with **no source predicate**, and
   breaks ties with `ORDER BY s.run_date DESC, s.harness ASC, s.source ASC`. The served row's source
   is whichever source published the winning score — recorded as `RankingRow.evidence_source`
   (`rank.py:105`, assigned at `rank.py:247`).
3. **A second source for that benchmark already exists as a first-class citizen.**
   `rank.py:52` registers `"epoch_swe_bench_verified"` in `SOURCE_ATTRIBUTION`, next to
   `"epoch_deepswe_external"` at `rank.py:53`, and `rank.py:57-70` `secondary_evidence_sources`
   does `SELECT DISTINCT source FROM scores WHERE benchmark = ?` — the codebase's own model is that
   **one benchmark has many sources.** `coding` names only one of them.

**Constructed and measured.** Fixture: the wave's own `_seeded_db`, with `swebench` rows re-dated
to 5 days old (fresh) and a parallel set of `epoch_swe_bench_verified` rows for the same benchmark
at `+5.0` score and `2024-06-08` (800 days old), so Epoch wins `best_primary`:

```
GET /v1/recommendations?task=coding   ->  200
  source_health : {"source":"swebench","rows":3,"newest_evaluation_date":"2026-08-12",
                   "age_days":5,"stale":false,"notice":null}
  stale_notice  : None
  picks[].evidence_date : ['2024-06-08', '2024-06-08', '2024-06-08']
  sources       : ['Pricing data: BerriAI/litellm ...', 'Epoch AI, AI Benchmarking Hub ...']

  actual winning rows: ('epoch_swe_bench_verified', '2024-06-08', 3)
  source_health() itself says: [('epoch_swe_bench_verified', 800, True), ('swebench', 5, False)]
```

Every pick's `evidence_date` is 2024-06-08. The attribution block carries the **Epoch** citation —
because `recommend.py:364-367` builds it from `{r.evidence_source for r in rows}`, the true set. The
engine, asked directly, reports `epoch_swe_bench_verified` as 800 days stale. **The payload
nonetheless states `"stale": false`, `"age_days": 5`.**

**The single payload now contradicts itself:** `sources` says the evidence came from Epoch;
`source_health.source` says `swebench`. That is the Trap 1 / M5 BLOCKING-1 shape this project has
already paid for twice — two renderings of one run disagreeing — except both renderings are inside
the *same* JSON object this time.

**Why this is worse than the defect it replaced,** and why it must not ship as a stated limitation:
the original BLOCKING-1 served `stale_notice: null`, the *absence* of a claim. This serves
`"stale": false` — a positive, machine-readable assertion of freshness over 800-day-old evidence. A
client that renders `stale == false` as "current" is now actively misled rather than merely
uninformed. Failing open with a number is worse than failing open with a silence.

**Reachability, stated honestly.** The current operator databases do not trigger it: `advisor.db`
and `owner_advisor.db` both hold `SWE-bench Verified` from `swebench` only, so today the key and
the truth coincide. This is **one ingest run** from being live, not a synthetic edge case — the
Epoch SWE-bench source is already registered, already attributed, and already has an ingest path.

**Remedy, and it needs no engine change** (so W1's "no engine change" constraint is not a reason to
defer). The adapter can ask the same question `secondary_evidence_sources` already asks:
`SELECT DISTINCT source FROM scores WHERE benchmark = ?`, take the health of **every** source
publishing this surface's primary benchmark, and report the block stale if **any** of them is
stale. That over-discloses, which is the correct direction, and it is strictly more truthful than
today's single wrong key. (The precise fix — reporting health for exactly
`{r.evidence_source for r in rows}`, which `recommend.py:364` already computes — would need that
set exposed on `Recommendation`; additive, but engine work, so it belongs to W3. Do the
benchmark-wide version now.)

---

**BLOCKING-2 — `src/app/workflows/coverage.py:253`, newly reachable through
`src/app/adapter/main.py:197` — evidence dated in the FUTURE is reported healthy.** — V3C-33/45
(safety control failing open) — **introduced by this fix**, in the sense that the fix is what
attached this branch to the network.

`coverage.py:253` reads `stale = age > window_days if age is not None else rows > 0`. A future date
yields a **negative** `age`, which is not `> 90`, so `stale` is `False`. Measured, with the newest
`run_date` set 400 days ahead:

```
{"source":"swebench","rows":3,"newest_evaluation_date":"2027-09-21",
 "age_days":-400,"stale":false,"notice":null}
```

The function's own comment at `coverage.py:66-69` records that a prior review hardened exactly this
line so that an *unknown* age reports stale — *"exactly the direction a health check must never
fail in."* That reasoning covered `None` and never covered *negative*. Impossible data is an error
condition, and this control answers an error condition with "healthy".

Not attacker-controlled — it needs a bad upstream date or a skewed clock on the ingesting host, not
a crafted request. It is BLOCKING anyway because `permission-matrix.md` §11 makes fail-direction
misapplication categorical and a fail-open may not be ledgered, and because until this delta the
branch was CLI-only: **the fix is what made a latent engine fail-open into a network-facing one.**
That is the direct answer to "did the wall clock introduce anything" — yes, this.

**Remedy, one line, in the adapter, no engine change:** treat `age_days is not None and age_days < 0`
as stale with its own notice ("this source's newest evaluation date is in the future; its age
cannot be established"). Fixing `coverage.py:253` itself is the better long-term move and belongs
to W3 with the rest of the engine work.

---

### MINOR

**MINOR-8 — `src/app/adapter/main.py:296` — the API reads a LOCAL-timezone wall clock while the
`coverage` CLI reads UTC, so the two can disagree about the same database at the same instant.**
`main.py:296` calls `dt.date.today()` (local). `src/app/workflows/coverage.py` `main()` calls
`dt.datetime.now(tz=dt.UTC).date()`. Measured on this host, right now:

```
local date 2026-08-17   |   UTC date 2026-08-16   |   equal: False
```

At the 90-day boundary that is a `stale` flag of `True` in one artifact and `False` in the other,
for one database, at one instant — the same two-renderings-disagree shape as Trap 1, and the same
one the `--today` flag exists to keep deterministic in tests and CI. It also makes the served number
depend on the deploy host's timezone, which no deploy artifact records. Fix is one expression:
`dt.datetime.now(tz=dt.UTC).date()`. (The boundary itself is `> 90`, so exactly 90 days reads
fresh — verified at 89/90/91; that matches the CLI and is fine.)

**MINOR-9 — `src/app/adapter/main.py:80-84` — the `nosniff` middleware does not cover the `500`,
and `test_responses_forbid_content_type_sniffing` asserts less than it claims.**
Starlette's `ServerErrorMiddleware` sits outside user middleware, so an unhandled exception bypasses
`_no_sniff` entirely. Measured: `200`, `400`, `404`, `405` and `/health` all carry
`x-content-type-options: nosniff`; the `500` carries **none**, with `content-type:
text/plain; charset=utf-8`.
Exploitability is nil — the `500` body is the fixed string `Internal Server Error`, it echoes no
input, and I re-confirmed it leaks nothing even when the exception message contains a filesystem
path. The finding is that the guard's *claim* is broader than its coverage: the docstring says
"never let a browser guess otherwise" and the test checks two statuses. Fix: register the header in
an `exception_handler`/`ServerErrorMiddleware` as well, or narrow the claim and extend the test to
assert the `500` explicitly.

**MINOR-10 — `src/app/adapter/main.py:297-306` — the fix adds a new fail-closed error branch with
no citing test.** Coverage on the delta is `93%`, missing `169, 297-298, 308-309, 383-384`. Lines
`297-298` are the *new* `except sqlite3.DatabaseError` wrapper around `_source_health_json`;
`308-309` and `383-384` are the two pre-existing error branches MINOR-4 already named. I exercised
`297-298` by hand — a valid-SQLite-but-foreign-schema database returns
`{"source":"epoch_deepswe_external","rows":0,"stale":true,"notice":"This surface's evidence source
could not be read; freshness is unknown."}`, which is **correct and fails closed** — but nothing in
the suite asserts it. This is the same V3C-02 shape as the original BLOCKING-1 at a smaller scale:
correct code, one refactor from a silent hole. It is also still true that none of these three
branches writes a server-side log line or a correlation ID (MINOR-4, still open).

---

## The coordinator's specific questions, answered

| Asked | Answer |
|---|---|
| Timezone | **Real defect — MINOR-8.** Local vs UTC; the API and the CLI disagree on this host today. |
| A frozen clock | **No defect.** `dt.date.today()` is read per request (`main.py:296`), never cached at import; a long-lived process ages correctly. Two reads per `task=coding` request could straddle midnight and give the two answers dates one day apart — harmless at a 90-day window, not worth a finding. |
| Newest date in the **FUTURE** | **Real defect — BLOCKING-2.** Reports `stale: false`, `age_days: -400`. |
| A source present under a **different id** | **Real defect — BLOCKING-1a**, and this is the general form of the question. A source id that does not match `spec.primary_source` is invisible to the health block, whether it is a rename, a second feed, or a new ingest. The absent-key path itself is correct and fails closed (`main.py:198-210`, verified: `arena` absent yields `rows: 0, stale: true` with a notice) — but it only fires when the named source is missing entirely, not when a *different* source supplied the rows. |
| A category whose primary source is not the source its rows came from | **Real, and the most serious finding of this delta — BLOCKING-1a.** Constructed, measured, and reproduced above; `coding` served entirely from 800-day-old `epoch_swe_bench_verified` rows while reporting `swebench` healthy. Your instinct was right. |

---

## What the fix got right

- **The wall clock is genuinely wired, and the direction is right where the key is right.** On the
  standard fixture both coding surfaces now report `stale: true` with a notice each, where the
  original served `stale_notice: null` for both. That is the original BLOCKING-1 symptom fixed.
- **Unknown is not healthy, in both of its forms.** An absent source (`main.py:198-210`) and an
  undated-but-populated source (`main.py:217-222`) both report `stale: true` with a distinct,
  operator-legible notice. A foreign-schema database also fails closed (`main.py:297-306`). All
  three verified by hand.
- **`test_the_shipped_surface_is_exactly_the_declared_surface` is the right test**, and
  `_all_routes` genuinely recurses into mounts — the `Mount` case has no `.methods`, so the walk
  falls through to `route.app.routes`. It asserts the route **set**, which is the question the
  original test failed to ask.
- **The precedence guard was rewritten from a denylist to a property test with a closed exemption
  set**, and `test_the_precedence_exemptions_stay_closed` guards the escape hatch. This was not
  something I raised; it is a correct and unprompted hardening of the milestone's central contract.
- **`test_the_api_never_writes_to_the_database` got stronger**, not weaker: it now asserts the
  request actually returned `200` (so the invariant cannot pass vacuously) and that no
  `pipeline.db-*` sidecar was left behind — the exact check I ran by hand in the first pass.
- **The stay-green mutant on the CWD default was handled correctly** per V3C-72: the fault stayed
  green, and the mandatory new test was written rather than the fault being waived.
- **D-115 landed** (`docs/decisions.md`), closing the K.8 public-contract obligation for the Ruling A
  envelope. `source_health` is a new frozen `/v1` field and should be named in the same place.
- **No regression in anything I broke last time:** read-only seam still byte- and mtime-clean with no
  sidecars, no path or stack in any error body including the `500`, no SQL injection reachable, no
  mutating route, `422` still unreachable, and the added `GROUP BY` costs ~1.4 ms per request —
  negligible against the snapshot copy, so no new DoS.

## Gates

- [x] Re-ran the delta's suite: **21 passed**. `ruff` and `mypy` clean on both files.
- [x] No source or test file modified by this review; all probes ran from the scratchpad.
      `git status --porcelain -- src tests` shows only the coordinator's two files.
- [x] Fault-injection claim spot-checked against the tree: the mutants named as killed correspond to
      real assertions (route set, absent-source health, echo cap, nosniff, CWD default).
- [ ] **Fail direction (V3C-33/45) — TWO violations remain**, BLOCKING-1a and BLOCKING-2. Neither may
      be ledgered.

## What has to happen before W1 closes

1. **BLOCKING-1a** — key the health block on the sources that actually publish this surface's
   primary benchmark, not on `spec.primary_source`. Citing test: a fixture with two sources on one
   benchmark where the *stale* one wins the ranking, asserting `stale: true`. That test is also the
   mutant that kills the current implementation.
2. **BLOCKING-2** — clamp a negative `age_days` to stale, with its own notice, in the adapter.
   Citing test: a future-dated fixture.
3. **MINOR-8** — one expression, `dt.datetime.now(tz=dt.UTC).date()`; cheap enough to take now.
4. **The W-017 ledger amendment genuinely needs to land**, with the vector wording and the Stage-4.3
   escalation. It is currently not in the tree.
5. MINOR-9 and MINOR-10 may carry to W2 with the rest of MINOR-4's logging work.
