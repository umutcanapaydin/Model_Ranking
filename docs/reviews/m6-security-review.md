# M6 Closure Security Review (Stage 4.0)

**Reviewer:** Security-Reviewer subagent
**Date:** 2026-08-17
**Stage:** 4.0 milestone closure — BLOCKING before 4.3 deploy
**Scope:** `git diff 1faaf77..HEAD` — the whole M6 combined surface
**Risk tier:** HIGH (new unauthenticated external HTTP surface + schema migration + CORS/startup config)

## Scope note

This review covers the combined M6 surface, not any single wave:

1. A read-only `/v1` HTTP surface.
2. One serializer behind three renderings.
3. An English contract migration.
4. A schema migration.
5. A YAML expansion guard.
6. CORS + startup validation.
7. Deploy proposals (`Dockerfile`, `fly.toml` — PROPOSALS, not adopted) and
   `scripts/smoke_deps.py` (deploy-gate outbound calls, not in the serving path).

Priority of this pass, in order:

1. **Independent re-derivation of W-017** (memory amplification in
   `src/app/adapter/main.py:serving_snapshot`). The W3 pass ruled the deferral
   defensible only on the condition that this closure pass measures the
   amplification itself rather than citing prior figures. Prior numbers:
   ~450,000x at 51 MB (W1), ~9,100x at 761 KB (W3).
2. Verification of three carried claims (YAML guard coverage incl. the
   remote-fed aider client; gitleaks clean + W-001 allowlist shape;
   `/v1` is exactly three GET routes, no mutating verb).
3. Combined-surface findings — defects visible only when the waves are
   composed, not when each is read alone.
4. Deploy proposals and `scripts/smoke_deps.py`, budget permitting.

Findings are appended below as they are derived. Sections are written
incrementally by design (three prior attempts to this review were lost to
transport errors before anything reached disk).

Classification rules used: **BLOCKING** = ships now and is exploitable now.
**MINOR** = hygienic, not exploitable in current scope. **NOTE** = observation
or follow-up. A fail-open finding is never ledgered as MINOR — it blocks.

---

## Findings

### 1. W-017 — independent re-derivation

`src/app/adapter/main.py:229-255` (`serving_snapshot`), reached from
`src/app/adapter/main.py:572` on every unauthenticated
`GET /v1/recommendations`.

#### Method

Measured, not cited. Three measurements, each in a fresh interpreter, against
the operator databases actually present in the tree.

**(a) Marginal resident cost of one held snapshot.** N snapshots opened and held
live, every page touched, `ru_maxrss` sampled before and after, N varied so the
marginal cost is a slope rather than a single reading contaminated by the
interpreter's own watermark. Against `advisor.db` (1,019,904 bytes on disk;
`page_size` 4096, 249 pages, 1 free):

| N held | RSS delta over base |
|---|---|
| 1 | 3,227,648 |
| 16 | 23,920,640 |
| 64 | 90,521,600 |

Slope 16→64: `(90,521,600 − 23,920,640) / 48` = **1,387,520 bytes per held
snapshot**. Slope 1→16 agrees at 1,379,532. That is 1.36x the file on disk —
the in-memory pages plus SQLite's own per-connection structures.

**(b) End-to-end cost of one in-flight request**, which is the operative figure,
because the engine then writes into the private copy
(`build_price_medians` does `DELETE FROM px_median` + `INSERT`, the defect
`serving_snapshot` exists to contain) and the answer is built on top of it.
`TestClient` driven from a thread pool, peak RSS sampled continuously,
4N requests per run:

| concurrency N | peak RSS delta |
|---|---|
| 1 | 294,912 |
| 8 | 15,187,968 |

Marginal: `(15,187,968 − 294,912) / 7` = **2,127,580 bytes per concurrent
in-flight request** — **2.09x the database file**.

**(c) The attacker's side of the ratio.** Both defaults are valid
(`task=coding`, `budget=unlimited`, `main.py:543-544`), so no query string is
needed. The minimal request that triggers a full copy is
`GET /v1/recommendations HTTP/1.1` + a one-character `Host` + CRLF =
**45 bytes**. Response is 1,599 bytes.

#### My number

**~47,000x.** `2,127,580 / 45 = 47,280` bytes of server memory committed per
byte of unauthenticated attacker request, at today's 996 KiB database.

This sits between W1's ~450,000x (51 MB) and W3's ~9,100x (761 KB), and the
reason is methodological, stated because it changes the ruling: **both prior
figures divided the database file size by the request size.** They measured
the file. I measured resident memory, which is 2.09x the file once SQLite's
page cache, connection structures and the engine's own writes into the copy are
counted. Corrected to the same method, W3's 761 KB case is ~35,400x and W1's
51 MB case is ~944,000x.

#### The ruling, and why the ratio is not what decides it

The per-byte ratio is the wrong quantity to rule on, and this is the finding
the second measurement was commissioned to produce. **The ratio is dominated by
the database size, which is an operator variable, not an attacker one.** An
attacker cannot move it. Reporting it as a severity makes the number look like
it describes an adversary's leverage when it actually describes the operator's
data volume; that is how ~9,100x and ~450,000x could both be honestly derived
from the same code and disagree by 50x.

The quantity that decides is the **ceiling**:

```
peak concurrent memory = min(in-flight requests, 40) × 2.09 × db_size
```

40 is measured, not assumed: the `/v1` handlers are `def`, not `async def`
(`main.py:523`, `main.py:542`), so Starlette runs them on the AnyIO worker
thread pool, whose default limiter this environment reports at **40 tokens**.
Requests beyond 40 queue without allocating. So the in-process bound exists —
it is just nowhere written down, and it is nowhere near the deploy proposal's
assumptions.

Evaluated at three database sizes:

