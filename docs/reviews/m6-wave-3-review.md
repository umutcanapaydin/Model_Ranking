---
record_type: review
id: m6-wave-3-review
status: ratified
date: 2026-08-17
---
# Wave 3 Code Review (m6)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author any line of this wave)
**Date:** 2026-08-17
**Commit range:** `67fd92b..915e97b` + working tree (one doc-only uncommitted edit)
**Source:** A (baseline `subagent-profiles/Code-Reviewer.md` v4.0, read from the protected base ref)
**Risk tier:** HIGH (migration, auto-escalated — V3C-78)

**V4C-03/04 fields:** author-family / reviewer-family unknown to this seat; recorded as *not
established* rather than asserted. Fresh-context assertion: this seat authored none of the wave's
code and read the plan and the profile before the diff.

---

## Verdict

**BLOCKING** — 4 BLOCKING, 11 MINOR.

The wave's engineering is, on the whole, careful: the migration is genuinely atomic, the expansion
guard's arithmetic is correct and the fix it replaced really was wrong, and the W-009 reconciliation
does what it says. What it does not have is proof for the two clauses it declares closed. Two of the
four BLOCKINGs are the same defect the wave already caught once in itself — a citing test that proves
the mechanism and asserts nothing about the served behaviour — and one of those has a mutant that
survives deletion of the entire feature.

---

## Findings

### BLOCKING (must fix before next wave)

---

**BLOCKING-1 — `validate_startup_config` is called by nothing. REQ-API-006's startup clause is unmet in the shipped process (V3C-51, V3C-73/F6).**

`src/app/adapter/main.py:115` defines it. `grep -n` over `src/` returns exactly one line — the
definition. The only invocations in the repository are four test calls.

```
src/app/adapter/main.py:115:def validate_startup_config(env: str | None = None) -> tuple[str, ...]:
tests/unit/test_api_config.py:60:        validate_startup_config(env="production")
tests/unit/test_api_config.py:73:        validate_startup_config(env="production")
tests/unit/test_api_config.py:86:    problems = validate_startup_config(env="development")
tests/unit/test_api_config.py:98:        validate_startup_config(env="development")
```

Proven against the live surface — production environment, no database, no build stamp:

```
$ env -u MODEL_RANKING_DB -u APP_BUILD APP_ENV=production python
>>> from app.adapter import main as adapter          # no ConfigError
>>> TestClient(adapter.app).get("/health")
200 {'status': 'ok', 'version': '0.1.0', 'build': 'unknown'}
>>> TestClient(adapter.app).get("/v1/categories")
200 {'categories': [...]}
```

The process boots, answers `/health` with `build: unknown`, and serves `/v1`. The plan's criterion
(`docs/plans/m6-plan.md:116`) is "security-relevant config is validated at startup and **the process
refuses to serve in production if it is wrong**". It does not refuse. Permission-matrix §11 lists
"security config not validated at startup (V3C-51)" as a BLOCKING web/API baseline failure.

The docstring at `src/app/adapter/main.py:116` states the function checks the config "once, at
import". It could not have: `_db_path`, which it calls at line 126, is not defined until line 231 —
after `app` is constructed at line 139 and after the only import-time config code at line 148.
Calling it beside `_ALLOWED_ORIGINS` as written would raise `NameError`. The wiring was not merely
forgotten; the module's ordering makes the docstring's claim impossible.

The wave's fault injection reports killing a mutant called "production booting without a database"
(`docs/plans/m6-wave-3-close.md` row 5). What that mutant killed was a mutation of a function no
production path reaches. That is precisely the class row 5 says it went looking for.

*Remedy:* move `_db_path` above line 115, call `validate_startup_config()` at import next to
`_ALLOWED_ORIGINS`, and add a test that imports the module in a production environment and asserts
the refusal — not one that calls the function.

---

**BLOCKING-2 — A fourth YAML entry point exists, it is unguarded, and it is the only one with a remote producer (W-005 incomplete).**

`src/app/clients/aider.py:66`:

```python
entries = yaml.safe_load(raw)
```

`raw` arrives from `AiderClient.fetch_raw()` at `src/app/clients/aider.py:38-45`, which is
`httpx.get("https://raw.githubusercontent.com/Aider-AI/aider/main/.../polyglot_leaderboard.yml")`.
There is no size bound on the response and no expansion bound on the parse.

