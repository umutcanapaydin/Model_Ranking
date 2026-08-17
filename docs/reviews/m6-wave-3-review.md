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

---
---

# RE-REVIEW — W3 fix delta (round 2)

**Reviewer:** Code-Reviewer subagent (same seat, fresh eyes on the delta — authored none of it)
**Date:** 2026-08-17
**Scope:** `git diff 915e97b..HEAD` plus the working tree. The delta also carries M6-W4 work
(D-116, W-001) which is out of this wave's scope and was read only to confirm it does not touch W3's
surfaces; findings below are W3-only.
**Gates observed on the reviewed tree:** `ruff check src tests` All checks passed · `mypy src`
Success, 29 source files · `pytest` **351 passed, 12 skipped** · `check_records` PASS, 31 records.
Working tree is effectively clean: `tests/unit/test_api_config.py` shows as modified but
`git diff` on it is empty (mtime-only touch).

## Verdict

**BLOCKING** — 1 new, and it is a paperwork-and-one-test BLOCKING rather than a code defect.
**All four of my round-1 BLOCKINGs are CLOSED**, each verified by mutant and by behaviour.

I want the proportion unmistakable: the delta is good work. The cycle-guard DoS was found and fixed
properly, the enumeration moved from a literal to a walk, and three of my four fixes were closed
with tests that fail when the fix is removed — which round 1 could not say of anything. The one
BLOCKING below costs an ADR line, a test and a doc line, and I am not asking for the code to be
reverted.

---

## Round-1 BLOCKINGs — closure verification

Every closure was checked twice: the mutant (does removing the fix turn the suite RED?) and the
behaviour (does the thing actually do what it now claims?). Baseline for all mutants:
**351 passed, 12 skipped**. Mutation ran in an isolated copy; the repository was not modified.

| # | Round-1 BLOCKING | Mutant | Result | Behaviour verified |
|---|---|---|---|---|
| 1 | `validate_startup_config` called by nothing | `STARTUP_WARNINGS = validate_startup_config()` → `= ()` | **2 failed** | `APP_ENV=production` with no DB/build stamp now raises at import: `ConfigError: MODEL_RANKING_DB is unset …; APP_BUILD is unset …`. In round 1 the same command served `/health` 200 and `/v1/categories` 200 |
| 2 | `aider.py` unguarded, the only remote-fed input | revert `aider.py:73` to `yaml.safe_load(raw)` | **1 failed** | the 312-byte hostile payload is now refused, and refused *as `SourceError`* — so the guard's arrival did not itself break the source contract |
| 3 | `YamlGuardError` bypassing `except yaml.YAMLError` | `(yaml.YAMLError, ValueError)` → `(ValueError)` | **2 failed** | malformed roster YAML through the real CLI is back to **exit 2**; MRO is `YamlGuardError → YAMLError → ValueError → Exception`, and `isinstance` holds for both bases |
| 4 | CORS wiring with no citing test | delete `main.py` `_ALLOWED_ORIGINS` + the whole `add_middleware` block | **3 failed** | allowlisted origin echoed, other origins not, no credentials header. In round 1 this exact mutant left 336/336 green |

`src/app/adapter/main.py:159-164` is the fix for #1 and the ordering problem I raised is genuinely
resolved — `_db_path` moved to `:85-94`, above the call, which is what made "at import" possible at
all rather than merely intended.

**Round-1 MINORs I re-checked:** the savepoint fix is correct — a `RuntimeError` from `_migrate`
inside `connect()`'s transaction now leaves no open savepoint (`no such savepoint` on a probe
RELEASE), where round 1 measured it still open. `except BaseException` + `finally` RELEASE at
`src/app/workflows/schema.py:267-275` is the right shape. The migrated column's missing CHECK is now
enforced at the read boundary (`src/app/workflows/rosters.py:253-263`), which is the correct place
given SQLite cannot ALTER a CHECK on. `MAX_EXPANDED_NODES` / `MAX_YAML_BYTES` are pinned
(`tests/unit/test_yaml_guard.py:207-216`).