| db size | per in-flight request | ceiling at 40 threads | ceiling at fly.toml hard_limit 8 |
|---|---|---|---|
| 996 KiB (today) | 2.1 MB | **84 MB** | 17 MB |
| 5 MB | 10.5 MB | 418 MB | 84 MB |
| 51 MB (W1's figure) | 107 MB | **4.3 GB** | 856 MB |

**At today's size the service survives its own worst case.** 84 MB of transient
copies on top of a ~60 MB interpreter baseline is not an outage on any machine
anyone would deploy this to. Judged strictly on "ships and is exploitable now"
against the database that exists today, the amplification alone is **not**
BLOCKING, and I decline to inherit that adjective from either prior pass.

**Stage 4.3 should nonetheless HOLD, on a narrower and more defensible ground
than amplification.** The ceiling is linear in a file that an ingest pipeline
grows and that *nothing in this repository caps, measures, or checks*. The
milestone shipped a startup-validation gate for exactly this class of problem —
`validate_startup_config` (`main.py:127-148`) refuses to boot production when
`MODEL_RANKING_DB` is unset or `APP_BUILD` is unknown — and did not extend it to
the one configuration value that determines whether the process can survive its
own traffic. The deploy proposal compounds it: `fly.toml:38-44` names
`soft_limit 4 / hard_limit 8` as "W-017's containment", but **`fly.toml`
declares no `[[vm]]` section at all**, so the machine takes Fly's
`shared-cpu-1x` default of 256 MB. At a 5 MB database — five times today's, an
ordinary quarter of ingest — `soft_limit 4` alone is 42 MB and survives; at
51 MB the same "containment" is 856 MB against a 256 MB machine. The containment
number was chosen without the memory number beside it, and the two are in
different files with no check tying them together.

So: **HOLD 4.3**, and the condition is cheap, deterministic, and fail-closed —
which is what makes it a hold rather than a ledger entry:

1. Extend `validate_startup_config` to stat the database and refuse to boot in
   production when `db_size × 2.09 × <declared concurrency>` exceeds a declared
   memory budget. This is the same clause (V3C-56) the milestone already
   implements twice; it is one more `problems.append`.
2. Declare `[[vm]] memory` explicitly in `fly.toml` and derive
   `hard_limit` from it, rather than asserting a limit and a machine size in
   two files that never meet.
3. Cap in-process concurrency explicitly rather than inheriting AnyIO's 40 by
   accident. A framework default is not a control; nothing in the diff names it,
   and nobody reviewing `fly.toml`'s `hard_limit 8` would learn that the process
   itself will happily run 40.

Failure mode, recorded because it bears on severity: exhaustion here is an
OOM-kill of a read-only process. No disclosure, no write, no auth bypass — the
operator's bytes are never touched (`open_readonly`, `main.py:215-226`, and
`test_the_api_never_writes_to_the_database`). This is availability only, and
availability controls fail OPEN by design (V3C-33/45). That is precisely why it
is a hold on a config gate and not a BLOCKING exploit finding.

**Classification: BLOCKING at Stage 4.3 as a deploy-gate condition** (items 1-3
above), **not** as an exploitable defect at Stage 4.0. The distinction is the
point: the milestone's code may close; the first deploy may not proceed on a
ceiling nobody has written down.

---

### 2. The three carried claims — verified, not assumed

#### 2a. YAML guard covers four inputs including the remote-fed client — **CONFIRMED**

Four call sites, enumerated by grep over `src/` and `scripts/`, and they are the
only YAML entry points in the tree:

- `src/app/clients/aider.py:82` — the remote one (third-party HTTP body).
- `src/app/workflows/epoch.py:42` — `data/epoch-source.yaml`.
- `src/app/workflows/plans.py:135` — `data/plans.yaml`.
- `src/app/workflows/rosters.py:100` — `data/rosters.yaml`.

`yaml.safe_load` appears exactly once outside these — at
`src/app/workflows/yaml_guard.py:137`, inside the guard, after both bounds have
been applied. There is no unguarded parse path. The `import yaml` still present
in each of the four modules is for the exception type, not a second parser.

The guard itself fails **closed** in every direction I could reach it from:
non-`str` input, oversize input, unparseable input, recursive anchor, and
over-budget expansion all raise (`yaml_guard.py:110-135`). The cycle detector
and the memo are per-call (`yaml_guard.py:129`), which the comment at
`yaml_guard.py:70-81` records as the fix for a prior module-scope version that
turned one hostile document into a persistent refusal of legitimate ones. I
re-read that specifically because a guard that fails open may never be
ledgered — this one does not.

**MINOR-1 — `src/app/clients/aider.py:41-55`: the size bound is applied after
the body is already in memory, and the comment claims otherwise.**
The comment at `aider.py:46-48` states the check "bounds what the SOCKET is
given". It does not. `httpx.get` is non-streaming: it reads the complete
response body before returning, so `len(resp.content)` at `aider.py:49` is
evaluated on bytes that have already been allocated. A hostile or compromised
upstream streaming gigabytes exhausts memory before line 49 executes. The
correct shape is `httpx.stream` with an incremental byte counter that aborts
mid-read.

MINOR rather than BLOCKING on two grounds: this is the operator-run ingest path,
not the serving path (`D-116` keeps ingestion off the serving host, and the
`Dockerfile` ships no ingest entry point), and the upstream is a pinned
`raw.githubusercontent.com` URL. But it is recorded rather than waived, because
the defect here is the **comment**: it tells the next reviewer the socket is
bounded, and the next reviewer will believe it. A wrong claim about where a
bound sits is worse than no claim, since it retires the question.

#### 2b. gitleaks clean, and W-001's allowlist is label-shaped — **CONFIRMED**

Three scans run, all clean:

- Full history: 61 commits, ~3.10 MB — `no leaks found`.
- M6 range `1faaf77..HEAD`: 18 commits, ~619 KB — `no leaks found`.
- Working tree `--no-git`: ~3.88 MB — `no leaks found`.

The W-001 entry at `.gitleaks.toml:33-38` is a **regex** in `[allowlist].regexes`
matching the literal label shape `D-\d{3}-compliant`. It is not a path
suppression. `docs/reviews/**` — this file's own directory, and the place a real
leak would land because these files quote live tool output — remains fully in
scope, which the three scans above confirm empirically rather than by reading
the config. The pattern is zero-entropy and cannot mask a credential.

The pre-existing `[allowlist].paths` entries (`.env.example`,
`docs/external-articles/**`, `docs/external-skills/**`) are not from this
milestone and are unchanged in the diff.

#### 2c. Exactly three GET routes, no mutating verb — **CONFIRMED**

Enumerated from the live ASGI app rather than by reading decorators:

| path | methods |
|---|---|
| `/health` | GET |
| `/v1/categories` | GET |
| `/v1/recommendations` | GET |

Probed against a `TestClient`: `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` and
`HEAD` on `/v1/recommendations` all return **405**. There is no mutating verb on
the surface and no route beyond the three.

Additionally verified, and worth recording as good hygiene rather than assuming
it: FastAPI's default introspection routes are **off** —
`docs_url=None, redoc_url=None, openapi_url=None` at `main.py:154-156`, and
`/openapi.json`, `/docs`, `/redoc` all return 404 when probed. That is a real
reduction: an OpenAPI document on an unauthenticated surface publishes the
parameter space for free.

---

### 3. The combined surface — what only appears when the waves are composed

Each of these is invisible in the wave that introduced it. Each is a defect only
because of what a *different* wave did.

#### BLOCKING-1 — the publication allowlist was deleted by the wave that fixed the mirror

`src/app/workflows/serialize.py:45-68` composed with
`src/app/adapter/main.py:403-462` and `main.py:400`.

W1 shipped `/v1` with a hand-written dictionary naming all nineteen `Pick`
fields and all ten `Recommendation` fields. That enumeration was a genuine
drift hazard and W1's own review killed it correctly — deleting `stale_notice`
left thirteen tests green.