The three inputs the wave *did* guard — `plans.py`, `rosters.py`, `epoch.py` — are repo-committed
curated files. The one input this project actually fetches from a third-party host over the network
is the one that was skipped. `yaml_guard.py:5-13` justifies the wave by "M6 puts a network surface
in front of the same process"; this call site has been reading a network producer since M2.

Measured, in `parse_polyglot`'s own expected shape (a top-level list):

```
hostile payload bytes: 312
parse_polyglot ACCEPTED it: rows=0 skipped=9 in 0.001s   <-- UNGUARDED
the guard WOULD have refused it: expands to 490329055 nodes, past the 500000 limit
json.dumps of the loaded object: 2288202255 bytes in 13.8s
```

312 bytes in, 2.29 GB out of any downstream consumer that walks the structure — roughly 7.3-million-fold
amplification, from a host this project does not control.

The test written to prevent exactly this is `tests/unit/test_yaml_guard.py:93-106`. It hard-codes
three names and one directory:

```python
for name in ("plans", "rosters", "epoch"):
    source = Path(f"src/app/workflows/{name}.py").read_text()
    if "yaml.safe_load(" in source:
        unguarded.append(name)
```

So the test that exists to prove "a guard on two of three inputs is a guard on none" is itself a
guard on three of four. It will stay green for every future entry point as well.

This also falsifies the wave's V3C-101 producer enumeration (checklist row 9c): "its producers are
the three `yaml.safe_load` call sites in `plans.py`, `rosters.py` and `epoch.py`". Enumerated from
code, there are four.

*Remedy:* route `aider.py:66` through `safe_load_bounded`, cap `fetch_raw`'s response body, and
rewrite the wiring test to discover call sites by walking `src/` rather than by listing them.

---

**BLOCKING-3 — The guard breaks the frozen K.8 contract "CLI exit codes" (permission-matrix §11: broken contract surface / public contract changed without ADR).**

`YamlGuardError` subclasses `ValueError` (`src/app/workflows/yaml_guard.py:63`), not
`yaml.YAMLError`. All three call sites wrap only `yaml.YAMLError`:

```
src/app/workflows/plans.py:134:    except yaml.YAMLError as exc:
src/app/workflows/rosters.py:101:  except yaml.YAMLError as exc:
src/app/workflows/epoch.py:42:     except yaml.YAMLError as exc:
```

`safe_load_bounded` converts every parse failure to `YamlGuardError` at `yaml_guard.py:86-88`, so
those handlers can no longer fire for malformed input, and the guard's own refusals (oversize,
over-expansion) were never covered by them. All three parsers now raise a bare `ValueError` where
they previously raised the project's `SourceError`.

Measured, same input, before and after:

```
BEFORE (67fd92b): parse_rosters(malformed) -> SourceError: rosters-curated: unparseable YAML: ...
AFTER  (HEAD):    parse_rosters(malformed) -> YamlGuardError  <-- NOT SourceError
```

Through the live CLI entry point, whose handler is `src/app/workflows/rosters.py:214`
(`except SourceError` → print `error: ...` → `return 2`):

```
$ python -m app.workflows.rosters --check-staleness /tmp/bad.yaml
Traceback ... expected ',' or ']', but got ':'
actual exit code = 1
```

Exit 2 became exit 1. In this CLI, exit 1 is not "error" — `rosters.py:219-221` returns 1 for
"stale rosters found". A CI cadence job now reads an unparseable roster file as a staleness result.
`CLI exit codes` is named on the frozen contract list at `docs/plans/m6-plan.md:203`, and no ADR
records a change to it. No test covers the path; `make test` is green.

*Remedy:* one line — `class YamlGuardError(ValueError, yaml.YAMLError)`, or make it inherit
`yaml.YAMLError` outright — plus a citing test per CLI that asserts exit 2 on a malformed file.

---

**BLOCKING-4 — The CORS wiring has no citing test: deleting the entire feature leaves the suite green (V3C-02 GATE, V3C-73/F6).**

Mutant run in an isolated copy (the repository under review was not modified). Removed
`src/app/adapter/main.py:148-160` in full — the `_ALLOWED_ORIGINS = cors_origins()` assignment, the
`CORSMiddleware` import and the entire `app.add_middleware(...)` call:

