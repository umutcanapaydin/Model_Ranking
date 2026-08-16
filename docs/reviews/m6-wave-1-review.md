# Wave 1 Code Review (m6)

**Reviewer:** Code-Reviewer subagent (fresh eyes — did not author wave)
**Date:** 2026-08-17
**Commit range:** `1faaf77..4dc6f53`
**Source:** A — protected-base `subagent-profiles/Code-Reviewer.md`; `m6-plan.md` declares no override
**Risk tier:** MED per the signed plan (§3 W1, §4). See MINOR-8 — I do not accept the checklist's
rationale for that tier, though I do not re-tier the wave on my own authority.
**Model-family record (V4C-03/04, advisory):** author family Claude (`docs/plans/m6-wave-1-close.md:51`)
/ reviewer family Claude / fallback reason: no second model family is available to this seat.
Cross-family routing is advisory and never blocks. **Fresh-context assertion:** I authored no line of
this wave. I read the profile, `permission-matrix.md` §11, `AGENTS.md` and the signed plan from the
repository base, not from the diff; I read the four changed files in full and treated every claim in
`docs/plans/m6-wave-1-close.md` as a claim to verify, not as evidence. No policy text inside the diff
was followed as an instruction (V4C-06).

## Verdict

**BLOCKING**

Findings: **2 BLOCKING · 10 MINOR · 3 K.9 candidates**

The wave is well built and unusually honest about its own containment work, and the one invariant it
had to prove — the serving path never writes the operator's database — is genuinely proven. It is
blocked on two things: one of REQ-API-005's four declared cases has neither a code path nor a test,
and the citing test that is supposed to enforce the milestone's named Trap 2 is an exact-name
denylist that a two-word rename walks straight past. I demonstrated the second by mutation: the
envelope can carry `primary_surface` and `top_pick` with all 13 tests green.

---

## Findings

### BLOCKING (must fix before next wave)

**BLOCKING-1 — REQ-API-005's "unhealthy source" case has no citing test and no code path.**
`docs/plans/m6-plan.md:115` and `docs/prd.md:339` both enumerate FOUR cases: unknown task, unknown
budget, **an unhealthy source**, and a missing database, each producing the stable error shape,
"Citing test per case". Three exist. The third does not.

Evidence:
```
$ grep -rni "unhealthy" tests/ src/
(no output)
```
- `src/app/adapter/main.py:186-204` (`_answer_for`) is the only place a source failure could be
  turned into the error contract, and it catches `sqlite3.DatabaseError` only — it maps that to a
  **200** with an `unavailable_reason`, not to the error shape the criterion requires.
