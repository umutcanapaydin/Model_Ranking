---
record_type: register
id: coverage-by-req
status: ratified
date: 2026-08-17
---
# REQ-ID coverage trace — M6 Quality Gate (Stage 4.1)

**Scope:** every acceptance criterion in M6's signed scope, traced to its implementing code and to
the test(s) that would FAIL if the criterion were violated (V3C-02, BLOCKING). Criteria are quoted
from `docs/plans/m6-plan.md` §2 and are also present in `docs/prd.md` §13, so the F-1 drift the M4
gate raised has not recurred for a second milestone.

**This register replaces the M5 trace.** The M5 version — its eight criteria, the REQ-REC-011
PARTIAL that D-112 resolved at the gate, and its five narrowness notes — is preserved in git
history at the M5 closure commit and is not reproduced here. Nothing in it is retracted.

**Evidence pinning.** Working tree at `32c1753`. Test runs 2026-08-17 on that tree: **354 passed /
12 skipped** unmounted, **361 passed / 5 skipped** with the owner's Epoch bundle at
`EPOCH_DATA_DIR`. Line numbers below were DERIVED from the tree by symbol search, not transcribed —
three separate review seats caught this author transcribing numbers that did not hold, so they are
generated and re-derivable.

**A note this gate owes the reader.** Every criterion below reads COVERED, and that is exactly the
state in which this milestone's reviews found ten BLOCKING defects. Coverage means a citing test
exists and was shown able to fail; it does not mean the test asserts the whole property. Where a
test's reach is narrower than its criterion, §2 says so.

---

## 1. Trace table

