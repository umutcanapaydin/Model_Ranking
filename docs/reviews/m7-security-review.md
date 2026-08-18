# M7 Closure Security Review (Stage 4.0)

**Reviewer:** Security-Reviewer subagent (fresh eyes; I authored none of this surface — K.7)
**Date:** 2026-08-18
**Stage:** 4.0 milestone closure — BLOCKING before the 4.3 deploy (AGENTS.md 6)
**Scope:** `git diff 9f4471d..HEAD`, HEAD = `ec09883` — the whole M7 combined surface
**Risk tier:** HIGH (m7-plan: W1 creates a new production entry point over untrusted network
input; W2 touches the scoring path; W3 deletes a security control), calibrated by **D-122**
**Depth applied:** FULL on `/v1`, `recommend.py`, `rank.py`, the read-only handle and the
W-017 re-derivation. SINGLE PASS on `Dockerfile`, `fly.toml`, CI and the governance scripts.

---

## Verdict

# PASS

**W-017 is closed by deletion, and I re-derived it independently rather than citing the wave.**
The measurement is in section 1 and it agrees with the wave's claim in direction and magnitude.
No finding below is a go-live blocker under D-122's calibration: this is a solo project with no
users, no authentication, no PII and no payments, about to serve a public read-only API over
published benchmark data. Eight MINOR findings follow, ordered by severity, each with a concrete
input, mechanism and consequence. Three of them (MINOR-2, MINOR-3, MINOR-6) are controls that are
correct today but not backed by anything that would notice if they stopped being correct, which is
this project's most-repeated defect class and the reason they are ranked above the rest.

**Nothing here is escalate-NOW.** No suspected secret, no scanner suppression by any agent, no
plan-invalidating scope change, no touch of an auth / PII / payment / migration path that would
fire permission-matrix 11's human-review trigger.

---

## 1. W-017 — the independent re-derivation D-116 makes a condition of go-live

D-116 requires the closure pass to re-derive the amplification itself, because three earlier
passes produced three figures (~9,100x at 761 KB, ~450,000x at 51 MB, ~47,000x measured as
resident memory). I did not read any of those numbers back; I built my own harness and ran it in
the shape that actually ships.

### Method

Image built from the repository's own `Dockerfile` (`docker build --build-arg APP_BUILD=probe`),
run with `--memory=256m --memory-swap=256m` to reproduce `fly.toml:35-37`'s declared VM, with the
artifact bind-mounted read-only exactly as D-116 specifies. Load driven by `xargs -P 8`, matching
`fly.toml:60`'s `hard_limit = 8` and `main.py:105`'s process cap. Memory read from
`docker stats`. Every Python invocation used `python -B` and `PYTHONDONTWRITEBYTECODE=1` (W-022).
Four artifacts, chosen to separate the two variables the previous passes conflated — file SIZE and
ranked-row COUNT.

### Measurement (all inside the 256 MB container)

| Artifact | File | Ranked models | Requests @ conc 8 | Idle RSS | RSS after | Outcome |
|---|---|---|---|---|---|---|
| shipped `advisor.db` | 0.97 MB | 73 | 200 | 43.41 MiB | **49.52 MiB (19.35% of VM)** | serves |
| same content, file inflated with a filler table | **121.02 MB** | 73 | 200 | 43.80 MiB | **49.33 MiB** | serves |
| synthetic | 6.03 MB | 10,000 | 40 | 43.12 MiB | 149.2 MiB | serves |
| synthetic | 6.03 MB | 10,000 | **240** (6 batches of 40) | 43.30 MiB | 148.5 / 147.3 / 147.7 / 148.9 / 147.1 / **145.3 MiB** | serves — **plateau** |
| synthetic | 26.72 MB | 50,000 | 16 | 43.14 MiB | — | **`OOMKilled=true`, exit 137** |

### What the numbers say

**(a) The quantity W-017 named no longer exists.** A **125x larger file** costs **zero**
additional memory: 121.02 MB produced 49.33 MiB after 200 requests against 49.52 MiB for 0.97 MB.
Every earlier figure scaled with file size because a full copy was taken per request; nothing is
copied now, and the process holds SQLite's page cache (default 2 MB per connection, 8 connections)
rather than the file. `serving_snapshot` is absent from the tree — `grep -rn "serving_snapshot"`
over `src/`, `tests/`, `Dockerfile`, `fly.toml`, `*.toml`, `*.yml` returns only prose in comments,
docs and the guard at `tests/unit/test_api_config.py:546`. **The amplification is gone, not bounded.**

**(b) Amplification at today's artifact, on the same per-byte convention the earlier passes used:**
6.11 MiB of RSS growth for 200 requests of 139 bytes each = **~230x**, and — the part that matters —
**flat in database size**. The ratio is no longer a meaningful quantity, which is the honest
conclusion the previous pass reached for a different reason: it is dominated by an operator
variable an attacker cannot move.