But on an **unauthenticated public surface** that enumeration was also something
else, which no single wave was positioned to see: it was the **publication
allowlist**. A field reached anonymous callers only because a human had written
its name into the adapter.

W2 replaced it with `recommendation_json`, an `asdict` walk over the whole
dataclass, filtered by `RELOCATED_FIELDS` — a list of exactly two entries
(`main.py:400`), both of which are *relocations*, not exclusions. Nothing in the
path excludes anything. `_answer_json`'s docstring states the new property
plainly and treats it as the achievement: *a field added to the engine arrives
here whether anyone remembers it or not* (`main.py:411-415`).

**For the CLI that is right. For an anonymous HTTP surface it inverts the
default from deny to allow.** The engine dataclasses are the pipeline's internal
model. A future field — an ingest diagnostic, an operator note, a source
credential fragment, a raw un-normalised vendor string, an internal id — is
published to the public internet by default, and nobody is asked.

**And no compensating control exists.** I checked the test suite specifically
for one, because a moved allowlist is not a deleted allowlist. It is deleted
here. `tests/unit/test_serializer_parity.py` enforces the passthrough direction
only: `test_every_recommendation_field_reaches_the_v1_answer:52` and
`test_every_pick_field_reaches_the_v1_answer:64`. There is a
"cites exactly what it cites, no more" test — but for CSV against JSON
(`:264`), not for engine against public payload. **A new engine field is
published to anonymous callers with the entire suite green.** The one test that
could catch it is written to guarantee the opposite.

This is BLOCKING, and specifically it may not be ledgered, because the direction
is fail-open: the default for an unreviewed field is *disclosed*. That is the
Lovable failure mode in the profile's own industry context — a serialization
default that publishes whatever the model happens to hold.

**Remedy, and it keeps W2's fix intact:** add an explicit published-field set for
the `/v1` rendering and a test asserting the payload's key set equals it
exactly. Adding an engine field then fails one test with a message naming the
field, and a human decides. The drift fix survives; the review step comes back.

#### BLOCKING-2 — the startup gate disables itself on an unvalidated string, and the deploy proposals are what set it

`src/app/adapter/main.py:75`, `main.py:133`, `main.py:146-148`.

`validate_startup_config` fails closed *only* when `APP_ENV` lowercases into
`PRODUCTION_ENVS = {"production", "prod"}` (`main.py:75`). The default when
`APP_ENV` is unset is `"development"` (`main.py:133`) — warn and serve.

**`APP_ENV` is itself never validated.** Any value that is not one of two exact
strings silently turns the entire gate off. `staging`, `live`, `prd`, `PROD_EU`,
a trailing space in a Fly secret, or the variable simply not surviving a
container rebuild — each of these produces a process that boots, logs one
`WARNING` line to stdout, and serves. I confirmed it rather than reasoning about
it: with `APP_ENV=staging` and `MODEL_RANKING_DB` unset, the module imports
cleanly, `STARTUP_WARNINGS` carries the unmet-config message, `APP_BUILD` is
`unknown`, and the app is live.

This is the defining fail-open shape: **the enablement of a fail-closed control
is a free-text environment variable with a permissive default and no
validation.** V3C-51 requires validating security config at startup and failing
in production; the implementation validates the config but not the one value
that decides whether validation has teeth.

Composition is what makes it BLOCKING rather than theoretical. W3 wrote the
validator. W4 wrote `Dockerfile:19` and `fly.toml:24`, which are the *only*
places `APP_ENV=production` is ever set — and both files are **PROPOSALS, not
adopted**, marked so in their own first lines. So the milestone ships a
fail-closed gate whose sole activation lives in two files the milestone
explicitly declines to adopt. Deploy by any route other than these two
unadopted files and the gate is off, silently, with `/health` returning 200.

Mitigating, and recorded so the severity is calibrated rather than inflated: the
CORS wildcard and malformed-origin refusals are **not** behind this gate. They
raise `ConfigError` in every environment (`main.py:136`, and `cors_origins`
raises unconditionally at `main.py:120` and `main.py:123`). The safety-class
control fails closed everywhere; what `APP_ENV` gates is the deploy-verifiability
class. That is why this is BLOCKING at the 4.3 deploy gate rather than a
Stage 4.0 exploit.

**Remedy:** validate `APP_ENV` itself — an unrecognised value is a
`ConfigError`, not a silent downgrade to development. Invert the default so that
*unset* means production-strict and a developer machine opts out explicitly. The
project's own posture is default-deny; this is the one place it is
default-permit.

#### BLOCKING-3 — `/health` is green during a total evidence outage, and 4.3 verifies deploys with `/health`

`src/app/adapter/main.py:511-519`, `main.py:138-139`, `main.py:564-568`,
`Dockerfile:22`, `fly.toml:25`, `fly.toml:46-52`.

Two waves each wired half of this.

W3's startup validator checks that `MODEL_RANKING_DB` **is set**
(`main.py:138`, `_db_path()` returns `None` only for empty/unset). It never
stats the file, never opens it, never checks it is readable.

W4's deploy proposals then set that variable unconditionally in the image
(`Dockerfile:22`, `fly.toml:25`, both `/data/advisor.db`) against a mounted
volume (`fly.toml:27-29`) whose contents are shipped separately — the
`Dockerfile:41-43` comment states the database is a mounted artefact rebuilt on
the owner's machine, deliberately not in the image.

**Composed, the startup check can never fire in the proposed deployment.** It is
satisfied by a string being present in the image, which W4 guarantees, rather
than by a database being present on the volume, which nothing guarantees. An
empty or unmounted volume produces: process boots, no warning, `/health` returns
`{"status": "ok", ...}`, and every single `/v1/recommendations` returns 503
`evidence_unavailable` (`main.py:565-568`). `/v1/categories` also returns 200,
because it reads only in-process constants (`main.py:523-538`) — so two of the
three routes look healthy during a complete outage of the only route that
carries data.

`fly.toml:46-52` points its platform health check at `/health`, so Fly restarts
nothing and reports the machine healthy. And Stage 4.3's own verification step
is `curl /health | jq .build` — **the deploy gate consults the one signal this
composition guarantees is green.** L.8's rule is exactly this: configured is not
working, and here the check confirms configured.

Fail direction: a monitoring signal that reports healthy while the service
cannot serve is fail-open in the direction that matters for a health check —
the same defect `_source_health_json:298-306` was written to fix one layer down,
reappearing one layer up. That module's own docstring names the principle
("the one direction a health check may never fail in") while the process-level
health check violates it.

**Remedy:** stat and open the database read-only at startup and fail closed in
production if it is absent or unreadable; and have `/health` report evidence
readability as a distinct field so the deploy gate and the platform probe both
see the outage. This composes cleanly with W-017's remedy — both want the
database's size and readability measured once at boot.

#### MINOR-2 — `DECLARED_ROUTES` is a declaration nothing in the process consumes

`src/app/adapter/main.py:67-69`.