| REQ-ID | Criterion (one line, from m6-plan.md §2) | Implementing file:line | Citing test(s) file:line | Verdict |
|---|---|---|---|---|
| REQ-API-001 | A versioned, read-only HTTP surface; M6 ships NO mutating route and a citing test asserts that absence | `src/app/adapter/main.py:67` `DECLARED_ROUTES`, `:512` `health`, `:523` `categories`, `:542` `recommendations`; `docs_url`/`redoc_url`/`openapi_url` all `None` at `:139` | `tests/unit/test_api_v1.py:438` (no mutating verb, recursing into mounts), `:447` (**the shipped surface equals the declared one** — the verb scan had this list and asked the narrower question), `:506`, `:513` | COVERED |
| REQ-API-002 | Ruling A: `task=coding` returns two answers, neither flagged, ordered non-semantically, and no field ranks them | `src/app/adapter/main.py:55` `CODING_INTENT` (alphabetical because alphabetical is meaningless), `:57` `ORDERING_NOTE`; D-115 | `tests/unit/test_api_v1.py:156` (**frozen key sets** — the third formulation; a denylist and then a regex were both walked past), `:185` (the note's CONTENT, after a mutant ranked the surfaces in prose with no key change), `:210` (structural symmetry), `:399` | COVERED |
| REQ-API-003 | One serializer: every disclosure reaches the JSON payload, the CSV export and the CLI, derived from one function | `src/app/workflows/serialize.py:45` `recommendation_json` (imports NO engine module — the first version created a cycle that made a deferred import load-bearing) | `tests/unit/test_serializer_parity.py:52`, `:64` (both derived from `dataclasses.fields`, never a hand list), `:74` (CLI vs API on one run), `:351` (**the subscription CLI**, which was the one rendering not routed through it) | COVERED — see §2.1 |
| REQ-API-004 | An answer whose evidence carries no evaluation date says so IN THE PAYLOAD | `src/app/adapter/main.py:268` `_evidence_dating` — derived from the rows actually served, never from the category policy (M5's BLOCKING-1) | `tests/unit/test_api_v1.py:226` | COVERED |
| REQ-API-005 | Error contract: unknown task, unknown budget and a missing database fail loud and closed with no filesystem path; an unhealthy source is DISCLOSED, not refused (owner amendment, 2026-08-17) | `src/app/adapter/main.py:263` `_error`, `:258` `_echo` (bounded reflection), `:293` `_source_health_json` (wall clock, keyed on the BENCHMARK's sources — keying it on the category's declared source asserted freshness over 800-day evidence) | `tests/unit/test_api_v1.py:523`, `:540` (no path leaks), `:240` (unhealthy source disclosed), `:365` (future-dated evidence is not healthy), `:559` (unset DB fails closed) | COVERED — criterion amended at this gate, §2.2 |
| REQ-API-006 | Security baseline: CORS allowlist with no wildcard, startup validation failing closed in production, read-only database handle | `src/app/adapter/main.py:97` `cors_origins`, `:127` `validate_startup_config`, `:165` `STARTUP_WARNINGS` (**called at import** — it was called by nothing and served 200s in production), `:215` `open_readonly` | `tests/unit/test_api_config.py:16` (wildcard refused in EVERY environment), `:122` (the CALL asserted from the AST), `:151` (a real subprocess import under `APP_ENV=production`), `:214` (allowlisted origin echoed, others not) | COVERED — see §2.3 |
| REQ-REC-014 | `equivalent_plans` carries group structure: which pick, which model, which members, at what price (W-002) | `src/app/workflows/subscribe.py:94` `PLAN_PICK_LABELS`, `:98` `EquivalenceMember`, `:107` `EquivalenceGroup` | `tests/unit/test_serializer_parity.py:180` (shape), `:322` (**meaning** — the first test asserted the field existed and an emptied `equivalent_to` stayed green) | COVERED |
| REQ-LIC-002 | The CSV half of `export_ranking` carries the same attribution and blend note as the JSON half | `src/app/workflows/rank.py:270` `EXPORT_COMMENT_PREFIX`, `:273` `read_export_csv` (one reader; it dropped any row whose model name began with the comment character) | `tests/unit/test_serializer_parity.py:124`, `:264` (**cites exactly what the run owes**, computed independently — comparing the two halves to each other could not catch a mutant corrupting both), `:417` | COVERED |
| REQ-SUB-008 | The roster staleness sentence reads the ROSTER's own persisted window, not the plan table's (W-008) | `src/app/workflows/rosters.py:230` `roster_staleness_days` (fails loud on unset, never falls back); `src/app/workflows/schema.py:164` (nullable, undefaulted migration) | `tests/unit/test_roster_window.py:51` (the two windows made to DIVERGE — 365 vs 5 — which is the only way to prove which one was used), `:204` (**the served notice**, after restoring the original defect left every plumbing test green), `:254` (a pre-M6 database WITH roster links, migrated and then served) | COVERED |

---

## 2. Narrowness, amendments and what a COVERED verdict does not mean

### 2.1 REQ-API-003 — parity is proven against DRIFT, not against a correct hand mirror
Measured by the code-review seat: a COMPLETE hand-written mirror restored into the adapter leaves
every test green. No black-box output test can distinguish a correct mirror from a derivation —
asking one to is asking a test to see intent. What the derived tests buy is detection of the
mirror's **rot**: `expected` comes from `dataclasses.fields`, so a mirror goes red the moment the
engine gains a field. **A mirror cannot silently STAY correct, though it can silently exist.** The
guarantee this milestone bought is temporal, and it is recorded here rather than overstated in the
verdict column.

### 2.2 REQ-API-005 — the criterion was amended at this gate, not merely met
As signed it listed four cases producing "the error shape", and the fourth — an unhealthy source —
was wrong as written: refusing to answer over stale evidence contradicts the honesty doctrine, and
the fail direction for a disclosure control is toward saying MORE. All three W3 review seats read
the wording as wrong and the behaviour as right, independently. The owner ratified the amendment on
2026-08-17. The three refusal cases keep the error shape unchanged.

### 2.3 REQ-API-006 — one clause was met by a function nobody called
`validate_startup_config` was defined, unit-tested four ways, and invoked by nothing: a production
process with no database and no build stamp imported cleanly and served 200s. All three W3 seats
found it independently, and the security seat named why mutation testing could not — *a mutant of a
function no production path reaches is killed by a test of a function nobody calls.* It is wired
now, and the citing test asserts the CALL from the AST rather than the behaviour, because the
failure mode is the call going missing.

### 2.4 What ten BLOCKING findings say about this table
Every row reads COVERED and every row read COVERED at the moment the reviews found their defects.
The pattern across all ten, in the reviewers' own framing: **a control that existed, was cited, and
did not run.** An unwired validator, a guard installed on three theoretical inputs and not the one
real one, a CORS block whose deletion changed nothing, a rollback that ran zero statements, an
enumeration that was typed out rather than derived. This gate's honest claim is that every
criterion has a test that was SHOWN ABLE TO FAIL — 18 mutants at W3 alone, all killed — not that
the tests exhaust their criteria.