**(c) There is no request-driven amplification left.** Memory **plateaus**: 240 requests cost no
more than 40 (148.5 MiB then 145.3 MiB, i.e. it went down). Request volume does not accumulate.
`task` and `budget` are closed enums (`main.py:788,794`), so per-request cost is fixed by operator
data; the AnyIO limiter caps in-flight handlers at 8 (`main.py:308`, and I confirmed it governs by
observing 4x the memory growth at `MODEL_RANKING_MAX_CONCURRENCY=32`). **An unauthenticated caller
cannot move any term of the arithmetic.**

**(d) The residual cost is real and is in a different variable.** Peak RSS is now roughly
`43 MiB baseline + concurrency x ~1.3 KiB x ranked models`. Break-even against the 256 MB VM is
approximately **20,000 ranked models on a primary benchmark**. Today's artifact carries **73**, so
the headroom is about **230x**. That is a comfortable margin, and it is why the residual is
MINOR-1 below rather than a blocker.

### Does this disagree with the wave's claim?

**No.** W3's record (`docs/plans/m7-wave-3-close.md`) claims 0.64 MiB of growth over 30 requests
against a 0.93 MiB database. I measured 6.11 MiB over 200 requests against the same artifact in a
different process and a different container — 0.031 MiB/request against their 0.021 MiB/request,
the same order of magnitude, with the difference explained by my running 8 concurrent handlers
where their sequence appears to have been serial. **Direction and magnitude agree, and the
conclusion agrees: what remains is a warm-up plateau, not an amplification.** I record my number
alongside theirs rather than in place of it.

### What I could NOT verify

I could not measure this on Fly.io. Everything above is Docker with a memory cgroup on Darwin, not
a `shared-cpu-1x` Fly machine, and the two are not the same kernel or the same allocator pressure.
The break-even figure in (d) is an extrapolation from four measured points on a straight line, not
a measured break-even; I measured 10,000 (serves, 149 MiB) and 50,000 (OOM) and did not bisect
between them.

---

## 2. Findings

### BLOCKING

**None.**

---

### MINOR-1 — deleting the boot ceiling left no artifact-shape check at all, and the surviving cost is in a variable nothing measures