```
baseline: 336 passed, 12 skipped
mutant A (CORS middleware wiring deleted entirely): 336 passed, 12 skipped
```

Nothing moved. The nine REQ-API-006 tests exercise `cors_origins()` and `validate_startup_config()`
as pure functions. The single test that enters through the live surface —
`tests/unit/test_api_config.py:101-116`, whose docstring reads "Built is not wired (V3C-73): the
absence is asserted on a real response" — asserts that no `access-control-allow-origin` header is
present when no allowlist is configured. With no allowlist configured, that header is absent whether
the middleware exists or not. The assertion is vacuous.

Consequently `allow_credentials=False` (main.py:157), `allow_methods=["GET"]` (main.py:158) and the
allowlist's actual effect are all unasserted. I verified by hand that the implementation is in fact
correct — allowed origin returns `ACAO: https://app.example.com`, a non-allowlisted origin returns
no header, a `DELETE` preflight is refused 400, no credentials header is emitted. That is what makes
this blocking rather than academic: the code is right, unproven, and deletable without a signal.

Root cause is a testability defect, not an oversight of diligence: `_ALLOWED_ORIGINS = cors_origins()`
runs at module import (main.py:148), so no `monkeypatch` after import can reach it and there is no
seam to test the configured path through. Checklist row 5 reports "11 mutants, 11 killed"; this
mutant is not among the eleven, and it is the same stay-green class as the W-008 mutant the wave
did catch.

*Remedy:* a `build_app()` factory (or a subprocess/reimport test with the env set) plus a test that
asserts the header IS returned for an allowlisted origin and is NOT for another.

---

### MINOR (queue for K.9 gap-fill or next-M)

- **`src/app/workflows/schema.py:164`** — the migration entry omits the CHECK constraint the DDL
  carries at `schema.py:84`, so a migrated database and a fresh one have different schemas.
  Measured: migrated DB accepted `roster_staleness_days = -7`; fresh DB raised
  `IntegrityError: CHECK constraint failed`. This is not a SQLite limitation — I verified
  `ALTER TABLE t ADD COLUMN x INTEGER CHECK (x IS NULL OR x > 0)` is accepted and enforced. No test
  asserts fresh/migrated schema parity, which is the general form of the gap.

- **`src/app/workflows/schema.py:264-271`** — `migrate()` releases the SAVEPOINT in `except
  sqlite3.Error` where `finally` is correct. Measured: a `RuntimeError` raised inside `_migrate`
  leaves `model_ranking_schema_migrate` open. This leak is *new with W-009* — before this wave
  `connect()` called `_migrate` directly and had no savepoint to leak. Low reachability today
  (`_migrate` issues only SQL); wrong shape on the wave's headline change.