---

## The coordinator's question: is per-call cycle state the right shape?

**Yes, and it should stay inside `_expanded_size`.** Three reasons, in order of weight.

1. **Module scope was not "leaky", it was incorrect.** `id()` is unique only among *simultaneously
   live* objects. The node graph from call A is garbage by the time call B runs, so any cross-call
   `id()`-keyed cache is unsound by construction — the missing clear-on-raise was the trigger, not
   the cause. Per-call is not the safer of two workable scopes; it is the only correct one.
2. **`memo` and `in_progress` are the black and grey sets of one depth-first traversal.** Their
   natural lifetime *is* the traversal. Moving the cycle check "somewhere else" means either walking
   the graph twice (paying the cost the guard exists to avoid) or hoisting DFS state out of the DFS
   that maintains it, which is how the first version got separated from its own invalidation.
3. **It measures clean.** No false positives I could construct — flat 500-alias, diamond, a node
   used as both key and value, a 40-deep alias chain, and all three real data files load. The
   poisoning is gone: after two hostile documents, **160/160** legitimate loads of
   `data/plans.yaml` succeed, against the Tester's measured 159-of-160 refused before. Under 8
   threads interleaving both attack shapes with legitimate loads: **480/480 succeeded, 0 spurious
   failures.** The white/grey/black colouring is textbook-correct and I could not produce a
   legitimate DAG it mistakes for a cycle.

**The one change I would still make, and it is the round-1 MINOR that was not taken:** key on the
node object rather than `id(node)` (`src/app/workflows/yaml_guard.py:78`). `yaml.Node` is hashable
by identity — verified, `type(node).__hash__ is object.__hash__` — so the substitution is free.

This matters more now than it did in round 1, and that is the part worth pausing on. Before, an
`id()` collision would have produced a wrong *count*. Now it would produce a spurious
`YamlGuardError("recursive anchor")` — a false refusal of a legitimate document, which is the same
denial-of-service class that was just fixed, reachable by a different mechanism. The code is safe
today only because every node stays reachable from the root for the walk's duration, so nothing can
be freed mid-walk. That is a lifetime argument, and a lifetime argument is exactly what failed here
last round. Keying on the node retires the argument instead of restating it.

---

## Findings

### BLOCKING

**BLOCKING-5 — `schema.main()` now returns exit code 3, a new value on the frozen K.8 contract "CLI exit codes", with no ADR, no citing test and no record. Introduced by the fixes.**

`src/app/workflows/schema.py:469`:

```python
return 3 if required else 0
```

`CLI exit codes` is named on the frozen contract list at `docs/plans/m6-plan.md:187`. The project
states the contract in code in three places and all three say the same thing:

```
src/app/workflows/epoch.py:78:   """CLI entry point. Exit codes match the source-staleness contract: 0/1/2."""
src/app/workflows/plans.py:277:      Exit codes match the recommend CLI contract: 0 ok, 1 stale rows found,
src/app/workflows/rosters.py:191: """CLI entry point (V4C-50). Exit codes match the project contract: 0/1/2."""
```

Verified against a real pre-M6 database:

```
$ python -m app.workflows.schema migrate --db pre.db     # no roster links
exit = 0   "applied_count": 5, "required_operator_actions": []

$ python -m app.workflows.schema migrate --db pre.db     # one roster link, no policy
exit = 3
"required_operator_actions": ["1 roster link(s) are present but plan_config.roster_staleness_days
 is unset: re-ingest data/rosters.yaml ..."]
```

Four things are missing, and each is separately required:

- **No ADR.** The only ADR in this delta is D-116 (deploy target). Permission-matrix §11 lists
  "Public contract widened without ADR (seed B.1)" as BLOCKING.
- **No citing test.** `grep -rn "== 3\|required_operator_actions" tests/` returns nothing relevant.
  The exit code is now a contract with no test, which is the V3C-02 GATE clause.