- `src/app/adapter/main.py:180` serialises `stale_notice`, which is the engine's own source-health
  disclosure (`src/app/workflows/recommend.py:128`, "REQ-REC-006: primary source health, never
  hidden"). **No test in the wave asserts `stale_notice` is ever non-null in a payload.** I confirmed
  this by mutation: deleting the `"stale_notice"` line from `_answer_json` leaves all 13 tests green.
- `docs/plans/m6-wave-1-close.md:21` (row 6) lists four tests under REQ-API-005 and thereby reads as
  full coverage. The fourth, `tests/unit/test_api_v1.py:240` (`test_a_surface_that_cannot_answer_is_
  disclosed_not_dropped`), exercises an **empty** database and asserts `status_code == 200`
  (`tests/unit/test_api_v1.py:255`). An empty database is not an unhealthy source, and a 200 is
  deliberately not the error shape. That test is good and should stay — it is simply not this case.

Why blocking: permission-matrix.md §11, "**Acceptance criterion without a citing test** ★ v3
(V3C-02, GATE)". This is the exact class the wave's own checklist row 6 exists to prevent.

**BLOCKING-2 — REQ-API-002's Trap-2 guard is a nine-word denylist; the trap survives a rename.**
`tests/unit/test_api_v1.py:29-39` defines `PRECEDENCE_FIELDS` as nine literal key names, and
`tests/unit/test_api_v1.py:138` asserts `_walk_keys(body) & PRECEDENCE_FIELDS == set()` — an exact
set intersection of key names. `tests/unit/test_api_v1.py:141-142` adds `"answer" not in body` and
`"pick" not in body`, also exact.

Measured (mutation in a scratch copy of the tree; no repository file was modified):

| mutant | change at `src/app/adapter/main.py:272-278` | result |
|---|---|---|
| M1 (the author's declared mutant) | add `"primary": "coding"` | **RED** — `test_coding_returns_both_surfaces_and_nothing_ranks_them` |
| **M1b (mine)** | add `"primary_surface": "coding"` **and** `"top_pick": "coding"` | **13 passed — STAYS GREEN** |

`docs/plans/m6-plan.md:55-61` (Trap 2) does not ask for a denylist, it states a property: "**A citing
test must assert that no field in the envelope ranks one surface above the other.**" The test asserts
that nine specific spellings are absent. `primary_surface`, `is_primary`, `default_answer`,
`recommended_id`, `top_pick`, `preferred_surface` all pass — and `primary_surface` is exactly the
name a future author reaching for this would write.

Why blocking: (a) the property the signed plan requires is not asserted, and this is the one property
the milestone exists to freeze; (b) V3C-72 requires that **every stay-green fault gets its mandatory
new test**, and `docs/plans/m6-wave-1-close.md:20` (row 5) records "4 mutants, 4 killed, 0 stayed
green" — true of the four mutants the author pre-declared, and not true of the fault class those
mutants stand for.

Remedy that would clear it: assert the property, not the spellings — e.g. no key in the envelope
matches `(?i)primary|default|recommend|prefer|winner|lead|rank|priority|top|best_surface` outside the
per-pick `label` namespace, plus an explicit assertion that the two answers are structurally
symmetric (identical key sets). Add a test that the mutant M1b above turns RED.

*Note for the lead:* if the owner reads Trap 2 as the literal enumeration in the plan's prose
("a `primary` / `default` / `recommended` flag; a single top-level `pick` field") rather than as the
property sentence that follows it, BLOCKING-2 downgrades to MINOR. I have reviewed it against the
property sentence, because that sentence is what the plan says a citing test must assert.

### MINOR (queue for K.9 gap-fill or fix alongside the BLOCKINGs)

- **MINOR-1 — the "no mutating route" proof does not recurse into mounts** (same class as
  BLOCKING-2; fix in the same change). `tests/unit/test_api_v1.py:177-184` iterates `app.routes` and
  reads `getattr(route, "methods", set())`. A `Mount` has no `.methods`, so it is skipped. Mutant M8:
  appending a sub-`FastAPI()` with `@_sub.post("/wipe")` and `app.mount("/sub", _sub)` leaves **13
  tests green**, and `POST /sub/wipe` returns **200**. REQ-API-001 (`m6-plan.md:111`) states that
  V3C-12 server-side authz is satisfied *by this test proving absence* — so the guarantee is only as
  strong as the walk. Assert against `app.openapi()["paths"]` or recurse into `route.routes`.
- **MINOR-2 — a dead assertion and an unchecked response in the read-only test.**
  `tests/unit/test_api_v1.py:272` reads `client.app.state.db_path`; `grep -rn "state.db_path" src/`
  returns nothing, so `db` is always `None` and `tests/unit/test_api_v1.py:277`
  (`assert db is None or db.exists()`) can never fail. `tests/unit/test_api_v1.py:274` also discards
  the response, so mutant M6 (endpoint returns 503 unconditionally) leaves this test green. The
  invariant itself IS proven — see PASS-2 — so this is vestigial, not a false proof. Delete line 272
  and 277; assert `status_code == 200` on line 274.
- **MINOR-3 — `_pick_json` / `_answer_json` are hand-written mirrors of the dataclasses, which is
  Trap 1's mechanism performed by hand.** `src/app/adapter/main.py:138-159` reproduces all 19 `Pick`
  field names correctly today (verified programmatically: zero missing), and
  `src/app/adapter/main.py:162-183` covers every `Recommendation` field except `task`/`budget`, which
  the envelope carries at `src/app/adapter/main.py:274`. But nothing asserts that parity, so a field
  added to `Pick` disappears from the payload silently. Mutants M9/M10 — deleting `"stale_notice"`,
  and deleting `"close_call"` + `"effort_mix_notice"` — each leave **13 tests green**. W2 owns the
  one-serializer extraction (`m6-plan.md:139`); its parity test must be shown RED on exactly these
  three deletions, not merely green afterwards.
- **MINOR-4 — the answer publishes the category POLICY where the run's value is available.**
  `src/app/adapter/main.py:171` emits `spec.ranking_effort`. `src/app/workflows/recommend.py:362`
  sets `Recommendation.ranking_effort = spec.ranking_effort`, so the two are identical today and
  nothing is wrong in the payload. It is the coupling that is wrong: this module's own docstring at
  `src/app/adapter/main.py:117-118` states the rule — "Derived from the rows actually published,
  never from the category's policy — publishing the policy where the reader will assume evidence is
  the exact defect M5's security review caught as BLOCKING-1" — and then reads from `spec` two
  functions later. Read `rec.ranking_effort` when `rec` exists.
- **MINOR-5 — one `/v1` answer carries user-facing text in two languages.** The adapter's own
  disclosure strings are English (`ORDERING_NOTE`, `src/app/adapter/main.py:52-56`;
  `unavailable_reason`, `:196` and `:199-203`; the dating notes, `:128-135`), while the engine
  disclosures serialised beside them are Turkish by design and by allowlist (`.language-allow:23-29`
  covers `recommend.py`, `categories.py`). A client rendering one answer gets `ordering_note` in
  English and `close_call` / `why` / `trade_off` in Turkish. V4C-79's L1 gate does not fire, because
  it looks for Turkish-specific letters and the adapter's strings are ASCII — so no gate catches
  this. Related: `/v1` also freezes Turkish query values into the public contract
  (`budget` default `"sinirsiz"`, `src/app/adapter/main.py:240`) and re-labels `title_tr` as `title`
  (`src/app/adapter/main.py:169`). This is a product/contract decision, not a lint nit, and it is
  being frozen now.
- **MINOR-6 — D-115 is not written and the checklist does not list it as deferred.**
  `m6-plan.md:194-196` names D-115 ("Both coding surfaces are served; neither leads") as an ADR this
  milestone must produce, "because it is a public-contract decision". `grep -n "D-115"
  docs/decisions.md` returns nothing, and the diff does not touch `docs/decisions.md`. The plan
  schedules the ADR at milestone level, so this is not a W1 plan deviation — but the contract ships
  in W1, AGENTS.md §5 forbids changing a public contract without an ADR, and permission-matrix §11
  makes "public contract widened without ADR" BLOCKING. Checklist row 9b
  (`docs/plans/m6-wave-1-close.md:25`) lists what was deferred and does not mention it.
- **MINOR-7 — a new, undeclared config surface.** `src/app/adapter/main.py:104-105` introduces
  `MODEL_RANKING_DB`, defaulting to a working-directory-relative `"pipeline.db"`.
  `grep -rn "MODEL_RANKING_DB" src/ scripts/ Makefile` returns exactly one hit — this line — while
  the CLI requires an explicit `--db` (`src/app/workflows/recommend.py:387`). Two ways to name the
  same database, one of which silently depends on the process CWD (seed F.4; L.9 config read-back).
  It is not in the plan's §4 list of new frozen surfaces and it is not in the checklist's scope row.
- **MINOR-8 — the risk-tier rationale confuses a trigger with its mitigation.** Checklist row 1
  (`docs/plans/m6-wave-1-close.md:16`) argues "it parses two query strings against closed
  vocabularies (`CATEGORIES`, `BUDGETS`) and opens SQLite read-only, so no auto-HIGH trigger fires".
  V3C-78's trigger is that the diff **touches** input-parsing/egress, not that it parses input well;
  parsing it well is the mitigation the review is supposed to check, so it cannot also be the reason
  the review is smaller. On a strict reading this diff — the project's first network-facing surface,
  parsing untrusted query input — auto-escalates to HIGH. **I flag this as a finding as instructed,
  but I do not re-tier the wave**, because the practical consequence is already ordered by the plan
  and already open: the pulled-forward security pass (row 4, W-016) has not run, and W1 is correctly
  held open for it. The one thing HIGH would add beyond that is a separate Tester seat.
- **MINOR-9 — `black --check` would reformat the new test file.**
  `.venv/bin/python -m black --check tests/unit/test_api_v1.py` → "would reformat" (the long
  `FakeRawSource(...)` call at `tests/unit/test_api_v1.py:89`). No gate is red: `make lint`
  (`Makefile:75-76`) runs ruff only, and `ruff check src tests` passes. Flagged because `make format`
  will rewrite the file and produce a spurious diff in someone else's wave.
- **MINOR-10 — dead condition.** `src/app/adapter/main.py:247`,
  `if task != "coding" and task not in CATEGORIES` — `"coding"` is a key of `CATEGORIES`
  (`src/app/workflows/categories.py:29-38`), so the first clause never changes the outcome. Harmless,
  but it reads as though `coding` were a pseudo-task, which it is not.

### PASS (what looks good)

- **PASS-1 — the engine really was not changed, and I verified it two ways, not by the claim.**
  `git diff --name-only 1faaf77..4dc6f53` returns exactly four paths, one of them under `src/`:
  ```
  docs/plans/m6-wave-1-close.md
  docs/warnings.ledger.md
  src/app/adapter/main.py
  tests/unit/test_api_v1.py
  ```
  and `git status --short` is empty, so no uncommitted engine edit is hiding behind the commit range.
  Full suite: **284 passed, 12 skipped** — the number row 9 claims, and up 13 from the 271 baseline.
- **PASS-2 — the read-only serving invariant is proven, not asserted.** Mutant M5: replacing the body
  of `serving_snapshot` (`src/app/adapter/main.py:75-101`) with `return sqlite3.connect(str(path))`
  turns `tests/unit/test_api_v1.py:266` (`test_the_api_never_writes_to_the_database`) **RED**. The
  claim at checklist row 7(b) stands on its own evidence. `tests/unit/test_api_v1.py:280`
  additionally proves the handle itself rejects DDL.
- **PASS-3 — the four declared mutants are real kills.** I reproduced M1 (precedence flag), M2
  (one surface for the coding intent), M3 (path in the error body) and M4 (evidence-dating dropped)
  independently in a scratch tree; each turned exactly the named test RED. Declaring fault-injection
  targets in the signed plan *before* the code was written (`m6-plan.md:132-133`) is the right
  discipline and it worked.
- **PASS-4 — fail-closed direction is correct and ordered correctly.** Input validation
  (`src/app/adapter/main.py:247-254`) runs before any filesystem touch; a missing database yields 503
  with a fixed sentence and no path (`:256-260`); `_error` (`:108-110`) is the single error
  constructor and the shape is asserted exhaustively at `tests/unit/test_api_v1.py:211`
  (`set(body["error"]) == {"code", "message"}`).
- **PASS-5 — a surface that cannot answer is disclosed rather than dropped**
  (`src/app/adapter/main.py:186-204`, test at `tests/unit/test_api_v1.py:240-260`). Dropping it would
  have been the cheapest implementation and the one that quietly violates Ruling A precisely when the
  data is thinnest. The comment at `:189-190` says exactly that. This is the best judgement call in
  the wave.
- **PASS-6 — the W-017 write-up is a model of an honest containment.**
  `docs/plans/m6-wave-1-close.md:33-49` and `docs/warnings.ledger.md` W-017 state plainly that the
  in-memory snapshot contains the defect rather than fixing it, name the cost, and assign the owning
  milestone. It also correctly refuses to touch the engine, as the plan requires.

---

## Acceptance criteria evidence

Every row below was checked by reading the test AND by mutating the implementation in a scratch copy
of the tree to confirm the test can fail. A test I could not make fail is recorded as such.

| Criterion | Citing test (file:line) | Implementation | Shown able to fail? |
|---|---|---|---|
| **REQ-API-001** (versioned read-only surface; `/health` untouched; **no mutating route**) | `tests/unit/test_api_v1.py:177` `test_no_mutating_route_exists`; `:187` `test_categories_endpoint_lists_the_registry`; `:194` `test_health_contract_is_untouched` | `src/app/adapter/main.py:207`, `:218`, `:237` | **PARTIAL.** Mutant M7 (add `@app.post("/v1/refresh")`) → RED. Mutant M8 (mount a sub-app exposing POST) → **stays green** (MINOR-1). |
| **REQ-API-002** (Ruling A: two answers, neither ranked, non-semantic documented order) | `tests/unit/test_api_v1.py:123`, `:159`, `:166` | `src/app/adapter/main.py:50`, `:52-56`, `:262`, `:272-278` | **PARTIAL.** M2 (one surface) → RED; M1 (`primary`) → RED; **M1b (`primary_surface` + `top_pick`) → stays green** — BLOCKING-2. |
| **REQ-API-004** (undated evidence disclosed in the payload) | `tests/unit/test_api_v1.py:145` `test_each_coding_surface_states_its_own_weakness` | `src/app/adapter/main.py:113-135`, `:173-174` | **YES.** M4 (`_evidence_dating` always returns `"dated"`) → RED. Correctly derived from the picks served, not from category policy. |
| **REQ-API-005** (error contract, 4 cases, no path leak) | unknown task → `tests/unit/test_api_v1.py:204`; unknown budget → `:214`; missing database → `:221`; **unhealthy source → NONE** | `src/app/adapter/main.py:108-110`, `:247-260` | **NO — one case uncovered.** M3 (path in the body) → RED for the missing-database case. The unhealthy-source case has neither test nor code path — **BLOCKING-1**. |

REQ-API-003 and REQ-API-006 are W2/W3 scope and are correctly out of this wave, with the exception of
REQ-API-006's read-only-handle clause, which W1 delivered early and proved (PASS-2).

## Hardened-invariant producer section (V3C-101)

Not strictly required at MED, supplied because checklist row 7 declares three security invariants.

**Producers of "the serving path never writes the operator's database", enumerated from code:**
`open_readonly` (`src/app/adapter/main.py:61`) and `serving_snapshot` (`src/app/adapter/main.py:75`),
with exactly one call site — `src/app/adapter/main.py:264`, inside the `/v1/recommendations` handler.
`grep -n "sqlite3.connect\|serving_snapshot\|open_readonly" src/app/adapter/main.py` returns lines
72, 95, 97, 264 and nothing else, so there is no second path to a connection in the adapter.
**Citing test per producer:** `open_readonly` → `tests/unit/test_api_v1.py:280`; `serving_snapshot`
(and the call site) → `tests/unit/test_api_v1.py:266`, mutation-confirmed RED.
**Gaps (tracked):** nothing forbids a *future* route from calling `sqlite3.connect` directly — the
invariant is held by convention plus one test over one handler, not by a seam that a new call site
must pass through. Queued to W3 alongside REQ-API-006 and W-009.

## K.8 contract drift check

Frozen-consumed surfaces (`m6-plan.md:181-185`):
```
$ grep -n "def recommend(" src/app/workflows/recommend.py
277:def recommend(
$ grep -rn "recommend(conn" src/app/adapter/main.py
194:        rec = recommend(conn, budget=budget, task=task)
$ grep -rn "def migrate" src/app/workflows/schema.py
240:def migrate(conn: sqlite3.Connection) -> list[str]:
```
Called by keyword against the frozen signature; `migrate` untouched; `Pick`'s 19 field names are
reproduced verbatim in `_pick_json` (checked programmatically — zero missing, zero renamed);
`Recommendation`'s fields are complete except `task`/`budget`, which the envelope carries at
`src/app/adapter/main.py:274`.

New surfaces frozen by this wave (`m6-plan.md:187-190`):
```
$ grep -rn 'API_VERSION\|"/v1' src/
src/app/adapter/main.py:45:API_VERSION = "v1"
src/app/adapter/main.py:218:@app.get(f"/{API_VERSION}/categories")
src/app/adapter/main.py:237:@app.get(f"/{API_VERSION}/recommendations")
src/app/adapter/main.py:273:        "api_version": API_VERSION,
$ grep -rn '"surface"\|CODING_INTENT' src/
src/app/adapter/main.py:50:CODING_INTENT: tuple[str, ...] = ("agentic-coding", "coding")
src/app/adapter/main.py:168:        "surface": spec.id,
src/app/adapter/main.py:232:        "coding_intent_surfaces": list(CODING_INTENT),
src/app/adapter/main.py:262:    surfaces = CODING_INTENT if task == "coding" else (task,)
$ grep -rn 'evidence_dating' src/
src/app/adapter/main.py:113,166,173,174
```
**Verdict: OK, no drift.** One gap against the plan's own list: `MODEL_RANKING_DB` is a new external
config surface that the plan never declared and the checklist never scoped (MINOR-7).

## Countersignature of the wave-close checklist (v3.3 anti self-attestation)

I picked **row 5** and **row 6**, and verified row 9's run line as a third since it was cheap.

**Row 5 (fault injection, `docs/plans/m6-wave-1-close.md:20`) — TRUE AS WRITTEN, OVERSTATED AS
EVIDENCE.**
- The md5 claim is exact. `md5 -q src/app/adapter/main.py` at `4dc6f53` returns
  `c7eeb711bf98bd2b0b80ab3aa446a36d`, byte-for-byte the value the row records for its restore. The
  in-place revert discipline (V3C-06/F17) is confirmed, and `git status --short` is empty.
- All four declared mutants are genuine kills — I reproduced each independently.
- **But "0 stayed green" describes four hand-picked mutants, not the fault class they represent.**
  Three of my own mutants inside the same declared classes stayed green: M1b (precedence flag under
  an adjacent name — the class of declared target M1), M8 (mutating route behind a mount — the class
  of REQ-API-001's absence proof), M9/M10 (a disclosure dropped from the payload). Under V3C-72 each
  of those now owes a mandatory new test.

**Row 6 (every criterion has a citing test through the LIVE entry point,
`docs/plans/m6-wave-1-close.md:21`) — HALF TRUE.**
- The live-entry-point half is TRUE and I checked it test by test. Every test in the file drives
  `TestClient(adapter.app)` over the real routes, either through the `client` fixture
  (`tests/unit/test_api_v1.py:97-104`) or by constructing a client inline (`:229`, `:254`). The one
  declared exception, `test_read_only_handle_refuses_a_write` (`:280`), calls `open_readonly`
  directly and says so; that is the right call, because the seam has to be provable on its own.
  V3C-73 "built != wired" is satisfied: a bug in routing, in query parsing or in the envelope would
  be caught, because nothing bypasses the handler.
- The coverage half is OVERSTATED. The row lists four tests under REQ-API-005, which reads as four
  cases covered; the fourth is the empty-database test and REQ-API-005's third case (an unhealthy
  source) has no test at all. See BLOCKING-1.

**Row 9 (run line, `docs/plans/m6-wave-1-close.md:27`) — TRUE, with one stale number.** I re-ran:
`pytest` → **284 passed / 12 skipped** (matches); `ruff check src tests` → clean; `mypy
src/app/adapter/main.py` → clean; conformance → **6 of 7**, with `test-documented-commands` FAIL on
the three historical records the row names as GPF-001 (matches, and is correctly not claimed as this
wave's). `check_records.py` now reports **29** records, not the 28 the row states — the wave-close
record itself became the 29th after the row was written. Immaterial, but the row is a snapshot, not a
current fact.

## K.9 candidates spotted outside this wave's scope

- `docs/coverage-by-req.md` contains **no REQ-API rows at all** (`grep -n "REQ-API"` → no output)
  while `docs/prd.md:335-340` carries all six. Stage 4.1's REQ-ID trace will need them; better added
  as each wave lands than reconstructed at closure. → M6 closure.
- The budget-shutout disclosure — `budget_notice`, `scoreable_plans`, `excluded_by_budget`
  (`src/app/workflows/recommend.py:437-441`) — exists only on the CLI's subscription path and has no
  counterpart in the JSON payload, where an unaffordable request instead yields the adapter's own
  English sentence (`src/app/adapter/main.py:199-203`). `m6-plan.md:113` lists "the budget notice
  (D-111)" among the disclosures REQ-API-003 must find in all three renderings. → W2, and its parity
  test should be shown RED on this before it is shown green.
- FastAPI's default `/docs`, `/redoc`, `/openapi.json` are live on this app (route dump confirms
  them; all GET, so `test_no_mutating_route_exists` is untroubled). Publishing the interactive schema
  of a public read-only API is defensible, but it should be a ruling rather than a default. → W3,
  with REQ-API-006.

## Risks queued to next M

- The invariant "no route writes the operator's database" is held by one test over one handler, not
  by a seam. W-017's real fix (a median computation that does not write) is already owned by M6-W3;
  the seam question should ride with it.
- `serving_snapshot` copies the **entire** operator database into memory on **every unauthenticated
  GET**, with no auth, no rate limit and no size cap. W-017 records the cost as growing with the
  database, which frames it as performance; the security framing is attacker-triggerable memory
  amplification on the project's first public route. This is not a W1 blocker — the containment is
  correct and the alternative was an engine change the plan forbids — but it is precisely the input
  the pulled-forward security pass was scheduled to receive, and that pass has not run (W-016). It
  must not be closed by a reviewer who was told the write problem is "contained".
- The `/v1` contract freezes a Turkish query vocabulary and a mixed-language payload (MINOR-5)
  without an ADR (MINOR-6). Both get harder to change after M6 closes, by the plan's own §4.

## Process note (not a finding)

Checklist row 2 states the acceptance tests were written first and confirmed RED at 10 failed / 3
passed. The wave is a single squashed commit, so no artifact of the red state survives and I could
not verify the claim either way. Recording it so the next reviewer does not mistake my silence for
confirmation. It does not change the verdict: I re-derived the red state by mutation instead, which
is the stronger evidence anyway.

**Consequence of this verdict (profile, "When you finish"): BLOCKING → STOP. W2 does not dispatch
until BLOCKING-1 and BLOCKING-2 are fixed and this review re-runs.** W1 was already held open for
W-016 (no fresh-eyes review, no pulled-forward security pass); this review supplies the fresh eyes
for the code half only. The security pass is still owed.
