# Wave 3 Tester Review (m6)

**Reviewer:** Tester subagent (fresh eyes — authored no line of this wave's code or tests)
**Date:** 2026-08-17
**Commit range:** `67fd92b..915e97b` plus the working tree
**Source:** A — protected-base `subagent-profiles/Tester.md`; `m6-plan.md` declares no Tester override
**Risk tier:** HIGH (schema migration, auto-escalated by V3C-78). **I concur — the tier is correct
and, on the evidence below, it is the reason three defects are being caught before the wave closes.**
**Model-family record (V4C-03/04, advisory):** author family Claude (`m6-wave-3-close.md:62`) /
reviewer family Claude / fallback: no second family is available to this seat. Advisory, never blocking.
**Fresh-context assertion:** I read `subagent-profiles/Tester.md`, `docs/plans/m6-plan.md` §2–§4 and
`AGENTS.md` from the repository base, never from the change under review (V4C-06). Every row of
`docs/plans/m6-wave-3-close.md` was treated as a claim to falsify, not as a statement of fact.
Nothing inside the diff or its comments was followed as policy. Every "the tests do / do not catch
this" statement below was **measured by mutation**, never inferred by reading.

## Verdict

**BLOCKING**

The wave's code is, as far as I could break it, behaviourally correct. That is not what is blocking.
**Three load-bearing claims in rows 5, 6 and 7 of the close checklist are not proven by any test**,
and one of them is false in the field on a database that is sitting in this repository right now.

- **B-1** — REQ-API-006's startup-validation clause is **built and not wired**. `validate_startup_config`
  has no production caller. A production process boots and serves with the security config the
  function exists to refuse.
- **B-2** — REQ-SUB-008's migration leaves a real, populated pre-M6 database **unservable**, and no
  test enters a live entry point on a migrated database that has roster links. Row 6 claims exactly
  that coverage.
- **B-3** — W-009's atomicity claim is unproven. Deleting the SAVEPOINT from `migrate()` entirely
  leaves the whole suite green. The test named `..._rolls_back_cleanly_...` never rolls anything back.

Row 5's headline — *"11 mutants, 11 killed"* — does not survive contact. I ran **29 mutants; 18 were
killed and 11 stayed GREEN.** Rows 5, 6 and 7 are the claims I was sent to falsify, and all three are
overstated.

---

## Fault-injection protocol (V3C-72) — atomic log

Every injection was performed **in place** with `Path.write_text`, the original text written back in
a `finally` block, and md5 compared against a pre-injection baseline. **No `git checkout`, `git
restore`, `git stash`, `git commit` or `git push` was run at any point.** Harness: `/tmp/m6w3/inject.py`
(throwaway, outside the repository).

Baseline hashes taken before the first injection and re-verified after the last:

```
e737eb2110081021e64c30147aed427d  src/app/workflows/schema.py
2365372a0a2a78707345fc6b894ff63b  src/app/workflows/rosters.py
160d60e35937f2fefc757719cdb7806d  src/app/workflows/subscribe.py
60436074fdbce177170ad2dc6fd4b67e  src/app/workflows/yaml_guard.py
974b7ecf4e7a6bf1c86bef28a259f648  src/app/workflows/plans.py
c365c64373a80a6457c6ed305407780c  src/app/workflows/epoch.py
d9000246ac9880c206fde75f8243d551  src/app/adapter/main.py
8cc21b83af21215a0143ec6e57803f8d  tests/unit/test_roster_window.py
96025bb7c04e7350e3edac2aed0324fa  tests/unit/test_yaml_guard.py
cab2b04b67e50f24c0f9b556dd2d41f3  tests/unit/test_api_config.py
```

`diff baseline.md5 after.md5` → **ALL 10 FILES BYTE-IDENTICAL.** `git status --short` at the end shows
exactly one modified file, `docs/plans/m6-wave-3-close.md`, which was already modified in the working
tree **before this review began** and was not touched by me. No file in the repository differs because
of this seat.

### Mutant ledger — 29 run, 18 killed, **11 stayed GREEN**

| # | Mutant | Result | Killed by |
|---|---|---|---|
| M01 | `validate_startup_config` short-circuits to `return ()` | RED | 4 tests in `test_api_config.py` |
| **M02** | **`validate_startup_config` renamed out of existence; suite run MINUS `test_api_config.py`** | **GREEN (327 passed)** | **nothing — no production caller exists** |
| **M03** | **`allow_credentials=False` → `True`** (`main.py:157`) | **GREEN** | **nothing** |
| **M04** | **`allow_origins=list(_ALLOWED_ORIGINS)` → `["*"]`** (`main.py:154`) | **GREEN** | **nothing** |
| **M05** | **CORS middleware never installed (`if _ALLOWED_ORIGINS:` → `if False:`)** | **GREEN** | **nothing** |
| M06 | expansion bound removed from `yaml_guard` | RED | `test_yaml_guard.py:35,76` |
| M07 | shared nodes counted once (graph size, not expanded size) | RED | `test_yaml_guard.py:35,76` |
| M08 | expansion counted additively (`len(node.value)`) | RED | `test_yaml_guard.py:35,76` |
| M09 | byte-size bound removed | RED | `test_yaml_guard.py:54` |
| M10 | `rosters.py` back to `yaml.safe_load(raw)` | RED | `test_yaml_guard.py:93` |
| M11 | `epoch.py` back to `yaml.safe_load(raw)` | RED | `test_yaml_guard.py:93` |
| **M12** | **`rosters.py` bypasses the guard via `yaml.load(raw, Loader=yaml.SafeLoader)`** | **GREEN** | **nothing — the wiring test is a literal grep for `yaml.safe_load(`** |
| M13 | served notice reads `plan_config.staleness_days` again (the original W-008 defect) | RED | `test_roster_window.py:203` |
| M14 | `roster_staleness_days` silently falls back to the plan window | RED | `test_roster_window.py:107` |
| M15 | migration column gains `DEFAULT 30` | RED | `test_roster_window.py:107` |
| M16 | `ingest_rosters` stops persisting the window | RED | `test_roster_window.py:76` + 4 in `test_rosters.py` |
| M17 | `connect()` calls the private `_migrate` again | RED | `test_roster_window.py:157` |
| M18 | `plan_config.roster_staleness_days` removed from `_MIGRATIONS` | RED | `test_roster_window.py:107` |
| **M19** | **`ROLLBACK TO model_ranking_schema_migrate` deleted from `migrate()`** | **GREEN** | **nothing** |
| M20 | roster rows never aged (early-out always taken) | RED | `test_roster_window.py:203` + 2 in `test_rosters.py` |
| M21 | early-out removed: a plan-only database now demands a roster policy | RED | 21 tests |
| **M22** | **guard moved AFTER the parse (`yaml.safe_load(raw)` executed before the bound is checked)** | **GREEN** | **nothing — despite `test_yaml_guard.py:35`'s docstring claiming the opposite** |
| M23 | CORS validated only in production | RED | `test_api_config.py:90` |
| M24 | production fail-closed downgraded to a warning | RED | `test_api_config.py:53,63` |
| M25 | malformed-origin (scheme) check removed | RED | `test_api_config.py:32` |
| **M26** | **`APP_ENV` read without `.lower()` (so `APP_ENV=Production` escapes fail-closed)** | **GREEN** | **nothing** |
| **M27** | **SAVEPOINT removed ENTIRELY from `migrate()` — `return _migrate(conn)`** | **GREEN (336 passed)** | **nothing** |
| **M28** | **`MAX_EXPANDED_NODES` loosened 20× (500k → 10,000,000)** | **GREEN** | **nothing** |
| M29 | `MAX_EXPANDED_NODES` loosened 200× (500k → 100,000,000) | RED | `test_yaml_guard.py:35` |

Row 5 of the close checklist claims *"11 mutants, 11 killed; 1 stayed green on first contact."* Eight
of my eleven stay-greens are in areas that row explicitly lists as covered: *"a wildcard accepted"*
(M04 — accepted at the middleware, not at the parser), *"production booting without a database"*
(M02 — it does), and the migration's atomicity (M19, M27). **The eleven mutants that were run were
the eleven the author expected to survive.**

---

## BLOCKING

### B-1 — `src/app/adapter/main.py:115` — the startup validator has no production caller (V3C-73, REQ-API-006)

Row 7 claims invariant **(c) "production fails CLOSED at startup on missing security config"**, cited
to `test_production_refuses_to_boot_without_its_evidence_database` (`tests/unit/test_api_config.py:53`).
That test calls `validate_startup_config(env="production")` **directly**. Nothing else does.

```
$ grep -rn "validate_startup_config" src/ scripts/ Makefile
src/app/adapter/main.py:115:def validate_startup_config(...)      # the definition
```
No import-time call, no `@app.on_event("startup")`, no `lifespan=`. `make run` is
`uvicorn app.adapter.main:app`, which only imports the module. Measured through the live app:

```
$ env -u MODEL_RANKING_DB -u MODEL_RANKING_CORS_ORIGINS APP_ENV=production .venv/bin/python -c "..."
APP_BUILD = unknown | db path = None
PRODUCTION BOOTED. /health -> 200 {'status': 'ok', 'version': '0.1.0', 'build': 'unknown'}
/v1/categories -> 200 {...}
```

A production process with **no evidence database and no build stamp** boots and answers. The function
whose docstring says *"Check the security-relevant configuration once, at import, and fail CLOSED in
production"* is never invoked at import. M02 proves it mechanically: rename the function out of
existence and the entire suite minus `test_api_config.py` is 327 passed.

The wave has the antidote to this defect **in its own test file** — `test_roster_window.py:157` asserts
from source that production calls the migration entry point the tests exercise, precisely because
"the suite then reports on a path nobody takes." The same reasoning was not applied to the validator
one file over.

This is BLOCKING under §1 of the profile: a criterion whose citing test does not exercise the claimed
behaviour is coverage theater, and under permission-matrix §11 a PASS on an unproven security clause
is not available.

**Also unwired in the same block, and worse:** `APP_BUILD` is a plain module-level constant
(`main.py:47`), so even with the validator wired at import, `test_production_refuses_to_boot_without_a_build_stamp`
(`test_api_config.py:63`) only passes because it `monkeypatch.setattr`s the constant. Nothing proves
the real boot path reads it.

### B-2 — `src/app/workflows/rosters.py:242` — the migration leaves an existing populated database unservable, and no live-entrypoint test says so

`test_a_pre_m6_database_migrates_without_inventing_a_policy` (`test_roster_window.py:107`) builds a
database containing **only** a `plan_config` table with one row. It has no `plan_models`, therefore no
roster links, therefore `_stale_notice`'s new early-out at `subscribe.py:300` returns before
`roster_staleness_days()` is ever reached on the serving path. The test then asserts the loud failure
by calling `_roster_window(conn)` — a unit shim (`test_roster_window.py:26`), not a live entry point.
**Row 6 lists this test as proof of live-entrypoint coverage for REQ-SUB-008. It is not.**

The database shape that actually exists is the one with roster links. It is in this repository:

```
$ .venv/bin/python -c "...PRAGMA table_info(plan_config)..."
advisor.db  cols=['id','staleness_days','cap_dusuk','cap_orta']  roster_links=18  row=(1, 30, 10.0, 25.0)
```

Migrated with the shipped operator command, which reports success:

```
$ cp advisor.db /tmp/m6w3/advisor-copy.db
$ .venv/bin/python -m app.workflows.schema migrate --db /tmp/m6w3/advisor-copy.db
{ "database": "...", "applied": ["plan_config.roster_staleness_days", "scores.effort"], "applied_count": 2 }
```

Then served through the live CLI entry point:

```
$ .venv/bin/python -m app.workflows.recommend --subscription --budget unlimited --task assistant \
    --db /tmp/m6w3/advisor-copy.db
{"error": "plan_config.roster_staleness_days is unset — re-ingest data/rosters.yaml ..."}
```

`schema migrate` exits 0 and prints a success payload; the next `recommend --subscription` fails.
**That is the exact W-004 symptom class `_validate_migration_input` was written to eliminate** — the
docstring at `schema.py:328` describes it in those words — reinstated by this wave with a different
column. A migration that adds a column the serving path requires, does not backfill it, and ships no
operator step to fill it is not finished.

The author met this shape and patched around it. `tests/unit/test_subscribe.py:594` was edited this
wave to add `UPDATE plan_config SET roster_staleness_days = 30` to a fixture that inserts roster links
by hand — *"A database carrying roster links with no roster window is incoherent."* That fixture is
`advisor.db`. The test was made to supply the value; the migration was not.

I am not ruling on whether fail-loud or backfill is the right answer — that is the owner's call and
a Code-Reviewer's. I am ruling that **the wave ships a migration whose post-migration serving state
is untested through any live entry point**, while row 6 claims otherwise.

### B-3 — `src/app/workflows/schema.py:264-271` — the migration's rollback is described, never proven

W-009's entire premise (`schema.py:250` docstring, row 6, plan §3 W3.3) is that the SAVEPOINT wrapper
was *"exercised by tests and by nothing else"* and that this mattered. After the reconciliation, the
SAVEPOINT is exercised by **nothing that can tell whether it is there**:

- **M19** (delete `ROLLBACK TO`) → 336 passed.
- **M27** (delete the whole SAVEPOINT/try/except/RELEASE, leaving `return _migrate(conn)`) → **336 passed.**

`test_the_public_migration_rolls_back_cleanly_inside_a_caller_transaction` (`test_roster_window.py:180`)
calls `migrate(conn)` on an **already-current** schema. It returns `[]` — zero statements executed, no
failure raised — so the SAVEPOINT does nothing observable and its absence is invisible. The test's name
promises a rollback proof; its body proves that a no-op nests without erroring. That is a
mirror-implementation test under V3C-86, which is BLOCKING at HIGH tier.

The rollback **does** work — I proved it myself, which is the point: a Tester had to, because the suite
does not. Booby-trapped a pre-M6 database with a pre-existing `scores__m5_effort` table so the scores
rebuild fails partway through:

```
migrate() raised OperationalError: table scores__m5_effort already exists
plan_config cols before:                          ['id','staleness_days','cap_dusuk','cap_orta']
plan_config cols after failed migrate (in txn):   ['id','staleness_days','cap_dusuk','cap_orta']
ROLLED BACK CLEANLY? True
```

The behaviour is right. The proof is missing, on a HIGH-tier wave whose tier exists for this.

---

## Acceptance-criterion coverage (V3C-02)

- **REQ-SUB-008** → `tests/unit/test_roster_window.py:203`
  (`test_the_served_notice_ages_a_roster_link_on_the_roster_window`, cites W-008) — **GREEN, and it is
  the one test in this file that earns its place.** It enters through `recommend_subscription` on a real
  database, sets plan 365 / roster 5 against a 10-day-old link, and asserts **both** directions. M13
  (restore the original defect) and M20 (never age roster rows) both kill it. Supporting:
  `:50` and `:76` GREEN and each killed by a mutant (M16). `:33` is a schema-shape assertion that
  proves nothing behavioural and would survive M13 — harmless, but it is not coverage.
  **Not proven:** the post-migration serving state on a database that has roster links → **B-2**.
- **W-005** → `tests/unit/test_yaml_guard.py:35,54,60,66,76,93` — **GREEN.** The arithmetic is the
  strongest part of this wave; see the audit below. **Weakened by:** the wiring test being a grep
  (M12) and the "before it is parsed" claim being unenforced (M22) → MINOR-1, MINOR-2.
- **W-009** → `tests/unit/test_roster_window.py:157` — **GREEN** for the single-entry-point half
  (M17 kills it). The atomicity half is **unproven** → **B-3**.
- **REQ-API-006** →
  - *CORS is an allowlist, never allow-all* → `test_api_config.py:16,32,39,45,90` — **GREEN at the
    parser only.** Every one of these tests exercises `cors_origins()` as a pure function. **No test
    exercises the middleware the function feeds** (M03, M04, M05 all GREEN; `main.py:150-152` is in
    the coverage report's uncovered list). → MINOR-3.
  - *config validated at startup, refuses to serve in production* → `test_api_config.py:53,63,76` —
    **NOT PROVEN** → **B-1**.
  - *database handle opened read-only* → satisfied in W1; not re-checked here.
  - *no plaintext credential in source* → satisfied in W1; not re-checked here.

## Row 7 — the four new security invariants, each against the mutant that should kill its negative test

| Invariant | Negative test | Mutant | Result |
|---|---|---|---|
| **(a)** curated YAML bounded by EXPANDED size, not alias count | `test_yaml_guard.py:76` | M07 (count shared nodes once), M08 (count additively) | **HOLDS** — both RED. This is a genuinely well-chosen invariant and a genuinely load-bearing test. |
| **(b)** a wildcard CORS origin is refused in every environment | `test_api_config.py:90` | M23 (validate only in production) | **HOLDS at the parser** — RED. **DOES NOT HOLD at the surface**: M04 puts a literal `"*"` into `add_middleware` and 336 tests pass. The invariant as written ("a wildcard origin is refused") is proven for the env var and not for the served header. |
| **(c)** production fails CLOSED at startup on missing security config | `test_api_config.py:53` | M24 (downgrade to warning) → RED; **M02 (no production caller) → GREEN** | **DOES NOT HOLD.** The negative test fails when the *function* is broken and passes when the *invariant* is absent. → **B-1** |
| **(d)** an unset roster policy fails loud rather than borrowing the plan window | `test_roster_window.py:107` | M14 (silent fallback), M15 (`DEFAULT 30`), M18 (drop the migration entry) | **HOLDS at the unit boundary** — all three RED. Not proven through a live entry point → **B-2**. |

Two of four invariants are proven as stated. One is proven for its helper and not for its effect.
One is not proven at all.

## The YAML guard's arithmetic — independent audit

I did not take `_expanded_size` on trust. Constructed documents whose true expansion is computable by
hand, and compared:

**Boundary.** `a: &a [<9 scalars>]` + `b: [*a × k]`. By hand the root mapping expands to
`5 + 9 + 10k` nodes. Measured against `MAX_EXPANDED_NODES = 500_000`:

| k | predicted | `_expanded_size` | match | verdict |
|---|---|---|---|---|
| 49 997 | 499 984 | 499 984 | ✅ | LOADED |
| 49 998 | 499 994 | 499 994 | ✅ | LOADED |
| 49 999 | 500 004 | 500 004 | ✅ | REFUSED |
| 50 000 | 500 014 | 500 014 | ✅ | REFUSED |

**The multiplication is exact, and `>` is the right comparison at the boundary.** Memoising by
`id(node)` over a graph with shared alias nodes is correct here because the memo returns the cached
*subtree total* and the caller re-adds it per reference — the sharing is in the graph, the
multiplication is in the sum. Node lifetime is safe: the composed root holds every child alive for the
whole walk, so no `id` can be recycled mid-traversal.

**Cycles.** `a: &a [*a]` and `a: &a [*a × 10]` both terminate — the `memo[key] = 1` pre-seed at
`yaml_guard.py:56` is a correct cycle guard. No `RecursionError`, no hang. Sizes 3 and 13.

**Merge keys (`<<:`), which the docstring does not mention.** They are counted, because a merge's value
node is an ordinary alias in the composed graph. A deliberate merge-key bomb — 50 keys at level 0, then
8 levels each merging 9 references to the level below — composes to **4 909 344 003** nodes and is
**REFUSED**. Note this is a conservative over-estimate: merging the same mapping nine times yields one
set of keys, not nine, so the guard over-counts merge expansion. Over-counting is the safe direction
and the shipped curated files are nowhere near the bound (`test_yaml_guard.py:45` is what keeps that
honest). **No change needed; the docstring should say `<<:` is covered.**

**A correction to the guard's stated premise, which the Code-Reviewer should see.** `yaml_guard.py:4-6`
asserts that M4 measured *"MemoryError in about ten seconds under a 1 GiB limit"* from this document.
That is not reproducible at the load boundary this guard sits on:

```
safe_load of the 'billion laughs' doc: 0.001s, peak RSS 16.8 MB
h[0] is h[1] (shared object?): True
len(h) = 9   id-distinct members: 1
```

PyYAML's `SafeConstructor` caches constructed objects per node, so `safe_load` returns a **shared DAG**
and never materialises the expansion. The guard is still correctly placed and still load-bearing — the
amplification is realised by any *consumer* that walks or copies the DAG, and `parse_plans_doc` /
`parse_rosters` iterate entries immediately after the load — but the docstring's factual claim about
`safe_load` itself is wrong, and a future agent will use it to decide where the guard belongs.

## Databases the author did not build

| Scenario | Built | Result |
|---|---|---|
| Pre-M6 db with **roster links and no policy**, rows in every table | ✅ | Migrates, then **serving raises `ValueError`** → **B-2**. Untested. |
| `plan_config` with **no row at all** | ✅ | Fails loud: `"plan_config missing — ingest the curated plan table first"` (`rosters.py:244-245`). Correct — and **uncovered**, per the coverage report. → MINOR-6 |
| Migration **fails partway** | ✅ | Rolls back cleanly, verified column-for-column. Correct — and **untested** → **B-3**. |
| **8 concurrent** `connect()`/migrate on one file | ✅ | All 8 succeed, final schema correct, 1 scores row preserved, no stray `scores__m5_effort`. `BEGIN IMMEDIATE` serialises correctly. **Correct and untested** → MINOR-5. |
| `migrate()` run **twice / three times** on the same connection | ✅ | `[]`, `[]` — idempotent. Covered by `test_roster_window.py:152`. |
| Pre-M6 db with rows in **every** table | ✅ | Row counts preserved across the migration: `models 3, scores 3, plans 4, plan_config 1, plan_models 4`. |

## Red→green on reported symptoms

- **W-008** (roster link aged on the plan table's clock) → `test_roster_window.py:203` reproduces it.
  I confirmed the red half myself: **M13** restores the original defect verbatim and that test is the
  only one in 336 that fails. Genuine red→green. Row 5's account of how this test came to exist —
  found by injection after the first version proved only plumbing — matches what I measured, and it is
  the one row of that checklist that is fully honest.
- **W-005** → `test_yaml_guard.py:35,76` fail on M06/M07/M08. Genuine.
- **W-009** → `test_roster_window.py:157` fails on M17. Genuine for the entry-point half only.

## Test-integrity (V3C-86 — BLOCKING at HIGH tier)

- **Weakened / deleted-to-green: CLEAN.** `git diff 67fd92b -- tests/` removes **no** `assert`, no
  `def test`, no `pytest.raises`, and adds no `skip`/`xfail`. The only edit to a pre-existing test file
  is `tests/unit/test_subscribe.py:594`, five added lines that give a hand-built fixture the roster
  policy the new code requires. It does not weaken an assertion. (It is, however, the evidence for
  **B-2**: the fixture was made coherent, the migration was not.)
- **Mirror-implementation: TWO FOUND.**
  - `test_roster_window.py:180` — asserts a no-op nests; survives total removal of the SAVEPOINT (M27).
    → **B-3**.
  - `test_yaml_guard.py:35` — its docstring states *"If this test ever hangs or dies instead of raising,
    the guard has been moved to after the parser, which is the one place it cannot work."* M22 moves
    the parse before the bound and the suite is green. The name promises ordering; the body proves
    refusal. → MINOR-2.
- `test_roster_window.py:157` and `test_yaml_guard.py:93` are **source-grep** tests. They are the right
  instinct for "built ≠ wired" and I would keep both, but a grep asserts spelling, not behaviour — see
  MINOR-1 for the bypass that walks straight through one of them.

## Suite result

- `make test`: **336 passed, 12 skipped** (checklist row 2 claims 335 — the difference is not a
  discrepancy I could attribute to a missing test; every test named in row 6 exists and runs).
- Coverage on touched code: `adapter/main.py` **95%** (uncovered: **150-152 — the CORS middleware
  block**, 270, 473-474, 482-483, 558) · `workflows/schema.py` **94%** · `workflows/rosters.py` **84%**
  (uncovered includes **244-245**, the `plan_config missing` branch) · `workflows/subscribe.py` **96%**
  · `workflows/yaml_guard.py` **90%**. TOTAL **85%**. No drop on any touched module.
- The uncovered ranges are not incidental: `main.py:150-152` is the mechanical confirmation of MINOR-3,
  and `rosters.py:244-245` of MINOR-6.

## Mocks / contract tests (V3C-44)

This wave adds no external integration. The three YAML inputs route through one canonical loader,
`safe_load_bounded` — that consolidation is a V3C-44 improvement, and `test_yaml_guard.py:45` running
the guard against the **real shipped** `data/plans.yaml` and `data/rosters.yaml` is the contract test
for it. No bespoke per-test YAML stub appeared. **OK.**

## MINOR (queue to next-M unless the author is already in the file)

- **MINOR-1** — `tests/unit/test_yaml_guard.py:93`. The wiring test greps for the literal string
  `yaml.safe_load(`. `yaml.load(raw, Loader=yaml.SafeLoader)` is semantically identical, bypasses the
  guard, and passes the grep (**M12 GREEN**). Assert against the loader that is *called* — e.g. patch
  `yaml_guard.safe_load_bounded` and require every parse entry point to route through it — or extend
  the grep to `yaml.load(`/`yaml.full_load(`/`yaml.unsafe_load(`.
- **MINOR-2** — `tests/unit/test_yaml_guard.py:35`. The docstring's ordering claim is unenforced
  (**M22 GREEN**). A `monkeypatch` on `yaml.safe_load` asserting it is never reached on a refused
  document would make the name true.
- **MINOR-3** — `src/app/adapter/main.py:148-158`. Nothing tests the middleware, only the function that
  configures it: **M03** (`allow_credentials=True`), **M04** (literal `"*"` origins) and **M05** (no
  middleware at all) are all invisible. `_ALLOWED_ORIGINS` is bound at import, so `monkeypatch.setenv`
  after import can never reach it — the test needs a subprocess or an `importlib.reload`. The positive
  direction does work; I measured it out-of-band with the env var set before import (allowed origin
  echoed, `https://evil.example.com` not). **It just isn't tested**, and V3C-13's own clause
  (allow-all *with credentials*) has no test at the place where credentials are actually configured.
- **MINOR-4** — `src/app/workflows/yaml_guard.py:34`. `MAX_EXPANDED_NODES` is a security parameter with
  no boundary test: it can be loosened **20×** invisibly (**M28 GREEN**) and is only pinned somewhere
  below 108× (M29 RED at 200×). A two-line test at `k=49998`/`k=49999` — the exact pair I computed
  above — pins it precisely and costs nothing.
- **MINOR-5** — no test covers concurrent migration. I verified 8-way concurrency is correct; E.5 lists
  concurrency among the hard criteria that must ship in the wave that creates them, and a migration
  wave is that wave.
- **MINOR-6** — `src/app/workflows/rosters.py:244-245`, the `plan_config missing` branch, is uncovered.
  Correct behaviour, no test.
- **MINOR-7** — `src/app/adapter/main.py:120`. The `.lower()` that makes `APP_ENV=Production` fail
  closed is untested (**M26 GREEN**). One parametrised case closes it.
- **MINOR-8** — `src/app/workflows/yaml_guard.py:4-6` and `:41-52`. The docstring's *"MemoryError in
  about ten seconds"* claim about `safe_load` is not reproducible (measured: 0.001 s, 16.8 MB, shared
  objects). The guard is right; the stated reason is not, and the docstring is silent on `<<:` merge
  keys, which it does in fact bound. For the Code-Reviewer.
- **MINOR-9** — `docs/plans/m6-wave-3-close.md:20`. Row 5's *"11 mutants, 11 killed"* is not a safe
  summary to carry into closure. Eleven of twenty-nine survive, three of them on behaviours that row
  names as covered. Suggest the row record the mutants **run and survived**, not only the score.

## Tests added/extended this review

**None.** Per the rules of this seat I modified no file in the repository; all injection, fixture and
database work was done under `/tmp/m6w3/` and every touched source file is md5-identical to its
pre-review state. The three BLOCKING findings each name the test that must be written, and B-1's and
B-3's are small enough to land in this wave:

1. **(B-1)** a test that boots the **real ASGI app** under `APP_ENV=production` with `MODEL_RANKING_DB`
   unset — in a subprocess, so import-time wiring is exercised — and asserts the process refuses to
   start. Plus the source-shaped guard this wave already applies to the migration at
   `test_roster_window.py:157`: assert `validate_startup_config` has a call site.
2. **(B-3)** a test that makes a migration fail **partway** — a pre-M6 database with a pre-existing
   `scores__m5_effort` table is sufficient and takes four lines — and asserts no column was added.
   It must fail when the SAVEPOINT is removed.
3. **(B-2)** — the most important one — below.

## The single most important missing test

**A pre-M6 database that has roster links, migrated through `schema migrate`, then asked for a
subscription recommendation through the live entry point.**

Every existing REQ-SUB-008 test builds either a *fresh* database (which `connect()` + `ingest_rosters`
always populates) or a *roster-free* one (which takes the new early-out). Neither is the database that
exists. `advisor.db` — in this repository, 18 roster links, pre-M6 `plan_config` — migrates with an
`applied_count: 2` success payload and then returns `{"error": "...roster_staleness_days is unset..."}`
to the next question a user asks. **The wave's migration and the wave's serving path were each tested
against a database the other one would never see.** One test that runs both against the same database
catches it, and it is the test whose absence let a HIGH-tier wave report a clean fault-injection pass.

---

**Verdict: BLOCKING.** Rows 5, 6 and 7 of `docs/plans/m6-wave-3-close.md` overstate what is proven and
must be corrected before the wave closes. The wave does not close until B-1, B-2 and B-3 have passing
citing tests. The code, as far as 29 mutants and six hand-built databases could reach it, is correct —
which is exactly why it needs to be proven rather than asserted.