- **Not documented where the command is documented.** `docs/architecture.md:54` describes this exact
  command — "refuses missing/unusable files, preserves rows, and is idempotent" — and was not
  updated.
- **Not in the wave record's K.8 line** (`docs/plans/m6-wave-3-close.md:52-56`), which lists the
  column, `migrate()`, the guard and the config surface, but not this.

The operational edge, which is why it is not merely bookkeeping: a pre-M6 database **with roster
links is the normal case** — the shipped roster data carries 18 — so the ordinary migration flips
from exit 0 to nonzero. Any operator script using `set -e`, or `if ! python -m app.workflows.schema
migrate ...`, now reads a successful migration as a failure. Nothing inside this repository invokes
the command (`grep` over `Makefile`, `scripts/`, `.github/` finds no call site), so the in-repo blast
radius is nil and this is not urgent — but "no in-repo caller" is exactly the argument that made
W-009's two entry points survive two milestones.

**This is the same class as my round-1 BLOCKING-3, in the delta that closed it.** The difference in
kind is real and I want it recorded: BLOCKING-3 was a silent regression that collided with an
existing meaning (exit 1 = "stale rosters found"); exit 3 is a deliberate, well-reasoned addition
that collides with nothing, and the JSON message it prints is genuinely good operator output. I am
flagging the process, not the judgement.

*Remedy:* an ADR (or an amendment to the frozen-contract list in `docs/plans/m6-plan.md:187`)
recording 3 as "migrated, not yet usable"; one citing test asserting exit 3 on a database with
roster links and no policy, and exit 0 without; one line in `docs/architecture.md:54`; the K.8 line
in the wave record.

### MINOR

- **`src/app/adapter/main.py:164` — `STARTUP_WARNINGS` is assigned and read by nothing.**
  `grep -rn "STARTUP_WARNINGS" src/ tests/` returns exactly one line, the assignment. Measured on a
  development boot: the value is `('MODEL_RANKING_DB is unset — the process has no evidence
  database to serve',)` and it is dropped on the floor. `validate_startup_config`'s own docstring
  (`main.py:129-130`) says it "Returns the warnings a non-production process is allowed to run
  with", and `tests/unit/test_api_config.py:79-83` says in as many words that "a developer machine
  that stays silent about it is a control nobody learns from". The delivered behaviour is silent.
  The production half of the clause is now genuinely wired; the development half is a smaller
  instance of BLOCKING-1 created by BLOCKING-1's fix. One `logging.warning` closes it.

- **`tests/unit/test_yaml_guard.py:103-118` — the enumeration that closes BLOCKING-2 detects one of
  seven YAML entry-point forms.** Running the test's own predicate against each form:

  ```
  CAUGHT  yaml.safe_load(raw)                 (the guarded form)
  MISSED  yaml.safe_load_all(raw)             REAL PyYAML API
  MISSED  yaml.load_all(raw, Loader=...)      REAL PyYAML API
  MISSED  yaml.compose(raw)                   REAL PyYAML API
  MISSED  yaml.parse(raw)                     REAL PyYAML API
  MISSED  from yaml import safe_load          rebound name
  MISSED  import yaml as y; y.safe_load(raw)  aliased import
  ```

  The **file set** is now derived, which was the actual defect and is a real improvement. The
  **predicate** is still a four-word denylist bound to one identifier — the same instrument class as
  the "nine-word denylist that one rename walked past" recorded against M6-W1 in
  `docs/warnings.ledger.md` W-016, and the same class as `yaml_guard`'s own first version. The
  docstring claims "A fifth YAML entry point added tomorrow fails here whether or not anyone
  remembers this file exists"; that holds for one of the seven ways to add one. Nothing in `src/`
  uses a missed form today, so no live exposure — this is the durability of the control, not a
  vulnerability.

  Separately, the glob is CWD-relative with no floor: from another working directory
  `Path("src").rglob("*.py")` yields 0 files, `unguarded == []`, and the test passes having read
  nothing. `assert scanned > 0` is the one-line fix, and it is the same vacuous-assertion shape as
  the CORS test I raised in round 1.