The constant's own comment says the surface is *"asserted exactly, not merely
scanned for mutating verbs"*. In the process it is asserted nowhere: the only
consumers are in `tests/unit/test_api_v1.py`, and that test deliberately writes
the expected set out by hand rather than reading the constant
(`test_api_v1.py:458-467`, with the comment that the constant "was
self-declaring"). So the test is sound and the surface is genuinely pinned by
CI — but the module-level constant is now a dangling declaration that two of the
three readers of this file will assume is enforced at runtime. Per V4C-49, a rule
that names a shape should ship its gate in the same change. MINOR: the control
exists, it is just not where the code says it is.

#### PASS observations on the combined surface

Verified by probe, not by reading:

- `X-Content-Type-Options: nosniff` present on 200, 400 and — via the dedicated
  handler at `main.py:198-212`, which exists because `ServerErrorMiddleware` sits
  outside user middleware — on 500. Content type is `application/json`
  throughout.
- Reflected input is bounded and inert. `task=<script>x</script>` returns 400
  with the value `repr`'d inside a JSON body, truncated at 40 characters by
  `_echo` (`main.py:258-260`), served as `application/json` with `nosniff`. Not
  a browser-executable path.
- Error bodies carry no filesystem path in any branch I could reach — the 503
  at `main.py:565-568` deliberately refuses to say where it looked, and the 500
  at `main.py:210` refuses to carry the exception text, which is the one place a
  secret reaches a response without a decision.
- Serving is read-only in fact, not just intent: `open_readonly`
  (`main.py:215-226`) derives the URI through `Path.resolve().as_uri()` rather
  than string concatenation, so a `?` in the path cannot drop the mode.
- `allow_credentials=False` is hard-coded (`main.py:184`) and the CORS
  middleware is only mounted when an explicit allowlist exists
  (`main.py:176-187`). Wildcards raise rather than warn, in every environment.

---

### 4. Deploy proposals and the deploy-gate script

Reviewed as PROPOSALS. Both files declare themselves unadopted in their first
lines and `.github/CODEOWNERS` marks them as a K.10 cross-team surface, so
nothing here is BLOCKING at Stage 4.0 — but each item below must be closed
before the file is adopted, and BLOCKING-2 and BLOCKING-3 above already depend
on these files.

#### MINOR-3 — `Dockerfile:9-11`: the image resolves dependencies floating, at every build

`RUN pip install --no-cache-dir --prefix=/install .` against a `pyproject.toml`
carrying only lower bounds (`fastapi>=0.115`, `uvicorn[standard]>=0.32`,
`pydantic>=2.9`, `httpx>=0.27`, `pyyaml>=6.0`), and there is **no lockfile in
the repository** — no `requirements*.txt`, no `uv.lock`, no `poetry.lock`. Two
builds of the same commit produce different dependency sets, and a rebuild is
how a compromised upstream release reaches production without a code change.
`FROM python:3.11-slim` is likewise unpinned by digest (`Dockerfile:6`,
`Dockerfile:13`). V3C-05/10/65 asks for every dependency saved to the manifest
and the toolchain pinned in CI; the manifest here records intent, not
resolution. Remedy: a hashed lockfile installed with `--require-hashes`, and a
digest-pinned base image.

#### MINOR-4 — `fly.toml`: no `[[vm]]` section, so the containment number has no denominator

Already argued under W-017 and repeated here because it belongs to this file:
`fly.toml:38-44` names `soft_limit 4 / hard_limit 8` as W-017's containment,
while the file declares no machine memory at all and therefore inherits Fly's
`shared-cpu-1x` 256 MB default. A concurrency limit is only a containment
relative to a memory size, and the two are never stated together. Also note that
`hard_limit` is a **proxy routing** bound, not an in-process one: the process
itself will run 40 concurrent handlers regardless, because the `/v1` handlers
are sync (`main.py:523`, `main.py:542`) and inherit AnyIO's default limiter.

#### PASS — `Dockerfile` hardening that is real

Non-root `appuser` at uid 10001 (`Dockerfile:33-34`), two-stage build so the
toolchain does not ship, the evidence database kept as a mounted artefact rather
than baked into the image (`Dockerfile:41-43`), `APP_BUILD` passed as a build
arg rather than committed, `MODEL_RANKING_CORS_ORIGINS` left commented out
rather than set permissively (`Dockerfile:26-28`), and `force_https = true` in
`fly.toml:35`. D-116's shape decision — no ingestion on the serving host — is
the single largest risk reduction in the milestone: it keeps the network-fetching
code and the untrusted-producer boundary W-005 guards entirely off the public
surface.

#### NOTE-1 — `scripts/smoke_deps.py`: live outbound calls, correctly placed

Five live third-party fetches (`smoke_deps.py:101-107`), each through the real
client and the real parser rather than a typed-in URL — which is the right
design and the docstring's own account of why the previous shell version was
worthless (`smoke_deps.py:4-9`). Security posture checked and clean:

- **Not in the serving path and not in the image.** `Dockerfile:9-10` copies
  only `pyproject.toml` and `src/`; `scripts/` never reaches the container.
- **No credentials to leak.** I grepped `src/app/clients/` for `os.environ`,
  `getenv`, `token`, `Authorization`, `api_key` — every feed is unauthenticated
  public data and no client sends a credential. So the broad
  `except Exception` printing `str(exc)[:90]` at `smoke_deps.py:33-34`, and the
  full `traceback.print_exc()` under `-v` at `smoke_deps.py:36`, cannot surface a
  secret. They can surface local filesystem paths into a deploy log; on the
  owner's machine that is acceptable, and it is recorded here only so that
  routing this script's output into CI later is a decision rather than a drift.
- The `_aider` probe (`smoke_deps.py:62-69`) exercises the newly guarded remote
  YAML path end to end at the gate, which is the one place MINOR-1's
  post-download size check would be reached in anger.
- The deliberate refusal to retry the flaky Arena probe
  (`smoke_deps.py:93-97`) is correct and worth naming: a gate that retries until
  green reports a reliability the deploy will not have.

---

## Gates

- [x] **Secret scan green** — gitleaks clean on full history (61 commits),
      on `1faaf77..HEAD` (18 commits), and on the working tree (`--no-git`,
      3.88 MB). W-001's allowlist verified label-shaped, not path-scoped.
- [x] **pip-audit green** — `No known vulnerabilities found` (only the local
      `model-ranking` package skipped, as expected for an unpublished project).
- [x] **Slopsquat / new imports** — the milestone adds no new third-party
      import. `yaml_guard.py` uses `pyyaml`, already in the manifest;
      `smoke_deps.py` imports only project clients and the stdlib.
- [x] **Default-deny on the new external surface** — three GET routes, all
      mutating verbs 405, introspection routes off, CORS empty by default and
      wildcard-refusing, read-only DB handle, no filesystem path in any error
      body.
- [ ] **Startup security-config validation fails closed** — **NOT MET.**
      BLOCKING-2: the gate's own enablement is an unvalidated `APP_ENV` with a
      permissive default. BLOCKING-3: the database check validates a string, not
      a database.
- [x] **Prompt-injection / untrusted-producer hygiene** — the one genuinely
      external YAML producer is guarded (`aider.py:82`); the guard fails closed
      in every direction and its cycle/memo state is per-call. No `eval`, no
      instruction-following from fetched text; fetched content is parsed into
      typed dataclass rows and never into control flow.
- [x] **Permission matrix not violated** — no source or test file modified by
      this review; no `git commit/push/checkout/restore/stash` run; no
      destructive operation in the diff.
- [ ] **Migration reviewed** — the M6 schema migration is in scope of §11's
      human-review trigger. Reviewed at the serving boundary only: `open_readonly`
      (`main.py:215-226`) exists specifically so an anonymous GET cannot reach
      `schema.connect()`'s migrate-on-open, and that is correct and tested. The
      migration's own reversibility is **carried to the owner** as a §11
      human-review item rather than signed off here.
- [x] **PII / logging** — no customer PII in this project; the data is public
      benchmark and pricing records. The one new log statement
      (`main.py:171-173`) emits configuration warnings, no request data.
- [ ] **SAST** — not run. `bandit`/`semgrep` are not installed in this
      environment and installing a scanner was outside this pass's budget.
      Recorded as unmet rather than waived (V4C-13).

---

## Verdict

**BLOCKING** — three findings, all of them fail-open in direction, none of them
ledgerable.

The milestone's *code* is in good shape and several of its controls are better
than the profile expects. Every BLOCKING here is a **composition** defect: each
wave's change was right for the wave that made it, and wrong once placed beside
another wave's. That is exactly the class this closure review exists to catch,
and it is the reason a per-wave security pass could not have found any of them.

| # | Finding | file:line | Fail direction |
|---|---|---|---|
| BLOCKING-1 | Publication allowlist deleted by the mirror fix; new engine fields auto-publish to anonymous callers with all tests green | `serialize.py:45-68`, `main.py:400`, `main.py:403-462` | discloses by default |
| BLOCKING-2 | Startup gate disables itself on an unvalidated `APP_ENV`; its only activation lives in two unadopted files | `main.py:75`, `main.py:133`, `main.py:146-148` | control off by default |
| BLOCKING-3 | Startup check validates a string, not a database; `/health` green during total evidence outage, and 4.3 verifies deploys with `/health` | `main.py:138`, `main.py:511-519`, `Dockerfile:22`, `fly.toml:25,46-52` | reports healthy when broken |
| W-017 | Memory amplification — measured ~47,000x, ceiling unbounded in DB size, nothing caps or measures it | `main.py:229-255`, `main.py:572` | HOLD 4.3 (deploy-gate condition) |
| MINOR-1 | Aider size bound applied post-download; the comment claims the socket is bounded | `aider.py:41-55` | — |
| MINOR-2 | `DECLARED_ROUTES` consumed by nothing in the process | `main.py:67-69` | — |
| MINOR-3 | Image resolves dependencies floating; no lockfile, no digest pin | `Dockerfile:6,9-11,13` | — |
| MINOR-4 | `fly.toml` states a concurrency containment with no declared machine memory | `fly.toml:38-44` | — |
| NOTE-1 | `smoke_deps.py` live outbound calls — correctly placed, no credential exposure | `scripts/smoke_deps.py` | — |

**Counts: 3 BLOCKING + 1 HOLD (W-017), 4 MINOR, 1 NOTE.**

Stage 4.0 does not pass. Stage 4.3 does not proceed.

## Risks carried to the next milestone

- The migration's reversibility is a §11 human-review item and is not signed off
  by this pass.
- SAST was not run in this environment; queue `bandit`/`semgrep` into the
  Stage 2 gate rather than leaving it to a closure reviewer's local toolchain.
- The real W-017 fix remains the engine change: `build_price_medians` writing
  (`DELETE` + `INSERT` on `px_median`) is why a read API needs a private copy at
  all. Every containment in this milestone is downstream of that one write.


---
---

# RE-REVIEW — Stage 4.0 fix delta (`git diff ec952f5^..HEAD`)

**Reviewer:** Security-Reviewer subagent
**Date:** 2026-08-17
**Scope:** the two fix commits — `ec952f5` (three BLOCKING closed + W-022) and
`fd71b7e` (W-017's three conditions closed).
**Why a full pass and not a spot check:** V4C-49 — a fix inherits the risk class
of the bug it fixes. All six changes land directly on the unauthenticated
surface, the startup gate, or the containment arithmetic.

**Standing correction accepted.** The coordinator disclosed W-022: the
fault-injection harness was measuring stale bytecode, and at least one mutant
reported killed was not. I have therefore re-derived every number below myself,
under `python -B`, and cited none of the coordinator's figures as evidence. My
own W-017 measurement in the section above was taken in fresh interpreters
against live processes rather than by mutation, so it is unaffected; I have
re-checked its one load-bearing output (the RSS factor) regardless — see
RR-NOTE-1.

Classification unchanged: **BLOCKING** = ships now and is exploitable now.
**MINOR** = hygienic. **NOTE** = observation. A fail-open finding is never
ledgered.

---

## RR-BLOCKING-1 — the publication allowlist was restored for the ten fields and not for the nineteen

`src/app/adapter/main.py:509-536` (`PUBLIC_ANSWER_FIELDS` + `WITHHELD_ANSWER_FIELDS`),
`src/app/adapter/main.py:570` (the filter),
`tests/unit/test_api_config.py:310-341` (the citing test).

**BLOCKING-1's fix is correct and it is one level too shallow.**

`PUBLIC_ANSWER_FIELDS` governs the top level of an answer. `picks` is one
member of that set, and its value is the recursive `asdict` walk of every
`Pick` — nineteen fields, none of them declared anywhere, filtered by nothing.
The comprehension at `main.py:570` is a flat dict comprehension over
`engine.items()`; it never descends.

The original finding's own narration names the split exactly: W1's deleted
dictionary enumerated *"all nineteen `Pick` fields and all ten `Recommendation`
fields"* (`serialize.py:5-7`, and the docstring at `main.py:545-549` repeats
it). The fix reinstated the allowlist for the ten. The nineteen are still
governed by nothing, and they are where the per-model data actually is — model
name, vendor, harness, prices, evidence dates, confidence basis.

**Measured, not argued.** Two probes, fresh interpreter, `python -B`, against a
seeded database through a real `TestClient`:

(a) The mirror of the fix's own stay-green test, one level down. A
`recommendation_json` that injects `internal_vendor_api_key_fragment` into each
pick dict: **6 of 6 picks served that field to an anonymous caller**, value
intact. The top-level equivalent of this injection is caught by
`test_the_allowlist_actually_filters_an_undeclared_field`
(`test_api_config.py:421-461`); the nested one is caught by nothing.

(b) The real scenario rather than an injection. A `Pick` subclass carrying one
extra field `operator_debug_note`, passed through `_answer_json`. Served payload
key set for the pick: twenty keys, including `operator_debug_note`. **A field
added to the engine's `Pick` reaches the public internet with no human in the
path.**

**And the new citing test cannot fail on it.**
`test_no_engine_field_reaches_the_public_surface_undeclared`
(`test_api_config.py:310-341`) computes `{f.name for f in fields(Recommendation)}`
— ten names. `fields(Pick)` is never enumerated.
`test_the_public_payload_carries_only_declared_fields`
(`test_api_config.py:342-369`) compares `set(answer)`, the top-level keys, and
never opens `answer["picks"]`. So the property the fix commit claims — *"fails
when the engine gains a field until a human files it in one of three lists"* —
holds for ten of the twenty-nine engine fields and is false for the other
nineteen, with the entire suite green.

**Fail direction: discloses by default**, on an unauthenticated surface, which
is the same direction and the same surface as the finding it was fixing. It may
not be ledgered.

**Remedy, small and symmetrical:** a `PUBLIC_PICK_FIELDS` frozenset, the filter
applied to each pick, and the citing test extended to `fields(Pick)`. The three
existing lists become six; nothing else in the fix changes.

---

## RR-PASS-1 — BLOCKING-2 is closed, and it is closed correctly

`src/app/adapter/main.py:83` (`RELAXED_ENVS`), `main.py:195-203`, `main.py:197`.

The default is now inverted the way the finding asked: `strict` is the
complement of an explicitly spelled relaxed set, so "unknown" and "unset" both
land in the harsh branch. Re-derived myself, eight cases, each a fresh
interpreter under `python -B` with the environment scrubbed:

| `APP_ENV` | `MODEL_RANKING_DB` | result |
|---|---|---|
| unset | unset | **refuses** (`ConfigError`, both problems reported at once) |
| `staging` | unset | **refuses**, and names the unrecognised value |
| `" production "` (padded) | unset | **refuses** — `.strip()` at `main.py:190` |
| `PROD_EU` | unset | **refuses** |
| `development` | unset | boots with a warning — correct, that is the point |
| `test` | unset | boots with a warning |
| unset | real file, no `APP_BUILD` | **refuses** on `APP_BUILD` |
| unset | real file + `APP_BUILD` | boots, no warnings |

My original scenario — `APP_ENV=staging` with no database — now raises. The
`APP_BUILD` requirement moved from `environment in PRODUCTION_ENVS` to `strict`
(`main.py:225`), which is the same inversion applied to the second check, and it
is right.

`tests/conftest.py:18` (`os.environ.setdefault("APP_ENV", "test")`) is a
declaration and not a suppression, as its docstring claims: every test that
exercises the strict branch passes `env=` explicitly
(`test_api_config.py:371-393`, `:395-418`, `:485-509`) or spawns a real
subprocess (`test_api_config.py:151-176`), and `setdefault` cannot override an
environment that already names itself. I checked that the suppression reading
was wrong rather than assuming it.

---

## RR-BLOCKING-2 — BLOCKING-3's fix stats the file and never opens it, so `/health` is still green over an evidence outage — and the two databases in this tree are already in that state

`src/app/adapter/main.py:207-212` (`db.is_file()`),
`src/app/adapter/main.py:649-657` (`/health`),
`tests/unit/test_api_config.py:395-418`, `fly.toml:59-66`.

The finding's remedy had two parts. **One shipped.** The absent-file case is
genuinely closed: `MODEL_RANKING_DB` pointing into an unmounted volume now
raises at import, measured. A directory raises too.

**The other did not.** The check asks `Path.is_file()`. It never opens the
database, and `/health` still reports no evidence field. So the failure mode
moved from *file absent* to *file present and unusable* — which on a volume
whose contents are shipped separately (D-116 §2) is the more likely of the two,
because a partial copy, a wrong-permission file, or a stale artifact all leave a
file behind. Measured, six database states, real `TestClient` against the real
app, `python -B`:

| volume state | boots? | `/health` | `/v1/recommendations` |
|---|---|---|---|
| directory | **refuses** | — | — |
| absent | **refuses** | — | — |
| zero bytes | boots | `200 {"status":"ok"}` | 200, every answer `unavailable_reason` |
| truncated copy (⅓ of the file) | boots | `200 {"status":"ok"}` | 503 `evidence_unavailable` |
| non-SQLite bytes | boots | `200 {"status":"ok"}` | 503 `evidence_unavailable` |
| valid file, `chmod 000` | boots | `200 {"status":"ok"}` | 503 `evidence_unavailable` |

The zero-byte row is not an accident of my probe: the new citing test
`test_a_database_that_does_not_exist_fails_closed`
(`test_api_config.py:414-418`) writes `b""` and **asserts that it validates
clean**. An empty file is explicitly blessed by the test that closes this
finding.

**And this is not hypothetical here.** The two evidence artifacts sitting in
this tree — `advisor.db` (1,019,904 bytes) and `owner_advisor.db` (1,052,672
bytes), the file `Dockerfile:23` and `fly.toml:19` mount at `/data/advisor.db` —
are at a **pre-M6 schema**: `scores` has no `effort` column. The M6 schema
migration is deliberately operator-run
(`schema.py:419` — *"never runs from a read-only CLI"*), and the serving path is
read-only by design, so nothing on the serving host migrates them. Driven
end-to-end through `serving_snapshot`, both raise
`OperationalError: no such column: effort`, which the handler converts into an
answer carrying `unavailable_reason`.

The composed result, measured: **the process boots, startup validation passes
(the file exists and is inside the size budget), `/health` returns
`{"status":"ok","build":"deadbee"}`, and every `/v1/recommendations` returns
HTTP 200 with zero picks and "This surface's evidence could not be read."** Not
even a 503 — a 200. Stage 4.3 verifies deploys with `curl /health | jq .build`
(`fly.toml:59-63` points the platform probe at the same route), and a smoke test
that checks status codes passes too.

**Fail direction: reports healthy when broken** — unchanged from the original
finding, on a narrower but more probable trigger, and now with a *new* startup
check standing beside it that looks like it verified the database and only
weighed it. That is the reason this cannot be ledgered: the fix makes the gap
harder to see than it was before.

**Remedy, still small:** open the database read-only at startup and run one
cheap statement against it (`SELECT 1 FROM sqlite_master`, or a schema-version
probe that would have caught the `effort` column) and fail closed in a strict
environment; and add an `evidence` field to `/health` so the deploy gate and the
platform probe see the outage rather than the process.

---

## RR-PASS-2 — W-017's three conditions: all three are closed, and (c) is closed in the process, not only in a test

### Condition (a) — the ceiling is derived and the process refuses to boot past it — **CLOSED**

`src/app/adapter/main.py:102-120` (`RSS_FACTOR`, `MAX_CONCURRENT_REQUESTS`,
`MEMORY_BUDGET_MB`, `max_database_bytes`), `main.py:213-224` (the refusal).

`max_database_bytes()` is genuinely derived from the other two declared terms —
it is one expression over the two constants, so moving either moves the limit.
Measured against the live module: `MAX_CONCURRENT_REQUESTS=8`,
`MEMORY_BUDGET_MB=256`, `RSS_FACTOR=2.2`, `max_database_bytes() = 15,252,014`
(14.55 MiB), against a 1,019,904-byte database.

**I re-derived the one number of mine the gate now depends on**, because
`RSS_FACTOR` is my 2.09 rounded up and I measured that at ~1 MiB — where
SQLite's fixed per-connection overhead is a large share of the cost. If the
factor *grew* with size the budget would be optimistic in the exact regime the
gate authorises. Marginal resident cost per held snapshot, fresh interpreter,
`python -B`, N=8, three purpose-built databases:

| db size | marginal RSS per held snapshot | factor |
|---|---|---|
| 1,064,960 | 1,419,264 | 1.33 |
| 5,292,032 | 6,877,184 | 1.30 |
| 15,331,328 | 19,789,824 | 1.29 |

The copy term is flat-to-slightly-decreasing with size. **2.2 is conservative at
the ceiling, not just at today's size**, which is what the condition needed.

### Condition (b) — the VM is declared and a test fails on drift — **CLOSED**

`fly.toml:32-34` (`[[vm]] size` + `memory = "256mb"`),
`tests/unit/test_api_config.py:538-566`.

The `[[vm]]` block exists, so the containment now has a denominator. The
agreement test reads `fly.toml` with comment lines stripped
(`test_api_config.py:552-556`) and asserts four couplings: process concurrency ==
declared concurrency, budget == declared budget, `hard_limit` == process
concurrency, and declared VM >= budget. I checked the failure direction rather
than the success: if any of the four terms stops being declared in a shape the
regexes recognise, the first assertion fires with *"fly.toml stopped declaring a
term"*. It cannot silently degrade into matching nothing.

I also confirmed the coupling is live in both directions and not decorative:
raising `MODEL_RANKING_MAX_CONCURRENCY` to 40 (AnyIO's old default) against the
5.37 MB probe database makes the **process refuse to boot**, because the derived
limit falls to 3,050,402 bytes. The arithmetic is load-bearing.

### Condition (c) — the cap is real in the running process — **CLOSED, and I verified it outside the test**

`src/app/adapter/main.py:239-254` (`_lifespan`), `main.py:263` (wired),
`tests/unit/test_api_config.py:511-536`.

The coordinator's own test reads the limiter back from inside a running loop,
which is the right shape. But a lifespan that works under `anyio.run` is not
proof that it works under the process the `Dockerfile` actually starts, so I
measured that instead — `uvicorn app.adapter.main:app` (`Dockerfile:46`), real
HTTP over a socket, 60 parallel clients x 6 requests each, server RSS sampled
from outside the process, against a 5,365,760-byte seeded database:

| | predicted peak over baseline | measured |
|---|---|---|
| cap honoured (8) | ~90 MB | **81 MB** |
| cap not honoured (AnyIO's 40) | ~450 MB | — |

**81 MB.** The cap is honoured by the real server, not only by the test. This
was the condition most likely to be "built ≠ wired" (V3C-73) and it is wired.

---

## RR-MINOR-1 — the memory budget is the whole VM, so the derived ceiling has no room for the process itself

`src/app/adapter/main.py:111` and `main.py:120`, `fly.toml:24` and `fly.toml:34`.

`MEMORY_BUDGET_MB` is set to 256 and the VM is declared at 256 MB, so
`max_database_bytes()` solves for snapshots occupying **100% of the machine**:
`8 x 2.2 x 15,252,014 = 268,435,446` bytes = exactly 256.0 MiB. Nothing is
reserved for the interpreter, FastAPI, uvicorn, or the response objects.

Measured baseline of the real process — import, app construction, one `/health`
— is **60.9 MiB** (`ru_maxrss`, fresh interpreter). So at the size the gate
declares servable the process needs roughly **317 MiB on a 256 MiB machine**.
Using the factor I actually measured through the socket (1.89 rather than the
conservative 2.2) it is still ~281 MiB. Either way the gate says "safe" for a
band it cannot survive.

Corrected ceiling with a baseline term: `(256 - 61) MiB / (8 x 2.2)` =
**11.08 MiB**, against the 14.55 MiB the gate currently permits — the gate is
permissive by about 31%.

**MINOR and not BLOCKING**, deliberately: today's database is 1.02 MiB, eleven
times under even the corrected ceiling, and the failure is an OOM-kill of a
read-only process — availability only, no disclosure, no write, and the
attacker cannot move the term that decides it. But it belongs on the 4.3
checklist, because the number's whole purpose is to be trusted without being
re-derived. **Remedy:** one more declared term — `PROCESS_BASELINE_MB`,
subtracted before the division — which keeps the "derived, never typed"
property the docstring at `main.py:115-119` is right to insist on.

---

## RR-NOTE-1 — the comment-matching class, swept for others (the coordinator's specific ask)

The `fly.toml` bug — a guard that searched a whole file and matched its own
explanatory comment — was found and fixed by its author. I swept the repository
for the same shape: every place a test or gate asserts a property by searching
raw file text rather than parsed structure.

**Found one more, and it is live.**
`tests/unit/test_epoch_staleness.py:62-70`
(`test_weekly_workflow_wires_the_epoch_clock_without_a_conditional`) is a V4C-49
wiring guard: it searches `.github/workflows/contract-tests.yml` for the
staleness command, checks it appears exactly once, and checks no `if:` guards it.
Measured against a mutant that comments the step out — i.e. the cadence check no
longer runs in CI at all:

| workflow | guard |
|---|---|
| original | PASS |
| the step commented out, so the check is disabled | **PASS** |

A `#`-prefixed line still satisfies `count(command) == 1` and still satisfies
`command in plan_job`. Same shape, different file, and it is the shape's more
dangerous variant: here the comment-out is what *disables* the control. MINOR
rather than BLOCKING because this gates data-freshness cadence, not the
unauthenticated surface. **Remedy is the one already applied to `fly.toml`:**
strip comment lines, or parse the YAML and look at the job's steps.

**Checked and clean:**

- `scripts/bootstrap-check.sh:69` (C2, the L.7 `/health` contract) is three
  `grep -q` calls over the whole of `main.py` with no comment stripping — the
  same construction. I mutated `main.py` to delete the `/health` route entirely
  and re-ran them: `APP_BUILD` still matched (4 of its 5 occurrences are prose),
  but `"build"` and `"version"` did not, because those two literals occur
  exactly once in the file, in the return statement (`main.py:657`). The gate
  holds **today, by a property of the file rather than by construction** — the
  day a docstring quotes `"build"` it stops holding. Recorded, not blocking.
- `tests/unit/test_api_config.py:136` and `tests/unit/test_serializer_parity.py:461`
  both `ast.parse` the source and assert over the tree. That is the correct
  construction and it is immune to this class entirely; worth naming as the
  in-repo counterexample the other two should be moved to.

---

## RR-NOTE-2 — smaller observations on the fix delta

- **`PUBLIC_ANSWER_FIELDS` and `WITHHELD_ANSWER_FIELDS` are not asserted
  disjoint** (`main.py:521-536`, `test_api_config.py:310-341`). The citing test
  unions the three lists, so a field named in *both* is "declared" and is
  published while the record says it is withheld. One `assert not (PUBLIC &
  WITHHELD)` closes it. Not exploitable today — `WITHHELD` is empty.
- **Malformed containment values fail closed, but as raw tracebacks rather than
  through `ConfigError`** (`main.py:107`, `main.py:111`, `main.py:120`).
  Measured: `MODEL_RANKING_MAX_CONCURRENCY=0` gives `ZeroDivisionError`,
  `abc` and empty give `ValueError`, and `-1` imports but then refuses on the
  budget check because the derived limit goes negative. Every path refuses, which
  is the direction that matters, but none joins the "print all problems at once"
  shape V3C-51 pairs with L.6, and an operator reading a `ZeroDivisionError`
  traceback learns nothing about which variable was wrong.
- **The strictness inversion changed developer behaviour and that is recorded
  where it should be.** `APP_BUILD` is now required in every strict environment
  (`main.py:225`), not only production, so a bare `import app.adapter.main`
  refuses. `tests/conftest.py` declares the suite's environment rather than
  patching around the check — verified above, and the right shape.
- **`test_the_declared_numbers_agree_with_the_deploy_proposal` reads
  `Path("fly.toml")` relative to the working directory**
  (`test_api_config.py:556`). Run from anywhere but the repo root it raises
  `FileNotFoundError` — loud, so fail-closed, but it is the one path in that
  test that is not robust to how it is invoked.
- **The `/v1` surface is unchanged by the fixes.** Re-probed after the delta:
  three GET routes (`/health`, `/v1/categories`, `/v1/recommendations`);
  `POST`/`PUT`/`PATCH`/`DELETE` all 405; `/openapi.json`, `/docs`, `/redoc` all
  404. Adding a lifespan did not add a surface.

---

## Gates (re-review)

- [x] **Full suite** — `363 passed, 12 skipped` under `python -B`, matching the
      coordinator's claim. Re-run by me, not cited.
- [x] **`make check` exit 0** — including `check_records PASS [repo]`, the
      `L1` English gate, and the record self-tests, at the tree containing this
      file.
- [x] **gitleaks clean on the fix delta** — `ec952f5^..HEAD`, 2 commits,
      ~62 KB, `no leaks found`.
- [x] **No new external surface, no new dependency** — the delta adds
      `contextlib`, `collections.abc` and `anyio.to_thread`; `anyio` is already a
      transitive requirement of Starlette and is not newly declared. No new
      third-party import to slopsquat-check.
- [x] **No source or test file modified by this review**, no
      `git commit/push/checkout/restore/stash` run. All mutants were written to
      a scratch directory outside the repository.
- [x] **Bytecode disabled for every measurement** (`python -B`), per W-022.
- [ ] **`/health` reports serving capability** — NOT MET, see RR-BLOCKING-2.
- [ ] **Publication is a decision for every published field** — NOT MET for the
      nineteen `Pick` fields, see RR-BLOCKING-1.

## Re-review verdict

**BLOCKING** — two findings, both fail-open, neither ledgerable.

| original finding | status |
|---|---|
| BLOCKING-1 — publication allowlist deleted | **PARTIALLY CLOSED** — closed for the ten `Recommendation` fields, open for the nineteen `Pick` fields → **RR-BLOCKING-1** |
| BLOCKING-2 — startup gate disabled by an unvalidated `APP_ENV` | **CLOSED** — verified across eight environment cases |
| BLOCKING-3 — startup check validates a string, not a database | **PARTIALLY CLOSED** — absent file and directory now refuse; present-but-unusable still boots green → **RR-BLOCKING-2** |
| W-017 (a) derived ceiling, refuses to boot past it | **CLOSED** — and `RSS_FACTOR` re-verified conservative at the ceiling, 1.29–1.33 measured |
| W-017 (b) `[[vm]] memory` declared + drift test | **CLOSED** — coupling verified live in both directions |
| W-017 (c) thread limiter set in the lifespan | **CLOSED** — verified under a real `uvicorn`, 81 MB against a 450 MB uncapped prediction |

| # | new finding | file:line | fail direction |
|---|---|---|---|
| RR-BLOCKING-1 | the allowlist governs the top level only; a new `Pick` field publishes itself to anonymous callers, and the new citing test enumerates `fields(Recommendation)` only | `main.py:521-536`, `main.py:570`, `test_api_config.py:310-341` | discloses by default |
| RR-BLOCKING-2 | the startup check stats the file and never opens it; `/health` is 200 over an unreadable, truncated or schema-stale database — and both databases in this tree are schema-stale | `main.py:207-212`, `main.py:649-657`, `test_api_config.py:414-418` | reports healthy when broken |
| RR-MINOR-1 | the memory budget is 100% of the VM, so the derived ceiling has no room for the 60.9 MiB process; permissive by ~31% | `main.py:111`, `main.py:120`, `fly.toml:24,34` | guard says safe for a band it cannot survive |
| RR-NOTE-1 | one more comment-matching guard, live: a commented-out CI step still satisfies it | `tests/unit/test_epoch_staleness.py:62-70` | control disable is invisible |
| RR-NOTE-2 | disjointness, malformed-value ergonomics, relative path, surface re-probe | as listed | — |

**Counts (re-review): 2 BLOCKING, 1 MINOR, 2 NOTE. Closed: BLOCKING-2 and all
three W-017 conditions.**

### The shape worth naming

Both re-opened findings are the *same defect one level down from where it was
fixed*. BLOCKING-1's allowlist was restored for the ten fields the original
dictionary named and not for the nineteen it also named — and the original
finding's own text named both numbers. BLOCKING-3's database check was moved
from "is the variable set" to "is there a file" when the property that matters
is "can this process serve from it". Each fix took the finding's example rather
than the finding's class.

That is the coordinator's own recurring shape — a guard that reads the
description of the thing instead of the thing — arriving one more time, and this
time in the remedies rather than in a test. It is worth saying plainly because
the *verification* around both fixes is good: the fault-injection stay-green
test at `test_api_config.py:421-461` is exactly the right instinct, and it was
aimed one level too shallow, which is why it passed.

Stage 4.0 does not pass on this delta. Stage 4.3 does not proceed. Both remedies
are small and neither disturbs what the fix commits got right.