- **`src/app/workflows/plans.py:183`** — `INSERT OR REPLACE INTO plan_config` deletes and re-inserts
  the row, so `roster_staleness_days` silently reverts to NULL on every plan ingest. Measured:
  after plans+rosters, window=30 / roster links=18; after a plan-only re-ingest, window=None /
  links=0. It is *consistent* today only because `plans.py:180` also runs an unscoped
  `DELETE FROM plan_models`. The invariant `rosters.py:137-139` claims to hold ("writing it anywhere
  else would let a database carry links from one roster policy and a window from another") is
  actually held by a different module, by coincidence, with no test. Scope that DELETE by
  `link_source` — which `rosters.py:144` already does, so it is the natural next edit — and the
  database is left with roster links and no policy, and every roster-serving recommendation raises.

- **`src/app/workflows/rosters.py:140-143`** — the write REQ-SUB-008 rests on is unverified.
  `UPDATE plan_config SET roster_staleness_days = ? WHERE id = 1` affects 0 rows when `plan_config`
  is absent and reports success. Not reachable through the supported ingest order (plans creates the
  row), but a `rowcount` check costs one line on the wave's central persistence step.

- **`src/app/workflows/yaml_guard.py:36-40`** — `MAX_EXPANDED_NODES = 500_000` is safe, but its
  written rationale is not measured. The docstring says "the shipped curated files compose to a few
  thousand nodes"; measured, they compose to 231 (plans), 55 (rosters) and 13 (epoch) — headroom of
  2,165× to 38,462×, not "a few thousand". The claim "two orders of magnitude below the point where
  expansion becomes a memory problem" is unsupported: `yaml.safe_load` shares aliased node objects,
  so that fixture loads in 0.002 s at ~0 MB and no such point exists for `safe_load` itself. The
  real exposure is downstream walkers (`json.dumps` → 2.29 GB, above). Answering the question as
  posed: the arithmetic is right and the bound refuses the measured attack (54,481,013 > 500,000
  on the test fixture), so it is not a number that merely looked round — but the sentence explaining
  it describes a measurement nobody took, and the docstring should say what it actually protects.

- **`src/app/workflows/yaml_guard.py:47`** — `_expanded_size` memoises on `id(node)`. Correct *as
  used*: the whole graph stays reachable from `node` for the walk's duration, so no id can be
  recycled mid-walk, and I confirmed the result is deterministic across runs (54,481,013 three times
  on the test fixture). But `yaml.Node` is hashable by identity, so keying on the node itself is
  free and removes the hazard by construction rather than by an argument about lifetimes. The cycle
  guard (`memo[key] = 1`) also undercounts a genuinely recursive anchor; harmless for a fail-closed
  bound over DAGs, undocumented as an undercount.

- **`src/app/workflows/yaml_guard.py:84` + `:99`** — the document is parsed twice, once by
  `yaml.compose` for the bound and once by `yaml.safe_load` for the value. Correct, but 2× the work
  on every curated read; constructing from the already-composed node would avoid it.

- **`src/app/workflows/subscribe.py:295`** — function-level import with no circular dependency to
  justify it. Verified: hoisting it to module level imports cleanly, and `rosters.py:14-26` does not
  import `subscribe`. It hides a real module edge from the import graph.

- **`src/app/workflows/rosters.py:230`** — `roster_staleness_days` is defined *after*
  `if __name__ == "__main__": raise SystemExit(main())` at `rosters.py:226-227`, so in script mode
  the definition never executes. Harmless today (nothing needs it there); an append-at-end artifact
  on the wave's central new function.

- **`src/app/workflows/subscribe.py:300-305`** — the early return makes the "fail loud on an unset
  policy" invariant conditional on the ranking happening to serve a roster link. Verified on one
  database: one query raises `ValueError: ...roster_staleness_days is unset...` while another
  returns quietly. The reasoning in the comment is sound; the consequence — a loud failure that
  fires per-query rather than per-database — is not recorded anywhere.

- **`docs/plans/m6-wave-3-close.md` rows 2, 9, 9a** — checklist arithmetic drifts from the tree it
  is pinned to. Rows 2 and 9 claim "335 passed / 12 skipped"; measured on the closing tree,
  **336 passed / 12 skipped**. Row 9a claims "approximately 420 changed lines across 10 files";
  `git diff 67fd92b..HEAD --shortstat` reports **801 insertions / 12 deletions across 13 files**,
  and restricted to `src` + `tests`, **738 / 12 across 11 files**. Row 9a's whole function is the
  ≤400-line bar, and 420 reads as "marginally over" where 738 reads as ~85% over.

### PASS (what looks good)

- **The migration is genuinely atomic, and I confirmed it rather than took it.** Injecting a failure
  into the last migration step against a hand-built pre-M6 database left the file untouched:
  `plan_config` columns `['id','staleness_days','cap_dusuk','cap_orta']`, row `(1, 30, 10.0, 25.0)`
  intact, no stray tables. A clean re-run then added `roster_staleness_days` as `NULL`, and a third
  run returned `[]`. Second run, failure, and pre-M6 database all behave as the wave claims.

- **W-009's SAVEPOINT genuinely nests.** `migrate()` inside `connect()`'s `BEGIN IMMEDIATE`
  (`schema.py:367-370`) and inside `main()`'s (`schema.py:412-415`) both work, and the rollback
  scope on the `sqlite3.Error` path is identical to the pre-wave behaviour: `ROLLBACK TO` undoes the
  migration, the re-raise reaches the caller's `except sqlite3.Error`, and `conn.rollback()` undoes
  the rest — exactly what `_migrate` used to produce. Nothing rolls back more or less. (The one
  exception is the non-`sqlite3.Error` leak, filed above.)

- **The expansion guard's replacement is the right instrument and the wave's account of why is
  accurate.** Verified against the fixture: the measured attack composes to **54,481,013** expanded
  nodes from 287 bytes, and `_expanded_size` computes the DAG expansion exactly, level by level
  (10 → 91 → 820 → 7,381 → 66,430 → 597,871 → 5,380,840 → 48,427,561), linear in the document's
  real size because `yaml.compose` shares alias references. An alias *count* bound genuinely cannot
  see this, and the wave's own test disproving its first attempt
  (`tests/unit/test_yaml_guard.py:76-90`) is the strongest artifact in the wave.

- **The W-008 behavioural test is the real thing.** `tests/unit/test_roster_window.py:203-250` sets
  the two windows apart (plan 365, roster 5) against a 10-day-old link, drives
  `recommend_subscription` on a real database, asserts the notice appears, then widens the *roster*
  window alone and asserts it goes quiet. It asserts both directions, so it cannot pass by always
  finding something stale. The fail-loud invariant also holds through the live path — I confirmed
  `recommend_subscription` raises `ValueError: plan_config.roster_staleness_days is unset` on a
  served roster link with a NULL policy.

- **The CORS implementation itself is correct** (see BLOCKING-4 for why that is not enough):
  allowlisted origin → `ACAO`, other origin → no header, `DELETE` preflight → 400, no credentials
  header, and a wildcard raises at import so the module cannot boot with allow-all.

- **Gates are green on the closing tree:** `ruff check src tests` — All checks passed;
  `mypy src` — Success, no issues in 29 source files; `pytest` — 336 passed, 12 skipped.

---

## Acceptance criteria evidence

Per profile §5 and permission-matrix §11, a PASS requires `file:line` evidence per criterion. Two of
the four criteria below do not have it, which is why the verdict is BLOCKING rather than MINOR.

| Criterion | Evidence | Status |
|---|---|---|
| **REQ-SUB-008** — roster window persisted, read, consumed; unset fails loud | `src/app/workflows/schema.py:84` (column) + `:164` (migration) → `src/app/workflows/rosters.py:140-143` (ingest writes) → `rosters.py:230-253` (reads) → `src/app/workflows/subscribe.py:306` (consumes). Citing tests: `tests/unit/test_roster_window.py:203-250` through `recommend_subscription` on a real database, asserting both directions; `:76-104` through `ingest_plans`+`ingest_rosters`; `:107-154` through `connect()` on a hand-built M3-era database | **MET** |
| **W-005** — expanded-node bound on curated YAML | `src/app/workflows/yaml_guard.py:44-64` (bound) + `:82-99` (fail-closed order). Citing tests: `tests/unit/test_yaml_guard.py:35-42`, `:76-90`. Verified: 54,481,013 > 500,000 on the measured attack | **NOT MET** — the producer set is incomplete: `src/app/clients/aider.py:66` is unguarded and is the only remote-fed input (BLOCKING-2), and the wiring test at `tests/unit/test_yaml_guard.py:102` cannot see it |
| **W-009** — one migration entry point, production runs the SAVEPOINT path | `src/app/workflows/schema.py:369` + `:414` (callers moved to `migrate`), `:264-272` (SAVEPOINT). Citing tests: `tests/unit/test_roster_window.py:157-177` (asserted from source), `:180-200` (nests inside a caller transaction). Independently verified: mid-migration failure leaves the database byte-equivalent; re-run idempotent | **MET** (with the non-`sqlite3.Error` savepoint leak filed MINOR) |
| **REQ-API-006** — CORS allowlist; startup validation; fail closed in production | Wildcard/malformed refusal: `src/app/adapter/main.py:101-112`, cited by `tests/unit/test_api_config.py:16-50` — **MET**. Unset means no cross-origin: `main.py:97-99` + `tests/unit/test_api_config.py:39-42` — **MET**. Allowlist applied to the surface: `main.py:148-160`, **NO citing test** — deleting all 13 lines leaves 336/336 green (BLOCKING-4). Production fails closed on a missing database / unset `APP_BUILD`: `main.py:115-136`, **NO production caller** — the process boots and serves (BLOCKING-1) | **NOT MET** on two of four clauses |

## K.8 contract drift check

**`migrate` (frozen contract NAME) — OK, not renamed:**
```
$ grep -n "def migrate\|migrate(conn)" src/app/workflows/schema.py
250:def migrate(conn: sqlite3.Connection) -> list[str]:
369:        migrate(conn)  # W-009: the same entry point the tests exercise
414:        applied = migrate(conn)  # W-009: the same entry point the tests exercise
$ grep -rn "_migrate(conn)" src/
(no production call site remains — schema.py:266 only, inside migrate())
```

**`plan_config` (schema surface) — CHANGED, additive and nullable, as the plan permits:**
```
$ grep -n "roster_staleness_days" src/app/workflows/schema.py
84:    roster_staleness_days INTEGER CHECK (roster_staleness_days IS NULL OR roster_staleness_days > 0),
164:    ("plan_config", "roster_staleness_days", "INTEGER"),
```
Additive and nullable as declared. Drift noted: the migrated shape omits the CHECK (MINOR-1).

**`CLI exit codes` (frozen contract, `docs/plans/m6-plan.md:203`) — DRIFTED, and this one is BLOCKING:**
```
$ grep -n "except SourceError" src/app/workflows/rosters.py src/app/workflows/plans.py
src/app/workflows/rosters.py:214:    except SourceError as exc:
src/app/workflows/plans.py:303:    except SourceError as exc:
$ grep -n "class YamlGuardError" src/app/workflows/yaml_guard.py
63:class YamlGuardError(ValueError):
```
`YamlGuardError` is not a `SourceError` and not a `yaml.YAMLError`, so it reaches neither handler.
Measured: exit 2 → exit 1 on a malformed roster file (BLOCKING-3).

**New config surface — declared and grep-verified:**
```
$ grep -rn "MODEL_RANKING_CORS_ORIGINS\|APP_ENV" src/
src/app/adapter/main.py:97:    raw = os.environ.get("MODEL_RANKING_CORS_ORIGINS", "").strip()
src/app/adapter/main.py:104:  "MODEL_RANKING_CORS_ORIGINS contains '*'. ..."
src/app/adapter/main.py:110:  f"MODEL_RANKING_CORS_ORIGINS entry {origin!r} is not an absolute origin"
src/app/adapter/main.py:121:    environment = (env if env is not None else os.environ.get("APP_ENV", "development")).lower()
```
`APP_ENV` is read only by a function nothing calls, so the variable is declared but inert in the
running process (BLOCKING-1).

**Verdict: DRIFTED** — on `CLI exit codes`, without an ADR.

## §2a-bis Hardened-invariant producer section (V3C-101, REQUIRED)

**Invariant 1 — untrusted-document parsing.**
Producers of the hardened invariant, enumerated from code
(`grep -rn "yaml\.\(safe_load\|load\|full_load\|compose\|load_all\)" src/`):
1. `src/app/workflows/plans.py:135` → routed through `safe_load_bounded` ✅ — citing test
   `tests/unit/test_yaml_guard.py:93-106`
2. `src/app/workflows/rosters.py:100` → routed ✅ — same test
3. `src/app/workflows/epoch.py:42` → routed ✅ — same test
4. **`src/app/clients/aider.py:66` → NOT routed ❌ — no citing test, and the only producer fed from
   the network**

**Gaps (tracked):** producer 4 is BLOCKING-2. The enumerating test itself
(`tests/unit/test_yaml_guard.py:102`) is scoped to three hard-coded names in one directory and
cannot discover producer 4 or any future one.

**Invariant 2 — the roster staleness policy.**
Producers enumerated from code: `ingest_rosters` writes (`src/app/workflows/rosters.py:140-143`) —
citing test `tests/unit/test_roster_window.py:76-104`; `roster_staleness_days` reads
(`src/app/workflows/rosters.py:230-253`) — citing tests `tests/unit/test_roster_window.py:50-73`
and `:203-250`.
**Gap (tracked):** a *third* producer exists and is not enumerated — `src/app/workflows/plans.py:183`
resets the column to NULL via `INSERT OR REPLACE`, with no citing test (MINOR-3).

No auth / tenancy / money invariant is touched by this wave.

## v3.3 reviewer countersignature — 2 rows chosen by this seat

I chose the two rows carrying the most weight, before reading the others' evidence.

**Row 9c (V3C-101 producer list enumerated FROM CODE) → OVERSTATED.**
The row states "its producers are the three `yaml.safe_load` call sites in `plans.py`, `rosters.py`
and `epoch.py`, all three now routed through `safe_load_bounded` and **asserted from source**".
Enumerated from code there are **four**, and the fourth (`src/app/clients/aider.py:66`) is the only
one whose producer is remote. The row's own claim that the assertion comes from source rather than
from a list in the row is what makes this findable: the source assertion at
`tests/unit/test_yaml_guard.py:102` is itself a hard-coded list of three. Substituting one list for
another does not make the enumeration derived.

**Row 6 (every criterion has a citing test entering through the LIVE entrypoint, not a unit shim —
V3C-02 + V3C-73/F6) → OVERSTATED.**
- REQ-API-006 is credited with "nine tests in `tests/unit/test_api_config.py`, including one that
  asserts the ABSENCE of a CORS header on a real response". Four of the nine call
  `validate_startup_config`, which no production path calls (BLOCKING-1) — the definition of a unit
  shim. The one live-entrypoint test asserts an absence that holds with the middleware deleted
  (BLOCKING-4).
- REQ-SUB-008's fail-loud clause is credited to
  `test_a_pre_m6_database_migrates_without_inventing_a_policy`; that assertion
  (`tests/unit/test_roster_window.py:148-149`) is a direct call to `roster_staleness_days`, not a
  path through the served answer. The invariant does hold live — I checked — but the row claims the
  test enters that way, and it does not.
- The row is accurate for REQ-SUB-008's main criterion and for W-009.

Both rows I picked were overstated, which makes three waves out of three. The pattern is not
carelessness in any single row: each overstatement is a place where the evidence proves the
mechanism exists and the row claims the behaviour is covered. That is the same sentence row 5 wrote
about the W-008 mutant, and it is now the wave's characteristic failure mode rather than an incident.

## Risk tier assessment

**HIGH is correct, and if anything under-scoped.** The checklist's three auto-HIGH triggers
(migration, untrusted-input parsing, network-facing security config) are all genuinely present. A
fourth is now established: this wave changed a frozen K.8 public contract (`CLI exit codes`,
BLOCKING-3) without an ADR. The tier is not the author's to lower and was not lowered.

The escaped-blocker tripwire has not fired — the wave has not closed, correctly.

## K.9 candidates spotted outside this wave's scope

- `src/app/clients/aider.py:38-45` — `fetch_raw` applies no size cap to the HTTP response body
  before parsing. Bounding the graph is not enough if the bytes are unbounded first. Suggested:
  M6-W4, alongside BLOCKING-2's fix.
- `conformance/test-ci-yaml.py:104,192` — two further `yaml.safe_load` call sites outside `src/`.
  Not production, so not blocking, but they are inside the governance tooling that decides whether
  gates pass. Suggested: M7.
- `docs/warnings.ledger.md` W-017 still records "Owning milestone: **M6-W3**" while
  `docs/plans/m6-wave-3-close.md` row 9b defers it to Stage 4.3. The ledger row was not amended to
  match the deferral, so the two records now disagree about who owns it. Suggested: M6 closure.
- No test anywhere asserts that a migrated database and a freshly created one have the same schema.
  MINOR-1 is the current instance; the class will recur on every future column. Suggested: M6-W4.

## Risks queued to next M

- The two BLOCKINGs that survived every gate (BLOCKING-1, BLOCKING-4) share one shape: a citing test
  that calls a function directly instead of entering through the path production takes. The wave
  found this once by injection and wrote it up, then shipped two more of it. A grep-level control is
  available and cheap — for every symbol asserted by a security test, require at least one call site
  in `src/` that is not a test — and it would have caught both.
- `_ALLOWED_ORIGINS = cors_origins()` at import time is a testability defect that will keep
  producing untestable config. An app factory is the standard remedy and should land before the
  deploy wave, not after.
- The roster policy's lifecycle now spans three modules (`plans.py` resets it, `rosters.py` writes
  it, `subscribe.py` consumes it) with a test in only one. The coupling that keeps it coherent is
  an unscoped `DELETE` in the module that does not own the policy.

---

**Per profile §"When you finish": BLOCKING → STOP. The wave does not progress until these are fixed
and the review re-runs.** Findings were not communicated to the wave's authors before this verdict
was written.