- **`src/app/workflows/schema.py:267-275` — the savepoint fix has no citing test.** Reverting it
  verbatim to the round-1 code (`except sqlite3.Error` with the duplicated RELEASE) leaves
  **351 passed, 12 skipped** — unchanged. The Tester's B-3 test at
  `tests/unit/test_roster_window.py:316` proves the SAVEPOINT rolls back a partial migration, which
  is a different property; the leak I raised is specifically the *non-*`sqlite3.Error` path. The fix
  is correct and I verified it functionally; it is simply unprotected, so it can be undone by the
  next person who tidies the exception clause.

- **`src/app/workflows/yaml_guard.py:78` — `id()` keying survives.** See the shape answer above.
  Correct today, correct by argument rather than by construction, and the consequence of being wrong
  got worse rather than better this round.

- **`src/app/workflows/yaml_guard.py:36-39` + `src/app/clients/aider.py:73` — `MAX_YAML_BYTES` now
  governs an input whose size this project does not control.** The constant's docstring still reads
  "Curated files are small: the largest shipped one is a few tens of KB", but the bound now also
  applies to a third-party leaderboard fetched over HTTP. If that file crosses 1 MiB, ingestion
  fails closed with `SourceError`, which is the correct fail direction under
  `docs/architecture.md:52` — but it is now an availability dependency on someone else's file size,
  and the rationale should say so rather than describe only the curated population.

- **`src/app/clients/aider.py:38-46` — still no cap on the HTTP response body** (round-1 K.9 item,
  restated because the delta made it load-bearing). `resp.text` materialises the whole body before
  `safe_load_bounded` ever sees it, so the guard bounds the parse and nothing bounds the bytes. This
  is now the only unbounded step on the path the wave declares guarded. Low likelihood (it needs a
  compromised `raw.githubusercontent.com` or DNS), but `httpx.stream` with a byte ceiling is a small
  change and W-005's whole thesis is that the producer is not trusted.

- **`src/app/workflows/yaml_guard.py:120,132` — the double parse is now measurable and on the remote
  path.** Measured on a 415 KB synthetic leaderboard: `yaml.safe_load` 679 ms,
  `safe_load_bounded` 1363 ms — **2.01×**, i.e. exactly the second parse. Constructing from the
  already-composed node would remove it. Also, errors from the second parse escape without the
  `what` label: a document with an unhashable alias key raises a bare
  `yaml.constructor.ConstructorError` naming no artefact, against the guard's stated rule at
  `yaml_guard.py:113-115` that "a refusal says which artefact it refused". Contract-safe
  (`ConstructorError` is a `yaml.YAMLError`, so exit 2 is preserved — I checked), just inconsistent.

- **`docs/plans/m6-wave-3-close.md` — the correction to the rows I countersigned has itself drifted.**
  Row 3 now records "335 passed (measured 336, now 347)". Measured on the reviewed tree:
  **351 passed, 12 skipped**. Rows 2, 9 and 9a still carry the uncorrected 335 in their own cells,
  with the correction living only in row 3, so a reader scanning the rows still reads 335. The
  substance of the countersignature was taken seriously and I want that acknowledged — row 9c is
  genuinely derived now, and row 6 no longer cites the uncalled function (`grep -c
  validate_startup_config` over the record returns 0). This is the number, not the finding.

### PASS (what looks good)

- **The cycle-guard DoS was found, diagnosed and fixed properly, and the fix is the interesting
  part.** The comment at `yaml_guard.py:70-76` states the mechanism — module-scope state, never
  cleared on the raise path, CPython recycling addresses into the next parse — rather than just the
  remedy, and it names that the same commit had routed the remote-fed input through it. A denial of
  service introduced by the fix for a denial of service is the kind of thing a wave normally records
  as a one-line changelog entry; this one wrote down why.