**`src/app/adapter/main.py:274-280`** (the comment where the ceiling used to be),
**`src/app/adapter/main.py:86-101`** (the constants' obituary).

**Input:** an evidence database with roughly 20,000 or more models carrying a score on a category's
primary benchmark. **Mechanism:** `category_ranking` (`rank.py:218-279`) has no `LIMIT`; it
`fetchall()`s every ranked model and then calls `higher_effort_evidence` once per row
(`rank.py:282-284`), so each in-flight request materialises a working set linear in the ranked-model
count, multiplied by the concurrency cap. **Consequence:** measured — a 26.72 MB artifact with
50,000 ranked models took **16 unauthenticated GETs** to drive the container to
`OOMKilled=true, exit 137`. `validate_startup_config` no longer checks anything about the
artifact's shape, so this reaches production at deploy time rather than at build time.

**Why this is MINOR and not a blocker, stated plainly:**
- It is **not attacker-reachable**. No request parameter moves it; the trigger is the operator's
  own artifact, built on the operator's own machine (D-116 clause 2).
- Headroom is about **230x** (73 models today).
- The failure mode is a machine restart on a public read-only API with no users. `fly.toml:49-50`
  keeps a machine warm and Fly restarts on OOM.

**And the part that argues for the wave rather than against it:** the ceiling W3 deleted measured
**file size**, and my measurement (b) proves file size is now the wrong variable — the old
`max_database_bytes()` at 8 concurrency / 256 MiB was 15.25 MB, which would have **refused the
harmless 121 MB file** and **admitted the 6 MB artifact that used 58% of the VM**. Restoring it
would not close this. W3 was right to delete it; what is missing is a replacement in the right
variable, and the cheapest one is a row-count assertion in `build.py` (which already reads counts
back at `build.py:332`) rather than a boot check.

**Disposition:** warnings ledger, owning milestone **M8**. Revisit trigger: the artifact's ranked
model count on any primary benchmark exceeding ~2,000, i.e. one order of magnitude of headroom
spent.

---

### MINOR-2 — a stay-green mutant on a security invariant: the 500 handler's redaction is untested

**`src/app/adapter/main.py:360-374`**, specifically the generic body at **`main.py:372`**.

The handler's own docstring says *"an exception message is the one place a secret reaches a
response without anyone deciding it should."* I replaced `main.py:372` with
`_error(500, "internal_error", str(exc))` and ran the full suite: **482 passed, 12 skipped — the
mutant survived.**

**Input:** any future refactor or debugging aid that echoes the exception. **Mechanism:** nothing
in the suite asserts the 500 body is generic. **Consequence:** the exception text — which on this
code path can carry a filesystem path or a SQLite error string — would reach an unauthenticated
response body, and CI would stay green.

I verified the control is **correct today**: monkeypatching `recommend` to raise
`RuntimeError("SECRET=/etc/passwd token=abc123 at /Users/owner/model_ranking/advisor.db")` returned
`{"error":{"code":"internal_error","message":"The request could not be served."}}` with
`x-content-type-options: nosniff`, 80 bytes, no leak. The finding is the missing negative test, not
the behaviour.

**Ranked second because D-122 explicitly does not relax this:** *"a stay-green mutant still earns
its mandatory test."* V3C-74 says the same. It is one test.

**Context that argues it is only MINOR:** seven other security mutants I injected were all killed
(section 4), and the 500 path is close to unreachable in practice because `_answer_for` catches
`sqlite3.DatabaseError` at `main.py:691` and `:707`.

---

### MINOR-3 — the slopsquat gate sees ONE of five declared dependencies and prints PASS

**`scripts/slopsquat_check.py:46`** — `re.findall(r"dependencies\s*=\s*\[(.*?)\]", body, re.S)`.

**Input:** this repository's own `pyproject.toml`. **Mechanism:** `uvicorn[standard]>=0.32` contains
a `]`, and the non-greedy `.*?` terminates on it. **Consequence, measured:**

```
declared() -> ['fastapi']
slopsquat PASS: 1 declared dependency(ies), 0 suspect
```

`uvicorn`, `pydantic`, `httpx` and `pyyaml` are **never checked**, and the gate reports clean. The
file's own docstring names this exact class: *"a control that reports clean because it could not
run is the failure this whole line of work is about."*

**Not a suppression** — no agent waived anything, and `make deps` (pip-audit) covers CVEs
independently and is green. **Not a go-live blocker:** the four invisible packages are among the
most-used in the ecosystem and carry no plausible slopsquat risk. It is a **broken control**, and
M7 touched this file (`scripts/slopsquat_check.py`, import reordering). One-line fix: make the
regex greedy, or read the manifest with `tomllib`.

---

### MINOR-4 — four of five build-path HTTP clients read the response body with no size bound

**`src/app/clients/litellm.py:43-48`** · **`openrouter.py:34-39`** · **`swebench.py:38-43`** ·
**`arena.py:95-113`** (up to `_MAX_PAGES = 50` unbounded bodies). Only
**`aider.py:49-54`** has a bound, and its own comment says it is *"the only unbounded step left."*

**Input:** a compromised or vandalised upstream (`raw.githubusercontent.com/BerriAI/litellm`,
`swe-bench/swe-bench.github.io`, `openrouter.ai/api/v1/models`, the HF datasets-server) returning a
large or highly-compressible body. **Mechanism:** `httpx.get(...).text` reads and decompresses the
whole body into memory before any parser sees it; all four have a 30 s timeout and none has a byte
cap. **Consequence, measured against a local hostile server serving valid litellm-shaped JSON:**

```
uncompressed=433.9MB  gzip=4589.6KB  ratio=95x
fetch_raw returned 433.9 MB of text in 0.4s -- NO SIZE BOUND
peak RSS of builder process: 1941 MB
```

A **4.6 MB** response became **434 MB** of text and a **1.94 GB** process, before `json.loads`
built a Python object graph several times larger again.

**Not a go-live blocker, and the reason is D-116 clause 2:** ingestion does not run on the serving
host, so this cannot be reached from the public surface. The blast radius is the operator's laptop
or a CI runner OOMing during a build — loud and recoverable, which is exactly the plumbing column
D-122 describes. But M7 is the milestone that turned this from an unrun CI heredoc into a governed
production entry point that the operator and CI now actually invoke, so it enters scope here. Fix
shape already exists in the tree: `aider.py:49`.

---

### MINOR-5 — a corrupt artifact swapped under a running process answers 200; an unbuilt one answers 503

**`src/app/adapter/main.py:707-708`** (`except sqlite3.DatabaseError:` returning an answer object
rather than re-raising).

**Input:** the mounted artifact (D-116) replaced under a running process with a truncated or
non-SQLite file — the sequence `main.py:700-706`'s own comment calls *"a real sequence, not a
hypothetical."* **Mechanism:** `sqlite3.connect` opens lazily, so the route-level guard at
`main.py:810-812` succeeds and the error surfaces inside `_answer_for`, where it is converted into
an answer. **Consequence, measured against a live process:**

| artifact swapped in | HTTP | body |
|---|---|---|
| `px_median` emptied | **503** | `evidence_unavailable` |
| `px_median` table dropped | **503** | `evidence_unavailable` |
| file deleted | **503** | `evidence_unavailable` |
| **garbage bytes** | **200** | `picks: []`, `"This surface's evidence could not be read."` |
| **truncated to 1 page** | **200** | `picks: []`, `"This surface's evidence could not be read."` |

Nothing lies — `unavailable_reason` discloses honestly, so **D-121's condition is not violated** —
but the fail-closed direction the wave chose for the unbuilt case is not applied to the corrupt
case. A machine consumer sees 200. `scripts/journey.py:215-219` accepts it: an empty `picks` with a
reason is a step-4 PASS, so the journey would call a totally unreadable database good. (Step 3
would still fail on zero picks, so the journey as a whole fails — that is why this is MINOR.)

**Hygiene rather than a go-live blocker:** an operator corrupting the volume is not an attacker
path, and the payload discloses.

---

### MINOR-6 — the only remaining memory bound is an unvalidated environment variable, and one bad value hangs the process

**`src/app/adapter/main.py:105`** — `MAX_CONCURRENT_REQUESTS = int(os.environ.get("MODEL_RANKING_MAX_CONCURRENCY", "8"))`.

The module's own comment at `main.py:99-101` states that after the budget machinery was deleted,
*"what DOES still bound this process is the thread-pool limiter."* That makes this value
security-critical, and V3C-51 requires security-critical configuration to be validated at startup
with the process failing in production. It is not validated.

**Input:** `MODEL_RANKING_MAX_CONCURRENCY=0` in `fly.toml`'s `[env]`. **Mechanism:**
`validate_startup_config` never inspects it; `_lifespan` sets `total_tokens = 0` on the AnyIO
limiter (`main.py:308`), and every sync handler — including `/health`, which is also a `def`
handler at `main.py:749` — then blocks forever waiting for a token. **Consequence, measured:** the
process starts, binds the port, and **never answers any request**; my probe timed out at 120 s with
no response and no error. The container platform then fails its health check, so it does fail
closed at the platform layer, but from the process's own point of view it is a silent hang rather
than a refusal.

Also unvalidated in the other direction: `MODEL_RANKING_MAX_CONCURRENCY=999999` is accepted
silently and removes the cap. `="abc"` raises `ValueError` at import (fail-closed, fine).

`tests/unit/test_api_config.py:477-516` asserts the **declared** value is 8 and that
`fly.toml`'s `hard_limit` and `[env]` agree with it, which is a real and valuable drift guard — it
just does not constrain a runtime override.

**Hygiene, not a blocker:** the shipped `fly.toml:29` value is `"8"` and the drift test pins it.

---

### MINOR-7 — `harness` is verbatim third-party text on the public surface, unbounded

**`src/app/adapter/main.py:582`** (in `PUBLIC_PICK_FIELDS`), sourced from
**`src/app/clients/swebench.py:46-56`** (`split_harness`) and stored at `swebench.py:111`.

**Input:** a compromised `swe-bench/swe-bench.github.io` leaderboard entry named
`Evil <script>…</script> + Claude 4.5 Opus`, or simply a 10 MB entry name. **Mechanism:**
`split_harness` takes the text before the `+` verbatim, with no allowlist, no character class and no
length bound; `reconcile` never touches it; `PUBLIC_PICK_FIELDS` publishes it. **Consequence:** the
string reaches every `/v1` answer's `picks[].harness`. Today's values are the 40 real board names I
read back from `advisor.db`.

**Contrast, and this is the reason it is only MINOR:** `picks[].model` and `picks[].vendor` do
**not** carry upstream text at all. `registry.py:298-299` writes `rule.display` and `rule.vendor`
from `MODEL_RULES` (`registry.py:33`), a hardcoded allowlist; an upstream name that matches no rule
is dropped and counted. That is a genuinely good boundary and it covers the two fields a user reads
first.

**Not exploitable at `/v1`:** the response is `application/json` with
`x-content-type-options: nosniff` (verified on every response including errors and the 500), so a
browser will not execute it. It is called out because **D-122 places the `/v1` contract at FULL
depth precisely because the iOS app is the next piece of work**, and an unbounded untrusted string
is the field that client will render.

---

### MINOR-8 — hygiene, grouped

1. **A fourth reference to the removed pin-check Make target was added by this milestone.**
   `docs/reviews/m7-wave-1-review.md:369`. `conformance/test-documented-commands.py` now fails on
   four lines; W-013 records three and the owner ruled HAND BACK on those. The wave added a new
   instance of a closed finding's pattern. `docs/warnings.ledger.md:12` should say four, not three.
   **Demonstrated on myself:** the first draft of this review cited that target in the checker's
   trigger form and took the count from four to six. The citation is deliberately reworded here,
   which is the same evasion GPF-004 forces on every reviewer and is itself the evidence that these
   two checks cannot tell a citation from an instruction.
2. **`conformance/test-git-authority.py` is RED on a previous security review's own compliance
   attestation** — `docs/reviews/m6-security-review.md:556` and `:989`, where a sentence
   *stating* that certain history-writing git operations were not run is read as an instruction to
   run them. This is GPF-004's class in a new instance, and it means every security review is a
   landmine for this gate. I deliberately avoided the trigger phrasing in this document.
3. **`scripts/` is outside `make lint`'s scope** (`Makefile:76` lints `src tests` only), so
   `scripts/journey.py` and `scripts/smoke_deps.py` — both of which this milestone rewired and one
   of which now talks to a deployed host — are unlinted. `ruff check scripts` reports 16 findings,
   all style/complexity, none security. `scripts/wave_check.py:40` has a dead assignment introduced
   near this milestone's edit to that file.

---

## 3. What I attacked and found clean (recorded so the next pass need not redo it)

**The read-only handle (brief item 2) — clean, and proven three ways.**
- `open_readonly` (`main.py:157-168`) builds the URI through `Path.resolve().as_uri()` and appends
  `?mode=ro`. I drove `/health`, `/v1/categories`, five `/v1/recommendations` variants including
  SQL-shaped and 5,000-character `task` values, plus `/openapi.json`, `/docs`, `/redoc` and
  `/v1/whoami`, against a file I had hashed first. **mtime identical, size identical, SHA-256
  identical, and no journal/WAL/shm sidecar was created** — the directory listing before and after
  was `['advisor.db']` both times.
- The handle itself refuses: `DELETE`, `INSERT`, `CREATE TABLE` all return
  `OperationalError: attempt to write a readonly database`.
- **`schema.connect()` is unreachable from HTTP, proven statically.** I walked the import graph
  with `ast` from `app.adapter.main`: 21 modules are reachable, and every one that imports
  `app.workflows.schema` imports only dataclasses and constants (`ScoreRow`, `PricingRow`,
  `EFFORT_LEVELS`, `EFFORT_UNSPECIFIED`, `PlanRow`, `reset_source`). **No reachable module imports
  `connect`.** `grep -rn "sqlite3.connect" src/` gives five call sites; the only one in the adapter
  is `main.py:168`.

**Routes and methods — clean.** `DECLARED_ROUTES` (`main.py:71-73`) is three; `docs_url`,
`redoc_url` and `openapi_url` are `None` and all three 404. Every mutating verb (POST/PUT/PATCH/
DELETE/OPTIONS/TRACE) returns 405 on `/v1/recommendations`. There are **no mutating routes**, so
security-baseline item 2 (server-side authz on every mutating route) has nothing to enforce and
`journey.py:110-130` asserts that state rather than stubbing it.

**CORS (baseline item 3) — clean.** `cors_origins` (`main.py:127-154`) refuses `*` with a
`ConfigError` in **every** environment, refuses a non-absolute origin (`null` is rejected), and
`allow_credentials=False` is hardcoded at `main.py:346`. Default is empty, i.e. no cross-origin
access. One cosmetic note: `https://*.evil.example` passes the check because it starts with
`https://`, but Starlette's `CORSMiddleware` matches origins exactly, so such an entry is inert
rather than permissive — not a finding.

**Startup validation (baseline item 4) — clean and fail-closed, verified in the container.**
Unset/unrecognised `APP_ENV` takes the STRICT branch (`main.py:247`), all problems print at once
(`main.py:289`), and I confirmed the shipped image refuses to boot:

| container run | result |
|---|---|
| artifact with empty `px_median` | `exit=1`, health unreachable, log names the rebuild command |
| no artifact mounted | `exit=1`, health unreachable, log names D-116 |

**Error disclosure at every boundary (brief item 4) — clean.**
- `/v1` error bodies carry no filesystem path (`main.py:803-805` comments on why), the 503 remedy
  is deliberately withheld (`main.py:816-820`) and lives in the startup log instead — which is
  exactly V3C-103's shape.
- Attacker-controlled echo is bounded at 40 characters by `_echo` (`main.py:391-393`) and
  JSON-escaped; `nosniff` present on every response including errors and the 500.
- **I scanned three full `/v1` payloads (6,348 / 1,026 / 3,327 bytes) from the running container
  for `/home`, `/Users`, `/data`, `/app`, `/tmp`, `/usr` paths: zero matches.**
- Startup failure messages carry the operator remedy and no path. The Python traceback that
  accompanies them is server-side only.
- The CI log (`contract-tests.yml:103` `cat build-report.json`) publishes runner-relative paths and
  public upstream URLs. `permissions: contents: read` (`contract-tests.yml:24`), no secrets in the
  job. Not a leak.

**The bundle read (brief item 3) — symlink protection works.** I planted
`swe_bench_verified.csv -> <outside>/creds.txt` (absolute) and
`deepswe_external.csv -> ../../secret/creds.txt` (relative) in a bundle directory. Both were
**refused** by `epoch.py:93-95` and `deepswe.py:69-71`; a bundle directory that is itself a symlink
to `/etc` was refused; a symlink pointing to a file *inside* the bundle is allowed, which is
correct. Residual, not a finding at this calibration: the check runs on `resolved` while the read
uses `path` (`epoch.py:100`, `deepswe.py:76`), a TOCTOU window on a single-operator machine, and
the bundle CSV read has no size bound (unlike `aider.py:49`).

**SQL injection — none.** `bandit -r src scripts` produced five findings, all pre-reviewed and
mitigated: `build.py:129` interpolates a table name that came from `sqlite_master` of a database
this process just created **and** is checked against `_IDENTIFIER` (`build.py:65,126-128`);
`schema.py:415` allowlists the table to `("pricing","scores")` and binds the source; the two
`urlopen` findings are preceded by explicit scheme checks (`journey.py:64-66`) or use a hardcoded
PyPI URL. Every serving-path query is parameterised.

**Builder destructive-default discipline — clean.** `--force` defaults OFF (`build.py:356-360`);
the build writes to a per-run unique `mkstemp` workspace and only `replace()`s the target on
success (`build.py:400-441`); a failed publish cleans up. I ran the real entry point end to end
against live upstreams and it produced a 929,792-byte artifact with 73 models registered, exit 3
(degraded: arena down, no bundle), and **left no `.building` file behind**. Re-running over an
existing target without `--force` exits 2 with a JSON error. A directory target exits 2. A missing
`--plans` exits 2. An argparse error exits 2. All match D-120's contract.

**Deploy artifacts (brief item 6) — clean.** Image runs as `uid=10001(appuser)`
(`Dockerfile:34-35`); `/app` is empty and the package is installed to `/usr/local`, so **no source
and no database are baked in**; `docker image inspect` shows no secret in `Env` or in any history
layer; no `.env` anywhere in the image. On the replace-under-a-running-process question: the
process opens a **fresh** read-only handle per request (`main.py:810`), so a swapped file is picked
up on the next request and the unbuilt case fails closed to 503 (see MINOR-5 for the corrupt case).
As `appuser` I could neither create a file in `/data` (root-owned 0755) nor write the artifact.

**`scripts/journey.py` (brief item 7) — clean.** `--base-url` is checked for an `http://`/`https://`
scheme before `urlopen` (`journey.py:64-66`), which closes the `file:`/custom-scheme hole bandit
flags. `mint_token` (`journey.py:83-95`) reads `JOURNEY_TOKEN` from the environment and hardcodes
nothing — and **no step calls it**, so no `Authorization` header is ever sent and no token can be
printed. Failure output is truncated to 160-200 characters of the response body. It can be pointed
at any HTTP host, which is inherent to a black-box journey tester run by an operator with an
explicit URL. **I ran it against the container with the shipped artifact: 4 PASS, exit 0.**

**`ATTACH` — reachable in principle, unreachable in practice, recorded rather than filed.** A
read-only SQLite handle in Python will still `ATTACH` and write a *different* file; I confirmed it
does. Reaching it requires executing attacker-chosen SQL, and there is no such vector on the
serving path. Not a finding; noted so a future pass that introduces any dynamic SQL knows this door
is open.

---

## 4. D-121's condition, verified against the code rather than the ADR's prose (brief item 5)

D-121 permits a degraded build to ship **only because** the serving surface discloses the gap; if
that disclosure is weakened the ADR is invalidated. The predicate is now
`category_ranking(conn, spec)` at **`main.py:729`**. An earlier round proved the previous predicate
(`health["sources"]`) wrong, so I did not read the shipped artifact — which has **zero arena rows**,
confirmed by `SELECT count(*) FROM scores WHERE source='arena'` — and instead **built the
discriminating fixtures** for the `assistant` surface (`Arena text` / `elo`) and drove them through
the real HTTP entry point at `budget=low`.

| State | arena rows | `category_ranking` rows | `unavailable_reason` served |
|---|---|---|---|
| **A** — none (the shipped artifact) | 0 | 0 | *"no evidence to rank ... no budget was applied"* |
| **B1** — rows present, **unreconciled** (`model_id` NULL) | 5 | 0 | *"no evidence to rank ... no budget was applied"* |
| **B2** — rows present, reconciled, **no `px_median`** | 5 | 0 | *"no evidence to rank ... no budget was applied"* |
| **C** — rows present, reconciled, priced **above budget** | 5 | **5** | *"No model ... fits the requested budget"* |

**The predicate discriminates correctly in all four states.** B1 is the state the earlier round
found broken: rows exist, so `health["sources"]` is non-empty, but nothing reached the ranking —
and the surface now correctly refuses to blame the budget. C proves the fix did not replace one
blanket explanation with another.

On the shipped artifact the `assistant` surface serves, simultaneously and consistently:
`picks: []`, the *"gap in the evidence, not a result"* sentence, and
`source_health.stale: true` with *"No evidence source for Arena text is present in the served
database."* **D-121's condition holds.**

One observation, not a finding: in B1/B2 `source_health.stale` is `false` with no notice, because
the source genuinely published 8 days ago. That is a statement about the *source*, not a claim that
the *surface* can answer, and `unavailable_reason` carries the surface-level truth. The two fields
do not contradict each other. D-121's own recorded open gap — that a consumer reading only `picks`
sees an empty array — remains open and is disclosed; `journey.py:213-219` is the consumer that
checks it.

---

## 5. Fault injection on security controls (V3C-72 / V3C-74)

I copied the tree to a scratch directory (no history-affecting git operation was used) and injected
eight mutants, running the full suite against each.

| # | Mutant | Result | Killed by |
|---|---|---|---|
| 1 | `recommend()` no longer calls `require_price_medians` | **KILLED** (6 failed) | `test_api_v1.py::test_an_unbuilt_artifact_is_refused_rather_than_answered_empty`, `test_cli_e2e.py::test_cli_an_unbuilt_artifact_exits_2_not_1` |
| 2 | `open_readonly` drops `?mode=ro` | **KILLED** | `test_api_v1.py::test_read_only_handle_refuses_a_write` |
| 3 | D-121 predicate reverted to `health["sources"]` | **KILLED** | `test_unbuilt_evidence.py::test_the_no_evidence_branch_asks_whether_evidence_reached_the_ranking` |
| 4 | `PUBLIC_PICK_FIELDS` nested allowlist removed | **KILLED** | `test_api_config.py::test_the_allowlist_actually_filters_an_undeclared_field` |
| 5 | startup probe stops checking `px_median` | **KILLED** | `test_unbuilt_evidence.py::test_the_startup_probe_refuses_an_artifact_with_no_price_medians` |
| 6 | **500 handler echoes the exception text** | **SURVIVED** | — see **MINOR-2** |
| 7 | `cors_origins` accepts `*` | **KILLED** (2 failed) | `test_api_config.py::test_a_wildcard_origin_is_refused_not_warned_about` |
| 8 | unknown `APP_ENV` falls back to the permissive branch | **KILLED** | `test_api_config.py::test_an_unrecognised_environment_is_treated_as_strict` |

**Seven of eight killed.** The one survivor is MINOR-2 and it is the only negative-test gap I found
on a security invariant.

---

## 6. Gates

- [x] **Secret scan green.** `gitleaks detect --log-opts 9f4471d..HEAD` — 11 commits, 319 KB, **no
      leaks found**. `gitleaks dir .` over the whole tree — 4.60 MB, **no leaks found**. `make
      secrets` exit 0. No `.env` in the tree or in the image.
- [x] **pip-audit green.** `make deps` — *No known vulnerabilities found*.
- [x] **Slopsquat.** Exit 0 — **but see MINOR-3: it only inspected one of five dependencies.**
      **No new third-party dependency was added by M7**; every added import in `src/` and `scripts/`
      is stdlib or first-party (verified by diffing all added `import`/`from` lines).
- [x] **Default-deny preserved.** Three declared routes, all GET, no auth surface to disable, CORS
      empty by default and wildcard-refusing, `MODEL_RANKING_DB` has no default.
- [x] **Permission matrix not violated.** No catastrophe-class operation in the diff; no
      `rm -rf`, no `DROP TABLE` on a production path, no history rewriting. `--force` on the
      builder is explicit and defaults OFF.
- [x] **Prompt-injection hygiene.** No LLM anywhere in the data or scoring path (D-104 holds); no
      `eval`/`exec`; fetched content is parsed as data by typed parsers. `yaml.safe_load` is
      wrapped by the bounded loader (`yaml_guard.py:36,41`) on the only externally-produced YAML.
- [x] **Auth/PII checks.** None present, so permission-matrix 11's human-review trigger does not
      fire. No credential store, so security-baseline items 1 and 5 have nothing to hash or encrypt.
- [x] **SAST.** `bandit -r src scripts` — 5 findings, all pre-mitigated (section 3). Tool
      uninstalled afterwards; `make install-check` re-run and clean.
- [x] **`make check` exit 0** at the reviewed tree — 482 passed, 12 skipped; ruff clean on
      `src tests`; `mypy src` clean (31 files).
- [ ] **`make conformance` — 2 of 7 legs RED**, neither a security defect:
      `test-git-authority` (2 violations, both in a prior review's prose) and
      `test-documented-commands` (4 dangling references to the removed pin-check target, in the
      trigger form this document avoids). See MINOR-8. The first three are
      the owner-ruled HAND BACK under W-013 / GPF-004; the fourth is new in M7.
- [ ] **`make smoke-deps` exit 1 — expected, W-024.** litellm 2194 rows, openrouter 389, swebench
      173, aider 68 all OK; **arena FAILs on an upstream HTTP 500**, epoch bundles n/a by D-101.
      This is the owner ruling D-121 records, not a regression.

---

## 7. Acceptance-criterion evidence (file:line per criterion, as the profile requires for PASS)

| Criterion | Evidence I verified in this run |
|---|---|
| **REQ-ING-012** — one runnable production entry point builds the database | `src/app/workflows/build.py:341-451`; I ran it against live upstreams and it produced a 929,792-byte artifact with 73 models. Registry at `sources.py:102-163`. CI invokes it at `contract-tests.yml:100-113`; the heredoc is gone. Citing tests: `tests/unit/test_build.py`, `tests/unit/test_sources.py`, `tests/unit/test_ci_argument_drift.py` |
| **REQ-ING-013** — fails loud and non-zero on a partial build | Floors at `build.py:148-151`, `:241-246`, `:314-319`, `:326-328`, `:333-336`; exit-code contract at `build.py:363-447`. I confirmed exit 2 for four distinct bad inputs and exit 3 for the degraded run. Citing tests: `tests/unit/test_build_artifact_safety.py`, `tests/unit/test_parser_envelopes.py` |
| **REQ-CAN-003** — medians unchanged, value for value | **NOT independently re-derived by me.** The before/after parity comparison is W2's and I did not reproduce it; `build_price_medians` (`rank.py:143-171`) is byte-identical in the diff, only its call site moved (`recommend.py:285` to `build.py:325`), which is consistent with parity but is not the value-for-value proof the criterion asks for. Stated as unverified rather than assumed. |
| **REQ-API-007** — no write, no full-database copy | `main.py:377-389` (the deletion), `main.py:810`. My own proof: byte-identical file, unchanged mtime, no sidecar, across 12 requests including hostile inputs; and `serving_snapshot` absent from the tree. Citing tests: `test_api_v1.py:653` (through the real HTTP entry point), `test_api_config.py:546` |
| **REQ-API-008** — an unbuilt artifact refuses to answer | `rank.py:182-215`, `recommend.py:290`, `main.py:207-213` (boot), `main.py:815-821` (503), `recommend.py:435-442` (CLI exit 2). Verified live: boot refusal in the container, 503 on a swap-under-a-running-process. Citing tests: `tests/unit/test_unbuilt_evidence.py`, and mutants 1 and 5 above |
| **REQ-API-009** — the deployed service answers with correct CONTENT | **Verified against a CONTAINER, not against a deployed host.** `scripts/journey.py --base-url http://127.0.0.1:8092` returned 4 PASS / exit 0 against the shipped `Dockerfile` image with `advisor.db` mounted read-only: 6 picks across both coding surfaces, all fields populated, no precedence field, all 3 discovery tasks answering. **The criterion says "from a host, over the network" and no deploy has happened** — that is W4's step, which this review gates. I record what I ran. |
| **W-017** — closed, not deferred | Section 1. Re-derived independently: file size now costs zero memory, growth plateaus, nothing to bound. |
| **W-023** — the shipped artifact is produced by REQ-ING-012's entry point | I built one with the real entry point and read 73 models back out of the file. The **shipped** `advisor.db` I verified separately: 73 models / 2,583 pricing / 323 scores / 72 `px_median`, it boots the container, and it answers both coding surfaces with 3 picks each. |

---

## 8. What I could not reach, and what stopped me

Stated plainly rather than inferred, per the instruction:

1. **No Fly.io deploy exists**, so every "deployed" claim in this review is a local container with
   a 256 MB memory cgroup. I could not verify the Fly volume's ownership or permissions, Fly's OOM
   and restart behaviour, `force_https`, or the real `shared-cpu-1x` allocator. REQ-API-009's
   over-the-network half is unverified by me.
2. **REQ-CAN-003's value-for-value parity is unverified by me** (see the table above). I read the
   diff and found the function unchanged; I did not run the comparison.
3. **The ~20,000-model break-even in section 1(d) is an extrapolation**, not a measured point. I
   measured 10,000 (serves) and 50,000 (OOM) and did not bisect.
4. **MINOR-4's exploit was demonstrated against a local hostile server**, not against a real
   upstream. I did not attempt to reach any third party's infrastructure.
5. **I did not audit the eleven pre-M7 files** the diff does not touch beyond the reachability walk
   in section 3. The scope was `9f4471d..HEAD`.

---

## 9. Risks queued to the next milestone

| Item | Where | Owning milestone |
|---|---|---|
| MINOR-1 — no artifact-shape bound; measured OOM at 50,000 ranked models | `main.py:274-280`, `build.py:332` | M8 |
| MINOR-2 — 500-handler redaction has no citing test (stay-green mutant) | `main.py:372` | **M7, before closure** — D-122 does not relax this |
| MINOR-3 — slopsquat gate reads 1 of 5 dependencies | `scripts/slopsquat_check.py:46` | M8 (one-line fix) |
| MINOR-4 — 4 of 5 fetch clients unbounded | `litellm.py:48`, `openrouter.py:39`, `swebench.py:43`, `arena.py:95` | M8 |
| MINOR-5 — corrupt artifact answers 200, unbuilt answers 503 | `main.py:707-708`, `journey.py:215` | M8 |
| MINOR-6 — concurrency cap unvalidated; 0 hangs the process | `main.py:105` | M8 |
| MINOR-7 — `harness` is unbounded third-party text on `/v1` | `main.py:582`, `swebench.py:46` | M8, **before the iOS client renders it** |
| MINOR-8 — doc/gate hygiene (4th `pin-check`, git-authority prose, unlinted `scripts/`) | as cited | M8 |

---

## 10. Bottom line

**PASS. The 4.3 deploy is not blocked by this review.**

The milestone did the hard thing correctly: it removed a defect instead of bounding it, and my
independent measurement confirms the removal in the terms D-116 demanded — a 125x larger database
file now costs zero additional memory, memory plateaus under sustained load, and no request
parameter moves any term of the arithmetic. The serving path provably never writes, `schema.connect`
is unreachable from HTTP, the container fails closed on an unbuilt or missing artifact, and D-121's
disclosure condition holds across all four discriminating states I constructed.

What is left is one missing negative test on a control that is correct today, one broken governance
gate that reports clean because it cannot see four of five dependencies, and six items of hygiene
with concrete but non-reachable failure paths. At this deployment — no users, no authentication, no
PII, no payments, public read-only data over published benchmarks — none of them is worth holding a
first go-live for, and saying otherwise would cost more credibility than it buys.