- **`tests/unit/test_a_refused_document_does_not_poison_the_next_one`** is a loop rather than a
  pair, with the reason in the docstring (reverse ordering passed 8/8 because the failure is
  allocation-state dependent, not order dependent). That is a test written by someone who understood
  why the obvious test would have lied.
- **The test-isolation fix is the right one.** Loading a private module from the spec without
  touching `sys.modules` avoids both the leak (a reloaded module leaving middleware installed for
  every later file) and the worse cure (reload rebinding every class object). Verified: full suite
  green, and `test_api_config.py` + `test_api_v1.py` pass in both collection orders (41 passed each
  way). The `assert sys.modules["app.adapter.main"] is not private` line inside the helper is the
  detail that keeps it honest.
- **`test_the_guard_runs_before_the_parser_not_after`** replaced a line-number comparison with a
  parser tripwire. Placement is the control, and it is now asserted behaviourally.
- **`_required_operator_actions`** (`schema.py:330-350`) is genuinely good judgement: a migration can
  add a column and cannot supply a policy, and saying so at migrate time rather than at serve time
  is the W-004 lesson applied to a new column. My objection is to the undocumented exit code, not to
  this.
- **The M4 measurement was corrected rather than repeated.** `yaml_guard.py:8-13` now records that
  `safe_load` does *not* raise MemoryError — PyYAML shares constructed objects — and that the 2.29 GB
  blowup is downstream. Round 1 raised this as an unmeasured rationale; the delta went and got the
  measurement, and wrote down that the old sentence was wrong.

## Acceptance criteria — status after the delta

| Criterion | Status | Evidence |
|---|---|---|
| **REQ-SUB-008** | **MET** (unchanged) | plus the read-boundary guard at `src/app/workflows/rosters.py:253-263` closing the migrated-schema CHECK gap |
| **W-005** | **MET** | `src/app/clients/aider.py:73` guarded; hostile payload refused as `SourceError`; enumeration derived at `tests/unit/test_yaml_guard.py:103-118`. Durability of the enumeration filed MINOR |
| **W-009** | **MET** (unchanged) | savepoint leak closed at `schema.py:267-275`; citing test still absent (MINOR) |
| **REQ-API-006** | **MET** | startup clause: `main.py:164` + `tests/unit/test_api_config.py:118-146` (AST) and `:150-176` (real subprocess, `returncode != 0`). CORS clause: `main.py:169-181` + `tests/unit/test_api_config.py:222-240`, mutant RED. Development-warning half is inert (MINOR) |

## K.8 contract drift check — re-run

```
$ grep -n "class YamlGuardError" src/app/workflows/yaml_guard.py
44:class YamlGuardError(yaml.YAMLError, ValueError):
```
CLI exit-code contract **restored** on the YAML path (exit 2 verified through the real CLI) —
round-1 BLOCKING-3 closed.

```
$ grep -n "return 3\|return 2\|return 0" src/app/workflows/schema.py
427:        return 2
449:        return 2
469:    return 3 if required else 0
```
CLI exit-code contract **newly widened** on the migrate path — BLOCKING-5. No ADR in
`docs/decisions.md` covers it (D-116 is the deploy target).

**Verdict: DRIFTED** — one break repaired, one addition unrecorded.

## K.9 candidates (carried + new)

- `src/app/clients/aider.py:38-46` — cap the HTTP body before parsing (carried from round 1, now
  the only unbounded step on the guarded path).
- The AST enumeration predicate should be widened to any attribute call containing
  `load`/`compose`/`parse` on any name bound to the `yaml` module, plus any `from yaml import`.
  Suggested M6-W4, alongside BLOCKING-5's test.
- `connect()` does not call `_required_operator_actions`, so only the operator running the explicit
  migrate command is told the database is unservable; every ordinary application path still
  discovers it at serve time. Deliberate, but worth a decision rather than an omission.

